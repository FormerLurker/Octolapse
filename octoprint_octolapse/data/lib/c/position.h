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

#ifndef POSITION_H
#define POSITION_H
#include <string>
#include "parsed_command.h"
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif

class position
{
public:
	position();
	position(position &source);
	position(const std::string& xyz_axis_default_mode, const std::string& e_axis_default_mode, const std::string&
	         units_default);
	~position();
	static void copy(position &source, position* target);
	void reset_state();
	PyObject * to_py_tuple();
	PyObject * to_py_dict();
	parsed_command* p_command;
	double f_;
	bool f_null_;
	double x_;
	bool x_null_;
	double x_offset_;
	bool x_homed_;
	double y_;
	bool y_null_;
	double y_offset_;
	bool y_homed_;
	double z_;
	bool z_null_;
	double z_offset_;
	bool z_homed_;
	double e_;
	double e_offset_;
	bool is_relative_;
	bool is_relative_null_;
	bool is_extruder_relative_;
	bool is_extruder_relative_null_;
	bool is_metric_;
	bool is_metric_null_;
	double last_extrusion_height_;
	bool last_extrusion_height_null_;
	int layer_;
	double height_;
	bool is_printer_primed_;
	bool minimum_layer_height_reached_;
	double firmware_retraction_length_;
	bool firmware_retraction_length_null_;
	double firmware_unretraction_additional_length_;
	bool firmware_unretraction_additional_length_null_;
	double firmware_retraction_feedrate_;
	bool firmware_retraction_feedrate_null_;
	double firmware_unretraction_feedrate_;
	bool firmware_unretraction_feedrate_null_;
	double firmware_z_lift_;
	bool firmware_z_lift_null_;
	bool has_position_error_;
	std::string position_error_;
	bool has_homed_position_;
	double e_relative_;
	double extrusion_length_;
	double extrusion_length_total_;
	double retraction_length_;
	double deretraction_length_;
	bool is_extruding_start_;
	bool is_extruding_;
	bool is_primed_;
	bool is_retracting_start_;
	bool is_retracting_;
	bool is_retracted_;
	bool is_partially_retracted_;
	bool is_deretracting_start_;
	bool is_deretracting_;
	bool is_deretracted_;
	bool is_layer_change_;
	bool is_height_change_;
	bool is_travel_only_;
	bool is_zhop_;
	bool has_position_changed_;
	bool has_xy_position_changed_;
	bool has_state_changed_;
	bool has_received_home_command_;
	bool has_one_feature_enabled_;
	bool is_in_position_;
	bool in_path_position_;
	int file_line_number_;
	int gcode_number_;
	bool gcode_ignored_;
private:
	void initialize();
};
#endif