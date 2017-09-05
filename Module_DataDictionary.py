#!/usr/bin/python3

## Dictionary data structures.
#  @package Module_DataDictionary
#  @author Vincent Yahna
#
#  Data structures for storing
#  information about the structure
#  of an XML syntax.

import json
import subprocess
import os

## Abstract class for different dictionary formats.
#  The dictionaries are to be used for context-sensitive
#  autocompletion and displaying help information.
#  Initialize dictionary with a path to the file that stores the data
#  the dictionary will have components mapping objects to the parameters
#  they have and elements to elements that can go underneath them and
#  elements to attributes that they can have.
#  The dictionary can also be intialized with a python dictionary
#  of the same structure.
class DataDictionary:

	def __init__(self, queryBin):
		# This is the HiveAPIQuery executable
		self.queryBin = queryBin

		# Build the list of XML Elements & Attributs that the HIVE Parser supports loading
		self.elements = {
				"root" :
					[
						["hive"],
						[]
					],
				"hive" :
					[
						["metaParam", "object", "encrypted", "export", "system", "file", "platform", "param", "unclassified", "confidential", "secret", "topsecret", "script", "playback"],
						[]
					],
				"object" :
					[
						["metaParam", "object", "encrypted", "export", "system", "file", "platform", "param", "unclassified", "confidential", "secret", "topsecret", "script", "playback"],
						["id", "type", "entityID", "append", "serialize"]
					],
				"encrypted" :
					[
						["encryptionMethod", "cipherData"],
						[]
					],
				"param" :
					[
						[],
						["name", "value"]
					],
				"file" :
					[
						[],
						["name"]
					],
				"unclassified" :
					[
						["controlSystems", "isFGI", "isNATO", "foreignGovernments", "dissemination", "proprietary", "citation"],
						[]
					],
				"confidential" :
					[
						["controlSystems", "isFGI", "isNATO", "foreignGovernments", "dissemination", "proprietary", "citation"],
						[]
					],
				"secret" :
					[
						["controlSystems", "isFGI", "isNATO", "foreignGovernments", "dissemination", "proprietary", "citation"],
						[]
					],
				"topsecret" :
					[
						["controlSystems", "isFGI", "isNATO", "foreignGovernments", "dissemination", "proprietary", "citation"],
						[]
					],
				"citation" :
					[
						[],
						["lastName", "firstName", "version", "organization", "titleOfArticle", "title", "city", "publisher", "pagesBegin", "pagesEnd", "medium", "volume", "issue", "year", "exportControlled", "destructionNotice", "classificationReason", "derivedFrom", "declassification", "distributionStatementDate", "distributionStatementReleasingAuthorityMailingAddress", "distributionStatement", "distributionStatementReason", "classificationOfDocument", "classificationOfTitle"]
					]
			}

	## Runs the HiveAPIQuery tool and requests API information that can be used for autocomplete.
	# @param query - Which type of API information to return (type, channel, value, dis)
	# @param typ - This is the HIVE class to use in the query (acts as filter of query=type)
	# @param channel - The HIVE channel to query (acts as filter if query=channel)
	# @param value - The filter to use when checking for a HIVE channel's possible values
	def apiQuery(self, query, typ="", channel="", value="", dis=""):

		objs = []

		# Don't try to run the tool unless it exists and is executable
		if os.path.isfile(self.queryBin) and os.access(self.queryBin, os.X_OK):
	        # Hide the console window on Windows
			startupinfo = None
			if os.name == "nt":
				startupinfo = subprocess.STARTUPINFO()
				startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

			cmd = [self.queryBin, query]
			if typ != "":
				cmd.append('--type=%s' % typ)
			if channel != "":
				cmd.append('--channel=%s' % channel)
			if value != "":
				cmd.append('--value=%s' % value)
			if dis != "":
				cmd.append('--dis=%s' % dis)

			# They asked for a list of available object types, so lets ask HIVE
			apiStr = subprocess.check_output(cmd, timeout=10, universal_newlines=True,startupinfo=startupinfo)

			try:
				objs = json.loads(apiStr)
			except Exception as e:
				print("Exception while converting HiveAPIQuery results [%s] from JSON. Exception %s" % (apiStr, e))
		else:
			print("HiveAPIQuery binary was not found! [%s]" % self.queryBin)

		# print("Query {%s} returned [%s]" % (cmd, apiStr))
		return objs


	## Get a list of objects that can be passed to sublime's autocompletion plugin.
	#  @param addQuotes - boolean indicating whether to add quotes around the object type
	#  @returns a list of pairs of strings (trigger-completion pairs)
	def getObjectCompletions(self, prefix="", addQuotes = False):

		# Running the HiveAPQuery tool every time isn't the fastest thing, we might want to just save a
		# list of all the objects and only updated it if the HIVEAPIQuery tool is rebuilt, or like every 5mins.
		quotes = ''
		if addQuotes == True:
			quotes = '\"' #add quotes to the completion

		completions = []
		results = self.apiQuery("type", prefix)
		for obj in results:
			val = obj.replace(prefix, "", 1)
			completions.append([val, quotes + val + quotes])

			# If we had descriptions for the classes we would use
			# completions.append([val + "\t" + desc, quotes + val + quotes])

		return completions

	## Get a list of param names that can be passed to sublime's autocompletion plugin.
	#  @param objectType - the type of this parameter's parent object
	#  @param addQuotes - boolean indicating whether to add quotes around the param name
	#  @returns a list of pairs of strings (trigger-completion pairs)
	def getParamCompletions(self, objectType, addQuotes = False):

		quotes = ''
		if addQuotes == True:
			quotes = '\"' #add quotes to the completion

		completions = []
		results = self.apiQuery("channel", objectType)
		for param in results:
			completions.append([param[0] + "\t" + param[1], quotes + param[0] + quotes])

		return completions

	## Get a list of parameter values to pass to autocompletion
	#  @param paramName - a string of the parameter's name
	#  @param addQuotes - boolean indicating whether to add quotes around the param name
	#  @param objectType - the parent object type of the parameter
	#  @returns a list of pairs of strings
	def getParamValueCompletions(self, paramName, objectType, prefix = '', addQuotes=False):

		quotes = ''
		if(addQuotes):
			quotes = '\"'

		completions = []

		if paramName == "disEnumeration":
			# To prevent DIS Query tool from lagging, don't ask for DIS suggestions
			# unless there are at least 3 charaters in the string
			if len(prefix) >= 3:
				results = self.apiQuery("dis", objectType, paramName, dis=prefix)
				for v in results:
					asterix = ""
					if v[2] == 1:
						asterix = "*"

					completions.append([v[0] + "\t" + asterix + v[1], quotes + v[0].replace(prefix, "", 1) + quotes])
		else:
			results = self.apiQuery("value", objectType, paramName)
			for v in results:
				completions.append([v[0] + "\t" + str(v[1]), quotes + str(v[0]) + quotes])

		return completions


	## Get a list of elements to pass to autocompletion.
	#  @param element - the governing element above the current tag
	#  @returns a list of pairs of strings
	def getElementCompletions(self, element):
		completions = []
		if (self.elements is not None) and (element in self.elements):
			for el in self.elements[element][0]:
				completions.append([el, el])

		return completions

	## Get a list of attributes to pass to autocompletion.
	#  @param element - the element type of the current tag
	#  @returns a list of pairs of strings
	def getAttributeCompletions(self, element):
		completions = []
		if (self.elements is not None) and (element in self.elements):
			for attr in self.elements[element][1]:
				completions.append([attr, attr])

		return completions