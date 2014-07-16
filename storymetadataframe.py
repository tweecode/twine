import wx
import metrics

class StoryMetadataFrame(wx.Frame):
    """
    Changes automatically update as the user makes them;
    """

    def __init__(self, app, parent = None):
        self.app = app
        self.parent = parent
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = parent.title + ' Metadata', \
                          style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.CAPTION | wx.SYSTEM_MENU)

        panel = wx.Panel(parent = self, id = wx.ID_ANY)
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(borderSizer)
        panelSizer = wx.FlexGridSizer(8, 1, metrics.size('relatedControls'), metrics.size('relatedControls'))
        borderSizer.Add(panelSizer, flag = wx.ALL, border = metrics.size('windowBorder'))

        for name, desc in [
              ("identity", ("What your work identifies as:",
                            "Is it a game, a story, a poem, or something else?\n(This is used for dialogs and error messages only.)",
                            False)),
              ("description", ("A short description of your work:",
                               "This is inserted in the HTML file's <meta> description tag, used by\nsearch engines and other automated tools.",
                               True))
            ]:
            textlabel = wx.StaticText(panel, label = desc[0])
            if desc[2]:
                textctrl = wx.TextCtrl(panel, size=(200,60), style=wx.TE_MULTILINE)
            else:
                textctrl = wx.TextCtrl(panel, size=(200,-1))
            textctrl.SetValue(parent.metadata.get(name, ''))
            textctrl.Bind(wx.EVT_TEXT, lambda e, name=name, textctrl=textctrl:
                              self.saveSetting(name,textctrl.GetValue()))

            hSizer = wx.BoxSizer(wx.HORIZONTAL)
            hSizer.Add(textlabel,1,wx.ALIGN_LEFT|wx.ALIGN_TOP)
            hSizer.Add(textctrl,1,wx.EXPAND)
            panelSizer.Add(hSizer,flag=wx.ALL|wx.EXPAND)
            panelSizer.Add(wx.StaticText(panel, label = desc[1]))
            panelSizer.Add((1,2))

        panelSizer.Fit(self)
        borderSizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()
        self.panelSizer = panelSizer
        self.borderSizer = borderSizer

    def saveSetting(self, name, value):
        self.parent.metadata[name]=value
        self.parent.setDirty(True)
