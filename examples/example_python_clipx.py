#!/usr/bin/env python3
"""
eip2nats - Ejemplo para HBK ClipX

Conexión implícita (I/O Class 1) con assemblies:
  - Input  (T→O): Instance 100 (0x64) - Datos de medida ClipX → Scanner
  - Output (O→T): Instance 150 (0x96) - Datos de control Scanner → ClipX
  - Config:       Instance 151 (0x97) - Configuración (tamaño 0)
"""

import eip2nats
import time
import signal
import sys

keep_running = True

def signal_handler(sig, frame):
    global keep_running
    print("\nDeteniendo bridge...")
    keep_running = False

def main():
    print("=" * 60)
    print("  EIP to NATS Bridge - HBK ClipX")
    print("=" * 60)
    print()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configuración - MODIFICAR ESTAS VARIABLES
    clipx_address = "192.168.1.100"       # IP del ClipX
    nats_url      = "nats://localhost:4222"
    nats_subject  = "clipx.eip.data"

    # Tamaño en bytes de los datos T→O (ajustar según configuración del ClipX)
    T2O_SIZE = 64

    print("Configuración:")
    print(f"  ClipX:           {clipx_address}")
    print(f"  NATS:            {nats_url}")
    print(f"  Subject:         {nats_subject}")
    print(f"  Config Assembly: {eip2nats.devices.ClipX.CONFIG_ASSEMBLY} (0x{eip2nats.devices.ClipX.CONFIG_ASSEMBLY:02X})")
    print(f"  O2T Assembly:    {eip2nats.devices.ClipX.O2T_ASSEMBLY} (0x{eip2nats.devices.ClipX.O2T_ASSEMBLY:02X})")
    print(f"  T2O Assembly:    {eip2nats.devices.ClipX.T2O_ASSEMBLY} (0x{eip2nats.devices.ClipX.T2O_ASSEMBLY:02X})")
    print(f"  T2O Size:        {T2O_SIZE} bytes")
    print()

    # Crear bridge con los assemblies del ClipX (usando device preset)
    print("Creando bridge...")
    bridge = eip2nats.EIPtoNATSBridge(
        clipx_address,
        nats_url,
        nats_subject,
        use_binary_format=True,
        config_assembly=eip2nats.devices.ClipX.CONFIG_ASSEMBLY,
        o2t_assembly=eip2nats.devices.ClipX.O2T_ASSEMBLY,
        t2o_assembly=eip2nats.devices.ClipX.T2O_ASSEMBLY,
        t2o_size=T2O_SIZE,
    )

    print(f"  {bridge}")
    print()

    # Arrancar
    print("Iniciando bridge...")
    if not bridge.start():
        print("ERROR: No se pudo iniciar el bridge")
        return 1

    print("Bridge en ejecución - Pulsa Ctrl+C para detener")
    print()

    # Monitorizar
    last_received = 0
    last_published = 0

    while keep_running and bridge.is_running():
        time.sleep(5)

        received = bridge.get_received_count()
        published = bridge.get_published_count()

        rx_rate = (received - last_received) / 5.0
        tx_rate = (published - last_published) / 5.0
        reconnects = bridge.get_reconnect_count()

        print(f"Stats: RX={received:6d} ({rx_rate:5.1f}/s) | "
              f"TX={published:6d} ({tx_rate:5.1f}/s) | "
              f"Reconnects={reconnects}")

        last_received = received
        last_published = published

    # Detener
    print("\nDeteniendo bridge...")
    bridge.stop()

    print(f"\nMensajes recibidos:  {bridge.get_received_count()}")
    print(f"Mensajes publicados: {bridge.get_published_count()}")
    print(f"Reconexiones:        {bridge.get_reconnect_count()}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
