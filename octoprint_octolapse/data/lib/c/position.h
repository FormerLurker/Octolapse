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
#include "extruder.h"
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif

struct position
{
  position();
  position(int extruder_count);
  position(const position& pos); // Copy Constructor
  virtual ~position();
  position& operator=(const position& pos);
  void reset_state();
  PyObject* to_py_tuple();
  PyObject* to_py_dict();
  parsed_command command;
  int feature_type_tag;
  double f;
  bool f_null;
  double x;
  bool x_null;
  double x_offset;
  double x_firmware_offset;
  bool x_homed;
  double y;
  bool y_null;
  double y_offset;
  double y_firmware_offset;
  bool y_homed;
  double z;
  bool z_null;
  double z_offset;
  double z_firmware_offset;
  bool z_homed;
  bool is_metric;
  bool is_metric_null;
  double last_extrusion_height;
  bool last_extrusion_height_null;
  long layer;
  double height;
  int height_increment;
  int height_increment_change_count;
  bool is_printer_primed;
  bool has_definite_position;
  double z_relative;
  bool is_relative;
  bool is_relative_null;
  bool is_extruder_relative;
  bool is_extruder_relative_null;
  bool is_layer_change;
  bool is_height_change;
  bool is_height_increment_change;
  bool is_xy_travel;
  bool is_xyz_travel;
  bool is_zhop;
  bool has_position_changed;
  bool has_xy_position_changed;
  bool has_received_home_command;
  bool is_in_position;
  bool in_path_position;
  long file_line_number;
  long gcode_number;
  long file_position;
  bool gcode_ignored;
  bool is_in_bounds;
  bool is_empty;
  int current_tool;
  int num_extruders;
  extruder* p_extruders;
  extruder& get_current_extruder() const;
  extruder& get_extruder(int index) const;
  void set_num_extruders(int num_extruders_);
  void delete_extruders();
  double get_gcode_x() const;
  double get_gcode_y() const;
  double get_gcode_z() const;
  void set_xyz_axis_mode(const std::string& xyz_axis_default_mode);
  void set_e_axis_mode(const std::string& e_axis_default_mode);
  void set_units_default(const std::string& units_default);
  bool can_take_snapshot();
};
#endif
