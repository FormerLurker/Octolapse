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
#include "snapshot_plan.h"
#include <iostream>

snapshot_plan::snapshot_plan()
{
	file_line_ = 0;
	file_gcode_number_ = 0;
	p_initial_position_ = NULL;
	p_return_position_ = NULL;
	p_parsed_command_ = NULL;
	send_parsed_command_ = "";
	lift_amount_ = 0;
	retract_amount_ = 0;
}

snapshot_plan::snapshot_plan(const snapshot_plan & source)
{
	file_line_ = source.file_line_;
	file_gcode_number_ = source.file_gcode_number_;
	p_initial_position_ = new position(*source.p_initial_position_);
	
	for (unsigned int index=0; index < source.snapshot_positions_.size(); index++)
	{
		snapshot_positions_.push_back(new position(*source.snapshot_positions_[index]));
	}
	
	for (unsigned int index = 0; index < source.steps_.size(); index++)
	{
		steps_.push_back(new snapshot_plan_step(*source.steps_[index]));
	}

	p_return_position_ = new position(*source.p_return_position_);
	p_parsed_command_ = new parsed_command(*source.p_parsed_command_);
	send_parsed_command_ = source.send_parsed_command_;
	lift_amount_ = source.lift_amount_;
	retract_amount_ = source.retract_amount_;
}

snapshot_plan::~snapshot_plan()
{
	if (p_initial_position_ != NULL)
	{
		delete p_initial_position_;
		p_initial_position_ = NULL;
	}
	if (p_return_position_ != NULL)
	{
		delete p_return_position_;
		p_return_position_ = NULL;
	}
	if (p_parsed_command_ != NULL)
	{
		delete p_parsed_command_;
		p_parsed_command_ = NULL;
	}
	while (!snapshot_positions_.empty()) {
		position * p = snapshot_positions_.back();
		snapshot_positions_.pop_back();
		delete p;
	}
	
	while (!steps_.empty()) {
		snapshot_plan_step * p = steps_.back();
		steps_.pop_back();
		delete p;
	}
	
		
}

PyObject * snapshot_plan::build_py_object(std::vector<snapshot_plan *> p_plans)
{
	PyObject *py_snapshot_plans = PyList_New(0);
	if (py_snapshot_plans == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.build_py_object: Unable to create SnapshotPlans PyList object.");
		return NULL;
	}
	
	// Create each snapshot plan
	for (unsigned int plan_index = 0; plan_index < p_plans.size(); plan_index++)
	{
		PyObject * py_snapshot_plan = p_plans[plan_index]->to_py_object();
		if (py_snapshot_plan == NULL)
		{
			//PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.build_py_object: Unable to convert the snapshot plan to a PyObject.");
			return NULL;
		}
		bool success = !(PyList_Append(py_snapshot_plans, py_snapshot_plan) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.build_py_object: Unable to append the snapshot plan to the snapshot plan list.");
			return NULL;
		}
		// Need to decref after PyList_Append, since it increfs the PyObject
		// Todo: evaluate the effect of this  
		Py_DECREF(py_snapshot_plan);
		//std::cout << "py_snapshot_plan refcount = " << py_snapshot_plan->ob_refcnt << "\r\n";
	}
	
	return py_snapshot_plans;
}

PyObject * snapshot_plan::to_py_object()
{
	
	PyObject *py_snapshot_positions = PyList_New(0);
	if (py_snapshot_positions == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to create a PyList object to hold the snapshot positions.");
		return NULL;
	}
	
	for (unsigned int index = 0; index < snapshot_positions_.size(); index++)
	{
		PyObject * py_snapshot_position = snapshot_positions_[index]->to_py_tuple();
		if (py_snapshot_position == NULL)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to convert a snapshot position to a PyObject.");
			return NULL;
		}
		bool success = !(PyList_Append(py_snapshot_positions, py_snapshot_position) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to append the snapshot position to the snapshot position list.");
			return NULL;
		}
		// Need to decref after PyList_Append, since it increfs the PyObject
		Py_DECREF(py_snapshot_position);
		// Todo: evaluate the effect of this 
		//std::cout << "py_snapshot_position refcount = " << py_snapshot_position->ob_refcnt << "\r\n";
	}
	PyObject * py_initial_position = p_initial_position_->to_py_tuple();
	if (py_initial_position == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to create InitialPosition PyObject.");
		return NULL;
	}
	PyObject * py_return_position = p_return_position_->to_py_tuple();
	if (py_return_position == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to convert the return position to a tuple.");
		return NULL;
	}
	PyObject * py_steps = PyList_New(0);
	if (py_steps == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to create a PyList object to hold the snapshot plan steps.");
		return NULL;
	}
	for (unsigned int step_index = 0; step_index < steps_.size(); step_index++)
	{
		
		// create the snapshot step object with build
		PyObject * py_step = steps_[step_index]->to_py_object();
		if (py_step == NULL)
		{
			return NULL;
		}
		bool success = !(PyList_Append(py_steps, py_step) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to append the snapshot plan step to the snapshot plan step list.");
			return NULL;
		}
		// Need to decref after PyList_Append, since it increfs the PyObject
		// Todo: evaluate the effect of this 
		Py_DECREF(py_step);
		//std::cout << "py_step refcount = " << py_step->ob_refcnt << "\r\n";

	}
	PyObject* py_parsed_command = p_parsed_command_->to_py_object();
	if (py_parsed_command == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to convert the parsed_command to a PyObject.");
		return NULL;
	}
	PyObject *py_snapshot_plan = Py_BuildValue(
		"llOOOOOsdd",
		file_line_,
		file_gcode_number_,
		py_initial_position,
		py_snapshot_positions,
		py_return_position,
		py_steps,
		py_parsed_command,
		send_parsed_command_.c_str(),
		lift_amount_,
		retract_amount_
	);
	if (py_snapshot_plan == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing SnapshotPlan.to_py_object: Unable to create SnapshotPlan PyObject.");
		return NULL;
	}
	// Py_BuildValue Increfs PyObjects, so we need to decref those here:
	// Todo: evaluate the effect of this 
	Py_DECREF(py_initial_position);
	//std::cout << "py_initial_position refcount = " << py_initial_position->ob_refcnt << "\r\n";
	// Todo: evaluate the effect of this 
	Py_DECREF(py_snapshot_positions);
	//std::cout << "py_snapshot_positions refcount = " << py_snapshot_positions->ob_refcnt << "\r\n";
	// Todo: evaluate the effect of this 
	Py_DECREF(py_return_position);
	//std::cout << "py_return_position refcount = " << py_return_position->ob_refcnt << "\r\n";
	// Todo: evaluate the effect of this 
	Py_DECREF(py_steps);
	//std::cout << "py_steps refcount = " << py_steps->ob_refcnt << "\r\n";
	// Todo: evaluate the effect of this 
	Py_DECREF(py_parsed_command);
	//std::cout << "py_parsed_command refcount = " << py_parsed_command->ob_refcnt << "\r\n";
	
	return py_snapshot_plan;
}