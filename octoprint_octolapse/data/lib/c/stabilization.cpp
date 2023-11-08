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
#include "stabilization.h"
#include <ctime>
#include <vector>
#include <sstream>
#include "logging.h"
#include "utilities.h"
#include <iostream>
#include <fstream>

stabilization::stabilization(gcode_position_args position_args, stabilization_args stab_args,
	pythonGetCoordinatesCallback get_coordinates_callback,
	PyObject* py_get_coordinates_callback, pythonProgressCallback progress_callback,
	PyObject* py_progress_callback)
{
	std::string errors_;
	if (py_get_coordinates_callback != NULL && py_progress_callback != NULL)
	{
		has_python_callbacks_ = true;
	}
	else
	{
		has_python_callbacks_ = false;
	}
	progress_callback_ = progress_callback;
	_get_coordinates_callback = get_coordinates_callback;
	py_on_progress_received = py_progress_callback;
	py_get_snapshot_position_callback = py_get_coordinates_callback;
	native_progress_callback_ = NULL;
	stabilization_args_ = stab_args;
	gcode_position_args_ = position_args;
	is_running_ = true;
	gcode_parser_ = NULL;
	gcode_position_ = NULL;
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	file_position_ = 0;
	missed_snapshots_ = 0;
	snapshots_enabled_ = true;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	update_stabilization_coordinates();
}

stabilization::stabilization()
{
	std::string errors_;
	has_python_callbacks_ = false;
	native_progress_callback_ = NULL;
	progress_callback_ = NULL;
	stabilization_args_ = stabilization_args();
	gcode_position_args_ = gcode_position_args();
	is_running_ = true;
	gcode_parser_ = NULL;
	gcode_position_ = NULL;
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	file_position_ = 0;
	missed_snapshots_ = 0;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	_get_coordinates_callback = NULL;
	py_on_progress_received = NULL;
	py_get_snapshot_position_callback = NULL;
	snapshots_enabled_ = true;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	update_stabilization_coordinates();
}

stabilization::stabilization(gcode_position_args position_args, stabilization_args args, progressCallback progress)
{
	std::string errors_;
	has_python_callbacks_ = false;
	native_progress_callback_ = progress;
	progress_callback_ = NULL;
	stabilization_args_ = args;
	gcode_position_args_ = position_args;
	is_running_ = true;
	gcode_parser_ = NULL;
	gcode_position_ = NULL;
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	file_position_ = 0;
	missed_snapshots_ = 0;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	_get_coordinates_callback = NULL;
	py_on_progress_received = NULL;
	py_get_snapshot_position_callback = NULL;
	snapshots_enabled_ = true;
}

stabilization::stabilization(const stabilization& source)
{
	// Private copy constructor, don't copy me!	
	throw std::exception();
}

stabilization::~stabilization()
{
	delete_gcode_parser();
	delete_gcode_position();

	if (gcode_position_ != NULL)
	{
		delete gcode_position_;
		gcode_position_ = NULL;
	}
	if (py_on_progress_received != NULL)
		Py_XDECREF(py_on_progress_received);
	if (py_get_snapshot_position_callback != NULL)
		Py_XDECREF(py_get_snapshot_position_callback);
}

void stabilization::delete_gcode_parser()
{
	if (gcode_parser_ != NULL)
	{
		delete gcode_parser_;
		gcode_parser_ = NULL;
	}
}

void stabilization::delete_gcode_position()
{
	if (gcode_position_ != NULL)
	{
		delete gcode_position_;
		gcode_position_ = NULL;
	}
}

long stabilization::get_file_size(const std::string& file_path)
{
	// Todo:  Fix this function.  This is a pretty weak implementation :(
	std::ifstream file(file_path.c_str(), std::ios::in | std::ios::binary);
	const long l = (long)file.tellg();
	file.seekg(0, std::ios::end);
	const long m = (long)file.tellg();
	file.close();
	return (m - l);
}

double stabilization::get_next_update_time() const
{
	return clock() + (stabilization_args_.notification_period_seconds * CLOCKS_PER_SEC);
}

double stabilization::get_time_elapsed(double start_clock, double end_clock)
{
	return static_cast<double>(end_clock - start_clock) / CLOCKS_PER_SEC;
}

stabilization_results stabilization::process_file()
{
	if (gcode_parser_ != NULL)
	{
		delete gcode_parser_;
		gcode_parser_ = NULL;
	}
	if (gcode_position_ != NULL)
	{
		delete gcode_position_;
		gcode_position_ = NULL;
	}
	on_processing_start();
	// Construct the gcode_parser and gcode_position objects.
	gcode_parser_ = new gcode_parser();
	gcode_position_ = new gcode_position(gcode_position_args_);
	// Create a stringstream we can use for messaging.
	std::stringstream stream;
	// Make sure snapshots are enabled at the start of the process.
	snapshots_enabled_ = true;
	int read_lines_before_clock_check = 2000;
	std::cout << "stabilization::process_file - Processing file.\r\n";
	stream << "Stabilizing file at: " << stabilization_args_.file_path;
	octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, stream.str());
	is_running_ = true;

	double next_update_time = get_next_update_time();
	const clock_t start_clock = clock();
	file_size_ = get_file_size(stabilization_args_.file_path);

	std::string path = stabilization_args_.file_path;


#ifdef _MSC_VER


	std::wstring wpath = utilities::ToUtf16(path);
	stream << "Windows detected, encoding file as UTF16";
	octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, stream.str());
	std::ifstream gcodeFile(wpath.c_str());


#else
	std::ifstream gcodeFile(path.c_str());
#endif



	std::string line;
	int lines_with_no_commands = 0;
	if (gcodeFile.is_open())
	{
		stream.clear();
		stream.str("");
		stream << "Opened file for reading.  File Size: " << utilities::to_string(file_size_);
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, stream.str());
		parsed_command cmd;
		// Communicate every second
		while (std::getline(gcodeFile, line) && is_running_)
		{
			file_position_ = static_cast<long>(gcodeFile.tellg());
			lines_processed_++;

			cmd.clear();
			bool found_command = gcode_parser_->try_parse_gcode(line.c_str(), cmd);
			bool has_gcode = false;
			if (cmd.gcode.length() > 0)
			{
				has_gcode = true;
				gcodes_processed_++;
			}
			else
			{
				lines_with_no_commands++;
			}
			// If the current command is an @Octolapse command, check the paramaters and update any state as necessary
			if (cmd.command == "@OCTOLAPSE")
			{
				if (cmd.parameters.size() == 1)
				{
					parsed_command_parameter param = cmd.parameters[0];
					if (param.name == "STOP-SNAPSHOTS")
					{
						if (snapshots_enabled_)
						{
							octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO,
								"@Octolapse command detected - STOP-SNAPSHOTS - snapshots stopped.");
							snapshots_enabled_ = false;
						}
						else
						{
							octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO,
								"@Octolapse command detected - STOP-SNAPSHOTS - snapshots already stopped, command ignored.");
						}
					}
					else if (param.name == "START-SNAPSHOTS")
					{
						if (!snapshots_enabled_)
						{
							octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO,
								"@Octolapse command detected - START-SNAPSHOTS - snapshots started.");
							snapshots_enabled_ = true;
						}
						else
						{
							octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO,
								"@Octolapse command detected - START-SNAPSHOTS - snapshots already started, command ignored.");
						}
					}
				}
			}

			// Always process the command through the printer, even if no command is found
			// This is important so that comments can be analyzed
			//std::cout << "stabilization::process_file - updating position...";
			gcode_position_->update(cmd, lines_processed_, gcodes_processed_, file_position_);

			// Only continue to process if we've found a command.
			if (has_gcode)
			{
				if (snapshots_enabled_)
				{
					position* currentPositionPtr = gcode_position_->get_current_position_ptr();
					if (stabilization_args_.allow_snapshot_commands && process_snapshot_command(currentPositionPtr) && currentPositionPtr->can_take_snapshot())
					{
						// If we've received a snapshot command, and this isn't the smart gcode stabilizastion, add the snapshot
						add_plan_plan_from_snapshot_command(currentPositionPtr);
					}
					else
					{
						// process the position as usual
						process_pos(currentPositionPtr, gcode_position_->get_previous_position_ptr(), found_command);
					}

				}

				if ((lines_processed_ % read_lines_before_clock_check) == 0 && next_update_time < clock())
				{
					// ToDo: tellg does not do what I think it does, but why?
					long bytesRemaining = file_size_ - file_position_;
					double percentProgress = static_cast<double>(file_position_) / static_cast<double>(file_size_) * 100.0;
					double secondsElapsed = get_time_elapsed(start_clock, clock());
					double bytesPerSecond = static_cast<double>(file_position_) / secondsElapsed;
					double secondsToComplete = bytesRemaining / bytesPerSecond;
					//std::cout << "stabilization::process_file - notifying progress...";

					stream.clear();
					stream.str("");
					stream << "Stabilization Progress - Bytes Remaining: " << bytesRemaining <<
						", Seconds Elapsed: " << utilities::to_string(secondsElapsed) << ", Percent Progress:" << utilities::
						to_string(percentProgress);
					octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::DEBUG, stream.str());
					notify_progress(percentProgress, secondsElapsed, secondsToComplete, gcodes_processed_,
						lines_processed_);
					//std::cout << "Complete.\r\n";
					next_update_time = get_next_update_time();
				}
			}
		}
		// deallocate the parsed_command object

		gcodeFile.close();
		on_processing_complete();
		//std::cout << "stabilization::process_file - Completed Processing file.\r\n";
	}
	else
	{
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::ERROR, "Unable to open the gcode file for processing.");
	}
	const clock_t end_clock = clock();
	const double total_seconds = static_cast<double>(end_clock - start_clock) / CLOCKS_PER_SEC;
	stabilization_results results;
	results.seconds_elapsed = total_seconds;
	results.gcodes_processed = gcodes_processed_;
	results.lines_processed = lines_processed_;
	results.quality_issues = get_quality_issues();
	results.snapshot_plans = p_snapshot_plans_;
	results.processing_issues = get_processing_issues();
	// Calculate number of missed layers
	results.missed_layer_count = missed_snapshots_;
	stream.clear();
	stream.str("");
	stream << "Completed file processing\r\n";
	stream << "\tBytes Processed      : " << file_position_ << "\r\n";
	stream << "\tLines Processed      : " << lines_processed_ << "\r\n";
	stream << "\tSnapshots Found      : " << results.snapshot_plans.size() << "\r\n";
	stream << "\tTotal Seconds        : " << total_seconds << "\r\n";
	octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, stream.str());
	// Try to avoid logging the snapshot plan if it definitely won't be logged
	if (octolapse_may_be_logged(octolapse_log::SNAPSHOT_PLAN, octolapse_log::DEBUG))
	{
		stream.clear();
		stream.str("");
		stream << "Snapshot Plan Details:";
		for (unsigned int index = 0; index < results.snapshot_plans.size(); index++)
		{
			snapshot_plan pPlan = results.snapshot_plans[index];
			std::string gcode = pPlan.start_command.gcode;
			std::string feature_type_description = "unknown";
			if (pPlan.triggering_command_feature_type != feature_type_unknown_feature)
			{
				feature_type_description = "feature-";
				feature_type_description += feature_type_name[pPlan.triggering_command_feature_type];
			}
			else
				feature_type_description = position_type_name[pPlan.triggering_command_type];
			stream << "\r\n";
			stream << "\tPlan# " << index + 1;
			stream << ", Layer:" << pPlan.initial_position.layer;
			stream << ", Line:" << pPlan.file_line;
			stream << ", Position:" << pPlan.file_position;
			stream << ", StartX:" << pPlan.initial_position.x;
			stream << ", StartY:" << pPlan.initial_position.y;
			stream << ", StartZ:" << pPlan.initial_position.z;
			stream << ", Tool:" << pPlan.initial_position.current_tool;
			stream << ", Speed:" << pPlan.initial_position.f;
			stream << ", Distance:" << pPlan.distance_from_stabilization_point;
			stream << ", Travel Distance:" << pPlan.total_travel_distance;
			stream << ", Type:" << feature_type_description;
			stream << ", Gcode:" << pPlan.start_command.gcode;
			if (pPlan.start_command.comment.length() > 0)
				stream << ", Comment: " << pPlan.start_command.comment;
		}
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::DEBUG, stream.str());
	}
	return results;
}

void stabilization::notify_progress(const double percent_progress, const double seconds_elapsed,
	const double seconds_to_complete,
	const int gcodes_processed, const int lines_processed)
{
	if (has_python_callbacks_)
	{
		is_running_ = progress_callback_(py_on_progress_received, percent_progress, seconds_elapsed, seconds_to_complete,
			gcodes_processed, lines_processed);
	}
	else if (native_progress_callback_ != NULL)
	{
		is_running_ = native_progress_callback_(percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed,
			lines_processed);
	}
}

void stabilization::process_pos(position* current_pos, position* previous_pos, bool found_command)
{
	throw std::exception();
}

void stabilization::on_processing_start()
{
	// empty by default
}

void stabilization::on_processing_complete()
{
	throw std::exception();
}

std::vector<stabilization_quality_issue> stabilization::get_quality_issues()
{
	throw std::exception();
}

std::vector<stabilization_processing_issue> stabilization::get_internal_processing_issues()
{
	return std::vector<stabilization_processing_issue>();
}

std::vector<stabilization_processing_issue> stabilization::get_processing_issues()
{
	// Create a vector to hold the processing issue
	std::vector<stabilization_processing_issue> issues;
	// retrieve the current position object;
	position pos = gcode_position_->get_current_position();

	if (pos.is_relative_null)
	{
		// Add issue for missing xyz axis type
		stabilization_processing_issue issue;
		issue.description = "The XYZ axis mode was not set in the gcode file.";
		issue.issue_type = stabilization_processing_issue_type_xyz_axis_mode_unknown;
		issues.push_back(issue);
	}

	if (pos.is_extruder_relative_null)
	{
		// Add issue for missing e axis type
		stabilization_processing_issue issue;
		issue.description = "The E axis mode was not set in the gcode file.";
		issue.issue_type = stabilization_processing_issue_type_e_axis_mode_unknown;
		issues.push_back(issue);
	}

	if (!pos.has_definite_position)
	{
		// Add issue for no definite position
		stabilization_processing_issue issue;
		issue.description = "No definite position found.";
		issue.issue_type = stabilization_processing_issue_type_no_definite_position;
		issues.push_back(issue);
	}

	if (!pos.is_printer_primed)
	{
		// Add issue for no prime detected
		stabilization_processing_issue issue;
		issue.description = "Priming was not detected.";
		issue.issue_type = stabilization_processing_issue_type_printer_not_primed;
		issues.push_back(issue);
	}

	if (pos.is_metric_null)
	{
		// Add issue for metri  null
		stabilization_processing_issue issue;
		issue.description = "Units are not metric.";
		issue.issue_type = stabilization_processing_issue_type_no_metric_units;
		issues.push_back(issue);
	}

	// Get all internal issues of any override classes
	std::vector<stabilization_processing_issue> internal_issues = get_internal_processing_issues();
	// Add these issues to the master list
	for (std::vector<stabilization_processing_issue>::iterator it = internal_issues.begin(); it != internal_issues.end();
		++it)
	{
		issues.push_back(*it);
	}
	return issues;
}


void stabilization::get_next_xy_coordinates(double& x, double& y) const
{
	//octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Getting stabilization coordinates.");
	//std::cout << "Getting XY stabilization coordinates...";
	double x_ret, y_ret;
	if (has_python_callbacks_)
	{
		//std::cout << "calling python...";
		if (!_get_coordinates_callback(py_get_snapshot_position_callback, stabilization_args_.x_coordinate,
			stabilization_args_.y_coordinate, x_ret, y_ret))
			octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Failed dto get snapshot coordinates.");
	}
	else
	{
		//std::cout << "extracting from args...";
		x_ret = stabilization_args_.x_coordinate;
		y_ret = stabilization_args_.y_coordinate;
	}
	x = x_ret;
	y = y_ret;
	//std::cout << " - X coord: " << x;
	//std::cout << " - Y coord: " << y << "\r\n";
}

void stabilization::process_snapshot_command_parameters(position* p_cur_pos)
{
	double x = stabilization_x_;
	double y = stabilization_y_;

	for (std::vector<parsed_command_parameter>::const_iterator it = p_cur_pos->command.parameters.begin(); it != p_cur_pos
		->command
		.parameters
		.end();
		++it)
	{
		if ((*it).name == "X")
		{
			x = (*it).double_value;
		}
		else if ((*it).name == "Y")
		{
			y = (*it).double_value;
		}
	}
}

bool stabilization::process_snapshot_command(position* p_cur_pos)
{
	if (p_cur_pos->command.command == "@OCTOLAPSE")
	{
		bool ret_val = false;
		for (std::vector<parsed_command_parameter>::const_iterator it = p_cur_pos->command.parameters.begin(); it !=
			p_cur_pos->command.parameters.end(); ++it)
		{
			if ((*it).name == "TAKE-SNAPSHOT")
			{
				// Todo:  Figure out what to do here
				//process_snapshot_command_parameters(p_cur_pos);
				ret_val = true;
				break;
			}
		}
		return ret_val;
	}

	else if (
		stabilization_args_.snapshot_command.gcode.size() > 0 &&
		(
			stabilization_args_.snapshot_command.gcode == p_cur_pos->command.gcode
		)
	){
		return true;
	}
	else if (p_cur_pos->command.gcode == "SNAP") // Backwards Compatibility
	{
		return true;
	}
	return false;
}

void stabilization::add_plan_plan_from_snapshot_command(position* p_position)
{
	//std::cout << "Adding saved plan to plans...  F Speed" << p_saved_position_->f_ << " \r\n";
	snapshot_plan p_plan;
	double total_travel_distance;
	total_travel_distance = utilities::get_cartesian_distance(p_position->x, p_position->y, stabilization_x_,
		stabilization_y_);

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
	const bool all_stabilizations_disabled = stabilization_args_.x_stabilization_disabled && stabilization_args_.
		y_stabilization_disabled;

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

void stabilization::update_stabilization_coordinates()
{
	get_next_xy_coordinates(stabilization_x_, stabilization_y_);
}
