BLISS_DIR = bliss-0.73
BLISS_HEADERS = $(BLISS_DIR)/defs.hh \
                $(BLISS_DIR)/digraph_wrapper.hh \
                $(BLISS_DIR)/heap.hh \
                $(BLISS_DIR)/orbit.hh \
                $(BLISS_DIR)/partition.hh \
                $(BLISS_DIR)/timer.hh \
                $(BLISS_DIR)/uintseqhash.hh \
                $(BLISS_DIR)/utils.hh \

BLISS_SOURCES = $(BLISS_HEADERS:%.hh=%.cc)


WRAPPER_SOURCES = bliss_wrapper.cc $(BLISS_HEADERS:%.hh=%.cc)

bliss-wrapper:
	c++ -O3 -shared -std=c++11 -fPIC -Ipybind11-include `python-config --cflags --ldflags` $(WRAPPER_SOURCES) -o bliss_wrapper.so

intpyblissmodule: intpyblissmodule.cc setup.py
	python setup.py install --home=.

clean:
	rm -rf bliss_wrapper.so graph_module.so
	rm -f PyBliss.pyc setup.pyc
	rm -rf build
	rm -rf lib

default: intpyblissmodule bliss-wraper clean
