// Todo:  Convert to C++
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
#include "logging.h"
#include <string>
#include <iostream>
#include <climits>
#include "python_helpers.h"

static bool octolapse_loggers_created = false;
static PyObject *py_logging_module = NULL;
static PyObject *py_logging_configurator_name = NULL;
static PyObject *py_logging_configurator = NULL;
static PyObject *py_octolapse_gcode_parser_logger = NULL;
static PyObject *py_octolapse_gcode_position_logger = NULL;
static PyObject *py_octolapse_snapshot_plan_logger = NULL;
static PyObject *py_info_function_name = NULL;
static PyObject *py_warn_function_name = NULL;
static PyObject *py_error_function_name = NULL;
static PyObject *py_debug_function_name = NULL;
static PyObject *py_verbose_function_name = NULL;

void octolapse_initialize_loggers()
{
	// Create all of the objects necessary for logging
	// Import the octolapse.log module
	py_logging_module = PyImport_ImportModuleNoBlock("octoprint_octolapse.log");
	if (py_logging_module == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not import module 'octolapse.log'.");
		return;
	}
	//Py_INCREF(py_logging_module);
	// Get the logging configurator attribute string
	py_logging_configurator_name = PyObject_GetAttrString(py_logging_module, "LoggingConfigurator");
	if (py_logging_configurator_name == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not acquire the LoggingConfigurator attribute string.");
		return;
	}
	
	// Create a logging configurator
	PyGILState_STATE gstate = PyGILState_Ensure();
	py_logging_configurator = PyObject_CallObject(py_logging_configurator_name, NULL);
	PyGILState_Release(gstate);

	if (py_logging_configurator == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create a new instance of LoggingConfigurator.");
		return;
	}
	//Py_INCREF(py_logging_configurator);
	// Create the gcode_parser logging object
	py_octolapse_gcode_parser_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s", "octoprint_octolapse.gcode_parser");
	if (py_octolapse_gcode_parser_logger == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.gcode_parser child logger.");
		return;
	}
	//Py_INCREF(py_octolapse_gcode_parser_logger);

	// Create the gcode_position logging object
	py_octolapse_gcode_position_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s", "octoprint_octolapse.gcode_position");
	if (py_octolapse_gcode_position_logger == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.gcode_position child logger.");
		return;
	}
	//Py_INCREF(py_octolapse_gcode_position_logger);
	// Create the stabilization logging object
	py_octolapse_snapshot_plan_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s", "octoprint_octolapse.snapshot_plan");
	if (py_octolapse_snapshot_plan_logger == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.snapshot_plan child logger.");
		return;
	}
	//Py_INCREF(py_octolapse_snapshot_plan_logger);

	// create the function name py objects
	py_info_function_name = PyString_SafeFromString("info");
	py_warn_function_name = PyString_SafeFromString("warn");
	py_error_function_name = PyString_SafeFromString("error");
	py_debug_function_name = PyString_SafeFromString("debug");
	py_verbose_function_name = PyString_SafeFromString("verbose");

	octolapse_loggers_created = true;

}

void octolapse_log(int logger_type, int log_level, std::string message)
{

	if (!octolapse_loggers_created)
		return;
	PyObject * pyFunctionName;
	switch (log_level)
	{
		case INFO:
			pyFunctionName = py_info_function_name;
			break;
		case WARNING:
			pyFunctionName = py_warn_function_name;
			break;
		case ERROR:
			pyFunctionName = py_error_function_name;
			break;
		case DEBUG:
			pyFunctionName = py_debug_function_name;
			break;
		case VERBOSE:
			pyFunctionName = py_verbose_function_name;
			break;
		default:
			return;
	}
	PyObject * pyMessage = PyUnicode_SafeFromString(message.c_str());
	if (pyMessage == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "");
		PyErr_Format(PyExc_ValueError,
			"Unable to convert the log message '%s' to a PyString/Unicode message.", message.c_str());
		// Todo:  What should I do if this fails??
		return;
	}
	PyGILState_STATE state = PyGILState_Ensure();
	PyObject * ret_val;
	switch (logger_type)
	{
		case GCODE_PARSER:
			ret_val = PyObject_CallMethodObjArgs(py_octolapse_gcode_parser_logger, pyFunctionName, pyMessage, NULL);
			break;
		case GCODE_POSITION:
			ret_val = PyObject_CallMethodObjArgs(py_octolapse_gcode_position_logger, pyFunctionName, pyMessage, NULL);
			break;
		case SNAPSHOT_PLAN:
			ret_val = PyObject_CallMethodObjArgs(py_octolapse_snapshot_plan_logger, pyFunctionName, pyMessage, NULL);
			break;
		default:
			ret_val = NULL;
			break;
	}
	// We need to decref our message so that the GC can remove it.  Maybe?
	Py_DECREF(pyMessage);
	PyGILState_Release(state);
	if (ret_val == NULL)
	{
		if (!PyErr_Occurred())
			PyErr_SetString(PyExc_ValueError, "Logging.octolapse_log - unknown logger_type.");
		else
		{
			// I'm not sure what else to do here since I can't log the error.  I will print it 
			// so that it shows up in the console, but I can't log it, and there is no way to 
			// return an error.
			PyErr_Print();
			PyErr_Clear();
		}
	}
	Py_XDECREF(ret_val);
}