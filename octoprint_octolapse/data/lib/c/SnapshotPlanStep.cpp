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
#include "SnapshotPlanStep.h"

snapshot_plan_step::snapshot_plan_step()
{
	x = 0.0;
	y = 0.0;
	z = 0.0;
	e = 0.0;
	f = 0.0;
	action = "";
}

snapshot_plan_step::snapshot_plan_step(const snapshot_plan_step & source)
{
	x = source.x;
	y = source.y;
	z = source.z;
	e = source.e;
	f = source.f;
	action = source.action;
}
snapshot_plan_step::snapshot_plan_step(double x, double y, double z, double e, double f, std::string action) : x(x), y(y), z(z), e(e), f(f), action(action)
{
}

snapshot_plan_step::~snapshot_plan_step()
{
}

PyObject * snapshot_plan_step::to_py_object()
{
	// create the snapshot step object with build
	PyObject * py_step = Py_BuildValue("sddddd", action.c_str(), x, y, z, e, f);
	if (py_step == NULL)
	{
		return NULL;
	}
	return py_step;
}