#!/usr/bin/env python

#
# This module has basic utilities for working with wx.Rects.
#

import wx

def pointsToRect (p1, p2):
    """
    Returns a Rect defined by two points.
    """
    left = min(p1[0], p2[0])
    right = max(p1[0], p2[0])
    top = min(p1[1], p2[1])
    bottom = max(p1[1], p2[1])
    
    rect = wx.Rect(0, 0, 0, 0)
    rect.SetTopLeft((left, top))
    rect.SetBottomRight((right, bottom))
    
    return rect