# Examples - eip2nats

Usage examples for the EIP to NATS bridge.

## Files

### `example_python.py`
Complete example of using the bridge from Python.

**Features:**
- Simple configuration
- Statistics monitoring every 5 seconds
- Signal handling (Ctrl+C)
- Clean, commented code

**Run:**
```bash
source venv/bin/activate    # Linux
.\venv\Scripts\Activate     # Windows PowerShell

python examples/example_python.py
```

### `example_cpp.cpp`
C++ example for debugging the bridge without Python.

**Build and run:**
```bash
python scripts/build_example_cpp.py
build/example_cpp/example_cpp        # Linux
build\example_cpp\example_cpp.exe    # Windows
```

Or directly from VSCode with F5 ("C++ Example" configuration).

---

## Configuration

The example uses by default:
- **PLC**: `192.168.17.200`
- **NATS**: `nats://192.168.17.138:4222`
- **Subject**: `plc.eip.data`
- **Format**: Binary

### Change IPs

Edit the variables at the top of the script:

```python
plc_address = "192.168.1.100"      # Your PLC IP
nats_url = "nats://localhost:4222" # Your NATS server
nats_subject = "my.topic"          # Your subject
```

### Switch to JSON format

```python
use_binary = False  # False = JSON, True = Binary
```

---

## Create Your Own Example

```python
import eip2nats
import time

# 1. Create bridge (using device presets + application-specific t2o_size)
bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",              # PLC
    "nats://192.168.17.138:4222",  # NATS
    "plc.data",                    # Subject
    config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
    o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
    t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
    t2o_size=100,                  # Application-specific
)

# 2. Start
if bridge.start():
    # 3. Do something while running
    time.sleep(60)

    # 4. Check statistics
    print(f"Received: {bridge.get_received_count()}")
    print(f"Published: {bridge.get_published_count()}")
    print(f"Reconnections: {bridge.get_reconnect_count()}")

    # 5. Stop
    bridge.stop()
```

---

## Advanced Use Cases

### Example 1: With Flask API

```python
from flask import Flask, jsonify
import eip2nats

app = Flask(__name__)
bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",
    "nats://192.168.17.138:4222",
    "plc.data",
    config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
    o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
    t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
    t2o_size=100,
)

@app.route('/start')
def start():
    return jsonify({"success": bridge.start()})

@app.route('/stats')
def stats():
    return jsonify({
        "running": bridge.is_running(),
        "received": bridge.get_received_count(),
        "published": bridge.get_published_count()
    })

@app.route('/stop')
def stop():
    bridge.stop()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Example 2: Multiple PLCs

```python
import eip2nats
import time

# Create multiple bridges
bridges = [
    eip2nats.EIPtoNATSBridge("192.168.17.200", "nats://localhost:4222", "plc1.data",
                             config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
                             o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
                             t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
                             t2o_size=100),
    eip2nats.EIPtoNATSBridge("192.168.17.201", "nats://localhost:4222", "plc2.data",
                             config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
                             o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
                             t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
                             t2o_size=100),
    eip2nats.EIPtoNATSBridge("192.168.17.202", "nats://localhost:4222", "plc3.data",
                             config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
                             o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
                             t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
                             t2o_size=100),
]

# Start all
for i, bridge in enumerate(bridges):
    if bridge.start():
        print(f"Bridge {i+1} started")

# Monitor all
try:
    while True:
        time.sleep(5)
        for i, bridge in enumerate(bridges):
            print(f"Bridge {i+1}: RX={bridge.get_received_count()}, "
                  f"TX={bridge.get_published_count()}")
except KeyboardInterrupt:
    pass

# Stop all
for bridge in bridges:
    bridge.stop()
```

### Example 3: With Logging

```python
import eip2nats
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

bridge = eip2nats.EIPtoNATSBridge(
    "192.168.17.200",
    "nats://192.168.17.138:4222",
    "plc.data",
    config_assembly=eip2nats.devices.RM75E.CONFIG_ASSEMBLY,
    o2t_assembly=eip2nats.devices.RM75E.O2T_ASSEMBLY,
    t2o_assembly=eip2nats.devices.RM75E.T2O_ASSEMBLY,
    t2o_size=100,
)

logger.info("Starting bridge...")
if bridge.start():
    logger.info("Bridge started successfully")

    try:
        while bridge.is_running():
            time.sleep(10)
            logger.info(f"Stats - RX: {bridge.get_received_count()}, "
                       f"TX: {bridge.get_published_count()}")
    except KeyboardInterrupt:
        logger.info("Interrupt received")
    finally:
        bridge.stop()
        logger.info("Bridge stopped")
else:
    logger.error("Failed to start bridge")
```

---

## Tips

1. **Always use `try/finally`** to ensure `bridge.stop()` is called
2. **Check `bridge.is_running()`** periodically to detect disconnections
3. **Implement automatic reconnection** if the bridge goes down
4. **Use logging** in production instead of print
5. **Monitor statistics** to detect issues

---

## Troubleshooting

### Bridge won't connect to PLC

- Verify the PLC is powered on and reachable
- Try pinging the PLC IP
- Check PLC configuration (Assembly, RPI, path)

### No data received

- Check that the PLC is sending data
- Verify the Assembly configuration
- Check that the RPI is not too long

### Data not published to NATS

- Verify the NATS server is running
- Check network connectivity
- Review NATS server logs

---

For more information on development and debugging, see [`DEVELOPMENT.md`](../DEVELOPMENT.md) in the project root.
