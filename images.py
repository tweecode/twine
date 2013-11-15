#!/usr/bin/env python

#
# Images
#
# A module for handling base64 encoded images and other assets.
#

import sys, cStringIO, wx, re
    
def RemoveURIPrefix(text):
    """Removes the Data URI part of the base64 data"""
    index = text.find(';base64,')
    return text[index+8:] if index else text

def Base64ToBitmap(text):
    """Converts the base64 data URI back into a bitmap"""
    try:
        # Remove data URI prefix and MIME type
        text = RemoveURIPrefix(text)
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

def GetImageType(text):
    """Returns the part of the Data URI's MIME type that refers to the type of the image."""
    # By using (\w+), "svg+xml" becomes "svg"
    search = re.search(r"data:image/(\w+)", text);
    if (search):
        return "." + search.group(1)
    return None
