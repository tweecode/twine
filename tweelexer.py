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

        self.ctrl.StyleSetFont(TweeLexer.GOOD_LINK, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.GOOD_LINK, True)
        self.ctrl.StyleSetForeground(TweeLexer.GOOD_LINK, TweeLexer.GOOD_LINK_COLOR)
        self.ctrl.StyleSetFont(TweeLexer.BAD_LINK, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.BAD_LINK, True)
        self.ctrl.StyleSetForeground(TweeLexer.BAD_LINK, TweeLexer.BAD_LINK_COLOR)
        self.ctrl.StyleSetFont(TweeLexer.MARKUP, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.MARKUP, TweeLexer.MARKUP_COLOR)
        self.ctrl.StyleSetFont(TweeLexer.MACRO, bodyFont)
        self.ctrl.StyleSetBold(TweeLexer.MACRO, True)
        self.ctrl.StyleSetForeground(TweeLexer.MACRO, TweeLexer.MACRO_COLOR)
    
    def lex (self, event):
        """
        Lexes, or applies syntax highlighting, to text based on a
        wx.stc.EVT_STC_STYLENEEDED event.
        """
        pos = 0 # should be self.ctrl.GetEndStyled(), but doesn't work
        end = event.GetPosition()
        text = self.ctrl.GetTextRange(pos, end)
        style = TweeLexer.DEFAULT
        styleStart = pos
        inMarkup = False
        
        # we have to apply DEFAULT styles as necessary here, otherwise
        # old style ranges stick around, and things look very strange
                
        while pos < end:
            styleChanged = False

            # start of markup
            
            if not inMarkup and (text[pos:pos + 2] in TweeLexer.MARKUPS \
                                 or text[pos:pos + 6] == '<html>'):
                styleChanged = True
                inMarkup = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.MARKUP
                
            # end of markup

            if inMarkup and ((text[pos - 2:pos] in TweeLexer.MARKUPS \
                             and pos > styleStart + 2) \
                             or text[pos - 7:pos] == '</html>'):
                styleChanged = True
                inMarkup = False
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.DEFAULT                
            
            # start of macro
            
            if text[pos:pos + 2] == '<<':
                styleChanged = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.MACRO

            # end of macro
                
            if text[pos - 2:pos] == '>>':
                styleChanged = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.DEFAULT

            # start of link
            
            if text[pos:pos + 2] == '[[':
                styleChanged = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.GOOD_LINK
 
            # end of link
            
            if text[pos - 2:pos] == ']]':
                styleChanged = True
                if not self.passageExists(text[styleStart + 2:pos - 2]):
                    style = TweeLexer.BAD_LINK
                
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.DEFAULT
                       
            if styleChanged: styleStart = pos
            pos = pos + 1
            
        if styleStart != pos:
            # one last link check
            
            if style == TweeLexer.GOOD_LINK and \
                not self.passageExists(text[styleStart + 2:pos - 2]):
                style = TweeLexer.BAD_LINK
            
            self.applyStyle(styleStart, pos, style)

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

    # markup constants
    
    MARKUPS = ["''", "//", "__", "^^", "~~", "=="]

    # style constants
    
    DEFAULT = 0
    GOOD_LINK = 1
    BAD_LINK = 2
    MARKUP = 3
    MACRO = 4
    
    # style colors
    
    GOOD_LINK_COLOR = '#23648C'
    BAD_LINK_COLOR = '#7f2020'
    MARKUP_COLOR = '#29A339'
    MACRO_COLOR = '#691A52'
    
    TEXT_STYLES = 31    # mask for StartStyling() to indicate we're only changing text styles