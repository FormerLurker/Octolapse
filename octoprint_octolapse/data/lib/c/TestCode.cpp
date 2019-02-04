static PyObject* ConstructGcodeCommand(PyObject* self, PyObject *args)
{
    PyObject *dict = PyDict_New();

    for (int index = 0; index < 3; index++)
    {

        PyObject * val = PyString_FromString("test");

        PyDict_SetItemString(dict, "test", val); // reference to num stolen
        Py_DECREF(val);
    }
    PyObject *a = PyString_FromString("test");
    PyObject *b = PyString_FromString("test");
    PyObject *c = PyString_FromString("test");

    PyObject *ret_val = PyTuple_Pack(4,a,b,c,dict);
    Py_DECREF(a);
    Py_DECREF(b);
    Py_DECREF(c);
    Py_DECREF(dict);
    return ret_val;
}

static PyObject* DictConstructionSpeedTest(PyObject* self, PyObject *args)
{
    PyObject *dict = PyDict_New();

    for (int index = 0; index < 2; index++)
    {
        PyObject * val = PyString_FromString("test");
        PyDict_SetItemString(dict, "test", val); // reference to num stolen
        Py_DECREF(val);
    }
    return dict;
}

static PyObject* ListConstructionSpeedTest(PyObject* self, PyObject *args)
{
    PyObject *ret_object = PyList_New(4);
    if(ret_object==NULL)
    {
        return NULL;
    }
    for (int index = 0; index < 4; index++)
    {
        PyObject * val = PyString_FromString("test");
        if (val == NULL)
        {
            return NULL;
        }
        PyList_SET_ITEM(ret_object, index, val); // reference to num stolen
    }
    return ret_object;
}

static PyObject* ListBuildSpeedTest(PyObject* self, PyObject *args)
{
  return Py_BuildValue("[s,s,s,s]", "test","test","test","test");
}

static PyObject* ParseGcodeOld(PyObject* self, PyObject *args)
{

	const char* msg;
	if (!PyArg_ParseTuple(args, "s", &msg))
	{
		PyErr_SetString(moduleError, "This is an error");
		return NULL;
	}

    PyObject* ret_value = NULL;
    ParsedCommand* command = NULL;
    command = new ParsedCommand();
    if (!parse(msg, command))
    {
        command->parameters.clear();
        delete command;
        return Py_BuildValue("O", Py_False);
    }

    // get the parameters array
    unsigned int numParams = command->parameters.size();

    PyObject *paramList = PyList_New(numParams);
    if (!paramList)
    {
        PyErr_SetString(moduleError, "Could not create a parameter list!");
        command->parameters.clear();
        delete command;
        return NULL;
    }
    for (int index = 0; index < numParams; index++) {
        GcodeParameter curParam = command->parameters[index];
        PyObject *parameter = Py_BuildValue(
            "{s:s,s:s}",
            "name",curParam.Name.c_str()
            ,"value",curParam.Value.c_str()
        );
        if (!parameter) {
            command->parameters.clear();
            delete command;
            Py_DECREF(paramList);
            return NULL;
        }
        PyList_SET_ITEM(paramList, index, parameter); // reference to num stolen
    }
    ret_value = Py_BuildValue(
        "{s:s,s:N}",
        "cmd",command->cmd.c_str()
        ,"parameters", paramList
    );
    command->parameters.clear();
    delete command;
    return ret_value;

}

static PyObject* ParseGcodes(PyObject* self, PyObject *args)
{
    std::vector<std::string> *lines;
    lines = ParseStringListArg(args);
    if(lines == NULL)
    {
        PyErr_SetString(moduleError, "Couldn't parse the list of strings");
		return NULL;
    }

    if (lines->size() == 0)
    {
        PyErr_SetString(moduleError, "No lines were supplied");
		return NULL;
    }
    std::vector<ParsedCommand*> commands = parse(lines);

    // create a PyList to hold all of the return values
    PyObject *commandList = PyList_New(commands.size());
    if (!commandList)
    {
        PyErr_SetString(moduleError, "Could not create the command list!");
        return NULL;
    }
    for (int commandIndex=0; commandIndex < commands.size(); commandIndex++)
    {
        ParsedCommand * currentCommand = commands[commandIndex];
        if (currentCommand == NULL)
            continue;

        // get the parameters array
        unsigned int numParams = currentCommand->parameters.size();

        PyObject *paramList = PyList_New(numParams);
        if (paramList)
        {

            for (int index = 0; index < numParams; index++)
            {
                GcodeParameter curParam = currentCommand->parameters[index];
                PyObject *parameter = Py_BuildValue(
                    "{s:s,s:s}",
                    "name",curParam.Name.c_str()
                    ,"value",curParam.Value.c_str()
                );
                if (parameter) {
                    PyList_SET_ITEM(paramList, index, parameter); // reference to num stolen
                }

            }
            PyObject* ret_value = Py_BuildValue(
                "{s:s,s:N}",
                "cmd",currentCommand->cmd.c_str()
                ,"parameters", paramList
            );
            PyList_SET_ITEM(commandList, commandIndex, ret_value);
        }
    }

    freeParsedCommands(commands);

    return commandList;
    // TODO:  Cleanup memory!

}

static PyObject* ParseGcode(PyObject* self, PyObject *args)
{
	char * gcodeParam;
	if (!PyArg_ParseTuple(args, "s", &gcodeParam))
	{
		PyErr_SetString(moduleError, "This is an error");
		return NULL;
	}

    //std::string gcode = stripNewLines(gcodeParam);
    std::string strippedCommand = stripGcode(gcodeParam);
    if (strippedCommand.length() == 0 || !isGcodeWord(strippedCommand[0]))
    {
		return Py_BuildValue("O", Py_False);
    }
    std::string commandName;
    PyObject * pyCommandDict = PyDict_New();
    PyObject * pyCommandName;
    PyObject * pyParametersDict;
    PyObject * pyGcode;

 	int endAddressIndex = getFloatEndindex(strippedCommand, 1);

	if (endAddressIndex < 0)
	{
		commandName.append(1, strippedCommand[0]);
		endAddressIndex = 0;
	}
	else
		commandName.append(strippedCommand, 0, endAddressIndex+1);
    pyCommandName = PyString_FromString(commandName.c_str());
    PyDict_SetItemString(pyCommandDict, "cmd", pyCommandName); // reference to num stolen
    Py_DECREF(pyCommandName);
    pyGcode = PyString_FromString(gcodeParam);
    PyDict_SetItemString(pyCommandDict, "gcode", pyGcode); // reference to num stolen
    Py_DECREF(pyGcode);

	if (strippedCommand.length() > endAddressIndex + 1)
	{
		pyParametersDict = getParameters(strippedCommand, endAddressIndex + 1);
	    if (pyParametersDict != NULL)
	    {
	        PyDict_SetItemString(pyCommandDict, "parameters", pyParametersDict); // reference to num stolen
	        Py_DECREF(pyParametersDict);
    	}
	}
	return pyCommandDict;
}

static std::vector<std::string>* ParseStringListArg(PyObject *args)
{
    std::vector<std::string>* lines = new std::vector<std::string>();
    PyObject *obj;

    if (!PyArg_ParseTuple(args, "O", &obj)) {
        return NULL;
    }

    PyObject *iter = PyObject_GetIter(obj);
    if (!iter) {
        return NULL;
    }

    while (true) {

        PyObject *next = PyIter_Next(iter);
        if (!next) {
            break;
        }

        if (!PyString_Check(next)) {
            return NULL;
        }
        const char * line = PyString_AsString(next);
        //if(!PyArg_ParseTuple(next, "s", &msg))
        //    return false;

        lines->push_back(line);
      // do something with foo
    }
    return lines;
}
