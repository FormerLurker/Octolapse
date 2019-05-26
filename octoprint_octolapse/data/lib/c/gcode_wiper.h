#ifndef GCODE_WIPER_H
#define GCODE_WIPER_H

#include "gcode_wiper_position_list.h"
#include "position.h"
#include <vector>

#include "gcode_wiper_step.h"
/**
 * \brief Class to create wipe gcode for a given position.  Supports limited undo.
 */

class gcode_wiper
{
public:
	gcode_wiper();
	gcode_wiper(double retraction_length, double retraction_feedrate, double wipe_feedrate);
	virtual ~gcode_wiper();
	/**
	 * \brief Update the gcode wiper with a copy of the current position, and possibly a copy 
	 * of the previous position
	 * \param current_position the current position
	 * \param previous_position the previous position.
	 */
	void update(position& current_position, position& previous_position);
	/**
	 * \brief Creates the gcodes necessary to perform a 50/50 wipe in the current axis modes 
	 * and with all current offsets applied.
	 * \param  parsed_commands A vector to be filled with the list of parsed commands necessary 
	 * to perform a full wipe and retract.  If wiping is not possible, no commands will 
	 * be added to the vector.  You are responsible for deleting any added parsed_commands 
	 * pointers.
	 */
	void get_wipe_steps(std::vector<gcode_wiper_step*> &wipe_steps);

	/*
	 * \brief Removes the last update if possible.
	 */
	void undo();
private:
	
	/**
	 * \brief Prunes all history not necessary to generate wipe gcodes.
	 */
	void prune_history();
	void save_undo_data();
	void restore_undo_data();
	gcode_wiper_step* get_wipe_step(gcode_wiper_position* start_position, gcode_wiper_position* end_position, double &current_offset_e, double feedrate, bool is_return);
	gcode_wiper_step* get_retract_step(double e, double f);
	gcode_wiper_position_list history_;
	gcode_wiper_position* p_starting_position_;
	gcode_wiper_position* p_previous_starting_position_;
	double total_extrusion_;
	double previous_total_extrusion_;
	double retraction_length_;
	double half_retraction_length_;
	double wipe_feedrate_;
	double retraction_feedrate_;
};


#endif
