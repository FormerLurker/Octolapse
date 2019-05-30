#ifndef StabilizationSmartLayer_H
#define StabilizationSmartLayer_H
#include "stabilization.h"
#include "position.h"
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif

struct smart_layer_args
{
	smart_layer_args()
	{
		trigger_on_extrude = false;
		speed_threshold = 0;
	}
	smart_layer_args(PyObject * gcode_generator, PyObject * get_snapshot_position_callback)
	{
		trigger_on_extrude = false;
		speed_threshold = 0;
	}
	smart_layer_args(double x, double y)
	{
		trigger_on_extrude = false;
		speed_threshold = 0;
	}
	bool trigger_on_extrude;
	double speed_threshold;
};


static const char* SMART_LAYER_STABILIZATION = "smart_layer";
class stabilization_smart_layer : public stabilization
{
public:
	stabilization_smart_layer();
	stabilization_smart_layer(gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, progressCallback progress);
	stabilization_smart_layer(gcode_position_args* position_args, stabilization_args* stab_args, smart_layer_args* mt_args, pythonGetCoordinatesCallback get_coordinates,  pythonProgressCallback progress);
	~stabilization_smart_layer();
private:
	stabilization_smart_layer(const stabilization_smart_layer &source); // don't copy me
	void process_pos(position* p_current_pos, position* p_previous_pos);
	void on_processing_complete();
	void add_plan();
	void reset_saved_positions();
	void save_position(position* p_position, position_type type_, double distance);
	bool has_saved_position();
	/**
	 * \brief Returns the distance to the stabilization point if it is closer than 
	 * previous points, or -1 (less than 0) if it is not.
	 * \param p_position the position to test
	 * \param type_ the type of position we are comparing, either extrusion or retracted travel
	 * \return -1 if the position is not closer, or the current distance.
	 */
	double is_closer(position* p_position, position_type type_);
	
	// Layer/height tracking variables
	bool is_layer_change_wait_;
	int current_layer_;
	int last_tested_gcode_number_;
	bool has_one_extrusion_speed_;
	unsigned int current_height_increment_;
	double stabilization_x_;
	double stabilization_y_;
	smart_layer_args *smart_layer_args_;
	// closest extrusion/travel position tracking variables
	closest_position * p_closest_travel_;
	closest_position * p_closest_extrusion_;
};
#endif