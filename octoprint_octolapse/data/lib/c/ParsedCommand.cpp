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

#include "ParsedCommand.h"
#include <iostream>
parsed_command::parsed_command()
{
	cmd = "";
	gcode = "";
}
parsed_command::parsed_command(parsed_command & source)
{
	cmd = source.cmd;
	gcode = source.gcode;
	for (int index = 0; index < source.parameters.size(); index++)
		parameters.push_back(new parsed_command_parameter(*source.parameters[index]));
}

parsed_command::~parsed_command()
{
	for (unsigned int index = 0; index < parameters.size(); index++)
		delete parameters[index];
	parameters.clear();
}
void parsed_command::clear()
{
	cmd = "";
	gcode = "";
	for (unsigned int index = 0; index < parameters.size(); index++)
		delete parameters[index];
	parameters.clear();
}
PyObject * parsed_command::to_py_object()
{
	PyObject *ret_val;

	PyObject * pyCommandName = PyString_FromString(cmd.c_str());
	
	if (pyCommandName == NULL)
	{
		return NULL;
	}
	PyObject * pyGcode = PyString_FromString(gcode.c_str());
	if (pyGcode == NULL)
	{
		return NULL;
	}
	
	if (parameters.empty())
	{
		ret_val = PyTuple_Pack(3, pyCommandName, Py_None, pyGcode);
		if (ret_val == NULL)
		{
			return NULL;
		}
	}
	else
	{
		PyObject * pyParametersDict = PyDict_New();

		// Create the parameters dictionary
		if (pyParametersDict == NULL)
		{
			return NULL;
		}
		// Loop through our parameters vector and create and add PyDict items
		for (unsigned int index = 0; index < parameters.size(); index++)
		{
			parsed_command_parameter* param = parameters[index];
			PyObject * param_value = param->value_to_py_object();
			if (param_value == NULL)
				return NULL;
			
			if (PyDict_SetItemString(pyParametersDict, param->name.c_str(), param_value) != 0)
			{
				return NULL;
			}
			//Py_DECREF(param_value);
		}

		ret_val = PyTuple_Pack(3, pyCommandName, pyParametersDict, pyGcode);
		if (ret_val == NULL)
		{
			return NULL;
		}

		//Py_DECREF(pyParametersDict);
	}

	//Py_DECREF(pyCommandName);
	//Py_DECREF(pyGcode);
	
	return ret_val;
}
