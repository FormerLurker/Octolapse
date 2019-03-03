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

#include "StabilizationSnapToPrint.h"
#include <iostream>
#include "GcodePosition.h"

StabilizationSnapToPrint::StabilizationSnapToPrint(
	stabilization_args* args, progressCallback progress, std::string nearest_to_corner, bool favor_x_axis
) : stabilization(args, progress)
{
	nearest_to = nearest_to_corner;
	favor_x = favor_x_axis;
	is_layer_change_wait = false;
	current_layer = 0;
	current_height = 0.0;
	has_saved_position = false;
	saved_position_file_line = 0;
	saved_position_file_gcode_number = 0;
	current_file_position = 0;
	p_saved_position = NULL;
	p_saved_parsed_command = NULL;
}


StabilizationSnapToPrint::StabilizationSnapToPrint(): stabilization()
{
	nearest_to = "front-left";
	favor_x = false;
	is_layer_change_wait = false;
	current_layer = 0;
	current_height = 0.0;
	has_saved_position = false;
	saved_position_file_line = 0;
	saved_position_file_gcode_number = 0;
	current_file_position = 0;
	p_saved_position = NULL;
	p_saved_parsed_command = NULL;
}

StabilizationSnapToPrint::StabilizationSnapToPrint(
	stabilization_args* args, pythonProgressCallback progress, PyObject * python_progress,
	std::string nearest_to_corner, bool favor_x_axis) :stabilization(args, progress, python_progress)
{
	nearest_to = nearest_to_corner;
	favor_x = favor_x_axis;
	is_layer_change_wait = false;
	current_layer = 0;
	current_height = 0.0;
	has_saved_position = false;
	saved_position_file_line = 0;
	saved_position_file_gcode_number = 0;
	current_file_position = 0;
	p_saved_position = NULL;
	p_saved_parsed_command = NULL;
}

StabilizationSnapToPrint::StabilizationSnapToPrint(const StabilizationSnapToPrint &source)
{
	// Private copy constructor, don't copy me!	
}

StabilizationSnapToPrint::~StabilizationSnapToPrint()
{
	if (p_saved_position != NULL)
	{
		delete p_saved_position;
		p_saved_position = NULL;
	}
	if (p_saved_parsed_command != NULL)
	{
		delete p_saved_parsed_command;
		p_saved_parsed_command = NULL;
	}
}

void StabilizationSnapToPrint::process_pos(position* p_current_pos, parsed_command* p_command)
{
 	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change)
	{
		is_layer_change_wait = true;
	}
	if (!p_current_pos->is_extruding)
	{
		return;
	}

	if (is_layer_change_wait && has_saved_position)
	{
		AddSavedPlan();
	}

	// check for errors in position, layer, or height, and make sure we are extruding.
	if (p_current_pos->layer == 0 || p_current_pos->x_null || p_current_pos->y_null || p_current_pos->z_null)
	{
		return;
	}

	if (p_stabilization_args_->height_increment != 0)
	{
		// todo : improve this check, it doesn't need to be done on every command if Z hasn't changed

		double current_increment = p_current_pos->height - current_height;
		if (current_increment < p_stabilization_args_->height_increment)
		{
			return;
		}
	}
	if (IsCloser(p_current_pos))
	{
		// we need to make sure that we copy current_pos, because it's value will change
		// as we update the Position object
		// this was done to substantially increase performance within the position class, which
		// can take a long time to run on slower hardware.
		saved_position_file_line = lines_processed_;
		saved_position_file_gcode_number = gcodes_processed_;
		has_saved_position = true;
		// delete the current saved position and parsed command
		if (p_saved_position != NULL)
		{
			delete p_saved_position;
		}
		if (p_saved_parsed_command != NULL)
		{
			delete p_saved_parsed_command;
		}
		p_saved_position = new position(*p_current_pos);
		p_saved_parsed_command = new parsed_command(*p_command);
	}

}

bool StabilizationSnapToPrint::IsCloser(position * p_position)
{
	// check the bounding box
	if (p_stabilization_args_->is_bound)
	{
		if (
			p_position->x < p_stabilization_args_->x_min ||
			p_position->x > p_stabilization_args_->x_max ||
			p_position->y < p_stabilization_args_->y_min ||
			p_position->y > p_stabilization_args_->y_max ||
			p_position->z < p_stabilization_args_->z_min ||
			p_position->z > p_stabilization_args_->z_max)
		{
			return false;
		}
	}

	// if we have no saved position, this is the closest!
	if (!has_saved_position)
		return true;

	if (nearest_to == FRONT_LEFT)
	{
		if (favor_x)
		{
			if (p_position->x > p_saved_position->x)
				return false;
			else if (p_position->x < p_saved_position->x)
				return true;
			else if (p_position->y < p_saved_position->y)
				return true;
		}
		else
		{
			if (p_position->y > p_saved_position->y)
				return false;
			else if (p_position->y < p_saved_position->y)
				return true;
			else if (p_position->x < p_saved_position->x)
				return true;
		}
	}
	else if (nearest_to == FRONT_RIGHT)
	{
		if (favor_x)
		{
			if (p_position->x < p_saved_position->x)
				return false;
			else if (p_position->x > p_saved_position->x)
				return true;
			else if (p_position->y < p_saved_position->y)
				return true;
		}
		else
		{
			if (p_position->y > p_saved_position->y)
				return false;
			else if (p_position->y < p_saved_position->y)
				return true;
			else if (p_position->x > p_saved_position->x)
				return true;
		}
	}
	else if (nearest_to == BACK_LEFT)
	{
		if (favor_x)
		{
			if (p_position->x > p_saved_position->x)
				return false;
			else if (p_position->x < p_saved_position->x)
				return true;
			else if (p_position->y > p_saved_position->y)
				return true;
		}
		else
		{
			if (p_position->y < p_saved_position->y)
				return false;
			else if (p_position->y > p_saved_position->y)
				return true;
			else if (p_position->x < p_saved_position->x)
				return true;
		}
	}
	else if (nearest_to == BACK_RIGHT)
	{
		if (favor_x)
		{
			if (p_position->x < p_saved_position->x)
				return false;
			else if (p_position->x > p_saved_position->x)
				return true;
			else if (p_position->y > p_saved_position->y)
				return true;
		}
		else
		{
			if (p_position->y < p_saved_position->y)
				return false;
			else if (p_position->y > p_saved_position->y)
				return true;
			else if (p_position->x > p_saved_position->x)
				return true;
		}
	}
	return false;
}

void StabilizationSnapToPrint::AddSavedPlan()
{
	snapshot_plan* p_plan = new snapshot_plan();

	// create the initial position
	p_plan->p_initial_position = new position(*p_saved_position);
	// create the snapshot position (only 1)
	position * p_snapshot_position = new position(*p_saved_position);
	p_plan->snapshot_positions.push_back(p_snapshot_position);
	p_plan->p_return_position = new position(*p_saved_position);
	p_plan->p_parsed_command = new parsed_command(*p_saved_parsed_command);
	
	p_plan->file_line = saved_position_file_line;
	p_plan->file_gcode_number = saved_position_file_gcode_number;
	p_plan->lift_amount = p_stabilization_args_->disable_z_lift ? 0.0 : p_stabilization_args_->z_lift_height;
	p_plan->retract_amount = p_stabilization_args_->disable_retract ? 0.0 : p_stabilization_args_->retraction_length;
	p_plan->send_parsed_command = send_parsed_command_first;
	
	snapshot_plan_step* p_step = new snapshot_plan_step(0,0,0,0,0,snapshot_action);
	p_plan->steps.push_back(p_step);
	
	// Add the plan
	(*p_snapshot_plans).push_back(p_plan);

	current_height = p_saved_position->height;
	current_layer = p_saved_position->layer;
	// set the state for the next layer
	has_saved_position = false;
	saved_position_file_line = 0;
	current_file_position = 0;
	is_layer_change_wait = false;
	delete p_saved_position;
	p_saved_position = NULL;
	delete p_saved_parsed_command;
	p_saved_parsed_command = NULL;
}

void StabilizationSnapToPrint::on_processing_complete()
{
	if (has_saved_position)
	{
		AddSavedPlan();
	}
}

