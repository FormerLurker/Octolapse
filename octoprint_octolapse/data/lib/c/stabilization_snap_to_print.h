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

#ifndef StabilizationSnapToPrint_H
#define StabilizationSnapToPrint_H
#include "stabilization.h"
#include "position.h"
#include "trigger_position.h"
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#endif
class stabilization_snap_to_print :
	public stabilization
{
public:
	stabilization_snap_to_print(
		gcode_position_args* position_args, stabilization_args* stab_args, progressCallback progress
	);
	stabilization_snap_to_print(
		gcode_position_args* position_args, stabilization_args* stab_args,
		pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
	);

	stabilization_snap_to_print();
	~stabilization_snap_to_print();

private:
	stabilization_snap_to_print(const stabilization_snap_to_print &source); // don't copy me
	void process_pos(position& p_current_pos, position& p_previous_pos) override;
	void on_processing_complete() override;
	void add_saved_plan();
	bool has_saved_position();
	void reset_saved_positions();
	void delete_saved_positions();
	void save_position(position* p_position, trigger_position::position_type type_, double distance);
	bool is_closer(position * p_position, trigger_position::position_type type, double &distance);
	double stabilization_x_;
	double stabilization_y_;
	bool is_layer_change_wait_;
	int current_layer_;
	unsigned int current_height_increment_;
	trigger_position* p_closest_position_;
};


#endif
