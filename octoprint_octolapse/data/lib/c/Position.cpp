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

#include "Position.h"
#include "Logging.h"
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
	is_printer_primed = false;
	minimum_layer_height_reached = false;
	firmware_retraction_length = 0;
	firmware_retraction_length_null = true;
	firmware_unretraction_additional_length = 0;
	firmware_unretraction_additional_length_null = true;
	firmware_retraction_feedrate = 0;
	firmware_retraction_feedrate_null = true;
	firmware_unretraction_feedrate = 0;
	firmware_unretraction_feedrate_null = true;
	firmware_z_lift = 0;
	firmware_z_lift_null = true;
	has_position_error = false;
	position_error = "";
	has_homed_position = false;
	e_relative = 0;
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
	has_one_feature_enabled = false;
	in_path_position = false;
	is_zhop = false;
	is_layer_change = false;
	is_height_change = false;
	is_travel_only = false;
	has_position_changed = false;
	has_state_changed = false;
	has_received_home_command = false;
}

position::position()
{ 
	initialize();
}

position::position(position & source)
{
	if(source.p_command != NULL)
		p_command = new parsed_command(*source.p_command);
	f = source.f;
	f_null = source.f_null;
	x = source.x;
	x_null = source.x_null;
	x_offset = source.x_offset;
	x_homed = source.x_homed;
	y = source.y;
	y_null = source.y_null;
	y_offset = source.y_offset;
	y_homed = source.y_homed;
	z = source.z;
	z_null = source.z_null;
	z_offset = source.z_offset;
	z_homed = source.z_homed;
	e = source.e;
	e_offset = source.e_offset;
	is_relative = source.is_relative;
	is_relative_null = source.is_relative_null;
	is_extruder_relative = source.is_extruder_relative;
	is_extruder_relative_null = source.is_extruder_relative_null;
	is_metric = source.is_metric;
	is_metric_null = source.is_metric_null;
	last_extrusion_height = source.last_extrusion_height	;
	last_extrusion_height_null = source.last_extrusion_height_null;
	layer = source.layer;
	height = source.height;
	is_printer_primed = source.is_printer_primed;
	minimum_layer_height_reached = source.minimum_layer_height_reached;
	firmware_retraction_length = source.firmware_retraction_length;
	firmware_retraction_length_null = source.firmware_retraction_length_null;
	firmware_unretraction_additional_length = source.firmware_unretraction_additional_length;
	firmware_unretraction_additional_length_null = source.firmware_unretraction_additional_length_null;
	firmware_retraction_feedrate = source.firmware_retraction_feedrate;
	firmware_retraction_feedrate_null = source.firmware_retraction_feedrate_null;
	firmware_unretraction_feedrate = source.firmware_unretraction_feedrate;
	firmware_unretraction_feedrate_null = source.firmware_unretraction_feedrate_null;
	firmware_z_lift = source.firmware_z_lift;
	firmware_z_lift_null = source.firmware_z_lift_null;
	has_position_error = source.has_position_error;
	position_error = source.position_error;
	has_homed_position = source.has_homed_position;
	e_relative = source.e_relative;
	extrusion_length = source.extrusion_length;
	extrusion_length_total = source.extrusion_length_total;
	retraction_length = source.retraction_length;
	deretraction_length = source.deretraction_length;
	is_extruding_start = source.is_extruding_start;
	is_extruding = source.is_extruding;
	is_primed = source.is_primed;
	is_retracting_start = source.is_retracting_start;
	is_retracting = source.is_retracting;
	is_retracted = source.is_retracted;
	is_partially_retracted = source.is_partially_retracted;
	is_deretracting_start = source.is_deretracting_start;
	is_deretracting = source.is_deretracting;
	is_deretracted = source.is_deretracted;
	is_layer_change = source.is_layer_change;
	is_height_change = source.is_height_change;
	is_travel_only = source.is_travel_only;
	is_zhop = source.is_zhop;
	has_position_changed = source.has_position_changed;
	has_state_changed = source.has_state_changed;
	has_received_home_command = source.has_received_home_command;
	has_one_feature_enabled = source.has_one_feature_enabled;
	is_in_position = source.is_in_position;
	in_path_position = source.in_path_position;
}

position::position(const std::string& xyz_axis_default_mode, const std::string& e_axis_default_mode, const std::string&
                   units_default)
{
	initialize();

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

position::~position()
{
	if (p_command != NULL)
		delete p_command;
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
	target->f = source.f;
	target->f_null = source.f_null;
	target->x = source.x;
	target->x_null = source.x_null;
	target->x_offset = source.x_offset;
	target->x_homed = source.x_homed;
	target->y = source.y;
	target->y_null = source.y_null;
	target->y_offset = source.y_offset;
	target->y_homed = source.y_homed;
	target->z = source.z;
	target->z_null = source.z_null;
	target->z_offset = source.z_offset;
	target->z_homed = source.z_homed;
	target->e = source.e;
	target->e_offset = source.e_offset;
	target->is_relative = source.is_relative;
	target->is_relative_null = source.is_relative_null;
	target->is_extruder_relative = source.is_extruder_relative;
	target->is_extruder_relative_null = source.is_extruder_relative_null;
	target->is_metric = source.is_metric;
	target->is_metric_null = source.is_metric_null;
	target->last_extrusion_height = source.last_extrusion_height;
	target->last_extrusion_height_null = source.last_extrusion_height_null;
	target->layer = source.layer;
	target->height = source.height;
	target->is_printer_primed = source.is_printer_primed;
	target->minimum_layer_height_reached = source.minimum_layer_height_reached;
	target->firmware_retraction_length = source.firmware_retraction_length;
	target->firmware_retraction_length_null = source.firmware_retraction_length_null;
	target->firmware_unretraction_additional_length = source.firmware_unretraction_additional_length;
	target->firmware_unretraction_additional_length_null = source.firmware_unretraction_additional_length_null;
	target->firmware_retraction_feedrate = source.firmware_retraction_feedrate;
	target->firmware_retraction_feedrate_null = source.firmware_retraction_feedrate_null;
	target->firmware_unretraction_feedrate = source.firmware_unretraction_feedrate;
	target->firmware_unretraction_feedrate_null = source.firmware_unretraction_feedrate_null;
	target->firmware_z_lift = source.firmware_z_lift;
	target->firmware_z_lift_null = source.firmware_z_lift_null;
	target->has_position_error = source.has_position_error;
	target->position_error = source.position_error;
	target->has_homed_position = source.has_homed_position;
	target->e_relative = source.e_relative;
	target->extrusion_length = source.extrusion_length;
	target->extrusion_length_total = source.extrusion_length_total;
	target->retraction_length = source.retraction_length;
	target->deretraction_length = source.deretraction_length;
	target->is_extruding_start = source.is_extruding_start;
	target->is_extruding = source.is_extruding;
	target->is_primed = source.is_primed;
	target->is_retracting_start = source.is_retracting_start;
	target->is_retracting = source.is_retracting;
	target->is_retracted = source.is_retracted;
	target->is_partially_retracted = source.is_partially_retracted;
	target->is_deretracting_start = source.is_deretracting_start;
	target->is_deretracting = source.is_deretracting;
	target->is_deretracted = source.is_deretracted;
	target->is_layer_change = source.is_layer_change;
	target->is_height_change = source.is_height_change;
	target->is_travel_only = source.is_travel_only;
	target->is_zhop = source.is_zhop;
	target->has_position_changed = source.has_position_changed;
	target->has_state_changed = source.has_state_changed;
	target->has_received_home_command = source.has_received_home_command;
	target->has_one_feature_enabled = source.has_one_feature_enabled;
	target->is_in_position = source.is_in_position;
	target->in_path_position = source.in_path_position;
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
		"dddddddddddddddddddddllllllllllllllllllllllllllllllllllllllllllllO",
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
		extrusion_length, // 10
		extrusion_length_total, // 11
		retraction_length, // 12
		deretraction_length, // 13
		last_extrusion_height, // 14
		height, // 15
		firmware_retraction_length, // 16
		firmware_unretraction_additional_length, // 17
		firmware_retraction_feedrate, // 18
		firmware_unretraction_feedrate, // 19
		firmware_z_lift, // 20
		// Int
		layer, // 21
		// Bool (represented as an integer)
		x_homed, // 22
		y_homed, // 23
		z_homed, // 24
		is_relative, // 25
		is_extruder_relative, // 26
		is_metric, // 27
		is_printer_primed, // 28
		minimum_layer_height_reached, // 29
		has_position_error, // 30
		has_homed_position, // 31
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
		is_travel_only, // 44
		is_zhop, // 45
		has_position_changed, // 46
		has_state_changed, // 47
		has_received_home_command, // 48
		has_one_feature_enabled, // 49
		is_in_position, // 50
		in_path_position, // 51
		// Null bool, represented as integers
		x_null, // 52
		y_null, // 53
		z_null, // 54
		f_null, // 55
		is_relative_null, // 56
		is_extruder_relative_null, // 57
		last_extrusion_height_null, // 58
		is_metric_null, // 59
		firmware_retraction_length_null, // 60
		firmware_unretraction_additional_length_null, // 61
		firmware_retraction_feedrate_null, // 62
		firmware_unretraction_feedrate_null, // 63
		firmware_z_lift_null,  // 64
		// Objects
		py_command // 65
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

void position::reset_state()
{
	is_layer_change = false;
	is_height_change = false;
	is_travel_only = false;
	has_position_changed = false;
	has_state_changed = false;
	has_received_home_command = false;
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
		"{s:O,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
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
		"firmware_retraction_length",
		firmware_retraction_length,
		"firmware_unretraction_additional_length",
		firmware_unretraction_additional_length,
		"firmware_retraction_feedrate",
		firmware_retraction_feedrate,
		"firmware_unretraction_feedrate",
		firmware_unretraction_feedrate,
		"firmware_z_lift",
		firmware_z_lift,
		"e_relative",
		e_relative,
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
		firmware_retraction_length_null,
		"firmware_unretraction_additional_length_null",
		firmware_unretraction_additional_length_null,
		"firmware_retraction_feedrate_null",
		firmware_retraction_feedrate_null,
		"firmware_unretraction_feedrate_null",
		firmware_unretraction_feedrate_null,
		"firmware_z_lift_null",
		firmware_z_lift_null,
		"has_position_error",
		has_position_error,
		"has_homed_position",
		has_homed_position,
		"minimum_layer_height_reached",
		minimum_layer_height_reached,
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
		"is_travel_only",
		is_travel_only,
		"is_zhop",
		is_zhop,
		"has_position_changed",
		has_position_changed,
		"has_state_changed",
		has_state_changed,
		"has_received_home_command",
		has_received_home_command,
		"has_one_feature_enabled",
		has_one_feature_enabled,
		"is_in_position",
		is_in_position,
		"in_path_position",
		in_path_position

	);
	if (p_position == NULL)
	{
		return NULL;
	}
	return p_position;
}
