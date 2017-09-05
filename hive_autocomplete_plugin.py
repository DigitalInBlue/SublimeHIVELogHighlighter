#!/usr/bin/python3

## Autocompletion plugin
#  @package hive_autocomplete_plugin
#  @author Vincent Yahna
#
#  Plugin that autocompletes
#  parameters, object names, elements
#  attributes, and enum values for HIVE files.
#  Assumption: Each tag has less than 9000 characters
#  (for optimization purposes)

import sublime, sublime_plugin
from Hive_plugins.Module_DataDictionary import *
from Hive_plugins.Module_XMLTagIterator import *

## Dictionary containing mappings of objects to parameters and
#  mapping of elements to subelements and attributes.
#  Autocompletion and help info plugins store a reference to this object
DATA_DICTIONARY = None #cannot initialize dictionary at plugin load time

#Option names and default values
settings_file = 'hive.sublime-settings'




##the sublime selector that autocompletion should
#occur in. text.xml is for xml files
AUTOCOMPLETION_SELECTOR = "text.xml"

#enums

## context for object types
OBJECT_TYPE_CONTEXT = 1           #context for object type autocompletion
## context for object types with no quotes typed
OBJECT_TYPE_CONTEXT_NO_QUOTES = 2
## context for param names
PARAM_NAME_CONTEXT = 3
## context for param names with no quotes typed
PARAM_NAME_CONTEXT_NO_QUOTES = 4
## context for param values
PARAM_VALUE_CONTEXT = 5
## context for param values with no quotes typed
PARAM_VALUE_CONTEXT_NO_QUOTES = 6
## context for an element
ELEMENT_CONTEXT = 7
## context for an attribute
ATTRIBUTE_CONTEXT = 8
## context for an attribute value other
#  than object type, param name, and param value
ATTRIBUTE_VALUE_CONTEXT = 9
## context for an attribute value with no quotes typed
ATTRIBUTE_VALUE_CONTEXT_NO_QUOTES = 10
## context for an object type where colons
#  are not used as a word separator
#  but are present in the prefix
OBJECT_TYPE_COLON_CONTEXT = 11
## context for an object type where colons
#  are not used as a word separator
#  but are present in the prefix
#  and no quotes have been typed
OBJECT_TYPE_COLON_CONTEXT_NO_QUOTES = 12

CONTEXT_NAMES = [
	"None",
	"OBJECT_TYPE_CONTEXT",
	"OBJECT_TYPE_CONTEXT_NO_QUOTES",
	"PARAM_NAME_CONTEXT",
	"PARAM_NAME_CONTEXT_NO_QUOTES",
	"PARAM_VALUE_CONTEXT",
	"PARAM_VALUE_CONTEXT_NO_QUOTES",
	"ELEMENT_CONTEXT",
	"ATTRIBUTE_CONTEXT",
	"ATTRIBUTE_VALUE_CONTEXT",
	"ATTRIBUTE_VALUE_CONTEXT_NO_QUOTES",
	"OBJECT_TYPE_COLON_CONTEXT",
	"OBJECT_TYPE_COLON_CONTEXT_NO_QUOTES"
]

# Check if we are running on a Windows operating system
os_is_windows = os.name == 'nt'

# The default name of the clang-format executable
default_binary = 'HiveAPIQuery.exe' if os_is_windows else 'HiveAPIQuery'

def loadSettings():
	global queryBinary
	global inhibitComp

	settings = sublime.load_settings(settings_file)
	inhibitComp = settings.get("inhibit_other_completions", True)
	queryBinary = settings.get("hive_api_query", default_binary)

# This function taken from Stack Overflow response:
# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None

# Display input panel to update the path.
def updateQueryPath():
    loadSettings()
    w = sublime.active_window()
    w.show_input_panel("Path to HiveAPIQuery: ", queryBinary, setQueryPath, None, None)

def setQueryPath(path):
	settings = sublime.load_settings(settings_file)
	settings.set("hive_api_query", path)
	sublime.save_settings(settings_file)

	loadSettings()

def checkQueryBinary():
	# Make sure we could find the API Binary
	if which(queryBinary) == None:
		# Ask if they want to set it
		if sublime.ok_cancel_dialog("HiveAPIQuery binary was not found. Do you want to set a new path?"):
			updateQueryPath()

##  Once sublime has finished loading, the dictionary can be initialized
#   with the information in the settings file.
#   Sublime executes plugin_loaded once the api is ready to use
def plugin_loaded():
	global DATA_DICTIONARY

	loadSettings()
	checkQueryBinary()

	DATA_DICTIONARY = DataDictionary(queryBinary)

#///////////////////////////////////////////////GLOBAL METHODS/////////////////////////////////////////////////////////////////////

## Method for determining whether the given tokens form the beginning of a parameter tag.
#  @param tokens - a list of strings
#  @returns True if the first two tokens are '<' and 'param'
#  and False otherwise
def isParamTag(tokens):
	return len(tokens) >= 2 and tokens[0] == '<' and tokens[1] == 'param'

## Method for determining whether the given tokens form the beginning of an object tag.
#  @param tokens - a list of strings
#  @returns True if the first two tokens are '<' and 'object'
#  and False otherwise
def isObjectTag(tokens):
	return len(tokens) >=2 and tokens[0] == '<' and tokens[1] == 'object'


## Method that gives the element of the tag
#  at the location.
#  @param view - a view object
#  @param location - an integer for indexing into the view
#  @returns a string or None if no element is found
def getCurrentElementType(view, location):
	index = location -1 #initialize index to location left of cursor

	#get range from current cursor to either the beginning of file or a tag <
	while(index >= 0 and  view.substr(index) != '<' and view.substr(index) != '>'):
		index -= 1

	if(index < 0 or view.substr(index) != '<'):
		return None #the cursor is not in an XML tag

	currentRegion = sublime.Region(index, location)

	currentTag = view.substr(currentRegion)
	tokens = currentTag.replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').split()
	if(len(tokens) <= 1):
		return None
	return tokens[1]

## method that gets the value of the current param element's name attribute.
#  This method does not check whether the current tag is a param tag;
#  It just gets the value of a name attribute if available.
#  @param view - a sublime view object
#  @param location - an integer index into the view
#  @returns a string or None
def getCurrentParamName(view, location):
	index = location -1 #initialize index to location left of cursor

	#get range from current cursor to either the beginning of file or a tag <
	while(index >= 0 and  view.substr(index) != '<' and view.substr(index) != '>'):
		index -= 1

	if(index < 0 or view.substr(index) != '<'):
		return None #the cursor is not in an XML tag

	currentRegion = sublime.Region(index, location)

	currentTag = view.substr(currentRegion)
	tokens = currentTag.replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').split()

	index = 0
	while(index < len(tokens) and tokens[index] != 'name'):
		index = index + 1
	if(index + 3 < len(tokens)):
		return tokens[index + 3]
	else:
		return None


## Method that determines the context of the current cursor
#  @param view - a sublime view object
#  @param location - index for cursor location in the view
#  @param prefix - the current word being typed, which should
#  be removed from the list of tokens
#  @returns an enum value
def getContext(view, location, prefix=""):
	index = location -1 #initialize index to location left of cursor

	charCount = 0
	#get range from current cursor to either the beginning of file or a tag <
	while(index >= 0 and  view.substr(index) != '<' and view.substr(index) != '>' and charCount < 9000):
		index -= 1
		#for optimization, stop looking for < and > after charCount reaches 9000
		charCount += 1

	if(view.substr(index) != '<'):
		return 0 #the cursor is not in an XML tag

	currentRegion = sublime.Region(index, location)

	#currentTag may be an incomplete tag (no '>' )
	currentTag = view.substr(currentRegion)
	tokens = currentTag.replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').split()
	# print("Prefix [%s] CurrTag [%s], Tokens[%s]" % (prefix, currentTag, tokens))

	context = 0
	colonsNotWordSeparator = False
	#user might have begun typing the word to be autocompleted, so remove word if so
	if(len(tokens) != 0 and tokens[-1] == prefix):
		tokens.pop()
	#if the prefix is not found in tokens because of colons not being a word separator
	#then mark the colonsNotWordSeparator flag and pop the last token which ends with prefix
	elif(len(tokens) != 0 and view.substr(location - len(prefix)-1) == ':' and tokens[-1].endswith(prefix)):
		tokens.pop()
		colonsNotWordSeparator = True



	if(len(tokens) >= 5 and tokens[-1] == '\"'
		and tokens[-2] == '=' and tokens[-3] == 'type'
		and isObjectTag(tokens)):

		if(colonsNotWordSeparator):
			context = OBJECT_TYPE_COLON_CONTEXT
		else:
			context = OBJECT_TYPE_CONTEXT

	elif(len(tokens) >=4 and tokens[-1] == '='
		and tokens[-2] == 'type' and isObjectTag(tokens)):

		if(colonsNotWordSeparator):
			context = OBJECT_TYPE_COLON_CONTEXT_NO_QUOTES
		else:
			context = OBJECT_TYPE_CONTEXT_NO_QUOTES


	elif(len(tokens) >= 5 and tokens[-1] == '\"'
		and tokens[-2] == '=' and tokens[-3] == 'name'
		and isParamTag(tokens)):
		context = PARAM_NAME_CONTEXT
	elif(len(tokens) >=4 and tokens[-1] == '='
		and tokens[-2] == 'name' and isParamTag(tokens)):
		   context = PARAM_NAME_CONTEXT_NO_QUOTES
	elif(len(tokens) >= 3 and tokens[-1] == '"'
		and tokens[-2] == '=' and tokens[-3] == 'value'
		and isParamTag(tokens)):
		   context = PARAM_VALUE_CONTEXT
	elif(len(tokens) >= 2 and tokens[-1] == '=' and tokens[-2] == 'value' and isParamTag(tokens)):
		   context = PARAM_VALUE_CONTEXT_NO_QUOTES
	elif(tokens.count('\"') % 2 == 1):
		#odd number means inside of a quote
		#This is here to protect against lists of values
		#for attributes.
		context = ATTRIBUTE_VALUE_CONTEXT
	elif(len(tokens) >= 1 and tokens[-1] == '<'):
		   context = ELEMENT_CONTEXT
	elif(len(tokens) >= 3 and tokens[0] == '<' and tokens[-1] == '\"' and tokens[-2] == '='):
		context = ATTRIBUTE_VALUE_CONTEXT
	elif(len(tokens) >= 2 and tokens[0] == '<'
		and tokens[-1] != '='):
			context = ATTRIBUTE_CONTEXT
	elif(len(tokens) >= 2 and tokens[0] == '<' and tokens[-1] == '='):
		context = ATTRIBUTE_VALUE_CONTEXT_NO_QUOTES

	return context


## returns the object type as a string
#  that a parameter belongs to
#  or none if no object tag is found.
#  Does not check if the tag is an object tag,
#  it simply looks for an attribute called type.
#  @param view - a sublime view object
#  @param location -integer index into view
#  @returns a string
def getParentObjectName(view, location):
	tags = XMLTagIterator(view, location)
	parentTag = tags.getParent()
	if(parentTag is not None):
		tokens = view.substr(parentTag).replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').replace('>', ' > ').split()
	else:
		return None #no parent found

	#get the object type
	i = 0
	while(i < len(tokens) and tokens[i] != 'type'):
		i = i + 1
	if(i + 3 < len(tokens)):
		return tokens[i + 3]  #+ 3 to account for = and " after type
	else:
		return None #object type is not contained in the tag


## Get the element type of the tag governing
#  the current tag.
#  Works similarly to getParentObjectName.
#  Each tag before the current one is assessed
#  to determine where the parent tag is.
#  @returns a string of the element name
#  or 'root' if there is no governing tag (i.e. the root tag)
#  or None if the tag found has less than 2 tokens (which shouldn't be possible)
def getParentTagType(view, location):
	tags = XMLTagIterator(view, location)
	parentTag = tags.getParent()
	if(parentTag is not None):
		tokens = view.substr(parentTag).replace('=', ' = ').replace('<', ' < ').replace('\"', ' \" ').replace('>', ' > ').split()
	else:
		return 'root' #no parent found

	if(len(tokens) >= 2) :
		return tokens[1]  #return element (might return > for an incomplete tag)
	else:
		return None #tokens has less than two items (this shouldn't be possible)

## A method that finds the prefix for an object type
#  when colons are word separators.
#  @param view - a sublime view object
#  @param location - the location in the view where the
#  object type ends
#  @param suffix - the current part of the object type that
#  is being typed (the prefix for autocompletion)
#  @returns a string
def getObjectTypePrefix(view, location, suffix):
	index = location - 1
	while(index >= 0 and view.substr(index) != '=' and view.substr(index) != '\"'):
		index -=1
	return view.substr(sublime.Region(index + 1, location)).rstrip(suffix)

## Filters the object completions list based on
#  a prefix and trims the words based on the prefix.
#  @param completions - a list of trigger-completions pairs.
#  Should not include quotation marks.
#  @param prefix - a string
def filterObjectTypeCompletions(completions, prefix):
	i = len(completions) - 1
	while(i >= 0):
		if(completions[i][0].startswith(prefix)):
			completions[i][0] = completions[i][0].replace(prefix,"",1)
			completions[i][1] = completions[i][1].replace(prefix,"",1)
		else:
			completions.pop(i)
		i -= 1


#//////////////////////////END GLOBAL METHODS/////////////////////////////////////////////////////////////////////////////////////////////////////////////////


## An auto complete plugin
#  that gives context specfic completions for hive files.
#  All other completions are inhibited while using this plugin
class HiveAutoComplete(sublime_plugin.EventListener):
	## Constructor
	def __init__(self):
		## reference to global DATA_DICTIONARY
		self.DD = DATA_DICTIONARY #DATA_DICTIONARY will be None at initialization time


	## Method that feeds Sublime's autocomplete lists
	# returns a list of trigger-completion pairs
	# and possibly a flag preventing sublime from
	# adding its own completions.
	# Only the first cursor is checked
	def on_query_completions(self, view, prefix, locations):

		# we delay loading the dictionary until here because
		# we need to make sure sublime is done loading
		# and has executed plugin_loaded
		if(self.DD is None):
			self.DD = DATA_DICTIONARY

		items = []

		settings = view.settings()
		inXML = view.score_selector(locations[0], AUTOCOMPLETION_SELECTOR)

		#impede plugin if not in an xml file
		if not inXML:
			return items

		context = getContext(view, locations[0], prefix)
		# print("Context = %s(%d)" % (CONTEXT_NAMES[context], context))

		if self.DD is None:
			return items

		if(context == OBJECT_TYPE_CONTEXT):
			items = self.DD.getObjectCompletions()

		elif(context == OBJECT_TYPE_CONTEXT_NO_QUOTES):
			items = self.DD.getObjectCompletions(addQuotes=True)

		elif(context == PARAM_NAME_CONTEXT):
			items = self.DD.getParamCompletions(getParentObjectName(view, locations[0]))

		elif(context == PARAM_NAME_CONTEXT_NO_QUOTES):
			items = self.DD.getParamCompletions(getParentObjectName(view, locations[0]), addQuotes=True)

		elif(context == ELEMENT_CONTEXT):
			items = self.DD.getElementCompletions(getParentTagType(view, locations[0]))

		elif(context == ATTRIBUTE_CONTEXT):
			#get element type of current tag
			element = getCurrentElementType(view, locations[0])
			items = self.DD.getAttributeCompletions(element)


		elif(context == PARAM_VALUE_CONTEXT):
			valPrefix = getObjectTypePrefix(view, locations[0], prefix)
			paramName = getCurrentParamName(view, locations[0])
			parent = getParentObjectName(view, locations[0])
			items = self.DD.getParamValueCompletions(paramName, parent, valPrefix)

		elif(context == PARAM_VALUE_CONTEXT_NO_QUOTES):
			valPrefix = getObjectTypePrefix(view, locations[0], prefix)
			# Force add the quotes
			view.run_command("add_quotes", {"end": locations[0] +1, "start": locations[0] - (len(valPrefix) + len(prefix)) } )
			#move the cursor back before the last quote
			view.run_command("move", {"by": "characters", "forward": False})

			paramName = getCurrentParamName(view, locations[0])
			parent = getParentObjectName(view, locations[0])
			items = self.DD.getParamValueCompletions(paramName, parent, valPrefix, addQuotes=True)

		elif(context == ATTRIBUTE_VALUE_CONTEXT):
			pass
		elif(context ==ATTRIBUTE_VALUE_CONTEXT_NO_QUOTES):
			pass
		elif(context == OBJECT_TYPE_COLON_CONTEXT or context == OBJECT_TYPE_COLON_CONTEXT_NO_QUOTES):
			objPrefix = getObjectTypePrefix(view, locations[0], prefix)

			if(context == OBJECT_TYPE_COLON_CONTEXT_NO_QUOTES):
				#quotes must manually be inserted
				view.run_command("add_quotes", {"end": locations[0] +1, "start": locations[0] - (len(objPrefix) + len(prefix)) } )
				#move the cursor back before the last quote
				view.run_command("move", {"by": "characters", "forward": False})

			if(objPrefix.endswith("::")):
				items = self.DD.getObjectCompletions(prefix=objPrefix)
				# filterObjectTypeCompletions(items, objPrefix)

		items.sort()

		# If there are no items, or we are not preventin other auto complets from being shown
		# then just return the items.
		if len(items) == 0 or not inhibitComp:
			return items;

		return items
		# return (items, sublime.INHIBIT_WORD_COMPLETIONS)

## Plugin that adds quotes at two points
class AddQuotesCommand(sublime_plugin.TextCommand):
	## method executed when the plugin runs.
	#  @param edit - a sublime edit object
	#  @param start - the first place to add quotes
	#  @param end - the second place to add quotes
	def run(self, edit, start, end):
		self.view.insert(edit, start, '\"')
		self.view.insert(edit, end, '\"')

# Called to set the path to the HiveAPIQuery binary
class HiveApiQuerySetPathCommand(sublime_plugin.WindowCommand):
	def run(self):
		updateQueryPath()