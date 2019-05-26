#include "gcode_wiper.h"
#include "utilities.h"
#include "logging.h"

gcode_wiper::gcode_wiper()
{
	total_extrusion_ = 0.0;
	previous_total_extrusion_ = 0.0;
	retraction_length_ = 0.0;
	half_retraction_length_ = 0.0;
	wipe_feedrate_ = 0.0;
	retraction_feedrate_ = 0.0;
	p_starting_position_ = NULL;
	p_previous_starting_position_ = NULL;
}

gcode_wiper::gcode_wiper(double retraction_length, double retraction_feedrate, double wipe_feedrate)
{
	// Initialize members
	total_extrusion_ = 0.0;
	previous_total_extrusion_ = 0.0;

	// Set members from parameters
	retraction_length_ = retraction_length;
	retraction_feedrate_ = retraction_feedrate;
	wipe_feedrate_ = wipe_feedrate;

	// Set calculated members
	half_retraction_length_ = retraction_length / 2.0;
	p_starting_position_ = NULL;
	p_previous_starting_position_ = NULL;
}

gcode_wiper::~gcode_wiper()
{
	// p_starting_position and p_previous_starting_position can be the same item!
	if(p_starting_position_ == p_previous_starting_position_ && p_starting_position_ != NULL)
	{
		delete p_starting_position_;
		p_starting_position_ = NULL;
		p_previous_starting_position_ = NULL;
	}
	else
	{
		if (p_starting_position_ != NULL)
		{
			delete p_starting_position_;
			p_starting_position_ = NULL;
		}
		if (p_previous_starting_position_ != NULL)
		{
			delete p_previous_starting_position_;
			p_previous_starting_position_ = NULL;
		}
	}

}

void gcode_wiper::undo()
{
	restore_undo_data();
	history_.undo();
}

void gcode_wiper::save_undo_data()
{
	
	if (p_previous_starting_position_ != NULL && p_previous_starting_position_ != p_starting_position_)
	{
		delete p_previous_starting_position_;
	}

	p_previous_starting_position_ = p_starting_position_;

	previous_total_extrusion_ = total_extrusion_;
}

void gcode_wiper::restore_undo_data()
{
	if (p_starting_position_ != NULL && p_starting_position_ != p_previous_starting_position_)
	{
		delete p_starting_position_;
	}
	p_starting_position_ = p_previous_starting_position_;
	p_previous_starting_position_ = NULL;
	total_extrusion_ = previous_total_extrusion_;
	previous_total_extrusion_ = 0;
}

void gcode_wiper::update(position& current_position, position& previous_position)
{
	// determine if we should clear the wipe queue.We want to clear it out in the following cases :
	// 1.  if the layer has changed
	// 2.  If the current code is not extruding
	// This is a pretty restrictive list, but allowing more wiping gets complicated.
	// Improve this if possible
	save_undo_data();
	if (
		current_position.is_layer_change_ || 
		!(current_position.has_xy_position_changed_ && current_position.is_extruding_)
	)
	{
		total_extrusion_ = 0;
		history_.clear();
		return;
	}
	
	if (history_.size() == 0)
	{
		if (p_starting_position_ != NULL && p_starting_position_ != p_previous_starting_position_)
			delete p_starting_position_;
		p_starting_position_ = new gcode_wiper_position(previous_position);
	}

	history_.push_back(current_position);
	previous_total_extrusion_ = total_extrusion_;
	total_extrusion_ += current_position.e_relative_;
	
	prune_history();
}

void gcode_wiper::prune_history()
{
	// It's possible that multiple items are pruned from the beginning of the history.
	// keep track of the first pruned item.
	bool has_pruned_item = false;
	// removes items at the front of the history until removing more items would cause total_extrusion < half_retraction_length
	while (total_extrusion_ > half_retraction_length_)
	{
		// get a pointer to the first inserted history item
		gcode_wiper_position * front_item = history_.peek();
		const double new_total_extrusion = total_extrusion_ - front_item->e_relative;

		if (utilities::less_than(new_total_extrusion, half_retraction_length_))
		{
			// We want to keep the total extrusion length > half_retraction_length so that
			// we can do a full wipe if possible.  Since removing this gcode would mean we can't 
			// do a full wipe, break now.
			break;
		}
		
		// We need to remove the front most (earliest) item from the history
		// because it is not needed to generate wipe gcodes.

		if (!has_pruned_item)
		{
			//save_undo_data();
			// TODO:  Do we need this??  It's commented out because it smells
			// The previous_total_extrusion at this point will = total_extrusion_
			// but we have altered the extrusion by pulling the front, not the back
			// history item.  Correctly set the previous total extrusion
			//previous_total_extrusion_ = new_total_extrusion;
		}
		// Delete the starting_position if we have one, and it's not the same as the previous starting
		// position
		if (p_starting_position_ != NULL && p_previous_starting_position_ != p_starting_position_)
			delete p_starting_position_;

		// The front item is our new starting position.  Copy it.
		p_starting_position_ = new gcode_wiper_position(*front_item);
		// We've reduced the total extrusion, record the change.
		total_extrusion_ = new_total_extrusion;

		// Remove the front_item from the history list.  It will remain in the undo list
		// until after we call history_.clear() or history_.push_back()
		history_.remove();

		// Mark that we've pruned data so that we don't perform any additional
		// saves to the undo data, which will mess up our undo later.
		has_pruned_item = true;
	}
}

void gcode_wiper::get_wipe_steps(std::vector<gcode_wiper_step*> &wipe_steps)
{

	const int num_positions = history_.size();
	if (total_extrusion_ == 0 || p_starting_position_ == NULL || num_positions < 1)
	{
		return;
	}

	// save the starting x and y positions
	gcode_wiper_position* start_position = p_starting_position_;
	gcode_wiper_position* first_position = NULL;
	// We might have to change the start position if there is too much 
	// extrusion, but we don't want to alter the actual data.
	// If this is true later we will need to delete the start position
	bool has_altered_positions = false;
	// save the starting axis modes for convenience
	
	double missing_extrusion = retraction_length_ - total_extrusion_ * 2;
	if (utilities::less_than_or_equal(missing_extrusion, 0))
	{
		missing_extrusion = 0;
	}
	// Get the current position history.
	int start_index = -1;
	std::vector<gcode_wiper_position*> positions = *history_.get_position_history(start_index);
	first_position = positions[start_index];
	// See if we need to alter the middle position, in the case that we have more room to wipe in the 
	// history than we need
	const double extra_extrusion = total_extrusion_ - half_retraction_length_;
	if (utilities::greater_than(extra_extrusion, 0))
	{
		has_altered_positions = true;
		// The gcode we want to alter will always be the EARLIEST (first) one placed in the history.
		first_position = new gcode_wiper_position(*first_position);
		start_position = new gcode_wiper_position(*p_starting_position_);

		// calculate the ratio of extra extrusion compared to the total extrusion of the line
		const double extrusion_ratio = (first_position->e_relative - extra_extrusion) / first_position->e_relative;
		// scale the extrusion
		const double e_relative = first_position->e_relative * extrusion_ratio;
		// Calculate the x and y relative change
		const double x_relative = (start_position->x - first_position->x) * extrusion_ratio;
		const double y_relative = (start_position->y - first_position->y) * extrusion_ratio;

		// adjust the x y values of the starting position to reflect the change in extrusion distance
		
		start_position->x = first_position->x + x_relative;
		start_position->y = first_position->y + y_relative;
		// Adjust the e and e_relative positions of the earliest inserted history position
		// to account for the reduction in extrusion distance.
		// Note that we are retracting, so we need to subtract, not add e relative.
		first_position->e = first_position->e - e_relative;
		first_position->e_relative = e_relative;
	}
	// Track the offset_e, which is the easiest way to calculate the gcodes later
	double current_offset_e = 0;
	// Create a pointer to hold the previous position, which will be used as a starting point
	// for any produced gcodes
	gcode_wiper_position * previous_position = NULL;
	gcode_wiper_position * current_position = NULL;
	double feedrate = wipe_feedrate_;

	// We are going to loop through the list, first back to front, then front to back
	// However, we will only hit the starting position (p_starting_location, which was
	// added to the front of the list earlier in this function) once, and will skip its index
	// on the second pass
	for (int pass = 0; pass < 2; pass++)
	{
		int index;
		int step;
		int end;
		if (pass == 0)
		{
			index = positions.size() - 1;
			step = -1;
			end = start_index - 1;
		}
		else
		{
			index = start_index+1;
			step = 1;
			end = positions.size();
		}
		
		for (; (pass == 0 && index > end) || (pass == 1 && index < end); index = index + step)
		{
			if (index == start_index)
				current_position = first_position;
			else
				current_position = positions[index];

			if (previous_position == NULL)
			{
				previous_position = current_position;
				// use the offset E position as a convenience in case we are in absolute
				// extrusion mode.  This saves us from having to subtract the offset later.
				current_offset_e = current_position->get_offset_e();
				continue;
			}

			
			gcode_wiper_step* step = get_wipe_step(previous_position, current_position, current_offset_e, feedrate, pass != 0);
			wipe_steps.push_back(step);
			// the current position will be the previous position
			// for the next iteration, so save it now.
			previous_position = current_position;

			feedrate = -1;
			
		}
		if (pass == 0)
		{
			// Now we need to create a wipe command from the previous position to the starting point
			gcode_wiper_step* step = get_wipe_step(previous_position, start_position, current_offset_e, feedrate, false);
			wipe_steps.push_back(step);
			feedrate = -1;
			// Now we need to create a wipe command from the starting point to the previous position
			step = get_wipe_step(start_position, previous_position, current_offset_e, feedrate, true);
			wipe_steps.push_back(step);
		}
	}
	// It's possible we've finished wiping, but have more to 
		// retract.  If so, add the retraction now at the normal retraction
		// feedrate
	if (missing_extrusion > 0 && current_position != NULL)
	{
		// Only set the feedrate if the retraction and wipe feedrates differ.
		if (!utilities::is_equal(retraction_feedrate_, wipe_feedrate_))
		{
			feedrate = retraction_feedrate_;
		}

		// Get our e value depending on the extruder axis mode
		double e;
		if (current_position->is_extruder_relative)
		{
			e = -1 * missing_extrusion;
		}
		else
		{
			e = current_offset_e - missing_extrusion;
		}
		// Create the gcode and parameters for the final retract

		wipe_steps.push_back(get_retract_step(e, feedrate));
	}

	if(has_altered_positions)
	{
		delete start_position;
		start_position = NULL;
		delete first_position;
		first_position = NULL;
	}

}

gcode_wiper_step* gcode_wiper::get_wipe_step(gcode_wiper_position* start_position, gcode_wiper_position* end_position, double &current_offset_e, double feedrate, bool is_return)
{
	double x, y, e;
	if (end_position->is_relative)
	{
		x = end_position->x - start_position->x;
		y = end_position->y - start_position->y;
	}
	else
	{
		// Since we're sending gcodes, we MUST use the offset positions when using absolute
		// mode.
		x = end_position->get_offset_x();
		y = end_position->get_offset_y();
	}

	if (end_position->is_extruder_relative)
	{
		if (is_return)
		{
			e = -1 * end_position->e_relative;
		}
		else
		{
			e = -1 * start_position->e_relative;
		}
		
	}
	else
	{
		if (is_return)
		{
			e = current_offset_e - end_position->e_relative;
			current_offset_e = e;
		}
		else
		{
			e = current_offset_e - start_position->e_relative;
			current_offset_e = e;
		}
		
	}
	return new gcode_wiper_step(x, y, e, feedrate);
}

gcode_wiper_step* gcode_wiper::get_retract_step(double e, double f)
{
	return new gcode_wiper_step(e, f);
}