#ifndef StabilizationMinimizeTravel_H
#define StabilizationMinimizeTravel_H
#include "Stabilization.h"
#include "Position.h"
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif
class minimize_travel_args
{
public:
	minimize_travel_args();
	minimize_travel_args(PyObject * gcode_generator, PyObject * get_snapshot_position_callback);
	minimize_travel_args(double x, double y);
	~minimize_travel_args();
	PyObject * py_get_snapshot_position_callback;
	PyObject * py_gcode_generator;
	void get_next_xy_coordinates();
	double x_coordinate;
	double y_coordinate;
	bool has_py_callbacks;

};

typedef bool(*pythonGetCoordinatesCallback)(PyObject* py_get_snapshot_position_callback, double x_initial, double y_initial, double* x_result, double* y_result);
static const char* MINIMIZE_TRAVEL_STABILIZATION = "minimize_travel";
class StabilizationMinimizeTravel :	public stabilization
{
public:
	StabilizationMinimizeTravel();
	StabilizationMinimizeTravel(gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, progressCallback progress);
	StabilizationMinimizeTravel(gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, pythonGetCoordinatesCallback get_coordinates,  pythonProgressCallback progress);
	~StabilizationMinimizeTravel();
protected:
	StabilizationMinimizeTravel(const StabilizationMinimizeTravel &source); // don't copy me
	void process_pos(position* p_current_pos, position* p_previous_pos);
	void on_processing_complete();
	void AddSavedPlan();
	// False if return < 0, else true
	pythonGetCoordinatesCallback _get_coordinates_callback;
	void get_next_xy_coordinates();
	double IsCloser(position* p_position);
	bool is_layer_change_wait;
	double x_coord;
	double y_coord;
	double current_closest_dist;
	int current_layer;
	double current_height;
	unsigned int current_height_increment;
	bool has_saved_position;
	position * p_saved_position;
	minimize_travel_args *_minimize_travel_args;
};



#endif