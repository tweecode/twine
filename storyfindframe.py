#!/usr/bin/python

#
# StoryFindFrame
# This allows the user to search a StoryPanel for a string of text.
# This is just a front-end to method calls on StoryPanel. 
#

import re, wx

class StoryFindFrame (wx.Frame):
    
    def __init__ (self, storyPanel, app, parent = None):
        self.storyPanel = storyPanel
        self.app = app
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Find in Story', \
                          style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.CAPTION | wx.SYSTEM_MENU)
        
        panel = wx.Panel(parent = self, id = wx.ID_ANY)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panelSizer)

        # find text and label
        
        findSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        findSizer.Add(wx.StaticText(panel, label = 'Find'), flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL, \
                      border = StoryFindFrame.SPACING, proportion = 0)
        self.findField = wx.TextCtrl(panel, id = wx.ID_ANY)
        findSizer.Add(self.findField, proportion = 1, flag = wx.ALL | wx.EXPAND, \
                      border = StoryFindFrame.SPACING)
        panelSizer.Add(findSizer, flag = wx.EXPAND)
        
        # option checkboxes
        
        optionSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.caseCheckbox = wx.CheckBox(panel, label = 'Match Case', id = wx.ID_ANY)
        self.wholeWordCheckbox = wx.CheckBox(panel, label = 'Whole Word', id = wx.ID_ANY)
        self.regexpCheckbox = wx.CheckBox(panel, label = 'Regular Expression', id = wx.ID_ANY)
        
        optionSizer.Add(self.caseCheckbox, flag = wx.ALL, border = StoryFindFrame.SPACING)
        optionSizer.Add(self.wholeWordCheckbox, flag = wx.ALL, border = StoryFindFrame.SPACING)
        optionSizer.Add(self.regexpCheckbox, flag = wx.ALL, border = StoryFindFrame.SPACING)
        panelSizer.Add(optionSizer)
        
        # find and close buttons
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.closeButton = wx.Button(panel, label = 'Close', id = wx.ID_ANY)
        self.closeButton.Bind(wx.EVT_BUTTON, lambda e: self.Destroy())
        
        self.findButton = wx.Button(panel, label = 'Find Next', id = wx.ID_ANY)
        self.findButton.Bind(wx.EVT_BUTTON, self.search)
        self.findButton.SetDefault()

        buttonSizer.Add(self.closeButton, flag = wx.ALL, border = StoryFindFrame.SPACING)        
        buttonSizer.Add(self.findButton, flag = wx.ALL, border = StoryFindFrame.SPACING)
        panelSizer.Add(buttonSizer, flag = wx.ALIGN_RIGHT)

        panelSizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()
        
    def search (self, event = None):
        regexp = self.findField.GetValue()
        flag = None
        
        if not self.caseCheckbox.GetValue():
            flag = re.IGNORECASE
        
        if not self.regexpCheckbox.GetValue():
            regexp = re.escape(regexp)
        
        if self.wholeWordCheckbox.GetValue():
            regexp = r'\b' + regexp + r'\b'
            
        self.storyPanel.findWidgetRegexp(regexp, flag)

    SPACING = 6