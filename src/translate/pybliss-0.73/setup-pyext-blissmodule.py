from distutils.core import setup, Extension

blissdir = './bliss-0.73'
blisssrcs = ['defs.cc', 'digraph_wrapper.cc', 'graph.cc', 'heap.cc',
             'orbit.cc', 'partition.cc', 'timer.cc','uintseqhash.cc',
             'utils.cc']
blisssrcs = [blissdir+'/'+src for src in blisssrcs]
cpp_args = ['-std=c++11']

ext_modules = [
    Extension(
        'pyext_blissmodule',
        ['pyext_blissmodule.cc']+blisssrcs,
        include_dirs=['pybind11/include', blissdir],
        language='c++',
        extra_compile_args = cpp_args,
    ),
]

setup(
    name='python extension Bliss module',
    author='Tommi Junttila, modified by Silvan Sievers',
    ext_modules=ext_modules,
)
