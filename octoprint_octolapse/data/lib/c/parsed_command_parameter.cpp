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

#include "parsed_command_parameter.h"
#include "parsed_command.h"
#include "logging.h"
#include "python_helpers.h"
parsed_command_parameter::parsed_command_parameter()
{
	//name_ = "";
	value_type_ = 'N';
	//double_value_ = 0.0;
	//string_value_ = "";
	//unsigned_long_value_ = 0;
}

parsed_command_parameter::parsed_command_parameter(parsed_command_parameter & source)
{
	name_ = source.name_;
	value_type_ = source.value_type_;
	double_value_ = source.double_value_;
	string_value_ = source.string_value_;
	unsigned_long_value_ = source.unsigned_long_value_;
}

parsed_command_parameter::parsed_command_parameter(char name, double double_value) : name_(name), double_value_(double_value)
{
	value_type_ = 'F';
	//string_value_ = "";
	//unsigned_long_value_ = 0;
}

parsed_command_parameter::parsed_command_parameter(char name, std::string string_value) : name_(name), string_value_(string_value)
{
	value_type_ = 'S';
	//double_value_ = 0.0;
	//unsigned_long_value_ = 0;
}

parsed_command_parameter::parsed_command_parameter(char name, unsigned int unsigned_int_value) : name_(name), string_value_(string_value_), unsigned_long_value_(unsigned_int_value)
{
	value_type_ = 'U';
	//double_value_ = 0.0;
	//string_value_ = "";
}
parsed_command_parameter::~parsed_command_parameter()
{

}

PyObject * parsed_command_parameter::value_to_py_object()
{
	PyObject * ret_val;
	// check the parameter type
	if (value_type_ == 'F')
	{
		ret_val = PyFloat_FromDouble(double_value_);
		if (ret_val == NULL)
		{
			std::string message = "parsedCommandParameter.value_to_py_object: Unable to convert double value to a PyObject.";
			octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
	}
	else if (value_type_ == 'N')
	{
		// None Type
		Py_INCREF(Py_None);
		ret_val = Py_None;
	}
	else if (value_type_ == 'S')
	{
		ret_val = PyUnicode_SafeFromString(string_value_.c_str());
		if (ret_val == NULL)
		{
			std::string message = "parsedCommandParameter.value_to_py_object: Unable to convert string value to a PyObject.";
			octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		
	}
	else if (value_type_ == 'U')
	{
		ret_val = PyLong_FromUnsignedLong(unsigned_long_value_);
		if (ret_val == NULL)
		{
			std::string message = "parsedCommandParameter.value_to_py_object: Unable to convert unsigned long value to a PyObject.";
			octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
	}
	else
	{
		std::string message = "The command parameter value type does not exist.  Value Type: ";
		message += value_type_;
		octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
		// There has been an error, we don't support this value_type!
		PyErr_SetString(PyExc_ValueError, "Error creating ParsedCommand: Unknown value_type");
		return NULL;
	}

	return ret_val;

}