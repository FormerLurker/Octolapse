#include "GcodeParser.h"
#include <vector>
#include <string>
#include <algorithm>
#include <set>
#include <stdio.h>
#include <cstring>
bool isGcodeWord(char c)
{
	for (int index = 0; index < sizeof(&GCODE_WORDS); ++index)
	{
		if (GCODE_WORDS[index] == c)
			return true;
	}
	return false;
}

const char* stripGcode(const char* gcode)
{
    std::string output;
	const int BUFFER_SIZE = 64;
	output.reserve(BUFFER_SIZE);
	int gcodeLength = std::strlen(gcode);
	for (int index = 0; index < gcodeLength; ++index)
	{
		char currentChar = gcode[index];
		if (currentChar == ';')
			return stripNewLines(output);
		else if (isspace(currentChar) || currentChar == '\r' || currentChar=='\n')
			continue;
		else {
			if (currentChar >= 97 && currentChar <= 122)
			{
				output.append(1, gcode[index] - 32);
			}
			else
				output.append(1, currentChar);
		}

	}
	return output.c_str();
}

const char * stripNewLines(std::string gcode)
{
    int index = gcode.length();
    for ( ; index >-1 ; index--)
    {
        if (!(gcode[index] == '\n' ||  gcode[index] == '\r'))
            break;
    }
    if(index > -1)
    {
        return gcode.substr(0, index+1).c_str();
    }
    else
    {
        return gcode.c_str();
    }

}


int getFloatEndindex(const char* gcode, int startIndex)
{
	bool hasSeenPeriod = false;
	bool hasSeenPlusOrMinus = false;
	char curLetter;
	unsigned int stringLength = (unsigned)strlen(gcode);
	for (; startIndex < stringLength; ++startIndex)
	{
        curLetter = gcode[startIndex];
		if ('0' <= curLetter && curLetter <= '9')
			continue;
        else if (curLetter == '+' || curLetter == '-')
        {
            if (!hasSeenPlusOrMinus)
            {
                hasSeenPlusOrMinus = true;
                continue;
            }
            else
            {
                startIndex=-1;
                break;
            }
        }
		else if (gcode[startIndex] == '.')
		{
			if (!hasSeenPeriod)
			{
				hasSeenPeriod = true;
				continue;
			}
			else
			{
				startIndex = -1;
				break;
			}

		}
		else
		{
			break;
		}

	}

	return startIndex;
}


