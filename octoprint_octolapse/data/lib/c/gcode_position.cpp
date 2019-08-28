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
#include "utilities.h"
#include "logging.h"

gcode_position::gcode_position()
{

	autodetect_position_ = false;
	home_x_ = 0;
	home_y_ = 0;
	home_z_ = 0;
	home_x_none_ = true;
	home_y_none_ = true;
	home_z_none_ = true;

	retraction_length_ = 0;
	z_lift_height_ = 0;
	priming_height_ = 0;
	minimum_layer_height_ = 0;
	g90_influences_extruder_ = false;
	e_axis_default_mode_ = "absolute";
	xyz_axis_default_mode_ = "absolute";
	units_default_ = "millimeters";
	gcode_functions_ = get_gcode_functions();

	is_bound_ = false;
	snapshot_x_min_ = 0;
	snapshot_x_max_ = 0;
	snapshot_y_min_ = 0;
	snapshot_y_max_ = 0;
	snapshot_z_min_ = 0;
	snapshot_z_max_ = 0;

	x_min_ = 0;
	x_max_ = 0;
	y_min_ = 0;
	y_max_ = 0;
	z_min_ = 0;
	z_max_ = 0;
	is_circular_bed_ = false;

	cur_pos_ = 0;
	position initial_pos;
	initial_pos.set_xyz_axis_mode(xyz_axis_default_mode_);
	initial_pos.set_e_axis_mode(e_axis_default_mode_);
	initial_pos.set_units_default(units_default_);
	for(int index = 0; index < NUM_POSITIONS; index ++)
	{
		add_position(initial_pos);
	}
	
	
}

gcode_position::gcode_position(gcode_position_args* args)
{
	autodetect_position_ = args->autodetect_position;
	home_x_ = args->home_x;
	home_y_ = args->home_y;
	home_z_ = args->home_z;
	home_x_none_ = args->home_x_none;
	home_y_none_ = args->home_y_none;
	home_z_none_ = args->home_z_none;

	retraction_length_ = args->retraction_length;
	z_lift_height_ = args->z_lift_height;
	priming_height_ = args->priming_height;
	minimum_layer_height_ = args->minimum_layer_height;
	g90_influences_extruder_ = args->g90_influences_extruder;
	e_axis_default_mode_ = args->e_axis_default_mode;
	xyz_axis_default_mode_ = args->xyz_axis_default_mode;
	units_default_ = args->units_default;
	gcode_functions_ = get_gcode_functions();

	is_bound_ = args->is_bound_;
	snapshot_x_min_ = args->snapshot_x_min;
	snapshot_x_max_ = args->snapshot_x_max;
	snapshot_y_min_ = args->snapshot_y_min;
	snapshot_y_max_ = args->snapshot_y_max;
	snapshot_z_min_ = args->snapshot_z_min;
	snapshot_z_max_ = args->snapshot_z_max;

	x_min_ = args->x_min;
	x_max_ = args->x_max;
	y_min_ = args->y_min;
	y_max_ = args->y_max;
	z_min_ = args->z_min;
	z_max_ = args->z_max;

	is_circular_bed_ = args->is_circular_bed;

	cur_pos_ = -1;
	position initial_pos;
	initial_pos.set_xyz_axis_mode(xyz_axis_default_mode_);
	initial_pos.set_e_axis_mode(e_axis_default_mode_);
	initial_pos.set_units_default(units_default_);
	for (int index = 0; index < NUM_POSITIONS; index++)
	{
		add_position(initial_pos);
	}

}

gcode_position::gcode_position(const gcode_position &source)
{
	// Private copy constructor - you can't copy this class
}


void gcode_position::add_position(position& pos)
{
	cur_pos_ = (++cur_pos_) % NUM_POSITIONS;
	positions_[cur_pos_] = pos;
}

void gcode_position::add_position(parsed_command& cmd)
{
	const int prev_pos = cur_pos_;
	cur_pos_ = (++cur_pos_) % NUM_POSITIONS;
	positions_[cur_pos_] = positions_[prev_pos];
	positions_[cur_pos_].reset_state();
	positions_[cur_pos_].p_command = cmd;
	positions_[cur_pos_].is_empty_ = false;
}

position gcode_position::get_current_position() const
{
	return positions_[cur_pos_];
}

position gcode_position::get_previous_position() const
{
	return  positions_[(cur_pos_ - 1)%NUM_POSITIONS];
}

position * gcode_position::get_current_position_ptr()
{
	return &positions_[cur_pos_];
}

position * gcode_position::get_previous_position_ptr()
{

	return &positions_[(cur_pos_ - 1 + NUM_POSITIONS) % NUM_POSITIONS];
}

void gcode_position::update(parsed_command& command, const int file_line_number, const int gcode_number)
{
	if (command.cmd_.empty())
		return;
	// Move the current position to the previous and the previous to the undo position
	// then copy previous to current

	
	add_position(command);
	position * p_current_pos = get_current_position_ptr();
	position * p_previous_pos = get_previous_position_ptr();
	p_current_pos->file_line_number_ = file_line_number;
	p_current_pos->gcode_number_ = gcode_number;
	// Does our function exist in our functions map?
	gcode_functions_iterator_ = gcode_functions_.find(command.cmd_);

	if (gcode_functions_iterator_ != gcode_functions_.end())
	{
		p_current_pos->gcode_ignored_ = false;
		// Execute the function to process this gcode
		const pos_function_type func = gcode_functions_iterator_->second;
		(this->*func)(p_current_pos, command);
		// calculate z and e relative distances
		p_current_pos->e_relative_ = (p_current_pos->e_ - p_previous_pos->e_);
		p_current_pos->z_relative_ = (p_current_pos->z_ - p_previous_pos->z_);
		// Have the XYZ positions changed after processing a command ?

		p_current_pos->has_xy_position_changed_ = (
			!utilities::is_equal(p_current_pos->x_, p_previous_pos->x_) ||
			!utilities::is_equal(p_current_pos->y_, p_previous_pos->y_)
			);
		p_current_pos->has_position_changed_ = (
			p_current_pos->has_xy_position_changed_ ||
			!utilities::is_equal(p_current_pos->z_, p_previous_pos->z_) ||
			!utilities::is_zero(p_current_pos->e_relative_) ||
			p_current_pos->x_null_ != p_previous_pos->x_null_ ||
			p_current_pos->y_null_ != p_previous_pos->y_null_ ||
			p_current_pos->z_null_ != p_previous_pos->z_null_);

		// see if our position is homed
		if (!p_current_pos->has_definite_position_)
		{
			p_current_pos->has_definite_position_ = (
				//p_current_pos->x_homed_ &&
				//p_current_pos->y_homed_ &&
				//p_current_pos->z_homed_ &&
				p_current_pos->is_metric_ &&
				!p_current_pos->is_metric_null_ &&
				!p_current_pos->x_null_ &&
				!p_current_pos->y_null_ &&
				!p_current_pos->z_null_ &&
				!p_current_pos->is_relative_null_ &&
				!p_current_pos->is_extruder_relative_null_);
		}
	}

	if (p_current_pos->has_position_changed_)
	{
		p_current_pos->extrusion_length_total_ += p_current_pos->e_relative_;

		if (utilities::greater_than(p_current_pos->e_relative_, 0) && p_previous_pos->is_extruding_ && !p_previous_pos->is_extruding_start_)
		{
			// A little shortcut if we know we were extruding (not starting extruding) in the previous command
			// This lets us skip a lot of the calculations for the extruder, including the state calculation
			p_current_pos->extrusion_length_ = p_current_pos->e_relative_;
		}
		else
		{

			// Update retraction_length and extrusion_length
			p_current_pos->retraction_length_ = p_current_pos->retraction_length_ - p_current_pos->e_relative_;
			if (utilities::less_than_or_equal(p_current_pos->retraction_length_, 0))
			{
				// we can use the negative retraction length to calculate our extrusion length!
				p_current_pos->extrusion_length_ = -1.0 * p_current_pos->retraction_length_;
				// set the retraction length to 0 since we are extruding
				p_current_pos->retraction_length_ = 0;
			}
			else
				p_current_pos->extrusion_length_ = 0;

			// calculate deretraction length
			if (utilities::greater_than(p_previous_pos->retraction_length_, p_current_pos->retraction_length_))
			{
				p_current_pos->deretraction_length_ = p_previous_pos->retraction_length_ - p_current_pos->retraction_length_;
			}
			else
				p_current_pos->deretraction_length_ = 0;

			// *************Calculate extruder state*************
			// rounding should all be done by now
			p_current_pos->is_extruding_start_ = utilities::greater_than(p_current_pos->extrusion_length_, 0) && !p_previous_pos->is_extruding_;
			p_current_pos->is_extruding_ = utilities::greater_than(p_current_pos->extrusion_length_, 0);
			p_current_pos->is_primed_ = utilities::is_zero(p_current_pos->extrusion_length_) && utilities::is_zero(p_current_pos->retraction_length_);
			p_current_pos->is_retracting_start_ = !p_previous_pos->is_retracting_ && utilities::greater_than(p_current_pos->retraction_length_, 0);
			p_current_pos->is_retracting_ = utilities::greater_than(p_current_pos->retraction_length_, p_previous_pos->retraction_length_);
			p_current_pos->is_partially_retracted_ = utilities::greater_than(p_current_pos->retraction_length_, 0) && utilities::less_than(p_current_pos->retraction_length_, retraction_length_);
			p_current_pos->is_retracted_ = utilities::greater_than_or_equal(p_current_pos->retraction_length_, retraction_length_);
			p_current_pos->is_deretracting_start_ = utilities::greater_than(p_current_pos->deretraction_length_, 0) && !p_previous_pos->is_deretracting_;
			p_current_pos->is_deretracting_ = utilities::greater_than(p_current_pos->deretraction_length_, p_previous_pos->deretraction_length_);
			p_current_pos->is_deretracted_ = utilities::greater_than(p_previous_pos->retraction_length_, 0) && utilities::is_zero(p_current_pos->retraction_length_);
			// *************End Calculate extruder state*************
		}
		// calculate last_extrusion_height and height
		// If we are extruding on a higher level, or if retract is enabled and the nozzle is primed
		// adjust the last extrusion height
		if (!utilities::is_equal(p_current_pos->z_, p_current_pos->last_extrusion_height_))
		{
			if (!p_current_pos->z_null_)
			{
				if (p_current_pos->is_extruding_ || p_current_pos->is_primed_)
				{
					p_current_pos->last_extrusion_height_ = p_current_pos->z_;
					p_current_pos->last_extrusion_height_null_ = false;
					// Is Primed
					if (!p_current_pos->is_printer_primed_)
					{
						// We haven't primed yet, check to see if we have priming height restrictions
						if (utilities::greater_than(priming_height_, 0))
						{
							// if a priming height is configured, see if we've extruded below the  height
							if (utilities::less_than(p_current_pos->last_extrusion_height_, priming_height_))
								p_current_pos->is_printer_primed_ = true;
						}
						else
							// if we have no priming height set, just set is_printer_primed = true.
							p_current_pos->is_printer_primed_ = true;
					}

					if (p_current_pos->is_printer_primed_)
					{
						// Calculate current height
						if (utilities::greater_than_or_equal(p_current_pos->z_, p_previous_pos->height_ + minimum_layer_height_))
						{
							p_current_pos->height_ = p_current_pos->z_;
							p_current_pos->is_layer_change_ = true;
							p_current_pos->layer_++;
						}
					}
				}

				// calculate is_zhop
				if (p_current_pos->is_extruding_ || p_current_pos->z_null_ || p_current_pos->last_extrusion_height_null_)
					p_current_pos->is_zhop_ = false;
				else
					p_current_pos->is_zhop_ = utilities::greater_than_or_equal(p_current_pos->z_ - p_current_pos->last_extrusion_height_, z_lift_height_);
			}

		}

		// Calcluate position restructions
		// TODO:  INCLUDE POSITION RESTRICTION CALCULATIONS!
		// Set is_in_bounds_ to false if we're not in bounds, it will be true at this point
		if (is_bound_)
		{
			bool is_in_bounds = true;
			if (!is_circular_bed_)
			{
				is_in_bounds = !(
					p_current_pos->x_ < snapshot_x_min_ ||
					p_current_pos->x_ > snapshot_x_max_ ||
					p_current_pos->y_ < snapshot_y_min_ ||
					p_current_pos->y_ > snapshot_y_max_ ||
					p_current_pos->z_ < snapshot_z_min_ ||
					p_current_pos->z_ > snapshot_z_max_
					);

			}
			else
			{
				double r;
				r = snapshot_x_max_; // good stand in for radius
				const double dist = sqrt(p_current_pos->x_*p_current_pos->x_ + p_current_pos->y_*p_current_pos->y_);
				is_in_bounds = utilities::less_than_or_equal(dist, r);

			}
			p_current_pos->is_in_bounds_ = is_in_bounds;
		}

	}
}

void gcode_position::undo_update()
{
	cur_pos_ = (cur_pos_ - 1) % NUM_POSITIONS;
}

// Private Members
std::map<std::string, gcode_position::pos_function_type> gcode_position::get_gcode_functions()
{
	std::map<std::string, pos_function_type> newMap;
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

void gcode_position::update_position(position* pos, double x, bool update_x, double y, bool update_y, double z, bool update_z, double e, bool update_e, double f, bool update_f, bool force, bool is_g1_g0)
{
	if (is_g1_g0)
	{
		if (!update_e)
		{
			if (update_z)
			{
				pos->is_xyz_travel_ = (update_x || update_y);
			}
			else
			{
				pos->is_xy_travel_ = (update_x || update_y);
			}
		}

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
				if (!pos->x_null_)
					pos->x_ = x + pos->x_;
				else
				{
					octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, "GcodePosition.update_position: Cannot update X because the XYZ axis mode is relative and X is null.");
				}
			}
			if (update_y)
			{
				if (!pos->y_null_)
					pos->y_ = y + pos->y_;
				else
				{
					octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, "GcodePosition.update_position: Cannot update Y because the XYZ axis mode is relative and Y is null.");
				}
			}
			if (update_z)
			{
				if (!pos->z_null_)
					pos->z_ = z + pos->z_;
				else
				{
					octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, "GcodePosition.update_position: Cannot update Z because the XYZ axis mode is relative and Z is null.");
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
		octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, message);
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
			octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, message);
		}
	}

}

void gcode_position::process_g0_g1(position* pos, parsed_command& cmd)
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
	for (unsigned int index = 0; index < cmd.parameters_.size(); index++)
	{
		const parsed_command_parameter p_cur_param = cmd.parameters_[index];
		if (p_cur_param.name_ == 'X')
		{
			update_x = true;
			x = p_cur_param.double_value_;
		}
		else if (p_cur_param.name_ == 'Y')
		{
			update_y = true;
			y = p_cur_param.double_value_;
		}
		else if (p_cur_param.name_ == 'E')
		{
			update_e = true;
			e = p_cur_param.double_value_;
		}
		else if (p_cur_param.name_ == 'Z')
		{
			update_z = true;
			z = p_cur_param.double_value_;
		}
		else if (p_cur_param.name_ == 'F')
		{
			update_f = true;
			f = p_cur_param.double_value_;
		}
	}
	update_position(pos, x, update_x, y, update_y, z, update_z, e, update_e, f, update_f, false, true);
}

void gcode_position::process_g2(position* pos, parsed_command& cmd)
{
	// ToDo:  Fix G2
}

void gcode_position::process_g3(position* pos, parsed_command& cmd)
{
	// Todo: Fix G3
}

void gcode_position::process_g10(position* pos, parsed_command& cmd)
{
	// Todo: Fix G10
}

void gcode_position::process_g11(position* pos, parsed_command& cmd)
{
	// Todo: Fix G11
}

void gcode_position::process_g20(position* pos, parsed_command& cmd)
{

}

void gcode_position::process_g21(position* pos, parsed_command& cmd)
{

}

void gcode_position::process_g28(position* pos, parsed_command& cmd)
{
	bool has_x = false;
	bool has_y = false;
	bool has_z = false;
	bool set_x_home = false;
	bool set_y_home = false;
	bool set_z_home = false;

	for (unsigned int index = 0; index < cmd.parameters_.size(); index++)
	{
		parsed_command_parameter p_cur_param = cmd.parameters_[index];
		if (p_cur_param.name_ == 'X')
			has_x = true;
		else if (p_cur_param.name_ == 'Y')
			has_y = true;
		else if (p_cur_param.name_ == 'Z')
			has_z = true;
	}
	if (has_x)
	{
		pos->x_homed_ = true;
		set_x_home = true;
	}
	if (has_y)
	{
		pos->y_homed_ = true;
		set_y_home = true;
	}
	if (has_z)
	{
		pos->z_homed_ = true;
		set_z_home = true;
	}
	if (!has_x && !has_y && !has_z)
	{
		pos->x_homed_ = true;
		pos->y_homed_ = true;
		pos->z_homed_ = true;
		set_x_home = true;
		set_y_home = true;
		set_z_home = true;
	}

	if (set_x_home && !home_x_none_)
	{
		pos->x_ = home_x_;
		pos->x_null_ = false;
	}
	// todo: set error flag on else
	if (set_y_home && !home_y_none_)
	{
		pos->y_ = home_y_;
		pos->y_null_ = false;
	}
	// todo: set error flag on else
	if (set_z_home && !home_z_none_)
	{
		pos->z_ = home_z_;
		pos->z_null_ = false;
	}
	// todo: set error flag on else
}

void gcode_position::process_g90(position* pos, parsed_command& cmd)
{
	// Set xyz to absolute mode
	if (pos->is_relative_null_)
		pos->is_relative_null_ = false;

	pos->is_relative_ = false;

	if (g90_influences_extruder_)
	{
		// If g90/g91 influences the extruder, set the extruder to absolute mode too
		if (pos->is_extruder_relative_null_)
			pos->is_extruder_relative_null_ = false;

		pos->is_extruder_relative_ = false;
	}

}

void gcode_position::process_g91(position* pos, parsed_command& cmd)
{
	// Set XYZ axis to relative mode
	if (pos->is_relative_null_)
		pos->is_relative_null_ = false;

	pos->is_relative_ = true;

	if (g90_influences_extruder_)
	{
		// If g90/g91 influences the extruder, set the extruder to relative mode too
		if (pos->is_extruder_relative_null_)
			pos->is_extruder_relative_null_ = false;

		pos->is_extruder_relative_ = true;
	}
}

void gcode_position::process_g92(position* pos, parsed_command& cmd)
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
	for (unsigned int index = 0; index < cmd.parameters_.size(); index++)
	{
		parsed_command_parameter p_cur_param = cmd.parameters_[index];
		char cmdName = p_cur_param.name_;
		if (cmdName == 'X')
		{
			update_x = true;
			x = p_cur_param.double_value_;
		}
		else if (cmdName == 'Y')
		{
			update_y = true;
			y = p_cur_param.double_value_;
		}
		else if (cmdName == 'E')
		{
			update_e = true;
			e = p_cur_param.double_value_;
		}
		else if (cmdName == 'Z')
		{
			update_z = true;
			z = p_cur_param.double_value_;
		}
		else if (cmdName == 'O')
		{
			o_exists = true;
		}
	}

	if (o_exists)
	{
		// Our fake O parameter exists, set axis to homed!
		// This is a workaround to allow folks to use octolapse without homing (for shame, lol!)
		pos->x_homed_ = true;
		pos->y_homed_ = true;
		pos->z_homed_ = true;
	}

	if (!o_exists && !update_x && !update_y && !update_z && !update_e)
	{
		if (!pos->x_null_)
			pos->x_offset_ = pos->x_;
		if (!pos->y_null_)
			pos->y_offset_ = pos->y_;
		if (!pos->z_null_)
			pos->z_offset_ = pos->z_;
		// Todo:  Does this reset E too?  Figure that $#$$ out Formerlurker!
		pos->e_offset_ = pos->e_;
	}
	else
	{
		if (update_x)
		{
			if (!pos->x_null_ && pos->x_homed_)
				pos->x_offset_ = pos->x_ - x;
			else
			{
				pos->x_ = x;
				pos->x_offset_ = 0;
				pos->x_null_ = false;
			}
		}
		if (update_y)
		{
			if (!pos->y_null_ && pos->y_homed_)
				pos->y_offset_ = pos->y_ - y;
			else
			{
				pos->y_ = y;
				pos->y_offset_ = 0;
				pos->y_null_ = false;
			}
		}
		if (update_z)
		{
			if (!pos->z_null_ && pos->z_homed_)
				pos->z_offset_ = pos->z_ - z;
			else
			{
				pos->z_ = z;
				pos->z_offset_ = 0;
				pos->z_null_ = false;
			}
		}
		if (update_e)
		{
			pos->e_offset_ = pos->e_ - e;
		}
	}
}

void gcode_position::process_m82(position* pos, parsed_command& cmd)
{
	// Set extrder mode to absolute
	if (pos->is_extruder_relative_null_)
		pos->is_extruder_relative_null_ = false;

	pos->is_extruder_relative_ = false;
}

void gcode_position::process_m83(position* pos, parsed_command& cmd)
{
	// Set extrder mode to relative
	if (pos->is_extruder_relative_null_)
		pos->is_extruder_relative_null_ = false;

	pos->is_extruder_relative_ = true;
}

void gcode_position::process_m207(position* pos, parsed_command& cmd)
{
	// Todo: impemente firmware retract
}

void gcode_position::process_m208(position* pos, parsed_command& cmd)
{
	// Todo: implement firmware retract
}
