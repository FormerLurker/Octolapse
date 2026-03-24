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

#ifndef GcodePositionProcessor_H
#define GcodePositionProcessor_H
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif
#include <string>
#include "gcode_position.h"
#include "gcode_parser.h"
#include "stabilization.h"
#include "stabilization_smart_layer.h"
#include "stabilization_smart_gcode.h"

namespace gpp
{
	static std::map<std::string, gcode_position*> gcode_positions;
	static gcode_parser* parser;
}

extern "C" {

	PyMODINIT_FUNC PyInit_GcodePositionProcessor(void);

	static PyObject* Initialize(PyObject* self, PyObject* args);
	static PyObject* Undo(PyObject* self, PyObject* args);
	static PyObject* Update(PyObject* self, PyObject* args);
	static PyObject* UpdatePosition(PyObject* self, PyObject* args);
	static PyObject* Parse(PyObject* self, PyObject* args);
	static PyObject* GetCurrentPositionTuple(PyObject* self, PyObject* args);
	static PyObject* GetCurrentPositionDict(PyObject* self, PyObject* args);
	static PyObject* GetPreviousPositionTuple(PyObject* self, PyObject* args);
	static PyObject* GetPreviousPositionDict(PyObject* self, PyObject* args);
	static PyObject* GetSnapshotPlans_SmartLayer(PyObject* self, PyObject* args);
	static PyObject* GetSnapshotPlans_SmartGcode(PyObject* self, PyObject* args);
}

static bool ParsePositionArgs(PyObject* py_args, gcode_position_args* args);
static bool ParseStabilizationArgs(PyObject* py_args, stabilization_args* args, PyObject** p_py_progress_callback,
	PyObject** p_py_snapshot_position_callback);
static bool ParseStabilizationArgs_SmartLayer(PyObject* py_args, smart_layer_args* args);
static bool ParseStabilizationArgs_SmartGcode(PyObject* py_args, smart_gcode_args* args);
static bool ExecuteStabilizationProgressCallback(PyObject* progress_callback, const double percent_complete,
	const double seconds_elapsed, const double estimated_seconds_remaining,
	const int gcodes_processed, const int lines_processed);
static bool ExecuteGetSnapshotPositionCallback(PyObject* py_get_snapshot_position_callback, double x_initial,
	double y_initial, double& x_result, double& y_result);
#endif
