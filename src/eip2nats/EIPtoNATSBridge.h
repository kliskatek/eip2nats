#ifndef EIP_TO_NATS_BRIDGE_H
#define EIP_TO_NATS_BRIDGE_H

#include <memory>
#include <thread>
#include <atomic>
#include <mutex>
#include <string>
#include <vector>
#include <nats.h>
#include <cip/connectionManager/NetworkConnectionParams.h>
#include "SessionInfo.h"
#include "ConnectionManager.h"

namespace bridge {

/// Assembly presets for known EIP devices
namespace devices {

struct RM75E {
    static constexpr uint8_t CONFIG_ASSEMBLY = 4;
    static constexpr uint8_t O2T_ASSEMBLY    = 2;
    static constexpr uint8_t T2O_ASSEMBLY    = 1;
};

struct ClipX {
    static constexpr uint8_t CONFIG_ASSEMBLY = 151;  // 0x97
    static constexpr uint8_t O2T_ASSEMBLY    = 150;  // 0x96
    static constexpr uint8_t T2O_ASSEMBLY    = 100;  // 0x64
};

} // namespace devices

/**
 * @brief Bridge between EtherNet/IP (using EIPScanner) and NATS
 *
 * This class manages an implicit EIP connection and publishes received
 * data to a NATS server in a separate thread.
 */
class EIPtoNATSBridge {
public:
    /**
     * @brief Constructor
     * @param plcAddress PLC IP address
     * @param natsUrl NATS server URL (e.g. "nats://192.168.17.138:4222")
     * @param natsSubject Subject/topic where data will be published
     * @param useBinaryFormat If true uses binary, if false uses JSON (default: true)
     */
    EIPtoNATSBridge(const std::string& plcAddress,
                    const std::string& natsUrl,
                    const std::string& natsSubject,
                    bool useBinaryFormat = true,
                    uint8_t configAssembly = devices::RM75E::CONFIG_ASSEMBLY,
                    uint8_t o2tAssembly = devices::RM75E::O2T_ASSEMBLY,
                    uint8_t t2oAssembly = devices::RM75E::T2O_ASSEMBLY,
                    uint16_t t2oSize = 0);

    /**
     * @brief Destructor - ensures everything is cleanly closed
     */
    ~EIPtoNATSBridge();

    /**
     * @brief Start the bridge: connect to NATS, open EIP connection and start the thread
     * @return true if started successfully, false on error
     */
    bool start();

    /**
     * @brief Stop the bridge: close EIP connection, disconnect from NATS and stop the thread
     */
    void stop();

    /**
     * @brief Check if the bridge is running
     * @return true if active, false if stopped
     */
    bool isRunning() const;

    /**
     * @brief Get the number of published messages
     * @return Count of messages sent to NATS
     */
    uint64_t getPublishedCount() const;

    /**
     * @brief Get the number of messages received from the PLC
     * @return Count of messages received via EIP
     */
    uint64_t getReceivedCount() const;

    /**
     * @brief Get the number of automatic reconnections
     * @return Count of successful EIP reconnections
     */
    uint64_t getReconnectCount() const;

private:
    // Configuration
    std::string plcAddress_;
    std::string natsUrl_;
    std::string natsSubject_;
    bool useBinaryFormat_;
    uint8_t configAssembly_;
    uint8_t o2tAssembly_;
    uint8_t t2oAssembly_;
    uint16_t t2oSize_;

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

    // Statistics
    std::atomic<uint64_t> publishedCount_;
    std::atomic<uint64_t> receivedCount_;

    // Reconnection
    std::atomic<bool> needsReconnect_;
    std::atomic<uint64_t> reconnectCount_;
    static constexpr int kReconnectDelayMs = 3000;

    /**
     * @brief Main worker thread function
     */
    void workerLoop();

    /**
     * @brief Initialize the NATS connection
     * @return true if connected successfully
     */
    bool initNATS();

    /**
     * @brief Initialize the EIP connection
     * @return true if connected successfully
     */
    bool initEIP();

    /**
     * @brief Close the NATS connection
     */
    void closeNATS();

    /**
     * @brief Close the EIP connection
     */
    void closeEIP();

    /**
     * @brief Publish data to NATS
     * @param data Vector of bytes to publish
     * @return true if published successfully
     */
    bool publishToNATS(const std::vector<uint8_t>& data);

    /**
     * @brief Callback for data received from the PLC
     */
    void onEIPDataReceived(uint32_t realTimeHeader,
                          uint16_t sequence,
                          const std::vector<uint8_t>& data);
};

} // namespace bridge

#endif // EIP_TO_NATS_BRIDGE_H
