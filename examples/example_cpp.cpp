/*
 * example_cpp.cpp
 *
 * Ejemplo de uso del bridge EIPtoNATSBridge en C++ puro (sin Python),
 * ideal para debugging con VSCode/GDB
 */

#include "EIPtoNATSBridge.h"
#include <iostream>
#include <thread>
#include <chrono>
#include <csignal>

using namespace bridge;

// Variable global para Ctrl+C
volatile bool keep_running = true;

void signal_handler(int signum) {
    std::cout << "\n🛑 Señal de interrupción recibida. Deteniendo..." << std::endl;
    keep_running = false;
}

int main(int argc, char** argv) {
    std::cout << "======================================" << std::endl;
    std::cout << "  EIPtoNATSBridge - Standalone Test" << std::endl;
    std::cout << "======================================" << std::endl;
    std::cout << std::endl;
    
    // Capturar Ctrl+C
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    // Configuración
    std::string plc_address = "192.168.17.200";
    std::string nats_url = "nats://192.168.17.138:4222";
    std::string nats_subject = "plc.cpp.test";
    bool use_binary = true;
    
    std::cout << "📋 Configuración:" << std::endl;
    std::cout << "   PLC: " << plc_address << std::endl;
    std::cout << "   NATS: " << nats_url << std::endl;
    std::cout << "   Subject: " << nats_subject << std::endl;
    std::cout << "   Formato: " << (use_binary ? "Binario" : "JSON") << std::endl;
    std::cout << std::endl;
    
    try {
        // Crear bridge
        std::cout << "🔧 Creando bridge..." << std::endl;
        EIPtoNATSBridge bridge(plc_address, nats_url, nats_subject, use_binary);
        
        // PUNTO DE BREAKPOINT ÚTIL AQUÍ
        // Puedes inspeccionar el bridge antes de iniciar
        
        std::cout << "✅ Bridge creado" << std::endl;
        std::cout << std::endl;
        
        // Iniciar
        std::cout << "🚀 Iniciando bridge..." << std::endl;
        if (!bridge.start()) {
            std::cerr << "❌ Error al iniciar el bridge" << std::endl;
            std::cerr << std::endl;
            std::cerr << "💡 Verifica que:" << std::endl;
            std::cerr << "   • El PLC esté accesible" << std::endl;
            std::cerr << "   • El servidor NATS esté corriendo" << std::endl;
            return 1;
        }
        
        std::cout << "✅ Bridge iniciado correctamente" << std::endl;
        std::cout << std::endl;
        
        // Monitorear
        std::cout << "📊 Monitoreando (Ctrl+C para detener)..." << std::endl;
        std::cout << "----------------------------------------" << std::endl;
        
        uint64_t last_received = 0;
        uint64_t last_published = 0;
        
        while (keep_running && bridge.isRunning()) {
            std::this_thread::sleep_for(std::chrono::seconds(2));
            
            uint64_t received = bridge.getReceivedCount();
            uint64_t published = bridge.getPublishedCount();
            
            // Calcular rate
            double rx_rate = (received - last_received) / 2.0;
            double tx_rate = (published - last_published) / 2.0;
            
            // Timestamp
            auto now = std::chrono::system_clock::now();
            auto time = std::chrono::system_clock::to_time_t(now);
            char timestamp[20];
            std::strftime(timestamp, sizeof(timestamp), "%H:%M:%S", std::localtime(&time));
            
            std::cout << "[" << timestamp << "] "
                     << "RX=" << received << " (" << rx_rate << "/s) | "
                     << "TX=" << published << " (" << tx_rate << "/s)"
                     << std::endl;
            
            // PUNTO DE BREAKPOINT ÚTIL AQUÍ
            // Puedes inspeccionar las estadísticas en tiempo real
            
            last_received = received;
            last_published = published;
        }
        
        // Detener
        std::cout << std::endl;
        std::cout << "🛑 Deteniendo bridge..." << std::endl;
        bridge.stop();
        
        // Estadísticas finales
        std::cout << std::endl;
        std::cout << "======================================" << std::endl;
        std::cout << "📊 Estadísticas finales:" << std::endl;
        std::cout << "   Mensajes recibidos: " << bridge.getReceivedCount() << std::endl;
        std::cout << "   Mensajes publicados: " << bridge.getPublishedCount() << std::endl;
        std::cout << "======================================" << std::endl;
        std::cout << std::endl;
        
        if (bridge.getReceivedCount() > 0) {
            std::cout << "✅ Test completado exitosamente" << std::endl;
            return 0;
        } else {
            std::cout << "⚠️  No se recibieron datos del PLC" << std::endl;
            return 1;
        }
        
    } catch (const std::exception& e) {
        std::cerr << std::endl;
        std::cerr << "❌ Excepción: " << e.what() << std::endl;
        return 1;
    }
}
