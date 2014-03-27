import re, wx, wx.stc
import tweeregex

class TweeLexer:
    """
    This lexes (or syntax highlights) Twee syntax in a wx.StyledTextCtrl.
    This needs to be passed the control it will be lexing, so it can
    look up the body text as needed.
    """

    def __init__(self, control, frame):
        self.ctrl = control
        self.frame = frame
        self.app = frame.app
        self.ctrl.Bind(wx.stc.EVT_STC_STYLENEEDED, self.lex)
        self.initStyles()

    def initStyles(self):
        """
        Initialize style definitions. This is automatically invoked when
        the constructor is called, but should be called any time font
        preferences are changed.
        """
        bodyFont = wx.Font(self.app.config.ReadInt('windowedFontSize'), wx.MODERN, wx.NORMAL, \
                           wx.NORMAL, False, self.app.config.Read('windowedFontFace'))
        monoFont = wx.Font(self.app.config.ReadInt('monospaceFontSize'), wx.MODERN, wx.NORMAL, \
                           wx.NORMAL, False, self.app.config.Read('monospaceFontFace'))

        self.ctrl.StyleClearAll()

        # Styles 1-8 are BOLD, ITALIC, UNDERLINE, and bitwise combinations thereof
        for i in range(0,8):
            self.ctrl.StyleSetFont(i, bodyFont)
            if (i & 1):
                self.ctrl.StyleSetBold(i, True)
            if (i & 2):
                self.ctrl.StyleSetItalic(i, True)
            if (i & 4):
                self.ctrl.StyleSetUnderline(i, True)

        for i in [self.GOOD_LINK, self.BAD_LINK, self.STORYINCLUDE_LINK, self.MARKUP, self.INLINE_STYLE, self.BAD_INLINE_STYLE,
                  self.HTML, self.HTML_BLOCK, self.MACRO, self.COMMENT, self.SILENT, self.EXTERNAL,
                  self.IMAGE, self.PARAM, self.PARAM_VAR, self.PARAM_STR, self.PARAM_NUM, self.PARAM_BOOL]:
            self.ctrl.StyleSetFont(i, bodyFont)

        self.ctrl.StyleSetBold(self.GOOD_LINK, True)
        self.ctrl.StyleSetForeground(self.GOOD_LINK, self.GOOD_LINK_COLOR)

        self.ctrl.StyleSetBold(self.BAD_LINK, True)
        self.ctrl.StyleSetForeground(self.BAD_LINK, self.BAD_LINK_COLOR)
        
        self.ctrl.StyleSetBold(self.STORYINCLUDE_LINK, True)
        self.ctrl.StyleSetForeground(self.STORYINCLUDE_LINK, self.STORYINCLUDE_COLOR)

        self.ctrl.StyleSetForeground(self.MARKUP, self.MARKUP_COLOR)

        self.ctrl.StyleSetForeground(self.INLINE_STYLE, self.MARKUP_COLOR)

        self.ctrl.StyleSetBold(self.BAD_INLINE_STYLE, True)
        self.ctrl.StyleSetForeground(self.BAD_INLINE_STYLE, self.BAD_LINK_COLOR)

        self.ctrl.StyleSetBold(self.HTML, True)
        self.ctrl.StyleSetForeground(self.HTML, self.HTML_COLOR)

        self.ctrl.StyleSetForeground(self.HTML_BLOCK, self.HTML_COLOR)

        self.ctrl.StyleSetBold(self.MACRO, True)
        self.ctrl.StyleSetForeground(self.MACRO, self.MACRO_COLOR)

        self.ctrl.StyleSetItalic(self.COMMENT, True)
        self.ctrl.StyleSetForeground(self.COMMENT, self.COMMENT_COLOR)

        self.ctrl.StyleSetForeground(self.SILENT, self.COMMENT_COLOR)

        self.ctrl.StyleSetFont(self.MONO, monoFont)

        self.ctrl.StyleSetBold(self.EXTERNAL, True)
        self.ctrl.StyleSetForeground(self.EXTERNAL, self.EXTERNAL_COLOR)

        self.ctrl.StyleSetBold(self.IMAGE, True)
        self.ctrl.StyleSetForeground(self.IMAGE, self.IMAGE_COLOR)

        self.ctrl.StyleSetBold(self.PARAM, True)
        self.ctrl.StyleSetForeground(self.PARAM, self.PARAM_COLOR)

        self.ctrl.StyleSetBold(self.PARAM_VAR, True)
        self.ctrl.StyleSetForeground(self.PARAM_VAR, self.PARAM_VAR_COLOR)

        self.ctrl.StyleSetBold(self.PARAM_STR, True)
        self.ctrl.StyleSetForeground(self.PARAM_STR, self.PARAM_STR_COLOR)

        self.ctrl.StyleSetBold(self.PARAM_NUM, True)
        self.ctrl.StyleSetForeground(self.PARAM_NUM, self.PARAM_NUM_COLOR)

        self.ctrl.StyleSetBold(self.PARAM_BOOL, True)
        self.ctrl.StyleSetForeground(self.PARAM_BOOL, self.PARAM_BOOL_COLOR)

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

    def lex(self, event):
        """
        Lexes, or applies syntax highlighting, to text based on a
        wx.stc.EVT_STC_STYLENEEDED event.
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
            elif self.externalPassageExists(m.group(1)):
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
        prev = 0
        text = self.ctrl.GetTextUTF8()
        style = self.DEFAULT
        styleStack = []
        styleStart = pos
        inSilence = False
        macroNestStack = []; # macro nesting
        header = self.getHeader()

        self.applyStyle(0, len(text), self.DEFAULT);

        iterator = re.finditer(re.compile(tweeregex.COMBINED_REGEX, re.U|re.I), text[pos:]);

        for p in iterator:
            prev = pos+1
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
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)

                # check for prettylinks
                s2 = self.GOOD_LINK
                if not m.group(2):
                    if self.externalPassageExists(m.group(1)):
                        s2 = self.STORYINCLUDE_LINK
                    elif not self.passageExists(m.group(1)):
                        s2 = badLinkStyle(m.group(1))
                else:
                    if self.externalPassageExists(m.group(2)):
                        s2 = self.STORYINCLUDE_LINK
                    elif not self.passageExists(m.group(2)):
                        s2 = badLinkStyle(m.group(2))
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

                for i in header.nested_macros():
                    # For matching pairs of macros (if/endif etc)
                    if name == i:
                        styled = True
                        self.applyStyle(pos, length, self.BAD_LINK)
                        macroNestStack.append((i,pos, m))
                        if i=="silently":
                            inSilence = True;
                            styleStack.append(style)
                            style = self.SILENT
                    elif header.is_endtag(name, i):
                        if macroNestStack and macroNestStack[-1][0] == i:
                            # Re-style open macro
                            macroStart,macroMatch = macroNestStack.pop()[1:];
                            applyMacroStyle(macroStart,macroMatch)
                        else:
                            styled = True
                            self.applyStyle(pos, length, self.BAD_LINK)
                        if i=="silently":
                            inSilence = False;
                            style = styleStack.pop() if styleStack else self.DEFAULT

                if not styled:
                    applyMacroStyle(pos,m)
                pos += length-1
                styleStart = pos+1

            # image (cannot have interior markup)
            elif nextToken == self.IMAGE:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                # Check for linked images
                if m.group(5):
                    self.applyStyle(pos, m.start(5), self.IMAGE)
                    if not self.passageExists(m.group(5)):
                        s2 = badLinkStyle(m.group(5))
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
                if (style == self.INLINE_STYLE or style == self.BAD_INLINE_STYLE):
                    self.applyStyle(styleStart, pos-styleStart+2, style)
                    style = styleStack.pop() if styleStack else self.DEFAULT
                    styleStart = pos+2
                else:
                    self.applyStyle(styleStart, pos-styleStart, style)
                    styleStack.append(style)
                    n = re.match(r"((?:([^\(@]+)\(([^\)]+)(?:\):))|(?:([^:@]+):([^;@]+);))+",text[pos+2:],re.U|re.I)
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
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, nextToken)
                pos += length-1
                styleStart = pos+1

        # Finish up unclosed styles
        self.applyStyle(styleStart, len(text), style)

    def passageExists(self, title):
        """
        Returns whether a given passage exists in the story.
        """
        return (self.frame.widget.parent.passageExists(title, False))
    
    def externalPassageExists(self, title):
        """
        Returns whether a given passage exists in a StoryIncludes resource.
        """
        return (self.frame.widget.parent.externalPassageExists(title))

    def applyStyle(self, start, end, style):
        """
        Applies a style to a certain range.
        """
        self.ctrl.StartStyling(start, self.TEXT_STYLES)
        self.ctrl.SetStyling(end, style)

    def getHeader(self):
        """Returns the current selected target header for this Twee Lexer."""
        return self.frame.getHeader()

    # style constants
    # ordering of BOLD through to THREE_STYLES is important
    DEFAULT, BOLD, ITALIC, BOLD_ITALIC, UNDERLINE, BOLD_UNDERLINE, ITALIC_UNDERLINE, THREE_STYLES, \
    GOOD_LINK, STORYINCLUDE_LINK, BAD_LINK, MARKUP, MACRO, SILENT, COMMENT, MONO, IMAGE, EXTERNAL, HTML, HTML_BLOCK, INLINE_STYLE, \
    BAD_INLINE_STYLE, PARAM_VAR, PARAM_STR, PARAM_NUM, PARAM_BOOL, PARAM = range(0,27)

    # markup constants

    MARKUPS = {"''" : BOLD, "//" : ITALIC, "__" : UNDERLINE, "^^" : MARKUP, "~~" : MARKUP, "==" : MARKUP}

    # nested macros

    NESTED_MACROS = [ "if", "silently" ]

    # style colors

    GOOD_LINK_COLOR = '#3333cc'
    EXTERNAL_COLOR = '#337acc'
    STORYINCLUDE_COLOR = '#906fe2'
    BAD_LINK_COLOR = '#cc3333'
    MARKUP_COLOR = '#008200'
    MACRO_COLOR = '#a94286'
    COMMENT_COLOR = '#868686'
    IMAGE_COLOR = '#088A85'
    HTML_COLOR = '#4d4d9d'

    # param colours

    PARAM_COLOR = '#7f456a'
    PARAM_VAR_COLOR = '#005682'
    PARAM_BOOL_COLOR = '#626262'
    PARAM_STR_COLOR = '#008282'
    PARAM_NUM_COLOR = '#A15000'

    TEXT_STYLES = 31    # mask for StartStyling() to indicate we're only changing text styles

def badLinkStyle(dest):
    # Apply style for a link destination which does not seem to be an existent passage
    for t in ['http:', 'https:', 'ftp:', 'mailto:', 'javascript:', 'data:', '.', '/', '\\', '#']:
        if t in dest.lower():
            return TweeLexer.EXTERNAL
    iscode = re.search(tweeregex.MACRO_PARAMS_VAR_REGEX+"|"+tweeregex.MACRO_PARAMS_FUNC_REGEX, dest, re.U)
    return TweeLexer.PARAM if iscode else TweeLexer.BAD_LINK
