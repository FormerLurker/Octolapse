#pragma once
#include<stdarg.h>
#include <string>
#include <map>

enum octolapse_loggers {GCODE_PARSER,GCODE_POSITION,SNAPSHOT_PLAN};
enum octolapse_log_levels {INFO, WARNING, ERROR, DEBUG, VERBOSE};
void octolapse_initialize_loggers();
void octolapse_log(int logger_type, int log_level, std::string message);

