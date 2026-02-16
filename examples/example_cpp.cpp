/*
 * example_cpp.cpp
 *
 * Example usage of the EIPtoNATSBridge in pure C++ (without Python),
 * ideal for debugging with VSCode/GDB
 */

#include "EIPtoNATSBridge.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <csignal>

using namespace bridge;

// Global variable for Ctrl+C
volatile bool keep_running = true;

void signal_handler(int signum) {
    std::cout << "\nInterrupt signal received. Stopping..." << std::endl;
    keep_running = false;
}

int main(int argc, char** argv) {
    std::cout << "======================================" << std::endl;
    std::cout << "  EIPtoNATSBridge - Standalone Test" << std::endl;
    std::cout << "======================================" << std::endl;
    std::cout << std::endl;

    // Capture Ctrl+C
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Configuration
    std::string plc_address = "192.168.17.200";
    std::string nats_url = "nats://192.168.17.138:4222";
    std::string nats_subject = "plc.cpp.test";
    bool use_binary = true;

    std::cout << "Configuration:" << std::endl;
    std::cout << "   PLC: " << plc_address << std::endl;
    std::cout << "   NATS: " << nats_url << std::endl;
    std::cout << "   Subject: " << nats_subject << std::endl;
    std::cout << "   Format: " << (use_binary ? "Binary" : "JSON") << std::endl;
    std::cout << std::endl;

    try {
        // Create bridge (using RM75E device presets)
        std::cout << "Creating bridge..." << std::endl;
        EIPtoNATSBridge bridge(plc_address, nats_url, nats_subject, use_binary,
                               devices::RM75E::CONFIG_ASSEMBLY,
                               devices::RM75E::O2T_ASSEMBLY,
                               devices::RM75E::T2O_ASSEMBLY,
                               100  // t2o_size: application-specific
        );

        // USEFUL BREAKPOINT HERE
        // You can inspect the bridge before starting

        std::cout << "Bridge created" << std::endl;
        std::cout << std::endl;

        // Start
        std::cout << "Starting bridge..." << std::endl;
        if (!bridge.start()) {
            std::cerr << "Error starting the bridge" << std::endl;
            std::cerr << std::endl;
            std::cerr << "Check that:" << std::endl;
            std::cerr << "   - The PLC is reachable" << std::endl;
            std::cerr << "   - The NATS server is running" << std::endl;
            return 1;
        }

        std::cout << "Bridge started successfully" << std::endl;
        std::cout << std::endl;

        // Monitor
        std::cout << "Monitoring (Ctrl+C to stop)..." << std::endl;
        std::cout << "----------------------------------------" << std::endl;

        uint64_t last_received = 0;
        uint64_t last_published = 0;

        while (keep_running && bridge.isRunning()) {
            std::this_thread::sleep_for(std::chrono::seconds(2));

            uint64_t received = bridge.getReceivedCount();
            uint64_t published = bridge.getPublishedCount();

            // Calculate rate
            double rx_rate = (received - last_received) / 2.0;
            double tx_rate = (published - last_published) / 2.0;

            // Timestamp
            auto now = std::chrono::system_clock::now();
            auto time = std::chrono::system_clock::to_time_t(now);
            char timestamp[20];
            std::strftime(timestamp, sizeof(timestamp), "%H:%M:%S", std::localtime(&time));

            std::cout << "[" << timestamp << "] "
                     << "RX=" << received << " (" << rx_rate << "/s) | "
                     << "TX=" << published << " (" << tx_rate << "/s) | "
                     << "Reconnects=" << bridge.getReconnectCount()
                     << std::endl;

            // USEFUL BREAKPOINT HERE
            // You can inspect real-time statistics

            last_received = received;
            last_published = published;
        }

        // Stop
        std::cout << std::endl;
        std::cout << "Stopping bridge..." << std::endl;
        bridge.stop();

        // Final statistics
        std::cout << std::endl;
        std::cout << "======================================" << std::endl;
        std::cout << "Final statistics:" << std::endl;
        std::cout << "   Messages received: " << bridge.getReceivedCount() << std::endl;
        std::cout << "   Messages published: " << bridge.getPublishedCount() << std::endl;
        std::cout << "   Reconnections: " << bridge.getReconnectCount() << std::endl;
        std::cout << "======================================" << std::endl;
        std::cout << std::endl;

        if (bridge.getReceivedCount() > 0) {
            std::cout << "Test completed successfully" << std::endl;
            return 0;
        } else {
            std::cout << "Warning: No data received from PLC" << std::endl;
            return 1;
        }

    } catch (const std::exception& e) {
        std::cerr << std::endl;
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
}
