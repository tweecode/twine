#!/usr/bin/env python

#
# PassageFrame
# A PassageFrame is a window that allows the user to change the contents
# of a passage. This must be paired with a PassageWidget; it gets to the
# underlying passage via it, and also notifies it of changes made here.
#
# This doesn't require the user to save his changes -- as he makes changes,
# they are automatically updated everywhere.
#

import os, re, wx, wx.stc
from fseditframe import FullscreenEditFrame

class PassageFrame (wx.Frame):
    
    def __init__ (self, parent, widget, app):
        self.widget = widget
        self.app = app
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = 'Untitled Passage - ' + self.app.NAME, \
                          size = PassageFrame.DEFAULT_SIZE)
        self.syncTimer = None
        self.Bind(wx.EVT_TIMER, self.syncParent)
        
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
        
        passageMenu.Append(PassageFrame.PASSAGE_REBUILD_STORY, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.widget.parent.parent.rebuild, id = PassageFrame.PASSAGE_REBUILD_STORY)

        passageMenu.AppendSeparator()

        passageMenu.Append(PassageFrame.PASSAGE_FULLSCREEN, '&Fullscreen View\tF12')
        self.Bind(wx.EVT_MENU, self.openFullscreen, id = PassageFrame.PASSAGE_FULLSCREEN)

        passageMenu.Append(wx.ID_CLOSE, '&Close Passage\tCtrl-W')
        self.Bind(wx.EVT_MENU, lambda e: self.Destroy(), id = wx.ID_CLOSE)        
        
        # Edit menu
        
        editMenu = wx.Menu()
        
        editMenu.Append(wx.ID_UNDO, '&Undo\tCtrl-Z')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Undo(), id = wx.ID_UNDO)

        editMenu.Append(wx.ID_REDO, '&Redo\tCtrl-Y')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Redo(), id = wx.ID_REDO)
        
        editMenu.AppendSeparator()
        
        editMenu.Append(wx.ID_CUT, 'Cu&t\tCtrl-X')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Cut(), id = wx.ID_CUT)

        editMenu.Append(wx.ID_COPY, '&Copy\tCtrl-C')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Copy(), id = wx.ID_COPY)
        
        editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl-V')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Paste(), id = wx.ID_PASTE)

        editMenu.Append(wx.ID_SELECTALL, 'Select &All\tCtrl-A')
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.SelectAll(), id = wx.ID_SELECTALL)

        # menus
        
        self.menus = wx.MenuBar()
        self.menus.Append(passageMenu, '&Passage')
        self.menus.Append(editMenu, '&Edit')
        self.SetMenuBar(self.menus)

        # controls
        
        self.panel = wx.Panel(self)
        allSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(allSizer)
        
        # title/tag controls
        
        self.topControls = wx.Panel(self.panel)
        topSizer = wx.FlexGridSizer(3, 2, PassageFrame.SPACING, PassageFrame.SPACING)
        
        titleLabel = wx.StaticText(self.topControls, style = wx.ALIGN_RIGHT, label = PassageFrame.TITLE_LABEL)
        self.titleInput = wx.TextCtrl(self.topControls)
        tagsLabel = wx.StaticText(self.topControls, style = wx.ALIGN_RIGHT, label = PassageFrame.TAGS_LABEL)
        self.tagsInput = wx.TextCtrl(self.topControls)
        topSizer.Add(titleLabel)
        topSizer.Add(self.titleInput, 1, flag = wx.EXPAND | wx.ALL)
        topSizer.Add(tagsLabel)
        topSizer.Add(self.tagsInput, 1, flag = wx.EXPAND | wx.ALL)
        topSizer.AddGrowableCol(1, 1)
        self.topControls.SetSizer(topSizer)
        
        # body text
        
        self.bodyInput = wx.stc.StyledTextCtrl(self.panel, style = wx.TE_MULTILINE | wx.TE_PROCESS_TAB)
        self.bodyInput.SetMargins(4, 4)
        self.bodyInput.SetMarginWidth(1, 0)
        self.bodyInput.SetWrapMode(wx.stc.STC_WRAP_WORD)
        self.bodyInput.SetSelBackground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT))
        self.bodyInput.SetSelForeground(True, wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT))
                
        # final layout
        
        allSizer.Add(self.topControls, flag = wx.ALL | wx.EXPAND, border = PassageFrame.SPACING)
        allSizer.Add(self.bodyInput, proportion = 1, flag = wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, \
                     border = PassageFrame.SPACING)
        self.applyPrefs()
        self.syncInputs()
        self.bodyInput.EmptyUndoBuffer()
        self.updateSubmenus()
        
        # event bindings
        # we need to do this AFTER setting up initial values
        
        self.titleInput.Bind(wx.EVT_TEXT, self.syncPassage)
        self.tagsInput.Bind(wx.EVT_TEXT, self.syncPassage)
        self.bodyInput.Bind(wx.stc.EVT_STC_CHANGE, self.syncPassage)
        self.bodyInput.Bind(wx.stc.EVT_STC_START_DRAG, self.prepDrag)
        self.Bind(wx.EVT_CLOSE, self.closeFullscreen)
        self.Bind(wx.EVT_MENU_OPEN, self.updateSubmenus)
        self.Bind(wx.EVT_UPDATE_UI, self.updateUI)
        
        if not re.match('Untitled Passage \d+', self.widget.passage.title):
            self.bodyInput.SetFocus()
            self.bodyInput.SetSelection(-1, -1)

        self.SetIcon(self.app.icon)
        self.Show(True)

    def syncInputs (self):
        """Updates the inputs based on the passage's state."""
        self.titleInput.SetValue(self.widget.passage.title)
        self.bodyInput.SetText(self.widget.passage.text)
    
        tags = ''
        
        for tag in self.widget.passage.tags:
            tags += tag + ' '
            
        self.tagsInput.SetValue(tags)
        self.SetTitle(self.widget.passage.title + ' - ' + self.app.NAME)
    
    def syncPassage (self, event = None):
        """Updates the passage based on the inputs; asks our matching widget to repaint."""
        self.widget.passage.title = self.titleInput.GetValue()
        self.widget.passage.text = self.bodyInput.GetText()
        self.widget.passage.tags = []
        
        for tag in self.tagsInput.GetValue().split(' '):
            if tag != '': self.widget.passage.tags.append(tag)
        
        self.SetTitle(self.widget.passage.title + ' - ' + self.app.NAME)
        
        # reset sync timer

        if (self.syncTimer): self.syncTimer.Stop()
        self.syncTimer = wx.Timer(self)        
        self.syncTimer.Start(PassageFrame.PARENT_SYNC_DELAY, wx.TIMER_ONE_SHOT)
        
    def syncParent (self, event = None):
        """Sends a repaint message to our parent StoryFrame."""
        self.widget.parent.Refresh()
        self.widget.parent.parent.setDirty(True)
        self.syncTimer = None
    
    def openFullscreen (self, event = None):
        """Opens a FullscreenEditFrame for this passage's body text."""
        self.Hide()
        self.fullscreen = FullscreenEditFrame(None, self.app, \
                                              title = self.widget.passage.title + ' - ' + self.app.NAME, \
                                              initialText = self.widget.passage.text, \
                                              callback = self.setBodyText, frame = self)
    
    def closeFullscreen (self, event = None):
        """Closes this editor's fullscreen counterpart, if any."""
        try: self.fullscreen.Destroy()
        except: pass
        event.Skip()
        
    def openOtherEditor (self, event = None, title = None):
        """
        Opens another passage for editing. If it does not exist, then
        it creates it next to this one and then opens it. You may pass
        this a string title OR an event. If you pass an event, it presumes
        it is a wx.CommandEvent, and uses the exact text of the menu as the title.
        """

        # this is a bit retarded
        # we seem to be receiving CommandEvents, not MenuEvents,
        # so we can only see menu item IDs
        # unfortunately all our menu items are dynamically generated
        # so we gotta work our way back to a menu name
        
        if not title: title = self.menus.FindItemById(event.GetId()).GetLabel()
        found = False

        # check if the passage already exists
        
        for widget in self.widget.parent.widgets:
            if widget.passage.title == title:
                found = True
                editingWidget = widget
                break
        
        if not found:
            editingWidget = self.widget.parent.newWidget(title = title, pos = self.widget.pos)
       
        editingWidget.openEditor()
       
    def setBodyText (self, text):
        """Changes the body text field directly."""
        self.bodyInput.SetText(text)
        self.Show(True)
        
    def prepDrag (self, event):
        """
        Tells our StoryPanel about us so that it can tell us what to do in response to
        dropping some text into it. We also force the event into a copy operation, not
        a move one, so it doesn't trash any existing text.
        """
        event.SetDragAllowMove(False)
        self.widget.parent.textDragSource = self
        
    def editSelection (self, event = None):
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
    
    def linkSelection (self):
        """Transforms the selection into a link by surrounding it with double brackets."""
        selStart = self.bodyInput.GetSelectionStart()
        selEnd = self.bodyInput.GetSelectionEnd()
        self.bodyInput.InsertText(selStart, '[[')
        self.bodyInput.InsertText(selEnd + 2, ']]')
        self.bodyInput.SetSelection(selStart, selEnd + 4)
    
    def stripCrud (self, text):
        """Strips extraneous crud from around text, likely a partial selection of a link."""
        return text.strip(""" "'<>[]""")
    
    def updateUI (self, event):
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
        
        # link selected text menu item
        
        editSelected = self.menus.FindItemById(PassageFrame.PASSAGE_EDIT_SELECTION)
        selection = self.bodyInput.GetSelectedText()
        
        if selection != '':
            if not re.match(r'^\[\[.*\]\]$', selection):
                if len(selection) < 25:
                    editSelected.SetText('Create &Link Named "' + selection + '"\tCtrl-L')
                else:
                    editSelected.SetText('Create &Link From Selected Text\tCtrl-L')
            else:
                if len(selection) < 25:
                    editSelected.SetText('&Edit Passage Named "' + self.stripCrud(selection) + '"\tCtrl-L')
                else:
                    editSelected.SetText('&Edit Passage From Selected Text\tCtrl-L')
            editSelected.Enable(True)
        else:
            editSelected.SetText('Create &Link From Selected Text\tCtrl-L')
            editSelected.Enable(False)

    def updateSubmenus (self, event = None):
        """
        Updates our passage menus. This should be called sparingly, i.e. not during
        a UI update event, as it is doing a bunch of removing and adding of items.
        """
                
        # separate outgoing and broken links
        
        outgoing = []
        incoming = []
        broken = []
        
        for link in self.widget.passage.links():
            found = False
            
            for widget in self.widget.parent.widgets:
                if widget.passage.title == link:
                    outgoing.append(link)
                    found = True
                    break
                
            if not found: broken.append(link)

        # incoming links

        for widget in self.widget.parent.widgets:
            if self.widget.passage.title in widget.passage.links():
                incoming.append(widget.passage.title)
                
        # repopulate the menus

        def populate (menu, links):
            for item in menu.GetMenuItems():
                menu.DeleteItem(item)
            
            if len(links):   
                for link in links:
                    item = menu.Append(wx.ID_ANY, link)
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
        
    def applyPrefs (self):
        """Applies user prefs to this frame."""
        bodyFont = wx.Font(self.app.config.ReadInt('windowedFontSize'), wx.MODERN, wx.NORMAL, \
                           wx.NORMAL, False, self.app.config.Read('windowedFontFace'))
        defaultStyle = self.bodyInput.GetStyleAt(0)
        self.bodyInput.StyleSetFont(defaultStyle, bodyFont)
    
    def __repr__ (self):
        return "<PassageFrame '" + self.passage.title + "'>"
    
    # timing constants
    
    PARENT_SYNC_DELAY = 500
    
    # control constants
    
    DEFAULT_SIZE = (550, 600)
    SPACING = 6
    TITLE_LABEL = 'Title'
    TAGS_LABEL = 'Tags (separate with spaces)'
        
    # menu constants (not defined by wx)
    
    PASSAGE_FULLSCREEN = 1001
    PASSAGE_EDIT_SELECTION = 1002
    PASSAGE_REBUILD_STORY = 1003