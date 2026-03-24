#include "python_helpers.h"
#include "logging.h"

int PyUnicode_SafeCheck(PyObject* py)
{
	return PyUnicode_Check(py);
}

const char* PyUnicode_SafeAsString(PyObject* py)
{
	return PyUnicode_AsUTF8(py);
}

PyObject* PyString_SafeFromString(const char* str)
{
    return PyUnicode_FromString(str);
}

PyObject* PyUnicode_SafeFromString(std::string str)
{
	return PyUnicode_FromString(str.c_str());
}

double PyFloatOrInt_AsDouble(PyObject* py_double_or_int)
{
  if (PyFloat_CheckExact(py_double_or_int))
    return PyFloat_AsDouble(py_double_or_int);
  else if (PyLong_CheckExact(py_double_or_int))
    return static_cast<double>(PyLong_AsLong(py_double_or_int));
  return 0;
}

long PyIntOrLong_AsLong(PyObject* value)
{
  long ret_val;
	ret_val = PyLong_AsLong(value);
  return ret_val;
}

bool PyFloatLongOrInt_Check(PyObject* py_object)
{
  return (
    PyFloat_Check(py_object) || PyLong_Check(py_object)
  );
}
