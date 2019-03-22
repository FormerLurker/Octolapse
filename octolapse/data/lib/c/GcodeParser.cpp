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
#include "GcodeParser.h"
#include "Logging.h"
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

bool gcode_parser::is_gcode_word(char c)
{
	for (unsigned int index = 0; index < GCODE_WORDS.size(); ++index)
	{
		if (GCODE_WORDS[index] == c)
			return true;
	}
	return false;
}

std::string gcode_parser::strip_gcode(std::string gcode)
{
	std::string output;
	const int buffer_size = 64;
	output.reserve(buffer_size);
	const int gcode_length = gcode.size();
	for (int index = 0; index < gcode_length; ++index)
	{
		const char currentChar = gcode[index];
		if (currentChar == ';')
			return output;
		else if (isspace(currentChar) || currentChar == '\r' || currentChar == '\n')
			continue;
		else {
			if (currentChar >= 97 && currentChar <= 122)
			{
				output.append(1, gcode[index] - 32);
			}
			else
				output.append(1, currentChar);
		}

	}
	return output;
}

std::string gcode_parser::strip_new_lines(std::string gcode)
{
	int index = gcode.length();
	for (; index >-1; index--)
	{
		if (!(gcode[index] == '\n' || gcode[index] == '\r'))
			break;
	}
	if (index > -1)
	{
		return gcode.substr(0, index + 1);
	}
	else
	{
		return gcode;
	}

}

int gcode_parser::get_double_end_index(std::string gcode, int start_index)
{
	bool hasSeenPeriod = false;
	bool hasSeenPlusOrMinus = false;
	char curLetter;
	unsigned int stringLength = gcode.size();
	for (; static_cast<unsigned int>(start_index) < stringLength; ++start_index)
	{
		curLetter = gcode[start_index];
		if ('0' <= curLetter && curLetter <= '9')
			continue;
		else if (curLetter == '+' || curLetter == '-')
		{

			if (!hasSeenPlusOrMinus)
			{
				hasSeenPlusOrMinus = true;
				continue;
			}
			else
			{
				start_index = -1;
				break;
			}
		}
		else if (gcode[start_index] == '.')
		{
			if (!hasSeenPeriod)
			{
				hasSeenPeriod = true;
				continue;
			}
			else
			{
				start_index = -1;
				break;
			}

		}
		else
		{
			break;
		}

	}

	return start_index;
}

void gcode_parser::parse_gcode(std::string gcode, parsed_command * command)
{
	command->gcode = gcode;
	std::string strippedCommand = strip_gcode(gcode);
	if (strippedCommand.size() == 0 || !is_gcode_word(strippedCommand[0]))
	{
		if (strippedCommand.size() == 0)
			return;
	}
	command->cmd.append(strippedCommand, 0, 1);
	int endAddressIndex;

	if (command->cmd == "T")
	{
		endAddressIndex = 0;
	}
	else
	{
		endAddressIndex = get_double_end_index(strippedCommand, 1);
		if (endAddressIndex > 1)
		{
			command->cmd.append(strippedCommand, 1, endAddressIndex - 1);
		}
	}
	if (parsable_commands_.find(command->cmd) != parsable_commands_.end() && strippedCommand.size() > endAddressIndex)
	{
		if (text_only_functions_.find(command->cmd) != text_only_functions_.end())
		{
			get_text_only_parameter(command->cmd, gcode, &command->parameters);
		}
		else
		{
			get_parameters(strippedCommand, endAddressIndex, &command->parameters);
		}
	}
}

void gcode_parser::get_text_only_parameter(std::string command_name, std::string gcode_param, std::vector<parsed_command_parameter*>* parameters)
{
	parsed_command_parameter * param = new parsed_command_parameter();
	param->name = "TEXT";
	param->value_type = 'T';
	unsigned int textIndex;
	unsigned int foundCount = 0;
	int textStartIndex = -1;
	bool skippedSpace = false;
	for (textIndex = 0; textIndex < gcode_param.size(); textIndex++)
	{
		if (textStartIndex < 0)
		{
			if (gcode_param[textIndex] == command_name[foundCount])
			{
				foundCount++;
				if (foundCount == command_name.size())
				{
					textStartIndex = textIndex + 1;
					continue;
				}
			}
		}
		else if (!skippedSpace)
		{
			if (gcode_param[textIndex] == ' ')
				textStartIndex++;
			skippedSpace = true;
		}
		else if (gcode_param[textIndex] == ';' || gcode_param[textIndex] == '\r' || gcode_param[textIndex] == '\n')
		{
			break;
		}

	}
	std::string text = "";
	if (textIndex - textStartIndex > 0)
	{
		param->string_value = gcode_param.substr(textStartIndex, textIndex - textStartIndex);
	}

	parameters->push_back(param);

}

double gcode_parser::parse_double(const char * p) {
	double r = 0.0;
	bool neg = false;
	if (*p == '-') {
		neg = true;
		++p;
	}
	else if (*p == '+') {
		++p;
	}
	while (*p >= '0' && *p <= '9') {
		r = (r*10.0) + (*p - '0');
		++p;
	}
	if (*p == '.') {
		double f = 0.0;
		int n = 0;
		++p;
		while (*p >= '0' && *p <= '9') {
			f = (f*10.0) + (*p - '0');
			++p;
			++n;
		}
		r += f / std::pow(10.0, n);
	}
	if (neg) {
		r = -r;
	}
	return r;
}
double gcode_parser::parse_double(std::string value) {
	double r = 0.0;
	bool neg = false;
	unsigned int index = 0;
	if (value[index] == '-') {
		neg = true;
		index++;
	}
	else if (value[index] == '+') {
		index++;
	}
	while (value[index] >= '0' && value[index] <= '9') {
		r = (r*10.0) + (value[index] - '0');
		index++;
	}
	if (value[index] == '.') {
		double f = 0.0;
		int n = 0;
		index++;
		while (value[index] >= '0' && value[index] <= '9') {
			f = (f*10.0) + (value[index] - '0');
			index++;
			++n;
		}
		r += f / std::pow(10.0, n);
	}
	if (neg) {
		r = -r;
	}
	return r;
}

void gcode_parser::get_parameters(std::string commandString, int startIndex, std::vector<parsed_command_parameter*> * parameters)
{

	while ((unsigned int)startIndex < commandString.size())
	{
		parsed_command_parameter* p_param = new parsed_command_parameter();
		p_param->name.append(commandString, startIndex, 1);

		int endParameterIndex = 2;

		bool isTCommand = startIndex == 0 && commandString[0] == 'T';
		if (!isTCommand)
		{
			endParameterIndex = get_double_end_index(commandString, startIndex + 1);
		}

		if (endParameterIndex < 0 || endParameterIndex - (startIndex + 1) < 1)
		{
			p_param->value_type = 'N';
		}
		else
		{
			std::string value;
			value.append(commandString, startIndex + 1, endParameterIndex - startIndex - 1);
			if (!isTCommand)
			{
				// See if it's a double or not
				bool is_valid;
				double paramValue = 0.0;
				try
				{
					//parsedDouble = std::atof(value.c_str());
					paramValue = parse_double(value.c_str());
					is_valid = true;
				}
				catch (std::exception)
				{
					is_valid = false;
				}
				if (is_valid)
				{
					p_param->double_value = paramValue;
					p_param->value_type = 'F';
				}
				else
				{
					p_param->string_value = value;
					p_param->value_type = 'S';
				}

			}
			else
			{
				p_param->string_value = value;
				p_param->value_type = 'S';
			}
		}
		parameters->push_back(p_param);
		// Find more parameters
		startIndex = endParameterIndex;

	}
}

// Superfast gcode parser - v2
bool gcode_parser::try_parse_gcode(const char * gcode, parsed_command * command)
{
	char * p = const_cast<char *>(gcode);
	char * gcode_command;
	if(!try_extract_gcode_command(&p, &gcode_command ))
	{
		std::string message = "No gcode command was found: ";
		message += gcode;
		octolapse_log(GCODE_PARSER, ERROR, message);
		return false;
	}
	std::vector<parsed_command_parameter> parameters;

	if (parsable_commands_.find(gcode_command) == parsable_commands_.end())
	{
		command->cmd = gcode_command;
		command->gcode = gcode;
		return true;
	}

	if (text_only_functions_.find(command->cmd) != text_only_functions_.end())
	{
		parsed_command_parameter * p_text_command = new parsed_command_parameter();
		char * text_value;

		if(!try_extract_text_parameter(&p, &text_value))
		{
			delete[] gcode_command;
			return false;
		}
		p_text_command->name = "TEXT";
		p_text_command->string_value = text_value;
	}
	else
	{
		if (gcode_command[0]=='T')
		{
			parsed_command_parameter* param = new parsed_command_parameter();

			if(!try_extract_t_parameter(&p,param))
			{
				delete param;
			}
			else
				command->parameters.push_back(param);
		}
		else
		{
			while (true)
			{
				parsed_command_parameter* param = new parsed_command_parameter();
				if (try_extract_parameter(&p, param))
					command->parameters.push_back(param);
				else
				{
					delete param;
					break;
				}
			}
		}
	}
	command->cmd = gcode_command;
	command->gcode = gcode;
	return true;
	
}

const unsigned int MAX_GCODE_COMMAND_LENGTH = 10;
const unsigned int NEW_GCODE_COMMAND_ARRAY_LENGTH = MAX_GCODE_COMMAND_LENGTH + 1;

bool try_extract_gcode_command(char ** p_p_gcode, char ** p_p_command)
{
	char * new_command = new char[NEW_GCODE_COMMAND_ARRAY_LENGTH];
	int positions = MAX_GCODE_COMMAND_LENGTH; // We need to save one space as a null terminator
	char * c = new_command;
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
		*c++ = gcode_word;
		positions--;
		p++;

		if (gcode_word != 'T')
		{
			// the T command is special, it has no address

			// Now look for a command address
			while ((*p >= '0' && *p <= '9') || *p == ' ') {
				if (*p != ' ')
				{
					if (positions-- == 0)
					{
						delete[] new_command;
						return false;
					}
					else
					{
						found_command = true;
						*c++ = *p++;
					}

				}
				else
					++p;
			}
			if (*p == '.') {
				if (positions-- == 0)
				{
					delete[] new_command;
					return false;
				}
				*c++ = *p++;
				found_command = false;
				while ((*p >= '0' && *p <= '9') || *p == ' ') {
					if (*p != ' ')
					{
						if (positions-- == 0)
						{
							delete[] new_command;
							return false;
						}

						found_command = true;
						*c++ = *p++;
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
	if (!found_command)
		delete [] new_command;
	else
	{
		*c = '\0';
		*p_p_command = new_command;
		*p_p_gcode = p;
	}
	return found_command;
}

bool try_extract_unsigned_long(char ** p_p_gcode, unsigned long * p_value) {
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
			r = (r*10.0) + (*p - '0');
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

bool try_extract_double(char ** p_p_gcode, double * p_double) {
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

const unsigned int MAX_GCODE_TEXT_PARAMETER_LENGTH = 50;
const unsigned int NEW_GCODE_TEXT_PARAMETER_ARRAY_LENGTH = MAX_GCODE_TEXT_PARAMETER_LENGTH + 1;

bool try_extract_text_parameter(char ** p_p_gcode, char ** p_p_parameter)
{
	// Skip initial whitespace
	char * text_parameter = new char[NEW_GCODE_TEXT_PARAMETER_ARRAY_LENGTH];
	int positions = MAX_GCODE_TEXT_PARAMETER_LENGTH; // We need to save one space as a null terminator
	char * t = text_parameter;
	char * p = *p_p_gcode;
	
	// Ignore Leading Spaces
	while (*p == ' ')
	{
		p++;
	}
	// Add all values, stop at end of string or when we hit a ';'

	while (*p != '\0' && *p != ';')
	{
		if(positions-- == 0)
		{
			delete[] text_parameter;
			return false;
		}
		*t++ = *p++;
	}
	if(positions == MAX_GCODE_TEXT_PARAMETER_LENGTH)
	{
		delete[] text_parameter;
		return false;
	}
	*t = '\0';
	*p_p_parameter = text_parameter;
	*p_p_gcode = p;
	return true;

}

bool try_extract_parameter(char ** p_p_gcode, parsed_command_parameter * parameter)
{
	char * p = *p_p_gcode;
	char param_name;

	// Ignore Leading Spaces
	while (*p == ' ')
	{
		p++;
	}

	// Deal with case sensitivity
	if (*p >= 'a' && *p <= 'z')
		param_name = *p++ - 32;
	else if (*p >= 'A' && *p <= 'Z')
		param_name = *p++;
	else
		return false;

	// Add all values, stop at end of string or when we hit a ';'
	if (try_extract_double(&p,&parameter->double_value))
	{
		parameter->value_type = 'F';
	}
	else
	{
		char * text_value;
		if(try_extract_text_parameter(&p, &text_value))
		{
			parameter->string_value = text_value;
			parameter->value_type = 'S';
		}
		else
		{
			return false;
		}
	}

	parameter->name = param_name;
	*p_p_gcode = p;
	return true;

}

bool try_extract_t_parameter(char ** p_p_gcode, parsed_command_parameter * parameter)
{
	char * p = *p_p_gcode;
	parameter->name = "T";
	// Ignore Leading Spaces
	while (*p == ' ')
	{
		p++;
	}
	if (*p == 'c' || *p == 'C')
		parameter->string_value = "C";
	if (*p == 'x' || *p == 'X')
		parameter->string_value = "X"; 
	else if (*p == '?')
		parameter->string_value = "?";
	else
	{
		unsigned int value;
		if(!try_extract_unsigned_long(&p,&parameter->unsigned_long_value))
		{
			return false;
		}
		parameter->value_type = 'U';
	}
	return true;
}
