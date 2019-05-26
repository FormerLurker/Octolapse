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
	gcode_wiper_step(double x, double y, double e, double f)
	{
		is_wipe_step = true;
		offset_x = x;
		offset_y = y;
		offset_e = e;
		feedrate = f;
	}
	gcode_wiper_step(double e, double f)
	{
		is_wipe_step = false;
		offset_x = 0;
		offset_y = 0;
		offset_e = e;
		feedrate = f;
	}
	bool is_wipe_step;
	double offset_x;
	double offset_y;
	double offset_e;
	double feedrate;
	PyObject * to_py_dict();
	static PyObject * to_py_object(std::vector<gcode_wiper_step*> steps);
};

