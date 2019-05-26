#pragma once
#include "position.h"
struct gcode_wiper_position {
	gcode_wiper_position() {
		is_relative = false;
		is_extruder_relative = false;
		x = 0;
		x_offset = 0;
		y = 0;
		y_offset = 0;
		z = 0;
		e = 0;
		e_offset = 0;
		e_relative = 0;
	}
	gcode_wiper_position(position &pos) {
		is_relative = pos.is_relative_;
		is_extruder_relative = pos.is_extruder_relative_;
		x = pos.x_;
		x_offset = pos.x_offset_;
		y = pos.y_;
		y_offset = pos.y_offset_;
		z = pos.z_;
		e = pos.e_;
		e_offset = pos.e_offset_;
		e_relative = pos.e_relative_;
	}
	double get_offset_x()
	{
		return x - x_offset;
	}
	double get_offset_y()
	{
		return y - y_offset;
	}
	double get_offset_e()
	{
		return e - e_offset;
	}

	bool is_relative;
	bool is_extruder_relative;
	double x;
	double x_offset;
	double y;
	double y_offset;
	double z;
	double e;
	double e_offset;
	double e_relative;
};

