#pragma once
#include <string>

class utilities
{
public:
  static int round_up_to_int(double x);
  static bool is_equal(double x, double y);
  static bool greater_than(double x, double y);
  static bool greater_than_or_equal(double x, double y);
  static bool less_than(double x, double y);
  static bool less_than_or_equal(double x, double y);
  static bool is_zero(double x);
  static double get_cartesian_distance(double x1, double y1, double x2, double y2);
  static std::string to_string(double value);
  static std::string ltrim(const std::string& s);
  static std::string rtrim(const std::string& s);
  static std::string trim(const std::string& s);
  static std::istream& safe_get_line(std::istream& is, std::string& t);
  static bool is_in_caseless_trim(const std::string& lhs, const char** rhs);
#ifdef _MSC_VER
  static std::wstring ToUtf16(std::string str);
  
#endif
protected:
  static const std::string WHITESPACE_;
private:
  utilities();
};
