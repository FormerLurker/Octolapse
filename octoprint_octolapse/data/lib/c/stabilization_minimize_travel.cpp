#include "stabilization_minimize_travel.h"
#include "utilities.h"
#include "logging.h"
#include <iostream>
minimize_travel_args::minimize_travel_args()
{
	x_coordinate_ = 0;
	y_coordinate_ = 0;
	py_get_snapshot_position_callback = NULL;
	py_gcode_generator = NULL;
}

minimize_travel_args::minimize_travel_args(PyObject * gcode_generator, PyObject * get_snapshot_position_callback)
{
	x_coordinate_ = 0;
	y_coordinate_ = 0;
	py_get_snapshot_position_callback = get_snapshot_position_callback;
	py_gcode_generator = gcode_generator;
}
minimize_travel_args::minimize_travel_args(double x, double y)
{
	x_coordinate_ = x;
	y_coordinate_ = y;
	py_get_snapshot_position_callback = NULL;
	py_gcode_generator = NULL;
}
minimize_travel_args::~minimize_travel_args()
{
	if(py_get_snapshot_position_callback != NULL)
		Py_XDECREF(py_get_snapshot_position_callback);
	if(py_gcode_generator != NULL)
		Py_XDECREF(py_gcode_generator);
	
}

stabilization_minimize_travel::stabilization_minimize_travel()
{
	stabilization_x_ = 0;
	stabilization_y_ = 0;
	is_layer_change_wait_ = false;
	current_layer_ = 0;
	current_height_ = 0.0;
	current_height_increment_ = 0;
	
	current_closest_dist_ = -1;
	has_saved_position_ = false;
	minimize_travel_args_ = NULL;
	p_saved_position_ = NULL;
	has_python_coordinate_callback = true;
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
	has_python_coordinate_callback = false;
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
	has_python_coordinate_callback = true;
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

	if (has_python_coordinate_callback)
	{
		//std::cout << "calling python...";
		if(!_get_coordinates_callback(minimize_travel_args_->py_get_snapshot_position_callback, minimize_travel_args_->x_coordinate_, minimize_travel_args_->y_coordinate_, &stabilization_x_, &stabilization_y_))
			octolapse_log(SNAPSHOT_PLAN, INFO, "Failed dto get snapshot coordinates.");
	}

	else
	{
		//std::cout << "extracting from args...";
		stabilization_x_ = minimize_travel_args_->x_coordinate_;
		stabilization_y_ = minimize_travel_args_->y_coordinate_;
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

	if (!p_current_pos->is_extruding_ || !p_current_pos->has_xy_position_changed_ || p_current_pos->gcode_ignored_ || !p_current_pos->is_in_bounds_)
	{
		return;
	}

	if (is_layer_change_wait_ && has_saved_position_)
	{
		if (p_stabilization_args_->height_increment_ != 0)
		{
			// todo : improve this check, it doesn't need to be done on every command if Z hasn't changed
			const double increment_double = p_current_pos->last_extrusion_height_ / p_stabilization_args_->height_increment_;
			unsigned const int increment = utilities::round_up_to_int(increment_double);
			if (increment > current_height_increment_)
			{
				if (increment > 1.0 && has_saved_position_)
				{
					current_height_increment_ = increment;
					add_saved_plan();
				}
				else
				{
					octolapse_log(octolapse_loggers::SNAPSHOT_PLAN, octolapse_log_levels::WARNING, "Octolapse missed a layer while creating a snapshot plan due to a height restriction.");
				}
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
		delete_saved_wipe_steps();
		get_current_wipe_steps(saved_wipe_steps_);
	}
	
	// If the previous command was at the same height, and the extruder is primed, check the starting
	// point of the current command to see if it's closer.
	if (p_previous_pos->is_primed_ && utilities::is_equal(p_current_pos->z_, p_previous_pos->z_))
	{
		//std::cout << "Running IsCloser on previous position.\r\n";
		double distance = is_closer(p_previous_pos);
		if (distance != -1.0)
		{
			//std::cout << "Previous position is closer!\r\n";
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
			delete_saved_wipe_steps();
			get_previous_wipe_steps(saved_wipe_steps_);
		}
	}
	//std::cout << "Complete.\r\n";

}

double stabilization_minimize_travel::is_closer(position * p_position)
{
	
	//std::cout << "Checking for saved position...";
	// if we have no saved position, this is the closest!
	if (!has_saved_position_)
	{
		double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
		if(distance  != -1)
			//std::cout << " - IsCloser Complete, no saved position.\r\n";
		return distance;
	}

	// If the speed is faster than the saved speed, this is the closest point
	if (p_stabilization_args_->fastest_speed_)
	{
		//std::cout << "Checking for faster speed than " << p_saved_position_->f_;
		if (utilities::greater_than(p_position->f_, p_saved_position_->f_))
		{
			//std::cout << " - IsCloser Complete, " << p_position->f_ << " is faster than " << p_saved_position_->f_ << "\r\n";
			double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
			if (distance > -1)
				return distance;
		}
		else if (utilities::less_than(p_position->f_, p_saved_position_->f_))
		{
			//std::cout << " - IsCloser Complete, " << p_position->f_ << " too slow.\r\n";"COMP
			return -1.0;
		}
		//std::cout << "\r\n";
		
	}
	//std::cout << "Checking for closer position...";
	// Compare the saved points cartesian distance from the current point
	double distance = utilities::get_cartesian_distance(p_position->x_, p_position->y_, stabilization_x_, stabilization_y_);
	if (distance != -1.0 && (current_closest_dist_ < 0 || utilities::greater_than(current_closest_dist_, distance)))
	{
		//std::cout << " - IsCloser Complete, closer.\r\n";
		return distance;
	}
	
	//std::cout << " - IsCloser Complete, not closer.\r\n";
	return -1.0;
}

void stabilization_minimize_travel::add_saved_plan()
{
	//std::cout << "Adding saved plan to plans...  F Speed" << p_saved_position_->f_ << " \r\n";
	snapshot_plan* p_plan = new snapshot_plan();

	// create the initial position
	p_plan->p_triggering_command_ = new parsed_command(*p_saved_position_->p_command);
	p_plan->p_start_command_ = new parsed_command(*p_saved_position_->p_command);
	p_plan->p_initial_position_ = new position(*p_saved_position_);
	snapshot_plan_step* p_travel_step = new snapshot_plan_step(&stabilization_x_, &stabilization_y_, NULL, NULL, NULL, travel_action);
	p_plan->steps_.push_back(p_travel_step);
	snapshot_plan_step* p_snapshot_step = new snapshot_plan_step(NULL, NULL, NULL, NULL, NULL, snapshot_action);
	p_plan->steps_.push_back(p_snapshot_step);

	p_plan->p_return_position_ = new position(*p_saved_position_);
	p_plan->p_end_command_ = NULL;

	p_plan->file_line_ = p_saved_position_->file_line_number_;
	p_plan->file_gcode_number_ = p_saved_position_->gcode_number_;
	// Move all of the elements from the saved wipe steps into the snapshot plan wipe steps
	move_saved_wipe_steps(p_plan->wipe_steps_);
		
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