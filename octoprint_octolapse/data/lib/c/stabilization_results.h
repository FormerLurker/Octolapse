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
#ifndef STABILIZATION_RESULTS_H
#define STABILIZATION_RESULTS_H
#include <string>
#include <vector>
#include "snapshot_plan.h"

enum stabilization_quality_issue_type
{
  stabilization_quality_issue_fast_trigger = 1,
  stabilization_quality_issue_snap_to_print_low_quality = 2,
  stabilization_quality_issue_no_print_features = 3
};

enum stabilization_processing_issue_type
{
  stabilization_processing_issue_type_xyz_axis_mode_unknown = 1,
  stabilization_processing_issue_type_e_axis_mode_unknown = 2,
  stabilization_processing_issue_type_no_definite_position = 3,
  stabilization_processing_issue_type_printer_not_primed = 4,
  stabilization_processing_issue_type_no_metric_units = 5,
  stabilization_processing_issue_type_no_snapshot_commands_found = 6
};

struct stabilization_quality_issue
{
  std::string description;
  stabilization_quality_issue_type issue_type;
  PyObject* to_py_object() const;
};

struct replacement_token
{
  std::string key;
  std::string value;
};

struct stabilization_processing_issue
{
  std::string description;
  stabilization_processing_issue_type issue_type;
  std::vector<replacement_token> replacement_tokens;
  PyObject* to_py_object() const;
};

struct stabilization_results
{
  stabilization_results();
  PyObject* to_py_object();
  std::vector<snapshot_plan> snapshot_plans;
  double seconds_elapsed;
  long gcodes_processed;
  long lines_processed;
  int missed_layer_count;
  std::vector<stabilization_quality_issue> quality_issues;
  std::vector<stabilization_processing_issue> processing_issues;
};


#endif
