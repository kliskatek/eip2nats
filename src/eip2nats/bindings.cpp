#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "EIPtoNATSBridge.h"

namespace py = pybind11;

PYBIND11_MODULE(eip_nats_bridge, m) {
    m.doc() = "EIP to NATS Bridge - Bridge between EtherNet/IP and NATS";

    py::class_<bridge::EIPtoNATSBridge>(m, "EIPtoNATSBridge")
        .def(py::init<const std::string&, const std::string&, const std::string&>(),
             py::arg("plc_address"),
             py::arg("nats_url"),
             py::arg("nats_subject"),
             "Bridge constructor\n\n"
             "Args:\n"
             "    plc_address (str): PLC IP address (e.g. '192.168.17.200')\n"
             "    nats_url (str): NATS server URL (e.g. 'nats://192.168.17.138:4222')\n"
             "    nats_subject (str): NATS subject/topic (e.g. 'plc.data')")

        .def(py::init<const std::string&, const std::string&, const std::string&, bool>(),
             py::arg("plc_address"),
             py::arg("nats_url"),
             py::arg("nats_subject"),
             py::arg("use_binary_format"),
             "Bridge constructor with custom format\n\n"
             "Args:\n"
             "    plc_address (str): PLC IP address\n"
             "    nats_url (str): NATS server URL\n"
             "    nats_subject (str): NATS subject/topic\n"
             "    use_binary_format (bool): True for binary, False for JSON")

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

        .def("__repr__", [](const bridge::EIPtoNATSBridge &bridge) {
            return "<EIPtoNATSBridge running=" +
                   std::string(bridge.isRunning() ? "True" : "False") +
                   " received=" + std::to_string(bridge.getReceivedCount()) +
                   " published=" + std::to_string(bridge.getPublishedCount()) + ">";
        });

    // Module information
    m.attr("__version__") = "1.0.2";
    m.attr("__author__") = "Ibon Zalbide";
}
