#pragma once
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif
#include <string>
int PyUnicode_SafeCheck(PyObject* py);
const char* PyUnicode_SafeAsString(PyObject* py);
PyObject* PyString_SafeFromString(const char* str);
PyObject* PyUnicode_SafeFromString(std::string str);
std::wstring PyObject_SafeFileNameAsWstring(PyObject* py);
double PyFloatOrInt_AsDouble(PyObject* py_double_or_int);
long PyIntOrLong_AsLong(PyObject* value);
bool PyFloatLongOrInt_Check(PyObject* value);
