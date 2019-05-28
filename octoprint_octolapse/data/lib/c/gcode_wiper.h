#ifndef GCODE_WIPER_H
#define GCODE_WIPER_H

#include "gcode_wiper_position_list.h"
#include "position.h"
#include <vector>

#include "gcode_wiper_step.h"
struct gcode_wiper_args
{
	gcode_wiper_args()
	{
		retraction_length = 0.0;
		wipe_feedrate = 0.0;
		retraction_feedrate = 0.0;
		x_y_travel_speed = 0.0;
		wipe_distance = 0.8;
	}
	double retraction_length;
	double x_y_travel_speed;
	double wipe_feedrate;
	double retraction_feedrate;
	double wipe_distance;
};
/**
 * \brief Class to create wipe gcode for a given position.  Supports limited undo.
 */
class gcode_wiper
{
public:
	gcode_wiper();
	gcode_wiper(gcode_wiper_args args);
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
	gcode_wiper_step* get_wipe_step(gcode_wiper_position* start_position, gcode_wiper_position* end_position, double feedrate, bool is_return);
	static gcode_wiper_step* get_retract_step(double e, double f);
	static gcode_wiper_step* get_travel_step(double x, double y, double f);
	
	/**
	 * \brief Clips a to/from position pair, altering the to position so that the to/from movement is equal to the 
	 * distance to clip
	 * \param distance_to_clip The distance to remove from the end of the from-to movement.
	 * \param from_position the starting position.  This pointer WILL replaced with a new object WITHOUT deleting the 
	 * object.  You must store the supplied pointer and the modified pointer and delete them when you are finished.
	 * \param to_position the endpoint of the path.  This pointer WILL replaced with a new object WITHOUT deleting the 
	 * object.  You must store the supplied pointer and the modified pointer and delete them when you are finished.
	 */
	void clip_wipe_path(double distance_to_clip, gcode_wiper_position* &from_position, gcode_wiper_position* &to_position);
	gcode_wiper_position_list history_;
	// Settings
	gcode_wiper_args settings_;
	// History Tracking Variables
	double total_distance_;
	double previous_total_distance_;
	gcode_wiper_position* p_starting_position_;
	gcode_wiper_position* p_previous_starting_position_;

};

#endif