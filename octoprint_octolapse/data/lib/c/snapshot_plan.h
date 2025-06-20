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
#ifndef SNAPSHOT_PLAN_H
#define SNAPSHOT_PLAN_H
#include "snapshot_plan_step.h"
#include "parsed_command.h"
#include "position.h"
#include "trigger_position.h"
#include <vector>
#include <map>

struct snapshot_plan
{
  snapshot_plan();
  PyObject* to_py_object();
  static PyObject* build_py_object(std::vector<snapshot_plan>& plans);
  long file_line;
  long file_gcode_number;
  long file_position;
  position_type triggering_command_type;
  feature_type triggering_command_feature_type;
  parsed_command triggering_command;
  parsed_command start_command;
  position initial_position;
  bool has_initial_position;
  std::vector<snapshot_plan_step> steps;
  position return_position;
  parsed_command end_command;
  double distance_from_stabilization_point;
  double total_travel_distance;
  double saved_travel_distance;
};

#endif
