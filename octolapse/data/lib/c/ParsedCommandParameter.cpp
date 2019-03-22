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

#include "ParsedCommandParameter.h"
#include "ParsedCommand.h"

parsed_command_parameter::parsed_command_parameter()
{
	name = "";
	value_type = 'N';
	double_value = 0.0;
	string_value = "";
	unsigned_long_value = 0;
}

parsed_command_parameter::parsed_command_parameter(parsed_command_parameter & source)
{
	name = source.name;
	value_type = source.value_type;
	double_value = source.double_value;
	string_value = source.string_value;
	unsigned_long_value = source.unsigned_long_value;
}

parsed_command_parameter::parsed_command_parameter(std::string name, double double_value) : name(name), double_value(double_value)
{
	value_type = 'F';
	string_value = "";
	unsigned_long_value = 0;
}

parsed_command_parameter::parsed_command_parameter(std::string name, std::string string_value) : name(name), string_value(string_value)
{
	value_type = 'S';
	double_value = 0.0;
	unsigned_long_value = 0;
}

parsed_command_parameter::parsed_command_parameter(std::string name, unsigned int unsigned_int_value) : name(name), string_value(string_value), unsigned_long_value(unsigned_int_value)
{
	value_type = 'U';
	double_value = 0.0;
	string_value = "";
}
parsed_command_parameter::~parsed_command_parameter()
{

}

PyObject * parsed_command_parameter::value_to_py_object()
{
	PyObject * ret_val;
	// check the parameter type
	if (value_type == 'F')
	{
		ret_val = PyFloat_FromDouble(double_value);
		if (ret_val == NULL)
		{
			return NULL;
		}
	}
	else if (value_type == 'N')
	{
		// None Type
		Py_INCREF(Py_None);
		ret_val = Py_None;
	}
	else if (value_type == 'S')
	{
		ret_val = PyString_FromString(string_value.c_str());
		if (ret_val == NULL)
		{
			return NULL;
		}
		
	}
	else if (value_type == 'U')
	{
		ret_val = PyLong_FromUnsignedLong(unsigned_long_value);
	}
	else
	{
		// There has been an error, we don't support this value_type!
		PyErr_SetString(PyExc_ValueError, "Error creating ParsedCommand: Unknown value_type");
		return NULL;
	}

	return ret_val;

}