#!/usr/bin/python

#
# StoryFindFrame
# This allows the user to search a StoryPanel for a string of text.
# This is just a front-end to method calls on StoryPanel. 
#

import re, wx
from searchpanels import FindPanel

class StoryFindFrame (wx.Frame):
    
    def __init__ (self, storyPanel, app, parent = None):
        self.storyPanel = storyPanel
        self.app = app
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Find in Story', \
                          style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.CAPTION | wx.SYSTEM_MENU)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        findPanel = FindPanel(parent = self, onFind = self.onFind, onClose = self.onClose)
        findPanel.focus()
        sizer.Add(findPanel)
        sizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()
        
    def onFind (self, regexp, flags):            
        self.storyPanel.findWidgetRegexp(regexp, flags)
        
    def onClose (self):
        self.Close()

#
# StoryReplaceFrame
# This allows the user to replace text across an entire StoryPanel.
# This is just a front-end to method calls on StoryPanel. 
#

import re, wx
from searchpanels import ReplacePanel

class StoryReplaceFrame (wx.Frame):
    
    def __init__ (self, storyPanel, app, parent = None):
        self.storyPanel = storyPanel
        self.app = app
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Replace Across Entire Story', \
                          style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.CAPTION | wx.SYSTEM_MENU)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        replacePanel = ReplacePanel(self, allowIncremental = True, \
                                    onFind=self.onFind, onReplace=self.onReplace, \
                                    onReplaceAll = self.onReplaceAll, onClose = self.onClose)
        sizer.Add(replacePanel)
        replacePanel.focus()
        
        sizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()

    def onFind (self, regexp, flags):            
        self.storyPanel.findWidgetRegexp(regexp, flags)

    def onReplace(self, findRegexp, flags, replaceRegexp):
        self.storyPanel.replaceRegexpInSelectedWidget(findRegexp, replaceRegexp, flags)
        
    def onReplaceAll (self, findRegexp, flags, replaceRegexp):        
        self.storyPanel.replaceRegexpInWidgets(findRegexp, replaceRegexp, flags)

    def onClose (self):
        self.Close()
