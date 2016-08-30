#include <pybind11/pybind11.h>

#include "bliss-0.73/graph.hh"

using namespace std;
using namespace pybind11::literals;
namespace py = pybind11;

PYBIND11_PLUGIN(bliss_wrapper) {
    py::module m("bliss_wrapper", "pybind11 bliss plugin");

    //py::class_<bliss::AbstractGraph>(m, "AbstractGraph")
        //.def(py::init<>())

    py::class_<bliss::Digraph>(m, "Digraph")
        .def(py::init<int>(), "N"_a=0);

    return m.ptr();
}
