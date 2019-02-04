#ifndef GcodeParser_H
#define GcodeParser_H
#include <string>
static const char GCODE_WORDS[] = { 'G', 'M', 'T' };
const char* stripGcode(const char*);
const char* stripNewLines(std::string gcode);
int getFloatEndindex(const char* gcode, int startIndex);
bool isGcodeWord(char c);

#endif
