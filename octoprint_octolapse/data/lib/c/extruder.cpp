#include "extruder.h"
#include "logging.h"

extruder::extruder()
{
  x_firmware_offset = 0;
  y_firmware_offset = 0;
  z_firmware_offset = 0;
  e = 0;
  e_offset = 0;
  e_relative = 0;
  extrusion_length = 0;
  extrusion_length_total = 0;
  retraction_length = 0;
  deretraction_length = 0;
  is_extruding_start = false;
  is_extruding = false;
  is_primed = false;
  is_retracting_start = false;
  is_retracting = false;
  is_retracted = false;
  is_partially_retracted = false;
  is_deretracting_start = false;
  is_deretracting = false;
  is_deretracted = false;
}

double extruder::get_offset_e() const
{
  return e - e_offset;
}

PyObject* extruder::to_py_tuple() const
{
  //std::cout << "Building extruder py_tuple.\r\n";
  PyObject* py_extruder = Py_BuildValue(
    // ReSharper disable once StringLiteralTypo
    "ddddddddddllllllllll",
    // Floats
    x_firmware_offset, // 0
    y_firmware_offset, // 1
    z_firmware_offset, // 2
    e, // 3
    e_offset, // 4
    e_relative, // 5
    extrusion_length, // 6
    extrusion_length_total, // 7
    retraction_length, // 8
    deretraction_length, // 9
    // Bool (represented as an integer)
    (long int)(is_extruding_start ? 1 : 0), // 10
    (long int)(is_extruding ? 1 : 0), // 11
    (long int)(is_primed ? 1 : 0), // 12
    (long int)(is_retracting_start ? 1 : 0), // 13
    (long int)(is_retracting ? 1 : 0), // 14
    (long int)(is_retracted ? 1 : 0), // 15
    (long int)(is_partially_retracted ? 1 : 0), // 16
    (long int)(is_deretracting_start ? 1 : 0), // 17
    (long int)(is_deretracting ? 1 : 0), // 18
    (long int)(is_deretracted ? 1 : 0) // 19
  );
  if (py_extruder == NULL)
  {
    std::string message =
      "extruder.to_py_tuple: Unable to convert extruder value to a PyObject tuple via Py_BuildValue.";
    octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
    return NULL;
  }
  return py_extruder;
}

PyObject* extruder::to_py_dict() const
{
  PyObject* p_extruder = Py_BuildValue(
    "{s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:d,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i,s:i}",
    // FLOATS
    "x_firmware_offset",
    x_firmware_offset,
    "y_firmware_offset",
    y_firmware_offset,
    "z_firmware_offset",
    z_firmware_offset,
    "e",
    e,
    "e_offset",
    e_offset,
    "e_relative",
    e_relative,
    "extrusion_length",
    extrusion_length,
    "extrusion_length_total",
    extrusion_length_total,
    "retraction_length",
    retraction_length,
    "deretraction_length",
    deretraction_length,
    // Bool (represented as an integer)
    "is_extruding_start",
    (long int)(is_extruding_start ? 1 : 0),
    "is_extruding",
    (long int)(is_extruding ? 1 : 0),
    "is_primed",
    (long int)(is_primed ? 1 : 0),
    "is_retracting_start",
    (long int)(is_retracting_start ? 1 : 0),
    "is_retracting",
    (long int)(is_retracting ? 1 : 0),
    "is_retracted",
    (long int)(is_retracted ? 1 : 0),
    "is_partially_retracted",
    (long int)(is_partially_retracted ? 1 : 0),
    "is_deretracting_start",
    (long int)(is_deretracting_start ? 1 : 0),
    "is_deretracting",
    (long int)(is_deretracting ? 1 : 0),
    "is_deretracted",
    (long int)(is_deretracted ? 1 : 0)
  );
  if (p_extruder == NULL)
  {
    std::string message = "extruder.to_py_dict: Unable to convert extruder value to a dict PyObject via Py_BuildValue.";
    octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
    return NULL;
  }
  return p_extruder;
}

PyObject* extruder::build_py_object(extruder* p_extruders, const unsigned int num_extruders)
{
  //std::cout << "Building extruders py_object.\r\n";
  PyObject* py_extruders = PyList_New(0);
  if (py_extruders == NULL)
  {
    std::string message = "Error executing Extruder.build_py_object: Unable to create Extruder PyList object.";
    octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
    return NULL;
  }

  // Create each snapshot plan
  for (unsigned int index = 0; index < num_extruders; index++)
  {
    PyObject* py_extruder = p_extruders[index].to_py_tuple();
    if (py_extruder == NULL)
    {
      return NULL;
    }
    bool success = !(PyList_Append(py_extruders, py_extruder) < 0); // reference to pSnapshotPlan stolen
    if (!success)
    {
      std::string message =
        "Error executing Extruder.build_py_object Unable to append the extruder to the extruders list.";
      octolapse_log_exception(octolapse_log::GCODE_POSITION, message);
      return NULL;
    }
    // Need to decref after PyList_Append, since it increfs the PyObject
    Py_DECREF(py_extruder);
  }

  return py_extruders;
}
