#ifndef DIGRAPH_WRAPPER_HH
#define DIGRAPH_WRAPPER_HH

#include <vector>

namespace bliss {
class Digraph;
}

class DigraphWrapper {
private:
    bliss::Digraph *graph;
    std::vector<const unsigned int *> automorphisms;
public:
    DigraphWrapper();
    ~DigraphWrapper();
    void add_vertex(int color);
    void add_edge(int v1, int v2);
    void find_automorphisms();
    void add_automorphism(const unsigned int *automorphism);

    const std::vector<const unsigned int *> &get_automorphisms() const {
        return automorphisms;
    }
};

#endif
