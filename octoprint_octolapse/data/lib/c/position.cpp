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
#include <iostream>

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

void position::set_units_default(const std::string& units_default)
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

bool position::can_take_snapshot()
{
  return (
    !is_relative_null &&
    !is_extruder_relative_null &&
    has_definite_position &&
    is_printer_primed &&
    !is_metric_null
  );
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
  x_firmware_offset = 0;
  x_homed = false;
  y = 0;
  y_null = true;
  y_offset = 0;
  y_firmware_offset = 0;
  y_homed = false;
  z = 0;
  z_null = true;
  z_offset = 0;
  z_firmware_offset = 0;
  z_homed = false;
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
  height_increment = 0;
  height_increment_change_count = 0;
  is_printer_primed = false;
  has_definite_position = false;
  z_relative = 0;
  is_in_position = false;
  in_path_position = false;
  is_zhop = false;
  is_layer_change = false;
  is_height_change = false;
  is_height_increment_change = false;
  is_xy_travel = false;
  is_xyz_travel = false;
  has_xy_position_changed = false;
  has_position_changed = false;
  has_received_home_command = false;
  file_line_number = -1;
  gcode_number = -1;
  file_position = -1;
  gcode_ignored = true;
  is_in_bounds = true;
  current_tool = -1;
  p_extruders = NULL;
  set_num_extruders(0);
}

position::position(int extruder_count)
{
  is_empty = true;
  feature_type_tag = 0;
  f = 0;
  f_null = true;
  x = 0;
  x_null = true;
  x_offset = 0;
  x_firmware_offset = 0;
  x_homed = false;
  y = 0;
  y_null = true;
  y_offset = 0;
  y_firmware_offset = 0;
  y_homed = false;
  z = 0;
  z_null = true;
  z_offset = 0;
  z_firmware_offset = 0;
  z_homed = false;
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
  height_increment = 0;
  height_increment_change_count = 0;
  is_printer_primed = false;
  has_definite_position = false;
  z_relative = 0;
  is_in_position = false;
  in_path_position = false;
  is_zhop = false;
  is_layer_change = false;
  is_height_change = false;
  is_height_increment_change = false;
  is_xy_travel = false;
  is_xyz_travel = false;
  has_xy_position_changed = false;
  has_position_changed = false;
  has_received_home_command = false;
  file_line_number = -1;
  gcode_number = -1;
  file_position = -1;
  gcode_ignored = true;
  is_in_bounds = true;
  current_tool = 0;
  p_extruders = NULL;
  set_num_extruders(extruder_count);
}

position::position(const position& pos)
{
  is_empty = pos.is_empty;
  feature_type_tag = pos.feature_type_tag;
  f = pos.f;
  f_null = pos.f_null;
  x = pos.x;
  x_null = pos.x_null;
  x_offset = pos.x_offset;
  x_firmware_offset = pos.x_firmware_offset;
  x_homed = pos.x_homed;
  y = pos.y;
  y_null = pos.y_null;
  y_offset = pos.y_offset;
  y_firmware_offset = pos.y_firmware_offset;
  y_homed = pos.y_homed;
  z = pos.z;
  z_null = pos.z_null;
  z_offset = pos.z_offset;
  z_firmware_offset = pos.z_firmware_offset;
  z_homed = pos.z_homed;
  is_relative = pos.is_relative;
  is_relative_null = pos.is_relative_null;
  is_extruder_relative = pos.is_extruder_relative;
  is_extruder_relative_null = pos.is_extruder_relative_null;
  is_metric = pos.is_metric;
  is_metric_null = pos.is_metric_null;
  last_extrusion_height = pos.last_extrusion_height;
  last_extrusion_height_null = pos.last_extrusion_height_null;
  layer = pos.layer;
  height = pos.height;
  height_increment = pos.height_increment;
  height_increment_change_count = pos.height_increment_change_count;
  is_printer_primed = pos.is_printer_primed;
  has_definite_position = pos.has_definite_position;
  z_relative = pos.z_relative;
  is_in_position = pos.is_in_position;
  in_path_position = pos.in_path_position;
  is_zhop = pos.is_zhop;
  is_layer_change = pos.is_layer_change;
  is_height_change = pos.is_height_change;
  is_height_increment_change = pos.is_height_increment_change;
  is_xy_travel = pos.is_xy_travel;
  is_xyz_travel = pos.is_xyz_travel;
  has_xy_position_changed = pos.has_xy_position_changed;
  has_position_changed = pos.has_position_changed;
  has_received_home_command = pos.has_received_home_command;
  file_line_number = pos.file_line_number;
  gcode_number = pos.gcode_number;
  file_position = pos.file_position;
  gcode_ignored = pos.gcode_ignored;
  is_in_bounds = pos.is_in_bounds;
  current_tool = pos.current_tool;
  p_extruders = NULL;
  command = pos.command;
  set_num_extruders(pos.num_extruders);
  for (int index = 0; index < pos.num_extruders; index++)
  {
    p_extruders[index] = pos.p_extruders[index];
  }
}

position::~position()
{
  delete_extruders();
}

position& position::operator=(const position& pos)
{
  is_empty = pos.is_empty;
  feature_type_tag = pos.feature_type_tag;
  f = pos.f;
  f_null = pos.f_null;
  x = pos.x;
  x_null = pos.x_null;
  x_offset = pos.x_offset;
  x_firmware_offset = pos.x_firmware_offset;
  x_homed = pos.x_homed;
  y = pos.y;
  y_null = pos.y_null;
  y_offset = pos.y_offset;
  y_firmware_offset = pos.y_firmware_offset;
  y_homed = pos.y_homed;
  z = pos.z;
  z_null = pos.z_null;
  z_offset = pos.z_offset;
  z_firmware_offset = pos.z_firmware_offset;
  z_homed = pos.z_homed;
  is_relative = pos.is_relative;
  is_relative_null = pos.is_relative_null;
  is_extruder_relative = pos.is_extruder_relative;
  is_extruder_relative_null = pos.is_extruder_relative_null;
  is_metric = pos.is_metric;
  is_metric_null = pos.is_metric_null;
  last_extrusion_height = pos.last_extrusion_height;
  last_extrusion_height_null = pos.last_extrusion_height_null;
  layer = pos.layer;
  height = pos.height;
  height_increment = pos.height_increment;
  height_increment_change_count = pos.height_increment_change_count;
  is_printer_primed = pos.is_printer_primed;
  has_definite_position = pos.has_definite_position;
  z_relative = pos.z_relative;
  is_in_position = pos.is_in_position;
  in_path_position = pos.in_path_position;
  is_zhop = pos.is_zhop;
  is_layer_change = pos.is_layer_change;
  is_height_change = pos.is_height_change;
  is_height_increment_change = pos.is_height_increment_change;
  is_xy_travel = pos.is_xy_travel;
  is_xyz_travel = pos.is_xyz_travel;
  has_xy_position_changed = pos.has_xy_position_changed;
  has_position_changed = pos.has_position_changed;
  has_received_home_command = pos.has_received_home_command;
  file_line_number = pos.file_line_number;
  file_position = pos.file_position;
  gcode_number = pos.gcode_number;
  gcode_ignored = pos.gcode_ignored;
  is_in_bounds = pos.is_in_bounds;
  current_tool = pos.current_tool;
  command = pos.command;
  if (num_extruders != pos.num_extruders)
  {
    set_num_extruders(pos.num_extruders);
  }
  for (int index = 0; index < pos.num_extruders; index++)
  {
    p_extruders[index] = pos.p_extruders[index];
  }
  return *this;
}

void position::set_num_extruders(int num_extruders_)
{
  delete_extruders();
  num_extruders = num_extruders_;
  if (num_extruders_ > 0)
  {
    p_extruders = new extruder[num_extruders_];
  }
}

void position::delete_extruders()
{
  if (p_extruders != NULL)
  {
    delete[] p_extruders;
    p_extruders = NULL;
  }
}

double position::get_gcode_x() const
{
  return x - x_offset + x_firmware_offset;
}

double position::get_gcode_y() const
{
  return y - y_offset + y_firmware_offset;
}

double position::get_gcode_z() const
{
  return z - z_offset + z_firmware_offset;
}

extruder& position::get_current_extruder() const
{
  int tool_number = current_tool;
  if (current_tool >= num_extruders)
    tool_number = num_extruders - 1;
  else if (current_tool < 0)
    tool_number = 0;
  return p_extruders[tool_number];
}

extruder& position::get_extruder(int index) const
{
  if (index >= num_extruders)
    index = num_extruders - 1;
  else if (index < 0)
    index = 0;
  return p_extruders[index];
}

void position::reset_state()
{
  is_layer_change = false;
  is_height_change = false;
  is_height_increment_change = false;
  is_xy_travel = false;
  is_xyz_travel = false;
  has_position_changed = false;
  has_received_home_command = false;
  gcode_ignored = true;

  //is_in_bounds = true; // I dont' think we want to reset this every time since it's only calculated if the current position
  // changes.
  p_extruders[current_tool].e_relative = 0;
  z_relative = 0;
  feature_type_tag = 0;
}

PyObject* position::to_py_tuple()
{
  //std::cout << "Building position py_object.\r\n";
  PyObject* py_command;
  if (command.is_empty)
  {
    py_command = Py_None;
  }
  else
  {
    py_command = command.to_py_object();
    if (py_command == NULL)
    {
      return NULL;
    }
  }
  PyObject* py_extruders = extruder::build_py_object(p_extruders, num_extruders);
  if (py_extruders == NULL)
  {
    return NULL;
  }
  //std::cout << "Building position py_tuple.\r\n";
  PyObject* pyPosition = Py_BuildValue(
    // ReSharper disable once StringLiteralTypo
    "ddddddddddddddddddlllllllllllllllllllllllllllllllllllllllllOO",
    // Floats
    x, // 0
    y, // 1
    z, // 2
    f, // 3
    x_offset, // 4
    y_offset, // 5
    z_offset, // 6
    x_firmware_offset, // 7
    y_firmware_offset, // 8
    z_firmware_offset, // 9
    z_relative, // 10
    last_extrusion_height, // 11
    height, // 12
    0.0, // 13 - Firmware Retraction Length
    0.0, // 14 - Firmware Unretraction Additional Length
    0.0, // 15 - Firmware Retraction Feedrate
    0.0, // 16 - Firmware Unretraction Feedrate
    0.0, // 17 - Firmware Unretraction ZLift
    // Int
    layer, // 18
    height_increment, // 19 !!!!!!!!!
    height_increment_change_count, // 20 !!!!!!
    current_tool, // 21
    num_extruders, // 22
    // Bool (represented as an integer)
    (long int)(x_homed ? 1 : 0), // 23
    (long int)(y_homed ? 1 : 0), // 24
    (long int)(z_homed ? 1 : 0), // 25
    (long int)(is_relative ? 1 : 0), // 26
    (long int)(is_extruder_relative ? 1 : 0), // 27
    (long int)(is_metric ? 1 : 0), // 28
    (long int)(is_printer_primed ? 1 : 0), // 29
    (long int)(has_definite_position ? 1 : 0), // 30
    (long int)(is_layer_change ? 1 : 0), // 31
    (long int)(is_height_change ? 1 : 0), // 32
    (long int)(is_height_increment_change ? 1 : 0), // 33
    (long int)(is_xy_travel ? 1 : 0), // 34
    (long int)(is_xyz_travel ? 1 : 0), // 35
    (long int)(is_zhop ? 1 : 0), // 36
    (long int)(has_xy_position_changed ? 1 : 0), // 37
    (long int)(has_position_changed ? 1 : 0), // 38
    (long int)(has_received_home_command ? 1 : 0), // 39
    (long int)(is_in_position ? 1 : 0), // 40
    (long int)(in_path_position ? 1 : 0), // 41
    (long int)(is_in_bounds ? 1 : 0), // 42
    // Null bool, represented as integers
    (long int)(x_null ? 1 : 0), // 43
    (long int)(y_null ? 1 : 0), // 44
    (long int)(z_null ? 1 : 0), // 45
    (long int)(f_null ? 1 : 0), // 46
    (long int)(is_relative_null ? 1 : 0), // 47
    (long int)(is_extruder_relative_null ? 1 : 0), // 48
    (long int)(last_extrusion_height_null ? 1 : 0), // 49
    (long int)(is_metric_null ? 1 : 0), // 50
    (long int)(true ? 1 : 0), // 51 - Firmware retraction length null
    (long int)(true ? 1 : 0), // 52 - Firmware unretraction additional length null
    (long int)(true ? 1 : 0), // 53 - Firmware retraction feedrate null
    (long int)(true ? 1 : 0), // 54 - Firmware unretraction feedrate null
    (long int)(true ? 1 : 0), // 55 - Firmware ZLift Null
    // file statistics
    file_line_number, // 56
    gcode_number, // 57
    file_position, // 58
    // Objects
    py_command, // 59
    py_extruders // 60

  );
  if (pyPosition == NULL)
  {
    //std::cout << "No py_object returned for position!\r\n";
    std::string message =
      "position.to_py_tuple: Unable to convert position value to a PyObject tuple via Py_BuildValue.";
    octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
    return NULL;
  }
  //std::cout << "Finished building pyPosition.\r\n";
  Py_DECREF(py_command);
  Py_DECREF(py_extruders);
  //std::cout << "Returning pyPosition.\r\n";
  return pyPosition;
}

PyObject* position::to_py_dict()
{
  PyObject* py_command;
  if (command.command.length() == 0)
  {
    py_command = Py_None;
  }
  else
  {
    py_command = command.to_py_object();
  }
  PyObject* py_extruders = extruder::build_py_object(p_extruders, num_extruders);
  if (py_extruders == NULL)
  {
    return NULL;
  }
  PyObject* p_position = Py_BuildValue(
    "{s:O,s:O,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
    "parsed_command",
    py_command,
    "extruders",
    py_extruders,
    // FLOATS
    "x_firmware_offset",
    x_firmware_offset,
    "y_firmware_offset",
    y_firmware_offset,
    "z_firmware_offset",
    z_firmware_offset,
    "x",
    x,
    "y",
    y,
    "z",
    z,
    "f",
    f,
    "e",
    x_offset,
    "y_offset",
    y_offset,
    "z_offset",
    z_offset,
    "last_extrusion_height",
    last_extrusion_height,
    "height",
    height,
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
    "z_relative",
    z_relative,
    // Ints
    "layer",
    layer,
    "height_increment",
    height_increment,
    "height_increment_change_count",
    height_increment_change_count,
    "current_tool",
    current_tool,
    "num_extruders",
    num_extruders,
    // Bools
    "x_null",
    (long int)(x_null ? 1 : 0),
    "y_null",
    (long int)(y_null ? 1 : 0),
    "z_null",
    (long int)(z_null ? 1 : 0),
    "f_null",
    (long int)(f_null ? 1 : 0),
    "x_homed",
    (long int)(x_homed ? 1 : 0),
    "y_homed",
    (long int)(y_homed ? 1 : 0),
    "z_homed",
    (long int)(z_homed ? 1 : 0),
    "is_relative",
    (long int)(is_relative ? 1 : 0),
    "is_relative_null",
    (long int)(is_relative_null ? 1 : 0),
    "is_extruder_relative",
    (long int)(is_extruder_relative ? 1 : 0),
    "is_extruder_relative_null",
    (long int)(is_extruder_relative_null ? 1 : 0),
    "is_metric",
    (long int)(is_metric ? 1 : 0),
    "is_metric_null",
    (long int)(is_metric_null ? 1 : 0),
    "is_printer_primed",
    (long int)(is_printer_primed ? 1 : 0),
    "last_extrusion_height_null",
    (long int)(last_extrusion_height_null ? 1 : 0),
    "firmware_retraction_length_null",
    (long int)(false ? 1 : 0),
    "firmware_unretraction_additional_length_null",
    (long int)(false ? 1 : 0),
    "firmware_retraction_feedrate_null",
    (long int)(false ? 1 : 0),
    "firmware_unretraction_feedrate_null",
    (long int)(false ? 1 : 0),
    "firmware_z_lift_null",
    (long int)(false ? 1 : 0),
    "has_position_error",
    (long int)(false ? 1 : 0),
    "has_definite_position",
    (long int)(has_definite_position ? 1 : 0),
    "is_layer_change",
    (long int)(is_layer_change ? 1 : 0),
    "is_height_change",
    (long int)(is_height_change ? 1 : 0),
    "is_height_increment_change",
    (long int)(is_height_increment_change ? 1 : 0),
    "is_xy_travel",
    (long int)(is_xy_travel ? 1 : 0),
    "is_xyz_travel",
    (long int)(is_xyz_travel ? 1 : 0),
    "is_zhop",
    (long int)(is_zhop ? 1 : 0),
    "has_xy_position_changed",
    (long int)(has_xy_position_changed ? 1 : 0),
    "has_position_changed",
    (long int)(has_position_changed ? 1 : 0),
    "has_received_home_command",
    (long int)(has_received_home_command ? 1 : 0),
    "is_in_position",
    (long int)(is_in_position ? 1 : 0),
    "in_path_position",
    (long int)(in_path_position ? 1 : 0),
    "file_line_number",
    file_line_number,
    "file_position",
    file_position,
    "gcode_number",
    gcode_number,
    "is_in_bounds",
    (long int)(is_in_bounds ? 1 : 0)
  );
  if (p_position == NULL)
  {
    std::string message = "position.to_py_dict: Unable to convert position value to a dict PyObject via Py_BuildValue.";
    octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
    return NULL;
  }
  Py_DECREF(py_command);
  Py_DECREF(py_extruders);

  return p_position;
}
