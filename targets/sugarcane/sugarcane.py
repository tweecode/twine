import header

class Header (header.Header):

    def __init__(self, id, path):
        super(Header, self).__init__(id, path)

    def files_to_embed(self):
        """Returns an Ordered Dictionary of file names to embed into the output."""
        list = super(Header, self).files_to_embed()
        list['"SUGARCANE"'] = 'code.js'
        return list