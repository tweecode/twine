from collections import defaultdict
from itertools import izip, chain
import sys, wx, re, pickle
import geometry
from tiddlywiki import TiddlyWiki
from passagewidget import PassageWidget

class StoryPanel(wx.ScrolledWindow):
    """
    A StoryPanel is a container for PassageWidgets. It translates
    between logical coordinates and pixel coordinates as the user
    zooms in and out, and communicates those changes to its widgets.

    A discussion on coordinate systems: logical coordinates are notional,
    and do not change as the user zooms in and out. Pixel coordinates
    are extremely literal: (0, 0) is the top-left corner visible to the
    user, no matter where the scrollbar position is.

    This class (and PassageWidget) deal strictly in logical coordinates, but
    incoming events are in pixel coordinates. We convert these to logical
    coordinates as soon as possible.
    """

    def __init__(self, parent, app, id = wx.ID_ANY, state = None):
        wx.ScrolledWindow.__init__(self, parent, id)
        self.app = app
        self.parent = parent

        # inner state

        self.snapping = self.app.config.ReadBool('storyPanelSnap')
        self.widgetDict = dict()
        self.visibleWidgets = None
        self.includedPassages = set()
        self.draggingMarquee = False
        self.draggingWidgets = None
        self.notDraggingWidgets = None
        self.undoStack = []
        self.undoPointer = -1
        self.lastSearchRegexp = None
        self.lastSearchFlags = None
        self.lastScrollPos = -1
        self.trackinghover = None
        self.tooltiptimer = wx.PyTimer(self.tooltipShow)
        self.tooltipplace = None
        self.tooltipobj = None
        self.textDragSource = None

        if state:
            self.scale = state['scale']
            for widget in state['widgets']:
                pw = PassageWidget(self, self.app, state = widget)
                self.widgetDict[pw.passage.title] = pw
            if 'snapping' in state:
                self.snapping = state['snapping']
        else:
            self.scale = 1
            for title in ('Start', 'StoryTitle', 'StoryAuthor'):
                self.newWidget(title = title, text = self.parent.defaultTextForPassage(title), quietly = True)

        self.pushUndo(action = '')
        self.undoPointer -= 1

        # cursors

        self.dragCursor = wx.StockCursor(wx.CURSOR_SIZING)
        self.badDragCursor = wx.StockCursor(wx.CURSOR_NO_ENTRY)
        self.scrollCursor = wx.StockCursor(wx.CURSOR_SIZING)
        self.defaultCursor = wx.StockCursor(wx.CURSOR_ARROW)
        self.SetCursor(self.defaultCursor)

        # events

        self.SetDropTarget(StoryPanelDropTarget(self))
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: e)
        self.Bind(wx.EVT_PAINT, self.paint)
        self.Bind(wx.EVT_SIZE, self.resize)
        self.Bind(wx.EVT_LEFT_DOWN, self.handleClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.handleDoubleClick)
        self.Bind(wx.EVT_RIGHT_UP, self.handleRightClick)
        self.Bind(wx.EVT_MIDDLE_UP, self.handleMiddleClick)
        self.Bind(wx.EVT_ENTER_WINDOW, self.handleHoverStart)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.handleHoverStop)
        self.Bind(wx.EVT_MOTION, self.handleHover)

    def newWidget(self, title = None, text = '', tags = (), pos = None, quietly = False, logicals = False):
        """Adds a new widget to the container."""

        # defaults

        if not title:
            if tags and tags[0] in TiddlyWiki.INFO_TAGS:
                type = "Untitled " + tags[0].capitalize()
            else:
                type = "Untitled Passage"
            title = self.untitledName(type)
        if not pos: pos = StoryPanel.INSET
        if not logicals: pos = self.toLogical(pos)

        new = PassageWidget(self, self.app, title = title, text = text, tags = tags, pos = pos)
        self.widgetDict[new.passage.title] = new
        self.snapWidget(new, quietly)
        self.resize()
        self.Refresh()
        if not quietly: self.parent.setDirty(True, action = 'New Passage')
        return new

    def changeWidgetTitle(self, oldTitle, newTitle):
        widget = self.widgetDict.pop(oldTitle)
        widget.passage.title = newTitle
        self.widgetDict[newTitle] = widget

    def snapWidget(self, widget, quickly = False):
        """
        Snaps a widget to our grid if self.snapping is set.
        Then, call findSpace()
        """
        if self.snapping:
            pos = list(widget.pos)

            for coord in range(2):
                distance = pos[coord] % StoryPanel.GRID_SPACING
                if distance > StoryPanel.GRID_SPACING / 2:
                    pos[coord] += StoryPanel.GRID_SPACING - distance
                else:
                    pos[coord] -= distance
                pos[coord] += StoryPanel.INSET[coord]

            widget.pos = pos
            self.Refresh()
        if quickly:
            widget.findSpaceQuickly()
        else:
            widget.findSpace()

    def cleanup(self):
        """Snaps all widgets to the grid."""
        oldSnapping = self.snapping
        self.snapping = True
        self.eachWidget(self.snapWidget)
        self.snapping = oldSnapping
        self.parent.setDirty(True, action = 'Clean Up')
        self.Refresh()

    def toggleSnapping(self):
        """Toggles whether snapping is on."""
        self.snapping = self.snapping is not True
        self.app.config.WriteBool('storyPanelSnap', self.snapping)

    def copyWidgets(self):
        """Copies selected widgets into the clipboard."""
        data = []
        for widget in self.widgetDict.itervalues():
            if widget.selected: data.append(widget.serialize())

        clipData = wx.CustomDataObject(wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT))
        clipData.SetData(pickle.dumps(data, 1))

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipData)
            wx.TheClipboard.Close()

    def cutWidgets(self):
        """Cuts selected widgets into the clipboard."""
        self.copyWidgets()
        self.removeWidgets()
        self.Refresh()

    def pasteWidgets(self, pos = (0,0), logicals = False):
        """Pastes widgets from the clipboard."""
        clipFormat = wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT)
        clipData = wx.CustomDataObject(clipFormat)

        if wx.TheClipboard.Open():
            gotData = wx.TheClipboard.IsSupported(clipFormat) and wx.TheClipboard.GetData(clipData)
            wx.TheClipboard.Close()

            if gotData:
                data = pickle.loads(clipData.GetData())

                self.eachWidget(lambda w: w.setSelected(False, False))

                if not pos: pos = StoryPanel.INSET
                if not logicals: pos = self.toLogical(pos)

                for widget in data:
                    newPassage = PassageWidget(self, self.app, state = widget, pos = pos, title = self.untitledName(widget['passage'].title))
                    newPassage.findSpace()
                    newPassage.setSelected(True, False)
                    self.widgetDict[newPassage.passage.title] = newPassage
                    self.snapWidget(newPassage, False)

                self.parent.setDirty(True, action = 'Paste')
                self.resize()
                self.Refresh()


    def removeWidget(self, title, saveUndo = True):
        """
        Deletes a passed widget. You can ask this to save an undo state manually,
        but by default, it doesn't.
        """
        widget = self.widgetDict.pop(title, None)
        if widget is None:
            return

        if widget in self.visibleWidgets: self.visibleWidgets.remove(widget)
        if self.tooltipplace is widget:
            self.tooltipplace = None
        if saveUndo: self.parent.setDirty(True, action = 'Delete')
        self.Refresh()

    def removeWidgets(self, event = None, saveUndo = True):
        """
        Deletes all selected widgets. You can ask this to save an undo state manually,
        but by default, it doesn't.
        """

        selected = set(
            title
            for title, widget in self.widgetDict.iteritems()
            if widget.selected
            )

        connected = set(
            title
            for title, widget in self.widgetDict.iteritems()
            if not widget.selected and selected.intersection(widget.linksAndDisplays())
            )

        if connected:
            message = 'Are you sure you want to delete ' + \
                      (('"' + next(iter(selected)) + '"? Links to it') if len(selected) == 1 else
                      (str(len(selected)) + ' passages? Links to them')) + \
                       ' from ' + \
                      (('"' + next(iter(connected)) + '"') if len(connected) == 1 else
                      (str(len(connected)) + ' other passages')) + \
                      ' will become broken.'
            dialog = wx.MessageDialog(self.parent, message,
                                      'Delete Passage' + ('s' if len(selected) > 1 else ''), \
                                      wx.ICON_WARNING | wx.OK | wx.CANCEL )

            if dialog.ShowModal() != wx.ID_OK:
                return

        for title in selected:
            self.removeWidget(title, saveUndo)

    def findWidgetRegexp(self, regexp = None, flags = None):
        """
        Finds the next PassageWidget that matches the regexp passed.
        You may leave off the regexp, in which case it uses the last
        search performed. This begins its search from the current selection.
        If nothing is found, then an error alert is shown.
        """

        if regexp is None:
            regexp = self.lastSearchRegexp
            flags = self.lastSearchFlags

        self.lastSearchRegexp = regexp
        self.lastSearchFlags = flags

        # find the current selection
        # if there are multiple selections, we just use the first

        i = -1

        # look for selected PassageWidgets
        widgets = self.widgetDict.values()
        for num, widget in enumerate(widgets):
            if widget.selected:
                i = num
                break

        # if no widget is selected, start at first widget
        if i==len(widgets)-1:
            i=-1

        for widget in widgets:
            if widget.containsRegexp(regexp, flags):
                widget.setSelected(True)
                self.scrollToWidget(widget)
                return
            i += 1

        # fallthrough: text not found

        dialog = wx.MessageDialog(self, 'The text you entered was not found in your story.', \
                                  'Not Found', wx.ICON_INFORMATION | wx.OK)
        dialog.ShowModal()

    def replaceRegexpInSelectedWidget(self, findRegexp, replacementRegexp, flags):
        for widget in self.widgetDict.values():
            if widget.selected:
                widget.replaceRegexp(findRegexp, replacementRegexp, flags)
                widget.clearPaintCache()
                self.Refresh()
                self.parent.setDirty(True, action = 'Replace in Currently Selected Widget')

    def replaceRegexpInWidgets(self, findRegexp, replacementRegexp, flags):
        """
        Performs a string replace on all widgets in this StoryPanel.
        It shows an alert once done to tell the user how many replacements were
        made.
        """
        replacements = 0

        for widget in self.widgetDict.values():
            replacements += widget.replaceRegexp(findRegexp, replacementRegexp, flags)

        if replacements > 0:
            self.Refresh()
            self.parent.setDirty(True, action = 'Replace Across Entire Story')

        message = '%d replacement' % replacements
        if replacements != 1:
            message += 's were '
        else:
            message += ' was '
        message += 'made in your story.'

        dialog = wx.MessageDialog(self, message, 'Replace Complete', wx.ICON_INFORMATION | wx.OK)
        dialog.ShowModal()

    def scrollToWidget(self, widget):
        """
        Scrolls so that the widget passed is visible.
        """
        widgetRect = widget.getPixelRect()
        xUnit,yUnit = self.GetScrollPixelsPerUnit()
        sx = (widgetRect.x-20) / float(xUnit)
        sy = (widgetRect.y-20) / float(yUnit)
        self.Scroll(max(sx, 0), max(sy - 20, 0))

    def pushUndo(self, action):
        """
        Pushes the current state onto the undo stack. The name parameter describes
        the action that triggered this call, and is displayed in the Undo menu.
        """

        # delete anything above the undoPointer

        while self.undoPointer < len(self.undoStack) - 2: self.undoStack.pop()

        # add a new state onto the stack

        state = { 'action': action, 'widgets': [] }
        for widget in self.widgetDict.itervalues(): state['widgets'].append(widget.serialize())
        self.undoStack.append(state)
        self.undoPointer += 1

    def undo(self):
        """
        Restores the undo state at self.undoPointer to the current view, then
        decreases self.undoPointer by 1.
        """
        self.widgetDict = dict()
        self.visibleWidgets = None
        state = self.undoStack[self.undoPointer]
        for widgetState in state['widgets']:
            widget = PassageWidget(self, self.app, state = widgetState)
            self.widgetDict[widget.passage.title] = widget
        self.undoPointer -= 1
        self.Refresh()

    def redo(self):
        """
        Moves the undo pointer up 2, then calls undo() to restore state.
        """
        self.undoPointer += 2
        self.undo()

    def canUndo(self):
        """Returns whether an undo is available to the user."""
        return self.undoPointer > -1

    def undoAction(self):
        """Returns the name of the action that the user will be undoing."""
        return self.undoStack[self.undoPointer + 1]['action']

    def canRedo(self):
        """Returns whether a redo is available to the user."""
        return self.undoPointer < len(self.undoStack) - 2

    def redoAction(self):
        """Returns the name of the action that the user will be redoing."""
        return self.undoStack[self.undoPointer + 2]['action']

    def handleClick(self, event):
        """
        Passes off execution to either startMarquee or startDrag,
        depending on whether the user clicked a widget.
        """
        # start a drag if the user clicked a widget
        # or a marquee if they didn't

        for widget in self.widgetDict.itervalues():
            if widget.getPixelRect().Contains(event.GetPosition()):
                if not widget.selected: widget.setSelected(True, not event.ShiftDown())
                self.startDrag(event, widget)
                return
        self.startMarquee(event)

    def handleDoubleClick(self, event):
        """Dispatches an openEditor() call to a widget the user clicked."""
        for widget in self.widgetDict.itervalues():
            if widget.getPixelRect().Contains(event.GetPosition()): widget.openEditor()

    def handleRightClick(self, event):
        """Either opens our own contextual menu, or passes it off to a widget."""
        for widget in self.widgetDict.itervalues():
            if widget.getPixelRect().Contains(event.GetPosition()):
                widget.openContextMenu(event)
                return
        self.PopupMenu(StoryPanelContext(self, event.GetPosition()), event.GetPosition())

    def handleMiddleClick(self, event):
        """Creates a new widget centered at the mouse position."""
        pos = event.GetPosition()
        offset = self.toPixels((PassageWidget.SIZE / 2, 0), scaleOnly = True)
        pos.x = pos.x - offset[0]
        pos.y = pos.y - offset[0]
        self.newWidget(pos = pos)

    def startMarquee(self, event):
        """Starts a marquee selection."""
        if not self.draggingMarquee:
            self.draggingMarquee = True
            self.dragOrigin = event.GetPosition()
            self.dragCurrent = event.GetPosition()
            self.dragRect = geometry.pointsToRect(self.dragOrigin, self.dragOrigin)

            # deselect everything

            for widget in self.widgetDict.itervalues():
                widget.setSelected(False, False)

            # grab mouse focus

            self.Bind(wx.EVT_MOUSE_EVENTS, self.followMarquee)
            self.CaptureMouse()
            self.Refresh()

    def followMarquee(self, event):
        """
        Follows the mouse during a marquee selection.
        """
        if event.LeftIsDown():
            # scroll and adjust coordinates

            offset = self.scrollWithMouse(event)
            self.oldDirtyRect = self.dragRect.Inflate(2, 2)
            self.oldDirtyRect.x -= offset[0]
            self.oldDirtyRect.y -= offset[1]

            self.dragCurrent = event.GetPosition()
            self.dragOrigin.x -= offset[0]
            self.dragOrigin.y -= offset[1]
            self.dragCurrent.x -= offset[0]
            self.dragCurrent.y -= offset[1]

            # dragRect is what is drawn onscreen
            # it is in unscrolled coordinates

            self.dragRect = geometry.pointsToRect(self.dragOrigin, self.dragCurrent)

            # select all enclosed widgets

            logicalOrigin = self.toLogical(self.CalcUnscrolledPosition(self.dragRect.x, self.dragRect.y), scaleOnly = True)
            logicalSize = self.toLogical((self.dragRect.width, self.dragRect.height), scaleOnly = True)
            logicalRect = wx.Rect(logicalOrigin[0], logicalOrigin[1], logicalSize[0], logicalSize[1])

            for widget in self.widgetDict.itervalues():
                widget.setSelected(widget.intersects(logicalRect), False)

            self.Refresh(True, self.oldDirtyRect.Union(self.dragRect))
        else:
            self.draggingMarquee = False

            # clear event handlers

            self.Bind(wx.EVT_MOUSE_EVENTS, None)
            self.ReleaseMouse()
            self.Refresh()

    def startDrag(self, event, clickedWidget):
        """
        Starts a widget drag. The initial event is caught by PassageWidget, but
        it passes control to us so that we can move all selected widgets at once.
        """
        if not self.draggingWidgets or not len(self.draggingWidgets):
            # cache the sets of dragged vs not-dragged widgets
            self.draggingWidgets = []
            self.notDraggingWidgets = []
            self.clickedWidget = clickedWidget
            self.actuallyDragged = False
            self.dragCurrent = event.GetPosition()
            self.oldDirtyRect = clickedWidget.getPixelRect()

            # have selected widgets remember their original position
            # in case they need to snap back to it after a bad drag

            for widget in self.widgetDict.itervalues():
                if widget.selected:
                    self.draggingWidgets.append(widget)
                    widget.predragPos = widget.pos
                else:
                    self.notDraggingWidgets.append(widget)

            # grab mouse focus

            self.Bind(wx.EVT_MOUSE_EVENTS, self.followDrag)
            self.CaptureMouse()

    def followDrag(self, event):
        """Follows mouse motions during a widget drag."""
        if event.LeftIsDown():
            self.actuallyDragged = True
            pos = event.GetPosition()

            # find change in position
            deltaX = pos[0] - self.dragCurrent[0]
            deltaY = pos[1] - self.dragCurrent[1]

            deltaX = self.toLogical((deltaX, -1), scaleOnly = True)[0]
            deltaY = self.toLogical((deltaY, -1), scaleOnly = True)[0]

            # offset selected passages

            for widget in self.draggingWidgets: widget.offset(deltaX, deltaY)
            self.dragCurrent = pos

            # if there any overlaps, then warn the user with a bad drag cursor

            goodDrag = True

            for widget in self.draggingWidgets:
                if widget.intersectsAny(dragging = True):
                    goodDrag = False
                    break

            # in fast drawing, we dim passages
            # to indicate no connectors should be drawn for them
            # while dragging is occurring
            #
            # in slow drawing, we dim passages
            # to indicate you're not allowed to drag there

            for widget in self.draggingWidgets:
                widget.setDimmed(self.app.config.ReadBool('fastStoryPanel') or not goodDrag)

            if goodDrag: self.SetCursor(self.dragCursor)
            else: self.SetCursor(self.badDragCursor)

            # scroll in response to the mouse,
            # and shift passages accordingly

            widgetScroll = self.toLogical(self.scrollWithMouse(event), scaleOnly = True)
            for widget in self.draggingWidgets: widget.offset(widgetScroll[0], widgetScroll[1])

            # figure out our dirty rect

            dirtyRect = self.oldDirtyRect
            for widget in self.draggingWidgets:
                dirtyRect.Union(widget.getDirtyPixelRect())
                for link in widget.linksAndDisplays():
                    widget2 = self.findWidget(link)
                    if widget2:
                        dirtyRect.Union(widget2.getDirtyPixelRect())

            self.Refresh(True, dirtyRect)
        else:

            if self.actuallyDragged:
                # is this a bad drag?

                goodDrag = True

                for widget in self.draggingWidgets:
                    if widget.intersectsAny(dragging = True):
                        goodDrag = False
                        break

                if goodDrag:
                    for widget in self.draggingWidgets:
                        self.snapWidget(widget)
                        widget.setDimmed(False)
                    if widget.pos != widget.predragPos:
                        self.parent.setDirty(True, action = 'Move')
                    self.resize()
                else:
                    for widget in self.draggingWidgets:
                        widget.pos = widget.predragPos
                        widget.setDimmed(False)

                self.Refresh()

            else:
                # change the selection
                self.clickedWidget.setSelected(True, not event.ShiftDown())

            # general cleanup
            self.draggingWidgets = None
            self.notDraggingWidgets = None
            self.Bind(wx.EVT_MOUSE_EVENTS, None)
            self.ReleaseMouse()
            self.SetCursor(self.defaultCursor)

    def scrollWithMouse(self, event):
        """
        If the user has moved their mouse outside the window
        bounds, this tries to scroll to keep up. This returns a tuple
        of pixels of the scrolling; if none has happened, it returns (0, 0).
        """
        pos = event.GetPosition()
        size = self.GetSize()
        scroll = [0, 0]
        changed = False

        if pos.x < 0:
            scroll[0] = -1
            changed = True
        else:
            if pos.x > size[0]:
                scroll[0] = 1
                changed = True

        if pos.y < 0:
            scroll[1] = -1
            changed = True
        else:
            if pos.y > size[1]:
                scroll[1] = 1
                changed = True

        pixScroll = [0, 0]

        if changed:
            # scroll the window

            oldPos = self.GetViewStart()
            self.Scroll(oldPos[0] + scroll[0], oldPos[1] + scroll[1])

            # return pixel change
            # check to make sure we actually were able to scroll the direction we asked

            newPos = self.GetViewStart()

            if oldPos[0] != newPos[0]:
                pixScroll[0] = scroll[0] * StoryPanel.SCROLL_SPEED
            if oldPos[1] != newPos[1]:
                pixScroll[1] = scroll[1] * StoryPanel.SCROLL_SPEED

        return pixScroll

    def untitledName(self, base = 'Untitled Passage'):
        """Returns a string for an untitled PassageWidget."""
        number = 1

        if not base.startswith('Untitled ') and base not in self.widgetDict:
            return base

        for widget in self.widgetDict.itervalues():
            match = re.match(re.escape(base) + ' (\d+)', widget.passage.title)
            if match: number = int(match.group(1)) + 1

        return base + ' ' + str(number)

    def eachWidget(self, function):
        """Runs a function on every passage in the panel."""
        for widget in self.widgetDict.values():
            function(widget)

    def sortedWidgets(self):
        """Returns a sorted list of widgets, left to right, top to bottom."""
        return sorted(self.widgetDict.itervalues(), PassageWidget.posCompare)

    def taggedWidgets(self, tag):
        """Returns widgets that have the given tag"""
        return (a for a in self.widgetDict.itervalues() if tag in a.passage.tags)

    def selectedWidget(self):
        """Returns any one selected widget."""
        for widget in self.widgetDict.itervalues():
            if widget.selected: return widget
        return None

    def eachSelectedWidget(self, function):
        """Runs a function on every selected passage in the panel."""
        for widget in self.widgetDict.values():
            if widget.selected: function(widget)

    def hasSelection(self):
        """Returns whether any passages are selected."""
        for widget in self.widgetDict.itervalues():
            if widget.selected: return True
        return False

    def hasMultipleSelection(self):
        """Returns 0 if no passages are selected, one if one or two if two or more are selected."""
        selected = 0
        for widget in self.widgetDict.itervalues():
            if widget.selected:
                selected += 1
                if selected > 1:
                    return selected
        return selected

    def findWidget(self, title):
        """Returns a PassageWidget with the title passed. If none exists, it returns None."""
        return self.widgetDict.get(title)

    def passageExists(self, title, includeIncluded = True):
        """
        Returns whether a given passage exists in the story.

        If includeIncluded then will also check external passages referenced via StoryIncludes
        """
        return title in self.widgetDict or (includeIncluded and self.includedPassageExists(title))

    def clearIncludedPassages(self):
        """Clear the includedPassages set"""
        self.includedPassages.clear()

    def addIncludedPassage(self, title):
        """Add a title to the set of external passages"""
        self.includedPassages.add(title)

    def includedPassageExists(self, title):
        """Add a title to the set of external passages"""
        return title in self.includedPassages

    def refreshIncludedPassageList(self):
        def callback(passage):
            if passage.title == 'StoryIncludes' or passage.title in self.widgetDict:
                return
            self.addIncludedPassage(passage.title)

        self.clearIncludedPassages()

        widget = self.widgetDict.get('StoryIncludes')
        if widget is not None:
            self.parent.readIncludes(widget.passage.text.splitlines(), callback, silent = True)

    def toPixels(self, logicals, scaleOnly = False):
        """
        Converts a tuple of logical coordinates to pixel coordinates. If you need to do just
        a straight conversion from logicals to pixels without worrying about where the scrollbar
        is, then call with scaleOnly set to True.
        """
        converted = (logicals[0] * self.scale, logicals[1] * self.scale)
        if scaleOnly:
            return converted
        return self.CalcScrolledPosition(converted)


    def toLogical(self, pixels, scaleOnly = False):
        """
        Converts a tuple of pixel coordinates to logical coordinates. If you need to do just
        a straight conversion without worrying about where the scrollbar is, then call with
        scaleOnly set to True.
        """
        # order of operations here is important, though I don't totally understand why

        if scaleOnly:
            converted = pixels
        else:
            converted = self.CalcUnscrolledPosition(pixels)

        converted = (converted[0] / self.scale, converted[1] / self.scale)
        return converted

    def getSize(self):
        """
        Returns a tuple (width, height) of the smallest rect needed to
        contain all children widgets.
        """
        width, height = 0, 0

        for i in self.widgetDict.itervalues():
            rightSide = i.pos[0] + i.getSize()[0]
            bottomSide = i.pos[1] + i.getSize()[1]
            width = max(width, rightSide)
            height = max(height, bottomSide)
        return (width, height)

    def zoom(self, scale):
        """
        Sets zoom to a certain level. Pass a number to set the zoom
        exactly, pass 'in' or 'out' to zoom relatively, and 'fit'
        to set the zoom so that all children are visible.
        """
        oldScale = self.scale

        if isinstance(scale, float):
            self.scale = scale
        elif scale == 'in':
            self.scale += 0.2
        elif scale == 'out':
            self.scale -= 0.2
        elif scale == 'fit':
            self.zoom(1.0)
            neededSize = self.toPixels(self.getSize(), scaleOnly = True)
            actualSize = self.GetSize()
            widthRatio = actualSize.width / neededSize[0]
            heightRatio = actualSize.height / neededSize[1]
            self.scale = min(widthRatio, heightRatio)
            self.Scroll(0, 0)

        self.scale = max(self.scale, 0.2)
        scaleDelta = self.scale - oldScale

        # figure out what our scroll bar positions should be moved to
        # to keep in scale

        origin = list(self.GetViewStart())
        origin[0] += scaleDelta * origin[0]
        origin[1] += scaleDelta * origin[1]

        self.resize()
        self.Refresh()
        self.Scroll(origin[0], origin[1])
        self.parent.updateUI()




    def arrowPolygonsToLines(self, list):
        for polygon in list:
            yield polygon[0][0], polygon[0][1], polygon[1][0], polygon[1][1]
            yield polygon[1][0], polygon[1][1], polygon[2][0], polygon[2][1]

    def paint(self, event):
        """Paints marquee selection, widget connectors, and widgets onscreen."""
        # do NOT call self.DoPrepareDC() no matter what the docs may say
        # we already take into account our scroll origin in our
        # toPixels() method

        # OS X already double buffers drawing for us; if we try to do it
        # ourselves, performance is horrendous

        if sys.platform == 'darwin':
            gc = wx.PaintDC(self)
        else:
            gc = wx.BufferedPaintDC(self)

        updateRect = self.updateVisableRectsAndReturnUpdateRegion()

        # background

        gc.SetBrush(wx.Brush(StoryPanel.FLAT_BG_COLOR if self.app.config.ReadBool('flatDesign')
                             else StoryPanel.BACKGROUND_COLOR))
        gc.DrawRectangle(updateRect.x - 1, updateRect.y - 1, updateRect.width + 2, updateRect.height + 2)

        # connectors
        arrowheads = (self.scale > StoryPanel.ARROWHEAD_THRESHOLD)
        lineDictonary = defaultdict(list)
        arrowDictonary = defaultdict(list) if arrowheads else None
        displayArrows = self.app.config.ReadBool('displayArrows')
        imageArrows = self.app.config.ReadBool('imageArrows')
        flatDesign = self.app.config.ReadBool('flatDesign')
        for widget in self.visibleWidgets:
            if not widget.dimmed:
                widget.addConnectorLinesToDict(displayArrows, imageArrows, flatDesign, lineDictonary, arrowDictonary, updateRect)

        for (color, width) in lineDictonary.iterkeys():
            gc.SetPen(wx.Pen(color, width))
            lines = list(izip(*[iter(chain(*lineDictonary[(color, width)]))] * 4))
            gc.DrawLineList(lines)
        if arrowheads:
            for (color, width) in arrowDictonary.iterkeys():
                gc.SetPen(wx.Pen(color, width))
                arrows = arrowDictonary[(color, width)]
                if self.app.config.ReadBool('flatDesign'):
                    gc.SetBrush(wx.Brush(color))
                    gc.DrawPolygonList(arrows)
                else:
                    lines = list(self.arrowPolygonsToLines(arrows))
                    gc.DrawLineList(lines)

        for widget in self.visibleWidgets:
            # Could be "visible" only insofar as its arrow is visible
            if updateRect.Intersects(widget.getPixelRect()):
                widget.paint(gc)

        # marquee selection
        # with slow drawing, use alpha blending for interior

        if self.draggingMarquee:
            if self.app.config.ReadBool('fastStoryPanel'):
                gc.SetPen(wx.Pen('#ffffff', 1, wx.DOT))
                gc.SetBrush(wx.Brush(wx.WHITE, wx.TRANSPARENT))
            else:
                gc = wx.GraphicsContext.Create(gc)
                marqueeColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
                gc.SetPen(wx.Pen(marqueeColor))
                r, g, b = marqueeColor.Get(False)
                marqueeColor = wx.Colour(r, g, b, StoryPanel.MARQUEE_ALPHA)
                gc.SetBrush(wx.Brush(marqueeColor))

            gc.DrawRectangle(self.dragRect.x, self.dragRect.y, self.dragRect.width, self.dragRect.height)


    def updateVisableRectsAndReturnUpdateRegion(self):
        """
        Updates the self.visibleWidgets list if necessary based on the current scroll position.
        :return: The update region that would need to be redrawn
        """
        # Determine visible passages
        updateRect = self.GetUpdateRegion().GetBox()
        scrollPos = (self.GetScrollPos(wx.HORIZONTAL), self.GetScrollPos(wx.VERTICAL))
        if self.visibleWidgets is None or scrollPos != self.lastScrollPos:
            self.lastScrollPos = scrollPos
            updateRect = self.GetClientRect()
            displayArrows = self.app.config.ReadBool('displayArrows')
            imageArrows = self.app.config.ReadBool('imageArrows')
            self.visibleWidgets = [widget for widget in self.widgetDict.itervalues()
                                   # It's visible if it's in the client rect, or is being moved.
                                   if (widget.dimmed
                                       or updateRect.Intersects(widget.getPixelRect())
                                       # It's also visible if an arrow FROM it intersects with the Client Rect
                                       or [w2 for w2 in widget.getConnectedWidgets(displayArrows, imageArrows)
                                           if geometry.lineRectIntersection(widget.getConnectorLine(w2,clipped=False), updateRect)])]
        return updateRect

    def resize(self, event = None):
        """
        Sets scrollbar settings based on panel size and widgets inside.
        This is designed to always give the user more room than they actually need
        to see everything already created, so that they can scroll down or over
        to add more things.
        """
        neededSize = self.toPixels(self.getSize(), scaleOnly = True)
        visibleSize = self.GetClientSize()

        maxWidth = max(neededSize[0], visibleSize[0]) + visibleSize[0]
        maxHeight = max(neededSize[1], visibleSize[1]) + visibleSize[1]

        self.SetVirtualSize((maxWidth, maxHeight))
        self.SetScrollRate(StoryPanel.SCROLL_SPEED, StoryPanel.SCROLL_SPEED)
        self.visibleWidgets = None

    def serialize(self):
        """Returns a dictionary of state suitable for pickling."""
        state = { 'scale': self.scale, 'widgets': [], 'snapping': self.snapping }

        for widget in self.widgetDict.itervalues():
            state['widgets'].append(widget.serialize())

        return state

    def serialize_noprivate(self):
        """Returns a dictionary of state suitable for pickling without passage marked with a Twine.private tag."""
        state = { 'scale': self.scale, 'widgets': [], 'snapping': self.snapping }

        for widget in self.widgetDict.itervalues():
            if not any('Twine.private' in t for t in widget.passage.tags):
                state['widgets'].append(widget.serialize())

        return state

    def handleHoverStart(self, event):
        """Turns on hover tracking when mouse enters the frame."""
        self.trackinghover = True

    def handleHoverStop(self, event):
        """Turns off hover tracking when mouse leaves the frame."""
        self.trackinghover = False

    def tooltipShow(self):
        """ Show the tooltip, showing a text sample for text passages,
        and some image size info for image passages."""
        if self.tooltipplace is not None and self.trackinghover and not self.draggingWidgets:
            m = wx.GetMousePosition()
            p = self.tooltipplace.passage
            length = len(p.text)
            if p.isImage():
                mimeType = "unknown"
                mimeTypeRE = re.search(r"data:image/([^;]*);",p.text)
                if mimeTypeRE:
                    mimeType = mimeTypeRE.group(1)
                # Including the data URI prefix in the byte count, just because.
                text = "Image type: " + mimeType + "\nSize: "+ str(len(p.text)/1024)+" KB"
            else:
                text = "Title: " + p.title + "\n" + ("Tags: " + ", ".join(p.tags) + '\n\n' if p.tags else "")
                text += p.text[:840]
                if length >= 840:
                    text += "..."
            # Don't show a tooltip for a 0-length passage
            if length > 0:
                self.tooltipobj = wx.TipWindow(self, text, min(240, max(160,length/2)), wx.Rect(m[0],m[1],1,1))

    def handleHover(self, event):
        self.updateVisableRectsAndReturnUpdateRegion()
        if self.trackinghover and not self.draggingWidgets and not self.draggingMarquee:
            position = self.toLogical(event.GetPosition())
            for widget in self.visibleWidgets:
                if widget.getLogicalRect().Contains(position):
                    if widget is not self.tooltipplace:
                        # Stop current timer
                        if self.tooltiptimer.IsRunning():
                            self.tooltiptimer.Stop()
                        self.tooltiptimer.Start(800, wx.TIMER_ONE_SHOT)
                        self.tooltipplace = widget
                        if self.tooltipobj:
                            if isinstance(self.tooltipobj, wx.TipWindow):
                                try:
                                    self.tooltipobj.Close()
                                except:
                                    pass
                            self.tooltipobj = None
                    return

        self.tooltiptimer.Stop()
        self.tooltipplace = None
        if self.tooltipobj:
            if isinstance(self.tooltipobj, wx.TipWindow):
                try:
                    self.tooltipobj.Close()
                except:
                    pass
            self.tooltipobj = None

    def getHeader(self):
        """Returns the current selected target header for this Story Panel."""
        return self.parent.getHeader()


    INSET = (10, 10)
    ARROWHEAD_THRESHOLD = 0.5   # won't be drawn below this zoom level
    FIRST_CSS = """/* Your story will use the CSS in this passage to style the page.
Give this passage more tags, and it will only affect passages with those tags.
Example selectors: */

body {
\t/* This affects the entire page */
\t
\t
}
.passage {
\t/* This only affects passages */
\t
\t
}
.passage a {
\t/* This affects passage links */
\t
\t
}
.passage a:hover {
\t/* This affects links while the cursor is over them */
\t
\t
}"""
    BACKGROUND_COLOR = '#555753'
    FLAT_BG_COLOR = '#c6c6c6'
    MARQUEE_ALPHA = 32 # out of 256
    SCROLL_SPEED = 25
    EXTRA_SPACE = 200
    GRID_SPACING = 140
    CLIPBOARD_FORMAT = 'TwinePassages'
    UNDO_LIMIT = 10

# context menu

class StoryPanelContext(wx.Menu):
    def __init__(self, parent, pos):
        wx.Menu.__init__(self)
        self.parent = parent
        self.pos = pos

        if self.parent.parent.menus.IsEnabled(wx.ID_PASTE):
            pastePassage = wx.MenuItem(self, wx.NewId(), 'Paste Passage Here')
            self.AppendItem(pastePassage)
            self.Bind(wx.EVT_MENU, lambda e: self.parent.pasteWidgets(self.getPos()), id = pastePassage.GetId())

        newPassage = wx.MenuItem(self, wx.NewId(), 'New Passage Here')
        self.AppendItem(newPassage)
        self.Bind(wx.EVT_MENU, self.newWidget, id = newPassage.GetId())

        self.AppendSeparator()

        newPassage = wx.MenuItem(self, wx.NewId(), 'New Stylesheet Here')
        self.AppendItem(newPassage)
        self.Bind(wx.EVT_MENU, lambda e: self.newWidget(e, text = StoryPanel.FIRST_CSS, tags = ['stylesheet']), id = newPassage.GetId())

        newPassage = wx.MenuItem(self, wx.NewId(), 'New Script Here')
        self.AppendItem(newPassage)
        self.Bind(wx.EVT_MENU, lambda e: self.newWidget(e, tags = ['script']), id = newPassage.GetId())

        newPassage = wx.MenuItem(self, wx.NewId(), 'New Annotation Here')
        self.AppendItem(newPassage)
        self.Bind(wx.EVT_MENU, lambda e: self.newWidget(e, tags = ['annotation']), id = newPassage.GetId())

    def getPos(self):
        pos = self.pos
        offset = self.parent.toPixels((PassageWidget.SIZE / 2, 0), scaleOnly = True)
        pos.x = pos.x - offset[0]
        pos.y = pos.y - offset[0]
        return pos

    def newWidget(self, event, text = '', tags = ()):
        self.parent.newWidget(pos = self.getPos(), text = text, tags = tags)

# drag and drop listener

class StoryPanelDropTarget(wx.PyDropTarget):
    def __init__(self, panel):
        wx.PyDropTarget.__init__(self)
        self.panel = panel
        self.data = wx.DataObjectComposite()
        self.filedrop = wx.FileDataObject()
        self.textdrop = wx.TextDataObject()
        self.data.Add(self.filedrop,False)
        self.data.Add(self.textdrop,False)
        self.SetDataObject(self.data)

    def OnData(self, x, y, d):
        if self.GetData():
            type = self.data.GetReceivedFormat().GetType()
            if type in [wx.DF_UNICODETEXT, wx.DF_TEXT]:
                # add the new widget

                # Check for invalid characters, or non-unique titles
                text = self.textdrop.GetText()
                if "|" in text:
                    return None
                else:
                    if self.panel.passageExists(text):
                        return None

                self.panel.newWidget(title = text, pos = (x, y))

                # update the source text with a link
                # this is set by PassageFrame.prepDrag()
                # (note: if text is dragged from outside Twine into it,
                # then it won't be set for the destination.)
                if self.panel.textDragSource:
                    self.panel.textDragSource.linkSelection()
                    # Cancel the deletion of the source text by returning None
                    return None

            elif type == wx.DF_FILENAME:

                imageRegex = r'\.(?:jpe?g|png|gif|webp|svg)$'
                files = self.filedrop.GetFilenames()

                # Check if dropped files contains multiple images,
                # so the correct dialogs are displayed

                imagesImported = 0
                multipleImages = len([re.search(imageRegex, file) for file in files]) > 1

                for file in files:

                    fname = file.lower()
                    # Open a file if it's .tws

                    if fname.endswith(".tws"):
                        self.panel.app.open(file)

                    # Import a file if it's HTML, .tw or .twee

                    elif fname.endswith(".twee") or fname.endswith(".tw"):
                        self.panel.parent.importSource(file)
                    elif fname.endswith(".html") or fname.endswith(".htm"):
                        self.panel.parent.importHtml(file)
                    elif re.search(imageRegex, fname):
                        text, title = self.panel.parent.openFileAsBase64(fname)
                        imagesImported += 1 if self.panel.parent.finishImportImage(text, title, showdialog = not multipleImages) else 0

                if imagesImported > 1:
                    dialog = wx.MessageDialog(self.panel.parent, 'Multiple image files imported successfully.', 'Images added', \
                          wx.ICON_INFORMATION | wx.OK)
                    dialog.ShowModal()

        return d
