def getfloat(value,default):
	try:
		return float(value)
	except ValueError:
		return float(default)

def getint(value,default):
	try:
		return int(value)
	except ValueError:
		return default

def getbool(value,default):
	try:
		return bool(value)
	except ValueError:
		return default

def getstring(value,default):
	if value is not None and len(value) > 0:
		return value
	return default


def getobject(value,default):
	if value is None:
		return default
	return value