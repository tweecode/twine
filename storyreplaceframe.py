#!/usr/bin/python

#
# StoryFindFrame
# This allows the user to replace text across an entire StoryPanel.
# This is just a front-end to method calls on StoryPanel. 
#

import re, wx

class StoryReplaceFrame (wx.Frame):
    
    def __init__ (self, storyPanel, app, parent = None):
        self.storyPanel = storyPanel
        self.app = app
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Replace Across Entire Story', \
                          style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.CAPTION | wx.SYSTEM_MENU)
        
        panel = wx.Panel(parent = self, id = wx.ID_ANY)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panelSizer)
        
        fieldSizer = wx.FlexGridSizer(2, 2)
        fieldSizer.AddGrowableCol(1, 1)

        # find text and label
        
        fieldSizer.Add(wx.StaticText(panel, label = 'Find'), flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL, \
                       border = StoryReplaceFrame.SPACING, proportion = 0)
        self.findField = wx.TextCtrl(panel, id = wx.ID_ANY)
        fieldSizer.Add(self.findField, proportion = 1, flag = wx.ALL | wx.EXPAND, \
                      border = StoryReplaceFrame.SPACING)

        # replace text and label
        
        fieldSizer.Add(wx.StaticText(panel, label = 'Replace With'), flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL, \
                       border = StoryReplaceFrame.SPACING, proportion = 0)
        self.replaceField = wx.TextCtrl(panel, id = wx.ID_ANY)
        fieldSizer.Add(self.replaceField, proportion = 1, flag = wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, \
                       border = StoryReplaceFrame.SPACING)
        
        panelSizer.Add(fieldSizer, flag = wx.EXPAND)
        
        # option checkboxes
        
        optionSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.caseCheckbox = wx.CheckBox(panel, label = 'Match Case', id = wx.ID_ANY)
        self.wholeWordCheckbox = wx.CheckBox(panel, label = 'Whole Word', id = wx.ID_ANY)
        self.regexpCheckbox = wx.CheckBox(panel, label = 'Regular Expression', id = wx.ID_ANY)
        
        optionSizer.Add(self.caseCheckbox, flag = wx.ALL, border = StoryReplaceFrame.SPACING)
        optionSizer.Add(self.wholeWordCheckbox, flag = wx.ALL, border = StoryReplaceFrame.SPACING)
        optionSizer.Add(self.regexpCheckbox, flag = wx.ALL, border = StoryReplaceFrame.SPACING)
        panelSizer.Add(optionSizer)
        
        # find and close buttons
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.closeButton = wx.Button(panel, label = 'Close', id = wx.ID_ANY)
        self.closeButton.Bind(wx.EVT_BUTTON, lambda e: self.Destroy())
        
        self.findButton = wx.Button(panel, label = 'Replace All', id = wx.ID_ANY)
        self.findButton.Bind(wx.EVT_BUTTON, self.replace)
        self.findButton.SetDefault()

        buttonSizer.Add(self.closeButton, flag = wx.ALL, border = StoryReplaceFrame.SPACING)        
        buttonSizer.Add(self.findButton, flag = wx.ALL, border = StoryReplaceFrame.SPACING)
        panelSizer.Add(buttonSizer, flag = wx.ALIGN_RIGHT)

        panelSizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()
        
    def replace (self, event = None):        
        findRegexp = self.findField.GetValue()
        replaceRegexp = self.replaceField.GetValue()
        flag = None
        
        if not self.caseCheckbox.GetValue():
            flag = re.IGNORECASE
        
        if not self.regexpCheckbox.GetValue():
            findRegexp = re.escape(findRegexp)
            replaceRegexp = re.escape(replaceRegexp)
        
        if self.wholeWordCheckbox.GetValue():
            findRegexp = r'\b' + regexp + r'\b'
            
        self.storyPanel.replaceRegexpInWidgets(findRegexp, replaceRegexp, flag)

    SPACING = 6