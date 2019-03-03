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
#include "GcodePosition.h"
#include "GcodeParser.h"
#include "Stabilization.h"

namespace gpp {
	static gcode_position* position;
	static gcode_parser* parser;
}

extern "C"
{
	void initGcodePositionProcessor(void);
	static PyObject* Initialize(PyObject* self, PyObject *args);
	static PyObject* Undo(PyObject* self, PyObject *args);
	static PyObject* Update(PyObject* self, PyObject *args);
	static PyObject* Parse(PyObject* self, PyObject *args);
	static PyObject* GetCurrentPositionTuple(PyObject* self);
	static PyObject* GetCurrentPositionDict(PyObject* self);
	static PyObject* GetPreviousPositionTuple(PyObject* self);
	static PyObject* GetPreviousPositionDict(PyObject* self);
	static PyObject* Reset(PyObject* self, PyObject *args);
	static PyObject * GetSnapshotPlans_LockToPrint(PyObject *self, PyObject *args);
}
static bool ParsePositionArgs(PyObject *args, gcode_position_args* position_args);
static bool ParseUpdateArgs(PyObject *args, std::string*);
static bool ParseStabilizationArgs(PyObject *args, stabilization_args* stabilizationArgs);
static bool ExecuteStabilizationProgressCallback(PyObject* progress_callback, const double percent_complete, const double seconds_elapsed, const double estimated_seconds_remaining, const long gcodes_processed, const long lines_processed);
#endif

