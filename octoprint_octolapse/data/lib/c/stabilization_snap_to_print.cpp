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
#include "logging.h"
#include "utilities.h"
stabilization_snap_to_print::stabilization_snap_to_print() : stabilization()
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	p_closest_position_ = NULL;
	get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
}

stabilization_snap_to_print::stabilization_snap_to_print(
	gcode_position_args* position_args, stabilization_args* stab_args, progressCallback progress
) : stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	p_closest_position_ = NULL;
	get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
}

stabilization_snap_to_print::stabilization_snap_to_print(
	gcode_position_args* position_args, stabilization_args* stab_args,  
	pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
) :stabilization(position_args, stab_args, get_coordinates, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	p_closest_position_ = NULL;
	get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
}

stabilization_snap_to_print::stabilization_snap_to_print(const stabilization_snap_to_print &source)
{
	// Private copy constructor, don't copy me!	
}

stabilization_snap_to_print::~stabilization_snap_to_print()
{
	// delete any saved extrusion/travel tracking structs
	delete_saved_positions();
}

bool stabilization_snap_to_print::has_saved_position()
{
	return p_closest_position_ != NULL;
}

void stabilization_snap_to_print::reset_saved_positions()
{
	// cleanup memory
	delete_saved_positions();
	// set the state for the next layer
	is_layer_change_wait_ = false;
}

void stabilization_snap_to_print::delete_saved_positions()
{
	// cleanup memory
	if (p_closest_position_ != NULL)
	{
		delete p_closest_position_;
		p_closest_position_ = NULL;
	}
}

void stabilization_snap_to_print::save_position(position* p_position, position_type type_, double distance)
{
	if (type_ == position_type::extrusion)
	{
		// delete the current saved position and parsed command
		delete_saved_positions();
		//std::cout << "Creating new saved position.\r\n";
		p_closest_position_ = new trigger_position(position_type::extrusion, distance, p_position);
	}
}

void stabilization_snap_to_print::process_pos(position* p_current_pos, position* p_previous_pos)
{
	//std::cout << "Processing Position for gcode:"<< p_current_pos->p_command->gcode_ << ".\r\n";
	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change_ && p_current_pos->layer_ > 1)
	{
		is_layer_change_wait_ = true;
	}

	if (!p_current_pos->is_extruding_ || !p_current_pos->has_xy_position_changed_ || p_current_pos->gcode_ignored_ || !p_current_pos->is_in_bounds_)
	{
		return;
	}

	if (is_layer_change_wait_ && has_saved_position())
	{
		if (p_stabilization_args_->height_increment != 0)
		{
			//std::cout << "Checking Height Increment.\r\n";
			// todo : improve this check, it doesn't need to be done on every command if Z hasn't changed
			const double increment_double = p_current_pos->last_extrusion_height_ / p_stabilization_args_->height_increment;
			unsigned const int increment = utilities::round_up_to_int(increment_double);
			//std::cout << "Last Increment: " << current_height_increment_ << " Current Increment double" << increment_double << " Current Increment int:" << increment;
			if (increment > current_height_increment_)
			{
				if (increment > 1)
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
		//std::cout << "Completed Checking Height Increment.\r\n";
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
	//std::cout << "Checking for closer position.\r\n";
	double distance = is_closer(p_current_pos, position_type::extrusion);
	if (utilities::greater_than_or_equal(distance, 0.0))
	{
		save_position(p_current_pos, position_type::extrusion, distance);
	}
	
	// If the previous command was at the same height, and the extruder is primed, check the starting
	// point of the current command to see if it's closer.
	if (p_previous_pos->is_primed_ && utilities::is_equal(p_current_pos->z_, p_previous_pos->z_))
	{
		//std::cout << "Checking for closer previous position.\r\n";
		distance = is_closer(p_previous_pos, position_type::extrusion);
		if (utilities::greater_than_or_equal(distance, 0.0))
		{
			save_position(p_previous_pos, position_type::extrusion, distance);
		}
	}
}

double stabilization_snap_to_print::is_closer(position * p_position, position_type type)
{
	trigger_position* p_current_closest;
	if (type == position_type::extrusion)
	{
		p_current_closest = p_closest_position_;
	}
	else
		return -1.0;

	if (p_current_closest == NULL)
	{
		//std::cout << "No closer position, returning distance.\r\n";
		return utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
	}

	// If the speed is faster than the saved speed, this is the closest point
	if (p_stabilization_args_->fastest_speed && p_current_closest->type == position_type::extrusion)
	{
		//std::cout << "Checking for faster speed than " << p_current_closest->p_position->f_;
		if (utilities::greater_than(p_position->f_, p_current_closest->p_position->f_))
		{
			//std::cout << " - IsCloser Complete, " << p_position->f_ << " is faster than " << p_current_closest->p_position->f_ << "\r\n";
			const double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
			if (distance > -1)
			{
				return distance;
			}

		}
		else if (utilities::less_than(p_position->f_, p_current_closest->p_position->f_))
		{
			//std::cout << " - IsCloser Complete, " << p_position->f_ << " too slow.\r\n";
			return -1.0;
		}
	}
	//std::cout << "Calculating nearest distance...";
	// Compare the saved points cartesian distance from the current point
	const double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
	if (utilities::greater_than_or_equal(distance, 0) )
	{
		if(utilities::is_equal(p_current_closest->distance, distance) && !p_snapshot_plans_->empty())
		{
			//std::cout << "Closest position tie detected, ";
			// get the last snapshot plan position
			position* last_position = (*p_snapshot_plans_)[p_snapshot_plans_->size() - 1]->p_initial_position;
			const double old_distance_from_previous = utilities::get_cartesian_distance(p_current_closest->p_position->x_, p_current_closest->p_position->y_, last_position->x_, last_position->y_);
			const double new_distance_from_previous = utilities::get_cartesian_distance(p_position->x_, p_position->y_, last_position->x_, last_position->y_);
			if (utilities::less_than(new_distance_from_previous, old_distance_from_previous))
			{
				//std::cout << "new is closer to the last initial snapshot position.\r\n";
				return distance;
			}
			//std::cout << "old position is closer to the last initial snapshot position.\r\n";
		}
		// Todo:  handle ties.  If there is a tie, choose the position that's closest to the previous position
		else if (utilities::greater_than(p_current_closest->distance, distance))
		{
			//std::cout << " - IsCloser Complete, closer.\r\n";
			return distance;
		}
	}
	//std::cout << " - IsCloser Complete, not closer.\r\n";
	return -1.0;
}

void stabilization_snap_to_print::add_saved_plan()
{
	///td::cout << "Adding saved plan.\r\n";
	if (p_closest_position_ != NULL)
	{
		snapshot_plan* p_plan = new snapshot_plan();
		// create the initial position
		p_plan->p_triggering_command = new parsed_command(*p_closest_position_->p_position->p_command);
		p_plan->p_start_command = new parsed_command(*p_closest_position_->p_position->p_command);
		p_plan->p_initial_position = new position(*p_closest_position_->p_position);
		snapshot_plan_step* p_step = new snapshot_plan_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
		p_plan->steps.push_back(p_step);
		p_plan->p_return_position = new position(*p_closest_position_->p_position);
		p_plan->p_end_command = NULL;
		p_plan->file_line = p_closest_position_->p_position->file_line_number_;
		p_plan->file_gcode_number = p_closest_position_->p_position->gcode_number_;
		// Add the plan
		p_snapshot_plans_->push_back(p_plan);
		current_layer_ = p_closest_position_->p_position->layer_;
		// set the state for the next layer
	}
	
	reset_saved_positions();
	get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
	//std::cout << "Saved plan added.\r\n";
}

void stabilization_snap_to_print::on_processing_complete()
{
	if (has_saved_position())
	{
		add_saved_plan();
	}
}

