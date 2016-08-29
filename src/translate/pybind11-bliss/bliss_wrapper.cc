#include <pybind11/pybind11.h>

//#include "bliss-0.73/graph.hh"

using namespace std;
using namespace pybind11::literals;
namespace py = pybind11;

class BlissWrapper {
private:
    //bliss::Digraph *graph;
public:
    BlissWrapper() {
        //graph = new bliss::Digraph();
        //cout << "init function" << endl;
        //bliss::Digraph graph;
        //graph.add_vertex(1);
        //graph.add_vertex(2);
        //graph.add_vertex(3);
    }
    //~BlissWrapper() {
        //delete graph;
    //}
    void add_vertex(int color) {
        cout << color << endl;
        //graph->add_vertex(color);
    }
    void add_edge(int v1, int v2) {
        //graph->add_edge(v1, v2);
    }
};

PYBIND11_PLUGIN(bliss_wrapper) {
    py::module m("bliss_wrapper", "pybind11 bliss plugin");

    py::class_<BlissWrapper>(m, "BlissWrapper")
        .def(py::init<>())
        .def("add_vertex", &BlissWrapper::add_vertex, "doc",
            "color"_a)
        .def("add_edge", &BlissWrapper::add_edge, "doc",
            "v1"_a, "v2"_a);

    return m.ptr();
}
