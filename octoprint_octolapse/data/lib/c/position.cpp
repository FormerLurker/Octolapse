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

#include "position.h"
#include "logging.h"

void position::set_xyz_axis_mode(const std::string& xyz_axis_default_mode)
{
	if (xyz_axis_default_mode == "relative" || xyz_axis_default_mode == "force-relative")
	{
		is_relative_ = true;
		is_relative_null_ = false;
	}
	else if (xyz_axis_default_mode == "absolute" || xyz_axis_default_mode == "force-absolute")
	{
		is_relative_ = false;
		is_relative_null_ = false;
	}

	
}

void position::set_e_axis_mode(const std::string& e_axis_default_mode)
{
	if (e_axis_default_mode == "relative" || e_axis_default_mode == "force-relative")
	{
		is_extruder_relative_ = true;
		is_extruder_relative_null_ = false;
	}
	else if (e_axis_default_mode == "absolute" || e_axis_default_mode == "force-absolute")
	{
		is_extruder_relative_ = false;
		is_extruder_relative_null_ = false;
	}

	
}
void position::set_units_default(const std::string&	units_default)
{
	if (units_default == "inches")
	{
		is_metric_ = false;
		is_metric_null_ = false;
	}
	else if (units_default == "millimeters")
	{
		is_metric_ = true;
		is_metric_null_ = false;
	}
}


position::position()
{ 
	f_ = 0;
	f_null_ = true;
	x_ = 0;
	x_null_ = true;
	x_offset_ = 0;
	x_homed_ = false;
	y_ = 0;
	y_null_ = true;
	y_offset_ = 0;
	y_homed_ = false;
	z_ = 0;
	z_null_ = true;
	z_offset_ = 0;
	z_homed_ = false;
	e_ = 0;
	e_offset_ = 0;
	is_relative_ = false;
	is_relative_null_ = true;
	is_extruder_relative_ = false;
	is_extruder_relative_null_ = true;
	is_metric_ = true;
	is_metric_null_ = true;
	last_extrusion_height_ = 0;
	last_extrusion_height_null_ = true;
	layer_ = 0;
	height_ = 0;
	current_height_increment_ = 0;
	is_printer_primed_ = false;
	has_definite_position_ = false;
	e_relative_ = 0;
	z_relative_ = 0;
	extrusion_length_ = 0;
	extrusion_length_total_ = 0;
	retraction_length_ = 0;
	deretraction_length_ = 0;
	is_extruding_start_ = false;
	is_extruding_ = false;
	is_primed_ = false;
	is_retracting_start_ = false;
	is_retracting_ = false;
	is_retracted_ = false;
	is_partially_retracted_ = false;
	is_deretracting_start_ = false;
	is_deretracting_ = false;
	is_deretracted_ = false;
	is_in_position_ = false;
	in_path_position_ = false;
	is_zhop_ = false;
	is_layer_change_ = false;
	is_height_change_ = false;
	is_xy_travel_ = false;
	is_xyz_travel_ = false;
	has_xy_position_changed_ = false;
	has_position_changed_ = false;
	has_state_changed_ = false;
	has_received_home_command_ = false;
	file_line_number_ = -1;
	gcode_number_ = -1;
	gcode_ignored_ = true;
	is_in_bounds_ = true;
}


PyObject* position::to_py_tuple()
{
	PyObject * py_command;
	if(p_command.is_empty)
	{
		py_command = Py_None;
	}
	else
	{
		py_command = p_command.to_py_object();
	}
	PyObject* pyPosition = Py_BuildValue(
		// ReSharper disable once StringLiteralTypo
		"ddddddddddddddddddddddlllllllllllllllllllllllllllllllllllllllllllllllO",
		// Floats
		x_, // 0
		y_, // 1
		z_, // 2
		f_, // 3
		e_, // 4
		x_offset_, // 5
		y_offset_, // 6
		z_offset_, // 7
		e_offset_, // 8
		e_relative_, // 9
		z_relative_, // 10
		extrusion_length_, // 11
		extrusion_length_total_, // 12
		retraction_length_, // 13
		deretraction_length_, // 14
		last_extrusion_height_, // 15
		height_, // 16
		0.0, // 17
		0.0, // 18
		0.0, // 19
		0.0, // 20
		0.0, // 21
		// Int
		layer_, // 22
		// Bool (represented as an integer)
		x_homed_, // 23
		y_homed_, // 24
		z_homed_, // 25
		is_relative_, // 26
		is_extruder_relative_, // 27
		is_metric_, // 28
		is_printer_primed_, // 29
		false,
		has_definite_position_, // 31
		is_extruding_start_, // 32
		is_extruding_, // 33
		is_primed_, // 34
		is_retracting_start_, // 35
		is_retracting_, // 36
		is_retracted_, // 37
		is_partially_retracted_, // 38
		is_deretracting_start_, // 39
		is_deretracting_, // 40
		is_deretracted_, // 41
		is_layer_change_, // 42
		is_height_change_, // 43
		is_xy_travel_, // 44
		is_xyz_travel_, // 45
		is_zhop_, // 46
		has_xy_position_changed_, // 47
		has_position_changed_, // 48
		has_state_changed_, // 49
		has_received_home_command_, // 50
		is_in_position_, // 51
		in_path_position_, // 52
		// Null bool, represented as integers
		x_null_, // 53
		y_null_, // 54
		z_null_, // 55
		f_null_, // 56
		is_relative_null_, // 57
		is_extruder_relative_null_, // 58
		last_extrusion_height_null_, // 59
		is_metric_null_, // 60
		true, // 61
		true, // 62
		true, // 63
		true, // 64
		true,  // 65
		// file statistics
		file_line_number_, // 66
		gcode_number_, // 67
		// is in bounds
		is_in_bounds_, // 68
		// Objects
		py_command // 69
	);
	if (pyPosition == NULL)
	{
		std::string message = "Position.to_py_tuple - Unable to create the position.";
		PyErr_Print();
		octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return NULL;
	}
	Py_DECREF(py_command);
	return pyPosition;

}

double position::get_offset_x()
{
	return x_ - x_offset_;
}
double position::get_offset_y()
{
	return y_ - y_offset_;
}
double position::get_offset_z()
{
	return z_ - z_offset_;
}
double position::get_offset_e()
{
	return e_ - e_offset_;
}

void position::reset_state()
{
	is_layer_change_ = false;
	is_height_change_ = false;
	is_xy_travel_ = false;
	is_xyz_travel_ = false;
	has_position_changed_ = false;
	has_state_changed_ = false;
	has_received_home_command_ = false;
	gcode_ignored_ = true;
	is_in_bounds_ = true;
	e_relative_ = 0;
	z_relative_ = 0;
}

PyObject* position::to_py_dict()
{
	PyObject * py_command;
	if (p_command.cmd_.length() == 0)
	{
		py_command = Py_None;
	}
	else
	{
		py_command = p_command.to_py_object();
	}

	PyObject * p_position = Py_BuildValue(
		"{s:O,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
		"parsed_command",
		py_command,
		// FLOATS
		"x",
		x_,
		"y",
		y_,
		"z",
		z_,
		"f",
		f_,
		"e",
		e_,
		"x_offset",
		x_offset_,
		"y_offset",
		y_offset_,
		"z_offset",
		z_offset_,
		"e_offset",
		e_offset_,
		"last_extrusion_height",
		last_extrusion_height_,
		"height",
		height_,
		"current_height_increment_",
		current_height_increment_,
		"firmware_retraction_length",
		0.0,
		"firmware_unretraction_additional_length",
		0.0,
		"firmware_retraction_feedrate",
		0.0,
		"firmware_unretraction_feedrate",
		0.0,
		"firmware_z_lift",
		0.0,
		"e_relative",
		e_relative_,
		"z_relative",
		z_relative_,
		"extrusion_length",
		extrusion_length_,
		"extrusion_length_total",
		extrusion_length_total_,
		"retraction_length",
		retraction_length_,
		"deretraction_length",
		deretraction_length_,
		"layer", 
		layer_,
		"x_null",
		x_null_,
		"y_null",
		y_null_,
		"z_null",
		z_null_,
		"f_null",
		f_null_,
		"x_homed",
		x_homed_,
		"y_homed",
		y_homed_,
		"z_homed",
		z_homed_,
		"is_relative",
		is_relative_,
		"is_relative_null",
		is_relative_null_,
		"is_extruder_relative",
		is_extruder_relative_,
		"is_extruder_relative_null",
		is_extruder_relative_null_,
		"is_metric",
		is_metric_,
		"is_metric_null",
		is_metric_null_,
		"is_printer_primed",
		is_printer_primed_,
		"last_extrusion_height_null",
		last_extrusion_height_null_,
		"firmware_retraction_length_null",
		false,
		"firmware_unretraction_additional_length_null",
		false,
		"firmware_retraction_feedrate_null",
		false,
		"firmware_unretraction_feedrate_null",
		false,
		"firmware_z_lift_null",
		false,
		"has_position_error",
		false,
		"has_definite_position",
		has_definite_position_,
		"is_extruding_start",
		is_extruding_start_,
		"is_extruding",
		is_extruding_,
		"is_primed",
		is_primed_,
		"is_retracting_start",
		is_retracting_start_,
		"is_retracting",
		is_retracting_,
		"is_retracted",
		is_retracted_,
		"is_partially_retracted",
		is_partially_retracted_,
		"is_deretracting_start",
		is_deretracting_start_,
		"is_deretracting",
		is_deretracting_,
		"is_deretracted",
		is_deretracted_,
		"is_layer_change",
		is_layer_change_,
		"is_height_change",
		is_height_change_,
		"is_xy_travel",
		is_xy_travel_,
		"is_xyz_travel",
		is_xyz_travel_,
		"is_zhop",
		is_zhop_,
		"has_xy_position_changed",
		has_xy_position_changed_,
		"has_position_changed",
		has_position_changed_,
		"has_state_changed",
		has_state_changed_,
		"has_received_home_command",
		has_received_home_command_,
		"is_in_position",
		is_in_position_,
		"in_path_position",
		in_path_position_,
		"file_line_number",
		file_line_number_,
		"gcode_number",
		gcode_number_,
		"is_in_bounds",
		is_in_bounds_
	);
	if (p_position == NULL)
	{
		return NULL;
	}
	return p_position;
}
