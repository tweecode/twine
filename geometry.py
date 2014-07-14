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

    lengthRatio = distance / length

    x = line[1][0] - ((line[1][0] - line[0][0]) * math.cos(angle) - \
                      (line[1][1] - line[0][1]) * math.sin(angle)) * lengthRatio
    y = line[1][1] - ((line[1][1] - line[0][1]) * math.cos(angle) + \
                      (line[1][0] - line[0][0]) * math.sin(angle)) * lengthRatio

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
    return math.sqrt((line[1][0] - line[0][0]) ** 2 + (line[1][1] - line[0][1]) ** 2)

def lineRectIntersection(line, rect, excludeTrivial = False):
    """
    Returns a x,y pair corresponding to where a line and a
    wx.Rect intersect. If they do not intersect, then None
    is returned. This returns the first intersection it happens
    to find, not all of them.

    By default, it will immediately return an endpoint if one of
    them is inside the rectangle. The excludeTrivial prevents
    this behavior.
    """
    if not excludeTrivial:
        for i in range(2):
            if rect.Contains(line[i]):
                return line[i]

    # See Cohen-Sutherland Line-Clipping Algorithm

    # pylint: disable=invalid-name
    LEFT   = 0b0001
    RIGHT  = 0b0010
    BOTTOM = 0b0100
    TOP    = 0b1000

    xmin, ymin = rect.GetTopLeft()
    xmax, ymax = rect.GetBottomRight()

    def computeCode(x, y):
        code = 0

        if x < xmin:
            code |= LEFT
        elif x > xmax:
            code |= RIGHT

        if y < ymin:
            code |= BOTTOM
        elif y > ymax:
            code |= TOP

        return code


    x0, y0 = line[0]
    x1, y1 = line[1]

    codeStart = computeCode(x0, y0)
    codeEnd = computeCode(x1, y1)

    if (codeStart & codeEnd) != 0:
        return None

    x, y = 0, 0
    while True:
        if (codeStart | codeEnd) == 0:
            return x, y
        elif not (codeStart & codeEnd) == 0:
            return None
        else:
            outsideCode = max(codeStart, codeEnd)

            # Checks for trivial cases with horizontal and vertical lines.
            if x1 == x0:
                if outsideCode & TOP != 0:
                    return x1, ymax
                else:
                    return x1, ymin
            if y1 == y0:
                if outsideCode & LEFT != 0:
                    return xmin, y1
                else:
                    return xmax, y1

            if outsideCode & TOP != 0:
                x, y = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0), ymax
            elif outsideCode & BOTTOM != 0:
                x, y = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0), ymin
            elif outsideCode & LEFT != 0:
                x, y = xmin, y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
            elif outsideCode & RIGHT != 0:
                x, y = xmax, y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)

            if outsideCode == codeStart:
                x0, y0 = x, y
                codeStart = computeCode(x0, y0)
            else:
                x1, y1 = x, y
                codeEnd = computeCode(x1, y1)

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
