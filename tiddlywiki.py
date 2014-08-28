"""
A Python implementation of the Twee compiler.

This code was written by Chris Klimas <klimas@gmail.com>
It is licensed under the GNU General Public License v2
http://creativecommons.org/licenses/GPL/2.0/

This file defines two classes: Tiddler and TiddlyWiki. These match what
you'd normally see in a TiddlyWiki; the goal here is to provide classes
that translate between Twee and TiddlyWiki output seamlessly.
"""

import re, time, locale, os, codecs
import tweeregex
from tweelexer import TweeLexer

class TiddlyWiki(object):
    """An entire TiddlyWiki."""

    def __init__(self):
        self.tiddlers = {}
        self.storysettings = {}

    def hasTiddler(self, name):
        return name in self.tiddlers

    def toTwee(self, order = None):
        """Returns Twee source code for this TiddlyWiki.
        The 'order' argument is a sequence of passage titles specifying the order
        in which passages should appear in the output string; by default passages
        are returned in arbitrary order.
        """
        tiddlers = self.tiddlers
        if order is None:
            order = tiddlers.keys()
        return u''.join(tiddlers[i].toTwee() for i in order)

    def read(self, filename):
        try:
            source = codecs.open(filename, 'rU', 'utf_8_sig', 'strict')
            w = source.read()
        except UnicodeDecodeError:
            try:
                source = codecs.open(filename, 'rU', 'utf16', 'strict')
                w = source.read()
            except:
                source = open(filename, 'rU')
                w = source.read()
        source.close()
        return w

    def toHtml(self, app, header = None, order = None, startAt = '', defaultName = '', metadata = {}):
        """Returns HTML code for this TiddlyWiki."""
        if not order: order = self.tiddlers.keys()
        output = u''

        if not header:
            app.displayError("building: no story format was specified.\n"
                            + "Please select another format from the Story Format submenu",
                            stacktrace = False)
            return

        try:
            headerPath = header.path + 'header.html'
            # TODO: Move file reading to Header class.
            output = self.read(headerPath)

        except IOError:
            app.displayError("building: the story format '" + header.label + "' isn't available.\n"
                + "Please select another format from the Story Format submenu",
                stacktrace = False)
            return


        def insertEngine(app, output, filename, label, extra = ''):
            if output.count(label) > 0:
                try:
                    enginecode = self.read(filename)
                    return output.replace(label,enginecode + extra)

                except IOError:
                    app.displayError("building: the file '" + filename + "' used by the story format '" + header.label + "' wasn't found",
                                     stacktrace = False)
                    return ''
            else:
                return output

        # Insert version number
        output = output.replace('"VERSION"', "Made in " + app.NAME + " " + app.VERSION)

        # Insert timestamp
        # Due to Windows limitations, the timezone offset must be computed manually.
        tz_offset = (lambda t: '%s%02d%02d' % (('+' if t <= 0 else '-',) + divmod(abs(t) / 60, 60)))(time.timezone)
        # Obtain the encoding expected to be used by strftime in this locale
        strftime_encoding = locale.getlocale(locale.LC_TIME)[1] or locale.getpreferredencoding()
        # Write the timestamp
        output = output.replace('"TIME"', "Built on "+time.strftime("%d %b %Y at %H:%M:%S, "+tz_offset).decode(strftime_encoding))

        # Insert the test play "start at passage" value
        if startAt:
            output = output.replace('"START_AT"', '"' + startAt.replace('\\', r'\\').replace('"', '\"') + '"')
        else:
            output = output.replace('"START_AT"', '""')

        # Embed any engine related files required by the header.

        embedded = header.filesToEmbed()
        for key in embedded.keys():
            output = insertEngine(app, output, embedded[key], key)
            if not output: return ''

        # Insert the Backup Story Title

        if defaultName:
            name = defaultName.replace('"',r'\"')
            # Just gonna assume the <title> has no attributes
            output = re.sub(r'<title>.*?<\/title>', '<title>'+name+'</title>', output, count=1, flags=re.I|re.M) \
                .replace('"Untitled Story"', '"'+name+'"')

        # Insert the metadata

        metatags = ''
        for name, content in metadata.iteritems():
            if content:
                metatags += '<meta name="' + name.replace('"','&quot;') + '" content="' + content.replace('"','&quot;') + '">\n'

        if metatags:
            output = re.sub(r'<\/title>\s*\n?', lambda a: a.group(0) + metatags, output, flags=re.I, count=1)

        # Check if the scripts are personally requesting jQuery or Modernizr
        jquery = 'jquery' in self.storysettings and self.storysettings['jquery'] != "off"
        modernizr = 'modernizr' in self.storysettings and self.storysettings['modernizr'] != "off"
        blankCSS = 'blankcss' in self.storysettings and self.storysettings['blankcss'] != "off"

        for i in filter(lambda a: (a.isScript() or a.isStylesheet()), self.tiddlers.itervalues()):
            if not jquery and i.isScript() and re.search(r'requires? jquery', i.text, re.I):
                jquery = True
            if not modernizr and re.search(r'requires? modernizr', i.text, re.I):
                modernizr = True
            if not blankCSS and i.isStylesheet() and re.search(r'blank stylesheet', i.text, re.I):
                blankCSS = True
            if jquery and modernizr and not blankCSS:
                break

        # Insert jQuery
        if jquery:
            output = insertEngine(app, output, app.builtinTargetsPath + 'jquery.js', '"JQUERY"')
            if not output: return
        else:
            output = output.replace('"JQUERY"','')

        # Insert Modernizr
        if modernizr:
            output = insertEngine(app, output, app.builtinTargetsPath + 'modernizr.js', '"MODERNIZR"')
            if not output: return
        else:
            output = output.replace('"MODERNIZR"','')

        # Remove default CSS
        if blankCSS:
            # Just gonna assume the html id is quoted correctly if at all.
            output = re.sub(r'<style\s+id=["\']?defaultCSS["\']?\s*>(?:[^<]|<(?!\/style>))*<\/style>', '', output, flags=re.I|re.M, count=1)

        rot13 = 'obfuscate' in self.storysettings and \
            self.storysettings['obfuscate'] != 'off'
        # In case it was set to "swap" (legacy 1.4.1 file),
        # alter and remove old properties.
        if rot13:
            self.storysettings['obfuscate'] = "rot13"
            if 'obfuscatekey' in self.storysettings:
                del self.storysettings['obfuscatekey']

        # Finally add the passage data
        storyfragments = []
        for i in order:
            tiddler = self.tiddlers[i]
            # Strip out comments from storysettings and reflect any alterations made
            if tiddler.title == 'StorySettings':
                tiddler.text = ''.join([(str(k)+":"+str(v)+"\n") for k,v in self.storysettings.iteritems()])
            if self.NOINCLUDE_TAGS.isdisjoint(tiddler.tags):
                storyfragments.append(tiddler.toHtml(rot13 and tiddler.isObfuscateable()))
        storycode = u''.join(storyfragments)

        if output.count('"STORY_SIZE"') > 0:
            output = output.replace('"STORY_SIZE"', '"' + str(len(storyfragments)) + '"')

        if output.count('"STORY"') > 0:
            output = output.replace('"STORY"', storycode)
        else:
            output += storycode
            if header:
                footername = header.path + 'footer.html'
                if os.path.exists(footername):
                    output += self.read(footername)
                else:
                    output += '</div></body></html>'

        return output

    def toRtf(self, order = None):
        """Returns RTF source code for this TiddlyWiki."""
        if not order: order = self.tiddlers.keys()

        def rtf_encode_char(unicodechar):
            if ord(unicodechar) < 128:
                return str(unicodechar)
            return r'\u' + str(ord(unicodechar)) + r'?'

        def rtf_encode(unicodestring):
            return r''.join(rtf_encode_char(c) for c in unicodestring)

        # preamble

        output = r'{\rtf1\ansi\ansicpg1251' + '\n'
        output += r'{\fonttbl\f0\fswiss\fcharset0 Arial;\f1\fmodern\fcharset0 Courier;}' + '\n'
        output += r'{\colortbl;\red128\green128\blue128;\red51\green51\blue204;}' + '\n'
        output += r'\margl1440\margr1440\vieww9000\viewh8400\viewkind0' + '\n'
        output += r'\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx792' + '\n'
        output += r'\tx8640\ql\qnatural\pardirnatural\pgnx720\pgny720' + '\n'

        # content

        for i in order:
            # Handle the situation where items are in the order set but not in the tiddlers set.
            if i not in self.tiddlers:
                continue
            text = rtf_encode(self.tiddlers[i].text)
            text = re.sub(r'\n', '\\\n', text) # newlines
            text = re.sub(tweeregex.LINK_REGEX, r'\\b\cf2 \ul \1\ulnone \cf0 \\b0 ', text) # links
            text = re.sub(r"''(.*?)''", r'\\b \1\\b0 ', text) # bold
            text = re.sub(r'\/\/(.*?)\/\/', r'\i \1\i0 ', text) # italics
            text = re.sub(r"\^\^(.*?)\^\^", r'\\super \1\\nosupersub ', text) # sup
            text = re.sub(r"~~(.*?)~~", r'\\sub \1\\nosupersub ', text) # sub
            text = re.sub(r"==(.*?)==", r'\\strike \1\\strike0 ', text) # strike
            text = re.sub(r'(\<\<.*?\>\>)', r'\\f1\cf1 \1\cf0\\f0 ', text) # macros
            text = re.sub(tweeregex.HTML_REGEX, r'\\f1\cf1 \g<0>\cf0\\f0 ', text) # macros
            text = re.sub(tweeregex.MONO_REGEX, r'\\f1 \1\\f0 ', text) # monospace
            text = re.sub(tweeregex.COMMENT_REGEX, '', text) # comments

            output += r'\fs24\b1 ' + rtf_encode(self.tiddlers[i].title) + r'\b0\fs20 ' + '\\\n'
            output += text + '\\\n\\\n'

        output += '}'

        return output

    def addTwee(self, source):
        """Adds Twee source code to this TiddlyWiki.
        Returns the tiddler titles in the order they occurred in the Twee source.
        """
        source = source.replace("\r\n", "\n")
        source = '\n' + source
        tiddlers = source.split('\n::')[1:]

        order = []
        for i in tiddlers:
            tiddler = Tiddler('::' + i)
            self.addTiddler(tiddler)
            order.append(tiddler.title)
        return order

    def addHtml(self, source):
        """Adds HTML source code to this TiddlyWiki.
        Returns the tiddler titles in the order they occurred in the HTML.
        """
        order = []
        divs = re.search(r'<div\s+id=(["\']?)store(?:A|-a)rea\1(?:\s+data-size=(["\']?)\d+\2)?(?:\s+hidden)?\s*>(.*)</div>', source,
                        re.DOTALL)
        if divs:
            divs = divs.group(3)
            # HTML may be obfuscated.
            obfuscatekey = ''
            storysettings_re = r'[^>]*\stiddler=["\']?StorySettings["\']?[^>]*>.*?</div>'
            storysettings = re.search(r'<div'+storysettings_re, divs, re.DOTALL)
            if storysettings:
                ssTiddler = self.addTiddler(Tiddler(storysettings.group(0), 'html'))
                obfuscate = re.search(r'obfuscate\s*:\s*((?:[^\no]|o(?!ff))*)\s*(?:\n|$)', ssTiddler.text, re.I)
                if obfuscate:
                    if "swap" in obfuscate.group(1):
                        # Find the legacy 'obfuscatekey' option from 1.4.0.
                        match = re.search(r'obfuscatekey\s*:\s*(\w*)\s*(?:\n|$)', ssTiddler.text, re.I)
                        if match:
                            obfuscatekey = match.group(1)
                            nss = u''
                            for nsc in obfuscatekey:
                                if nss.find(nsc) == -1 and not nsc in ':\\\"n0':
                                    nss = nss + nsc
                            obfuscatekey = nss
                    else:
                        obfuscatekey = "anbocpdqerfsgthuivjwkxlymz"
                divs = divs[:storysettings.start(0)] + divs[storysettings.end(0):]

            for div in divs.split('<div'):
                div.strip()
                if div:
                    tiddler = Tiddler('<div' + div, 'html', obfuscatekey)
                    self.addTiddler(tiddler)
                    order.append(tiddler.title)
        return order

    def addHtmlFromFilename(self, filename):
        return self.addHtml(self.read(filename))

    def addTweeFromFilename(self, filename):
        return self.addTwee(self.read(filename))

    def addTiddler(self, tiddler):
        """Adds a Tiddler object to this TiddlyWiki."""
        self.tiddlers[tiddler.title] = tiddler
        return tiddler

    FORMATTED_INFO_PASSAGES = frozenset([
            'StoryMenu', 'StoryTitle', 'StoryAuthor', 'StorySubtitle', 'StoryInit'])
    UNFORMATTED_INFO_PASSAGES = frozenset(['StoryIncludes', 'StorySettings'])
    INFO_PASSAGES = FORMATTED_INFO_PASSAGES | UNFORMATTED_INFO_PASSAGES
    SPECIAL_TAGS = frozenset(['Twine.image'])
    NOINCLUDE_TAGS = frozenset(['Twine.private', 'Twine.system'])
    INFO_TAGS = frozenset(['script', 'stylesheet', 'annotation']) | SPECIAL_TAGS | NOINCLUDE_TAGS


class Tiddler: # pylint: disable=old-style-class
    """A single tiddler in a TiddlyWiki.

    Note: Converting this to a new-style class breaks pickling of new TWS files on old Twine releases.
    """

    def __init__(self, source, type = 'twee', obfuscatekey = ""):
        # cache of passage names linked from this one
        self.links = []
        self.displays = []
        self.images = []
        self.macros = []

        """Pass source code, and optionally 'twee' or 'html'"""
        if type == 'twee':
            self.initTwee(source)
        else:
            self.initHtml(source, obfuscatekey)

    def __getstate__(self):
        """Need to retain pickle format backwards-compatibility with Twine 1.3.5 """
        now = time.localtime()
        return {
            'created': now,
            'modified': now,
            'title': self.title,
            'tags': self.tags,
            'text': self.text,
        }

    def __repr__(self):
        return "<Tiddler '" + self.title + "'>"

    def initTwee(self, source):
        """Initializes a Tiddler from Twee source code."""

        # used only during builds
        self.pos = [0,0]

        # figure out our title

        lines = source.strip().split('\n')

        meta_bits = lines[0].split('[')
        self.title = meta_bits[0].strip(' :')

        # find tags

        self.tags = []

        if len(meta_bits) > 1:
            tag_bits = meta_bits[1].split(' ')

            for tag in tag_bits:
                self.tags.append(tag.strip('[]'))

        # and then the body text

        self.text = u''

        for line in lines[1:]:
            self.text += line + "\n"

        self.text = self.text.strip()


    def initHtml(self, source, obfuscatekey = ""):
        """Initializes a Tiddler from HTML source code."""

        def decode_obfuscate_swap(text):
            """
            Does basic character pair swapping obfuscation.
            No longer used since 1.4.2, but can decode passages from 1.4.0 and 1.4.1
            """
            r = ''
            for c in text:
                upper = c.isupper()
                p = obfuscatekey.find(c.lower())
                if p != -1:
                    if p % 2 == 0:
                        p1 = p + 1
                        if p1 >= len(obfuscatekey):
                            p1 = p
                    else:
                        p1 = p - 1
                    c = obfuscatekey[p1].upper() if upper else obfuscatekey[p1]
                r = r + c
            return r

        # title

        self.title = 'Untitled Passage'
        title_re = re.compile(r'(?:data\-)?(?:tiddler|name)="([^"]*?)"')
        title = title_re.search(source)
        if title:
            self.title = title.group(1)

        # tags

        self.tags = []
        tags_re = re.compile(r'(?:data\-)?tags="([^"]*?)"')
        tags = tags_re.search(source)
        if tags and tags.group(1) != '':
            self.tags = tags.group(1).split(' ')

        # position
        self.pos = [0,0]
        pos_re = re.compile(r'(?:data\-)?(?:twine\-)?position="([^"]*?)"')
        pos = pos_re.search(source)
        if pos:
            coord = pos.group(1).split(',')
            if len(coord) == 2:
                try:
                    self.pos = map(int, coord)
                except ValueError:
                    pass

        # body text
        self.text = ''
        text_re = re.compile(r'<div(?:[^"]|(?:".*?"))*?>((?:[^<]|<(?!\/div>))*)<\/div>')
        text = text_re.search(source)
        if text:
            self.text = decode_text(text.group(1))

        # deobfuscate
        # Note that we call isObfuscateable() using the raw title and tags, since if
        # the tiddler is not obfuscatable, those will be stored non-obfuscated.
        if obfuscatekey and self.isObfuscateable():
            self.title = decode_obfuscate_swap(self.title)
            self.tags = [decode_obfuscate_swap(tag) for tag in self.tags]
            self.text = decode_obfuscate_swap(self.text)

    def toHtml(self, rot13):
        """Returns an HTML representation of this tiddler.
        The encoder arguments are sequences of functions that take a single text argument
        and return a modified version of the given text.
        """

        def applyRot13(text):
            return text.decode('rot13') if rot13 else text

        def iterArgs():
            yield 'tiddler', applyRot13(self.title.replace('"', '&quot;'))
            if self.tags:
                yield 'tags', ' '.join(applyRot13(tag) for tag in self.tags)

        return u'<div%s%s>%s</div>' % (
            ''.join(' %s="%s"' % arg for arg in iterArgs()),
            ' twine-position="%d,%d"' % tuple(self.pos) if hasattr(self, "pos") else "",
            encode_text(applyRot13(self.text))
            )


    def toTwee(self):
        """Returns a Twee representation of this tiddler."""
        output = u':: ' + self.title

        if len(self.tags) > 0:
            output += u' ['
            for tag in self.tags:
                output += tag + ' '
            output = output.strip()
            output += u']'

        output += u"\n" + self.text + u"\n\n\n"
        return output

    def isImage(self):
        return 'Twine.image' in self.tags

    def isAnnotation(self):
        return 'annotation' in self.tags

    def isStylesheet(self):
        return 'stylesheet' in self.tags

    def isScript(self):
        return 'script' in self.tags

    def isInfoPassage(self):
        return self.title in TiddlyWiki.INFO_PASSAGES

    def isStoryText(self):
        """ Excludes passages which do not contain renderable Twine code. """
        return self.title not in TiddlyWiki.UNFORMATTED_INFO_PASSAGES \
            and TiddlyWiki.INFO_TAGS.isdisjoint(self.tags)

    def isStoryPassage(self):
        """ A more restrictive variant of isStoryText that excludes the StoryTitle, StoryMenu etc."""
        return self.title not in TiddlyWiki.INFO_PASSAGES \
            and TiddlyWiki.INFO_TAGS.isdisjoint(self.tags)

    def isObfuscateable(self):
        """Returns true iff this tiddler can be obfuscated when placed in the data store."""
        return self.title != 'StorySettings' and not self.isImage()

    def linksAndDisplays(self):
        return list(set(self.links+self.displays))

    def update(self):
        """
        Update the lists of all passages linked/displayed by this one.
        Returns internal links and <<choice>>/<<actions>> macros.
        """
        if not self.isStoryText() and not self.isAnnotation() and not self.isStylesheet():
            self.displays = []
            self.links = []
            self.variableLinks = []
            self.images = []
            self.macros = []
            return

        images = set()
        macros = set()
        links = set()
        variableLinks = set()

        def addLink(link):
            style = TweeLexer.linkStyle(link)
            if style == TweeLexer.PARAM:
                variableLinks.add(link)
            elif style != TweeLexer.EXTERNAL:
                links.add(link)

        # <<display>>
        self.displays = list(set(re.findall(r'\<\<display\s+[\'"]?(.+?)[\'"]?\s?\>\>', self.text, re.IGNORECASE)))

        macros = set()
        # other macros (including shorthand <<display>>)
        for m in re.finditer(tweeregex.MACRO_REGEX, self.text):
            # Exclude shorthand <<print>>
            if m.group(1) and m.group(1)[0] != '$':
                macros.add(m.group(1))
        self.macros = list(macros)

        # Regular hyperlinks (also matches wiki-style links inside macros)
        for m in re.finditer(tweeregex.LINK_REGEX, self.text):
            addLink(m.group(2) or m.group(1))

        # Include images
        for m in re.finditer(tweeregex.IMAGE_REGEX, self.text):
            if m.group(5):
                addLink(m.group(5))

        # HTML data-passage links
        for m in re.finditer(tweeregex.HTML_REGEX, self.text):
            attrs = m.group(2)
            if attrs:
                dataPassage = re.search(r"""data-passage\s*=\s*(?:([^<>'"=`\s]+)|'((?:[^'\\]*\\.)*[^'\\]*)'|"((?:[^"\\]*\\.)*[^"\\]*)")""", attrs)
                if dataPassage:
                    link = dataPassage.group(1) or dataPassage.group(2) or dataPassage.group(3)
                    if m.group(1) == "img":
                        images.add(link)
                    else:
                        addLink(link)

        # <<choice passage_name [link_text]>>
        for block in re.findall(r'\<\<choice\s+(.*?)\s?\>\>', self.text):
            item = re.match(r'(?:"([^"]*)")|(?:\'([^\']*)\')|([^"\'\[\s]\S*)', block)
            if item:
                links.add(''.join(item.groups('')))

        # <<actions '' ''>>
        for block in re.findall(r'\<\<actions\s+(.*?)\s?\>\>', self.text):
            links.update(re.findall(r'[\'"](.*?)[\'"]', block))

        self.links = list(links)
        self.variableLinks = list(variableLinks)

        # Images

        for block in re.finditer(tweeregex.IMAGE_REGEX, self.text):
            images.add(block.group(4))

        self.images = list(images)

#
# Helper functions
#

def encode_text(text):
    """Encodes a string for use in HTML output."""
    output = text \
        .replace('\\', '\s') \
        .replace('\t', '\\t') \
        .replace('&', '&amp;') \
        .replace('<', '&lt;') \
        .replace('>', '&gt;') \
        .replace('"', '&quot;') \
        .replace('\0', '&#0;')
    output = re.sub(r'\r?\n', r'\\n', output)
    return output

def decode_text(text):
    """Decodes a string from HTML."""
    return text \
        .replace('\\n', '\n') \
        .replace('\\t', '\t') \
        .replace('\s', '\\') \
        .replace('&quot;', '"') \
        .replace('&gt;', '>') \
        .replace('&lt;', '<') \
        .replace('&amp;', '&')

def encode_date(date):
    """Encodes a datetime in TiddlyWiki format."""
    return time.strftime('%Y%m%d%H%M', date)


def decode_date(date):
    """Decodes a datetime from TiddlyWiki format."""
    return time.strptime(date, '%Y%m%d%H%M')
