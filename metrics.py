#!/usr/bin/env python

#
# Metrics
# This module offers advice on how to size the UI appropriately
# for the OS we're running on.
#

import sys
    
def size (type):
    """
    Returns the number of pixels to use for a certain context.
    Recognized keywords:
    
    windowBorder - around the edges of a window
    controlSpace - between controls
    fontMin - smallest font size to ever use
    fontMax - largest font size to use, as a recommendation
    """
    if type == 'windowBorder':
        if sys.platform == 'win32': return 11
        if sys.platform == 'darwin': return 16
        return 13
    
    if type == 'controlSpace':
        if sys.platform == 'win32': return 7
        if sys.platform == 'darwin': return 12
        return 9
        
    if type == 'fontMin':
        if sys.platform == 'win32': return 9
        if sys.platform == 'darwin': return 10
        
    if type == 'fontMax':
        return 24