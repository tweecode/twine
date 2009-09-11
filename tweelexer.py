#!/usr/bin/env python

#
# TweeLexer
# This lexes (or syntax highlights) Twee syntax in a wx.StyledTextCtrl.
# This needs to be passed the control it will be lexing, so it can
# look up the body text as needed.
#

import re, wx, wx.stc

class TweeLexer:
    
    def __init__ (self, control, app):
        self.ctrl = control
        self.app = app
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
        self.ctrl.StyleSetForeground(TweeLexer.GOOD_LINK, TweeLexer.GOOD_LINK_COLOR)
        self.ctrl.StyleSetFont(TweeLexer.BAD_LINK, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.BAD_LINK, TweeLexer.BAD_LINK_COLOR)
        self.ctrl.StyleSetFont(TweeLexer.MARKUP, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.MARKUP, TweeLexer.MARKUP_COLOR)
        self.ctrl.StyleSetFont(TweeLexer.MACRO, bodyFont)
        self.ctrl.StyleSetForeground(TweeLexer.MACRO, TweeLexer.MACRO_COLOR)
    
    def lex (self, event):
        """
        Lexes, or applies syntax highlighting, to text based on a
        wx.stc.EVT_STC_STYLENEEDED event.
        """
        print "lexing"
        pos = 0 #self.ctrl.GetEndStyled()
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
            
            if not inMarkup and text[pos:pos + 2] in TweeLexer.MARKUPS:
                styleChanged = True
                inMarkup = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.MARKUP
                
            # end of markup

            if inMarkup and text[pos - 2:pos] in TweeLexer.MARKUPS \
                and pos > styleStart + 2:
                styleChanged = True
                inMarkup = False
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.DEFAULT                
            
            # start of macro
            
            if text[pos:pos + 2] == '<<':
                styleChanged = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.MACRO

            # start of link
            
            if text[pos:pos + 2] == '[[':
               styleChanged = True
               self.applyStyle(styleStart, pos, style)
               style = TweeLexer.GOOD_LINK
           
            # end of either macro or link
                
            if (text[pos - 2:pos] == '>>') \
                or (text[pos - 2:pos] == ']]'):
                styleChanged = True
                self.applyStyle(styleStart, pos, style)
                style = TweeLexer.DEFAULT
            
            if styleChanged: styleStart = pos
            pos = pos + 1
            
        if styleStart != pos:
            self.applyStyle(styleStart, pos, style)

    def applyStyle (self, start, end, style):
        """
        Applies a style to a certain range.
        """
        print 'applying style', style, 'to', (start, end)
        self.ctrl.StartStyling(start, TweeLexer.TEXT_STYLES)
        self.ctrl.SetStyling(end, style)

    # markup constants
    
    MARKUPS = ["''", "//", "=="]

    # style constants
    
    DEFAULT = 0
    GOOD_LINK = 1
    BAD_LINK = 2
    MARKUP = 3
    MACRO = 4
    
    # style colors
    
    GOOD_LINK_COLOR = '#0000ff'
    BAD_LINK_COLOR = '#ff00ff'
    MARKUP_COLOR = '#00ff00'
    MACRO_COLOR = '#ff00ff'
    
    TEXT_STYLES = 31    # mask for StartStyling() to indicate we're only changing text styles