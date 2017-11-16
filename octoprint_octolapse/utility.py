FLOAT_MATH_EQUALITY_RANGE = 0.000001

def getfloat(value,default,key=None):
	try:
		return float(value)
	except ValueError:
		return float(default)

def getint(value,default,key=None):
	try:
		return int(value)
	except ValueError:
		return default

def getbool(value,default,key=None):
	try:
		return bool(value)
	except ValueError:
		return default

def getstring(value,default,key=None):
	if(key is not None):
		if(key in value):
			return getstring(value,default)

	if value is not None and len(value) > 0:
		return value
	return default


def getobject(value,default,key=None):
	if value is None:
		return default
	return value
def is_sequence(arg):
    return (not hasattr(arg, "strip") and
            hasattr(arg, "__getitem__") or
            hasattr(arg, "__iter__"))
