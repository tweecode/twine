import wx
import metrics

class PreferenceFrame(wx.Frame):
    """
    This allows the user to set their preferences. Changes automatically
    update as the user makes them; when they're done, they close the window.
    """

    def __init__(self, app, parent = None):
        self.app = app
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = self.app.NAME + ' Preferences', \
                          style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.CAPTION | wx.SYSTEM_MENU)

        panel = wx.Panel(parent = self, id = wx.ID_ANY)
        borderSizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(borderSizer)
        panelSizer = wx.FlexGridSizer(14, 2, metrics.size('relatedControls'), metrics.size('relatedControls'))
        borderSizer.Add(panelSizer, flag = wx.ALL, border = metrics.size('windowBorder'))

        self.editorFont = wx.FontPickerCtrl(panel, style = wx.FNTP_FONTDESC_AS_LABEL)
        self.editorFont.SetSelectedFont(self.getPrefFont('windowed'))
        self.editorFont.Bind(wx.EVT_FONTPICKER_CHANGED, lambda e: self.saveFontPref('windowed', \
                             self.editorFont.GetSelectedFont()))

        self.monoFont = wx.FontPickerCtrl(panel, style = wx.FNTP_FONTDESC_AS_LABEL)
        self.monoFont.SetSelectedFont(self.getPrefFont('monospace'))
        self.monoFont.Bind(wx.EVT_FONTPICKER_CHANGED, lambda e: self.saveFontPref('monospace', \
                             self.monoFont.GetSelectedFont()))

        self.fsFont = wx.FontPickerCtrl(panel, style = wx.FNTP_FONTDESC_AS_LABEL)
        self.fsFont.SetSelectedFont(self.getPrefFont('fs'))
        self.fsFont.Bind(wx.EVT_FONTPICKER_CHANGED, lambda e: self.saveFontPref('fs', \
                         self.fsFont.GetSelectedFont()))

        self.fsTextColor = wx.ColourPickerCtrl(panel)
        self.fsTextColor.SetColour(self.app.config.Read('fsTextColor'))
        self.fsTextColor.Bind(wx.EVT_COLOURPICKER_CHANGED, lambda e: self.savePref('fsTextColor', \
                              self.fsTextColor.GetColour()))

        self.fsBgColor = wx.ColourPickerCtrl(panel)
        self.fsBgColor.SetColour(self.app.config.Read('fsBgColor'))
        self.fsBgColor.Bind(wx.EVT_COLOURPICKER_CHANGED, lambda e: self.savePref('fsBgColor', \
                              self.fsBgColor.GetColour()))

        fsLineHeightPanel = wx.Panel(panel)
        fsLineHeightSizer = wx.BoxSizer(wx.HORIZONTAL)
        fsLineHeightPanel.SetSizer(fsLineHeightSizer)

        self.fsLineHeight = wx.ComboBox(fsLineHeightPanel, choices = ('100', '125', '150', '175', '200'))
        self.fsLineHeight.Bind(wx.EVT_TEXT, lambda e: self.savePref('fsLineHeight', int(self.fsLineHeight.GetValue())))
        self.fsLineHeight.SetValue(str(self.app.config.ReadInt('fslineHeight')))

        fsLineHeightSizer.Add(self.fsLineHeight, flag = wx.ALIGN_CENTER_VERTICAL)
        fsLineHeightSizer.Add(wx.StaticText(fsLineHeightPanel, label = '%'), flag = wx.ALIGN_CENTER_VERTICAL)

        def checkbox(self, name, label, panel=panel):
            setattr(self, name, wx.CheckBox(panel, label=label))
            attr = getattr(self, name)
            attr.Bind(wx.EVT_CHECKBOX, lambda e, name=name, attr=attr: self.savePref(name, attr.GetValue()))
            attr.SetValue(self.app.config.ReadBool(name))

        checkbox(self, "fastStoryPanel", 'Faster but rougher story map display')
        checkbox(self, "flatDesign", 'Flat Design(TM) mode')
        checkbox(self, "imageArrows", 'Connector arrows for images and stylesheets')
        checkbox(self, "displayArrows", 'Connector arrows for <<display>>ed passages')
        checkbox(self, "createPassagePrompt", 'Offer to create new passages for broken links')
        checkbox(self, "importImagePrompt", 'Offer to import externally linked images')
        checkbox(self, "passageWarnings", 'Warn about possible passage code errors')

        panelSizer.Add(wx.StaticText(panel, label = 'Normal Font'), flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(self.editorFont)
        panelSizer.Add(wx.StaticText(panel, label = 'Monospace Font'), flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(self.monoFont)
        panelSizer.Add(wx.StaticText(panel, label = 'Fullscreen Editor Font'), flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(self.fsFont)
        panelSizer.Add(wx.StaticText(panel, label = 'Fullscreen Editor Text Color'), flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(self.fsTextColor)
        panelSizer.Add(wx.StaticText(panel, label = 'Fullscreen Editor Background Color'), \
                       flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(self.fsBgColor)
        panelSizer.Add(wx.StaticText(panel, label = 'Fullscreen Editor Line Spacing'), flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(fsLineHeightPanel, flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add(self.fastStoryPanel) # pylint: disable=no-member
        panelSizer.Add((1,2))
        panelSizer.Add(self.flatDesign) # pylint: disable=no-member
        panelSizer.Add((1,2))
        panelSizer.Add(self.imageArrows) # pylint: disable=no-member
        panelSizer.Add((1,2))
        panelSizer.Add(self.displayArrows) # pylint: disable=no-member
        panelSizer.Add((1,2))
        panelSizer.Add(wx.StaticText(panel, label = 'When closing a passage:'), flag = wx.ALIGN_CENTER_VERTICAL)
        panelSizer.Add((1,2))
        panelSizer.Add(self.createPassagePrompt) # pylint: disable=no-member
        panelSizer.Add((1,2))
        panelSizer.Add(self.importImagePrompt) # pylint: disable=no-member
        panelSizer.Add((1,2))
        panelSizer.Add(self.passageWarnings) # pylint: disable=no-member

        panelSizer.Fit(self)
        borderSizer.Fit(self)
        self.SetIcon(self.app.icon)
        self.Show()
        self.panelSizer = panelSizer
        self.borderSizer = borderSizer

    def getPrefFont(self, key):
        """
        Returns a font saved in preferences as a wx.Font instance.
        """
        return wx.Font(self.app.config.ReadInt(key + 'FontSize'), wx.FONTFAMILY_MODERN, \
                       wx.FONTSTYLE_NORMAL, wx.NORMAL, False, self.app.config.Read(key + 'FontFace'))

    def savePref(self, key, value):
        """
        Saves changes to a preference and sends an update message to the application.
        """
        if isinstance(value, wx.Colour):
            self.app.config.Write(key, value.GetAsString(wx.C2S_HTML_SYNTAX))
        elif type(value) is int:
            self.app.config.WriteInt(key, value)
        elif type(value) is bool:
            self.app.config.WriteBool(key, value)
        else:
            self.app.config.Write(key, value)

        self.app.applyPrefs()

    def saveFontPref(self, key, font):
        """
        Saves a user-chosen font to preference keys, then sends an update message to the application.
        """
        self.app.config.Write(key + 'FontFace', font.GetFaceName())
        self.app.config.WriteInt(key + 'FontSize', font.GetPointSize())
        self.app.applyPrefs()
        self.panelSizer.Fit(self)
        self.borderSizer.Fit(self)

