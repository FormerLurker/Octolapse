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
/*
int main(int argc, char *argv[])
{
	Py_SetProgramName(argv[0]);
	//initGcodePositionProcessor();
	return 0;
}*/
static PyMethodDef GcodePositionProcessorMethods[] = {
	{ "Initialize", (PyCFunction)Initialize,  METH_VARARGS  ,"Initialize the internal shared position processor." },
{ "Undo",  (PyCFunction)Undo,  METH_VARARGS  ,"Undo an update made to the current position.  You can only undo once." },
{ "Update",  (PyCFunction)Update,  METH_VARARGS  ,"Undo an update made to the current position.  You can only undo once." },
{ "Parse",  (PyCFunction)Parse,  METH_VARARGS  ,"Parse gcode text into a ParsedCommand." },
{ "GetCurrentPositionTuple",  (PyCFunction)GetCurrentPositionTuple,  METH_NOARGS  ,"Returns the current position of the global GcodePosition tracker in a faster but harder to handle tuple form." },
{ "GetCurrentPositionDict",  (PyCFunction)GetCurrentPositionDict,  METH_NOARGS  ,"Returns the current position of the global GcodePosition tracker in a slower but easier to deal with dict form." },
{ "GetPreviousPositionTuple",  (PyCFunction)GetPreviousPositionTuple,  METH_NOARGS  ,"Returns the previous position of the global GcodePosition tracker in a faster but harder to handle tuple form." },
{ "GetPreviousPositionDict",  (PyCFunction)GetPreviousPositionDict,  METH_NOARGS  ,"Returns the previous position of the global GcodePosition tracker in a slower but easier to deal with dict form." },
{ "Reset",  (PyCFunction)Reset,  METH_VARARGS  ,"Reset the current position, optionally from a supplied position." },
{ "GetSnapshotPlans_LockToPrint", (PyCFunction)GetSnapshotPlans_LockToPrint, METH_VARARGS, "Parses a gcode file and returns snapshot plans for a 'SnapToPrint' stabilization." },

{ NULL, NULL, 0, NULL }
};

extern "C"
{
	void initGcodePositionProcessor(void)
	{
		std::cout << "Initializing GcodePositionProcessor V1.0.0 - Copyright (C) 2019  Brad Hochgesang...";
		Py_Initialize();
		PyEval_InitThreads();

		PyObject *m = Py_InitModule("GcodePositionProcessor", GcodePositionProcessorMethods);
		gpp::position = NULL;
		gpp::parser = new gcode_parser();

		std::cout << "complete\r\n";
	}

	PyObject * GetSnapshotPlans_LockToPrint(PyObject *self, PyObject *args)
	{
		PyObject *p_stabilization_args;
		PyObject *p_progress_callback;
		char * file_path;
		char * nearest_to_corner;

		int iFavorXAxis;
		if (!PyArg_ParseTuple(
			args,
			"sOOsi",
			&file_path,
			&p_stabilization_args,
			&p_progress_callback,
			&nearest_to_corner,
			&iFavorXAxis))
		{
			PyErr_SetString(PyExc_ValueError, "Error parsing parameters for GetSnapshotPlansLockToPrint.");
			return NULL;
		}
		// get the progress callback
		if (!PyCallable_Check(p_progress_callback)) {
			PyErr_SetString(PyExc_TypeError, "parameter must be callable");
			return NULL;
		}
		// Extract the stabilization args
		stabilization_args s_args;
		if (!ParseStabilizationArgs(p_stabilization_args, &s_args))
		{
			return NULL;
		}
		//Py_DECREF(p_stabilization_args);

		const bool favor_x_axis = iFavorXAxis > 0;
		// Create our stabilization object
		StabilizationSnapToPrint* p_stabilization = new StabilizationSnapToPrint(&s_args,
			pythonProgressCallback(ExecuteStabilizationProgressCallback),
			p_progress_callback,
			nearest_to_corner,
			favor_x_axis);

		stabilization_results* results = p_stabilization->process_file(file_path);
		/*snapshot_plan * p_plan1 = results.snapshot_plans[0];
		PyObject * py_test_return = p_plan1->to_py_object();
		return py_test_return;*/

		PyObject * py_snapshot_plans = snapshot_plan::build_py_object(results->p_snapshot_plans);
		if (py_snapshot_plans == NULL)
		{
			PyErr_Print();
			return NULL;
		}
		PyObject * py_results = Py_BuildValue("(l,s,O,d,l,l)", results->success, results->errors.c_str(), py_snapshot_plans, results->seconds_elapsed, results->gcodes_processed, results->lines_processed);
		if (py_results == NULL)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Error building callback arguments - Terminating");
			return NULL;
		}

		PyGILState_STATE state = PyGILState_Ensure();
		//Py_DECREF(py_snapshot_plans);
		//Py_DECREF(p_progress_callback);
		delete p_stabilization;
		delete results;
		PyGILState_Release(state);

		return py_results;
	}
	static PyObject* Initialize(PyObject* self, PyObject *args)
	{
		position_args positionArgs;

		if (!ParsePositionArgs(args, &positionArgs))
		{
			return NULL; // The call failed, ParsePositionArgs has taken care of the error message
		}

		// Create the parser object (only done once, not redone in Reset()
		gpp::position = new gcode_position(positionArgs);
		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Reset(PyObject* self, PyObject *args)
	{
		position_args positionArgs;
		if (!ParsePositionArgs(args, &positionArgs))
			return NULL; // The call failed, ParsePositionArgs has taken care of the error message
						 // Create the position object

		delete gpp::position;
		gpp::position = new gcode_position(positionArgs);
		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Undo(PyObject* self, PyObject *args)
	{
		gpp::position->undo_update();
		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Update(PyObject* self, PyObject *args)
	{
		std::string gcode;
		if (!ParseUpdateArgs(args, &gcode))
		{
			return NULL;
		}
		parsed_command command;
		gpp::parser->parse_gcode(gcode, &command);
		gpp::position->update(&command);

		return Py_BuildValue("O", Py_True);
	}

	static PyObject* Parse(PyObject* self, PyObject *args)
	{
		std::string gcode;
		if (!ParseUpdateArgs(args, &gcode))
		{
			return NULL;
		}
		parsed_command command;
		gpp::parser->parse_gcode(gcode, &command);
		// Convert ParsedCommand to python object
		return command.to_py_object();
	}

	static PyObject* GetCurrentPositionTuple(PyObject* self)
	{
		return gpp::position->p_current_pos->to_py_tuple();
	}
	
	static PyObject* GetCurrentPositionDict(PyObject* self)
	{
		return gpp::position->p_current_pos->to_py_dict();
	}

	static PyObject* GetPreviousPositionTuple(PyObject* self)
	{
		return gpp::position->p_previous_pos->to_py_tuple();
	}

	static PyObject* GetPreviousPositionDict(PyObject* self)
	{
		return gpp::position->p_previous_pos->to_py_dict();
	}
}
static bool ExecuteStabilizationProgressCallback(PyObject* progress_callback, const double percent_complete, const double seconds_elapsed, const double estimated_seconds_remaining, const long gcodes_processed, const long lines_processed)
{
	PyObject * funcArgs = Py_BuildValue("(d,d,d,i,i)", percent_complete, seconds_elapsed, estimated_seconds_remaining, gcodes_processed, lines_processed);
	if (funcArgs == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationProgressCallback - Error building callback arguments - Terminating");
		return false;
	}
	PyGILState_STATE gstate;
	gstate = PyGILState_Ensure();
	PyObject * pContinueProcessing = PyObject_CallObject(progress_callback, funcArgs);
	PyGILState_Release(gstate);

	if (pContinueProcessing == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationProgressCallback - Failed to call python - Terminating");
		return false;
	}
	//Py_DECREF(funcArgs);

	const bool continue_processing = PyInt_AsLong(pContinueProcessing) > 0;
	Py_DECREF(pContinueProcessing);

	// Returns true if not cancelled, false if cancelled.
	std::cout << "Is Cancelled = " << !continue_processing << "\r\n";
	return continue_processing;

}

/// Argument Parsing
static bool ParsePositionArgs(PyObject *args, position_args *positionArgs)
{
	PyObject * poLocationDetectionCommands; // Hold the PyList

	char * pXYZAxisDefaultMode;
	char * pEAxisDefaultMode;
	char * pUnitsDefault;
	int iAutoDetectPosition;
	int iOriginXIsNone;
	int iOriginYIsNone;
	int iOriginZIsNone;
	if (!PyArg_ParseTuple(
		args, "ififififfffisssO",
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
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ParsePositionArgs failed: unable to parse parameters.");
		return false;
	}
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
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Unable to build position arguments, LocationDetectionCommands is not a list.");
		return false;
	}

	for (int index = 0; index < listSize; index++) {
		PyObject *pListItem = PyList_GetItem(poLocationDetectionCommands, index);
		//Py_INCREF(pListItem);
		if (!PyString_Check(pListItem)) {
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, "Argument 13 (location_detection_commands) must be a list of strings.");
			return false;
		}
		std::string command = PyString_AsString(pListItem);
		positionArgs->location_detection_commands.push_back(command);
		//Py_DECREF(pListItem);
	}

	//Py_DECREF(poLocationDetectionCommands);

	return true;
}

static bool ParseStabilizationArgs(PyObject *args, stabilization_args* stabilizationArgs)
{
	PyObject * pPositionArgs; // Hold the position args

	char * pStabilizationType;
	int iDisableRetraction;
	int iDisableZLift;
	int iIsBound;
	if (!PyArg_ParseTuple(
		args,
		"Oiddddddsididdd",
		&pPositionArgs,
		&iIsBound,
		&stabilizationArgs->x_min,
		&stabilizationArgs->x_max,
		&stabilizationArgs->y_min,
		&stabilizationArgs->y_max,
		&stabilizationArgs->z_min,
		&stabilizationArgs->z_max,
		&pStabilizationType,
		&iDisableRetraction,
		&stabilizationArgs->retraction_length,
		&iDisableZLift,
		&stabilizationArgs->z_lift_height,
		&stabilizationArgs->height_increment,
		&stabilizationArgs->notification_period_seconds))
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ParseStabilizationArgs failed: unable to parse parameters.");
		return false;
	}
	stabilizationArgs->is_bound = iIsBound > 0;
	stabilizationArgs->disable_retract = iDisableRetraction > 0;
	stabilizationArgs->disable_z_lift = iDisableZLift > 0;
	stabilizationArgs->stabilization_type = pStabilizationType;
	position_args position_args;
	if (!ParsePositionArgs(pPositionArgs, &position_args))
		return false;
	//Py_DECREF(pPositionArgs);
	stabilizationArgs->position_args = position_args;
	return true;
}

static bool ParseUpdateArgs(PyObject *args, std::string* gcode)
{
	char* gcode_param;
	if (!PyArg_ParseTuple(args, "s", &gcode_param))
	{
		PyErr_SetString(PyExc_ValueError, "Update requires at least one parameter: the gcode string");
		return false;
	}
	(*gcode) = gcode_param;
	return true;
}
