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

#ifndef GCODE_PARSER_H
#define GCODE_PARSER_H
#include <string>
#include <vector>
#include <set>
#include "parsed_command.h"
#include "parsed_command_parameter.h"
static const std::string GCODE_WORDS = "GMT";

class gcode_parser
{
public:
  gcode_parser();
  ~gcode_parser();
  bool try_parse_gcode(const char* gcode, parsed_command& command);
  parsed_command parse_gcode(const char* gcode);
private:
  gcode_parser(const gcode_parser& source);
  // Variables and lookups
  std::set<std::string> text_only_functions_;
  std::set<std::string> parsable_commands_;
  // Functions
  bool try_extract_double(char** p_p_gcode, double* p_double) const;
  static bool try_extract_gcode_command(char** p_p_gcode, std::string* p_command);
  static bool try_extract_text_parameter(char** p_p_gcode, std::string* p_parameter);
  bool try_extract_parameter(char** p_p_gcode, parsed_command_parameter* parameter) const;
  static bool try_extract_t_parameter(char** p_p_gcode, parsed_command_parameter* parameter);
  static bool try_extract_unsigned_long(char** p_p_gcode, unsigned long* p_value);
  double static ten_pow(unsigned short n);
  bool try_extract_comment(char** p_p_gcode, std::string* p_comment);
  static bool try_extract_at_command(char** p_p_gcode, std::string* p_command);
  bool try_extract_octolapse_parameter(char** p_p_gcode, parsed_command_parameter* p_parameter);
};
#endif
