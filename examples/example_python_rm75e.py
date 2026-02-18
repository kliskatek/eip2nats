#!/usr/bin/env python3
"""
eip2nats usage example
Run inside the virtual environment: source venv/bin/activate
"""

import eip2nats
import time
import signal
import sys

# Control variable
keep_running = True

def signal_handler(sig, frame):
    """Handler for Ctrl+C"""
    global keep_running
    print("\nStopping bridge...")
    keep_running = False

def main():
    print("=" * 60)
    print("  EIP to NATS Bridge - Example")
    print("=" * 60)
    print()

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Configuration - MODIFY THESE VARIABLES
    plc_address = "192.168.17.200"
    nats_url = "nats://192.168.17.138:4222"
    nats_subject = "plc.eip.data"

    T2O_SIZE = 100   # T→O connection size in bytes
    RPI      = 2000  # Requested Packet Interval in µs (2000 = 2 ms)
    PORT     = 2222  # Local UDP port for receiving I/O data

    print("Configuration:")
    print(f"   PLC: {plc_address}")
    print(f"   NATS: {nats_url}")
    print(f"   Subject: {nats_subject}")
    print(f"   Config Assembly: {eip2nats.devices.RM75E.CONFIG_ASSEMBLY} (0x{eip2nats.devices.RM75E.CONFIG_ASSEMBLY:02X})")
    print(f"   O2T Assembly:    {eip2nats.devices.RM75E.O2T_ASSEMBLY} (0x{eip2nats.devices.RM75E.O2T_ASSEMBLY:02X})")
    print(f"   T2O Assembly:    {eip2nats.devices.RM75E.T2O_ASSEMBLY} (0x{eip2nats.devices.RM75E.T2O_ASSEMBLY:02X})")
    print(f"   T2O Size:        {T2O_SIZE} bytes")
    print(f"   RPI:             {RPI} µs")
    print(f"   Port:            {PORT}")
    print()

    # Create bridge (using RM75E device presets)
    print("Creating bridge...")
    bridge = eip2nats.EIPtoNATSBridge(
        plc_address,
        nats_url,
        nats_subject,
        use_binary_format=True,
        config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
        o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
        t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
        t2o_size=T2O_SIZE,
        rpi=RPI,
        port=PORT,
    )

    print(f"   {bridge}")
    print()

    # Start
    print("Starting bridge...")
    if not bridge.start():
        print("ERROR: Failed to start bridge")
        return 1

    print("Bridge running")
    print("   Press Ctrl+C to stop")
    print()

    # Monitor
    last_received = 0
    last_published = 0

    while keep_running and bridge.is_running():
        time.sleep(5)

        received = bridge.get_received_count()
        published = bridge.get_published_count()

        # Calculate rate
        received_rate = (received - last_received) / 5.0
        published_rate = (published - last_published) / 5.0

        reconnects = bridge.get_reconnect_count()
        print(f"Stats: RX={received:6d} ({received_rate:5.1f}/s) | "
              f"TX={published:6d} ({published_rate:5.1f}/s) | "
              f"Reconnects={reconnects}")

        last_received = received
        last_published = published

    # Stop
    print("\nStopping bridge...")
    bridge.stop()

    # Final statistics
    print("\n" + "=" * 60)
    print("Final statistics:")
    print(f"   Messages received: {bridge.get_received_count()}")
    print(f"   Messages published: {bridge.get_published_count()}")
    print(f"   Reconnections: {bridge.get_reconnect_count()}")
    print("=" * 60)
    print("\nDone")

    return 0

if __name__ == "__main__":
    sys.exit(main())
