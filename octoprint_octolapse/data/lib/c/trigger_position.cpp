#include "trigger_position.h"
#include "utilities.h"
#include "stabilization_smart_layer.h"

position_type trigger_position::get_type(position* p_pos)
{
  if (p_pos->get_current_extruder().is_partially_retracted || p_pos->get_current_extruder().is_deretracted)
    return position_type_unknown;

  if (p_pos->get_current_extruder().is_extruding && utilities::greater_than(p_pos->get_current_extruder().e_relative, 0)
  )
  {
    return position_type_extrusion;
  }
  else if (p_pos->is_xy_travel)
  {
    if (p_pos->get_current_extruder().is_retracted)
    {
      if (p_pos->is_zhop)
        return position_type_lifted_retracted_travel;
      else
        return position_type_retracted_travel;
    }
    else
    {
      if (p_pos->is_zhop)
        return position_type_lifted_travel;
      else
        return position_type_travel;
    }
  }
  else if (utilities::greater_than(p_pos->z_relative, 0))
  {
    if (p_pos->get_current_extruder().is_retracted)
    {
      if (p_pos->is_xyz_travel)
      {
        if (p_pos->is_zhop)
          return position_type_lifted_retracted_travel;
        else
          return position_type_lifting_retracted_travel;
      }
      else
      {
        if (p_pos->is_zhop)
          return position_type_retracted_lifted;
        else
          return position_type_retracted_lifting;
      }
    }
    else
    {
      if (p_pos->is_xyz_travel)
      {
        if (p_pos->is_zhop)
          return position_type_lifted_travel;
        else
          return position_type_lifting_travel;
      }
      else
      {
        if (p_pos->is_zhop)
          return position_type_lifted;
        else
          return position_type_lifting;
      }
    }
  }
  else if (utilities::less_than(p_pos->get_current_extruder().e_relative, 0) && p_pos
                                                                                ->get_current_extruder().is_retracted)
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


void trigger_positions::set_previous_initial_position(position& pos)
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

bool trigger_positions::get_position(trigger_position& pos)
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

    if (utilities::greater_than(args_.minimum_speed, 0) && utilities::greater_than_or_equal(
      position_list_[position_type_fastest_extrusion].pos.f, args_.minimum_speed))
    {
      return true;
    }
    if (utilities::less_than_or_equal(args_.minimum_speed, 0) && utilities::greater_than(
      fastest_extrusion_speed_, slowest_extrusion_speed_))
    {
      return true;
    }
  }
  return false;
}

// Gets the snap to print position from the position list
bool trigger_positions::get_snap_to_print_position(trigger_position& pos)
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
        if (current_closest_index < 0 || utilities::less_than(feature_position_list_[index].distance,
                                                              feature_position_list_[current_closest_index].distance))
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

  // if the p_extrusion distance is less than or equal to the p_fastest_extrusion distance, return that.
  if (utilities::less_than_or_equal(position_list_[position_type_extrusion].distance,
                                    position_list_[position_type_fastest_extrusion].distance))
  {
    pos = position_list_[position_type_extrusion];
  }
  else
    pos = position_list_[position_type_fastest_extrusion];

  // return p_fastest_extrusion, which is equal to or less than the travel distance of p_extrusion
  return true;
}

bool trigger_positions::get_fast_position(trigger_position& pos)
{
  pos.is_empty = true;
  int current_closest_index = -1;
  // Loop backwards so that in the case of ties, the best match (the one with the higher enum value) is selected
  for (int index = trigger_position::num_position_types - 1; index > -1; index--)
  {
    if (!position_list_[index].is_empty)
    {
      if (current_closest_index < 0 || utilities::less_than(position_list_[index].distance,
                                                            position_list_[current_closest_index].distance))
        current_closest_index = index;
    }
  }
  if (current_closest_index > -1)
  {
    pos = position_list_[current_closest_index];
    return true;
  }
  return false;
}

bool trigger_positions::get_compatibility_position(trigger_position& pos)
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

bool trigger_positions::get_high_quality_position(trigger_position& pos)
{
  for (int index = NUM_FEATURE_TYPES - 1; index > feature_type_inner_perimeter_feature - 1; index--)
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

void trigger_positions::try_save_retracted_position(position* p_current_pos)
{
  if (p_current_pos->get_current_extruder().is_retracted)
    previous_retracted_pos_ = *p_current_pos;
  else if (p_current_pos->get_current_extruder().is_extruding && !p_current_pos
                                                                  ->get_current_extruder().is_extruding_start)
    previous_retracted_pos_.is_empty = true;
}

void trigger_positions::try_save_primed_position(position* p_current_pos)
{
  if (p_current_pos->get_current_extruder().is_primed)
    previous_primed_pos_ = *p_current_pos;
  else if (p_current_pos->get_current_extruder().is_extruding && !p_current_pos
                                                                  ->get_current_extruder().is_extruding_start)
    previous_primed_pos_.is_empty = true;
}

void trigger_positions::clear()
{
  // reset all tracking variables
  fastest_extrusion_speed_ = -1;
  slowest_extrusion_speed_ = -1;
  previous_initial_pos_.is_empty = true;
  previous_retracted_pos_.is_empty = true;
  previous_primed_pos_.is_empty = true;

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


bool trigger_positions::can_process_position(position* pos, const position_type type)
{
  if (type == position_type_unknown || pos->is_empty)
    return false;


  // check for errors in position, layer, or height
  if (pos->layer == 0 || pos->x_null || pos->y_null || pos->z_null)
  {
    return false;
  }
  // See if we should ignore the current position because it is not in bounds, or because it wasn't processed
  if (pos->gcode_ignored || !pos->is_in_bounds)
    return false;

  // Never save any positions that are below the highest extrusion point.
  if (utilities::less_than(pos->z, pos->last_extrusion_height))
  {
    // if the current z height is less than the maximum extrusion height!
    // Do not add this point else we might ram into the printed part!
    // Note:  This is even a problem for snap to print, since the extruder will appear to drop, which makes for a bad timelapse
    return false;
  }
  return true;
}


double trigger_positions::get_stabilization_distance(position* p_pos) const
{
  double x, y;
  if (args_.x_stabilization_disabled && previous_initial_pos_.is_empty)
  {
    x = p_pos->x;
  }
  else
  {
    x = stabilization_x_;
  }
  if (args_.y_stabilization_disabled && previous_initial_pos_.is_empty)
  {
    y = p_pos->y;
  }
  else
  {
    y = stabilization_y_;
  }

  return utilities::get_cartesian_distance(p_pos->x, p_pos->y, x, y);
}

/// Try to add a position to the position list.  Returns false if no position can be added.
void trigger_positions::try_add(position* p_current_pos, position* p_previous_pos)
{
  // Get the position type
  const position_type type = trigger_position::get_type(p_current_pos);

  if (!can_process_position(p_current_pos, type))
  {
    return;
  }

  // add any feature positions if a feature tag exists, and if we are in high quality or compatibility mode
  if (
    p_current_pos->feature_type_tag != feature_type::feature_type_unknown_feature &&
    (
      args_.type == trigger_type_high_quality ||
      args_.type == trigger_type_compatibility ||
      (args_.type == trigger_type_snap_to_print && type == position_type_extrusion && args_.snap_to_print_high_quality)
    )
  )
  {
    // only add features if we are extruding.
    if (p_current_pos->get_current_extruder().is_extruding)
    {
      try_add_feature_position_internal(p_current_pos);
      if (p_current_pos->get_current_extruder().is_extruding_start)
      {
        // if this is an extrusion_stat (also an extrusion), we will want to add the
        // starting point of the extrusion as well , which would not have been marked as an extrusion
        position* start_pos = NULL;
        // set the latest saved retracted (preferred) or primed position
        if (!previous_retracted_pos_.is_empty)
          start_pos = &previous_retracted_pos_;
        else
          start_pos = &previous_primed_pos_;

        if (
          start_pos != NULL &&
          start_pos->x == p_previous_pos->x &&
          start_pos->y == p_previous_pos->y &&
          start_pos->z == p_previous_pos->z
        )
        {
          // If we have a starting position that matches the previous position (retracted or primed)
          // try to add the previous position to the feature position list
          try_add_feature_position_internal(p_previous_pos);
        }
      }
    }
  }

  if (args_.type == trigger_type_snap_to_print)
  {
    // Do special things for snap to print trigger


    // If this isn't an extrusion, we might need to save some of the positions for future reference
    try_save_retracted_position(p_current_pos);
    try_save_primed_position(p_current_pos);
  }
  const double distance = get_stabilization_distance(p_current_pos);
  //std::cout << "Distance:" << distance << "\r\n";
  try_add_internal(p_current_pos, distance, type);

  // If we are using snap to print, and the current position is = is_extruding_start
  if (args_.type == trigger_type_snap_to_print)
  {
    if (p_current_pos->get_current_extruder().is_extruding_start)
    {
      // try to add the snap_to_print starting position
      try_add_extrusion_start_positions(p_previous_pos);
    }
    else if (p_current_pos->get_current_extruder().is_extruding)
    {
      previous_retracted_pos_.is_empty = true;
      previous_primed_pos_.is_empty = true;
    }
  }
}

void trigger_positions::try_add_feature_position_internal(position* p_pos)
{
  bool add_position = false;
  const double distance = get_stabilization_distance(p_pos);
  const feature_type type = static_cast<feature_type>(p_pos->feature_type_tag);

  if (feature_position_list_[type].is_empty)
  {
    add_position = true;
  }
  else if (utilities::less_than(distance, feature_position_list_[type].distance))
  {
    add_position = true;
  }
  else if (utilities::is_equal(feature_position_list_[type].distance, distance) && !previous_initial_pos_.is_empty)
  {
    //std::cout << "Closest position tie detected, ";
    const double old_distance_from_previous = utilities::get_cartesian_distance(
      feature_position_list_[type].pos.x, feature_position_list_[type].pos.y, previous_initial_pos_.x,
      previous_initial_pos_.y);
    const double new_distance_from_previous = utilities::get_cartesian_distance(
      p_pos->x, p_pos->y, previous_initial_pos_.x, previous_initial_pos_.y);
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
    add_feature_position_internal(p_pos, distance, static_cast<feature_type>(type));
  }
}

void trigger_positions::add_feature_position_internal(position* p_pos, double distance, feature_type type)
{
  feature_position_list_[p_pos->feature_type_tag].pos = *p_pos;
  feature_position_list_[p_pos->feature_type_tag].distance = distance;
  feature_position_list_[p_pos->feature_type_tag].type_feature = type;
  feature_position_list_[p_pos->feature_type_tag].is_empty = false;
}

// Adds a position to the internal position list.
void trigger_positions::add_internal(position* p_pos, double distance, position_type type)
{
  position_list_[type].pos = *p_pos;
  position_list_[type].distance = distance;
  position_list_[type].type_position = type;
  position_list_[type].is_empty = false;
}

void trigger_positions::try_add_extrusion_start_positions(position* p_extrusion_start_pos)
{
  // Try to add the start of the extrusion to the snap to print stabilization
  if (!previous_retracted_pos_.is_empty)
    try_add_extrusion_start_position(p_extrusion_start_pos, previous_retracted_pos_);
  else if (!previous_primed_pos_.is_empty)
    try_add_extrusion_start_position(p_extrusion_start_pos, previous_primed_pos_);
}

void trigger_positions::try_add_extrusion_start_position(position* p_extrusion_start_pos, position& saved_pos)
{
  // A special case where we are trying to add a snap to print position from the start of an extrusion.
  // Note that we do not need to add any checks for max speed or thresholds, since that will have been taken care of
  if (
    saved_pos.x != p_extrusion_start_pos->x ||
    saved_pos.y != p_extrusion_start_pos->y ||
    saved_pos.z != p_extrusion_start_pos->z
  )
  {
    return;
  }

  const double distance = get_stabilization_distance(&saved_pos);

  // See if we need to update the fastest extrusion position
  if (
    utilities::is_equal(fastest_extrusion_speed_, p_extrusion_start_pos->f)
    && utilities::less_than(distance, position_list_[position_type_fastest_extrusion].distance))
  {
    // add the current position as the fastest extrusion speed 
    add_internal(&saved_pos, distance, position_type_fastest_extrusion);
  }


  bool add_position = false;
  if (position_list_[position_type_extrusion].is_empty)
  {
    add_position = true;
  }
  else if (utilities::less_than(distance, position_list_[position_type_extrusion].distance))
  {
    add_position = true;
  }
  else if (utilities::is_equal(position_list_[position_type_extrusion].distance, distance) && !previous_initial_pos_.
    is_empty)
  {
    //std::cout << "Closest position tie detected, ";
    const double old_distance_from_previous = utilities::get_cartesian_distance(
      position_list_[position_type_extrusion].pos.x,
      position_list_[position_type_extrusion].pos.y,
      previous_initial_pos_.x,
      previous_initial_pos_.y
    );
    const double new_distance_from_previous = utilities::get_cartesian_distance(
      saved_pos.x, saved_pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
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
    add_internal(&saved_pos, distance, position_type_extrusion);
  }
}

// Try to add a position to the internal position list.
void trigger_positions::try_add_internal(position* p_pos, double distance, position_type type)
{
  // If this is an extrusion type position, we need to handle it with care since we want to track both the closest 
  // extrusion and the closest extrusion at the fastest speed (inluding any speed filters that are supplied.
  if (type == position_type_extrusion)
  {
    // First make sure to update the fastest and slowest extrusion speeds.
    // important for implementing any 'min_extrusion_speed_difference_' rules.
    if (slowest_extrusion_speed_ == -1 || utilities::less_than(p_pos->f, slowest_extrusion_speed_))
    {
      slowest_extrusion_speed_ = p_pos->f;
    }

    // See if the feedrate is faster than our minimum speed.
    if (args_.minimum_speed > 0)
    {
      // see if we should filter out this position due to the feedrate
      if (utilities::less_than_or_equal(p_pos->f, args_.minimum_speed))
        return;
    }

    // Now that we've filtered any feed rates below the minimum speed, let's let's see if we've set a new speed record
    bool add_fastest = false;
    if (utilities::greater_than(p_pos->f, fastest_extrusion_speed_))
    {
      fastest_extrusion_speed_ = p_pos->f;
      add_fastest = true;
    }
    else if (
      utilities::is_equal(fastest_extrusion_speed_, p_pos->f)
      && utilities::less_than(distance, position_list_[position_type_fastest_extrusion].distance))
    {
      add_fastest = true;
    }

    if (add_fastest)
    {
      // add the current position as the fastest extrusion speed 
      add_internal(p_pos, distance, position_type_fastest_extrusion);
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
    const double old_distance_from_previous = utilities::get_cartesian_distance(
      position_list_[type].pos.x, position_list_[type].pos.y, previous_initial_pos_.x, previous_initial_pos_.y);
    const double new_distance_from_previous = utilities::get_cartesian_distance(
      p_pos->x, p_pos->y, previous_initial_pos_.x, previous_initial_pos_.y);
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
    add_internal(p_pos, distance, type);
  }
}
