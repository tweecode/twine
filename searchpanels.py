import re, wx
import metrics

class FindPanel(wx.Panel):
    """
    This allows the user to enter a search term and select various
    criteria (i.e. "match case", etc.) There are two callbacks:

    onFind (regexp, flags)
    Regexp corresponds to the user's search, and flags should be used
    when performing that search.

    onClose()
    When the user clicks the Close button.
    """

    def __init__(self, parent, onFind = None, onClose = None):
        self.findCallback = onFind
        self.closeCallback = onClose

        wx.Panel.__init__(self, parent)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # find text and label

        findSizer = wx.BoxSizer(wx.HORIZONTAL)

        findSizer.Add(wx.StaticText(self, label = 'Find'), flag = wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, \
                      border = metrics.size('relatedControls'), proportion = 0)
        self.findField = wx.TextCtrl(self)
        findSizer.Add(self.findField, proportion = 1, flag = wx.BOTTOM | wx.EXPAND, \
                      border = metrics.size('relatedControls'))
        sizer.Add(findSizer, flag = wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border = metrics.size('windowBorder'))

        # option checkboxes

        optionSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.caseCheckbox = wx.CheckBox(self, label = 'Match Case')
        self.wholeWordCheckbox = wx.CheckBox(self, label = 'Whole Word')
        self.regexpCheckbox = wx.CheckBox(self, label = 'Regular Expression')

        optionSizer.Add(self.caseCheckbox, flag = wx.BOTTOM | wx.RIGHT, border = metrics.size('relatedControls'))
        optionSizer.Add(self.wholeWordCheckbox, flag = wx.BOTTOM | wx.LEFT | wx.RIGHT, \
                        border = metrics.size('relatedControls'))
        optionSizer.Add(self.regexpCheckbox, flag = wx.BOTTOM | wx.LEFT, \
                        border = metrics.size('relatedControls'))
        sizer.Add(optionSizer, flag = wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, \
                  border = metrics.size('windowBorder'))

        # find and close buttons

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.closeButton = wx.Button(self, label = 'Close')
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)

        self.findButton = wx.Button(self, label = 'Find Next')
        self.findButton.Bind(wx.EVT_BUTTON, self.onFind)

        buttonSizer.Add(self.closeButton, flag = wx.TOP | wx.RIGHT, border = metrics.size('buttonSpace'))
        buttonSizer.Add(self.findButton, flag = wx.TOP, border = metrics.size('buttonSpace'))
        sizer.Add(buttonSizer, flag = wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT | wx.RIGHT, \
                  border = metrics.size('windowBorder'))
        sizer.Fit(self)

    def focus(self):
        """
        Focuses the proper text input and sets our default button.
        """
        self.findField.SetFocus()
        self.findButton.SetDefault()

    def updateUI(self, event):
        pass

    def onFind(self, event):
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

    def onClose(self, event):
        """
        Passes on a close message to our callback.
        """
        if self.closeCallback: self.closeCallback()

class ReplacePanel(wx.Panel):
    """
    This allows the user to enter a search and replace term and select
    various criteria (i.e. "match case", etc.) There are two callbacks:

    onFind (regexp, flags)
    Regexp corresponds to the user's search, and flags should be used
    when performing that search.

    onReplace (regexp, flags, replaceTerm)
    Like find, only with a replaceTerm.

    onReplaceAll (regexp, flags, replaceTerm)
    Like replace, only the user is signalling that they want to replace
    all instances at once.

    onClose()
    When the user clicks the Close button.

    You may also pass in a parameter to set whether users can perform
    incremental searches, or if they may only replace all.
    """

    def __init__(self, parent, allowIncremental = True, \
                  onFind = None, onReplace = None, onReplaceAll = None, onClose = None):
        self.allowIncremental = allowIncremental
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

        fieldSizer.Add(wx.StaticText(self, label = 'Find'), \
                       flag = wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, \
                       border = metrics.size('relatedControls'), proportion = 0)
        self.findField = wx.TextCtrl(self)
        fieldSizer.Add(self.findField, proportion = 1, flag = wx.BOTTOM | wx.EXPAND, \
                       border = metrics.size('relatedControls'))

        # replace text and label

        fieldSizer.Add(wx.StaticText(self, label = 'Replace With'), \
                       flag = wx.BOTTOM | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, \
                       border = metrics.size('relatedControls'), proportion = 0)
        self.replaceField = wx.TextCtrl(self)
        fieldSizer.Add(self.replaceField, proportion = 1, flag = wx.BOTTOM | wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, \
                       border = metrics.size('relatedControls'))

        sizer.Add(fieldSizer, flag = wx.EXPAND | wx.TOP | wx.LEFT | wx.RIGHT, border = metrics.size('windowBorder'))

        # option checkboxes

        optionSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.caseCheckbox = wx.CheckBox(self, label = 'Match Case')
        self.wholeWordCheckbox = wx.CheckBox(self, label = 'Whole Word')
        self.regexpCheckbox = wx.CheckBox(self, label = 'Regular Expression')

        optionSizer.Add(self.caseCheckbox, flag = wx.BOTTOM | wx.TOP | wx.RIGHT, \
                        border = metrics.size('relatedControls'))
        optionSizer.Add(self.wholeWordCheckbox, flag = wx.BOTTOM | wx.TOP | wx.LEFT | wx.RIGHT, \
                        border = metrics.size('relatedControls'))
        optionSizer.Add(self.regexpCheckbox, flag = wx.BOTTOM | wx.TOP | wx.LEFT, \
                        border = metrics.size('relatedControls'))
        sizer.Add(optionSizer, flag = wx.LEFT | wx.RIGHT, border = metrics.size('windowBorder'))

        # find and close buttons

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.closeButton = wx.Button(self, label = 'Close')
        self.closeButton.Bind(wx.EVT_BUTTON, self.onClose)
        buttonSizer.Add(self.closeButton, flag = wx.TOP | wx.RIGHT, border = metrics.size('buttonSpace'))

        if allowIncremental:
            buttonSizer.Add(wx.Panel(self))
            self.findButton = wx.Button(self, label = 'Find Next')
            self.findButton.Bind(wx.EVT_BUTTON, self.onFind)
            buttonSizer.Add(self.findButton, flag = wx.TOP | wx.LEFT | wx.RIGHT, \
                            border = metrics.size('buttonSpace'))
            self.replaceButton = wx.Button(self, label = 'Replace')
            self.replaceButton.Bind(wx.EVT_BUTTON, self.onReplace)
            buttonSizer.Add(self.replaceButton, flag = wx.TOP | wx.RIGHT, border = metrics.size('buttonSpace'))

        self.replaceAllButton = wx.Button(self, label = 'Replace All')
        self.replaceAllButton.Bind(wx.EVT_BUTTON, self.onReplaceAll)
        buttonSizer.Add(self.replaceAllButton, flag = wx.TOP, border = metrics.size('buttonSpace'))

        sizer.Add(buttonSizer, flag = wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, \
                  border = metrics.size('windowBorder'))
        sizer.Fit(self)

    def focus(self):
        """
        Focuses the proper text input and sets our default button.
        """
        self.findField.SetFocus()
        if self.allowIncremental:
            self.replaceButton.SetDefault()
        else:
            self.replaceAllButton.SetDefault()

    def onFind(self, event):
        """
        Passes a find message to our callback.
        """
        if self.findCallback:
            regexps = self.assembleRegexps()
            self.findCallback(regexps['find'], regexps['flags'])

    def onReplace(self, event):
        """
        Passes a replace message to our callback.
        """
        if self.replaceCallback:
            regexps = self.assembleRegexps()
            self.replaceCallback(regexps['find'], regexps['flags'], regexps['replace'])

    def onReplaceAll(self, event):
        """
        Passes a replace all message to our callback.
        """
        if self.replaceAllCallback:
            regexps = self.assembleRegexps()
            self.replaceAllCallback(regexps['find'], regexps['flags'], regexps['replace'])

    def onClose(self, event):
        """
        Passes on a close message to our callback.
        """
        if self.closeCallback: self.closeCallback()

    def assembleRegexps(self):
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

        if not self.caseCheckbox.GetValue():
            result['flags'] = re.IGNORECASE

        if self.wholeWordCheckbox.GetValue():
            result['find'] = r'\b' + result['find'] + r'\b'

        return result
