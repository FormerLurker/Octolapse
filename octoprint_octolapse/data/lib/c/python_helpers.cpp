#include "python_helpers.h"
#include "logging.h"
int PyUnicode_SafeCheck(PyObject * py)
{
#if PY_MAJOR_VERSION >= 3
	return PyUnicode_Check(py);
#else
	return PyUnicode_Check(py);
#endif
}

const char* PyUnicode_SafeAsString(PyObject * py)
{
#if PY_MAJOR_VERSION >= 3
	return PyUnicode_AsUTF8(py);
#else
	return (char *)PyString_AsString(py);
#endif
}

PyObject * PyString_SafeFromString(const char * str)
{
#if PY_MAJOR_VERSION >= 3
	return PyUnicode_FromString(str);
#else
	return PyString_FromString(str);
#endif
}

PyObject * PyUnicode_SafeFromString(std::string str)
{
#if PY_MAJOR_VERSION >= 3
	return PyUnicode_FromString(str.c_str());
#else
	// TODO:  try PyUnicode_DecodeUnicodeEscape maybe?
	//return PyUnicode_DecodeUTF8(str.c_str(), NULL, "replace");
	PyObject * pyString = PyString_FromString(str.c_str());
	if (pyString == NULL)
	{
		PyErr_Print();
		std::string message = "Unable to convert the c_str to a python string: ";
		message += str;
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return NULL;
	}
	PyObject * pyUnicode = PyUnicode_FromEncodedObject(pyString, NULL, "replace");
	Py_DECREF(pyString);
	return pyUnicode;
#endif
}

double PyFloatOrInt_AsDouble(PyObject* py_double_or_int)
{
	if (PyFloat_CheckExact(py_double_or_int))
		return PyFloat_AsDouble(py_double_or_int);
#if PY_MAJOR_VERSION < 3
	else if (PyInt_CheckExact(py_double_or_int))
		return static_cast<double>(PyInt_AsLong(py_double_or_int));
#endif
	else if (PyLong_CheckExact(py_double_or_int))
		return static_cast<double>(PyLong_AsLong(py_double_or_int));
	return 0;
}

long PyIntOrLong_AsLong(PyObject * value)
{
	long ret_val;
#if PY_MAJOR_VERSION < 3
	if (PyInt_Check(value))
	{
		ret_val = PyInt_AsLong(value);
	}
	else
	{
		ret_val = PyLong_AsLong(value);
	}
#else
	ret_val = PyLong_AsLong(value);
#endif
	return ret_val;
}

bool PyFloatLongOrInt_Check(PyObject* py_object)
{
	return (
		PyFloat_Check(py_object) || PyLong_Check(py_object)
#if PY_MAJOR_VERSION < 3
		|| PyInt_Check(py_object)
#endif
		);

}