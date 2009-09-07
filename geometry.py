#!/usr/bin/env python

#
# This module has basic utilities for working with wx.Rects
# and Lines (which are tuples of wx.Points).
#

import math, wx

def clipLineByRects (line, *rects):
    """
    Clips a line (e.g. an array of wx.Points) so it does
    not overlap any of the rects passed. The line must be
    the first parameter, but you may pass any number of rects.
    """
    result = line
    
    # this is not as awful as it looks,
    # "for rectLine in rectLines" does it 4 times max
    # so we're actually O(n)
        
    for rect in rects:
        rectLines = None
        for i in range(2):
            if rect.Inside(result[i]):
                if not rectLines: rectLines = rectToLines(rect)
                for rectLine in rectLines:
                    intersection = lineIntersection(result, rectLine)
                    if intersection:
                        result[i] = intersection
                        break
    return result

def endPointProjectedFrom(line, angle, distance):
    """
    Projects an endpoint from the second wx.Point of a line at
    a given angle and distance. The angle should be given in radians.
    """
    
    # taken from http://mathforum.org/library/drmath/view/54146.html
    
    lengthRatio = distance / lineLength(line)
    
    x = line[1].x - ((line[1].x - line[0].x) * math.cos(angle) - \
                     (line[1].y - line[0].y) * math.sin(angle)) * lengthRatio
    y = line[1].y - ((line[1].y - line[0].y) * math.cos(angle) + \
                     (line[1].x - line[0].x) * math.sin(angle)) * lengthRatio

    return wx.Point(x, y)

def pointsToRect (p1, p2):
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

def rectToLines (rect):
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

def lineLength (line):
    """
    Returns the length of a line.
    """
    return math.sqrt((line[1].x - line[0].x) ** 2 + (line[1].y - line[0].y) ** 2)

def lineIntersection (line1, line2):
    """
    Returns a wx.Point corresponding to where two line
    segments intersect. If they do not intersect, then None
    is returned.
    """
    
    # this is translated from
    # http://workshop.evolutionzone.com/2007/09/10/code-2d-line-intersection/
    
    # distances of the two lines
    
    distX1 = line1[1].x - line1[0].x
    distX2 = line2[1].x - line2[0].x
    distY1 = line1[1].y - line1[0].y
    distY2 = line2[1].y - line2[0].y
    distX3 = line1[0].x - line2[0].x
    distY3 = line1[0].y - line2[0].y
    
    # length of the lines
    
    line1Length = math.sqrt(distX1 ** 2 + distY1 ** 2)
    line2Length = math.sqrt(distX2 ** 2 + distY2 ** 2)
    
    if line1Length == 0 or line2Length == 0: return None
        
    # angle between lines
    
    dotProduct = distX1 * distX2 + distY1 * distY2
    angle = dotProduct / (line1Length * line2Length)
    
    # check to see if lines are parallel
    
    if abs(angle) == 1:
        return None
    
    # find the intersection point
    # we cast the divisor as a float
    # to force uA and uB to be floats too
    
    divisor = float(distY2 * distX1 - distX2 * distY1)
    uA = (distX2 * distY3 - distY2 * distX3) / divisor
    uB = (distX1 * distY3 - distY1 * distX3) / divisor
    intersection = wx.Point(line1[0].x + uA * distX1, \
                            line1[0].y + uA * distY1)
        
    # find the combined length of the two segments
    # between intersection and line1's endpoints
    
    distX1 = intersection.x - line1[0].x
    distX2 = intersection.x - line1[1].x
    distY1 = intersection.y - line1[0].y
    distY2 = intersection.y - line1[1].y
    distLine1 = math.sqrt(distX1 ** 2 + distY1 ** 2) + \
                    math.sqrt(distX2 ** 2 + distY2 ** 2)
    
    # ... and then for line2
    
    distX1 = intersection.x - line2[0].x
    distX2 = intersection.x - line2[1].x
    distY1 = intersection.y - line2[0].y
    distY2 = intersection.y - line2[1].y
    distLine2 = math.sqrt(distX1 ** 2 + distY1 ** 2) + \
                    math.sqrt(distX2 ** 2 + distY2 ** 2)
    
    # if these two are the same, then we know
    # the intersection is actually on the line segments, and not in space
    #
    # I had to goose the accuracy down a lot :(
    
    if (abs(distLine1 - line1Length) < 0.2) and \
       (abs(distLine2 - line2Length) < 0.2):
        return intersection
    else:
        return None