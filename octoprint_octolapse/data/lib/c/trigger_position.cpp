#include "trigger_position.h"
#include "utilities.h"
#include <iterator>

trigger_position::position_type trigger_position::get_type(position* p_position)
{
	if (p_position->is_partially_retracted_ || p_position->is_deretracted_)
		return trigger_position::unknown;
	
	if (p_position->is_extruding_ && utilities::greater_than(p_position->e_relative_, 0))
	{
		return trigger_position::extrusion;
	}
	else if(p_position->is_xy_travel_)
	{
		if (p_position->is_retracted_)
		{
			if (p_position->is_zhop_)
				return trigger_position::lifted_retracted_travel;
			else
				return trigger_position::retracted_travel;
		}
		else 
		{
			if (p_position->is_zhop_)
				return trigger_position::lifted_travel;
			else
				return trigger_position::travel;
		}
	}
	else if(utilities::greater_than(p_position->z_relative_, 0))
	{
		if (p_position->is_retracted_)
		{
			if(p_position->is_xyz_travel_)
			{
				if (p_position->is_zhop_)
					return trigger_position::lifted_retracted_travel;
				else
					return trigger_position::lifting_retracted_travel;
			}
			else
			{
				if (p_position->is_zhop_)
					return trigger_position::retracted_lifted;
				else
					return trigger_position::retracted_lifting;
			}
		}
		else
		{
			if (p_position->is_xyz_travel_)
			{
				if (p_position->is_zhop_)
					return trigger_position::lifted_travel;
				else
					return trigger_position::lifting_travel;
			}
			else
			{
				if (p_position->is_zhop_)
					return trigger_position::lifted;
				else
					return trigger_position::lifting;
			}
		}
		
	}
	else if(utilities::less_than(p_position->e_relative_ , 0) && p_position->is_retracted_)
	{
		return trigger_position::retraction;
	}
	else
	{
		return trigger_position::unknown;
	}
}

trigger_positions::trigger_positions(double distance_threshold_percent)
{
	distance_threshold_percent_ = distance_threshold_percent;
	initialize_position_list();
}

trigger_positions::trigger_positions()
{
	distance_threshold_percent_ = 0;
	initialize_position_list();
}

void trigger_positions::initialize_position_list()
{
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		position_list_[index] = NULL;
	}
}

void trigger_positions::set_distance_threshold_percent(double distance_threshold_percent)
{
	distance_threshold_percent_ = distance_threshold_percent;
}

trigger_positions::~trigger_positions()
{
	clear();
}

bool trigger_positions::is_empty()
{
	for (unsigned int index = 0; index < trigger_position::num_position_types; index++)
	{
		if (position_list_[index] != NULL)
			return false;
	}
	return true;
}

trigger_position* trigger_positions::get_fastest_position()
{
	trigger_position* current_closest = NULL;
	// Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
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

trigger_position* trigger_positions::get_compatibility_position()
{
	trigger_position* current_closest = NULL;
	double closest_distance;
	// Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		if (index < (int)trigger_position::quality_cutoff && current_closest != NULL)
			return current_closest;

		trigger_position* current_position = position_list_[index];
		
		if (current_position != NULL)
		{
			if (current_closest == NULL || utilities::less_than(current_position->distance, current_closest->distance))
				current_closest = current_position;
		}
	}
	return current_closest;
}

trigger_position* trigger_positions::get_normal_quality_position()
{
	trigger_position* current_closest = NULL;
	double closest_distance;
	// Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
	for (int index = trigger_position::num_position_types - 1; index > trigger_position::extrusion; index--)
	{
		if (index < trigger_position::quality_cutoff && current_closest != NULL)
			return current_closest;

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
	for (int index = trigger_position::num_position_types - 1; index > trigger_position::extrusion; index--)
	{
		if (index < trigger_position::quality_cutoff && current_closest != NULL)
			return current_closest;

		trigger_position* current_position = position_list_[index];

		if (current_position != NULL)
		{
			if (current_closest == NULL)
			{
				current_closest = current_position;
			}
			else
			{
				if (!utilities::is_zero(current_position->distance))
				{
					const double difference_percent = 100.0 * (1.0 - (current_position->distance / current_closest->distance));
					// If our current position is closer to the previous distance by at least the set distance threshold, 
					// record the current position as the closest position
					if (utilities::greater_than(difference_percent, distance_threshold_percent_))
					{
						current_closest = current_position;
					}
				}
			}
		}
	}
	return current_closest;
}

trigger_position* trigger_positions::get_best_quality_position()
{
	for (int index = trigger_position::num_position_types - 1; index > trigger_position::quality_cutoff - 1; index--)
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
	for (unsigned int index = 0; index < trigger_position::num_position_types; index++)
	{
		trigger_position* current_position = position_list_[index];
		if (current_position != NULL)
		{
			delete current_position;
			position_list_[index] = NULL;
		}
	}
}

void trigger_positions::add(trigger_position::position_type type, double distance, position *p_position)
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
	trigger_position::position_type type = trigger_position::get_type(p_position);
	trigger_position* current_position = position_list_[type];
	if (current_position != NULL)
	{
		delete current_position;
	}
	position_list_[type] = new trigger_position(type, distance, p_position);
}

trigger_position* trigger_positions::get(trigger_position::position_type type)
{
	return position_list_[type];
}

