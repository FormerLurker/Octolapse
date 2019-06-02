#include "trigger_position.h"
#include "utilities.h"
#include <iterator>

position_type trigger_position::get_type(position* p_position)
{
	if (p_position->is_partially_retracted_ || p_position->is_deretracted_)
		return position_type::unknown;
	
	if (p_position->is_extruding_ && utilities::greater_than(p_position->e_relative_, 0))
	{
		return position_type::extrusion;
	}
	else if(p_position->is_xy_travel_)
	{
		if (p_position->is_retracted_)
		{
			if (p_position->is_zhop_)
				return position_type::lifted_retracted_travel;
			else
				return position_type::retracted_travel;
		}
		else 
		{
			if (p_position->is_zhop_)
				return position_type::lifted_travel;
			else
				return position_type::travel;
		}
	}
	else if(utilities::greater_than(p_position->z_relative_, 0))
	{
		if (!p_position->is_xyz_travel_)
		{
			if (p_position->is_zhop_)
				return position_type::lifted;
			else
				return position_type::lifting;
		}
		else if (p_position->is_retracted_)
		{
			if (p_position->is_zhop_)
				return position_type::lifted_retracted_travel;
			else
				return position_type::lifting_retracted_travel;
		}
		else
		{
			if (p_position->is_zhop_)
				return position_type::lifted_travel;
			else
				return position_type::lifting_travel;
		}
	}
	else if(utilities::less_than(p_position->e_relative_ , 0) && p_position->is_retracted_)
	{
		return position_type::retraction;
	}
	else
	{
		return position_type::unknown;
	}
}

trigger_positions::trigger_positions(double distance_threshold)
{
	distance_threshold_ = distance_threshold;
	initialize_position_list();
}

trigger_positions::trigger_positions()
{
	distance_threshold_ = 0;
	initialize_position_list();
}

void trigger_positions::initialize_position_list()
{
	for (int index = num_position_types - 1; index > -1; index--)
	{
		position_list_[index] = NULL;
	}
}

void trigger_positions::set_distance_threshold(double distance_threshold)
{
	distance_threshold_ = distance_threshold;
}

trigger_positions::~trigger_positions()
{
	clear();
}

bool trigger_positions::is_empty()
{
	for (unsigned int index = 0; index < num_position_types; index++)
	{
		if (position_list_[index] != NULL)
			return false;
	}
	return true;
}

trigger_position* trigger_positions::get_closest_position()
{
	trigger_position* current_closest = NULL;
	// Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
	for (int index = num_position_types - 1; index > -1; index--)
	{
		trigger_position* current_position = position_list_[index];

		if (current_position != NULL)
		{
			if (current_closest == NULL || utilities::less_than(current_position->distance, current_closest->distance))
				current_closest = current_position;
		}
	}
	return current_closest;
}

trigger_position* trigger_positions::get_closest_non_extrude_position()
{
	trigger_position* current_closest = NULL;
	double closest_distance;
	// Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
	for (int index = num_position_types - 1; index > extrusion; index--)
	{
		trigger_position* current_position = position_list_[index];

		if (current_position != NULL)
		{
			if (current_closest == NULL || utilities::less_than(current_position->distance, current_closest->distance))
				current_closest = current_position;
		}
	}
	return current_closest;
}

trigger_position* trigger_positions::get_high_quality_position()
{
	trigger_position* current_closest = NULL;
	for (int index = num_position_types - 1; index > extrusion; index--)
	{
		trigger_position* current_position = position_list_[index];
		if (current_position != NULL)
		{
			if (current_closest == NULL)
			{
				current_closest = current_position;
			}
			else
			{
				const double difference = current_closest->distance - current_position->distance;
				// If our current position is closer to the previous distance by at least the set distance threshold, 
				// record the current position as the closest position
				if (utilities::greater_than(difference, distance_threshold_))
				{
					current_closest = current_position;
				}
			}
		}
	}
	return current_closest;
}

trigger_position* trigger_positions::get_best_quality_position()
{
	for (int index = num_position_types - 1; index > extrusion; index--)
	{
		trigger_position* current_position = position_list_[index];
		if (current_position != NULL)
			return current_position;
	}
	return NULL;
}

trigger_position** trigger_positions::get_all()
{
	return position_list_;
}

void trigger_positions::clear()
{
	for (unsigned int index = 0; index < num_position_types; index++)
	{
		trigger_position* current_position = position_list_[index];
		if (current_position != NULL)
		{
			delete current_position;
			position_list_[index] = NULL;
		}
	}
}

void trigger_positions::add(position_type type, double distance, position *p_position)
{
	trigger_position* current_position = position_list_[type];
	if(current_position != NULL)
	{
		delete current_position;
	}
	position_list_[type] = new trigger_position(type, distance, p_position);
}

void trigger_positions::add(double distance, position *p_position)
{
	position_type type = trigger_position::get_type(p_position);
	trigger_position* current_position = position_list_[type];
	if (current_position != NULL)
	{
		delete current_position;
	}
	position_list_[type] = new trigger_position(type, distance, p_position);
}

trigger_position* trigger_positions::get(position_type type)
{
	return position_list_[type];
}

