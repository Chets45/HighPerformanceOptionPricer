#include <pybind11/pybind11.h>
#include "Option.h" // Your main Option class header

namespace py = pybind11;


PYBIND11_MODULE(option_pricer_cpp, m) {
    m.doc() = "High-performance C++ option pricer";

    py::enum_<OptionType>(m, "OptionType")
        .value("Call", OptionType::Call)
        .value("Put", OptionType::Put)
        .export_values();

    py::class_<Option>(m, "Option")
        .def(py::init<double, double, double, double, double, OptionType>())
        .def("price", &Option::price)
        .def("delta", &Option::delta)
        .def("gamma", &Option::gamma)
        .def("vega", &Option::vega)
        .def("theta", &Option::theta)
        .def("rho", &Option::rho)
        .def("implied_volatility", &Option::impliedVolatility);
}