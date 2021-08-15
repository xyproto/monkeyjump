#!/usr/bin/python
#-*-coding:utf-8-*-
#vim: set enc=utf8:
#
# author:   Alexander Rødseth <rodseth@gmail.com>
# date:     July 2004
#

from burnlib.imageengine import Graphics
from burnlib.goengine import GoGrid
from burnlib.imageengine import fullscreen_control
from burnlib.configreader import Keybindings
from sys import exit as sysexit
import os
import os.path

def sysexitwrapper(exitcode=0):
    """ Quits the entire program with an exitcode """
    sysexit(exitcode)

def displaywrapper(fn):
    """ Shows an image with the external "display" program (ImageMagick) """
    os.system("display %s &" % fn )

class Parser(object):

    def __init__(self, resolution=(640, 480), fullscreen=False, BOARD=19, THEMEDIR="themes", CONFDIR="."):
        # Setup the screen and a GoGrid
        #print "parser size", BOARD

        themeconf = open(os.path.join(CONFDIR, "theme.conf")).read().split("\n")[:-1]
        themename = [line for line in themeconf if not line.strip().startswith("#")][0].strip()
        specific_themedir = os.path.join(THEMEDIR, themename)

        self.screen = Graphics(size=resolution, fullscreen=fullscreen, BOARD=BOARD, SPECIFIC_THEMEDIR=specific_themedir)
        self.gogrid = fullscreen_control(self.screen, GoGrid, bpp=32, gridsize=(BOARD, BOARD), gnugoconf=os.path.join(CONFDIR, "gnugocmd.conf"), SPECIFIC_THEMEDIR=specific_themedir)
        self.refresh()

        # Create a function-collection and register functions
        self.fc = FunctionCollection()
        self.regfunctions()

    def regfunctions(self):
        """ Connect names with functions. The names can be used for keybinding or in the console.
            In the future, I'll throw in XMLRPC as well, which should be really easy.
            "str" is the currently the only supported type in the keybinding-file.
        """
        self.fc.add("up", self.gogrid.up)
        self.fc.add("down", self.gogrid.down)
        self.fc.add("right", self.gogrid.right)
        self.fc.add("left", self.gogrid.left)
        self.fc.add("toggle", self.gogrid.toggle)
        self.fc.add("togglecolor", self.gogrid.togglecolor, ["str", "str", "str"])
        self.fc.add("togglewhite", self.gogrid.togglewhite)
        self.fc.add("toggleblack", self.gogrid.toggleblack)
        self.fc.add("save", self.gogrid.save, ["str"])
        self.fc.add("savetransp", self.gogrid.savetransp, ["str"])
        self.fc.add("grow", self.grow)
        self.fc.add("shrink", self.shrink)
        self.fc.add("refresh", self.refresh)
        self.fc.add("console", self.console)
        self.fc.add("quit", self.gogrid.quit, ["str"])
        self.fc.add("getcolor", self.gogrid.pickupcolor)
        self.fc.add("clear", self.gogrid.fullclear)
        self.fc.add("jumppos", self.gogrid.jumppos, ["str", "str"])
        self.fc.add("gnugoblack", self.gogrid.gnugoblack)
        self.fc.add("gnugowhite", self.gogrid.gnugowhite)
        self.fc.add("showboard", self.gogrid.showboard)
        self.fc.add("gnugoinfo", self.gogrid.gnugoinfo)
        self.fc.add("liststones", self.gogrid.liststones)
        self.fc.add("passblack", self.gogrid.passblack)
        self.fc.add("passwhite", self.gogrid.passwhite)
        self.fc.add("undo", self.gogrid.undo)
        self.fc.add("gtp", self.gogrid.gtp, ["str"])
        self.fc.add("multigtp", self.gogrid.multigtp, ["str"])
        self.fc.add("playblack", self.gogrid.playblack, ["str"])
        self.fc.add("playwhite", self.gogrid.playwhite, ["str"])
        self.fc.add("newaswhite", self.gogrid.newaswhite, ["str"])
        self.fc.add("loadsgf", self.gogrid.loadsgf, ["str"])
        self.fc.add("reloadsgf", self.gogrid.loadsgf)
        self.fc.add("next", self.gogrid.__next__)
        self.fc.add("nextorload", self.gogrid.nextorload)
        self.fc.add("previous", self.gogrid.previous)
        self.fc.add("savesgf", self.gogrid.savesgf, ["str"])
        self.fc.add("level", self.gogrid.level, ["str"])
        self.fc.add("nextlevel", self.gogrid.nextlevel)
        self.fc.add("time", self.gogrid.time, ["str", "str", "str"])
        self.fc.add("futurewhite", self.gogrid.futurewhite)
        self.fc.add("mousepos", self.gogrid.mousepos, ["int", "int"])
        self.fc.add("playguess", self.gogrid.playguess)
        self.fc.add("guessorplace", self.gogrid.guessorplace)
        self.fc.add("showlastmove", self.gogrid.showlastmove)
        self.fc.add("toggleillegal", self.gogrid.toggleillegal)
        self.fc.add("play100moves", self.gogrid.play100moves)
        self.fc.add("analyze", self.gogrid.analyze)
        self.fc.add("myplay", self.gogrid.myplay, ["str"])
        self.fc.add("status", self.gogrid.status)

    def grow(self):
        """ Zoom in """
        # Grow the image-control
        self.screen.clearControl(self.gogrid)
        self.gogrid.grow(1.1)

    def shrink(self):
        """ Zoom out """
        # Shrink the image-control
        self.screen.clearControl(self.gogrid)
        self.gogrid.grow(0.9)

    def refresh(self):
        """ Refresh the image """
        self.screen.blitControl(self.gogrid)
        self.screen.refresh()

    def __call__(self, *params):
        self.fc(*params)

    def console(self):
        """ Enter the console (can be done recursively as well) """
        self.fc.minimal_console(everytime=["refresh"])

class KeyParser(object):

    def __init__(self, filename="keybindings.conf", resolution=(640, 480),
            fullscreen=False, BOARD=19, THEMEDIR="themes", CONFDIR="."):
        #print "kp boardsize", BOARD
        self.keybindings = Keybindings(filename)
        self.parser = Parser(resolution=resolution, fullscreen=fullscreen, BOARD=BOARD, THEMEDIR=THEMEDIR, CONFDIR=CONFDIR)

    def __call__(self, keycode):
        for bound_keycode, command in list(self.keybindings.items()):
            if keycode == bound_keycode:
                self.parser(*command)

    def command(self, commandstring):
        self.parser(commandstring)

    def refresh(self):
        self.parser.refresh()

    def quit(self):
        self.parser("quit")

class ParameterChecker(object):
    """
    ParameterChecker is given a type at construction-time,
    and can later check if a given value fits to that type.
    The types can be defined much more specific than ordinary
    Python-types, using custom-made functions as validators.
    """

    def strIsPythonType(self, str):
        try:
            if not (type(eval(str + "()")) == type(type)):
                return True
            else:
                return False
        except NameError:
            return False
        except TypeError:
            return False

    def getPythonType(self, str):
        return type(eval(str + "()"))

    def __init__(self, exampleType):
        """
        exampleType can be used as an example type,
        or contain a string describing a special kind of type, like "byte".
        Typical ways to call this constructor:
            i = ParameterChecker(int())
            i = ParameterChecker(0)
            s = ParameterChecker(str())
            s = ParameterChecker("any string")
            f = ParameterChecker(float())
            f = ParameterChecker(0.0)
            b = ParameterChecker("byte")
        """
        # For the future
        self._type = "BUG: unset type-string!"
        # Is this a "special kind of type"
        if type(exampleType) == type(type):
            print("Warning! Type is of type type!")
        if type(exampleType) == type(str()) and exampleType in ["byte"]:
            if exampleType == "byte":
                self._type = "byte"
                def aByte(value):
                    if type(value) == type(int()):
                        if (value >= 0) and (value <= 255):
                            return True
                    return False
                self._valifunc = aByte
            # Add more types here later
            #else:
            #    # You should never reach this place
            #    print "BUG: exampleType list and exampleType ifs don't match!"
            #    assert(0)
        # Create a validation function based on exampleType 
        elif self.strIsPythonType(exampleType):
            self._type = exampleType
            correct_type = self.getPythonType(exampleType)
            self._valifunc = lambda x:type(x) == correct_type
        else:
            self._type = str(type(exampleType)).split("'")[1]
            self._valifunc = lambda x:type(x) == type(exampleType)

    """
    Uses the validation function to check if a given parameter is okay
    """
    def valid(self, value):
        return self._valifunc(value)

    def __str__(self):
        return self._type
    
class ParameterListChecker(object):
    """
    Takes a list of types (as types or exampletypes),
    and has a valid function for checking a list of values.
    """

    def __init__(self, typelist):
        self.validators = list(map(ParameterChecker, typelist))

    def valid(self, values):
        got = len(values)
        want = len(self.validators)
        if got == want:
            error_info = ""
            for i, validator in enumerate(self.validators):
                value = values[i]
                if not validator.valid(values[i]):
                        # Error-message-info
                        valuetype = str(type(value)).split("'")[1]
                        error_info = i + 1, str(validator), valuetype, value
                        break
            else:
                # All params are ok, no break occured
                return True

            # Some params are wrong, break occured
            print('Parameter nr %i is invalid, wanted type %s, got type %s. Look: %s' % error_info)
            return False
        else:
            if got < want:
                print("Too few parameters. I wanted %i but got %i." % (want, got))
            else:
                print("Too many parameters. I wanted %i but got %i." % (want, got))
            return False

class FunctionWrapper(object):
    """
    A strongly typed function.
    Takes a Python-function and a list of parameter-types.
    Useful for scriptability and undoability.
    """

    def __init__(self, function, paramTypeList):
        self._paramTypeList = paramTypeList
        self._function = function
    
    def __call__(self, *params):
        pc = ParameterListChecker(self._paramTypeList)
        if pc.valid(params):
            # Extended call-syntax =)
            return self._function(*params)
        return "invalid parameters"
    
    def getParamTypeList(self):
        return self._paramTypeList

class FunctionCollection(object):
    
    def __init__(self):
        self._functions = {}
    
    def add(self, alias, function, paramTypeList=[]):
        if alias not in self._functions:
            self._functions[alias] = FunctionWrapper(function, paramTypeList)
            return True
        else:
            print("That function is already defined.")
            return False

    def remove(self, alias):
        if alias in self._functions:
            del self._functions[alias]
            return True
        else:
            print("Unable to find the function that was set for removal.")
            return False

    def __call__(self, alias, *parameters):
        if alias in self._functions:
            return self._functions[alias](*parameters)
        else:
            print("Unable to find the given function.")
            return False

    def getParamList(self, alias):
        """ Returns a list of functiontypes for a specific function """
        if alias in self._functions:
            return self._functions[alias].getParamTypeList()
        else:
            print("Unable to find the given function:", alias)
            return False

    # Deprecated
    def minimal_console(self, everytime=[]):

        def convert_if_possible(s):
            try:
                try:
                    if "." in s:
                        return float(s)
                    else:
                        return int(s)
                except ValueError:
                    return int(s)
            except ValueError:
                return s

        def list_functions():
            """ Returns a sorted list of available functions """
            l = list(self._functions.keys())
            l.sort()
            return l

        def docstr(function):
            """ Returns the docstring for a function """
            if function in self._functions:
                helptext = self._functions[function]._function.__doc__
                if helptext == None:
                    return "No help is available for the given function. :/"
                else:
                    return helptext.strip()

    
        self.add("list", list_functions, [])
        self.add("params", self.getParamList, ["str"])
        self.add("help", docstr, ["str"])
        self.add("quit", sysexitwrapper, ["int"])

        print()
        print("Welcome to the minimal console!")
        print()
        print("Use list for available commands.")
        print("Use help to examine commands.")
        print("Use params to get a list of wanted parameters.") 
        print("Use ! in front of Python-expressions.")
        print()

        while 1:
            try:
                cmd = input("# ").strip()
                if len(cmd) > 0 and cmd[0] == "!":
                    print(eval(cmd[1:]))
                elif len(cmd) > 0 and cmd.find("exit") == 0:
                    print("Done with console.")
                    break
                else:
                    plist = list(map(convert_if_possible, cmd.split(" ")))
                    result = self(*plist)
                    if not (result == None):
                        print(result)
                # Do all the script-commands in everytime now
                list(map(self, everytime))
            except IndexError:
                print("IndexError")
            except EOFError:
                print(os.sep + "EOFError, exiting console")
                break
