import wx, re, locale
from tiddlywiki import TiddlyWiki
import tweeregex
import metrics

class StatisticsDialog(wx.Dialog):
    """
    A StatisticsDialog displays the number of characters, words,
    passages, links, and broken links in a StoryPanel.

    This is not a live count.
    """

    def __init__(self, parent, storyPanel, app, id = wx.ID_ANY):
        wx.Dialog.__init__(self, parent, id, title = 'Story Statistics')
        self.storyPanel = storyPanel

        # layout

        panel = wx.Panel(parent = self)
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(self.panelSizer)

        # count controls

        countPanel = wx.Panel(parent = panel)
        countPanelSizer = wx.FlexGridSizer(6, 2, metrics.size('relatedControls'), metrics.size('relatedControls'))
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

        self.variablesCount = wx.StaticText(countPanel)
        countPanelSizer.Add(self.variablesCount, flag = wx.ALIGN_RIGHT)
        countPanelSizer.Add(wx.StaticText(countPanel, label = 'Variables Used'))

        self.panelSizer.Add(countPanel, flag = wx.ALL | wx.ALIGN_CENTER, border = metrics.size('relatedControls'))

        self.count(panel)

        okButton = wx.Button(parent = panel, label = 'OK')
        okButton.Bind(wx.EVT_BUTTON, lambda e: self.Close())
        self.panelSizer.Add(okButton, flag = wx.ALL | wx.ALIGN_CENTER, border = metrics.size('relatedControls'))

        self.panelSizer.Fit(self)

        size = self.GetSize()
        if size.width < StatisticsDialog.MIN_WIDTH:
            size.width = StatisticsDialog.MIN_WIDTH
            self.SetSize(size)

        self.panelSizer.Layout()
        self.SetIcon(app.icon)
        self.Show()

    def count(self, panel):
        """
        Sets values for the various counts.
        """

        # have to do some trickery here because Python doesn't do
        # closures the way JavaScript does

        counts = { 'words': 0, 'chars': 0, 'passages': 0, 'links': 0, 'brokenLinks': 0 }
        variables = set()
        tags = set()

        def count(widget, counts):
            if widget.passage.isStoryText():
                counts['chars'] += len(widget.passage.text)
                counts['words'] += len(widget.passage.text.split(None))
                counts['passages'] += 1
                counts['links'] += len(widget.passage.links)
                counts['brokenLinks'] += len(widget.getBrokenLinks())
                # Find variables
                iterator = re.finditer(tweeregex.MACRO_REGEX + "|" + tweeregex.LINK_REGEX, widget.passage.text, re.U|re.I)
                for p in iterator:
                    iterator2 = re.finditer(tweeregex.MACRO_PARAMS_REGEX, p.group(0), re.U|re.I)
                    for p2 in iterator2:
                        if p2.group(4):
                            variables.add(p2.group(4))
                # Find tags
                for a in widget.passage.tags:
                    if a not in TiddlyWiki.INFO_TAGS:
                        tags.add(a)

        self.storyPanel.eachWidget(lambda w: count(w, counts))
        for key in counts:
            counts[key] = locale.format('%d', counts[key], grouping = True)

        self.characters.SetLabel(str(counts['chars']))
        self.words.SetLabel(str(counts['words']))
        self.passages.SetLabel(str(counts['passages']))
        self.links.SetLabel(str(counts['links']))
        self.brokenLinks.SetLabel(str(counts['brokenLinks']))
        self.variablesCount.SetLabel(str(len(variables)))

        if len(variables):
            text = ', '.join(sorted(variables))
            variablesCtrl = wx.TextCtrl(panel, -1, size=(StatisticsDialog.MIN_WIDTH*.9, 60), style=wx.TE_MULTILINE|wx.TE_READONLY)
            variablesCtrl.AppendText(text)
            self.panelSizer.Add(variablesCtrl, flag = wx.ALIGN_CENTER)

        if len(tags):
            text = ', '.join(sorted(tags))
            tagsCtrl = wx.TextCtrl(panel, -1, size=(StatisticsDialog.MIN_WIDTH*.9, 60), style=wx.TE_MULTILINE|wx.TE_READONLY)
            tagsCtrl.AppendText(text)
            self.panelSizer.Add(wx.StaticText(panel, label = str(len(tags)) + " Tags"), flag = wx.ALIGN_CENTER)
            self.panelSizer.Add(tagsCtrl, flag = wx.ALIGN_CENTER)

    MIN_WIDTH = 300

