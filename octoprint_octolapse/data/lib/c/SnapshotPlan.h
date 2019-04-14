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
#ifndef SNAPSHOT_PLAN_H
#define SNAPSHOT_PLAN_H
#include "SnapshotPlanStep.h"
#include "ParsedCommand.h"
#include "Position.h"
#include <vector>
class snapshot_plan
{
public:
	snapshot_plan();
	snapshot_plan(const snapshot_plan & source);
	~snapshot_plan();
	PyObject * to_py_object();
	static PyObject * build_py_object(std::vector<snapshot_plan *> plans);
	long file_line;
	long file_gcode_number;
	position * p_initial_position;
	std::vector<position*>  snapshot_positions;
	position * p_return_position;
	std::vector<snapshot_plan_step*> steps;
	parsed_command * p_parsed_command;
	std::string send_parsed_command;
	double lift_amount;
	double retract_amount;
};

#endif
