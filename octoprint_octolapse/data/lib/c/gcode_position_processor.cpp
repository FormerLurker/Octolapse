////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
// Copyright(C) 2019  Brad Hochgesang
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// This program is free software : you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.If not, see the following :
// https ://github.com/FormerLurker/Octolapse/blob/master/LICENSE
//
// You can contact the author either through the git - hub repository, or at the
// following email address : FormerLurker@pm.me
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

#include "gcode_position_processor.h"
#include <iomanip>
#include <sstream>
#include <iostream>
#include "utilities.h"
#include "stabilization_smart_layer.h"
#include "stabilization.h"
#include "logging.h"
#include "python_helpers.h"

#ifdef _DEBUG
#include "test.h"
#endif
// Sometimes used to test performance in release mode.
//#include "test.h"

int main(int argc, wchar_t* argv[])
{
	wchar_t* program = argv[0];
	if (program == NULL) {
		fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
		exit(1);
	}

	// Add a built-in module, before Py_Initialize
	PyImport_AppendInittab("GcodePositionProcessor", PyInit_GcodePositionProcessor);

#if PY_VERSION_HEX < 0x03080000
	Py_SetProgramName(program);
	// Initialize the Python interpreter.  Required.
	Py_Initialize();
#else
	{
		PyStatus status;

		PyConfig config;
		PyConfig_InitPythonConfig(&config);

		if (argc && argv) {
			status = PyConfig_SetString(&config, &config.program_name, program);
			if (PyStatus_Exception(status)) {
				PyConfig_Clear(&config);
				return 1;
			}

			status = PyConfig_SetArgv(&config, argc, argv);
			if (PyStatus_Exception(status)) {
				PyConfig_Clear(&config);
				return 1;
			}
		}

		status = Py_InitializeFromConfig(&config);
		if (PyStatus_Exception(status)) {
			PyConfig_Clear(&config);
			return 1;
		}

		PyConfig_Clear(&config);
	}
#endif





#if PY_VERSION_HEX < 0x03090000
	std::cout << "Initializing threads...";
	Py_SetProgramName(program);
#endif
	// Optionally import the module; alternatively, import can be deferred until the embedded script imports it.
	PyImport_ImportModule("GcodePositionProcessor");
	PyMem_RawFree(program);
	return 0;
}

struct module_state
{
	PyObject* error;
};
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))

// Python 2 module method definition
static PyMethodDef GcodePositionProcessorMethods[] = {
  {"Initialize", (PyCFunction)Initialize, METH_VARARGS, "Initialize the internal shared position processor."},
  {"Undo", (PyCFunction)Undo, METH_VARARGS, "Undo an update made to the current position.  You can only undo once."},
  {
	"Update", (PyCFunction)Update, METH_VARARGS, "Undo an update made to the current position.  You can only undo once."
  },
  {"UpdatePosition", (PyCFunction)UpdatePosition, METH_VARARGS, "Update x,y,z,e and f for the given position key."},
  {"Parse", (PyCFunction)Parse, METH_VARARGS, "Parse gcode text into a ParsedCommand."},
  {
	"GetCurrentPositionTuple", (PyCFunction)GetCurrentPositionTuple, METH_VARARGS,
	"Returns the current position of the global GcodePosition tracker in a faster but harder to handle tuple form."
  },
  {
	"GetCurrentPositionDict", (PyCFunction)GetCurrentPositionDict, METH_VARARGS,
	"Returns the current position of the global GcodePosition tracker in a slower but easier to deal with dict form."
  },
  {
	"GetPreviousPositionTuple", (PyCFunction)GetPreviousPositionTuple, METH_VARARGS,
	"Returns the previous position of the global GcodePosition tracker in a faster but harder to handle tuple form."
  },
  {
	"GetPreviousPositionDict", (PyCFunction)GetPreviousPositionDict, METH_VARARGS,
	"Returns the previous position of the global GcodePosition tracker in a slower but easier to deal with dict form."
  },
  {
	"GetSnapshotPlans_SmartLayer", (PyCFunction)GetSnapshotPlans_SmartLayer, METH_VARARGS,
	"Parses a gcode file and returns snapshot plans for a 'SmartLayer' stabilization."
  },
  {
	"GetSnapshotPlans_SmartGcode", (PyCFunction)GetSnapshotPlans_SmartGcode, METH_VARARGS,
	"Parses a gcode file and returns snapshot plans for a 'SmartGcode' stabilization."
  },
  {NULL, NULL, 0, NULL}
};

// Python 3 module method definition
static int GcodePositionProcessor_traverse(PyObject* m, visitproc visit, void* arg) {
	Py_VISIT(GETSTATE(m)->error);
	return 0;
}

static int GcodePositionProcessor_clear(PyObject* m) {
	Py_CLEAR(GETSTATE(m)->error);
	return 0;
}

static struct PyModuleDef moduledef = {
	PyModuleDef_HEAD_INIT,
	"GcodePositionProcessor",
	NULL,
	sizeof(struct module_state),
	GcodePositionProcessorMethods,
	NULL,
	GcodePositionProcessor_traverse,
	GcodePositionProcessor_clear,
	NULL
};

#define INITERROR return NULL

PyMODINIT_FUNC
PyInit_GcodePositionProcessor(void)
{
	std::cout << "Initializing GcodePositionProcessor V1.0.1 - Copyright (C) 2019  Brad Hochgesang...";

	std::cout << "Python 3+ Detected...";
	PyObject* module = PyModule_Create(&moduledef);


	if (module == NULL)
		INITERROR;
	struct module_state* st = GETSTATE(module);

	st->error = PyErr_NewException((char*)"GcodePositionProcessor.Error", NULL, NULL);
	if (st->error == NULL)
	{
		Py_DECREF(module);
		INITERROR;
	}
	octolapse_initialize_loggers();
	gpp::parser = new gcode_parser();

	std::cout << "complete\r\n";
	return module;
}

extern "C" {

	static PyObject* GetSnapshotPlans_SmartLayer(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Running smart layer stabilization preprocessing.");
		// TODO:  add error reporting and logging
		PyObject* py_position_args;
		PyObject* py_stabilization_args;
		PyObject* py_stabilization_type_args;
		//std::cout << "Parsing Arguments\r\n";
		if (!PyArg_ParseTuple(
			args,
			"OOO",
			&py_position_args,
			&py_stabilization_args,
			&py_stabilization_type_args))
		{
			std::string message = "GcodePositionProcessor.GetSnapshotPlans_SmartLayer - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
			return NULL;
		}
		// Removed by BH on 4-28-2019
		// Extract the position args
		gcode_position_args p_args;
		//std::cout << "Parsing position arguments\r\n";
		if (!ParsePositionArgs(py_position_args, &p_args))
		{
			return NULL;
		}

		// Extract the stabilization args
		stabilization_args s_args;
		//std::cout << "Parsing stabilization arguments\r\n";
		PyObject* py_progress_received_callback = NULL;
		PyObject* py_snapshot_position_callback = NULL;
		if (!ParseStabilizationArgs(py_stabilization_args, &s_args, &py_progress_received_callback,
			&py_snapshot_position_callback))
		{
			return NULL;
		}
		//std::cout << "Parsing smart layer arguments\r\n";
		smart_layer_args mt_args;
		if (!ParseStabilizationArgs_SmartLayer(py_stabilization_type_args, &mt_args))
		{
			return NULL;
		}
		//std::cout << "Creating Stabilization.\r\n";
		// Create our stabilization object
		set_internal_log_levels(false);
		stabilization_smart_layer stabilization(
			p_args,
			s_args,
			mt_args,
			pythonGetCoordinatesCallback(ExecuteGetSnapshotPositionCallback),
			py_snapshot_position_callback,
			pythonProgressCallback(ExecuteStabilizationProgressCallback),
			py_progress_received_callback
		);
		stabilization_results results = stabilization.process_file();
		set_internal_log_levels(true);


		PyObject* py_results = results.to_py_object();
		if (py_results == NULL)
		{
			return NULL;
		}
		//Py_DECREF(py_position_args);
		//Py_DECREF(py_stabilization_args);
		//Py_DECREF(py_stabilization_type_args);
		//std::cout << "py_progress_callback refcount = " << py_progress_callback->ob_refcnt << "\r\n";
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Snapshot plan creation complete, returning plans.");
		//std::cout << "py_results refcount = " << py_results->ob_refcnt << "\r\n";
		return py_results;
	}

	static PyObject* GetSnapshotPlans_SmartGcode(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Running smart gcode stabilization preprocessing.");
		// TODO:  add error reporting and logging
		PyObject* py_position_args;
		PyObject* py_stabilization_args;
		PyObject* py_stabilization_type_args;
		//std::cout << "Parsing Arguments\r\n";
		if (!PyArg_ParseTuple(
			args,
			"OOO",
			&py_position_args,
			&py_stabilization_args,
			&py_stabilization_type_args))
		{
			std::string message = "GcodePositionProcessor.GetSnapshotPlans_SmartGcode - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
			return NULL;
		}
		// Removed by BH on 4-28-2019
		// Extract the position args
		gcode_position_args p_args;
		//std::cout << "Parsing position arguments\r\n";
		if (!ParsePositionArgs(py_position_args, &p_args))
		{
			return NULL;
		}

		// Extract the stabilization args
		stabilization_args s_args;
		//std::cout << "Parsing stabilization arguments\r\n";
		PyObject* py_progress_received_callback = NULL;
		PyObject* py_snapshot_position_callback = NULL;
		if (!ParseStabilizationArgs(py_stabilization_args, &s_args, &py_progress_received_callback,
			&py_snapshot_position_callback))
		{
			return NULL;
		}
		//std::cout << "Parsing smart layer arguments\r\n";
		smart_gcode_args mt_args;
		if (!ParseStabilizationArgs_SmartGcode(py_stabilization_type_args, &mt_args))
		{
			return NULL;
		}
		//std::cout << "Creating Stabilization.\r\n";
		// Create our stabilization object
		set_internal_log_levels(false);
		stabilization_smart_gcode stabilization(
			p_args,
			s_args,
			mt_args,
			pythonGetCoordinatesCallback(ExecuteGetSnapshotPositionCallback),
			py_snapshot_position_callback,
			pythonProgressCallback(ExecuteStabilizationProgressCallback),
			py_progress_received_callback
		);
		stabilization_results results = stabilization.process_file();
		set_internal_log_levels(true);


		PyObject* py_results = results.to_py_object();
		if (py_results == NULL)
		{
			return NULL;
		}
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Snapshot plan creation complete, returning plans.");
		return py_results;
	}

	static PyObject* Initialize(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		// Create the gcode position object 
		octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::INFO, "Initializing gcode position processor.");
		const char* pKey;
		PyObject* py_position_args;
		if (!PyArg_ParseTuple(
			args, "sO",
			&pKey,
			&py_position_args
		))
		{
			std::string message = "GcodePositionProcessor.Initialize - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}

		gcode_position_args positionArgs;

		// Create the gcode position object 
		octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::INFO, "Parsing initialization position args.");

		if (!ParsePositionArgs(py_position_args, &positionArgs))
		{
			return NULL; // The call failed, ParseInitializationArgs has taken care of the error message
		}

		// see if we already have a gcode_position object for the given key
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(pKey);
		gcode_position* p_gcode_position = NULL;
		if (gcode_position_iterator != gpp::gcode_positions.end())
		{
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::INFO, "Existing processor found, deleting.");
			delete gcode_position_iterator->second;
		}
		// Separate delete step.  Something is going on here.
		if (gcode_position_iterator != gpp::gcode_positions.end())
		{
			gpp::gcode_positions.erase(gcode_position_iterator);
		}

		std::string message = "Adding processor with key:";
		message.append(pKey).append("\r\n");

		octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::INFO, message);
		// Create the new position object
		gcode_position* p_new_position = new gcode_position(positionArgs);
		// add the new gcode position to our list of objects
		gpp::gcode_positions.insert(std::pair<std::string, gcode_position*>(pKey, p_new_position));
		// Return True
		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Undo(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::DEBUG,
			"Undoing the last gcode position update."
		);
		const char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GcodePositionProcessor.Undo - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}
		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		p_gcode_position->undo_update();

		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Update(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::VERBOSE,
			"Updating current position from gcode."
		);
		const char* key;
		const char* gcode;
		if (!PyArg_ParseTuple(args, "ss", &key, &gcode))
		{
			std::string message = "GcodePositionProcessor.Update - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}

		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			std::string message = "GcodePositionProcessor.Update - No position processor was found for the given key: ";
			message += key;
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, message);
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		parsed_command command;
		gpp::parser->try_parse_gcode(gcode, command);
		p_gcode_position->update(command, -1, -1, -1);

		return p_gcode_position->get_current_position_ptr()->to_py_tuple();
	}

	static PyObject* UpdatePosition(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::VERBOSE,
			"Manually updating current position."
		);
		char* key;
		double x;
		long update_x;
		double y;
		long update_y;
		double z;
		long update_z;
		double e;
		long update_e;
		double f;
		long update_f;

		if (!PyArg_ParseTuple(
			args, "sdldldldldl",
			&key,
			&x,
			&update_x,
			&y,
			&update_y,
			&z,
			&update_z,
			&e,
			&update_e,
			&f,
			&update_f
		))
		{
			std::string message = "GcodePositionProcessor.UpdatePosition - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}
		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			std::string message = "GcodePositionProcessor.UpdatePosition - No position processor was found for the given key: ";
			message += key;
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, message);
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;
		position* pos = p_gcode_position->get_current_position_ptr();
		p_gcode_position->update_position(
			pos,
			x,
			update_x > 0,
			y,
			update_y > 0,
			z,
			update_z > 0,
			e,
			update_e > 0,
			f,
			update_f > 0,
			true,
			false);

		return p_gcode_position->get_current_position_ptr()->to_py_tuple();
	}

	static PyObject* Parse(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_PARSER, octolapse_log::VERBOSE,
			"Parsing gcode."
		);
		const char* gcode;
		if (!PyArg_ParseTuple(args, "s", &gcode))
		{
			std::string message = "GcodePositionProcessor.Parse - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
			return NULL;
		}
		parsed_command command;
		gpp::parser->try_parse_gcode(gcode, command);
		return command.to_py_object();
	}

	static PyObject* GetCurrentPositionTuple(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::VERBOSE,
			"Getting current position tuple."
		);
		const char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GcodePositionProcessor.Parse - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}
		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
				"Could not find a position processor with the given key.");
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;
		return p_gcode_position->get_current_position().to_py_tuple();
	}

	static PyObject* GetCurrentPositionDict(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::VERBOSE,
			"Getting current position dict."
		);
		char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GcodePositionProcessor.GetCurrentPositionDict - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}

		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
				"Could not find a position processor with the given key.");
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		return p_gcode_position->get_current_position().to_py_dict();
	}

	static PyObject* GetPreviousPositionTuple(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::VERBOSE,
			"Getting previous position tuple."
		);
		const char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GcodePositionProcessor.GetPreviousPositionTuple - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}
		// Get the position processor by key
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
				"GcodePositionProcessor.GetPreviousPositionTuple - Could not find a position processor with the given key.");
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;
		return p_gcode_position->get_previous_position().to_py_tuple();
	}

	static PyObject* GetPreviousPositionDict(PyObject* self, PyObject* args)
	{
		set_internal_log_levels(true);
		octolapse_log(
			octolapse_log::GCODE_POSITION, octolapse_log::VERBOSE,
			"Getting previous position dict."
		);
		char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GcodePositionProcessor.GetPreviousPositionDict - Error parsing parameters.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return NULL;
		}

		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
				"GcodePositionProcessor.GetPreviousPositionDict - Could not find a position processor with the given key.");
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		return p_gcode_position->get_previous_position().to_py_dict();
	}
}

static bool ExecuteStabilizationProgressCallback(PyObject* progress_callback, const double percent_complete,
	const double seconds_elapsed, const double estimated_seconds_remaining,
	const int gcodes_processed, const int lines_processed)
{
	//octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::VERBOSE, "Executing the stabilization progress callback.");
	PyObject* funcArgs = Py_BuildValue("(d,d,d,i,i)", percent_complete, seconds_elapsed, estimated_seconds_remaining,
		gcodes_processed, lines_processed);
	if (funcArgs == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteStabilizationProgressCallback - Error parsing parameters.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}


	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* pContinueProcessing = PyObject_CallObject(progress_callback, funcArgs);
	PyGILState_Release(gstate);

	Py_DECREF(funcArgs);

	if (pContinueProcessing == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ExecuteStabilizationProgressCallback - Failed to call python progress callback.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}

	bool continue_processing = PyLong_AsLong(pContinueProcessing) > 0;
	Py_DECREF(pContinueProcessing);
	return continue_processing;
}

static bool ExecuteGetSnapshotPositionCallback(PyObject* py_get_snapshot_position_callback, double x_initial,
	double y_initial, double& x_result, double& y_result)
{
	//octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::VERBOSE, "Executing the get_snapshot_position callback.");
	PyObject* funcArgs = Py_BuildValue("(d,d)", x_initial, y_initial);
	if (funcArgs == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Error parsing parameters.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}


	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject* pyCoordinates = PyObject_CallObject(py_get_snapshot_position_callback, funcArgs);
	PyGILState_Release(gstate);

	Py_DECREF(funcArgs);

	if (pyCoordinates == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Failed to call python get stabilization position callback.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	PyObject* pyX = PyDict_GetItemString(pyCoordinates, "x");
	if (pyX == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Failed to parse the return x value.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	x_result = PyFloatOrInt_AsDouble(pyX);
	PyObject* pyY = PyDict_GetItemString(pyCoordinates, "y");
	if (pyY == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Failed to parse the return y value.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	y_result = PyFloatOrInt_AsDouble(pyY);
	Py_DECREF(pyCoordinates);
	return true;
}

/// Argument Parsing
static bool ParsePositionArgs(PyObject* py_args, gcode_position_args* args)
{
	octolapse_log(
		octolapse_log::GCODE_POSITION, octolapse_log::DEBUG,
		"Parsing Position Args."
	);
	// Here is the full structure of the position args:
	// get the volume py object
	PyObject* py_volume = PyDict_GetItemString(py_args, "volume");
	if (py_volume == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve volume from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}

	// Here is the full structure of the position args:
	// get the volume py object
	PyObject* py_bed_type = PyDict_GetItemString(py_volume, "bed_type");
	if (py_bed_type == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve bed_type from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	// Extract the bed type string
	args->is_circular_bed = strcmp(PyUnicode_SafeAsString(py_bed_type), "circular") == 0;
	// Get Build Plate Area
	PyObject* py_x_min = PyDict_GetItemString(py_volume, "min_x");
	if (py_x_min == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve min_x from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->x_min = PyFloatOrInt_AsDouble(py_x_min);

	PyObject* py_x_max = PyDict_GetItemString(py_volume, "max_x");
	if (py_x_max == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve max_x from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->x_max = PyFloatOrInt_AsDouble(py_x_max);

	PyObject* py_y_min = PyDict_GetItemString(py_volume, "min_y");
	if (py_y_min == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve min_y from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->y_min = PyFloatOrInt_AsDouble(py_y_min);

	PyObject* py_y_max = PyDict_GetItemString(py_volume, "max_y");
	if (py_y_max == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve max_y from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->y_max = PyFloatOrInt_AsDouble(py_y_max);

	PyObject* py_z_min = PyDict_GetItemString(py_volume, "min_z");
	if (py_z_min == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve min_z from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->z_min = PyFloatOrInt_AsDouble(py_z_min);

	PyObject* py_z_max = PyDict_GetItemString(py_volume, "max_z");
	if (py_z_max == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve max_z from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->z_max = PyFloatOrInt_AsDouble(py_z_max);

	// Get Bounds
	PyObject* py_bounds = PyDict_GetItemString(py_volume, "bounds");
	if (py_bounds == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve bounds from the position args dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	// If py_bounds is a dict, we have no snapshot boundaries other than the printer volume
	if (PyDict_Check(py_bounds) < 1)
	{
		octolapse_log(
			octolapse_log::GCODE_PARSER, octolapse_log::DEBUG,
			"No snapshot restrictions set."
		);
		args->is_bound_ = false;
	}
	else
	{
		args->is_bound_ = true;
		octolapse_log(
			octolapse_log::GCODE_PARSER, octolapse_log::INFO,
			"Snapshot restrictions set."
		);

		PyObject* py_snapshot_x_min = PyDict_GetItemString(py_bounds, "min_x");
		if (py_snapshot_x_min == NULL)
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - Unable to retrieve min_x from the bounds dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		args->snapshot_x_min = PyFloatOrInt_AsDouble(py_snapshot_x_min);

		PyObject* py_snapshot_x_max = PyDict_GetItemString(py_bounds, "max_x");
		if (py_snapshot_x_max == NULL)
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - Unable to retrieve max_x from the bounds dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		args->snapshot_x_max = PyFloatOrInt_AsDouble(py_snapshot_x_max);

		PyObject* py_snapshot_y_min = PyDict_GetItemString(py_bounds, "min_y");
		if (py_snapshot_y_min == NULL)
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - Unable to retrieve min_y from the bounds dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		args->snapshot_y_min = PyFloatOrInt_AsDouble(py_snapshot_y_min);

		PyObject* py_snapshot_y_max = PyDict_GetItemString(py_bounds, "max_y");
		if (py_snapshot_y_max == NULL)
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - Unable to retrieve max_y from the bounds dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		args->snapshot_y_max = PyFloatOrInt_AsDouble(py_snapshot_y_max);

		PyObject* py_snapshot_z_min = PyDict_GetItemString(py_bounds, "min_z");
		if (py_snapshot_z_min == NULL)
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - Unable to retrieve min_z from the bounds dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		args->snapshot_z_min = PyFloatOrInt_AsDouble(py_snapshot_z_min);

		PyObject* py_snapshot_z_max = PyDict_GetItemString(py_bounds, "max_z");
		if (py_snapshot_z_max == NULL)
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - Unable to retrieve max_z from the bounds dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		args->snapshot_z_max = PyFloatOrInt_AsDouble(py_snapshot_z_max);

		std::stringstream stream;

		stream << "Bounds - " <<
			"X:(" << utilities::to_string(args->snapshot_x_min) << "," << utilities::to_string(args->snapshot_x_max) << ") "
			<<
			"Y:(" << utilities::to_string(args->snapshot_y_min) << "," << utilities::to_string(args->snapshot_y_max) << ") "
			<<
			"Z:(" << utilities::to_string(args->snapshot_z_min) << "," << utilities::to_string(args->snapshot_z_max) << ") ";
		octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::DEBUG, stream.str());
	}

#pragma region location_detection_commands
	// Get LocationDetection Commands
	PyObject* py_location_detection_commands = PyDict_GetItemString(py_args, "location_detection_commands");
	if (py_location_detection_commands == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve location_detection_commands from the bounds dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	// Extract the elements from  the location detection command list pyobject
	const int listSize = PyList_Size(py_location_detection_commands);
	if (listSize < 0)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to build position arguments, LocationDetectionCommands is not a list.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}

	for (int index = 0; index < listSize; index++)
	{
		PyObject* pyListItem = PyList_GetItem(py_location_detection_commands, index);
		if (pyListItem == NULL)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Could not extract a list item from index from the location detection commands.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		if (!PyUnicode_SafeCheck(pyListItem))
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Argument 16 (location_detection_commands) must be a list of strings.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		std::string command = PyUnicode_SafeAsString(pyListItem);
		args->location_detection_commands.push_back(command);
	}
#pragma endregion Parse the list of location detection commands

	// xyz_axis_default_mode
	PyObject* py_xyz_axis_default_mode = PyDict_GetItemString(py_args, "xyz_axis_default_mode");
	if (py_xyz_axis_default_mode == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve xyz_axis_default_mode from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->xyz_axis_default_mode = PyUnicode_SafeAsString(py_xyz_axis_default_mode);

	// e_axis_default_mode
	PyObject* py_e_axis_default_mode = PyDict_GetItemString(py_args, "e_axis_default_mode");
	if (py_e_axis_default_mode == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve e_axis_default_mode from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->e_axis_default_mode = PyUnicode_SafeAsString(py_e_axis_default_mode);

	// units_default
	PyObject* py_units_default = PyDict_GetItemString(py_args, "units_default");
	if (py_units_default == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve units_default from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->units_default = PyUnicode_SafeAsString(py_units_default);

	// autodetect_position
	PyObject* py_autodetect_position = PyDict_GetItemString(py_args, "autodetect_position");
	if (py_autodetect_position == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve autodetect_position from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->autodetect_position = PyLong_AsLong(py_autodetect_position) > 0;

	// Here is the full structure of the position args:
	// get the volume py object
	PyObject* py_home = PyDict_GetItemString(py_args, "home_position");
	if (py_home == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve home_position from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}

	// home_x
	PyObject* py_home_x = PyDict_GetItemString(py_home, "home_x");
	if (py_home_x == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve home_x from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	if (py_home_x == Py_None)
	{
		args->home_x_none = true;
	}
	else
	{
		args->home_x = PyFloatOrInt_AsDouble(py_home_x);
	}

	// home_y
	PyObject* py_home_y = PyDict_GetItemString(py_home, "home_y");
	if (py_home_y == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve home_y from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	if (py_home_y == Py_None)
	{
		args->home_y_none = true;
	}
	else
	{
		args->home_y = PyFloatOrInt_AsDouble(py_home_y);
	}

	// home_z
	PyObject* py_home_z = PyDict_GetItemString(py_home, "home_z");
	if (py_home_z == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve home_z from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	if (py_home_z == Py_None)
	{
		args->home_z_none = true;
	}
	else
	{
		args->home_z = PyFloatOrInt_AsDouble(py_home_z);
	}

	// num_extruders
	PyObject* py_num_extruders = PyDict_GetItemString(py_args, "num_extruders");
	if (py_num_extruders == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve num_extruders from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->set_num_extruders(PyLong_AsLong(py_num_extruders));

	// py_shared_extruder
	PyObject* py_shared_extruder = PyDict_GetItemString(py_args, "shared_extruder");
	if (py_shared_extruder == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve shared_extruder from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->shared_extruder = PyLong_AsLong(py_shared_extruder) > 0;

	// zero_based_extruder
	PyObject* py_zero_based_extruder = PyDict_GetItemString(py_args, "zero_based_extruder");
	if (py_zero_based_extruder == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve zero_based_extruder from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->zero_based_extruder = PyLong_AsLong(py_zero_based_extruder) > 0;

	// default extruder
	PyObject* py_default_extruder_index = PyDict_GetItemString(py_args, "default_extruder_index");
	if (py_default_extruder_index == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve default_extruder_index from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	// The zero based default extruder
	args->default_extruder = PyLong_AsLong(py_default_extruder_index);

	// get the slicer settings dictionary
	PyObject* py_slicer_settings_dict = PyDict_GetItemString(py_args, "slicer_settings");
	if (py_slicer_settings_dict == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve slicer_settings from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}


#pragma region Extract extruder objects
	PyObject* py_extruders = PyDict_GetItemString(py_slicer_settings_dict, "extruders");
	if (py_extruders == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve extruders list from the slicer settings dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	if (!PyList_Check(py_extruders))
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - The extruders object in the slicer settings dict is not a list.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	const int extruder_list_size = PyList_Size(py_extruders);
	//std::cout << "Found " << extruder_list_size << " extruders.\r\n";
	// make sure there is at lest one item in the list
	if (extruder_list_size < 1)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to build a list of extruders from the slicer settings dict arguments.  There are no extruders in the list.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	if (extruder_list_size < args->num_extruders)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Too few extruders were detected.  There must be at least as many extruders in the list the num_extruders variable.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	for (int index = 0; index < extruder_list_size; index++)
	{
		//std::cout << "Extracting the current extruder #" << index << ".\r\n";
		PyObject* py_extruder = PyList_GetItem(py_extruders, index);
		if (py_extruder == NULL)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Could not extract an extruder from index from the extruders list.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		// Extract the z_lift_height from the current extruder
		PyObject* py_z_lift_height = PyDict_GetItemString(py_extruder, "z_lift_height");
		if (py_z_lift_height == NULL)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve z_lift_height list from the current extruder.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}

		if (!(PyFloatLongOrInt_Check(py_z_lift_height) || py_z_lift_height == Py_None))
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - The z_lift_height object must a float or int.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}

		if (py_z_lift_height == Py_None)
		{
			args->z_lift_heights[index] = 0;
		}
		else
		{
			double height = PyFloatOrInt_AsDouble(py_z_lift_height);
			args->z_lift_heights[index] = height;
		}

		// Extract the retraction_length from the current extruder
		PyObject* py_retraction_length = PyDict_GetItemString(py_extruder, "retraction_length");
		if (py_retraction_length == NULL)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve retraction_length list from the current extruder.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		if (!(PyFloatLongOrInt_Check(py_retraction_length) || py_retraction_length == Py_None))
		{
			std::string message = "GcodePositionProcessor.ParsePositionArgs - The z_lift_height object must a float or int.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		if (py_z_lift_height == Py_None)
		{
			args->retraction_lengths[index] = 0;
		}
		else
		{
			double length = PyFloatOrInt_AsDouble(py_retraction_length);
			args->retraction_lengths[index] = length;
		}
	}

#pragma endregion Parse extruder objects

#pragma region Extract firmware extruder offsets from the printer settings
	// Only extract extruder offsets if there is more than one extruder.
	if (args->num_extruders > 1)
	{
		PyObject* py_extruder_offsets = PyDict_GetItemString(py_args, "extruder_offsets");
		if (py_extruder_offsets == NULL)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve extruder_offsets from the position dict.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		if (!PyList_Check(py_extruder_offsets))
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - The extruder_offsets object in the position dict is not a list.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}

		int extruder_offsets_list_size = PyList_Size(py_extruder_offsets);
		//std::cout << "Found " << extruder_list_size << " extruders.\r\n";
		// make sure there is at lest one item in the list
		if (extruder_offsets_list_size < args->num_extruders && !args->shared_extruder)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Too few extruder offsets were detected.  There must be at least as many extruder offsets in the list as the num_extruders variable when not using a shared extruder.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		if (extruder_offsets_list_size > args->num_extruders && !args->shared_extruder)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Too many extruder offsets were detected.  There can only be as many extruder offsets in the list as the num_extruders variable when not using a shared extruder.";
			octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
			return false;
		}
		if (extruder_offsets_list_size > 0 && args->shared_extruder)
		{
			std::string message =
				"GcodePositionProcessor.ParsePositionArgs - Firmware extruder offset values are not allowed when using shared extruders.  Setting offsets to 0.";
			octolapse_log(octolapse_log::WARNING, octolapse_log::GCODE_POSITION, message);
			extruder_offsets_list_size = 0;
		}

		for (int index = 0; index < extruder_offsets_list_size; index++)
		{
			std::cout << "Extracting the current extruder offset#" << index << ".\r\n";
			PyObject* py_extruder_offset = PyList_GetItem(py_extruder_offsets, index);
			if (py_extruder_offset == NULL)
			{
				std::string message =
					"GcodePositionProcessor.ParsePositionArgs - Could not extract an extruder offset by index from the extruder_offsets list.";
				octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
				return false;
			}
			// Extract the x_firmware_offset from the current extruder (called x)
			PyObject* py_extruder_offset_x = PyDict_GetItemString(py_extruder_offset, "x");
			if (py_extruder_offset_x == NULL)
			{
				std::string message =
					"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve an x offset from a list item in the the extruder_offsets list.";
				octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
				return false;
			}
			std::cout << "Checking x offset value.\r\n";
			if (!(PyFloatLongOrInt_Check(py_extruder_offset_x) || py_extruder_offset_x == Py_None))
			{
				std::string message =
					"GcodePositionProcessor.ParsePositionArgs - The extruder_offset.x object must a float or int.";
				octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
				return false;
			}
			std::cout << "Assigning x offset value.\r\n";
			if (py_extruder_offset_x == Py_None)
			{
				args->x_firmware_offsets[index] = 0;
			}
			else
			{
				double x = PyFloatOrInt_AsDouble(py_extruder_offset_x);
				args->x_firmware_offsets[index] = x;
			}
			// Extract the x_firmware_offset from the current extruder (called x)
			PyObject* py_extruder_offset_y = PyDict_GetItemString(py_extruder_offset, "y");
			if (py_extruder_offset_y == NULL)
			{
				std::string message =
					"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve an y offset from a list item in the the extruder_offsets list.";
				octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
				return false;
			}
			std::cout << "Checking y offset value.\r\n";
			if (!(PyFloatLongOrInt_Check(py_extruder_offset_y) || py_extruder_offset_y == Py_None))
			{
				std::string message =
					"GcodePositionProcessor.ParsePositionArgs - The extruder_offset.y object must a float or int.";
				octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
				return false;
			}
			std::cout << "Assigning y offset value.\r\n";
			if (py_extruder_offset_y == Py_None)
			{
				args->y_firmware_offsets[index] = 0;
			}
			else
			{
				double y = PyFloatOrInt_AsDouble(py_extruder_offset_y);
				args->y_firmware_offsets[index] = y;
			}
		}
	}

#pragma endregion Extract firmware extruder offsets from the printer settings
	// priming_height
	PyObject* py_priming_height = PyDict_GetItemString(py_args, "priming_height");
	if (py_priming_height == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve priming_height from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->priming_height = PyFloatOrInt_AsDouble(py_priming_height);

	// minimum_layer_height
	PyObject* py_minimum_layer_height = PyDict_GetItemString(py_args, "minimum_layer_height");
	if (py_minimum_layer_height == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve minimum_layer_height from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->minimum_layer_height = PyFloatOrInt_AsDouble(py_minimum_layer_height);

	// g90_influences_extruder
	PyObject* py_g90_influences_extruder = PyDict_GetItemString(py_args, "g90_influences_extruder");
	if (py_g90_influences_extruder == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParsePositionArgs - Unable to retrieve g90_influences_extruder from the position dict.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return false;
	}
	args->g90_influences_extruder = PyLong_AsLong(py_g90_influences_extruder) > 0;

	return true;
}

static bool ParseStabilizationArgs(PyObject* py_args, stabilization_args* args, PyObject** py_progress_callback,
	PyObject** py_snapshot_position_callback)
{
	octolapse_log(
		octolapse_log::SNAPSHOT_PLAN, octolapse_log::DEBUG,
		"Parsing Stabilization Args."
	);
	//std::cout << "Parsing Stabilization Args.\r\n";
	// gcode_generator
	PyObject* py_gcode_generator = PyDict_GetItemString(py_args, "gcode_generator");
	if (py_gcode_generator == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve gcode_generator from the smart layer stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	// Need to incref py_gcode_generator, borrowed ref and we're holding it!
	// This should no longer be true...
	//Py_INCREF(py_gcode_generator);
	// extract the get_snapshot_position callback
	PyObject* py_get_snapshot_position_callback = PyObject_GetAttrString(py_gcode_generator, "get_snapshot_position");
	if (py_get_snapshot_position_callback == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve get_snapshot_position function from the gcode_generator object.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	// make sure it is callable
	if (!PyCallable_Check(py_get_snapshot_position_callback))
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve get_snapshot_position function from the gcode_generator object.";
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::ERROR, message);
		return false;
	}
	// py_get_snapshot_position_callback is a new reference, no reason to incref
	*py_snapshot_position_callback = py_get_snapshot_position_callback;
	// on_progress_received
	PyObject* py_on_progress_received = PyDict_GetItemString(py_args, "on_progress_received");
	if (py_on_progress_received == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve on_progress_received from the stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	// need to incref this so it doesn't vanish later (borrowed reference we are saving)
	Py_IncRef(py_on_progress_received);
	*py_progress_callback = py_on_progress_received;


	// height_increment
	PyObject* py_height_increment = PyDict_GetItemString(py_args, "height_increment");
	if (py_height_increment == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve height_increment from the stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->height_increment = PyFloatOrInt_AsDouble(py_height_increment);

	// x_axis_stabilization_disabled
	PyObject* py_x_stabilization_disabled = PyDict_GetItemString(py_args, "x_stabilization_disabled");
	if (py_x_stabilization_disabled == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve x_stabilization_disabled from the stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->x_stabilization_disabled = PyLong_AsLong(py_x_stabilization_disabled) > 0;

	// x_axis_stabilization_disabled
	PyObject* py_y_stabilization_disabled = PyDict_GetItemString(py_args, "y_stabilization_disabled");
	if (py_x_stabilization_disabled == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve y_stabilization_disabled from the stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->y_stabilization_disabled = PyLong_AsLong(py_y_stabilization_disabled) > 0;

	// allow_snapshot_commands
	PyObject* py_allow_snapshot_commands = PyDict_GetItemString(py_args, "allow_snapshot_commands");
	if (py_allow_snapshot_commands == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve allow_snapshot_commands from the stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->allow_snapshot_commands = PyLong_AsLong(py_allow_snapshot_commands) > 0;

	// notification_period_seconds
	PyObject* py_notification_period_seconds = PyDict_GetItemString(py_args, "notification_period_seconds");
	if (py_notification_period_seconds == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve notification_period_seconds from the stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->notification_period_seconds = PyFloatOrInt_AsDouble(py_notification_period_seconds);


	// file_path
	PyObject* py_dict_key = PyString_SafeFromString("file_path");
	PyObject* py_dict_item = PyDict_GetItem(py_args, py_dict_key);
	if (py_dict_item == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs - Unable to retrieve the file_path from the stabilization args dict.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	Py_DecRef(py_dict_key);
	/*
	Py_UNICODE* py_dict_item_unicode = PyUnicode_AsUnicode(py_dict_item);
	//PyObject* py_file_path = PyDict_GetItemString(py_args, "file_path");
	if (py_dict_item_unicode == NULL)
	{
	  std::string message =
		"GcodePositionProcessor.ParseStabilizationArgs - Unable to convert the file_path dict item to a Py_UNICODE .";
	  octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
	  return false;
	}*/

	args->file_path = PyUnicode_SafeAsString(py_dict_item);

	args->snapshot_command.clear();

	// Extract the snapshot_command
	PyObject* py_snapshot_command = PyDict_GetItemString(py_args, "snapshot_command");
	if (py_snapshot_command == NULL)
	{
		std::string message =
			"ParseStabilizationArgs - Unable to retrieve snapshot_command from the stabilization args dict.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->snapshot_command_text = PyUnicode_SafeAsString(py_snapshot_command);

	gcode_parser parser;
	parser.try_parse_gcode(args->snapshot_command_text.c_str(), args->snapshot_command);
	if (args->snapshot_command.gcode.empty())
	{
		std::string message =
			"ParseStabilizationArgs - No alternative snapshot command was provided, using default command only.";
		message += args->snapshot_command_text;
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, message);
	}
	else
	{
		std::string message = "ParseStabilizationArgs - Alternative snapshot gcode (";
		message += args->snapshot_command.gcode;
		message += ") parsed successfully.";
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, message);
	}

	//std::cout << "Stabilization Args parsed successfully.\r\n";
	return true;
}

static bool ParseStabilizationArgs_SmartLayer(PyObject* py_args, smart_layer_args* args)
{
	octolapse_log(
		octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO,
		"Parsing Smart Layer Stabilization Args."
	);
	//std::cout << "Parsing smart layer args.\r\n";
	// Extract trigger_on_extrude
	PyObject* py_trigger_type = PyDict_GetItemString(py_args, "trigger_type");
	if (py_trigger_type == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs_SmartLayer - Unable to retrieve trigger_type from the smart layer trigger stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->smart_layer_trigger_type = static_cast<trigger_type>(PyLong_AsLong(py_trigger_type));

	PyObject* py_snap_to_print_high_quality = PyDict_GetItemString(py_args, "snap_to_print_high_quality");
	if (py_snap_to_print_high_quality == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs_SmartLayer - Unable to retrieve snap_to_print_high_quality from the smart layer trigger stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->snap_to_print_high_quality = PyLong_AsLong(py_snap_to_print_high_quality) > 0;

	PyObject* py_snap_to_print_smooth = PyDict_GetItemString(py_args, "snap_to_print_smooth");
	if (py_snap_to_print_smooth == NULL)
	{
		std::string message =
			"GcodePositionProcessor.ParseStabilizationArgs_SmartLayer - Unable to retrieve snap_to_print_smooth from the smart layer trigger stabilization args.";
		octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
		return false;
	}
	args->snap_to_print_smooth = PyLong_AsLong(py_snap_to_print_smooth) > 0;

	return true;
}

static bool ParseStabilizationArgs_SmartGcode(PyObject* py_args, smart_gcode_args* args)
{
	octolapse_log(
		octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO,
		"Parsing Smart Gcode Stabilization Args."
	);



	return true;
}
