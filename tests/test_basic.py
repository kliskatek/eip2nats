"""
Tests básicos para eip2nats
"""
import pytest


def test_import():
    """Verifica que el módulo se puede importar"""
    import eip2nats
    assert hasattr(eip2nats, 'EIPtoNATSBridge')


def test_version():
    """Verifica que tiene versión"""
    import eip2nats
    assert hasattr(eip2nats, '__version__')
    assert isinstance(eip2nats.__version__, str)


def test_create_bridge():
    """Verifica que se puede crear una instancia del bridge"""
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
    """Verifica creación con formato binario"""
    import eip2nats
    
    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject",
        True  # Binary format
    )
    
    assert bridge is not None


def test_bridge_with_json_format():
    """Verifica creación con formato JSON"""
    import eip2nats
    
    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject",
        False  # JSON format
    )
    
    assert bridge is not None


def test_repr():
    """Verifica que __repr__ funciona"""
    import eip2nats
    
    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.1.100",
        "nats://localhost:4222",
        "test.subject"
    )
    
    repr_str = repr(bridge)
    assert "EIPtoNATSBridge" in repr_str
    assert "running=" in repr_str


# Tests de integración (requieren PLC y NATS server reales)
@pytest.mark.skip(reason="Requiere PLC y NATS server configurados")
def test_start_stop():
    """Test de inicio y parada del bridge"""
    import eip2nats
    import time
    
    bridge = eip2nats.EIPtoNATSBridge(
        "192.168.17.200",
        "nats://192.168.17.138:4222",
        "test.plc.data"
    )
    
    # Iniciar
    assert bridge.start() is True
    assert bridge.is_running() is True
    
    # Esperar un poco
    time.sleep(2)
    
    # Detener
    bridge.stop()
    assert bridge.is_running() is False
