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
#include "Stabilization.h"
#include <fstream>
#include <time.h>
#include <iostream>
#include <vector>
#include "Logging.h"



stabilization::stabilization(
	gcode_position_args* position_args, stabilization_args* stab_args, pythonProgressCallback progress
)
{
	std::string errors_;
	if (stab_args->py_on_progress_received != NULL)
	{
		python_callbacks = true;
		python_progress_callback_ = stab_args->py_on_progress_received;
	}
	else
	{
		python_callbacks = false;
		python_progress_callback_ = NULL;
	}
	progress_callback_ = progress;
	native_progress_callback_ = NULL;
	p_stabilization_args_ = stab_args;
	is_running_ = true;
	gcode_parser_ = new gcode_parser();
	gcode_position_ = new gcode_position(position_args);
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	update_period_seconds_ = stab_args->notification_period_seconds;
}

stabilization::stabilization()
{
	std::string errors_;
	python_callbacks = false;
	native_progress_callback_ = NULL;
	python_progress_callback_ = NULL;
	progress_callback_ = NULL;
	p_stabilization_args_ = NULL;
	is_running_ = true;
	gcode_parser_ = NULL;
	gcode_position_ = NULL;
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	update_period_seconds_ = 0.25;
}

stabilization::stabilization(gcode_position_args* position_args, stabilization_args* args, progressCallback progress)
{
	std::string errors_; 
	python_callbacks = false;
	native_progress_callback_ = progress;
	python_progress_callback_ = NULL;
	progress_callback_ = NULL;
	p_stabilization_args_ = args;
	is_running_ = true;
	gcode_parser_ = new gcode_parser();
	gcode_position_ = new gcode_position(position_args);
	file_size_ = 0;
	lines_processed_ = 0;
	gcodes_processed_ = 0;
	update_period_seconds_ = args->notification_period_seconds;
}

stabilization::stabilization(const stabilization &source)
{
	// Private copy constructor, don't copy me!	
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
	
}

long stabilization::get_file_size(const std::string& file_path)
{
	// Todo:  Fix this function.  This is a pretty weak implementation :(
	std::ifstream file(file_path.c_str(), std::ios::in | std::ios::binary);
	const long l = file.tellg();
	file.seekg(0, std::ios::end);
	const long m = file.tellg();
	file.close();
	return (m - l);
}

double stabilization::get_next_update_time() const
{
	return clock() + (update_period_seconds_ * CLOCKS_PER_SEC);
}

double stabilization::get_time_elapsed(double start_clock, double end_clock)
{
	return static_cast<double>(end_clock - start_clock) / CLOCKS_PER_SEC;
}

void stabilization::process_file(stabilization_results* results)
{
	
	p_snapshot_plans = &results->snapshot_plans;
	//std::cout << "stabilization::process_file - Processing file.\r\n";
	octolapse_log(SNAPSHOT_PLAN, INFO, "Processing File.");
	PyThreadState *_save = NULL;
	is_running_ = true;
	
	double next_update_time = get_next_update_time();
	const clock_t start_clock = clock();

	// todo : clear out everything for a fresh go!
	file_size_ = get_file_size(p_stabilization_args_->file_path);
	std::ifstream gcodeFile(p_stabilization_args_->file_path.c_str());
	std::string line;

	if (gcodeFile.is_open())
	{
		// Communicate every second
		parsed_command* cmd = new parsed_command();
		while (std::getline(gcodeFile, line) && is_running_)
		{
			lines_processed_++;
			cmd->clear();
			//std::cout << "stabilization::process_file - parsing gcode: " << line << "...";
			gcode_parser_->try_parse_gcode(line.c_str(), cmd);
			//std::cout << "Complete.\r\n";
			if (!cmd->cmd.empty())
			{

				gcodes_processed_++;
				//std::cout << "stabilization::process_file - updating position...";
				gcode_position_->update(cmd, lines_processed_, gcodes_processed_);
				//std::cout << "Complete.\r\n";
				process_pos(gcode_position_->p_current_pos, gcode_position_->p_previous_pos);
				if (next_update_time < clock())
				{
					// ToDo: tellg does not do what I think it does, but why?
					long currentPosition = gcodeFile.tellg();
					long bytesRemaining = file_size_ - currentPosition;
					double percentProgress = (double)currentPosition / (double)file_size_*100.0;
					double secondsElapsed = get_time_elapsed(start_clock, clock());
					double bytesPerSecond = (double)currentPosition / secondsElapsed;
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
		delete cmd;
		//std::cout << "stabilization::process_file - Completed Processing file.\r\n";
	}

	const clock_t end_clock = clock();
	const double total_seconds = static_cast<double>(end_clock - start_clock) / CLOCKS_PER_SEC;
	results->success = errors_.empty();
	results->errors = errors_;
	results->seconds_elapsed = total_seconds;
	results->gcodes_processed = gcodes_processed_;
	results->lines_processed = lines_processed_;
	octolapse_log(SNAPSHOT_PLAN, INFO, "Completed file processing.");
	p_snapshot_plans = NULL;
}

double stabilization::get_carteisan_distance(double x1, double y1, double x2, double y2)
{
	// Compare the saved points cartesian distance from the current point
	double xdif = x1 - x2;
	double ydif = y1 - y2;
	double dist_squared = xdif * xdif + ydif * ydif;
	if (dist_squared < 0)
	{
		//std::cout << "Negative Distance found!  Returning -1\r\n";
		return -1.0;
	}
	return sqrt(xdif*xdif + ydif * ydif);
}

void stabilization::notify_progress(const double percent_progress, const double seconds_elapsed, const double seconds_to_complete,
	const long gcodes_processed, const long lines_processed)
{
	if (python_callbacks)
	{
		is_running_ = progress_callback_(python_progress_callback_, percent_progress, seconds_elapsed, seconds_to_complete, gcodes_processed, lines_processed);
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



stabilization_args::stabilization_args() 
{
	stabilization_type = "";
	is_bound = false;
	x_min = 0;
	x_max = 0;
	y_min = 0;
	y_max = 0;
	z_min = 0;
	z_max = 0;
	height_increment = 0.0;
	disable_retract = false;
	disable_z_lift = false;
	notification_period_seconds = 0.25;
	fastest_speed = true;
	// Gcode Generation Settings
	retraction_length = 0.0;
	z_lift_height = 0.0;
	file_path = "";
};

stabilization_args::~stabilization_args()
{

}

