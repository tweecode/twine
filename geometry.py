"""
This module has basic utilities for working with wx.Rects
and Lines (which are tuples of wx.Points).
"""

import math, wx

def clipLineByRects(line, *rects):
    """
    Clips a line (e.g. an array of wx.Points) so it does
    not overlap any of the rects passed. The line must be
    the first parameter, but you may pass any number of rects.
    """
    result = line

    for rect in rects:
        rectLines = None
        for i in range(2):
            if rect.Contains(result[i]):
                intersection = lineRectIntersection(result, rect, excludeTrivial = True)
                if intersection:
                    result[i] = intersection
                    break
    return result

def endPointProjectedFrom(line, angle, distance):
    """
    Projects an endpoint from the second wx.Point of a line at
    a given angle and distance. The angle should be given in radians.
    """
    length = lineLength(line)
    if length == 0: return line[1]

    # taken from http://mathforum.org/library/drmath/view/54146.html

    lengthRatio = distance / lineLength(line)

    x = line[1].x - ((line[1].x - line[0].x) * math.cos(angle) - \
                     (line[1].y - line[0].y) * math.sin(angle)) * lengthRatio
    y = line[1].y - ((line[1].y - line[0].y) * math.cos(angle) + \
                     (line[1].x - line[0].x) * math.sin(angle)) * lengthRatio

    return wx.Point(x, y)

def pointsToRect(p1, p2):
    """
    Returns the smallest wx.Rect that encloses two points.
    """
    left = min(p1[0], p2[0])
    right = max(p1[0], p2[0])
    top = min(p1[1], p2[1])
    bottom = max(p1[1], p2[1])

    rect = wx.Rect(0, 0, 0, 0)
    rect.SetTopLeft((left, top))
    rect.SetBottomRight((right, bottom))

    return rect

def rectToLines(rect):
    """
    Converts a wx.Rect into an array of lines
    (e.g. tuples of wx.Points)
    """
    topLeft = rect.GetTopLeft()
    topRight = rect.GetTopRight()
    bottomLeft = rect.GetBottomLeft()
    bottomRight = rect.GetBottomRight()
    return (topLeft, topRight), (topLeft, bottomLeft), (topRight, bottomRight), \
           (bottomLeft, bottomRight)

def lineLength(line):
    """
    Returns the length of a line.
    """
    return math.sqrt((line[1].x - line[0].x) ** 2 + (line[1].y - line[0].y) ** 2)

def lineRectIntersection(line, rect, excludeTrivial = False):
    """
    Returns a wx.Point corresponding to where a line and a
    wx.Rect intersect. If they do not intersect, then None
    is returned. This returns the first intersection it happens
    to find, not all of them.

    By default, it will immediately return an endpoint if one of
    them is inside the rectangle. The excludeTrivial prevents
    this behavior.
    """

    # check for trivial case, where one point is inside the rect

    if not excludeTrivial:
        for i in range(2):
            if rect.Contains(line[i]): return line[i]

    # check for intersection with borders

    rectLines = rectToLines(rect)
    for rectLine in rectLines:
        intersection = lineIntersection(line, rectLine)
        if intersection: return intersection
    return None

def lineIntersection(line1, line2):
    """
    Returns a wx.Point corresponding to where two line
    segments intersect. If they do not intersect, or they are parallel, then None
    is returned.
    """
    ax1,ay1,ax2,ay2 = line1[0][0],line1[0][1],line1[1][0],line1[1][1]
    bx1,by1,bx2,by2 = line2[0][0],line2[0][1],line2[1][0],line2[1][1]
    s1x = ax2-ax1
    s1y = ay2-ay1
    s2x = bx2-bx1
    s2y = by2-by1
    denominator = float(-s2x * s1y + s1x * s2y)
    if denominator == 0:
        #Collinear or Parallel returns none as in original
        return None

    s = (-s1y * (ax1 - bx1) + s1x * (ay1 - by1))
    if not 0 <= s <= denominator: return None
    t = ( s2x * (ay1 - by1) - s2y * (ax1 - bx1))
    if not 0 <= t <= denominator: return None
    t /= denominator
    ix = ax1 + (t * s1x)
    iy = ay1 + (t * s1y)
    return wx.Point(ix, iy)