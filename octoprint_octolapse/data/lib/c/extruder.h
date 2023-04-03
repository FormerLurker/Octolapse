#pragma once
#ifdef _DEBUG
//#undef _DEBUG
#include <Python.h>
//python311_d.lib
#else
#include <Python.h>
#endif
struct extruder
{
  extruder();
  double x_firmware_offset;
  double y_firmware_offset;
  double z_firmware_offset;
  double e;
  double e_offset;
  double e_relative;
  double extrusion_length;
  double extrusion_length_total;
  double retraction_length;
  double deretraction_length;
  bool is_extruding_start;
  bool is_extruding;
  bool is_primed;
  bool is_retracting_start;
  bool is_retracting;
  bool is_retracted;
  bool is_partially_retracted;
  bool is_deretracting_start;
  bool is_deretracting;
  bool is_deretracted;
  double get_offset_e() const;
  PyObject* to_py_tuple() const;
  PyObject* to_py_dict() const;
  static PyObject* build_py_object(extruder* p_extruders, unsigned int num_extruders);
};
