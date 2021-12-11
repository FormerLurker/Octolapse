#include "utilities.h"
#include <cmath>
#include <sstream>
#include <iostream>
#include <cctype>
#include <cstring>


#ifdef _MSC_VER
    #include <Windows.h>  
    #include <fileapi.h > 
    
    std::wstring utilities::ToUtf16(std::string str)
    {
        UINT codepage = 65001;
        #ifdef IS_PYTHON_EXTENSION
            codepage = 65001; // CP_UTF8
        #else
            codepage = 65000; // CP_UTF7
        #endif
        std::wstring ret;
        int len = MultiByteToWideChar(codepage, 0, str.c_str(), str.length(), NULL, 0);
        if (len > 0)
        {
            ret.resize(len);
            MultiByteToWideChar(codepage, 0, str.c_str(), str.length(), &ret[0], len);
        }
        return ret;
    }
#endif


// Had to increase the zero tolerance because prusa slicer doesn't always retract enough while wiping.
const double ZERO_TOLERANCE = 0.00005;
const std::string utilities::WHITESPACE_ = " \n\r\t\f\v";

int utilities::round_up_to_int(double x)
{
  return int(x + ZERO_TOLERANCE);
}

bool utilities::is_equal(double x, double y)
{
  double abs_difference = std::fabs(x - y);
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
  return std::fabs(x) < ZERO_TOLERANCE;
}

double utilities::get_cartesian_distance(double x1, double y1, double x2, double y2)
{
  // Compare the saved points cartesian distance from the current point
  double xdif = x1 - x2;
  double ydif = y1 - y2;
  double dist_squared = xdif * xdif + ydif * ydif;
  return sqrt(xdif * xdif + ydif * ydif);
}

std::string utilities::to_string(double value)
{
  std::ostringstream os;
  os << value;
  return os.str();
}

std::string utilities::ltrim(const std::string& s)
{
  size_t start = s.find_first_not_of(WHITESPACE_);
  return (start == std::string::npos) ? "" : s.substr(start);
}

std::string utilities::rtrim(const std::string& s)
{
  size_t end = s.find_last_not_of(WHITESPACE_);
  return (end == std::string::npos) ? "" : s.substr(0, end + 1);
}

std::string utilities::trim(const std::string& s)
{
  return rtrim(ltrim(s));
}

std::istream& utilities::safe_get_line(std::istream& is, std::string& t)
{
  t.clear();
  // The characters in the stream are read one-by-one using a std::streambuf.
  // That is faster than reading them one-by-one using the std::istream.
  // Code that uses streambuf this way must be guarded by a sentry object.
  // The sentry object performs various tasks,
  // such as thread synchronization and updating the stream state.

  std::istream::sentry se(is, true);
  std::streambuf* sb = is.rdbuf();

  for (;;)
  {
    const int c = sb->sbumpc();
    switch (c)
    {
    case '\n':
      return is;
    case '\r':
      if (sb->sgetc() == '\n')
        sb->sbumpc();
      return is;
    case EOF:
      // Also handle the case when the last line has no line ending
      if (t.empty())
        is.setstate(std::ios::eofbit);
      return is;
    default:
      t += static_cast<char>(c);
    }
  }
}

/// <summary>
/// Checks to see if the lhs is in the rhs.
/// </summary>
/// <param name="lhs">The string to search for in the array.  Case will be ignored, as will beginning and ending whitespace</param>
/// <param name="rhs">A null terminated LOWERCASE array of const char * that is already trimmed.</param>
/// <returns></returns>
bool utilities::is_in_caseless_trim(const std::string& lhs, const char** rhs)
{
  unsigned int lhend = lhs.find_last_not_of(WHITESPACE_);
  unsigned int lhstart = lhs.find_first_not_of(WHITESPACE_);
  unsigned int size = lhend - lhstart + 1;
  int index = 0;

  while (rhs[index] != NULL)
  {
    const char* rhString = rhs[index++];
    if (rhString == NULL)
    {
      break;
    }
    // If the sizes minus the whitespace doesn't match, the strings can't match
    if (size != strlen(rhString))
    {
      continue;
    }

    // The sizes match, loop through and compare
    bool failed = false;
    for (unsigned int i = 0; i < size; ++i)
    {
      if (std::tolower(lhs[i + lhstart]) != rhString[i])
      {
        // Something didn't match, return false
        failed = true;
        break;
      }
    }
    if (!failed)
    {
      return true;
    }
  }

  // If we are here, this string does not appear
  return false;
}


