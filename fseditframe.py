import sys, wx, wx.stc

class FullscreenEditFrame(wx.Frame):
    """
    This opens a modal fullscreen editor with some text. When the user's done,
    this calls the callback function passed to the constructor with the new text.

    A lot of the stuff dealing with wx.stc.StyledTextCtrl comes from:
    http://www.psychicorigami.com/2009/01/05/a-5k-python-fullscreen-text-editor/
    """

    def __init__(self, parent, app, frame = None, title = '', initialText = '', callback = lambda i: i):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = title, size = (400, 400))
        self.app = app
        self.callback = callback
        self.frame = frame
        self.cursorVisible = True

        # menu bar
        # this is never seen by the user,
        # but lets them hit ctrl-S to save

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append(wx.ID_SAVE, '&Save Story\tCtrl-S')
        self.Bind(wx.EVT_MENU, lambda e: self.frame.widget.parent.parent.save, id = wx.ID_SAVE)
        menuBar.Append(menu, 'Commands')
        self.SetMenuBar(menuBar)

        # margins

        self.marginPanel = wx.Panel(self)
        marginSizer = wx.BoxSizer(wx.VERTICAL)  # doesn't really matter
        self.marginPanel.SetSizer(marginSizer)

        # content

        self.panel = wx.Panel(self.marginPanel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        marginSizer.Add(self.panel, 1, flag = wx.EXPAND | wx.LEFT | wx.RIGHT, border = 100)

        # controls

        self.editCtrl = wx.stc.StyledTextCtrl(self.panel, style = wx.NO_BORDER | wx.TE_NO_VSCROLL | \
                                              wx.TE_MULTILINE | wx.TE_PROCESS_TAB)
        self.editCtrl.SetMargins(0, 0)
        self.editCtrl.SetMarginWidth(1, 0)
        self.editCtrl.SetWrapMode(wx.stc.STC_WRAP_WORD)
        self.editCtrl.SetText(initialText)
        self.editCtrl.SetUseHorizontalScrollBar(False)
        self.editCtrl.SetUseVerticalScrollBar(False)
        self.editCtrl.SetCaretPeriod(750)

        self.directions = wx.StaticText(self.panel, label = FullscreenEditFrame.DIRECTIONS, style = wx.ALIGN_CENTRE)
        labelFont = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        labelFont.SetPointSize(FullscreenEditFrame.LABEL_FONT_SIZE)
        self.directions.SetFont(labelFont)

        self.applyPrefs()
        sizer.Add(self.editCtrl, 1, flag = wx.EXPAND | wx.ALL)
        sizer.Add(self.directions, 0, flag = wx.TOP | wx.BOTTOM, border = 6)
        self.panel.SetSizer(sizer)

        # events

        self.Bind(wx.EVT_KEY_DOWN, self.keyListener)
        self.Bind(wx.EVT_MOTION, self.showCursor)
        self.editCtrl.Bind(wx.EVT_KEY_DOWN, self.keyListener)
        self.editCtrl.Bind(wx.EVT_MOTION, self.showCursor)

        self.editCtrl.SetFocus()
        self.editCtrl.SetSelection(-1, -1)
        self.SetIcon(self.app.icon)
        self.Show(True)
        self.ShowFullScreen(True)

    def close(self):
        self.callback(self.editCtrl.GetText())
        if sys.platform == 'darwin': self.ShowFullScreen(False)
        self.Close()

    def applyPrefs(self):
        """
        Applies user preferences to this frame.
        """
        editFont = wx.Font(self.app.config.ReadInt('fsFontSize'), wx.FONTFAMILY_MODERN, \
                           wx.FONTSTYLE_NORMAL, wx.NORMAL, False, self.app.config.Read('fsFontFace'))
        bgColor = self.app.config.Read('fsBgColor')
        textColor = self.app.config.Read('fsTextColor')
        lineHeight = self.app.config.ReadInt('fslineHeight') / float(100)

        self.panel.SetBackgroundColour(bgColor)
        self.marginPanel.SetBackgroundColour(bgColor)

        self.editCtrl.SetBackgroundColour(bgColor)
        self.editCtrl.SetForegroundColour(textColor)
        self.editCtrl.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, bgColor)
        self.editCtrl.SetCaretForeground(textColor)
        self.editCtrl.SetSelBackground(True, textColor)
        self.editCtrl.SetSelForeground(True, bgColor)

        defaultStyle = self.editCtrl.GetStyleAt(0)
        self.editCtrl.StyleSetForeground(defaultStyle, textColor)
        self.editCtrl.StyleSetBackground(defaultStyle, bgColor)
        self.editCtrl.StyleSetFont(defaultStyle, editFont)

        # we stuff a larger font into a style def we never use
        # to force line spacing

        editFont.SetPointSize(editFont.GetPointSize() * lineHeight)
        self.editCtrl.StyleSetFont(wx.stc.STC_STYLE_BRACELIGHT, editFont)

        self.directions.SetForegroundColour(textColor)

    def keyListener(self, event):
        """
        Listens for a key that indicates this frame should close; otherwise lets the event propagate.
        This also hides the mouse cursor; the showCursor method, bound to the mouse motion event,
        restores it when the user moves it.
        """
        key = event.GetKeyCode()

        if key == wx.WXK_F12:
            self.close()

        if key == wx.WXK_ESCAPE:
            self.close()
            self.frame.Destroy()

        self.hideCursor()
        event.Skip()

    def hideCursor(self, event = None):
        if self.cursorVisible:
            self.SetCursor(wx.StockCursor(wx.CURSOR_BLANK))
            self.editCtrl.SetCursor(wx.StockCursor(wx.CURSOR_BLANK))
            self.cursorVisible = False

    def showCursor(self, event = None):
        if not self.cursorVisible:
            self.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))
            self.editCtrl.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))
            self.cursorVisible = True

    DIRECTIONS = 'Press Escape to close this passage, F12 to leave fullscreen.'
    LABEL_FONT_SIZE = 10
