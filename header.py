import os, imp, re, tweeregex, tweelexer
from collections import OrderedDict

class Header(object):
    # The name "id" is too short and is the name of a builtin, but it's part of the interface now.
    # pylint: disable=invalid-name,redefined-builtin

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
        """
        Returns a list of StorySettings dictionaries.
        Alternatively, it could return a string saying that it isn't supported, and suggesting an alternative.
        """

        return [{
                "type": "checkbox",
                "name": "undo",
                "label": "Let the player undo moves",
                "desc": "In Sugarcane, this enables the browser's back button.\n"
                        "In Jonah, this lets the player click links in previous passages.",
                "default": "on"
            },{
                "type": "checkbox",
                "name": "bookmark",
                "label": "Let the player use passage bookmarks",
                "desc": "This enables the Bookmark links in Jonah and Sugarcane.\n"
                        "(If the player can't undo, bookmarks are always disabled.)",
                "requires": "undo",
                "default": "on"
            },{
                "type": "checkbox",
                "name": "hash",
                "label": "Automatic URL hash updates",
                "desc": "The story's URL automatically updates, so that it always links to the\n"
                        "current passage. Naturally, this renders the bookmark link irrelevant.",
                "requires": "undo",
                "default": "off"
            },{
                "type": "checkbox",
                "name": "exitprompt",
                "label": "Prompt before closing or reloading the page",
                "desc": "In most browsers, this asks the player to confirm closing or reloading the\n"
                        "page after they've made at least 1 move.",
                "default": "off"
            },{
                "type": "checkbox",
                "name": "blankcss",
                "label": "Don't use the Story Format's default CSS",
                "desc": "Removes most of the story format's CSS styling, so that you can\n"
                        "write stylesheets without having to override the default styles.\n"
                        "Individual stylesheets may force this on by containing the text 'blank stylesheet'",
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
                "desc": "This enables the jQuery() function and the $() shorthand.\n"
                        "Individual scripts may force this on by containing the text 'requires jQuery'.",
            },{
                "type": "checkbox",
                "name": "modernizr",
                "label": "Include the Modernizr script library?",
                "desc": "This adds CSS classes to the <html> element that can be used to write\n"
                        "more compatible CSS or scripts. See http://modernizr.com/docs for details.\n"
                        "Individual scripts/stylesheets may force this on by containing the\n"
                        "text 'requires Modernizr'.",
            }]

    def isEndTag(self, name, tag):
        """Return true if the name is equal to an endtag."""
        return name == ('end' + tag)

    def nestedMacros(self):
        """Returns a list of macro names that support nesting."""
        return ['if', 'silently', 'nobr']

    def passageTitleColor(self, passage):
        """
        Returns a tuple pair of colours for a given passage's title.
        Colours can be HTML 1 hex strings like "#555753", or int triples (85, 87, 83)
        or wx.Colour objects.
        First is the normal colour, second is the Flat Design(TM) colour.
        """
        if passage.isScript():
            return ((89, 66, 28),(226, 170, 80))
        elif passage.isStylesheet():
            return ((111, 49, 83),(234, 123, 184))
        elif passage.isInfoPassage():
            return ((28, 89, 74), (41, 214, 113))
        elif passage.title == "Start":
            return ("#4ca333", "#4bdb24")

    def invisiblePassageTags(self):
        """Returns a list of passage tags which, for whatever reason, shouldn't be displayed on the Story Map."""
        return frozenset()

    def passageChecks(self):
        """
        Returns tuple of list of functions to perform on the passage whenever it's closed.
        The main tuple's three lists are: Twine checks, then Stylesheet checks, then Script checks.
        """

        """
        Twine code checks
        Each function should return an iterable (or be a generator) of tuples containing:
            * warning message string,
            * None, or a tuple:
                * start index where to begin substitution
                * string to substitute
                * end index
        """
        # Arguments are part of the interface even if the default implementation doesn't use them.
        # pylint: disable=unused-argument
        def checkUnmatchedMacro(tag, start, end, style, passage=None):
            if style == tweelexer.TweeLexer.BAD_MACRO:
                matchKind = "start" if "end" in tag else "end"
                yield ("The macro tag " + tag + "\ndoes not have a matching " + matchKind + " tag.", None)

        def checkInequalityExpression(tag, start, end, style, passage=None):
            if style == tweelexer.TweeLexer.MACRO:
                r = re.search(r"\s+((and|or|\|\||&&)\s+([gl]te?|is|n?eq|(?:[=!<]|>(?!>))=?))\s+" + tweeregex.UNQUOTED_REGEX, tag)
                if r:
                    yield (tag + ' contains "' + r.group(1) + '", which isn\'t valid code.\n'
                            + 'There should probably be an expression, or a variable, between "' + r.group(2) + '" and "' + r.group(3) + '".', None)

        def checkIfMacro(tag, start, end, style, passage=None):
            if style == tweelexer.TweeLexer.MACRO:
                ifMacro = re.search(tweeregex.MACRO_REGEX.replace(r"([^>\s]+)", r"(if\b|else ?if\b)"), tag)
                if ifMacro:
                    # Check that the single = assignment isn't present in an if/elseif condition.
                    r = re.search(r"([^=<>!~])(=(?!=))(.?)" + tweeregex.UNQUOTED_REGEX, tag)
                    if r:
                        warning = tag + " contains the = operator.\nYou must use 'is' instead of '=' in <<if>> and <<else if>> tags."
                        insertion = "is"
                        if r.group(1) != " ":
                            insertion = " "+insertion
                        if r.group(3) != " ":
                            insertion += " "
                        # Return the warning message, and a 3-tuple consisting of
                        # start index of replacement, the replacement, end index of replacement
                        yield (warning, (start+r.start(2), insertion, start+r.end(2)))

        def checkHTTPSpelling(tag, start, end, style, passage=None):
            if style == tweelexer.TweeLexer.EXTERNAL:
                # Corrects the incorrect spellings "http//" and "http:/" (and their https variants)
                regex = re.search(r"\bhttp(s?)(?:\/\/|\:\/(?=[^\/]))", tag)
                if regex:
                    yield (r"You appear to have misspelled 'http" + regex.group(1) + "://'.",
                            (start+regex.start(0), "http" + regex.group(1) + "://", start+regex.end(0)))

        """
        Script checks
        """
        def checkScriptTagsInScriptPassage(passage):
            # Check that a script passage does not contain "<script type='text/javascript'>" style tags.
            ret = []
            scriptTags = re.finditer(r"(?:</?script\b[^>]*>)" + tweeregex.UNQUOTED_REGEX, passage.text)
            for scriptTag in scriptTags:
                warning = "This script contains " + scriptTag.group(0) + ".\nScript passages should only contain Javascript code, not raw HTML."
                ret.append((warning, (scriptTag.start(0), "", scriptTag.end(0))))
            return ret

        return ([checkUnmatchedMacro, checkInequalityExpression, checkIfMacro, checkHTTPSpelling],[],[checkScriptTagsInScriptPassage])

    @staticmethod
    def factory(type, path, builtinPath):
        header_def = path + type + '.py'
        if os.access(header_def, os.R_OK):
            py_mod = imp.load_source(type, header_def)
            obj = py_mod.Header(type, path, builtinPath)
        else:
            obj = Header(type, path, builtinPath)
        return obj

