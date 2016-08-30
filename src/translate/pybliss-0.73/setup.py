from distutils.core import setup, Extension

#
# The directory in which the true bliss is hiding
#
blissdir = './bliss-0.73'
# The essential bliss source files
blisssrcs = ['defs.cc', 'digraph_wrapper.cc', 'graph.cc', 'heap.cc',
             'orbit.cc', 'partition.cc', 'timer.cc','uintseqhash.cc',
             'utils.cc']
blisssrcs = [blissdir+'/'+src for src in blisssrcs]

module1 = Extension('pybliss',
                    define_macros = [('MAJOR_VERSION', '0'),
                                     ('MINOR_VERSION', '73')],
                    include_dirs = [blissdir],
                    sources = ['pyblissmodule.cc']+blisssrcs
                    )

setup (name = 'PyBliss',
       version = '0.73',
       author = 'Tommi Junttila, modified by Silvan Sievers',
       ext_modules = [module1])
