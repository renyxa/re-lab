# Copyright (C) 2013 David Tardon (dtardon@redhat.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 or later of the GNU General Public
# License as published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA
#

# reverse-engineered specification: http://doc.the-ebook.org/LrfFormat
# (2013)

import struct
import zlib

from utils import add_iter, add_pgiter, rdata

lrf_object_types = {
	0x1: 'Page Tree',
	0x2: 'Page',
	0x3: 'Header',
	0x4: 'Footer',
	0x5: 'Page Atr',
	0x6: 'Block',
	0x7: 'Block Atr',
	0x8: 'Mini Page',
	0x9: 'Block List',
	0xa: 'Text',
	0xb: 'Text Atr',
	0xc: 'Image',
	0xd: 'Canvas',
	0xe: 'Paragraph Atr',
	0x11: 'Image Stream',
	0x12: 'Import',
	0x13: 'Button',
	0x14: 'Window',
	0x15: 'Pop Up Win',
	0x16: 'Sound',
	0x17: 'Plane Stream',
	0x19: 'Font',
	0x1a: 'Object Info',
	0x1c: 'Book Atr',
	0x1d: 'Simple Text',
	0x1e: 'Toc',
}

lrf_thumbnail_types = {
	0x11: "JPEG",
	0x12: "PNG",
	0x13: "BMP",
	0x14: "GIF",
}

# variable length
V = None

lrf_tags = {
	0xf500 : ('Object Start', 6),
	0xf501 : ('Object End', 0),
	0xf502 : ('Object Info Link', 4),
	0xf503 : ('Link', 4),
	0xf504 : ('Stream Size', 4),
	0xf505 : ('Stream Start', 0),
	0xf506 : ('Stream End', 0),
	0xf507 : ('Contained Objects List', 4),
	0xf508 : ('F508', 4),
	0xf509 : ('F509', 4),
	0xf50a : ('F50A', 4),
	0xf50b : ('F50B', V),
	0xf50d : ('F50D', V),
	0xf50e : ('F50E', 2),
	0xf511 : ('Font Size', 2),
	0xf512 : ('Font Width', 2),
	0xf513 : ('Font Escapement', 2),
	0xf514 : ('Font Orientation', 2),
	0xf515 : ('Font Weight', 2),
	0xf516 : ('Font Facename', V),
	0xf517 : ('Text Color', 4),
	0xf518 : ('Text Bg Color', 4),
	0xf519 : ('Word Space', 2),
	0xf51a : ('Letter Space', 2),
	0xf51b : ('Base Line Skip', 2),
	0xf51c : ('Line Space', 2),
	0xf51d : ('Par Indent', 2),
	0xf51e : ('Par Skip', 2),
	0xf521 : ('F521', 2),
	0xf522 : ('F522', 2),
	0xf523 : ('F523', 2),
	0xf524 : ('F524', 2),
	0xf525 : ('Page Height', 2),
	0xf526 : ('Page Width', 2),
	0xf527 : ('F527', 2),
	0xf528 : ('F528', 2),
	0xf529 : ('F529', 6),
	0xf52a : ('F52A', 2),
	0xf52b : ('F52B', 2),
	0xf52c : ('F52C', 2),
	0xf52d : ('F52D', 4),
	0xf52e : ('F52E', 2),
	0xf531 : ('Block Width', 2),
	0xf532 : ('Block Height', 2),
	0xf533 : ('Block Rule', 2),
	0xf534 : ('F534', 4),
	0xf535 : ('F535', 2),
	0xf536 : ('F536', 2),
	0xf537 : ('F537', 4),
	0xf538 : ('F538', 2),
	0xf539 : ('F539', 2),
	0xf53a : ('F53A', 2),
	0xf53c : ('F53C', 2),
	0xf53d : ('F53D', 2),
	0xf53e : ('F53E', 2),
	0xf541 : ('Mini Page Height', 2),
	0xf542 : ('Mini Page Width', 2),
	0xf544 : ('F544', 4),
	0xf545 : ('F545', 4),
	0xf546 : ('Location Y', 2),
	0xf547 : ('Location X', 2),
	0xf548 : ('F548', 2),
	0xf549 : ('Put Sound', 8),
	0xf54a : ('Image Rect', 8),
	0xf54b : ('Image Size', 4),
	0xf54c : ('Image Stream', 4),
	0xf54d : ('F54D', 0),
	0xf54e : ('F54E', 12),
	0xf551 : ('Canvas Width', 2),
	0xf552 : ('Canvas Height', 2),
	0xf553 : ('F553', 4),
	0xf554 : ('Stream Flags', 2),
	0xf555 : ('F555', V),
	0xf556 : ('F556', V),
	0xf557 : ('F557', 2),
	0xf558 : ('F558', 2),
	0xf559 : ('Font File Name', V),
	0xf55a : ('F55A', V),
	0xf55b : ('View Point', 4),
	0xf55c : ('Page List', V),
	0xf55d : ('Font Face Name', V),
	0xf55e : ('F55E', 2),
	0xf561 : ('F561', 2),
	0xf562 : ('F562', 0),
	0xf563 : ('F563', 0),
	0xf564 : ('F564', 0),
	0xf565 : ('F565', 0),
	0xf566 : ('F566', 0),
	0xf565 : ('F565', 0),
	0xf566 : ('F566', 0),
	0xf567 : ('F567', 0),
	0xf568 : ('F568', 0),
	0xf569 : ('F569', 0),
	0xf56a : ('F56A', 0),
	0xf56b : ('F56B', 0),
	0xf56c : ('Jump To', 8),
	0xf56d : ('F56D', V),
	0xf56e : ('F56E', 0),
	0xf571 : ('F571', 0),
	0xf572 : ('F572', 0),
	0xf573 : ('Ruled Line', 10),
	0xf575 : ('Ruby Align', 2),
	0xf576 : ('Ruby Overhang', 2),
	0xf577 : ('Empty Dots Position', 2),
	0xf578 : ('Empty Dots Code', V),
	0xf579 : ('Empty Line Position', 2),
	0xf57a : ('Empty Line Mode', 2),
	0xf57b : ('Child Page Tree', 4),
	0xf57c : ('Parent Page Tree', 4),
	0xf581 : ('Begin Italic', 0),
	0xf582 : ('End Italic', 0),
	0xf5a1 : ('Begin P', 4),
	0xf5a2 : ('End P', 0),
	0xf5a5 : ('Koma Gaiji', V),
	0xf5a6 : ('Koma Emp Dot Char', 0),
	0xf5a7 : ('Begin Button', 4),
	0xf5a8 : ('End Button', 0),
	0xf5a9 : ('Begin Ruby', 0),
	0xf5aa : ('End Ruby', 0),
	0xf5ab : ('Begin Ruby Base', 0),
	0xf5ac : ('End Ruby Base', 0),
	0xf5ad : ('Begin Ruby Text', 0),
	0xf5ae : ('End Ruby Text', 0),
	0xf5b1 : ('Koma Yokomoji', 0),
	0xf5b2 : ('F5B2', 0),
	0xf5b3 : ('Begin Tate', 0),
	0xf5b4 : ('End Tate', 0),
	0xf5b5 : ('Begin Nekase', 0),
	0xf5b6 : ('End Nekase', 0),
	0xf5b7 : ('Begin Sup', 0),
	0xf5b8 : ('End Sup', 0),
	0xf5b9 : ('Begin Sub', 0),
	0xf5ba : ('End Sub', 0),
	0xf5bb : ('F5BB', 0),
	0xf5bc : ('F5BC', 0),
	0xf5bd : ('F5BD', 0),
	0xf5be : ('F5BE', 0),
	0xf5c1 : ('Begin Emp Line', 0),
	0xf5c2 : ('F5C2', 0),
	0xf5c3 : ('Begin Draw Char', 2),
	0xf5c4 : ('End Draw Char', 0),
	0xf5c5 : ('F5C5', 2),
	0xf5c6 : ('F5C6', 2),
	0xf5c7 : ('F5C7', 0),
	0xf5c8 : ('Koma Auto Spacing', 2),
	0xf5c9 : ('F5C9', 0),
	0xf5ca : ('Space', 2),
	0xf5cb : ('F5CB', V),
	0xf5cc : ('Text Size', 2),
	0xf5d1 : ('Koma Plot', V),
	0xf5d2 : ('EOL', 0),
	0xf5d4 : ('Wait', 2),
	0xf5d6 : ('Sound Stop', 0),
	0xf5d7 : ('Move Obj', 14),
	0xf5d8 : ('Book Font', 4),
	0xf5d9 : ('Koma Plot Text', 8),
	0xf5da : ('F5DA', 2),
	0xf5db : ('F5DB', 2),
	0xf5dc : ('F5DC', 2),
	0xf5dd : ('Char Space', 2),
	0xf5f1 : ('Line Width', 2),
	0xf5f2 : ('Line Color', 4),
	0xf5f3 : ('Fill Color', 4),
	0xf5f4 : ('Line Mode', 2),
	0xf5f5 : ('Move To', 4),
	0xf5f6 : ('Line To', 4),
	0xf5f7 : ('Draw Box', 4),
	0xf5f8 : ('Draw Ellipse', 4),
	0xf5f9 : ('F5F9', 6),
}

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class lrf_parser(object):

	class stream_state:

		def __init__(self):
			self.stream_flags = 0
			self.stream_size = 0
			self.stream_started = False
			self.stream_read = False

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.pseudo_encryption_key = 0
		self.version = 0
		self.header_size = 0
		self.root_oid = 0
		self.object_count = 0
		self.object_index_offset = 0
		self.toc_oid = None
		self.toc_offset = 0
		self.metadata_size = 0
		self.thumbnail_type = None
		self.thumbnail_size = 0

		self.stream_level = 1
		self.stream_states = []
		self.object_type = None

	def open_stream_level(self):
		if (self.stream_level > len(self.stream_states)):
			self.stream_states.append(self.stream_state())
		assert(self.stream_level == len(self.stream_states))

	def close_stream_level(self):
		self.stream_states.pop(-1)
		assert(len(self.stream_states) >= 0)
		assert(self.stream_level > 0)

	def is_in_stream(self):
		if len(self.stream_states) == self.stream_level:
			return self.stream_states[-1].stream_started and not self.stream_states[-1].stream_read
		return False

	def read_header(self):
		data = self.data

		self.version = read(data, 8, '<H')
		self.pseudo_encryption_key = read(data, 0xa, '<H')
		self.object_count = read(data, 0x10, '<Q')
		self.object_index_offset = read(data, 0x18, '<Q')
		(self.toc_oid, off) = rdata(data, 0x44, '<I')
		(self.toc_offset, off) = rdata(data, off, '<I')
		(self.metadata_size, off) = rdata(data, off, '<H')
		if (self.version > 800):
			(self.thumbnail_type, off) = rdata(data, off, '<H')
			(self.thumbnail_size, off) = rdata(data, off, '<I')

		self.header_size = off

		add_pgiter(self.page, 'Header', 'lrf', 'header', data[0:off], self.parent)

	def read_toc(self):
		data = self.data
		off = self.toc_offset
		(oid, off) = rdata(data, off, '<I')
		assert(oid == self.toc_oid)
		(start, off) = rdata(data, off, '<I')
		(length, off) = rdata(data, off, '<I')
		end = start + length
		add_pgiter(self.page, 'TOC', 'lrf', 0, data[start:end], self.parent)

	def read_metadata(self):
		start = self.header_size
		end = start + self.metadata_size
		metaiter = add_pgiter(self.page, 'Metadata', 'lrf', 0, self.data[start:end], self.parent)
		# There are 4 bytes at the beginning that might be uncompressed size.
		# TODO: check
		try:
			content = zlib.decompress(self.data[start + 4:end])
		except zlib.error:
			content = self.data
		add_pgiter(self.page, 'Uncompressed content', 'lrf', 'text', content, metaiter)

	def read_thumbnail(self):
		start = self.header_size + self.metadata_size
		end = start + self.thumbnail_size
		typ = "Unknown"
		if lrf_thumbnail_types.has_key(self.thumbnail_type):
			typ = lrf_thumbnail_types[self.thumbnail_type]
		add_pgiter(self.page, 'Thumbnail (%s)' % typ, 'lrf', 0, self.data[start:end], self.parent)

	def decrypt_stream(self, data):
		declen = len(data)
		keybyte = ((declen % self.pseudo_encryption_key) + 0x0f) & 0xff
		if self.object_type == 0x11 or self.object_type == 0x17 or self.object_type == 0x19:
			if declen > 0x400:
				declen = 0x400
		decdata = map(lambda c : chr((ord(c) ^ keybyte) & 0xff), data[0:declen])
		decdata.append(data[declen:len(data)])
		return ''.join(decdata)

	def read_stream(self, data, parent):
		strmiter = add_pgiter(self.page, 'Stream', 'lrf', 0, data, parent)
		# data = self.decrypt_stream(self.data[start:start + length])
		# add_pgiter(self.page, '[Unobfuscated]', 'lrf', 0, data, strmiter)

		# This is what I see for text streams anyway. But it is probably
		# recorded in the stream's flags.
		# TODO: check stream flags
		content = data
		content_name = 'Content'
		if len(data) > 64:
			# there are 4 bytes of something that looks like uncompressed size
			# at the beginning
			try:
				content = zlib.decompress(data[4:])
				content_name = 'Uncompressed content'
			except zlib.error:
				pass
		cntiter = add_pgiter(self.page, content_name, 'lrf', 0, content, strmiter)
		self.stream_level += 1
		# There are streams that do not contain tags. Maybe only text
		# streams contain tags.
		if len(content) > 1 and ord(content[1]) == 0xf5:
			self.read_object_tags(content, cntiter)
		self.stream_level -= 1
		self.stream_states[-1].stream_read = True

	def read_object_tag(self, n, data, start, parent):
		end = len(data)
		if self.is_in_stream():
			stream_end = start + self.stream_states[-1].stream_size
			self.read_stream(data[start:stream_end], parent)
			return stream_end

		callback = 0
		(tag, off) = rdata(data, start, '<H')
		name = 'Tag %x' % tag
		length = None
		if ((tag & 0xff00) >> 8) == 0xf5:
			if lrf_tags.has_key(tag):
				(name, length) = lrf_tags[tag]
		else:
			callback = 'text'
			name = 'Data'

		# try to find the next tag
		if length is None:
			pos = off
			while data[pos] != chr(0xf5) and pos < end:
				pos += 1
			if pos < end:
				pos -= 1
			elif pos <= off:
				return end
			else: # not found
				return end
			length = pos - off

		if tag == 0xf504:
			self.open_stream_level()
			self.stream_states[-1].stream_size = read(data, off, '<I')
		elif tag == 0xf505:
			self.open_stream_level()
			self.stream_states[-1].stream_started = True
		elif tag == 0xf554:
			self.open_stream_level()
			self.stream_states[-1].stream_flags = read(data, off, '<H')
		elif tag == 0xf506:
			self.close_stream_level()

		if off + length <= end:
			add_pgiter(self.page, '%s (%d)' % (name, n), 'lrf', callback, data[start:off + length], parent)
		else:
			return end

		return off + length

	def read_object_tags(self, data, parent):
		n = 0
		pos = self.read_object_tag(n, data, 0, parent)
		while pos < len(data):
			n += 1
			pos = self.read_object_tag(n, data, pos, parent)

	def read_object(self, idxoff, parent):
		data = self.data
		(oid, off) = rdata(data, idxoff, '<I')
		(start, off) = rdata(data, off, '<I')
		(length, off) = rdata(data, off, '<I')
		otp = read(data, start + 6, '<H')

		otype = otp
		if lrf_object_types.has_key(otp):
			otype = lrf_object_types[otp]

		objiter = add_pgiter(self.page, 'Object %x (%s)' % (oid, otype), 'lrf', 0, data[start:start + length], parent)
		self.object_type = otype
		self.read_object_tags(data[start:start + length], objiter)
		self.object_type = None

	def read_objects(self):
		data = self.data

		idxstart = self.object_index_offset
		idxend = idxstart + self.object_count * 16

		objstart = read(data, idxstart + 4, '<I')
		last_obj = idxend - 16
		(last_obj_offset, offset) = rdata(data, last_obj + 4, '<I')
		last_obj_len = read(data, offset, '<I')
		objend = last_obj_offset + last_obj_len

		objiter = add_pgiter(self.page, 'Objects', 'lrf', 0, data[objstart:objend], self.parent)
		idxiter = add_pgiter(self.page, 'Object index', 'lrf', 0, data[idxstart:idxend], self.parent)
		for i in range(self.object_count):
			off = idxstart + 16 * i
			oid = read(data, off, '<I')
			add_pgiter(self.page, 'Entry %x' % (oid), 'lrf', 'idxentry', data[off:off + 16], idxiter)
			self.read_object(off, objiter)

	def read(self):
		parent = self.parent
		self.parent = add_pgiter(self.page, 'File', 'lrf', 0, self.data, parent)
		self.read_header()
		self.read_metadata()
		if (self.version > 800):
			self.read_thumbnail()
		# self.read_toc()
		self.read_objects()

def add_header(hd, size, data):
	add_iter(hd, 'Version', read(data, 8, '<H'), 8, 2, '<H')
	add_iter(hd, 'Pseudo Enc. Key', read(data, 0xa, '<H'), 0xa, 2, '<H')
	add_iter(hd, 'Number of objects', read(data, 0x10, '<Q'), 0x10, 8, '<Q')

def add_index_entry(hd, size, data):
	add_iter(hd, 'Offset', read(data, 4, '<I'), 4, 4, '<I')
	add_iter(hd, 'Length', read(data, 8, '<I'), 8, 4, '<I')

def add_text(hd, size, data):
	text = u''
	off = 0
	while off < size:
		(c, off) = rdata(data, off, '<H')
		text += unichr(c)
	add_iter(hd, 'Text', text, 0, size, 's')

lrf_ids = {
	'header': add_header,
	'idxentry': add_index_entry,
	'text': add_text,
}

def open(buf, page, parent):
	reader = lrf_parser(buf, page, parent)
	reader.read()

# vim: set ft=python ts=4 sw=4 noet:
