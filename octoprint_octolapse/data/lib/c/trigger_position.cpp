#include "trigger_position.h"
#include "utilities.h"
#include <iterator>
#include "stabilization_smart_layer.h"

position_type trigger_position::get_type(position& pos_)
{
	if ( pos_.is_partially_retracted ||  pos_.is_deretracted)
		return position_type_unknown;
	
	if ( pos_.is_extruding && utilities::greater_than( pos_.e_relative, 0))
	{
		return position_type_extrusion;
	}
	else if( pos_.is_xy_travel)
	{
		if ( pos_.is_retracted)
		{
			if ( pos_.is_zhop)
				return position_type_lifted_retracted_travel;
			else
				return position_type_retracted_travel;
		}
		else 
		{
			if ( pos_.is_zhop)
				return position_type_lifted_travel;
			else
				return position_type_travel;
		}
	}
	else if(utilities::greater_than( pos_.z_relative, 0))
	{
		if ( pos_.is_retracted)
		{
			if( pos_.is_xyz_travel)
			{
				if ( pos_.is_zhop)
					return position_type_lifted_retracted_travel;
				else
					return position_type_lifting_retracted_travel;
			}
			else
			{
				if ( pos_.is_zhop)
					return position_type_retracted_lifted;
				else
					return position_type_retracted_lifting;
			}
		}
		else
		{
			if ( pos_.is_xyz_travel)
			{
				if ( pos_.is_zhop)
					return position_type_lifted_travel;
				else
					return position_type_lifting_travel;
			}
			else
			{
				if ( pos_.is_zhop)
					return position_type_lifted;
				else
					return position_type_lifting;
			}
		}
		
	}
	else if(utilities::less_than( pos_.e_relative , 0) &&  pos_.is_retracted)
	{
		return position_type_retraction;
	}
	else
	{
		return position_type_unknown;
	}
}

trigger_positions::trigger_positions()
{
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;
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


void trigger_positions::set_previous_initial_position(position &pos)
{
	previous_initial_pos_ = pos;
	previous_initial_pos_.is_empty = false;
}

bool trigger_positions::is_empty() const
{
	for (unsigned int index = 0; index < trigger_position::num_position_types; index++)
	{
		if (!position_list_[index].is_empty)
			return false;
	}
	return true;
}

bool trigger_positions::get_position(trigger_position &pos)
{
	switch (args_.type)
	{
		case trigger_type_snap_to_print:
			return get_snap_to_print_position(pos);
		case trigger_type_fast:
			return get_fast_position(pos);
		case trigger_type_compatibility:
			return get_compatibility_position(pos);
		case trigger_type_high_quality:
			return get_high_quality_position(pos);
	}
	return false;

}

// Returns the fastest extrusion position, or NULL if there is not one (including any speed requirements)
bool trigger_positions::has_fastest_extrusion_position() const
{
	// If there are no fastest speeds return null
	if (slowest_extrusion_speed_ == -1 || fastest_extrusion_speed_ == -1)
	{
		return false;
	}

	// the fastest_extrusion_speed_ must be greater than 0, else we haven't found any extrusions!
	if (utilities::greater_than(fastest_extrusion_speed_, 0))
	{
		// if we have a minimum speed or more than one extrusion speed was detected
		if (position_list_[position_type_fastest_extrusion].is_empty)
			return false;

		if (utilities::greater_than(args_.minimum_speed, 0) && utilities::greater_than_or_equal(position_list_[position_type_fastest_extrusion].pos.f, args_.minimum_speed))
		{
			return true;
		}
		if (utilities::less_than_or_equal(args_.minimum_speed, 0) && utilities::greater_than(fastest_extrusion_speed_, slowest_extrusion_speed_))
		{
			return true;
		}
	}
	return false;
}

// Gets the snap to print position from the position list
bool trigger_positions::get_snap_to_print_position(trigger_position &pos)
{
	pos.is_empty = true;
	const bool has_fastest_position = has_fastest_extrusion_position();
	// If we are snapping to the closest and fastest point, return that if it exists.
	if (args_.snap_to_print_high_quality)
	{
		int current_closest_index = -1;
		// First try to get the closest known high quality feature position if one exists
		for (int index = NUM_FEATURE_TYPES - 1; index > feature_type::feature_type_inner_perimeter_feature - 1; index--)
		{
			if (!feature_position_list_[index].is_empty)
			{
				if (current_closest_index < 0 || utilities::less_than(feature_position_list_[index].distance, feature_position_list_[current_closest_index].distance))
					current_closest_index = index;
			}
		}
		if (current_closest_index > -1)
		{
			pos = feature_position_list_[current_closest_index];
			return true;
		}

		if (has_fastest_position)
		{
			pos = position_list_[position_type_fastest_extrusion];
		}
		else
		{
			pos = position_list_[position_type_extrusion];
		}
		return !pos.is_empty;
	}
	
	// If extrusion position is empty return the fastest position if it exists
	if (position_list_[position_type_extrusion].is_empty && !has_fastest_position)
	{
		return false;
	}

	if (position_list_[position_type_extrusion].is_empty)
	{
		pos = position_list_[position_type_fastest_extrusion];
		return true;
	}

	// We have both!
		
	// if the p_extrusion distance is less than the p_fastest_extrusion distance, return that.
	if (utilities::less_than(position_list_[position_type_extrusion].distance, position_list_[position_type_fastest_extrusion].distance))
	{
		pos = position_list_[position_type_extrusion];
	}
	else
		pos = position_list_[position_type_fastest_extrusion];

	// return p_fastest_extrusion, which is equal to or less than the travel distance of p_extrusion
	return true;
}

bool trigger_positions::get_fast_position(trigger_position &pos)
{
	pos.is_empty = true;
	int current_closest_index = -1;
	// Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		if (!position_list_[index].is_empty)
		{
			if (current_closest_index < 0 || utilities::less_than(position_list_[index].distance, position_list_[current_closest_index].distance))
				current_closest_index = index;
		}
	}
	if (current_closest_index > -1)
	{
		pos = position_list_[current_closest_index];
		return true;
	}
}

bool trigger_positions::get_compatibility_position(trigger_position &pos)
{
	for (int index = NUM_FEATURE_TYPES - 1; index > feature_type::feature_type_inner_perimeter_feature - 1; index--)
	{
		if (!feature_position_list_[index].is_empty)
		{
			pos = feature_position_list_[index];
			return true;
		}
	}
	int current_best_index = -1;
	for (int index = trigger_position::num_position_types - 1; index > -1; index--)
	{
		if (index == position_type_fastest_extrusion && has_fastest_extrusion_position())
		{
			pos = position_list_[index];
			return true;
		}
		else if (!position_list_[index].is_empty)
		{
			pos = position_list_[index];
			return true;
		}
	}
	return false;
}

bool trigger_positions::get_high_quality_position(trigger_position &pos)
{
	for (int index = NUM_FEATURE_TYPES - 1; index >  feature_type::feature_type_inner_perimeter_feature - 1; index--)
	{
		if (!feature_position_list_[index].is_empty)
		{
			pos = feature_position_list_[index];
			return true;
		}
	}
	for (int index = trigger_position::num_position_types - 1; index > trigger_position::quality_cutoff - 1; index--)
	{
		if (index == position_type_fastest_extrusion)
		{
			if (has_fastest_extrusion_position())
			{
				pos = position_list_[index];
				return true;
			}
			continue;
		}
		else if (!position_list_[index].is_empty)
		{
			pos = position_list_[index];
			return true;
		}
	}
	return false;
}

void trigger_positions::save_retracted_position(position& retracted_pos)
{
	if (!retracted_pos.is_retracted)
		return;

	previous_retracted_pos_ = retracted_pos;
}

void trigger_positions::save_primed_position(position& primed_pos)
{
	if (!primed_pos.is_primed)
		return;
	p_previous_primed_pos_ = primed_pos;
}

void trigger_positions::clear()
{
	// reset all tracking variables
	fastest_extrusion_speed_ = -1;
	slowest_extrusion_speed_ = -1;
	previous_initial_pos_.is_empty = true;
	previous_retracted_pos_.is_empty = true;
	p_previous_primed_pos_.is_empty = true;

	// clear out any saved positions
	for (unsigned int index = 0; index < trigger_position::num_position_types; index++)
	{
		position_list_[index].is_empty = true;
	}

	// clear out any saved feature positions
	for (unsigned int index = 0; index < NUM_FEATURE_TYPES; index++)
	{
		feature_position_list_[index].is_empty = true;
	}
}

trigger_position trigger_positions::get(const position_type type)
{
	return position_list_[type];
}


bool trigger_positions::can_process_position(position& pos, const position_type type)
{
	if (type == position_type_unknown || pos.is_empty)
		return false;


	// check for errors in position, layer, or height
	if (pos.layer == 0 || pos.x_null || pos.y_null || pos.z_null)
	{
		return false;
	}
	// See if we should ignore the current position because it is not in bounds, or because it wasn't processed
	if (pos.gcode_ignored || !pos.is_in_bounds)
		return false;
	
	// Never save any positions that are below the highest extrusion point.
	if (utilities::less_than(pos.z, pos.last_extrusion_height))
	{
		// if the current z height is less than the maximum extrusion height!
		// Do not add this point else we might ram into the printed part!
		// Note:  This is even a problem for snap to print, since the extruder will appear to drop, which makes for a bad timelapse
		return false;
	}
	return true;
}


double trigger_positions::get_stabilization_distance(position& pos) const
{
	double x, y;
	if (args_.x_stabilization_disabled && previous_initial_pos_.is_empty)
	{
		x = pos.x;
	}
	else
	{
		x = stabilization_x_;
	}
	if (args_.y_stabilization_disabled && previous_initial_pos_.is_empty)
	{
		y = pos.y;
	}
	else
	{
		y = stabilization_y_;
	}

	return utilities::get_cartesian_distance(pos.x, pos.y, x, y);
}

/// Try to add a position to the position list.  Returns false if no position can be added.
void trigger_positions::try_add(position &current_pos, position &previous_pos)
{
	
	// Get the position type
	const position_type type = trigger_position::get_type(current_pos);

	if (!can_process_position(current_pos, type))
	{
		return;
	}

	// add any feature positions if a feature tag exists, and if we are in high quality or compatibility mode
	if (
		current_pos.feature_type_tag != feature_type::feature_type_unknown_feature &&
		(
			args_.type == trigger_type_high_quality || 
			args_.type == trigger_type_compatibility ||
			(args_.type == trigger_type_snap_to_print && type == position_type_extrusion && args_.snap_to_print_high_quality)
		)
	)
	{
		try_add_feature_position_internal(current_pos, get_stabilization_distance(current_pos));
	}

	
	if (args_.type == trigger_type_snap_to_print)
	{
		// Do special things for snap to print trigger

		if (type != position_type_extrusion)
		{
			// If this isn't an extrusion, we might need to save some of the positions for future reference
			save_retracted_position(current_pos);
			save_primed_position(current_pos);
			return;
		}
		
	}
		
	try_add_internal(current_pos, get_stabilization_distance(current_pos), type);

	// If we are using snap to print, and the current position is = is_extruding_start
	if (args_.type == trigger_type_snap_to_print && current_pos.is_extruding_start)
	{
		// try to add the snap_to_print starting position
		try_add_extrusion_start_positions(previous_pos);
	}
	

}
void trigger_positions::try_add_feature_position_internal(position & pos, double distance)
{
	bool add_position = false;
	if (feature_position_list_[pos.feature_type_tag].is_empty)
	{
		add_position = true;
	}
	else if (utilities::less_than(distance, feature_position_list_[pos.feature_type_tag].distance))
	{
		add_position = true;
	}
	else if (utilities::is_equal(feature_position_list_[pos.feature_type_tag].distance, distance) && !previous_initial_pos_.is_empty)
	{
		//std::cout << "Closest position tie detected, ";
		const double old_distance_from_previous = utilities::get_cartesian_distance(feature_position_list_[pos.feature_type_tag].pos.x, feature_position_list_[pos.feature_type_tag].pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
		const double new_distance_from_previous = utilities::get_cartesian_distance(pos.x, pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
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
		add_feature_position_internal(pos, distance);
	}
}

void trigger_positions::add_feature_position_internal(position &pos, double distance)
{
	feature_position_list_[pos.feature_type_tag].pos = pos;
	feature_position_list_[pos.feature_type_tag].distance = distance;
	feature_position_list_[pos.feature_type_tag].type_feature = static_cast<feature_type>(pos.feature_type_tag);
	feature_position_list_[pos.feature_type_tag].is_empty = false;

}
// Adds a position to the internal position list.
void trigger_positions::add_internal(position &pos, double distance, position_type type)
{
	position_list_[type].pos = pos;
	position_list_[type].distance = distance;
	position_list_[type].type_position = type;
	position_list_[type].is_empty = false;

}

void trigger_positions::try_add_extrusion_start_positions(position& extrusion_start_pos)
{
	// Try to add the start of the extrusion to the snap to print stabilization
	if (!previous_retracted_pos_.is_empty)
		try_add_extrusion_start_position(extrusion_start_pos, previous_retracted_pos_);
	else if (!p_previous_primed_pos_.is_empty)
		try_add_extrusion_start_position( extrusion_start_pos, p_previous_primed_pos_);

}

void trigger_positions::try_add_extrusion_start_position(position & extrusion_start_pos, position & saved_pos)
{
	// A special case where we are trying to add a snap to print position from the start of an extrusion.
	// This is currently implemented only for a retracted position, but in theory we should add a primed position too, and use it as a backup.
	// Note that we do not need to add any checks for max speed or thresholds, since that will have been taken care of
	if (
		saved_pos.x != extrusion_start_pos.x ||
		saved_pos.y != extrusion_start_pos.y ||
		saved_pos.z != extrusion_start_pos.z
		)
	{
		return;
	}

	const double distance = get_stabilization_distance(saved_pos);

	// See if we need to update the fastest extrusion position
	if (
		utilities::is_equal(fastest_extrusion_speed_, extrusion_start_pos.f)
		&& utilities::less_than(distance, position_list_[position_type_fastest_extrusion].distance))
	{
		// add the current position as the fastest extrusion speed 
		add_internal(saved_pos, distance, position_type::position_type_fastest_extrusion);
	}

	
	bool add_position = false;
	if (!position_list_[position_type::position_type_extrusion].is_empty)
	{
		add_position = true;
	}
	else if (utilities::less_than(distance, position_list_[position_type::position_type_extrusion].distance))
	{
		add_position = true;
	}
	else if (utilities::is_equal(position_list_[position_type::position_type_extrusion].distance, distance) && !previous_initial_pos_.is_empty)
	{
		//std::cout << "Closest position tie detected, ";
		const double old_distance_from_previous = utilities::get_cartesian_distance(
			position_list_[position_type::position_type_extrusion].pos.x, 
			position_list_[position_type_extrusion].pos.y, 
			previous_initial_pos_.x, 
			previous_initial_pos_.y
		);
		const double new_distance_from_previous = utilities::get_cartesian_distance(saved_pos.x, saved_pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
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
		add_internal(saved_pos, distance, position_type::position_type_extrusion);
	}
}

// Try to add a position to the internal position list.
void trigger_positions::try_add_internal(position & pos, double distance, position_type type)
{

	// If this is an extrusion type position, we need to handle it with care since we want to track both the closest 
	// extrusion and the closest extrusion at the fastest speed (inluding any speed filters that are supplied.
	if (type == position_type_extrusion)
	{
		// First make sure to update the fastest and slowest extrusion speeds.
		// important for implementing any 'min_extrusion_speed_difference_' rules.
		if (slowest_extrusion_speed_ == -1 || utilities::less_than(pos.f, slowest_extrusion_speed_))
		{
			slowest_extrusion_speed_ = pos.f;
		}
		
		// See if the feedrate is faster than our minimum speed.
		if (args_.minimum_speed > -1)
		{
			// see if we should filter out this position due to the feedrate
			if (utilities::less_than_or_equal(pos.f, args_.minimum_speed))
				return;
		}

		// Now that we've filtered any feed rates below the minimum speed, let's let's see if we've set a new speed record
		bool add_fastest = false;
		if (utilities::greater_than(pos.f, fastest_extrusion_speed_))
		{
			fastest_extrusion_speed_ = pos.f;
			add_fastest = true;
		}
		else if (
			utilities::is_equal(fastest_extrusion_speed_, pos.f)
			&& utilities::less_than(distance, position_list_[position_type_fastest_extrusion].distance))
		{
			add_fastest = true;
		}

		if (add_fastest)
		{
			// add the current position as the fastest extrusion speed 
			add_internal(pos, distance, position_type_fastest_extrusion);
		}

	}
	
	// See if we have a closer position	for any but the 'fastest_extrusion' position (it will have been dealt with by now)
	// First get the current closest position by type
	
	bool add_position = false;
	if (position_list_[type].is_empty)
	{
		add_position = true;
	}
	else if (utilities::less_than(distance, position_list_[type].distance))
	{
		add_position = true;
	}
	else if (utilities::is_equal(position_list_[type].distance, distance) && !previous_initial_pos_.is_empty)
	{
		//std::cout << "Closest position tie detected, ";
		const double old_distance_from_previous = utilities::get_cartesian_distance(position_list_[type].pos.x, position_list_[type].pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
		const double new_distance_from_previous = utilities::get_cartesian_distance(pos.x, pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
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
		add_internal(pos, distance, type);
	}
}