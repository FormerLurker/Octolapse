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
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
#include <string>
#include "gcode_position.h"
#include "gcode_parser.h"
#include "stabilization.h"
#include "stabilization_snap_to_print.h"
#include "stabilization_minimize_travel.h"
namespace gpp {
	static std::map<std::string, gcode_position*> gcode_positions;
	static gcode_parser* parser;
}

extern "C"
{
#if PY_MAJOR_VERSION >= 3
	PyMODINIT_FUNC PyInit_GcodePositionProcessor(void);
#else
	extern "C" void initGcodePositionProcessor(void);
#endif
	static PyObject* Initialize(PyObject* self, PyObject *args);
	static PyObject* Undo(PyObject* self, PyObject *args);
	static PyObject* Update(PyObject* self, PyObject *args);
	static PyObject* UpdatePosition(PyObject* self, PyObject *args);
	static PyObject* Parse(PyObject* self, PyObject *args);
	static PyObject* GetCurrentPositionTuple(PyObject* self, PyObject *args);
	static PyObject* GetCurrentPositionDict(PyObject* self, PyObject *args);
	static PyObject* GetPreviousPositionTuple(PyObject* self, PyObject *args);
	static PyObject* GetPreviousPositionDict(PyObject* self, PyObject *args);
	static PyObject * GetSnapshotPlans_SnapToPrint(PyObject *self, PyObject *args);
	static PyObject * GetSnapshotPlans_MinimizeTravel(PyObject *self, PyObject *args);
}
static bool ParseInitializationArgs(PyObject *args, gcode_position_args *positionArgs);
static bool ParsePositionArgs(PyObject *args, gcode_position_args *positionArgs);
static bool ParseStabilizationArgs(PyObject *args, stabilization_args* stabilizationArgs);
static bool ParseStabilizationArgs_SnapToPrint(PyObject *args, snap_to_print_args* snapToPrintArgs);
static bool ParseStabilizationArgs_MinimizeTravel(PyObject *args, minimize_travel_args* stabilizationArgs);
static bool ExecuteStabilizationProgressCallback(PyObject* progress_callback, const double percent_complete, const double seconds_elapsed, const double estimated_seconds_remaining, const long gcodes_processed, const long lines_processed);
static bool ExecuteGetSnapshotPositionCallback(PyObject* py_get_snapshot_position_callback, double x_initial, double y_initial, double* x_result, double* y_result);
#endif

