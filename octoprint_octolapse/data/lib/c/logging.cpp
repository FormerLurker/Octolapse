// Todo:  Convert to C++
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif
#include "logging.h"
#include <string>
#include "python_helpers.h"

static bool octolapse_loggers_created = false;
static bool check_log_levels_real_time = true;
static PyObject* py_logging_module = NULL;
static PyObject* py_logging_configurator_name = NULL;
static PyObject* py_logging_configurator = NULL;
static PyObject* py_octolapse_gcode_parser_logger = NULL;
static long gcode_parser_log_level = 0;
static PyObject* py_octolapse_gcode_position_logger = NULL;
static long gcode_position_log_level = 0;
static PyObject* py_octolapse_snapshot_plan_logger = NULL;
static long snapshot_plan_log_level = 0;
static PyObject* py_info_function_name = NULL;
static PyObject* py_warn_function_name = NULL;
static PyObject* py_error_function_name = NULL;
static PyObject* py_debug_function_name = NULL;
static PyObject* py_verbose_function_name = NULL;
static PyObject* py_critical_function_name = NULL;
static PyObject* py_get_effective_level_function_name = NULL;

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

  // Create the gcode_parser logging object
  py_octolapse_gcode_parser_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s",
                                                         "octoprint_octolapse.gcode_parser");
  if (py_octolapse_gcode_parser_logger == NULL)
  {
    PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.gcode_parser child logger.");
    return;
  }

  // Create the gcode_position logging object
  py_octolapse_gcode_position_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s",
                                                           "octoprint_octolapse.gcode_position");
  if (py_octolapse_gcode_position_logger == NULL)
  {
    PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.gcode_position child logger.");
    return;
  }

  // Create the stabilization logging object
  py_octolapse_snapshot_plan_logger = PyObject_CallMethod(py_logging_configurator, (char*)"get_logger", (char *)"s",
                                                          "octoprint_octolapse.snapshot_plan");
  if (py_octolapse_snapshot_plan_logger == NULL)
  {
    PyErr_SetString(PyExc_ImportError, "Could not create the octolapse.snapshot_plan child logger.");
    return;
  }

  // create the function name py objects
  py_info_function_name = PyString_SafeFromString("info");
  py_warn_function_name = PyString_SafeFromString("warn");
  py_error_function_name = PyString_SafeFromString("error");
  py_debug_function_name = PyString_SafeFromString("debug");
  py_verbose_function_name = PyString_SafeFromString("verbose");
  py_critical_function_name = PyString_SafeFromString("critical");
  py_get_effective_level_function_name = PyString_SafeFromString("getEffectiveLevel");
  octolapse_loggers_created = true;
}

void set_internal_log_levels(bool check_real_time)
{
  check_log_levels_real_time = check_real_time;
  if (!check_log_levels_real_time)
  {
    PyObject* py_gcode_parser_log_level = PyObject_CallMethodObjArgs(py_octolapse_gcode_parser_logger,
                                                                     py_get_effective_level_function_name, NULL);
    if (py_gcode_parser_log_level == NULL)
    {
      PyErr_Print();
      PyErr_SetString(PyExc_ValueError,
                      "Logging.octolapse_log - Could not retrieve the log level for the gcode parser logger.");
    }
    gcode_parser_log_level = PyIntOrLong_AsLong(py_gcode_parser_log_level);

    PyObject* py_gcode_position_log_level = PyObject_CallMethodObjArgs(py_octolapse_gcode_position_logger,
                                                                       py_get_effective_level_function_name, NULL);
    if (py_gcode_position_log_level == NULL)
    {
      PyErr_Print();
      PyErr_SetString(PyExc_ValueError,
                      "Logging.octolapse_log - Could not retrieve the log level for the gcode position logger.");
    }
    gcode_position_log_level = PyIntOrLong_AsLong(py_gcode_position_log_level);

    PyObject* py_snapshot_plan_log_level = PyObject_CallMethodObjArgs(py_octolapse_snapshot_plan_logger,
                                                                      py_get_effective_level_function_name, NULL);
    if (py_snapshot_plan_log_level == NULL)
    {
      PyErr_Print();
      PyErr_SetString(PyExc_ValueError,
                      "Logging.octolapse_log - Could not retrieve the log level for the snapshot plan logger.");
    }
    snapshot_plan_log_level = PyIntOrLong_AsLong(py_snapshot_plan_log_level);

    Py_XDECREF(py_gcode_parser_log_level);
    Py_XDECREF(py_gcode_position_log_level);
    Py_XDECREF(py_snapshot_plan_log_level);
  }
}

bool octolapse_may_be_logged(const int logger_type, const int log_level)
{
  int current_log_level;
  switch (logger_type)
  {
  case octolapse_log::GCODE_PARSER:
    current_log_level = gcode_parser_log_level;
    break;
  case octolapse_log::GCODE_POSITION:
    current_log_level = gcode_position_log_level;
    break;
  case octolapse_log::SNAPSHOT_PLAN:
    current_log_level = snapshot_plan_log_level;
    break;
  default:
    return false;
  }

  if (!check_log_levels_real_time)
  {
    //std::cout << "Current Log Level: " << current_log_level << " requested:" << log_level;
    // For speed we are going to check the log levels here before attempting to send any logging info to Python.
    if (current_log_level > log_level)
    {
      return false;
    }
  }
  return true;
}

void octolapse_log_exception(const int logger_type, const std::string& message)
{
  octolapse_log(logger_type, octolapse_log::ERROR, message, true);
}

void octolapse_log(const int logger_type, const int log_level, const std::string& message)
{
  octolapse_log(logger_type, log_level, message, false);
}

void octolapse_log(const int logger_type, const int log_level, const std::string& message, bool is_exception)
{
  if (!octolapse_loggers_created)
    return;

  // Get the appropriate logger
  PyObject* py_logger;
  long current_log_level = 0;
  switch (logger_type)
  {
  case octolapse_log::GCODE_PARSER:
    py_logger = py_octolapse_gcode_parser_logger;
    current_log_level = gcode_parser_log_level;
    break;
  case octolapse_log::GCODE_POSITION:
    py_logger = py_octolapse_gcode_position_logger;
    current_log_level = gcode_position_log_level;
    break;
  case octolapse_log::SNAPSHOT_PLAN:
    py_logger = py_octolapse_snapshot_plan_logger;
    current_log_level = snapshot_plan_log_level;
    break;
  default:
    PyErr_SetString(PyExc_ValueError, "Logging.octolapse_log - unknown logger_type.");
    return;
  }

  if (!check_log_levels_real_time)
  {
    //std::cout << "Current Log Level: " << current_log_level << " requested:" << log_level;
    // For speed we are going to check the log levels here before attempting to send any logging info to Python.
    if (current_log_level > log_level)
    {
      return;
    }
  }

  PyObject* pyFunctionName = NULL;

  PyObject* error_type = NULL;
  PyObject* error_value = NULL;
  PyObject* error_traceback = NULL;
  bool error_occurred = false;
  if (is_exception)
  {
    // if an error has occurred, use the exception function to log the entire error
    pyFunctionName = py_error_function_name;
    if (PyErr_Occurred())
    {
      error_occurred = true;
      PyErr_Fetch(&error_type, &error_value, &error_traceback);
      PyErr_NormalizeException(&error_type, &error_value, &error_traceback);
    }
  }
  else
  {
    switch (log_level)
    {
    case octolapse_log::INFO:
      pyFunctionName = py_info_function_name;
      break;
    case octolapse_log::WARNING:
      pyFunctionName = py_warn_function_name;
      break;
    case octolapse_log::ERROR:
      pyFunctionName = py_error_function_name;
      break;
    case octolapse_log::DEBUG:
      pyFunctionName = py_debug_function_name;
      break;
    case octolapse_log::VERBOSE:
      pyFunctionName = py_verbose_function_name;
      break;
    case octolapse_log::CRITICAL:
      pyFunctionName = py_critical_function_name;
      break;
    default:
      return;
    }
  }
  PyObject* pyMessage = PyUnicode_SafeFromString(message);
  if (pyMessage == NULL)
  {
    PyErr_Format(PyExc_ValueError,
                 "Unable to convert the log message '%s' to a PyString/Unicode message.", message.c_str());
    return;
  }
  PyGILState_STATE state = PyGILState_Ensure();
  PyObject* ret_val = PyObject_CallMethodObjArgs(py_logger, pyFunctionName, pyMessage, NULL);
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
  else
  {
    // Set the exception if we are doing exception logging.
    if (is_exception)
    {
      if (error_occurred)
        PyErr_Restore(error_type, error_value, error_traceback);
      else
        PyErr_SetString(PyExc_Exception, message.c_str());
    }
  }
  Py_XDECREF(ret_val);
}
