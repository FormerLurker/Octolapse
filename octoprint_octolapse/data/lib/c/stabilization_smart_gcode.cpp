#include "stabilization_smart_gcode.h"
#include "utilities.h"
#include "trigger_position.h"

stabilization_smart_gcode::stabilization_smart_gcode()
{
	// Initialize travel args
	smart_gcode_args_ = smart_gcode_args();
	// initialize layer/height tracking variables
	snapshot_commands_found_ = 0;
	// Make sure the default smart gocde processing is skipped so we can track errors
	stabilization_args_.allow_snapshot_commands = false;
}

stabilization_smart_gcode::stabilization_smart_gcode(gcode_position_args position_args, stabilization_args stab_args,
	smart_gcode_args mt_args, progressCallback progress) :
	stabilization(position_args, stab_args, progress)
{
	// Initialize travel args
	smart_gcode_args_ = mt_args;
	// initialize layer/height tracking variables
	snapshot_commands_found_ = 0;
	// Make sure the default smart gocde processing is skipped so we can track errors
	stabilization_args_.allow_snapshot_commands = false;
	update_stabilization_coordinates();
}

stabilization_smart_gcode::stabilization_smart_gcode(gcode_position_args position_args, stabilization_args stab_args,
	smart_gcode_args mt_args,
	pythonGetCoordinatesCallback get_coordinates,
	PyObject* py_get_coordinates_callback,
	pythonProgressCallback progress, PyObject* py_progress_callback) :
	stabilization(position_args, stab_args, get_coordinates, py_get_coordinates_callback, progress, py_progress_callback)
{
	// Initialize travel args
	smart_gcode_args_ = mt_args;
	// initialize layer/height tracking variables
	snapshot_commands_found_ = 0;
	// Make sure the default smart gocde processing is skipped so we can track errors
	stabilization_args_.allow_snapshot_commands = false;
	update_stabilization_coordinates();
}

stabilization_smart_gcode::~stabilization_smart_gcode()
{
}

stabilization_smart_gcode::stabilization_smart_gcode(const stabilization_smart_gcode& source)
{
}

void stabilization_smart_gcode::process_pos(position* p_current_pos, position* p_previous_pos, bool found_command)
{
	if (process_snapshot_command(p_current_pos))
	{
		snapshot_commands_found_++;
		if (!p_current_pos->can_take_snapshot())
		{
			missed_snapshots_++;
			// ToDo:  Record more details about missed snapshot
		}
		else
		{
			add_plan_plan_from_snapshot_command(p_current_pos);
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
		replacement_token snapshot_command_text_token;
		snapshot_command_text_token.key = "snapshot_command_text";
		if (stabilization_args_.snapshot_command.gcode.size() > 0)
		{
			snapshot_command_text_token.value = ", ";
			snapshot_command_text_token.value += stabilization_args_.snapshot_command_text;
		}
		else
		{
			snapshot_command_text_token.value = "";
		}
		issue.replacement_tokens.push_back(snapshot_command_text_token);

		replacement_token snapshot_command_token;
		snapshot_command_token.key = "snapshot_command_gcode";
		if (stabilization_args_.snapshot_command.gcode.size() > 0)
		{
			snapshot_command_token.value = ", ";
			snapshot_command_token.value += stabilization_args_.snapshot_command.gcode;
		}
		else
		{
			snapshot_command_token.value = "";
		}
		issue.replacement_tokens.push_back(snapshot_command_token);


		issue.issue_type = stabilization_processing_issue_type_no_snapshot_commands_found;
		issues.push_back(issue);
	}
	return issues;
}


