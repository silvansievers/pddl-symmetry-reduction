BLISS_DIR = bliss-0.73
BLISS_HEADERS = $(BLISS_DIR)/defs.hh \
                $(BLISS_DIR)/digraph_wrapper.hh \
                $(BLISS_DIR)/graph.hh \
                $(BLISS_DIR)/heap.hh \
                $(BLISS_DIR)/orbit.hh \
                $(BLISS_DIR)/partition.hh \
                $(BLISS_DIR)/timer.hh \
                $(BLISS_DIR)/uintseqhash.hh \
                $(BLISS_DIR)/utils.hh \

BLISS_SOURCES = $(BLISS_HEADERS:%.hh=%.cc)

default: pybind11-blissmodule

all: pybind11-blissmodule pyext-blissmodule

pybind11-blissmodule:
	c++ -O3 -shared -std=c++11 -fPIC -Ipybind11-include `python-config --cflags --ldflags` $(BLISS_SOURCES) pybind11_blissmodule.cc -o pybind11_blissmodule.so

pyext-blissmodule:
	c++ -O3 -shared -std=c++11 -fPIC -Ipybind11-include `python-config --cflags --ldflags` $(BLISS_SOURCES) pyext_blissmodule.cc -o pyext_blissmodule.so

clean:
	rm -rf pybind11_blissmodule.so
	rm -rf pyext_blissmodule.so


