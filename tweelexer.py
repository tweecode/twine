import re
import tweeregex

class TweeLexer(object):
    """Abstract base class that does lexical scanning on TiddlyWiki formatted text.
    """

    def getText(self):
        """Returns the text to lex.
        """
        raise NotImplementedError

    def getHeader(self):
        """Returns the current selected target header for this Twee Lexer.
        """
        raise NotImplementedError

    def passageExists(self, title):
        """Returns whether a given passage exists in the story.
        """
        raise NotImplementedError

    def includedPassageExists(self, title):
        """Returns whether a given passage exists in a StoryIncludes resource.
        """
        raise NotImplementedError

    def applyStyle(self, start, end, style):
        """Applies a style to a certain range.
        """
        raise NotImplementedError

    def lexMatchToken(self, text):
        m = text[:2].lower()
        if m in self.MARKUPS:
            return (self.MARKUP, self.MARKUPS[m])

        # link
        m = re.match(tweeregex.LINK_REGEX,text,re.U|re.I)
        if m: return (self.GOOD_LINK, m)

        # macro
        m = re.match(tweeregex.MACRO_REGEX,text,re.U|re.I)
        if m: return (self.MACRO, m)

        # image (cannot have interior markup)
        m = re.match(tweeregex.IMAGE_REGEX,text,re.U|re.I)
        if m: return (self.IMAGE, m)

        # Old-version HTML block (cannot have interior markup)
        m = re.match(tweeregex.HTML_BLOCK_REGEX,text,re.U|re.I)
        if m: return (self.HTML_BLOCK, m)

        # Inline HTML tags
        m = re.match(tweeregex.HTML_REGEX,text,re.U|re.I)
        if m: return (self.HTML, m)

        # Inline styles
        m = re.match(tweeregex.INLINE_STYLE_REGEX,text,re.U|re.I)
        if m: return (self.INLINE_STYLE, m)

        # Monospace
        m = re.match(tweeregex.MONO_REGEX,text,re.U|re.I)
        if m: return (self.MONO, m)

        # Comment
        m = re.match(tweeregex.COMMENT_REGEX,text,re.U|re.I)
        if m: return (self.COMMENT, m)

        return (None, None)

    def lex(self):
        """Performs lexical analysis on the text.
        Calls applyStyle() for each region found.
        """

        def applyParamStyle(pos2, contents):
            iterator = re.finditer(tweeregex.MACRO_PARAMS_REGEX, contents, re.U)
            for param in iterator:
                if param.group(1):
                    # String
                    self.applyStyle(pos2 + param.start(1), len(param.group(1)), self.PARAM_STR)
                elif param.group(2):
                    # Number
                    self.applyStyle(pos2 + param.start(2), len(param.group(2)), self.PARAM_NUM)
                elif param.group(3):
                    # Boolean or null
                    self.applyStyle(pos2 + param.start(3), len(param.group(3)), self.PARAM_BOOL)
                elif param.group(4):
                    # Variable
                    self.applyStyle(pos2 + param.start(4), len(param.group(4)), self.PARAM_VAR)

        def applyMacroStyle(pos, m):
            length = m.end(0)
            if self.passageExists(m.group(1)):
                self.applyStyle(pos, length, self.GOOD_LINK)
            elif self.includedPassageExists(m.group(1)):
                self.applyStyle(pos, length, self.STORYINCLUDE_LINK)
            else:
                self.applyStyle(pos, length, self.MACRO)
            # Apply different style to the macro contents
            group = 2 if m.group(1)[0] != '$' else 1
            contents = m.group(group)
            if contents:
                pos2 = pos + m.start(group)
                self.applyStyle(pos2, len(m.group(group)), self.PARAM)
                applyParamStyle(pos2, contents)

        pos = 0
        text = self.getText()
        style = self.DEFAULT
        styleStack = []
        styleStart = pos
        inSilence = False
        macroNestStack = [] # macro nesting
        header = self.getHeader()

        self.applyStyle(0, len(text), self.DEFAULT)

        iterator = re.finditer(re.compile(tweeregex.COMBINED_REGEX, re.U|re.I), text[pos:])

        for p in iterator:
            pos = p.start()

            nextToken, m = self.lexMatchToken(p.group(0))

            # important: all style ends must be handled before beginnings
            # otherwise we start treading on each other in certain circumstances

            # markup
            if not inSilence and nextToken == self.MARKUP:
                if (style <= self.THREE_STYLES and style & m) or style == self.MARKUP:
                    self.applyStyle(styleStart, pos-styleStart+2, style)
                    style = styleStack.pop() if styleStack else self.DEFAULT
                    styleStart = pos+2
                else:
                    self.applyStyle(styleStart, pos-styleStart, style)
                    styleStack.append(style)
                    markup = m
                    if markup <= self.THREE_STYLES and style <= self.THREE_STYLES:
                        style |= markup
                    else:
                        style = markup
                    styleStart = pos
                pos += 1

            #link
            elif nextToken == self.GOOD_LINK:
                length = m.end(0)
                self.applyStyle(styleStart, pos-styleStart, style)

                # check for prettylinks
                s2 = self.GOOD_LINK
                if not m.group(2):
                    if self.includedPassageExists(m.group(1)):
                        s2 = self.STORYINCLUDE_LINK
                    elif not self.passageExists(m.group(1)):
                        s2 = TweeLexer.linkStyle(m.group(1))
                else:
                    if self.includedPassageExists(m.group(2)):
                        s2 = self.STORYINCLUDE_LINK
                    elif not self.passageExists(m.group(2)):
                        s2 = TweeLexer.linkStyle(m.group(2))
                self.applyStyle(pos, length, s2)
                # Apply a plainer style to the text, if any
                if m.group(2):
                    self.applyStyle(pos + m.start(1), len(m.group(1)), self.BOLD)
                if m.group(3):
                    self.applyStyle(pos + m.start(3), len(m.group(3)), self.PARAM)
                    applyParamStyle(pos + m.start(3), m.group(3))
                pos += length-1
                styleStart = pos+1

            #macro
            elif nextToken == self.MACRO:
                name = m.group(1)
                length = m.end(0)
                # Finish the current style
                self.applyStyle(styleStart, pos-styleStart, style)
                styled = False

                for i in header.nestedMacros():
                    # For matching pairs of macros (if/endif etc)
                    if name == i:
                        styled = True
                        macroNestStack.append((i,pos, m))
                        if i=="silently":
                            inSilence = True
                            styleStack.append(style)
                            style = self.SILENT
                    elif header.isEndTag(name, i):
                        if macroNestStack and macroNestStack[-1][0] == i:
                            # Re-style open macro
                            macroStart,macroMatch = macroNestStack.pop()[1:]
                            applyMacroStyle(macroStart,macroMatch)
                        else:
                            styled = True
                            self.applyStyle(pos, length, self.BAD_MACRO)
                        if i=="silently":
                            inSilence = False
                            style = styleStack.pop() if styleStack else self.DEFAULT

                if not styled:
                    applyMacroStyle(pos,m)
                pos += length-1
                styleStart = pos+1

            # image (cannot have interior markup)
            elif nextToken == self.IMAGE:
                length = m.end(0)
                self.applyStyle(styleStart, pos-styleStart, style)
                # Check for linked images
                if m.group(5):
                    self.applyStyle(pos, m.start(5), self.IMAGE)
                    if not self.passageExists(m.group(5)):
                        s2 = TweeLexer.linkStyle(m.group(5))
                        self.applyStyle(pos+m.start(5)-1, (m.end(5)-m.start(5))+2, s2)
                    else:
                        self.applyStyle(pos+m.start(5)-1, (m.end(5)-m.start(5))+2, self.GOOD_LINK)
                    self.applyStyle(pos+length-1,1, self.IMAGE)
                else:
                    self.applyStyle(pos, length, self.IMAGE)
                pos += length-1
                styleStart = pos+1

            # Inline styles
            elif not inSilence and nextToken == self.INLINE_STYLE:
                if style == self.INLINE_STYLE or style == self.BAD_INLINE_STYLE:
                    self.applyStyle(styleStart, pos-styleStart+2, style)
                    style = styleStack.pop() if styleStack else self.DEFAULT
                    styleStart = pos+2
                else:
                    self.applyStyle(styleStart, pos-styleStart, style)
                    styleStack.append(style)
                    n = re.match(tweeregex.INLINE_STYLE_PROP_REGEX,text[pos+2:],re.U|re.I)
                    if n:
                        style = self.INLINE_STYLE
                        length = len(n.group(0))+2
                    else:
                        style = self.BAD_INLINE_STYLE
                        length = 2
                    styleStart = pos
                    pos += length-1

            # others
            elif nextToken in [self.HTML, self.HTML_BLOCK, self.COMMENT, self.MONO]:
                length = m.end(0)
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, nextToken)
                pos += length-1
                styleStart = pos+1

        # Finish up unclosed styles
        self.applyStyle(styleStart, len(text), style)

        # Fix up unmatched macros
        while macroNestStack:
            macroStart,macroMatch = macroNestStack.pop()[1:]
            self.applyStyle(macroStart, macroMatch.end(0), self.BAD_MACRO)

    @staticmethod
    def linkStyle(dest):
        """Apply style for a link destination which does not seem to be an existent passage"""
        for t in ['http:', 'https:', 'ftp:', 'mailto:', 'javascript:', 'data:', r'[\./]*/']:
            if re.match(t, dest.lower()):
                return TweeLexer.EXTERNAL
        iscode = re.search(tweeregex.MACRO_PARAMS_VAR_REGEX+"|"+tweeregex.MACRO_PARAMS_FUNC_REGEX, dest, re.U)
        return TweeLexer.PARAM if iscode else TweeLexer.BAD_LINK

    # style constants
    # ordering of BOLD through to THREE_STYLES is important
    STYLE_CONSTANTS = range(0,28)
    DEFAULT, BOLD, ITALIC, BOLD_ITALIC, UNDERLINE, BOLD_UNDERLINE, ITALIC_UNDERLINE, THREE_STYLES, \
    GOOD_LINK, STORYINCLUDE_LINK, BAD_LINK, MARKUP, MACRO, BAD_MACRO, SILENT, COMMENT, MONO, IMAGE, EXTERNAL, HTML, HTML_BLOCK, INLINE_STYLE, \
    BAD_INLINE_STYLE, PARAM_VAR, PARAM_STR, PARAM_NUM, PARAM_BOOL, PARAM = STYLE_CONSTANTS

    # markup constants

    MARKUPS = {"''" : BOLD, "//" : ITALIC, "__" : UNDERLINE, "^^" : MARKUP, "~~" : MARKUP, "==" : MARKUP}

    # nested macros

    NESTED_MACROS = [ "if", "silently" ]


class VerifyLexer(TweeLexer):
    """Looks for errors in passage bodies.
    """

    # Takes a PassageWidget instead of a PassageFrame
    def __init__(self, widget):
        self.widget = widget
        self.twineChecks, self.stylesheetChecks, self.scriptChecks = self.getHeader().passageChecks()

    def getText(self):
        return self.widget.passage.text

    def getHeader(self):
        return self.widget.parent.parent.header

    def passageExists(self, title):
        return self.widget.parent.passageExists(title, False)

    def includedPassageExists(self, title):
        return self.widget.parent.includedPassageExists(title)

    def check(self):
        """Collect error messages for this passage, using the overridden applyStyles() method."""
        self.errorList = []
        if self.widget.passage.isScript():
            for i in self.scriptChecks:
                self.errorList += [e for e in i(passage=self.widget.passage)]

        elif self.widget.passage.isStylesheet():
            for i in self.stylesheetChecks:
                self.errorList += [e for e in i(passage=self.widget.passage)]

        else:
            self.lex()
        return sorted(self.errorList, key = lambda a: (a[1][0] if a[1] else float('inf')))

    def applyStyle(self, start, length, style):
        """Runs all of the checks on the current lex token, then saves errors produced."""
        end = start+length
        tag = self.widget.passage.text[start:end]
        for i in self.twineChecks:
            self.errorList += [e for e in i(tag, start=start, end=end, style=style, passage=self.widget.passage)]
