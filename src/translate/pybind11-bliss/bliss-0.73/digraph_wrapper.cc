#include "digraph_wrapper.hh"

#include "graph.hh"

#include <iostream>

using namespace std;

void _add_automorphism(void* param, unsigned int size, const unsigned int *automorphism) {
    DigraphWrapper *wrapper = static_cast<DigraphWrapper *>(param);
    wrapper->add_automorphism(automorphism);
}

DigraphWrapper::DigraphWrapper() {
    graph = new bliss::Digraph();
}

DigraphWrapper::~DigraphWrapper() {
    delete graph;
}

void DigraphWrapper::add_vertex(int color) {
    graph->add_vertex(color);
}

void DigraphWrapper::add_edge(int v1, int v2) {
    graph->add_edge(v1, v2);
}

void DigraphWrapper::find_automorphisms() {
    graph->set_splitting_heuristic(bliss::Digraph::shs_fs);
    bliss::Stats stats;
    cout << "Wrapper: searching for automorphisms... " << endl;
    graph->find_automorphisms(stats, &(_add_automorphism), this);
}

void DigraphWrapper::add_automorphism(const unsigned int *automorphism) {
    automorphisms.push_back(automorphism);
}
