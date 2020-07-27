#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "bliss-0.73/digraph_wrapper.h"

using namespace std;
using namespace pybind11::literals;
namespace py = pybind11;

PYBIND11_MODULE(pybind11_blissmodule, module) {
    module.doc() = "pybind11 bliss module";

    py::class_<DigraphWrapper>(module, "DigraphWrapper")
        .def(py::init<>())
        .def("add_vertex", &DigraphWrapper::add_vertex, "doc",
            "color"_a)
        .def("add_edge", &DigraphWrapper::add_edge, "doc",
            "v1"_a, "v2"_a)
        .def("find_automorphisms", &DigraphWrapper::find_automorphisms,
            "doc", py::arg("time_limit") = 0);
}
