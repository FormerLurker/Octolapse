#include "gcode_wiper_step.h"

PyObject * gcode_wiper_step::to_py_dict()
{
	PyObject * py_step = Py_BuildValue(
		"{s:i,s:d,s:d,s:d,s:d}",
		"step_type",
		step_type,
		"x",
		x,
		"y",
		y,
		"e",
		e,
		"f",
		f
	);
	if (py_step == NULL)
	{
		PyErr_Print();
		PyErr_SetString(PyExc_ValueError, "Error executing gcode_wiper_step.to_py_dict(): Unable to create the step dict.");
		return NULL;
	}
	return py_step;
}

PyObject* gcode_wiper_step::to_py_object(std::vector<gcode_wiper_step*> steps)
{
	PyObject *py_steps = PyList_New(0);
	if (py_steps == NULL)
	{
		PyErr_SetString(PyExc_ValueError, "Error executing gcode_wiper_step.to_py_object(std::vector<gcode_wiper_step*> steps): Unable to create PyList object.");
		return NULL;
	}

	// Create each snapshot plan
	for (unsigned int plan_index = 0; plan_index < steps.size(); plan_index++)
	{
		PyObject * py_step = steps[plan_index]->to_py_dict();
		if (py_step == NULL)
		{
			PyErr_SetString(PyExc_ValueError, "Error executing gcode_wiper_step.to_py_object: Unable to convert the snapshot plan to a PyObject.");
			return NULL;
		}
		bool success = !(PyList_Append(py_steps, py_step) < 0); // reference to pSnapshotPlan stolen
		if (!success)
		{
			PyErr_Print();
			PyErr_SetString(PyExc_ValueError, "Error executing gcode_wiper_step.to_py_object: Unable to append the wipe step to the step list.");
			return NULL;
		}
		Py_DECREF(py_step);
	}
	return py_steps;
}