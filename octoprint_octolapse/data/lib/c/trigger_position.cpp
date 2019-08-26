#include "trigger_position.h"
#include "utilities.h"
#include <iterator>
#include "stabilization_smart_layer.h"

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

trigger_positions::trigger_positions()
{
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		position_list_[index] = NULL;
	}
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;
	p_previous_initial_position_ = NULL;
	p_previous_retracted_position_ = NULL;
	p_previous_primed_position_ = NULL;

	stabilization_x_ = 0;
	stabilization_y_ = 0;
}

trigger_positions::~trigger_positions()
{
	clear();
}

void trigger_positions::initialize(trigger_position_args args)
{
	clear();
	args_ = args;
}

void trigger_positions::set_stabilization_coordinates(double x, double y)
{
	stabilization_x_ = x;
	stabilization_y_ = y;
}


void trigger_positions::set_previous_initial_position(position * pos)
{
	p_previous_initial_position_ = pos;
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

trigger_position * trigger_positions::get_position()
{
	switch (args_.type)
	{
		case trigger_position::trigger_type::snap_to_print:
			return get_snap_to_print_position();
		case trigger_position::trigger_type::fast:
			return get_fast_position();
		case trigger_position::trigger_type::compatibility:
			return get_compatibility_position();
		case trigger_position::trigger_type::high_quality:
			return get_high_quality_position();
		default:
			return NULL;
	}
}

// Returns the fastest extrusion position, or NULL if there is not one (including any speed requirements)
trigger_position* trigger_positions::get_fastest_extrusion_position()
{
	// If there are no fastest speeds return null
	if (slowest_extrusion_speed_ == -1 || fastest_extrusion_speed_ == -1)
	{
		return NULL;
	}

	// the fastest_extrusion_speed_ must be greater than 0, else we haven't found any extrusions!
	if (utilities::greater_than(fastest_extrusion_speed_, 0))
	{
		trigger_position * p_fastest_extrusion = position_list_[trigger_position::fastest_extrusion];
		// if we have a minimum speed or more than one extrusion speed was detected
		if (p_fastest_extrusion == NULL)
			return p_fastest_extrusion;

		if (utilities::greater_than(args_.minimum_speed, 0) && utilities::greater_than_or_equal(p_fastest_extrusion->p_position->f_, args_.minimum_speed))
		{
			return p_fastest_extrusion;
		}
		if (utilities::less_than_or_equal(args_.minimum_speed, 0) && utilities::greater_than(fastest_extrusion_speed_, slowest_extrusion_speed_))
		{
			return p_fastest_extrusion;
		}
	}
	return NULL;
}

// Gets the snap to print position from the position list
trigger_position* trigger_positions::get_snap_to_print_position()
{
	// If we are snapping to the closest and fastest point, return that if it exists.
	trigger_position* p_fastest_extrusion = get_fastest_extrusion_position();
	if (args_.snap_to_fastest && p_fastest_extrusion != NULL)
	{
		return p_fastest_extrusion;
	}

	// get the current best extrusion position
	trigger_position* p_extrusion = position_list_[trigger_position::position_type::extrusion];

	// If p_extrusion is null, return p_fastest_extrusion
	if (p_extrusion == NULL)
		return p_fastest_extrusion;

	// if p_fastest_extrusion is null, return p_extrusion
	if (p_fastest_extrusion == NULL)
		return p_extrusion;

	// if the p_extrusion distance is less than the p_fastest_extrusion distance, return that.
	if (utilities::less_than(p_extrusion->distance, p_fastest_extrusion->distance))
		return p_extrusion;

	// return p_fastest_extrusion, which is equal to or less than the travel distance of p_extrusion
	return p_fastest_extrusion;
}

trigger_position* trigger_positions::get_fast_position()
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
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		trigger_position* current_position = NULL;
		if (index == trigger_position::fastest_extrusion)
			current_position = get_fastest_extrusion_position();
		else
			current_position = position_list_[index];


		if (current_position != NULL)
		{
			return current_position;
		}
	}
	return NULL;
}
/*
trigger_position* trigger_positions::get_normal_quality_position()
{
	trigger_position* current_closest = NULL;
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		if (index < trigger_position::quality_cutoff && current_closest != NULL)
			return current_closest;

		trigger_position* current_position = NULL;
		if (index == trigger_position::fastest_extrusion)
			current_position = get_fastest_extrusion_position();
		else
			current_position = position_list_[index];
		
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
					if (utilities::greater_than(difference_percent, args_.distance_threshold_percent))
					{
						current_closest = current_position;
					}

				}
			}
		}
	}
	return current_closest;
}
*/
trigger_position* trigger_positions::get_high_quality_position()
{
	for (int index = trigger_position::num_position_types - 1; index > trigger_position::quality_cutoff - 1; index--)
	{
		trigger_position* current_position = NULL;
		if (index == trigger_position::fastest_extrusion)
			current_position = get_fastest_extrusion_position();
		else
			current_position = position_list_[index];

		if (current_position != NULL)
		{
			return current_position;
		}
	}
	return NULL;
}

trigger_position** trigger_positions::get_all()
{
	return position_list_;
}

void trigger_positions::save_retracted_position(position* p_retracted_position)
{
	if (!p_retracted_position->is_retracted_)
		return;

	if (p_previous_retracted_position_ != NULL)
		delete p_previous_retracted_position_;

	p_previous_retracted_position_ = new position(*p_retracted_position);
}

void trigger_positions::save_primed_position(position* p_primed_position)
{
	if (!p_primed_position->is_primed_)
		return;

	if (p_previous_primed_position_ != NULL)
		delete p_previous_primed_position_;

	p_previous_primed_position_ = new position(*p_primed_position);
}

void trigger_positions::clear()
{
	// reset all tracking variables
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;
	p_previous_initial_position_ = NULL;

	// delete the previous retracted position
	if (p_previous_retracted_position_ != NULL)
	{
		delete p_previous_retracted_position_;
		p_previous_retracted_position_ = NULL;
	}

	// delete the previous retracted position
	if (p_previous_primed_position_ != NULL)
	{
		delete p_previous_primed_position_;
		p_previous_primed_position_ = NULL;
	}

	// clear out any saved positions
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

trigger_position* trigger_positions::get(trigger_position::position_type type)
{
	return position_list_[type];
}


bool trigger_positions::can_process_position(position* p_position, trigger_position::position_type type)
{
	if (type == trigger_position::unknown)
		return false;

	// check for errors in position, layer, or height
	if (p_position->layer_ == 0 || p_position->x_null_ || p_position->y_null_ || p_position->z_null_)
	{
		return false;
	}
	// See if we should ignore the current position because it is not in bounds, or because it wasn't processed
	if (p_position->gcode_ignored_ || !p_position->is_in_bounds_)
		return false;

	return true;
}


double trigger_positions::get_stabilization_distance(position* p_position)
{
	double x, y;
	if (args_.x_stabilization_disabled)
	{
		if (p_previous_initial_position_ != NULL)
			x = p_previous_initial_position_->x_;
		else
			x = p_position->x_;
	}
	else
	{
		x = stabilization_x_;
	}

	if (args_.y_stabilization_disabled)
	{
		if (p_previous_initial_position_ != NULL)
			y = p_previous_initial_position_->y_;
		else
			y = p_position->y_;
	}
	else
	{
		y = stabilization_y_;
	}
	return utilities::get_cartesian_distance(p_position->x_, p_position->y_, x, y);
}

/// Try to add a position to the position list.  Returns false if no position can be added.
void trigger_positions::try_add(position *p_position, position *p_previous_position)
{
	// Get the position type
	trigger_position::position_type type = trigger_position::get_type(p_position);

	if (!can_process_position(p_position, type))
		return;

	if (args_.type == trigger_position::snap_to_print && type != trigger_position::extrusion)
	{
		save_retracted_position(p_position);
		save_primed_position(p_position);
		return;
	}

	try_add_internal(p_position, get_stabilization_distance(p_position), type);

	// If we are using snap to print, and the current position is = is_extruding_start
	if (args_.type == trigger_position::snap_to_print && p_position->is_extruding_start_)
	{
		// try to add the snap_to_print starting position
		try_add_extrusion_start_positions(p_previous_position);
	}
	

}

// Adds a position to the internal position list.
void trigger_positions::add_internal(position *p_position, double distance, trigger_position::position_type type)
{
	trigger_position* current_position = position_list_[type];
	if (current_position != NULL)
	{
		delete current_position;
	}
	position_list_[type] = new trigger_position(type, distance, p_position);
}

void trigger_positions::try_add_extrusion_start_positions(position* p_extrusion_start_position)
{
	// Try to add the start of the extrusion to the snap to print stabilization
	if (p_previous_retracted_position_ != NULL)
		try_add_extrusion_start_position(p_extrusion_start_position, p_previous_retracted_position_);
	else if (p_previous_primed_position_ != NULL)
		try_add_extrusion_start_position( p_extrusion_start_position, p_previous_primed_position_);

}

void trigger_positions::try_add_extrusion_start_position(position * p_extrusion_start_position, position * p_saved_position)
{
	// A special case where we are trying to add a snap to print position from the start of an extrusion.
	// This is currently implemented only for a retracted position, but in theory we should add a primed position too, and use it as a backup.
	// Note that we do not need to add any checks for max speed or thresholds, since that will have been taken care of
	if (
		p_saved_position->x_ != p_extrusion_start_position->x_ ||
		p_saved_position->y_ != p_extrusion_start_position->y_ ||
		p_saved_position->z_ != p_extrusion_start_position->z_
		)
	{
		return;
	}

	double distance = get_stabilization_distance(p_saved_position);

	// See if we need to update the fastest extrusion position
	if (
		utilities::is_equal(fastest_extrusion_speed_, p_extrusion_start_position->f_)
		&& utilities::less_than(distance, get(trigger_position::position_type::fastest_extrusion)->distance))
	{
		// add the current position as the fastest extrusion speed 
		add_internal(p_saved_position, distance, trigger_position::position_type::fastest_extrusion);
	}

	trigger_position* p_current_closest = get(trigger_position::position_type::extrusion);
	bool add_position = false;
	if (p_current_closest == NULL)
	{
		add_position = true;
	}
	else if (utilities::less_than(distance, p_current_closest->distance))
	{
		add_position = true;
	}
	else if (utilities::is_equal(p_current_closest->distance, distance) && p_previous_initial_position_ != NULL)
	{
		//std::cout << "Closest position tie detected, ";
		const double old_distance_from_previous = utilities::get_cartesian_distance(p_current_closest->p_position->x_, p_current_closest->p_position->y_, p_previous_initial_position_->x_, p_previous_initial_position_->y_);
		const double new_distance_from_previous = utilities::get_cartesian_distance(p_saved_position->x_, p_saved_position->y_, p_previous_initial_position_->x_, p_previous_initial_position_->y_);
		if (utilities::less_than(new_distance_from_previous, old_distance_from_previous))
		{
			//std::cout << "new is closer to the last initial snapshot position.\r\n";
			add_position = true;
		}
		//std::cout << "old position is closer to the last initial snapshot position.\r\n";
	}
	if (add_position)
	{
		// add the current position as the fastest extrusion speed 
		add_internal(p_saved_position, distance, trigger_position::position_type::extrusion);
	}
}

// Try to add a position to the internal position list.
void trigger_positions::try_add_internal(position * p_position, double distance, trigger_position::position_type type)
{

	// If this is an extrusion type position, we need to handle it with care since we want to track both the closest 
	// extrusion and the closest extrusion at the fastest speed (inluding any speed filters that are supplied.
	if (type == trigger_position::extrusion)
	{
		// First make sure to update the fastest and slowest extrusion speeds.
		// important for implementing any 'min_extrusion_speed_difference_' rules.
		if (slowest_extrusion_speed_ == -1 || utilities::less_than(p_position->f_, slowest_extrusion_speed_))
		{
			slowest_extrusion_speed_ = p_position->f_;
		}
		
		// See if the feedrate is faster than our minimum speed.
		if (args_.minimum_speed > -1)
		{
			// see if we should filter out this position due to the feedrate
			if (utilities::less_than_or_equal(p_position->f_, args_.minimum_speed))
				return;
		}

		// Now that we've filtered any feedrates below the minimum speed, let's let's see if we've set a new speed record
		bool add_fastest = false;
		if (utilities::greater_than(p_position->f_, fastest_extrusion_speed_))
		{
			fastest_extrusion_speed_ = p_position->f_;
			add_fastest = true;
		}
		else if (
			utilities::is_equal(fastest_extrusion_speed_, p_position->f_)
			&& utilities::less_than(distance, get(trigger_position::position_type::fastest_extrusion)->distance))
		{
			add_fastest = true;
		}

		if (add_fastest)
		{
			// add the current position as the fastest extrusion speed 
			add_internal(p_position, distance, trigger_position::position_type::fastest_extrusion);
		}

	}
	
	// See if we have a closer position	for any but the 'fastest_extrusion' position (it will have been dealt with by now)
	// First get the current closest position by type
	trigger_position* p_current_closest = get(type);
	
	bool add_position = false;
	if (p_current_closest == NULL)
	{
		add_position = true;
	}
	else if (utilities::less_than(distance, p_current_closest->distance))
	{
		add_position = true;
	}
	else if (utilities::is_equal(p_current_closest->distance, distance) && p_previous_initial_position_ != NULL)
	{
		//std::cout << "Closest position tie detected, ";
		const double old_distance_from_previous = utilities::get_cartesian_distance(p_current_closest->p_position->x_, p_current_closest->p_position->y_, p_previous_initial_position_->x_, p_previous_initial_position_->y_);
		const double new_distance_from_previous = utilities::get_cartesian_distance(p_position->x_, p_position->y_, p_previous_initial_position_->x_, p_previous_initial_position_->y_);
		if (utilities::less_than(new_distance_from_previous, old_distance_from_previous))
		{
			//std::cout << "new is closer to the last initial snapshot position.\r\n";
			add_position = true;
		}
		//std::cout << "old position is closer to the last initial snapshot position.\r\n";
	}
	if(add_position)
	{
		// add the current position as the fastest extrusion speed 
		add_internal(p_position, distance, type);
	}
}