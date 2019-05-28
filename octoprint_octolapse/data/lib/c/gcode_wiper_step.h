#pragma once
#include <vector>

#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
enum gcode_wiper_step_type { retract = 0, wipe = 1, travel = 2 };
struct gcode_wiper_step
{
	
	gcode_wiper_step(double x_coord, double y_coord, double e_coord, double feedrate)
	{
		step_type = static_cast<int>(gcode_wiper_step_type::wipe);
		x = x_coord;
		y = y_coord;
		e = e_coord;
		f = feedrate;
	}
	gcode_wiper_step(double e_coord, double feedrate)
	{
		step_type = static_cast<int>(gcode_wiper_step_type::retract);
		x = 0;
		y = 0;
		e = e_coord;
		f = feedrate;
	}
	gcode_wiper_step(double x_coord, double y_coord, double feedrate)
	{
		step_type = static_cast<int>(gcode_wiper_step_type::travel);
		x = x_coord;
		y = y_coord;
		e = 0;
		f = feedrate;
	}
	int step_type;
	double x;
	double y;
	double e;
	double f;
	PyObject * to_py_dict();
	static PyObject * to_py_object(std::vector<gcode_wiper_step*> steps);
};

