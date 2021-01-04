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
#include "snapshot_plan_step.h"
#include "python_helpers.h"
#include "logging.h"

snapshot_plan_step::snapshot_plan_step()
{
  p_x = NULL;
  p_y = NULL;
  p_z = NULL;
  p_e = NULL;
  p_f = NULL;
  action = "";
}

snapshot_plan_step::snapshot_plan_step(const snapshot_plan_step& source)
{
  if (source.p_x != NULL)
  {
    p_x = new double;
    *p_x = *source.p_x;
  }
  else
  {
    p_x = NULL;
  }

  if (source.p_y != NULL)
  {
    p_y = new double;
    *p_y = *source.p_y;
  }
  else
  {
    p_y = NULL;
  }


  if (source.p_z != NULL)
  {
    p_z = new double;
    *p_z = *source.p_z;
  }
  else
  {
    p_z = NULL;
  }

  if (source.p_e != NULL)
  {
    p_e = new double;
    *p_e = *source.p_e;
  }
  else
  {
    p_e = NULL;
  }

  if (source.p_f != NULL)
  {
    p_f = new double;
    *p_f = *source.p_f;
  }
  else
  {
    p_f = NULL;
  }

  action = source.action;
}

snapshot_plan_step::snapshot_plan_step(double* x, double* y, double* z, double* e, double* f, std::string action_type)
{
  if (x != NULL)
  {
    p_x = new double;
    *p_x = *x;
  }
  else
  {
    p_x = NULL;
  }

  if (y != NULL)
  {
    p_y = new double;
    *p_y = *y;
  }
  else
  {
    p_y = NULL;
  }


  if (z != NULL)
  {
    p_z = new double;
    *p_z = *z;
  }
  else
  {
    p_z = NULL;
  }

  if (e != NULL)
  {
    p_e = new double;
    *p_e = *e;
  }
  else
  {
    p_e = NULL;
  }

  if (f != NULL)
  {
    p_f = new double;
    *p_f = *f;
  }
  else
  {
    p_f = NULL;
  }

  action = action_type;
}

snapshot_plan_step::~snapshot_plan_step()
{
  if (p_x != NULL)
  {
    delete p_x;
    p_x = NULL;
  }
  if (p_y != NULL)
  {
    delete p_y;
    p_y = NULL;
  }
  if (p_z != NULL)
  {
    delete p_z;
    p_z = NULL;
  }
  if (p_e != NULL)
  {
    delete p_e;
    p_e = NULL;
  }
  if (p_f != NULL)
  {
    delete p_f;
    p_f = NULL;
  }
}

PyObject* snapshot_plan_step::to_py_object() const
{
  PyObject* py_x;
  if (p_x == NULL)
  {
    py_x = Py_None;
    Py_IncRef(py_x);
  }
  else
  {
    py_x = PyFloat_FromDouble(*p_x);
  }
  if (py_x == NULL)
  {
    std::string message = "snapshot_plan_step.to_py_object: Unable to convert the X value to a python object.";
    octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
    return NULL;
  }

  PyObject* py_y;
  if (p_y == NULL)
  {
    py_y = Py_None;
    Py_IncRef(py_y);
  }
  else
  {
    py_y = PyFloat_FromDouble(*p_y);
  }
  if (py_y == NULL)
  {
    std::string message = "snapshot_plan_step.to_py_object: Unable to convert the Y value to a python object.";
    octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
    return NULL;
  }

  PyObject* py_z;
  if (p_z == NULL)
  {
    py_z = Py_None;
    Py_IncRef(py_z);
  }
  else
  {
    py_z = PyFloat_FromDouble(*p_z);
  }
  if (py_z == NULL)
  {
    std::string message = "snapshot_plan_step.to_py_object: Unable to convert the Z value to a python object.";
    octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
    return NULL;
  }

  PyObject* py_e;
  if (p_e == NULL)
  {
    py_e = Py_None;
    Py_IncRef(py_e);
  }
  else
  {
    py_e = PyFloat_FromDouble(*p_e);
  }
  if (py_e == NULL)
  {
    std::string message = "snapshot_plan_step.to_py_object: Unable to convert the E value to a python object.";
    octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
    return NULL;
  }

  PyObject* py_f;
  if (p_f == NULL)
  {
    py_f = Py_None;
    Py_IncRef(py_f);
  }
  else
  {
    py_f = PyFloat_FromDouble(*p_f);
  }
  if (py_f == NULL)
  {
    std::string message = "snapshot_plan_step.to_py_object: Unable to convert the F value to a python object.";
    octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
    return NULL;
  }

  PyObject* py_step = Py_BuildValue("sOOOOO", action.c_str(), py_x, py_y, py_z, py_e, py_f);
  if (py_step == NULL)
  {
    std::string message = "snapshot_plan_step.to_py_object: Unable to create the snapshot plan step PyObject.";
    octolapse_log_exception(octolapse_log::SNAPSHOT_PLAN, message);
    return NULL;
  }
  Py_DecRef(py_x);
  Py_DecRef(py_y);
  Py_DecRef(py_z);
  Py_DecRef(py_e);
  Py_DecRef(py_f);
  return py_step;
}
