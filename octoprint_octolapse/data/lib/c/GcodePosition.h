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
#ifndef GCODE_POSITION_H
#define GCODE_POSITION_H
#include <string>
#include <vector>
#include <map>
#include "GcodeParser.h"
#include "Position.h"

struct gcode_position_args {
	gcode_position_args() {
		autodetect_position = true;
		origin_x = 0;
		origin_y = 0;
		origin_z = 0;
		origin_x_none = false;
		origin_y_none = false;
		origin_z_none = false;
		retraction_length = 0;
		z_lift_height = 0;
		priming_height = 0;
		minimum_layer_height = 0;
		g90_influences_extruder = false;
		xyz_axis_default_mode = "absolute";
		e_axis_default_mode = "absolute";
		units_default = "millimeters";
		std::vector<std::string> location_detection_commands; // Final list of location detection commands
	}
	bool autodetect_position;
	double origin_x;
	double origin_y;
	double origin_z;
	bool origin_x_none;
	bool origin_y_none;
	bool origin_z_none;
	double retraction_length;
	double z_lift_height;
	double priming_height;
	double minimum_layer_height;
	bool g90_influences_extruder;
	std::string key;
	std::string xyz_axis_default_mode;
	std::string e_axis_default_mode;
	std::string units_default;
	std::vector<std::string> location_detection_commands; // Final list of location detection commands
};

class gcode_position
{
public:
	typedef void(gcode_position::*posFunctionType)(position*, parsed_command*);
	gcode_position(gcode_position_args args);
	gcode_position();
	~gcode_position();

	void update(parsed_command* cmd, int file_line_number, int gcode_number);
	void update_position(position*, double x, bool update_x, double y, bool update_y, double z, bool update_z, double e, bool update_e, double f, bool update_f, bool force, bool is_g1);
	void undo_update();
	position* p_previous_pos;
	position* p_current_pos;
	position* p_undo_pos;
	static bool is_equal(double x, double y);
	static bool greater_than(double x, double y);
	static bool greater_than_or_equal(double x, double y);
	static bool less_than(double x, double y);
	static bool less_than_or_equal(double x, double y);
	static bool is_zero(double x);
private:
	gcode_position(const gcode_position & source);
	bool _autodetect_position;
	double _priming_height;
	double _origin_x;
	double _origin_y;
	double _origin_z;
	bool _origin_x_none;
	bool _origin_y_none;
	bool _origin_z_none;
	double _retraction_length;
	double _z_lift_height;
	double _minimum_layer_height;
	bool _g90_influences_extruder;
	std::string _e_axis_default_mode;
	std::string _xyz_axis_default_mode;
	std::string _units_default;
	std::map<std::string, posFunctionType> _gcode_functions;
	std::map<std::string, posFunctionType>::iterator _gcode_functions_iterator;
	// Private Functions
	double RoundDouble(double);
	
	std::map<std::string, posFunctionType> GetGcodeFunctions();
	/// Process Gcode Command Functions
	void process_g0_g1(position*, parsed_command*);
	void process_g2(position*, parsed_command*);
	void process_g3(position*, parsed_command*);
	void process_g10(position*, parsed_command*);
	void process_g11(position*, parsed_command*);
	void process_g20(position*, parsed_command*);
	void process_g21(position*, parsed_command*);
	void process_g28(position*, parsed_command*);
	void process_g90(position*, parsed_command*);
	void process_g91(position*, parsed_command*);
	void process_g92(position*, parsed_command*);
	void process_m82(position*, parsed_command*);
	void process_m83(position*, parsed_command*);
	void process_m207(position*, parsed_command*);
	void process_m208(position*, parsed_command*);

};

#endif
