"""
A module for handling base64 encoded images and other assets.
"""

import cStringIO, wx, re

def addURIPrefix(text, mimeType):
    """ Adds the Data URI MIME prefix to the base64 data"""
    # SVG MIME-type is the same for both images and fonts
    mimeType = mimeType.lower()
    if mimeType in 'gif|jpg|jpeg|png|webp|svg':
        mimeGroup = "image/"
    elif mimeType == 'woff':
        mimeGroup = "application/font-"
    elif mimeType in 'ttf|otf':
        mimeGroup = "application/x-font-"
    else:
        mimeGroup = "application/octet-stream"

    # Correct certain MIME types
    if mimeType == "jpg":
        mimeType = "jpeg"
    elif mimeType == "svg":
        mimeType += "+xml"
    return "data:" + mimeGroup + mimeType + ";base64," + text

def removeURIPrefix(text):
    """Removes the Data URI part of the base64 data"""
    index = text.find(';base64,')
    return text[index+8:] if index else text

def base64ToBitmap(text):
    """Converts the base64 data URI back into a bitmap"""
    try:
        # Remove data URI prefix and MIME type
        text = removeURIPrefix(text)
        # Convert to bitmap
        imgData = text.decode('base64')
        stream = cStringIO.StringIO(imgData)
        return wx.BitmapFromImage(wx.ImageFromStream(stream))
    except:
        pass

def bitmapToBase64PNG(bmp):
    img = bmp.ConvertToImage()
    # "PngZL" in wxPython 2.9 is equivalent to wx.IMAGE_OPTION_PNG_COMPRESSION_LEVEL in wxPython Phoenix
    img.SetOptionInt("PngZL", 9)
    stream = cStringIO.StringIO()
    try:
        img.SaveStream(stream, wx.BITMAP_TYPE_PNG)
        return "data:image/png;base64," + stream.getvalue().encode('base64')
    except:
        pass

def getImageType(text):
    """Returns the part of the Data URI's MIME type that refers to the type of the image."""
    # By using (\w+), "svg+xml" becomes "svg"
    search = re.search(r"data:image/(\w+)", text)
    if search:
        return "." + search.group(1)
    #Fallback
    search = re.search(r"application:x-(\w+)", text)
    if search:
        return "." + search.group(1)
    return ""
