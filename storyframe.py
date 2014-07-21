import sys, re, os, urllib, urlparse, pickle, wx, codecs, tempfile, images, version
from wx.lib import imagebrowser
from tiddlywiki import TiddlyWiki
from storypanel import StoryPanel
from passagewidget import PassageWidget
from statisticsdialog import StatisticsDialog
from storysearchframes import StoryFindFrame, StoryReplaceFrame
from storymetadataframe import StoryMetadataFrame
from utils import isURL


class StoryFrame(wx.Frame):
    """
    A StoryFrame displays an entire story. Its main feature is an
    instance of a StoryPanel, but it also has a menu bar and toolbar.
    """

    def __init__(self, parent, app, state=None, refreshIncludes=True):
        wx.Frame.__init__(self, parent, wx.ID_ANY, title=StoryFrame.DEFAULT_TITLE, \
                          size=StoryFrame.DEFAULT_SIZE)
        self.app = app
        self.parent = parent
        self.pristine = True  # the user has not added any content to this at all
        self.dirty = False  # the user has not made unsaved changes
        self.storyFormats = {}  # list of available story formats
        self.lastTestBuild = None
        self.title = ""

        # inner state

        if state:
            self.buildDestination = state.get('buildDestination', '')
            self.saveDestination = state.get('saveDestination', '')
            self.setTarget(state.get('target', 'sugarcane').lower())
            self.metadata = state.get('metadata', {})
            self.storyPanel = StoryPanel(self, app, state=state['storyPanel'])
            self.pristine = False
        else:
            self.buildDestination = ''
            self.saveDestination = ''
            self.metadata = {}
            self.setTarget('sugarcane')
            self.storyPanel = StoryPanel(self, app)

        if refreshIncludes:
            self.storyPanel.refreshIncludedPassageList()

        # window events

        self.Bind(wx.EVT_CLOSE, self.checkClose)
        self.Bind(wx.EVT_UPDATE_UI, self.updateUI)

        # Timer for the auto build file watcher
        self.autobuildtimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.autoBuildTick, self.autobuildtimer)

        # File menu

        fileMenu = wx.Menu()

        fileMenu.Append(wx.ID_NEW, '&New Story\tCtrl-Shift-N')
        self.Bind(wx.EVT_MENU, self.app.newStory, id=wx.ID_NEW)

        fileMenu.Append(wx.ID_OPEN, '&Open Story...\tCtrl-O')
        self.Bind(wx.EVT_MENU, self.app.openDialog, id=wx.ID_OPEN)

        recentFilesMenu = wx.Menu()
        self.recentFiles = wx.FileHistory(self.app.RECENT_FILES)
        self.recentFiles.Load(self.app.config)
        self.app.verifyRecentFiles(self)
        self.recentFiles.UseMenu(recentFilesMenu)
        self.recentFiles.AddFilesToThisMenu(recentFilesMenu)
        fileMenu.AppendMenu(wx.ID_ANY, 'Open &Recent', recentFilesMenu)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 0), id=wx.ID_FILE1)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 1), id=wx.ID_FILE2)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 2), id=wx.ID_FILE3)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 3), id=wx.ID_FILE4)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 4), id=wx.ID_FILE5)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 5), id=wx.ID_FILE6)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 6), id=wx.ID_FILE7)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 7), id=wx.ID_FILE8)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 8), id=wx.ID_FILE9)
        self.Bind(wx.EVT_MENU, lambda e: self.app.openRecent(self, 9), id=wx.ID_FILE9 + 1)

        fileMenu.AppendSeparator()

        fileMenu.Append(wx.ID_SAVE, '&Save Story\tCtrl-S')
        self.Bind(wx.EVT_MENU, self.save, id=wx.ID_SAVE)

        fileMenu.Append(wx.ID_SAVEAS, 'S&ave Story As...\tCtrl-Shift-S')
        self.Bind(wx.EVT_MENU, self.saveAs, id=wx.ID_SAVEAS)

        fileMenu.Append(wx.ID_REVERT_TO_SAVED, '&Revert to Saved')
        self.Bind(wx.EVT_MENU, self.revert, id=wx.ID_REVERT_TO_SAVED)

        fileMenu.AppendSeparator()

        # Import submenu

        importMenu = wx.Menu()

        importMenu.Append(StoryFrame.FILE_IMPORT_HTML, 'Compiled &HTML File...')
        self.Bind(wx.EVT_MENU, self.importHtmlDialog, id=StoryFrame.FILE_IMPORT_HTML)
        importMenu.Append(StoryFrame.FILE_IMPORT_SOURCE, 'Twee Source &Code...')
        self.Bind(wx.EVT_MENU, self.importSourceDialog, id=StoryFrame.FILE_IMPORT_SOURCE)

        fileMenu.AppendMenu(wx.ID_ANY, '&Import', importMenu)

        # Export submenu

        exportMenu = wx.Menu()

        exportMenu.Append(StoryFrame.FILE_EXPORT_SOURCE, 'Twee Source &Code...')
        self.Bind(wx.EVT_MENU, self.exportSource, id=StoryFrame.FILE_EXPORT_SOURCE)

        exportMenu.Append(StoryFrame.FILE_EXPORT_PROOF, '&Proofing Copy...')
        self.Bind(wx.EVT_MENU, self.proof, id=StoryFrame.FILE_EXPORT_PROOF)

        fileMenu.AppendMenu(wx.ID_ANY, '&Export', exportMenu)

        fileMenu.AppendSeparator()

        fileMenu.Append(wx.ID_CLOSE, '&Close Story\tCtrl-W')
        self.Bind(wx.EVT_MENU, self.checkCloseMenu, id=wx.ID_CLOSE)

        fileMenu.Append(wx.ID_EXIT, 'E&xit Twine\tCtrl-Q')
        self.Bind(wx.EVT_MENU, lambda e: self.app.exit(), id=wx.ID_EXIT)

        # Edit menu

        editMenu = wx.Menu()

        editMenu.Append(wx.ID_UNDO, '&Undo\tCtrl-Z')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.undo(), id=wx.ID_UNDO)

        if sys.platform == 'darwin':
            shortcut = 'Ctrl-Shift-Z'
        else:
            shortcut = 'Ctrl-Y'

        editMenu.Append(wx.ID_REDO, '&Redo\t' + shortcut)
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.redo(), id=wx.ID_REDO)

        editMenu.AppendSeparator()

        editMenu.Append(wx.ID_CUT, 'Cu&t\tCtrl-X')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.cutWidgets(), id=wx.ID_CUT)

        editMenu.Append(wx.ID_COPY, '&Copy\tCtrl-C')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.copyWidgets(), id=wx.ID_COPY)

        editMenu.Append(wx.ID_PASTE, '&Paste\tCtrl-V')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.pasteWidgets(), id=wx.ID_PASTE)

        editMenu.Append(wx.ID_DELETE, '&Delete\tDel')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.removeWidgets(e, saveUndo=True), id=wx.ID_DELETE)

        editMenu.Append(wx.ID_SELECTALL, 'Select &All\tCtrl-A')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachWidget(lambda i: i.setSelected(True, exclusive=False)),
                  id=wx.ID_SELECTALL)

        editMenu.AppendSeparator()

        editMenu.Append(wx.ID_FIND, 'Find...\tCtrl-F')
        self.Bind(wx.EVT_MENU, self.showFind, id=wx.ID_FIND)

        editMenu.Append(StoryFrame.EDIT_FIND_NEXT, 'Find Next\tCtrl-G')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.findWidgetRegexp(), id=StoryFrame.EDIT_FIND_NEXT)

        if sys.platform == 'darwin':
            shortcut = 'Ctrl-Shift-H'
        else:
            shortcut = 'Ctrl-H'

        editMenu.Append(wx.ID_REPLACE, 'Replace Across Story...\t' + shortcut)
        self.Bind(wx.EVT_MENU, self.showReplace, id=wx.ID_REPLACE)

        editMenu.AppendSeparator()

        editMenu.Append(wx.ID_PREFERENCES, 'Preferences...\tCtrl-,')
        self.Bind(wx.EVT_MENU, self.app.showPrefs, id=wx.ID_PREFERENCES)

        # View menu

        viewMenu = wx.Menu()

        viewMenu.Append(wx.ID_ZOOM_IN, 'Zoom &In\t=')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom('in'), id=wx.ID_ZOOM_IN)

        viewMenu.Append(wx.ID_ZOOM_OUT, 'Zoom &Out\t-')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom('out'), id=wx.ID_ZOOM_OUT)

        viewMenu.Append(wx.ID_ZOOM_FIT, 'Zoom to &Fit\t0')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom('fit'), id=wx.ID_ZOOM_FIT)

        viewMenu.Append(wx.ID_ZOOM_100, 'Zoom &100%\t1')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.zoom(1), id=wx.ID_ZOOM_100)

        viewMenu.AppendSeparator()

        viewMenu.Append(StoryFrame.VIEW_SNAP, 'Snap to &Grid', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.toggleSnapping(), id=StoryFrame.VIEW_SNAP)

        viewMenu.Append(StoryFrame.VIEW_CLEANUP, '&Clean Up Passages')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.cleanup(), id=StoryFrame.VIEW_CLEANUP)

        viewMenu.AppendSeparator()

        viewMenu.Append(StoryFrame.VIEW_TOOLBAR, '&Toolbar', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.toggleToolbar, id=StoryFrame.VIEW_TOOLBAR)

        # Story menu

        self.storyMenu = wx.Menu()

        # New Passage submenu

        self.newPassageMenu = wx.Menu()

        self.newPassageMenu.Append(StoryFrame.STORY_NEW_PASSAGE, '&Passage\tCtrl-N')
        self.Bind(wx.EVT_MENU, self.storyPanel.newWidget, id=StoryFrame.STORY_NEW_PASSAGE)

        self.newPassageMenu.AppendSeparator()

        self.newPassageMenu.Append(StoryFrame.STORY_NEW_STYLESHEET, 'S&tylesheet')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.newWidget(text=self.storyPanel.FIRST_CSS, \
                                                                   tags=['stylesheet']),
                  id=StoryFrame.STORY_NEW_STYLESHEET)

        self.newPassageMenu.Append(StoryFrame.STORY_NEW_SCRIPT, '&Script')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.newWidget(tags=['script']), id=StoryFrame.STORY_NEW_SCRIPT)

        self.newPassageMenu.Append(StoryFrame.STORY_NEW_ANNOTATION, '&Annotation')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.newWidget(tags=['annotation']),
                  id=StoryFrame.STORY_NEW_ANNOTATION)

        self.storyMenu.AppendMenu(wx.ID_ANY, 'New', self.newPassageMenu)

        self.storyMenu.Append(wx.ID_EDIT, '&Edit Passage\tCtrl-E')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e)), id=wx.ID_EDIT)

        self.storyMenu.Append(StoryFrame.STORY_EDIT_FULLSCREEN, 'Edit in &Fullscreen\tF12')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.eachSelectedWidget(lambda w: w.openEditor(e, fullscreen=True)), \
                  id=StoryFrame.STORY_EDIT_FULLSCREEN)

        self.storyMenu.AppendSeparator()

        self.importImageMenu = wx.Menu()
        self.importImageMenu.Append(StoryFrame.STORY_IMPORT_IMAGE, 'From &File...')
        self.Bind(wx.EVT_MENU, self.importImageDialog, id=StoryFrame.STORY_IMPORT_IMAGE)
        self.importImageMenu.Append(StoryFrame.STORY_IMPORT_IMAGE_URL, 'From Web &URL...')
        self.Bind(wx.EVT_MENU, self.importImageURLDialog, id=StoryFrame.STORY_IMPORT_IMAGE_URL)

        self.storyMenu.AppendMenu(wx.ID_ANY, 'Import &Image', self.importImageMenu)

        self.storyMenu.Append(StoryFrame.STORY_IMPORT_FONT, 'Import &Font...')
        self.Bind(wx.EVT_MENU, self.importFontDialog, id=StoryFrame.STORY_IMPORT_FONT)

        self.storyMenu.AppendSeparator()

        # Story Settings submenu

        self.storySettingsMenu = wx.Menu()

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_START, 'Start')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_START)

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_TITLE, 'StoryTitle')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_TITLE)

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_SUBTITLE, 'StorySubtitle')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_SUBTITLE)

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_AUTHOR, 'StoryAuthor')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_AUTHOR)

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_MENU, 'StoryMenu')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_MENU)

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_INIT, 'StoryInit')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_INIT)

        # Separator for 'visible' passages (title, subtitle) and those that solely affect compilation
        self.storySettingsMenu.AppendSeparator()

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_SETTINGS, 'StorySettings')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_SETTINGS)

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_INCLUDES, 'StoryIncludes')
        self.Bind(wx.EVT_MENU, self.createInfoPassage, id=StoryFrame.STORYSETTINGS_INCLUDES)

        self.storySettingsMenu.AppendSeparator()

        self.storySettingsMenu.Append(StoryFrame.STORYSETTINGS_HELP, 'About Special Passages')
        self.Bind(wx.EVT_MENU, lambda e: wx.LaunchDefaultBrowser('http://twinery.org/wiki/special_passages'),
                  id=StoryFrame.STORYSETTINGS_HELP)

        self.storyMenu.AppendMenu(wx.ID_ANY, 'Special Passages', self.storySettingsMenu)

        self.storyMenu.AppendSeparator()

        self.storyMenu.Append(StoryFrame.REFRESH_INCLUDES_LINKS, 'Update StoryIncludes Links')
        self.Bind(wx.EVT_MENU, lambda e: self.storyPanel.refreshIncludedPassageList(),
                  id=StoryFrame.REFRESH_INCLUDES_LINKS)

        self.storyMenu.AppendSeparator()

        # Story Format submenu

        storyFormatMenu = wx.Menu()
        storyFormatCounter = StoryFrame.STORY_FORMAT_BASE

        for key in sorted(app.headers.keys()):
            header = app.headers[key]
            storyFormatMenu.Append(storyFormatCounter, header.label, kind=wx.ITEM_CHECK)
            self.Bind(wx.EVT_MENU, lambda e, target=key: self.setTarget(target), id=storyFormatCounter)
            self.storyFormats[storyFormatCounter] = header
            storyFormatCounter += 1

        if storyFormatCounter:
            storyFormatMenu.AppendSeparator()

        storyFormatMenu.Append(StoryFrame.STORY_FORMAT_HELP, '&About Story Formats')
        self.Bind(wx.EVT_MENU, lambda e: self.app.storyFormatHelp(), id=StoryFrame.STORY_FORMAT_HELP)

        self.storyMenu.AppendMenu(wx.ID_ANY, 'Story &Format', storyFormatMenu)

        self.storyMenu.Append(StoryFrame.STORY_METADATA, 'Story &Metadata...')
        self.Bind(wx.EVT_MENU, self.showMetadata, id=StoryFrame.STORY_METADATA)

        self.storyMenu.Append(StoryFrame.STORY_STATS, 'Story &Statistics\tCtrl-I')
        self.Bind(wx.EVT_MENU, self.stats, id=StoryFrame.STORY_STATS)

        # Build menu

        buildMenu = wx.Menu()

        buildMenu.Append(StoryFrame.BUILD_TEST, '&Test Play\tCtrl-T')
        self.Bind(wx.EVT_MENU, self.testBuild, id=StoryFrame.BUILD_TEST)

        buildMenu.Append(StoryFrame.BUILD_TEST_HERE, 'Test Play From Here\tCtrl-Shift-T')
        self.Bind(wx.EVT_MENU,
                  lambda e: self.storyPanel.eachSelectedWidget(lambda w: self.testBuild(startAt=w.passage.title)), \
                  id=StoryFrame.BUILD_TEST_HERE)

        buildMenu.Append(StoryFrame.BUILD_VERIFY, '&Verify All Passages')
        self.Bind(wx.EVT_MENU, self.verify, id=StoryFrame.BUILD_VERIFY)

        buildMenu.AppendSeparator()
        buildMenu.Append(StoryFrame.BUILD_BUILD, '&Build Story...\tCtrl-B')
        self.Bind(wx.EVT_MENU, self.build, id=StoryFrame.BUILD_BUILD)

        buildMenu.Append(StoryFrame.BUILD_REBUILD, '&Rebuild Story\tCtrl-R')
        self.Bind(wx.EVT_MENU, self.rebuild, id=StoryFrame.BUILD_REBUILD)

        buildMenu.Append(StoryFrame.BUILD_VIEW_LAST, '&Rebuild and View\tCtrl-L')
        self.Bind(wx.EVT_MENU, lambda e: self.rebuild(displayAfter=True), id=StoryFrame.BUILD_VIEW_LAST)

        buildMenu.AppendSeparator()

        self.autobuildmenuitem = buildMenu.Append(StoryFrame.BUILD_AUTO_BUILD, '&Auto Build', kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.autoBuild, self.autobuildmenuitem)
        buildMenu.Check(StoryFrame.BUILD_AUTO_BUILD, False)

        # Help menu

        helpMenu = wx.Menu()

        helpMenu.Append(StoryFrame.HELP_MANUAL, 'Twine &Wiki')
        self.Bind(wx.EVT_MENU, self.app.openDocs, id=StoryFrame.HELP_MANUAL)

        helpMenu.Append(StoryFrame.HELP_FORUM, 'Twine &Forum')
        self.Bind(wx.EVT_MENU, self.app.openForum, id=StoryFrame.HELP_FORUM)

        helpMenu.Append(StoryFrame.HELP_GITHUB, 'Twine\'s Source Code on &GitHub')
        self.Bind(wx.EVT_MENU, self.app.openGitHub, id=StoryFrame.HELP_GITHUB)

        helpMenu.AppendSeparator()

        helpMenu.Append(wx.ID_ABOUT, '&About Twine')
        self.Bind(wx.EVT_MENU, self.app.about, id=wx.ID_ABOUT)

        # add menus

        self.menus = wx.MenuBar()
        self.menus.Append(fileMenu, '&File')
        self.menus.Append(editMenu, '&Edit')
        self.menus.Append(viewMenu, '&View')
        self.menus.Append(self.storyMenu, '&Story')
        self.menus.Append(buildMenu, '&Build')
        self.menus.Append(helpMenu, '&Help')
        self.SetMenuBar(self.menus)

        # enable/disable paste menu option depending on clipboard contents

        self.clipboardMonitor = ClipboardMonitor(self.menus.FindItemById(wx.ID_PASTE).Enable)
        self.clipboardMonitor.Start(100)

        # extra shortcuts

        self.SetAcceleratorTable(wx.AcceleratorTable([ \
            (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_EDIT), \
            (wx.ACCEL_CTRL, wx.WXK_RETURN, StoryFrame.STORY_EDIT_FULLSCREEN) \
            ]))

        iconPath = self.app.iconsPath

        self.toolbar = self.CreateToolBar(style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self.toolbar.SetToolBitmapSize((StoryFrame.TOOLBAR_ICON_SIZE, StoryFrame.TOOLBAR_ICON_SIZE))

        self.toolbar.AddLabelTool(StoryFrame.STORY_NEW_PASSAGE, 'New Passage', \
                                  wx.Bitmap(iconPath + 'newpassage.png'), \
                                  shortHelp=StoryFrame.NEW_PASSAGE_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.newWidget(), id=StoryFrame.STORY_NEW_PASSAGE)

        self.toolbar.AddSeparator()

        self.toolbar.AddLabelTool(wx.ID_ZOOM_IN, 'Zoom In', \
                                  wx.Bitmap(iconPath + 'zoomin.png'), \
                                  shortHelp=StoryFrame.ZOOM_IN_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom('in'), id=wx.ID_ZOOM_IN)

        self.toolbar.AddLabelTool(wx.ID_ZOOM_OUT, 'Zoom Out', \
                                  wx.Bitmap(iconPath + 'zoomout.png'), \
                                  shortHelp=StoryFrame.ZOOM_OUT_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom('out'), id=wx.ID_ZOOM_OUT)

        self.toolbar.AddLabelTool(wx.ID_ZOOM_FIT, 'Zoom to Fit', \
                                  wx.Bitmap(iconPath + 'zoomfit.png'), \
                                  shortHelp=StoryFrame.ZOOM_FIT_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom('fit'), id=wx.ID_ZOOM_FIT)

        self.toolbar.AddLabelTool(wx.ID_ZOOM_100, 'Zoom to 100%', \
                                  wx.Bitmap(iconPath + 'zoom1.png'), \
                                  shortHelp=StoryFrame.ZOOM_ONE_TOOLTIP)
        self.Bind(wx.EVT_TOOL, lambda e: self.storyPanel.zoom(1.0), id=wx.ID_ZOOM_100)

        self.SetIcon(self.app.icon)

        if app.config.ReadBool('storyFrameToolbar'):
            self.showToolbar = True
            self.toolbar.Realize()
        else:
            self.showToolbar = False
            self.toolbar.Realize()
            self.toolbar.Hide()

    def revert(self, event=None):
        """Reverts to the last saved version of the story file."""
        bits = os.path.splitext(self.saveDestination)
        title = '"' + os.path.basename(bits[0]) + '"'
        if title == '""': title = 'your story'

        message = 'Revert to the last saved version of ' + title + '?'
        dialog = wx.MessageDialog(self, message, 'Revert to Saved', wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)

        if dialog.ShowModal() == wx.ID_YES:
            self.Destroy()
            self.app.open(self.saveDestination)
            self.dirty = False
            self.checkClose(None)

    def checkClose(self, event):
        self.checkCloseDo(event, byMenu=False)

    def checkCloseMenu(self, event):
        self.checkCloseDo(event, byMenu=True)

    def checkCloseDo(self, event, byMenu):
        """
        If this instance's dirty flag is set, asks the user if they want to save the changes.
        """

        if self.dirty:
            bits = os.path.splitext(self.saveDestination)
            title = '"' + os.path.basename(bits[0]) + '"'
            if title == '""': title = 'your story'

            message = 'Do you want to save the changes to ' + title + ' before closing?'
            dialog = wx.MessageDialog(self, message, 'Unsaved Changes', \
                                      wx.ICON_WARNING | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT)
            result = dialog.ShowModal()
            if result == wx.ID_CANCEL:
                event.Veto()
                return
            elif result == wx.ID_NO:
                self.dirty = False
            else:
                self.save(None)
                if self.dirty:
                    event.Veto()
                    return

        # ask all our widgets to close any editor windows

        for w in list(self.storyPanel.widgetDict.itervalues()):
            if isinstance(w, PassageWidget):
                w.closeEditor()

        if self.lastTestBuild and os.path.exists(self.lastTestBuild.name):
            try:
                os.remove(self.lastTestBuild.name)
            except OSError, ex:
                print >> sys.stderr, 'Failed to remove lastest test build:', ex
        self.lastTestBuild = None

        self.app.removeStory(self, byMenu)
        if event is not None:
            event.Skip()
        self.Destroy()

    def saveAs(self, event=None):
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

    def exportSource(self, event=None):
        """Asks the user to choose a file to export source to, then exports the wiki."""
        dialog = wx.FileDialog(self, 'Export Source Code', os.getcwd(), "", \
                               'Twee File (*.twee;* .tw; *.txt)|*.twee;*.tw;*.txt|All Files (*.*)|*.*',
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            try:
                path = dialog.GetPath()
                tw = TiddlyWiki()

                for widget in self.storyPanel.widgetDict.itervalues(): tw.addTiddler(widget.passage)
                dest = codecs.open(path, 'w', 'utf-8-sig', 'replace')
                order = [widget.passage.title for widget in self.storyPanel.sortedWidgets()]
                dest.write(tw.toTwee(order))
                dest.close()
            except:
                self.app.displayError('exporting your source code')

        dialog.Destroy()

    def importHtmlDialog(self, event=None):
        """Asks the user to choose a file to import HTML tiddlers from, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import From Compiled HTML', os.getcwd(), '', \
                               'HTML Twine game (*.html;* .htm; *.txt)|*.html;*.htm;*.txt|All Files (*.*)|*.*',
                               wx.FD_OPEN | wx.FD_CHANGE_DIR)

        if dialog.ShowModal() == wx.ID_OK:
            self.importHtml(dialog.GetPath())

    def importHtml(self, path):
        """Imports the tiddler objects in a HTML file into the story."""
        self.importSource(path, True)

    def importSourceDialog(self, event=None):
        """Asks the user to choose a file to import source from, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import Source Code', os.getcwd(), '', \
                               'Twee File (*.twee;* .tw; *.txt)|*.twee;*.tw;*.txt|All Files (*.*)|*.*',
                               wx.FD_OPEN | wx.FD_CHANGE_DIR)

        if dialog.ShowModal() == wx.ID_OK:
            self.importSource(dialog.GetPath())

    def importSource(self, path, html=False):
        """Imports the tiddler objects in a Twee file into the story."""

        try:
            # have a TiddlyWiki object parse it for us
            tw = TiddlyWiki()
            if html:
                tw.addHtmlFromFilename(path)
            else:
                tw.addTweeFromFilename(path)

            # add passages for each of the tiddlers the TiddlyWiki saw
            if len(tw.tiddlers):
                removedWidgets = []
                skippedTitles = set()

                # Ask user how to resolve any passage title conflicts
                for title in tw.tiddlers.viewkeys() & self.storyPanel.widgetDict.viewkeys():

                    dialog = wx.MessageDialog(self, 'There is already a passage titled "' + title \
                                                + '" in this story. Replace it with the imported passage?',
                                                'Passage Title Conflict', \
                                                wx.ICON_WARNING | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT)
                    check = dialog.ShowModal()
                    if check == wx.ID_YES:
                        removedWidgets.append(title)
                    elif check == wx.ID_CANCEL:
                        return
                    elif check == wx.ID_NO:
                        skippedTitles.add(title)

                # Remove widgets elected to be replaced
                for title in removedWidgets:
                    self.storyPanel.removeWidget(title)

                # Insert widgets now
                lastpos = [0, 0]
                addedWidgets = []
                for tiddler in tw.tiddlers.itervalues():
                    if tiddler.title in skippedTitles:
                        continue
                    new = self.storyPanel.newWidget(title=tiddler.title, tags=tiddler.tags,
                                                    text=tiddler.text, quietly=True,
                                                    pos=tiddler.pos if tiddler.pos else lastpos)
                    lastpos = new.pos
                    addedWidgets.append(new)

                self.setDirty(True, 'Import')
                for widget in addedWidgets:
                    widget.clearPaintCache()
            else:
                if html:
                    what = "compiled HTML"
                else:
                    what = "Twee source"
                dialog = wx.MessageDialog(self, 'No passages were found in this file. Make sure ' + \
                                          'this is a ' + what + ' file.', 'No Passages Found', \
                                          wx.ICON_INFORMATION | wx.OK)
                dialog.ShowModal()
        except:
            self.app.displayError('importing')

    def importImageURL(self, url, showdialog=True):
        """
        Downloads the image file from the url and creates a passage.
        Returns the resulting passage name, or None
        """
        try:
            # Download the file
            urlfile = urllib.urlopen(url)
            path = urlparse.urlsplit(url)[2]
            title = os.path.splitext(os.path.basename(path))[0]
            file = urlfile.read().encode('base64').replace('\n', '')

            # Now that the file's read, check the info
            maintype = urlfile.info().getmaintype()
            if maintype != "image":
                self.app.displayError("importing from the web: The server served " + maintype + " instead of an image",
                                      stacktrace=False)
                return None
            # Convert the file
            mimeType = urlfile.info().gettype()
            urlfile.close()
            text = "data:" + mimeType + ";base64," + file
            return self.finishImportImage(text, title, showdialog=showdialog)
        except:
            self.app.displayError('importing from the web')
            return None

    def importImageURLDialog(self, event=None):
        dialog = wx.TextEntryDialog(self, "Enter the image URL (GIFs, JPEGs, PNGs, SVGs and WebPs only)",
                                    "Import Image from Web", "http://")
        if dialog.ShowModal() == wx.ID_OK:
            self.importImageURL(dialog.GetValue())

    def importImageFile(self, file, replace=None, showdialog=True):
        """
        Perform the file I/O to import an image file, then add it as an image passage.
        Returns the name of the resulting passage, or None
        """
        try:
            if not replace:
                text, title = self.openFileAsBase64(file)
                return self.finishImportImage(text, title, showdialog=showdialog)
            else:
                replace.passage.text = self.openFileAsBase64(file)[0]
                replace.updateBitmap()
                return replace.passage.title
        except IOError:
            self.app.displayError('importing an image')
            return None

    def importImageDialog(self, event=None, useImageDialog=False, replace=None):
        """Asks the user to choose an image file to import, then imports into the current story.
           replace is a Tiddler, if any, that will be replaced by the image."""
        # Use the wxPython image browser?
        if useImageDialog:
            dialog = imagebrowser.ImageDialog(self, os.getcwd())
            dialog.ChangeFileTypes([('Web Image File', '*.(gif|jpg|jpeg|png|webp|svg)')])
            dialog.ResetFiles()
        else:
            dialog = wx.FileDialog(self, 'Import Image File', os.getcwd(), '', \
                                   'Web Image File|*.gif;*.jpg;*.jpeg;*.png;*.webp;*.svg|All Files (*.*)|*.*',
                                   wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            file = dialog.GetFile() if useImageDialog else dialog.GetPath()
            self.importImageFile(file, replace)

    def importFontDialog(self, event=None):
        """Asks the user to choose a font file to import, then imports into the current story."""
        dialog = wx.FileDialog(self, 'Import Font File', os.getcwd(), '', \
                               'Web Font File (.ttf, .otf, .woff, .svg)|*.ttf;*.otf;*.woff;*.svg|All Files (*.*)|*.*',
                               wx.FD_OPEN | wx.FD_CHANGE_DIR)
        if dialog.ShowModal() == wx.ID_OK:
            self.importFont(dialog.GetPath())

    def openFileAsBase64(self, file):
        """Opens a file and returns its base64 representation, expressed as a Data URI with MIME type"""
        file64 = open(file, 'rb').read().encode('base64').replace('\n', '')
        title, mimeType = os.path.splitext(os.path.basename(file))
        return (images.addURIPrefix(file64, mimeType[1:]), title)

    def newTitle(self, title):
        """ Check if a title is being used, and increment its number if it is."""
        while self.storyPanel.passageExists(title):
            try:
                match = re.search(r'(\s\d+)$', title)
                if match:
                    title = title[:match.start(1)] + " " + str(int(match.group(1)) + 1)
                else:
                    title += " 2"
            except:
                pass
        return title

    def finishImportImage(self, text, title, showdialog=True):
        """Imports an image into the story as an image passage."""
        # Check for title usage
        title = self.newTitle(title)

        self.storyPanel.newWidget(text=text, title=title, tags=['Twine.image'])
        if showdialog:
            dialog = wx.MessageDialog(self, 'Image file imported successfully.\n' + \
                                      'You can include the image in your passages with this syntax:\n\n' + \
                                      '[img[' + title + ']]', 'Image added', \
                                      wx.ICON_INFORMATION | wx.OK)
            dialog.ShowModal()
        return title

    def importFont(self, file, showdialog=True):
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

            self.storyPanel.newWidget(text=text, title=title2, tags=['stylesheet'])
            if showdialog:
                dialog = wx.MessageDialog(self, 'Font file imported successfully.\n' + \
                                          'You can use the font in your stylesheets with this CSS attribute syntax:\n\n' + \
                                          'font-family: ' + title + ";", 'Font added', \
                                          wx.ICON_INFORMATION | wx.OK)
                dialog.ShowModal()
            return True
        except IOError:
            self.app.displayError('importing a font')
            return False

    def defaultTextForPassage(self, title):
        if title == 'Start':
            return "Your story will display this passage first. Edit it by double clicking it."

        elif title == 'StoryTitle':
            return self.DEFAULT_TITLE

        elif title == 'StorySubtitle':
            return "This text appears below the story's title."

        elif title == 'StoryAuthor':
            return "Anonymous"

        elif title == 'StoryMenu':
            return "This passage's text will be included in the menu for this story."

        elif title == 'StoryInit':
            return """/% Place your story's setup code in this passage.
Any macros in this passage will be run before the Start passage (or any passage you wish to Test Play) is run. %/
"""

        elif title == 'StoryIncludes':
            return """List the file paths of any .twee or .tws files that should be merged into this story when it's built.

You can also include URLs of .tws and .twee files, too.
"""

        else:
            return ""

    def createInfoPassage(self, event):
        """Open an editor for a special passage; create it if it doesn't exist yet."""

        id = event.GetId()
        title = self.storySettingsMenu.FindItemById(id).GetLabel()

        # What to do about StoryIncludes files?
        editingWidget = self.storyPanel.findWidget(title)
        if editingWidget is None:
            editingWidget = self.storyPanel.newWidget(title=title, text=self.defaultTextForPassage(title))

        editingWidget.openEditor()

    def save(self, event=None):
        if self.saveDestination == '':
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

    def verify(self, event=None):
        """Runs the syntax checks on all passages."""
        noprobs = True
        for widget in self.storyPanel.widgetDict.itervalues():
            result = widget.verifyPassage(self)
            if result == -1:
                break
            elif result > 0:
                noprobs = False
        if noprobs:
            wx.MessageDialog(self, "No obvious problems found in " + str(
                len(self.storyPanel.widgetDict)) + " passage" + (
                                 "s." if len(self.storyPanel.widgetDict) > 1 else ".") \
                             + "\n\n(There may still be problems when the story is played, of course.)",
                             "Verify All Passages", wx.ICON_INFORMATION).ShowModal()

    def build(self, event=None):
        """Asks the user to choose a location to save a compiled story, then passed control to rebuild()."""
        path, filename = os.path.split(self.buildDestination)
        dialog = wx.FileDialog(self, 'Build Story', path or os.getcwd(), filename, \
                               "Web Page (*.html)|*.html", \
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR)

        if dialog.ShowModal() == wx.ID_OK:
            self.buildDestination = dialog.GetPath()
            self.rebuild(None, displayAfter=True)

        dialog.Destroy()

    def testBuild(self, event=None, startAt=''):
        self.rebuild(temp=True, startAt=startAt, displayAfter=True)

    def rebuild(self, event=None, temp=False, displayAfter=False, startAt=''):
        """
        Builds an HTML version of the story. Pass whether to use a temp file, and/or open the file afterwards.
        """
        try:
            # assemble our tiddlywiki and write it out
            hasstartpassage = False
            tw = TiddlyWiki()
            for widget in self.storyPanel.widgetDict.itervalues():
                if widget.passage.title == 'StoryIncludes':

                    def callback(passage, tw=tw):
                        if passage.title == 'StoryIncludes':
                            return
                        # Check for uniqueness
                        elif passage.title in self.storyPanel.widgetDict:
                            # Not bothering with a Yes/No dialog here.
                            raise Exception('A passage titled "' + passage.title + '" is already present in this story')
                        elif tw.hasTiddler(passage.title):
                            raise Exception(
                                'A passage titled "' + passage.title + '" has been included by a previous StoryIncludes file')

                        tw.addTiddler(passage)
                        self.storyPanel.addIncludedPassage(passage.title)

                    self.readIncludes(widget.passage.text.splitlines(), callback)
                    # Might as well suppress the warning for a StoryIncludes file
                    hasstartpassage = True

                elif TiddlyWiki.NOINCLUDE_TAGS.isdisjoint(widget.passage.tags):
                    widget.passage.pos = widget.pos
                    tw.addTiddler(widget.passage)
                    if widget.passage.title == "Start":
                        hasstartpassage = True

            # is there a Start passage?
            if hasstartpassage == False:
                self.app.displayError('building your story because there is no "Start" passage. ' + "\n"
                                      + 'Your story will build but the web browser will not be able to run the story. ' + "\n"
                                      + 'Please add a passage with the title "Start"')

            widget = self.storyPanel.widgetDict.get('StorySettings')
            if widget is not None:
                lines = widget.passage.text.splitlines()
                for line in lines:
                    if ':' in line:
                        (skey, svalue) = line.split(':')
                        skey = skey.strip().lower()
                        svalue = svalue.strip()
                        tw.storysettings[skey] = svalue

            # Write the output file
            header = self.app.headers.get(self.target)
            metadata = self.metadata
            if temp:
                # This implicitly closes the previous test build
                if self.lastTestBuild and os.path.exists(self.lastTestBuild.name):
                    os.remove(self.lastTestBuild.name)
                path = (os.path.exists(self.buildDestination) and self.buildDestination) \
                       or (os.path.exists(self.saveDestination) and self.saveDestination) or None
                html = tw.toHtml(self.app, header, startAt=startAt, defaultName=self.title, metadata=metadata)
                if html:
                    self.lastTestBuild = tempfile.NamedTemporaryFile(mode='wb', suffix=".html", delete=False,
                                                                     dir=(path and os.path.dirname(path)) or None)

                    self.lastTestBuild.write(html.encode('utf-8-sig'))
                    self.lastTestBuild.close()
                    if displayAfter: self.viewBuild(name=self.lastTestBuild.name)
            else:
                dest = open(self.buildDestination, 'wb')
                dest.write(tw.toHtml(self.app, header, defaultName=self.title, metadata=metadata).encode('utf-8-sig'))
                dest.close()
                if displayAfter: self.viewBuild()
        except:
            self.app.displayError('building your story')

    def getLocalDir(self):
        dir = (self.saveDestination != '' and os.path.dirname(self.saveDestination)) or None
        if not (dir and os.path.isdir(dir)):
            dir = os.getcwd()
        return dir

    def readIncludes(self, lines, callback, silent=False):
        """
        Examines all of the source files included via StoryIncludes, and performs a callback on each passage found.

        callback is a function that takes 1 Tiddler object.
        """
        twinedocdir = self.getLocalDir()

        excludetags = TiddlyWiki.NOINCLUDE_TAGS
        self.storyPanel.clearIncludedPassages()
        for line in lines:
            try:
                if line.strip():

                    extension = os.path.splitext(line)[1]

                    if extension not in ['.tws', '.tw', '.txt', '.twee']:
                        raise Exception('File format not recognized')

                    if isURL(line):
                        openedFile = urllib.urlopen(line)
                    else:
                        openedFile = open(os.path.join(twinedocdir, line), 'r')

                    if extension == '.tws':
                        s = StoryFrame(None, app=self.app, state=pickle.load(openedFile), refreshIncludes=False)
                        openedFile.close()

                        for widget in s.storyPanel.widgetDict.itervalues():
                            if excludetags.isdisjoint(widget.passage.tags):
                                callback(widget.passage)
                        s.Destroy()

                    else:
                        s = openedFile.read()
                        openedFile.close()

                        tw1 = TiddlyWiki()
                        tw1.addTwee(s)
                        tiddlerkeys = tw1.tiddlers.keys()
                        for tiddlerkey in tiddlerkeys:
                            passage = tw1.tiddlers[tiddlerkey]
                            if excludetags.isdisjoint(passage.tags):
                                callback(passage)

            except:
                if not silent:
                    self.app.displayError(
                        'reading the file named "' + line + '" which is referred to by the StoryIncludes passage',
                        stacktrace=False)

    def viewBuild(self, event=None, name=''):
        """
        Opens the last built file in a Web browser.
        """
        path = u'file://' + urllib.pathname2url((name or self.buildDestination).encode('utf-8'))
        path = path.replace('file://///', 'file:///')
        wx.LaunchDefaultBrowser(path)

    def autoBuild(self, event=None):
        """
        Toggles the autobuild feature
        """
        if self.autobuildmenuitem.IsChecked():
            self.autobuildtimer.Start(5000)
            self.autoBuildStart()
        else:
            self.autobuildtimer.Stop()

    def autoBuildTick(self, event=None):
        """
        Called whenever the autobuild timer checks up on things
        """
        for pathname, oldmtime in self.autobuildfiles.iteritems():
            newmtime = os.stat(pathname).st_mtime
            if newmtime != oldmtime:
                # print "Auto rebuild triggered by: ", pathname
                self.autobuildfiles[pathname] = newmtime
                self.rebuild()
                break

    def autoBuildStart(self):
        self.autobuildfiles = {}
        if self.saveDestination == '':
            twinedocdir = os.getcwd()
        else:
            twinedocdir = os.path.dirname(self.saveDestination)

        widget = self.storyPanel.widgetDict.get('StoryIncludes')
        if widget is not None:
            for line in widget.passage.text.splitlines():
                if not isURL(line):
                    pathname = os.path.join(twinedocdir, line)
                    # Include even non-existant files, in case they eventually appear
                    mtime = os.stat(pathname).st_mtime
                    self.autobuildfiles[pathname] = mtime

    def stats(self, event=None):
        """
        Displays a StatisticsDialog for this frame.
        """

        statFrame = StatisticsDialog(parent=self, storyPanel=self.storyPanel, app=self.app)
        statFrame.ShowModal()

    def showMetadata(self, event=None):
        """
        Shows a StoryMetadataFrame for this frame.
        """

        if not hasattr(self, 'metadataFrame'):
            self.metadataFrame = StoryMetadataFrame(parent=self, app=self.app)
        else:
            try:
                self.metadataFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'metadataFrame')
                self.showMetadata(event)

    def showFind(self, event=None):
        """
        Shows a StoryFindFrame for this frame.
        """

        if not hasattr(self, 'findFrame'):
            self.findFrame = StoryFindFrame(self.storyPanel, self.app)
        else:
            try:
                self.findFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'findFrame')
                self.showFind(event)

    def showReplace(self, event=None):
        """
        Shows a StoryReplaceFrame for this frame.
        """
        if not hasattr(self, 'replaceFrame'):
            self.replaceFrame = StoryReplaceFrame(self.storyPanel, self.app)
        else:
            try:
                self.replaceFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'replaceFrame')
                self.showReplace(event)

    def proof(self, event=None):
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
                # Exclude images from RTF, they appear as large unreadable blobs of base64 text.
                if 'Twine.image' not in widget.passage.tags:
                    tw.addTiddler(widget.passage)

            order = [widget.passage.title for widget in self.storyPanel.sortedWidgets()]
            dest.write(tw.toRtf(order))
            dest.close()
        except:
            self.app.displayError('building a proofing copy of your story')

    def setTarget(self, target):
        self.target = target
        self.header = self.app.headers[target]

    def updateUI(self, event=None):
        """Adjusts menu items to reflect the current state."""

        selections = self.storyPanel.hasMultipleSelection()

        # window title
        if self.saveDestination == '':
            self.title = StoryFrame.DEFAULT_TITLE
        else:
            bits = os.path.splitext(self.saveDestination)
            self.title = os.path.basename(bits[0])

        percent = str(int(round(self.storyPanel.scale * 100)))
        dirtyText = '' if not self.dirty else ' *'
        titleText = self.title + dirtyText + ' (' + percent + '%) ' + '- ' + self.app.NAME + ' ' + version.versionString
        if not self.GetTitle() == titleText:
            self.SetTitle(titleText)

        if not self.menus:
            return

        # File menu

        self.menus.FindItemById(wx.ID_REVERT_TO_SAVED).Enable(self.saveDestination != '' and self.dirty)

        # Edit menu
        undoItem = self.menus.FindItemById(wx.ID_UNDO)
        undoItem.Enable(self.storyPanel.canUndo())
        undoItem.SetText('Undo ' + self.storyPanel.undoAction() + '\tCtrl-Z'
                         if self.storyPanel.canUndo() else "Can't Undo\tCtrl-Z")

        redoItem = self.menus.FindItemById(wx.ID_REDO)
        redoItem .Enable(self.storyPanel.canRedo())
        redoItem .SetText('Redo ' + self.storyPanel.redoAction() + '\tCtrl-Y'
                                  if self.storyPanel.canRedo() else "Can't Redo\tCtrl-Y")

        for item in wx.ID_CUT, wx.ID_COPY, wx.ID_DELETE:
            self.menus.FindItemById(item).Enable(selections > 0)

        self.menus.FindItemById(StoryFrame.EDIT_FIND_NEXT).Enable(self.storyPanel.lastSearchRegexp is not None)

        # View menu
        self.menus.FindItemById(StoryFrame.VIEW_TOOLBAR).Check(self.showToolbar)
        self.menus.FindItemById(StoryFrame.VIEW_SNAP).Check(self.storyPanel.snapping)

        # Story menu, Build menu

        editItem = self.menus.FindItemById(wx.ID_EDIT)
        testItem = self.menus.FindItemById(StoryFrame.BUILD_TEST_HERE)
        if selections == 1:
            widget = self.storyPanel.selectedWidget()
            editItem.SetItemLabel("Edit \"" + widget.passage.title + "\"")
            editItem.Enable(True)
            # Only allow test plays from story passages
            testItem.SetItemLabel("Test Play From \"" + widget.passage.title + "\""
                                  if widget.passage.isStoryPassage() else "Test Play From Here")
            testItem.Enable(widget.passage.isStoryPassage())
        else:
            editItem.SetItemLabel("&Edit Passage")
            editItem.Enable(False)
            testItem.SetItemLabel("Test Play From Here")
            testItem.Enable(False)

        self.menus.FindItemById(StoryFrame.STORY_EDIT_FULLSCREEN).Enable(selections == 1)
        self.menus.FindItemById(StoryFrame.BUILD_REBUILD).Enable(self.buildDestination != '')
        self.menus.FindItemById(StoryFrame.BUILD_VIEW_LAST).Enable(self.buildDestination != '')

        hasStoryIncludes = self.buildDestination != '' and 'StoryIncludes' in self.storyPanel.widgetDict
        self.autobuildmenuitem.Enable(hasStoryIncludes)
        self.menus.FindItemById(StoryFrame.REFRESH_INCLUDES_LINKS).Enable(hasStoryIncludes)

        # Story format submenu
        for key in self.storyFormats:
            self.menus.FindItemById(key).Check(self.target == self.storyFormats[key].id)

    def toggleToolbar(self, event=None):
        """Toggles the toolbar onscreen."""
        if self.showToolbar:
            self.showToolbar = False
            self.toolbar.Hide()
            self.app.config.WriteBool('storyFrameToolbar', False)
        else:
            self.showToolbar = True
            self.toolbar.Show()
            self.app.config.WriteBool('storyFrameToolbar', True)
        self.SendSizeEvent()

    def setDirty(self, value, action=None):
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

    def applyPrefs(self):
        """Passes on the apply message to child widgets."""
        self.storyPanel.eachWidget(lambda w: w.applyPrefs())
        self.storyPanel.Refresh()

    def serialize(self):
        """Returns a dictionary of state suitable for pickling."""
        return {'target': self.target, 'buildDestination': self.buildDestination, \
                'saveDestination': self.saveDestination, \
                'storyPanel': self.storyPanel.serialize(),
                'metadata': self.metadata,
        }

    def serialize_noprivate(self, dest):
        """Returns a dictionary of state suitable for pickling."""
        return {'target': self.target, 'buildDestination': '', \
                'saveDestination': dest, \
                'storyPanel': self.storyPanel.serialize_noprivate(),
                'metadata': self.metadata,
        }

    def __repr__(self):
        return "<StoryFrame '" + self.saveDestination + "'>"

    def getHeader(self):
        """Returns the current selected target header for this Story Frame."""
        return self.header

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

    [STORY_NEW_PASSAGE, STORY_NEW_SCRIPT, STORY_NEW_STYLESHEET, STORY_NEW_ANNOTATION, STORY_EDIT_FULLSCREEN,
     STORY_STATS, STORY_METADATA, \
     STORY_IMPORT_IMAGE, STORY_IMPORT_IMAGE_URL, STORY_IMPORT_FONT, STORY_FORMAT_HELP, STORYSETTINGS_START,
     STORYSETTINGS_TITLE, STORYSETTINGS_SUBTITLE, STORYSETTINGS_AUTHOR, \
     STORYSETTINGS_MENU, STORYSETTINGS_SETTINGS, STORYSETTINGS_INCLUDES, STORYSETTINGS_INIT, STORYSETTINGS_HELP,
     REFRESH_INCLUDES_LINKS] = range(401, 422)

    STORY_FORMAT_BASE = 501

    [BUILD_VERIFY, BUILD_TEST, BUILD_TEST_HERE, BUILD_BUILD, BUILD_REBUILD, BUILD_VIEW_LAST, BUILD_AUTO_BUILD] = range(
        601, 608)

    [HELP_MANUAL, HELP_GROUP, HELP_GITHUB, HELP_FORUM] = range(701, 705)

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


class ClipboardMonitor(wx.Timer):
    """
    Monitors the clipboard and notifies a callback when the format of the contents
    changes from or to Twine passage data.
    """

    def __init__(self, callback):
        wx.Timer.__init__(self)
        self.callback = callback
        self.dataFormat = wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT)
        self.state = None

    def Notify(self, *args, **kwargs):
        if wx.TheClipboard.Open():
            newState = wx.TheClipboard.IsSupported(self.dataFormat)
            wx.TheClipboard.Close()
            if newState != self.state:
                self.state = newState
                self.callback(newState)
