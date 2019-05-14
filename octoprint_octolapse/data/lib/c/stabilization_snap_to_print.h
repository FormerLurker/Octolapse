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
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
class snap_to_print_args
{
public:
	snap_to_print_args();
	snap_to_print_args(std::string nearest_to_corner, bool favor_x_axis);
	~snap_to_print_args();
	std::string nearest_to_corner;
	bool favor_x_axis;
};

static const char * FRONT_LEFT = "front-left";
static const char * FRONT_RIGHT = "front-right";
static const char * BACK_LEFT = "back-left";
static const char * BACK_RIGHT = "back-right";
static const char * FAVOR_X = "x";
static const char * FAVOR_Y = "y";
static const char* LOCK_TO_PRINT_CORNER_STABILIZATION = "lock-to-print-corner";
class stabilization_snap_to_print :
	public stabilization
{
public:
	stabilization_snap_to_print(
		gcode_position_args* position_args, stabilization_args* stab_args, snap_to_print_args* snap_args, 
		progressCallback progress
	);
	stabilization_snap_to_print(
		gcode_position_args* position_args, stabilization_args* stab_args, snap_to_print_args* snap_args, 
		pythonProgressCallback progress
	);

	stabilization_snap_to_print();
	~stabilization_snap_to_print();

protected:
	stabilization_snap_to_print(const stabilization_snap_to_print &source); // don't copy me
	void process_pos(position* p_current_pos, position* p_previous_pos);
	void on_processing_complete();
	void add_saved_plan();
	bool is_closer(position* p_position);
	bool is_layer_change_wait_;
	snap_to_print_args* snap_to_print_args_;
	int current_layer_;
	double current_height_;
	unsigned int current_height_increment_;
	bool has_saved_position_;
	position * p_saved_position_;
};


#endif
