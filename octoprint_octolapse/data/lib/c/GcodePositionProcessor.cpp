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

#include "GcodePositionProcessor.h"
#include <iostream>
#include "StabilizationSnapToPrint.h"
#include "Stabilization.h"
#include "Logging.h"
#include "bytesobject.h"
#include "PythonHelpers.h"
#ifdef _DEBUG
#include "test.h"
#endif


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
	{ "GetSnapshotPlans_LockToPrint", (PyCFunction)GetSnapshotPlans_LockToPrint, METH_VARARGS, "Parses a gcode file and returns snapshot plans for a 'SnapToPrint' stabilization." },
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
	static PyObject * GetSnapshotPlans_LockToPrint(PyObject *self, PyObject *args)
	{
		// TODO:  add error reporting and logging
		PyObject *py_stabilization_args;
		PyObject *py_progress_callback;
		char * file_path;
		char * nearest_to_corner;

		int iFavorXAxis;
		if (!PyArg_ParseTuple(
			args,
			"sOOsi",
			&file_path,
			&py_stabilization_args,
			&py_progress_callback,
			&nearest_to_corner,
			&iFavorXAxis))
		{
			PyErr_SetString(PyExc_ValueError, "Error parsing parameters for GetSnapshotPlansLockToPrint.");
			return NULL;
		}
		// get the progress callback
		if (!PyCallable_Check(py_progress_callback)) {
			PyErr_SetString(PyExc_TypeError, "parameter must be callable");
			return NULL;
		}
		Py_INCREF(py_progress_callback);
		Py_INCREF(py_stabilization_args);
		
		// Extract the stabilization args
		stabilization_args s_args;
		if (!ParseStabilizationArgs(py_stabilization_args, &s_args))
		{
			return NULL;
		}
		

		const bool favor_x_axis = iFavorXAxis > 0;
		// Create our stabilization object
		StabilizationSnapToPrint stabilization(&s_args,
			pythonProgressCallback(ExecuteStabilizationProgressCallback),
			py_progress_callback,
			nearest_to_corner,
			favor_x_axis);
		stabilization_results results;
		stabilization.process_file(file_path, &results);
		octolapse_log(SNAPSHOT_PLAN, INFO, "Building snapshot plans.");

		PyObject * py_snapshot_plans = snapshot_plan::build_py_object(results.snapshot_plans);
		if (py_snapshot_plans == NULL)
		{
			return NULL;
		}
		octolapse_log(SNAPSHOT_PLAN, INFO, "Creating return values.");
		PyObject * py_results = Py_BuildValue("(l,s,O,d,l,l)", results.success, results.errors.c_str(), py_snapshot_plans, results.seconds_elapsed, results.gcodes_processed, results.lines_processed);
		if (py_results == NULL)
		{
			octolapse_log(SNAPSHOT_PLAN, ERROR, "Unable to create a Tuple from the snapshot plan list.");
			PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Error building callback arguments - Terminating");
			return NULL;
		}
		// Bring the snapshot plan refcount to 1
		Py_DECREF(py_snapshot_plans);
		//std::cout << "py_snapshot_plans refcount = " << py_snapshot_plans->ob_refcnt << "\r\n";
		Py_DECREF(py_progress_callback);
		//std::cout << "py_progress_callback refcount = " << py_progress_callback->ob_refcnt << "\r\n";
		Py_DECREF(py_stabilization_args);
		//std::cout << "py_progress_callback refcount = " << py_progress_callback->ob_refcnt << "\r\n";
		octolapse_log(SNAPSHOT_PLAN, INFO, "Snapshot plan creation complete, returning plans.");
		//std::cout << "py_results refcount = " << py_results->ob_refcnt << "\r\n";
		return py_results;
	}

	static PyObject* Initialize(PyObject* self, PyObject *args)
	{
		gcode_position_args positionArgs;

		if (!ParseInitializationArgs(args, &positionArgs))
		{
			return NULL; // The call failed, ParseInitializationArgs has taken care of the error message
		}

		// Create the gcode position object 
		octolapse_log(SNAPSHOT_PLAN, INFO, "Parsing initialization args.");
		gcode_position * p_new_position = new gcode_position(positionArgs);
		// see if we already have a gcode_position object for the given key
		std::map<std::string, gcode_position*>::iterator gcode_position_iterator = gpp::gcode_positions.find(positionArgs.key);
		if (gcode_position_iterator != gpp::gcode_positions.end())
		{
			octolapse_log(SNAPSHOT_PLAN, INFO, "Existing processor found, removing.");
			delete gcode_position_iterator->second;
			gpp::gcode_positions.erase(gcode_position_iterator);
		}
		std::string message = "Adding processor with key:";
		message.append(positionArgs.key).append("\r\n");

		octolapse_log(SNAPSHOT_PLAN, INFO, message);
		// add the new gcode position to our list of objects
		gpp::gcode_positions.insert(std::pair<std::string, gcode_position*>(positionArgs.key, p_new_position));
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

		PyObject * py_position = p_gcode_position->p_current_pos->to_py_tuple();
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
			p_gcode_position->p_current_pos,
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

		PyObject * py_position = p_gcode_position->p_current_pos->to_py_tuple();
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
		return p_gcode_position->p_current_pos->to_py_tuple();
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

		return p_gcode_position->p_current_pos->to_py_dict();
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
		return p_gcode_position->p_previous_pos->to_py_tuple();
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

		return p_gcode_position->p_previous_pos->to_py_dict();
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

/// Argument Parsing
static bool ParseInitializationArgs(PyObject *args, gcode_position_args *positionArgs)
{
	//PyObject_Print(args, stdout, Py_PRINT_RAW);

	PyObject * poLocationDetectionCommands; // Hold the PyList
	const char * pKey;
	const char * pXYZAxisDefaultMode;
	const char * pEAxisDefaultMode;
	const char * pUnitsDefault;
	long iAutoDetectPosition;
	long iOriginXIsNone;
	long iOriginYIsNone;
	long iOriginZIsNone;
	if (!PyArg_ParseTuple(
		args, "(sldldldlddddlsssO)",
		&pKey,
		&iAutoDetectPosition,
		&positionArgs->origin_x,
		&iOriginXIsNone,
		&positionArgs->origin_y,
		&iOriginYIsNone,
		&positionArgs->origin_z,
		&iOriginZIsNone,
		&positionArgs->retraction_length,
		&positionArgs->z_lift_height,
		&positionArgs->priming_height,
		&positionArgs->minimum_layer_height,
		&positionArgs->g90_influences_extruder,
		&pXYZAxisDefaultMode,
		&pEAxisDefaultMode,
		&pUnitsDefault,
		&poLocationDetectionCommands
	))
	{
		std::string message = "GcodePositionProcessor.ParseInitializationArgs failed: unable to parse parameters.";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}
	Py_INCREF(poLocationDetectionCommands);

	positionArgs->key = pKey;
	positionArgs->autodetect_position = iAutoDetectPosition;
	positionArgs->origin_x_none = iOriginXIsNone > 0;
	positionArgs->origin_y_none = iOriginYIsNone > 0;
	positionArgs->origin_z_none = iOriginZIsNone > 0;
	positionArgs->xyz_axis_default_mode = pXYZAxisDefaultMode;
	positionArgs->e_axis_default_mode = pEAxisDefaultMode;
	positionArgs->units_default = pUnitsDefault;

	// Extract the elements from  the location detection command list pyobject
	int listSize = PyList_Size(poLocationDetectionCommands);
	if (listSize < 0)
	{
		std::string message = "Unable to build position arguments, LocationDetectionCommands is not a list.";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}

	for (int index = 0; index < listSize; index++) {
		PyObject *pyListItem = PyList_GetItem(poLocationDetectionCommands, index);
		if (pyListItem == NULL)
		{
			std::string message = "Could not extract a list item from index from the location detection commands.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return false;
		}
		Py_INCREF(pyListItem);
		if (!PyUnicode_SafeCheck(pyListItem)) {
			std::string message = "An element in the location_detection_commands is not a unicode string.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return false;
		}
		std::string command = PyUnicode_SafeAsString(pyListItem);
		
		positionArgs->location_detection_commands.push_back(command);
		Py_DECREF(pyListItem);
	}
	Py_DECREF(poLocationDetectionCommands);
	return true;
}

static bool ParsePositionArgs(PyObject *args, gcode_position_args *positionArgs)
{
	//PyObject_Print(args, stdout, Py_PRINT_RAW);

	PyObject* pyLocationDetectionCommands; // Hold the PyList
	char* pXYZAxisDefaultMode;
	char* pEAxisDefaultMode;
	char* pUnitsDefault;
	long iAutoDetectPosition;
	long iOriginXIsNone;
	long iOriginYIsNone;
	long iOriginZIsNone;
	if (!PyArg_ParseTuple(
		args, "ldldldlddddlsssO",
		&iAutoDetectPosition,
		&positionArgs->origin_x,
		&iOriginXIsNone,
		&positionArgs->origin_y,
		&iOriginYIsNone,
		&positionArgs->origin_z,
		&iOriginZIsNone,
		&positionArgs->retraction_length,
		&positionArgs->z_lift_height,
		&positionArgs->priming_height,
		&positionArgs->minimum_layer_height,
		&positionArgs->g90_influences_extruder,
		&pXYZAxisDefaultMode,
		&pEAxisDefaultMode,
		&pUnitsDefault,
		&pyLocationDetectionCommands
	))
	{
		std::string message = "GcodePositionProcessor.ParsePositionArgs failed: unable to parse parameters.";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}
	Py_INCREF(pyLocationDetectionCommands);
	positionArgs->autodetect_position = iAutoDetectPosition;
	positionArgs->origin_x_none = iOriginXIsNone > 0;
	positionArgs->origin_y_none = iOriginYIsNone > 0;
	positionArgs->origin_z_none = iOriginZIsNone > 0;
	positionArgs->xyz_axis_default_mode = pXYZAxisDefaultMode;
	positionArgs->e_axis_default_mode = pEAxisDefaultMode;
	positionArgs->units_default = pUnitsDefault;

	// Extract the elements from  the location detection command list pyobject
	int listSize = PyList_Size(pyLocationDetectionCommands);
	if (listSize < 0)
	{
		std::string message = "Unable to build position arguments, LocationDetectionCommands is not a list.";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}

	for (int index = 0; index < listSize; index++) {
		PyObject *pyListItem = PyList_GetItem(pyLocationDetectionCommands, index);
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
		positionArgs->location_detection_commands.push_back(command);
	}
	Py_DECREF(pyLocationDetectionCommands);
	return true;
}

static bool ParseStabilizationArgs(PyObject *args, stabilization_args* stabilizationArgs)
{
	PyObject * pyPositionArgs; // Hold the position args

	PyObject* pyStabilizationType;
	int iDisableRetraction;
	int iDisableZLift;
	int iIsBound;
	int iFastestSpeed;
	if (!PyArg_ParseTuple(
		args,
		"OiddddddUiididdd",
		&pyPositionArgs,
		&iIsBound,
		&stabilizationArgs->x_min,
		&stabilizationArgs->x_max,
		&stabilizationArgs->y_min,
		&stabilizationArgs->y_max,
		&stabilizationArgs->z_min,
		&stabilizationArgs->z_max,
		&pyStabilizationType,
		&iFastestSpeed,
		&iDisableRetraction,
		&stabilizationArgs->retraction_length,
		&iDisableZLift,
		&stabilizationArgs->z_lift_height,
		&stabilizationArgs->height_increment,
		&stabilizationArgs->notification_period_seconds))
	{
		std::string message = "GcodePositionProcessor.ParseStabilizationArgs failed: unable to parse parameters.";
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return false;
	}
	Py_INCREF(pyPositionArgs);
	Py_INCREF(pyStabilizationType);
	stabilizationArgs->fastest_speed = iFastestSpeed > 0;
	stabilizationArgs->is_bound = iIsBound > 0;
	stabilizationArgs->disable_retract = iDisableRetraction > 0;
	stabilizationArgs->disable_z_lift = iDisableZLift > 0;
	stabilizationArgs->stabilization_type = PyUnicode_SafeAsString(pyStabilizationType);
	gcode_position_args position_args;
	if (!ParsePositionArgs(pyPositionArgs, &position_args))
		return false;
	Py_DECREF(pyPositionArgs);
	Py_DECREF(pyStabilizationType);
	stabilizationArgs->position_args = position_args;
	return true;
}

