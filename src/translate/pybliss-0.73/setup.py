from distutils.core import setup, Extension

blissdir = './bliss-0.73'
blisssrcs = ['defs.cc', 'digraph_wrapper.cc', 'graph.cc', 'heap.cc',
             'orbit.cc', 'partition.cc', 'timer.cc','uintseqhash.cc',
             'utils.cc']
blisssrcs = [blissdir+'/'+src for src in blisssrcs]

module1 = Extension('pyext_blissmodule',
                    define_macros = [('MAJOR_VERSION', '0'),
                                     ('MINOR_VERSION', '73')],
                    include_dirs = [blissdir],
                    sources = ['pyext_blissmodule.cc']+blisssrcs
                    )

setup (name = 'python extension Bliss module',
       version = '0.73',
       author = 'Tommi Junttila, modified by Silvan Sievers',
       ext_modules = [module1])
