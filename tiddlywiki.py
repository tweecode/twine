#
# TiddlyWiki.py
#
# A Python implementation of the Twee compiler.
#
# This code was written by Chris Klimas <klimas@gmail.com>
# It is licensed under the GNU General Public License v2
# http://creativecommons.org/licenses/GPL/2.0/
#
# This file defines two classes: Tiddler and TiddlyWiki. These match what
# you'd normally see in a TiddlyWiki; the goal here is to provide classes
# that translate between Twee and TiddlyWiki output seamlessly.
#

import re, datetime, time, locale, os, sys, tempfile, codecs
import tweelexer
from tweelexer import TweeLexer

#
# TiddlyWiki class
#

class TiddlyWiki:
	"""An entire TiddlyWiki."""
	
	def __init__ (self, author = 'twee'):
		"""Optionally pass an author name."""
		self.author = author
		self.tiddlers = {}
		self.storysettings = {}

	def hasTiddler(self, name):
		return name in self.tiddlers
	
	def tryGetting (self, names, default = ''):
		"""Tries retrieving the text of several tiddlers by name; returns default if none exist."""
		for name in names:
			if name in self.tiddlers:
				return self.tiddlers[name].text
				
		return default
		
	def toTwee (self, order = None):
		"""Returns Twee source code for this TiddlyWiki."""
		if not order: order = self.tiddlers.keys()		
		output = u''
		
		for i in order:
			output += self.tiddlers[i].toTwee()
		
		return output
		
	def read(self, filename):
		try:
			source = codecs.open(filename, 'r', 'utf_8_sig', 'strict')
			w = source.read()
		except UnicodeDecodeError:
			try:
				source = codecs.open(filename, 'r', 'utf16', 'strict')
				w = source.read()
			except:
				source = open(filename, 'rb')
				w = source.read()
		source.close()
		# Normalise line endings
		w = w.replace('\r\n','\n')
		return w
	
	def toHtml (self, app, target = None, order = None, startAt = '', defaultName = ''):
		"""Returns HTML code for this TiddlyWiki. If target is passed, adds a header."""
		if not order: order = self.tiddlers.keys()
		output = u''
		
		if not target:
			app.displayError("building: no story format was specified.\n"
							+ "Please select another format from the Story Format submenu.\n\n")
			return
		
		try:
			headerPath = os.sep + 'targets' + os.sep + target + os.sep + 'header.html'
			
			if sys.platform == "darwin":
				externalFormatDir = re.sub('[^/]+.app/.*', '', app.getPath())
				if os.access(externalFormatDir + headerPath, os.R_OK):
					headerPath = externalFormatDir + headerPath
				else:
					headerPath = app.getPath() + headerPath
			else:
				headerPath = app.getPath() + headerPath
			output = self.read(headerPath)
		except IOError:
			app.displayError("building: the story format '" + target + "' isn't available.\n"
				+ "Please select another format from the Story Format submenu.\n\n")
			return
		
		
		def insertEngine(app, output, filename, label, extra = ''):
			if output.count(label) > 0:
				try:
					enginecode = self.read(app.getPath() + os.sep + 'targets' + os.sep + filename)
					return output.replace(label,enginecode + extra)
				except IOError:
					app.displayError("building: the file '" + filename + "' used by the story format '" + target + "' wasn't found.\n\n")
					return None
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
		if (startAt):
			output = output.replace('"START_AT"', '"' + startAt.replace('\\', r'\\').replace('"', '\"') + '"')
		else:
			output = output.replace('"START_AT"', '""')
		
		# Insert the main engine
		output = insertEngine(app, output, 'engine.js', '"ENGINE"')
		if not output: return
		
		# Insert Sugarcane/Jonah code if the storyformat is a Sugarcane/Jonah offshoot
		output = insertEngine(app, output, 'sugarcane/code.js', '"SUGARCANE"')
		if not output: return
		output = insertEngine(app, output, 'jonah/code.js', '"JONAH"')
		if not output: return
		
		# Insert the Backup Story Title
		if defaultName:
			output = output.replace('"Untitled Story"', '"'+defaultName.replace('"',r'\"')+'"')
		
		falseOpts = ["false", "off", "0"]
		
		# Check if the scripts are personally requesting jQuery or Modernizr
		jquery = 'jquery' in self.storysettings and self.storysettings['jquery'] not in falseOpts
		modernizr = 'modernizr' in self.storysettings and self.storysettings['modernizr'] not in falseOpts
		
		for i in filter(lambda a: (a.isScript() or a.isStylesheet()), self.tiddlers.itervalues()):
			if not jquery and i.isScript() and re.search(r'requires? jquery', i.text, re.I):
				jquery = True
			if not modernizr and re.search(r'requires? modernizr', i.text, re.I):
				modernizr = True
			if jquery and modernizr:
				break
		
		# Insert jQuery
		if jquery:
			output = insertEngine(app, output, 'jquery.js', '"JQUERY"')
			if not output: return
		else:
			output = output.replace('"JQUERY"','')
		
		# Insert Modernizr
		if modernizr:
			output = insertEngine(app, output, 'modernizr.js', '"MODERNIZR"')
			if not output: return
		else:
			output = output.replace('"MODERNIZR"','')
		
		obfuscate = 'obfuscate' in self.storysettings and \
			self.storysettings['obfuscate'] == 'swap' and 'obfuscatekey' in self.storysettings;
		
		if obfuscate:
			# Quick Rot13 shortcut
			if self.storysettings['obfuscatekey'] == 'rot13':
				self.storysettings['obfuscatekey'] = "anbocpdqerfsgthuivjwkxlymz";
			nss = u''
			for nsc in self.storysettings['obfuscatekey']:
				if nss.find(nsc) == -1 and not nsc in ':\\\"n0':
					nss = nss + nsc
			self.storysettings['obfuscatekey'] = nss
		
		storycode = u''
		for i in order:
			if not any(t in self.NOINCLUDE_TAGS for t in self.tiddlers[i].tags):
				if (self.tiddlers[i].title == 'StorySettings' or not obfuscate):
					storycode += self.tiddlers[i].toHtml(self.author)
				else:
					storycode += self.tiddlers[i].toHtml(self.author, obfuscation = True, obfuscationkey = self.storysettings['obfuscatekey'])
		
		if output.count('"STORY"') > 0:
			output = output.replace('"STORY"', storycode)
		else:
			output += storycode
			if (target):
				footername = app.getPath() + os.sep + 'targets' + os.sep + target + os.sep + 'footer.html'
				if os.path.exists(footername):
					output += self.read(footername)
				else:
					output += '</div></body></html>'

		return output
	
	def toRtf (self, order = None):
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
			text = rtf_encode(self.tiddlers[i].text)
			text = re.sub(r'\n', '\\\n', text) # newlines
			text = re.sub(TweeLexer.LINK_REGEX, r'\\b\cf2 \ul \1\ulnone \cf0 \\b0', text) # links
			text = re.sub(r"''(.*?)''", r'\\b \1\\b0 ', text) # bold
			text = re.sub(r'\/\/(.*?)\/\/', r'\i \1\i0 ', text) # italics
			text = re.sub(r"\^\^(.*?)\^\^", r'\\super \1\\nosupersub ', text) # sup
			text = re.sub(r"~~(.*?)~~", r'\\sub \1\\nosupersub ', text) # sub
			text = re.sub(r"==(.*?)==", r'\\strike \1\\strike0 ', text) # strike
			text = re.sub(r'(\<\<.*?\>\>)', r'\\f1\cf1 \1\cf0\\f0', text) # macros
			text = re.sub(TweeLexer.HTML_REGEX, r'\\f1\cf1 \g<0>\cf0\\f0', text) # macros
			text = re.sub(TweeLexer.MONO_REGEX, r'\\f1 \1\\f0', text) # monospace
			text = re.sub(TweeLexer.COMMENT_REGEX, '', text) # comments

			output += r'\fs24\b1' + rtf_encode(self.tiddlers[i].title) + r'\b0\fs20' + '\\\n'
			output += text + '\\\n\\\n'
		
		output += '}'
			
		return output
				
	def addTwee (self, source):
		"""Adds Twee source code to this TiddlyWiki."""
		source = source.replace("\r\n", "\n")
		tiddlers = source.split('\n::')
		
		for i in tiddlers:
			self.addTiddler(Tiddler('::' + i))
			
	def addHtml (self, source):
		
		"""Adds HTML source code to this TiddlyWiki."""	
		divs = re.search(r'<div\sid=["\']?store(?:A|-a)rea["\']?>(.*)</div>', source,
						re.DOTALL)
		if divs:
			divs = divs.group(1);
			# HTML may be obfuscated.
			obfuscationkey = ''
			storysettings_re = r'[^>]*\stiddler=["\']?StorySettings["\']?[^>]*>.*?</div>'
			storysettings = re.search(r'<div'+storysettings_re, divs, re.DOTALL)
			if storysettings:
				ssTiddler = self.addTiddler(Tiddler(storysettings.group(0), 'html'))
				if re.search(r'obfuscate\s*:\s*swap\s*[\n$]', ssTiddler.text, re.I):
					match = re.search(r'obfuscatekey\s*:\s*(\w*)\s*[\n$]', ssTiddler.text, re.I)
					if match:
						obfuscationkey = match.group(1)
						nss = u''
						for nsc in obfuscationkey:
							if nss.find(nsc) == -1 and not nsc in ':\\\"n0':
								nss = nss + nsc
						obfuscationkey = nss
				divs = divs[:storysettings.start(0)] + divs[storysettings.end(0)+1:]
			
			for div in divs.split('<div'):
				div.strip()
				if div:
					self.addTiddler(Tiddler('<div' + div, 'html', obfuscationkey))
			
	def addHtmlFromFilename(self, filename):
		self.addTweeFromFilename(filename, True)
		
	def addTweeFromFilename(self, filename, html = False):
		w = self.read(filename)
		if html:
			self.addHtml(w)
		else:
			self.addTwee(w)

	def addTiddler (self, tiddler):
		"""Adds a Tiddler object to this TiddlyWiki."""
		
		if tiddler.title in self.tiddlers:
			if (tiddler == self.tiddlers[tiddler.title]) and \
				 (tiddler.modified > self.tiddlers[tiddler.title].modified):
				self.tiddlers[tiddler.title] = tiddler
		else:
			self.tiddlers[tiddler.title] = tiddler
		
		return tiddler
	
	INFO_PASSAGES = ['StoryMenu', 'StoryTitle', 'StoryAuthor', 'StorySubtitle', 'StoryIncludes', 'StorySettings', 'StartPassages']
	FORMATTED_INFO_PASSAGES = ['StoryMenu', 'StoryTitle', 'StoryAuthor', 'StorySubtitle']
	SPECIAL_TAGS = ['Twine.image']
	NOINCLUDE_TAGS = ['Twine.private', 'Twine.system']
	INFO_TAGS = ['script', 'stylesheet', 'annotation'] + SPECIAL_TAGS + NOINCLUDE_TAGS
#
# Tiddler class
#

class Tiddler:
	"""A single tiddler in a TiddlyWiki."""
	
	def __init__ (self, source, type = 'twee', obfuscationkey = ""):
		# cache of passage names linked from this one
		self.links = []
		self.displays = []
		self.images = []
		self.macros = []
        
		"""Pass source code, and optionally 'twee' or 'html'"""
		if type == 'twee':
			self.initTwee(source)
		else:
			self.initHtml(source, obfuscationkey)

	def __getstate__ (self):
		"""Need to retain pickle format backwards-compatibility with Twine 1.3.5 """
		return {
			'created': self.created,
			'modified': self.modified,
			'title': self.title,
			'tags': self.tags,
			'text': self.text,
		}
		
	def __repr__ (self):
		return "<Tiddler '" + self.title + "'>"

	def __cmp__ (self, other):
		"""Compares a Tiddler to another."""
		return hasattr(other, 'text') and self.text == other.text
	
	def initTwee (self, source):
		"""Initializes a Tiddler from Twee source code."""
	
		# we were just born
		
		self.created = self.modified = time.localtime()
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
		
		
	def initHtml (self, source, obfuscationkey = ""):
		"""Initializes a Tiddler from HTML source code."""
		
		# title
		
		self.title = 'Untitled Passage'
		title_re = re.compile(r'(?:data\-)?(?:tiddler|name)="([^"]*?)"')
		title = title_re.search(source)
		if title:
			self.title = title.group(1)
			if obfuscationkey:
				self.title = encode_obfuscate_swap(self.title, obfuscationkey);
				
		# tags
		
		self.tags = []
		tags_re = re.compile(r'(?:data\-)?tags="([^"]*?)"')
		tags = tags_re.search(source)
		if tags and tags.group(1) != '':
			if obfuscationkey:
				self.tags = encode_obfuscate_swap(tags.group(1), obfuscationkey).split(' ');
			else: self.tags = tags.group(1).split(' ')	
			
		# creation date
		
		self.created = time.localtime()
		created_re = re.compile(r'(?:data\-)?created="([^"]*?)"')
		created = created_re.search(source)
		if created:
			self.created = decode_date(created.group(1))
			
		# modification date
		
		self.modified = time.localtime()
		modified_re = re.compile(r'(?:data\-)?modified="([^"]*?)"')
		modified = modified_re.search(source)
		if (modified):
			self.modified = decode_date(modified.group(1))

		# position
		self.pos = [0,0]
		pos_re = re.compile(r'(?:data\-)?(?:twine\-)?position="([^"]*?)"')
		pos = pos_re.search(source)
		if (pos):
			self.pos = map(int, pos.group(1).split(','))
		
		# body text
		self.text = ''
		text_re = re.compile(r'<div(?:[^"]|(?:".*?"))*?>((?:[^<]|<(?!\/div>))*)<\/div>')
		text = text_re.search(source)
		if (text):
			self.text = decode_text(text.group(1))
			if obfuscationkey:
				self.text = encode_obfuscate_swap(self.text, obfuscationkey);
		
	def toHtml (self, author = 'twee', obfuscation = False, obfuscationkey = ''):
		"""Returns an HTML representation of this tiddler."""
			
		now = time.localtime()
		output = ''
		title = self.title.replace('"','&quot;')
		if not obfuscation:
			output = u'<div tiddler="' + title + '" tags="'
			for tag in self.tags:
				output += tag + ' '
		else:
			output = u'<div tiddler="' + encode_obfuscate_swap(title, obfuscationkey) + '" tags="'
			for tag in self.tags:
				output += encode_obfuscate_swap(tag + ' ', obfuscationkey)
		output = output.strip()

		output += '" modified="' + encode_date(self.modified) + '"'
		output += ' created="' + encode_date(self.created) + '"' 
		if hasattr(self, 'pos'):
			output += ' twine-position="' + str(int(self.pos[0])) + ',' + str(int(self.pos[1])) + '"'
		output += ' modifier="' + author.replace('"','&quot;') + '">'
		output += encode_text(self.text, obfuscation, obfuscationkey) + '</div>'
		 
		return output
		
		
	def toTwee (self):
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
	
	def isStoryText(self):
		return not (('script' in self.tags) or self.isStylesheet()
			or self.isAnnotation() or any('Twine.' in i for i in self.tags)
			or (self.title in TiddlyWiki.INFO_PASSAGES and self.title not in TiddlyWiki.FORMATTED_INFO_PASSAGES))
	
	def isStoryPassage(self):
		""" A more restrictive variant of isStoryText that excludes the StoryTitle, StoryMenu etc."""
		return self.isStoryText() and self.title not in TiddlyWiki.INFO_PASSAGES
	
	def linksAndDisplays(self):
		return list(set(self.links+self.displays))
    
	def update(self, includeInternal = True, includeMacros = True):
		"""
		Update the lists of all passages linked/displayed by this one. By default,
		returns internal links and <<choice>>/<<actions>> macros.
		"""
		if not self.isStoryText() and not self.isAnnotation() and not self.isStylesheet():
			self.displays = []
			self.links = []
			self.images = []
			self.macros = []
			return
        
		# <<display>>
		self.displays = re.findall(r'\<\<display\s+[\'"]?(.+?)[\'"]?\s?\>\>', self.text, re.IGNORECASE)
		
		self.macros = []
		# other macros (including shorthand <<display>>)
		iterator = re.finditer(TweeLexer.MACRO_REGEX, self.text)
		for m in iterator:
			# Exclude shorthand <<print>>
			if m.group(1) and m.group(1)[0] != '$':
				self.macros.append(m.group(1))
        
		links = []
		actions = []
		choices = []
		images = []
		
		# regular hyperlinks
		if includeInternal:
			iterator = re.finditer(TweeLexer.LINK_REGEX, self.text)
			for m in iterator:
				links.append(m.group(2) or m.group(1))
			
			# Include images
			iterator = re.finditer(TweeLexer.IMAGE_REGEX, self.text)
			for m in iterator:
				if m.group(5):
					links.append(m.group(5))

		if includeMacros:
			
			# <<choice>>
			choices = []
			choiceBlocks = re.findall(r'\<\<choice\s+(.*?)\s?\>\>', self.text)
			for block in choiceBlocks:
				# New style <<choice>>
				item = re.match(TweeLexer.LINK_REGEX, block)
				if item:
					choices.append(m.group(2) or m.group(1))
				else:
					# Old style
					item = re.match(r'(?:"([^"]*)")|(?:\'([^\']*)\')|([^"\'\s]\S*)', block)
					if item:
						choices.append(re.sub(r'^[^\|]*\|', '', ''.join(item.groups(''))))
			
			# <<actions '' ''>>
			
			actions = []
			actionBlocks = re.findall(r'\<\<actions\s+(.*?)\s?\>\>', self.text)
			for block in actionBlocks:
				actions = actions + re.findall(r'[\'"](.*?)[\'"]', block)
		
		# remove duplicates by converting to a set
		
		self.links = list(set(links + choices + actions))
		
		# Images
		
		imageBlocks = re.finditer(TweeLexer.IMAGE_REGEX, self.text)
		for block in imageBlocks:
			images.append(block.group(4))
		
		self.images = images

#
# Helper functions
#


def encode_text (text, obfuscation, obfuscationkey):
	"""Encodes a string for use in HTML output."""
	output = text
	if obfuscation: output = encode_obfuscate_swap(output, obfuscationkey)
	output = output.replace('\\', '\s')
	output = output.replace('\t', '\\t')
	output = re.sub(r'\r?\n', r'\\n', output)
	output = output.replace('<', '&lt;')
	output = output.replace('>', '&gt;')
	output = output.replace('"', '&quot;')
	return output

def encode_obfuscate_swap(text, obfuscationkey):
	"""Does basic character pair swapping obfuscation""" 
	r = ''
	for c in text:
		upper = c.isupper()
		p = obfuscationkey.find(c.lower())
		if p <> -1:
			if p % 2 == 0:
				p1 = p + 1
				if p1 >= len(obfuscationkey): 
					p1 = p
			else:
				p1 = p - 1
			c = obfuscationkey[p1].upper() if upper else obfuscationkey[p1]
		r = r + c
	return r
	
def decode_text (text):
	"""Decodes a string from HTML."""
	output = text
	output = output.replace('\\n', '\n')
	output = output.replace('\\t', '\t')
	output = output.replace('\s', '\\')
	output = output.replace('&lt;', '<')
	output = output.replace('&gt;', '>')
	output = output.replace('&quot;', '"')
	return output
	
	
def encode_date (date):
	"""Encodes a datetime in TiddlyWiki format."""
	return time.strftime('%Y%m%d%H%M', date)
	

def decode_date (date):
	"""Decodes a datetime from TiddlyWiki format."""
	return time.strptime(date, '%Y%m%d%H%M')
