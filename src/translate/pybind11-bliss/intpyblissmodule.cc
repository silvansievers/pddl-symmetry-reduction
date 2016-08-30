#include <Python.h>
#include <cstdio>

#include "digraph_wrapper.hh"

static void _destroy(void *g)
{
  if(g)
    {
      //fprintf(stderr, "Free: %x\n", (unsigned int)g);
      delete (DigraphWrapper *)g;
    }
}

static PyObject *
create(PyObject *self, PyObject *args)
{
  DigraphWrapper *g = new DigraphWrapper();
  if(!g)
    Py_RETURN_NONE;

  //fprintf(stderr, "Alloc: %x\n", (unsigned int)g);
  PyObject *py_g = PyCObject_FromVoidPtr(g, &_destroy);
  if(!py_g)
    Py_RETURN_NONE;
  return py_g;
}


#if 0
static PyObject *
graph_delete(PyObject *self, PyObject *args)
{
  PyObject *py_g = NULL;

  if(!PyArg_ParseTuple(args, "O", &py_g))
    Py_RETURN_NONE;
  if(!PyCObject_Check(py_g))
    Py_RETURN_NONE;
  bliss::Digraph *g = (bliss::Digraph *)PyCObject_AsVoidPtr(py_g);
  delete g;
  Py_RETURN_NONE;
}
#endif


static PyObject *
add_vertex(PyObject *self, PyObject *args)
{
  PyObject *py_g = NULL;
  unsigned int color;

  if(!PyArg_ParseTuple(args, "OI", &py_g, &color))
    Py_RETURN_NONE;
  if(!PyCObject_Check(py_g))
    Py_RETURN_NONE;

  DigraphWrapper *g = (DigraphWrapper *)PyCObject_AsVoidPtr(py_g);
  assert(g);

  g->add_vertex(color);
  Py_RETURN_NONE;
}


static PyObject *
add_edge(PyObject *self, PyObject *args)
{
  PyObject *py_g = NULL;
  unsigned int v1;
  unsigned int v2;

  if(!PyArg_ParseTuple(args, "OII", &py_g, &v1, &v2))
    Py_RETURN_NONE;
  if(!PyCObject_Check(py_g))
    Py_RETURN_NONE;

  DigraphWrapper* g = (DigraphWrapper *)PyCObject_AsVoidPtr(py_g);
  assert(g);

  g->add_edge(v1, v2);
  Py_RETURN_NONE;
}

/*
static PyObject *
pybliss_find_automorphisms(PyObject *self, PyObject *args)
{
  PyObject *py_g = NULL;
  PyObject *py_reporter = NULL;
  PyObject *py_reporter_arg = NULL;
  DigraphWrapper *g = 0;

  if(!PyArg_ParseTuple(args, "OOO", &py_g, &py_reporter, &py_reporter_arg))
    Py_RETURN_NONE;
  if(!PyCObject_Check(py_g))
    Py_RETURN_NONE;
  if(!PyFunction_Check(py_reporter))
    {
      assert(py_reporter == Py_None);
      py_reporter = NULL;
    }

  g = (DigraphWrapper *)PyCObject_AsVoidPtr(py_g);
  assert(g);

  bliss::Stats stats;
  ReporterStruct s;
  s.py_reporter = py_reporter;
  s.py_reporter_arg = py_reporter_arg;
  g->find_automorphisms(stats, &_reporter, &s);
  Py_RETURN_NONE;
}*/

static PyMethodDef Methods[] = {
    {"create", create, METH_VARARGS, ""},
    /*{"delete",  graph_delete, METH_VARARGS, ""},*/
    {"add_vertex", add_vertex, METH_VARARGS, ""},
    {"add_edge", add_edge, METH_VARARGS, ""},
    //{"find_automorphisms",  pybliss_find_automorphisms, METH_VARARGS,
     //"Find a generating set for Aut(G)."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};


PyMODINIT_FUNC
initintpybliss(void)
{
  (void)Py_InitModule("intpybliss", Methods);
}

