import copy, math, colorsys, re, wx, tiddlywiki, tweelexer
import geometry, metrics, images
from passageframe import PassageFrame, ImageFrame, StorySettingsFrame

class PassageWidget(object):
    """
    A PassageWidget is a box standing in for a proxy for a single
    passage in a story. Users can drag them around, double-click
    to open a PassageFrame, and so on.

    This must have a StoryPanel as its parent.

    See the comments on StoryPanel for more information on the
    coordinate systems are used here. In general, you should
    always pass methods logical coordinates, and expect back
    logical coordinates. Use StoryPanel.toPixels() to convert.
    """

    def __init__(self, parent, app, pos = (0, 0), title = '', text = '', tags = (), state = None):
        # inner state

        self.parent = parent
        self.app = app
        self.dimmed = False
        self.brokenEmblem = wx.Bitmap(self.app.iconsPath + 'brokenemblem.png')
        self.externalEmblem = wx.Bitmap(self.app.iconsPath + 'externalemblem.png')
        self.paintBuffer = wx.MemoryDC()
        self.paintBufferBounds = None
        if state:
            self.passage = state['passage']
            self.pos = list(pos) if pos != (0,0) else state['pos']
            self.selected = state['selected']
        else:
            self.passage = tiddlywiki.Tiddler('')
            self.selected = False
            self.pos = list(pos)
        if title: self.passage.title = title
        if text: self.passage.text = text
        if tags: self.passage.tags += tags

        self.bitmap = None
        self.updateBitmap()
        self.passage.update()

    def getSize(self):
        """Returns this instance's logical size."""
        if self.passage.isAnnotation():
            return (PassageWidget.SIZE+self.parent.GRID_SPACING, PassageWidget.SIZE+self.parent.GRID_SPACING)
        return (PassageWidget.SIZE, PassageWidget.SIZE)

    def getCenter(self):
        """Returns this instance's center in logical coordinates."""
        pos = list(self.pos)
        pos[0] += self.getSize()[0] / 2
        pos[1] += self.getSize()[1] / 2
        return pos

    def getLogicalRect(self):
        """Returns this instance's rectangle in logical coordinates."""
        size = self.getSize()
        return wx.Rect(self.pos[0], self.pos[1], size[0], size[1])

    def getPixelRect(self):
        """Returns this instance's rectangle onscreen."""
        origin = self.parent.toPixels(self.pos)
        size = self.parent.toPixels(self.getSize(), scaleOnly = True)
        return wx.Rect(origin[0], origin[1], size[0], size[1])

    def getDirtyPixelRect(self):
        """
        Returns a pixel rectangle of everything that needs to be redrawn for the widget
        in its current position. This includes the widget itself as well as any
        other widgets it links to.
        """
        dirtyRect = self.getPixelRect()

        # first, passages we link to

        for link in self.passage.links:
            widget = self.parent.findWidget(link)
            if widget:
                dirtyRect.Union(widget.getPixelRect())

        # then, those that link to us

        def addLinkingToRect(widget):
            if self.passage.title in widget.passage.links:
                dirtyRect.Union(widget.getPixelRect())

        self.parent.eachWidget(addLinkingToRect)

        return dirtyRect

    def offset(self, x = 0, y = 0):
        """Offsets this widget's position by logical coordinates."""
        self.pos = list(self.pos)
        self.pos[0] += x
        self.pos[1] += y

    def findSpace(self):
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
            self.pos[int(math.floor((turns*2) % 2))] += self.parent.GRID_SPACING * griddivision * int(math.copysign(1, turns % 2 - 1))
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


    def containsRegexp(self, regexp, flags):
        """
        Returns whether this widget's passage contains a regexp.
        """
        return (re.search(regexp, self.passage.title, flags) is not None
                or re.search(regexp, self.passage.text, flags) is not None)

    def replaceRegexp(self, findRegexp, replaceRegexp, flags):
        """
        Performs a regexp replace in this widget's passage title and
        body text. Returns the number of replacements actually made.
        """
        compiledRegexp = re.compile(findRegexp, flags)

        oldTitle = self.passage.title
        newTitle, titleReps = re.subn(compiledRegexp, replaceRegexp, oldTitle)
        self.passage.text, textReps = re.subn(compiledRegexp, replaceRegexp, self.passage.text)
        if titleReps > 0:
            self.parent.changeWidgetTitle(oldTitle, newTitle)

        return titleReps + textReps

    def linksAndDisplays(self):
        return self.passage.linksAndDisplays() + self.getShorthandDisplays()

    def getShorthandDisplays(self):
        """Returns a list of macro tags which match passage names."""
        return filter(self.parent.passageExists, self.passage.macros)

    def getBrokenLinks(self):
        """Returns a list of broken links in this widget."""
        return filter(lambda a: not self.parent.passageExists(a), self.passage.links)

    def getIncludedLinks(self):
        """Returns a list of included passages in this widget."""
        return filter(self.parent.includedPassageExists, self.passage.links)

    def getVariableLinks(self):
        """Returns a list of links which use variables/functions, in this widget."""
        return filter(lambda a: tweelexer.TweeLexer.linkStyle(a) == tweelexer.TweeLexer.PARAM, self.passage.links)

    def setSelected(self, value, exclusive = True):
        """
        Sets whether this widget should be selected. Pass a false value for
        exclusive to prevent other widgets from being deselected.
        """

        if exclusive:
            self.parent.eachWidget(lambda i: i.setSelected(False, False))

        old = self.selected
        self.selected = value
        if self.selected != old:
            self.clearPaintCache()

            # Figure out the dirty rect
            dirtyRect = self.getPixelRect()
            for link in self.linksAndDisplays() + self.passage.images:
                widget = self.parent.findWidget(link)
                if widget:
                    dirtyRect.Union(widget.getDirtyPixelRect())
            if self.passage.isStylesheet():
                for t in self.passage.tags:
                    if t not in tiddlywiki.TiddlyWiki.INFO_TAGS:
                        for widget in self.parent.taggedWidgets(t):
                            if widget:
                                dirtyRect.Union(widget.getDirtyPixelRect())
            self.parent.Refresh(True, dirtyRect)

    def setDimmed(self, value):
        """Sets whether this widget should be dimmed."""
        old = self.dimmed
        self.dimmed = value
        if self.dimmed != old:
            self.clearPaintCache()

    def clearPaintCache(self):
        """
        Forces the widget to be repainted from scratch.
        """
        self.paintBufferBounds = None

    def openContextMenu(self, event):
        """Opens a contextual menu at the event position given."""
        self.parent.PopupMenu(PassageWidgetContext(self), event.GetPosition())

    def openEditor(self, event = None, fullscreen = False):
        """Opens a PassageFrame to edit this passage."""
        image = self.passage.isImage()

        if not hasattr(self, 'passageFrame'):
            if image:
                self.passageFrame = ImageFrame(None, self, self.app)
            elif self.passage.title == "StorySettings":
                self.passageFrame = StorySettingsFrame(None, self, self.app)
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

    def closeEditor(self, event = None):
        """Closes the PassageFrame associated with this, if it exists."""
        try: self.passageFrame.closeEditor()
        except: pass
        try: self.passageFrame.Destroy()
        except: pass

    def verifyPassage(self, window):
        """
        Check that the passage syntax is well-formed.
        Return -(corrections made) if the check was aborted, +(corrections made) otherwise
        """
        passage = self.passage
        checks = tweelexer.VerifyLexer(self).check()

        problems = 0

        oldtext = passage.text
        newtext = ""
        index = 0
        for warning, replace in checks:
            problems += 1
            if replace:
                start, sub, end = replace
                answer = wx.MessageDialog(window, warning + "\n\nMay I try to fix this for you?",
                                          'Problem in ' + self.passage.title,
                                          wx.ICON_WARNING | wx.YES_NO | wx.CANCEL | wx.YES_DEFAULT
                                          ).ShowModal()
                if answer == wx.ID_YES:
                    newtext += oldtext[index:start] + sub
                    index = end
                    if hasattr(self, 'passageFrame') and self.passageFrame:
                        self.passageFrame.bodyInput.SetText(newtext + oldtext[index:])
                elif answer == wx.ID_CANCEL:
                    return -problems
            else:
                answer = wx.MessageDialog(window, warning+"\n\nKeep checking?", 'Problem in '+self.passage.title, wx.ICON_WARNING | wx.YES_NO) \
                    .ShowModal()
                if answer == wx.ID_NO:
                    return problems

            passage.text = newtext + oldtext[index:]

        return problems

    def intersectsAny(self, dragging = False):
        """Returns whether this widget intersects any other in the same StoryPanel."""

        #Enforce positive coordinates
        if not 'Twine.hide' in self.passage.tags:
            if self.pos[0] < 0 or self.pos[1] < 0:
                return True

        # we do this manually so we don't have to go through all of them

        for widget in self.parent.notDraggingWidgets if dragging else self.parent.widgetDict.itervalues():
            if widget != self and self.intersects(widget):
                return True

        return False

    def intersects(self, other):
        """
        Returns whether this widget intersects another widget or wx.Rect.
        This uses logical coordinates, so you can do this without actually moving the widget onscreen.
        """
        selfRect = self.getLogicalRect()

        if isinstance(other, PassageWidget):
            other = other.getLogicalRect()
        return selfRect.Intersects(other)

    def applyPrefs(self):
        """Passes on the message to any editor windows."""
        self.clearPaintCache()
        try: self.passageFrame.applyPrefs()
        except: pass
        try: self.passageFrame.fullscreen.applyPrefs()
        except: pass

    def updateBitmap(self):
        """If an image passage, updates the bitmap to match the contained base64 data."""
        if self.passage.isImage():
            self.bitmap = images.base64ToBitmap(self.passage.text)

    def getConnectorLine(self, otherWidget, clipped=True):
        """
        Get the line that would be drawn between this widget and another.
        """
        start = self.getCenter()
        end = otherWidget.getCenter()

        #Tweak to make overlapping lines easier to see by shifting the end point
        #Devision by a large constant to so the behavior is not overly noticeable while dragging
        lengthSquared = ((start[0]-end[0])**2+(start[1]-end[1])**2)/1024**2
        end[0] += (0.5 - math.sin(lengthSquared))*PassageWidget.SIZE/8.0
        end[1] += (0.5 - math.cos(lengthSquared))*PassageWidget.SIZE/8.0
        if clipped:
            [start, end] = geometry.clipLineByRects([start, end], otherWidget.getLogicalRect())
        return self.parent.toPixels(start), self.parent.toPixels(end)

    def getConnectedWidgets(self, displayArrows, imageArrows):
        """
        Returns a list of titles of all widgets that will have lines drawn to them.
        """
        ret = []

        for link in self.linksAndDisplays():
            if link in self.passage.links or displayArrows:
                widget = self.parent.findWidget(link)
                if widget:
                    ret.append(widget)

        if imageArrows:
            for link in self.passage.images:
                widget = self.parent.findWidget(link)
                if widget:
                    ret.append(widget)

            if self.passage.isStylesheet():
                for t in self.passage.tags:
                    if t not in tiddlywiki.TiddlyWiki.INFO_TAGS:
                        for otherWidget in self.parent.taggedWidgets(t):
                            if not otherWidget.dimmed and not otherWidget.passage.isStylesheet():
                                ret.append(otherWidget)
        return ret

    def addConnectorLinesToDict(self, displayArrows, imageArrows, flatDesign, lineDictonary, arrowDictonary=None, updateRect=None):
        """
        Appended the connector lines originating from this widget to the list contained in the
        line directory under the appropriate color,width key.
        If an arrow dictionary is also passed it adds the arrows in a similar manner.
        If an update rect is passed it skips any lines, and the associated arrows,
        which lie outside the update rectangle.

        Note: Assumes the list existed in the passed in dictionaries. Either make sure this is the case or
        use a defaultDict.
        """

        colors = PassageWidget.FLAT_COLORS if flatDesign else PassageWidget.COLORS
        # Widths for selected and non selected lines
        widths = 2 * (2 * flatDesign + 1), 1 * (2 * flatDesign + 1)
        widths = max(self.parent.toPixels((widths[0], 0), scaleOnly=True)[0], 2), \
                 max(self.parent.toPixels((widths[1], 0), scaleOnly=True)[0], 1)
        widgets = self.getConnectedWidgets(displayArrows, imageArrows)
        if widgets:
            for widget in widgets:
                link = widget.passage.title

                if self.passage.isAnnotation():
                    color = colors['connectorAnnotation']
                elif (link in self.passage.displays + self.passage.macros) and link not in self.passage.links:
                    color = colors['connectorDisplay']
                elif link in self.passage.images or self.passage.isStylesheet():
                    color = colors['connectorResource']
                else:
                    color = colors['connector']
                width = widths[not self.selected]
                line, arrow = self.getConnectorTo(widget, not arrowDictonary is None, updateRect)
                lineDictonary[(color, width)].extend(line)
                if arrow:
                    arrowDictonary[(color, width)].extend(arrow)


    def getConnectorTo(self, otherWidget, arrowheads=False, updateRect=None):
        # does it actually need to be drawn?
        if otherWidget == self:
            return [], []
        start, end = self.getConnectorLine(otherWidget)
        if updateRect and not geometry.lineRectIntersection([start, end], updateRect):
            return [], []

        line = [[start[0], start[1]], [end[0], end[1]]]

        if not arrowheads:
            return line, []
        else:
            length = max(self.parent.toPixels((PassageWidget.ARROWHEAD_LENGTH, 0), scaleOnly=True)[0], 1)
            arrowheadr = geometry.endPointProjectedFrom((start, end), PassageWidget.ARROWHEAD_ANGLE,  length)
            arrowheadl = geometry.endPointProjectedFrom((start, end), 0 - PassageWidget.ARROWHEAD_ANGLE, length)
        return line, [(arrowheadl, end, arrowheadr)]

    def paint(self, dc):
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

    def getTitleColor(self):
        """
        Returns the title bar style that matches this widget's passage.
        """
        flat = self.app.config.ReadBool('flatDesign')
        # First, rely on the header to supply colours
        custom = self.getHeader().passageTitleColor(self.passage)
        if custom:
            return custom[flat]
        # Use default colours
        if self.passage.isAnnotation():
            ind = 'annotation'
        elif self.passage.isImage():
            ind = 'imageTitleBar'
        elif any(t.startswith('Twine.') for t in self.passage.tags):
            ind = 'privateTitleBar'
        elif not self.linksAndDisplays() and not self.getIncludedLinks() and not self.passage.variableLinks:
            ind = 'endTitleBar'
        else:
            ind = 'titleBar'
        colors = PassageWidget.FLAT_COLORS if flat else PassageWidget.COLORS
        return colors[ind]

    def cachePaint(self, size):
        """
        Caches the widget so self.paintBuffer is up-to-date.
        """

        def wordWrap(text, lineWidth, gc):
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

        # Which set of colors to use
        flat = self.app.config.ReadBool('flatDesign')
        colors = PassageWidget.FLAT_COLORS if flat else PassageWidget.COLORS

        def dim(c, dim, flat=flat):
            """Lowers a color's alpha if dim is true."""
            if isinstance(c, wx.Colour):
                c = list(c.Get(includeAlpha=True))
            elif type(c) is str:
                c = list(ord(a) for a in c[1:].decode('hex'))
            else:
                c = list(c)

            if len(c) < 4:
                c.append(255)
            if dim:
                a = PassageWidget.FLAT_DIMMED_ALPHA if flat else PassageWidget.DIMMED_ALPHA
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
        gc = self.paintBuffer if self.app.config.ReadBool('fastStoryPanel') else wx.GraphicsContext.Create(self.paintBuffer)

        # text font sizes
        # wxWindows works with points, so we need to doublecheck on actual pixels

        titleFontSize = self.parent.toPixels((metrics.size('widgetTitle'), -1), scaleOnly = True)[0]
        titleFontSize = sorted((metrics.size('fontMin'), titleFontSize, metrics.size('fontMax')))[1]
        excerptFontSize = sorted((metrics.size('fontMin'), titleFontSize * 0.9, metrics.size('fontMax')))[1]

        if self.app.config.ReadBool('flatDesign'):
            titleFont = wx.Font(titleFontSize, wx.SWISS, wx.NORMAL, wx.LIGHT, False, 'Arial')
            excerptFont = wx.Font(excerptFontSize, wx.SWISS, wx.NORMAL, wx.LIGHT, False, 'Arial')
        else:
            titleFont = wx.Font(titleFontSize, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Arial')
            excerptFont = wx.Font(excerptFontSize, wx.SWISS, wx.NORMAL, wx.NORMAL, False, 'Arial')
        titleFontHeight = math.fabs(titleFont.GetPixelSize()[1])
        excerptFontHeight = math.fabs(excerptFont.GetPixelSize()[1])
        tagBarColor = dim(tuple(i*256 for i in colorsys.hsv_to_rgb(0.14 + math.sin(hash("".join(self.passage.tags)))*0.08,
                                                                   0.58 if flat else 0.28,
                                                                   0.88)), self.dimmed)
        tags = set(self.passage.tags) - (tiddlywiki.TiddlyWiki.INFO_TAGS | self.getHeader().invisiblePassageTags())

        # inset for text (we need to know this for layout purposes)
        inset = titleFontHeight / 3

        # frame
        if self.passage.isAnnotation():
            frameColor = colors['frame']
            c = wx.Colour(*colors['annotation'])
            frameInterior = (c,c)
        else:
            frameColor = dim(colors['frame'], self.dimmed)
            frameInterior = (dim(colors['bodyStart'], self.dimmed), dim(colors['bodyEnd'], self.dimmed))

        if not flat:
            gc.SetPen(wx.Pen(frameColor, 1))
            if isinstance(gc, wx.GraphicsContext):
                gc.SetBrush(gc.CreateLinearGradientBrush(0, 0, 0, size.height, \
                                                         frameInterior[0], frameInterior[1]))
            else:
                gc.GradientFillLinear(wx.Rect(0, 0, size.width - 1, size.height - 1), \
                                frameInterior[0], frameInterior[1], wx.SOUTH)
                gc.SetBrush(wx.TRANSPARENT_BRUSH)

            gc.DrawRectangle(0, 0, size.width - 1, size.height - 1)
        else:
            gc.SetPen(wx.Pen(frameInterior[0]))
            gc.SetBrush(wx.Brush(frameInterior[0]))
            gc.DrawRectangle(0, 0, size.width, size.height)

        greek = size.width <= PassageWidget.MIN_GREEKING_SIZE * (2 if self.passage.isAnnotation() else 1)

        # title bar
        titleBarHeight = PassageWidget.GREEK_HEIGHT*3 if greek else titleFontHeight + (2 * inset)
        if self.passage.isAnnotation():
            titleBarColor = frameInterior[0]
        else:
            titleBarColor = dim(self.getTitleColor(), self.dimmed)
        gc.SetPen(wx.Pen(titleBarColor, 1))
        gc.SetBrush(wx.Brush(titleBarColor))
        if flat:
            gc.DrawRectangle(0, 0, size.width, titleBarHeight)
        else:
            gc.DrawRectangle(1, 1, size.width - 3, titleBarHeight)

        if not greek:
            # draw title
            # we let clipping prevent writing over the frame
            if isinstance(gc, wx.GraphicsContext):
                gc.ResetClip()
                gc.Clip(inset, inset, size.width - (inset * 2), titleBarHeight - 2)
            else:
                gc.DestroyClippingRegion()
                gc.SetClippingRect(wx.Rect(inset, inset, size.width - (inset * 2), titleBarHeight - 2))

            titleTextColor = dim(colors['titleText'], self.dimmed)

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
                    gc.Clip(inset, inset, size.width - (inset * 2), size.height - (inset * 2)-1)
                else:
                    gc.DestroyClippingRegion()
                    gc.SetClippingRect(wx.Rect(inset, inset, size.width - (inset * 2), size.height - (inset * 2)-1))

                if self.passage.isAnnotation():
                    excerptTextColor = wx.Colour(*colors['annotationText'])
                else:
                    excerptTextColor = dim(colors['excerptText'], self.dimmed)

                if isinstance(gc, wx.GraphicsContext):
                    gc.SetFont(excerptFont, excerptTextColor)
                else:
                    gc.SetFont(excerptFont)
                    gc.SetTextForeground(excerptTextColor)

                excerptLines = wordWrap(self.passage.text, size.width - (inset * 2), gc)

                for line in excerptLines:
                    gc.DrawText(line, inset, excerptTop)
                    excerptTop += excerptFontHeight * PassageWidget.LINE_SPACING \
                        * min(1.75,max(1,1.75*size.width/260 if (self.passage.isAnnotation() and line) else 1))
                    if excerptTop + excerptFontHeight > size.height - inset: break

            if (self.passage.isStoryText() or self.passage.isStylesheet()) and tags:

                tagBarHeight = excerptFontHeight + (2 * inset)
                gc.SetPen(wx.Pen(tagBarColor, 1))
                gc.SetBrush(wx.Brush(tagBarColor))
                gc.DrawRectangle(0, size.height-tagBarHeight-1, size.width, tagBarHeight+1)

                # draw tags

                tagTextColor = dim(colors['frame'], self.dimmed)

                if isinstance(gc, wx.GraphicsContext):
                    gc.SetFont(excerptFont, tagTextColor)
                else:
                    gc.SetFont(excerptFont)
                    gc.SetTextForeground(tagTextColor)

                text = wordWrap(' '.join(tags), size.width - (inset * 2), gc)[0]

                gc.DrawText(text, inset*2, (size.height-tagBarHeight))
        else:
            # greek title

            gc.SetPen(wx.Pen(colors['titleText'], PassageWidget.GREEK_HEIGHT))
            height = inset
            width = (size.width - inset) / 2

            if isinstance(gc, wx.GraphicsContext):
                gc.StrokeLine(inset, height, width, height)
            else:
                gc.DrawLine(inset, height, width, height)

            height += PassageWidget.GREEK_HEIGHT * 3

            # greek body text
            if not self.passage.isImage():

                gc.SetPen(wx.Pen(colors['annotationText'] \
                    if self.passage.isAnnotation() else colors['greek'], PassageWidget.GREEK_HEIGHT))

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

            if (self.passage.isStoryText() or self.passage.isStylesheet()) and tags:

                tagBarHeight = PassageWidget.GREEK_HEIGHT*3
                gc.SetPen(wx.Pen(tagBarColor, 1))
                gc.SetBrush(wx.Brush(tagBarColor))
                height = size.height-tagBarHeight-2
                width = size.width-4
                gc.DrawRectangle(2, height, width, tagBarHeight)

                gc.SetPen(wx.Pen(colors['greek'], PassageWidget.GREEK_HEIGHT))
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

                width = size.width
                height = size.height - titleBarHeight

                # choose smaller of vertical and horizontal scale factor, to preserve aspect ratio
                scale = min(width/float(self.bitmap.GetWidth()), height/float(self.bitmap.GetHeight()))

                img = self.bitmap.ConvertToImage()
                if scale != 1:
                    img = img.Scale(scale*self.bitmap.GetWidth(),scale*self.bitmap.GetHeight())

                # offset image horizontally or vertically, to centre after scaling
                offsetWidth = (width - img.GetWidth())/2
                offsetHeight = (height - img.GetHeight())/2
                if isinstance(gc, wx.GraphicsContext):
                    gc.DrawBitmap(img.ConvertToBitmap(self.bitmap.GetDepth()),
                                  1 + offsetWidth, titleBarHeight + 1 + offsetHeight,
                                  img.GetWidth(), img.GetHeight())
                else:
                    gc.DrawBitmap(img.ConvertToBitmap(self.bitmap.GetDepth()),
                                  1 + offsetWidth, titleBarHeight + 1 + offsetHeight)

        if isinstance(gc, wx.GraphicsContext):
            gc.ResetClip()
        else:
            gc.DestroyClippingRegion()

        # draw a broken link emblem in the bottom right if necessary
        # fixme: not sure how to do this with transparency

        def showEmblem(emblem, gc=gc, size=size, inset=inset):
            emblemSize = emblem.GetSize()
            emblemPos = [ size.width - (emblemSize[0] + inset), \
                          size.height - (emblemSize[1] + inset) ]

            if isinstance(gc, wx.GraphicsContext):
                gc.DrawBitmap(emblem, emblemPos[0], emblemPos[1], emblemSize[0], emblemSize[1])
            else:
                gc.DrawBitmap(emblem, emblemPos[0], emblemPos[1])

        if len(self.getBrokenLinks()):
            showEmblem(self.brokenEmblem)
        elif len(self.getIncludedLinks()) or len(self.passage.variableLinks):
            showEmblem(self.externalEmblem)

        # finally, draw a selection over ourselves if we're selected

        if self.selected:
            color = dim(titleBarColor if flat else wx.SystemSettings_GetColour(wx.SYS_COLOUR_HIGHLIGHT), self.dimmed)
            if self.app.config.ReadBool('fastStoryPanel'):
                gc.SetPen(wx.Pen(color, 2 + flat))
            else:
                gc.SetPen(wx.TRANSPARENT_PEN)

            if isinstance(gc, wx.GraphicsContext):
                r, g, b = color.Get(False)
                color = wx.Colour(r, g, b, 64)
                gc.SetBrush(wx.Brush(color))
            else:
                gc.SetBrush(wx.TRANSPARENT_BRUSH)

            gc.DrawRectangle(0, 0, size.width, size.height)

        self.paintBufferBounds = size

    def serialize(self):
        """Returns a dictionary with state information suitable for pickling."""
        return { 'selected': self.selected, 'pos': self.pos, 'passage': copy.copy(self.passage) }

    @staticmethod
    def posCompare(first, second):
        """
        Sorts PassageWidgets so that the results appear left to right,
        top to bottom. A certain amount of slack is assumed here in
        terms of positioning.
        """

        yDistance = int(first.pos[1] - second.pos[1])
        if abs(yDistance) > 5:
            return yDistance

        xDistance = int(first.pos[0] - second.pos[0])
        if xDistance != 0:
            return xDistance

        return id(first) - id(second) # punt on ties

    def __repr__(self):
        return "<PassageWidget '" + self.passage.title + "'>"

    def getHeader(self):
        """Returns the current selected target header for this Passage Widget."""
        return self.parent.getHeader()

    MIN_PIXEL_SIZE = 10
    MIN_GREEKING_SIZE = 50
    GREEK_HEIGHT = 2
    SIZE = 120
    SHADOW_SIZE = 5
    COLORS = {
               'frame': (0, 0, 0), \
               'bodyStart': (255, 255, 255), \
               'bodyEnd': (212, 212, 212), \
               'annotation': (85, 87, 83), \
               'endTitleBar': (16, 51, 96), \
               'titleBar': (52, 101, 164), \
               'imageTitleBar': (8, 138, 133), \
               'privateTitleBar': (130, 130, 130), \
               'titleText': (255, 255, 255), \
               'excerptText': (0, 0, 0), \
               'annotationText': (255,255,255), \
               'greek': (102, 102, 102),
               'connector': (186, 189, 182),
               'connectorDisplay': (132, 164, 189),
               'connectorResource': (110, 112, 107),
               'connectorAnnotation': (0, 0, 0),
            }
    FLAT_COLORS = {
               'frame': (0, 0, 0),
               'bodyStart':  (255, 255, 255),
               'bodyEnd':  (255, 255, 255),
               'annotation': (212, 212, 212),
               'endTitleBar': (36, 54, 219),
               'titleBar': (36, 115, 219),
               'imageTitleBar': (36, 219, 213),
               'privateTitleBar': (153, 153, 153),
               'titleText': (255, 255, 255),
               'excerptText': (96, 96, 96),
               'annotationText': (0,0,0),
               'greek': (192, 192, 192),
               'connector': (143, 148, 137),
               'connectorDisplay': (137, 193, 235),
               'connectorResource': (186, 188, 185),
               'connectorAnnotation': (255, 255, 255),
               'selection': (28, 102, 176)
            }
    DIMMED_ALPHA = 0.5
    FLAT_DIMMED_ALPHA = 0.9
    LINE_SPACING = 1.2
    CONNECTOR_WIDTH = 2.0
    CONNECTOR_SELECTED_WIDTH = 5.0
    ARROWHEAD_LENGTH = 10
    MIN_ARROWHEAD_LENGTH = 5
    ARROWHEAD_ANGLE = math.pi / 6

# contextual menu

class PassageWidgetContext(wx.Menu):
    def __init__(self, parent):
        wx.Menu.__init__(self)
        self.parent = parent
        title = '"' + parent.passage.title + '"'

        if parent.passage.isStoryPassage():
            test = wx.MenuItem(self, wx.NewId(), 'Test Play From Here')
            self.AppendItem(test)
            self.Bind(wx.EVT_MENU, lambda e: self.parent.parent.parent.testBuild(startAt = parent.passage.title), id = test.GetId())

        edit = wx.MenuItem(self, wx.NewId(), 'Edit ' + title)
        self.AppendItem(edit)
        self.Bind(wx.EVT_MENU, self.parent.openEditor, id = edit.GetId())

        delete = wx.MenuItem(self, wx.NewId(), 'Delete ' + title)
        self.AppendItem(delete)
        self.Bind(wx.EVT_MENU, lambda e: self.parent.parent.removeWidget(self.parent.passage.title), id = delete.GetId())


