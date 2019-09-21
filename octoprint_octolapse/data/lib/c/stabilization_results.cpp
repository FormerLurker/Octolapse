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
#include "stabilization_results.h"
#include "logging.h"
stabilization_results::stabilization_results()
{
	bool success = false;
	double seconds_elapsed = 0;
	long gcodes_processed = 0;
	long lines_processed = 0;
}

PyObject* stabilization_results::to_py_object()
{
	PyObject * py_snapshot_plans = snapshot_plan::build_py_object(snapshot_plans);
	if (py_snapshot_plans == NULL)
	{
		//octolapse_log(SNAPSHOT_PLAN, ERROR, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Snapshot_plan::build_py_object returned Null");
		//PyErr_SetString(PyExc_ValueError, "GcodePositionProcessor.ExecuteStabilizationCompleteCallback - Snapshot_plan::build_py_object returned Null - Terminating");
		return NULL;
	}
	PyObject * py_results = Py_BuildValue("(l,s,O,d,l,l,s)", success, errors.c_str(), py_snapshot_plans, seconds_elapsed, gcodes_processed, lines_processed, quality_issues.c_str());
	if (py_results == NULL)
	{
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::ERROR, "Unable to create a Tuple from the snapshot plan list.");
		PyErr_SetString(PyExc_ValueError, "stabilization_results.ExecuteStabilizationCompleteCallback - Error building callback arguments - Terminating");
		return NULL;
	}
	// Bring the snapshot plan refcount to 1
	Py_DECREF(py_snapshot_plans);

	return py_results;
}

