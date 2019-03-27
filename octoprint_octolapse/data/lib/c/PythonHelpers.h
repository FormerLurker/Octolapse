#pragma once
#include "Python.h"
#include <string>
int PyUnicode_SafeCheck(PyObject * py);
const char* PyUnicode_SafeAsString(PyObject * py);
PyObject * PyString_SafeFromString(const char * str);
PyObject * PyString_SafeUnicodeFromString(std::string str);