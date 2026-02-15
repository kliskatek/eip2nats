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
    Logger(LogLevel::INFO) << "EIPtoNATSBridge created - PLC: " << plcAddress
                           << " NATS: " << natsUrl
                           << " Subject: " << natsSubject
                           << " Format: " << (useBinaryFormat ? "Binary" : "JSON");
}

EIPtoNATSBridge::~EIPtoNATSBridge() {
    if (running_) {
        Logger(LogLevel::WARNING) << "Bridge destroyed while running - stopping...";
        stop();
    }
}

bool EIPtoNATSBridge::start() {
    if (running_) {
        Logger(LogLevel::WARNING) << "Bridge is already running";
        return false;
    }

    Logger(LogLevel::INFO) << "Starting EIPtoNATS Bridge...";

    // Initialize NATS first
    if (!initNATS()) {
        Logger(LogLevel::ERROR) << "Failed to initialize NATS";
        return false;
    }

    // Initialize EIP
    if (!initEIP()) {
        Logger(LogLevel::ERROR) << "Failed to initialize EIP";
        closeNATS();
        return false;
    }

    // Start the worker thread
    shouldStop_ = false;
    running_ = true;
    workerThread_ = std::thread(&EIPtoNATSBridge::workerLoop, this);

    Logger(LogLevel::INFO) << "Bridge started successfully";
    return true;
}

void EIPtoNATSBridge::stop() {
    if (!running_) {
        Logger(LogLevel::WARNING) << "Bridge is already stopped";
        return;
    }

    Logger(LogLevel::INFO) << "Stopping EIPtoNATS Bridge...";

    // Signal the thread to stop
    shouldStop_ = true;

    // Wait for the thread to finish
    if (workerThread_.joinable()) {
        workerThread_.join();
    }

    // Close connections
    closeEIP();
    closeNATS();

    running_ = false;

    Logger(LogLevel::INFO) << "Bridge stopped - Messages received: "
                           << receivedCount_ << " - Messages published: "
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
    Logger(LogLevel::INFO) << "Connecting to NATS: " << natsUrl_;

    natsStatus s;

    // Create options
    s = natsOptions_Create(&natsOpts_);
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error creating NATS options: " << natsStatus_GetText(s);
        return false;
    }

    // Set URL
    s = natsOptions_SetURL(natsOpts_, natsUrl_.c_str());
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error setting NATS URL: " << natsStatus_GetText(s);
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
        return false;
    }

    // Set timeout
    s = natsOptions_SetTimeout(natsOpts_, 5000);
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error setting NATS timeout: " << natsStatus_GetText(s);
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
        return false;
    }

    // Connect
    s = natsConnection_Connect(&natsConn_, natsOpts_);
    if (s != NATS_OK) {
        Logger(LogLevel::ERROR) << "Error connecting to NATS: " << natsStatus_GetText(s);
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
        return false;
    }

    Logger(LogLevel::INFO) << "Connected to NATS successfully";
    return true;
}

bool EIPtoNATSBridge::initEIP() {
    Logger(LogLevel::INFO) << "Connecting to EIP PLC: " << plcAddress_;

    try {
        // Create SessionInfo
        sessionInfo_ = std::make_shared<SessionInfo>(plcAddress_, 0xAF12);

        // Create ConnectionManager
        connectionManager_ = std::make_unique<ConnectionManager>();

        // Configure connection parameters
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

        // Open connection
        ioConnection_ = connectionManager_->forwardOpen(sessionInfo_, parameters);

        if (auto ptr = ioConnection_.lock()) {
            // Set up listener for received data
            ptr->setReceiveDataListener([this](auto realTimeHeader, auto sequence, auto data) {
                this->onEIPDataReceived(realTimeHeader, sequence, data);
            });

            // Set up listener for connection close
            ptr->setCloseListener([this]() {
                Logger(LogLevel::WARNING) << "EIP connection closed by the PLC";
                shouldStop_ = true;
            });

            Logger(LogLevel::INFO) << "EIP connection opened successfully";
            return true;
        } else {
            Logger(LogLevel::ERROR) << "Error: Could not obtain IOConnection pointer";
            return false;
        }

    } catch (const std::exception& e) {
        Logger(LogLevel::ERROR) << "Exception initializing EIP: " << e.what();
        return false;
    }
}

void EIPtoNATSBridge::closeNATS() {
    std::lock_guard<std::mutex> lock(natsMutex_);

    if (natsConn_ != nullptr) {
        Logger(LogLevel::INFO) << "Closing NATS connection...";
        natsConnection_Destroy(natsConn_);
        natsConn_ = nullptr;
    }

    if (natsOpts_ != nullptr) {
        natsOptions_Destroy(natsOpts_);
        natsOpts_ = nullptr;
    }
}

void EIPtoNATSBridge::closeEIP() {
    Logger(LogLevel::INFO) << "Closing EIP connection...";

    if (connectionManager_ && sessionInfo_) {
        try {
            connectionManager_->forwardClose(sessionInfo_, ioConnection_);
            Logger(LogLevel::INFO) << "Forward Close sent";
        } catch (const std::exception& e) {
            Logger(LogLevel::ERROR) << "Error in forward close: " << e.what();
        }
    }

    ioConnection_.reset();
    connectionManager_.reset();
    sessionInfo_.reset();
}

void EIPtoNATSBridge::workerLoop() {
    Logger(LogLevel::INFO) << "Worker thread started";

    while (!shouldStop_ && connectionManager_->hasOpenConnections()) {
        // Handle EIP connections (process incoming data)
        connectionManager_->handleConnections(std::chrono::milliseconds(1));
    }

    Logger(LogLevel::INFO) << "Worker thread finishing";
}

bool EIPtoNATSBridge::publishToNATS(const std::vector<uint8_t>& data) {
    std::lock_guard<std::mutex> lock(natsMutex_);

    if (natsConn_ == nullptr) {
        Logger(LogLevel::ERROR) << "No active NATS connection";
        return false;
    }

    natsStatus s;

    if (useBinaryFormat_) {
        // Publish binary data directly (more efficient)
        s = natsConnection_Publish(natsConn_,
                                   natsSubject_.c_str(),
                                   data.data(),
                                   data.size());
    } else {
        // Publish as JSON (for debugging or interoperability)
        std::ostringstream jsonStream;
        jsonStream << "{\"timestamp\":" << time(nullptr)
                   << ",\"sequence\":" << receivedCount_
                   << ",\"size\":" << data.size()
                   << ",\"data\":\"";

        // Convert bytes to hexadecimal
        for (const auto& byte : data) {
            jsonStream << std::hex << std::setfill('0') << std::setw(2) << (int)byte;
        }

        jsonStream << "\"}";
        std::string jsonStr = jsonStream.str();

        s = natsConnection_PublishString(natsConn_, natsSubject_.c_str(), jsonStr.c_str());
    }

    if (s == NATS_OK) {
        publishedCount_++;
        Logger(LogLevel::DEBUG) << "Published to NATS [" << publishedCount_ << "]: "
                               << data.size() << " bytes ("
                               << (useBinaryFormat_ ? "binary" : "JSON") << ")";
        return true;
    } else {
        Logger(LogLevel::ERROR) << "Error publishing to NATS: " << natsStatus_GetText(s);
        return false;
    }
}

void EIPtoNATSBridge::onEIPDataReceived(uint32_t realTimeHeader,
                                        uint16_t sequence,
                                        const std::vector<uint8_t>& data) {
    receivedCount_++;

    // Detailed log of received data
    std::ostringstream ss;
    ss << "EIP RX [" << receivedCount_ << "] seq=" << sequence
       << " size=" << data.size() << " data=";
    for (const auto& byte : data) {
        ss << std::hex << std::setfill('0') << std::setw(2) << (int)byte << " ";
    }

    Logger(LogLevel::DEBUG) << ss.str();

    // Publish to NATS
    if (!publishToNATS(data)) {
        Logger(LogLevel::WARNING) << "Failed to publish data to NATS";
    }
}
