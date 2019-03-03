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
	double f;
	bool f_null;
	double x;
	bool x_null;
	double x_offset;
	bool x_homed;
	double y;
	bool y_null;
	double y_offset;
	bool y_homed;
	double z;
	bool z_null;
	double z_offset;
	bool z_homed;
	double e;
	double e_offset;
	bool is_relative;
	bool is_relative_null;
	bool is_extruder_relative;
	bool is_extruder_relative_null;
	bool is_metric;
	bool is_metric_null;
	double last_extrusion_height;
	bool last_extrusion_height_null;
	int layer;
	double height;
	bool is_printer_primed;
	bool minimum_layer_height_reached;
	double firmware_retraction_length;
	bool firmware_retraction_length_null;
	double firmware_unretraction_additional_length;
	bool firmware_unretraction_additional_length_null;
	double firmware_retraction_feedrate;
	bool firmware_retraction_feedrate_null;
	double firmware_unretraction_feedrate;
	bool firmware_unretraction_feedrate_null;
	double firmware_z_lift;
	bool firmware_z_lift_null;
	bool has_position_error;
	std::string position_error;
	bool has_homed_position;
	double e_relative;
	double extrusion_length;
	double extrusion_length_total;
	double retraction_length;
	double deretraction_length;
	bool is_extruding_start;
	bool is_extruding;
	bool is_primed;
	bool is_retracting_start;
	bool is_retracting;
	bool is_retracted;
	bool is_partially_retracted;
	bool is_deretracting_start;
	bool is_deretracting;
	bool is_deretracted;
	bool is_layer_change;
	bool is_height_change;
	bool is_travel_only;
	bool is_zhop;
	bool has_position_changed;
	bool has_state_changed;
	bool has_received_home_command;
	bool has_one_feature_enabled;
	bool is_in_position;
	bool in_path_position;
private:
	void initialize();
};
#endif