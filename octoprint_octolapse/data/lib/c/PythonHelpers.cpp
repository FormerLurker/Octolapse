#include "PythonHelpers.h"
#include "Logging.h"
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

PyObject * PyString_SafeUnicodeFromString(std::string str)
{
#if PY_MAJOR_VERSION >= 3
	return PyUnicode_FromString(str.c_str());
#else
	return PyUnicode_FromString(str.c_str());
#endif
}
