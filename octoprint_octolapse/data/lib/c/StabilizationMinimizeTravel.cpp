#include "StabilizationMinimizeTravel.h"
#include <math.h>
#include <iostream>
minimize_travel_args::minimize_travel_args()
{
	x_coordinate = 0;
	y_coordinate = 0;
	has_py_callbacks = false;
	py_get_snapshot_position_callback = NULL;
	py_gcode_generator = NULL;
}

minimize_travel_args::minimize_travel_args(PyObject * gcode_generator, PyObject * get_snapshot_position_callback)
{
	has_py_callbacks = true;
	x_coordinate = 0;
	y_coordinate = 0;
	py_get_snapshot_position_callback = get_snapshot_position_callback;
	py_gcode_generator = gcode_generator;
}
minimize_travel_args::minimize_travel_args(double x, double y)
{
	has_py_callbacks = false;
	x_coordinate = x;
	y_coordinate = y;
	py_get_snapshot_position_callback = NULL;
	py_gcode_generator = NULL;
}
minimize_travel_args::~minimize_travel_args()
{
	/*if (has_py_callbacks)
	{
		Py_XDECREF(py_get_snapshot_position_callback);
		Py_XDECREF(py_gcode_generator);
	}*/
}

StabilizationMinimizeTravel::StabilizationMinimizeTravel()
{
	x_coord = 0;
	y_coord = 0;
	is_layer_change_wait = false;
	current_layer = 0;
	current_height = 0.0;
	current_height_increment = 0;
	
	current_closest_dist = -1;
	has_saved_position = false;
	_minimize_travel_args = NULL;
	p_saved_position = NULL;
}

StabilizationMinimizeTravel::StabilizationMinimizeTravel(
	gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, progressCallback progress
) :stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait = false;
	current_layer = 0;
	current_height = 0.0;
	current_height_increment = 0;
	_minimize_travel_args = mt_args;
	current_closest_dist = -1;
	has_saved_position = false; 
	p_saved_position = NULL;
	// Get the initial stabilization coordinates
	get_next_xy_coordinates();
}

StabilizationMinimizeTravel::StabilizationMinimizeTravel(
	gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
) : stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait = false;
	current_layer = 0;
	current_height = 0.0;
	current_height_increment = 0;
	_get_coordinates_callback = get_coordinates;
	_minimize_travel_args = mt_args;
	current_closest_dist = -1;
	has_saved_position = false;
	p_saved_position = NULL;
	// Get the initial stabilization coordinates
	get_next_xy_coordinates();
}

StabilizationMinimizeTravel::StabilizationMinimizeTravel(const StabilizationMinimizeTravel &source)
{

}

StabilizationMinimizeTravel::~StabilizationMinimizeTravel()
{
	if (p_saved_position != NULL)
	{
		delete p_saved_position;
		p_saved_position = NULL;
	}
}
void StabilizationMinimizeTravel::get_next_xy_coordinates()
{
	//std::cout << "Getting XY stabilization coordinates...";

	if (_minimize_travel_args->has_py_callbacks)
	{
		//std::cout << "calling python...";
		_get_coordinates_callback(_minimize_travel_args->py_get_snapshot_position_callback, _minimize_travel_args->x_coordinate, _minimize_travel_args->y_coordinate, &x_coord, &y_coord);
	}

	else
	{
		//std::cout << "extracting from args...";
		x_coord = _minimize_travel_args->x_coordinate;
		y_coord = _minimize_travel_args->y_coordinate;
	}
	//std::cout << " - X coord: " << x_coord;
	//std::cout << " - Y coord: " << y_coord << "\r\n";
}

void StabilizationMinimizeTravel::process_pos(position* p_current_pos, position* p_previous_pos)
{
	//std::cout << "StabilizationMinimizeTravel::process_pos - Processing Position...";
	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change && p_current_pos->layer > 1)
	{
		is_layer_change_wait = true;
	}

	if (!p_current_pos->is_extruding || !p_current_pos->has_xy_position_changed)
	{
		//std::cout << "Complete.\r\n";
		return;
	}

	if (is_layer_change_wait && has_saved_position)
	{
		if (p_stabilization_args_->height_increment != 0)
		{
			// todo : improve this check, it doesn't need to be done on every command if Z hasn't changed
			unsigned const int increment = int(p_current_pos->height / p_stabilization_args_->height_increment);

			if (increment > current_height_increment)
			{
				if (increment > 1 && has_saved_position)
					AddSavedPlan();
				// TODO:  LOG MISSED LAYER
				//else
				//   Log missed layer
				current_height_increment = increment;
			}
		}
		else
		{
			AddSavedPlan();
		}

	}

	// check for errors in position, layer, or height, and make sure we are extruding.
	if (p_current_pos->layer == 0 || p_current_pos->x_null || p_current_pos->y_null || p_current_pos->z_null)
	{
		return;
	}

	// Is the endpoint of the current command closer
	// Note that we need to save the position immediately
	// so that the IsCloser check for the previous_pos will
	// have a saved command to check.
	double distance = IsCloser(p_current_pos);
	if (distance != -1.0)
	{
		has_saved_position = true;
		// delete the current saved position and parsed command
		if (p_saved_position != NULL)
		{
			//std::cout << "Deleting saved position.\r\n";
			delete p_saved_position;
		}
		//std::cout << "Creating new saved position.\r\n";
		p_saved_position = new position(*p_current_pos);
		current_closest_dist = distance;
	}
	// If the previous command was at the same height, and the extruder is primed, check the starting
	// point of the current command to see if it's closer.
	if (p_previous_pos->is_primed && gcode_position::is_equal(p_current_pos->z, p_previous_pos->z))
	{
		//std::cout << "Running IsCloser on previous position.\r\n";
		double distance = IsCloser(p_previous_pos);
		if (distance != -1.0)
		{
			has_saved_position = true;
			// delete the current saved position and parsed command
			if (p_saved_position != NULL)
			{
				//std::cout << "Deleting saved position.\r\n";
				delete p_saved_position;
			}
			//std::cout << "Creating new saved position.\r\n";
			p_saved_position = new position(*p_previous_pos);
			current_closest_dist = distance;
		}
	}
	//std::cout << "Complete.\r\n";

}

double StabilizationMinimizeTravel::IsCloser(position * p_position)
{
	//std::cout << " - running IsCloser.  Checking bounds...";
	// check the bounding box
	if (p_stabilization_args_->is_bound)
	{
		if (
			p_position->x < p_stabilization_args_->x_min ||
			p_position->x > p_stabilization_args_->x_max ||
			p_position->y < p_stabilization_args_->y_min ||
			p_position->y > p_stabilization_args_->y_max ||
			p_position->z < p_stabilization_args_->z_min ||
			p_position->z > p_stabilization_args_->z_max)
		{
			//std::cout << " - IsCloser Complete, out of bounds.\r\n";
			return -1.0;
		}
	}
	//std::cout << "Checking for saved position...";
	// if we have no saved position, this is the closest!
	if (!has_saved_position)
	{
		double distance = stabilization::get_carteisan_distance(p_position->x, p_position->y, x_coord, y_coord);
		if(distance  != -1)
			//std::cout << " - IsCloser Complete, no saved position.\r\n";
		return distance;
	}

	// If the speed is faster than the saved speed, this is the closest point
	if (p_stabilization_args_->fastest_speed)
	{
		//std::cout << "Checking for faster speed...";
		if (gcode_position::greater_than(p_position->f, p_saved_position->f))
		{
			//std::cout << " - IsCloser Complete, faster.\r\n";
			double distance = stabilization::get_carteisan_distance(p_position->x, p_position->y, x_coord, y_coord);
			if (distance != -1)
				//std::cout << " - IsCloser Complete, no saved position.\r\n";
			return distance;
		}
		else if (gcode_position::less_than(p_position->f, p_saved_position->f))
		{
			//std::cout << " - IsCloser Complete, curspeed too slow.\r\n";
			return -1.0;
		}
		//std::cout << "No faster speed found...";
	}
	//std::cout << "Checking for closer position...";
	// Compare the saved points cartesian distance from the current point
	double distance = stabilization::get_carteisan_distance(p_position->x, p_position->y, x_coord, y_coord);
	if (distance != -1.0 && (current_closest_dist < 0 || gcode_position::greater_than(current_closest_dist, distance)))
	{
		//std::cout << " - IsCloser Complete, closer.\r\n";
		return distance;
	}
	
	//std::cout << " - IsCloser Complete, not closer.\r\n";
	return -1.0;
}

void StabilizationMinimizeTravel::AddSavedPlan()
{
	//std::cout << "Adding saved plan to plans...";
	snapshot_plan* p_plan = new snapshot_plan();

	// create the initial position
	p_plan->p_initial_position = new position(*p_saved_position);
	// create the snapshot position (only 1)
	position * p_snapshot_position = new position(*p_saved_position);
	p_snapshot_position->x = x_coord;
	p_snapshot_position->y = y_coord;
	p_plan->snapshot_positions.push_back(p_snapshot_position);
	p_plan->p_return_position = new position(*p_saved_position);
	p_plan->p_parsed_command = new parsed_command(*p_saved_position->p_command);

	p_plan->file_line = p_saved_position->file_line_number;
	p_plan->file_gcode_number = p_saved_position->gcode_number;
	p_plan->lift_amount = p_stabilization_args_->disable_z_lift ? 0.0 : p_stabilization_args_->z_lift_height;
	p_plan->retract_amount = p_stabilization_args_->disable_retract ? 0.0 : p_stabilization_args_->retraction_length;
	p_plan->send_parsed_command = send_parsed_command_first;

	snapshot_plan_step* p_travel_step = new snapshot_plan_step(x_coord, y_coord, 0, 0, 0, travel_action);
	p_plan->steps.push_back(p_travel_step);
	snapshot_plan_step* p_snapshot_step = new snapshot_plan_step(0, 0, 0, 0, 0, snapshot_action);
	p_plan->steps.push_back(p_snapshot_step);

	// Add the plan
	p_snapshot_plans->push_back(p_plan);

	current_height = p_saved_position->height;
	current_layer = p_saved_position->layer;
	// set the state for the next layer
	has_saved_position = false;
	is_layer_change_wait = false;
	delete p_saved_position;
	p_saved_position = NULL;

	current_closest_dist = -1.0;
	get_next_xy_coordinates();
	//std::cout << "Complete.\r\n";
}

void StabilizationMinimizeTravel::on_processing_complete()
{
	//std::cout << "Running on_process_complete...";
	if (has_saved_position)
	{
		AddSavedPlan();
	}
	//std::cout << "Complete.\r\n";
}