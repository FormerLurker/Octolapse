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
#include "gcode_position.h"
#include <math.h>
#include <iostream>
#include "logging.h"

gcode_position::gcode_position()
{
	autodetect_position_ = false;
	origin_x_ = 0;
	origin_y_ = 0;
	origin_z_ = 0;
	origin_x_none_ = true;
	origin_y_none_ = true;
	origin_z_none_ = true;

	retraction_length_ = 0;
	z_lift_height_ = 0;
	priming_height_ = 0;
	minimum_layer_height_ = 0;
	g90_influences_extruder_ = false;
	e_axis_default_mode_ = "absolute";
	xyz_axis_default_mode_ = "absolute";
	units_default_ = "millimeters";
	gcode_functions_ = get_gcode_functions();

	p_previous_pos_ = new position(xyz_axis_default_mode_, e_axis_default_mode_, units_default_);
	p_current_pos_ = new position(xyz_axis_default_mode_, e_axis_default_mode_, units_default_);
	p_undo_pos_ = new position(xyz_axis_default_mode_, e_axis_default_mode_, units_default_);
}

gcode_position::gcode_position(gcode_position_args* args)
{
	autodetect_position_ = args->autodetect_position;
	origin_x_ = args->origin_x;
	origin_y_ = args->origin_y;
	origin_z_ = args->origin_z;
	origin_x_none_ = args->origin_x_none;
	origin_y_none_ = args->origin_y_none;
	origin_z_none_ = args->origin_z_none;

	retraction_length_ = args->retraction_length;
	z_lift_height_ = args->z_lift_height;
	priming_height_ = args->priming_height;
	minimum_layer_height_ = args->minimum_layer_height;
	g90_influences_extruder_ = args->g90_influences_extruder;
	e_axis_default_mode_ = args->e_axis_default_mode;
	xyz_axis_default_mode_ = args->xyz_axis_default_mode;
	units_default_ = args->units_default;
	gcode_functions_ = get_gcode_functions();

	p_previous_pos_ = new position(xyz_axis_default_mode_,e_axis_default_mode_, units_default_);
	p_current_pos_ = new position(xyz_axis_default_mode_, e_axis_default_mode_, units_default_);
	p_undo_pos_ = new position(xyz_axis_default_mode_, e_axis_default_mode_, units_default_);
}

gcode_position::gcode_position(const gcode_position &source)
{
	// Private copy constructor - you can't copy this class
}

gcode_position::~gcode_position()
{
	if (p_previous_pos_ != NULL)
	{
		delete p_previous_pos_;
		p_previous_pos_ = NULL;
	}
	if (p_current_pos_ != NULL)
	{
		delete p_current_pos_;
		p_current_pos_ = NULL;
	}
	if (p_undo_pos_ != NULL)
	{
		delete p_undo_pos_;
		p_undo_pos_ = NULL;
	}
}

position * gcode_position::get_current_position()
{
	return p_current_pos_;
}

position * gcode_position::get_previous_position()
{
	return p_previous_pos_;
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
	if (command->cmd_.empty())
		return;
	// Move the current position to the previous and the previous to the undo position
	// then copy previous to current

	position * old_undo_pos = p_undo_pos_;
	p_undo_pos_ = p_previous_pos_;
	p_previous_pos_ = p_current_pos_;
	p_current_pos_ = old_undo_pos;
	position::copy(*p_previous_pos_, p_current_pos_);
	p_current_pos_->reset_state();

	// add our parsed command to the current position
	if (p_current_pos_->p_command != NULL)
	{
		delete p_current_pos_->p_command;
		p_current_pos_->p_command = NULL;
	}
	p_current_pos_->p_command = new parsed_command(*command);

	p_current_pos_->file_line_number_ = file_line_number;
	p_current_pos_->gcode_number_ = gcode_number;
	// Does our function exist in our functions map?
	gcode_functions_iterator_ = gcode_functions_.find(command->cmd_);
	if (gcode_functions_iterator_ != gcode_functions_.end())
	{
		p_current_pos_->gcode_ignored_ = false;
		// Execute the function to process this gcode
		posFunctionType func = gcode_functions_iterator_->second;
		(this->*func)(p_current_pos_, command);

		// Have the XYZ positions changed after processing a command ?
		p_current_pos_->e_relative_ = p_current_pos_->e_ - p_previous_pos_->e_;
		p_current_pos_->has_xy_position_changed_ = (
			!is_equal(p_current_pos_->x_, p_previous_pos_->x_) ||
			!is_equal(p_current_pos_->y_, p_previous_pos_->y_)
		);
		p_current_pos_->has_position_changed_ = (
			p_current_pos_->has_xy_position_changed_ ||
			!is_equal(p_current_pos_->z_, p_previous_pos_->z_) ||
			!is_zero(p_current_pos_->e_relative_) ||
			p_current_pos_->x_null_ != p_previous_pos_->x_null_ ||
			p_current_pos_->y_null_ != p_previous_pos_->y_null_ ||
			p_current_pos_->z_null_ != p_previous_pos_->z_null_);

		// see if our position is homed
		if (!p_current_pos_->has_homed_position_)
		{
			p_current_pos_->has_homed_position_ = (
				p_current_pos_->x_homed_ &&
				p_current_pos_->y_homed_ &&
				p_current_pos_->z_homed_ &&
				p_current_pos_->is_metric_ &&
				!p_current_pos_->is_metric_null_ &&
				!p_current_pos_->x_null_ &&
				!p_current_pos_->y_null_ &&
				!p_current_pos_->z_null_ &&
				!p_current_pos_->is_relative_null_ &&
				!p_current_pos_->is_extruder_relative_null_);
		}
	}

	if (p_current_pos_->has_position_changed_)
	{
		p_current_pos_->extrusion_length_total_ += p_current_pos_->e_relative_;

		if (greater_than(p_current_pos_->e_relative_, 0) && p_previous_pos_->is_extruding_ && !p_previous_pos_->is_extruding_start_)
		{
			// A little shortcut if we know we were extruding (not starting extruding) in the previous command
			// This lets us skip a lot of the calculations for the extruder, including the state calculation
			p_current_pos_->extrusion_length_ = p_current_pos_->e_relative_;
		}
		else
		{
			
			// Update retraction_length and extrusion_length
			p_current_pos_->retraction_length_ = p_current_pos_->retraction_length_ - p_current_pos_->e_relative_;
			if (less_than_or_equal(p_current_pos_->retraction_length_, 0))
			{
				// we can use the negative retraction length to calculate our extrusion length!
				p_current_pos_->extrusion_length_ = -1.0 * p_current_pos_->retraction_length_;
				// set the retraction length to 0 since we are extruding
				p_current_pos_->retraction_length_ = 0;
			}
			else
				p_current_pos_->extrusion_length_ = 0;

			// calculate deretraction length
			if (greater_than(p_previous_pos_->retraction_length_, p_current_pos_->retraction_length_))
			{
				p_current_pos_->deretraction_length_ = p_previous_pos_->retraction_length_ - p_current_pos_->retraction_length_;
			}
			else
				p_current_pos_->deretraction_length_ = 0;
			
			// *************Calculate extruder state*************
			// rounding should all be done by now
			p_current_pos_->is_extruding_start_ = greater_than(p_current_pos_->extrusion_length_, 0) && !p_previous_pos_->is_extruding_;
			p_current_pos_->is_extruding_ = greater_than(p_current_pos_->extrusion_length_, 0);
			p_current_pos_->is_primed_ = is_zero(p_current_pos_->extrusion_length_) && is_zero(p_current_pos_->retraction_length_);
			p_current_pos_->is_retracting_start_ = !p_previous_pos_->is_retracting_ && greater_than(p_current_pos_->retraction_length_, 0);
			p_current_pos_->is_retracting_ = greater_than(p_current_pos_->retraction_length_, p_previous_pos_->retraction_length_);
			p_current_pos_->is_partially_retracted_ = greater_than(p_current_pos_->retraction_length_, 0) && less_than(p_current_pos_->retraction_length_, retraction_length_);
			p_current_pos_->is_retracted_ = greater_than_or_equal(p_current_pos_->retraction_length_, retraction_length_);
			p_current_pos_->is_deretracting_start_ = greater_than(p_current_pos_->deretraction_length_, 0) && !p_previous_pos_->is_deretracting_;
			p_current_pos_->is_deretracting_ = greater_than(p_current_pos_->deretraction_length_, p_previous_pos_->deretraction_length_);
			p_current_pos_->is_deretracted_ = greater_than(p_previous_pos_->retraction_length_,0) && is_zero(p_current_pos_->retraction_length_);
			// *************End Calculate extruder state*************
		}
		// calculate last_extrusion_height and height
		// If we are extruding on a higher level, or if retract is enabled and the nozzle is primed
		// adjust the last extrusion height
		if (!is_equal(p_current_pos_->z_, p_current_pos_->last_extrusion_height_))
		{
			if (!p_current_pos_->z_null_)
			{
				if (p_current_pos_->is_extruding_)
				{
					p_current_pos_->last_extrusion_height_ = p_current_pos_->z_;
					p_current_pos_->last_extrusion_height_null_ = false;
					// Is Primed
					if (!p_current_pos_->is_printer_primed_)
					{
						// We haven't primed yet, check to see if we have priming height restrictions
						if (greater_than(priming_height_, 0))
						{
							// if a priming height is configured, see if we've extruded below the  height
							if (less_than(p_current_pos_->last_extrusion_height_, priming_height_))
								p_current_pos_->is_printer_primed_ = true;
						}
						else
							// if we have no priming height set, just set is_printer_primed = true.
							p_current_pos_->is_printer_primed_ = true;
					}

					// Has Reached Minimum layer height
					if (!p_current_pos_->minimum_layer_height_reached_)
					{
						if (greater_than(minimum_layer_height_, 0))
						{
							// if a minimum layer height is configured, see if we've extruded above it
							if (greater_than_or_equal(p_current_pos_->last_extrusion_height_, minimum_layer_height_))
								p_current_pos_->minimum_layer_height_reached_ = true;
						}
						else
							// if we have no minimum layer height set, just set to true
							p_current_pos_->minimum_layer_height_reached_ = true;
					}
				}

				// Calculate layer Change
				if (
					//((p_current_pos_->is_primed_ && p_current_pos_->layer_ > 0) || p_current_pos_->is_extruding_)
					p_current_pos_->is_extruding_ && p_current_pos_->is_printer_primed_)
				{

					if (greater_than(p_current_pos_->z_, p_previous_pos_->height_))
					{
						p_current_pos_->height_ = p_current_pos_->z_;
						// calculate layer change
						if (p_current_pos_->minimum_layer_height_reached_ && greater_than(p_current_pos_->height_ - p_previous_pos_->height_, 0) || p_current_pos_->layer_ == 0)
						{
							p_current_pos_->is_layer_change_ = true;
							p_current_pos_->layer_++;
						}
					}
				}
				// calculate is_zhop
				if (p_current_pos_->is_extruding_ || p_current_pos_->z_null_ || p_current_pos_->last_extrusion_height_null_)
					p_current_pos_->is_zhop_ = false;
				else
					p_current_pos_->is_zhop_ = greater_than_or_equal(p_current_pos_->z_ - p_current_pos_->last_extrusion_height_, z_lift_height_);
			}

		}

		// Calcluate position restructions
		// TODO:  INCLUDE POSITION RESTRICTION CALCULATIONS!
		// tODO:  iNCLUDE FEATURE DETECTION!
	}
	
}

void gcode_position::undo_update()
{
	position* temp = p_current_pos_;
	p_current_pos_ = p_previous_pos_;
	p_previous_pos_ = p_undo_pos_;
	p_undo_pos_ = temp;
}

// Private Members
std::map<std::string, gcode_position::posFunctionType> gcode_position::get_gcode_functions()
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
		pos->is_travel_only_ = !update_e && !update_z && (update_x || update_y);
	}
	if (update_f)
	{
		pos->f_ = f;
		pos->f_null_ = false;
	}

	if (force)
	{
		if (update_x)
		{
			pos->x_ = x + pos->x_offset_;
			pos->x_null_ = false;
		}
		if (update_y)
		{
			pos->y_ = y + pos->y_offset_;
			pos->y_null_ = false;
		}
		if (update_z)
		{
			pos->z_ = z + pos->z_offset_;
			pos->z_null_ = false;
		}
		// note that e cannot be null and starts at 0
		if (update_e)
			pos->e_ = e + pos->e_offset_;
		return;
	}

	if (!pos->is_relative_null_)
	{
		if (pos->is_relative_) {
			if (update_x)
			{
				if(!pos->x_null_)
					pos->x_ = x + pos->x_;
				else
				{
					octolapse_log(GCODE_POSITION, ERROR, "GcodePosition.update_position: Cannot update X because the XYZ axis mode is relative and X is null.");
				}
			}
			if (update_y)
			{
				if(!pos->y_null_)
					pos->y_ = y + pos->y_;
				else
				{
					octolapse_log(GCODE_POSITION, ERROR, "GcodePosition.update_position: Cannot update Y because the XYZ axis mode is relative and Y is null.");
				}
			}
			if (update_z)
			{
				if(!pos->z_null_)
					pos->z_ = z + pos->z_;
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
				pos->x_ = x + pos->x_offset_;
				pos->x_null_ = false;
			}
			if (update_y)
			{
				pos->y_ = y + pos->y_offset_;
				pos->y_null_ = false;
			}
			if (update_z)
			{
				pos->z_ = z + pos->z_offset_;
				pos->z_null_ = false;
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
		if (!pos->is_extruder_relative_null_)
		{
			if (pos->is_extruder_relative_)
			{
				pos->e_ = e + pos->e_;
			}
			else
			{
				pos->e_ = e + pos->e_offset_;
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
	
	for (unsigned int index = 0; index < parsedCommandPtr->parameters_.size(); index++)
	{
		parsed_command_parameter * p_cur_param = parsedCommandPtr->parameters_[index];
		std::string cmdName = p_cur_param->name_;
		if (cmdName == "X")
		{
			update_x = true;
			x = p_cur_param->double_value_;
		}
		else if (cmdName == "Y")
		{
			update_y = true;
			y = p_cur_param->double_value_;
		}
		else if (cmdName == "E")
		{
			update_e = true;
			e = p_cur_param->double_value_;
		}
		else if (cmdName == "Z")
		{
			update_z = true;
			z = p_cur_param->double_value_;
		}
		else if (cmdName == "F")
		{
			update_f = true;
			f = p_cur_param->double_value_;
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

	for (unsigned int index = 0; index < p_parsed_command->parameters_.size(); index++)
	{
		parsed_command_parameter* p_cur_param = p_parsed_command->parameters_[index];
		if (p_cur_param->name_ == "X")
			has_x = true;
		else if (p_cur_param->name_ == "Y")
			has_y = true;
		else if (p_cur_param->name_ == "Z")
			has_z = true;
	}
	if (has_x)
	{
		p_position->x_homed_ = true;
		if (autodetect_position_)
			set_x_origin = true;
	}
	if (has_y)
	{
		p_position->y_homed_ = true;
		if (!autodetect_position_)
			set_y_origin = true;
	}
	if (has_z)
	{
		p_position->z_homed_ = true;
		if (!autodetect_position_)
			set_z_origin = true;
	}
	if (!has_x && !has_y && !has_z)
	{
		p_position->x_homed_ = true;
		p_position->y_homed_ = true;
		p_position->z_homed_ = true;
		if (!autodetect_position_)
		{
			set_x_origin = true;
			set_y_origin = true;
			set_z_origin = true;
		}
	}

	if (set_x_origin && !origin_x_none_)
	{
		p_position->x_ = origin_x_;
		p_position->x_null_ = false;
	}
	// todo: set error flag on else
	if (set_y_origin && !origin_y_none_)
	{
		p_position->y_ = origin_y_;
		p_position->y_null_ = false;
	}
	// todo: set error flag on else
	if (set_z_origin && !origin_z_none_)
	{
		p_position->z_ = origin_z_;
		p_position->z_null_ = false;
	}
	// todo: set error flag on else
}

void gcode_position::process_g90(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set xyz to absolute mode
	if (posPtr->is_relative_null_)
		posPtr->is_relative_null_ = false;

	posPtr->is_relative_ = false;

	if (g90_influences_extruder_)
	{
		// If g90/g91 influences the extruder, set the extruder to absolute mode too
		if (posPtr->is_extruder_relative_null_)
			posPtr->is_extruder_relative_null_ = false;

		posPtr->is_extruder_relative_ = false;
	}

}

void gcode_position::process_g91(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set XYZ axis to relative mode
	if (posPtr->is_relative_null_)
		posPtr->is_relative_null_ = false;

	posPtr->is_relative_ = true;

	if (g90_influences_extruder_)
	{
		// If g90/g91 influences the extruder, set the extruder to relative mode too
		if (posPtr->is_extruder_relative_null_)
			posPtr->is_extruder_relative_null_ = false;

		posPtr->is_extruder_relative_ = true;
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
	for (unsigned int index = 0; index < p_parsed_command->parameters_.size(); index++)
	{
		parsed_command_parameter * p_cur_param = p_parsed_command->parameters_[index];
		std::string cmdName = p_cur_param->name_;
		if (cmdName == "X")
		{
			update_x = true;
			x = p_cur_param->double_value_;
		}
		else if (cmdName == "Y")
		{
			update_y = true;
			y = p_cur_param->double_value_;
		}
		else if (cmdName == "E")
		{
			update_e = true;
			e = p_cur_param->double_value_;
		}
		else if (cmdName == "Z")
		{
			update_z = true;
			z = p_cur_param->double_value_;
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
		p_position->x_homed_ = true;
		p_position->y_homed_ = true;
		p_position->z_homed_ = true;
	}

	if (!o_exists && !update_x && !update_y && !update_z && !update_e)
	{
		if (!p_position->x_null_)
			p_position->x_offset_ = p_position->x_;
		if (!p_position->y_null_)
			p_position->y_offset_ = p_position->y_;
		if (!p_position->z_null_)
			p_position->z_offset_ = p_position->z_;
		// Todo:  Does this reset E too?  Figure that $#$$ out Formerlurker!
		p_position->e_offset_ = p_position->e_;
	}
	else
	{
		if (update_x)
		{
			if (!p_position->x_null_ && p_position->x_homed_)
				p_position->x_offset_ = p_position->x_ - x;
			else
			{
				p_position->x_ = x;
				p_position->x_offset_ = 0;
				p_position->x_null_ = false;
			}
		}
		if (update_y)
		{
			if (!p_position->y_null_ && p_position->y_homed_)
				p_position->y_offset_ = p_position->y_ - y;
			else
			{
				p_position->y_ = y;
				p_position->y_offset_ = 0;
				p_position->y_null_ = false;
			}
		}
		if (update_z)
		{
			if (!p_position->z_null_ && p_position->z_homed_)
				p_position->z_offset_ = p_position->z_ - z;
			else
			{
				p_position->z_ = z;
				p_position->z_offset_ = 0;
				p_position->z_null_ = false;
			}
		}
		if (update_e)
		{
			p_position->e_offset_ = p_position->e_ - e;
		}
	}
}

void gcode_position::process_m82(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set extrder mode to absolute
	if (posPtr->is_extruder_relative_null_)
		posPtr->is_extruder_relative_null_ = false;

	posPtr->is_extruder_relative_ = false;
}

void gcode_position::process_m83(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Set extrder mode to relative
	if (posPtr->is_extruder_relative_null_)
		posPtr->is_extruder_relative_null_ = false;

	posPtr->is_extruder_relative_ = true;
}

void gcode_position::process_m207(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: impemente firmware retract
}

void gcode_position::process_m208(position* posPtr, parsed_command* parsedCommandPtr)
{
	// Todo: implement firmware retract
}
