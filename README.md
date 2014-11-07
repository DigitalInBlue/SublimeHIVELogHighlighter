# HIVE Log Highlighter

## Summary

Syntax highlighter for Hybrid Integration and Visualization Engine (HIVE) log files (.nlog).  

## Requires
* HIVE

## Installation
To install the HIVE Log Highlighter use the [Package Control](http://wbond.net/sublime_packages/package_control) installer.

You can also do a manual installation by cloning this repository into your Packages folder. Sublime Text -> Preferences -> Browse Packages...

```git clone git@github.com:DigitalInBlue/SublimeHIVELogHighlighter.git```

## Setup
Once installed you will want to change your Color Scheme to ensure the colors match what is displayed in the terminal window when running HIVE. To
change the color scheme in Sublime Text select Preferences -> Color Scheme -> HIVE Log File -> Hive-Monokai

The Hive-Monokai color scheme is very similar to the Monokai color scheme with a few modifications to ensure the log level colors match
what is seen in the HIVE console window.

## Usage
* Open a HIVE .nlog file with Sublime Text.
* You can also open the HIVE source file at the line that generated the log message by:
  * Right click on the file name and select "HIVE Open File" from the context menu
  * Clicking on the file name and pressing Ctrl+Enter
  * Alt+Double Left click on the file name

## Upcomming features
* Ability to open input files at that line that caused the log message to be written.

## Making Changes
The syntax highlighting rules were written in YAML and then converted to the tmLanguage format using the 
[AAAPackageDev](https://bitbucket.org/guillermooo/aaapackagedev) plugin.
