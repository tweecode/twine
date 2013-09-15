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

        self.ctrl.StyleSetFont(self.GOOD_LINK, bodyFont)
        self.ctrl.StyleSetBold(self.GOOD_LINK, True)
        self.ctrl.StyleSetForeground(self.GOOD_LINK, self.GOOD_LINK_COLOR)
        
        self.ctrl.StyleSetFont(self.BAD_LINK, bodyFont)
        self.ctrl.StyleSetBold(self.BAD_LINK, True)
        self.ctrl.StyleSetForeground(self.BAD_LINK, self.BAD_LINK_COLOR)
       
        self.ctrl.StyleSetFont(self.MARKUP, bodyFont)
        self.ctrl.StyleSetForeground(self.MARKUP, self.MARKUP_COLOR)
        
        self.ctrl.StyleSetFont(self.HTML, bodyFont)
        self.ctrl.StyleSetBold(self.HTML, True)
        self.ctrl.StyleSetForeground(self.HTML, self.HTML_COLOR)
        
        self.ctrl.StyleSetFont(self.HTML_BLOCK, bodyFont)
        self.ctrl.StyleSetForeground(self.HTML_BLOCK, self.HTML_COLOR)
        
        self.ctrl.StyleSetFont(self.MACRO, bodyFont)
        self.ctrl.StyleSetBold(self.MACRO, True)
        self.ctrl.StyleSetForeground(self.MACRO, self.MACRO_COLOR)
                
        self.ctrl.StyleSetFont(self.COMMENT, bodyFont)
        self.ctrl.StyleSetItalic(self.COMMENT, True)
        self.ctrl.StyleSetForeground(self.COMMENT, self.COMMENT_COLOR)
        
        self.ctrl.StyleSetFont(self.SILENT, bodyFont)
        self.ctrl.StyleSetForeground(self.SILENT, self.COMMENT_COLOR)
        
        self.ctrl.StyleSetFont(self.MONO, monoFont)
        
        self.ctrl.StyleSetFont(self.EXTERNAL, bodyFont)
        self.ctrl.StyleSetBold(self.EXTERNAL, True)
        self.ctrl.StyleSetForeground(self.EXTERNAL, self.EXTERNAL_COLOR)
        
        self.ctrl.StyleSetFont(self.IMAGE, bodyFont)
        self.ctrl.StyleSetBold(self.IMAGE, True)
        self.ctrl.StyleSetForeground(self.IMAGE, self.IMAGE_COLOR)
      
    def lexMatchToken(self, text):
        m = text[:2].lower()
        if m in self.MARKUPS:
            return (self.MARKUP, self.MARKUPS[m])
        
        # link
        m = re.match(self.LINK_REGEX,text,re.I)
        if m: return (self.GOOD_LINK, m)
        
        # macro
        m = re.match(self.MACRO_REGEX,text,re.I)
        if m: return (self.MACRO, m)
        
        # image (cannot have interior markup)
        m = re.match(self.IMAGE_REGEX,text,re.I)
        if m: return (self.IMAGE, m)
        
        # Old-version HTML block (cannot have interior markup)
        m = re.match(self.HTML_BLOCK_REGEX,text,re.I)
        if m: return (self.HTML_BLOCK, m)
        
        # Inline HTML tags
        m = re.match(self.HTML_REGEX,text,re.I)
        if m: return (self.HTML, m)
        
        # Inline styles
        m = re.match(self.INLINE_STYLE_REGEX,text,re.I)
        if m: return (self.INLINE_STYLE, m)
        
        # Monospace
        m = re.match(self.MONO_REGEX,text,re.I)
        if m: return (self.MONO, m)
        
        # Comment
        m = re.match(self.COMMENT_REGEX,text,re.I)
        if m: return (self.COMMENT, m)
        
        return (None, None)
    
    def lex (self, event):
        """
        Lexes, or applies syntax highlighting, to text based on a
        wx.stc.EVT_STC_STYLENEEDED event.
        """
        
        pos = 0
        prev = 0
        text = self.ctrl.GetTextUTF8()
        style = self.DEFAULT
        styleStack = []
        styleStart = pos
        inSilence = False
        macroNestStack = []; # macro nesting
        
        iterator = re.finditer(re.compile(self.COMBINED_REGEX, re.I), text[pos:]);
        
        for p in iterator:
            prev = pos+1
            pos = p.start()
            self.applyStyle(prev, pos, style);
            
            nextToken, m = self.lexMatchToken(p.group(0))
            

            # important: all style ends must be handled before beginnings
            # otherwise we start treading on each other in certain circumstances

            # markup
            if not inSilence and nextToken == self.MARKUP:
                if (style & m):
                    self.applyStyle(styleStart, pos-styleStart+2, style) 
                    style = styleStack.pop() if styleStack else self.DEFAULT 
                    styleStart = pos+2
                else: 
                    self.applyStyle(styleStart, pos-styleStart, style)  
                    styleStack.append(style)
                    markup = m
                    if markup <= self.THREE_STYLES:
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
                    if not self.passageExists(m.group(1)):
                        s2 = self.BAD_LINK
                else:
                    if not self.passageExists(m.group(2)):
                        s2 = self.BAD_LINK
                        for t in ['http://', 'https://', 'ftp://']:
                          if m.group(2).lower().startswith(t):
                            s2 = self.EXTERNAL
                self.applyStyle(pos, length, s2)
                pos += length-1
                styleStart = pos+1
                 
            #macro               
            elif nextToken == self.MACRO:
                length = m.end(0)
                name = m.group(1).lower()
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, self.MACRO)
                for i in self.NESTED_MACROS:
                    # For matching pairs of macros (if/endif etc)
                    if name == i:
                        self.applyStyle(pos, length, self.BAD_LINK)
                        macroNestStack.append((i, pos, length))
                        if i=="silently":
                            inSilence = True;
                            styleStack.append(style)
                            style = self.SILENT
                    elif name == ('end' + i):
                        if macroNestStack and macroNestStack[-1][0] == i:
                            # Re-style open macro
                            macroStart,macroLength = macroNestStack.pop()[1:];
                            self.applyStyle(macroStart,macroLength, self.MACRO)
                        else:
                            self.applyStyle(pos, length, self.BAD_LINK)
                        if i=="silently":
                            inSilence = False;
                            style = styleStack.pop() if styleStack else self.DEFAULT 
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
                        s2 = self.BAD_LINK
                        for t in ['http://', 'https://', 'ftp://']:
                          if t in m.group(5).lower():
                            s2 = self.EXTERNAL
                        self.applyStyle(pos+m.start(5)-1, (m.end(5)-m.start(5))+2, s2)
                    else:
                        self.applyStyle(pos+m.start(5)-1, (m.end(5)-m.start(5))+2, self.GOOD_LINK)
                    self.applyStyle(pos+length-1,1, self.IMAGE)
                else:
                    self.applyStyle(pos, length, self.IMAGE)
                pos += length-1
                styleStart = pos+1
                
            # Inline styles
            elif nextToken == self.INLINE_STYLE:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                n = re.search("(?:([^\(@]+)\(([^\)]+)(?:\):))|(?:([^:@]+):([^;]+);)",text[pos:pos+m.end(0)],re.I)
                if n:
                    self.applyStyle(pos,length,self.MARKUP)
                    pos += length-1
                else:
                    self.applyStyle(pos,length,self.BAD_LINK)
                    pos += length-1
                styleStart = pos+1
                
            # others
            elif nextToken in [self.HTML, self.HTML_BLOCK, self.COMMENT, self.MONO]:
                length = m.end(0);
                self.applyStyle(styleStart, pos-styleStart, style)
                self.applyStyle(pos, length, nextToken)
                pos += length-1
                styleStart = pos+1

    def passageExists (self, title):
        """
        Returns whether a given passage exists in the story.
        """
        return (self.frame.widget.parent.findWidget(title) != None)
        
    def applyStyle (self, start, end, style):
        """
        Applies a style to a certain range.
        """
        self.ctrl.StartStyling(start, self.TEXT_STYLES)
        self.ctrl.SetStyling(end, style)

    # style constants
    # ordering of BOLD through to THREE_STYLES is important
    DEFAULT, BOLD, ITALIC, BOLD_ITALIC, UNDERLINE, BOLD_UNDERLINE, ITALIC_UNDERLINE, THREE_STYLES, \
    GOOD_LINK, BAD_LINK, MARKUP, MACRO, SILENT, COMMENT, MONO, IMAGE, EXTERNAL, HTML, HTML_BLOCK, INLINE_STYLE = range(20)
    
    # markup constants
    
    MARKUPS = {"''" : BOLD, "//" : ITALIC, "__" : UNDERLINE, "^^" : MARKUP, "~~" : MARKUP, "==" : MARKUP}
    
    # regexes
    LINK_REGEX = r"\[\[([^\|\]]*?)(?:(?:\]\])|(?:\|(.*?)\]\]))"
    MACRO_REGEX = r"<<([^>\s]+)(?:\s*)((?:[^>]|>(?!>))*)>>"
    IMAGE_REGEX = r"\[([<]?)(>?)img\[(?:([^\|\]]+)\|)?([^\[\]\|]+)\](?:\[([^\]]*)\]?)?(\])"
    HTML_BLOCK_REGEX = r"<html>((?:.|\n)*?)</html>"
    HTML_REGEX = r"<(?:\/?\w+|\w+(?:(?:\s+\w+(?:\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?)>"
    INLINE_STYLE_REGEX = r"@@(?:[^@]|@(?!@))*@@"
    MONO_REGEX = r"^\{\{\{\n((?:^[^\n]*\n)+?)(^\}\}\}$\n?)|\{\{\{((?:.|\n)*?)\}\}\}"
    COMMENT_REGEX = r"/%((?:.|\n)*?)%/"
    
    COMBINED_REGEX = '(' + ')|('.join([ LINK_REGEX, MACRO_REGEX, IMAGE_REGEX, HTML_BLOCK_REGEX, HTML_REGEX, INLINE_STYLE_REGEX,\
                      MONO_REGEX, COMMENT_REGEX, "''|//|__|^^|~~|==" ]) + ')'
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
    HTML_COLOR = '#4242a9'
    
    TEXT_STYLES = 31    # mask for StartStyling() to indicate we're only changing text styles