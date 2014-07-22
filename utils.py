from urlparse import urlparse

def isURL(location):
    return urlparse(location).scheme != ''
