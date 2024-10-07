// Copyright (C) 2024 Stewart Miles
// Licensed to the Python Software Foundation under a contributor agreement.
// See LICENSE.txt and CONTRIBUTORS.txt.

// Use the limited API to ensure ABI compatibility across all major Python
// versions starting from 3.2
// https://docs.python.org/3/c-api/stable.html#limited-c-api
#if !defined(Py_LIMITED_API)
#define Py_LIMITED_API 3
#endif  // !defined(Py_LIMITED_API)
#define PY_SSIZE_T_CLEAN
#include <Python.h>

// Name and doc string for this module.
#define MODULE_NAME calculate
#define MODULE_DOCS "Calculates Fibonacci numbers."

// Convert the argument into a string.
#define _STRINGIFY(x) #x
#define STRINGIFY(x) _STRINGIFY(x)

// Calculate a Fibonacci number at the specified index of the sequence.
static PyObject *fib(PyObject *self, PyObject *args)
{
    long int index;
    if (!PyArg_ParseTuple(args, "l", &index)) {
        PyErr_SetString(PyExc_ValueError, "An index must be specified.");
    }

    long int current_value = 1;
    long int previous_value = 0;
    index--;
    for ( ; index > 0 ; --index) {
      long int next_value = current_value + previous_value;
      previous_value = current_value;
      current_value = next_value;
    }
    return PyLong_FromLong(current_value);
}

// Exposes methods in this module.
static PyMethodDef methods[] =
{
   {
       "fib",
       fib,
       METH_VARARGS,
       PyDoc_STR("Calculate a Fibonacci number.\n"
                 "\n"
                 ":param index: Index of the number in the Fibonacci sequence\n"
                 "  to calculate.\n"
                 "\n"
                 ":returns: Fibonacci number at the specified index.\n"
                 "  For example an index of 7 will return 13\n"),
   },
};

#if PY_MAJOR_VERSION >= 3
// Defines the module.
static struct PyModuleDef module =
{
    PyModuleDef_HEAD_INIT,
    STRINGIFY(MODULE_NAME),
    PyDoc_STR(MODULE_DOCS),
    -1,
    methods,
};
#endif  // PY_MAJOR_VERSION >= 3

// Expands to the init function name.
#define _PYINIT_FUNCTION_NAME(prefix, name) prefix ## name
#define PYINIT_FUNCTION_NAME(prefix, name) _PYINIT_FUNCTION_NAME(prefix, name)

// Initialize this module.
#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC
PYINIT_FUNCTION_NAME(PyInit_, MODULE_NAME)(void)
{
    return PyModule_Create(&module);
}
#else
PyMODINIT_FUNC
PYINIT_FUNCTION_NAME(init, MODULE_NAME)(void)
{
    // Ignore the returned module object.
    (void)Py_InitModule(STRINGIFY(MODULE_NAME), methods);
}
#endif  // PY_MAJOR_VERSION >= 3
