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
#include "ParsedCommand.h"
#include "ParsedCommandParameter.h"
static const std::string GCODE_WORDS = "GMT";


bool try_extract_double(char ** p, double * p_double);
bool try_extract_gcode_command(char ** p_p_gcode, char ** command);
bool try_extract_text_parameter(char ** p_p_gcode, char ** p_p_parameter);
bool try_extract_parameter(char ** p_p_gcode, parsed_command_parameter * parameter);
bool try_extract_t_parameter(char ** p_p_gcode, parsed_command_parameter * parameter);
class gcode_parser
{
public:
	gcode_parser();
	~gcode_parser();
	void parse_gcode(std::string gcode, parsed_command* command);
	bool try_parse_gcode(const char * gcode, parsed_command * command);
private:
	gcode_parser(const gcode_parser &source);
	// Variables and lookups
	std::set<std::string> text_only_functions_;
	std::set<std::string> parsable_commands_;
	// Functions
	void get_parameters(std::string, int startIndex, std::vector<parsed_command_parameter*> *parameters);
	void get_text_only_parameter(std::string command_name, std::string gcode_param, std::vector<parsed_command_parameter*> *parameters);
	static std::string strip_gcode(std::string);
	std::string strip_new_lines(std::string gcode);
	static int get_double_end_index(std::string gcode, int start_index);
	static bool is_gcode_word(char c);
	double parse_double(const char* p);
	double parse_double(std::string value);

};
#endif
