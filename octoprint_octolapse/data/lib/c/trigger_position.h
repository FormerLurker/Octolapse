#pragma once
#include "position.h"
#include "gcode_comment_processor.h"

/**
 * \brief A struct to hold the closest position, which  is used by the stabilization preprocessors.
 */
static const std::string position_type_name[14] = {
  "unknown",
  "extrusion",
  "lifting",
  "lifted",
  "travel",
  "lifting_travel",
  "lifted_travel",
  "retraction",
  "retracted_lifting",
  "retracted_lifted",
  "retracted_travel",
  "lifting_retracted_travel",
  "lifted_retracted_travel",
  "fastest_extrusion"
};

enum trigger_type
{
  trigger_type_snap_to_print,
  trigger_type_fast,
  trigger_type_compatibility,
  trigger_type_high_quality
};

enum position_type
{
  position_type_unknown,
  position_type_extrusion,
  position_type_lifting,
  position_type_lifted,
  position_type_travel,
  position_type_lifting_travel,
  position_type_lifted_travel,
  position_type_retraction,
  position_type_retracted_lifting,
  position_type_retracted_lifted,
  position_type_retracted_travel,
  position_type_lifting_retracted_travel,
  position_type_lifted_retracted_travel,
  position_type_fastest_extrusion
};

struct trigger_position
{
  /**
   * \brief The type of trigger position to use when creating snapshot plans\n
   * fastest - Gets the closest position\n
   * compatibility - Gets the best quality position available.
   * high_quality - Gets the best quality position availiable, but stops searching after the quality_cutoff (retraction)
   */

  static const unsigned int num_position_types = 14;
  static const position_type quality_cutoff = position_type_retraction;

  trigger_position()
  {
    type_position = position_type_unknown;
    distance = -1;
    is_empty = true;
    type_feature = feature_type_unknown_feature;
  }

  trigger_position(position_type type_, double distance_, position pos_)
  {
    type_position = type_;
    distance = distance_;
    pos = pos_;
    is_empty = false;
    type_feature = feature_type_unknown_feature;
  }

  trigger_position(feature_type feature_, double distance_, position pos_)
  {
    type_position = position_type_unknown;
    distance = distance_;
    pos = pos_;
    is_empty = false;
    type_feature = feature_;
  }

  static position_type get_type(position* p_pos);
  position_type type_position;
  feature_type type_feature;
  double distance;
  position pos;
  bool is_empty;
};

struct trigger_position_args
{
public:
  trigger_position_args()
  {
    type = trigger_type_compatibility;
    minimum_speed = 0;
    snap_to_print_high_quality = false;
    x_stabilization_disabled = true;
    y_stabilization_disabled = true;
  }

  trigger_type type;
  double minimum_speed;
  bool snap_to_print_high_quality;
  bool x_stabilization_disabled;
  bool y_stabilization_disabled;
};

class trigger_positions
{
public:
  trigger_positions();
  ~trigger_positions();
  bool get_position(trigger_position& pos);

  void initialize(trigger_position_args args);
  void clear();
  void try_add(position* p_current_pos, position* p_previous_pos);
  bool is_empty() const;
  trigger_position get(position_type type);
  void set_stabilization_coordinates(double x, double y);
  void set_previous_initial_position(position& pos);
private:
  bool has_fastest_extrusion_position() const;
  bool get_snap_to_print_position(trigger_position& pos);
  bool get_fast_position(trigger_position& pos);
  bool get_compatibility_position(trigger_position& pos);
  bool get_high_quality_position(trigger_position& pos);

  double get_stabilization_distance(position* p_pos) const;

  //trigger_position* get_normal_quality_position();
  void try_save_retracted_position(position* p_current_pos);
  void try_save_primed_position(position* p_current_pos);
  static bool can_process_position(position* pos, position_type type);
  void add_internal(position* p_pos, double distance, position_type type);
  void try_add_feature_position_internal(position* p_pos);
  void add_feature_position_internal(position* p_pos, double distance, feature_type type);
  void try_add_internal(position* p_pos, double distance, position_type type);
  void try_add_extrusion_start_positions(position* p_extrusion_start_pos);
  void try_add_extrusion_start_position(position* p_extrusion_start_pos, position& saved_pos);

  trigger_position position_list_[trigger_position::num_position_types];
  trigger_position feature_position_list_[NUM_FEATURE_TYPES];
  // arguments
  trigger_position_args args_;
  double stabilization_x_;
  double stabilization_y_;
  // Tracking variables
  double fastest_extrusion_speed_;
  double slowest_extrusion_speed_;
  position previous_initial_pos_;
  position previous_retracted_pos_;
  position previous_primed_pos_;
};
