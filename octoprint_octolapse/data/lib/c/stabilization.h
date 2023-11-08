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
#define _CRT_SECURE_NO_DEPRECATE
#include <string>
#include "position.h"
#include "gcode_position.h"
#include "snapshot_plan.h"
#include "stabilization_results.h"
#include <vector>
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif

static const char* travel_action = "travel";
static const char* snapshot_action = "snapshot";
static const char* send_parsed_command_first = "first";
static const char* send_parsed_command_last = "last";
static const char* send_parsed_command_never = "never";

class stabilization_args
{
public:
    stabilization_args()
    {
        height_increment = 0.0;
        notification_period_seconds = 0.25;
        file_path = "";
        x_coordinate = 0;
        y_coordinate = 0;
        x_stabilization_disabled = false;
        y_stabilization_disabled = false;
        allow_snapshot_commands = true;
        snapshot_command_text = "@OCTOLAPSE TAKE-SNAPSHOT";
        snapshot_command.command = "@OCTOLAPSE";
        parsed_command_parameter parameter;
        parameter.name = "TAKE-SNAPSHOT";
        snapshot_command.gcode = "@OCTOLAPSE TAKE-SNAPSHOT";
        snapshot_command.parameters.push_back(parameter);
    }

    ~stabilization_args()
    {
    }

    std::string file_path;
    double height_increment;
    double notification_period_seconds;

    /**
     * \brief If true, only @Octolapse commands will be processed.
     */
    bool allow_snapshot_commands;

    /**
     * \brief If true, the x axis will stabilize at the layer change point.
     */
    bool x_stabilization_disabled;
    /**
     * \brief If true, the y axis will stabilize at the layer change point.
     */
    bool y_stabilization_disabled;

    double x_coordinate;
    double y_coordinate;
    parsed_command snapshot_command;
    std::string snapshot_command_text;
};

typedef bool (*progressCallback)(double percentComplete, double seconds_elapsed, double estimatedSecondsRemaining,
    long gcodesProcessed, long linesProcessed);
typedef bool (*pythonProgressCallback)(PyObject* python_progress_callback, double percentComplete,
    double seconds_elapsed, double estimatedSecondsRemaining, int gcodesProcessed,
    int linesProcessed);
typedef bool (*pythonGetCoordinatesCallback)(PyObject* py_get_snapshot_position_callback, double x_initial,
    double y_initial, double& x_result, double& y_result);

class stabilization
{
public:

    stabilization();
    // constructor for use when running natively
    stabilization(gcode_position_args position_args, stabilization_args args, progressCallback progress);
    // constructor for use when being called from python
    stabilization(gcode_position_args position_args, stabilization_args args,
        pythonGetCoordinatesCallback get_coordinates, PyObject* py_get_coordinates_callback,
        pythonProgressCallback progress, PyObject* py_progress_callback);
    virtual ~stabilization();
    stabilization_results process_file();

private:
    stabilization(const stabilization& source); // don't copy me!
    double get_next_update_time() const;
    static double get_time_elapsed(double start_clock, double end_clock);
    bool has_python_callbacks_;
    // False if return < 0, else true
    pythonGetCoordinatesCallback _get_coordinates_callback;
    void notify_progress(double percent_progress, double seconds_elapsed, double seconds_to_complete,
        int gcodes_processed, int lines_processed);

    PyObject* py_on_progress_received;
    PyObject* py_get_snapshot_position_callback;

protected:
    /**
     * \brief Gets the next xy stabilization point
     * \param x The current x stabilization point, will be replaced with the next x point.
     * \param y The current y stabilization point, will be replaced with the next y point
     */
    void delete_gcode_parser();
    void delete_gcode_position();
    void get_next_xy_coordinates(double& x, double& y) const;
    virtual void process_pos(position* p_current_pos, position* p_previous_pos, bool found_command);
    virtual void on_processing_start();
    virtual void on_processing_complete();
    virtual std::vector<stabilization_processing_issue> get_internal_processing_issues();
    virtual std::vector<stabilization_quality_issue> get_quality_issues();
    virtual std::vector<stabilization_processing_issue> get_processing_issues();
    bool process_snapshot_command(position* p_cur_pos);
    void process_snapshot_command_parameters(position* p_cur_pos);
    void add_plan_plan_from_snapshot_command(position* p_position);
    void update_stabilization_coordinates();
    std::vector<snapshot_plan> p_snapshot_plans_;
    bool is_running_;
    gcode_position_args gcode_position_args_;
    stabilization_args stabilization_args_;
    progressCallback native_progress_callback_;
    pythonProgressCallback progress_callback_;
    gcode_position* gcode_position_;
    gcode_parser* gcode_parser_;
    long get_file_size(const std::string& file_path);
    long file_size_;
    int lines_processed_;
    int gcodes_processed_;
    long file_position_;
    int missed_snapshots_;
    bool snapshots_enabled_;
    double stabilization_x_;
    double stabilization_y_;
};
#endif
