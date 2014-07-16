import wx
from searchpanels import FindPanel, ReplacePanel

class PassageSearchFrame(wx.Frame):
    """
    This allows a user to do search and replaces on a PassageFrame.
    By default, this shows the Find tab initially, but this can be
    set via the constructor.
    """

    def __init__(self, parent, passageFrame, app, initialState = 0):
        self.passageFrame = passageFrame
        self.app = app
        wx.Frame.__init__(self, parent, title = 'Find/Replace In Passage')
        panel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panelSizer)

        self.notebook = wx.Notebook(panel)
        self.findPanel = FindPanel(self.notebook, onFind = self.passageFrame.findRegexp, \
                                   onClose = self.Close)
        self.replacePanel = ReplacePanel(self.notebook, onFind = self.passageFrame.findRegexp, \
                                         onReplace = self.passageFrame.replaceOneRegexp, \
                                         onReplaceAll = self.passageFrame.replaceAllRegexps, \
                                         onClose = self.Close)
        self.notebook.AddPage(self.findPanel, 'Find')
        self.notebook.AddPage(self.replacePanel, 'Replace')
        self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onChangeTab)

        self.notebook.ChangeSelection(initialState)
        if initialState == PassageSearchFrame.FIND_TAB:
            self.findPanel.focus()
        else:
            self.replacePanel.focus()

        panelSizer.Add(self.notebook, 1, wx.EXPAND)
        panelSizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()

    def onChangeTab(self, event):
        if event.GetSelection() == PassageSearchFrame.FIND_TAB:
            self.findPanel.focus()
        else:
            self.replacePanel.focus()

        # for some reason, we have to manually propagate the event from here

        event.Skip(True)

    FIND_TAB = 0
    REPLACE_TAB = 1

