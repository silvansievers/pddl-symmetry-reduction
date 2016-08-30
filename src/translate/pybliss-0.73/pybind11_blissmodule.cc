#include <pybind11/pybind11.h>

#include "bliss-0.73/digraph_wrapper.hh"

using namespace std;
using namespace pybind11::literals;
namespace py = pybind11;

PYBIND11_PLUGIN(bliss_wrapper) {
    py::module m("bliss_wrapper", "pybind11 bliss plugin");

    py::class_<DigraphWrapper>(m, "DigraphWrapper")
        .def(py::init<>())
        .def("add_vertex", &DigraphWrapper::add_vertex, "doc",
            "color"_a)
        .def("add_edge", &DigraphWrapper::add_edge, "doc",
            "v1"_a, "v2"_a)
        .def("find_automorphisms", &DigraphWrapper::find_automorphisms)
        .def("add_automorphism", &DigraphWrapper::add_automorphism)
        .def("get_automorphisms", &DigraphWrapper::get_automorphisms);

    return m.ptr();
}
