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

std::string stripGcode(std::string gcode)
{
    std::string output;
	const int BUFFER_SIZE = 64;
	output.reserve(BUFFER_SIZE);
	int gcodeLength = gcode.size();
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
	return output;
}

std::string stripNewLines(std::string gcode)
{
    int index = gcode.length();
    for ( ; index >-1 ; index--)
    {
        if (!(gcode[index] == '\n' ||  gcode[index] == '\r'))
            break;
    }
    if(index > -1)
    {
        return gcode.substr(0, index+1);
    }
    else
    {
        return gcode;
    }

}


int getFloatEndindex(std::string gcode, int startIndex)
{
	bool hasSeenPeriod = false;
	bool hasSeenPlusOrMinus = false;
	char curLetter;
	unsigned int stringLength = gcode.size();
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


