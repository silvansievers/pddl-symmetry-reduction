default: pyext-blissmodule

pybind11-blissmodule: pybind11_blissmodule.cc setup-pybind11-blissmodule.py
	python setup-pybind11-blissmodule.py build_ext --inplace

pyext-blissmodule: pyext_blissmodule.cc setup-pyext-blissmodule.py
	python setup-pyext-blissmodule.py build_ext --inplace

clean:
	rm -rf pybind11_blissmodule.so
	rm -rf pyext_blissmodule.so
	rm -rf build


