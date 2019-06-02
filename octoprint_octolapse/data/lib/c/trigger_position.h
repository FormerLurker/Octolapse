#pragma once
#include "position.h"
#include <map>;
enum position_type { unknown, extrusion, retraction, lifting, lifted, travel, lifting_travel, lifted_travel, retracted_travel, lifting_retracted_travel, lifted_retracted_travel};
static const unsigned int num_position_types = 11;
static const std::string position_type_name[11] = {
	"unknown", "extrusion", "retraction", "lifting", "lifted", "travel", "lifting_travel", "lifted_travel", "retracted_travel", "lifting_retracted_travel"," lifted_retracted_travel"
};
/**
 * \brief A struct to hold the closest position, which  is used by the stabilization preprocessors.
 */
struct trigger_position
{
	trigger_position()
	{
		type = position_type::unknown;
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
	trigger_position* get_closest_position();
	trigger_position* get_closest_non_extrude_position();
	trigger_position* get_high_quality_position();
	trigger_position* get_best_quality_position();
	trigger_position** get_all();
	void set_distance_threshold(double distance_threshold);
	void clear();
	void add(position_type type, double distance, position *p_position);
	void add(double distance, position *p_position);
	bool is_empty();
	trigger_position* get(position_type type);
private:
	void initialize_position_list();
	trigger_position* position_list_[num_position_types];
	double distance_threshold_;
};

