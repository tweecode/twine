#!/usr/bin/env python

# 
# StoryFrame
# A StoryFrame displays an entire story. Its main feature is an
# instance of a StoryPanel, but it also has a menu bar and toolbar.
#

import sys, re, os, urllib, urlparse, pickle, wx, codecs, time, tempfile, images
from wx.lib import imagebrowser
from tiddlywiki import TiddlyWiki
from storypanel import StoryPanel
from passagewidget import PassageWidget
from statisticsdialog import StatisticsDialog
from storysearchframes import StoryFindFrame, StoryReplaceFrame
from random import shuffle

class StoryFrame (wx.Frame):
    
    def __init__(self, parent, app, state = None):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title = StoryFrame.DEFAULT_TITLE, \
                          size = StoryFrame.DEFAULT_SIZE)     
        self.app = app
        self.parent = parent
        self.pristine = True    # the user has not added any content to this at all
        self.dirty = False      # the user has not made unsaved changes
        self.storyFormats = {}  # list of available story formats
        self.lastTestBuild = None
        self.title = ""
        
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
        
        # Import submenu
        
        importMenu = wx.Menu()

        importMenu.Append(StoryFrame.FILE_IMPORT_HTML, 'Compiled &HTML File...')
        self.Bind(wx.EVT_MENU, self.importHtmlDialog, id = StoryFrame.FILE_IMPORT_HTML) 
        importMenu.Append(StoryFrame.FILE_IMPORT_SOURCE, 'Twee Source &Code...')
        self.Bind(wx.EVT_MENU, self.importSourceDialog, id = StoryFrame.FILE_IMPORT_SOURCE) 
        
        fileMenu.AppendMenu(wx.ID_ANY, '&Import', importMenu)
        
        # Export submenu
        
        exportMenu = wx.Menu()
        
        exportMenu.Append(StoryFrame.FILE_EXPORT_SOURCE, 'Twee Source &Code...')
        self.Bind(wx.EVT_MENU, self.exportSource, id = StoryFrame.FILE_EXPORT_SOURCE)
        
        exportMenu.Append(StoryFrame.FILE_EXPORT_PROOF, '&Proofing Copy...')
        self.Bind(wx.EVT_MENU, self.proof, id = StoryFrame.FILE_EXPORT_PROOF) 
        
        fileMenu.AppendMenu(wx.ID_ANY, '&Export', exportMenu)
        
        fileMenu.AppendSeparator()
        
        fileMenu.Append(wx.ID_CLOSE, '&Close Story\tCtrl-W')
        self.Bind(wx.EVT_MENU, self.checkCloseMenu, id = wx.ID_CLOSE)
        
        fileMenu.Append(wx.ID_EXIT, 'E&xit Twine\tCtrl-Q')
        self.Bind(wx.EVT_MENU, lambda e: self.app.exit(), id = wx.ID_EXIT)
        

        
        # Edit menu
        
        editMenu = wx.Menu()
        
        editMenu.Append(wx.ID_UNDO, '&Undo\tCtrl-Z')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.undo(), id = wx.ID_UNDO)
        
        if sys.platform == 'darwin':
            shortcut = 'Ctrl-Shift-Z'
        else:
            shortcut = 'Ctrl-Y'
            
        editMenu.Append(wx.ID_REDO, '&Redo\t' + shortcut)
        self.Bind(wx.EVT_MENU, lambda e: self.bodyInput.Redo(), id = wx.ID_REDO)

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
        
        editMenu.Append(wx.ID_REPLACE, 'Replace Across Story...\t' + shortcut)
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
        
        # New Passage submenu
        
        self.newPassageMenu = wx.Menu()
        
        self.newPassageMenu.Append(StoryFrame.STORY_NEW_PASSAGE, '&Passage\tCtrl-N')
        self.Bind(wx.EVT_MENU, self.storyPanel.newWidget, id = StoryFrame.STORY_NEW_PASSAGE)
        
        self.newPassageMenu.AppendSeparator()
        
        self.newPassageMenu.Append(StoryFrame.STORY_NEW_STYLESHEET, 'S&tylesheet')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.newWidget(text = self.storyPanel.FIRST_CSS, \
                                                                   tags = ['stylesheet']), id = StoryFrame.STORY_NEW_STYLESHEET)

        self.newPassageMenu.Append(StoryFrame.STORY_NEW_SCRIPT, '&Script')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.newWidget(tags = ['script']), id = StoryFrame.STORY_NEW_SCRIPT)
        
        self.newPassageMenu.Append(StoryFrame.STORY_NEW_ANNOTATION, '&Annotation')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.newWidget(tags = ['annotation']), id = StoryFrame.STORY_NEW_ANNOTATION)
        
        self.storyMenu.AppendMenu(wx.ID_ANY, 'New', self.newPassageMenu)
        
        self.storyMenu.Append(wx.ID_EDIT, '&Edit Passage\tCtrl-E')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e)), id = wx.ID_EDIT)

        self.storyMenu.Append(StoryFrame.STORY_EDIT_FULLSCREEN, 'Edit in &Fullscreen\tF12')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e, fullscreen = True)), \
                  id = StoryFrame.STORY_EDIT_FULLSCREEN)
 
        self.storyMenu.AppendSeparator()
        
        self.importImageMenu = wx.Menu()
        self.importImageMenu.Append(StoryFrame.STORY_IMPORT_IMAGE, 'From &File...')
        self.Bind(wx.EVT_MENU, self.importImageDialog, id = StoryFrame.STORY_IMPORT_IMAGE)
        self.importImageMenu.Append(StoryFrame.STORY_IMPORT_IMAGE_URL, 'From Web &URL...')
        self.Bind(wx.EVT_MENU, self.importImageURL, id = StoryFrame.STORY_IMPORT_IMAGE_URL)
        
        self.storyMenu.AppendMenu(wx.ID_ANY, 'Import &Image', self.importImageMenu)
        
        self.storyMenu.Append(StoryFrame.STORY_IMPORT_FONT, 'Import &Font...')
        self.Bind(wx.EVT_MENU, self.importFontDialog, id = StoryFrame.STORY_IMPORT_FONT)
        
        self.storyMenu.AppendSeparator()
        
        # Story Settings submenu
        
        self.storySettingsMenu = wx.Menu()
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_START, 'Start')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_START)
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_TITLE, 'StoryTitle')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_TITLE)
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_SUBTITLE, 'StorySubtitle')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_SUBTITLE)
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_AUTHOR, 'StoryAuthor')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_AUTHOR)
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_MENU, 'StoryMenu')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_MENU)
        
        # Separator for 'visible' passages (title, subtitle) and those that solely affect compilation
        self.storySettingsMenu.AppendSeparator()
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_SETTINGS, 'StorySettings')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_SETTINGS)
        
        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_INCLUDES, 'StoryIncludes')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id = StoryFrame.STORYSETTINGS_INCLUDES)
        
        self.storyMenu.AppendMenu(wx.ID_ANY, 'Special Passages', self.storySettingsMenu)

        self.storyMenu.AppendSeparator()

        self.storyMenu.Append(StoryFrame.STORY_STATS, 'Story &Statistics\tCtrl-I')
        self.Bind(wx.EVT_MENU, self.stats, id = StoryFrame.STORY_STATS) 

        # Story Format submenu
        
        storyFormatMenu = wx.Menu()
        storyFormatCounter = StoryFrame.STORY_FORMAT_BASE
        storyFormatPath = app.getPath() + os.sep + 'targets' + os.sep 
        	
        for sfdir in os.listdir(storyFormatPath):
            try:
                if os.access(storyFormatPath + sfdir + os.sep + 'header.html', os.R_OK):
                    storyFormatMenu.Append(storyFormatCounter, sfdir.capitalize(), kind = wx.ITEM_CHECK)
                    self.Bind(wx.EVT_MENU, lambda e,target=sfdir: self.setTarget(target), id = storyFormatCounter)
                    self.storyFormats[storyFormatCounter] = sfdir
                    storyFormatCounter += 1
            except:
                pass
        
        if sys.platform == "darwin":
            try:
                externalFormatPath = re.sub('[^/]+.app/.*', '', app.getPath()) + os.sep + 'targets' + os.sep        
                for sfdir in os.listdir(externalFormatPath):
                    if os.access(externalFormatPath + sfdir + os.sep + 'header.html', os.R_OK):
                        storyFormatMenu.Append(storyFormatCounter, sfdir.capitalize(), kind = wx.ITEM_CHECK)
                        self.Bind(wx.EVT_MENU, lambda e,target=sfdir: self.setTarget(target), id = storyFormatCounter)
                        self.storyFormats[storyFormatCounter] = sfdir
                        storyFormatCounter += 1
            except:
                pass
                
        if storyFormatCounter:
            storyFormatMenu.AppendSeparator()
       
        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_HELP, '&About Story Formats')        
        self.Bind(wx.EVT_MENU, lambda e: self.app.storyFormatHelp(), id = StoryFrame.STORY_FORMAT_HELP)
        
        self.storyMenu.AppendMenu(wx.ID_ANY, 'Story &Format', storyFormatMenu)
        
        # Build menu
        
        buildMenu = wx.Menu()
        
        buildMenu.Append(StoryFrame.BUILD_TEST, '&Test Play\tCtrl-T')
        self.Bind(wx.EVT_MENU, self.testBuild, id = StoryFrame.BUILD_TEST)  
        
        buildMenu.Append(StoryFrame.BUILD_TEST_HERE, 'Test Play From Here\tCtrl-Shift-T')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: self.testBuild(startAt = w.passage.title)), \
            id = StoryFrame.BUILD_TEST_HERE)  
        
        buildMenu.AppendSeparator()
        buildMenu.Append(StoryFrame.BUILD_BUILD, '&Build Story...\tCtrl-B')
        self.Bind(wx.EVT_MENU, self.build, id = StoryFrame.BUILD_BUILD)
        
        buildMenu.Append(StoryFrame.BUILD_REBUILD, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.rebuild, id = StoryFrame.BUILD_REBUILD) 

        buildMenu.Append(StoryFrame.BUILD_VIEW_LAST, '&View Last Build\tCtrl-L')
        self.Bind(wx.EVT_MENU, self.viewBuild, id = StoryFrame.BUILD_VIEW_LAST)
        
        self.autobuildmenuitem = buildMenu.Append(StoryFrame.BUILD_AUTO_BUILD, '&Auto Build', kind = wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.autoBuild, self.autobuildmenuitem)
        buildMenu.Check(StoryFrame.BUILD_AUTO_BUILD, False)
        
        # Help menu
        
        helpMenu = wx.Menu()
 
        helpMenu.Append(StoryFrame.HELP_MANUAL, 'Twine &Wiki')
        self.Bind(wx.EVT_MENU, self.app.openDocs, id = StoryFrame.HELP_MANUAL)
        
        helpMenu.Append(StoryFrame.HELP_FORUM, 'Twine &Forum')
        self.Bind(wx.EVT_MENU, self.app.openForum, id = StoryFrame.HELP_FORUM)
        
        helpMenu.Append(StoryFrame.HELP_GITHUB, 'Twine\'s Source Code on &GitHub')
        self.Bind(wx.EVT_MENU, self.app.openGitHub, id = StoryFrame.HELP_GITHUB)
        
        helpMenu.AppendSeparator()
        
        helpMenu.Append(wx.ID_ABOUT, '&About Twine')
        self.Bind(wx.EVT_MENU, self.app.about, id = wx.ID_ABOUT)
        
        # add menus
        
        self.menus = wx.MenuBar()
        self.menus.Append(fileMenu, '&File')
        self.menus.Append(editMenu, '&Edit')
        self.menus.Append(viewMenu, '&View')
        self.menus.Append(self.storyMenu, '&Story')
        self.menus.Append(buildMenu, '&Build')
        self.menus.Append(helpMenu, '&Help')
        self.SetMenuBar(self.menus)
        
        # extra shortcuts
        
        self.SetAcceleratorTable(wx.AcceleratorTable([ \
                                    (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_EDIT), \
                                    (wx.ACCEL_CTRL, wx.WXK_RETURN, StoryFrame.STORY_EDIT_FULLSCREEN) \
                                                      ]))

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
            
    def __del__(self):
        if self.lastTestBuild and os.path.exists(self.lastTestBuild.name):
            os.remove(self.lastTestBuild.name)
        
    def revert (self, event = None):
        """Reverts to the last saved version of the story file."""
        bits = os.path.splitext(self.saveDestination)
        title = '"' + os.path.basename(bits[0]) + '"'
        if title == '""': title = 'your story'
        
        message = 'Revert to the last saved version of ' + title + '?'
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
        If this instance's dirty flag is set, asks the user if they want to save the changes.
        """
                
        if (self.dirty):
            bits = os.path.splitext(self.saveDestination)
            title = '"' + os.path.basename(bits[0]) + '"'
            if title == '""': title = 'your story' 

            message = 'Do you want to save the changes to ' + title + ' before closing?'
            dialog = wx.MessageDialog(self, message, 'Unsaved Changes', \
                                      wx.ICON_WARNING | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT)
            result = dialog.ShowModal();
            if (result == wx.ID_CANCEL):
                event.Veto()
                return
            elif (result == wx.ID_NO):
                self.dirty = False
            else:
                self.save(None)
                if self.dirty:
                    event.Veto()
                    return
        
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
                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
    
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
                               'Twee File (*.twee;* .tw; *.txt)|*.twee;*.tw;*.txt|All Files (*.*)|*.*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
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
        
    def importHtmlDialog(self, event = None):
        """Asks the user to choose a file to import HTML tiddlers from, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import From Compiled HTML', os.getcwd(), '', \
                               'HTML Twine game (*.html;* .htm; *.txt)|*.html;*.htm;*.txt|All Files (*.*)|*.*', wx.FD_OPEN | wx.FD_CHANGE_DIR)
        
        if dialog.ShowModal() == wx.ID_OK:
            self.importHtml(dialog.GetPath())
            
    def importHtml (self, path):
        """Imports the tiddler objects in a HTML file into the story."""
        self.importSource(path, True)

    def importSourceDialog(self, event = None):
        """Asks the user to choose a file to import source from, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import Source Code', os.getcwd(), '', \
                               'Twee File (*.twee;* .tw; *.txt)|*.twee;*.tw;*.txt|All Files (*.*)|*.*', wx.FD_OPEN | wx.FD_CHANGE_DIR)
        
        if dialog.ShowModal() == wx.ID_OK:
            self.importSource(dialog.GetPath())
        
    def importSource (self, path, html = False):
        """Imports the tiddler objects in a Twee file into the story."""
        
        try:
            # have a TiddlyWiki object parse it for us
            tw = TiddlyWiki()
            if html:
                tw.addHtmlFromFilename(path)
            else:
                tw.addTweeFromFilename(path)
            
            allWidgetTitles = []
            
            self.storyPanel.eachWidget(lambda e: allWidgetTitles.append(e.passage.title))
            
            # add passages for each of the tiddlers the TiddlyWiki saw
            if len(tw.tiddlers):
                removedWidgets = []
                skippedTitles = []
                
                # Check for passage title conflicts
                for t in tw.tiddlers:
                    
                    if t in allWidgetTitles:
                        dialog = wx.MessageDialog(self, 'There is already a passage titled "' + t \
                                              + '" in this story. Replace it with the imported passage?', 'Passage Title Conflict', \
                                              wx.ICON_WARNING | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT);
                        check = dialog.ShowModal();
                        if check == wx.ID_YES:
                            removedWidgets.append(t)
                        elif check == wx.ID_CANCEL:
                            return
                        elif check == wx.ID_NO:
                            skippedTitles.append(t)
                
                # Remove widgets elected to be replaced
                for t in removedWidgets:
                    self.storyPanel.removeWidget(self.storyPanel.findWidget(t))
                
                # Insert widgets now
                lastpos = [0, 0]
                addedWidgets = []
                for t in tw.tiddlers:
                    t = tw.tiddlers[t]
                    if t.title in skippedTitles:
                        continue
                    new = self.storyPanel.newWidget(title = t.title, tags = t.tags, text = t.text, quietly = True,
                                                    pos = t.pos if t.pos else lastpos)
                    lastpos = new.pos
                    addedWidgets.append(new)
                    
                self.setDirty(True, 'Import')
                for t in addedWidgets:
                    t.clearPaintCache()
            else:
                dialog = wx.MessageDialog(self, 'No passages were found in this file. Make sure ' + \
                                          'this is a Twee source file.', 'No Passages Found', \
                                          wx.ICON_INFORMATION | wx.OK)
                dialog.ShowModal()
        except:
            self.app.displayError('importing')
    
    def importImageURL(self, event = None):
        dialog = wx.TextEntryDialog(self, "Enter the image URL (GIFs, JPEGs, PNGs, SVGs and WebPs only)", "Import Image from Web", "http://")
        if dialog.ShowModal() == wx.ID_OK:
            try:
                # Download the file
                url = dialog.GetValue()
                urlfile = urllib.urlopen(url)
                path = urlparse.urlsplit(url)[2]
                title = os.path.splitext(os.path.basename(path))[0]
                file = urlfile.read().encode('base64').replace('\n', '')
                
                # Now that the file's read, check the info
                maintype = urlfile.info().getmaintype();
                if maintype != "image":
                    raise Exception("The server served "+maintype+" instead of an image.")
                # Convert the file
                mimeType = urlfile.info().gettype()
                urlfile.close()
                text = "data:"+mimeType+";base64,"+file
                self.importImage(text, title)
            except:
                self.app.displayError('importing from the web')
                            
    def importImageDialog(self, event = None, useImageDialog = False, replace = None):
        """Asks the user to choose an image file to import, then imports into the current story.
           replace is a Tiddler, if any, that will be replaced by the image."""
        # Use the wxPython image browser?
        if useImageDialog:
            dialog = imagebrowser.ImageDialog(self, os.getcwd())
            dialog.ChangeFileTypes([ ('Web Image File', '*.(gif|jpg|jpeg|png|webp|svg)')])
            dialog.ResetFiles()
        else:
            dialog = wx.FileDialog(self, 'Import Image File', os.getcwd(), '', \
                                   'Web Image File|*.gif;*.jpg;*.jpeg;*.png;*.webp;*.svg|All Files (*.*)|*.*', wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetFile() if useImageDialog else dialog.GetPath()
            try:
                if not replace:
                    text, title = self.openFileAsBase64(file)
                    self.importImage(text, title)
                else:
                    replace.passage.text = self.openFileAsBase64(file)[0]
                    replace.updateBitmap()
            except IOError:
                self.app.displayError('importing an image')
    
    def importFontDialog(self, event = None):
        """Asks the user to choose a font file to import, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import Font File', os.getcwd(), '', \
                                   'Web Font File (.ttf, .otf, .woff, .svg)|*.ttf;*.otf;*.woff;*.svg|All Files (*.*)|*.*', wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            self.importFont(dialog.GetPath())
        
    def openFileAsBase64(self, file):
        """Opens a file and returns its base64 representation, expressed as a Data URI with MIME type"""
        file64 = open(file, 'rb').read().encode('base64').replace('\n', '')
        title, mimeType = os.path.splitext(os.path.basename(file))
        return (images.AddURIPrefix(file64, mimeType[1:]), title)
    
    def newTitle(self, title):
        """ Check if a title is being used, and increment its number if it is."""
        while self.storyPanel.findWidget(title):
            try:
                match = re.search(r'(\s\d+)$', title)
                if match:
                    title = title[:match.start(1)] + " " + str(int(match.group(1)) + 1)
                else:
                    title += " 2"
            except: pass
        return title
    
    def importImage(self, text, title, showdialog = True):
        """Imports an image into the story as an image passage."""          
        # Check for title usage
        title = self.newTitle(title)
        
        self.storyPanel.newWidget(text = text, title = title, tags = ['Twine.image'])
        if showdialog:
            dialog = wx.MessageDialog(self, 'Image file imported successfully.\n' + \
                                      'You can include the image in your passages with this syntax:\n\n' + \
                                      '[img[' + title + ']]', 'Image added', \
                                      wx.ICON_INFORMATION | wx.OK)
            dialog.ShowModal()
        return True
        
    def importFont(self, file, showdialog = True):
        """Imports a font into the story as a font passage."""
        try:
            text, title = self.openFileAsBase64(file)

            title2 = self.newTitle(title)
            
            # Wrap in CSS @font-face declaration
            text = \
"""font[face=\"""" + title + """\"] {
    font-family: \"""" + title + """\";
}
@font-face {
    font-family: \"""" + title + """\";
    
    src: url(""" + text + """);
}"""
            
            self.storyPanel.newWidget(text = text, title = title2, tags = ['stylesheet'])
            if showdialog:
                dialog = wx.MessageDialog(self, 'Font file imported successfully.\n' + \
                                          'You can use the font in your stylesheets with this CSS attribute syntax:\n\n' + \
                                          'font-family: '+ title + ";", 'Font added', \
                                          wx.ICON_INFORMATION | wx.OK)
                dialog.ShowModal()
            return True
        except IOError:
            self.app.displayError('importing a font')
            return False
    
    def createInfoPassage(self, event = None):
        """Create, or otherwise open, one of the """
        id = event.GetId()
        title = self.storySettingsMenu.FindItemById(id).GetLabel()
        defaultText = ""
        found = False
        
        if id == self.STORYSETTINGS_TITLE:
            defaultText = self.DEFAULT_TITLE
        
        elif id == self.STORYSETTINGS_SUBTITLE:
            defaultText = "This text appears below the story's title."
        
        elif id == self.STORYSETTINGS_AUTHOR:
            defaultText = "Anonymous"
        
        elif id == self.STORYSETTINGS_MENU:
            defaultText = "This passage's text will be included in the menu for this story."
        
        elif id == self.STORYSETTINGS_INCLUDES:
            defaultText = """List the file paths of any .twee or .tws files that should be merged into this story when it's built.
 
You can also include URLs of .tws and .twee files, too."""
        
        elif id == self.STORYSETTINGS_SETTINGS:         
            # Generate a random obfuscateKey
            obfuscateKey = list('anbocpdqerfsgthuivjwkxlymz')
            shuffle(obfuscateKey)
            defaultText = """--Let the player undo moves? (on / off)
--In Sugarcane, this enables the browser's back button.
--In Jonah, this lets the player click links in previous
--passages.

Undo: on

--Let the player use bookmarks? (on / off)
--This enables the Bookmark links in Jonah and Sugarcane
--(If the player can't undo, bookmarks are always disabled.)

Bookmark: on

--Enable Javascript error alerts? (on / off)
--This interrupts the game once a Javascript error is
--raised, indicating a bug in either Twine or a script.

Errors: on

--Obfuscate the story's HTML source to prevent possible
--spoilers? (swap / off)

Obfuscate: off

--String of letter pairs to use for swap-style obfuscation

ObfuscateKey: """ + ''.join(obfuscateKey) + """

--Include the jQuery script library? (on / off)
--Individual scripts may force this on by
--containing the text 'requires jQuery'.

jQuery: off

--Include the Modernizr script library? (on / off)
--Individual scripts/stylesheets may force this on by
--containing the text 'requires Modernizr'.

Modernizr: off
"""
        
        for widget in self.storyPanel.widgets:
            if widget.passage.title == title:
                found = True
                editingWidget = widget
                break
        
        if not found:
            editingWidget = self.storyPanel.newWidget(title = title, text = defaultText)
        
        editingWidget.openEditor()
        
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
        dialog = wx.FileDialog(self, 'Build Story', self.buildDestination or os.getcwd(), "", \
                         "Web Page (*.html)|*.html", \
                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
    
        if dialog.ShowModal() == wx.ID_OK:
            self.buildDestination = dialog.GetPath()
            self.rebuild(None, displayAfter = True)
        
        dialog.Destroy()
    
    def testBuild(self, event = None, startAt = ''):
        self.rebuild(temp = True, startAt = startAt, displayAfter = True)
        
    def rebuild (self, event = None, temp = False, displayAfter = False, startAt = ''):
        """
        Builds an HTML version of the story. Pass whether to use a temp file, and/or open the file afterwards.
        """      
        try:
            # assemble our tiddlywiki and write it out
            hasstartpassage = False
            tw = TiddlyWiki()
            for widget in self.storyPanel.widgets:
                if widget.passage.title == 'StoryIncludes':
                    # Might as well suppress the warning for a StoryIncludes file
                    hasstartpassage = True
                elif not any(t in TiddlyWiki.NOINCLUDE_TAGS for t in widget.passage.tags):
                    widget.passage.pos = widget.pos
                    tw.addTiddler(widget.passage)
                    if widget.passage.title == "Start":
                        hasstartpassage = True

            # is there a Start passage?
            if hasstartpassage == False:
                self.app.displayError('building your story because there is no "Start" passage. ' + "\n" 
                                      + 'Your story will build but the web browser will not be able to run the story. ' + "\n"
                                      + 'Please add a passage with the title "Start"')

            for widget in self.storyPanel.widgets:
                if widget.passage.title == 'StoryIncludes':
                    tw = self.buildIncludes(tw, widget.passage.text.splitlines()) or tw
                    break
            
            # Decode story settings
            for widget in self.storyPanel.widgets:
                if widget.passage.title == 'StorySettings':
                    lines = widget.passage.text.splitlines()
                    for line in lines: 
                        if ':' in line:
                            (skey,svalue) = line.split(':')
                            skey = skey.strip().lower()
                            svalue = svalue.strip().lower()
                            tw.storysettings[skey] = svalue or True
                    break
            
            # Write the output file
            if temp:
                # This implicitly closes the previous test build
                if self.lastTestBuild and os.path.exists(self.lastTestBuild.name):
                    os.remove(self.lastTestBuild.name)
                path = (os.path.exists(self.buildDestination) and self.buildDestination) \
                    or (os.path.exists(self.saveDestination) and self.saveDestination) or None
                self.lastTestBuild = tempfile.NamedTemporaryFile(mode = 'w', suffix = ".html", delete = False,
                    dir = (path and os.path.dirname(path)) or None)
                self.lastTestBuild.write(tw.toHtml(self.app, self.target, startAt = startAt, defaultName = self.title).encode('utf-8'))
                self.lastTestBuild.close()
                if displayAfter: self.viewBuild(name = self.lastTestBuild.name)
            else:
                dest = open(self.buildDestination, 'w')
                dest.write(tw.toHtml(self.app, self.target, defaultName = self.title).encode('utf-8'))
                dest.close()
                if displayAfter: self.viewBuild()
        except:
            self.app.displayError('building your story')
            
    def buildIncludes(self, tw, lines):
        """
        Modify the passed TiddlyWiki object by including passages from the given files.
        """
        excludepassages = TiddlyWiki.INFO_PASSAGES
        for line in lines:
            try:
                if line.strip():
                    extension = os.path.splitext(line)[1] 
                    if extension == '.tws':
                        
                        if any(line.startswith(t) for t in ['http://', 'https://', 'ftp://']):
                            openedFile = urllib.urlopen(line)
                        else:
                            openedFile = open(line, 'r')
                        s = StoryFrame(None, app = self.app, state = pickle.load(openedFile))
                        openedFile.close()
                        
                        for widget in s.storyPanel.widgets:
                            if not any(widget.passage.title in t for t in excludepassages) and \
                            not any(t in TiddlyWiki.NOINCLUDE_TAGS for t in widget.passage.tags):
                            
                                # Check for uniqueness
                                if self.storyPanel.findWidget(widget.passage.title):
                                    # Not bothering with a Yes/No dialog here.
                                    raise Exception('A passage titled "'+ widget.passage.title + '" is already present in this story')
                                elif tw.hasTiddler(widget.passage.title):
                                    raise Exception('A passage titled "'+ widget.passage.title + '" has been included by a previous StoryIncludes file')
                                
                                tw.addTiddler(widget.passage)
                        s.Destroy()
                        
                    elif extension == '.tw' or extension == '.txt' or extension == '.twee':
                        
                        if any(line.startswith(t) for t in ['http://', 'https://', 'ftp://']):
                            openedFile = urllib.urlopen(line)
                            s = openedFile.read()
                            openedFile.close()
                            t = tempfile.NamedTemporaryFile(delete=False)
                            cleanuptempfile = True
                            t.write(s)
                            t.close()
                            filename = t.name
                        else:
                            filename = line
                            cleanuptempfile = False
                            
                        tw1 = TiddlyWiki()
                        tw1.addTweeFromFilename(filename)
                        if cleanuptempfile: os.remove(filename)
                        tiddlerkeys = tw1.tiddlers.keys()
                        for tiddlerkey in tiddlerkeys:
                            passage = tw1.tiddlers[tiddlerkey]
                            if not any(passage.title == t for t in excludepassages) and \
                            not any(t in TiddlyWiki.NOINCLUDE_TAGS for t in passage.tags):
                                tw.addTiddler(passage)
                    else:
                        raise Exception('File format not recognized')
            except:
                self.app.displayError('including the file named "' + line + '" which is referred to by the StoryIncludes passage\n')
                return None
        return tw
    
    def viewBuild (self, event = None, name = ''):
        """
        Opens the last built file in a Web browser.
        """
        path = 'file://' + urllib.pathname2url(name or self.buildDestination)
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
            twinedocdir = os.getcwd()
        else:
            twinedocdir = os.path.dirname(self.saveDestination)
        
        for widget in self.storyPanel.widgets:
            if widget.passage.title == 'StoryIncludes':
                for line in widget.passage.text.splitlines():
                    if (not line.startswith(t) for t in ['http://', 'https://', 'ftp://']):
                        pathname = os.path.join(twinedocdir, line)
                        # Include even non-existant files, in case they eventually appear
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
                           wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        
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
        multipleSelection = self.storyPanel.hasMultipleSelection()
        
        canPaste = False
        if wx.TheClipboard.Open():
            canPaste = wx.TheClipboard.IsSupported(wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT))
            wx.TheClipboard.Close()
        
        # window title
        
        if self.saveDestination == '':
            self.title = StoryFrame.DEFAULT_TITLE
        else:
            bits = os.path.splitext(self.saveDestination)
            self.title = os.path.basename(bits[0])
        
        percent = str(int(round(self.storyPanel.scale * 100)))
        dirty = ''
        if self.dirty: dirty = ' *'

        self.SetTitle(self.title + dirty + ' (' + percent + '%) ' + '- ' + self.app.NAME)
        
        if not self.menus: return
            
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
        
        # Story menu, Build menu
        
        editItem = self.menus.FindItemById(wx.ID_EDIT)
        testItem = self.menus.FindItemById(StoryFrame.BUILD_TEST_HERE)
        editItem.SetItemLabel("&Edit Passage");
        editItem.Enable(False)
        testItem.SetItemLabel("Test Play From Here");
        testItem.Enable(False)
        if hasSelection and not multipleSelection:
            widget = self.storyPanel.selectedWidget();
            editItem.SetItemLabel("Edit \"" + widget.passage.title + "\"")
            editItem.Enable(True)
            # Only allow test plays from story pasages
            if widget.passage.isStoryPassage(): 
                testItem.SetItemLabel("Test Play From \"" + widget.passage.title + "\"")
                testItem.Enable(True)
        
        editFullscreenItem = self.menus.FindItemById(StoryFrame.STORY_EDIT_FULLSCREEN)
        editFullscreenItem.Enable(hasSelection and not multipleSelection)
        
        rebuildItem = self.menus.FindItemById(StoryFrame.BUILD_REBUILD)
        rebuildItem.Enable(self.buildDestination != '')
        
        viewLastItem = self.menus.FindItemById(StoryFrame.BUILD_VIEW_LAST)
        viewLastItem.Enable(self.buildDestination != '')

        autoBuildItem = self.menus.FindItemById(StoryFrame.BUILD_AUTO_BUILD)
        autoBuildItem.Enable(self.buildDestination != '' and self.storyPanel.findWidget("StoryIncludes") != None)
        
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
    
    FILE_IMPORT_SOURCE = 101
    FILE_EXPORT_PROOF = 102
    FILE_EXPORT_SOURCE = 103
    FILE_IMPORT_HTML = 104
    
    EDIT_FIND_NEXT = 201
    
    VIEW_SNAP = 301
    VIEW_CLEANUP = 302
    VIEW_TOOLBAR = 303
    
    [STORY_NEW_PASSAGE, STORY_NEW_SCRIPT, STORY_NEW_STYLESHEET, STORY_NEW_ANNOTATION, STORY_EDIT_FULLSCREEN, STORY_STATS, \
     STORY_IMPORT_IMAGE, STORY_IMPORT_IMAGE_URL, STORY_IMPORT_FONT, STORY_FORMAT_HELP, STORYSETTINGS_START, STORYSETTINGS_TITLE, STORYSETTINGS_SUBTITLE, STORYSETTINGS_AUTHOR, \
     STORYSETTINGS_MENU, STORYSETTINGS_SETTINGS, STORYSETTINGS_INCLUDES] = range(401,418)
    
    STORY_FORMAT_BASE = 501
    
    [BUILD_TEST, BUILD_TEST_HERE, BUILD_BUILD, BUILD_REBUILD, BUILD_VIEW_LAST, BUILD_AUTO_BUILD] = range(601, 607)
    
    [HELP_MANUAL, HELP_GROUP, HELP_GITHUB, HELP_FORUM] = range(701,705)

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