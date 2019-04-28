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
#include "GcodePosition.h"
#include <math.h>
#include <iostream>
#include "Logging.h"

gcode_position::gcode_position()
{
	_autodetect_position = false;
	_origin_x = 0;
	_origin_y = 0;
	_origin_z = 0;
	_origin_x_none = true;
	_origin_y_none = true;
	_origin_z_none = true;

	_retraction_length = 0;
	_z_lift_height = 0;
	_priming_height = 0;
	_minimum_layer_height = 0;
	_g90_influences_extruder = false;
	_e_axis_default_mode = "absolute";
	_xyz_axis_default_mode = "absolute";
	_units_default = "millimeters";
	_gcode_functions = GetGcodeFunctions();

	p_previous_pos = new position(_xyz_axis_default_mode, _e_axis_default_mode, _units_default);
	p_current_pos = new position(_xyz_axis_default_mode, _e_axis_default_mode, _units_default);
	p_undo_pos = new position(_xyz_axis_default_mode, _e_axis_default_mode, _units_default);
}

gcode_position::gcode_position(gcode_position_args* args)
{
	_autodetect_position = args->autodetect_position;
	_origin_x = args->origin_x;
	_origin_y = args->origin_y;
	_origin_z = args->origin_z;
	_origin_x_none = args->origin_x_none;
	_origin_y_none = args->origin_y_none;
	_origin_z_none = args->origin_z_none;

	_retraction_length = args->retraction_length;
	_z_lift_height = args->z_lift_height;
	_priming_height = args->priming_height;
	_minimum_layer_height = args->minimum_layer_height;
	_g90_influences_extruder = args->g90_influences_extruder;
	_e_axis_default_mode = args->e_axis_default_mode;
	_xyz_axis_default_mode = args->xyz_axis_default_mode;
	_units_default = args->units_default;
	_gcode_functions = GetGcodeFunctions();

	p_previous_pos = new position(_xyz_axis_default_mode,_e_axis_default_mode, _units_default);
	p_current_pos = new position(_xyz_axis_default_mode, _e_axis_default_mode, _units_default);
	p_undo_pos = new position(_xyz_axis_default_mode, _e_axis_default_mode, _units_default);
}

gcode_position::gcode_position(const gcode_position &source)
{
	// Private copy constructor - you can't copy this class
}

gcode_position::~gcode_position()
{
	if (p_previous_pos != NULL)
	{
		delete p_previous_pos;
		p_previous_pos = NULL;
	}
	if (p_current_pos != NULL)
	{
		delete p_current_pos;
		p_current_pos = NULL;
	}
	if (p_undo_pos != NULL)
	{
		delete p_undo_pos;
		p_undo_pos = NULL;
	}
}

const double ZERO_TOLERANCE = 0.000000005;

bool gcode_position::is_equal(double x, double y)
{
	return fabs(x - y) < ZERO_TOLERANCE;
}

bool gcode_position::greater_than(double x, double y)
{
	return x > y && !is_equal(x, y);
}

bool gcode_position::greater_than_or_equal(double x, double y)
{
	return x > y || is_equal(x, y);
}

bool gcode_position::less_than(double x, double y)
{
	return x < y && !is_equal(x, y);
}

bool gcode_position::less_than_or_equal(double x, double y)
{
	return x < y || is_equal(x, y);
}

bool gcode_position::is_zero(double x)
{
	return fabs(x) < ZERO_TOLERANCE;
}

void gcode_position::update(parsed_command *command,int file_line_number, int gcode_number)
{
	if (command->cmd.empty())
		return;
	// Move the current position to the previous and the previous to the undo position
	// then copy previous to current

	position * old_undo_pos = p_undo_pos;
	p_undo_pos = p_previous_pos;
	p_previous_pos = p_current_pos;
	p_current_pos = old_undo_pos;
	position::copy(*p_previous_pos, p_current_pos);
	p_current_pos->reset_state();

	// add our parsed command to the current position
	if (p_current_pos->p_command != NULL)
	{
		delete p_current_pos->p_command;
		p_current_pos->p_command = NULL;
	}
	p_current_pos->p_command = new parsed_command(*command);

	p_current_pos->file_line_number = file_line_number;
	p_current_pos->gcode_number = gcode_number;
	// Does our function exist in our functions map?
	_gcode_functions_iterator = _gcode_functions.find(command->cmd);
	if (_gcode_functions_iterator != _gcode_functions.end())
	{
		// Execute the function to process this gcode
		posFunctionType func = _gcode_functions_iterator->second;
		(this->*func)(p_current_pos, command);

		// Have the XYZ positions changed after processing a command ?
		p_current_pos->e_relative = p_current_pos->e - p_previous_pos->e;
		p_current_pos->has_xy_position_changed = (
			!is_equal(p_current_pos->x, p_previous_pos->x) ||
			!is_equal(p_current_pos->y, p_previous_pos->y)
		);
		p_current_pos->has_position_changed = (
			p_current_pos->has_xy_position_changed ||
			!is_equal(p_current_pos->z, p_previous_pos->z) ||
			!is_zero(p_current_pos->e_relative) ||
			p_current_pos->x_null != p_previous_pos->x_null ||
			p_current_pos->y_null != p_previous_pos->y_null ||
			p_current_pos->z_null != p_previous_pos->z_null);

		// see if our position is homed
		if (!p_current_pos->has_homed_position)
		{
			p_current_pos->has_homed_position = (
				p_current_pos->x_homed &&
				p_current_pos->y_homed &&
				p_current_pos->z_homed &&
				p_current_pos->is_metric &&
				!p_current_pos->is_metric_null &&
				!p_current_pos->x_null &&
				!p_current_pos->y_null &&
				!p_current_pos->z_null &&
				!p_current_pos->is_relative_null &&
				!p_current_pos->is_extruder_relative_null);
		}
	}

	if (p_current_pos->has_position_changed)
	{
		p_current_pos->extrusion_length_total += p_current_pos->e_relative;

		if (greater_than(p_current_pos->e_relative, 0) && p_previous_pos->is_extruding && !p_previous_pos->is_extruding_start)
		{
			// A little shortcut if we know we were extruding (not starting extruding) in the previous command
			// This lets us skip a lot of the calculations for the extruder, including the state calculation
			p_current_pos->extrusion_length = p_current_pos->e_relative;
		}
		else
		{
			
			// Update retraction_length and extrusion_length
			p_current_pos->retraction_length = p_current_pos->retraction_length - p_current_pos->e_relative;
			if (less_than_or_equal(p_current_pos->retraction_length, 0))
			{
				// we can use the negative retraction length to calculate our extrusion length!
				p_current_pos->extrusion_length = -1.0 * p_current_pos->retraction_length;
				// set the retraction length to 0 since we are extruding
				p_current_pos->retraction_length = 0;
			}
			else
				p_current_pos->extrusion_length = 0;

			// calculate deretraction length
			if (greater_than(p_previous_pos->retraction_length, p_current_pos->retraction_length))
			{
				p_current_pos->deretraction_length = p_previous_pos->retraction_length - p_current_pos->retraction_length;
			}
			else
				p_current_pos->deretraction_length = 0;
			
			// *************Calculate extruder state*************
			// rounding should all be done by now
			p_current_pos->is_extruding_start = greater_than(p_current_pos->extrusion_length, 0) && !p_previous_pos->is_extruding;
			p_current_pos->is_extruding = greater_than(p_current_pos->extrusion_length, 0);
			p_current_pos->is_primed = is_zero(p_current_pos->extrusion_length) && is_zero(p_current_pos->retraction_length);
			p_current_pos->is_retracting_start = !p_previous_pos->is_retracting && greater_than(p_current_pos->retraction_length, 0);
			p_current_pos->is_retracting = greater_than(p_current_pos->retraction_length, p_previous_pos->retraction_length);
			p_current_pos->is_partially_retracted = greater_than(p_current_pos->retraction_length, 0) && less_than(p_current_pos->retraction_length, _retraction_length);
			p_current_pos->is_retracted = greater_than_or_equal(p_current_pos->retraction_length, _retraction_length);
			p_current_pos->is_deretracting_start = greater_than(p_current_pos->deretraction_length, 0) && !p_previous_pos->is_deretracting;
			p_current_pos->is_deretracting = greater_than(p_current_pos->deretraction_length, p_previous_pos->deretraction_length);
			p_current_pos->is_deretracted = greater_than(p_previous_pos->retraction_length,0) && is_zero(p_current_pos->retraction_length);
			// *************End Calculate extruder state*************
		}
		// calculate last_extrusion_height and height
		// If we are extruding on a higher level, or if retract is enabled and the nozzle is primed
		// adjust the last extrusion height
		if (!is_equal(p_current_pos->z, p_current_pos->last_extrusion_height))
		{
			if (!p_current_pos->z_null)
			{
				if (p_current_pos->is_extruding)
				{
					p_current_pos->last_extrusion_height = p_current_pos->z;
					p_current_pos->last_extrusion_height_null = false;
					// Is Primed
					if (!p_current_pos->is_printer_primed)
					{
						// We haven't primed yet, check to see if we have priming height restrictions
						if (greater_than(_priming_height, 0))
						{
							// if a priming height is configured, see if we've extruded below the  height
							if (less_than(p_current_pos->last_extrusion_height, _priming_height))
								p_current_pos->is_printer_primed = true;
						}
						else
							// if we have no priming height set, just set is_printer_primed = true.
							p_current_pos->is_printer_primed = true;
					}

					// Has Reached Minimum layer height
					if (!p_current_pos->minimum_layer_height_reached)
					{
						if (greater_than(_minimum_layer_height, 0))
						{
							// if a minimum layer height is configured, see if we've extruded above it
							if (greater_than_or_equal(p_current_pos->last_extrusion_height, _minimum_layer_height))
								p_current_pos->minimum_layer_height_reached = true;
						}
						else
							// if we have no minimum layer height set, just set to true
							p_current_pos->minimum_layer_height_reached = true;
					}
				}

				// Calculate layer Change
				if (
					((p_current_pos->is_primed && greater_than(p_current_pos->layer, 0)) || p_current_pos->is_extruding)
					&& p_current_pos->is_printer_primed)
				{

					if (greater_than(p_current_pos->z, p_previous_pos->height))
					{
						p_current_pos->height = p_current_pos->z;
						// calculate layer change
						if (p_current_pos->minimum_layer_height_reached && greater_than(p_current_pos->height - p_previous_pos->height, 0) || p_current_pos->layer == 0)
						{
							p_current_pos->is_layer_change = true;
							p_current_pos->layer++;
						}
					}
				}
				// calculate is_zhop
				if (p_current_pos->is_extruding || p_current_pos->z_null || p_current_pos->last_extrusion_height_null)
					p_current_pos->is_zhop = false;
				else
					p_current_pos->is_zhop = greater_than_or_equal(p_current_pos->z - p_current_pos->last_extrusion_height, _z_lift_height);
			}

		}

		// Calcluate position restructions
		// TODO:  INCLUDE POSITION RESTRICTION CALCULATIONS!
		// tODO:  iNCLUDE FEATURE DETECTION!
	}
	
}

void gcode_position::undo_update()
{
	position* temp = p_current_pos;
	p_current_pos = p_previous_pos;
	p_previous_pos = p_undo_pos;
	p_undo_pos = temp;
}

// Private Members
std::map<std::string, gcode_position::posFunctionType> gcode_position::GetGcodeFunctions()
{
	std::map<std::string, posFunctionType> newMap;
	newMap.insert(std::make_pair("G0", &gcode_position::process_g0_g1));
	newMap.insert(std::make_pair("G1", &gcode_position::process_g0_g1));
	newMap.insert(std::make_pair("G2", &gcode_position::process_g2));
	newMap.insert(std::make_pair("G3", &gcode_position::process_g3));
	newMap.insert(std::make_pair("G10", &gcode_position::process_g10));
	newMap.insert(std::make_pair("G11", &gcode_position::process_g11));
	newMap.insert(std::make_pair("G20", &gcode_position::process_g20));
	newMap.insert(std::make_pair("G21", &gcode_position::process_g21));
	newMap.insert(std::make_pair("G28", &gcode_position::process_g28));
	newMap.insert(std::make_pair("G90", &gcode_position::process_g90));
	newMap.insert(std::make_pair("G91", &gcode_position::process_g91));
	newMap.insert(std::make_pair("G92", &gcode_position::process_g92));
	newMap.insert(std::make_pair("M82", &gcode_position::process_m82));
	newMap.insert(std::make_pair("M83", &gcode_position::process_m83));
	newMap.insert(std::make_pair("M207", &gcode_position::process_m207));
	newMap.insert(std::make_pair("M208", &gcode_position::process_m208));
	return newMap;
}

void gcode_position::update_position(position* pos, double x, bool update_x, double y, bool update_y, double z, bool update_z, double e, bool update_e, double f, bool update_f, bool force, bool is_g1)
{
	if (is_g1)
	{
		pos->is_travel_only = !update_e && !update_z && (update_x || update_y);
	}
	if (update_f)
	{
		pos->f = f;
		pos->f_null = false;
	}

	if (force)
	{
		if (update_x)
		{
			pos->x = x + pos->x_offset;
			pos->x_null = false;
		}
		if (update_y)
		{
			pos->y = y + pos->y_offset;
			pos->y_null = false;
		}
		if (update_z)
		{
			pos->z = z + pos->z_offset;
			pos->z_null = false;
		}
		// note that e cannot be null and starts at 0
		if (update_e)
			pos->e = e + pos->e_offset;
		return;
	}

	if (!pos->is_relative_null)
	{
		if (pos->is_relative) {
			if (update_x)
			{
				if(!pos->x_null)
					pos->x = x + pos->x;
				else
				{
					octolapse_log(GCODE_POSITION, ERROR, "GcodePosition.update_position: Cannot update X because the XYZ axis mode is relative and X is null.");
				}
			}
			if (update_y)
			{
				if(!pos->y_null)
					pos->y = y + pos->y;
				else
				{
					octolapse_log(GCODE_POSITION, ERROR, "GcodePosition.update_position: Cannot update Y because the XYZ axis mode is relative and Y is null.");
				}
			}
			if (update_z)
			{
				if(!pos->z_null)
					pos->z = z + pos->z;
				else
				{
					octolapse_log(GCODE_POSITION, ERROR, "GcodePosition.update_position: Cannot update Z because the XYZ axis mode is relative and Z is null.");
				}
			}
		}
		else
		{
			if (update_x)
			{
				pos->x = x + pos->x_offset;
				pos->x_null = false;
			}
			if (update_y)
			{
				pos->y = y + pos->y_offset;
				pos->y_null = false;
			}
			if (update_z)
			{
				pos->z = z + pos->z_offset;
				pos->z_null = false;
			}
		}
	}
	else
	{
		std::string message = "The XYZ axis mode is not set, cannot update position.";
		octolapse_log(GCODE_POSITION, ERROR, message);
	}

	if (update_e)
	{
		if (!pos->is_extruder_relative_null)
		{
			if (pos->is_extruder_relative)
			{
				pos->e = e + pos->e;
			}
			else
			{
				pos->e = e + pos->e_offset;
			}
		}
		else
		{
			std::string message = "The E axis mode is not set, cannot update position.";
			octolapse_log(GCODE_POSITION, ERROR, message);
		}
	}
	
}

void gcode_position::process_g0_g1(position* posPtr, parsed_command* parsedCommandPtr)
{
	bool update_x = false;
	bool update_y = false;
	bool update_z = false;
	bool update_e = false;
	bool update_f = false;
	double x = 0;
	double y = 0;
	double z = 0;
	double e = 0;
	double f = 0;
	
	for (unsigned int index = 0; index < parsedCommandPtr->parameters.size(); index++)
	{
		parsed_command_parameter * p_cur_param = parsedCommandPtr->parameters[index];
		std::string cmdName = p_cur_param->name;
		if (cmdName == "X")
		{
			update_x = true;
			x = p_cur_param->double_value;
		}
		else if (cmdName == "Y")
		{
			update_y = true;
			y = p_cur_param->double_value;
		}
		else if (cmdName == "E")
		{
			update_e = true;
			e = p_cur_param->double_value;
		}
		else if (cmdName == "Z")
		{
			update_z = true;
			z = p_cur_param->double_value;
		}
		else if (cmdName == "F")
		{
			update_f = true;
			f = p_cur_param->double_value;
		}
	}
	update_position(posPtr, x, update_x, y, update_y, z, update_z, e, update_e, f, update_f, false, true);
}

void gcode_position::process_g2(position* posPtr, parsed_command* parsedCommandPtr)
{
	// ToDo:  Fix G2
}

void gcode_position::process_g3(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: Fix G3
}

void gcode_position::process_g10(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: Fix G10
}

void gcode_position::process_g11(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: Fix G11
}

void gcode_position::process_g20(position* posPtr, parsed_command* parsedCommandPtr)
{

}

void gcode_position::process_g21(position* posPtr, parsed_command* parsedCommandPtr)
{

}

void gcode_position::process_g28(position* p_position, parsed_command* p_parsed_command)
{
	bool has_x = false;
	bool has_y = false;
	bool has_z = false;
	bool set_x_origin = false;
	bool set_y_origin = false;
	bool set_z_origin = false;

	for (unsigned int index = 0; index < p_parsed_command->parameters.size(); index++)
	{
		parsed_command_parameter* p_cur_param = p_parsed_command->parameters[index];
		if (p_cur_param->name == "X")
			has_x = true;
		else if (p_cur_param->name == "Y")
			has_y = true;
		else if (p_cur_param->name == "Z")
			has_z = true;
	}
	if (has_x)
	{
		p_position->x_homed = true;
		if (_autodetect_position)
			set_x_origin = true;
	}
	if (has_y)
	{
		p_position->y_homed = true;
		if (!_autodetect_position)
			set_y_origin = true;
	}
	if (has_z)
	{
		p_position->z_homed = true;
		if (!_autodetect_position)
			set_z_origin = true;
	}
	if (!has_x && !has_y && !has_z)
	{
		p_position->x_homed = true;
		p_position->y_homed = true;
		p_position->z_homed = true;
		if (!_autodetect_position)
		{
			set_x_origin = true;
			set_y_origin = true;
			set_z_origin = true;
		}
	}

	if (set_x_origin && !_origin_x_none)
	{
		p_position->x = _origin_x;
		p_position->x_null = false;
	}
	// todo: set error flag on else
	if (set_y_origin && !_origin_y_none)
	{
		p_position->y = _origin_y;
		p_position->y_null = false;
	}
	// todo: set error flag on else
	if (set_z_origin && !_origin_z_none)
	{
		p_position->z = _origin_z;
		p_position->z_null = false;
	}
	// todo: set error flag on else
}

void gcode_position::process_g90(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set xyz to absolute mode
	if (posPtr->is_relative_null)
		posPtr->is_relative_null = false;

	posPtr->is_relative = false;

	if (_g90_influences_extruder)
	{
		// If g90/g91 influences the extruder, set the extruder to absolute mode too
		if (posPtr->is_extruder_relative_null)
			posPtr->is_extruder_relative_null = false;

		posPtr->is_extruder_relative = false;
	}

}

void gcode_position::process_g91(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set XYZ axis to relative mode
	if (posPtr->is_relative_null)
		posPtr->is_relative_null = false;

	posPtr->is_relative = true;

	if (_g90_influences_extruder)
	{
		// If g90/g91 influences the extruder, set the extruder to relative mode too
		if (posPtr->is_extruder_relative_null)
			posPtr->is_extruder_relative_null = false;

		posPtr->is_extruder_relative = true;
	}
}

void gcode_position::process_g92(position* p_position, parsed_command* p_parsed_command)
{
	// Set position offset
	bool update_x = false;
	bool update_y = false;
	bool update_z = false;
	bool update_e = false;
	bool o_exists = false;
	double x = 0;
	double y = 0;
	double z = 0;
	double e = 0;
	for (unsigned int index = 0; index < p_parsed_command->parameters.size(); index++)
	{
		parsed_command_parameter * p_cur_param = p_parsed_command->parameters[index];
		std::string cmdName = p_cur_param->name;
		if (cmdName == "X")
		{
			update_x = true;
			x = p_cur_param->double_value;
		}
		else if (cmdName == "Y")
		{
			update_y = true;
			y = p_cur_param->double_value;
		}
		else if (cmdName == "E")
		{
			update_e = true;
			e = p_cur_param->double_value;
		}
		else if (cmdName == "Z")
		{
			update_z = true;
			z = p_cur_param->double_value;
		}
		else if (cmdName == "O")
		{
			o_exists = true;
		}
	}

	if (o_exists)
	{
		// Our fake O parameter exists, set axis to homed!
		// This is a workaround to allow folks to use octolapse without homing (for shame, lol!)
		p_position->x_homed = true;
		p_position->y_homed = true;
		p_position->z_homed = true;
	}

	if (!o_exists && !update_x && !update_y && !update_z && !update_e)
	{
		if (!p_position->x_null)
			p_position->x_offset = p_position->x;
		if (!p_position->y_null)
			p_position->y_offset = p_position->y;
		if (!p_position->z_null)
			p_position->z_offset = p_position->z;
		// Todo:  Does this reset E too?  Figure that $#$$ out Formerlurker!
		p_position->e_offset = p_position->e;
	}
	else
	{
		if (update_x)
		{
			if (!p_position->x_null && p_position->x_homed)
				p_position->x_offset = p_position->x - x;
			else
			{
				p_position->x = x;
				p_position->x_offset = 0;
				p_position->x_null = false;
			}
		}
		if (update_y)
		{
			if (!p_position->y_null && p_position->y_homed)
				p_position->y_offset = p_position->y - y;
			else
			{
				p_position->y = y;
				p_position->y_offset = 0;
				p_position->y_null = false;
			}
		}
		if (update_z)
		{
			if (!p_position->z_null && p_position->z_homed)
				p_position->z_offset = p_position->z - z;
			else
			{
				p_position->z = z;
				p_position->z_offset = 0;
				p_position->z_null = false;
			}
		}
		if (update_e)
		{
			p_position->e_offset = p_position->e - e;
		}
	}
}

void gcode_position::process_m82(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set extrder mode to absolute
	if (posPtr->is_extruder_relative_null)
		posPtr->is_extruder_relative_null = false;

	posPtr->is_extruder_relative = false;
}

void gcode_position::process_m83(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set extrder mode to relative
	if (posPtr->is_extruder_relative_null)
		posPtr->is_extruder_relative_null = false;

	posPtr->is_extruder_relative = true;
}

void gcode_position::process_m207(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: impemente firmware retract
}

void gcode_position::process_m208(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: implement firmware retract
}
