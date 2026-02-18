/*
 * example_cpp_clipx.cpp
 *
 * Standalone EtherNet/IP implicit connection test for HBK ClipX.
 * Uses EIPScanner directly (no NATS, no bridge) to open an I/O Class 1
 * connection and print raw data received from the ClipX.
 *
 * Assembly instances (from EDS - Anybus / HMS Networks stack):
 *   Input  (T→O): 100  (0x64) - ClipX → Scanner  (166 bytes)
 *   Output (O→T): 101  (0x65) - Scanner → ClipX   (44 bytes)
 *   Config:         1  (0x01)
 *
 * Connection path: 0x20 0x04 0x24 0x01 0x2C 0x65 0x2C 0x64
 */

#include "SessionInfo.h"
#include "ConnectionManager.h"
#include "cip/connectionManager/NetworkConnectionParams.h"
#include "utils/Logger.h"

#include <iostream>
#include <iomanip>
#include <sstream>
#include <thread>
#include <chrono>
#include <csignal>
#include <cstring>

#ifdef _WIN32
#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")
#endif

using namespace eipScanner;
using namespace eipScanner::cip;
using namespace eipScanner::cip::connectionManager;

// ── ClipX assembly configuration (from EDS) ──────────────
static constexpr uint8_t  CONFIG_ASSEMBLY = 1;    // 0x01
static constexpr uint8_t  O2T_ASSEMBLY    = 101;  // 0x65  Scanner → ClipX (44 bytes)
static constexpr uint8_t  T2O_ASSEMBLY    = 100;  // 0x64  ClipX → Scanner (166 bytes)
// EIPScanner adds CIP I/O headers automatically, so use data-only sizes:
//   O2T: 44 data → EIPScanner sends 50 on wire (+4 RT header +2 seq)
//   T2O: 166 data → EIPScanner sends 168 on wire (+2 seq)
static constexpr uint16_t O2T_SIZE        = 0;   // Assembly 101 data
static constexpr uint16_t T2O_SIZE        = 166;  // Assembly 100 data
static constexpr uint32_t RPI             = 1000; // Requested Packet Interval (µs)

// ── Global stop flag ──────────────────────────────────────
volatile bool keep_running = true;

void signal_handler(int) {
    std::cout << "\nInterrupt received. Stopping..." << std::endl;
    keep_running = false;
}

int main() {
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cerr << "WSAStartup failed" << std::endl;
        return 1;
    }
#endif

    std::cout << "==========================================" << std::endl;
    std::cout << "  EIPScanner - HBK ClipX implicit test" << std::endl;
    std::cout << "==========================================" << std::endl;
    std::cout << std::endl;

    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // ── Configuration ─────────────────────────────────────
    std::string clipx_ip = "192.168.17.114";  // Change to your ClipX IP

    std::cout << "ClipX IP:        " << clipx_ip << std::endl;
    std::cout << "Config Assembly: " << (int)CONFIG_ASSEMBLY << " (0x" << std::hex << (int)CONFIG_ASSEMBLY << ")" << std::dec << std::endl;
    std::cout << "O2T Assembly:    " << (int)O2T_ASSEMBLY    << " (0x" << std::hex << (int)O2T_ASSEMBLY    << ")" << std::dec << std::endl;
    std::cout << "T2O Assembly:    " << (int)T2O_ASSEMBLY    << " (0x" << std::hex << (int)T2O_ASSEMBLY    << ")" << std::dec << std::endl;
    std::cout << "O2T Data Size:   " << O2T_SIZE << " bytes" << std::endl;
    std::cout << "T2O Data Size:   " << T2O_SIZE << " bytes" << std::endl;
    std::cout << "RPI:             " << RPI << " µs" << std::endl;
    std::cout << std::endl;

    try {
        // ── Create session ────────────────────────────────
        auto sessionInfo = std::make_shared<SessionInfo>(clipx_ip, 0xAF12);
        auto connectionManager = std::make_unique<ConnectionManager>();

        // ── Connection parameters ─────────────────────────
        ConnectionParameters params;
        params.connectionPath = {0x20, 0x04, 0x24, CONFIG_ASSEMBLY, 0x2C, O2T_ASSEMBLY, 0x2C, T2O_ASSEMBLY};
        params.o2tRealTimeFormat = true;
        params.originatorVendorId = 342;
        params.originatorSerialNumber = 0x12345;

        // Match working parameters from Wireshark capture:
        // T2O: P2P, Low Priority, Fixed, 168 bytes (0x40A8)
        params.t2oNetworkConnectionParams |= NetworkConnectionParams::P2P;
        params.t2oNetworkConnectionParams |= T2O_SIZE;

        // O2T: P2P, Low Priority, Fixed, 50 bytes (0x4032)
        params.o2tNetworkConnectionParams |= NetworkConnectionParams::P2P;
        params.o2tNetworkConnectionParams |= O2T_SIZE;

        params.o2tRPI = RPI;
        params.t2oRPI = RPI;
        params.connectionTimeoutMultiplier = 4;
        params.transportTypeTrigger |= NetworkConnectionParams::CLASS1 | NetworkConnectionParams::TRIG_CYCLIC;

        // ── Forward Open ──────────────────────────────────
        std::cout << "Opening implicit connection..." << std::endl;
        auto ioConnection = connectionManager->forwardOpen(sessionInfo, params);

        if (auto ptr = ioConnection.lock()) {
            std::cout << "Connection opened successfully!" << std::endl;
            std::cout << std::endl;

            // Initialize O2T buffer (44 bytes of zeros) so the scanner
            // sends heartbeat packets and the ClipX doesn't timeout
            std::vector<uint8_t> o2tData(O2T_SIZE, 0);
            ptr->setDataToSend(o2tData);

            uint64_t rxCount = 0;

            // Set up data listener
            ptr->setReceiveDataListener([&rxCount](auto realTimeHeader, auto sequence, auto data) {
                rxCount++;

                if (rxCount%100==0) {
                    // Print header
                    std::cout << "[RX #" << rxCount << "] seq=" << sequence
                            << " size=" << data.size() << " bytes" << std::endl;

                    // Print raw hex dump
                    std::ostringstream hex;
                    hex << "  HEX: ";
                    for (size_t i = 0; i < data.size(); i++) {
                        hex << std::hex << std::setfill('0') << std::setw(2) << (int)data[i] << " ";
                        if ((i + 1) % 16 == 0 && i + 1 < data.size()) {
                            hex << "\n       ";
                        }
                    }
                    std::cout << hex.str() << std::dec << std::endl;

                    // Try to read first float (offset 0) as example
                    if (data.size() >= 4) {
                        float value;
                        std::memcpy(&value, data.data(), sizeof(float));
                        std::cout << "  Float@0: " << value << std::endl;
                    }

                    std::cout << std::endl;
                }
            });

            ptr->setCloseListener([]() {
                std::cerr << "Connection closed by ClipX!" << std::endl;
                keep_running = false;
            });

            // ── Main loop ─────────────────────────────────
            std::cout << "Listening for data (Ctrl+C to stop)..." << std::endl;
            std::cout << "----------------------------------------" << std::endl;

            while (keep_running && connectionManager->hasOpenConnections()) {
                connectionManager->handleConnections(std::chrono::milliseconds(1));
            }

            // ── Cleanup ───────────────────────────────────
            std::cout << std::endl;
            std::cout << "Closing connection..." << std::endl;
            connectionManager->forwardClose(sessionInfo, ioConnection);

            std::cout << "Total messages received: " << rxCount << std::endl;

        } else {
            std::cerr << "Error: Forward Open failed - could not open IO connection" << std::endl;
            return 1;
        }

    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }

    std::cout << "Done." << std::endl;

#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
