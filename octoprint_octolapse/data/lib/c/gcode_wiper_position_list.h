
#ifndef POSITION_LIST_H
#define POSITION_LIST_H
#include <vector>
#include "gcode_wiper_position.h"

/**
 * \brief A class to hold a history list of positions with limited undo capability. 
 * \details Supports up to one undo operate after a push, push_back, or possibly after a clear.
 */
class gcode_wiper_position_list
{
public:
	gcode_wiper_position_list();
	~gcode_wiper_position_list();

	/**
	 * \brief Adds a copy of the provided position to the end of the history list.  
	 * Can be undone with undo()
	 * Note:  Calling this command removes any existing undo positions
	 * \param pos The position to copy and add to the position history.
	 */
	void push_back(position &pos);
	
	/**
	* \brief Attempts to undo the last action.  It will remove the most recently pushed item and restore any items in the undo list from a clear() or remove_front()
	**/
	bool undo();
	/**
	 * \brief Clears out the current position history.  If there was history to clear, 
	 * this operation can be undone via a call to undo()
	 * Note:  Calling this command removes any existing undo positions
	**/
	void clear();
	/**
	* \brief Returns a position pointer for the fist history element.  This element may be deleted via a call to clear() or unto_push()
	**/
	gcode_wiper_position* peek();
	/**
	* \brief Returns a position pointer for the last history element.  This element may be deleted via a call to clear() or unto_push()
	**/
	gcode_wiper_position* peek_back();
	/**
	 * \brief Removes the first (earliest) history element and add it to the undo positions
	 * Note:  This command does NOT remove any existing undo positions.
	 */
	void remove();

	/**
	 * \brief Returns a position pointer at the supplied index
	 * Note:  This command does NOT remove any existing undo positions.
	 * \param index The history index.
	 * \return The position at the given index, or NULL if there is no position at that index.
	 */
	gcode_wiper_position* get_at(int index);
	
	/**
	 * \brief Gets the size of the position history.
	 * \return The number of positions in the current history.
	 */
	int size() const;
	/**
	 * \brief Creates a copy of all current positions and adds them at the end of the supplied vector.  
	 * You must delete the containing position pointers yourself!  Warning:  this function is slow
	 * \param copy_to_vector This vector is filled with a copy of the current position history.
	 */
	void copy_position_history(std::vector<gcode_wiper_position*> &copy_to_vector);

	/**
	 * \brief Gets a pointer to the actual position history and updates the supplied starting index.
	 * Warning:  do not modify the position history, otherwise the wipe history and gcode generation
	 * will not work properly.
	 * \param starting_index Will be updated with the starting index.
	 */
	std::vector<gcode_wiper_position*>* get_position_history(int &starting_index);
private:

	/**
	 * \brief Can't copy this object.  It will raise an exception if you try.
	 * \param source 
	 */
	gcode_wiper_position_list(gcode_wiper_position_list &source);
	/**
	 * \brief Clears all items in the position history list, including any undo histories.
	 */
	void clear_all_();
	/**
	 * \brief Removes any preserved undo position histories used to undo after a clear.
	 */
	void remove_undo_positions_();
	std::vector<gcode_wiper_position*> position_history_;
	unsigned int current_start_index_;
	bool can_undo_;
	
};

#endif