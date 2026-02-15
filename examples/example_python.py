#!/usr/bin/env python3
"""
Ejemplo de uso de eip2nats
Ejecutar dentro del entorno virtual: source venv/bin/activate
"""

import eip2nats
import time
import signal
import sys

# Variable de control
keep_running = True

def signal_handler(sig, frame):
    """Manejador para Ctrl+C"""
    global keep_running
    print("\n🛑 Deteniendo bridge...")
    keep_running = False

def main():
    print("=" * 60)
    print("  EIP to NATS Bridge - Ejemplo")
    print("=" * 60)
    print()
    
    # Configurar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuración - MODIFICA ESTAS VARIABLES
    plc_address = "192.168.17.200"
    nats_url = "nats://192.168.17.138:4222"
    nats_subject = "plc.eip.data"
    
    print("📋 Configuración:")
    print(f"   PLC: {plc_address}")
    print(f"   NATS: {nats_url}")
    print(f"   Subject: {nats_subject}")
    print()
    
    # Crear bridge
    print("🔧 Creando bridge...")
    bridge = eip2nats.EIPtoNATSBridge(
        plc_address,
        nats_url,
        nats_subject,
        True  # True = binario, False = JSON
    )
    
    print(f"   {bridge}")
    print()
    
    # Iniciar
    print("🚀 Iniciando bridge...")
    if not bridge.start():
        print("❌ Error al iniciar el bridge")
        return 1
    
    print("✅ Bridge corriendo")
    print("   Presiona Ctrl+C para detener")
    print()
    
    # Monitorear
    last_received = 0
    last_published = 0
    
    while keep_running and bridge.is_running():
        time.sleep(5)
        
        received = bridge.get_received_count()
        published = bridge.get_published_count()
        
        # Calcular rate
        received_rate = (received - last_received) / 5.0
        published_rate = (published - last_published) / 5.0
        
        print(f"📊 RX={received:6d} ({received_rate:5.1f}/s) | "
              f"TX={published:6d} ({published_rate:5.1f}/s)")
        
        last_received = received
        last_published = published
    
    # Detener
    print("\n🛑 Deteniendo bridge...")
    bridge.stop()
    
    # Estadísticas finales
    print("\n" + "=" * 60)
    print("📊 Estadísticas finales:")
    print(f"   Mensajes recibidos: {bridge.get_received_count()}")
    print(f"   Mensajes publicados: {bridge.get_published_count()}")
    print("=" * 60)
    print("\n✅ Programa finalizado")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
