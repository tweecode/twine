#!/usr/bin/env python

import sys, os, locale, re, pickle, wx
import metrics
from storyframe import StoryFrame
from prefframe import PreferenceFrame

class App (wx.App):    
    """This bootstraps our application and keeps track of preferences, etc."""
    
    NAME = 'Twine'
    VERSION = '1.3.6 (running on Python %s.%s)' % (sys.version_info[0], sys.version_info[1]) #Named attributes not available in Python 2.6
    RECENT_FILES = 10

    def __init__ (self, redirect = False):
        """Initializes the application."""
        wx.App.__init__(self, redirect = redirect)
        locale.setlocale(locale.LC_ALL, '')
        self.stories = []
        self.loadPrefs()

        # try to load our app icon under win32
        # if it doesn't work, we continue anyway

        self.icon = wx.EmptyIcon()
        
        if sys.platform == 'win32':
            try:
                self.icon = wx.Icon('icons' + os.sep + 'app.ico', wx.BITMAP_TYPE_ICO)
            except:
                pass
        
        
        # restore save location

        try:
            os.chdir(self.config.Read('savePath'))
        except:
            os.chdir(os.path.expanduser('~'))

        if not self.openOnStartup():
            if self.config.HasEntry('LastFile') \
            and os.path.exists(self.config.Read('LastFile')):
                self.open(self.config.Read('LastFile'))
            else:
                self.newStory()
        
    def newStory (self, event = None):
        """Opens a new, blank story."""
        s = StoryFrame(parent = None, app = self)
        self.stories.append(s)
        s.Show(True)
    
    def removeStory (self, story, byMenu = False):
        """Removes a story from our collection. Should be called when it closes."""
        try:
            self.stories.remove(story)
            if byMenu:
                counter = 0
                for s in self.stories: 
                    if isinstance(s, StoryFrame): 
                        counter = counter + 1 
                if counter == 0:
                    self.newStory()

        except ValueError:
            None
        
    def openDialog (self, event = None):
        """Opens a story file of the user's choice."""
        opened = False
        dialog = wx.FileDialog(None, 'Open Story', os.getcwd(), "", "Twine Story (*.tws)|*.tws", \
                               wx.OPEN | wx.FD_CHANGE_DIR)
                                                
        if dialog.ShowModal() == wx.ID_OK:
            opened = True
            self.config.Write('savePath', os.getcwd())
            self.addRecentFile(dialog.GetPath())
            self.open(dialog.GetPath())
                    
        dialog.Destroy()

    def openRecent (self, story, index):
        """Opens a recently-opened file."""
        filename = story.recentFiles.GetHistoryFile(index)
        if not os.path.exists(filename):
            self.removeRecentFile(story, index)
        else:
            self.open(filename)
            self.addRecentFile(filename)
    
    def open (self, path):
        """Opens a specific story file."""
        try:            
            openedFile = open(path, 'r')
            newStory = StoryFrame(None, app = self, state = pickle.load(openedFile))
            newStory.saveDestination = path
            self.stories.append(newStory)
            newStory.Show(True)
            self.addRecentFile(path)
            self.config.Write('LastFile', path)
            openedFile.close()
            
            # weird special case:
            # if we only had one story opened before
            # and it's pristine (e.g. no changes ever made to it),
            # then we close it after opening the file successfully
            
            if (len(self.stories) == 2) and (self.stories[0].pristine):
                self.stories[0].Destroy()
                
        except:
            self.displayError('opening your story')
    
    def openOnStartup (self):
        """
        Opens any files that were passed via argv[1:]. Returns
        whether anything was opened.
        """
        if len(sys.argv) is 1:
            return False
        
        for file in sys.argv[1:]:
            self.open(file)
            
        return True
    
    def exit (self, event = None):
        """Closes all open stories, implicitly quitting."""
        # need to make a copy of our stories list since
        # stories removing themselves will alter the list midstream
        for s in list(self.stories):
            if isinstance(s, StoryFrame):
                s.Close()
        
    def showPrefs (self, event = None):
        """Shows the preferences dialog."""
        if (not hasattr(self, 'prefFrame')):
            self.prefFrame = PreferenceFrame(self)
        else:
            try:
                self.prefFrame.Raise()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'prefFrame')
                self.showPrefs(event)           
    
    def addRecentFile (self, path):
        """Adds a path to the recent files history and updates the menus."""
        for s in self.stories:
            if isinstance(s, StoryFrame):
                s.recentFiles.AddFileToHistory(path)
                s.recentFiles.Save(self.config)

    def removeRecentFile(self, story, index):
        """Remove all missing files from the recent files history and update the menus."""
        
        def removeRecentFile_do(story, index, showdialog = True):
            filename = story.recentFiles.GetHistoryFile(index)
            story.recentFiles.RemoveFileFromHistory(index)
            story.recentFiles.Save(self.config)
            if showdialog:
                text = 'The file ' + filename + ' no longer exists.\n' + \
                       'This file has been removed from the Recent Files list.'
                dlg = wx.MessageDialog(None, text, 'Information', wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()
                return True
            else:
                return False
        showdialog = True
        for s in self.stories:
            if s != story and isinstance(s, StoryFrame):
                removeRecentFile_do(s, index, showdialog)
                showdialog = False
        removeRecentFile_do(story, index, showdialog)
                
    def verifyRecentFiles(self, story):
        done = False
        while done == False:
            for index in range(story.recentFiles.GetCount()):
                if not os.path.exists(story.recentFiles.GetHistoryFile(index)):
                    self.removeRecentFile(story, index)
                    done = False
                    break
            else:
                done = True
    
    def about (self, event = None):
        """Shows the about dialog."""
        info = wx.AboutDialogInfo()
        info.SetName(self.NAME)
        info.SetVersion(self.VERSION)
        info.SetDescription('\nA tool for creating interactive stories\nwritten by Chris Klimas\n\n1.3.6 contributors:\nEmmanuel Turner, Henry Soule, Leon Arnott, Phillip Sutton, Misty De Meo, and others.')
        info.SetCopyright('The Twee compiler and associated JavaScript files in this application are released under the GNU Public License.\n\nThe game engine is a derivative work of Jeremy Ruston\'s TiddlyWiki project and is used under the terms of its license.')
        wx.AboutBox(info)
    
    def storyFormatHelp (self, event = None):
        """Opens the online manual to the section on story formats."""
        wx.LaunchDefaultBrowser('http://gimcrackd.com/etc/doc/#basic,storyformats')
    
    def openDocs (self, event = None):
        """Opens the online manual."""
        wx.LaunchDefaultBrowser('http://gimcrackd.com/etc/doc/')
        
    def openGroup (self, event = None):
        """Opens the Google group."""
        wx.LaunchDefaultBrowser('http://groups.google.com/group/tweecode/')
        
    def openGitHub (self, event = None):
        """Opens the GitHub page."""
        wx.LaunchDefaultBrowser('https://github.com/tweecode/twine')

    def loadPrefs (self):
        """Loads user preferences into self.config, setting up defaults if none are set."""
        self.config = wx.Config('Twine')
        
        monoFont = wx.SystemSettings.GetFont(wx.SYS_ANSI_FIXED_FONT)
        
        if not self.config.HasEntry('savePath'):
            self.config.Write('savePath', os.path.expanduser('~'))
        if not self.config.HasEntry('fsTextColor'):
            self.config.Write('fsTextColor', '#afcdff')
        if not self.config.HasEntry('fsBgColor'):
            self.config.Write('fsBgColor', '#100088')
        if not self.config.HasEntry('fsFontFace'):
            self.config.Write('fsFontFace', metrics.face('mono'))
        if not self.config.HasEntry('fsFontSize'):
            self.config.WriteInt('fsFontSize', metrics.size('fsEditorBody'))
        if not self.config.HasEntry('fsLineHeight'):
            self.config.WriteInt('fsLineHeight', 120)
        if not self.config.HasEntry('windowedFontFace'):
            self.config.Write('windowedFontFace', metrics.face('mono'))
        if not self.config.HasEntry('windowedFontSize'):
            self.config.WriteInt('windowedFontSize', metrics.size('editorBody'))
        if not self.config.HasEntry('storyFrameToolbar'):
            self.config.WriteBool('storyFrameToolbar', True)
        if not self.config.HasEntry('storyPanelSnap'):
            self.config.WriteBool('storyPanelSnap', False)
        if not self.config.HasEntry('fastStoryPanel'):
            self.config.WriteBool('fastStoryPanel', False)
            
    def applyPrefs (self):
        """Asks all of our stories to update themselves based on a preference change."""
        map(lambda s: s.applyPrefs(), self.stories)

    def displayError (self, activity):
        """
        Displays an error dialog with diagnostic info. Call with what you were doing
        when the error occurred (e.g. 'saving your story', 'building your story'.)
        """
        exception = sys.exc_info()
        text = 'An error occurred while ' + activity + ' ('
        text += str(exception[1]) + ').'
        error = wx.MessageDialog(None, text, 'Error', wx.OK | wx.ICON_ERROR)
        error.ShowModal()

    def getPath (self):
        """Returns the path to the executing script or application."""
        scriptPath = os.path.realpath(sys.path[0])
        
        # OS X py2app'd apps will direct us right into the app bundle
        
        scriptPath = re.sub('[^/]+.app/.*', '', scriptPath)
        
        # Windows py2exe'd apps add an extraneous library.zip at the end
        
        scriptPath = scriptPath.replace('\\\w*.zip', '')
        return scriptPath

# start things up if we were called directly
if __name__ == "__main__":
    app = App()
    app.MainLoop()
