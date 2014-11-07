import sublime, sublime_plugin
import os, re

class HiveOpenFileCommand(sublime_plugin.TextCommand):
	def run(self, edit):		
		print('OpenFile')
		# Check the first selection
		s = self.view.sel()[0]

		# Make sure its a hive.log.file section
		if self.view.scope_name(s.begin()).find("hive.log.file") != -1:
			# Extract out just the file info
			fullLogFile = self.view.substr(self.view.extract_scope(s.begin()))
			matchObj = re.match( r'([^\(]+)\(([0-9]+)\)', fullLogFile)
			if matchObj:
				if os.path.exists(matchObj.group(1)):
					# Open the file and wait until its done loading
					fileView = self.view.window().open_file(matchObj.group(1))	
					sublime.set_timeout(lambda: self.select_text(fileView, matchObj.group(2)), 10)

	def select_text(self, view, line):
		print("Waiting on load")
		if not view.is_loading():
			sublime.status_message('this line is processed')
			view.run_command("goto_line", {"line": line} )
		else:
			sublime.set_timeout(lambda: self.select_text(view, line), 10)					
