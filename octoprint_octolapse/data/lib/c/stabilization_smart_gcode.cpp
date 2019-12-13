#include "stabilization_smart_gcode.h"
#include "utilities.h"
#include "trigger_position.h"

stabilization_smart_gcode::stabilization_smart_gcode()
{
	// Initialize travel args
	smart_gcode_args_ = smart_gcode_args();
	// initialize layer/height tracking variables
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	snapshot_commands_found_ = 0;
}

stabilization_smart_gcode::stabilization_smart_gcode(gcode_position_args position_args, stabilization_args stab_args, smart_gcode_args mt_args, progressCallback progress) :stabilization(position_args, stab_args, progress)
{
	// Initialize travel args
	smart_gcode_args_ = mt_args;
	// initialize layer/height tracking variables
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	snapshot_commands_found_ = 0;
	update_stabilization_coordinates();
}

stabilization_smart_gcode::stabilization_smart_gcode(gcode_position_args position_args, stabilization_args stab_args, smart_gcode_args mt_args, pythonGetCoordinatesCallback get_coordinates, PyObject * py_get_coordinates_callback, pythonProgressCallback progress, PyObject * py_progress_callback) : stabilization(position_args, stab_args, get_coordinates, py_get_coordinates_callback, progress, py_progress_callback)
{
	// Initialize travel args
	smart_gcode_args_ = mt_args;
	// initialize layer/height tracking variables
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	snapshot_commands_found_ = 0;
	update_stabilization_coordinates();
}


stabilization_smart_gcode::~stabilization_smart_gcode()
{
}

stabilization_smart_gcode::stabilization_smart_gcode(const stabilization_smart_gcode &source)
{

}


void stabilization_smart_gcode::process_pos(position * p_current_pos, position * p_previous_pos, bool found_command)
{
	if (p_current_pos->command.gcode == smart_gcode_args_.snapshot_command.gcode)
	{
		snapshot_commands_found_++;
		if (!p_current_pos->can_take_snapshot())
		{
			missed_snapshots_++;
			// ToDo:  Record more details about missed snapshot
		}
		else
		{
			add_plan(p_current_pos);
		}
		
	}
}

void stabilization_smart_gcode::on_processing_complete()
{
}

std::vector<stabilization_quality_issue> stabilization_smart_gcode::get_quality_issues()
{
	return std::vector<stabilization_quality_issue>();
}

std::vector<stabilization_processing_issue> stabilization_smart_gcode::get_internal_processing_issues()
{
	std::vector<stabilization_processing_issue> issues;
	if (snapshot_commands_found_ == 0)
	{
		stabilization_processing_issue issue;
		issue.description = "No snapshot commands were found.";
		replacement_token token;
		token.key = "snapshot_command";
		token.value = smart_gcode_args_.snapshot_command.gcode;
		issue.replacement_tokens.push_back(token);
		issue.issue_type = stabilization_processing_issue_type_no_snapshot_commands_found;
		issues.push_back(issue);
	}
	return issues;
}

void stabilization_smart_gcode::add_plan(position * p_position)
{
	//std::cout << "Adding saved plan to plans...  F Speed" << p_saved_position_->f_ << " \r\n";
	snapshot_plan p_plan;
	double total_travel_distance;
	total_travel_distance = utilities::get_cartesian_distance(p_position->x, p_position->y, stabilization_x_, stabilization_y_);
	
	p_plan.total_travel_distance = total_travel_distance * 2;
	p_plan.saved_travel_distance = 0;
	p_plan.distance_from_stabilization_point = total_travel_distance;
	p_plan.triggering_command_type = position_type_unknown;
	p_plan.triggering_command_feature_type = static_cast<feature_type>(p_position->feature_type_tag);
	// create the initial position
	p_plan.triggering_command = p_position->command;
	p_plan.start_command = p_position->command;
	p_plan.initial_position = *p_position;
	p_plan.has_initial_position = true;
	const bool all_stabilizations_disabled = stabilization_args_.x_stabilization_disabled && stabilization_args_.y_stabilization_disabled;

	if (!all_stabilizations_disabled)
	{
		double x_stabilization, y_stabilization;
		if (stabilization_args_.x_stabilization_disabled)
			x_stabilization = p_position->x;
		else
			x_stabilization = stabilization_x_;

		if (stabilization_args_.y_stabilization_disabled)
			y_stabilization = p_position->y;
		else
			y_stabilization = stabilization_y_;

		const snapshot_plan_step p_travel_step(&x_stabilization, &y_stabilization, NULL, NULL, NULL, travel_action);
		p_plan.steps.push_back(p_travel_step);
	}

	const snapshot_plan_step p_snapshot_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
	p_plan.steps.push_back(p_snapshot_step);

	p_plan.return_position = *p_position;

	p_plan.file_line = p_position->file_line_number;
	p_plan.file_gcode_number = p_position->gcode_number;
	p_plan.file_position = p_position->file_position;

	// Add the plan
	p_snapshot_plans_.push_back(p_plan);
	// get the next coordinates
	update_stabilization_coordinates();
	
}

void stabilization_smart_gcode::update_stabilization_coordinates()
{
	get_next_xy_coordinates(stabilization_x_, stabilization_y_);
}