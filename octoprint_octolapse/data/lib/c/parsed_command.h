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

#ifndef PARSED_COMMAND_H
#define PARSED_COMMAND_H
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif
#include <string>
#include <vector>
#include "parsed_command_parameter.h"

struct parsed_command
{
public:
  parsed_command();
  std::string command;
  std::string gcode;
  std::string comment;
  bool is_empty;
  bool is_known_command;
  std::vector<parsed_command_parameter> parameters;
  PyObject* to_py_object();
  void clear();
};

#endif
