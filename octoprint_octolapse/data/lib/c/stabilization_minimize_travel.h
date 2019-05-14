#ifndef StabilizationMinimizeTravel_H
#define StabilizationMinimizeTravel_H
#include "stabilization.h"
#include "position.h"
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
	double x_coordinate_;
	double y_coordinate_;
	bool has_py_callbacks_;

};

typedef bool(*pythonGetCoordinatesCallback)(PyObject* py_get_snapshot_position_callback, double x_initial, double y_initial, double* x_result, double* y_result);
static const char* MINIMIZE_TRAVEL_STABILIZATION = "minimize_travel";
class stabilization_minimize_travel :	public stabilization
{
public:
	stabilization_minimize_travel();
	stabilization_minimize_travel(gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, progressCallback progress);
	stabilization_minimize_travel(gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, pythonGetCoordinatesCallback get_coordinates,  pythonProgressCallback progress);
	~stabilization_minimize_travel();
protected:
	stabilization_minimize_travel(const stabilization_minimize_travel &source); // don't copy me
	void process_pos(position* p_current_pos, position* p_previous_pos);
	void on_processing_complete();
	void add_saved_plan();
	// False if return < 0, else true
	pythonGetCoordinatesCallback _get_coordinates_callback;
	void get_next_xy_coordinates();
	double is_closer(position* p_position);
	bool is_layer_change_wait_;
	double x_coord_;
	double y_coord_;
	double current_closest_dist_;
	int current_layer_;
	double current_height_;
	unsigned int current_height_increment_;
	bool has_saved_position_;
	position * p_saved_position_;
	minimize_travel_args *minimize_travel_args_;
};



#endif