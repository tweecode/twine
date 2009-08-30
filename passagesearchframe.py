#!/usr/bin/env python

#
# PassageSearchFrame
# This allows a user to do search and replaces on a PassageFrame.
# By default, this shows the Find tab initially, but this can be
# set via the constructor.
#

import re, wx
from searchpanels import FindPanel, ReplacePanel

class PassageSearchFrame (wx.Frame):
    
    def __init__ (self, parent, passageFrame, app, initialState = None):
        self.passageFrame = passageFrame
        self.app = app
        wx.Frame.__init__(self, parent, title = 'Find/Replace In Passage')
        panel = wx.Panel(self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panelSizer)
                
        self.notebook = wx.Notebook(panel)
        findPanel = FindPanel(self.notebook, onFind = self.passageFrame.findRegexp, \
                              onClose = lambda: self.Close())
        replacePanel = ReplacePanel(self.notebook, onFind = self.passageFrame.findRegexp, \
                                    onReplace = self.passageFrame.replaceOneRegexp, \
                                    onReplaceAll = self.passageFrame.replaceAllRegexps, \
                                    onClose = lambda: self.Close())
        self.notebook.AddPage(findPanel, 'Find')
        self.notebook.AddPage(replacePanel, 'Replace')
        panelSizer.Add(self.notebook, 1, wx.EXPAND)
        panelSizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()
    
    FIND_TAB = 0
    REPLACE_TAB = 1
        