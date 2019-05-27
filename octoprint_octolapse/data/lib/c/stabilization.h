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

#ifndef STABILIZATION_H
#define STABILIZATION_H
#include <string>
#include "position.h"
#include "gcode_position.h"
#include "snapshot_plan.h"
#include "stabilization_results.h"
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
#include <vector>
static const char* travel_action = "travel";
static const char* snapshot_action = "snapshot";
static const char* send_parsed_command_first = "first";
static const char* send_parsed_command_last = "last";
static const char* send_parsed_command_never = "never";

class stabilization_args {
public:
	stabilization_args();
	~stabilization_args();
	PyObject* py_on_progress_received;
	std::string stabilization_type_;
	std::string file_path_;
	double height_increment_;
	double notification_period_seconds_;
	bool fastest_speed_;
};
typedef bool(*progressCallback)(double percentComplete, double seconds_elapsed, double estimatedSecondsRemaining, long gcodesProcessed, long linesProcessed);
typedef bool(*pythonProgressCallback)(PyObject* python_progress_callback, double percentComplete, double seconds_elapsed, double estimatedSecondsRemaining, long gcodesProcessed, long linesProcessed);

class NotImplemented : public std::logic_error
{
public:
	NotImplemented() : std::logic_error("Function not yet implemented") { };
};

class stabilization
{
public:

	stabilization();
	// constructor for use when running natively
	stabilization(gcode_position_args* position_args, stabilization_args* args, progressCallback progress);
	// constructor for use when being called from python
	stabilization(gcode_position_args* position_args, stabilization_args* args, pythonProgressCallback progress);
	virtual ~stabilization();
	void process_file(stabilization_results* results);
	
private:
	stabilization(const stabilization &source); // don't copy me!
	double update_period_seconds_;
	double get_next_update_time() const;
	static double get_time_elapsed(double start_clock, double end_clock);
	bool python_callbacks_;
	void notify_progress(double percent_progress, double seconds_elapsed, double seconds_to_complete,
		long gcodes_processed, long lines_processed);
	gcode_position_args* p_args_;
protected:
	virtual void process_pos(position* p_current_pos, position* p_previous_pos);
	virtual void on_processing_complete();
	
	/**
	 * \brief Gets the current commands required to perform a wipe if fully retracted.
	 * \return 
	 */
	void get_current_wipe_steps(std::vector<gcode_wiper_step*> &wipe_steps);
	/**
	 * \brief Gets the wipe commands from the previous position.  This will perform an undo on the
	 * current gcode_position processor, will fetch the wipe commands, then will re-update the position
	 * leaving it in the original state.
	 * \param wipe_commands The wipe commands will be copied here
	 */
	void get_previous_wipe_steps(std::vector<gcode_wiper_step*> &wipe_steps);
	void delete_saved_wipe_steps();
	void move_saved_wipe_steps(std::vector<gcode_wiper_step*> &target);
	std::vector<gcode_wiper_step*> saved_wipe_steps_;
	std::vector<snapshot_plan*>* p_snapshot_plans_;
	bool is_running_;
	std::string errors_;
	stabilization_args* p_stabilization_args_;
	progressCallback native_progress_callback_;
	pythonProgressCallback progress_callback_;
	PyObject* python_progress_callback_;
	gcode_position* gcode_position_;
	gcode_parser* gcode_parser_;
	long get_file_size(const std::string& file_path);
	long file_size_;
	long lines_processed_;
	long gcodes_processed_;

	
};
#endif