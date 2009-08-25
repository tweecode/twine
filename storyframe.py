#!/usr/bin/env python

# 
# StoryFrame
# A StoryFrame displays an entire story. Its main feature is an
# instance of a StoryPanel, but it also has a menu bar and toolbar.
#

import wx, os, urllib, pickle
from tiddlywiki import TiddlyWiki
from storypanel import StoryPanel
from statisticsdialog import StatisticsDialog
from storyfindframe import StoryFindFrame
from storyreplaceframe import StoryReplaceFrame

class StoryFrame (wx.Frame):
    
    def __init__(self, parent, app, state = None):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = StoryFrame.DEFAULT_TITLE, \
                          size = StoryFrame.DEFAULT_SIZE)     
        self.app = app
        self.parent = parent
        self.pristine = True    # the user has not added any content to this at all
        self.dirty = False      # the user has not made unsaved changes

        # inner state
        
        if (state):
            self.buildDestination = state['buildDestination']
            self.saveDestination = state['saveDestination']
            self.target = state['target']
            self.storyPanel = StoryPanel(self, app, state = state['storyPanel'])
            self.pristine = False
        else:
            self.buildDestination = ''
            self.saveDestination = ''
            self.target = 'sugarcane'
            self.storyPanel = StoryPanel(self, app)
        
        # window events
        
        self.Bind(wx.EVT_CLOSE, self.checkClose)
        self.Bind(wx.EVT_UPDATE_UI, self.updateUI)
        
        # File menu
        
        fileMenu = wx.Menu()
        
        fileMenu.Append(wx.ID_NEW, '&New Story\tCtrl-Shift-N')
        self.Bind(wx.EVT_MENU, self.app.newStory, id = wx.ID_NEW)
        
        fileMenu.Append(wx.ID_OPEN, '&Open Story...\tCtrl-O')
        self.Bind(wx.EVT_MENU, self.app.openDialog, id = wx.ID_OPEN)
        
        recentFilesMenu = wx.Menu()
        self.app.recentFiles.UseMenu(recentFilesMenu)
        self.app.recentFiles.AddFilesToThisMenu(recentFilesMenu)
        fileMenu.AppendMenu(wx.ID_ANY, 'Open &Recent', recentFilesMenu)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(0), id = wx.ID_FILE1)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(1), id = wx.ID_FILE2)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(2), id = wx.ID_FILE3)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(3), id = wx.ID_FILE4)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(4), id = wx.ID_FILE5)
        
        fileMenu.AppendSeparator()
        
        fileMenu.Append(wx.ID_SAVE, '&Save Story\tCtrl-S')
        self.Bind(wx.EVT_MENU, self.save, id = wx.ID_SAVE)
        
        fileMenu.Append(wx.ID_SAVEAS, 'S&ave Story As...\tCtrl-Shift-S')
        self.Bind(wx.EVT_MENU, self.saveAs, id = wx.ID_SAVEAS)

        fileMenu.Append(wx.ID_REVERT_TO_SAVED, '&Revert to Saved')
        self.Bind(wx.EVT_MENU, self.revert, id = wx.ID_REVERT_TO_SAVED)
        
        fileMenu.AppendSeparator()

        fileMenu.Append(StoryFrame.FILE_EXPORT_PROOF, 'Export &Proofing Copy...')
        self.Bind(wx.EVT_MENU, self.proof, id = StoryFrame.FILE_EXPORT_PROOF) 

        fileMenu.Append(StoryFrame.FILE_IMPORT_SOURCE, '&Import Source Code...')
        self.Bind(wx.EVT_MENU, self.importSource, id = StoryFrame.FILE_IMPORT_SOURCE) 

        fileMenu.Append(StoryFrame.FILE_EXPORT_SOURCE, 'Export Source &Code...')
        self.Bind(wx.EVT_MENU, self.exportSource, id = StoryFrame.FILE_EXPORT_SOURCE)

        fileMenu.AppendSeparator()
        
        fileMenu.Append(wx.ID_CLOSE, '&Close Story\tCtrl-W')
        self.Bind(wx.EVT_MENU, lambda e: self.Close(), id = wx.ID_CLOSE)
        
        fileMenu.Append(wx.ID_EXIT, 'E&xit Twine\tCtrl-Q')
        self.Bind(wx.EVT_MENU, lambda e: self.app.exit(), id = wx.ID_EXIT)
        
        # Edit menu
        
        editMenu = wx.Menu()
        
        editMenu.Append(wx.ID_UNDO, '&Undo\tCtrl-Z')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.undo(), id = wx.ID_UNDO)
        
        editMenu.Append(wx.ID_REDO, '&Redo\tCtrl-Y')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.redo(), id = wx.ID_REDO)

        editMenu.AppendSeparator()
        
        editMenu.Append(wx.ID_CUT, 'Cu&t\tCtrl-X')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.cutWidgets(), id = wx.ID_CUT)
        
        editMenu.Append(wx.ID_COPY, '&Copy\tCtrl-C')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.copyWidgets(), id = wx.ID_COPY)
        
        editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl-V')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.pasteWidgets(), id = wx.ID_PASTE)
        
        editMenu.Append(wx.ID_DELETE, '&Delete\tDel')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.removeWidgets(e, saveUndo = True), id = wx.ID_DELETE)

        editMenu.Append(wx.ID_SELECTALL, 'Select &All\tCtrl-A')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachWidget(lambda i: i.setSelected(True, exclusive = False)), id = wx.ID_SELECTALL)
        
        editMenu.AppendSeparator()
        
        editMenu.Append(wx.ID_FIND, 'Find...\tCtrl-F')
        self.Bind(wx.EVT_MENU, self.showFind, id = wx.ID_FIND)

        editMenu.Append(StoryFrame.EDIT_FIND_NEXT, 'Find Next\tCtrl-G')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.findWidgetRegexp(), id = StoryFrame.EDIT_FIND_NEXT)
        
        editMenu.Append(wx.ID_REPLACE, 'Replace Across Entire Story...\tCtrl-H')
        self.Bind(wx.EVT_MENU, self.showReplace, id = wx.ID_REPLACE)

        editMenu.AppendSeparator()
        
        editMenu.Append(wx.ID_PREFERENCES, 'Preferences...\tCtrl-,')
        self.Bind(wx.EVT_MENU, self.app.showPrefs, id = wx.ID_PREFERENCES)
        
        # View menu
 
        viewMenu = wx.Menu()
        
        viewMenu.Append(wx.ID_ZOOM_IN, 'Zoom &In\t=')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom('in'), id = wx.ID_ZOOM_IN)
        
        viewMenu.Append(wx.ID_ZOOM_OUT, 'Zoom &Out\t-')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom('out'), id = wx.ID_ZOOM_OUT)
        
        viewMenu.Append(wx.ID_ZOOM_FIT, 'Zoom to &Fit\t0')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom('fit'), id = wx.ID_ZOOM_FIT)

        viewMenu.Append(wx.ID_ZOOM_100, 'Zoom &100%\t1')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom(1), id = wx.ID_ZOOM_100)
        
        viewMenu.AppendSeparator()

        viewMenu.Append(StoryFrame.VIEW_SNAP, 'Snap to &Grid', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.toggleSnapping(), id = StoryFrame.VIEW_SNAP)

        viewMenu.Append(StoryFrame.VIEW_CLEANUP, '&Clean Up Passages')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.cleanup(), id = StoryFrame.VIEW_CLEANUP)
        
        viewMenu.AppendSeparator()
        
        viewMenu.Append(StoryFrame.VIEW_TOOLBAR, '&Toolbar', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleToolbar, id = StoryFrame.VIEW_TOOLBAR)

        # Story menu

        storyMenu = wx.Menu()
        
        storyMenu.Append(StoryFrame.STORY_NEW_PASSAGE, '&New Passage\tCtrl-N')
        self.Bind(wx.EVT_MENU, self.storyPanel.newWidget, id = StoryFrame.STORY_NEW_PASSAGE)
        
        storyMenu.Append(wx.ID_EDIT, '&Edit Passage\tCtrl-E')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e)), id = wx.ID_EDIT)

        storyMenu.Append(StoryFrame.STORY_EDIT_FULLSCREEN, '&Edit Passage Text Fullscreen\tF12')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e, fullscreen = True)), \
                  id = StoryFrame.STORY_EDIT_FULLSCREEN)
        
        storyMenu.Append(wx.ID_DELETE, '&Delete Passage')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.removeWidgets(e, saveUndo = True), id = wx.ID_DELETE)
 
        storyMenu.AppendSeparator()
        
        storyMenu.Append(StoryFrame.STORY_BUILD, '&Build Story...\tCtrl-B')
        self.Bind(wx.EVT_MENU, self.build, id = StoryFrame.STORY_BUILD)        
        
        storyMenu.Append(StoryFrame.STORY_REBUILD, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.rebuild, id = StoryFrame.STORY_REBUILD) 

        storyMenu.Append(StoryFrame.STORY_VIEW_LAST, '&View Last Build\tCtrl-L')
        self.Bind(wx.EVT_MENU, self.viewBuild, id = StoryFrame.STORY_VIEW_LAST)

        storyMenu.AppendSeparator()

        storyMenu.Append(StoryFrame.STORY_STATS, 'Story &Statistics\tCtrl-I')
        self.Bind(wx.EVT_MENU, self.stats, id = StoryFrame.STORY_STATS) 

        # Story Format submenu
        
        storyFormatMenu = wx.Menu()
        
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_SUGARCANE, '&Sugarcane', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, lambda e: self.setTarget('sugarcane'), id = StoryFrame.STORY_FORMAT_SUGARCANE) 
        
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_JONAH, '&Jonah', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, lambda e: self.setTarget('jonah'), id = StoryFrame.STORY_FORMAT_JONAH) 
        
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_TW2, 'TiddlyWiki &2', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, lambda e: self.setTarget('tw2'), id = StoryFrame.STORY_FORMAT_TW2) 
        
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_TW1, 'TiddlyWiki &1', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, lambda e: self.setTarget('tw'), id = StoryFrame.STORY_FORMAT_TW1) 
        
        storyFormatMenu.AppendSeparator()
        
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_HELP, '&About Story Formats')        
        self.Bind(wx.EVT_MENU, lambda e: self.app.storyFormatHelp(), id = StoryFrame.STORY_FORMAT_HELP)
        
        storyMenu.AppendMenu(wx.ID_ANY, 'Story &Format', storyFormatMenu)
        
        # Help menu
        
        helpMenu = wx.Menu()
 
        helpMenu.Append(StoryFrame.HELP_MANUAL, 'Online &Help')
        self.Bind(wx.EVT_MENU, self.app.openDocs, id = StoryFrame.HELP_MANUAL)

        helpMenu.Append(StoryFrame.HELP_GROUP, '&Discuss Twine Online')
        self.Bind(wx.EVT_MENU, self.app.openGroup, id = StoryFrame.HELP_GROUP)

        helpMenu.Append(StoryFrame.HELP_BUG, 'Report a &Bug')
        self.Bind(wx.EVT_MENU, self.app.reportBug, id = StoryFrame.HELP_BUG)
        
        helpMenu.AppendSeparator()
        
        helpMenu.Append(wx.ID_ABOUT, '&About Twine')
        self.Bind(wx.EVT_MENU, self.app.about, id = wx.ID_ABOUT)
        
        # add menus
        
        self.menus = wx.MenuBar()
        self.menus.Append(fileMenu, '&File')
        self.menus.Append(editMenu, '&Edit')
        self.menus.Append(viewMenu, '&View')
        self.menus.Append(storyMenu, '&Story')
        self.menus.Append(helpMenu, '&Help')
        self.SetMenuBar(self.menus)

        # add toolbar

        iconPath = self.app.getPath() + os.sep + 'icons' + os.sep
        
        self.toolbar = self.CreateToolBar(style = wx.TB_FLAT | wx.TB_NODIVIDER)
        self.toolbar.SetToolBitmapSize((StoryFrame.TOOLBAR_ICON_SIZE, StoryFrame.TOOLBAR_ICON_SIZE))
        
        self.toolbar.AddLabelTool(StoryFrame.STORY_NEW_PASSAGE, 'New Passage', \
                                  wx.Bitmap(iconPath + 'newpassage.png'), \
                                  shortHelp = StoryFrame.NEW_PASSAGE_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.newWidget(), id = StoryFrame.STORY_NEW_PASSAGE)
        
        self.toolbar.AddSeparator()
        
        self.toolbar.AddLabelTool(wx.ID_ZOOM_IN, 'Zoom In', \
                                  wx.Bitmap(iconPath + 'zoomin.png'), \
                                  shortHelp = StoryFrame.ZOOM_IN_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom('in'), id = wx.ID_ZOOM_IN)
        
        self.toolbar.AddLabelTool(wx.ID_ZOOM_OUT, 'Zoom Out', \
                                  wx.Bitmap(iconPath + 'zoomout.png'), \
                                  shortHelp = StoryFrame.ZOOM_OUT_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom('out'), id = wx.ID_ZOOM_OUT)  
          
        self.toolbar.AddLabelTool(wx.ID_ZOOM_FIT, 'Zoom to Fit', \
                                  wx.Bitmap(iconPath + 'zoomfit.png'), \
                                  shortHelp = StoryFrame.ZOOM_FIT_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom('fit'), id = wx.ID_ZOOM_FIT)
        
        self.toolbar.AddLabelTool(wx.ID_ZOOM_100, 'Zoom to 100%', \
                                  wx.Bitmap(iconPath + 'zoom1.png'), \
                                  shortHelp = StoryFrame.ZOOM_ONE_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom(1.0), id = wx.ID_ZOOM_100)

        self.SetIcon(self.app.icon)
        self.showToolbar = True
        self.toolbar.Realize()
        self.Show(True)
        
    def revert (self, event = None):
        """Reverts to the last saved version of the story file."""
        bits = os.path.splitext(self.saveDestination)
        title = os.path.basename(bits[0])
        message = 'Revert to the last version of ' + title + ' you saved?'
        dialog = wx.MessageDialog(self, message, 'Revert to Saved', wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
        
        if (dialog.ShowModal() == wx.ID_YES):
            self.Destroy()
            self.open(self.saveDestination)
    
    def checkClose (self, event):
        """
        If this instance's dirty flag is set, asks the user to confirm that they don't want to save changes.
        """
                
        if (self.dirty):
            bits = os.path.splitext(self.saveDestination)
            title = os.path.basename(bits[0])

            message = 'Close ' + title + ' without saving changes?'
            dialog = wx.MessageDialog(self, message, 'Save Changes', \
                                      wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
            if (dialog.ShowModal() == wx.ID_NO):
                event.Veto()
                return
        
        # ask all our widgets to close any editor windows
        
        map(lambda w: w.closeEditor(), self.storyPanel.widgets)
        self.app.removeStory(self)
        event.Skip()
        
    def saveAs (self, event = None):
        """Asks the user to choose a file to save state to, then passes off control to save()."""
        dialog = wx.FileDialog(self, 'Save Story As', os.getcwd(), "", \
                         "Twine Story (*.tws)|*.tws", \
                           wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
    
        if dialog.ShowModal() == wx.ID_OK:
            self.saveDestination = dialog.GetPath()
            self.app.config.Write('savePath', os.getcwd())
            self.app.addRecentFile(self.saveDestination)
            self.save(None)
        
        dialog.Destroy()
        
    def exportSource (self, event = None):
        """Asks the user to choose a file to export source to, then exports the wiki."""
        dialog = wx.FileDialog(self, 'Export Source Code', os.getcwd(), "", \
                               "Text File (*.txt)|*.txt", wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            try:
                path = dialog.GetPath()
                tw = TiddlyWiki()
                
                for widget in self.storyPanel.widgets: tw.addTiddler(widget.passage)
                dest = open(path, 'w')            
                dest.write(tw.toTwee())
                dest.close()
            except:
                self.app.displayError('exporting your source code')

        dialog.Destroy()
        
    def importSource (self, event = None):
        """Asks the user to choose a file to import source from, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import Source Code', os.getcwd(), '', \
                               'Text Files (*.txt)|*.txt|Twee Source Code (*.tw)|*.tw', wx.OPEN | wx.FD_CHANGE_DIR)
        
        if dialog.ShowModal() == wx.ID_OK:
            try:
                # have a TiddlyWiki object parse it for us
                
                source = open(dialog.GetPath(), 'r')
                tw = TiddlyWiki()
                tw.addTwee(source.read())
                source.close()
                
                # add passages for each of the tiddlers the TiddlyWiki saw
                
                if len(tw.tiddlers):
                    for t in tw.tiddlers:
                        tiddler = tw.tiddlers[t]
                        new = self.storyPanel.newWidget(title = tiddler.title, text = tiddler.text, quietly = True)
                        new.tags = tiddler.tags
                    self.setDirty(True, 'Import')
                else:
                    dialog = wx.MessageDialog(self, 'No passages were found in this file. Make sure ' + \
                                              'this is a Twee source file.', 'No Passages Found', \
                                              wx.ICON_INFO | wx.OK)
                    dialog.ShowModal()
            except:
                self.app.displayError('importing your source code')
    
    def save (self, event = None):
        if (self.saveDestination == ''):
            self.saveAs()
            return
        
        try:
            dest = open(self.saveDestination, 'w')
            pickle.dump(self.serialize(), dest)
            dest.close()
            self.setDirty(False)
        except:
            self.app.displayError('saving your story')

    def build (self, event = None):
        """Asks the user to choose a location to save a compiled story, then passed control to rebuild()."""
        dialog = wx.FileDialog(self, 'Build Story', os.getcwd(), "", \
                         "Web Page (*.html)|*.html", \
                           wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
    
        if dialog.ShowModal() == wx.ID_OK:
            self.buildDestination = dialog.GetPath()
            self.rebuild(None, True)
        
        dialog.Destroy()
                
    def rebuild (self, event = None, displayAfter = False):
        """
        Builds an HTML version of the story. Pass whether to open the destination file afterwards.
        """
        try:
            # open destination for writing
            
            dest = open(self.buildDestination, 'w')
    
            # assemble our tiddlywiki and write it out
            
            tw = TiddlyWiki()
            
            for widget in self.storyPanel.widgets:
                tw.addTiddler(widget.passage)
            
            dest.write(tw.toHtml(self.app, self.target).encode('utf-8'))
            dest.close()        
            if displayAfter: self.viewBuild()
        except:
            self.app.displayError('building your story')
    
    def viewBuild (self, event = None):
        """
        Opens the last built file in a Web browser.
        """
        path = 'file://' + urllib.pathname2url(self.buildDestination)
        path = path.replace('file://///', 'file:///')
        wx.LaunchDefaultBrowser(path)        
        
    def stats (self, event = None):
        """
        Displays a StatisticsDialog for this frame.
        """
        
        statFrame = StatisticsDialog(parent = self, storyPanel = self.storyPanel, app = self.app)
        statFrame.ShowModal()

    def showFind (self, event = None):
        """
        Shows a StoryFindFrame for this frame.
        """

        if (not hasattr(self, 'findFrame')):
            self.findFrame = StoryFindFrame(self.storyPanel, self.app)
        else:
            try:
                self.findFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'findFrame')
                self.showFind(event)

    def showReplace (self, event = None):
        """
        Shows a StoryReplaceFrame for this frame.
        """
        if (not hasattr(self, 'replaceFrame')):
            self.replaceFrame = StoryReplaceFrame(self.storyPanel, self.app)
        else:
            try:
                self.replaceFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'replaceFrame')
                self.showReplace(event)

    def proof (self, event = None):
        """
        Builds an RTF version of the story. Pass whether to open the destination file afterwards.
        """
           
        # ask for our destination
        
        dialog = wx.FileDialog(self, 'Proof Story', os.getcwd(), "", \
                         "RTF Document (*.rtf)|*.rtf", \
                           wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            dialog.Destroy()
        else:
            dialog.Destroy()
            return
        
        try:
            # open destination for writing
        
            dest = open(path, 'w')
            
            # assemble our tiddlywiki and write it out
            
            tw = TiddlyWiki()
            
            self.storyPanel.eachWidget(lambda w: tw.addTiddler(w.passage))
            dest.write(tw.toRtf())
            dest.close()
        except:
            self.app.displayError('building a proofing copy of your story')
        
    def setTarget (self, target):
        self.target = target
        
    def updateUI (self, event = None):
        """Adjusts menu items to reflect the current state."""

        hasSelection = self.storyPanel.hasSelection()

        canPaste = False
        if wx.TheClipboard.Open():
            canPaste = wx.TheClipboard.IsSupported(wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT))
            wx.TheClipboard.Close()
        
        # window title
        
        if self.saveDestination == '':
            title = StoryFrame.DEFAULT_TITLE
        else:
            bits = os.path.splitext(self.saveDestination)
            title = os.path.basename(bits[0])
        
        percent = str(int(round(self.storyPanel.scale * 100)))
        dirty = ''
        if self.dirty: dirty = ' *'

        self.SetTitle(title + dirty + ' (' + percent + '%) ' + '- ' + self.app.NAME)
        
        # File menu
        
        revertItem = self.menus.FindItemById(wx.ID_REVERT_TO_SAVED)
        revertItem.Enable(self.saveDestination != '' and self.dirty)
        
        # Edit menu
        
        undoItem = self.menus.FindItemById(wx.ID_UNDO)
        undoItem.Enable(self.storyPanel.canUndo())
        if self.storyPanel.canUndo():
            undoItem.SetText('Undo ' + self.storyPanel.undoAction() + '\tCtrl-Z')
        else:
            undoItem.SetText("Can't Undo\tCtrl-Z")
        
        redoItem = self.menus.FindItemById(wx.ID_REDO)
        redoItem.Enable(self.storyPanel.canRedo())
        if self.storyPanel.canRedo():
            redoItem.SetText('Redo ' + self.storyPanel.redoAction() + '\tCtrl-Y')
        else:
            redoItem.SetText("Can't Redo\tCtrl-Y")
        
        cutItem = self.menus.FindItemById(wx.ID_CUT)
        cutItem.Enable(hasSelection)
        copyItem = self.menus.FindItemById(wx.ID_COPY)
        copyItem.Enable(hasSelection)
        deleteItem = self.menus.FindItemById(wx.ID_DELETE)
        deleteItem.Enable(hasSelection)      
        pasteItem = self.menus.FindItemById(wx.ID_PASTE)
        pasteItem.Enable(canPaste)
        
        findAgainItem = self.menus.FindItemById(StoryFrame.EDIT_FIND_NEXT)
        findAgainItem.Enable(self.storyPanel.lastSearchRegexp != None)
        
        # View menu
        
        toolbarItem = self.menus.FindItemById(StoryFrame.VIEW_TOOLBAR)
        toolbarItem.Check(self.showToolbar)
        snapItem = self.menus.FindItemById(StoryFrame.VIEW_SNAP)
        snapItem.Check(self.storyPanel.snapping)
        
        # Story menu
        
        editItem = self.menus.FindItemById(wx.ID_EDIT)
        editItem.Enable(hasSelection)
        
        editFullscreenItem = self.menus.FindItemById(StoryFrame.STORY_EDIT_FULLSCREEN)
        editFullscreenItem.Enable(hasSelection and not self.storyPanel.hasMultipleSelection())
        
        rebuildItem = self.menus.FindItemById(StoryFrame.STORY_REBUILD)
        rebuildItem.Enable(self.buildDestination != '')
        
        viewLastItem = self.menus.FindItemById(StoryFrame.STORY_VIEW_LAST)
        viewLastItem.Enable(self.buildDestination != '')
        
        # Story format submenu
        
        formatItems = {}
        formatItems['sugarcane'] = self.menus.FindItemById(StoryFrame.STORY_FORMAT_SUGARCANE)
        formatItems['jonah'] = self.menus.FindItemById(StoryFrame.STORY_FORMAT_JONAH)
        formatItems['tw'] = self.menus.FindItemById(StoryFrame.STORY_FORMAT_TW1)
        formatItems['tw2'] = self.menus.FindItemById(StoryFrame.STORY_FORMAT_TW2)
        
        for key in formatItems:
            formatItems[key].Check(self.target == key)
        
    def toggleToolbar (self, event = None):
        """Toggles the toolbar onscreen."""
        if (self.showToolbar):
            self.showToolbar = False
            self.toolbar.Hide()
        else:
            self.showToolbar = True
            self.toolbar.Show()
        self.SendSizeEvent()
        
    def setDirty (self, value, action = None):
        """
        Sets the dirty flag to the value passed. Make sure to use this instead of
        setting the dirty property directly, as this method automatically updates
        the pristine property as well.
        
        If you pass an action parameter, this action will be saved for undoing under
        that name.
        """
        self.dirty = value
        self.pristine = False
        
        if value is True and action:
            self.storyPanel.pushUndo(action)
    
    def applyPrefs (self):
        """Passes on the apply message to child widgets."""
        self.storyPanel.eachWidget(lambda w: w.applyPrefs())
    
    def serialize (self):
        """Returns a dictionary of state suitable for pickling."""
        return { 'target': self.target, 'buildDestination': self.buildDestination, \
                 'saveDestination': self.saveDestination, \
                 'storyPanel': self.storyPanel.serialize() }
    
    def __repr__ (self):
        return "<StoryFrame '" + self.saveDestination + "'>"
    
    # menu constants
    # (that aren't already defined by wx)
    
    FILE_PAGE_SETUP = 101       # release 3 :)
    FILE_PRINT = 102            # release 3
    FILE_IMPORT_SOURCE = 103
    FILE_EXPORT_PROOF = 104
    FILE_EXPORT_SOURCE = 105
    
    EDIT_FIND_NEXT = 201
        
    VIEW_SNAP = 301
    VIEW_CLEANUP = 302
    VIEW_TOOLBAR = 303
    
    STORY_NEW_PASSAGE = 401
    STORY_EDIT_FULLSCREEN = 402
    STORY_BUILD = 403
    STORY_REBUILD = 404
    STORY_VIEW_LAST = 405
    STORY_STATS = 406
    
    STORY_FORMAT_SUGARCANE = 408
    STORY_FORMAT_JONAH = 409
    STORY_FORMAT_TW1 = 410
    STORY_FORMAT_TW2 = 411
    STORY_FORMAT_HELP = 412
    
    HELP_MANUAL = 501
    HELP_GROUP = 502
    HELP_BUG = 503

    # tooltip labels
    
    NEW_PASSAGE_TOOLTIP = 'Add a new passage to your story'
    ZOOM_IN_TOOLTIP = 'Zoom in'
    ZOOM_OUT_TOOLTIP = 'Zoom out'
    ZOOM_FIT_TOOLTIP = 'Zoom so all passages are visible onscreen'
    ZOOM_ONE_TOOLTIP = 'Zoom to 100%'

    # size constants
    
    DEFAULT_SIZE = (800, 600)
    TOOLBAR_ICON_SIZE = 32
    
    # misc stuff
    
    DEFAULT_TITLE = 'Untitled Story'