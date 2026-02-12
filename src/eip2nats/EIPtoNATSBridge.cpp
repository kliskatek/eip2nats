#include "EIPtoNATSBridge.h"
#include "utils/Logger.h"
#include "utils/Buffer.h"
#include <sstream>
#include <iomanip>
#include <chrono>

using namespace bridge;
using namespace eipScanner;
using namespace eipScanner::cip;
using namespace eipScanner::cip::connectionManager;
using namespace eipScanner::utils;

EIPtoNATSBridge::EIPtoNATSBridge(const std::string& plcAddress, 
                                 const std::string& natsUrl,
                                 const std::string& natsSubject,
                                 bool useBinaryFormat)
    : plcAddress_(plcAddress)
    , natsUrl_(natsUrl)
    , natsSubject_(natsSubject)
    , useBinaryFormat_(useBinaryFormat)
    , natsConn_(nullptr)
    , natsOpts_(nullptr)
    , connectionManager_(nullptr)
    , running_(false)
    , shouldStop_(false)
    , publishedCount_(0)
    , receivedCount_(0)
{
    Logger(LogLevel::INFO) << "EIPtoNATSBridge creado - PLC: " << plcAddress 
                           << " NATS: " << natsUrl 
                           << " Subject: " << natsSubject
                           << " Formato: " << (useBinaryFormat ? "Binario" : "JSON");
}

EIPtoNATSBridge::~EIPtoNATSBridge() {
    if (running_) {
        Logger(LogLevel::WARNING) << "Bridge destruido mientras estaba corriendo - deteniendo...";
        stop();
    }
}

bool EIPtoNATSBridge::start() {
    if (running_) {
        Logger(LogLevel::WARNING) << "Bridge ya está corriendo";
        return false;
    }
    
    Logger(LogLevel::INFO) << "Iniciando EIPtoNATS Bridge...";
    
    // Inicializar NATS primero
    if (!initNATS()) {
        Logger(LogLevel::ERROR) << "Fallo al inicializar NATS";
        return false;
    }
    
    // Inicializar EIP
    if (!initEIP()) {
        Logger(LogLevel::ERROR) << "Fallo al inicializar EIP";
        closeNATS();
        return false;
    }
    
    // Arrancar el thread worker
    shouldStop_ = false;
    running_ = true;
    workerThread_ = std::thread(&EIPtoNATSBridge::workerLoop, this);
    
    Logger(LogLevel::INFO) << "✅ Bridge iniciado exitosamente";
    return true;
}

void EIPtoNATSBridge::stop() {
    if (!running_) {
        Logger(LogLevel::WARNING) << "Bridge ya está detenido";
        return;
    }
    
    Logger(LogLevel::INFO) << "Deteniendo EIPtoNATS Bridge...";
    
    // Señalizar al thread que debe detenerse
    shouldStop_ = true;
    
    // Esperar a que el thread termine
    if (workerThread_.joinable()) {
        workerThread_.join();
    }
    
    // Cerrar conexiones
    closeEIP();
    closeNATS();
    
    running_ = false;
    
    Logger(LogLevel::INFO) << "✅ Bridge detenido - Mensajes recibidos: " 
                           << receivedCount_ << " - Mensajes publicados: " 
                           << publishedCount_;
}

bool EIPtoNATSBridge::isRunning() const {
    return running_;
}

uint64_t EIPtoNATSBridge::getPublishedCount() const {
    return publishedCount_;
}

uint64_t EIPtoNATSBridge::getReceivedCount() const {
    return receivedCount_;
}

bool EIPtoNATSBridge::initNATS() {
    Logger(LogLevel::INFO) << "Conectando a NATS: " << natsUrl_;
    
    natsStatus s;
    
    // Crear opciones
    s = natsOptions_Create(&natsOpts_);
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error creando opciones NATS: " << natsStatus_GetText(s);
        return false;
    }
    
    // Configurar URL
    s = natsOptions_SetURL(natsOpts_, natsUrl_.c_str());
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error configurando URL NATS: " << natsStatus_GetText(s);
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
        return false;
    }
    
    // Configurar timeout
    s = natsOptions_SetTimeout(natsOpts_, 5000);
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error configurando timeout NATS: " << natsStatus_GetText(s);
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
        return false;
    }
    
    // Conectar
    s = natsConnection_Connect(&natsConn_, natsOpts_);
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error conectando a NATS: " << natsStatus_GetText(s);
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
        return false;
    }
    
    Logger(LogLevel::INFO) << "✅ Conectado a NATS exitosamente";
    return true;
}

bool EIPtoNATSBridge::initEIP() {
    Logger(LogLevel::INFO) << "Conectando a PLC EIP: " << plcAddress_;
    
    try {
        // Crear SessionInfo
        sessionInfo_ = std::make_shared<SessionInfo>(plcAddress_, 0xAF12);
        
        // Crear ConnectionManager
        connectionManager_ = std::make_unique<ConnectionManager>();
        
        // Configurar parámetros de conexión (basado en tu código original)
        ConnectionParameters parameters;
        parameters.connectionPath = {0x20, 0x04, 0x24, 4, 0x2C, 2, 0x2C, 1};
        parameters.o2tRealTimeFormat = true;
        parameters.originatorVendorId = 342;
        parameters.originatorSerialNumber = 0x12345;
        
        parameters.t2oNetworkConnectionParams |= NetworkConnectionParams::P2P;
        parameters.t2oNetworkConnectionParams |= NetworkConnectionParams::SCHEDULED_PRIORITY;
        parameters.t2oNetworkConnectionParams |= 100;
        
        parameters.o2tNetworkConnectionParams |= NetworkConnectionParams::P2P;
        parameters.o2tNetworkConnectionParams |= NetworkConnectionParams::SCHEDULED_PRIORITY;
        parameters.o2tNetworkConnectionParams |= 0;
        
        parameters.o2tRPI = 2000;
        parameters.t2oRPI = 2000;
        parameters.transportTypeTrigger |= NetworkConnectionParams::CLASS1 | NetworkConnectionParams::TRIG_CYCLIC;
        
        // Abrir conexión
        ioConnection_ = connectionManager_->forwardOpen(sessionInfo_, parameters);
        
        if (auto ptr = ioConnection_.lock()) {
            // Configurar listener para datos recibidos
            ptr->setReceiveDataListener([this](auto realTimeHeader, auto sequence, auto data) {
                this->onEIPDataReceived(realTimeHeader, sequence, data);
            });
            
            // Configurar listener para cierre de conexión
            ptr->setCloseListener([this]() {
                Logger(LogLevel::WARNING) << "Conexión EIP cerrada por el PLC";
                shouldStop_ = true;
            });
            
            Logger(LogLevel::INFO) << "✅ Conexión EIP abierta exitosamente";
            return true;
        } else {
            Logger(LogLevel::ERROR) << "Error: No se pudo obtener el puntero de IOConnection";
            return false;
        }
        
    } catch (const std::exception& e) {
        Logger(LogLevel::ERROR) << "Excepción al inicializar EIP: " << e.what();
        return false;
    }
}

void EIPtoNATSBridge::closeNATS() {
    std::lock_guard<std::mutex> lock(natsMutex_);
    
    if (natsConn_ != nullptr) {
        Logger(LogLevel::INFO) << "Cerrando conexión NATS...";
        natsConnection_Destroy(natsConn_);
        natsConn_ = nullptr;
    }
    
    if (natsOpts_ != nullptr) {
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
    }
}

void EIPtoNATSBridge::closeEIP() {
    Logger(LogLevel::INFO) << "Cerrando conexión EIP...";
    
    if (connectionManager_ && sessionInfo_) {
        try {
            connectionManager_->forwardClose(sessionInfo_, ioConnection_);
            Logger(LogLevel::INFO) << "Forward Close enviado";
        } catch (const std::exception& e) {
            Logger(LogLevel::ERROR) << "Error en forward close: " << e.what();
        }
    }
    
    ioConnection_.reset();
    connectionManager_.reset();
    sessionInfo_.reset();
}

void EIPtoNATSBridge::workerLoop() {
    Logger(LogLevel::INFO) << "Thread worker iniciado";
    
    while (!shouldStop_ && connectionManager_->hasOpenConnections()) {
        // Manejar las conexiones EIP (procesar datos entrantes)
        connectionManager_->handleConnections(std::chrono::milliseconds(1));
    }
    
    Logger(LogLevel::INFO) << "Thread worker finalizando";
}

bool EIPtoNATSBridge::publishToNATS(const std::vector<uint8_t>& data) {
    std::lock_guard<std::mutex> lock(natsMutex_);
    
    if (natsConn_ == nullptr) {
        Logger(LogLevel::ERROR) << "No hay conexión NATS activa";
        return false;
    }
    
    natsStatus s;
    
    if (useBinaryFormat_) {
        // Publicar datos binarios directamente (más eficiente)
        s = natsConnection_Publish(natsConn_, 
                                   natsSubject_.c_str(), 
                                   data.data(), 
                                   data.size());
    } else {
        // Publicar como JSON (para debugging o interoperabilidad)
        std::ostringstream jsonStream;
        jsonStream << "{\"timestamp\":" << time(nullptr) 
                   << ",\"sequence\":" << receivedCount_
                   << ",\"size\":" << data.size()
                   << ",\"data\":\"";
        
        // Convertir bytes a hexadecimal
        for (const auto& byte : data) {
            jsonStream << std::hex << std::setfill('0') << std::setw(2) << (int)byte;
        }
        
        jsonStream << "\"}";
        std::string jsonStr = jsonStream.str();
        
        s = natsConnection_PublishString(natsConn_, natsSubject_.c_str(), jsonStr.c_str());
    }
    
    if (s == NATS_OK) {
        publishedCount_++;
        Logger(LogLevel::DEBUG) << "Publicado a NATS [" << publishedCount_ << "]: " 
                               << data.size() << " bytes (" 
                               << (useBinaryFormat_ ? "binario" : "JSON") << ")";
        return true;
    } else {
        Logger(LogLevel::ERROR) << "Error publicando a NATS: " << natsStatus_GetText(s);
        return false;
    }
}

void EIPtoNATSBridge::onEIPDataReceived(uint32_t realTimeHeader, 
                                        uint16_t sequence, 
                                        const std::vector<uint8_t>& data) {
    receivedCount_++;
    
    // Log detallado de lo recibido
    std::ostringstream ss;
    ss << "EIP RX [" << receivedCount_ << "] seq=" << sequence 
       << " size=" << data.size() << " data=";
    for (const auto& byte : data) {
        ss << std::hex << std::setfill('0') << std::setw(2) << (int)byte << " ";
    }
    
    Logger(LogLevel::DEBUG) << ss.str();
    
    // Publicar a NATS
    if (!publishToNATS(data)) {
        Logger(LogLevel::WARNING) << "Fallo al publicar datos a NATS";
    }
}
