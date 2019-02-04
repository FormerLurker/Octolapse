// A2DD.h
#ifndef GcodeParser_H
#define GcodeParser_H
#include <vector>
#include <string>
#include <string>
#include <algorithm>
#include <set>
#include <stdio.h>


static const char GCODE_WORDS[] = { 'G', 'M', 'T' };

typedef struct GcodeParameter
{
	std::string Name;
	std::string Value;
}GcodeParameter;

typedef struct ParsedCommand
{
	std::string cmd;
	std::vector<struct GcodeParameter> parameters;
}ParsedCommand;

const char* stripGcode(const char*);
const char* stripNewLines(std::string gcode);
int getFloatEndindex(const char* gcode, int startIndex);
bool isGcodeWord(char c);

#endif
