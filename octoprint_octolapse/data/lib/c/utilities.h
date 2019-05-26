#pragma once

class utilities{
public:
	static int round_up_to_int(double x);
	static bool is_equal(double x, double y);
	static bool greater_than(double x, double y);
	static bool greater_than_or_equal(double x, double y);
	static bool less_than(double x, double y);
	static bool less_than_or_equal(double x, double y);
	static bool is_zero(double x);
private:
	utilities();

};

