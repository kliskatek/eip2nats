#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "EIPtoNATSBridge.h"

namespace py = pybind11;

#ifndef EIP2NATS_VERSION
#define EIP2NATS_VERSION "0.0.0"
#endif

PYBIND11_MODULE(eip_nats_bridge, m) {
    m.doc() = "EIP to NATS Bridge - Bridge between EtherNet/IP and NATS";

    py::class_<bridge::EIPtoNATSBridge>(m, "EIPtoNATSBridge")
        .def(py::init<const std::string&, const std::string&, const std::string&, bool, uint8_t, uint8_t, uint8_t, uint16_t>(),
             py::arg("plc_address"),
             py::arg("nats_url"),
             py::arg("nats_subject"),
             py::arg("use_binary_format") = true,
             py::arg("config_assembly") = bridge::devices::RM75E::CONFIG_ASSEMBLY,
             py::arg("o2t_assembly") = bridge::devices::RM75E::O2T_ASSEMBLY,
             py::arg("t2o_assembly") = bridge::devices::RM75E::T2O_ASSEMBLY,
             py::arg("t2o_size") = 0,
             "Bridge constructor\n\n"
             "Args:\n"
             "    plc_address (str): PLC IP address (e.g. '192.168.17.200')\n"
             "    nats_url (str): NATS server URL (e.g. 'nats://192.168.17.138:4222')\n"
             "    nats_subject (str): NATS subject/topic (e.g. 'plc.data')\n"
             "    use_binary_format (bool): True for binary, False for JSON (default: True)\n"
             "    config_assembly (int): Configuration assembly instance (default: 4)\n"
             "    o2t_assembly (int): O2T data assembly instance (default: 2)\n"
             "    t2o_assembly (int): T2O data assembly instance (default: 1)\n"
             "    t2o_size (int): T2O connection size in bytes (default: 100)")

        .def("start", &bridge::EIPtoNATSBridge::start,
             "Start the bridge: connect to NATS, open EIP connection and start the thread\n\n"
             "Returns:\n"
             "    bool: True if started successfully, False on error")

        .def("stop", &bridge::EIPtoNATSBridge::stop,
             "Stop the bridge: close EIP connection, disconnect from NATS and stop the thread")

        .def("is_running", &bridge::EIPtoNATSBridge::isRunning,
             "Check if the bridge is running\n\n"
             "Returns:\n"
             "    bool: True if active, False if stopped")

        .def("get_published_count", &bridge::EIPtoNATSBridge::getPublishedCount,
             "Get the number of messages published to NATS\n\n"
             "Returns:\n"
             "    int: Count of sent messages")

        .def("get_received_count", &bridge::EIPtoNATSBridge::getReceivedCount,
             "Get the number of messages received from the PLC\n\n"
             "Returns:\n"
             "    int: Count of received messages")

        .def("get_reconnect_count", &bridge::EIPtoNATSBridge::getReconnectCount,
             "Get the number of automatic reconnections\n\n"
             "Returns:\n"
             "    int: Count of reconnections")

        .def("__repr__", [](const bridge::EIPtoNATSBridge &bridge) {
            return "<EIPtoNATSBridge running=" +
                   std::string(bridge.isRunning() ? "True" : "False") +
                   " received=" + std::to_string(bridge.getReceivedCount()) +
                   " published=" + std::to_string(bridge.getPublishedCount()) +
                   " reconnects=" + std::to_string(bridge.getReconnectCount()) + ">";
        });

    // Device presets (eip2nats.devices.RM75E)
    auto devices = m.def_submodule("devices", "Assembly presets for known EIP devices");

    py::class_<bridge::devices::RM75E>(devices, "RM75E",
             "Assembly presets for the RM75E device")
        .def_property_readonly_static("CONFIG_ASSEMBLY",
             [](py::object) { return bridge::devices::RM75E::CONFIG_ASSEMBLY; })
        .def_property_readonly_static("O2T_ASSEMBLY",
             [](py::object) { return bridge::devices::RM75E::O2T_ASSEMBLY; })
        .def_property_readonly_static("T2O_ASSEMBLY",
             [](py::object) { return bridge::devices::RM75E::T2O_ASSEMBLY; });

    // Module information
    m.attr("__version__") = EIP2NATS_VERSION;
    m.attr("__author__") = "Ibon Zalbide";
}
