#pragma once
#include <string>
#include <map>

struct octolapse_log
{
	enum octolapse_loggers { GCODE_PARSER, GCODE_POSITION, SNAPSHOT_PLAN };
	enum octolapse_log_levels {NOSET = 0, VERBOSE = 5, DEBUG = 10, INFO=20, WARNING=30, ERROR=40, CRITICAL=50};
};

void octolapse_initialize_loggers();
void octolapse_log(const int logger_type, const int log_level, const std::string &message);
void set_internal_log_levels(bool check_real_time);


