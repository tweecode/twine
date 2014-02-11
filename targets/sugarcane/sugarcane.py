import header

class Header (header.Header):

    def __init__(self, id, path, builtinPath):
        super(Header, self).__init__(id, path, builtinPath)

    def filesToEmbed(self):
        """Returns an Ordered Dictionary of file names to embed into the output."""
        list = super(Header, self).filesToEmbed()
        return list
