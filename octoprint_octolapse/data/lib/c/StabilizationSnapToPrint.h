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
#include "Stabilization.h"
#include "Position.h"
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
static const char * FRONT_LEFT = "front-left";
static const char * FRONT_RIGHT = "front-right";
static const char * BACK_LEFT = "back-left";
static const char * BACK_RIGHT = "back-right";
static const char * FAVOR_X = "x";
static const char * FAVOR_Y = "y";
static const char* LOCK_TO_PRINT_CORNER_STABILIZATION = "lock-to-print-corner";
class StabilizationSnapToPrint :
	public stabilization
{
public:
	StabilizationSnapToPrint(stabilization_args* args, progressCallback progress, std::string nearest_to_corner, bool favor_x_axis);
	StabilizationSnapToPrint(
		stabilization_args* args, pythonProgressCallback progress, PyObject * python_progress,
		std::string nearest_to_corner, bool favor_x_axis);
	StabilizationSnapToPrint(stabilization_args* args, std::string nearest_to_corner, bool favor_x_axis);
	StabilizationSnapToPrint();
	~StabilizationSnapToPrint();

protected:
	StabilizationSnapToPrint(const StabilizationSnapToPrint &source); // don't copy me
	void initialize(std::string nearest_to_corner, bool favor_x_axis);
	void process_pos(position* p_current_pos, position* p_previous_pos);
	void on_processing_complete();
	void AddSavedPlan();
	bool IsCloser(position* p_position);
	bool is_layer_change_wait;
	std::string nearest_to;
	bool favor_x;
	int current_layer;
	double current_height;
	unsigned int current_height_increment;
	bool has_saved_position;
	position * p_saved_position;
};

#endif
