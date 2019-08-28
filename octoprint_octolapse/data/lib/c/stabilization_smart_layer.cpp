#include "stabilization_smart_layer.h"
#include "utilities.h"
#include "logging.h"
#include <iostream>


stabilization_smart_layer::stabilization_smart_layer()
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
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;

	trigger_position_args default_args;
	closest_positions_.initialize(default_args);
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
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;

	p_smart_layer_args_ = mt_args;
	// initialize closest extrusion/travel tracking structs
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	current_layer_saved_extrusion_speed_ = -1;
	standard_layer_trigger_distance_ = 0.0;

	trigger_position_args default_args;
	default_args.type = mt_args->smart_layer_trigger_type;
	default_args.minimum_speed = mt_args->speed_threshold;
	default_args.snap_to_fastest = mt_args->snap_to_fastest;
	default_args.x_stabilization_disabled = stab_args->x_stabilization_disabled;
	default_args.y_stabilization_disabled = stab_args->y_stabilization_disabled;
	closest_positions_.initialize(default_args);
	last_snapshot_initial_position_.is_empty_ = true;
	update_stabilization_coordinates();
}

stabilization_smart_layer::stabilization_smart_layer(
	gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
) : stabilization(position_args, stab_args, get_coordinates, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_increment_ = 0;
	has_one_extrusion_speed_ = true;
	last_tested_gcode_number_ = -1;
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;

	p_smart_layer_args_ = mt_args;
	// Get the initial stabilization coordinates
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	current_layer_saved_extrusion_speed_ = -1;
	standard_layer_trigger_distance_ = 0.0;

	trigger_position_args default_args;
	default_args.type = mt_args->smart_layer_trigger_type;
	default_args.minimum_speed = mt_args->speed_threshold;
	default_args.snap_to_fastest = mt_args->snap_to_fastest;
	default_args.x_stabilization_disabled = stab_args->x_stabilization_disabled;
	default_args.y_stabilization_disabled = stab_args->y_stabilization_disabled;
	closest_positions_.initialize(default_args);
	last_snapshot_initial_position_.is_empty_ = true;
	update_stabilization_coordinates();
}

stabilization_smart_layer::stabilization_smart_layer(const stabilization_smart_layer &source)
{
	
}

stabilization_smart_layer::~stabilization_smart_layer()
{
	
}

void stabilization_smart_layer::update_stabilization_coordinates()
{
	bool stabilize_first_position_only = p_smart_layer_args_->smart_layer_trigger_type == trigger_position::snap_to_print && p_smart_layer_args_->stabilize_first_position_only;
	bool stabilization_disabled = p_stabilization_args_->x_stabilization_disabled && p_stabilization_args_->y_stabilization_disabled;
	if (
		(stabilization_disabled || stabilize_first_position_only)
		&& !last_snapshot_initial_position_.is_empty_
	)
	{
		stabilization_x_ = last_snapshot_initial_position_.x_;
		stabilization_y_ = last_snapshot_initial_position_.y_;
	}
	else
	{
		// Get the next stabilization point
		get_next_xy_coordinates(&stabilization_x_, &stabilization_y_);
	}
	closest_positions_.set_stabilization_coordinates(stabilization_x_, stabilization_y_);
}
void stabilization_smart_layer::process_pos(position& p_current_pos, position& p_previous_pos)
{
	//std::cout << "StabilizationSmartLayer::process_pos - Processing Position...";
	// if we're at a layer change, add the current saved plan
	if (p_current_pos.is_layer_change_ && p_current_pos.layer_ > 1)
	{
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::VERBOSE, "Layer change detected.");
		is_layer_change_wait_ = true;
		// get distance from current point to the stabilization point
		
		standard_layer_trigger_distance_ = utilities::get_cartesian_distance(
			p_current_pos.x_, p_current_pos.y_,
			stabilization_x_, stabilization_y_
		);
	}
			
	if (is_layer_change_wait_ && !closest_positions_.is_empty())
	{
		bool can_add_saved_plan = true;
		if (p_stabilization_args_->height_increment != 0)
		{
			can_add_saved_plan = false;
			const double increment_double = p_current_pos.height_ / p_stabilization_args_->height_increment;
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
	octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::VERBOSE, "Adding closest position.");
	closest_positions_.try_add(p_current_pos, p_previous_pos);
	last_tested_gcode_number_ = p_current_pos.gcode_number_;
}

void stabilization_smart_layer::add_plan()
{
	trigger_position p_closest;
	if (closest_positions_.get_position(p_closest))
	{
		//std::cout << "Adding saved plan to plans...  F Speed" << p_saved_position_->f_ << " \r\n";
		snapshot_plan p_plan;
		double total_travel_distance;
		if (p_smart_layer_args_->smart_layer_trigger_type == trigger_position::snap_to_print)
		{
			total_travel_distance = 0;
		}
		else
		{
			total_travel_distance = p_closest.distance * 2;
		}

		p_plan.total_travel_distance = total_travel_distance;
		p_plan.saved_travel_distance = (standard_layer_trigger_distance_ * 2) - total_travel_distance;
		p_plan.triggering_command_type = p_closest.type;
		p_plan.triggering_command_feature_type = p_closest.feature_type;
		// create the initial position
		p_plan.p_triggering_command = p_closest.p_position.p_command;
		p_plan.p_start_command = p_closest.p_position.p_command;
		p_plan.p_initial_position = p_closest.p_position;
		p_plan.has_initial_position = true;
		const bool all_stabilizations_disabled = p_stabilization_args_->x_stabilization_disabled && p_stabilization_args_->y_stabilization_disabled;
		
		if (!(all_stabilizations_disabled || p_smart_layer_args_->smart_layer_trigger_type == trigger_position::snap_to_print))
		{
			double x_stabilization, y_stabilization;
			if (p_stabilization_args_->x_stabilization_disabled)
				x_stabilization = p_closest.p_position.x_;
			else
				x_stabilization = stabilization_x_;

			if (p_stabilization_args_->y_stabilization_disabled)
				y_stabilization = p_closest.p_position.y_;
			else
				y_stabilization = stabilization_y_;

			const snapshot_plan_step p_travel_step(&x_stabilization, &y_stabilization, NULL, NULL, NULL, travel_action);
			p_plan.steps.push_back(p_travel_step);
		}

		const snapshot_plan_step p_snapshot_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
		p_plan.steps.push_back(p_snapshot_step);

		p_plan.p_return_position = p_closest.p_position;
		p_plan.file_line = p_closest.p_position.file_line_number_;
		p_plan.file_gcode_number = p_closest.p_position.gcode_number_;

		// Add the plan
		p_snapshot_plans_.push_back(p_plan);
		current_layer_ = p_closest.p_position.layer_;
		last_snapshot_initial_position_ = p_plan.p_initial_position;
		// only get the next coordinates if we've actually added a plan.
		update_stabilization_coordinates();
		
		// reset the saved positions
		reset_saved_positions();
		// Need to set the initial position after resetting the saved positions
		closest_positions_.set_previous_initial_position(last_snapshot_initial_position_);
	}
	else
	{
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::WARNING, "No point snapshot position found for layer.");
		// reset the saved positions
		reset_saved_positions();
	}
	
	
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