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
	p_x_ = NULL;
	p_y_ = NULL;
	p_z_ = NULL;
	p_e_ = NULL;
	p_f_ = NULL;
	action_ = "";
}

snapshot_plan_step::snapshot_plan_step(const snapshot_plan_step & source)
{
	if (source.p_x_ != NULL)
	{
		p_x_ = new double;
		*p_x_ = *source.p_x_;
	}
	else
	{
		p_x_ = NULL;
	}

	if (source.p_y_ != NULL)
	{
		p_y_ = new double;
		*p_y_ = *source.p_y_;
	}
	else
	{
		p_y_ = NULL;
	}


	if (source.p_z_ != NULL)
	{
		p_z_ = new double;
		*p_z_ = *source.p_z_;
	}
	else
	{
		p_z_ = NULL;
	}

	if (source.p_e_ != NULL)
	{
		p_e_ = new double;
		*p_e_ = *source.p_e_;
	}
	else
	{
		p_e_ = NULL;
	}

	if (source.p_f_ != NULL)
	{
		p_f_ = new double;
		*p_f_ = *source.p_f_;
	}
	else
	{
		p_f_ = NULL;
	}

	action_ = source.action_;
}
snapshot_plan_step::snapshot_plan_step(double* x, double* y, double* z, double* e, double* f, std::string action) 
{
	if (x != NULL)
	{
		p_x_ = new double;
		*p_x_ = *x;
	}
	else
	{
		p_x_ = NULL;
	}

	if (y != NULL)
	{
		p_y_ = new double;
		*p_y_ = *y;
	}
	else
	{
		p_y_ = NULL;
	}


	if (z != NULL)
	{
		p_z_ = new double;
		*p_z_ = *z;
	}
	else
	{
		p_z_ = NULL;
	}

	if (e != NULL)
	{
		p_e_ = new double;
		*p_e_ = *e;
	}
	else
	{
		p_e_ = NULL;
	}

	if (f != NULL)
	{
		p_f_ = new double;
		*p_f_ = *f;
	}
	else
	{
		p_f_ = NULL;
	}

	action_ = action;
}

snapshot_plan_step::~snapshot_plan_step()
{
	if (p_x_ != NULL)
	{
		delete p_x_;
		p_x_ = NULL;
	}
	if(p_y_ != NULL)
	{
		delete p_y_;
		p_y_ = NULL;
	}
	if (p_z_ != NULL)
	{
		delete p_z_;
		p_z_ = NULL;
	}
	if (p_e_ != NULL)
	{
		delete p_e_;
		p_e_ = NULL;
	}
	if (p_f_ != NULL)
	{
		delete p_f_;
		p_f_ = NULL;
	}
	
}

PyObject * snapshot_plan_step::to_py_object()
{
	PyObject * py_x;
	if(p_x_ == NULL)
	{
		py_x = Py_None;
		Py_IncRef(Py_None);
	}
	else
	{
		py_x = PyFloat_FromDouble(*p_x_);
	}
	if (py_x == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to convert the X value to a python object.");
		return NULL;
	}
	
	PyObject * py_y;
	if (p_y_ == NULL)
	{
		py_y = Py_None;
		Py_IncRef(Py_None);
	}
	else
	{
		py_y = PyFloat_FromDouble(*p_y_);
	}
	if (py_y == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to convert the Y value to a python object.");
		return NULL;
	}

	PyObject * py_z;
	if (p_z_ == NULL)
	{
		py_z = Py_None;
		Py_IncRef(Py_None);
	}
	else
	{
		py_z = PyFloat_FromDouble(*p_z_);
	}
	if (py_z == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to convert the Z value to a python object.");
		return NULL;
	}

	PyObject * py_e;
	if (p_e_ == NULL)
	{
		py_e = Py_None;
		Py_IncRef(Py_None);
	}
	else
	{
		py_e = PyFloat_FromDouble(*p_e_);
	}
	if (py_e == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to convert the E value to a python object.");
		return NULL;
	}

	PyObject * py_f;
	if (p_f_ == NULL)
	{
		py_f = Py_None;
		Py_IncRef(Py_None);
	}
	else
	{
		py_f = PyFloat_FromDouble(*p_f_);
	}
	if (py_f == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to convert the F value to a python object.");
		return NULL;
	}

	PyObject * py_step = Py_BuildValue("sOOOOO", action_.c_str(), py_x, py_y, py_z, py_e, py_f);
	if (py_step == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlanStep.to_py_object: Unable to create the snapshot plan step PyObject.");
		return NULL;
	}
	Py_DecRef(py_x);
	Py_DecRef(py_y);
	Py_DecRef(py_z);
	Py_DecRef(py_e);
	Py_DecRef(py_f);
	return py_step;
}