///////////////////////////////////////////////////////////////////////////////////
// Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
// Copyright(C) 2019  Brad Hochgesang
///////////////////////////////////////////////////////////////////////////////////
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
///////////////////////////////////////////////////////////////////////////////////
#ifndef STABILIZATION_H
#define STABILIZATION_H
#include "Position.h"
#include "GcodePosition.h"
#include "SnapshotPlan.h"
#include "StabilizationResults.h"
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

typedef struct stabilization_args {
	stabilization_args() {
		is_bound = false;
		x_min = 0;
		x_max = 0;
		y_min = 0;
		y_max = 0;
		z_min = 0;
		z_max = 0;
		stabilization_type = "";
		disable_retract = false;
		retraction_length = 0.0;
		disable_z_lift = false;
		z_lift_height = 0.0;
		height_increment = 0.0;
		notification_period_seconds = 0.25;
	};
	position_args position_args;
	bool is_bound;
	double x_min;
	double x_max;
	double y_min;
	double y_max;
	double z_min;
	double z_max;
	std::string stabilization_type;
	bool disable_retract;
	double retraction_length;
	bool disable_z_lift;
	double z_lift_height;
	double height_increment;
	double notification_period_seconds;
} stabilization_args;

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
	stabilization(stabilization_args* args, progressCallback progress);
	// constructor for use when being called from python
	stabilization(stabilization_args* args, pythonProgressCallback progress, PyObject * python_progress);
	virtual ~stabilization();
	stabilization_results* process_file(const std::string& file_path);

private:
	stabilization(const stabilization &source); // don't copy me!
	double update_period_seconds_;
	double get_next_update_time() const;
	static double get_time_elapsed(double start_clock, double end_clock);
	bool python_callbacks;
	void notify_progress(double percent_progress, double seconds_elapsed, double seconds_to_complete,
		long gcodes_processed, long lines_processed);
	position_args* p_args_;
protected:
	virtual void process_pos(position* p_current_pos, parsed_command* p_command);
	virtual void on_processing_complete();
	std::vector<snapshot_plan*>* p_snapshot_plans;
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
