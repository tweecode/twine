#!/usr/bin/env python

#
# StatisticsDialog
# A StatisticsDialog displays the number of characters, words,
# passages, links, and broken links in a StoryPanel.
#
# This is not a live count.
#

import wx, re, locale

class StatisticsDialog (wx.Dialog):
    
    def __init__ (self, parent, storyPanel, app, id = wx.ID_ANY):
        wx.Dialog.__init__(self, parent, id, title = 'Story Statistics')
        self.storyPanel = storyPanel
        
        # layout
        
        panel = wx.Panel(parent = self)
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(panelSizer)
        
        # count controls
        
        countPanel = wx.Panel(parent = panel)
        countPanelSizer = wx.FlexGridSizer(5, 2, StatisticsDialog.SPACING, StatisticsDialog.SPACING)
        countPanel.SetSizer(countPanelSizer)
        
        self.characters = wx.StaticText(countPanel)
        countPanelSizer.Add(self.characters, flag = wx.ALIGN_RIGHT)
        countPanelSizer.Add(wx.StaticText(countPanel, label = 'Characters'))
        
        self.words = wx.StaticText(countPanel)
        countPanelSizer.Add(self.words, flag = wx.ALIGN_RIGHT)
        countPanelSizer.Add(wx.StaticText(countPanel, label = 'Words'))
        
        self.passages = wx.StaticText(countPanel)
        countPanelSizer.Add(self.passages, flag = wx.ALIGN_RIGHT)
        countPanelSizer.Add(wx.StaticText(countPanel, label = 'Passages'))
        
        self.links = wx.StaticText(countPanel)
        countPanelSizer.Add(self.links, flag = wx.ALIGN_RIGHT)
        countPanelSizer.Add(wx.StaticText(countPanel, label = 'Links'))
        
        self.brokenLinks = wx.StaticText(countPanel)
        countPanelSizer.Add(self.brokenLinks, flag = wx.ALIGN_RIGHT)
        countPanelSizer.Add(wx.StaticText(countPanel, label = 'Broken Links'))

        panelSizer.Add(countPanel, flag = wx.ALL | wx.ALIGN_CENTER, border = 6)
        
        okButton = wx.Button(parent = panel, label = 'OK')
        okButton.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        panelSizer.Add(okButton, flag = wx.ALL | wx.ALIGN_CENTER, border = 12)
        
        panelSizer.Fit(self)
        
        size = self.GetSize()
        if size.width < StatisticsDialog.MIN_WIDTH:
            size.width = StatisticsDialog.MIN_WIDTH
            self.SetSize(size)

        self.count()
        panelSizer.Layout()
        self.SetIcon(app.icon)
        self.Show()
        
    def count (self):
        """
        Sets values for the various counts.
        """
        
        # have to do some trickery here because Python doesn't do
        # closures the way JavaScript does
        
        counts = { 'words': 0, 'chars': 0, 'passages': 0, 'links': 0, 'brokenLinks': 0 }
        
        def count (widget, counts):
            counts['chars'] += len(widget.passage.text)
            counts['words'] += len(widget.passage.text.split(None))
            counts['passages'] += 1
            counts['links'] += len(widget.passage.links())
            counts['brokenLinks'] += len(widget.getBrokenLinks())
        
        self.storyPanel.eachWidget(lambda w: count(w, counts))
        for key in counts:
            counts[key] = locale.format('%d', counts[key], grouping = True)
            
        self.characters.SetLabel(str(counts['chars']))
        self.words.SetLabel(str(counts['words']))
        self.passages.SetLabel(str(counts['passages']))
        self.links.SetLabel(str(counts['links']))
        self.brokenLinks.SetLabel(str(counts['brokenLinks']))


    SPACING = 6
    MIN_WIDTH = 200     # total guesstimate