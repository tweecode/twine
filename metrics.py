"""
This module offers advice on how to size the UI appropriately
for the OS we're running on.
"""

import sys

def size(type):
    """
    Returns the number of pixels to use for a certain context.
    Recognized keywords:

    windowBorder - around the edges of a window
    buttonSpace - between buttons
    relatedControls - between related controls
    unrelatedControls - between unrelated controls
    focusRing - space to leave to allow for focus rings
    fontMin - smallest font size to ever use
    fontMax - largest font size to use, as a recommendation
    widgetTitle - starting font size for widget titles, as a recommendation
    editorBody - starting font size for body editor, as a recommendation
    fsEditorBody - starting font size for fullscreen editor, as a recommendation
    storySettingsWidth - starting width of StorySettings editor
    storySettingsHeight - starting height of StorySettings editor
    """
    if type == 'windowBorder':
        if sys.platform == 'win32': return 11
        if sys.platform == 'darwin': return 16
        return 13

    if type == 'relatedControls':
        if sys.platform == 'win32': return 7
        if sys.platform == 'darwin': return 6
        return 9

    if type == 'unrelatedControls':
        if sys.platform == 'win32': return 11
        if sys.platform == 'darwin': return 12
        return 9

    if type == 'buttonSpace':
        if sys.platform == 'win32': return 7
        if sys.platform == 'darwin': return 12
        return 9

    if type == 'focusRing':
        return 3

    if type == 'fontMin':
        if sys.platform == 'win32': return 8
        if sys.platform == 'darwin': return 11

    if type == 'fontMax':
        return 24

    if type == 'widgetTitle':
        if sys.platform == 'win32': return 9
        if sys.platform == 'darwin': return 13
        return 11

    if type == 'editorBody':
        if sys.platform == 'win32': return 11
        if sys.platform == 'darwin': return 13
        return 11

    if type == 'fsEditorBody':
        if sys.platform == 'win32': return 16
        if sys.platform == 'darwin': return 20
        return 11

    if type == 'storySettingsWidth':
        if sys.platform == 'darwin': return 550
        return 450

    if type == 'storySettingsHeight':
        if sys.platform == 'darwin': return 650
        return 550

def face(type):
    """
    Returns a font face name.
    Recognized keywords:

    sans - sans-serif
    mono - monospaced
    """
    if type == 'sans':
        if sys.platform == 'win32': return 'Arial'
        if sys.platform == 'darwin': return 'Helvetica'
        return 'Sans'

    if type == 'mono':
        if sys.platform == 'win32': return 'Consolas'
        if sys.platform == 'darwin': return 'Monaco'
        return 'Fixed'

    if type == 'mono2':
        if sys.platform in ['win32', 'darwin']: return 'Courier New'
        return 'Fixed'
