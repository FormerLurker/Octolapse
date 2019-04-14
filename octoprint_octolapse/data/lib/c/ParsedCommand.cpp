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
#include "bytesobject.h"
#include "Logging.h"
#include <iostream>
#include <sstream>
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
	for (std::vector< parsed_command_parameter * >::iterator it = parameters.begin(); it != parameters.end(); ++it)
	{
		delete (*it);
	}
	parameters.clear();
}
void parsed_command::clear()
{
	cmd = "";
	gcode = "";
	for (std::vector< parsed_command_parameter * >::iterator it = parameters.begin(); it != parameters.end(); ++it)
	{
		delete (*it);
	}
	parameters.clear();
}
PyObject * parsed_command::to_py_object()
{
	PyObject *ret_val;
	PyObject * pyCommandName = PyUnicode_FromString(cmd.c_str());
	
	if (pyCommandName == NULL)
	{
		PyErr_Print();
		std::string message = "Unable to convert the parameter name to unicode: ";
		message += cmd;
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return NULL;
	}
	PyObject * pyGcode = PyUnicode_FromString(gcode.c_str());
	if (pyGcode == NULL)
	{
		PyErr_Print();
		std::string message = "Unable to convert the gcode to unicode: ";
		message += gcode;
		octolapse_log(GCODE_PARSER, ERROR, message);
		PyErr_SetString(PyExc_ValueError, message.c_str());
		return NULL;
	}
	
	if (parameters.empty())
	{
		ret_val = PyTuple_Pack(3, pyCommandName, Py_None, pyGcode);
		if (ret_val == NULL)
		{
			PyErr_Print();
			std::string message = "Unable to convert the parsed_command (no parameters) to a tuple.  Command: ";
			message += cmd;
			message += " Gcode: ";
			message += gcode;
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		// We will need to decref pyCommandName and pyGcode later
	}
	else
	{
		PyObject * pyParametersDict = PyDict_New();

		// Create the parameters dictionary
		if (pyParametersDict == NULL)
		{
			PyErr_Print();
			std::string message = "ParsedCommand.to_py_object: Unable to create the parameters dict.";
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		// Loop through our parameters vector and create and add PyDict items
		for (unsigned int index = 0; index < parameters.size(); index++)
		{
			parsed_command_parameter* param = parameters[index];
			PyObject * param_value = param->value_to_py_object();
			// Errors here will be handled by value_to_py_object, just return NULL
			if (param_value == NULL)
				return NULL;
			
			//PyObject * pyParamNameUnicode = PyUnicode_FromString(param->name.c_str());
			if (PyDict_SetItemString(pyParametersDict, param->name.c_str(), param_value) != 0)
			{
				PyErr_Print();
				// Handle error here, display detailed message
				std::string message = "Unable to add the command parameter to the parameters dictionary.  Parameter Name: ";
				message += param->name;
				message += " Value Type: ";
				message += param->value_type;
				message += " Value: ";

				switch (param->value_type)
				{
				case 'S':
					message += param->string_value;
					break;
				case 'N':
					message += "None";
					break;
				case 'F':
				{
					std::ostringstream doubld_str;
					doubld_str << param->double_value;
					message += doubld_str.str();
					message += param->string_value;
				}
					break;
				case 'U':
				{
					std::ostringstream unsigned_strs;
					unsigned_strs << param->unsigned_long_value;
					message += unsigned_strs.str();
					message += param->string_value;
				}
					break;
				default:
					break;
				}
				PyErr_SetString(PyExc_ValueError, message.c_str());
				return NULL;
			}
			Py_DECREF(param_value);
			//std::cout << "param_value refcount = " << param_value->ob_refcnt << "\r\n";
		}

		ret_val = PyTuple_Pack(3, pyCommandName, pyParametersDict, pyGcode);
		if (ret_val == NULL)
		{
			PyErr_Print();
			std::string message = "Unable to convert the parsed_command (with parameters) to a tuple.  Command: ";
			message += cmd;
			message += " Gcode: ";
			message += gcode;
			octolapse_log(GCODE_PARSER, ERROR, message);
			PyErr_SetString(PyExc_ValueError, message.c_str());
			return NULL;
		}
		// PyTuple_Pack makes a reference of its own, decref pyParametersDict.  
		// We will need to decref pyCommandName and pyGcode later
		Py_DECREF(pyParametersDict);
		//std::cout << "pyParametersDict refcount = " << pyParametersDict->ob_refcnt << "\r\n";
	}
	// If we're here, we need to decref pyCommandName and pyGcode.
	Py_DECREF(pyCommandName);
	Py_DECREF(pyGcode);
	//std::cout << "pyCommandName refcount = " << pyCommandName->ob_refcnt << "\r\n";
	//std::cout << "pyGcode refcount = " << pyGcode->ob_refcnt << "\r\n";
	//std::cout << "ret_val refcount = " << ret_val->ob_refcnt << "\r\n";
	return ret_val;
}
