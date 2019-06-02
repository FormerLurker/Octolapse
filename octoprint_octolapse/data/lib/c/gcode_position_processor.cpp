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
#include <iostream>
#include "stabilization_snap_to_print.h"
#include "stabilization_smart_layer.h"
#include "stabilization.h"
#include "logging.h"
#include "bytesobject.h"
#include "python_helpers.h"
#ifdef _DEBUG
#include "test.h"
#endif
// Sometimes used to test performance in release mode.
//#include "test.h"

#if PY_MAJOR_VERSION >= 3
int main(int argc, char *argv[])
{
	wchar_t *program = Py_DecodeLocale(argv[0], NULL);
	if (program == NULL) {
		fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
		exit(1);
	}

	// Add a built-in module, before Py_Initialize
	PyImport_AppendInittab("GcodePositionProcessor", PyInit_GcodePositionProcessor);

	// Pass argv[0] to the Python interpreter
	Py_SetProgramName(program);

	// Initialize the Python interpreter.  Required.
	Py_Initialize();
	std::cout << "Initializing threads...";
	PyEval_InitThreads();
	// Optionally import the module; alternatively, import can be deferred until the embedded script imports it.
	PyImport_ImportModule("GcodePositionProcessor");
	PyMem_RawFree(program);
	return 0;
}

#else

int main(int argc, char *argv[])
{
#ifdef _DEBUG
	run_tests(argc, argv);
	return 0;
#else
	// I use this sometimes to test performance in release mode
	//run_tests(argc, argv);
	//return 0;
	Py_SetProgramName(argv[0]);
	Py_Initialize();
	PyEval_InitThreads();
	initGcodePositionProcessor();
	return 0;
#endif
}
#endif

struct module_state {
	PyObject *error;
};
#if PY_MAJOR_VERSION >= 3
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#else
#define GETSTATE(m) (&_state)
static struct module_state _state;
#endif

// Python 2 module method definition
static PyMethodDef GcodePositionProcessorMethods[] = {
	{ "Initialize", (PyCFunction)Initialize,  METH_VARARGS  ,"Initialize the internal shared position processor." },
	{ "Undo",  (PyCFunction)Undo,  METH_VARARGS  ,"Undo an update made to the current position.  You can only undo once." },
	{ "Update",  (PyCFunction)Update,  METH_VARARGS  ,"Undo an update made to the current position.  You can only undo once." },
	{ "UpdatePosition",  (PyCFunction)UpdatePosition,  METH_VARARGS  ,"Update x,y,z,e and f for the given position key." },
	{ "Parse",  (PyCFunction)Parse,  METH_VARARGS  ,"Parse gcode text into a ParsedCommand." },
	{ "GetCurrentPositionTuple",  (PyCFunction)GetCurrentPositionTuple,  METH_VARARGS  ,"Returns the current position of the global GcodePosition tracker in a faster but harder to handle tuple form." },
	{ "GetCurrentPositionDict",  (PyCFunction)GetCurrentPositionDict,  METH_VARARGS  ,"Returns the current position of the global GcodePosition tracker in a slower but easier to deal with dict form." },
	{ "GetPreviousPositionTuple",  (PyCFunction)GetPreviousPositionTuple,  METH_VARARGS  ,"Returns the previous position of the global GcodePosition tracker in a faster but harder to handle tuple form." },
	{ "GetPreviousPositionDict",  (PyCFunction)GetPreviousPositionDict,  METH_VARARGS  ,"Returns the previous position of the global GcodePosition tracker in a slower but easier to deal with dict form." },
	{ "GetSnapshotPlans_SnapToPrint", (PyCFunction)GetSnapshotPlans_SnapToPrint, METH_VARARGS, "Parses a gcode file and returns snapshot plans for a 'SnapToPrint' stabilization." },
	{ "GetSnapshotPlans_SmartLayer", (PyCFunction)GetSnapshotPlans_SmartLayer, METH_VARARGS, "Parses a gcode file and returns snapshot plans for a 'SmartLayer' stabilization." },
	{ NULL, NULL, 0, NULL }
};

// Python 3 module method definition
#if PY_MAJOR_VERSION >= 3
static int GcodePositionProcessor_traverse(PyObject *m, visitproc visit, void *arg) {
	Py_VISIT(GETSTATE(m)->error);
	return 0;
}

static int GcodePositionProcessor_clear(PyObject *m) {
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

#else
#define INITERROR return

extern "C" void initGcodePositionProcessor(void)
#endif
{
		std::cout << "Initializing GcodePositionProcessor V1.0.0 - Copyright (C) 2019  Brad Hochgesang...";
		
#if PY_MAJOR_VERSION >= 3
		std::cout << "Python 3+ Detected...";
		PyObject *module = PyModule_Create(&moduledef);
#else
		std::cout << "Python 2 Detected...";
		PyObject *module = Py_InitModule("GcodePositionProcessor", GcodePositionProcessorMethods);
#endif

		if (module == NULL)
			INITERROR;
		struct module_state *st = GETSTATE(module);

		st->error = PyErr_NewException((char*)"GcodePositionProcessor.Error", NULL, NULL);
		if (st->error == NULL) {
			Py_DECREF(module);
			INITERROR;
		}
		octolapse_initialize_loggers();
		gpp::parser = new gcode_parser();

		std::cout << "complete\r\n";

#if PY_MAJOR_VERSION >= 3
		return module;
#endif
}

extern "C"
{
	/*
	void initGcodePositionProcessor(void)
	{
		
		Py_Initialize();
		//PyEval_InitThreads();

		PyObject *m = Py_InitModule("GcodePositionProcessor", GcodePositionProcessorMethods);
		octolapse_initialize_loggers();
		gpp::parser = new gcode_parser();
		std::cout << "complete\r\n";
	}
	*/
	static PyObject * GetSnapshotPlans_SnapToPrint(PyObject *self, PyObject *args)
	{
		// TODO:  add error reporting and logging
		PyObject *py_position_args;
		PyObject *py_stabilization_args;
		
		if (!PyArg_ParseTuple(
			args,
			"OO",
			&py_position_args,
			&py_stabilization_args)
		)
		{
			PyErr_SetString(PyExc_ValueError, "Error parsing parameters for GcodePositionProcessor.GetSnapshotPlans_LockToPrint.");
			return NULL;
		}
		
		gcode_position_args p_args;
		if (!ParsePositionArgs(py_position_args, &p_args))
		{
			return NULL;
		}

		// Extract the stabilization args
		stabilization_args s_args;
		if (!ParseStabilizationArgs(py_stabilization_args, &s_args))
		{
			return NULL;
		}
		
		// Create our stabilization object
		stabilization_snap_to_print stabilization(
			&p_args, 
			&s_args,
			pythonGetCoordinatesCallback(ExecuteGetSnapshotPositionCallback),
			pythonProgressCallback(ExecuteStabilizationProgressCallback)
		);

		stabilization_results results;
		stabilization.process_file(&results);
		octolapse_log(SNAPSHOT_PLAN, INFO, "Building snapshot plans.");

		PyObject * py_snapshot_plans = snapshot_plan::build_py_object(results.snapshot_plans_);
		if (py_snapshot_plans == NULL)
		{
			return NULL;
		}
		octolapse_log(SNAPSHOT_PLAN, INFO, "Creating return values.");
		PyObject * py_results = Py_BuildValue("(l,s,O,d,l,l)", results.success_, results.errors_.c_str(), py_snapshot_plans, results.seconds_elapsed_, results.gcodes_processed_, results.lines_processed_);
		if (py_results == NULL)
		{
			octolapse_log(SNAPSHOT_PLAN, ERROR, "Unable to create a Tuple from the snapshot plan list.");
			PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Error building callback arguments - Terminating");
			return NULL;
		}
		// Bring the snapshot plan refcount to 1
		//Py_DECREF(py_snapshot_plans);
		//Py_DECREF(py_position_args);
		//Py_DECREF(py_stabilization_args);
		//Py_DECREF(py_stabilization_type_args);
		//std::cout << "py_progress_callback refcount = " << py_progress_callback->ob_refcnt << "\r\n";
		octolapse_log(SNAPSHOT_PLAN, INFO, "Snapshot plan creation complete, returning plans.");
		//std::cout << "py_results refcount = " << py_results->ob_refcnt << "\r\n";
		return py_results;
	}

	static PyObject * GetSnapshotPlans_SmartLayer(PyObject *self, PyObject *args)
	{
		octolapse_log(SNAPSHOT_PLAN, INFO, "Running smart layer stabilization preprocessing.");
		// TODO:  add error reporting and logging
		PyObject *py_position_args;
		PyObject *py_stabilization_args;
		PyObject *py_stabilization_type_args;
		//std::cout << "Parsing Arguments\r\n";
		if (!PyArg_ParseTuple(
			args,
			"OOO",
			&py_position_args,
			&py_stabilization_args,
			&py_stabilization_type_args))
		{
			octolapse_log(SNAPSHOT_PLAN, ERROR, "Error parsing parameters for GcodePositionProcessor.GetSnapshotPlans_LockToPrint.");
			PyErr_SetString(PyExc_ValueError, "Error parsing parameters for GcodePositionProcessor.GetSnapshotPlans_LockToPrint.");
			return NULL;
		}
		// Removed by BH on 4-28-2019
		//Py_INCREF(py_position_args);
		//Py_INCREF(py_stabilization_args);
		//Py_INCREF(py_stabilization_type_args);
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
		if (!ParseStabilizationArgs(py_stabilization_args, &s_args))
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
		stabilization_smart_layer stabilization(
			&p_args,
			&s_args,
			&mt_args,
			pythonGetCoordinatesCallback(ExecuteGetSnapshotPositionCallback),
			pythonProgressCallback(ExecuteStabilizationProgressCallback)
		);

		stabilization_results results;
		//std::cout << "Processing gcode file.\r\n";
		stabilization.process_file(&results);
		octolapse_log(SNAPSHOT_PLAN, INFO, "Building snapshot plans.");

		PyObject * py_snapshot_plans = snapshot_plan::build_py_object(results.snapshot_plans_);
		if (py_snapshot_plans == NULL)
		{
			octolapse_log(SNAPSHOT_PLAN, ERROR, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Snapshot_plan::build_py_object returned Null");
			PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Snapshot_plan::build_py_object returned Null - Terminating");
			return NULL;
		}
		octolapse_log(SNAPSHOT_PLAN, INFO, "Creating return values.");
		PyObject * py_results = Py_BuildValue("(l,s,O,d,l,l)", results.success_, results.errors_.c_str(), py_snapshot_plans, results.seconds_elapsed_, results.gcodes_processed_, results.lines_processed_);
		if (py_results == NULL)
		{
			octolapse_log(SNAPSHOT_PLAN, ERROR, "Unable to create a Tuple from the snapshot plan list.");
			PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Error building callback arguments - Terminating");
			return NULL;
		}
		// Bring the snapshot plan refcount to 1
		Py_DECREF(py_snapshot_plans);
		//Py_DECREF(py_position_args);
		//Py_DECREF(py_stabilization_args);
		//Py_DECREF(py_stabilization_type_args);
		//std::cout << "py_progress_callback refcount = " << py_progress_callback->ob_refcnt << "\r\n";
		octolapse_log(SNAPSHOT_PLAN, INFO, "Snapshot plan creation complete, returning plans.");
		//std::cout << "py_results refcount = " << py_results->ob_refcnt << "\r\n";
		return py_results;
	}

	static PyObject* Initialize(PyObject* self, PyObject *args)
	{
		// Create the gcode position object 
		octolapse_log(SNAPSHOT_PLAN, INFO, "Initializing gcode position processor.");
		const char * pKey;
		PyObject* py_position_args;
		if (!PyArg_ParseTuple(
			args, "sO",
			&pKey,
			&py_position_args
		))
		{
			std::string message = "GcodePositionProcessor.Initialize failed: unable to parse the initialization parameters.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}

		gcode_position_args positionArgs;

		// Create the gcode position object 
		octolapse_log(SNAPSHOT_PLAN, INFO, "Parsing initialization position args.");

		if (!ParsePositionArgs(py_position_args, &positionArgs))
		{
			octolapse_log(SNAPSHOT_PLAN, ERROR, "Error parsing initialization position args.");
			return NULL; // The call failed, ParseInitializationArgs has taken care of the error message
		}
				
		// see if we already have a gcode_position object for the given key
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(pKey);
		gcode_position* p_gcode_position = NULL;
		if (gcode_position_iterator != gpp::gcode_positions.end())
		{
			octolapse_log(SNAPSHOT_PLAN, INFO, "Existing processor found, deleting.");
			delete gcode_position_iterator->second;
		}
		// Separate delete step.  Something is going on here.
		if (gcode_position_iterator != gpp::gcode_positions.end())
		{
			gpp::gcode_positions.erase(gcode_position_iterator);
		}

		std::string message = "Adding processor with key:";
		message.append(pKey).append("\r\n");

		octolapse_log(SNAPSHOT_PLAN, INFO, message);
		// Create the new position object
		gcode_position * p_new_position = new gcode_position(&positionArgs);
		// add the new gcode position to our list of objects
		gpp::gcode_positions.insert(std::pair<std::string, gcode_position*>(pKey, p_new_position));
		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Undo(PyObject* self, PyObject *args)
	{
		const char * key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			PyErr_SetString(PyExc_ValueError, "Undo requires at least one parameter: the gcode_position key");
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

	static PyObject* Update(PyObject* self, PyObject *args)
	{
		const char* key;
		const char* gcode;
		if (!PyArg_ParseTuple(args, "ss", &key, &gcode))
		{
			std::string message = "GcodePositionProcessor.Update - requires at least two parameters: the key and the gcode string";
			PyErr_Print();
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;

		}
		
		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		parsed_command command;
		if(gpp::parser->try_parse_gcode(gcode, &command))
			p_gcode_position->update(&command, -1, -1);

		PyObject * py_position = p_gcode_position->get_current_position()->to_py_tuple();
		if (py_position == NULL)
		{
			std::string message = "GcodePositionProcessor.Update - Unable to convert the position to a tuple.";
			PyErr_Print();
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		return py_position;
	}

	static PyObject* UpdatePosition(PyObject* self, PyObject *args)
	{
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
			std::string message = "Unable to parse the UpdatePosition argument list.";
			PyErr_Print();
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			std::string message = "No parser was found for the given key: ";
			message += key;
			octolapse_log(GCODE_PARSER, ERROR, message);
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		p_gcode_position->update_position(
			p_gcode_position->get_current_position(),
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

		PyObject * py_position = p_gcode_position->get_current_position()->to_py_tuple();
		if (py_position == NULL)
		{
			return NULL;
		}

		return py_position;
	}

	static PyObject* Parse(PyObject* self, PyObject *args)
	{
		const char* gcode;
		if (!PyArg_ParseTuple(args, "s", &gcode))
		{
			std::string message = "Parse requires at least one parameter: the gcode string.  Either this parameter is missing or it is not a unicode string.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		parsed_command command;
		bool success = gpp::parser->try_parse_gcode(gcode, &command);
		if (!success)
			return Py_BuildValue("O", Py_False);
		// Convert ParsedCommand to python object
		// note that all error handling will be done within the 
		// to_py_object function
		return command.to_py_object();
		
	}

	static PyObject* GetCurrentPositionTuple(PyObject* self, PyObject *args)
	{
		const char * key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GetCurrentPositionTuple requires at least one parameter: the gcode_position key";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		// Get the parser
		octolapse_log(SNAPSHOT_PLAN, INFO, "Retrieving the current position processor for the supplied key.");
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			octolapse_log(SNAPSHOT_PLAN, INFO, "Could not find a position processor with the given key.");
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;
		octolapse_log(SNAPSHOT_PLAN, INFO, "Creating and returning the current position tuple.");
		return p_gcode_position->get_current_position()->to_py_tuple();
	}

	static PyObject* GetCurrentPositionDict(PyObject* self, PyObject *args)
	{
		char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GetCurrentPositionTuple requires at least one parameter: the gcode_position key";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}

		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		return p_gcode_position->get_current_position()->to_py_dict();
	}

	static PyObject* GetPreviousPositionTuple(PyObject* self, PyObject *args)
	{
		const char * key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GetCurrentPositionTuple requires at least one parameter: the gcode_position key";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		// Get the position processor by key
		octolapse_log(SNAPSHOT_PLAN, INFO, "Retrieving the current position processor for the supplied key.");
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			octolapse_log(SNAPSHOT_PLAN, INFO, "Could not find a position processor with the given key.");
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;
		octolapse_log(SNAPSHOT_PLAN, INFO, "Creating and returning the previous position tuple.");
		return p_gcode_position->get_previous_position()->to_py_tuple();
	}

	static PyObject* GetPreviousPositionDict(PyObject* self, PyObject *args)
	{
		char* key;
		if (!PyArg_ParseTuple(args, "s", &key))
		{
			std::string message = "GetCurrentPositionTuple requires at least one parameter: the gcode_position key";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}

		// Get the parser
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(key);
		if (gcode_position_iterator == gpp::gcode_positions.end())
		{
			return Py_BuildValue("O", Py_False);
		}
		gcode_position* p_gcode_position = gcode_position_iterator->second;

		return p_gcode_position->get_previous_position()->to_py_dict();
	}
}

static bool ExecuteStabilizationProgressCallback(PyObject* progress_callback, const double percent_complete, const double seconds_elapsed, const double estimated_seconds_remaining, const long gcodes_processed, const long lines_processed)
{
	octolapse_log(SNAPSHOT_PLAN, VERBOSE, "Executing the stabilization progress callback.");
	PyObject * funcArgs = Py_BuildValue("(d,d,d,i,i)", percent_complete, seconds_elapsed, estimated_seconds_remaining, gcodes_processed, lines_processed);
	if (funcArgs == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteStabilizationProgressCallback - Error building callback arguments - Terminating";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}


	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject * pContinueProcessing = PyObject_CallObject(progress_callback, funcArgs);
	PyGILState_Release(gstate);

	Py_DECREF(funcArgs);

	if (pContinueProcessing == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteStabilizationProgressCallback - Failed to call python - Terminating";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}

	bool continue_processing = PyLong_AsLong(pContinueProcessing) > 0;
	Py_DECREF(pContinueProcessing);
	return continue_processing;

}

static bool ExecuteGetSnapshotPositionCallback(PyObject* py_get_snapshot_position_callback, double x_initial, double y_initial, double* x_result, double* y_result )
{
	//std::cout << "Executing get_snapshot_position callback.\r\n";
	octolapse_log(SNAPSHOT_PLAN, VERBOSE, "Executing the get_snapshot_position callback.");
	PyObject * funcArgs = Py_BuildValue("(d,d)", x_initial, y_initial);
	if (funcArgs == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Error building callback arguments - Terminating";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}


	PyGILState_STATE gstate = PyGILState_Ensure();
	PyObject * pyCoordinates = PyObject_CallObject(py_get_snapshot_position_callback, funcArgs);
	PyGILState_Release(gstate);

	Py_DECREF(funcArgs);

	if (pyCoordinates == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Failed to call python - Terminating";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}
	//std::cout << "Extracting X coordinate.\r\n";
	PyObject * pyX = PyDict_GetItemString(pyCoordinates,"x");
	if (pyX == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Failed to parse the return x value - Terminating";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}
	*x_result = PyFloatOrInt_AsDouble(pyX);
	//std::cout << "Extracting Y coordinate.\r\n";
	PyObject * pyY = PyDict_GetItemString(pyCoordinates, "y");
	if (pyY == NULL)
	{
		std::string message = "GcodePositionProcessor.ExecuteGetSnapshotPositionCallback - Failed to parse the return y value - Terminating";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}
	*y_result = PyFloatOrInt_AsDouble(pyY);
	//std::cout << "Next Stabilization Coordinates: X" << *x_result << " Y"<< *y_result <<"\r\n";
	Py_DECREF(pyCoordinates);
	return true;

}

/// Argument Parsing
static bool ParsePositionArgs(PyObject *py_args, gcode_position_args *args)
{
	// Get IsBound
	PyObject * py_is_bound = PyDict_GetItemString(py_args, "is_bound");
	if (py_is_bound == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve is_bound from the position args dict.");
		return false;
	}
	args->is_bound_ = PyLong_AsLong(py_is_bound) > 0;

	if (args->is_bound_)
	{
		// Extract the bounds
		PyObject * py_bounds = PyDict_GetItemString(py_args, "bounds");
		if (py_bounds == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve bounds from the position args dict.");
			return false;
		}

		PyObject * py_x_min = PyDict_GetItemString(py_bounds, "x_min");
		if (py_x_min == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve x_min from the bounds dict.");
			return false;
		}
		args->x_min_ = PyFloatOrInt_AsDouble(py_x_min);

		PyObject * py_x_max = PyDict_GetItemString(py_bounds, "x_max");
		if (py_x_max == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve x_max from the bounds dict.");
			return false;
		}
		args->x_max_ = PyFloatOrInt_AsDouble(py_x_max);

		PyObject * py_y_min = PyDict_GetItemString(py_bounds, "y_min");
		if (py_y_min == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve y_min from the bounds dict.");
			return false;
		}
		args->y_min_ = PyFloatOrInt_AsDouble(py_y_min);

		PyObject * py_y_max = PyDict_GetItemString(py_bounds, "y_max");
		if (py_y_max == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve y_max from the bounds dict.");
			return false;
		}
		args->y_max_ = PyFloatOrInt_AsDouble(py_y_max);

		PyObject * py_z_min = PyDict_GetItemString(py_bounds, "z_min");
		if (py_z_min == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve z_min from the bounds dict.");
			return false;
		}
		args->z_min_ = PyFloatOrInt_AsDouble(py_z_min);

		PyObject * py_z_max = PyDict_GetItemString(py_bounds, "z_max");
		if (py_z_max == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_TypeError, "Unable to retrieve z_max from the bounds dict.");
			return false;
		}
		args->z_max_ = PyFloatOrInt_AsDouble(py_z_max);
	}
	//PyObject_Print(args, stdout, Py_PRINT_RAW);

	// Get LocationDetection Commands
	PyObject * py_location_detection_commands = PyDict_GetItemString(py_args, "location_detection_commands");
	if (py_location_detection_commands == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve py_location_detection_commands from the position args dict.");
		return false;
	}
	// Extract the elements from  the location detection command list pyobject
	int listSize = PyList_Size(py_location_detection_commands);
	if (listSize < 0)
	{
		std::string message = "Unable to build position arguments, LocationDetectionCommands is not a list.";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}

	for (int index = 0; index < listSize; index++) {
		PyObject *pyListItem = PyList_GetItem(py_location_detection_commands, index);
		if (pyListItem == NULL)
		{
			std::string message = "Could not extract a list item from index from the location detection commands.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return false;
		}
		if (!PyUnicode_SafeCheck(pyListItem)) {
			std::string message = "Argument 16 (location_detection_commands) must be a list of strings.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());

			return false;
		}
		std::string command = PyUnicode_SafeAsString(pyListItem);
		args->location_detection_commands.push_back(command);
	}
	
	// xyz_axis_default_mode
	PyObject * py_xyz_axis_default_mode = PyDict_GetItemString(py_args, "xyz_axis_default_mode");
	if (py_xyz_axis_default_mode == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve xyz_axis_default_mode from the position dict.");
		return false;
	}
	args->xyz_axis_default_mode = PyUnicode_SafeAsString(py_xyz_axis_default_mode);

	// e_axis_default_mode
	PyObject * py_e_axis_default_mode = PyDict_GetItemString(py_args, "e_axis_default_mode");
	if (py_e_axis_default_mode == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve e_axis_default_mode from the position dict.");
		return false;
	}
	args->e_axis_default_mode = PyUnicode_SafeAsString(py_e_axis_default_mode);

	// units_default
	PyObject * py_units_default = PyDict_GetItemString(py_args, "units_default");
	if (py_units_default == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve units_default from the position dict.");
		return false;
	}
	args->units_default = PyUnicode_SafeAsString(py_units_default);

	// autodetect_position
	PyObject * py_autodetect_position = PyDict_GetItemString(py_args, "autodetect_position");
	if (py_autodetect_position == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve autodetect_position from the position dict.");
		return false;
	}
	args->autodetect_position = PyLong_AsLong(py_autodetect_position) > 0;

	// origin_x
	PyObject * py_origin_x = PyDict_GetItemString(py_args, "origin_x");
	if (py_origin_x == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve origin_x from the position dict.");
		return false;
	}
	if (py_origin_x == Py_None)
	{
		args->origin_x_none = true;
	}
	else
	{
		args->origin_x = PyFloatOrInt_AsDouble(py_origin_x);
	}
	
	// origin_y
	PyObject * py_origin_y = PyDict_GetItemString(py_args, "origin_y");
	if (py_origin_y == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve origin_y from the position dict.");
		return false;
	}
	if (py_origin_y == Py_None)
	{
		args->origin_y_none = true;
	}
	else
	{
		args->origin_y = PyFloatOrInt_AsDouble(py_origin_y);
	}

	// origin_z
	PyObject * py_origin_z = PyDict_GetItemString(py_args, "origin_z");
	if (py_origin_z == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve origin_z from the position dict.");
		return false;
	}
	if (py_origin_z == Py_None)
	{
		args->origin_z_none = true;
	}
	else
	{
		args->origin_z = PyFloatOrInt_AsDouble(py_origin_z);
	}
	// get the slicer settings dictionary

	PyObject * py_slicer_settings_dict = PyDict_GetItemString(py_args, "slicer_settings");
	if (py_slicer_settings_dict == NULL)
	{
		PyErr_Print();
		octolapse_log(SNAPSHOT_PLAN, ERROR, "Unable to retrieve slicer settings from the position dict.");
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve slicer settings from the position dict.");
		return false;
	}
	
	// retraction_length
	PyObject * py_retraction_length = PyDict_GetItemString(py_slicer_settings_dict, "retraction_length");
	if (py_retraction_length == NULL)
	{
		PyErr_Print();
		octolapse_log(SNAPSHOT_PLAN, ERROR, "Unable to retrieve retraction_length from the slicer settings dict.");
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve retraction_length from the slicer settings dict.");
		return false;
	}
	args->retraction_length = PyFloatOrInt_AsDouble(py_retraction_length);

	// z_lift_height
	PyObject * py_z_lift_height = PyDict_GetItemString(py_slicer_settings_dict, "z_lift_height");
	if (py_z_lift_height == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve z_lift_height from the slicer settings dict.");
		return false;
	}
	args->z_lift_height = PyFloatOrInt_AsDouble(py_z_lift_height);

	// priming_height
	PyObject * py_priming_height = PyDict_GetItemString(py_args, "priming_height");
	if (py_priming_height == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve priming_height from the position dict.");
		return false;
	}
	args->priming_height = PyFloatOrInt_AsDouble(py_priming_height);

	// minimum_layer_height
	PyObject * py_minimum_layer_height = PyDict_GetItemString(py_args, "minimum_layer_height");
	if (py_minimum_layer_height == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve minimum_layer_height from the position dict.");
		return false;
	}
	args->minimum_layer_height = PyFloatOrInt_AsDouble(py_minimum_layer_height);

	// g90_influences_extruder
	PyObject * py_g90_influences_extruder = PyDict_GetItemString(py_args, "g90_influences_extruder");
	if (py_g90_influences_extruder == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve g90_influences_extruder from the position dict.");
		return false;
	}
	args->g90_influences_extruder = PyLong_AsLong(py_g90_influences_extruder) > 0;
	
	return true;
}

static bool ParseStabilizationArgs(PyObject *py_args, stabilization_args* args)
{
	//std::cout << "Parsing Stabilization Args.\r\n";
	// gcode_generator
	PyObject * py_gcode_generator = PyDict_GetItemString(py_args, "gcode_generator");
	if (py_gcode_generator == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve gcode_generator from the smart layer stabilization args.");
		return false;
	}
	// Need to incref py_gcode_generator, borrowed ref and we're holding it!
	Py_INCREF(py_gcode_generator);
	args->py_gcode_generator = py_gcode_generator;
	// extract the get_snapshot_position callback
	PyObject * py_get_snapshot_position_callback = PyObject_GetAttrString(py_gcode_generator, "get_snapshot_position");
	if (py_get_snapshot_position_callback == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve get_snapshot_position function from the gcode_generator object.");
		return false;
	}
	// make sure it is callable
	if (!PyCallable_Check(py_get_snapshot_position_callback)) {
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "The get_snapshot_position attribute must be callable.");
		return NULL;
	}
	// py_get_snapshot_position_callback is a new reference, no reason to incref
	args->py_get_snapshot_position_callback = py_get_snapshot_position_callback;

	// height_increment
	PyObject * py_height_increment = PyDict_GetItemString(py_args, "height_increment");
	if (py_height_increment == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve height_increment from the stabilization args.");
		return false;
	}
	args->height_increment = PyFloatOrInt_AsDouble(py_height_increment);

	// fastest_speed
	PyObject * py_fastest_speed = PyDict_GetItemString(py_args, "fastest_speed");
	if (py_fastest_speed == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve fastest_speed from the stabilization args.");
		return false;
	}
	args->fastest_speed = PyLong_AsLong(py_fastest_speed) > 0;

	// notification_period_seconds
	PyObject * py_notification_period_seconds = PyDict_GetItemString(py_args, "notification_period_seconds");
	if (py_notification_period_seconds == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve notification_period_seconds from the stabilization args.");
		return false;
	}
	args->notification_period_seconds = PyFloatOrInt_AsDouble(py_notification_period_seconds);

	// on_progress_received
	PyObject * py_on_progress_received = PyDict_GetItemString(py_args, "on_progress_received");
	if (py_on_progress_received == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve on_progress_received from the stabilization args.");
		return false;
	}
	// need to incref this so it doesn't vanish later (borrowed reference we are saving)
	Py_IncRef(py_on_progress_received);
	args->py_on_progress_received = py_on_progress_received;

	// file_path
	PyObject * py_file_path = PyDict_GetItemString(py_args, "file_path");
	if (py_file_path == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve file_path from the stabilization args.");
		return false;
	}
	args->file_path = PyUnicode_SafeAsString(py_file_path);
	//std::cout << "Stabilization Args parsed successfully.\r\n";
	return true;
}

static bool ParseStabilizationArgs_SmartLayer(PyObject *py_args, smart_layer_args* args)
{
	//std::cout << "Parsing smart layer args.\r\n";
	// Extract trigger_on_extrude
	PyObject * py_trigger_type = PyDict_GetItemString(py_args, "trigger_type");
	if (py_trigger_type == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve trigger_type from the smart layer trigger stabilization args.");
		return false;
	}
	args->smart_layer_trigger_type = static_cast<trigger_type>(PyLong_AsLong(py_trigger_type));

	// Extract speed_threshold
	PyObject * py_speed_threshold = PyDict_GetItemString(py_args, "speed_threshold");
	if (py_speed_threshold == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve speed_threshold from the smart layer trigger stabilization args.");
		return false;
	}
	args->speed_threshold = PyFloatOrInt_AsDouble(py_speed_threshold);

	// Extract speed_threshold
	PyObject * py_distance_threshold = PyDict_GetItemString(py_args, "distance_threshold");
	if (py_distance_threshold == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_TypeError, "Unable to retrieve distance_threshold from the smart layer trigger stabilization args.");
		return false;
	}
	args->distance_threshold = PyFloatOrInt_AsDouble(py_distance_threshold);
	//std::cout << "Smart layer args parsed successfully.\r\n";
	
	return true;
}
