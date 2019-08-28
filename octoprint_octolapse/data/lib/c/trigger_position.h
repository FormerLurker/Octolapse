#pragma once
#include "position.h"
#include "gcode_comment_processor.h"

/**
 * \brief A struct to hold the closest position, which  is used by the stabilization preprocessors.
 */
static const std::string position_type_name[14] = {
		"unknown", "extrusion", "lifting", "lifted", "travel", "lifting_travel", "lifted_travel", "retraction", "retracted_lifting", "retracted_lifted", "retracted_travel", "lifting_retracted_travel"," lifted_retracted_travel", "fastest_extrusion"
};
struct trigger_position
{
	/**
	 * \brief The type of trigger position to use when creating snapshot plans\n
	 * fastest - Gets the closest position\n
	 * compatibility - Gets the best quality position available.
	 * high_quality - Gets the best quality position availiable, but stops searching after the quality_cutoff (retraction)
	 */
	enum trigger_type { snap_to_print, fast, compatibility, high_quality };
	enum position_type { unknown, extrusion, lifting, lifted, travel, lifting_travel, lifted_travel, retraction, retracted_lifting, retracted_lifted, retracted_travel, lifting_retracted_travel, lifted_retracted_travel, fastest_extrusion };
	
	static const unsigned int num_position_types = 14;
	static const position_type quality_cutoff = trigger_position::retraction;
	
	trigger_position()
	{
		type = trigger_position::unknown;
		distance = -1;
		is_empty = true;
		feature_type = gcode_comment_processor::unknown_feature;
	}
	trigger_position(position_type type_, double distance_, position p_position_)
	{
		type = type_;
		distance = distance_;
		p_position = p_position_;
		is_empty = false;
		feature_type = gcode_comment_processor::unknown_feature;
	}
	trigger_position(gcode_comment_processor::feature_type feature_type_, double distance_, position p_position_)
	{
		type = trigger_position::unknown;
		distance = distance_;
		p_position = p_position_;
		is_empty = false;
		feature_type = feature_type_;
	}
	static position_type get_type(position& p_position);
	position_type type;
	gcode_comment_processor::feature_type feature_type;
	double distance;
	position p_position;
	bool is_empty;
};

struct trigger_position_args
{
public:
	trigger_position_args()
	{
		type = trigger_position::trigger_type::compatibility;
		minimum_speed = 0;
		snap_to_fastest = false;
		x_stabilization_disabled = true;
		y_stabilization_disabled = true;
	}
	trigger_position::trigger_type type;
	double minimum_speed;
	bool snap_to_fastest;
	bool x_stabilization_disabled;
	bool y_stabilization_disabled;
};

class trigger_positions
{
public:
	trigger_positions();
	~trigger_positions();
	bool get_position(trigger_position &pos);

	void initialize(trigger_position_args args);
	void clear();
	void try_add(position &p_position, position &p_previous_position);
	bool is_empty();
	trigger_position get(trigger_position::position_type type);
	void set_stabilization_coordinates(double x, double y);
	void set_previous_initial_position(position &pos);
private:
	bool has_fastest_extrusion_position();
	bool get_snap_to_print_position(trigger_position &pos);
	bool get_fast_position(trigger_position &pos);
	bool get_compatibility_position(trigger_position &pos);
	bool get_high_quality_position(trigger_position &pos);

	double get_stabilization_distance(position& p_position) const;

	//trigger_position* get_normal_quality_position();
	void save_retracted_position(position& p_retracted_position);
	void save_primed_position(position& p_primed_position);
	static bool can_process_position(position& p_position, trigger_position::position_type type);
	void add_internal(position& p_position, double distance, trigger_position::position_type type);
	void try_add_feature_position_internal(position & p_position, double distance);
	void add_feature_position_internal(position &p_position, double distance);
	void try_add_internal(position& p_position, double distance, trigger_position::position_type type);
	void try_add_extrusion_start_positions(position& p_extrusion_start_position);
	void try_add_extrusion_start_position(position& p_extrusion_start_position, position& p_saved_position);
	trigger_position position_list_[trigger_position::num_position_types];
	trigger_position feature_position_list_[NUM_FEATURE_TYPES];
	// arguments
	trigger_position_args args_;
	double stabilization_x_;
	double stabilization_y_;
	// Tracking variables
	double fastest_extrusion_speed_;
	double slowest_extrusion_speed_;
	position p_previous_initial_position_;
	position p_previous_retracted_position_;
	position p_previous_primed_position_;
	
};

