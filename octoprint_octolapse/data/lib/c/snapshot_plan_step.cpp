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
#include "snapshot_plan_step.h"
#include "python_helpers.h"
#include <iostream>
snapshot_plan_step::snapshot_plan_step()
{
	x_ = 0.0;
	y_ = 0.0;
	z_ = 0.0;
	e_ = 0.0;
	f_ = 0.0;
	action_ = "";
}

snapshot_plan_step::snapshot_plan_step(const snapshot_plan_step & source)
{
	x_ = source.x_;
	y_ = source.y_;
	z_ = source.z_;
	e_ = source.e_;
	f_ = source.f_;
	action_ = source.action_;
}
snapshot_plan_step::snapshot_plan_step(double x, double y, double z, double e, double f, std::string action) : x_(x), y_(y), z_(z), e_(e), f_(f), action_(action)
{
}

snapshot_plan_step::~snapshot_plan_step()
{
}

PyObject * snapshot_plan_step::to_py_object()
{
	PyObject * py_step = Py_BuildValue("sddddd", action_.c_str(), x_, y_, z_, e_, f_);
	if (py_step == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to create the snapshot plan step PyObject.");
		return NULL;
	}
	return py_step;
}