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

#include "stabilization_snap_to_print.h"
#include <iostream>
#include "gcode_position.h"
#include "logging.h"

snap_to_print_args::snap_to_print_args()
{
	nearest_to_corner = "back-left";
	favor_x_axis = false;

}
snap_to_print_args::snap_to_print_args(std::string nearest_to, bool favor_x)
{
	nearest_to_corner = nearest_to;
	favor_x_axis = favor_x;

}
snap_to_print_args::~snap_to_print_args()
{

}

stabilization_snap_to_print::stabilization_snap_to_print() : stabilization()
{
	snap_to_print_args_ = NULL;
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	has_saved_position_ = false;
	p_saved_position_ = NULL;
}

stabilization_snap_to_print::stabilization_snap_to_print(
	gcode_position_args* position_args, stabilization_args* stab_args, snap_to_print_args* snap_args, 
	progressCallback progress
) : stabilization(position_args, stab_args, progress)
{
	snap_to_print_args_ = snap_args;
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	has_saved_position_ = false;
	p_saved_position_ = NULL;
}

stabilization_snap_to_print::stabilization_snap_to_print(
	gcode_position_args* position_args, stabilization_args* stab_args, snap_to_print_args* snap_args, 
	pythonProgressCallback progress
) :stabilization(position_args, stab_args, progress)
{
	snap_to_print_args_ = snap_args;
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	has_saved_position_ = false;
	p_saved_position_ = NULL;
}

stabilization_snap_to_print::stabilization_snap_to_print(const stabilization_snap_to_print &source)
{
	// Private copy constructor, don't copy me!	
}

stabilization_snap_to_print::~stabilization_snap_to_print()
{
	if (p_saved_position_ != NULL)
	{
		delete p_saved_position_;
		p_saved_position_ = NULL;
	}
}

void stabilization_snap_to_print::process_pos(position* p_current_pos, position* p_previous_pos)
{
	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change_ && p_current_pos->layer_ > 1)
	{
		is_layer_change_wait_ = true;
	}

	if (!p_current_pos->is_extruding_ || !p_current_pos->has_xy_position_changed_ || p_current_pos->gcode_ignored_)
	{
		return;
	}

	if (is_layer_change_wait_ && has_saved_position_)
	{
		if (p_stabilization_args_->height_increment_ != 0)
		{
			// todo : improve this check, it doesn't need to be done on every command if Z hasn't changed
			const double increment_double = p_current_pos->last_extrusion_height_ / p_stabilization_args_->height_increment_;
			unsigned const int increment = gcode_position::round_up_to_int(increment_double);
			std::cout << "Last Increment: " << current_height_increment_ << " Current Increment double" << increment_double << " Current Increment int:" << increment;
			if (increment > current_height_increment_)
			{
				if (increment > 1 && has_saved_position_)
				{
					current_height_increment_ = increment;
					add_saved_plan();
				}
				else
				{
					octolapse_log(octolapse_loggers::SNAPSHOT_PLAN, octolapse_log_levels::WARNING, "Octolapse missed a layer while creating a snapshot plan due to a height restriction.");
				}
			}
		}
		else
		{
			add_saved_plan();
		}
		
	}

	// check for errors in position, layer, or height, and make sure we are extruding.
	if (p_current_pos->layer_ == 0 || p_current_pos->x_null_ || p_current_pos->y_null_ || p_current_pos->z_null_)
	{
		return;
	}

	// Is the endpoint of the current command closer
	// Note that we need to save the position immediately
	// so that the IsCloser check for the previous_pos will
	// have a saved command to check.
	if (is_closer(p_current_pos))
	{
		has_saved_position_ = true;
		// delete the current saved position and parsed command
		if (p_saved_position_ != NULL)
			delete p_saved_position_;

		p_saved_position_ = new position(*p_current_pos);
	}
	// If the previous command was at the same height, and the extruder is primed, check the starting
	// point of the current command to see if it's closer.
	if (p_previous_pos->is_primed_ && gcode_position::is_equal(p_current_pos->z_, p_previous_pos->z_))
	{
		if (is_closer(p_previous_pos))
		{
			has_saved_position_ = true;
			// delete the current saved position and parsed command
			if (p_saved_position_ != NULL)
				delete p_saved_position_;
			p_saved_position_ = new position(*p_previous_pos);
		}
	}

}

bool stabilization_snap_to_print::is_closer(position * p_position)
{
	// check the bounding box
	if (p_stabilization_args_->is_bound_)
	{
		if (
			p_position->x_ < p_stabilization_args_->x_min_ ||
			p_position->x_ > p_stabilization_args_->x_max_ ||
			p_position->y_ < p_stabilization_args_->y_min_ ||
			p_position->y_ > p_stabilization_args_->y_max_ ||
			p_position->z_ < p_stabilization_args_->z_min_ ||
			p_position->z_ > p_stabilization_args_->z_max_)
		{
			return false;
		}
	}

	// if we have no saved position, this is the closest!
	if (!has_saved_position_)
		return true;

	// If the speed is faster than the saved speed, this is the closest point
	if (p_stabilization_args_->fastest_speed_)
	{
		if (gcode_position::greater_than(p_position->f_, p_saved_position_->f_))
			return true;
		else if (gcode_position::less_than(p_position->f_, p_saved_position_->f_))
			return false;
	}
	if (snap_to_print_args_->nearest_to_corner == FRONT_LEFT)
	{
		if (snap_to_print_args_->favor_x_axis)
		{
			if (gcode_position::greater_than(p_position->x_, p_saved_position_->x_))
				return false;
			else if (gcode_position::less_than(p_position->x_, p_saved_position_->x_))
				return true;
			else if (gcode_position::less_than(p_position->y_, p_saved_position_->y_))
				return true;
		}
		else
		{
			if (gcode_position::greater_than(p_position->y_, p_saved_position_->y_))
				return false;
			else if (gcode_position::less_than(p_position->y_, p_saved_position_->y_))
				return true;
			else if (gcode_position::less_than(p_position->x_, p_saved_position_->x_))
				return true;
		}
	}
	else if (snap_to_print_args_->nearest_to_corner == FRONT_RIGHT)
	{
		if (snap_to_print_args_->favor_x_axis)
		{
			if (gcode_position::less_than(p_position->x_, p_saved_position_->x_))
				return false;
			else if (gcode_position::greater_than(p_position->x_, p_saved_position_->x_))
				return true;
			else if (gcode_position::less_than(p_position->y_, p_saved_position_->y_))
				return true;
		}
		else
		{
			if (gcode_position::greater_than(p_position->y_, p_saved_position_->y_))
				return false;
			else if (gcode_position::less_than(p_position->y_, p_saved_position_->y_))
				return true;
			else if (gcode_position::greater_than(p_position->x_, p_saved_position_->x_))
				return true;
		}
	}
	else if (snap_to_print_args_->nearest_to_corner == BACK_LEFT)
	{
		if (snap_to_print_args_->favor_x_axis)
		{
			if (gcode_position::greater_than(p_position->x_, p_saved_position_->x_))
				return false;
			else if (gcode_position::less_than(p_position->x_, p_saved_position_->x_))
				return true;
			else if (gcode_position::greater_than(p_position->y_, p_saved_position_->y_))
				return true;
		}
		else
		{
			if (gcode_position::less_than(p_position->y_, p_saved_position_->y_))
				return false;
			else if (gcode_position::greater_than(p_position->y_, p_saved_position_->y_))
				return true;
			else if (gcode_position::less_than(p_position->x_, p_saved_position_->x_))
				return true;
		}
	}
	else if (snap_to_print_args_->nearest_to_corner == BACK_RIGHT)
	{
		if (snap_to_print_args_->favor_x_axis)
		{
			if (gcode_position::less_than(p_position->x_, p_saved_position_->x_))
				return false;
			else if (gcode_position::greater_than(p_position->x_, p_saved_position_->x_))
				return true;
			else if (gcode_position::greater_than(p_position->y_, p_saved_position_->y_))
				return true;
		}
		else
		{
			if (gcode_position::less_than(p_position->y_, p_saved_position_->y_))
				return false;
			else if (gcode_position::greater_than(p_position->y_, p_saved_position_->y_))
				return true;
			else if (gcode_position::greater_than(p_position->x_, p_saved_position_->x_))
				return true;
		}
	}
	return false;
}

void stabilization_snap_to_print::add_saved_plan()
{
	snapshot_plan* p_plan = new snapshot_plan();
	// create the initial position
	p_plan->p_triggering_command_ = new parsed_command(*p_saved_position_->p_command);
	p_plan->p_start_command_ = new parsed_command(*p_saved_position_->p_command);
	p_plan->p_initial_position_ = new position(*p_saved_position_);
	snapshot_plan_step* p_step = new snapshot_plan_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
	p_plan->steps_.push_back(p_step);
	p_plan->p_return_position_ = new position(*p_saved_position_);
	p_plan->p_end_command_ = NULL;
	p_plan->file_line_ = p_saved_position_->file_line_number_;
	p_plan->file_gcode_number_ = p_saved_position_->gcode_number_;
	// Add the plan
	p_snapshot_plans_->push_back(p_plan);

	current_height_ = p_saved_position_->height_;
	current_layer_ = p_saved_position_->layer_;
	// set the state for the next layer
	has_saved_position_ = false;
	is_layer_change_wait_ = false;
	delete p_saved_position_;
	p_saved_position_ = NULL;

}

void stabilization_snap_to_print::on_processing_complete()
{
	if (has_saved_position_)
	{
		add_saved_plan();
	}
}

