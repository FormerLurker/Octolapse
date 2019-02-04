#ifndef FastPythonGcodeParser_H
#define FastPythonGcodeParser_H
#include "Python.h"
#include <string>
#include <set>

PyObject* moduleError;
std::set<std::string> text_only_functions;
std::string text_only_function_names[] = {"M117"}; // "M117" is an example of a command that would work here.
std::set<std::string> parsable_commands;
std::string parsable_command_names[] = {"G0","G1","G2","G3","G10","G11","G20","G21","G28","G29","G80","G90","G91","G92","M82","M83","M104","M105","M106","M109","M114","M116","M140","M141","M190","M191","M207","M208","M240","M400","T"};
extern "C" void initfastgcodeparser(void);
extern "C" PyObject* ParseGcode(PyObject* self, PyObject *args);
static PyObject* getParameters(std::string commandString, int startIndex);
static void getParameters(std::string, int startIndex, PyObject * parameterDict);
static PyObject* getTextOnlyParameter(std::string commandName, std::string gcodeParam);
#endif

