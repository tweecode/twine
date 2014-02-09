#!/usr/bin/python

import os, imp
from collections import OrderedDict
from random import shuffle

class Header (object):

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
        
        # Randomise the obfuscate key
        obfuscatekey = list('anbocpdqerfsgthuivjwkxlymz')
        shuffle(obfuscatekey)
        obfuscatekey = ''.join(obfuscatekey)
        
        return [{
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
                "name": "obfuscate",
                "label": "Obfuscate the HTML source to obscure spoilers",
                "values": ("swap","off")
            },{
                "type": "text",
                "name": "obfuscatekey",
                "label": "Obfuscation key:",
                "default": obfuscatekey
            },{
                "type": "text",
                "name": "identity",
                "label": "What your game identifies as:",
                "desc": "Is it a game, a story, a poem, or something else?\n(This is used for dialogs and error messages only.)",
                "default": "game"
            },{
                "type": "checkbox",
                "name": "jquery",
                "label": "Include the jQuery script library?",
                "desc": "Individual scripts may force this on by containing the text 'requires jQuery'.",
            },{
                "type": "checkbox",
                "name": "modernizr",
                "label": "Include the Modernizr script library?",
                "desc": "Individual scripts/stylesheets may force this on by containing the\ntext 'requires Modernizr'.",
            }]
    
    def is_endtag(self, name, tag):
        """Return true if the name is equal to an endtag."""
        return (name == ('end' + tag))

    def nested_macros(self):
        """Returns a list of macro names that support nesting."""
        return ['if', 'silently', 'nobr']
    
    @staticmethod
    def factory(type, path, builtinPath):
        header_def = path + type + '.py'
        if os.access(header_def, os.R_OK):
            py_mod = imp.load_source(type, header_def)
            obj = py_mod.Header(type, path, builtinPath)
        else:
            obj = Header(type, path, builtinPath)
        return obj
