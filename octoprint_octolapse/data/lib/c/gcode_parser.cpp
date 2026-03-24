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
#include "utilities.h"

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
  parsable_command_names.push_back("M218");
  parsable_command_names.push_back("M240");
  parsable_command_names.push_back("M400");
  parsable_command_names.push_back("M563");
  parsable_command_names.push_back("T");
  parsable_command_names.push_back("@OCTOLAPSE");

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

gcode_parser::gcode_parser(const gcode_parser& source)
{
  // Private copy constructor - you can't copy this class
}

gcode_parser::~gcode_parser()
{
  text_only_functions_.clear();
  parsable_commands_.clear();
}

parsed_command gcode_parser::parse_gcode(const char* gcode)
{
  parsed_command p_cmd;
  try_parse_gcode(gcode, p_cmd);
  return p_cmd;
}

// Superfast gcode parser - v2
bool gcode_parser::try_parse_gcode(const char* gcode, parsed_command& command)
{
  // Create a command
  //octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::VERBOSE, gcode);
  char* p_gcode = const_cast<char *>(gcode);
  char* p = const_cast<char *>(gcode);
  command.is_empty = true;
  command.is_known_command = try_extract_gcode_command(&p, &(command.command));
  if (!command.is_known_command)
  {
    while (true)
    {
      char c = *p_gcode;
      if (c == '\0' || c == ';' || c == ' ' || c == '\t')
        break;
      else if (c > 31)
      {
        command.is_empty = false;
        break;
      }
      p_gcode++;
    }
    // Don't bother logging this...  Not worth it
    //std::string message = "No gcode command was found: ";
    //message += gcode;
    //octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::DEBUG, message);
    command.command = "";
  }
  else
    command.is_empty = false;

  bool has_seen_character = false;
  while (true)
  {
    char cur_char = *p_gcode;
    if (cur_char == '\0' || cur_char == ';')
      break;
    else if (cur_char > 32 || cur_char == ' ' && has_seen_character)
    {
      if (cur_char >= 'a' && cur_char <= 'z')
        command.gcode.push_back(cur_char - 32);
      else
        command.gcode.push_back(cur_char);
      has_seen_character = true;
    }
    p_gcode++;
  }
  command.gcode = utilities::rtrim(command.gcode);

  if (command.is_known_command)
  {
    //command->gcode_ = gcode;
    //std::vector<parsed_command_parameter> parameters;

    if (parsable_commands_.find(command.command) == parsable_commands_.end())
    {
      // Don't bother logging this.  Too much logging.
      //std::string message = "The gcode command is not in the parsable commands set: ";
      //message += gcode;
      //octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::VERBOSE, message);
      return true;
    }
    if (command.command.length() > 0 && command.command == "@OCTOLAPSE")
    {
      parsed_command_parameter octolapse_parameter;

      if (!try_extract_octolapse_parameter(&p, &octolapse_parameter))
      {
        std::string message = "Unable to extract an octolapse parameter from: ";
        message += p;
        octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::WARNING, message);
        return true;
      }
      command.parameters.push_back(octolapse_parameter);
      // Extract any additional parameters the old way
      while (true)
      {
        //std::cout << "GcodeParser.try_parse_gcode - Trying to extract parameters.\r\n";
        parsed_command_parameter param;
        if (try_extract_parameter(&p, &param))
          command.parameters.push_back(param);
        else
        {
          //std::cout << "GcodeParser.try_parse_gcode - No parameters found.\r\n";
          break;
        }
      }
    }
    else if (
      text_only_functions_.find(command.command) != text_only_functions_.end() ||
      (
        command.command.length() > 0 && command.command[0] == '@'
      )
    )
    {
      //std::cout << "GcodeParser.try_parse_gcode - Text only parameter found.\r\n";
      parsed_command_parameter text_command;
      if (!try_extract_text_parameter(&p, &(text_command.string_value)))
      {
        std::string message = "Unable to extract a text parameter from: ";
        message += p;
        octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::WARNING, message);
        return true;
      }
      text_command.name = '\0';
      command.parameters.push_back(text_command);
    }
    else
    {
      if (command.command[0] == 'T')
      {
        //std::cout << "GcodeParser.try_parse_gcode - T parameter found.\r\n";
        parsed_command_parameter param;

        if (!try_extract_t_parameter(&p, &param))
        {
          std::string message = "Unable to extract a parameter from the T command: ";
          message += gcode;
          octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::ERROR, message);
        }
        else
          command.parameters.push_back(param);
      }
      else
      {
        while (true)
        {
          //std::cout << "GcodeParser.try_parse_gcode - Trying to extract parameters.\r\n";
          parsed_command_parameter param;
          if (try_extract_parameter(&p, &param))
            command.parameters.push_back(param);
          else
          {
            //std::cout << "GcodeParser.try_parse_gcode - No parameters found.\r\n";
            break;
          }
        }
      }
    }
  }
  try_extract_comment(&p_gcode, &(command.comment));


  return command.is_known_command;
}

bool gcode_parser::try_extract_gcode_command(char** p_p_gcode, std::string* p_command)
{
  char* p = *p_p_gcode;
  char gcode_word;
  bool found_command = false;

  // Ignore Leading Spaces
  while (*p == ' ')
  {
    p++;
  }
  // See if this is an @ command, which can be used in octoprint for controlling octolapse
  if (*p == '@')
  {
    found_command = gcode_parser::try_extract_at_command(&p, p_command);
  }
  else
  {
  }
  // Deal with case sensitivity
  if (*p >= 'a' && *p <= 'z')
    gcode_word = *p - 32;
  else
    gcode_word = *p;
  if (gcode_word == 'G' || gcode_word == 'M' || gcode_word == 'T')
  {
    // Set the gcode word of the new command to the current pointer's location and increment both
    (*p_command).push_back(gcode_word);
    p++;

    if (gcode_word != 'T')
    {
      // the T command is special, it has no address

      // Now look for a command address
      while ((*p >= '0' && *p <= '9') || *p == ' ')
      {
        if (*p != ' ')
        {
          found_command = true;
          (*p_command).push_back(*p++);
        }
        else if (found_command)
        {
          // Previously we just ignored all spaces,
          // but for the command itself, it might be a good idea
          // to assume the space is important.
          // instead, keep moving forward until no spaces are found
          while (*p == ' ')
          {
            p++;
          }
          break;
        }
        else
        {
          // a space was encountered, but no command was found.
          // increment the pointer and continue to search
          // for an address
          ++p;
        }
      }
      if (*p == '.')
      {
        (*p_command).push_back(*p++);
        found_command = false;
        while ((*p >= '0' && *p <= '9') || *p == ' ')
        {
          if (*p != ' ')
          {
            found_command = true;
            (*p_command).push_back(*p++);
          }
          else
            ++p;
        }
      }
    }
    else
    {
      // peek at the next character and see if it is either a number, a question mark, a c, x, or integer.
      // Use a different pointer so as not to mess up parameter parsing
      char* p_t = p;
      // skip any whitespace
      // Ignore Leading Spaces
      while (*p_t == ' ' || *p_t == '\t')
      {
        p_t++;
      }
      // create a char to hold the t parameter
      char t_param = '\0';
      // 
      if (*p_t >= 'a' && *p_t <= 'z')
        t_param = *p_t - 32;
      else
        t_param = *p_t;


      if (t_param == 'C' || t_param == 'X' || t_param == '?')
      {
        p_t++;
        // The next letter looks good!  Now see if there are any other characters before the end of the line (excluding comments)
        while (*p_t == ' ' || *p_t == '\t')
        {
          p_t++;
        }
        if (*p_t == ';' || *p_t == '\0')
          found_command = true;
      }
      else if (t_param >= '0' && t_param <= '9')
      {
        found_command = true;
      }
    }
  }
  *p_p_gcode = p;
  return found_command;
}

bool gcode_parser::try_extract_at_command(char** p_p_gcode, std::string* p_command)
{
  char* p = *p_p_gcode;
  bool found_command = false;
  while (*p != '\0' && *p != ';' && *p != ' ')
  {
    if (!found_command)
    {
      found_command = true;
    }
    if (*p >= 'a' && *p <= 'z')
      (*p_command).push_back(*p++ - 32);
    else
      (*p_command).push_back(*p++);
  }
  *p_p_gcode = p;
  return found_command;
}

bool gcode_parser::try_extract_unsigned_long(char** p_p_gcode, unsigned long* p_value)
{
  char* p = *p_p_gcode;
  unsigned int r = 0;
  bool found_numbers = false;
  // skip any leading whitespace
  while (*p == ' ')
    ++p;

  while ((*p >= '0' && *p <= '9') || *p == ' ')
  {
    if (*p != ' ')
    {
      found_numbers = true;
      r = static_cast<unsigned int>((r * 10.0) + (*p - '0'));
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

double gcode_parser::ten_pow(unsigned short n)
{
  double r = 1.0;

  while (n > 0)
  {
    r *= 10;
    --n;
  }

  return r;
}

bool gcode_parser::try_extract_double(char** p_p_gcode, double* p_double) const
{
  char* p = *p_p_gcode;
  bool neg = false;
  double r = 0;
  bool found_numbers = false;
  // skip any leading whitespace
  while (*p == ' ')
    ++p;
  // Check for negative sign
  if (*p == '-')
  {
    neg = true;
    ++p;
    while (*p == ' ')
      ++p;
  }
  else if (*p == '+')
  {
    // Positive sign doesn't affect anything since we assume positive
    ++p;
    while (*p == ' ')
      ++p;
  }
  // skip any additional whitespace


  while ((*p >= '0' && *p <= '9') || *p == ' ')
  {
    if (*p != ' ')
    {
      found_numbers = true;
      r = (r * 10.0) + (*p - '0');
    }
    ++p;
  }
  if (*p == '.')
  {
    double f = 0.0;
    unsigned short n = 0;
    ++p;
    while ((*p >= '0' && *p <= '9') || *p == ' ')
    {
      if (*p != ' ')
      {
        found_numbers = true;
        f = (f * 10.0) + (*p - '0');
        ++n;
      }
      ++p;
    }
    //r += f / std::pow(10.0, n);
    r += f / ten_pow(n);
  }
  if (neg)
  {
    r = -r;
  }
  if (found_numbers)
  {
    *p_double = r;
    *p_p_gcode = p;
  }

  return found_numbers;
}

bool gcode_parser::try_extract_text_parameter(char** p_p_gcode, std::string* p_parameter)
{
  // Skip initial whitespace
  //std::cout << "GcodeParser.try_extract_parameter - Trying to extract a text parameter from  " << *p_p_gcode << "\r\n";
  char* p = *p_p_gcode;

  // Ignore Leading Spaces
  while (*p == ' ')
  {
    p++;
  }
  // Add all values, stop at end of string or when we hit a ';'

  while (*p != '\0' && *p != ';')
  {
    (*p_parameter).push_back(*p++);
  }
  *p_p_gcode = p;
  return true;
}

bool gcode_parser::try_extract_octolapse_parameter(char** p_p_gcode, parsed_command_parameter* p_parameter)
{
  p_parameter->name = "";
  p_parameter->value_type = 'N';
  // Skip initial whitespace
  //std::cout << "GcodeParser.try_extract_parameter - Trying to extract a text parameter from  " << *p_p_gcode << "\r\n";
  char* p = *p_p_gcode;
  bool has_found_parameter = false;
  // Ignore Leading Spaces
  while (*p == ' ')
  {
    p++;
  }
  // extract name, make all caps.
  while (*p != '\0' && *p != ';' && *p != ' ')
  {
    if (!has_found_parameter)
    {
      has_found_parameter = true;
    }

    if (*p >= 'a' && *p <= 'z')
    {
      p_parameter->name.push_back(*p++ - 32);
    }
    else
    {
      p_parameter->name.push_back(*p++);
    }
  }
  // Todo: Handle any otolapse commands require a string parameter
  /*
  // Ignore spaces after the command name
  while (*p == ' ')
  {
    p++;
  }
  // Extract the value (we may do this per command in the future).  This will output mixed case.
  bool has_parameter_value = false;
  while (*p != '\0' && *p != ';')
  {
    if (!has_parameter_value)
    {
      p_parameter->value_type = 'S';
      has_parameter_value = true;
    }
    p_parameter->string_value.push_back(*p++);
  }
  if (has_parameter_value)
  {
    p_parameter->string_value = utilities::rtrim(p_parameter->string_value);
  }
  */
  *p_p_gcode = p;
  return has_found_parameter;
}

bool gcode_parser::try_extract_parameter(char** p_p_gcode, parsed_command_parameter* parameter) const
{
  //std::cout << "GcodeParser.try_extract_parameter - Trying to extract a parameter from  " << *p_p_gcode << "\r\n";
  char* p = *p_p_gcode;

  // Ignore Leading Spaces
  while (*p == ' ')
  {
    p++;
  }

  // Deal with case sensitivity
  if (*p >= 'a' && *p <= 'z')
    parameter->name = *p++ - 32;
  else if (*p >= 'A' && *p <= 'Z')
    parameter->name = *p++;
  else
    return false;
  // TODO:  See if unsigned long works....

  // Add all values, stop at end of string or when we hit a ';'
  if (try_extract_double(&p, &(parameter->double_value)))
  {
    parameter->value_type = 'F';
  }
  else
  {
    if (try_extract_text_parameter(&p, &(parameter->string_value)))
    {
      parameter->value_type = 'S';
    }
    else
    {
      return false;
    }
  }

  *p_p_gcode = p;
  return true;
}

bool gcode_parser::try_extract_t_parameter(char** p_p_gcode, parsed_command_parameter* parameter)
{
  //std::cout << "Trying to extract a T parameter from " << *p_p_gcode << "\r\n";
  char* p = *p_p_gcode;
  parameter->name = 'T';
  // Ignore Leading Spaces
  while (*p == L' ')
  {
    p++;
  }

  if (*p == L'c' || *p == L'C')
  {
    //std::cout << "Found C value for T parameter\r\n";
    parameter->string_value = "C";
    parameter->value_type = 'S';
  }
  else if (*p == L'x' || *p == L'X')
  {
    //std::cout << "Found X value for T parameter\r\n";
    parameter->string_value = "X";
    parameter->value_type = 'S';
  }
  else if (*p == L'?')
  {
    //std::cout << "Found ? value for T parameter\r\n";
    parameter->string_value = "?";
    parameter->value_type = 'S';
  }
  else
  {
    //std::cout << "No char t parameter found, looking for unsigned int values.\r\n";
    if (!try_extract_unsigned_long(&p, &(parameter->unsigned_long_value)))
    {
      std::string message = "GcodeParser.try_extract_t_parameter: Unable to extract parameters from the T command.";
      octolapse_log(octolapse_log::GCODE_PARSER, octolapse_log::WARNING, message);
      //std::cout << "No parameter for the T command.\r\n";
      return false;
    }
    parameter->value_type = 'U';
  }
  return true;
}

bool gcode_parser::try_extract_comment(char** p_p_gcode, std::string* p_comment)
{
  // Skip initial whitespace
  //std::cout << "GcodeParser.try_extract_parameter - Trying to extract a text parameter from  " << *p_p_gcode << "\r\n";
  char* p = *p_p_gcode;

  // Ignore Leading Spaces
  while (*p != '\0' && *p != ';')
  {
    p++;
  }

  // Add all values, stop at end of string or when we hit a ';'
  while (*p == ';' || *p == ' ')
  {
    p++;
  }
  while (*p != '\0')
  {
    if (*p != '\r' && *p != '\n')
      (*p_comment).push_back(*p++);
    else
      p++;
  }
  *p_p_gcode = p;
  return p_comment->length() != 0;
}
