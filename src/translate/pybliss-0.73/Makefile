BLISS_DIR = bliss-0.73
BLISS_HEADERS = $(BLISS_DIR)/defs.h \
                $(BLISS_DIR)/digraph_wrapper.h \
                $(BLISS_DIR)/graph.h \
                $(BLISS_DIR)/heap.h \
                $(BLISS_DIR)/orbit.h \
                $(BLISS_DIR)/partition.h \
                $(BLISS_DIR)/timer.h \
                $(BLISS_DIR)/uintseqhash.h \
                $(BLISS_DIR)/utils.h \

BLISS_SOURCES = $(BLISS_HEADERS:%.h=%.cc)

pybind11_blissmodule.so: $(BLISS_HEADERS) $(BLISS_SOURCES) pybind11_blissmodule.cc
	c++ -O3 -Wall -shared -std=c++11 -fPIC `python3 -m pybind11 --includes`  $(BLISS_SOURCES) pybind11_blissmodule.cc -o pybind11_blissmodule.so

clean:
	rm -rf pybind11_blissmodule.so


