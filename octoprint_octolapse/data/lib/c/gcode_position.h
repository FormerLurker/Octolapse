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
#include "gcode_parser.h"
#include "position.h"
#include "gcode_comment_processor.h"
#define NUM_POSITIONS 10
struct gcode_position_args {
	gcode_position_args() {
		// Wipe Variables
		autodetect_position = true;
		is_circular_bed = false;
		home_x = 0;
		home_y = 0;
		home_z = 0;
		home_x_none = false;
		home_y_none = false;
		home_z_none = false;
		retraction_length = 0;
		z_lift_height = 0;
		priming_height = 0;
		minimum_layer_height = 0;
		g90_influences_extruder = false;
		xyz_axis_default_mode = "absolute";
		e_axis_default_mode = "absolute";
		units_default = "millimeters";
		is_bound_ = false;
		x_min = 0;
		x_max = 0;
		y_min = 0;
		y_max = 0;
		z_min = 0;
		z_max = 0;
		snapshot_x_min = 0;
		snapshot_x_max = 0;
		snapshot_y_min = 0;
		snapshot_y_max = 0;
		snapshot_z_min = 0;
		snapshot_z_max = 0;
		std::vector<std::string> location_detection_commands; // Final list of location detection commands
	}
	bool autodetect_position;
	bool is_circular_bed;
	// Wipe variables
	double home_x;
	double home_y;
	double home_z;
	bool home_x_none;
	bool home_y_none;
	bool home_z_none;
	double retraction_length;
	double z_lift_height;
	double priming_height;
	double minimum_layer_height;
	bool g90_influences_extruder;
	bool is_bound_;
	double snapshot_x_min;
	double snapshot_x_max;
	double snapshot_y_min;
	double snapshot_y_max;
	double snapshot_z_min;
	double snapshot_z_max;
	double x_min;
	double x_max;
	double y_min;
	double y_max;
	double z_min;
	double z_max;
	std::string xyz_axis_default_mode;
	std::string e_axis_default_mode;
	std::string units_default;
	std::vector<std::string> location_detection_commands; // Final list of location detection commands
};

class gcode_position
{
public:
	typedef void(gcode_position::*pos_function_type)(position*, parsed_command&);
	gcode_position(gcode_position_args* args);
	gcode_position();

	void update(parsed_command &command, int file_line_number, int gcode_number);
	void update_position(position *position, double x, bool update_x, double y, bool update_y, double z, bool update_z, double e, bool update_e, double f, bool update_f, bool force, bool is_g1_g0);
	void undo_update();
	position get_current_position() const;
	position get_previous_position() const;
	position * get_current_position_ptr();
	position * get_previous_position_ptr();
	gcode_comment_processor* get_gcode_comment_processor();
private:
	gcode_position(const gcode_position &source);
	position positions_[static_cast<int>(NUM_POSITIONS)];
	int cur_pos_;
	void add_position(parsed_command &);
	void add_position(position &);
	bool autodetect_position_;
	double priming_height_;
	double home_x_;
	double home_y_;
	double home_z_;
	bool home_x_none_;
	bool home_y_none_;
	bool home_z_none_;
	double retraction_length_;
	double z_lift_height_;
	double minimum_layer_height_;
	bool g90_influences_extruder_;
	std::string e_axis_default_mode_;
	std::string xyz_axis_default_mode_;
	std::string units_default_;
	bool is_bound_;
	double x_min_;
	double x_max_;
	double y_min_;
	double y_max_;
	double z_min_;
	double z_max_;
	bool is_circular_bed_;
	double snapshot_x_min_;
	double snapshot_x_max_;
	double snapshot_y_min_;
	double snapshot_y_max_;
	double snapshot_z_min_;
	double snapshot_z_max_;

	std::map<std::string, pos_function_type> gcode_functions_;
	std::map<std::string, pos_function_type>::iterator gcode_functions_iterator_;
	
	std::map<std::string, pos_function_type> get_gcode_functions();
	/// Process Gcode Command Functions
	void process_g0_g1(position*, parsed_command&);
	void process_g2(position*, parsed_command&);
	void process_g3(position*, parsed_command&);
	void process_g10(position*, parsed_command&);
	void process_g11(position*, parsed_command&);
	void process_g20(position*, parsed_command&);
	void process_g21(position*, parsed_command&);
	void process_g28(position*, parsed_command&);
	void process_g90(position*, parsed_command&);
	void process_g91(position*, parsed_command&);
	void process_g92(position*, parsed_command&);
	void process_m82(position*, parsed_command&);
	void process_m83(position*, parsed_command&);
	void process_m207(position*, parsed_command&);
	void process_m208(position*, parsed_command&);

	gcode_comment_processor comment_processor_;

};

#endif
