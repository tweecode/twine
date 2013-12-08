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

import sys, os, copy, math, re, wx, storypanel, tiddlywiki
import geometry, metrics, images
from passageframe import PassageFrame, ImageFrame

class PassageWidget:
    
    def __init__ (self, parent, app, id = wx.ID_ANY, pos = (0, 0), title = '', text = '', tags = [], state = None):
        # inner state
        
        self.parent = parent
        self.app = app
        self.dimmed = False
        if sys.platform == 'darwin':
            self.brokenEmblem = wx.Bitmap(re.sub('lib/.*', '', os.path.realpath(sys.path[0])) + "icons" + os.sep + 'brokenemblem.png')
        else:
            self.brokenEmblem = wx.Bitmap(self.app.getPath() + os.sep + 'icons' + os.sep + 'brokenemblem.png')
        self.paintBuffer = wx.MemoryDC()
        self.paintBufferBounds = None
        pos = list(pos)
        
        if state:
            self.passage = state['passage']
            self.pos = state['pos']
            self.selected = state['selected']
        else:
            self.passage = tiddlywiki.Tiddler('')
            self.passage.title = title
            self.passage.text = text
            self.passage.tags += tags
            self.selected = False
            self.pos = list(pos)
        
        self.bitmap = None
        self.updateBitmap()
        self.passage.update()
            
    def getSize (self):
        """Returns this instance's logical size."""
        if "annotation" in self.passage.tags:
            return (PassageWidget.SIZE+self.parent.GRID_SPACING, PassageWidget.SIZE+self.parent.GRID_SPACING)
        return (PassageWidget.SIZE, PassageWidget.SIZE)
            
    def getCenter (self):
        """Returns this instance's center in logical coordinates."""
        pos = list(self.pos)
        pos[0] += self.getSize()[0] / 2
        pos[1] += self.getSize()[1] / 2
        return pos

    def getLogicalRect (self):
        """Returns this instance's rectangle in logical coordinates."""
        size = self.getSize()
        return wx.Rect(self.pos[0], self.pos[1], size[0], size[1])

    def getPixelRect (self):
        """Returns this instance's rectangle onscreen."""
        origin = self.parent.toPixels(self.pos)
        size = self.parent.toPixels(self.getSize(), scaleOnly = True)
        return wx.Rect(origin[0], origin[1], size[0], size[1])

    def getDirtyPixelRect (self):
        """
        Returns a pixel rectangle of everything that needs to be redrawn for the widget
        in its current position. This includes the widget itself as well as any
        other widgets it links to.
        """            
        dirtyRect = self.getPixelRect()
        
        # first, passages we link to
        
        for link in self.passage.links:
            widget = self.parent.findWidget(link)
            if widget: dirtyRect = dirtyRect.Union(widget.getPixelRect())
        
        # then, those that link to us
        # Python closures are odd, require lists to affect things outside
        
        bridge = [ dirtyRect ]
        
        def addLinkingToRect (widget):
            if self.passage.title in widget.passage.links:
                dirtyRect = bridge[0].Union(widget.getPixelRect())
        
        self.parent.eachWidget(addLinkingToRect)

        return dirtyRect
    
    def offset (self, x = 0, y = 0):
        """Offsets this widget's position by logical coordinates."""
        self.pos = list(self.pos)
        self.pos[0] += x
        self.pos[1] += y
 
    def findSpace (self):
        """Moves this widget so it doesn't overlap any others."""        
        turns = 0.0
        movecount = 1
        """
        Don't adhere to the grid if snapping isn't enabled.
        Instead, move in 1/5 grid increments.
        """
        griddivision = 1 if self.parent.snapping else 0.2
        
        while self.intersectsAny() and turns < 99*griddivision:
            """Move in an Ulam spiral pattern: n spaces left, n spaces up, n+1 spaces right, n+1 spaces down"""
            self.pos[int(math.floor((turns*2) % 2))] += self.parent.GRID_SPACING * griddivision * int(math.copysign(1, turns % 2 - 1));
            movecount -= 1
            if movecount <= 0:
                turns += 0.5
                movecount = int(math.ceil(turns)/griddivision)
                
    def findSpaceQuickly(self):
        """ A quicker findSpace where the position and visibility doesn't really matter """
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
        for link in self.passage.links:
            if not self.parent.findWidget(link):
                brokens.append(link)
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
        if self.selected != old:
            self.clearPaintCache()
            
            # Figure out the dirty rect
            dirtyRect = self.getPixelRect()
            for link in self.passage.linksAndDisplays() + self.passage.images:
                widget = self.parent.findWidget(link)
                if widget:
                    dirtyRect = dirtyRect.Union(widget.getDirtyPixelRect())
            if self.passage.isStylesheet():
                for t in self.passage.tags: 
                    if t not in tiddlywiki.TiddlyWiki.INFO_TAGS:
                        for widget in self.parent.taggedWidgets(t):
                            if widget:
                                dirtyRect = dirtyRect.Union(widget.getDirtyPixelRect())
            self.parent.Refresh(True, dirtyRect)
        
    def setDimmed (self, value):
        """Sets whether this widget should be dimmed."""
        old = self.dimmed
        self.dimmed = value
        if self.dimmed != old:
            self.clearPaintCache()
                               
    def clearPaintCache (self):
        """
        Forces the widget to be repainted from scratch.
        """
        self.paintBufferBounds = None

    def openContextMenu (self, event):
        """Opens a contextual menu at the event position given."""
        self.parent.PopupMenu(PassageWidgetContext(self), event.GetPosition())
        
    def openEditor (self, event = None, fullscreen = False):
        """Opens a PassageFrame to edit this passage."""
        image = self.passage.isImage()
        
        if (not hasattr(self, 'passageFrame')):
            if image:
                self.passageFrame = ImageFrame(None, self, self.app)
            else:
                self.passageFrame = PassageFrame(None, self, self.app)
                if fullscreen: self.passageFrame.openFullscreen()
        else:
            try:
                self.passageFrame.Iconize(False)
                self.passageFrame.Raise()
                if fullscreen and not image: self.passageFrame.openFullscreen()
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

    def intersectsAny (self, dragging = False):
        """Returns whether this widget intersects any other in the same StoryPanel."""
        
        #Enforce positive coordinates
        if not 'Twine.hide' in self.passage.tags:
            if ((self.pos[0] < 0) or (self.pos[1] < 0)):
                return True
        
        # we do this manually so we don't have to go through all of them
        
        for widget in (self.parent.notDraggingWidgets if dragging else self.parent.widgets):
            if (widget != self) and (self.intersects(widget)):
                return True
            
        return False

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
        
    def updateBitmap(self):
        """If an image passage, updates the bitmap to match the contained base64 data."""
        if self.passage.isImage():
            self.bitmap = images.Base64ToBitmap(self.passage.text)
    
    def paintConnectorTo (self, otherWidget, arrowheads, color, width, gc, updateRect = None):
        """
        Paints a connecting line between this widget and another,
        with optional arrowheads. You may pass either a wx.GraphicsContext
        (anti-aliased drawing) or a wx.PaintDC.
        """
        start = self.parent.toPixels(self.getCenter())
        end = self.parent.toPixels(otherWidget.getCenter())
                    
        # Additional tweak to make overlapping arrows more visible
        
        length = min(math.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)/32, 16)
        
        if start[1] != end[1]:
            start[0] += length * math.copysign(1, start[1] - end[1]);
            end[0] += length * math.copysign(1, start[1] - end[1]);
        if start[0] != end[0]:
            start[1] += length * math.copysign(1, start[0] - end[0]);
            end[1] += length * math.copysign(1, start[0] - end[0]);
        
        # Clip the end of the arrow
        
        start, end = geometry.clipLineByRects([start, end], otherWidget.getPixelRect())
                    
        # does it actually need to be drawn?
                
        if otherWidget == self:
            return
        
        if updateRect and not geometry.lineRectIntersection([start, end], updateRect):
            return
            
        # ok, really draw the line
        
        lineWidth = max(self.parent.toPixels((width, 0), scaleOnly = True)[0], 1)
        gc.SetPen(wx.Pen(color, lineWidth))
        
        if isinstance(gc, wx.GraphicsContext):
            gc.StrokeLine(start[0], start[1], end[0], end[1])
        else:
            gc.DrawLine(start[0], start[1], end[0], end[1])
        
        # arrowheads at end

        if not arrowheads: return
         
        arrowheadLength = max(self.parent.toPixels((PassageWidget.ARROWHEAD_LENGTH, 0), scaleOnly = True)[0], 1)
        arrowhead = geometry.endPointProjectedFrom((start, end), angle = PassageWidget.ARROWHEAD_ANGLE, \
                                                   distance = arrowheadLength)
        
        if isinstance(gc, wx.GraphicsContext):
            gc.StrokeLine(end[0], end[1], arrowhead[0], arrowhead[1])
        else:
            gc.DrawLine(end[0], end[1], arrowhead[0], arrowhead[1])
            
        arrowhead = geometry.endPointProjectedFrom((start, end), angle = 0 - PassageWidget.ARROWHEAD_ANGLE, \
                                                   distance = arrowheadLength)

        if isinstance(gc, wx.GraphicsContext):
            gc.StrokeLine(end[0], end[1], arrowhead[0], arrowhead[1])
        else:
            gc.DrawLine(end[0], end[1], arrowhead[0], arrowhead[1]) 

    def paintConnectors (self, gc, arrowheads = True, dontDraw = [], updateRect = None):
        """
        Paints all connectors originating from this widget. This accepts
        a list of widget titles that will not be drawn to. It returns this
        list, along with any other bad links this widget contains.
        
        As with other paint calls, you may pass either a wx.GraphicsContext
        or wx.PaintDC.
        """       
        
        if not self.app.config.ReadBool('fastStoryPanel'):
            gc = wx.GraphicsContext.Create(gc)
        
        for link in self.passage.linksAndDisplays():
            if link in dontDraw: continue
            
            otherWidget = self.parent.findWidget(link)
            if not otherWidget or not otherWidget.passage.isStoryPassage(): dontDraw.append(link)
        
            if otherWidget and not otherWidget.dimmed:
                color = PassageWidget.CONNECTOR_DISPLAY_COLOR if link not in self.passage.links else PassageWidget.CONNECTOR_COLOR
                width = PassageWidget.CONNECTOR_SELECTED_WIDTH if self.selected else PassageWidget.CONNECTOR_WIDTH
                self.paintConnectorTo(otherWidget, arrowheads, color, width, gc, updateRect)
        
        for i in self.passage.images:
            if i not in dontDraw:
                otherWidget = self.parent.findWidget(i)
                if otherWidget and not otherWidget.dimmed:
                    color = PassageWidget.CONNECTOR_RESOURCE_COLOR
                    width = (2 if self.selected else 1)
                    self.paintConnectorTo(otherWidget, arrowheads, color, width, gc, updateRect)
        
        if self.passage.isStylesheet():
            for t in self.passage.tags: 
                if t not in tiddlywiki.TiddlyWiki.INFO_TAGS:
                    for otherWidget in self.parent.taggedWidgets(t):
                        if not otherWidget.dimmed and not otherWidget.passage.isStylesheet():
                            color = PassageWidget.CONNECTOR_RESOURCE_COLOR
                            width = (2 if self.selected else 1)
                            self.paintConnectorTo(otherWidget, arrowheads, color, width, gc, updateRect)
        
        return dontDraw
    
    def paint (self, dc):
        """
        Handles paint events, either blitting our paint buffer or
        manually redrawing.
        """
        pixPos = self.parent.toPixels(self.pos)
        pixSize = self.parent.toPixels(self.getSize(), scaleOnly = True)
        rect = wx.Rect(pixPos[0], pixPos[1], pixSize[0], pixSize[1])
        
        if (not self.paintBufferBounds) \
            or (rect.width != self.paintBufferBounds.width \
                or rect.height != self.paintBufferBounds.height):
            self.cachePaint(wx.Size(rect.width, rect.height))
        
        dc.Blit(rect.x, rect.y, rect.width, rect.height, self.paintBuffer, 0, 0)
    
    def getTitleColorIndex(self):
        # Find the StartPassages passage
        if self.passage.isAnnotation():
            return 'annotation'
        elif self.passage.isImage():
            return 'imageTitleBar'
        elif any(t.startswith('Twine.') for t in self.passage.tags):
            return 'privateTitleBar'
        elif 'script' in self.passage.tags:
            return 'scriptTitleBar'
        elif self.passage.isStylesheet():
            return 'stylesheetTitleBar'
        elif self.passage.title in tiddlywiki.TiddlyWiki.INFO_PASSAGES:
            return 'storyInfoTitleBar'
        elif self.passage.title == "Start":
            return 'startTitleBar'
        elif not self.passage.linksAndDisplays():
            return 'endTitleBar'
        return 'titleBar'
    
    def cachePaint (self, size):
        """
        Caches the widget so self.paintBuffer is up-to-date.
        """

        def wordWrap (text, lineWidth, gc, lineBreaks = False):
            """
            Returns a list of lines from a string 
            This is somewhat based on the wordwrap function built into wx.lib.
            (For some reason, GraphicsContext.GetPartialTextExtents()
            is returning totally wrong numbers but GetTextExtent() works fine.)
            
            This assumes that you've already set up the font you want on the GC.
            It gloms multiple spaces together, but for our purposes that's ok.
            """
            words = re.finditer('\S+\s*', text.replace('\r',''))
            lines = ''
            currentLine = ''
            
            for w in words:
                word = w.group(0)
                wordWidth = gc.GetTextExtent(currentLine + word)[0]
                if wordWidth < lineWidth:
                    currentLine += word
                    if '\n' in word:
                        lines += currentLine
                        currentLine = ''
                else:
                    lines += currentLine + '\n'
                    currentLine = word
            lines += currentLine
            return lines.split('\n')

        def dim (c, dim):
            """Lowers a color's alpha if dim is true."""
            if isinstance(c, wx.Colour): c = list(c.Get(includeAlpha = True))
            if len(c) < 4:
                c = list(c)
                c.append(255)
            if dim:
                a = PassageWidget.DIMMED_ALPHA
                if not self.app.config.ReadBool('fastStoryPanel'):
                    c[3] *= a
                else:
                    c[0] *= a
                    c[1] *= a
                    c[2] *= a
            return wx.Colour(*c)

        # set up our buffer

        bitmap = wx.EmptyBitmap(size.width, size.height)
        self.paintBuffer.SelectObject(bitmap)
        
        # switch to a GraphicsContext as necessary

        if self.app.config.ReadBool('fastStoryPanel'):
            gc = self.paintBuffer
        else:
            gc = wx.GraphicsContext.Create(self.paintBuffer)            
        
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
        if self.passage.isAnnotation():
            c = wx.Colour(*PassageWidget.COLORS['annotation'], alpha = 1)
            frameInterior = (c,c)
        else:
            frameInterior = (dim(PassageWidget.COLORS['bodyStart'], self.dimmed), \
                         dim(PassageWidget.COLORS['bodyEnd'], self.dimmed))
        
        gc.SetPen(wx.Pen(frameColor, 1))
                
        if isinstance(gc, wx.GraphicsContext):
            gc.SetBrush(gc.CreateLinearGradientBrush(0, 0, 0, size.height, \
                                                     frameInterior[0], frameInterior[1]))     
        else:
            gc.GradientFillLinear(wx.Rect(0, 0, size.width - 1, size.height - 1), \
                            frameInterior[0], frameInterior[1], wx.SOUTH)
            gc.SetBrush(wx.TRANSPARENT_BRUSH)

        gc.DrawRectangle(0, 0, size.width - 1, size.height - 1)
        
        if size.width > PassageWidget.MIN_GREEKING_SIZE * (2 if self.passage.isAnnotation() else 1):
            # title bar
            
            titleBarHeight = titleFontHeight + (2 * inset)
            titleBarColor = dim(PassageWidget.COLORS[self.getTitleColorIndex()], self.dimmed)
            gc.SetPen(wx.Pen(titleBarColor, 1))
            gc.SetBrush(wx.Brush(titleBarColor))
            gc.DrawRectangle(1, 1, size.width - 3, titleBarHeight)            

            # draw title
            # we let clipping prevent writing over the frame

            if isinstance(gc, wx.GraphicsContext):
                gc.ResetClip()
                gc.Clip(inset, inset, size.width - (inset * 2), titleBarHeight - 2)
            else:
                gc.DestroyClippingRegion()
                gc.SetClippingRect(wx.Rect(inset, inset, size.width - (inset * 2), titleBarHeight - 2))
                
            titleTextColor = dim(PassageWidget.COLORS['titleText'], self.dimmed)
            
            if isinstance(gc, wx.GraphicsContext):
                gc.SetFont(titleFont, titleTextColor)
            else:
                gc.SetFont(titleFont)
                gc.SetTextForeground(titleTextColor)
                
            if self.passage.title:
                gc.DrawText(self.passage.title, inset, inset)
            
            # draw excerpt
    
            if not self.passage.isImage():
                excerptTop = inset + titleBarHeight
        
                # we split the excerpt by line, then draw them in turn
                # (we use a library to determine breaks, but have to draw the lines ourselves)
        
                if isinstance(gc, wx.GraphicsContext):
                    gc.ResetClip()
                    gc.Clip(inset, inset, size.width - (inset * 2), size.height - (inset * 2))
                else:
                    gc.DestroyClippingRegion()
                    gc.SetClippingRect(wx.Rect(inset, inset, size.width - (inset * 2), size.height - (inset * 2)))
                
                if self.passage.isAnnotation():
                    excerptTextColor = wx.Colour(*PassageWidget.COLORS['annotationText'])
                else:
                    excerptTextColor = dim(PassageWidget.COLORS['excerptText'], self.dimmed)
    
                if isinstance(gc, wx.GraphicsContext):
                    gc.SetFont(excerptFont, excerptTextColor)
                else:
                    gc.SetFont(excerptFont)
                    gc.SetTextForeground(excerptTextColor)
                    
                excerptLines = wordWrap(self.passage.text, size.width - (inset * 2), gc, self.passage.isAnnotation())
                
                for line in excerptLines:
                    gc.DrawText(line, inset, excerptTop)
                    excerptTop += excerptFontHeight * PassageWidget.LINE_SPACING \
                        * min(1.75,max(1,1.75*size.width/260 if (self.passage.isAnnotation() and line) else 1))
                    if excerptTop + excerptFontHeight > size.height - inset: break
                    
            if (self.passage.isStoryText() and self.passage.tags) or \
                    (self.passage.isStylesheet() and len(self.passage.tags) > 1):
                
                tagBarHeight = excerptFontHeight + (2 * inset)
                tagBarColor = dim((226, 201, 162), self.dimmed)
                gc.SetPen(wx.Pen(tagBarColor, 1))
                gc.SetBrush(wx.Brush(tagBarColor))
                gc.DrawRectangle(0, size.height-tagBarHeight-1, size.width, tagBarHeight+1)            
    
                # draw tags
                    
                tagTextColor = dim(PassageWidget.COLORS['excerptText'], self.dimmed)
                
                if isinstance(gc, wx.GraphicsContext):
                    gc.SetFont(excerptFont, tagTextColor)
                else:
                    gc.SetFont(excerptFont)
                    gc.SetTextForeground(tagTextColor)
                    
                text = wordWrap(" ".join(a for a in self.passage.tags if a not in tiddlywiki.TiddlyWiki.INFO_TAGS),
                                size.width - (inset * 2), gc)[0]
                
                gc.DrawText(text, inset*2, (size.height-tagBarHeight))
        else:
            # greek title
            titleBarHeight = PassageWidget.GREEK_HEIGHT*3
            titleBarColor = dim(PassageWidget.COLORS[self.getTitleColorIndex()], self.dimmed)
            gc.SetPen(wx.Pen(titleBarColor, 1))
            gc.SetBrush(wx.Brush(titleBarColor))
            gc.DrawRectangle(1, 1, size.width - 3, PassageWidget.GREEK_HEIGHT * 3)
            
            gc.SetPen(wx.Pen('#ffffff', PassageWidget.GREEK_HEIGHT))
            height = inset
            width = (size.width - inset) / 2
            
            if isinstance(gc, wx.GraphicsContext):
                gc.StrokeLine(inset, height, width, height)
            else:
                gc.DrawLine(inset, height, width, height)
                
            height += PassageWidget.GREEK_HEIGHT * 3
            
            # greek body text
            if not self.passage.isImage():
                
                gc.SetPen(wx.Pen(self.COLORS['annotationText'] \
                    if self.passage.isAnnotation() else '#666666', PassageWidget.GREEK_HEIGHT))
                
                chars = len(self.passage.text)
                while height < size.height - inset and chars > 0:
                    width = size.height - inset
                    
                    if height + (PassageWidget.GREEK_HEIGHT * 2) > size.height - inset:
                        width /= 2
                    elif chars < 80:
                        width = max(4, width * chars / 80)
    
                    if isinstance(gc, wx.GraphicsContext):
                        gc.StrokeLine(inset, height, width, height)
                    else:
                        gc.DrawLine(inset, height, width, height)
                        
                    height += PassageWidget.GREEK_HEIGHT * 2
                    chars -= 80
            
            # greek tags
            
            if (self.passage.isStoryText() and self.passage.tags) or \
                    (self.passage.isStylesheet() and len(self.passage.tags) > 1) :
                
                tagBarHeight = PassageWidget.GREEK_HEIGHT*3
                tagBarColor = dim((226, 201, 162), self.dimmed)
                gc.SetPen(wx.Pen(tagBarColor, 1))
                gc.SetBrush(wx.Brush(tagBarColor))
                height = size.height-tagBarHeight-2
                width = size.width-4
                gc.DrawRectangle(2, height, width, tagBarHeight)
                
                gc.SetPen(wx.Pen('#666666', PassageWidget.GREEK_HEIGHT))
                height += inset
                width = (width-inset*2)/2
                
                if isinstance(gc, wx.GraphicsContext):
                    gc.StrokeLine(inset, height, width, height)
                else:
                    gc.DrawLine(inset, height, width, height)
                
        if self.passage.isImage():
            if self.bitmap:
                if isinstance(gc, wx.GraphicsContext):
                    gc.ResetClip()
                    gc.Clip(1, titleBarHeight + 1, size.width - 3, size.height - 3)
                else:
                    gc.DestroyClippingRegion()
                    gc.SetClippingRect(wx.Rect(1, titleBarHeight + 1, size.width - 3, size.height - 3))
                
                scale = size.width/float(self.bitmap.GetWidth());
                img = self.bitmap.ConvertToImage();
                if scale != 1:
                    img = img.Scale(scale*self.bitmap.GetWidth(),scale*self.bitmap.GetHeight());
                if isinstance(gc, wx.GraphicsContext):
                    gc.DrawBitmap(img.ConvertToBitmap(self.bitmap.GetDepth()), 1, titleBarHeight + 1, img.GetWidth(), img.GetHeight())
                else:
                    gc.DrawBitmap(img.ConvertToBitmap(self.bitmap.GetDepth()), 1, titleBarHeight + 1)

        if isinstance(gc, wx.GraphicsContext):
            gc.ResetClip()
        else:
            gc.DestroyClippingRegion()
                                
        # draw a broken link emblem in the bottom right if necessary
        # fixme: not sure how to do this with transparency
        
        if len(self.getBrokenLinks()):
            emblemSize = self.brokenEmblem.GetSize()
            emblemPos = [ size.width - (emblemSize[0] + inset), \
                          size.height - (emblemSize[1] + inset) ]
            
            if isinstance(gc, wx.GraphicsContext):
                gc.DrawBitmap(self.brokenEmblem, emblemPos[0], emblemPos[1], emblemSize[0], emblemSize[1])
            else:
                gc.DrawBitmap(self.brokenEmblem, emblemPos[0], emblemPos[1])
            
        # finally, draw a selection over ourselves if we're selected
        
        if self.selected:
            color = dim(wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT), self.dimmed)
            gc.SetPen(wx.Pen(color, 2))
            
            if isinstance(gc, wx.GraphicsContext):
                r, g, b = color.Get(False)
                color = wx.Colour(r, g, b, 64)
                gc.SetBrush(wx.Brush(color))
            else:
                gc.SetBrush(wx.TRANSPARENT_BRUSH)
 
            gc.DrawRectangle(1, 1, size.width - 2, size.height - 2)
            
        self.paintBufferBounds = size
        
    def serialize (self):
        """Returns a dictionary with state information suitable for pickling."""
        return { 'selected': self.selected, 'pos': self.pos, 'passage': copy.copy(self.passage) }

    def sort (first, second):
        """
        Sorts PassageWidgets so that the results appear left to right,
        top to bottom. A certain amount of slack is assumed here in
        terms of positioning.
        """
        xDistance = int(first.pos[0] - second.pos[0])    
        yDistance = int(first.pos[1] - second.pos[1])
                
        if abs(yDistance) > 5:
            return yDistance
        else:
            if xDistance != 0:
                return xDistance
            else:
                return 1 # punt on ties
    
    def __repr__ (self):
        return "<PassageWidget '" + self.passage.title + "'>"
    
    MIN_PIXEL_SIZE = 10
    MIN_GREEKING_SIZE = 50
    GREEK_HEIGHT = 2
    SIZE = 120
    SHADOW_SIZE = 5
    COLORS = { 'frame': (0, 0, 0), \
               'bodyStart': (255, 255, 255), \
               'bodyEnd': (212, 212, 212), \
               'annotation': (85, 87, 83), \
               'startTitleBar': (76, 163, 51), \
               'endTitleBar': (16, 51, 96), \
               'titleBar': (52, 101, 164), \
               'storyInfoTitleBar': (28, 89, 74), \
               'scriptTitleBar': (89, 66, 28), \
               'stylesheetTitleBar': (111, 49, 83), \
               'imageTitleBar': (8, 138, 133), \
               'privateTitleBar': (130, 130, 130), \
               'titleText': (255, 255, 255), \
               'excerptText': (0, 0, 0),\
               'annotationText': (255,255,255) }
    DIMMED_ALPHA = 0.5
    LINE_SPACING = 1.2
    CONNECTOR_WIDTH = 2.0
    CONNECTOR_COLOR = '#babdb6'
    CONNECTOR_RESOURCE_COLOR = '#6e706b'
    CONNECTOR_DISPLAY_COLOR = '#84a4bd'
    CONNECTOR_SELECTED_WIDTH = 5.0
    ARROWHEAD_LENGTH = 10
    MIN_ARROWHEAD_LENGTH = 5
    ARROWHEAD_ANGLE = math.pi / 6
        
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
        
        if parent.passage.isStoryPassage():
            test = wx.MenuItem(self, wx.NewId(), 'Test Play From Here')
            self.AppendItem(test)
            self.Bind(wx.EVT_MENU, lambda e: self.parent.parent.parent.testBuild(startAt = parent.passage.title), id = test.GetId())
    
