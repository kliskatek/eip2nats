#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "EIPtoNATSBridge.h"

namespace py = pybind11;

PYBIND11_MODULE(eip_nats_bridge, m) {
    m.doc() = "EIP to NATS Bridge - Puente entre EtherNet/IP y NATS";

    py::class_<bridge::EIPtoNATSBridge>(m, "EIPtoNATSBridge")
        .def(py::init<const std::string&, const std::string&, const std::string&>(),
             py::arg("plc_address"),
             py::arg("nats_url"),
             py::arg("nats_subject"),
             "Constructor del bridge\n\n"
             "Args:\n"
             "    plc_address (str): Dirección IP del PLC (ej: '192.168.17.200')\n"
             "    nats_url (str): URL del servidor NATS (ej: 'nats://192.168.17.138:4222')\n"
             "    nats_subject (str): Subject/topic NATS (ej: 'plc.data')")
        
        .def(py::init<const std::string&, const std::string&, const std::string&, bool>(),
             py::arg("plc_address"),
             py::arg("nats_url"),
             py::arg("nats_subject"),
             py::arg("use_binary_format"),
             "Constructor del bridge con formato personalizado\n\n"
             "Args:\n"
             "    plc_address (str): Dirección IP del PLC\n"
             "    nats_url (str): URL del servidor NATS\n"
             "    nats_subject (str): Subject/topic NATS\n"
             "    use_binary_format (bool): True para binario, False para JSON")
        
        .def("start", &bridge::EIPtoNATSBridge::start,
             "Inicia el bridge: conecta a NATS, abre conexión EIP y arranca el thread\n\n"
             "Returns:\n"
             "    bool: True si se inició correctamente, False en caso de error")
        
        .def("stop", &bridge::EIPtoNATSBridge::stop,
             "Detiene el bridge: cierra conexión EIP, desconecta NATS y detiene el thread")
        
        .def("is_running", &bridge::EIPtoNATSBridge::isRunning,
             "Verifica si el bridge está corriendo\n\n"
             "Returns:\n"
             "    bool: True si está activo, False si está detenido")
        
        .def("get_published_count", &bridge::EIPtoNATSBridge::getPublishedCount,
             "Obtiene el número de mensajes publicados a NATS\n\n"
             "Returns:\n"
             "    int: Contador de mensajes enviados")
        
        .def("get_received_count", &bridge::EIPtoNATSBridge::getReceivedCount,
             "Obtiene el número de mensajes recibidos del PLC\n\n"
             "Returns:\n"
             "    int: Contador de mensajes recibidos")
        
        .def("__repr__", [](const bridge::EIPtoNATSBridge &bridge) {
            return "<EIPtoNATSBridge running=" + 
                   std::string(bridge.isRunning() ? "True" : "False") + 
                   " received=" + std::to_string(bridge.getReceivedCount()) +
                   " published=" + std::to_string(bridge.getPublishedCount()) + ">";
        });

    // Información del módulo
    m.attr("__version__") = "1.0.0";
    m.attr("__author__") = "Your Name";
}
