#!/usr/bin/python

import re, wx

#
# FindPanel
# This allows the user to enter a search term and select various
# criteria (i.e. "match case", etc.) There are two callbacks:
#
# onFind (regexp, flags)
# Regexp corresponds to the user's search, and flags should be used
# when performing that search.
#
# onClose()
# When the user clicks the Close button. 
#

class FindPanel (wx.Panel):
    
    def __init__ (self, parent, onFind = None, onClose = None):
        self.findCallback = onFind
        self.closeCallback = onClose

        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # find text and label
        
        findSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        findSizer.Add(wx.StaticText(self, label = 'Find'), flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL, \
                      border = FindPanel.SPACING, proportion = 0)
        self.findField = wx.TextCtrl(self)
        findSizer.Add(self.findField, proportion = 1, flag = wx.ALL | wx.EXPAND, border = FindPanel.SPACING)
        sizer.Add(findSizer, flag = wx.EXPAND)
        
        # option checkboxes
        
        optionSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.caseCheckbox = wx.CheckBox(self, label = 'Match Case')
        self.wholeWordCheckbox = wx.CheckBox(self, label = 'Whole Word')
        self.regexpCheckbox = wx.CheckBox(self, label = 'Regular Expression')
        
        optionSizer.Add(self.caseCheckbox, flag = wx.ALL, border = FindPanel.SPACING)
        optionSizer.Add(self.wholeWordCheckbox, flag = wx.ALL, border = FindPanel.SPACING)
        optionSizer.Add(self.regexpCheckbox, flag = wx.ALL, border = FindPanel.SPACING)
        sizer.Add(optionSizer)
        
        # find and close buttons
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.closeButton = wx.Button(self, label = 'Close')
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        
        self.findButton = wx.Button(self, label = 'Find Next')
        self.findButton.Bind(wx.EVT_BUTTON, self.onFind)
        self.findButton.SetDefault()

        buttonSizer.Add(self.closeButton, flag = wx.ALL, border = FindPanel.SPACING)        
        buttonSizer.Add(self.findButton, flag = wx.ALL, border = FindPanel.SPACING)
        sizer.Add(buttonSizer, flag = wx.ALIGN_RIGHT)
        sizer.Fit(self)
        
    def onFind (self, event):
        """
        Assembles a regexp based on field values and passes it on to our callback.
        """
        if self.findCallback:
            regexp = self.findField.GetValue()
            flags = None
        
            if not self.caseCheckbox.GetValue():
                flags = re.IGNORECASE
        
            if not self.regexpCheckbox.GetValue():
                regexp = re.escape(regexp)
        
            if self.wholeWordCheckbox.GetValue():
                regexp = r'\b' + regexp + r'\b'

            self.findCallback(regexp, flags)
            
    def onClose (self, event):
        """
        Passes on a close message to our callback.
        """
        if self.closeCallback: self.closeCallback()

    SPACING = 6

#
# ReplacePanel
# This allows the user to enter a search and replace term and select
# various criteria (i.e. "match case", etc.) There are two callbacks:
#
# onFind (regexp, flags)
# Regexp corresponds to the user's search, and flags should be used
# when performing that search.
#
# onReplace (regexp, flags, replaceTerm)
# Like find, only with a replaceTerm.
#
# onReplaceAll (regexp, flags, replaceTerm)
# Like replace, only the user is signalling that they want to replace
# all instances at once.
#
# onClose()
# When the user clicks the Close button. 
#
# You may also pass in a parameter to set whether users can perform
# incremental searches, or if they may only replace all.

class ReplacePanel (wx.Panel):
    
    def __init__ (self, parent, allowIncremental = True, \
                  onFind = None, onReplace = None, onReplaceAll = None, onClose = None):
        self.findCallback = onFind
        self.replaceCallback = onReplace
        self.replaceAllCallback = onReplaceAll
        self.closeCallback = onClose
        
        wx.Panel.__init__(self, parent)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        
        fieldSizer = wx.FlexGridSizer(2, 2)
        fieldSizer.AddGrowableCol(1, 1)

        # find text and label
        
        fieldSizer.Add(wx.StaticText(self, label = 'Find'), flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL, \
                       border = ReplacePanel.SPACING, proportion = 0)
        self.findField = wx.TextCtrl(self)
        fieldSizer.Add(self.findField, proportion = 1, flag = wx.ALL | wx.EXPAND, border = ReplacePanel.SPACING)

        # replace text and label
        
        fieldSizer.Add(wx.StaticText(self, label = 'Replace With'), flag = wx.ALL | wx.ALIGN_CENTER_VERTICAL, \
                       border = ReplacePanel.SPACING, proportion = 0)
        self.replaceField = wx.TextCtrl(self)
        fieldSizer.Add(self.replaceField, proportion = 1, flag = wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, \
                       border = ReplacePanel.SPACING)
        
        sizer.Add(fieldSizer, flag = wx.EXPAND)
        
        # option checkboxes
        
        optionSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.caseCheckbox = wx.CheckBox(self, label = 'Match Case')
        self.wholeWordCheckbox = wx.CheckBox(self, label = 'Whole Word')
        self.regexpCheckbox = wx.CheckBox(self, label = 'Regular Expression')
        
        optionSizer.Add(self.caseCheckbox, flag = wx.ALL, border = ReplacePanel.SPACING)
        optionSizer.Add(self.wholeWordCheckbox, flag = wx.ALL, border = ReplacePanel.SPACING)
        optionSizer.Add(self.regexpCheckbox, flag = wx.ALL, border = ReplacePanel.SPACING)
        sizer.Add(optionSizer)
                
        # find and close buttons
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.closeButton = wx.Button(self, label = 'Close')
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        buttonSizer.Add(self.closeButton, flag = wx.ALL, border = ReplacePanel.SPACING)        
      
        if allowIncremental:
            buttonSizer.Add(wx.Panel(self))
            self.findButton = wx.Button(self, label = 'Find Next')
            self.findButton.Bind(wx.EVT_BUTTON, self.onFind)
            buttonSizer.Add(self.findButton, flag = wx.ALL, border = ReplacePanel.SPACING)
            self.replaceButton = wx.Button(self, label = 'Replace')
            self.replaceButton.Bind(wx.EVT_BUTTON, self.onReplace)
            buttonSizer.Add(self.replaceButton, flag = wx.ALL, border = ReplacePanel.SPACING)
            
        self.replaceAllButton = wx.Button(self, label = 'Replace All')
        self.replaceAllButton.Bind(wx.EVT_BUTTON, self.onReplaceAll)
        buttonSizer.Add(self.replaceAllButton, flag = wx.ALL, border = ReplacePanel.SPACING)        
        
        if allowIncremental:
            self.replaceButton.SetDefault()
        else:
            self.replaceAllButton.SetDefault()

        sizer.Add(buttonSizer, flag = wx.ALIGN_RIGHT)
        sizer.Fit(self)

    def onFind (self, event):
        """
        Passes a find message to our callback.
        """
        if self.findCallback:
            regexps = self.assembleRegexps()
            self.findCallback(regexps['find'], regexps['flags'])
    
    def onReplace (self, event):
        """
        Passes a replace message to our callback.
        """
        if self.replaceCallback:
            regexps = self.assembleRegexps()
            self.replaceCallback(regexps['find'], regexps['flags'], regexps['replace'])
    
    def onReplaceAll (self, event):
        """
        Passes a replace all message to our callback.
        """
        if self.replaceAllCallback:
            regexps = self.assembleRegexps()
            self.replaceAllCallback(regexps['find'], regexps['flags'], regexps['replace'])

    def onClose (self, event):
        """
        Passes on a close message to our callback.
        """
        if self.closeCallback: self.closeCallback()
        
    def assembleRegexps (self):
        """
        Builds up the regexp the user is searching for. Returns a dictionary with
        keys 'find', 'replace', and 'flags'.
        """
        result = {}
        result['find'] = self.findField.GetValue()
        result['replace'] = self.replaceField.GetValue()    
        result['flags'] = None
        
        if not self.regexpCheckbox.GetValue():
            result['find'] = re.escape(result['find'])
            result['replace'] = re.escape(result['replace'])

        if not self.caseCheckbox.GetValue():
            result['flags'] = re.IGNORECASE
        
        if self.wholeWordCheckbox.GetValue():
            result['find'] = r'\b' + regexp + r'\b'
    
        return result

    SPACING = 6