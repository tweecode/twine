import sys, os, re, threading, wx, wx.lib.scrolledpanel, wx.animate, base64, tweeregex
import metrics, images
from version import versionString
from tweelexer import TweeLexer
from tweestyler import TweeStyler
from tiddlywiki import TiddlyWiki
from passagesearchframe import PassageSearchFrame
from fseditframe import FullscreenEditFrame
from utils import isURL
import cStringIO

class PassageFrame(wx.Frame):
    """
    A PassageFrame is a window that allows the user to change the contents
    of a passage. This must be paired with a PassageWidget; it gets to the
    underlying passage via it, and also notifies it of changes made here.

    This doesn't require the user to save their changes -- as they make
    changes, they are automatically updated everywhere.

    nb: This does not make use of wx.stc's built-in find/replace functions.
    This is partially for user interface reasons, as find/replace at the
    StoryPanel level uses Python regexps, not Scintilla ones. It's also
    because SearchPanel and ReplacePanel hand back regexps, so we wouldn't
    know what flags to pass to wx.stc.
    """

    def __init__(self, parent, widget, app):
        self.widget = widget
        self.app = app
        self.syncTimer = None
        self.lastFindRegexp = None
        self.lastFindFlags = None
        self.usingLexer = self.LEXER_NORMAL
        self.titleInvalid = False

        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Untitled Passage - ' + self.app.NAME + ' ' + versionString, \
                          size = PassageFrame.DEFAULT_SIZE)

        # Passage menu

        passageMenu = wx.Menu()

        passageMenu.Append(PassageFrame.PASSAGE_EDIT_SELECTION, 'Create &Link From Selection\tCtrl-L')
        self.Bind(wx.EVT_MENU, self.editSelection, id = PassageFrame.PASSAGE_EDIT_SELECTION)

        self.outLinksMenu = wx.Menu()
        self.outLinksMenuTitle = passageMenu.AppendMenu(wx.ID_ANY, 'Outgoing Links', self.outLinksMenu)
        self.inLinksMenu = wx.Menu()
        self.inLinksMenuTitle = passageMenu.AppendMenu(wx.ID_ANY, 'Incoming Links', self.inLinksMenu)
        self.brokenLinksMenu = wx.Menu()
        self.brokenLinksMenuTitle = passageMenu.AppendMenu(wx.ID_ANY, 'Broken Links', self.brokenLinksMenu)

        passageMenu.AppendSeparator()

        passageMenu.Append(wx.ID_SAVE, '&Save Story\tCtrl-S')
        self.Bind(wx.EVT_MENU, self.widget.parent.parent.save, id = wx.ID_SAVE)

        passageMenu.Append(PassageFrame.PASSAGE_VERIFY, '&Verify Passage\tCtrl-E')
        self.Bind(wx.EVT_MENU, lambda e: (self.widget.verifyPassage(self), self.offerAssistance()),\
                  id = PassageFrame.PASSAGE_VERIFY)

        passageMenu.Append(PassageFrame.PASSAGE_TEST_HERE, '&Test Play From Here\tCtrl-T')
        self.Bind(wx.EVT_MENU, lambda e: self.widget.parent.parent.testBuild(e, startAt = self.widget.passage.title),\
                  id = PassageFrame.PASSAGE_TEST_HERE)

        passageMenu.Append(PassageFrame.PASSAGE_REBUILD_STORY, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.widget.parent.parent.rebuild, id = PassageFrame.PASSAGE_REBUILD_STORY)

        passageMenu.AppendSeparator()

        passageMenu.Append(PassageFrame.PASSAGE_FULLSCREEN, '&Fullscreen View\tF12')
        self.Bind(wx.EVT_MENU, self.openFullscreen, id = PassageFrame.PASSAGE_FULLSCREEN)

        passageMenu.Append(wx.ID_CLOSE, '&Close Passage\tCtrl-W')
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), id = wx.ID_CLOSE)

        # Edit menu

        editMenu = wx.Menu()

        editMenu.Append(wx.ID_UNDO, '&Undo\tCtrl-Z')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Undo(), id = wx.ID_UNDO)

        if sys.platform == 'darwin':
            shortcut = 'Ctrl-Shift-Z'
        else:
            shortcut = 'Ctrl-Y'

        editMenu.Append(wx.ID_REDO, '&Redo\t' + shortcut)
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Redo(), id = wx.ID_REDO)

        editMenu.AppendSeparator()

        editMenu.Append(wx.ID_CUT, 'Cu&t\tCtrl-X')
        self.Bind(wx.EVT_MENU, lambda e: wx.Window.FindFocus().Cut(), id = wx.ID_CUT)

        editMenu.Append(wx.ID_COPY, '&Copy\tCtrl-C')
        self.Bind(wx.EVT_MENU, lambda e: wx.Window.FindFocus().Copy(), id = wx.ID_COPY)

        editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl-V')
        self.Bind(wx.EVT_MENU, lambda e: wx.Window.FindFocus().Paste(), id = wx.ID_PASTE)


        editMenu.Append(wx.ID_SELECTALL, 'Select &All\tCtrl-A')
        self.Bind(wx.EVT_MENU, lambda e: wx.Window.FindFocus().SelectAll(), id = wx.ID_SELECTALL)

        editMenu.AppendSeparator()

        editMenu.Append(wx.ID_FIND, '&Find...\tCtrl-F')
        self.Bind(wx.EVT_MENU, lambda e: self.showSearchFrame(PassageSearchFrame.FIND_TAB), id = wx.ID_FIND)

        editMenu.Append(PassageFrame.EDIT_FIND_NEXT, 'Find &Next\tCtrl-G')
        self.Bind(wx.EVT_MENU, self.findNextRegexp, id = PassageFrame.EDIT_FIND_NEXT)

        if sys.platform == 'darwin':
            shortcut = 'Ctrl-Shift-H'
        else:
            shortcut = 'Ctrl-H'

        editMenu.Append(wx.ID_REPLACE, '&Replace...\t' + shortcut)
        self.Bind(wx.EVT_MENU, lambda e: self.showSearchFrame(PassageSearchFrame.REPLACE_TAB), id = wx.ID_REPLACE)

        # help menu

        helpMenu = wx.Menu()

        if self.widget.passage.isStylesheet():
            helpMenu.Append(PassageFrame.HELP1, 'About Stylesheets')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/stylesheet'), id = PassageFrame.HELP1)
        elif self.widget.passage.isScript():
            helpMenu.Append(PassageFrame.HELP1, 'About Scripts')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/script'), id = PassageFrame.HELP1)
        else:
            helpMenu.Append(PassageFrame.HELP1, 'About Passages')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/passage'), id = PassageFrame.HELP1)

            helpMenu.Append(PassageFrame.HELP2, 'About Text Syntax')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/syntax'), id = PassageFrame.HELP2)

            helpMenu.Append(PassageFrame.HELP3, 'About Links')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/link'), id = PassageFrame.HELP3)

            helpMenu.Append(PassageFrame.HELP4, 'About Macros')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/macro'), id = PassageFrame.HELP4)

            helpMenu.Append(PassageFrame.HELP5, 'About Tags')
            self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/tag'), id = PassageFrame.HELP5)

        # menus

        self.menus = wx.MenuBar()
        self.menus.Append(passageMenu, '&Passage')
        self.menus.Append(editMenu, '&Edit')
        self.menus.Append(helpMenu, '&Help')
        self.SetMenuBar(self.menus)

        # controls

        self.panel = wx.Panel(self)
        allSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(allSizer)

        # title/tag controls

        self.topControls = wx.Panel(self.panel)
        topSizer = wx.FlexGridSizer(3, 2, metrics.size('relatedControls'), metrics.size('relatedControls'))

        self.titleLabel = wx.StaticText(self.topControls, style = wx.ALIGN_RIGHT, label = PassageFrame.TITLE_LABEL)
        self.titleInput = wx.TextCtrl(self.topControls)
        tagsLabel = wx.StaticText(self.topControls, style = wx.ALIGN_RIGHT, label = PassageFrame.TAGS_LABEL)
        self.tagsInput = wx.TextCtrl(self.topControls)
        topSizer.Add(self.titleLabel, 0, flag = wx.ALL, border = metrics.size('focusRing'))
        topSizer.Add(self.titleInput, 1, flag = wx.EXPAND | wx.ALL, border = metrics.size('focusRing'))
        topSizer.Add(tagsLabel, 0, flag = wx.ALL, border = metrics.size('focusRing'))
        topSizer.Add(self.tagsInput, 1, flag = wx.EXPAND | wx.ALL, border = metrics.size('focusRing'))
        topSizer.AddGrowableCol(1, 1)
        self.topControls.SetSizer(topSizer)

        # body text

        self.bodyInput = wx.stc.StyledTextCtrl(self.panel, style = wx.TE_PROCESS_TAB | wx.BORDER_SUNKEN)
        self.bodyInput.SetUseHorizontalScrollBar(False)
        self.bodyInput.SetMargins(8, 8)
        self.bodyInput.SetMarginWidth(1, 0)
        self.bodyInput.SetTabWidth(4)
        self.bodyInput.SetWrapMode(wx.stc.STC_WRAP_WORD)
        self.bodyInput.SetSelBackground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.bodyInput.SetSelForeground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
        self.bodyInput.SetFocus()

        # The default keyboard shortcuts for StyledTextCtrl are
        # nonstandard on Mac OS X
        if sys.platform == "darwin":
            # cmd-left/right to move to beginning/end of line
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_LEFT, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_HOMEDISPLAY)
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_LEFT, wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT, wx.stc.STC_CMD_HOMEDISPLAYEXTEND)
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_RIGHT, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_LINEENDDISPLAY)
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_RIGHT, wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT, wx.stc.STC_CMD_LINEENDDISPLAYEXTEND)
            # opt-left/right to move forward/back a word
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_LEFT, wx.stc.STC_SCMOD_ALT, wx.stc.STC_CMD_WORDLEFT)
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_LEFT, wx.stc.STC_SCMOD_ALT | wx.stc.STC_SCMOD_SHIFT, wx.stc.STC_CMD_WORDLEFTEXTEND)
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_RIGHT, wx.stc.STC_SCMOD_ALT, wx.stc.STC_CMD_WORDRIGHT)
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_RIGHT, wx.stc.STC_SCMOD_ALT | wx.stc.STC_SCMOD_SHIFT, wx.stc.STC_CMD_WORDRIGHTEXTEND)
            # cmd-delete to delete from the cursor to beginning of line
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_BACK, wx.stc.STC_SCMOD_CTRL, wx.stc.STC_CMD_DELLINELEFT)
            # opt-delete to delete the previous/current word
            self.bodyInput.CmdKeyAssign(wx.stc.STC_KEY_BACK, wx.stc.STC_SCMOD_ALT, wx.stc.STC_CMD_DELWORDLEFT)
            # cmd-shift-z to redo
            self.bodyInput.CmdKeyAssign(ord('Z'), wx.stc.STC_SCMOD_CTRL | wx.stc.STC_SCMOD_SHIFT, wx.stc.STC_CMD_REDO)

        # final layout

        allSizer.Add(self.topControls, flag = wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, border = metrics.size('windowBorder'))
        allSizer.Add(self.bodyInput, proportion = 1, flag = wx.TOP | wx.EXPAND, border = metrics.size('relatedControls'))
        self.lexer = TweeStyler(self.bodyInput, self)
        self.applyPrefs()
        self.syncInputs()
        self.bodyInput.EmptyUndoBuffer()
        self.updateSubmenus()
        self.setLexer()

        # event bindings
        # we need to do this AFTER setting up initial values

        self.titleInput.Bind(wx.EVT_TEXT, self.syncPassage)
        self.tagsInput.Bind(wx.EVT_TEXT, self.syncPassage)
        self.bodyInput.Bind(wx.stc.EVT_STC_CHANGE, self.syncPassage)
        self.bodyInput.Bind(wx.stc.EVT_STC_START_DRAG, self.prepDrag)
        self.Bind(wx.EVT_CLOSE, self.closeEditor)
        self.Bind(wx.EVT_MENU_OPEN, self.updateSubmenus)
        self.Bind(wx.EVT_UPDATE_UI, self.updateUI)

        if not re.match('Untitled Passage \d+', self.widget.passage.title):
            self.bodyInput.SetFocus()
            self.bodyInput.SetSelection(-1, -1)

        # Hack to force titles (>18 char) to display correctly.
        # NOTE: stops working if moved above bodyInput code.
        self.titleInput.SetInsertionPoint(0)

        self.SetIcon(self.app.icon)
        self.Show(True)

    def title(self, title = None):
        if not title:
            title = self.widget.passage.title
        return title + ' - ' + self.widget.parent.parent.title + ' - ' + self.app.NAME + ' ' + versionString

    def syncInputs(self):
        """Updates the inputs based on the passage's state."""
        self.titleInput.SetValue(self.widget.passage.title)
        self.bodyInput.SetText(self.widget.passage.text)

        tags = ''

        for tag in self.widget.passage.tags:
            tags += tag + ' '

        self.tagsInput.SetValue(tags)
        self.SetTitle(self.title())

    def syncPassage(self, event = None):
        """Updates the passage based on the inputs; asks our matching widget to repaint."""
        title = self.titleInput.GetValue() if len(self.titleInput.GetValue()) > 0 else ""
        title = title.replace('\n','')

        def error():
            self.titleInput.SetBackgroundColour((240,130,130))
            self.titleInput.Refresh()
            self.titleInvalid = True

        if title:
        # Check for title conflict
            otherTitled = self.widget.parent.findWidget(title)
            if otherTitled is not self.widget:
                self.titleLabel.SetLabel("Title is already in use!")
                error()
            elif self.widget.parent.includedPassageExists(title):
                self.titleLabel.SetLabel("Used by a StoryIncludes file.")
                error()
            elif "|" in title or "]" in title:
                self.titleLabel.SetLabel("No | or ] symbols allowed!")
                error()
            elif title == "StorySettings":
                self.titleLabel.SetLabel("That title is reserved.")
                error()
            else:
                if self.titleInvalid:
                    self.titleLabel.SetLabel(self.TITLE_LABEL)
                    self.titleInput.SetBackgroundColour((255,255,255))
                    self.titleInput.Refresh()
                    self.titleInvalid = True
                self.widget.parent.changeWidgetTitle(self.widget.passage.title, title)

        # Set body text
        self.widget.passage.text = self.bodyInput.GetText()
        # Preserve the special (uneditable) tags
        self.widget.passage.tags = []
        self.widget.clearPaintCache()

        for tag in self.tagsInput.GetValue().split(' '):
            if tag != '' and tag not in TiddlyWiki.SPECIAL_TAGS:
                self.widget.passage.tags.append(tag)
            if tag == "StoryIncludes" and self.widget.parent.parent.autobuildmenuitem.IsChecked():
                self.widget.parent.parent.autoBuildStart()

        self.SetTitle(self.title())

        # immediately mark the story dirty

        self.widget.parent.parent.setDirty(True)

        # reposition if changed size
        self.widget.findSpace()

        # reset redraw timer

        def reallySync(self):
            try:
                self.widget.parent.Refresh()
            except:
                pass

        if self.syncTimer:
            self.syncTimer.cancel()

        self.syncTimer = threading.Timer(PassageFrame.PARENT_SYNC_DELAY, reallySync, [self], {})
        self.syncTimer.start()

        # update links/displays lists
        self.widget.passage.update()

        # change our lexer as necessary

        self.setLexer()

    def openFullscreen(self, event = None):
        """Opens a FullscreenEditFrame for this passage's body text."""
        self.Hide()
        self.fullscreen = FullscreenEditFrame(None, self.app, \
                                              title = self.title(), \
                                              initialText = self.widget.passage.text, \
                                              callback = self.setBodyText, frame = self)

    def offerAssistance(self):
        """
        Offer to fulfill certain incomplete tasks evident from the state of the passage text.
        (Technically, none of this needs to be on passageFrame instead of passageWidget.)
        """

        # Offer to create passage for broken links
        if self.app.config.ReadBool('createPassagePrompt'):
            brokens = [link for link in self.widget.getBrokenLinks() if TweeLexer.linkStyle(link) == TweeLexer.BAD_LINK]
            if brokens :
                if len(brokens) > 1:
                    brokenmsg = 'create ' + str(len(brokens)) + ' new passages to match these broken links?'
                else:
                    brokenmsg = 'create the passage "' + brokens[0] + '"?'
                dialog = wx.MessageDialog(self, 'Do you want to ' + brokenmsg, 'Create Passages', \
                                                  wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT)
                check = dialog.ShowModal()
                if check == wx.ID_YES:
                    for title in brokens:
                        self.widget.parent.newWidget(title = title, pos = self.widget.parent.toPixels (self.widget.pos))
                elif check == wx.ID_CANCEL:
                    return False

        # Offer to import external images
        if self.app.config.ReadBool('importImagePrompt'):
            regex = tweeregex.EXTERNAL_IMAGE_REGEX
            externalimages = re.finditer(regex, self.widget.passage.text)
            check = None
            downloadedurls = {}
            storyframe = self.widget.parent.parent
            for img in externalimages:
                if not check:
                    dialog = wx.MessageDialog(self, 'Do you want to import the image files linked\nin this passage into the story file?', 'Import Images', \
                                                  wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT)
                    check = dialog.ShowModal()
                    if check == wx.ID_NO:
                        break
                    elif check == wx.ID_CANCEL:
                        return False
                # Download the image if it's at an absolute URL
                imgurl = img.group(4) or img.group(7)
                if not imgurl:
                    continue
                # If we've downloaded it before, don't do it again
                if imgurl not in downloadedurls:
                    # Internet image, or local image?
                    if isURL(imgurl):
                        imgpassagename = storyframe.importImageURL(imgurl, showdialog=False)
                    else:
                        imgpassagename = storyframe.importImageFile(storyframe.getLocalDir()+os.sep+imgurl, showdialog=False)
                    if not imgpassagename:
                        continue
                    downloadedurls[imgurl] = imgpassagename

            # Replace all found images
            for old, new in downloadedurls.iteritems():
                self.widget.passage.text = re.sub(regex.replace(tweeregex.IMAGE_FILENAME_REGEX, re.escape(old)),
                                                  lambda m: m.group(0).replace(old, new), self.widget.passage.text)

        if self.bodyInput.GetText() != self.widget.passage.text:
            self.bodyInput.SetText(self.widget.passage.text)

        # If it's StoryIncludes, update the links
        if self.widget.passage.title == "StoryIncludes":
            self.widget.parent.refreshIncludedPassageList()

        return True

    def closeEditor(self, event = None):
        """
        Do extra stuff on closing the editor
        """

        # Show warnings, do replacements
        if self.app.config.ReadBool('passageWarnings'):
            if self.widget.verifyPassage(self) == -1: return

        # Do help
        if not self.offerAssistance():
            return

        #Closes this editor's fullscreen counterpart, if any.
        try: self.fullscreen.Destroy()
        except: pass

        self.widget.passage.update()
        event.Skip()

    def openOtherEditor(self, event = None, title = None):
        """
        Opens another passage for editing. If it does not exist, then
        it creates it next to this one and then opens it. You may pass
        this a string title OR an event. If you pass an event, it presumes
        it is a wx.CommandEvent, and uses the exact text of the menu as the title.
        """

        # we seem to be receiving CommandEvents, not MenuEvents,
        # so we can only see menu item IDs
        # unfortunately all our menu items are dynamically generated
        # so we gotta work our way back to a menu name

        if not title: title = self.menus.FindItemById(event.GetId()).GetLabel()

        # check if the passage already exists

        editingWidget = self.widget.parent.findWidget(title)

        if not editingWidget:
            editingWidget = self.widget.parent.newWidget(title = title, pos = self.widget.parent.toPixels (self.widget.pos))

        editingWidget.openEditor()

    def showSearchFrame(self, type):
        """
        Shows a PassageSearchFrame for this frame, creating it if need be.
        The type parameter should be one of the constants defined in
        PassageSearchFrame, e.g. FIND_TAB or REPLACE_TAB.
        """
        if not hasattr(self, 'searchFrame'):
            self.searchFrame = PassageSearchFrame(self, self, self.app, type)
        else:
            try:
                self.searchFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'searchFrame')
                self.showSearchFrame(type)

    def setBodyText(self, text):
        """Changes the body text field directly."""
        self.bodyInput.SetText(text)
        self.Show(True)

    def prepDrag(self, event):
        """
        Tells our StoryPanel about us so that it can tell us what to do in response to
        dropping some text into it.
        """
        event.SetDragAllowMove(True)
        self.widget.parent.textDragSource = self

    def getSelection(self):
        """
        Returns the beginning and end of the selection as a tuple.
        """
        return self.bodyInput.GetSelection()

    def getSelectedText(self):
        """
        Returns the text currently selected.
        """
        return self.bodyInput.GetSelectedText()

    def setSelection(self, range):
        """
        Changes the current selection to the range passed.
        """
        self.bodyInput.SetSelection(range[0], range[1])

    def editSelection(self, event = None):
        """
        If the selection isn't already double-bracketed, then brackets are added.
        If a passage with the selection title doesn't exist, it is created.
        Finally, an editor is opened for the passage.
        """
        rawSelection = self.bodyInput.GetSelectedText()
        title = self.stripCrud(rawSelection)
        if not re.match(r'^\[\[.*\]\]$', rawSelection): self.linkSelection()
        self.openOtherEditor(title = title)
        self.updateSubmenus()

    def linkSelection(self):
        """Transforms the selection into a link by surrounding it with double brackets."""
        selStart = self.bodyInput.GetSelectionStart()
        selEnd = self.bodyInput.GetSelectionEnd()
        self.bodyInput.SetSelection(selStart, selEnd)
        self.bodyInput.ReplaceSelection("[["+self.bodyInput.GetSelectedText()+"]]")

    def findRegexp(self, regexp, flags):
        """
        Selects a regexp in the body text.
        """
        self.lastFindRegexp = regexp
        self.lastFindFlags = flags

        # find the beginning of our search

        text = self.bodyInput.GetText()
        oldSelection = self.bodyInput.GetSelection()

        # try past the selection

        match = re.search(regexp, text[oldSelection[1]:], flags)
        if match:
            self.bodyInput.SetSelection(match.start() + oldSelection[1], match.end() + oldSelection[1])
        else:
            # try before the selection
            match = re.search(regexp, text[:oldSelection[1]], flags)
            if match:
                self.bodyInput.SetSelection(match.start(), match.end())
            else:
                # give up
                dialog = wx.MessageDialog(self, 'The text you entered was not found in this passage.', \
                                          'Not Found', wx.ICON_INFORMATION | wx.OK)
                dialog.ShowModal()

    def findNextRegexp(self, event = None):
        """
        Performs a search for the last regexp that was searched for.
        """
        self.findRegexp(self.lastFindRegexp, self.lastFindFlags)

    def replaceOneRegexp(self, findRegexp, flags, replaceRegexp):
        """
        If the current selection matches the search regexp, a replacement
        is made. Otherwise, it calls findRegexp().
        """
        compiledRegexp = re.compile(findRegexp, flags)
        selectedText = self.bodyInput.GetSelectedText()
        match = re.match(findRegexp, selectedText, flags)

        if match and match.endpos == len(selectedText):
            oldStart = self.bodyInput.GetSelectionStart()
            newText = re.sub(compiledRegexp, replaceRegexp, selectedText)
            self.bodyInput.ReplaceSelection(newText)
            self.bodyInput.SetSelection(oldStart, oldStart + len(newText))
        else:
            # look for the next instance
            self.findRegexp(findRegexp, flags)

    def replaceAllRegexps(self, findRegexp, flags, replaceRegexp):
        """
        Replaces all instances of text in the body text and
        shows the user an alert about how many replacements
        were made.
        """
        replacements = 0
        compiledRegexp = re.compile(findRegexp, flags)

        newText, replacements = re.subn(compiledRegexp, replaceRegexp, self.bodyInput.GetText())
        if replacements > 0: self.bodyInput.SetText(newText)

        message = '%d replacement' % replacements
        if replacements != 1:
            message += 's were '
        else:
            message += ' was '
        message += 'made in this passage.'

        dialog = wx.MessageDialog(self, message, 'Replace Complete', wx.ICON_INFORMATION | wx.OK)
        dialog.ShowModal()

    def stripCrud(self, text):
        """Strips extraneous crud from around text, likely a partial selection of a link."""
        return text.strip(""" "'<>[]""")

    def setCodeLexer(self, css = False):
        """Basic CSS highlighting"""
        monoFont = wx.Font(self.app.config.ReadInt('monospaceFontSize'), wx.MODERN, wx.NORMAL, \
                           wx.NORMAL, False, self.app.config.Read('monospaceFontFace'))
        body = self.bodyInput
        body.StyleSetFont(wx.stc.STC_STYLE_DEFAULT, monoFont)
        body.StyleClearAll()
        if css:
            for i in range(1,17):
                body.StyleSetFont(i, monoFont)
            body.StyleSetForeground(wx.stc.STC_CSS_IMPORTANT, TweeStyler.MACRO_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_COMMENT, TweeStyler.COMMENT_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_ATTRIBUTE, TweeStyler.GOOD_LINK_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_CLASS, TweeStyler.MARKUP_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_ID, TweeStyler.MARKUP_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_TAG, TweeStyler.PARAM_BOOL_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_PSEUDOCLASS, TweeStyler.EXTERNAL_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_UNKNOWN_PSEUDOCLASS, TweeStyler.EXTERNAL_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_DIRECTIVE, TweeStyler.PARAM_VAR_COLOR)
            body.StyleSetForeground(wx.stc.STC_CSS_UNKNOWN_IDENTIFIER, TweeStyler.GOOD_LINK_COLOR)

            for i in [wx.stc.STC_CSS_CLASS, wx.stc.STC_CSS_ID, wx.stc.STC_CSS_TAG,
                      wx.stc.STC_CSS_PSEUDOCLASS, wx.stc.STC_CSS_OPERATOR, wx.stc.STC_CSS_IMPORTANT,
                      wx.stc.STC_CSS_UNKNOWN_PSEUDOCLASS, wx.stc.STC_CSS_DIRECTIVE]:
                body.StyleSetBold(i, True)

    def setLexer(self):
        """
        Sets our custom lexer for the body input so long as the passage
        is part of the story.
        """
        oldLexing = self.usingLexer

        if self.widget.passage.isStylesheet():
            if oldLexing != self.LEXER_CSS:
                self.setCodeLexer(css = True)
                self.usingLexer = self.LEXER_CSS
                self.bodyInput.SetLexer(wx.stc.STC_LEX_CSS)
        elif not self.widget.passage.isStoryText() and not self.widget.passage.isAnnotation():
            if oldLexing != self.LEXER_NONE:
                self.usingLexer = self.LEXER_NONE
                self.setCodeLexer()
                self.bodyInput.SetLexer(wx.stc.STC_LEX_NULL)
        elif oldLexing != self.LEXER_NORMAL:
            self.usingLexer = self.LEXER_NORMAL
            self.bodyInput.SetLexer(wx.stc.STC_LEX_CONTAINER)

        if oldLexing != self.usingLexer:
            if self.usingLexer == self.LEXER_NORMAL:
                self.lexer.initStyles()
            self.bodyInput.Colourise(0, len(self.bodyInput.GetText()))

    def updateUI(self, event):
        """Updates menus."""

        # basic edit menus

        undoItem = self.menus.FindItemById(wx.ID_UNDO)
        undoItem.Enable(self.bodyInput.CanUndo())

        redoItem = self.menus.FindItemById(wx.ID_REDO)
        redoItem.Enable(self.bodyInput.CanRedo())

        hasSelection = self.bodyInput.GetSelectedText() != ''

        cutItem = self.menus.FindItemById(wx.ID_CUT)
        cutItem.Enable(hasSelection)
        copyItem = self.menus.FindItemById(wx.ID_COPY)
        copyItem.Enable(hasSelection)

        pasteItem = self.menus.FindItemById(wx.ID_PASTE)
        pasteItem.Enable(self.bodyInput.CanPaste())

        # find/replace

        findNextItem = self.menus.FindItemById(PassageFrame.EDIT_FIND_NEXT)
        findNextItem.Enable(self.lastFindRegexp is not None)

        # link selected text menu item

        editSelected = self.menus.FindItemById(PassageFrame.PASSAGE_EDIT_SELECTION)
        selection = self.bodyInput.GetSelectedText()

        if selection != '':
            if not re.match(r'^\[\[.*\]\]$', selection):
                if len(selection) < 25:
                    editSelected.SetText('Create &Link "' + selection + '"\tCtrl-L')
                else:
                    editSelected.SetText('Create &Link From Selected Text\tCtrl-L')
            else:
                if len(selection) < 25:
                    editSelected.SetText('&Edit Passage "' + self.stripCrud(selection) + '"\tCtrl-L')
                else:
                    editSelected.SetText('&Edit Passage From Selected Text\tCtrl-L')
            editSelected.Enable(True)
        else:
            editSelected.SetText('Create &Link From Selected Text\tCtrl-L')
            editSelected.Enable(False)

    def updateSubmenus(self, event = None):
        """
        Updates our passage menus. This should be called sparingly, i.e. not during
        a UI update event, as it is doing a bunch of removing and adding of items.
        """

        # separate outgoing and broken links

        outgoing = []
        incoming = []
        broken = []

        # Remove externals

        for link in self.widget.passage.links:
            if len(link) > 0 and TweeLexer.linkStyle(link) == TweeLexer.BAD_LINK:
                if link in self.widget.parent.widgetDict:
                    outgoing.append(link)
                elif not self.widget.parent.includedPassageExists(link):
                    broken.append(link)

        # incoming links

        for widget in self.widget.parent.widgetDict.itervalues():
            if self.widget.passage.title in widget.passage.links \
            and len(widget.passage.title) > 0:
                incoming.append(widget.passage.title)

        # repopulate the menus

        def populate(menu, links):
            for item in menu.GetMenuItems():
                menu.DeleteItem(item)

            if len(links):
                for link in links:
                    item = menu.Append(-1, link)
                    self.Bind(wx.EVT_MENU, self.openOtherEditor, item)
            else:
                item = menu.Append(wx.ID_ANY, '(None)')
                item.Enable(False)

        outTitle = 'Outgoing Links'
        if len(outgoing) > 0: outTitle += ' (' + str(len(outgoing)) + ')'
        self.outLinksMenuTitle.SetText(outTitle)
        populate(self.outLinksMenu, outgoing)

        inTitle = 'Incoming Links'
        if len(incoming) > 0: inTitle += ' (' + str(len(incoming)) + ')'
        self.inLinksMenuTitle.SetText(inTitle)
        populate(self.inLinksMenu, incoming)

        brokenTitle = 'Broken Links'
        if len(broken) > 0: brokenTitle += ' (' + str(len(broken)) + ')'
        self.brokenLinksMenuTitle.SetText(brokenTitle)
        populate(self.brokenLinksMenu, broken)

    def applyPrefs(self):
        """Applies user prefs to this frame."""
        bodyFont = wx.Font(self.app.config.ReadInt('windowedFontSize'), wx.MODERN, wx.NORMAL,
                           wx.NORMAL, False, self.app.config.Read('windowedFontFace'))
        defaultStyle = self.bodyInput.GetStyleAt(0)
        self.bodyInput.StyleSetFont(defaultStyle, bodyFont)
        if hasattr(self, 'lexer'): self.lexer.initStyles()

    def __repr__(self):
        return "<PassageFrame '" + self.widget.passage.title + "'>"

    def getHeader(self):
        """Returns the current selected target header for this Passage Frame."""
        return self.widget.getHeader()

    # timing constants

    PARENT_SYNC_DELAY = 0.5

    # control constants

    DEFAULT_SIZE = (550, 600)
    TITLE_LABEL = 'Title'
    TAGS_LABEL = 'Tags (separate with spaces)'

    # menu constants (not defined by wx)

    EDIT_FIND_NEXT = 2001
    [PASSAGE_FULLSCREEN, PASSAGE_EDIT_SELECTION, PASSAGE_REBUILD_STORY, PASSAGE_TEST_HERE, PASSAGE_VERIFY] = range(1001,1006)
    [HELP1, HELP2, HELP3, HELP4, HELP5] = range(3001,3006)

    [LEXER_NONE, LEXER_NORMAL, LEXER_CSS] = range(0,3)


class StorySettingsFrame(PassageFrame):
    """A window which presents the current header's StorySettings."""

    def __init__(self, parent, widget, app):
        self.widget = widget
        self.app = app

        wx.Frame.__init__(self, parent, wx.ID_ANY, title = self.widget.passage.title + ' - ' + self.app.NAME + ' ' + versionString, \
                          size = (metrics.size('storySettingsWidth'), metrics.size('storySettingsHeight')), style=wx.DEFAULT_FRAME_STYLE)
        # menus

        self.menus = wx.MenuBar()
        self.SetMenuBar(self.menus)

        # controls

        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.panel.SetupScrolling()
        allSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(allSizer)

        # Read the storysettings definitions for this header
        self.storySettingsData = self.widget.parent.parent.header.storySettings()

        if not self.storySettingsData or type(self.storySettingsData) is str:
            label = self.storySettingsData or "The currently selected story format does not use StorySettings."
            allSizer.Add(wx.StaticText(self.panel, label = label),flag=wx.ALL|wx.EXPAND, border=metrics.size('windowBorder'))
            self.storySettingsData = {}

        self.ctrls = {}

        for data in self.storySettingsData:
            ctrlset = []
            name = ''
            if data["type"] == "checkbox":
                checkbox = wx.CheckBox(self.panel, label = data["label"])
                name = data["name"]
                # Read current value, and default it if it's not present
                currentValue = self.getSetting(name).lower()
                if not currentValue:
                    currentValue = data.get('default', 'off')
                    self.saveSetting(name, currentValue)
                checkbox.SetValue(currentValue not in ["off", "false", '0'])
                values = data.get("values", ("on","off")) # pylint: disable=unused-variable
                checkbox.Bind(wx.EVT_CHECKBOX, lambda e, checkbox=checkbox, name=name, values=values:
                              self.saveSetting(name, values[0] if checkbox.GetValue() else values[1] ))
                allSizer.Add(checkbox,flag=wx.ALL, border=metrics.size('windowBorder'))
                ctrlset.append(checkbox)

            elif data["type"] == "text":
                textlabel = wx.StaticText(self.panel, label = data["label"])
                textctrl = wx.TextCtrl(self.panel)
                name = data["name"]
                # Read current value
                currentValue = self.getSetting(name).lower()
                if not currentValue:
                    currentValue = data.get('default', '')
                    self.saveSetting(name, currentValue)
                textctrl.SetValue(currentValue or data.get("default",''))

                textctrl.Bind(wx.EVT_TEXT, lambda e, name=name, textctrl=textctrl:
                              self.saveSetting(name,textctrl.GetValue()))
                # Setup sizer for label/textctrl pair
                hSizer = wx.BoxSizer(wx.HORIZONTAL)
                hSizer.Add(textlabel,1,wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
                hSizer.Add(textctrl,1,wx.EXPAND)
                allSizer.Add(hSizer,flag=wx.ALL|wx.EXPAND, border=metrics.size('windowBorder'))
                ctrlset += [textlabel, textctrl]
            else:
                continue

            if "desc" in data:
                desc = wx.StaticText(self.panel, label = data["desc"])
                allSizer.Add(desc, 0, flag=wx.LEFT|wx.BOTTOM, border = metrics.size('windowBorder'))
                ctrlset.append(desc)

            self.ctrls[name] = ctrlset

        self.SetIcon(self.app.icon)
        self.SetTitle(self.title())
        self.Layout()
        self.enableCtrls()
        self.Show(True)

    def enableCtrls(self):
        # Check if each ctrl has a requirement or an incompatibility,
        # look it up, and enable/disable if so
        for data in self.storySettingsData:
            name = data["name"]
            if name in self.ctrls:
                if 'requires' in data:
                    set = self.getSetting(data['requires'])
                    for i in self.ctrls[name]:
                        i.Enable(set not in ["off", "false", '0'])

    def getSetting(self, valueName):
        search = re.search(r"(?:^|\n)"+valueName + r"\s*:\s*(\w*)\s*(?:\n|$)", self.widget.passage.text, flags=re.I)
        if search:
            return search.group(1)
        return ''

    def saveSetting(self, valueName, value):
        newEntry = valueName+":"+str(value)+'\n'
        sub = re.subn("^"+valueName+r"\s*:\s*[^\n]+\n", newEntry, self.widget.passage.text, flags=re.I|re.M)
        if sub[1]:
            self.widget.passage.text = sub[0]
        else:
            self.widget.passage.text += newEntry
        self.widget.parent.parent.setDirty(True)
        self.widget.clearPaintCache()
        self.widget.passage.update()
        self.enableCtrls()


class ImageFrame(PassageFrame):
    """
    A window which only displays passages whose text consists of base64 encoded images -
    the image is converted to a bitmap and displayed, if possible.
    """

    def __init__(self, parent, widget, app):
        self.widget = widget
        self.app = app
        self.syncTimer = None
        self.image = None
        self.gif = None

        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Untitled Passage - ' + self.app.NAME + ' ' + versionString, \
                          size = PassageFrame.DEFAULT_SIZE, style=wx.DEFAULT_FRAME_STYLE)

        # controls

        self.panel = wx.Panel(self)
        allSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(allSizer)

        # title control

        self.topControls = wx.Panel(self.panel)
        topSizer = wx.FlexGridSizer(3, 2, metrics.size('relatedControls'), metrics.size('relatedControls'))

        titleLabel = wx.StaticText(self.topControls, style = wx.ALIGN_RIGHT, label = PassageFrame.TITLE_LABEL)
        self.titleInput = wx.TextCtrl(self.topControls)
        self.titleInput.SetValue(self.widget.passage.title)
        self.SetTitle(self.title())

        topSizer.Add(titleLabel, 0, flag = wx.ALL, border = metrics.size('focusRing'))
        topSizer.Add(self.titleInput, 1, flag = wx.EXPAND | wx.ALL, border = metrics.size('focusRing'))
        topSizer.AddGrowableCol(1, 1)
        self.topControls.SetSizer(topSizer)

        # image pane

        self.imageScroller = wx.ScrolledWindow(self.panel)
        self.imageSizer = wx.GridSizer(1,1)
        self.imageScroller.SetSizer(self.imageSizer)

        # image menu

        passageMenu = wx.Menu()

        passageMenu.Append(self.IMPORT_IMAGE, '&Replace Image...\tCtrl-O')
        self.Bind(wx.EVT_MENU, self.replaceImage, id = self.IMPORT_IMAGE)

        passageMenu.Append(self.SAVE_IMAGE, '&Save Image...')
        self.Bind(wx.EVT_MENU, self.saveImage, id = self.SAVE_IMAGE)

        passageMenu.AppendSeparator()

        passageMenu.Append(wx.ID_SAVE, '&Save Story\tCtrl-S')
        self.Bind(wx.EVT_MENU, self.widget.parent.parent.save, id = wx.ID_SAVE)

        passageMenu.Append(PassageFrame.PASSAGE_REBUILD_STORY, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.widget.parent.parent.rebuild, id = PassageFrame.PASSAGE_REBUILD_STORY)

        passageMenu.AppendSeparator()

        passageMenu.Append(wx.ID_CLOSE, '&Close Image\tCtrl-W')
        self.Bind(wx.EVT_MENU, lambda e: self.Destroy(), id = wx.ID_CLOSE)

        # edit menu

        editMenu = wx.Menu()

        editMenu.Append(wx.ID_COPY, '&Copy\tCtrl-C')
        self.Bind(wx.EVT_MENU, self.copyImage, id = wx.ID_COPY)

        editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl-V')
        self.Bind(wx.EVT_MENU, self.pasteImage, id = wx.ID_PASTE)

        # menu bar

        self.menus = wx.MenuBar()
        self.menus.Append(passageMenu, '&Image')
        self.menus.Append(editMenu, '&Edit')
        self.SetMenuBar(self.menus)

        # finish

        allSizer.Add(self.topControls, flag = wx.TOP | wx.LEFT | wx.RIGHT | wx.EXPAND, border = metrics.size('windowBorder'))
        allSizer.Add(self.imageScroller, proportion = 1, flag = wx.TOP | wx.EXPAND, border = metrics.size('relatedControls'))

        # bindings
        self.titleInput.Bind(wx.EVT_TEXT, self.syncPassage)

        self.SetIcon(self.app.icon)
        self.updateImage()
        self.Show(True)

    def syncPassage(self, event = None):
        """Updates the image based on the title input; asks our matching widget to repaint."""
        if len(self.titleInput.GetValue()) > 0:
            self.widget.passage.title = self.titleInput.GetValue()
        else:
            self.widget.passage.title = 'Untitled Image'
        self.widget.clearPaintCache()

        self.SetTitle(self.title())

        # immediately mark the story dirty

        self.widget.parent.parent.setDirty(True)

        # reset redraw timer

        def reallySync(self):
            self.widget.parent.Refresh()

        if self.syncTimer:
            self.syncTimer.cancel()

        self.syncTimer = threading.Timer(PassageFrame.PARENT_SYNC_DELAY, reallySync, [self], {})
        self.syncTimer.start()


    def updateImage(self):
        """Assigns a bitmap to this frame's StaticBitmap component,
        unless it's a GIF, in which case, animate it."""
        if self.gif:
            self.gif.Stop()
        self.imageSizer.Clear(True)
        self.gif = None
        self.image = None
        size = (32,32)

        t = self.widget.passage.text
        # Get the bitmap (will be used as inactive for GIFs)
        bmp = self.widget.bitmap
        if bmp:
            size = bmp.GetSize()

            # GIF animation
            if t.startswith("data:image/gif"):

                self.gif = wx.animate.AnimationCtrl(self.imageScroller, size = size)
                self.imageSizer.Add(self.gif, 1, wx.ALIGN_CENTER)

                # Convert the full GIF to an Animation
                anim = wx.animate.Animation()
                data = base64.b64decode(t[t.index("base64,")+7:])
                anim.Load(cStringIO.StringIO(data))

                # Load the Animation into the AnimationCtrl

                # Crashes OS X..
                #self.gif.SetInactiveBitmap(bmp)
                self.gif.SetAnimation(anim)
                self.gif.Play()

            # Static images
            else:
                self.image = wx.StaticBitmap(self.imageScroller, style = wx.TE_PROCESS_TAB | wx.BORDER_SUNKEN)
                self.imageSizer.Add(self.image, 1, wx.ALIGN_CENTER)
                self.image.SetBitmap(bmp)

        self.SetSize((min(max(size[0], 320),1024),min(max(size[1], 240),768)+64))
        self.imageScroller.SetScrollRate(2,2)
        self.widget.clearPaintCache()
        self.Refresh()

        # Update copy menu
        copyItem = self.menus.FindItemById(wx.ID_COPY)
        copyItem.Enable(not not bmp)

    def replaceImage(self, event = None):
        """Replace the image with a new file, if possible."""
        self.widget.parent.parent.importImageDialog(replace = self.widget)
        self.widget.parent.parent.setDirty(True)
        self.updateImage()

    def saveImage(self, event = None):
        """Saves the base64 image as a file."""
        t = self.widget.passage.text
        # Get the extension
        extension = images.getImageType(t)
        dialog = wx.FileDialog(self, 'Save Image', os.getcwd(), self.widget.passage.title + extension, \
                               'Image File|*' + extension + '|All Files (*.*)|*.*', wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)

        if dialog.ShowModal() == wx.ID_OK:
            try:
                path = dialog.GetPath()

                dest = open(path, 'wb')

                data = base64.b64decode(images.removeURIPrefix(t))
                dest.write(data)

                dest.close()
            except:
                self.app.displayError('saving the image')

        dialog.Destroy()

    def copyImage(self, event = None):
        """Copy the bitmap to the clipboard"""
        clip = wx.TheClipboard
        if self.image and clip.Open():
            clip.SetData(wx.BitmapDataObject(self.image.GetBitmap() if not self.gif else self.gif.GetInactiveBitmap()))
            clip.Flush()
            clip.Close()

    def pasteImage(self, event = None):
        """Paste from the clipboard, converting to a PNG"""
        clip = wx.TheClipboard
        bdo = wx.BitmapDataObject()
        pasted = False

        # Try and read from the clipboard
        if clip.Open():
            pasted = clip.GetData(bdo)
            clip.Close()
        if not pasted:
            return

        # Convert bitmap to PNG
        bmp = bdo.GetBitmap()
        self.widget.passage.text = images.bitmapToBase64PNG(bmp)
        self.widget.updateBitmap()
        self.updateImage()

    IMPORT_IMAGE = 1004
    EXPORT_IMAGE = 1005
    SAVE_IMAGE = 1006

