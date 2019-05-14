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
#include "gcode_parser.h"
#include "logging.h"
#include <cmath>
#include <iostream>
gcode_parser::gcode_parser()
{
	// doesn't work in the ancient version of c++ I am forced to use :(
	// or at least I don't know how to us a newer one with python 2.7
	// help...
	/* 
	std::vector<std::string> text_only_function_names = { "M117" }; // "M117" is an example of a command that would work here.

	std::vector<std::string> parsable_command_names = {
		"G0","G1","G2","G3","G10","G11","G20","G21","G28","G29","G80","G90","G91","G92","M82","M83","M104","M105","M106","M109","M114","M116","M140","M141","M190","M191","M207","M208","M240","M400","T"
	};
	*/
	// Have to resort to barbarity.
	// Text only function names
	std::vector<std::string> text_only_function_names;
	text_only_function_names.push_back(("M117"));
	// parsable_command_names
	std::vector<std::string> parsable_command_names;
	parsable_command_names.push_back("G0");
	parsable_command_names.push_back("G1");
	parsable_command_names.push_back("G2");
	parsable_command_names.push_back("G3");
	parsable_command_names.push_back("G10");
	parsable_command_names.push_back("G11");
	parsable_command_names.push_back("G20");
	parsable_command_names.push_back("G21");
	parsable_command_names.push_back("G28");
	parsable_command_names.push_back("G29");
	parsable_command_names.push_back("G80");
	parsable_command_names.push_back("G90");
	parsable_command_names.push_back("G91");
	parsable_command_names.push_back("G92");
	parsable_command_names.push_back("M82");
	parsable_command_names.push_back("M83");
	parsable_command_names.push_back("M104");
	parsable_command_names.push_back("M105");
	parsable_command_names.push_back("M106");
	parsable_command_names.push_back("M109");
	parsable_command_names.push_back("M114");
	parsable_command_names.push_back("M116");
	parsable_command_names.push_back("M140");
	parsable_command_names.push_back("M141");
	parsable_command_names.push_back("M190");
	parsable_command_names.push_back("M191");
	parsable_command_names.push_back("M207");
	parsable_command_names.push_back("M208");
	parsable_command_names.push_back("M240");
	parsable_command_names.push_back("M400");
	parsable_command_names.push_back("T");

	for (unsigned int index = 0; index < text_only_function_names.size(); index++)
	{
		std::string functionName = text_only_function_names[index];
		text_only_functions_.insert(functionName);
	}

	for (unsigned int index = 0; index < parsable_command_names.size(); index++)
	{
		std::string commandName = parsable_command_names[index];
		parsable_commands_.insert(commandName);
	}

}

gcode_parser::gcode_parser(const gcode_parser &source)
{
	// Private copy constructor - you can't copy this class
}

gcode_parser::~gcode_parser()
{
	text_only_functions_.clear();
	parsable_commands_.clear();
}

// Superfast gcode parser - v2
bool gcode_parser::try_parse_gcode(const char * gcode, parsed_command * command)
{
	// Create a command
	//std::cout << "GcodeParser.try_parse_gcode - Parsing " << gcode << "\r\n";
	char * p = const_cast<char *>(gcode);
	if(!try_extract_gcode_command(&p, &(command->cmd_)))
	{
		std::string message = "No gcode command was found: ";
		message += gcode;
		octolapse_log(GCODE_PARSER, WARNING, message);
		return false;
	}
	command->gcode_ = gcode;
	std::vector<parsed_command_parameter> parameters;

	if (parsable_commands_.find(command->cmd_) == parsable_commands_.end())
	{
		//std::cout << "GcodeParser.try_parse_gcode - Not in command list, exiting.\r\n";
		std::string message = "The gcode command is not in the parsable commands set: ";
		message += gcode;
		octolapse_log(GCODE_PARSER, VERBOSE, message);
		return true;
	}

	if (text_only_functions_.find(command->cmd_) != text_only_functions_.end())
	{
		//std::cout << "GcodeParser.try_parse_gcode - Text only parameter found.\r\n";
		parsed_command_parameter * p_text_command = new parsed_command_parameter();

		if(!try_extract_text_parameter(&p, &(p_text_command->string_value_)))
		{
			std::string message = "Unable to extract a text parameter from: ";
			message += p;
			octolapse_log(GCODE_PARSER, WARNING, message);
			return true;
		}
		p_text_command->name_ = "TEXT";
	}
	else
	{
		if (command->cmd_[0] == 'T')
		{
			//std::cout << "GcodeParser.try_parse_gcode - T parameter found.\r\n";
			parsed_command_parameter* param = new parsed_command_parameter();

			if(!try_extract_t_parameter(&p,param))
			{
				std::string message = "Unable to extract a parameter from the T command: ";
				message += gcode;
				octolapse_log(GCODE_PARSER, ERROR, message);
				delete param;
				param = NULL;
			}
			else
				command->parameters_.push_back(param);
		}
		else
		{
			while (true)
			{
				//std::cout << "GcodeParser.try_parse_gcode - Trying to extract parameters.\r\n";
				parsed_command_parameter* param = new parsed_command_parameter();
				if (try_extract_parameter(&p, param))
					command->parameters_.push_back(param);
				else
				{
					//std::cout << "GcodeParser.try_parse_gcode - No parameters found.\r\n";
					delete param;
					param = NULL;
					break;
				}
			}
		}
	}
	
	return true;
	
}

bool gcode_parser::try_extract_gcode_command(char ** p_p_gcode, std::string * p_command)
{
	char * p = *p_p_gcode;
	char gcode_word;
	bool found_command = false;

	// Ignore Leading Spaces
	while (*p == ' ')
	{
		p++;
	}
	// Deal with case sensitivity
	if (*p >= 'a' && *p <= 'z')
		gcode_word = *p - 32;
	else
		gcode_word = *p;
	if (gcode_word == 'G' || gcode_word == 'M' || gcode_word == 'T')
	{
		// Set the gcode word of the new command to the current pointer's location and increment both
		(*p_command) += gcode_word;
		p++;

		if (gcode_word != 'T')
		{
			// the T command is special, it has no address

			// Now look for a command address
			while ((*p >= '0' && *p <= '9') || *p == ' ') {
				if (*p != ' ')
				{
					found_command = true;
					(*p_command) += *p++;
				}
				else
					++p;
			}
			if (*p == '.') {
				(*p_command) += *p++;
				found_command = false;
				while ((*p >= '0' && *p <= '9') || *p == ' ') {
					if (*p != ' ')
					{
						found_command = true;
						(*p_command) += *p++;
					}
					else
						++p;
				}
			}
		}
		else
		{
			found_command = true;
		}
	}
	*p_p_gcode = p;
	return found_command;
}

bool gcode_parser::try_extract_unsigned_long(char ** p_p_gcode, unsigned long * p_value) {
	char * p = *p_p_gcode;
	unsigned int r = 0;
	bool found_numbers = false;
	// skip any leading whitespace
	while (*p == ' ')
		++p;

	while ((*p >= '0' && *p <= '9') || *p == ' ') {
		if (*p != ' ')
		{
			found_numbers = true;
			r = (unsigned int)((r*10.0) + (*p - '0'));
		}
		++p;
	}
	if (found_numbers)
	{
		*p_value = r;
		*p_p_gcode = p;
	}
	
	return found_numbers;
}

bool gcode_parser::try_extract_double(char ** p_p_gcode, double * p_double) {
	char * p = *p_p_gcode;
	bool neg = false;
	double r = 0;
	bool found_numbers = false;
	// skip any leading whitespace
	while (*p == ' ')
		++p;
	// Check for negative sign
	if (*p == '-') {
		neg = true;
		++p;
		while (*p == ' ')
			++p;
	}
	else if (*p == '+') {
		// Positive sign doesn't affect anything since we assume positive
		++p;
		while (*p == ' ')
			++p;
	}
	// skip any additional whitespace
	

	while ((*p >= '0' && *p <= '9') || *p == ' ') {
		if (*p != ' ')
		{
			found_numbers = true;
			r = (r*10.0) + (*p - '0');
		}
		++p;
	}
	if (*p == '.') {
		double f = 0.0;
		int n = 0;
		++p;
		while ((*p >= '0' && *p <= '9') || *p == ' ') {
			if (*p != ' ')
			{
				found_numbers = true;
				f = (f*10.0) + (*p - '0');
				++n;
			}
			++p;
		}
		r += f / std::pow(10.0, n);
	}
	if (neg) {
		r = -r;
	}
	if (found_numbers)
	{
		*p_double = r;
		*p_p_gcode = p;
	}
	
	return found_numbers;
}

bool gcode_parser::try_extract_text_parameter(char ** p_p_gcode, std::string * p_parameter)
{
	// Skip initial whitespace
	//std::cout << "GcodeParser.try_extract_parameter - Trying to extract a text parameter from  " << *p_p_gcode << "\r\n";
	char * p = *p_p_gcode;
	
	// Ignore Leading Spaces
	while (*p == ' ')
	{
		p++;
	}
	// Add all values, stop at end of string or when we hit a ';'

	while (*p != '\0' && *p != ';')
	{
		(*p_parameter) += *p++;
	}
	*p_p_gcode = p;
	return true;

}

bool gcode_parser::try_extract_parameter(char ** p_p_gcode, parsed_command_parameter * parameter)
{
	//std::cout << "GcodeParser.try_extract_parameter - Trying to extract a parameter from  " << *p_p_gcode << "\r\n";
	char * p = *p_p_gcode;

	// Ignore Leading Spaces
	while (*p == ' ')
	{
		p++;
	}
	
	// Deal with case sensitivity
	if (*p >= 'a' && *p <= 'z')
		parameter->name_ += *p++ - 32;
	else if (*p >= 'A' && *p <= 'Z')
		parameter->name_ += *p++;
	else
		return false;

	// Add all values, stop at end of string or when we hit a ';'
	if (try_extract_double(&p,&(parameter->double_value_)))
	{
		parameter->value_type_ = 'F';
	}
	else
	{
		if(try_extract_text_parameter(&p, &(parameter->string_value_)))
		{
			parameter->value_type_ = 'S';
		}
		else
		{
			return false;
		}
	}

	*p_p_gcode = p;
	return true;

}

bool gcode_parser::try_extract_t_parameter(char ** p_p_gcode, parsed_command_parameter * parameter)
{
	//std::cout << "Trying to extract a T parameter from " << *p_p_gcode << "\r\n";
	char * p = *p_p_gcode;
	parameter->name_ = "T";
	// Ignore Leading Spaces
	while (*p == L' ')
	{
		p++;
	}

	if (*p == L'c' || *p == L'C')
	{
		//std::cout << "Found C value for T parameter\r\n";
		parameter->string_value_ = "C";
		parameter->value_type_ = 'S';
	}
	else if (*p == L'x' || *p == L'X')
	{
		//std::cout << "Found X value for T parameter\r\n";
		parameter->string_value_ = "X";
		parameter->value_type_ = 'S';
	}
	else if (*p == L'?')
	{
		//std::cout << "Found ? value for T parameter\r\n";
		parameter->string_value_ = "?";
		parameter->value_type_ = 'S';
	}
	else
	{
		//std::cout << "No char t parameter found, looking for unsigned int values.\r\n";
		if(!try_extract_unsigned_long(&p,&(parameter->unsigned_long_value_)))
		{
			std::string message = "GcodeParser.try_extract_t_parameter: Unable to extract parameters from the T command.";
			octolapse_log(GCODE_PARSER, WARNING, message);
			//std::cout << "No parameter for the T command.\r\n";
			return false;
		}
		parameter->value_type_ = 'U';
	}
	return true;
}
