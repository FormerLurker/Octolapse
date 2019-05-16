#include "stabilization_minimize_travel.h"
#include <math.h>
#include <iostream>
minimize_travel_args::minimize_travel_args()
{
	x_coordinate_ = 0;
	y_coordinate_ = 0;
	has_py_callbacks_ = false;
	py_get_snapshot_position_callback = NULL;
	py_gcode_generator = NULL;
}

minimize_travel_args::minimize_travel_args(PyObject * gcode_generator, PyObject * get_snapshot_position_callback)
{
	has_py_callbacks_ = true;
	x_coordinate_ = 0;
	y_coordinate_ = 0;
	py_get_snapshot_position_callback = get_snapshot_position_callback;
	py_gcode_generator = gcode_generator;
}
minimize_travel_args::minimize_travel_args(double x, double y)
{
	has_py_callbacks_ = false;
	x_coordinate_ = x;
	y_coordinate_ = y;
	py_get_snapshot_position_callback = NULL;
	py_gcode_generator = NULL;
}
minimize_travel_args::~minimize_travel_args()
{
	if (has_py_callbacks_)
	{
		Py_XDECREF(py_get_snapshot_position_callback);
		Py_XDECREF(py_gcode_generator);
	}
}

stabilization_minimize_travel::stabilization_minimize_travel()
{
	x_coord_ = 0;
	y_coord_ = 0;
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	
	current_closest_dist_ = -1;
	has_saved_position_ = false;
	minimize_travel_args_ = NULL;
	p_saved_position_ = NULL;
}

stabilization_minimize_travel::stabilization_minimize_travel(
	gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, progressCallback progress
) :stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	minimize_travel_args_ = mt_args;
	current_closest_dist_ = -1;
	has_saved_position_ = false; 
	p_saved_position_ = NULL;
	// Get the initial stabilization coordinates
	get_next_xy_coordinates();
}

stabilization_minimize_travel::stabilization_minimize_travel(
	gcode_position_args* position_args, stabilization_args* stab_args, minimize_travel_args* mt_args, pythonGetCoordinatesCallback get_coordinates, pythonProgressCallback progress
) : stabilization(position_args, stab_args, progress)
{
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	_get_coordinates_callback = get_coordinates;
	minimize_travel_args_ = mt_args;
	current_closest_dist_ = -1;
	has_saved_position_ = false;
	p_saved_position_ = NULL;
	// Get the initial stabilization coordinates
	get_next_xy_coordinates();
}

stabilization_minimize_travel::stabilization_minimize_travel(const stabilization_minimize_travel &source)
{

}

stabilization_minimize_travel::~stabilization_minimize_travel()
{
	if (p_saved_position_ != NULL)
	{
		delete p_saved_position_;
		p_saved_position_ = NULL;
	}
}
void stabilization_minimize_travel::get_next_xy_coordinates()
{
	//std::cout << "Getting XY stabilization coordinates...";

	if (minimize_travel_args_->has_py_callbacks_)
	{
		//std::cout << "calling python...";
		_get_coordinates_callback(minimize_travel_args_->py_get_snapshot_position_callback, minimize_travel_args_->x_coordinate_, minimize_travel_args_->y_coordinate_, &x_coord_, &y_coord_);
	}

	else
	{
		//std::cout << "extracting from args...";
		x_coord_ = minimize_travel_args_->x_coordinate_;
		y_coord_ = minimize_travel_args_->y_coordinate_;
	}
	//std::cout << " - X coord: " << x_coord;
	//std::cout << " - Y coord: " << y_coord << "\r\n";
}

void stabilization_minimize_travel::process_pos(position* p_current_pos, position* p_previous_pos)
{
	//std::cout << "StabilizationMinimizeTravel::process_pos - Processing Position...";
	// if we're at a layer change, add the current saved plan
	if (p_current_pos->is_layer_change_ && p_current_pos->layer_ > 1)
	{
		is_layer_change_wait_ = true;
	}

	if (!p_current_pos->is_extruding_ || !p_current_pos->has_xy_position_changed_ || p_current_pos->gcode_ignored_)
	{
		//std::cout << "Complete.\r\n";
		return;
	}

	if (is_layer_change_wait_ && has_saved_position_)
	{
		if (p_stabilization_args_->height_increment_ != 0)
		{
			// todo : improve this check, it doesn't need to be done on every command if Z hasn't changed
			unsigned const int increment = int(p_current_pos->height_ / p_stabilization_args_->height_increment_);

			if (increment > current_height_increment_)
			{
				if (increment > 1 && has_saved_position_)
					add_saved_plan();
				// TODO:  LOG MISSED LAYER
				//else
				//   Log missed layer
				current_height_increment_ = increment;
			}
		}
		else
		{
			add_saved_plan();
		}

	}

	// check for errors in position, layer, or height, and make sure we are extruding.
	if (p_current_pos->layer_ == 0 || p_current_pos->x_null_ || p_current_pos->y_null_ || p_current_pos->z_null_)
	{
		return;
	}

	// Is the endpoint of the current command closer
	// Note that we need to save the position immediately
	// so that the IsCloser check for the previous_pos will
	// have a saved command to check.
	double distance = is_closer(p_current_pos);
	if (distance != -1.0)
	{
		has_saved_position_ = true;
		// delete the current saved position and parsed command
		if (p_saved_position_ != NULL)
		{
			//std::cout << "Deleting saved position.\r\n";
			delete p_saved_position_;
		}
		//std::cout << "Creating new saved position.\r\n";
		p_saved_position_ = new position(*p_current_pos);
		current_closest_dist_ = distance;
	}
	// If the previous command was at the same height, and the extruder is primed, check the starting
	// point of the current command to see if it's closer.
	if (p_previous_pos->is_primed_ && gcode_position::is_equal(p_current_pos->z_, p_previous_pos->z_))
	{
		//std::cout << "Running IsCloser on previous position.\r\n";
		double distance = is_closer(p_previous_pos);
		if (distance != -1.0)
		{
			has_saved_position_ = true;
			// delete the current saved position and parsed command
			if (p_saved_position_ != NULL)
			{
				//std::cout << "Deleting saved position.\r\n";
				delete p_saved_position_;
			}
			//std::cout << "Creating new saved position.\r\n";
			p_saved_position_ = new position(*p_previous_pos);
			current_closest_dist_ = distance;
		}
	}
	//std::cout << "Complete.\r\n";

}

double stabilization_minimize_travel::is_closer(position * p_position)
{
	//std::cout << " - running IsCloser.  Checking bounds...";
	// check the bounding box
	if (p_stabilization_args_->is_bound_)
	{
		if (
			p_position->x_ < p_stabilization_args_->x_min_ ||
			p_position->x_ > p_stabilization_args_->x_max_ ||
			p_position->y_ < p_stabilization_args_->y_min_ ||
			p_position->y_ > p_stabilization_args_->y_max_ ||
			p_position->z_ < p_stabilization_args_->z_min_ ||
			p_position->z_ > p_stabilization_args_->z_max_)
		{
			//std::cout << " - IsCloser Complete, out of bounds.\r\n";
			return -1.0;
		}
	}
	//std::cout << "Checking for saved position...";
	// if we have no saved position, this is the closest!
	if (!has_saved_position_)
	{
		double distance = stabilization::get_carteisan_distance(p_position->x_, p_position->y_, x_coord_, y_coord_);
		if(distance  != -1)
			//std::cout << " - IsCloser Complete, no saved position.\r\n";
		return distance;
	}

	// If the speed is faster than the saved speed, this is the closest point
	if (p_stabilization_args_->fastest_speed_)
	{
		//std::cout << "Checking for faster speed...";
		if (gcode_position::greater_than(p_position->f_, p_saved_position_->f_))
		{
			//std::cout << " - IsCloser Complete, faster.\r\n";
			double distance = stabilization::get_carteisan_distance(p_position->x_, p_position->y_, x_coord_, y_coord_);
			if (distance != -1)
				//std::cout << " - IsCloser Complete, no saved position.\r\n";
			return distance;
		}
		else if (gcode_position::less_than(p_position->f_, p_saved_position_->f_))
		{
			//std::cout << " - IsCloser Complete, curspeed too slow.\r\n";
			return -1.0;
		}
		//std::cout << "No faster speed found...";
	}
	//std::cout << "Checking for closer position...";
	// Compare the saved points cartesian distance from the current point
	double distance = stabilization::get_carteisan_distance(p_position->x_, p_position->y_, x_coord_, y_coord_);
	if (distance != -1.0 && (current_closest_dist_ < 0 || gcode_position::greater_than(current_closest_dist_, distance)))
	{
		//std::cout << " - IsCloser Complete, closer.\r\n";
		return distance;
	}
	
	//std::cout << " - IsCloser Complete, not closer.\r\n";
	return -1.0;
}

void stabilization_minimize_travel::add_saved_plan()
{
	//std::cout << "Adding saved plan to plans...";
	snapshot_plan* p_plan = new snapshot_plan();

	// create the initial position
	p_plan->p_initial_position_ = new position(*p_saved_position_);
	// create the snapshot position (only 1)
	position * p_snapshot_position = new position(*p_saved_position_);
	p_snapshot_position->x_ = x_coord_;
	p_snapshot_position->y_ = y_coord_;
	
	p_plan->snapshot_positions_.push_back(p_snapshot_position);
	p_plan->p_return_position_ = new position(*p_saved_position_);
	p_plan->p_parsed_command_ = new parsed_command(*p_saved_position_->p_command);

	p_plan->file_line_ = p_saved_position_->file_line_number_;
	p_plan->file_gcode_number_ = p_saved_position_->gcode_number_;
	// Need to enter lift and retract amounts!
	p_plan->lift_amount_ = p_stabilization_args_->z_lift_height_;
	p_plan->retract_amount_ = p_stabilization_args_->retraction_length_;
	std::cout << "Adding retraction length: " << p_stabilization_args_->z_lift_height_ << "\r\n";
	p_plan->send_parsed_command_ = send_parsed_command_first;

	snapshot_plan_step* p_travel_step = new snapshot_plan_step(x_coord_, y_coord_, 0, 0, 0, travel_action);
	p_plan->steps_.push_back(p_travel_step);
	snapshot_plan_step* p_snapshot_step = new snapshot_plan_step(0, 0, 0, 0, 0, snapshot_action);
	p_plan->steps_.push_back(p_snapshot_step);

	// Add the plan
	p_snapshot_plans_->push_back(p_plan);

	current_height_ = p_saved_position_->height_;
	current_layer_ = p_saved_position_->layer_;
	// set the state for the next layer
	has_saved_position_ = false;
	is_layer_change_wait_ = false;
	delete p_saved_position_;
	p_saved_position_ = NULL;

	current_closest_dist_ = -1.0;
	get_next_xy_coordinates();
	//std::cout << "Complete.\r\n";
}

void stabilization_minimize_travel::on_processing_complete()
{
	//std::cout << "Running on_process_complete...";
	if (has_saved_position_)
	{
		add_saved_plan();
	}
	//std::cout << "Complete.\r\n";
}