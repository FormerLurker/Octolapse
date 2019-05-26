#include "position.h"
#include "gcode_wiper_position_list.h"
#include "snapshot_plan_step.h"


gcode_wiper_position_list::gcode_wiper_position_list()
{
	current_start_index_ = 0;
	can_undo_ = false;
}

gcode_wiper_position_list::gcode_wiper_position_list(gcode_wiper_position_list &source)
{
	throw std::exception("This function is not implemented, and probably shouldn't be");
}

gcode_wiper_position_list::~gcode_wiper_position_list()
{
	clear_all_();
}

void gcode_wiper_position_list::push_back(position &pos)
{
	// clear any position history if we have any
	remove_undo_positions_();
	position_history_.push_back(new gcode_wiper_position(pos));
	can_undo_ = true;
}

void gcode_wiper_position_list::clear()
{
	// clear out the existing undo codes.
	remove_undo_positions_();
	current_start_index_ = position_history_.size();
	if (!position_history_.empty())
	{		
		can_undo_ = true;
	}
	else
	{
		can_undo_ = false;
	}
	
}

void gcode_wiper_position_list::remove_undo_positions_()
{
	if (current_start_index_ > 0)
	{
		int num_positions_to_remove = current_start_index_;
		while (num_positions_to_remove-- > 0)
		{
			gcode_wiper_position* cur_pos = position_history_.front();
			delete cur_pos;
			position_history_.erase(position_history_.begin());
			
		}
		current_start_index_ = 0;
	}
	
}

void gcode_wiper_position_list::clear_all_()
{
	for (std::vector<gcode_wiper_position*>::iterator pos = position_history_.begin(); pos != position_history_.end(); ++pos)
	{
		delete *pos;
	}
	position_history_.clear();

	current_start_index_ = 0;
	can_undo_ = false;
}

// Undo the last push/push_back
bool gcode_wiper_position_list::undo()
{
	if (!can_undo_)
		return false;

	// see if there are elements to remove that aren't in the undo portion of the history
	if (size() > 0)
	{
		// Remove the last item in the history (this is not an undo position)
		gcode_wiper_position* pos_to_remove = position_history_.back();
		position_history_.pop_back();
		delete pos_to_remove;
	}
	
	current_start_index_ = 0;
	can_undo_ = false;
	return true;
}

gcode_wiper_position* gcode_wiper_position_list::peek_back()
{
	if (size() < 1)
		return NULL;
	return position_history_.back();
}

gcode_wiper_position* gcode_wiper_position_list::peek()
{
	if (size() < 1)
		return NULL;
	return position_history_[current_start_index_];
}

gcode_wiper_position* gcode_wiper_position_list::get_at(int index)
{
	if (index > size() - 1)
		return  NULL;

	const int requested_index = index + current_start_index_;
	
	return position_history_[requested_index];
}

void gcode_wiper_position_list::remove()
{
	if (position_history_.size() > current_start_index_)
	{
		current_start_index_++;
	}
}

int gcode_wiper_position_list::size() const
{
	return position_history_.size() - current_start_index_;
}

void gcode_wiper_position_list::copy_position_history(std::vector<gcode_wiper_position*> &copy_to_vector)
{
	// Clear out any existing parsed commands
	while (!copy_to_vector.empty()) {
		gcode_wiper_position * p = copy_to_vector.back();
		copy_to_vector.pop_back();
		delete p;
	}

	for(unsigned int history_index = current_start_index_; history_index < position_history_.size(); history_index++)
	{
		gcode_wiper_position* cur_pos = position_history_[history_index];
		copy_to_vector.push_back(new gcode_wiper_position(*cur_pos));
	}
}

std::vector<gcode_wiper_position*>* gcode_wiper_position_list::get_position_history(int &starting_index)
{
	starting_index = current_start_index_;
	return &position_history_;
}

