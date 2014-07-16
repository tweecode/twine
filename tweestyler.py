from tweelexer import TweeLexer
import wx, wx.stc

class TweeStyler(TweeLexer):
    """Applies syntax highlighting for Twee syntax in a wx.StyledTextCtrl.
    This needs to be passed the control it will be lexing, so it can
    look up the body text as needed.
    """

    def __init__(self, control, frame):
        self.ctrl = control
        self.frame = frame
        self.app = frame.app
        self.ctrl.Bind(wx.stc.EVT_STC_STYLENEEDED, lambda event: self.lex())
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

        self.ctrl.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, bodyFont)
        self.ctrl.StyleClearAll()

        for i in self.STYLE_CONSTANTS:
            self.ctrl.StyleSetFont(i, bodyFont)

        # Styles 1-8 are BOLD, ITALIC, UNDERLINE, and bitwise combinations thereof
        for i in range(0,8):
            if i & 1:
                self.ctrl.StyleSetBold(i, True)
            if i & 2:
                self.ctrl.StyleSetItalic(i, True)
            if i & 4:
                self.ctrl.StyleSetUnderline(i, True)

        self.ctrl.StyleSetBold(self.GOOD_LINK, True)
        self.ctrl.StyleSetForeground(self.GOOD_LINK, self.GOOD_LINK_COLOR)

        self.ctrl.StyleSetBold(self.BAD_LINK, True)
        self.ctrl.StyleSetForeground(self.BAD_LINK, self.BAD_LINK_COLOR)
        self.ctrl.StyleSetBold(self.BAD_MACRO, True)
        self.ctrl.StyleSetForeground(self.BAD_MACRO, self.BAD_LINK_COLOR)

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

    def getText(self):
        return self.ctrl.GetTextUTF8()

    def passageExists(self, title):
        return self.frame.widget.parent.passageExists(title, False)

    def includedPassageExists(self, title):
        return self.frame.widget.parent.includedPassageExists(title)

    def applyStyle(self, start, end, style):
        self.ctrl.StartStyling(start, self.TEXT_STYLES)
        self.ctrl.SetStyling(end, style)

    def getHeader(self):
        return self.frame.getHeader()

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
