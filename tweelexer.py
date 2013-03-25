#!/usr/bin/env python

#
# TweeLexer
# This lexes (or syntax highlights) Twee syntax in a wx.StyledTextCtrl.
# This needs to be passed the control it will be lexing, so it can
# look up the body text as needed.
#

import re, wx, wx.stc

class TweeLexer:
    
    def __init__ (self, control, frame):
        self.ctrl = control
        self.frame = frame
        self.app = frame.app
        self.ctrl.Bind(wx.stc.EVT_STC_STYLENEEDED, self.lex)
        self.initStyles()
        
    def initStyles (self):
        """
        Initialize style definitions. This is automatically invoked when
        the constructor is called, but should be called any time font
        preferences are changed.
        """
        bodyFont = wx.Font(self.app.config.ReadInt('windowedFontSize'), wx.MODERN, wx.NORMAL, \
                           wx.NORMAL, False, self.app.config.Read('windowedFontFace'))
        monoFont = wx.Font(self.app.config.ReadInt('windowedFontSize'), wx.MODERN, wx.NORMAL, \
                           wx.NORMAL, False, "Courier")

        # Styles 1-8 are BOLD, ITALIC, UNDERLINE, and bitwise combinations thereof
        for i in range(1,8):
            self.ctrl.StyleSetFont(i, bodyFont)
            if (i & 1):
                self.ctrl.StyleSetBold(i, True)
            if (i & 2):
                self.ctrl.StyleSetItalic(i, True)
            if (i & 4):
                self.ctrl.StyleSetUnderline(i, True)

        self.ctrl.StyleSetFont(TweeLexer.GOOD_LINK, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.GOOD_LINK, True)
        self.ctrl.StyleSetForeground(TweeLexer.GOOD_LINK, TweeLexer.GOOD_LINK_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.BAD_LINK, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.BAD_LINK, True)
        self.ctrl.StyleSetForeground(TweeLexer.BAD_LINK, TweeLexer.BAD_LINK_COLOR)
       
        self.ctrl.StyleSetFont(TweeLexer.MARKUP, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.MARKUP, TweeLexer.MARKUP_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.HTML, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.HTML, TweeLexer.HTML_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.MACRO, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.MACRO, True)
        self.ctrl.StyleSetForeground(TweeLexer.MACRO, TweeLexer.MACRO_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.COMMENT, bodyFont)
        self.ctrl.StyleSetItalic(TweeLexer.COMMENT, True)
        self.ctrl.StyleSetForeground(TweeLexer.COMMENT, TweeLexer.COMMENT_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.SILENT, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.SILENT, TweeLexer.COMMENT_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.MONO, monoFont)
        
        self.ctrl.StyleSetFont(TweeLexer.EXTERNAL, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.EXTERNAL, True)
        self.ctrl.StyleSetForeground(TweeLexer.EXTERNAL, TweeLexer.EXTERNAL_COLOR)
        
        self.ctrl.StyleSetFont(TweeLexer.IMAGE, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.IMAGE, True)
        self.ctrl.StyleSetForeground(TweeLexer.IMAGE, TweeLexer.IMAGE_COLOR)
        
    def lex (self, event):
        """
        Lexes, or applies syntax highlighting, to text based on a
        wx.stc.EVT_STC_STYLENEEDED event.
        """
        
        pos = 0 # should be self.ctrl.GetEndStyled(), but doesn't work
        end = self.ctrl.GetLength()
        text = self.ctrl.GetTextUTF8()
        style = TweeLexer.DEFAULT
        styleStack = []
        styleStart = pos
        inSilence = False
        macroNestStack = []; # macro nesting
        
        # we have to apply DEFAULT styles as necessary here, otherwise
        # old style ranges stick around, and things look very strange
                
        while pos < end:
            nextToken = text[pos: pos + 2].lower()

            # important: all style ends must be handled before beginnings
            # otherwise we start treading on each other in certain circumstances

            # markup
            if not inSilence and (nextToken in TweeLexer.MARKUPS):
                if (style & TweeLexer.MARKUPS[nextToken]):
                    self.applyStyle(styleStart, pos-styleStart+2, style) 
                    style = styleStack.pop() if styleStack else TweeLexer.DEFAULT 
                    styleStart = pos+2
                else: 
                    self.applyStyle(styleStart, pos-styleStart, style)  
                    styleStack.append(style)
                    markup = TweeLexer.MARKUPS[nextToken]
                    if markup <= TweeLexer.THREE_STYLES:
                        style |= markup
                    else:
                        style = markup
                    styleStart = pos
                pos += 1
                
            # link
            m = re.match("\\[\\[([^\\|\\]]*?)(?:(\\]\\])|(\\|(.*?)\\]\\]))",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                                            
                # check for prettylinks
                s2 = TweeLexer.GOOD_LINK
                if m.group(2):
                    if not self.passageExists(m.group(1)):
                        s2 = TweeLexer.BAD_LINK
                elif m.group(3):
                    if not self.passageExists(m.group(4)):
                        s2 = TweeLexer.BAD_LINK
                        for t in ['http://', 'https://', 'ftp://']:
                          if t in m.group(4).lower():
                            s2 = TweeLexer.EXTERNAL
                self.applyStyle(pos, length, s2)
                pos += length-1
                styleStart = pos+1
                                
            # macro
            m = re.match("<<([^>\\s]+)(?:\\s*)((?:[^>]|>(?!>))*)>>",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, TweeLexer.MACRO)
                for i in TweeLexer.NESTED_MACROS:
                    # For matching pairs of macros (if/endif etc)
                    if m.group(1).lower() == i:
                        self.applyStyle(pos, length, TweeLexer.BAD_LINK)
                        macroNestStack.append((i, pos, length))
                        if i=="silently":
                            inSilence = True;
                            styleStack.append(style)
                            style = TweeLexer.SILENT
                    elif m.group(1).lower() == ('end' + i):
                        if macroNestStack and macroNestStack[-1][0] == i:
                            # Re-style open macro
                            macroStart,macroLength = macroNestStack.pop()[1:];
                            self.applyStyle(macroStart,macroLength, TweeLexer.MACRO)
                        else:
                            self.applyStyle(pos, length, TweeLexer.BAD_LINK)
                        if i=="silently":
                            inSilence = False;
                            style = styleStack.pop() if styleStack else TweeLexer.DEFAULT 
                pos += length-1
                styleStart = pos+1
                        
            # image (cannot have interior markup)
            m = re.match("\\[([<]?)(>?)img\\[(?:([^\\|\\]]+)\\|)?([^\\[\\]\\|]+)\\](?:\\[([^\\]]*)\\]?)?(\\])",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                # Check for linked images
                if m.group(5):
                    self.applyStyle(pos, m.start(5), TweeLexer.IMAGE)
                    if not self.passageExists(m.group(5)):
                        s2 = TweeLexer.BAD_LINK
                        for t in ['http://', 'https://', 'ftp://']:
                          if t in m.group(5).lower():
                            s2 = TweeLexer.EXTERNAL
                        self.applyStyle(pos+m.start(5)-1, (m.end(5)-m.start(5))+2, s2)
                    else:
                        self.applyStyle(pos+m.start(5)-1, (m.end(5)-m.start(5))+2, TweeLexer.GOOD_LINK)
                    self.applyStyle(pos+length-1,1, TweeLexer.IMAGE)
                else:
                    self.applyStyle(pos, length, TweeLexer.IMAGE)
                pos += length-1
                styleStart = pos+1
                
            # HTML (cannot have interior markup)
            m = re.match("<html>((?:.|\\n)*?)</html>",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, TweeLexer.HTML)
                pos += length-1
                styleStart = pos+1
                
            # Inline styles
            m = re.match("@@(?:[^@]|@(?!@))*@@",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                n = re.search("(?:([^\(@]+)\(([^\)]+)(?:\):))|(?:([^:@]+):([^;]+);)",text[pos:pos+m.end(0)],re.I)
                if n:
                    self.applyStyle(pos,length,TweeLexer.MARKUP)
                    pos += length-1
                else:
                    self.applyStyle(pos,length,TweeLexer.BAD_LINK)
                    pos += length-1
                styleStart = pos+1
                
            # Monospace (both full-line and by char)
            m = re.match("^\\{\\{\\{\\n((?:^[^\\n]*\\n)+?)(^\\}\\}\\}$\\n?)|\\{\\{\\{((?:.|\\n)*?)\\}\\}\\}",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, TweeLexer.MONO)
                pos += length-1
                styleStart = pos+1   
                
                """(?:([^\(@]+)\(([^\)]+)(?:\):))
                |
                (?:([^:@]+):([^;]+);)"""
                
            # comment (cannot have interior markup)
            m = re.match("/%((?:.|\\n)*?)%/",text[pos:],re.I)
            if m:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                styleStart = pos
                self.applyStyle(pos, length, TweeLexer.COMMENT)
                pos += length-1
                styleStart = pos+1
            
            pos += 1

    def passageExists (self, title):
        """
        Returns whether a given passage exists in the story.
        """
        return (self.frame.widget.parent.findWidget(title) != None)
        
    def applyStyle (self, start, end, style):
        """
        Applies a style to a certain range.
        """
        self.ctrl.StartStyling(start, TweeLexer.TEXT_STYLES)
        self.ctrl.SetStyling(end, style)

    # style constants
    # ordering of BOLD through to THREE_STYLES is important
    DEFAULT, BOLD, ITALIC, BOLD_ITALIC, UNDERLINE, BOLD_UNDERLINE, ITALIC_UNDERLINE, THREE_STYLES, \
    GOOD_LINK, BAD_LINK, MARKUP, MACRO, SILENT, COMMENT, MONO, IMAGE, EXTERNAL, HTML = range(18)
    
    
    # markup constants
    
    MARKUPS = {"''" : BOLD, "//" : ITALIC, "__" : UNDERLINE, "^^" : MARKUP, "~~" : MARKUP, "==" : MARKUP}
    
    # nested macros
    
    NESTED_MACROS = [ "if", "silently" ]
    
    # style colors
    
    GOOD_LINK_COLOR = '#0000ff'
    EXTERNAL_COLOR = '#0077ff'
    BAD_LINK_COLOR = '#ff0000'
    MARKUP_COLOR = '#008200'
    MACRO_COLOR = '#a94286'
    COMMENT_COLOR = '#868686'
    IMAGE_COLOR = '#088A85'
    HTML_COLOR = '#3104B4'
    
    TEXT_STYLES = 31    # mask for StartStyling() to indicate we're only changing text styles