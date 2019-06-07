#pragma once
#include "position.h"
#include <map>

/**
 * \brief A struct to hold the closest position, which  is used by the stabilization preprocessors.
 */
static const std::string position_type_name[13] = {
		"unknown", "extrusion", "lifting", "lifted", "travel", "lifting_travel", "lifted_travel", "retraction", "retracted_lifting", "retracted_lifted", "retracted_travel", "lifting_retracted_travel"," lifted_retracted_travel"
};
struct trigger_position
{
	enum position_type { unknown, extrusion, lifting, lifted, travel, lifting_travel, lifted_travel, retraction, retracted_lifting, retracted_lifted, retracted_travel, lifting_retracted_travel, lifted_retracted_travel };
	static const unsigned int num_position_types = 13;
	static const position_type quality_cutoff = trigger_position::retraction;
	
	trigger_position()
	{
		type = trigger_position::unknown;
		distance = -1;
		p_position = NULL;
	}
	trigger_position(position_type type_, double distance_, position* p_position_)
	{
		type = type_;
		distance = distance_;
		p_position = new position(*p_position_);
	}
	~trigger_position()
	{
		if (p_position != NULL)
			delete p_position;
	}
	static position_type get_type(position* p_position);
	position_type type;
	double distance;
	position * p_position;
};

class trigger_positions
{
public:
	trigger_positions();
	trigger_positions(double distance_threshold);
	~trigger_positions();
	trigger_position* get_fastest_position();
	trigger_position* get_compatibility_position();
	trigger_position* get_normal_quality_position();
	trigger_position* get_high_quality_position();
	trigger_position* get_best_quality_position();
	trigger_position** get_all();
	void set_distance_threshold_percent(double distance_threshold_percent);
	void clear();
	void add(trigger_position::position_type type, double distance, position *p_position);
	void add(double distance, position *p_position);
	bool is_empty();
	trigger_position* get(trigger_position::position_type type);
private:
	void initialize_position_list();
	trigger_position* position_list_[trigger_position::num_position_types];
	double distance_threshold_percent_;
};

