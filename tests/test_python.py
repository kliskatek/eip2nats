"""
Basic tests for eip2nats
"""
import pytest


def test_import():
    """Verify that the module can be imported"""
    import eip2nats
    assert hasattr(eip2nats, 'EIPtoNATSBridge')


def test_version():
    """Verify that it has a version"""
    import eip2nats
    assert hasattr(eip2nats, '__version__')
    assert isinstance(eip2nats.__version__, str)


def test_create_bridge():
    """Verify that a bridge instance can be created"""
    import eip2nats

    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject"
    )

    assert bridge is not None
    assert not bridge.is_running()
    assert bridge.get_received_count() == 0
    assert bridge.get_published_count() == 0


def test_bridge_with_binary_format():
    """Verify creation with binary format"""
    import eip2nats

    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject",
        True  # Binary format
    )

    assert bridge is not None


def test_bridge_with_json_format():
    """Verify creation with JSON format"""
    import eip2nats

    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject",
        False  # JSON format
    )

    assert bridge is not None


def test_repr():
    """Verify that __repr__ works"""
    import eip2nats

    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject"
    )

    repr_str = repr(bridge)
    assert "EIPtoNATSBridge" in repr_str
    assert "running=" in repr_str


# Integration tests (require real PLC and NATS server)
@pytest.mark.skip(reason="Requires configured PLC and NATS server")
def test_start_stop():
    """Test bridge start and stop"""
    import eip2nats
    import time

    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.17.200",
        "nats://192.168.17.138:4222",
        "test.plc.data"
    )

    # Start
    assert bridge.start() is True
    assert bridge.is_running() is True

    # Wait a bit
    time.sleep(2)

    # Stop
    bridge.stop()
    assert bridge.is_running() is False
