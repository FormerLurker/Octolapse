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
/*
f
f_null
x
x_null
x_offset
x_homed
y
y_null
y_offset
y_homed
z
z_null
z_offset
z_homed
e
e_offset
is_relative
is_relative_null
is_extruder_relative
is_extruder_relative_null
is_metric
is_metric_null
last_extrusion_height
last_extrusion_height_null
layer
height
is_printer_primed
minimum_layer_height_reached
firmware_retraction_length
firmware_retraction_length_null
firmware_unretraction_additional_length
firmware_unretraction_additional_length_null
firmware_retraction_feedrate
firmware_retraction_feedrate_null
firmware_unretraction_feedrate
firmware_unretraction_feedrate_null
firmware_z_lift
firmware_z_lift_null
has_position_error
position_error
has_homed_position
e_relative
extrusion_length
extrusion_length_total
retraction_length
deretraction_length
is_extruding_start
is_extruding
is_primed
is_retracting_start
is_retracting
is_retracted
is_partially_retracted
is_deretracting_start
is_deretracting
is_deretracted
is_layer_change
is_height_change
is_travel_only
is_zhop
has_position_changed
has_state_changed
has_received_home_command
has_one_feature_enabled
is_in_position
in_path_position
*/

void position::initialize()
{
	p_command = NULL;
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
	is_printer_primed_ = false;
	minimum_layer_height_reached_ = false;
	firmware_retraction_length_ = 0;
	firmware_retraction_length_null_ = true;
	firmware_unretraction_additional_length_ = 0;
	firmware_unretraction_additional_length_null_ = true;
	firmware_retraction_feedrate_ = 0;
	firmware_retraction_feedrate_null_ = true;
	firmware_unretraction_feedrate_ = 0;
	firmware_unretraction_feedrate_null_ = true;
	firmware_z_lift_ = 0;
	firmware_z_lift_null_ = true;
	has_position_error_ = false;
	position_error_ = "";
	has_homed_position_ = false;
	e_relative_ = 0;
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
	has_one_feature_enabled_ = false;
	in_path_position_ = false;
	is_zhop_ = false;
	is_layer_change_ = false;
	is_height_change_ = false;
	is_travel_only_ = false;
	has_xy_position_changed_ = false;
	has_position_changed_ = false;
	has_state_changed_ = false;
	has_received_home_command_ = false;
	file_line_number_ = -1;
	gcode_number_ = -1;
	gcode_ignored_ = true;
	is_in_bounds_ = true;
}

position::position()
{ 
	initialize();
}

position::position(position & source)
{
	if(source.p_command != NULL)
		p_command = new parsed_command(*source.p_command);
	f_ = source.f_;
	f_null_ = source.f_null_;
	x_ = source.x_;
	x_null_ = source.x_null_;
	x_offset_ = source.x_offset_;
	x_homed_ = source.x_homed_;
	y_ = source.y_;
	y_null_ = source.y_null_;
	y_offset_ = source.y_offset_;
	y_homed_ = source.y_homed_;
	z_ = source.z_;
	z_null_ = source.z_null_;
	z_offset_ = source.z_offset_;
	z_homed_ = source.z_homed_;
	e_ = source.e_;
	e_offset_ = source.e_offset_;
	is_relative_ = source.is_relative_;
	is_relative_null_ = source.is_relative_null_;
	is_extruder_relative_ = source.is_extruder_relative_;
	is_extruder_relative_null_ = source.is_extruder_relative_null_;
	is_metric_ = source.is_metric_;
	is_metric_null_ = source.is_metric_null_;
	last_extrusion_height_ = source.last_extrusion_height_	;
	last_extrusion_height_null_ = source.last_extrusion_height_null_;
	layer_ = source.layer_;
	height_ = source.height_;
	is_printer_primed_ = source.is_printer_primed_;
	minimum_layer_height_reached_ = source.minimum_layer_height_reached_;
	firmware_retraction_length_ = source.firmware_retraction_length_;
	firmware_retraction_length_null_ = source.firmware_retraction_length_null_;
	firmware_unretraction_additional_length_ = source.firmware_unretraction_additional_length_;
	firmware_unretraction_additional_length_null_ = source.firmware_unretraction_additional_length_null_;
	firmware_retraction_feedrate_ = source.firmware_retraction_feedrate_;
	firmware_retraction_feedrate_null_ = source.firmware_retraction_feedrate_null_;
	firmware_unretraction_feedrate_ = source.firmware_unretraction_feedrate_;
	firmware_unretraction_feedrate_null_ = source.firmware_unretraction_feedrate_null_;
	firmware_z_lift_ = source.firmware_z_lift_;
	firmware_z_lift_null_ = source.firmware_z_lift_null_;
	has_position_error_ = source.has_position_error_;
	position_error_ = source.position_error_;
	has_homed_position_ = source.has_homed_position_;
	e_relative_ = source.e_relative_;
	extrusion_length_ = source.extrusion_length_;
	extrusion_length_total_ = source.extrusion_length_total_;
	retraction_length_ = source.retraction_length_;
	deretraction_length_ = source.deretraction_length_;
	is_extruding_start_ = source.is_extruding_start_;
	is_extruding_ = source.is_extruding_;
	is_primed_ = source.is_primed_;
	is_retracting_start_ = source.is_retracting_start_;
	is_retracting_ = source.is_retracting_;
	is_retracted_ = source.is_retracted_;
	is_partially_retracted_ = source.is_partially_retracted_;
	is_deretracting_start_ = source.is_deretracting_start_;
	is_deretracting_ = source.is_deretracting_;
	is_deretracted_ = source.is_deretracted_;
	is_layer_change_ = source.is_layer_change_;
	is_height_change_ = source.is_height_change_;
	is_travel_only_ = source.is_travel_only_;
	is_zhop_ = source.is_zhop_;
	has_xy_position_changed_ = source.has_xy_position_changed_;
	has_position_changed_ = source.has_position_changed_;
	has_state_changed_ = source.has_state_changed_;
	has_received_home_command_ = source.has_received_home_command_;
	has_one_feature_enabled_ = source.has_one_feature_enabled_;
	is_in_position_ = source.is_in_position_;
	in_path_position_ = source.in_path_position_;
	file_line_number_ = source.file_line_number_;
	gcode_number_ = source.gcode_number_;
	gcode_ignored_ = source.gcode_ignored_;
	is_in_bounds_ = source.is_in_bounds_;
}

position::position(const std::string& xyz_axis_default_mode, const std::string& e_axis_default_mode, const std::string&
                   units_default)
{
	initialize();

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

position::~position()
{
	octolapse_log(GCODE_POSITION, INFO, "Deleting position.");
	if (p_command != NULL)
	{
		delete p_command;
		p_command = NULL;
	}
	octolapse_log(GCODE_POSITION, INFO, "Finished deleting position.");
}

void position::copy(position &source, position* target)
{
	if (target->p_command != NULL)
	{
		delete target->p_command;
		target->p_command = NULL;
	}
	if(source.p_command != NULL)
		target->p_command = new parsed_command(*source.p_command);
	target->f_ = source.f_;
	target->f_null_ = source.f_null_;
	target->x_ = source.x_;
	target->x_null_ = source.x_null_;
	target->x_offset_ = source.x_offset_;
	target->x_homed_ = source.x_homed_;
	target->y_ = source.y_;
	target->y_null_ = source.y_null_;
	target->y_offset_ = source.y_offset_;
	target->y_homed_ = source.y_homed_;
	target->z_ = source.z_;
	target->z_null_ = source.z_null_;
	target->z_offset_ = source.z_offset_;
	target->z_homed_ = source.z_homed_;
	target->e_ = source.e_;
	target->e_offset_ = source.e_offset_;
	target->is_relative_ = source.is_relative_;
	target->is_relative_null_ = source.is_relative_null_;
	target->is_extruder_relative_ = source.is_extruder_relative_;
	target->is_extruder_relative_null_ = source.is_extruder_relative_null_;
	target->is_metric_ = source.is_metric_;
	target->is_metric_null_ = source.is_metric_null_;
	target->last_extrusion_height_ = source.last_extrusion_height_;
	target->last_extrusion_height_null_ = source.last_extrusion_height_null_;
	target->layer_ = source.layer_;
	target->height_ = source.height_;
	target->is_printer_primed_ = source.is_printer_primed_;
	target->minimum_layer_height_reached_ = source.minimum_layer_height_reached_;
	target->firmware_retraction_length_ = source.firmware_retraction_length_;
	target->firmware_retraction_length_null_ = source.firmware_retraction_length_null_;
	target->firmware_unretraction_additional_length_ = source.firmware_unretraction_additional_length_;
	target->firmware_unretraction_additional_length_null_ = source.firmware_unretraction_additional_length_null_;
	target->firmware_retraction_feedrate_ = source.firmware_retraction_feedrate_;
	target->firmware_retraction_feedrate_null_ = source.firmware_retraction_feedrate_null_;
	target->firmware_unretraction_feedrate_ = source.firmware_unretraction_feedrate_;
	target->firmware_unretraction_feedrate_null_ = source.firmware_unretraction_feedrate_null_;
	target->firmware_z_lift_ = source.firmware_z_lift_;
	target->firmware_z_lift_null_ = source.firmware_z_lift_null_;
	target->has_position_error_ = source.has_position_error_;
	target->position_error_ = source.position_error_;
	target->has_homed_position_ = source.has_homed_position_;
	target->e_relative_ = source.e_relative_;
	target->extrusion_length_ = source.extrusion_length_;
	target->extrusion_length_total_ = source.extrusion_length_total_;
	target->retraction_length_ = source.retraction_length_;
	target->deretraction_length_ = source.deretraction_length_;
	target->is_extruding_start_ = source.is_extruding_start_;
	target->is_extruding_ = source.is_extruding_;
	target->is_primed_ = source.is_primed_;
	target->is_retracting_start_ = source.is_retracting_start_;
	target->is_retracting_ = source.is_retracting_;
	target->is_retracted_ = source.is_retracted_;
	target->is_partially_retracted_ = source.is_partially_retracted_;
	target->is_deretracting_start_ = source.is_deretracting_start_;
	target->is_deretracting_ = source.is_deretracting_;
	target->is_deretracted_ = source.is_deretracted_;
	target->is_layer_change_ = source.is_layer_change_;
	target->is_height_change_ = source.is_height_change_;
	target->is_travel_only_ = source.is_travel_only_;
	target->is_zhop_ = source.is_zhop_;
	target->has_xy_position_changed_ = source.has_xy_position_changed_;
	target->has_position_changed_ = source.has_position_changed_;
	target->has_state_changed_ = source.has_state_changed_;
	target->has_received_home_command_ = source.has_received_home_command_;
	target->has_one_feature_enabled_ = source.has_one_feature_enabled_;
	target->is_in_position_ = source.is_in_position_;
	target->in_path_position_ = source.in_path_position_;
	target->file_line_number_ = source.file_line_number_;
	target->gcode_number_ = source.gcode_number_;
	target->gcode_ignored_ = source.gcode_ignored_;
	target->is_in_bounds_ = source.is_in_bounds_;
}

PyObject* position::to_py_tuple()
{
	PyObject * py_command;
	if(p_command == NULL)
	{
		py_command = Py_None;
	}
	else
	{
		py_command = p_command->to_py_object();
	}
	PyObject* pyPosition = Py_BuildValue(
		// ReSharper disable once StringLiteralTypo
		"dddddddddddddddddddddllllllllllllllllllllllllllllllllllllllllllllllllO",
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
		extrusion_length_, // 10
		extrusion_length_total_, // 11
		retraction_length_, // 12
		deretraction_length_, // 13
		last_extrusion_height_, // 14
		height_, // 15
		firmware_retraction_length_, // 16
		firmware_unretraction_additional_length_, // 17
		firmware_retraction_feedrate_, // 18
		firmware_unretraction_feedrate_, // 19
		firmware_z_lift_, // 20
		// Int
		layer_, // 21
		// Bool (represented as an integer)
		x_homed_, // 22
		y_homed_, // 23
		z_homed_, // 24
		is_relative_, // 25
		is_extruder_relative_, // 26
		is_metric_, // 27
		is_printer_primed_, // 28
		minimum_layer_height_reached_, // 29
		has_position_error_, // 30
		has_homed_position_, // 31
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
		is_travel_only_, // 44
		is_zhop_, // 45
		has_xy_position_changed_, // 46
		has_position_changed_, // 47
		has_state_changed_, // 48
		has_received_home_command_, // 49
		has_one_feature_enabled_, // 50
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
		firmware_retraction_length_null_, // 61
		firmware_unretraction_additional_length_null_, // 62
		firmware_retraction_feedrate_null_, // 63
		firmware_unretraction_feedrate_null_, // 64
		firmware_z_lift_null_,  // 65
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
		octolapse_log(GCODE_PARSER, ERROR, message);
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
	is_travel_only_ = false;
	has_position_changed_ = false;
	has_state_changed_ = false;
	has_received_home_command_ = false;
	gcode_ignored_ = true;
	is_in_bounds_ = true;
}

PyObject* position::to_py_dict()
{
	PyObject * py_command;
	if (p_command == NULL)
	{
		py_command = Py_None;
	}
	else
	{
		py_command = p_command->to_py_object();
	}

	PyObject * p_position = Py_BuildValue(
		"{s:O,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
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
		"firmware_retraction_length",
		firmware_retraction_length_,
		"firmware_unretraction_additional_length",
		firmware_unretraction_additional_length_,
		"firmware_retraction_feedrate",
		firmware_retraction_feedrate_,
		"firmware_unretraction_feedrate",
		firmware_unretraction_feedrate_,
		"firmware_z_lift",
		firmware_z_lift_,
		"e_relative",
		e_relative_,
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
		firmware_retraction_length_null_,
		"firmware_unretraction_additional_length_null",
		firmware_unretraction_additional_length_null_,
		"firmware_retraction_feedrate_null",
		firmware_retraction_feedrate_null_,
		"firmware_unretraction_feedrate_null",
		firmware_unretraction_feedrate_null_,
		"firmware_z_lift_null",
		firmware_z_lift_null_,
		"has_position_error",
		has_position_error_,
		"has_homed_position",
		has_homed_position_,
		"minimum_layer_height_reached",
		minimum_layer_height_reached_,
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
		"is_travel_only",
		is_travel_only_,
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
		"has_one_feature_enabled",
		has_one_feature_enabled_,
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
