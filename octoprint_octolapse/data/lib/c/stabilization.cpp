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
#include <time.h>
#include <vector>
#include <sstream>
#include "logging.h"
#include "utilities.h"
#include <iostream>
#include <fstream>

stabilization::stabilization(gcode_position_args position_args, stabilization_args stab_args, pythonGetCoordinatesCallback get_coordinates_callback, PyObject* py_get_coordinates_callback, pythonProgressCallback progress_callback, PyObject* py_progress_callback)
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
	is_running_ = true;
	gcode_parser_ = new gcode_parser();
	gcode_position_ = new gcode_position(position_args);
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	file_position_ = 0;
	missed_snapshots_ = 0;
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	
}

stabilization::stabilization()
{
	std::string errors_;
	has_python_callbacks_ = false;
	native_progress_callback_ = NULL;
	progress_callback_ = NULL;
	stabilization_args_ = stabilization_args();
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
	
}

stabilization::stabilization(gcode_position_args position_args, stabilization_args args, progressCallback progress)
{
	std::string errors_; 
	has_python_callbacks_ = false;
	native_progress_callback_ = progress;
	progress_callback_ = NULL;
	stabilization_args_ = args;
	is_running_ = true;
	gcode_parser_ = new gcode_parser();
	gcode_position_ = new gcode_position(position_args);
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
	
}

stabilization::stabilization(const stabilization &source)
{
	// Private copy constructor, don't copy me!	
	throw std::exception();
}

stabilization::~stabilization()
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
	if (py_on_progress_received != NULL)
		Py_XDECREF(py_on_progress_received);
	if (py_get_snapshot_position_callback != NULL)
		Py_XDECREF(py_get_snapshot_position_callback);
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
	int read_lines_before_clock_check = 1000;
	//std::cout << "stabilization::process_file - Processing file.\r\n";
	octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Processing File.");
	is_running_ = true;
	
	double next_update_time = get_next_update_time();
	const clock_t start_clock = clock();

	file_size_ = get_file_size(stabilization_args_.file_path);

	std::ifstream gcodeFile(stabilization_args_.file_path.c_str());
	std::string line;
	int lines_with_no_commands = 0;
	if (gcodeFile.is_open())
	{
		parsed_command cmd;
		// Communicate every second
		while (std::getline(gcodeFile, line) && is_running_)
		{
			file_position_ = static_cast<long>(gcodeFile.tellg());
			lines_processed_++;

			cmd.clear();
			bool found_command = gcode_parser_->try_parse_gcode(line.c_str(), cmd);
			if (cmd.gcode.length() > 0)
			{
				gcodes_processed_++;
			}
			else
			{
				lines_with_no_commands++;
			}

			// Always process the command through the printer, even if no command is found
			// This is important so that comments can be analyzed
			//std::cout << "stabilization::process_file - updating position...";
			gcode_position_->update(cmd, lines_processed_, gcodes_processed_, file_position_);

			// Only continue to process if we've found a command.
			if (found_command)
			{
				process_pos(gcode_position_->get_current_position_ptr(), gcode_position_->get_previous_position_ptr());

				if ( (lines_processed_ % read_lines_before_clock_check) == 0 && next_update_time < clock())
				{
					// ToDo: tellg does not do what I think it does, but why?
					long bytesRemaining = file_size_ - file_position_;
					double percentProgress = static_cast<double>(file_position_) / static_cast<double>(file_size_)*100.0;
					double secondsElapsed = get_time_elapsed(start_clock, clock());
					double bytesPerSecond = static_cast<double>(file_position_) / secondsElapsed;
					double secondsToComplete = bytesRemaining / bytesPerSecond;
					//std::cout << "stabilization::process_file - notifying progress...";
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
		octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::ERROR, "Unable to open the gcode file.");
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


	std::stringstream sstm;
	sstm << "Completed file processing\r\n";
	sstm << "\tSnapshots Found      : " << results.snapshot_plans.size() << "\r\n";
	sstm << "\tTotal Seconds        : " << total_seconds << "\r\n";
	sstm << "\tSnapshot Plan Details:";
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
		sstm << "\r\n";
		sstm << "\t\tPlan# " << index + 1;
		sstm << ", Layer:" << pPlan.initial_position.layer;
		sstm << ", Line:" << pPlan.file_line;
		sstm << ", Position:" << pPlan.file_position;
		sstm << ", StartX:" << pPlan.initial_position.x;
		sstm << ", StartY:" << pPlan.initial_position.y;
		sstm << ", StartZ:" << pPlan.initial_position.z;
		sstm << ", Tool:" << pPlan.initial_position.current_tool;
		sstm << ", Speed:" << pPlan.initial_position.f;
		sstm << ", Distance:" << pPlan.distance_from_stabilization_point;
		sstm << ", Travel Distance:" << pPlan.total_travel_distance;
		sstm << ", Type:" << feature_type_description;
		sstm << ", Gcode:" << utilities::trim(pPlan.start_command.gcode);
		if (pPlan.start_command.comment.length() > 0)
			sstm << ", Comment: " << pPlan.start_command.comment;
	}

	octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, sstm.str());
	return results;
}

void stabilization::notify_progress(const double percent_progress, const double seconds_elapsed, const double seconds_to_complete,
	const int gcodes_processed, const int lines_processed)
{
	if (has_python_callbacks_)
	{
		is_running_ = progress_callback_(py_on_progress_received, percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed, lines_processed);
	}
	else if(native_progress_callback_ != NULL)
	{
		is_running_ = native_progress_callback_(percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed, lines_processed);
	}

}

void stabilization::process_pos(position* current_pos, position* previous_pos)
{
	throw std::exception();
}

void stabilization::on_processing_complete()
{
	throw std::exception();
}

std::vector<stabilization_quality_issue> stabilization::get_quality_issues()
{
	throw std::exception();
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
	
	return issues;
}


void stabilization::get_next_xy_coordinates(double &x, double&y) const
{
	//octolapse_log(octolapse_log::SNAPSHOT_PLAN, octolapse_log::INFO, "Getting stabilization coordinates.");
	//std::cout << "Getting XY stabilization coordinates...";
	double x_ret, y_ret;
	if (has_python_callbacks_)
	{
		//std::cout << "calling python...";
		if (!_get_coordinates_callback(py_get_snapshot_position_callback, stabilization_args_.x_coordinate, stabilization_args_.y_coordinate, x_ret, y_ret))
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




