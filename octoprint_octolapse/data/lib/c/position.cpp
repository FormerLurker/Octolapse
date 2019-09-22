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
		is_relative = true;
		is_relative_null = false;
	}
	else if (xyz_axis_default_mode == "absolute" || xyz_axis_default_mode == "force-absolute")
	{
		is_relative = false;
		is_relative_null = false;
	}

	
}

void position::set_e_axis_mode(const std::string& e_axis_default_mode)
{
	if (e_axis_default_mode == "relative" || e_axis_default_mode == "force-relative")
	{
		is_extruder_relative = true;
		is_extruder_relative_null = false;
	}
	else if (e_axis_default_mode == "absolute" || e_axis_default_mode == "force-absolute")
	{
		is_extruder_relative = false;
		is_extruder_relative_null = false;
	}

	
}

void position::set_units_default(const std::string&	units_default)
{
	if (units_default == "inches")
	{
		is_metric = false;
		is_metric_null = false;
	}
	else if (units_default == "millimeters")
	{
		is_metric = true;
		is_metric_null = false;
	}
}

position::position()
{ 
	is_empty = true;
	feature_type_tag = 0;
	f = 0;
	f_null = true;
	x = 0;
	x_null = true;
	x_offset = 0;
	x_homed = false;
	y = 0;
	y_null = true;
	y_offset = 0;
	y_homed = false;
	z = 0;
	z_null = true;
	z_offset = 0;
	z_homed = false;
	e = 0;
	e_offset = 0;
	is_relative = false;
	is_relative_null = true;
	is_extruder_relative = false;
	is_extruder_relative_null = true;
	is_metric = true;
	is_metric_null = true;
	last_extrusion_height = 0;
	last_extrusion_height_null = true;
	layer = 0;
	height = 0;
	current_height_increment = 0;
	is_printer_primed = false;
	has_definite_position = false;
	e_relative = 0;
	z_relative = 0;
	extrusion_length = 0;
	extrusion_length_total = 0;
	retraction_length = 0;
	deretraction_length = 0;
	is_extruding_start = false;
	is_extruding = false;
	is_primed = false;
	is_retracting_start = false;
	is_retracting = false;
	is_retracted = false;
	is_partially_retracted = false;
	is_deretracting_start = false;
	is_deretracting = false;
	is_deretracted = false;
	is_in_position = false;
	in_path_position = false;
	is_zhop = false;
	is_layer_change = false;
	is_height_change = false;
	is_xy_travel = false;
	is_xyz_travel = false;
	has_xy_position_changed = false;
	has_position_changed = false;
	has_state_changed = false;
	has_received_home_command = false;
	file_line_number = -1;
	gcode_number = -1;
	gcode_ignored = true;
	is_in_bounds = true;
}

double position::get_offset_x()
{
	return x - x_offset;
}

double position::get_offset_y()
{
	return y - y_offset;
}

double position::get_offset_z()
{
	return z - z_offset;
}

double position::get_offset_e()
{
	return e - e_offset;
}


void position::reset_state()
{
	is_layer_change = false;
	is_height_change = false;
	is_xy_travel = false;
	is_xyz_travel = false;
	has_position_changed = false;
	has_state_changed = false;
	has_received_home_command = false;
	gcode_ignored = true;
	
	//is_in_bounds = true; // I dont' think we want to reset this every time since it's only calculated if the current position
	// changes.
	e_relative = 0;
	z_relative = 0;
	feature_type_tag = 0;
}

PyObject* position::to_py_tuple()
{
	PyObject * py_command;
	if (command.is_empty)
	{
		py_command = Py_None;
	}
	else
	{
		py_command = command.to_py_object();
	}
	PyObject* pyPosition = Py_BuildValue(
		// ReSharper disable once StringLiteralTypo
		"ddddddddddddddddddddddlllllllllllllllllllllllllllllllllllllllllllllllO",
		// Floats
		x, // 0
		y, // 1
		z, // 2
		f, // 3
		e, // 4
		x_offset, // 5
		y_offset, // 6
		z_offset, // 7
		e_offset, // 8
		e_relative, // 9
		z_relative, // 10
		extrusion_length, // 11
		extrusion_length_total, // 12
		retraction_length, // 13
		deretraction_length, // 14
		last_extrusion_height, // 15
		height, // 16
		0.0, // 17
		0.0, // 18
		0.0, // 19
		0.0, // 20
		0.0, // 21
		// Int
		layer, // 22
		// Bool (represented as an integer)
		x_homed, // 23
		y_homed, // 24
		z_homed, // 25
		is_relative, // 26
		is_extruder_relative, // 27
		is_metric, // 28
		is_printer_primed, // 29
		false,
		has_definite_position, // 31
		is_extruding_start, // 32
		is_extruding, // 33
		is_primed, // 34
		is_retracting_start, // 35
		is_retracting, // 36
		is_retracted, // 37
		is_partially_retracted, // 38
		is_deretracting_start, // 39
		is_deretracting, // 40
		is_deretracted, // 41
		is_layer_change, // 42
		is_height_change, // 43
		is_xy_travel, // 44
		is_xyz_travel, // 45
		is_zhop, // 46
		has_xy_position_changed, // 47
		has_position_changed, // 48
		has_state_changed, // 49
		has_received_home_command, // 50
		is_in_position, // 51
		in_path_position, // 52
		// Null bool, represented as integers
		x_null, // 53
		y_null, // 54
		z_null, // 55
		f_null, // 56
		is_relative_null, // 57
		is_extruder_relative_null, // 58
		last_extrusion_height_null, // 59
		is_metric_null, // 60
		true, // 61
		true, // 62
		true, // 63
		true, // 64
		true,  // 65
		// file statistics
		file_line_number, // 66
		gcode_number, // 67
		// is in bounds
		is_in_bounds, // 68
		// Objects
		py_command // 69
	);
	if (pyPosition == NULL)
	{
		std::string message = "position.to_py_tuple: Unable to convert position value to a PyObject tuple via Py_BuildValue.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return NULL;
	}
	Py_DECREF(py_command);
	return pyPosition;

}

PyObject* position::to_py_dict()
{
	PyObject * py_command;
	if (command.command.length() == 0)
	{
		py_command = Py_None;
	}
	else
	{
		py_command = command.to_py_object();
	}

	PyObject * p_position = Py_BuildValue(
		"{s:O,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
		"parsed_command",
		py_command,
		// FLOATS
		"x",
		x,
		"y",
		y,
		"z",
		z,
		"f",
		f,
		"e",
		e,
		"x_offset",
		x_offset,
		"y_offset",
		y_offset,
		"z_offset",
		z_offset,
		"e_offset",
		e_offset,
		"last_extrusion_height",
		last_extrusion_height,
		"height",
		height,
		"current_height_increment_",
		current_height_increment,
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
		e_relative,
		"z_relative",
		z_relative,
		"extrusion_length",
		extrusion_length,
		"extrusion_length_total",
		extrusion_length_total,
		"retraction_length",
		retraction_length,
		"deretraction_length",
		deretraction_length,
		"layer", 
		layer,
		"x_null",
		x_null,
		"y_null",
		y_null,
		"z_null",
		z_null,
		"f_null",
		f_null,
		"x_homed",
		x_homed,
		"y_homed",
		y_homed,
		"z_homed",
		z_homed,
		"is_relative",
		is_relative,
		"is_relative_null",
		is_relative_null,
		"is_extruder_relative",
		is_extruder_relative,
		"is_extruder_relative_null",
		is_extruder_relative_null,
		"is_metric",
		is_metric,
		"is_metric_null",
		is_metric_null,
		"is_printer_primed",
		is_printer_primed,
		"last_extrusion_height_null",
		last_extrusion_height_null,
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
		has_definite_position,
		"is_extruding_start",
		is_extruding_start,
		"is_extruding",
		is_extruding,
		"is_primed",
		is_primed,
		"is_retracting_start",
		is_retracting_start,
		"is_retracting",
		is_retracting,
		"is_retracted",
		is_retracted,
		"is_partially_retracted",
		is_partially_retracted,
		"is_deretracting_start",
		is_deretracting_start,
		"is_deretracting",
		is_deretracting,
		"is_deretracted",
		is_deretracted,
		"is_layer_change",
		is_layer_change,
		"is_height_change",
		is_height_change,
		"is_xy_travel",
		is_xy_travel,
		"is_xyz_travel",
		is_xyz_travel,
		"is_zhop",
		is_zhop,
		"has_xy_position_changed",
		has_xy_position_changed,
		"has_position_changed",
		has_position_changed,
		"has_state_changed",
		has_state_changed,
		"has_received_home_command",
		has_received_home_command,
		"is_in_position",
		is_in_position,
		"in_path_position",
		in_path_position,
		"file_line_number",
		file_line_number,
		"gcode_number",
		gcode_number,
		"is_in_bounds",
		is_in_bounds
	);
	if (p_position == NULL)
	{
		std::string message = "position.to_py_dict: Unable to convert position value to a dict PyObject via Py_BuildValue.";
		octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
		return NULL;
	}
	return p_position;
}
