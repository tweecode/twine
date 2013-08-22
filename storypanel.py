#!/usr/bin/env python

#
# StoryPanel
# A StoryPanel is a container for PassageWidgets. It translates
# between logical coordinates and pixel coordinates as the user
# zooms in and out, and communicates those changes to its widgets.
#
# A discussion on coordinate systems: logical coordinates are notional,
# and do not change as the user zooms in and out. Pixel coordinates
# are extremely literal: (0, 0) is the top-left corner visible to the
# user, no matter where the scrollbar position is.
#
# This class (and PassageWidget) deal strictly in logical coordinates, but
# incoming events are in pixel coordinates. We convert these to logical
# coordinates as soon as possible.
#

import sys, math, wx, re, pickle
import geometry, time
from passagewidget import PassageWidget

class StoryPanel (wx.ScrolledWindow):

    def __init__ (self, parent, app, id = wx.ID_ANY, state = None):
        wx.ScrolledWindow.__init__(self, parent, id)
        self.app = app
        self.parent = parent
        
        # inner state
        
        self.snapping = self.app.config.ReadBool('storyPanelSnap')
        self.widgets = []
        self.draggingMarquee = False
        self.draggingWidgets = False
        self.scrolling = False
        self.undoStack = []
        self.undoPointer = -1
        self.lastSearchRegexp = None
        self.lastSearchFlags = None
        self.trackinghover = None
        self.tooltipcounter = 0
        self.tooltipplace = ''
        self.tooltipobj = None
       
        if (state):
            self.scale = state['scale']
            for widget in state['widgets']:
                self.widgets.append(PassageWidget(self, self.app, state = widget))
            if (hasattr(state, 'snapping')) and state['snapping']: self.snapping = True
        else:
            self.scale = 1
            self.newWidget(title = StoryPanel.FIRST_TITLE, text = StoryPanel.FIRST_TEXT, quietly = True)
            
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
        
    def newWidget (self, title = None, text = '', pos = None, quietly = False):
        """Adds a new widget to the container."""
                
        # defaults
        
        if not title: title = self.untitledName()
        if not pos: pos = StoryPanel.INSET
        
        pos = self.toLogical(pos)
        new = PassageWidget(self, self.app, title = title, text = text, pos = pos)
        self.widgets.append(new)
        self.snapWidget(new)
        self.Refresh()
        self.resize()
        if not quietly: self.parent.setDirty(True, action = 'New Passage')
        return new
        
    def snapWidget (self, widget):
        """Snaps a widget to our grid if self.snapping is set."""
        if self.snapping:
            pos = list(widget.pos)
            
            for coord in range(2):
                distance = pos[coord] % StoryPanel.GRID_SPACING
                if (distance > StoryPanel.GRID_SPACING / 2):
                    pos[coord] += StoryPanel.GRID_SPACING - distance
                else:
                    pos[coord] -= distance
                pos[coord] += StoryPanel.INSET[coord]
                
            widget.pos = pos
            self.Refresh()
            
    def cleanup (self):
        """Snaps all widgets to the grid."""
        oldSnapping = self.snapping
        self.snapping = True
        self.eachWidget(self.snapWidget)
        self.snapping = oldSnapping
        self.parent.setDirty(True, action = 'Clean Up')
        self.Refresh()

    def toggleSnapping (self):
        """Toggles whether snapping is on."""
        self.snapping = self.snapping is not True
        self.app.config.WriteBool('storyPanelSnap', self.snapping)
        
    def copyWidgets (self):
        """Copies selected widgets into the clipboard."""
        data = []
        for widget in self.widgets:
            if widget.selected: data.append(widget.serialize())
        
        clipData = wx.CustomDataObject(wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT))
        clipData.SetData(pickle.dumps(data, 1))
        
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(clipData)
            wx.TheClipboard.Close()
            
    def cutWidgets (self):
        """Cuts selected widgets into the clipboard."""
        self.copyWidgets()
        self.removeWidgets()
        self.Refresh()
        
    def pasteWidgets (self):
        """Pastes widgets into the clipboard."""
        format = wx.CustomDataFormat(StoryPanel.CLIPBOARD_FORMAT)
        
        if wx.TheClipboard.Open() and wx.TheClipboard.IsSupported(format):
            clipData = wx.CustomDataObject(format)
            wx.TheClipboard.GetData(clipData)
            wx.TheClipboard.Close()
            data = pickle.loads(clipData.GetData())
                        
            self.eachWidget(lambda w: w.setSelected(False, False))
            
            for widget in data:
                newPassage = PassageWidget(self, self.app, state = widget)
                newPassage.findSpace()
                newPassage.setSelected(True, False)
                self.widgets.append(newPassage)
                
            self.parent.setDirty(True, action = 'Paste')
            self.Refresh()
            
    def removeWidget (self, widget, saveUndo = False):
        """
        Deletes a passed widget. You can ask this to save an undo state manually, 
        but by default, it doesn't.
        """
        self.widgets.remove(widget)
        if saveUndo: self.parent.setDirty(True, action = 'Delete')
        self.Refresh()
            
    def removeWidgets (self, event = None, saveUndo = False):
        """
        Deletes all selected widgets. You can ask this to save an undo state manually,
        but by default, it doesn't.
        """
        toDelete = []
        
        for widget in self.widgets:
            if widget.selected and widget.checkDelete(): toDelete.append(widget)
        
        for widget in toDelete: self.widgets.remove(widget)
        
        if len(toDelete):
            self.Refresh()
            if saveUndo: self.parent.setDirty(True, action = 'Delete')
        
    def findWidgetRegexp (self, regexp = None, flags = None):
        """
        Finds the next PassageWidget that matches the regexp passed.
        You may leave off the regexp, in which case it uses the last
        search performed. This begins its search from the current selection.
        If nothing is found, then an error alert is shown.
        """
        
        if regexp == None:
            regexp = self.lastSearchRegexp
            flags = self.lastSearchFlags
            
        self.lastSearchRegexp = regexp
        self.lastSearchFlags = flags
        
        # find the current selection
        # if there are multiple selections, we just use the first
        
        i = -1
        
        # look for selected PassageWidgets
        for num, widget in enumerate(self.widgets):
            if widget.selected: 
                i = num
                break

        # if no widget is selected, start at first widget
        if i==len(self.widgets)-1:
            i=-1
        
        for widget in self.widgets[i+1:]:
            if widget.containsRegexp(regexp, flags):
                widget.setSelected(True)
                self.scrollToWidget(widget)
                return
            i += 1
            
        # fallthrough: text not found
        
        dialog = wx.MessageDialog(self, 'The text you entered was not found in your story.', \
                                  'Not Found', wx.ICON_INFORMATION | wx.OK)
        dialog.ShowModal()

    def replaceRegexpInSelectedWidget (self, findRegexp, replacementRegexp, flags):
        for widget in self.widgets:                                            
            if widget.selected:
                widget.replaceRegexp(findRegexp, replacementRegexp, flags)         
                widget.clearPaintCache()
                self.Refresh()
                self.parent.setDirty(True, action = 'Replace in Currently Selected Widget')

    def replaceRegexpInWidgets (self, findRegexp, replacementRegexp, flags):
        """
        Performs a string replace on all widgets in this StoryPanel.
        It shows an alert once done to tell the user how many replacements were
        made.
        """
        replacements = 0
        
        for widget in self.widgets:
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

    def scrollToWidget (self, widget):
        """
        Scrolls so that the widget passed is visible.
        """
        widgetRect = widget.getPixelRect()
        xUnit,yUnit = self.GetScrollPixelsPerUnit()
        sx = (widgetRect.x-20) / float(xUnit)
        sy = (widgetRect.y-20) / float(yUnit)
        self.Scroll(max(sx, 0), max(sy - 20, 0))

    def pushUndo (self, action):
        """
        Pushes the current state onto the undo stack. The name parameter describes
        the action that triggered this call, and is displayed in the Undo menu.
        """
        
        # delete anything above the undoPointer
        
        while self.undoPointer < len(self.undoStack) - 2: self.undoStack.pop()
        
        # add a new state onto the stack
        
        state = { 'action': action, 'widgets': [] }
        for widget in self.widgets: state['widgets'].append(widget.serialize())
        self.undoStack.append(state)
        self.undoPointer += 1
        
    def undo (self):
        """
        Restores the undo state at self.undoPointer to the current view, then
        decreases self.undoPointer by 1.
        """
        self.widgets = []
        state = self.undoStack[self.undoPointer]
        for widget in state['widgets']:
            self.widgets.append(PassageWidget(self, self.app, state = widget))
        self.undoPointer -= 1
        self.Refresh()

    def redo (self):
        """
        Moves the undo pointer up 2, then calls undo() to restore state.
        """
        self.undoPointer += 2
        self.undo()
        
    def canUndo (self):
        """Returns whether an undo is available to the user."""
        return self.undoPointer > -1

    def undoAction (self):
        """Returns the name of the action that the user will be undoing."""
        return self.undoStack[self.undoPointer + 1]['action']
    
    def canRedo (self):
        """Returns whether a redo is available to the user."""
        return self.undoPointer < len(self.undoStack) - 2

    def redoAction (self):
        """Returns the name of the action that the user will be redoing."""
        return self.undoStack[self.undoPointer + 2]['action']
    
    def handleClick (self, event):
        """
        Passes off execution to either startMarquee or startDrag,
        depending on whether the user clicked a widget.
        """
        # start a drag if the user clicked a widget
        # or a marquee if they didn't
                
        for widget in self.widgets:
            if widget.getPixelRect().Contains(event.GetPosition()):
                if not widget.selected: widget.setSelected(True, not event.ShiftDown())
                self.startDrag(event, widget)
                return
        self.startMarquee(event)
        
    def handleDoubleClick (self, event):
        """Dispatches an openEditor() call to a widget the user clicked."""
        for widget in self.widgets:
            if widget.getPixelRect().Contains(event.GetPosition()): widget.openEditor()
            
    def handleRightClick (self, event):
        """Either opens our own contextual menu, or passes it off to a widget."""
        for widget in self.widgets:
            if widget.getPixelRect().Contains(event.GetPosition()):
                widget.openContextMenu(event)
                return
        self.PopupMenu(StoryPanelContext(self, event.GetPosition()), event.GetPosition())
        
    def handleMiddleClick (self, event):
        """Creates a new widget centered at the mouse position."""
        pos = event.GetPosition()
        offset = self.toPixels((PassageWidget.SIZE / 2, 0), scaleOnly = True)
        pos.x = pos.x - offset[0]
        pos.y = pos.y - offset[0]
        self.newWidget(pos = pos)
        
    def startMarquee (self, event):
        """Starts a marquee selection."""
        if not self.draggingMarquee:
            self.draggingMarquee = True
            self.dragOrigin = event.GetPosition()
            self.dragCurrent = event.GetPosition()
            self.dragRect = geometry.pointsToRect(self.dragOrigin, self.dragOrigin)
            
            # deselect everything
            
            map(lambda w: w.setSelected(False, False), self.widgets)
            
            # grab mouse focus
            
            self.Bind(wx.EVT_MOUSE_EVENTS, self.followMarquee)
            self.CaptureMouse()
            self.Refresh()

    def followMarquee (self, event):
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
            
            for widget in self.widgets:
                widget.setSelected(widget.intersects(logicalRect), False)
            
            self.Refresh(True, self.oldDirtyRect.Union(self.dragRect))
        else:
            self.draggingMarquee = False
                        
            # clear event handlers
            
            self.Bind(wx.EVT_MOUSE_EVENTS, None)
            self.ReleaseMouse()            
            self.Refresh()
            
    def startDrag (self, event, clickedWidget):
        """
        Starts a widget drag. The initial event is caught by PassageWidget, but
        it passes control to us so that we can move all selected widgets at once.
        """
        if not self.draggingWidgets:
            self.draggingWidgets = True
            self.clickedWidget = clickedWidget
            self.actuallyDragged = False
            self.dragCurrent = event.GetPosition()
            self.oldDirtyRect = clickedWidget.getPixelRect()
                        
            # have selected widgets remember their original position
            # in case they need to snap back to it after a bad drag
            
            for widget in self.widgets:
                if widget.selected:
                    widget.predragPos = widget.pos
            
            # grab mouse focus
            
            self.Bind(wx.EVT_MOUSE_EVENTS, self.followDrag)
            self.CaptureMouse()
        
    def followDrag (self, event):
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
            
            self.eachSelectedWidget(lambda p: p.offset(deltaX, deltaY))
            self.dragCurrent = pos
                        
            # if there any overlaps, then warn the user with a bad drag cursor
            
            goodDrag = True
            
            # TODO: optimize this loop
            
            for widget in self.widgets:
                if widget.selected and widget.intersectsAny():
                    goodDrag = False
                    break

            # in fast drawing, we dim passages
            # to indicate no connectors should be drawn for them
            # while dragging is occurring
            #
            # in slow drawing, we dim passages
            # to indicate you're not allowed to drag there
            
            if self.app.config.ReadBool('fastStoryPanel'):
                self.eachSelectedWidget(lambda w: w.setDimmed(True))
            else:
                self.eachSelectedWidget(lambda w: w.setDimmed(not goodDrag))
                
            if goodDrag: self.SetCursor(self.dragCursor)
            else: self.SetCursor(self.badDragCursor)
            
            # scroll in response to the mouse,
            # and shift passages accordingly
            
            widgetScroll = self.toLogical(self.scrollWithMouse(event), scaleOnly = True)
            self.eachSelectedWidget(lambda w: w.offset(widgetScroll[0], widgetScroll[1]))
                
            # figure out our dirty rect
            
            dirtyRect = self.oldDirtyRect
            
            for widget in self.widgets:
                if widget.selected:
                    dirtyRect = dirtyRect.Union(widget.getDirtyPixelRect())
            
            self.oldDirtyRect = dirtyRect
            self.Refresh(True, dirtyRect)
        else:
            self.draggingWidgets = False

            if self.actuallyDragged:
                # is this a bad drag?
    
                goodDrag = True
                
                for widget in self.widgets:
                    if widget.selected and widget.intersectsAny():
                        goodDrag = False
                        break
                    
                if goodDrag:
                    self.eachSelectedWidget(lambda w: self.snapWidget(w))
                    self.eachSelectedWidget(lambda w: w.setDimmed(False))
                    self.parent.setDirty(True, action = 'Move')
                    self.resize()
                else:
                    for widget in self.widgets:
                        if widget.selected:
                            widget.pos = widget.predragPos
                            widget.setDimmed(False)
                    self.Refresh()
            else:
                # change the selection
                self.clickedWidget.setSelected(True, not event.ShiftDown())
        
            # general cleanup
            
            self.Bind(wx.EVT_MOUSE_EVENTS, None)
            self.ReleaseMouse()        
            self.SetCursor(self.defaultCursor)
    
    def scrollWithMouse (self, event):
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
        
    def untitledName (self):
        """Returns a string for an untitled PassageWidget."""
        number = 1
        
        for widget in self.widgets:
            match = re.match(r'Untitled Passage (\d+)', widget.passage.title)
            if match: number = int(match.group(1)) + 1
                
        return 'Untitled Passage ' + str(number)
    
    def eachWidget (self, function):
        """Runs a function on every passage in the panel."""
        for widget in self.widgets:
            function(widget)

    def sortedWidgets (self):
        """Returns a sorted list of widgets, left to right, top to bottom."""
        return sorted(self.widgets, PassageWidget.sort)

    def eachSelectedWidget (self, function):
        """Runs a function on every selected passage in the panel."""
        for widget in self.widgets:
            if widget.selected: function(widget)
            
    def hasSelection (self):
        """Returns whether any passages are selected."""
        for widget in self.widgets:
            if widget.selected: return True
        return False
    
    def hasMultipleSelection (self):
        """Returns whether multiple passages are selected."""
        selected = 0
        for widget in self.widgets:
            if widget.selected:
                selected += 1
                if selected > 1: return True
        return False
            
    def findWidget (self, title):
        """Returns a PassageWidget with the title passed. If none exists, it returns None."""
        for widget in self.widgets:
            if widget.passage.title == title: return widget
        return None

    def toPixels (self, logicals, scaleOnly = False):
        """
        Converts a tuple of logical coordinates to pixel coordinates. If you need to do just
        a straight conversion from logicals to pixels without worrying about where the scrollbar
        is, then call with scaleOnly set to True.
        """
        converted = (logicals[0] * self.scale, logicals[1] * self.scale)
        if not scaleOnly: converted = self.CalcScrolledPosition(converted)
        return converted

    def toLogical (self, pixels, scaleOnly = False):
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

    def getSize (self):
        """
        Returns a tuple (width, height) of the smallest rect needed to
        contain all children widgets.
        """
        width, height = 0, 0
        
        for i in self.widgets:
            rightSide = i.pos[0] + i.getSize()[0]
            bottomSide = i.pos[1] + i.getSize()[1]
            width = max(width, rightSide)
            height = max(height, bottomSide)
        return (width, height)
    
    def zoom (self, scale):
        """
        Sets zoom to a certain level. Pass a number to set the zoom
        exactly, pass 'in' or 'out' to zoom relatively, and 'fit'
        to set the zoom so that all children are visible.
        """
        oldScale = self.scale
        
        if (isinstance(scale, float)):
            self.scale = scale
        else:
            if (scale == 'in'):
                self.scale += 0.2
            if (scale == 'out'):
                self.scale -= 0.2
            if (scale == 'fit'):
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

    def paint (self, event):
        """Paints marquee selection, widget connectors, and widgets onscreen."""
        # do NOT call self.DoPrepareDC() no matter what the docs may say
        # we already take into account our scroll origin in our
        # toPixels() method
        
        # in fast drawing, we ask for a standard paint context
        # in slow drawing, we ask for a anti-aliased one
        #
        # OS X already double buffers drawing for us; if we try to do it
        # ourselves, performance is horrendous

        if (sys.platform == 'darwin'):
            gc = wx.PaintDC(self)
        else:
            gc = wx.BufferedPaintDC(self)
           
        # background
        
        updateRegion = self.GetUpdateRegion()
        updateRect = updateRegion.GetBox()
        gc.SetBrush(wx.Brush(StoryPanel.BACKGROUND_COLOR))      
        gc.DrawRectangle(updateRect.x - 1, updateRect.y - 1, updateRect.width + 2, updateRect.height + 2)
                
        # connectors
        
        badLinks = []
        arrowheads = (self.scale > StoryPanel.ARROWHEAD_THRESHOLD)

        for widget in self.widgets:
            if widget.dimmed: continue
            badLinks = widget.paintConnectors(gc, arrowheads, badLinks, updateRect)
            
        # widgets
        
        for widget in self.widgets:
            if updateRegion.IntersectRect(widget.getPixelRect()): widget.paint(gc)
        
        # marquee selection
        # with slow drawing, use alpha blending for interior
        
        if self.draggingMarquee:
            if self.app.config.ReadBool('fastStoryPanel'):
                gc.SetPen(wx.Pen('#ffffff', 1, wx.DOT))
            else:
                gc = wx.GraphicsContext.Create(gc)
                marqueeColor = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
                gc.SetPen(wx.Pen(marqueeColor))
                r, g, b = marqueeColor.Get()
                marqueeColor = wx.Color(r, g, b, StoryPanel.MARQUEE_ALPHA)            
                gc.SetBrush(wx.Brush(marqueeColor))
                
            gc.DrawRectangle(self.dragRect.x, self.dragRect.y, self.dragRect.width, self.dragRect.height)
            
    def resize (self, event = None):
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
    
    def serialize (self):
        """Returns a dictionary of state suitable for pickling."""
        state = { 'scale': self.scale, 'widgets': [] }
                
        for widget in self.widgets:
            state['widgets'].append(widget.serialize())
            
        return state
    
    def serialize_noprivate (self):
        """Returns a dictionary of state suitable for pickling without passage marked with a Twine.private tag."""
        state = { 'scale': self.scale, 'widgets': [] }
                
        for widget in self.widgets:
            if not any('Twine.private' in t for t in widget.passage.tags):
                state['widgets'].append(widget.serialize())
            
        return state   

    def handleHoverStart(self, event):
        """Turns on hover tracking when mouse enters the frame."""
        self.trackinghover = True

    def handleHoverStop(self, event):
        """Turns off hover tracking when mouse leaves the frame."""
        self.trackinghover = False
        
    def handleHover(self, event):
        if self.trackinghover and not self.draggingWidgets and not self.draggingMarquee:
            for widget in self.widgets:
                if widget.getPixelRect().Contains(event.GetPosition()):
                    if self.tooltipcounter == 0 or widget.passage.title != self.tooltipplace:
                        self.tooltipcounter = time.time() + 0.500
                        self.tooltipplace = widget.passage.title
                        if self.tooltipobj != None:
                            if isinstance(self.tooltipobj, wx.TipWindow): 
                                self.tooltipobj.Close()
                            self.tooltipobj = None
                    elif time.time() >= self.tooltipcounter and self.tooltipobj == None:
                        self.tooltipobj = wx.TipWindow(self, self.tooltipplace, 80, wx.Rect(0,0,300,200))
                    return
        
        self.tooltipcounter = 0
        self.tooltipplace = None
        if self.tooltipobj != None:
            if isinstance(self.tooltipobj, wx.TipWindow): 
                self.tooltipobj.Close()
            self.tooltipobj = None

    INSET = (10, 10)
    ARROWHEAD_THRESHOLD = 0.5   # won't be drawn below this zoom level
    FIRST_TITLE = 'Start'
    FIRST_TEXT = 'Your story will display this passage first. Edit it by double clicking it.'   
    BACKGROUND_COLOR = '#555753'
    MARQUEE_ALPHA = 32 # out of 256
    SCROLL_SPEED = 25
    EXTRA_SPACE = 200
    GRID_SPACING = 140
    CLIPBOARD_FORMAT = 'TwinePassages'
    UNDO_LIMIT = 10
    
# context menu

class StoryPanelContext (wx.Menu):
    def __init__ (self, parent, pos):
        wx.Menu.__init__(self)
        self.parent = parent
        self.pos = pos
        
        newPassage = wx.MenuItem(self, wx.NewId(), 'New Passage Here')
        self.AppendItem(newPassage)
        self.Bind(wx.EVT_MENU, self.newWidget, id = newPassage.GetId())

    def newWidget (self, event):
        pos = self.pos
        offset = self.parent.toPixels((PassageWidget.SIZE / 2, 0), scaleOnly = True)
        pos.x = pos.x - offset[0]
        pos.y = pos.y - offset[0]
        self.parent.newWidget(pos = pos)
        
# drag and drop listener

class StoryPanelDropTarget (wx.TextDropTarget):
    def __init__ (self, panel):
        wx.TextDropTarget.__init__(self)
        self.panel = panel
        
    def OnDropText (self, x, y, data):
        # add the new widget
        
        self.panel.newWidget(title = data, pos = (x, y))
        
        # update the source text with a link
        # this is set by PassageFrame.prepDrag()
        
        self.panel.textDragSource.linkSelection()
