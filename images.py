#!/usr/bin/env python

#
# Images
#
# A module for handling base64 encoded images and other assets.
#

import sys, cStringIO, wx

def Base64ToBitmap(text):
    """Converts the base64 data URI back into a bitmap"""
    try:
        # Remove data URI prefix and MIME type
        text = text[text.find(';base64,')+8:]
        # Convert to bitmap
        imgData = text.decode('base64')
        stream = cStringIO.StringIO(imgData)
        return wx.BitmapFromImage(wx.ImageFromStream(stream))
    except:
        pass
    
def BitmapToBase64PNG(bmp):
    img = bmp.ConvertToImage()
    # "PngZL" in wxPython 2.9 is equivalent to wx.IMAGE_OPTION_PNG_COMPRESSION_LEVEL in wxPython Phoenix
    img.SetOptionInt("PngZL", 9)
    stream = cStringIO.StringIO()
    try:
        img.SaveStream(stream, wx.BITMAP_TYPE_PNG)
        return "data:image/png;base64," + stream.getvalue().encode('base64')
    except:
        pass
