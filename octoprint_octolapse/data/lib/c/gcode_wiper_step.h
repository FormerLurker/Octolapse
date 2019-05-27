#pragma once
#include <vector>

#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif

struct gcode_wiper_step
{
	gcode_wiper_step(double x_coord, double y_coord, double e_coord, double feedrate)
	{
		is_wipe_step = true;
		x = x_coord;
		y = y_coord;
		e = e_coord;
		f = feedrate;
	}
	gcode_wiper_step(double e_coord, double feedrate)
	{
		is_wipe_step = false;
		x = 0;
		y = 0;
		e = e_coord;
		f = feedrate;
	}
	bool is_wipe_step;
	double x;
	double y;
	double e;
	double f;
	PyObject * to_py_dict();
	static PyObject * to_py_object(std::vector<gcode_wiper_step*> steps);
};

