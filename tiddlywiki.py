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

import re, datetime, time, os, sys, tempfile, codecs

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
		
	def toHtml (self, app, target = None, order = None):
		"""Returns HTML code for this TiddlyWiki. If target is passed, adds a header."""
		if not order: order = self.tiddlers.keys()
		output = u''
		
		if (target):
			try:
				header = open(app.getPath() + os.sep + 'targets' + os.sep + target + os.sep + 'header.html')
				output = header.read()
				header.close()
			except IOError:
				app.displayError("building: the story format '" + target + "' isn't available.\n"
					+ "Please select another format from the Story Format submenu.\n\n")
			
			# Insert the main engine
			if output.count('"ENGINE"') > 0:
				try:
					engine = open(app.getPath() + os.sep + 'targets' + os.sep + 'engine.js')
					enginecode = engine.read()
					engine.close()
					output = output.replace('"ENGINE"',enginecode)
				except IOError:
					app.displayError("building: the file 'engine.js' used by the story format '" + target + "' wasn't found.\n\n")
		
		if self.storysettings.has_key('Obfuscate') and \
		self.storysettings['Obfuscate'] == 'SWAP' and self.storysettings.has_key('ObfuscateKey') :
			nss = u''
			for nsc in self.storysettings['ObfuscateKey']:
				if nss.find(nsc) == -1 and not nsc in ':\\\"n0':
					nss = nss + nsc
			self.storysettings['ObfuscateKey'] = nss
		
		for i in order:
			if not any('Twine.private' in t for t in self.tiddlers[i].tags) and \
			not any('Twine.system' in t for t in self.tiddlers[i].tags):
				if (not (self.storysettings.has_key('Obfuscate') and \
						self.storysettings['Obfuscate'] == 'SWAP' and \
						self.storysettings.has_key('ObfuscateKey'))) or \
					self.tiddlers[i].title == 'StorySettings':
					output += self.tiddlers[i].toHtml(self.author)
				else:
					output += self.tiddlers[i].toHtml(self.author, obfuscation = True, obfuscationkey = self.storysettings['ObfuscateKey'])
		
		if (target):
			footername = app.getPath() + os.sep + 'targets' + os.sep + target + os.sep + 'footer.html'
			if os.path.exists(footername):
				footer = open(footername,'r')
				output += footer.read()
				footer.close()
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
		output += r'{\fonttbl\f0\fswiss\fcharset0 Arial;}' + '\n'
		output += r'{\colortbl;\red128\green128\blue128;}' + '\n'
		output += r'\margl1440\margr1440\vieww9000\viewh8400\viewkind0' + '\n'
		output += r'\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx792' + '\n'
		output += r'\tx8640\ql\qnatural\pardirnatural\pgnx720\pgny720' + '\n'
		
		# content
		
		for i in order:
			text = rtf_encode(self.tiddlers[i].text)
			text = re.sub(r'\n', '\\\n', text) # newlines
			text = re.sub(r'\[\[(.*?)\]\]', r'\ul \1\ulnone ', text) # links
			text = re.sub(r'\/\/(.*?)\/\/', r'\i \1\i0 ', text) # italics
			text = re.sub(r'(\<\<.*?\>\>)', r'\cf1 \i \1\i0 \cf0', text) # macros

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
		divs_re = re.compile(r'<div id="storeArea">(.*)</div>',
												 re.DOTALL)
		divs = divs_re.search(source)
		if divs:
			for div in divs.group(1).split('<div'):
				self.addTiddler(Tiddler('<div' + div, 'html'))
				
	def addHtmlFromFilename(self, filename):
		self.addTweeFromFilename(filename, True)
		
	def addTweeFromFilename(self, filename, html = False):
		try:
			source = codecs.open(filename, 'r', 'utf-8-sig', 'strict')
			w = source.read()
		except UnicodeDecodeError:
			try:
				source = codecs.open(filename, 'r', 'utf16', 'strict')
				w = source.read()
			except:
				source = open(filename, 'rb')
				w = source.read()
		source.close()
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
	
	INFO_PASSAGES = ['StoryMenu', 'StoryTitle', 'StoryAuthor', 'StorySubtitle', 'StoryIncludes', 'StorySettings', 'StartPassages']
		
#
# Tiddler class
#

class Tiddler:
	"""A single tiddler in a TiddlyWiki."""
	
	def __init__ (self, source, type = 'twee'):
		# cache of passage names linked from this one
		self.links = []
		self.displays = []
		
		"""Pass source code, and optionally 'twee' or 'html'"""
		if type == 'twee':
			self.initTwee(source)
		else:
			self.initHtml(source)

	def __repr__ (self):
		return "<Tiddler '" + self.title + "'>"

	def __cmp__ (self, other):
		"""Compares a Tiddler to another."""
		return self.text == other.text
	
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
		
		
	def initHtml (self, source):
		"""Initializes a Tiddler from HTML source code."""
		
		# title
		
		self.title = 'untitled passage'
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
		text_re = re.compile(r'<div.*?>(.*)</div>')
		text = text_re.search(source)
		if (text):
			self.text = decode_text(text.group(1))
				
		
	def toHtml (self, author = 'twee', obfuscation = False, obfuscationkey = ''):
		"""Returns an HTML representation of this tiddler."""
			
		now = time.localtime()
		output = ''
		if not obfuscation:
			output = '<div tiddler="' + self.title + '" tags="'
			for tag in self.tags:
				output += tag + ' '
			output = output.strip()
		else:
			output = '<div tiddler="' + encode_obfuscate_swap(self.title, obfuscationkey) + '" tags="'
			for tag in self.tags:
				output += encode_obfuscate_swap(tag + ' ', obfuscationkey)
			output = output.strip()

		output += '" modified="' + encode_date(self.modified) + '"'
		output += ' created="' + encode_date(self.created) + '"' 
		output += ' twine-position="' + str(int(self.pos[0])) + ',' + str(int(self.pos[1])) + '"'
		output += ' modifier="' + author + '">'
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
	
	def isStoryText(self):
		return not (('script' in self.tags) or ('stylesheet' in self.tags) \
			or (self.title in TiddlyWiki.INFO_PASSAGES))

	def linksAndDisplays(self):
		return list(set(self.links+self.displays))
	
	def update(self, includeInternal = True, includeMacros = True):
		"""
		Update the lists of all passages linked/displayed by this one. By default,
		returns internal links and <<choice>>/<<actions>> macros.
		"""
		if not self.isStoryText():
			self.displays = []
			self.links = []
			return
		
		# <<display>>
		self.displays = re.findall(r'\<\<display\s+[\'"]?(.+?)[\'"]?\s?\>\>', self.text, re.IGNORECASE)
		
		links = []
		actions = []
		choices = []
		
		# regular hyperlinks
		if includeInternal:
			links = re.findall(r'\[\[(.+?)\]\]', self.text)
		
			# check for [[title|target]] formats
	
			def filterPrettyLinks (text):
				if '|' in text: return re.sub('.*\|', '', text)
				else: return text
			
			links = map(filterPrettyLinks, links)
			
			# Remove externals
			def filterExternals (text):
				for t in ['http://', 'https://', 'ftp://']:
					if text.lower().startswith(t): return False
				return True
				
			links = filter(filterExternals, links)

		if includeMacros:
			
			# <<choice ''>>
			
			choices = re.findall(r'\<\<choice\s+[\'"]?(.+?)[\'"]?\s?\>\>', self.text, re.IGNORECASE)

			# <<actions ''>>
			
			actions = []
			actionBlocks = re.findall(r'\<\<actions\s+(.*?)\s?\>\>', self.text, re.IGNORECASE)
			for block in actionBlocks:
				actions = actions + re.findall(r'[\'"](.*?)[\'"]', block)
		
		# remove duplicates by converting to a set
		
		self.links = list(set(links + choices + actions))

#
# Helper functions
#


def encode_text (text, obfuscation, obfuscationkey):
	"""Encodes a string for use in HTML output."""
	output = text
	if obfuscation: output = encode_obfuscate_swap(output, obfuscationkey)
	output = output.replace('\\', '\s')
	output = re.sub(r'\r?\n', r'\\n', output)
	output = output.replace('<', '&lt;')
	output = output.replace('>', '&gt;')
	output = output.replace('"', '&quot;')
	return output

def encode_obfuscate_swap(text, obfuscationkey):
	"""Does basic character pair swapping obfuscation""" 
	r = ''
	for c in text:
		p = obfuscationkey.find(c)
		if p <> -1:
			if p % 2 == 0:
				p1 = p + 1
				if p1 >= len(obfuscationkey): 
					p1 = p
			else:
				p1 = p - 1
			c = obfuscationkey[p1]
		r = r + c
	return r
	
def decode_text (text):
	"""Decodes a string from HTML."""
	output = text
	output = output.replace('\\n', '\n')
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