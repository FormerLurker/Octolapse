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
  value_type = 'N';
  name.reserve(1);
}

parsed_command_parameter::
parsed_command_parameter(const std::string name, double value) : name(name), double_value(value)
{
  value_type = 'F';
}

parsed_command_parameter::
parsed_command_parameter(const std::string name, const std::string value) : name(name), string_value(value)
{
  value_type = 'S';
}

parsed_command_parameter::
parsed_command_parameter(const std::string name, const unsigned long value) : name(name), unsigned_long_value(value)
{
  value_type = 'U';
}

parsed_command_parameter::~parsed_command_parameter()
{
}

PyObject* parsed_command_parameter::value_to_py_object()
{
  PyObject* ret_val;
  // check the parameter type
  if (value_type == 'F')
  {
    ret_val = PyFloat_FromDouble(double_value);
    if (ret_val == NULL)
    {
      std::string message = "parsedCommandParameter.value_to_py_object: Unable to convert double value to a PyObject.";
      octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
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
    ret_val = PyUnicode_SafeFromString(string_value.c_str());
    if (ret_val == NULL)
    {
      std::string message = "parsedCommandParameter.value_to_py_object: Unable to convert string value to a PyObject.";
      octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
      return NULL;
    }
  }
  else if (value_type == 'U')
  {
    ret_val = PyLong_FromUnsignedLong(unsigned_long_value);
    if (ret_val == NULL)
    {
      std::string message =
        "parsedCommandParameter.value_to_py_object: Unable to convert unsigned long value to a PyObject.";
      octolapse_log_exception(octolapse_log::GCODE_PARSER, message);
      return NULL;
    }
  }
  else
  {
    std::string message = "The command parameter value type does not exist.  Value Type: ";
    message += value_type;
    octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
    // There has been an error, we don't support this value_type!
    return NULL;
  }

  return ret_val;
}
