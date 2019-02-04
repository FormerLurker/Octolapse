#ifndef GcodeParser_H
#define GcodeParser_H
#include <string>
static const char GCODE_WORDS[] = { 'G', 'M', 'T' };
std::string stripGcode(std::string);
std::string stripNewLines(std::string gcode);
int getFloatEndindex(std::string gcode, int startIndex);
bool isGcodeWord(char c);

#endif
