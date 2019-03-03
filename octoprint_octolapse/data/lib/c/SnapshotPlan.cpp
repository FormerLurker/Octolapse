///////////////////////////////////////////////////////////////////////////////////
// Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
// Copyright(C) 2019  Brad Hochgesang
///////////////////////////////////////////////////////////////////////////////////
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
///////////////////////////////////////////////////////////////////////////////////
#include "SnapshotPlan.h"
#include <iostream>

snapshot_plan::snapshot_plan()
{
	file_line = 0;
	file_gcode_number = 0;
	p_initial_position = NULL;
	p_return_position = NULL;
	p_parsed_command = NULL;
	send_parsed_command = "";
	lift_amount = 0;
	retract_amount = 0;
}

snapshot_plan::snapshot_plan(const snapshot_plan & source)
{
	file_line = source.file_line;
	file_gcode_number = source.file_gcode_number;
	p_initial_position = new position(*source.p_initial_position);
	
	for (unsigned int index=0; index < source.snapshot_positions.size(); index++)
	{
		snapshot_positions.push_back(new position(*source.snapshot_positions[index]));
	}
	
	for (unsigned int index = 0; index < source.steps.size(); index++)
	{
		steps.push_back(new snapshot_plan_step(*source.steps[index]));
	}

	p_return_position = new position(*source.p_return_position);
	p_parsed_command = new parsed_command(*source.p_parsed_command);
	send_parsed_command = source.send_parsed_command;
	lift_amount = source.lift_amount;
	retract_amount = source.retract_amount;
}

snapshot_plan::~snapshot_plan()
{
	if (p_initial_position != NULL)
		delete p_initial_position;
	if (p_return_position != NULL)
		delete p_return_position;
	if (p_parsed_command != NULL)
		delete p_parsed_command;

	for (unsigned int index = 0; index < snapshot_positions.size(); index++)
		delete snapshot_positions[index];

	snapshot_positions.clear();
	
	for (unsigned int index = 0; index < steps.size(); index++)
		delete steps[index];
	steps.clear();
		
}

PyObject * snapshot_plan::build_py_object(std::vector<snapshot_plan *>* p_plans)
{
	PyObject *py_snapshot_plans = PyList_New(0);
	if (py_snapshot_plans == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing BuildSnapshotPlansPyObject: Unable to create SnapshotPlans PyList object.");
		return NULL;
	}
	
	// Create each snapshot plan
	for (unsigned int plan_index = 0; plan_index < (*p_plans).size(); plan_index++)
	{
		PyObject * py_snapshot_plan = (*p_plans)[plan_index]->to_py_object();
		bool success = !(PyList_Append(py_snapshot_plans, py_snapshot_plan) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing BuildSnapshotPlansPyObject: Unable to append the snapshot plan to the snapshot plan list.");
			return NULL;
		}
		//Py_DECREF(py_snapshot_plan);
	}
	return py_snapshot_plans;
}

PyObject * snapshot_plan::to_py_object()
{
	
	PyObject *py_snapshot_positions = PyList_New(0);
	if (py_snapshot_positions == NULL)
	{
		return NULL;
	}
	
	for (unsigned int index = 0; index < snapshot_positions.size(); index++)
	{
		PyObject * py_snapshot_position = snapshot_positions[index]->to_py_tuple();
		if (py_snapshot_position == NULL)
		{
			return NULL;
		}
		bool success = !(PyList_Append(py_snapshot_positions, py_snapshot_position) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing BuildSnapshotPlansPyObject: Unable to append the snapshot position to the snapshot position list.");
			return NULL;
		}
		//Py_DECREF(py_snapshot_position);
		
	}
	PyObject * py_initial_position = p_initial_position->to_py_tuple();
	if (py_initial_position == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing BuildSnapshotPlansPyObject: Unable to create InitialPosition PyObject.");
		return NULL;
	}
	PyObject * py_return_position = p_return_position->to_py_tuple();
	if (py_return_position == NULL)
	{
		return NULL;
	}
	PyObject * py_steps = PyList_New(0);
	if (py_steps == NULL)
	{
		return NULL;
	}
	for (unsigned int step_index = 0; step_index < steps.size(); step_index++)
	{
		
		// create the snapshot step object with build
		PyObject * py_step = steps[step_index]->to_py_object();
		if (py_step == NULL)
		{
			return NULL;
		}
		bool success = !(PyList_Append(py_steps, py_step) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing BuildSnapshotPlansPyObject: Unable to append the snapshot plan step to the snapshot plan step list.");
			return NULL;
		}
		//Py_DECREF(py_step);
		
	}
	PyObject* py_parsed_command = p_parsed_command->to_py_object();
	if (py_parsed_command == NULL)
	{
		return NULL;
	}
	PyObject *py_snapshot_plan = Py_BuildValue(
		"llOOOOOsdd",
		file_line,
		file_gcode_number,
		py_initial_position,
		py_snapshot_positions,
		py_return_position,
		py_steps,
		py_parsed_command,
		send_parsed_command.c_str(),
		lift_amount,
		retract_amount
	);
	if (py_snapshot_plan == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing BuildSnapshotPlansPyObject: Unable to create SnapshotPlan PyObject.");
		return NULL;
	}

	//Py_DECREF(py_initial_position);
	//Py_DECREF(py_snapshot_positions);
	//Py_DECREF(py_return_position);
	//Py_DECREF(py_steps);
	//Py_DECREF(py_parsed_command);
	//Py_DECREF(py_snapshot_plan);
	return py_snapshot_plan;
}
