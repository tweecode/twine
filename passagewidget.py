#!/usr/bin/env python

#
# PassageWidget
# A PassageWidget is a box standing in for a proxy for a single
# passage in a story. Users can drag them around, double-click
# to open a PassageFrame, and so on.
#
# This must have a StoryPanel as its parent.
#
# See the comments on StoryPanel for more information on the
# coordinate systems are used here. In general, you should
# always pass methods logical coordinates, and expect back
# logical coordinates. Use StoryPanel.toPixels() to convert.
#

import os, copy, math, re, wx, storypanel, tiddlywiki
import metrics
from passageframe import PassageFrame

class PassageWidget:
    
    def __init__ (self, parent, app, id = wx.ID_ANY, pos = (0, 0), title = '', text = '', state = None):
        # inner state
        
        self.parent = parent
        self.app = app
        self.dimmed = False
        self.brokenEmblem = wx.Bitmap(self.app.getPath() + os.sep + 'icons' + os.sep + 'brokenemblem.png')
        pos = list(pos)
        
        if state:
            self.passage = state['passage']
            self.pos = state['pos']
            self.selected = state['selected']
        else:
            self.passage = tiddlywiki.Tiddler('')
            self.passage.title = title
            self.passage.text = text
            self.selected = False
            self.pos = list(pos)
            self.findSpace()
            
    def getSize (self):
        """Returns this instance's logical size."""
        return (PassageWidget.SIZE, PassageWidget.SIZE)
            
    def getCenter (self):
        """Returns this instance's center in logical coordinates."""
        pos = list(self.pos)
        pos[0] += self.getSize()[0] / 2
        pos[1] += self.getSize()[1] / 2
        return pos

    def getLogicalRect (self):
        """Returns this instance's rectangle in logical coordinates."""
        return wx.Rect(self.pos[0], self.pos[1], PassageWidget.SIZE, PassageWidget.SIZE)

    def getPixelRect (self):
        """Returns this instance's rectangle onscreen."""
        origin = self.parent.toPixels(self.pos)
        size = self.parent.toPixels((PassageWidget.SIZE, -1), scaleOnly = True)[0]
        return wx.Rect(origin[0], origin[1], size, size)
     
    def offset (self, x = 0, y = 0):
        """Offsets this widget's position by logical coordinates."""
        self.pos = list(self.pos)
        self.pos[0] += x
        self.pos[1] += y
 
    def findSpace (self):
        """Moves this widget so it doesn't overlap any others."""        
        originalX = self.pos[0]
        
        while self.intersectsAny():
            self.pos[0] += self.parent.GRID_SPACING 
            rightEdge = self.pos[0] + PassageWidget.SIZE
            maxWidth = self.parent.toLogical((self.parent.GetSize().width - self.parent.INSET[0], -1), \
                                             scaleOnly = True)[0]
            if rightEdge > maxWidth:
                self.pos[0] = 10
                self.pos[1] += self.parent.GRID_SPACING

    def containsRegexp (self, regexp, flags):
        """
        Returns whether this widget's passage contains a regexp.
        """
        return (re.search(regexp, self.passage.title, flags) != None \
                or re.search(regexp, self.passage.text, flags) != None)
        
    def replaceRegexp (self, findRegexp, replaceRegexp, flags):
        """
        Performs a regexp replace in this widget's passage title and
        body text. Returns the number of replacements actually made.
        """
        compiledRegexp = re.compile(findRegexp, flags)
        titleReps = textReps = 0
        
        self.passage.title, titleReps = re.subn(compiledRegexp, replaceRegexp, self.passage.title)
        self.passage.text, textReps = re.subn(compiledRegexp, replaceRegexp, self.passage.text)
            
        return titleReps + textReps
      
    def getBrokenLinks (self):
        """Returns a list of broken links in this widget."""
        brokens = []
        for link in self.passage.links():
            if not self.parent.findWidget(link): brokens.append(link)
        return brokens
                 
    def setSelected (self, value, exclusive = True):
        """
        Sets whether this widget should be selected. Pass a false value for
        exclusive to prevent other widgets from being deselected.
        """        
        if (exclusive):
            self.parent.eachWidget(lambda i: i.setSelected(False, False))
        
        old = self.selected
        self.selected = value
        if self.selected != old: self.parent.Refresh(True, self.getPixelRect())
        
    def setDimmed (self, value):
        """Sets whether this widget should be dimmed."""
        self.dimmed = value

    def openContextMenu (self, event):
        """Opens a contextual menu at the event position given."""
        self.parent.PopupMenu(PassageWidgetContext(self), event.GetPosition())
        
    def openEditor (self, event = None, fullscreen = False):
        """Opens a PassageFrame to edit this passage."""
        if (not hasattr(self, 'passageFrame')):
            self.passageFrame = PassageFrame(None, self, self.app)
            if fullscreen: self.passageFrame.openFullscreen()
        else:
            try:
                self.passageFrame.Raise()
                if fullscreen: self.passageFrame.openFullscreen()
            except wx._core.PyDeadObjectError:
                # user closed the frame, so we need to recreate it
                delattr(self, 'passageFrame')
                self.openEditor(event, fullscreen)
                
    def closeEditor (self, event = None):
        """Closes the PassageFrame associated with this, if it exists."""
        try: self.passageFrame.closeFullscreen()
        except: pass
        try: self.passageFrame.Destroy()
        except: pass
        
    def checkDelete (self):
        """Warns the user about deleting this passage if links exist to it."""
        linked = False
        for widget in self.parent.widgets:
            if self.passage.title in widget.passage.links():
                linked = True
                break
          
        if linked:
            message = 'Are you sure you want to delete "' + self.passage.title + '"?' + \
                      ' Links to it from other passages will become broken.'
            dialog = wx.MessageDialog(self.parent, message, 'Delete Passage', \
                                      wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
            return dialog.ShowModal() == wx.ID_YES
                
        return True

    def intersectsAny (self):
        """Returns whether this widget intersects any other in the same StoryPanel."""
        intersects = False
        
        # we do this manually so we don't have to go through all of them
        
        for widget in self.parent.widgets:
            if (widget != self) and (self.intersects(widget)):
                intersects = True
                break

        return intersects

    def intersects (self, other):
        """
        Returns whether this widget intersects another widget or wx.Rect.
        This uses logical coordinates, so you can do this without actually moving the widget onscreen.
        """   
        selfRect = self.getLogicalRect()
        
        if isinstance(other, PassageWidget):
            other = other.getLogicalRect()
        return selfRect.Intersects(other)
    
    def applyPrefs (self):
        """Passes on the message to any editor windows."""
        try: self.passageFrame.applyPrefs()
        except: pass
        try: self.passageFrame.fullscreen.applyPrefs()
        except: pass

    def dirtyPixelRect (self):
        """
        Returns a pixel rectangle of everything that needs to be redrawn for the widget
        in its current position. This includes the widget itself as well as any
        other widgets it links to.
        """            
        dirtyRect = self.getPixelRect()
        
        # first, passages we link to
        
        for link in self.passage.links():
            widget = self.parent.findWidget(link)
            if widget: dirtyRect = dirtyRect.Union(widget.getPixelRect())
        
        # then, those that link to us
        # Python closures are odd, require lists to affect things outside
        
        bridge = [ dirtyRect ]
        
        def addLinkingToRect (widget):
            if self.passage.title in widget.passage.links():
                dirtyRect = bridge[0].Union(widget.getPixelRect())
        
        self.parent.eachWidget(addLinkingToRect)

        return dirtyRect

    def paint (self, gc):
        """Paints widget to the graphics context passed."""

        def wordWrap (text, lineWidth, gc):
            """
            Returns a list of lines from a string 
            This is somewhat based on the wordwrap function built into wx.lib.
            (For some reason, GraphicsContext.GetPartialTextExtents()
            is returning totally wrong numbers but GetTextExtent() works fine.)
            
            This assumes that you've already set up the font you want on the GC.
            It gloms multiple spaces together, but for our purposes that's ok.
            """
            words = text.split()
            lines = []
            currentWidth = 0
            currentLine = ''
            
            for word in words:
                wordWidth = gc.GetTextExtent(word + ' ')[0]
                if currentWidth + wordWidth < lineWidth:
                    currentLine += word + ' '
                    currentWidth += wordWidth
                else:
                    lines.append(currentLine)
                    currentLine = word + ' '
                    currentWidth = wordWidth
            
            lines.append(currentLine)
            return lines

        def dim (c, dim):
            """Lowers a color's alpha if dim is true."""
            if isinstance(c, wx.Color): c = list(c.Get(includeAlpha = True))
            if len(c) < 4:
                c = list(c)
                c.append(255)
            if dim: c[3] *= PassageWidget.DIMMED_ALPHA
            return wx.Color(c[0], c[1], c[2], c[3])
        
        pixPos = self.parent.toPixels(self.pos)
        pixSize = self.parent.toPixels(self.getSize(), scaleOnly = True)

        # text font sizes
        # wxWindows works with points, so we need to doublecheck on actual pixels

        titleFontSize = self.parent.toPixels((metrics.size('widgetTitle'), -1), scaleOnly = True)[0]
        titleFontSize = min(titleFontSize, metrics.size('fontMax'))
        titleFontSize = max(titleFontSize, metrics.size('fontMin'))
        excerptFontSize = min(titleFontSize * 0.9, metrics.size('fontMax'))
        excerptFontSize = max(excerptFontSize, metrics.size('fontMin'))
        titleFont = wx.Font(titleFontSize, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Arial')
        excerptFont = wx.Font(excerptFontSize, wx.SWISS, wx.NORMAL, wx.NORMAL, False, 'Arial')
        titleFontHeight = math.fabs(titleFont.GetPixelSize()[1])
        excerptFontHeight = math.fabs(excerptFont.GetPixelSize()[1])
                
        # inset for text (we need to know this for layout purposes)
        
        inset = titleFontHeight / 3
        
        # frame
        
        frameColor = dim(PassageWidget.COLORS['frame'], self.dimmed)
        frameInterior = (dim(PassageWidget.COLORS['bodyStart'], self.dimmed), \
                         dim(PassageWidget.COLORS['bodyEnd'], self.dimmed))
        
        gc.SetPen(wx.Pen(frameColor, 1))
        gc.SetBrush(gc.CreateLinearGradientBrush(pixPos[0], pixPos[1], \
                                                 pixPos[0], pixPos[1] + pixSize[1], \
                                                 frameInterior[0], frameInterior[1]))     
        gc.DrawRectangle(pixPos[0], pixPos[1], pixSize[0] - 1, pixSize[1] - 1)

        if pixSize[0] > PassageWidget.MIN_GREEKING_SIZE:
            # title bar
            
            titleBarHeight = titleFontHeight + (2 * inset)
            titleBarColor = dim(PassageWidget.COLORS['titleBar'], self.dimmed)
            gc.SetPen(wx.Pen(titleBarColor, 1))
            gc.SetBrush(wx.Brush(titleBarColor))
            gc.DrawRectangle(pixPos[0] + 1, pixPos[1] + 1, pixSize[0] - 3, titleBarHeight)            

            # draw title
            # we let clipping prevent writing over the frame
            
            gc.ResetClip()
            gc.Clip(pixPos[0] + inset, pixPos[1] + inset, pixSize[0] - (inset * 2), titleBarHeight - 2)
            titleTextColor = dim(PassageWidget.COLORS['titleText'], self.dimmed)
            gc.SetFont(titleFont, titleTextColor)
            gc.DrawText(self.passage.title, pixPos[0] + inset, pixPos[1] + inset)
            
            # draw excerpt
    
            excerptTop = pixPos[1] + inset + titleBarHeight
    
            # we split the excerpt by line, then draw them in turn
            # (we use a library to determine breaks, but have to draw the lines ourselves)
    
            gc.ResetClip()
            excerptTextColor = dim(PassageWidget.COLORS['excerptText'], self.dimmed)
            gc.SetFont(excerptFont, excerptTextColor)
            excerptLines = wordWrap(self.passage.text, pixSize[0] - (inset * 2), gc)
            
            for line in excerptLines:
                gc.DrawText(line, pixPos[0] + inset, excerptTop)
                excerptTop += excerptFontHeight * PassageWidget.LINE_SPACING
                if excerptTop + excerptFontHeight > (pixPos[1] + pixSize[1]) - inset: break
        else:
            # greek title
            
            titleBarColor = dim(PassageWidget.COLORS['titleBar'], self.dimmed)
            gc.SetPen(wx.Pen(titleBarColor, 1))
            gc.SetBrush(wx.Brush(titleBarColor))
            gc.DrawRectangle(pixPos[0] + 1, pixPos[1] + 1, pixSize[0] - 3, PassageWidget.GREEK_HEIGHT * 3)
            
            gc.SetPen(wx.Pen('#ffffff', PassageWidget.GREEK_HEIGHT))
            height = pixPos[1] + inset
            width = pixPos[0] + (pixSize[0] - inset ) / 2
            gc.StrokeLine(pixPos[0] + inset, height, width, height)
            height += PassageWidget.GREEK_HEIGHT * 3
            
            # greek body text
            
            gc.SetPen(wx.Pen('#666666', PassageWidget.GREEK_HEIGHT))
            
            while height < (pixPos[1] + pixSize[1]) - inset:
                width = pixSize[0] - inset
                
                if height + (PassageWidget.GREEK_HEIGHT * 2) > (pixPos[1] + pixSize[1]) - inset:
                    width = width / 2
                
                gc.StrokeLine(pixPos[0] + inset, height, pixPos[0] + width, height)
                height += PassageWidget.GREEK_HEIGHT * 2

        # draw a broken link emblem in the bottom right if necessary
        # fixme: not sure how to do this with transparency
        
        if len(self.getBrokenLinks()):
            emblemSize = self.brokenEmblem.GetSize()
            emblemPos = [ (pixPos[0] + pixSize[0]) - (emblemSize[0] + inset), \
                          (pixPos[1] + pixSize[1]) - (emblemSize[1] + inset) ]
            gc.DrawBitmap(self.brokenEmblem, emblemPos[0], emblemPos[1], emblemSize[0], emblemSize[1])
            
        # finally, draw a selection over ourselves if we're selected
        
        if self.selected:
            color = dim(wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT), self.dimmed)
            gc.SetPen(wx.Pen(color, 2))
            r, g, b = color.Get()
            color = wx.Color(r, g, b, 64)
            gc.SetBrush(wx.Brush(color))
            gc.DrawRectangle(pixPos[0] + 1, pixPos[1] + 1, pixSize[0] - 2, pixSize[1] - 2)
        
    def serialize (self):
        """Returns a dictionary with state information suitable for pickling."""
        return { 'selected': self.selected, 'pos': self.pos, 'passage': copy.copy(self.passage) }

    def sort (first, second):
        """
        Sorts PassageWidgets so that the results appear left to right,
        top to bottom. A certain amount of slack is assumed here in
        terms of positioning.
        """
        xDistance = first.pos[0] - second.pos[0]    
        yDistance = first.pos[1] - second.pos[1]
        
        if abs(yDistance) > 5:
            return yDistance
        else:
            return xDistance
    
    def __repr__ (self):
        return "<PassageWidget '" + self.passage.title + "'>"
    
    MIN_PIXEL_SIZE = 10
    MIN_GREEKING_SIZE = 50
    GREEK_HEIGHT = 2
    SIZE = 120
    SHADOW_SIZE = 5
    COLORS = { 'frame': (0, 0, 0), \
               'bodyStart': (255, 255, 255), \
               'bodyEnd': (228, 228, 226), \
               'titleBar': (52, 101, 164), \
               'titleText': (255, 255, 255), \
               'excerptText': (0, 0, 0) }
    DIMMED_ALPHA = 0.25
    LINE_SPACING = 1.2
        
# contextual menu

class PassageWidgetContext (wx.Menu):
    def __init__ (self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
        title = '"' + parent.passage.title + '"'
        
        edit = wx.MenuItem(self, wx.NewId(), 'Edit ' + title)
        self.AppendItem(edit)
        self.Bind(wx.EVT_MENU, self.parent.openEditor, id = edit.GetId())
        
        delete = wx.MenuItem(self, wx.NewId(), 'Delete ' + title)
        self.AppendItem(delete)
        self.Bind(wx.EVT_MENU, lambda e: self.parent.parent.removeWidget(self.parent), id = delete.GetId())