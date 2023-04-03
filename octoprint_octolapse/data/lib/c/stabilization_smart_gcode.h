#pragma once
#include "stabilization.h"
#include "parsed_command.h"
#include "parsed_command_parameter.h"
static const char* SMART_GCODE_STABILIZATION = "smart_gcode";

struct smart_gcode_args
{
  smart_gcode_args()
  {
  }
};

class stabilization_smart_gcode :
  public stabilization
{
public:
  stabilization_smart_gcode();
  stabilization_smart_gcode(gcode_position_args position_args, stabilization_args stab_args, smart_gcode_args mt_args,
                            progressCallback progress);
  stabilization_smart_gcode(gcode_position_args position_args, stabilization_args stab_args, smart_gcode_args mt_args,
                            pythonGetCoordinatesCallback get_coordinates, PyObject* py_get_coordinates_callback,
                            pythonProgressCallback progress, PyObject* py_progress_callback);
  virtual ~stabilization_smart_gcode();
private:
  static std::string default_snapshot_gcode_;
  stabilization_smart_gcode(const stabilization_smart_gcode& source); // don't copy me
  void process_pos(position* p_current_pos, position* p_previous_pos, bool found_command) override;
  void on_processing_complete() override;
  std::vector<stabilization_quality_issue> get_quality_issues() override;
  std::vector<stabilization_processing_issue> get_internal_processing_issues() override;
  smart_gcode_args smart_gcode_args_;
  int snapshot_commands_found_;
  
};
