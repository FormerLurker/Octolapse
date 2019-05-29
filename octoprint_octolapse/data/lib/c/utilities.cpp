#include "utilities.h"
#include <math.h>

const double ZERO_TOLERANCE = 0.000015;

int utilities::round_up_to_int(double x)
{
	return int(x + ZERO_TOLERANCE);
}

bool utilities::is_equal(double x, double y)
{
	double abs_difference = fabs(x - y);
	return abs_difference < ZERO_TOLERANCE;
}

bool utilities::greater_than(double x, double y)
{
	return x > y && !is_equal(x, y);
}

bool utilities::greater_than_or_equal(double x, double y)
{
	return x > y || is_equal(x, y);
}

bool utilities::less_than(double x, double y)
{
	return x < y && !is_equal(x, y);
}

bool utilities::less_than_or_equal(double x, double y)
{
	return x < y || is_equal(x, y);
}

bool utilities::is_zero(double x)
{
	return fabs(x) < ZERO_TOLERANCE;
}

double utilities::get_cartesian_distance(double x1, double y1, double x2, double y2)
{
	// Compare the saved points cartesian distance from the current point
	double xdif = x1 - x2;
	double ydif = y1 - y2;
	double dist_squared = xdif * xdif + ydif * ydif;
	if (dist_squared < 0)
	{
		//std::cout << "Negative Distance found!  Returning -1\r\n";
		return -1.0;
	}
	return sqrt(xdif*xdif + ydif * ydif);
}