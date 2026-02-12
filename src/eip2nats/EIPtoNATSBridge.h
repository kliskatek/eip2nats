#ifndef EIP_TO_NATS_BRIDGE_H
#define EIP_TO_NATS_BRIDGE_H

#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <string>
#include <vector>
#include <nats/nats.h>
#include <cip/connectionManager/NetworkConnectionParams.h>
#include "SessionInfo.h"
#include "ConnectionManager.h"

namespace bridge {

/**
 * @brief Puente entre EtherNet/IP (usando EIPScanner) y NATS
 * 
 * Esta clase gestiona una conexión EIP implícita y publica los datos
 * recibidos a un servidor NATS en un thread separado.
 */
class EIPtoNATSBridge {
public:
    /**
     * @brief Constructor
     * @param plcAddress Dirección IP del PLC
     * @param natsUrl URL del servidor NATS (ej: "nats://192.168.17.138:4222")
     * @param natsSubject Subject/topic donde publicar los datos
     * @param useBinaryFormat Si es true usa binario, si es false usa JSON (default: true)
     */
    EIPtoNATSBridge(const std::string& plcAddress, 
                    const std::string& natsUrl,
                    const std::string& natsSubject,
                    bool useBinaryFormat = true);
    
    /**
     * @brief Destructor - asegura que todo esté limpiamente cerrado
     */
    ~EIPtoNATSBridge();
    
    /**
     * @brief Inicia el bridge: conecta a NATS, abre conexión EIP y arranca el thread
     * @return true si todo se inició correctamente, false en caso de error
     */
    bool start();
    
    /**
     * @brief Detiene el bridge: cierra conexión EIP, desconecta NATS y detiene el thread
     */
    void stop();
    
    /**
     * @brief Verifica si el bridge está corriendo
     * @return true si está activo, false si está detenido
     */
    bool isRunning() const;
    
    /**
     * @brief Obtiene el número de mensajes publicados
     * @return Contador de mensajes enviados a NATS
     */
    uint64_t getPublishedCount() const;
    
    /**
     * @brief Obtiene el número de mensajes recibidos del PLC
     * @return Contador de mensajes recibidos por EIP
     */
    uint64_t getReceivedCount() const;

private:
    // Configuración
    std::string plcAddress_;
    std::string natsUrl_;
    std::string natsSubject_;
    bool useBinaryFormat_;
    
    // NATS
    natsConnection* natsConn_;
    natsOptions* natsOpts_;
    std::mutex natsMutex_;
    
    // EIP Scanner
    std::shared_ptr<eipScanner::SessionInfo> sessionInfo_;
    std::unique_ptr<eipScanner::ConnectionManager> connectionManager_;
    std::weak_ptr<eipScanner::IOConnection> ioConnection_;
    
    // Thread control
    std::thread workerThread_;
    std::atomic<bool> running_;
    std::atomic<bool> shouldStop_;
    
    // Estadísticas
    std::atomic<uint64_t> publishedCount_;
    std::atomic<uint64_t> receivedCount_;
    
    /**
     * @brief Función principal del thread worker
     */
    void workerLoop();
    
    /**
     * @brief Inicializa la conexión NATS
     * @return true si se conectó correctamente
     */
    bool initNATS();
    
    /**
     * @brief Inicializa la conexión EIP
     * @return true si se conectó correctamente
     */
    bool initEIP();
    
    /**
     * @brief Cierra la conexión NATS
     */
    void closeNATS();
    
    /**
     * @brief Cierra la conexión EIP
     */
    void closeEIP();
    
    /**
     * @brief Publica datos a NATS
     * @param data Vector de bytes a publicar
     * @return true si se publicó correctamente
     */
    bool publishToNATS(const std::vector<uint8_t>& data);
    
    /**
     * @brief Callback para datos recibidos del PLC
     */
    void onEIPDataReceived(uint32_t realTimeHeader, 
                          uint16_t sequence, 
                          const std::vector<uint8_t>& data);
};

} // namespace bridge

#endif // EIP_TO_NATS_BRIDGE_H
