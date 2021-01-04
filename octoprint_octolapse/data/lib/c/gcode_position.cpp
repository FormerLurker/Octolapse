////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Octolapse - A plugin for OctoPrint used for making stabilized timelapse videos.
// Copyright(C) 2019  Brad Hochgesang
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// This program is free software : you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.If not, see the following :
// https ://github.com/FormerLurker/Octolapse/blob/master/LICENSE
//
// You can contact the author either through the git - hub repository, or at the
// following email address : FormerLurker@pm.me
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#include "gcode_position.h"
#include "utilities.h"
#include "logging.h"
#include <algorithm>
#include <iterator>

gcode_position_args::gcode_position_args(const gcode_position_args& pos_args)
{
  shared_extruder = pos_args.shared_extruder;
  autodetect_position = pos_args.autodetect_position;
  is_circular_bed = pos_args.is_circular_bed;
  home_x = pos_args.home_x;
  home_y = pos_args.home_y;
  home_z = pos_args.home_z;
  home_x_none = pos_args.home_x_none;
  home_y_none = pos_args.home_y_none;
  home_z_none = pos_args.home_z_none;

  priming_height = pos_args.priming_height;
  minimum_layer_height = pos_args.minimum_layer_height;
  height_increment = pos_args.height_increment;
  g90_influences_extruder = pos_args.g90_influences_extruder;
  xyz_axis_default_mode = pos_args.xyz_axis_default_mode;
  e_axis_default_mode = pos_args.e_axis_default_mode;
  units_default = pos_args.units_default;
  is_bound_ = pos_args.is_bound_;
  x_min = pos_args.x_min;
  x_max = pos_args.x_max;
  y_min = pos_args.y_min;
  y_max = pos_args.y_max;
  z_min = pos_args.z_min;
  z_max = pos_args.z_max;
  snapshot_x_min = pos_args.snapshot_x_min;
  snapshot_x_max = pos_args.snapshot_x_max;
  snapshot_y_min = pos_args.snapshot_y_min;
  snapshot_y_max = pos_args.snapshot_y_max;
  snapshot_z_min = pos_args.snapshot_z_min;
  snapshot_z_max = pos_args.snapshot_z_max;

  default_extruder = pos_args.default_extruder;
  zero_based_extruder = pos_args.zero_based_extruder;
  num_extruders = pos_args.num_extruders;
  retraction_lengths = NULL;
  z_lift_heights = NULL;
  x_firmware_offsets = NULL;
  y_firmware_offsets = NULL;
  set_num_extruders(pos_args.num_extruders);
  // copy extruder specific members
  for (int index = 0; index < pos_args.num_extruders; index++)
  {
    retraction_lengths[index] = pos_args.retraction_lengths[index];
    z_lift_heights[index] = pos_args.z_lift_heights[index];
    if (!pos_args.shared_extruder)
    {
      x_firmware_offsets[index] = pos_args.x_firmware_offsets[index];
      y_firmware_offsets[index] = pos_args.y_firmware_offsets[index];
    }
    else
    {
      x_firmware_offsets[index] = 0;
      y_firmware_offsets[index] = 0;
    }
  }
  std::vector<std::string> location_detection_commands; // Final list of location detection commands
}

gcode_position_args& gcode_position_args::operator=(const gcode_position_args& pos_args)
{
  shared_extruder = pos_args.shared_extruder;
  autodetect_position = pos_args.autodetect_position;
  is_circular_bed = pos_args.is_circular_bed;
  home_x = pos_args.home_x;
  home_y = pos_args.home_y;
  home_z = pos_args.home_z;
  home_x_none = pos_args.home_x_none;
  home_y_none = pos_args.home_y_none;
  home_z_none = pos_args.home_z_none;

  priming_height = pos_args.priming_height;
  minimum_layer_height = pos_args.minimum_layer_height;
  height_increment = pos_args.height_increment;
  g90_influences_extruder = pos_args.g90_influences_extruder;
  xyz_axis_default_mode = pos_args.xyz_axis_default_mode;
  e_axis_default_mode = pos_args.e_axis_default_mode;
  units_default = pos_args.units_default;
  is_bound_ = pos_args.is_bound_;
  x_min = pos_args.x_min;
  x_max = pos_args.x_max;
  y_min = pos_args.y_min;
  y_max = pos_args.y_max;
  z_min = pos_args.z_min;
  z_max = pos_args.z_max;
  snapshot_x_min = pos_args.snapshot_x_min;
  snapshot_x_max = pos_args.snapshot_x_max;
  snapshot_y_min = pos_args.snapshot_y_min;
  snapshot_y_max = pos_args.snapshot_y_max;
  snapshot_z_min = pos_args.snapshot_z_min;
  snapshot_z_max = pos_args.snapshot_z_max;

  default_extruder = pos_args.default_extruder;
  zero_based_extruder = pos_args.zero_based_extruder;
  num_extruders = pos_args.num_extruders;
  delete_retraction_lengths();
  delete_x_firmware_offsets();
  delete_y_firmware_offsets();
  delete_z_lift_heights();
  set_num_extruders(pos_args.num_extruders);
  // copy extruder specific members
  for (int index = 0; index < pos_args.num_extruders; index++)
  {
    retraction_lengths[index] = pos_args.retraction_lengths[index];
    z_lift_heights[index] = pos_args.z_lift_heights[index];
    if (!pos_args.shared_extruder)
    {
      x_firmware_offsets[index] = pos_args.x_firmware_offsets[index];
      y_firmware_offsets[index] = pos_args.y_firmware_offsets[index];
    }
    else
    {
      x_firmware_offsets[index] = 0;
      y_firmware_offsets[index] = 0;
    }
  }
  std::vector<std::string> location_detection_commands; // Final list of location detection commands
  return *this;
}

void gcode_position_args::set_num_extruders(int num_extruders_)
{
  delete_retraction_lengths();
  delete_z_lift_heights();
  delete_x_firmware_offsets();
  delete_y_firmware_offsets();
  num_extruders = num_extruders_;
  retraction_lengths = new double[num_extruders_];
  z_lift_heights = new double[num_extruders_];
  x_firmware_offsets = new double[num_extruders_];
  y_firmware_offsets = new double[num_extruders_];
  // initialize arrays
  for (int index = 0; index < num_extruders; index++)
  {
    retraction_lengths[index] = 0.0;
    z_lift_heights[index] = 0.0;
    x_firmware_offsets[index] = 0.0;
    y_firmware_offsets[index] = 0.0;
  }
}

void gcode_position_args::delete_retraction_lengths()
{
  if (retraction_lengths != NULL)
  {
    delete[] retraction_lengths;
    retraction_lengths = NULL;
  }
}

void gcode_position_args::delete_z_lift_heights()
{
  if (z_lift_heights != NULL)
  {
    delete[] z_lift_heights;
    z_lift_heights = NULL;
  }
}

void gcode_position_args::delete_x_firmware_offsets()
{
  if (x_firmware_offsets != NULL)
  {
    delete[] x_firmware_offsets;
    x_firmware_offsets = NULL;
  }
}

void gcode_position_args::delete_y_firmware_offsets()
{
  if (y_firmware_offsets != NULL)
  {
    delete[] y_firmware_offsets;
    y_firmware_offsets = NULL;
  }
}

gcode_position::gcode_position()
{
  autodetect_position_ = false;
  home_x_ = 0;
  home_y_ = 0;
  home_z_ = 0;
  home_x_none_ = true;
  home_y_none_ = true;
  home_z_none_ = true;
  retraction_lengths_ = NULL;
  z_lift_heights_ = NULL;
  shared_extruder_ = false;
  set_num_extruders(0);
  zero_based_extruder_ = true;
  priming_height_ = 0;
  minimum_layer_height_ = 0;
  height_increment_ = 0;
  g90_influences_extruder_ = false;
  e_axis_default_mode_ = "absolute";
  xyz_axis_default_mode_ = "absolute";
  units_default_ = "millimeters";
  gcode_functions_ = get_gcode_functions();

  is_bound_ = false;
  snapshot_x_min_ = 0;
  snapshot_x_max_ = 0;
  snapshot_y_min_ = 0;
  snapshot_y_max_ = 0;
  snapshot_z_min_ = 0;
  snapshot_z_max_ = 0;

  x_min_ = 0;
  x_max_ = 0;
  y_min_ = 0;
  y_max_ = 0;
  z_min_ = 0;
  z_max_ = 0;
  is_circular_bed_ = false;

  cur_pos_ = 0;

  for (int index = 0; index < NUM_POSITIONS; index ++)
  {
    position initial_pos(num_extruders_);
    initial_pos.set_xyz_axis_mode(xyz_axis_default_mode_);
    initial_pos.set_e_axis_mode(e_axis_default_mode_);
    initial_pos.set_units_default(units_default_);
    add_position(initial_pos);
  }
}


gcode_position::gcode_position(gcode_position_args args)
{
  autodetect_position_ = args.autodetect_position;
  home_x_ = args.home_x;
  home_y_ = args.home_y;
  home_z_ = args.home_z;
  home_x_none_ = args.home_x_none;
  home_y_none_ = args.home_y_none;
  home_z_none_ = args.home_z_none;
  retraction_lengths_ = NULL;
  z_lift_heights_ = NULL;
  // Configure Extruders
  shared_extruder_ = args.shared_extruder;
  set_num_extruders(args.num_extruders);
  zero_based_extruder_ = args.zero_based_extruder;
  // Set the current extruder to the default extruder (0 based)
  int current_extruder = args.default_extruder;
  // make sure our current extruder is between 0 and num_extruders - 1
  if (current_extruder < 0)
  {
    current_extruder = 0;
  }
  else if (current_extruder > args.num_extruders - 1)
  {
    current_extruder = args.num_extruders - 1;
  }

  // copy the retraction lengths array
  for (int index = 0; index < args.num_extruders; index++)
  {
    retraction_lengths_[index] = args.retraction_lengths[index];
  }
  // Copy the z_lift_heights array from the arguments
  for (int index = 0; index < args.num_extruders; index++)
  {
    z_lift_heights_[index] = args.z_lift_heights[index];
  }
  // Copy the firmware offsets
  for (int index = 0; index < args.num_extruders; index++)
  {
    retraction_lengths_[index] = args.retraction_lengths[index];
  }

  priming_height_ = args.priming_height;
  minimum_layer_height_ = args.minimum_layer_height;
  height_increment_ = args.height_increment;
  g90_influences_extruder_ = args.g90_influences_extruder;
  e_axis_default_mode_ = args.e_axis_default_mode;
  xyz_axis_default_mode_ = args.xyz_axis_default_mode;
  units_default_ = args.units_default;
  gcode_functions_ = get_gcode_functions();

  is_bound_ = args.is_bound_;
  snapshot_x_min_ = args.snapshot_x_min;
  snapshot_x_max_ = args.snapshot_x_max;
  snapshot_y_min_ = args.snapshot_y_min;
  snapshot_y_max_ = args.snapshot_y_max;
  snapshot_z_min_ = args.snapshot_z_min;
  snapshot_z_max_ = args.snapshot_z_max;

  x_min_ = args.x_min;
  x_max_ = args.x_max;
  y_min_ = args.y_min;
  y_max_ = args.y_max;
  z_min_ = args.z_min;
  z_max_ = args.z_max;

  is_circular_bed_ = args.is_circular_bed;

  cur_pos_ = -1;
  num_extruders_ = args.num_extruders;

  // Configure the initial position
  position initial_pos(num_extruders_);
  initial_pos.set_xyz_axis_mode(xyz_axis_default_mode_);
  initial_pos.set_e_axis_mode(e_axis_default_mode_);
  initial_pos.set_units_default(units_default_);
  initial_pos.current_tool = current_extruder;
  for (int index = 0; index < args.num_extruders; index++)
  {
    initial_pos.p_extruders[index].x_firmware_offset = args.x_firmware_offsets[index];
    initial_pos.p_extruders[index].y_firmware_offset = args.y_firmware_offsets[index];
  }

  for (int index = 0; index < NUM_POSITIONS; index++)
  {
    add_position(initial_pos);
  }
}

gcode_position::gcode_position(const gcode_position& source)
{
  // Private copy constructor - you can't copy this class
}

gcode_position::~gcode_position()
{
  delete_retraction_lengths_();
  delete_z_lift_heights_();
}

void gcode_position::set_num_extruders(int num_extruders)
{
  delete_retraction_lengths_();
  delete_z_lift_heights_();
  if (shared_extruder_)
  {
    num_extruders_ = 1;
  }
  else
  {
    num_extruders_ = num_extruders;
  }
  retraction_lengths_ = new double[num_extruders];
  z_lift_heights_ = new double[num_extruders];
}

void gcode_position::delete_retraction_lengths_()
{
  if (retraction_lengths_ != NULL)
  {
    delete[] retraction_lengths_;
    retraction_lengths_ = NULL;
  }
}

void gcode_position::delete_z_lift_heights_()
{
  if (z_lift_heights_ != NULL)
  {
    delete[] z_lift_heights_;
    z_lift_heights_ = NULL;
  }
}

void gcode_position::add_position(position& pos)
{
  cur_pos_ = (++cur_pos_) % NUM_POSITIONS;
  positions_[cur_pos_] = pos;
}

void gcode_position::add_position(parsed_command& cmd)
{
  const int prev_pos = cur_pos_;
  cur_pos_ = (++cur_pos_) % NUM_POSITIONS;
  positions_[cur_pos_] = positions_[prev_pos];
  positions_[cur_pos_].reset_state();
  positions_[cur_pos_].command = cmd;
  positions_[cur_pos_].is_empty = false;
}

position gcode_position::get_current_position() const
{
  return positions_[cur_pos_];
}

position gcode_position::get_previous_position() const
{
  return positions_[(cur_pos_ - 1 + NUM_POSITIONS) % NUM_POSITIONS];
}

position* gcode_position::get_current_position_ptr()
{
  return &positions_[cur_pos_];
}

position* gcode_position::get_previous_position_ptr()
{
  return &positions_[(cur_pos_ - 1 + NUM_POSITIONS) % NUM_POSITIONS];
}

void gcode_position::update(parsed_command& command, const long file_line_number, const long gcode_number,
                            const long file_position)
{
  if (command.is_empty)
  {
    // process any comment sections
    comment_processor_.update(command.comment);
    return;
  }

  add_position(command);
  position* p_current_pos = get_current_position_ptr();
  position* p_previous_pos = get_previous_position_ptr();
  p_current_pos->file_line_number = file_line_number;
  p_current_pos->gcode_number = gcode_number;
  p_current_pos->file_position = file_position;
  comment_processor_.update(*p_current_pos);

  if (!command.is_known_command)
    return;

  // Does our function exist in our functions map?
  gcode_functions_iterator_ = gcode_functions_.find(command.command);

  if (gcode_functions_iterator_ != gcode_functions_.end())
  {
    p_current_pos->gcode_ignored = false;
    // Execute the function to process this gcode
    const pos_function_type func = gcode_functions_iterator_->second;
    (this->*func)(p_current_pos, command);
    // calculate z and e relative distances
    p_current_pos->get_current_extruder().e_relative = (p_current_pos->get_current_extruder().e - p_previous_pos
                                                                                                  ->get_extruder(
                                                                                                    p_current_pos->
                                                                                                    current_tool).e);
    p_current_pos->z_relative = (p_current_pos->z - p_previous_pos->z);
    // Have the XYZ positions changed after processing a command ?

    p_current_pos->has_xy_position_changed = (
      !utilities::is_equal(p_current_pos->x, p_previous_pos->x) ||
      !utilities::is_equal(p_current_pos->y, p_previous_pos->y)
    );
    p_current_pos->has_position_changed = (
      p_current_pos->has_xy_position_changed ||
      !utilities::is_equal(p_current_pos->z, p_previous_pos->z) ||
      !utilities::is_zero(p_current_pos->get_current_extruder().e_relative) ||
      p_current_pos->x_null != p_previous_pos->x_null ||
      p_current_pos->y_null != p_previous_pos->y_null ||
      p_current_pos->z_null != p_previous_pos->z_null);

    // see if our position is homed
    if (!p_current_pos->has_definite_position)
    {
      p_current_pos->has_definite_position = (
        //p_current_pos->x_homed_ &&
        //p_current_pos->y_homed_ &&
        //p_current_pos->z_homed_ &&
        p_current_pos->is_metric &&
        !p_current_pos->is_metric_null &&
        !p_current_pos->x_null &&
        !p_current_pos->y_null &&
        !p_current_pos->z_null &&
        !p_current_pos->is_relative_null &&
        !p_current_pos->is_extruder_relative_null);
    }
  }

  if (p_current_pos->has_position_changed)
  {
    p_current_pos->get_current_extruder().extrusion_length_total += p_current_pos->get_current_extruder().e_relative;

    if (
      utilities::greater_than(p_current_pos->get_current_extruder().e_relative, 0) &&
      p_previous_pos->current_tool == p_current_pos->current_tool &&
      // notice we can use the previous position's current extruder since we've made sure they are using the same tool
      p_previous_pos->get_current_extruder().is_extruding &&
      !p_previous_pos->get_current_extruder().is_extruding_start)
    {
      // A little shortcut if we know we were extruding (not starting extruding) in the previous command
      // This lets us skip a lot of the calculations for the extruder, including the state calculation
      p_current_pos->get_current_extruder().extrusion_length = p_current_pos->get_current_extruder().e_relative;
    }
    else
    {
      // Update retraction_length and extrusion_length
      p_current_pos->get_current_extruder().retraction_length = p_current_pos->get_current_extruder().retraction_length
        - p_current_pos->get_current_extruder().e_relative;
      if (utilities::less_than_or_equal(p_current_pos->get_current_extruder().retraction_length, 0))
      {
        // we can use the negative retraction length to calculate our extrusion length!
        p_current_pos->get_current_extruder().extrusion_length = -1.0 * p_current_pos
                                                                        ->get_current_extruder().retraction_length;
        // set the retraction length to 0 since we are extruding
        p_current_pos->get_current_extruder().retraction_length = 0;
      }
      else
        p_current_pos->get_current_extruder().extrusion_length = 0;

      // calculate deretraction length
      if (utilities::greater_than(p_previous_pos->get_extruder(p_current_pos->current_tool).retraction_length,
                                  p_current_pos->get_current_extruder().retraction_length))
      {
        p_current_pos->get_current_extruder().deretraction_length = p_previous_pos
                                                                    ->get_extruder(p_current_pos->current_tool).
                                                                    retraction_length - p_current_pos
                                                                                        ->get_current_extruder().
                                                                                        retraction_length;
      }
      else
        p_current_pos->get_current_extruder().deretraction_length = 0;

      // *************Calculate extruder state*************
      // rounding should all be done by now
      if (p_current_pos->current_tool == p_previous_pos->current_tool)
      {
        // On a toolchange some flags are not possible, so don't change them.
        // these flags include like is_extruding, is_extruding_start, is_retracting_start, is_retracting, is_deretracting_start and is_deretracting
        // Note that it's ok to use the previous pos current extruder since we've  made sure the current tool is identical
        p_current_pos->get_current_extruder().is_extruding_start = utilities::greater_than(
            p_current_pos->get_current_extruder().extrusion_length, 0) && !p_previous_pos
                                                                           ->get_current_extruder().is_extruding;
        p_current_pos->get_current_extruder().is_extruding = utilities::greater_than(
          p_current_pos->get_current_extruder().extrusion_length, 0);
        p_current_pos->get_current_extruder().is_retracting_start = !p_previous_pos
                                                                     ->get_current_extruder().is_retracting && utilities
          ::greater_than(p_current_pos->get_current_extruder().retraction_length, 0);
        p_current_pos->get_current_extruder().is_retracting = utilities::greater_than(
          p_current_pos->get_current_extruder().retraction_length,
          p_previous_pos->get_current_extruder().retraction_length);
        p_current_pos->get_current_extruder().is_deretracting = utilities::greater_than(
          p_current_pos->get_current_extruder().deretraction_length,
          p_previous_pos->get_current_extruder().deretraction_length);
        p_current_pos->get_current_extruder().is_deretracting_start = utilities::greater_than(
            p_current_pos->get_current_extruder().deretraction_length, 0) && !p_previous_pos
                                                                              ->get_current_extruder().is_deretracting;
      }
      else
      {
        p_current_pos->get_current_extruder().is_extruding_start = false;
        p_current_pos->get_current_extruder().is_extruding = false;
        p_current_pos->get_current_extruder().is_retracting_start = false;
        p_current_pos->get_current_extruder().is_retracting = false;
        p_current_pos->get_current_extruder().is_deretracting = false;
        p_current_pos->get_current_extruder().is_deretracting_start = false;
      }
      p_current_pos->get_current_extruder().is_primed = utilities::
        is_zero(p_current_pos->get_current_extruder().extrusion_length) && utilities::is_zero(
          p_current_pos->get_current_extruder().retraction_length);
      p_current_pos->get_current_extruder().is_partially_retracted = utilities::
        greater_than(p_current_pos->get_current_extruder().retraction_length, 0) && utilities::less_than(
          p_current_pos->get_current_extruder().retraction_length, retraction_lengths_[p_current_pos->current_tool]);
      p_current_pos->get_current_extruder().is_retracted = utilities::greater_than_or_equal(
        p_current_pos->get_current_extruder().retraction_length, retraction_lengths_[p_current_pos->current_tool]);
      p_current_pos->get_current_extruder().is_deretracted = utilities::greater_than(
        p_previous_pos->get_extruder(p_current_pos->current_tool).retraction_length, 0) && utilities::is_zero(
        p_current_pos->get_current_extruder().retraction_length);
      // *************End Calculate extruder state*************
    }

    // Calcluate position restructions
    // TODO:  INCLUDE POSITION RESTRICTION CALCULATIONS!
    // Set is_in_bounds_ to false if we're not in bounds, it will be true at this point
    bool is_in_bounds = true;
    if (is_bound_)
    {
      if (!is_circular_bed_)
      {
        is_in_bounds = !(
          utilities::less_than(p_current_pos->x, snapshot_x_min_) ||
          utilities::greater_than(p_current_pos->x, snapshot_x_max_) ||
          utilities::less_than(p_current_pos->y, snapshot_y_min_) ||
          utilities::greater_than(p_current_pos->y, snapshot_y_max_) ||
          utilities::less_than(p_current_pos->z, snapshot_z_min_) ||
          utilities::greater_than(p_current_pos->z, snapshot_z_max_)
        );
      }
      else
      {
        double r;
        r = snapshot_x_max_; // good stand in for radius
        const double dist = sqrt(p_current_pos->x * p_current_pos->x + p_current_pos->y * p_current_pos->y);
        is_in_bounds = utilities::less_than_or_equal(dist, r);
      }
      p_current_pos->is_in_bounds = is_in_bounds;
    }

    // calculate last_extrusion_height and height
    // If we are extruding on a higher level, or if retract is enabled and the nozzle is primed
    // adjust the last extrusion height
    if (utilities::greater_than(p_current_pos->z, p_current_pos->last_extrusion_height))
    {
      if (!p_current_pos->z_null)
      {
        // detect layer changes/ printer priming/last extrusion height and height 
        // Normally we would only want to use is_extruding, but we can also use is_deretracted if the layer is greater than 0
        if (p_current_pos->get_current_extruder().is_extruding || (p_current_pos->layer > 0 && p_current_pos
                                                                                               ->get_current_extruder().
                                                                                               is_deretracted))
        {
          // Is Primed
          if (!p_current_pos->is_printer_primed)
          {
            // We haven't primed yet, check to see if we have priming height restrictions
            if (utilities::greater_than(priming_height_, 0))
            {
              // if a priming height is configured, see if we've extruded below the  height
              if (utilities::less_than(p_current_pos->z, priming_height_))
                p_current_pos->is_printer_primed = true;
            }
            else
              // if we have no priming height set, just set is_printer_primed = true.
              p_current_pos->is_printer_primed = true;
          }

          if (p_current_pos->is_printer_primed && is_in_bounds)
          {
            // Update the last extrusion height
            p_current_pos->last_extrusion_height = p_current_pos->z;
            p_current_pos->last_extrusion_height_null = false;

            // Calculate current height
            if (utilities::greater_than_or_equal(p_current_pos->z, p_previous_pos->height + minimum_layer_height_))
            {
              p_current_pos->height = p_current_pos->z;
              p_current_pos->is_layer_change = true;
              p_current_pos->layer++;
              if (height_increment_ != 0)
              {
                const double increment_double = p_current_pos->height / height_increment_;
                unsigned const int increment = utilities::round_up_to_int(increment_double);
                if (increment > p_current_pos->height_increment && increment > 1)
                {
                  p_current_pos->height_increment = increment;
                  p_current_pos->is_height_increment_change = true;
                  p_current_pos->height_increment_change_count++;
                }
              }
            }
          }
        }

        // calculate is_zhop
        if (p_current_pos->get_current_extruder().is_extruding || p_current_pos->z_null || p_current_pos->
          last_extrusion_height_null)
          p_current_pos->is_zhop = false;
        else
          p_current_pos->is_zhop = utilities::greater_than_or_equal(
            p_current_pos->z - p_current_pos->last_extrusion_height, z_lift_heights_[p_current_pos->current_tool]);
      }
    }
  }
}

void gcode_position::undo_update()
{
  cur_pos_ = (cur_pos_ - 1 + NUM_POSITIONS) % NUM_POSITIONS;
}

// Private Members
std::map<std::string, gcode_position::pos_function_type> gcode_position::get_gcode_functions()
{
  std::map<std::string, pos_function_type> newMap;
  newMap.insert(std::make_pair("G0", &gcode_position::process_g0_g1));
  newMap.insert(std::make_pair("G1", &gcode_position::process_g0_g1));
  newMap.insert(std::make_pair("G2", &gcode_position::process_g2));
  newMap.insert(std::make_pair("G3", &gcode_position::process_g3));
  newMap.insert(std::make_pair("G10", &gcode_position::process_g10));
  newMap.insert(std::make_pair("G11", &gcode_position::process_g11));
  newMap.insert(std::make_pair("G20", &gcode_position::process_g20));
  newMap.insert(std::make_pair("G21", &gcode_position::process_g21));
  newMap.insert(std::make_pair("G28", &gcode_position::process_g28));
  newMap.insert(std::make_pair("G90", &gcode_position::process_g90));
  newMap.insert(std::make_pair("G91", &gcode_position::process_g91));
  newMap.insert(std::make_pair("G92", &gcode_position::process_g92));
  newMap.insert(std::make_pair("M82", &gcode_position::process_m82));
  newMap.insert(std::make_pair("M83", &gcode_position::process_m83));
  newMap.insert(std::make_pair("M207", &gcode_position::process_m207));
  newMap.insert(std::make_pair("M208", &gcode_position::process_m208));
  newMap.insert(std::make_pair("M218", &gcode_position::process_m218));
  newMap.insert(std::make_pair("M563", &gcode_position::process_m563));
  newMap.insert(std::make_pair("T", &gcode_position::process_t));
  return newMap;
}

void gcode_position::update_position(
  position* pos,
  const double x,
  const bool update_x,
  const double y,
  const bool update_y,
  const double z,
  const bool update_z,
  const double e,
  const bool update_e,
  const double f,
  const bool update_f,
  const bool force,
  const bool is_g1_g0) const
{
  if (is_g1_g0)
  {
    if (!update_e)
    {
      if (update_z)
      {
        pos->is_xyz_travel = (update_x || update_y);
      }
      else
      {
        pos->is_xy_travel = (update_x || update_y);
      }
    }
  }
  if (update_f)
  {
    pos->f = f;
    pos->f_null = false;
  }

  if (force)
  {
    if (update_x)
    {
      pos->x = x + pos->x_offset - pos->x_firmware_offset;
      pos->x_null = false;
    }
    if (update_y)
    {
      pos->y = y + pos->y_offset - pos->y_firmware_offset;
      pos->y_null = false;
    }
    if (update_z)
    {
      pos->z = z + pos->z_offset - pos->z_firmware_offset;
      pos->z_null = false;
    }
    // note that e cannot be null and starts at 0
    if (update_e)
      pos->get_current_extruder().e = e + pos->get_current_extruder().e_offset;
    return;
  }

  if (!pos->is_relative_null)
  {
    if (pos->is_relative)
    {
      if (update_x)
      {
        if (!pos->x_null)
          pos->x = x + pos->x;
        else
        {
          octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                        "GcodePosition.update_position: Cannot update X because the XYZ axis mode is relative and X is null.");
        }
      }
      if (update_y)
      {
        if (!pos->y_null)
          pos->y = y + pos->y;
        else
        {
          octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                        "GcodePosition.update_position: Cannot update Y because the XYZ axis mode is relative and Y is null.");
        }
      }
      if (update_z)
      {
        if (!pos->z_null)
          pos->z = z + pos->z;
        else
        {
          octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                        "GcodePosition.update_position: Cannot update Z because the XYZ axis mode is relative and Z is null.");
        }
      }
    }
    else
    {
      if (update_x)
      {
        pos->x_firmware_offset = pos->get_current_extruder().x_firmware_offset;
        pos->x = x + pos->x_offset - pos->x_firmware_offset;
        pos->x_null = false;
      }
      if (update_y)
      {
        pos->y_firmware_offset = pos->get_current_extruder().y_firmware_offset;
        pos->y = y + pos->y_offset - pos->y_firmware_offset;
        pos->y_null = false;
      }
      if (update_z)
      {
        pos->z_firmware_offset = pos->get_current_extruder().z_firmware_offset;
        pos->z = z + pos->z_offset - pos->z_firmware_offset;
        pos->z_null = false;
      }
    }
  }
  else
  {
    std::string message = "The XYZ axis mode is not set, cannot update position.";
    octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, message);
  }

  if (update_e)
  {
    if (!pos->is_extruder_relative_null)
    {
      if (pos->is_extruder_relative)
      {
        pos->get_current_extruder().e = e + pos->get_current_extruder().e;
      }
      else
      {
        pos->get_current_extruder().e = e + pos->get_current_extruder().e_offset;
      }
    }
    else
    {
      std::string message = "The E axis mode is not set, cannot update position.";
      octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR, message);
    }
  }
}

void gcode_position::process_g0_g1(position* pos, parsed_command& cmd)
{
  bool update_x = false;
  bool update_y = false;
  bool update_z = false;
  bool update_e = false;
  bool update_f = false;
  double x = 0;
  double y = 0;
  double z = 0;
  double e = 0;
  double f = 0;
  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    const parsed_command_parameter p_cur_param = cmd.parameters[index];
    if (p_cur_param.name == "X")
    {
      update_x = true;
      x = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "Y")
    {
      update_y = true;
      y = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "E")
    {
      update_e = true;
      e = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "Z")
    {
      update_z = true;
      z = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "F")
    {
      update_f = true;
      f = p_cur_param.double_value;
    }
  }
  update_position(pos, x, update_x, y, update_y, z, update_z, e, update_e, f, update_f, false, true);
}

void gcode_position::process_g2(position* pos, parsed_command& cmd)
{
  bool update_x = false;
  bool update_y = false;
  bool update_e = false;
  bool update_f = false;
  double x = 0;
  double y = 0;
  double e = 0;
  double f = 0;
  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    const parsed_command_parameter p_cur_param = cmd.parameters[index];
    if (p_cur_param.name == "X")
    {
      update_x = true;
      x = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "Y")
    {
      update_y = true;
      y = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "E")
    {
      update_e = true;
      e = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "F")
    {
      update_f = true;
      f = p_cur_param.double_value;
    }
  }
  update_position(pos, x, update_x, y, update_y, 0, false, e, update_e, f, update_f, false, true);
}

void gcode_position::process_g3(position* pos, parsed_command& cmd)
{
  return process_g2(pos, cmd);
}

void gcode_position::process_g10(position* pos, parsed_command& cmd)
{
  // Take 0 based extruder parameter in account
  int p = 0;
  bool has_p = false;
  double x = 0;
  bool has_x = false;
  double y = 0;
  bool has_y = false;
  double z = 0;
  bool has_z = false;
  double s = 0;
  bool has_s = false;
  // Handle extruder offset commands
  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    parsed_command_parameter p_cur_param = cmd.parameters[index];
    if (p_cur_param.name == "S")
    {
      has_s = true;
      if (p_cur_param.value_type == 'F')
        s = p_cur_param.double_value;
      else
        has_s = false;
    }
    else if (p_cur_param.name == "P")
    {
      has_p = true;
      if (p_cur_param.value_type == 'L')
      {
        p = static_cast<int>(p_cur_param.unsigned_long_value);
      }
      else if (p_cur_param.value_type == 'F')
      {
        double val = p_cur_param.double_value;
        val = val + 0.5 - (val < 0);
        p = static_cast<int>(val);
      }
      else
        has_p = false;
    }
    else if (p_cur_param.name == "X")
    {
      has_x = true;
      if (p_cur_param.value_type == 'F')
        x = p_cur_param.double_value;
      else
        has_x = false;
    }
    else if (p_cur_param.name == "Y")
    {
      has_y = true;
      if (p_cur_param.value_type == 'F')
        y = p_cur_param.double_value;
      else
        has_y = false;
    }
    else if (p_cur_param.name == "Z")
    {
      has_z = true;
      if (p_cur_param.value_type == 'F')
        z = p_cur_param.double_value;
      else
        has_z = false;
    }
  }
  // apply offsets
  if (has_p)
  {
    // Take 0 based extruder parameter in account before setting offsets
    if (!zero_based_extruder_)
    {
      p--;
    }
    if (p < 0)
    {
      p = 0;
      octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                    "GcodePosition.process_g10: Selected tool was less than 0.  Setting offset for tool index 0 instead.");
    }
    else if (p > num_extruders_ - 1)
    {
      p = num_extruders_ - 1;
      octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                    "GcodePosition.process_g10: Selected tool was greater than the number of configured tools.  Setting offset for the maximum tool index instead.");
    }
    if (has_x)
      pos->get_extruder(p).x_firmware_offset = x;
    if (has_y)
      pos->get_extruder(p).y_firmware_offset = y;
    if (has_z)
      pos->get_extruder(p).z_firmware_offset = z;
    return;
  }

  // Todo: add firmware retract here
}

void gcode_position::process_g11(position* pos, parsed_command& cmd)
{
  // Todo: Fix G11
}

void gcode_position::process_g20(position* pos, parsed_command& cmd)
{
}

void gcode_position::process_g21(position* pos, parsed_command& cmd)
{
}

void gcode_position::process_g28(position* pos, parsed_command& cmd)
{
  bool has_x = false;
  bool has_y = false;
  bool has_z = false;
  bool set_x_home = false;
  bool set_y_home = false;
  bool set_z_home = false;

  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    parsed_command_parameter p_cur_param = cmd.parameters[index];
    if (p_cur_param.name == "X")
      has_x = true;
    else if (p_cur_param.name == "Y")
      has_y = true;
    else if (p_cur_param.name == "Z")
      has_z = true;
  }
  if (has_x)
  {
    pos->x_homed = true;
    set_x_home = true;
  }
  if (has_y)
  {
    pos->y_homed = true;
    set_y_home = true;
  }
  if (has_z)
  {
    pos->z_homed = true;
    set_z_home = true;
  }
  if (!has_x && !has_y && !has_z)
  {
    pos->x_homed = true;
    pos->y_homed = true;
    pos->z_homed = true;
    set_x_home = true;
    set_y_home = true;
    set_z_home = true;
  }

  if (set_x_home && !home_x_none_)
  {
    pos->x = home_x_;
    pos->x_null = false;
  }
  // todo: set error flag on else
  if (set_y_home && !home_y_none_)
  {
    pos->y = home_y_;
    pos->y_null = false;
  }
  // todo: set error flag on else
  if (set_z_home && !home_z_none_)
  {
    pos->z = home_z_;
    pos->z_null = false;
  }
  // todo: set error flag on else
}

void gcode_position::process_g90(position* pos, parsed_command& cmd)
{
  // Set xyz to absolute mode
  if (pos->is_relative_null)
    pos->is_relative_null = false;

  pos->is_relative = false;

  if (g90_influences_extruder_)
  {
    // If g90/g91 influences the extruder, set the extruder to absolute mode too
    if (pos->is_extruder_relative_null)
      pos->is_extruder_relative_null = false;

    pos->is_extruder_relative = false;
  }
}

void gcode_position::process_g91(position* pos, parsed_command& cmd)
{
  // Set XYZ axis to relative mode
  if (pos->is_relative_null)
    pos->is_relative_null = false;

  pos->is_relative = true;

  if (g90_influences_extruder_)
  {
    // If g90/g91 influences the extruder, set the extruder to relative mode too
    if (pos->is_extruder_relative_null)
      pos->is_extruder_relative_null = false;

    pos->is_extruder_relative = true;
  }
}

void gcode_position::process_g92(position* pos, parsed_command& cmd)
{
  // Set position offset
  bool update_x = false;
  bool update_y = false;
  bool update_z = false;
  bool update_e = false;
  bool o_exists = false;
  double x = 0;
  double y = 0;
  double z = 0;
  double e = 0;
  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    parsed_command_parameter p_cur_param = cmd.parameters[index];
    if (p_cur_param.name == "X")
    {
      update_x = true;
      x = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "Y")
    {
      update_y = true;
      y = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "E")
    {
      update_e = true;
      e = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "Z")
    {
      update_z = true;
      z = p_cur_param.double_value;
    }
    else if (p_cur_param.name == "O")
    {
      o_exists = true;
    }
  }

  if (o_exists)
  {
    // Our fake O parameter exists, set axis to homed!
    // This is a workaround to allow folks to use octolapse without homing (for shame, lol!)
    pos->x_homed = true;
    pos->y_homed = true;
    pos->z_homed = true;
  }

  if (!o_exists && !update_x && !update_y && !update_z && !update_e)
  {
    if (!pos->x_null)
      pos->x_offset = pos->x + pos->x_firmware_offset;
    if (!pos->y_null)
      pos->y_offset = pos->y + pos->y_firmware_offset;
    if (!pos->z_null)
      pos->z_offset = pos->z + pos->z_firmware_offset;
    // Todo:  Does this reset E too?  Figure that $#$$ out Formerlurker!
    pos->get_current_extruder().e_offset = pos->get_current_extruder().e;
  }
  else
  {
    if (update_x)
    {
      if (!pos->x_null && pos->x_homed)
        pos->x_offset = pos->x - x + pos->x_firmware_offset;
      else
      {
        pos->x = x;
        pos->x_offset = 0;
        pos->x_null = false;
      }
    }
    if (update_y)
    {
      if (!pos->y_null && pos->y_homed)
        pos->y_offset = pos->y - y + pos->y_firmware_offset;
      else
      {
        pos->y = y;
        pos->y_offset = 0;
        pos->y_null = false;
      }
    }
    if (update_z)
    {
      if (!pos->z_null && pos->z_homed)
        pos->z_offset = pos->z - z + pos->z_firmware_offset;
      else
      {
        pos->z = z;
        pos->z_offset = 0;
        pos->z_null = false;
      }
    }
    if (update_e)
    {
      pos->get_current_extruder().e_offset = pos->get_current_extruder().e - e;
    }
  }
}

void gcode_position::process_m82(position* pos, parsed_command& cmd)
{
  // Set extrder mode to absolute
  if (pos->is_extruder_relative_null)
    pos->is_extruder_relative_null = false;

  pos->is_extruder_relative = false;
}

void gcode_position::process_m83(position* pos, parsed_command& cmd)
{
  // Set extrder mode to relative
  if (pos->is_extruder_relative_null)
    pos->is_extruder_relative_null = false;

  pos->is_extruder_relative = true;
}

void gcode_position::process_m207(position* pos, parsed_command& cmd)
{
  // Todo: impemente firmware retract
}

void gcode_position::process_m208(position* pos, parsed_command& cmd)
{
  // Todo: implement firmware retract
}

void gcode_position::process_m218(position* pos, parsed_command& cmd)
{
  // Set hotend offsets
  int t = 0;
  bool has_t = false;
  double x = 0;
  bool has_x = false;
  double y = 0;
  bool has_y = false;
  double z = 0;
  bool has_z = false;
  // Handle extruder offset commands
  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    parsed_command_parameter p_cur_param = cmd.parameters[index];

    if (p_cur_param.name == "T")
    {
      has_t = true;
      if (p_cur_param.value_type == 'L')
      {
        t = static_cast<int>(p_cur_param.unsigned_long_value);
      }
      else if (p_cur_param.value_type == 'F')
      {
        double val = p_cur_param.double_value;
        val = val + 0.5 - (val < 0);
        t = static_cast<int>(val);
      }
      else
        has_t = false;
    }
    else if (p_cur_param.name == "X")
    {
      has_x = true;
      if (p_cur_param.value_type == 'F')
        x = p_cur_param.double_value;
      else
        has_x = false;
    }
    else if (p_cur_param.name == "Y")
    {
      has_y = true;
      if (p_cur_param.value_type == 'F')
        y = p_cur_param.double_value;
      else
        has_y = false;
    }
    else if (p_cur_param.name == "Z")
    {
      has_z = true;
      if (p_cur_param.value_type == 'F')
        z = p_cur_param.double_value;
      else
        has_z = false;
    }
  }
  // apply offsets
  if (has_t)
  {
    // Take 0 based extruder parameter in account before setting offsets
    if (!zero_based_extruder_)
    {
      t--;
    }
    if (t < 0)
    {
      t = 0;
      octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                    "GcodePosition.process_m218: Selected tool was less than 0.  Setting offset for tool index 0 instead.");
    }
    else if (t > num_extruders_ - 1)
    {
      t = num_extruders_ - 1;
      octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                    "GcodePosition.process_m218: Selected tool was greater than the number of configured tools.  Setting offset for the maximum tool index instead.");
    }

    if (has_x)
      pos->get_extruder(t).x_firmware_offset = x;
    if (has_y)
      pos->get_extruder(t).y_firmware_offset = y;
    if (has_z)
      pos->get_extruder(t).z_firmware_offset = z;
    return;
  }
}

void gcode_position::process_m563(position* pos, parsed_command& cmd)
{
  // Todo:  Work on this command, which defines tools and will affect which tool is selected.
}

void gcode_position::process_t(position* pos, parsed_command& cmd)
{
  for (unsigned int index = 0; index < cmd.parameters.size(); index++)
  {
    parsed_command_parameter p_cur_param = cmd.parameters[index];
    if (p_cur_param.name == "T" && p_cur_param.value_type == 'U')
    {
      octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::DEBUG,
                    "GcodePosition.process_t: Tool change Detected.");
      pos->current_tool = static_cast<int>(p_cur_param.unsigned_long_value);
      if (!zero_based_extruder_)
      {
        pos->current_tool--;
      }
      if (pos->current_tool < 0)
      {
        pos->current_tool = 0;
        octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                      "GcodePosition.process_t: The tool index was less than 0.  Setting tool index to 0 instead.");
      }
      else if (pos->current_tool > num_extruders_ - 1)
      {
        pos->current_tool = num_extruders_ - 1;
        octolapse_log(octolapse_log::GCODE_POSITION, octolapse_log::ERROR,
                      "GcodePosition.process_t: The tool index was greater than the number of available tools.  Setting tool index to the max tool index instead.");
      }

      break;
    }
  }
}

gcode_comment_processor* gcode_position::get_gcode_comment_processor()
{
  return &comment_processor_;
}
