import os, imp, re, tweeregex
from collections import OrderedDict
from random import shuffle

class Header(object):

    def __init__(self, id, path, builtinPath):
        self.id = id.lower()
        self.path = path
        self.label = id.capitalize()
        self.builtinPath = builtinPath

    def filesToEmbed(self):
        """Returns an Ordered Dictionary of file names to embed into the output.

        The item key is the label to look for within the output.
        The item value is the name of the file who's contents will be embedded into the output.

        Internal headers referring to files outside their folders should use
        the following form for paths: self.builtinPath + ...

        External headers must use the following form for paths: self.path + "filename.js"
        """
        return OrderedDict([
            ('"JONAH"', self.builtinPath + os.sep + 'jonah' + os.sep + 'code.js'),
            ('"SUGARCANE"', self.builtinPath + os.sep + 'sugarcane' + os.sep + 'code.js'),
            ('"ENGINE"', self.builtinPath + os.sep + 'engine.js')
        ])

    def storySettings(self):
        """Returns a list of StorySettings dictionaries."""

        return [{
                "type": "text",
                "name": "identity",
                "label": "What your work identifies as:",
                "desc": "Is it a game, a story, a poem, or something else?\n(This is used for dialogs and error messages only.)",
                "default": "game"
            },{
                "type": "text",
                "name": "description",
                "label": "A short description of your work:",
                "desc": "This is inserted in the HTML file's <meta> description tag, used by\nsearch engines and other automated tools.",
                "default": ""
            },{
                "type": "checkbox",
                "name": "undo",
                "label": "Let the player undo moves",
                "desc": "In Sugarcane, this enables the browser's back button.\nIn Jonah, this lets the player click links in previous passages.",
                "default": "on"
            },{
                "type": "checkbox",
                "name": "bookmark",
                "label": "Let the player use passage bookmarks",
                "desc": "This enables the Bookmark links in Jonah and Sugarcane.\n(If the player can't undo, bookmarks are always disabled.)",
                "default": "on"
            },{
                "type": "checkbox",
                "name": "exitprompt",
                "label": "Prompt before closing or reloading the page",
                "desc": "In most browsers, this asks the player to confirm closing or reloading the \npage after they've made at least 1 move.",
                "default": "off"
            },{
                "type": "checkbox",
                "name": "obfuscate",
                "label": "Use ROT13 to obscure spoilers in the HTML source code?",
                "values": ("rot13", "off"),
                "default": "off"
            },{
                "type": "checkbox",
                "name": "jquery",
                "label": "Include the jQuery script library?",
                "desc": "This enables the jQuery() function and the $() shorthand.\nIndividual scripts may force this on by containing the text 'requires jQuery'.",
            },{
                "type": "checkbox",
                "name": "modernizr",
                "label": "Include the Modernizr script library?",
                "desc": "This adds CSS classes to the <html> element that can be used to write\nmore compatible CSS or scripts. See http://modernizr.com/docs for details.\nIndividual scripts/stylesheets may force this on by containing the\ntext 'requires Modernizr'.",
            }]

    def isEndTag(self, name, tag):
        """Return true if the name is equal to an endtag."""
        return (name == ('end' + tag))

    def nestedMacros(self):
        """Returns a list of macro names that support nesting."""
        return ['if', 'silently', 'nobr']
    
    def passageChecks(self):
        """
        Returns a list of checks to perform on the passage whenever it's closed.
        Each function should return a string warning message, or None
        """
        def checkIfMacro(passage):
            # Check that the single = assignment isn't present in an if/elseif condition.
            ifMacroRegex = tweeregex.MACRO_REGEX.replace(r"([^>\s]+)", r"(if\b|else ?if\b)")
            iter = re.finditer(ifMacroRegex, passage.text)
            for i in iter:
                if re.search(r"[^=<>!~]=(?!=)" + tweeregex.UNQUOTED_REGEX, i.group(2)):
                    return i.group(0) + " contains the = operator.\nPlease use 'is' instead of '=' in <<if>> and <<else>> tags."
        
        def checkScriptTagInScriptPassage(passage):
            # Check that s script passage does not contain "<script type='text/javascript>" style tags.
            if passage.isScript():
                if re.search(r"(?:</?script\b(?:[^>]|>" + tweeregex.QUOTED_REGEX + ")*>)" + tweeregex.UNQUOTED_REGEX, passage.text):
                    return "This script contains a HTML <script> tag.\nScript passages should only contain Javascript code, not raw HTML."
        
        return [checkIfMacro, checkScriptTagInScriptPassage]

    @staticmethod
    def factory(type, path, builtinPath):
        header_def = path + type + '.py'
        if os.access(header_def, os.R_OK):
            py_mod = imp.load_source(type, header_def)
            obj = py_mod.Header(type, path, builtinPath)
        else:
            obj = Header(type, path, builtinPath)
        return obj
