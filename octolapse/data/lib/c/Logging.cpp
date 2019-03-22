#include <Python.h>
#include "Logging.h"
#include <string>
#include <iostream>

static bool octolapse_loggers_created = false;
static PyObject *py_logging_module = NULL;
static PyObject *py_logging_configurator_name = NULL;
static PyObject *py_logging_configurator = NULL;
static PyObject *py_octolapse_gcode_parser_logger = NULL;
static PyObject *py_octolapse_gcode_position_logger = NULL;
static PyObject *py_octolapse_snapshot_plan_logger = NULL;

void octolapse_initialize_loggers()
{
	// Create all of the objects necessary for logging
	// Import the octolapse.log module
	py_logging_module = PyImport_ImportModuleNoBlock("octolapse.log");
	if (py_logging_module == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not import module 'octolapse.log'.");
		return;
	}
	// Get the logging configurator attribute string
	py_logging_configurator_name = PyObject_GetAttrString(py_logging_module, "LoggingConfigurator");
	if (py_logging_configurator_name == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not acquire the LoggingConfigurator attribute string.");
		return;
	}

	// Create a logging configurator
	py_logging_configurator = PyObject_CallObject(py_logging_configurator_name, NULL);

	if (py_logging_configurator == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create a new instance of LoggingConfigurator.");
		return;
	}
	
	// Create the gcode_parser logging object
	py_octolapse_gcode_parser_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s", "octolapse.gcode_parser");
	if (py_octolapse_gcode_parser_logger == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.gcode_parser child logger.");
		return;
	}
	

	// Create the gcode_position logging object
	py_octolapse_gcode_position_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s", "octolapse.gcode_position");
	if (py_octolapse_gcode_position_logger == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.gcode_position child logger.");
		return;
	}
	
	// Create the stabilization logging object
	py_octolapse_snapshot_plan_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s", "octolapse.snapshot_plan");
	if (py_octolapse_snapshot_plan_logger == NULL)
	{
		PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.snapshot_plan child logger.");
		return;
	}

	octolapse_loggers_created = true;

}

void octolapse_log(int logger_type, int log_level, std::string message)
{
	if (!octolapse_loggers_created)
		return;
	const char * function_name;
	switch (log_level)
	{
		case INFO:
			function_name = "info";
			break;
		case WARNING:
			function_name = "warn";
			break;
		case ERROR:
			function_name = "error";
			break;
		case DEBUG:
			function_name = "debug";
			break;
		case VERBOSE:
			function_name = "verbose";
			break;
		default:
			return;
	}

	PyGILState_STATE state = PyGILState_Ensure();
	switch (logger_type)
	{
		case GCODE_PARSER:
			PyObject_CallMethod(py_octolapse_gcode_parser_logger, (char *)function_name, (char *)"s", message.c_str());
			break;
		case GCODE_POSITION:
			PyObject_CallMethod(py_octolapse_gcode_position_logger, (char *)function_name, (char *)"s", message.c_str());
			break;
		case SNAPSHOT_PLAN:
			PyObject_CallMethod(py_octolapse_snapshot_plan_logger, (char *)function_name, (char *)"s", message.c_str());
			break;
		default:
			return;
	}
	PyGILState_Release(state);
}