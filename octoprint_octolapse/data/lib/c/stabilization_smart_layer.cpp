#include "stabilization_smart_layer.h"
#include "utilities.h"
#include "logging.h"
#include <iostream>


stabilization_smart_layer::stabilization_smart_layer()
{
	// Initialize travel args
	smart_layer_args_ = NULL;
	// Initialize python callback status
	has_python_coordinate_callback = false;
	// initialize stabilization point variables
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	// initialize layer/height tracking variables
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	// initialize extrusion tracking	
	p_closest_extrusion_ = NULL;
	
	// initialize travel tracking variables
	p_closest_travel_ = NULL;
}

stabilization_smart_layer::stabilization_smart_layer(
	gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, progressCallback progress
) :stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	
	smart_layer_args_ = mt_args;
	has_python_coordinate_callback = false;

	// initialize closest extrusion/travel tracking structs
	p_closest_extrusion_ = NULL;
	p_closest_travel_ = NULL;
	
	// Get the initial stabilization coordinates
	get_next_xy_coordinates();
}

stabilization_smart_layer::stabilization_smart_layer(
	gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
) : stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	_get_coordinates_callback = get_coordinates;
	smart_layer_args_ = mt_args;
	has_python_coordinate_callback = true;
	// initialize closest extrusion/travel tracking structs
	p_closest_extrusion_ = NULL;
	p_closest_travel_ = NULL;
	// Get the initial stabilization coordinates
	get_next_xy_coordinates();
}

stabilization_smart_layer::stabilization_smart_layer(const stabilization_smart_layer &source)
{
	
}

stabilization_smart_layer::~stabilization_smart_layer()
{
	// delete any saved extrusion/travel tracking structs
	if (p_closest_extrusion_ != NULL)
	{
		delete p_closest_extrusion_;
		p_closest_extrusion_ = NULL;
	}
	
	if (p_closest_travel_ != NULL)
	{
		delete p_closest_travel_;
		p_closest_travel_ = NULL;
	}
}

bool stabilization_smart_layer::has_saved_position()
{
	if (p_closest_travel_ != NULL || p_closest_extrusion_ != NULL)
		return true;
	return false;
}
void stabilization_smart_layer::get_next_xy_coordinates()
{
	//std::cout << "Getting XY stabilization coordinates...";

	if (has_python_coordinate_callback)
	{
		//std::cout << "calling python...";
		if(!_get_coordinates_callback(smart_layer_args_->py_get_snapshot_position_callback, smart_layer_args_->x_coordinate, smart_layer_args_->y_coordinate, &stabilization_x_, &stabilization_y_))
			octolapse_log(SNAPSHOT_PLAN, INFO, "Failed dto get snapshot coordinates.");
	}

	else
	{
		//std::cout << "extracting from args...";
		stabilization_x_ = smart_layer_args_->x_coordinate;
		stabilization_y_ = smart_layer_args_->y_coordinate;
	}
	//std::cout << " - X coord: " << x_coord;
	//std::cout << " - Y coord: " << y_coord << "\r\n";
}

void stabilization_smart_layer::process_pos(position* p_current_pos, position* p_previous_pos)
{
	//std::cout << "StabilizationSmartLayer::process_pos - Processing Position...";
	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change_ && p_current_pos->layer_ > 1)
	{
		is_layer_change_wait_ = true;
	}
	
	if (p_current_pos->gcode_ignored_ || !p_current_pos->is_in_bounds_ || !p_current_pos->has_xy_position_changed_)
		return;

	position_type type;
	if (
		p_current_pos->is_extruding_ && 
		smart_layer_args_->trigger_on_extrude
	)
	{
		type = position_type::extrusion;
	}
	else if (p_current_pos->is_retracted_ && (p_current_pos->is_travel_only_ || p_current_pos->is_zhop_))
	{
		type = position_type::retracted_travel;
	}
	else
	{
		// Not sure what this command is, so return without updating.
		return;
	}

	if (is_layer_change_wait_ && has_saved_position())
	{
		bool can_add_saved_plan = true;
		if (p_stabilization_args_->height_increment_ != 0)
		{
			can_add_saved_plan = false;
			const double increment_double = p_current_pos->last_extrusion_height_ / p_stabilization_args_->height_increment_;
			unsigned const int increment = utilities::round_up_to_int(increment_double);
			if (increment > current_height_increment_)
			{
				// We only update the height increment if we've detected extrusion on a layer
				if (increment > 1.0 && has_saved_position())
				{
					current_height_increment_ = increment;
					can_add_saved_plan = true;
				}
				else
				{
					octolapse_log(octolapse_loggers::SNAPSHOT_PLAN, octolapse_log_levels::WARNING, "Octolapse missed a layer while creating a snapshot plan due to a height restriction.");
				}
			}
		}
		if (can_add_saved_plan)
		{
			add_plan();
		}

	}

	// check for errors in position, layer, or height
	if (p_current_pos->layer_ == 0 || p_current_pos->x_null_ || p_current_pos->y_null_ || p_current_pos->z_null_)
	{
		return;
	}

	// Is the endpoint of the current command closer
	// Note that we need to save the position immediately
	// so that the IsCloser check for the previous_pos will
	// have a saved command to check.
	double distance = -1;
	distance = is_closer(p_current_pos, type);
	if (utilities::greater_than_or_equal(distance, 0.0))
	{
		save_position(p_current_pos, type, distance);
	}
	// If this is the first command on a new layer, the previous command is usually also a valid position
	// If the last command was not examined, test it IF we are at the same z height.
	if (
		last_tested_gcode_number_ != p_previous_pos->gcode_number_ &&
		smart_layer_args_->trigger_on_extrude &&
		utilities::is_equal(p_current_pos->z_, p_previous_pos->z_))
	{
		position_type previous_type = position_type::unknown;
		// get the previous command type
		if (p_previous_pos->is_primed_)
		{
			// We are sure that the previous command is primed, which we will treat as an extrusion
			type = position_type::extrusion;
		}
		// The next section was removed, but I wanted to keep it in for further consideration.
		// I don't think we need to consider the previous position if it's not an extrude.
		// We want the printer to complete the travel before taking a snapshot so that any 
		// strings are moved towards the interior of the print (usually the case).  At the 
		// very least, any stringing should be similar to the stringing on the original print.
		//else if (p_previous_pos->is_retracted_)
		//{
			// we are sure the previous position is a retracted travel
		//	type = position_type::retracted_travel;
		//}
		// Calculate the distance to the previous extrusion
		
		if (type != position_type::unknown)
		{
			distance = -1;

			distance = is_closer(p_previous_pos, type);

			if (utilities::greater_than_or_equal(distance, 0.0))
			{
				save_position(p_previous_pos, type, distance);
			}
		}
	}
	last_tested_gcode_number_ = p_current_pos->gcode_number_;
}

void stabilization_smart_layer::save_position(position* p_position, position_type type_, double distance)
{
	if (type_ == position_type::extrusion)
	{
		// delete the current saved position and parsed command
		if (p_closest_extrusion_ != NULL)
		{
			//std::cout << "Deleting saved position.\r\n";
			delete p_closest_extrusion_;
		}
		//std::cout << "Creating new saved position.\r\n";
		p_closest_extrusion_ = new closest_position(position_type::extrusion, distance, new position(*p_position));
	}
	else if (type_ == position_type::retracted_travel)
	{
		// delete the current saved position and parsed command
		if (p_closest_travel_ != NULL)
		{
			//std::cout << "Deleting saved position.\r\n";
			delete p_closest_travel_;
		}
		//std::cout << "Creating new saved position.\r\n";
		p_closest_travel_ = new closest_position(position_type::retracted_travel, distance, new position(*p_position));
	}
}

double stabilization_smart_layer::is_closer(position * p_position, position_type type)
{
	closest_position* p_current_closest = NULL;
	if (
		type == position_type::extrusion &&
		(
			utilities::is_equal(smart_layer_args_->extrude_trigger_speed_threshold,0) ||
			utilities::greater_than(p_position->f_, smart_layer_args_->extrude_trigger_speed_threshold)
		)
	)
	{
		p_current_closest = p_closest_extrusion_;
	}
	else if (type == position_type::retracted_travel)
	{
		p_current_closest = p_closest_travel_;
	}
	else
		return -1.0;
	
	if (p_current_closest == NULL)
	{
		return utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
	}

	// If the speed is faster than the saved speed, this is the closest point
	if (p_stabilization_args_->fastest_speed_ && p_current_closest->type == position_type::extrusion)
	{
		if(has_one_extrusion_speed_ && !utilities::is_equal(p_position->f_, p_current_closest->p_position->f_))
		{
			has_one_extrusion_speed_ = false;
		}
		//std::cout << "Checking for faster speed than " << p_saved_position_->f_;
		if (utilities::greater_than(p_position->f_, p_current_closest->p_position->f_))
		{
			//std::cout << " - IsCloser Complete, " << p_position->f_ << " is faster than " << p_saved_position_->f_ << "\r\n";
			const double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
			if (distance > -1)
			{
				return distance;
			}
			
		}
		else if (utilities::less_than(p_position->f_, p_current_closest->p_position->f_))
		{
			//std::cout << " - IsCloser Complete, " << p_position->f_ << " too slow.\r\n";"COMP
			return -1.0;
		}
	}
	//std::cout << "Checking for closer position...";
	// Compare the saved points cartesian distance from the current point
	const double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
	if (utilities::greater_than_or_equal(distance,0) && utilities::greater_than(p_current_closest->distance, distance))
	{
		//std::cout << " - IsCloser Complete, closer.\r\n";
		return distance;
	}
	//std::cout << " - IsCloser Complete, not closer.\r\n";
	return -1.0;
}

void stabilization_smart_layer::add_plan()
{
	closest_position * p_closest = NULL;
	if (
		p_closest_travel_ != NULL && (
			p_closest_extrusion_ == NULL ||
			has_one_extrusion_speed_ ||
			utilities::less_than(p_closest_travel_->distance, p_closest_extrusion_->distance)
		)
	)
	{
		p_closest = p_closest_travel_;
	}
	else
	{
		p_closest = p_closest_extrusion_;
	}
	if (p_closest != NULL)
	{
		//std::cout << "Adding saved plan to plans...  F Speed" << p_saved_position_->f_ << " \r\n";
		snapshot_plan* p_plan = new snapshot_plan();

		// create the initial position
		p_plan->p_triggering_command_ = new parsed_command(*p_closest->p_position->p_command);
		p_plan->p_start_command_ = new parsed_command(*p_closest->p_position->p_command);
		p_plan->p_initial_position_ = new position(*p_closest->p_position);
		snapshot_plan_step* p_travel_step = new snapshot_plan_step(&stabilization_x_, &stabilization_y_, NULL, NULL, NULL, travel_action);
		p_plan->steps_.push_back(p_travel_step);
		snapshot_plan_step* p_snapshot_step = new snapshot_plan_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
		p_plan->steps_.push_back(p_snapshot_step);

		p_plan->p_return_position_ = new position(*p_closest->p_position);
		p_plan->p_end_command_ = NULL;

		p_plan->file_line_ = p_closest->p_position->file_line_number_;
		p_plan->file_gcode_number_ = p_closest->p_position->gcode_number_;

		// Add the plan
		p_snapshot_plans_->push_back(p_plan);
		current_layer_ = p_closest->p_position->layer_;
	}
	reset_saved_positions();
	get_next_xy_coordinates();
	//std::cout << "Complete.\r\n";
}

void stabilization_smart_layer::reset_saved_positions()
{
	// cleanup memory
	if (p_closest_extrusion_ != NULL)
	{
		delete p_closest_extrusion_;
		p_closest_extrusion_ = NULL;
	}
	if (p_closest_travel_ != NULL)
	{
		delete p_closest_travel_;
		p_closest_travel_ = NULL;
	}

	// set the state for the next layer
	is_layer_change_wait_ = false;
	has_one_extrusion_speed_ = true;
}

void stabilization_smart_layer::on_processing_complete()
{
	//std::cout << "Running on_process_complete...";
	if (has_saved_position())
	{
		add_plan();
	}
	//std::cout << "Complete.\r\n";
}