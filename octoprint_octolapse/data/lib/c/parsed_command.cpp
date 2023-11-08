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

#include "parsed_command.h"
#include "python_helpers.h"
#include "logging.h"
#include <sstream>

parsed_command::parsed_command()
{
  command.reserve(8);
  gcode.reserve(128);
  comment.reserve(128);
  parameters.reserve(6);
  is_known_command = false;
  is_empty = true;
}

void parsed_command::clear()
{
  command.clear();
  gcode.clear();
  comment.clear();
  parameters.clear();
  is_known_command = false;
  is_empty = true;
}

PyObject* parsed_command::to_py_object()
{
  PyObject* ret_val;
  PyObject* pyCommandName = PyUnicode_SafeFromString(command.c_str());

  if (pyCommandName == NULL)
  {
    std::string message = "Unable to convert the parameter name to unicode: ";
    message += command;
    octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
    return NULL;
  }
  PyObject* pyGcode = PyUnicode_SafeFromString(gcode.c_str());
  if (pyGcode == NULL)
  {
    std::string message = "Unable to convert the gcode to unicode: ";
    message += gcode;
    octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
    return NULL;
  }

  PyObject* pyComment = PyUnicode_SafeFromString(comment.c_str());
  if (pyComment == NULL)
  {
    std::string message = "Unable to convert the gocde comment to unicode: ";
    message += comment;
    octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
    return NULL;
  }

  if (parameters.empty())
  {
    ret_val = PyTuple_Pack(4, pyCommandName, Py_None, pyGcode, pyComment);
    if (ret_val == NULL)
    {
      std::string message = "Unable to convert the parsed_command (no parameters) to a tuple.  Command: ";
      message += command;
      message += " Gcode: ";
      message += gcode;
      octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
      return NULL;
    }
    // We will need to decref pyCommandName and pyGcode later
  }
  else
  {
    PyObject* pyParametersDict = PyDict_New();

    // Create the parameters dictionary
    if (pyParametersDict == NULL)
    {
      std::string message = "ParsedCommand.to_py_object: Unable to create the parameters dict.";
      octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
      return NULL;
    }
    // Loop through our parameters vector and create and add PyDict items
    for (unsigned int index = 0; index < parameters.size(); index++)
    {
      parsed_command_parameter param = parameters[index];
      PyObject* param_value = param.value_to_py_object();
      // Errors here will be handled by value_to_py_object, just return NULL
      if (param_value == NULL)
      {
        return NULL;
      }
      if (PyDict_SetItemString(pyParametersDict, param.name.c_str(), param_value) != 0)
      {
        // Handle error here, display detailed message
        std::string message = "Unable to add the command parameter to the parameters dictionary.  Parameter Name: ";
        message += param.name;
        message += " Value Type: ";
        message += param.value_type;
        message += " Value: ";

        switch (param.value_type)
        {
        case 'S':
          message += param.string_value;
          break;
        case 'N':
          message += "None";
          break;
        case 'F':
          {
            std::ostringstream doubld_str;
            doubld_str << param.double_value;
            message += doubld_str.str();
            message += param.string_value;
          }
          break;
        case 'U':
          {
            std::ostringstream unsigned_strs;
            unsigned_strs << param.unsigned_long_value;
            message += unsigned_strs.str();
            message += param.string_value;
          }
          break;
        default:
          break;
        }
        octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
        return NULL;
      }
      // Todo: evaluate the effects of this
      Py_DECREF(param_value);
    }

    ret_val = PyTuple_Pack(4, pyCommandName, pyParametersDict, pyGcode, pyComment);
    if (ret_val == NULL)
    {
      std::string message = "Unable to convert the parsed_command (with parameters) to a tuple.  Command: ";
      message += command;
      message += " Gcode: ";
      message += gcode;
      octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
      return NULL;
    }
    // PyTuple_Pack makes a reference of its own, decref pyParametersDict.  
    // We will need to decref pyCommandName and pyGcode later
    // Todo: evaluate the effects of this
    Py_DECREF(pyParametersDict);
  }
  // If we're here, we need to decref pyCommandName and pyGcode.
  // Todo: evaluate the effects of this
  Py_DECREF(pyCommandName);
  // Todo: evaluate the effects of this
  Py_DECREF(pyGcode);
  Py_DECREF(pyComment);
  return ret_val;
}
