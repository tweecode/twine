#!/usr/bin/env python

# 
# StoryFrame
# A StoryFrame displays an entire story. Its main feature is an
# instance of a StoryPanel, but it also has a menu bar and toolbar.
#

import sys, os, urllib, pickle, wx, codecs, time
from tiddlywiki import TiddlyWiki
from storypanel import StoryPanel
from passagewidget import PassageWidget
from statisticsdialog import StatisticsDialog
from storysearchframes import StoryFindFrame, StoryReplaceFrame

class StoryFrame (wx.Frame):
    
    def __init__(self, parent, app, state = None):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = StoryFrame.DEFAULT_TITLE, \
                          size = StoryFrame.DEFAULT_SIZE)     
        self.app = app
        self.parent = parent
        self.pristine = True    # the user has not added any content to this at all
        self.dirty = False      # the user has not made unsaved changes
        self.storyFormats = {}  # list of available story formats

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
        
        # Timer for the auto build file watcher
        self.autobuildtimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.autoBuildTick, self.autobuildtimer)
        
        # File menu
        
        fileMenu = wx.Menu()
        
        fileMenu.Append(wx.ID_NEW, '&New Story\tCtrl-Shift-N')
        self.Bind(wx.EVT_MENU, self.app.newStory, id = wx.ID_NEW)
        
        fileMenu.Append(wx.ID_OPEN, '&Open Story...\tCtrl-O')
        self.Bind(wx.EVT_MENU, self.app.openDialog, id = wx.ID_OPEN)
        
        recentFilesMenu = wx.Menu()
        self.recentFiles = wx.FileHistory(self.app.RECENT_FILES)
        self.recentFiles.Load(self.app.config)
        self.app.verifyRecentFiles(self)
        self.recentFiles.UseMenu(recentFilesMenu)
        self.recentFiles.AddFilesToThisMenu(recentFilesMenu)
        fileMenu.AppendMenu(wx.ID_ANY, 'Open &Recent', recentFilesMenu)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 0), id = wx.ID_FILE1)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 1), id = wx.ID_FILE2)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 2), id = wx.ID_FILE3)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 3), id = wx.ID_FILE4)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 4), id = wx.ID_FILE5)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 5), id = wx.ID_FILE6)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 6), id = wx.ID_FILE7)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 7), id = wx.ID_FILE8)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 8), id = wx.ID_FILE9)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 9), id = wx.ID_FILE9 + 1)
        
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
        self.Bind(wx.EVT_MENU, self.checkCloseMenu, id = wx.ID_CLOSE)
        
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
        
        if sys.platform == 'darwin':
            shortcut = 'Ctrl-Shift-H'
        else:
            shortcut = 'Ctrl-H'
        
        editMenu.Append(wx.ID_REPLACE, 'Replace Across Entire Story...\t' + shortcut)
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

        self.storyMenu = wx.Menu()
        
        self.storyMenu.Append(StoryFrame.STORY_NEW_PASSAGE, '&New Passage\tCtrl-N')
        self.Bind(wx.EVT_MENU, self.storyPanel.newWidget, id = StoryFrame.STORY_NEW_PASSAGE)
        
        self.storyMenu.Append(wx.ID_EDIT, '&Edit Passage\tCtrl-E')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e)), id = wx.ID_EDIT)

        self.storyMenu.Append(StoryFrame.STORY_EDIT_FULLSCREEN, '&Edit Passage Text Fullscreen\tF12')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e, fullscreen = True)), \
                  id = StoryFrame.STORY_EDIT_FULLSCREEN)
        
        self.storyMenu.Append(wx.ID_DELETE, '&Delete Passage')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.removeWidgets(e, saveUndo = True), id = wx.ID_DELETE)
 
        self.storyMenu.AppendSeparator()
        
        self.storyMenu.Append(StoryFrame.STORY_BUILD, '&Build Story...\tCtrl-B')
        self.Bind(wx.EVT_MENU, self.build, id = StoryFrame.STORY_BUILD)        
        
        self.storyMenu.Append(StoryFrame.STORY_REBUILD, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.rebuild, id = StoryFrame.STORY_REBUILD) 

        self.storyMenu.Append(StoryFrame.STORY_VIEW_LAST, '&View Last Build\tCtrl-L')
        self.Bind(wx.EVT_MENU, self.viewBuild, id = StoryFrame.STORY_VIEW_LAST)
        
        self.autobuildmenuitem = self.storyMenu.Append(StoryFrame.STORY_AUTO_BUILD, '&Auto Build', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.autoBuild, self.autobuildmenuitem)
        self.storyMenu.Check(StoryFrame.STORY_AUTO_BUILD, False)

        self.storyMenu.AppendSeparator()

        self.storyMenu.Append(StoryFrame.STORY_STATS, 'Story &Statistics\tCtrl-I')
        self.Bind(wx.EVT_MENU, self.stats, id = StoryFrame.STORY_STATS) 

        # Story Format submenu
        
        storyFormatMenu = wx.Menu()
        storyFormatCounter = StoryFrame.STORY_FORMAT_BASE
        storyFormatPath = app.getPath() + os.sep + 'targets' + os.sep 
        for sfdir in os.listdir(storyFormatPath):
            if os.access(storyFormatPath + sfdir + os.sep + 'header.html', os.R_OK):
                if sfdir == 'jonah':
                    sfdirlabel = 'Jonah'
                elif sfdir == 'sugarcane': 
                    sfdirlabel = 'Sugarcane'
                elif sfdir == 'tw':
                    sfdirlabel = 'TW'
                elif sfdir == 'tw2':
                    sfdirlabel = 'TW2'
                else: 
                    sfdirlabel = sfdir 
                storyFormatMenu.Append(storyFormatCounter, sfdirlabel, kind = wx.ITEM_CHECK)
                self.Bind(wx.EVT_MENU, lambda e,target=sfdir: self.setTarget(target), id = storyFormatCounter)
                self.storyFormats[storyFormatCounter] = sfdir
                storyFormatCounter = storyFormatCounter + 1
        
        storyFormatMenu.AppendSeparator()
       
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_HELP, '&About Story Formats')        
        self.Bind(wx.EVT_MENU, lambda e: self.app.storyFormatHelp(), id = StoryFrame.STORY_FORMAT_HELP)
        
        self.storyMenu.AppendMenu(wx.ID_ANY, 'Story &Format', storyFormatMenu)
        
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
        self.menus.Append(self.storyMenu, '&Story')
        self.menus.Append(helpMenu, '&Help')
        self.SetMenuBar(self.menus)
        
        # extra shortcuts
        
        self.SetAcceleratorTable(wx.AcceleratorTable([ \
                                    (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_EDIT), \
                                    (wx.ACCEL_CTRL, wx.WXK_RETURN, StoryFrame.STORY_EDIT_FULLSCREEN) \
                                                      ]))

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
        
        if app.config.ReadBool('storyFrameToolbar'):
            self.showToolbar = True
            self.toolbar.Realize()
        else:
            self.showToolbar = False
            self.toolbar.Realize()
            self.toolbar.Hide()
            
        
    def revert (self, event = None):
        """Reverts to the last saved version of the story file."""
        bits = os.path.splitext(self.saveDestination)
        title = '"' + os.path.basename(bits[0]) + '"'
        if title == '""': title = 'your story'
        
        message = 'Revert to the last version of ' + title + ' you saved?'
        dialog = wx.MessageDialog(self, message, 'Revert to Saved', wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
        
        if (dialog.ShowModal() == wx.ID_YES):
            self.Destroy()
            self.app.open(self.saveDestination)
            self.dirty = False;
            self.checkClose(None)
    
    def checkClose (self, event):
        self.checkCloseDo(event,byMenu=False)
    
    def checkCloseMenu (self, event):
        self.checkCloseDo(event,byMenu=True)
        
    def checkCloseDo (self, event, byMenu):
        """
        If this instance's dirty flag is set, asks the user to confirm that they don't want to save changes.
        """
                
        if (self.dirty):
            bits = os.path.splitext(self.saveDestination)
            title = '"' + os.path.basename(bits[0]) + '"'
            if title == '""': title = 'your story' 

            message = 'Are you sure you want to close ' + title + ' without saving changes?'
            dialog = wx.MessageDialog(self, message, 'Unsaved Changes', \
                                      wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
            if (dialog.ShowModal() == wx.ID_NO):
                event.Veto()
                return
            else:
                self.dirty = False
        
        # ask all our widgets to close any editor windows
        
        for w in list(self.storyPanel.widgets):
            if isinstance(w, PassageWidget):
                w.closeEditor()

        self.app.removeStory(self, byMenu)
        if event != None:
            event.Skip()
        self.Destroy()
        
    def saveAs (self, event = None):
        """Asks the user to choose a file to save state to, then passes off control to save()."""
        dialog = wx.FileDialog(self, 'Save Story As', os.getcwd(), "", \
                         "Twine Story (*.tws)|*.tws|Twine Story without private content [copy] (*.tws)|*.tws", \
                           wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
    
        if dialog.ShowModal() == wx.ID_OK:
            if dialog.GetFilterIndex() == 0:
                self.saveDestination = dialog.GetPath()
                self.app.config.Write('savePath', os.getcwd())
                self.app.addRecentFile(self.saveDestination)
                self.save(None)
            elif dialog.GetFilterIndex() == 1:
                npsavedestination = dialog.GetPath()
                try:
                    dest = open(npsavedestination, 'wb')
                    pickle.dump(self.serialize_noprivate(npsavedestination), dest)
                    dest.close()
                    self.app.addRecentFile(npsavedestination)
                except:
                    self.app.displayError('saving your story')
                
        dialog.Destroy()
        
    def exportSource (self, event = None):
        """Asks the user to choose a file to export source to, then exports the wiki."""
        dialog = wx.FileDialog(self, 'Export Source Code', os.getcwd(), "", \
                               'Twee File (*.twee;* .tw; *.txt)|*.twee;*.tw;*.txt|All Files (*.*)|*.*', wx.SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            try:
                path = dialog.GetPath()
                tw = TiddlyWiki()
                
                for widget in self.storyPanel.widgets: tw.addTiddler(widget.passage)
                dest = codecs.open(path, 'w', 'utf-8-sig', 'replace')
                order = map(lambda w: w.passage.title, self.storyPanel.sortedWidgets())
                dest.write(tw.toTwee(order))
                dest.close()
            except:
                self.app.displayError('exporting your source code')

        dialog.Destroy()
        
    def importSource (self, event = None):
        """Asks the user to choose a file to import source from, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import Source Code', os.getcwd(), '', \
                               'Twee File (*.twee;* .tw; *.txt)|*.twee;*.tw;*.txt|All Files (*.*)|*.*', wx.OPEN | wx.FD_CHANGE_DIR)
        
        if dialog.ShowModal() == wx.ID_OK:
            try:
                # have a TiddlyWiki object parse it for us
                tw = TiddlyWiki()
                tw.addTweeFromFilename(dialog.GetPath())
                
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
            dest = open(self.saveDestination, 'wb')
            pickle.dump(self.serialize(), dest)
            dest.close()
            self.setDirty(False)
            self.app.config.Write('LastFile', self.saveDestination)
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
            # Remember current working dir and set to savefile's dir. InterTwine StoryIncludes are relative to the Twine file.
            cwd = os.getcwd()
            if self.saveDestination == '':
                twinedocdir = cwd
            else:
                twinedocdir = os.path.dirname(self.saveDestination)
                os.chdir(twinedocdir)
    
            # assemble our tiddlywiki and write it out
            hasstartpassage = False
            tw = TiddlyWiki()
            for widget in self.storyPanel.widgets:
                # if widget.passage.title != 'StoryIncludes' and \
                # not any('Twine.private' in t for t in widget.passage.tags) and \
                # not any('Twine.system' in t for t in widget.passage.tags):
                if widget.passage.title != 'StoryIncludes' and \
                not any(t.startswith('Twine.') for t in widget.passage.tags):
                    tw.addTiddler(widget.passage)
                    if widget.passage.title == "Start":
                        hasstartpassage = True

            # is there a Start passage?
            if hasstartpassage == False:
                self.app.displayError('building your story because there is no "Start" passage. ' + "\n" 
                                      + 'Your story will build but the web-browser will not be able to run the story. ' + "\n"
                                      + 'Please add a passage with the title "Start"')

            for widget in self.storyPanel.widgets:
                if widget.passage.title == 'StoryIncludes':
                    lines = widget.passage.text.splitlines()
                    lines.append('');
                    # State 0: Look for a filename
                    ## State 1: have filename, look for filename, EXCEPT, INCLUDE, ALIAS
                    ## State 2: EXCEPT mode, look for INCLUDE 3, ALIAS 4 or blank line 0
                    ## State 3: INCLUDE mode, look for EXCEPT 2, ALIAS 4 or blank line 0
                    ## State 4: ALIAS mode, look for EXCEPT 2, INCLUDE 2 or blank line 0
                    state = 0;
                    state_filename = '';
                    excludepassages = [ 'Start', 'StoryMenu', 'StoryTitle', 'StoryAuthor', 'StorySubtitle', 'StoryIncludes' ]
                    for line in lines:
                        if state == 0:
                            state_filename = line
                            state = 1
                            continue
                        elif state == 1:
                            try:
                                if state_filename.strip() != '':
                                    extension = os.path.splitext(state_filename)[1] 
                                    if extension == '.tws':
                                        if any(state_filename.startswith(t) for t in ['http://', 'https://', 'ftp://']):
                                            openedFile = urllib.urlopen(state_filename)
                                        else:
                                            openedFile = open(state_filename, 'r')
                                        s = StoryFrame(None, app = self.app, state = pickle.load(openedFile))
                                        openedFile.close()
                                        for widget in s.storyPanel.widgets:
                                            if not any(widget.passage.title in t for t in excludepassages) and \
                                            not any('Twine.private' in t for t in widget.passage.tags) and \
                                            not any('Twine.system' in t for t in widget.passage.tags):
                                                tw.addTiddler(widget.passage)
                                        s.Destroy()
                                    elif extension == '.tw' or extension == '.txt' or extension == '.twee':
                                        if any(state_filename.startswith(t) for t in ['http://', 'https://', 'ftp://']):
                                            openedFile = urllib.urlopen(state_filename)
                                            s = openedFile.read()
                                            openedFile.close()
                                            t = tempfile.NamedTemporaryFile(delete=False)
                                            cleanuptempfile = True
                                            t.write(s)
                                            t.close()
                                            filename = t.name
                                        else:
                                            filename = state_filename
                                            cleanuptempfile = False
                                            
                                        tw1 = TiddlyWiki()
                                        tw1.addTweeFromFilename(filename)
                                        if cleanuptempfile: os.remove(filename)
                                        tiddlerkeys = tw1.tiddlers.keys()
                                        for tiddlerkey in tiddlerkeys:
                                            passage = tw1.tiddlers[tiddlerkey]
                                            if not any(passage.title == t for t in excludepassages) and \
                                            not any('Twine.private' in t for t in passage.tags) and \
                                            not any('Twine.system' in t for t in passage.tags):
                                                tw.addTiddler(passage)
                                    else:
                                        raise 'File format not recognized'
                            except:
                                self.app.displayError('opening the Twine file named ' + state_filename + ' which is referred to by the passage StoryIncludes')
                            state_filename = line
                            state = 1
                            continue
                    break

            # Write the output file
            os.chdir(os.path.dirname(self.buildDestination))
            dest = open(self.buildDestination, 'w')
            dest.write(tw.toHtml(self.app, self.target).encode('utf-8'))
            dest.close()
            os.chdir(cwd)
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
        
    def autoBuild (self, event = None):
        """
        Toggles the autobuild feature
        """
        if self.autobuildmenuitem.IsChecked():
            self.autobuildtimer.Start(5000)
            self.autoBuildStart();
        else:
            self.autobuildtimer.Stop()
    
    def autoBuildTick (self, event = None):
        """
        Called whenever the autobuild timer checks up on things
        """
        for pathname, oldmtime in self.autobuildfiles.iteritems():
            newmtime = os.stat(pathname).st_mtime
            if newmtime != oldmtime:
                #print "Auto rebuild triggered by: ", pathname
                self.autobuildfiles[pathname] = newmtime
                self.rebuild()
                break
        
    def autoBuildStart (self):
        self.autobuildfiles = { }
        if self.saveDestination == '':
            twinedocdir = cwd
        else:
            twinedocdir = os.path.dirname(self.saveDestination)
        for f in os.listdir(twinedocdir):
            extension = os.path.splitext(f)[1] 
            if extension == '.tws' or extension == '.tw' or extension == '.txt' or extension == '.twee':
                pathname = os.path.join(twinedocdir, f)
                mtime = os.stat(pathname).st_mtime
                self.autobuildfiles[pathname] = mtime
        
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
            for widget in self.storyPanel.sortedWidgets():
                tw.addTiddler(widget.passage)

            order = map(lambda w: w.passage.title, self.storyPanel.sortedWidgets())            
            dest.write(tw.toRtf(order))
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

        for key in self.storyFormats:
            self.menus.FindItemById(key).Check(self.target == self.storyFormats[key])
        
    def toggleToolbar (self, event = None):
        """Toggles the toolbar onscreen."""
        if (self.showToolbar):
            self.showToolbar = False
            self.toolbar.Hide()
            self.app.config.WriteBool('storyFrameToolbar', False)
        else:
            self.showToolbar = True
            self.toolbar.Show()
            self.app.config.WriteBool('storyFrameToolbar', True)
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
        self.storyPanel.Refresh()
    
    def serialize (self):
        """Returns a dictionary of state suitable for pickling."""
        return { 'target': self.target, 'buildDestination': self.buildDestination, \
                 'saveDestination': self.saveDestination, \
                 'storyPanel': self.storyPanel.serialize() }
    
    def serialize_noprivate (self, dest):
        """Returns a dictionary of state suitable for pickling."""
        return { 'target': self.target, 'buildDestination': '', \
                 'saveDestination': dest, \
                 'storyPanel': self.storyPanel.serialize_noprivate() }

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
    STORY_AUTO_BUILD = 406
    STORY_STATS = 407
    
    STORY_FORMAT_HELP = 408
    STORY_FORMAT_BASE = 409    
    
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