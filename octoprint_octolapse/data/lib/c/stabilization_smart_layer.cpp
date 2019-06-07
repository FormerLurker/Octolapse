#include "stabilization_smart_layer.h"
#include "utilities.h"
#include "logging.h"
#include <iostream>


stabilization_smart_layer::stabilization_smart_layer() : closest_positions_(0)
{
	// Initialize travel args
	p_smart_layer_args_ = new smart_layer_args();
	// initialize layer/height tracking variables
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	current_layer_saved_extrusion_speed_ = -1;
	standard_layer_trigger_distance_ = 0.0;
}

stabilization_smart_layer::stabilization_smart_layer(
	gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, progressCallback progress
) :stabilization(position_args, stab_args, progress), closest_positions_(mt_args->distance_threshold_percent)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	
	p_smart_layer_args_ = mt_args;

	// initialize closest extrusion/travel tracking structs
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	current_layer_saved_extrusion_speed_ = -1;
	standard_layer_trigger_distance_ = 0.0;
	// Get the initial stabilization coordinates
	get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
}

stabilization_smart_layer::stabilization_smart_layer(
	gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
) : stabilization(position_args, stab_args, get_coordinates, progress), closest_positions_(mt_args->distance_threshold_percent)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	p_smart_layer_args_ = mt_args;
	// Get the initial stabilization coordinates
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	current_layer_saved_extrusion_speed_ = -1;
	standard_layer_trigger_distance_ = 0.0;
	get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
}

stabilization_smart_layer::stabilization_smart_layer(const stabilization_smart_layer &source)
{
	
}

stabilization_smart_layer::~stabilization_smart_layer()
{
	
}

smart_layer_args::trigger_type stabilization_smart_layer::get_trigger_type()
{
	if (p_smart_layer_args_->snap_to_print)
		return smart_layer_args::fastest;
	return p_smart_layer_args_->smart_layer_trigger_type;
}

bool stabilization_smart_layer::can_process_position(position* p_position, trigger_position::position_type type)
{

	if (type == trigger_position::unknown)
		return false;
	if (p_smart_layer_args_->snap_to_print && type != trigger_position::extrusion)
		return false;

	if (type == trigger_position::extrusion)
	{
		if (get_trigger_type() > smart_layer_args::compatibility)
			return false;
	}

	// check for errors in position, layer, or height
	if (p_position->layer_ == 0 || p_position->x_null_ || p_position->y_null_ || p_position->z_null_)
	{
		return false;
	}
	// See if we should ignore the current position because it is not in bounds, or because it wasn't processed
	if (p_position->gcode_ignored_ || !p_position->is_in_bounds_)
		return false;

	return true;
}

void stabilization_smart_layer::process_pos(position* p_current_pos, position* p_previous_pos)
{
	//std::cout << "StabilizationSmartLayer::process_pos - Processing Position...";
	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change_ && p_current_pos->layer_ > 1)
	{
		is_layer_change_wait_ = true;
		// get distance from current point to the stabilization point
		standard_layer_trigger_distance_ = utilities::get_cartesian_distance(
			p_current_pos->x_, p_current_pos->y_,
			stabilization_x_, stabilization_y_
		);
	}
			
	if (is_layer_change_wait_ && !closest_positions_.is_empty())
	{
		bool can_add_saved_plan = true;
		if (p_stabilization_args_->height_increment != 0)
		{
			can_add_saved_plan = false;
			const double increment_double = p_current_pos->height_ / p_stabilization_args_->height_increment;
			unsigned const int increment = utilities::round_up_to_int(increment_double);
			if (increment > current_height_increment_)
			{
				// We only update the height increment if we've detected extrusion on a layer
				if (increment > 1.0 && !closest_positions_.is_empty())
				{
					current_height_increment_ = increment;
					can_add_saved_plan = true;
				}
				else
				{
					octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::WARNING, "Octolapse missed a layer while creating a snapshot plan due to a height restriction.");
				}
			}
		}
		if (can_add_saved_plan)
		{
			add_plan();
		}

	}

	double distance = -1;
	// Get the current position type and see if we can process this type
	trigger_position::position_type current_type = trigger_position::get_type(p_current_pos);
	if (can_process_position(p_current_pos, current_type))
	{
		// Is the endpoint of the current command closer
		// Note that we need to save the position immediately
		// so that the IsCloser check for the previous_pos will
		// have a saved command to check.
		if (is_closer(p_current_pos, current_type, distance))
		{
			closest_positions_.add(current_type, distance, p_current_pos);
		}
	}
	// If this is the first command on a new layer, the previous command is usually also a valid position
	// If the last command was not examined, test it IF we are at the same z height.
	if (
		last_tested_gcode_number_ != p_previous_pos->gcode_number_ &&
		utilities::is_equal(p_current_pos->z_, p_previous_pos->z_))
	{
		trigger_position::position_type previous_type = trigger_position::get_type(p_previous_pos);
		if (can_process_position(p_previous_pos, previous_type))
		{
			// Calculate the distance to the previous extrusion
			if(is_closer(p_previous_pos, previous_type, distance))
				closest_positions_.add(previous_type, distance, p_previous_pos);
		}
	}
	last_tested_gcode_number_ = p_current_pos->gcode_number_;
}

bool stabilization_smart_layer::is_closer(position * p_position, trigger_position::position_type type, double &distance)
{
	// Fist check the speed threshold if we are running a fast trigger type
	// We want to ignore any extrusions that are below the speed threshold
	const bool filter_extrusion_speeds = get_trigger_type() == smart_layer_args::fast && type == trigger_position::extrusion;
	if (filter_extrusion_speeds)
	{
		// Initialize our previous extrusion speed if it's not been initialized
		if (current_layer_saved_extrusion_speed_ == -1)
			current_layer_saved_extrusion_speed_ = p_position->f_;
		// see if we have found more than one extrusion speed
		if (has_one_extrusion_speed_)
		{
			if (
				current_layer_saved_extrusion_speed_ != p_position->f_ ||
				(
					utilities::greater_than(p_smart_layer_args_->speed_threshold, 0) &&
					utilities::greater_than(p_position->f_, p_smart_layer_args_->speed_threshold)
					)
			)
			{
				has_one_extrusion_speed_ = false;
			}
		}
		// see if we should filter out this position due to the feedrate
		if (utilities::less_than_or_equal(p_position->f_, p_smart_layer_args_->speed_threshold))
			return false;

	}

	// Get the current closest position
	trigger_position* p_current_closest = closest_positions_.get(type);
	// Calculate the distance between the current point and the stabilization point
	double x2, y2;
	if (p_stabilization_args_->x_stabilization_disabled)
		x2 = p_position->x_;
	else
		x2 = stabilization_x_;
	if (p_stabilization_args_->y_stabilization_disabled)
		y2 = p_position->y_;
	else
		y2 = stabilization_y_;

	distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, x2,y2);
	// If we don't have any closest position, this is the closest
	if (p_current_closest == NULL)
	{
		return true;
	}

	if(filter_extrusion_speeds)
	{
		// Check to see if the current extrusion feedrate is faster than the current closest extrusion feedrate.  If it is, it's our new closest
		// extrusion position
		if (utilities::greater_than(p_position->f_, p_current_closest->p_position->f_))
		{
			return true;
		}
	}
	// See if we have a closer position	
	if (utilities::greater_than(p_current_closest->distance, distance))
	{
		//std::cout << " - IsCloser Complete, closer.\r\n";
		return true;
	}
	else if (utilities::is_equal(p_current_closest->distance, distance) && !p_snapshot_plans_->empty())
	{
		//std::cout << "Closest position tie detected, ";
		// get the last snapshot plan position
		position* last_position = (*p_snapshot_plans_)[p_snapshot_plans_->size() - 1]->p_initial_position;
		const double old_distance_from_previous = utilities::get_cartesian_distance(p_current_closest->p_position->x_, p_current_closest->p_position->y_, last_position->x_, last_position->y_);
		const double new_distance_from_previous = utilities::get_cartesian_distance(p_position->x_, p_position->y_, last_position->x_, last_position->y_);
		if (utilities::less_than(new_distance_from_previous, old_distance_from_previous))
		{
			//std::cout << "new is closer to the last initial snapshot position.\r\n";
			return true;
		}
		//std::cout << "old position is closer to the last initial snapshot position.\r\n";
	}
	//std::cout << " - IsCloser Complete, not closer.\r\n";
	return false;
}

trigger_position* stabilization_smart_layer::get_closest_position()
{
	switch (get_trigger_type())
	{
	case smart_layer_args::fastest:
			return closest_positions_.get_fastest_position();
		case smart_layer_args::fast:
			if (has_one_extrusion_speed_)
				return closest_positions_.get_compatibility_position();
			return closest_positions_.get_fastest_position();
		case smart_layer_args::compatibility:
			return closest_positions_.get_compatibility_position();
		case smart_layer_args::normal_quality:
			return closest_positions_.get_normal_quality_position();
		case smart_layer_args::high_quality:
			return closest_positions_.get_high_quality_position();
		case smart_layer_args::best_quality:
			return closest_positions_.get_best_quality_position();
		default:
			return NULL;
	}
}

void stabilization_smart_layer::add_plan()
{
	trigger_position * p_closest = get_closest_position();
	if (p_closest != NULL)
	{
		//std::cout << "Adding saved plan to plans...  F Speed" << p_saved_position_->f_ << " \r\n";
		snapshot_plan* p_plan = new snapshot_plan();
		double total_travel_distance = p_closest->distance * 2;
		p_plan->total_travel_distance = total_travel_distance;
		p_plan->saved_travel_distance = (standard_layer_trigger_distance_ * 2) - total_travel_distance;
		p_plan->triggering_command_type = p_closest->type;
		// create the initial position
		p_plan->p_triggering_command = new parsed_command(*p_closest->p_position->p_command);
		p_plan->p_start_command = new parsed_command(*p_closest->p_position->p_command);
		p_plan->p_initial_position = new position(*p_closest->p_position);

		bool all_stabilizations_disabled = p_stabilization_args_->x_stabilization_disabled && p_stabilization_args_->y_stabilization_disabled;
		
		if (!(all_stabilizations_disabled || p_smart_layer_args_->snap_to_print))
		{
			double x_stabilization, y_stabilization;
			if (p_stabilization_args_->x_stabilization_disabled)
				x_stabilization = p_closest->p_position->x_;
			else
				x_stabilization = stabilization_x_;

			if (p_stabilization_args_->y_stabilization_disabled)
				y_stabilization = p_closest->p_position->y_;
			else
				y_stabilization = stabilization_y_;

			snapshot_plan_step* p_travel_step = new snapshot_plan_step(&x_stabilization, &y_stabilization, NULL, NULL, NULL, travel_action);
			p_plan->steps.push_back(p_travel_step);
		}
		
		snapshot_plan_step* p_snapshot_step = new snapshot_plan_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
		p_plan->steps.push_back(p_snapshot_step);

		p_plan->p_return_position = new position(*p_closest->p_position);
		p_plan->p_end_command = NULL;

		p_plan->file_line = p_closest->p_position->file_line_number_;
		p_plan->file_gcode_number = p_closest->p_position->gcode_number_;

		// Add the plan
		p_snapshot_plans_->push_back(p_plan);
		current_layer_ = p_closest->p_position->layer_;
		// only get the next coordinates if we've actually added a plan.
		get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
	}
	else
	{
		std::cout << "No saved position available to add snapshot plan!";
	}
	// always reset the saved positions
	reset_saved_positions();
	
	//std::cout << "Complete.\r\n";
}

void stabilization_smart_layer::reset_saved_positions()
{
	// Clear the saved closest positions
	closest_positions_.clear();
	// set the state for the next layer
	is_layer_change_wait_ = false;
	has_one_extrusion_speed_ = true;
	current_layer_saved_extrusion_speed_ = -1;
	standard_layer_trigger_distance_ = 0.0;
}

void stabilization_smart_layer::on_processing_complete()
{
	//std::cout << "Running on_process_complete...";
	if (!closest_positions_.is_empty())
	{
		add_plan();
	}
	//std::cout << "Complete.\r\n";
}