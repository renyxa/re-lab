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

import struct

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
	0xf50A : ('F50A', 4),
	0xf50B : ('F50B', V),
	0xf50D : ('F50D', V),
	0xf50E : ('F50D', 2),
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
	# missing
	0xf525 : ('Page Height', 2),
	0xf526 : ('Page Width', 2),
	# missing
	0xf531 : ('Block Width', 2),
	0xf532 : ('Block Height', 2),
	0xf533 : ('Block Rule', 2),
	# missing
	0xf541 : ('Mini Page Height', 2),
	0xf542 : ('Mini Page Width', 2),
	# missing
	0xf546 : ('Location Y', 2),
	0xf547 : ('Location X', 2),
	0xf548 : ('F548', 2),
	0xf549 : ('Put Sound', 8),
	0xf54a : ('Image Rect', 8),
	0xf54b : ('Image Size', 4),
	0xf54c : ('Image Stream', 4),
	# missing
	0xf551 : ('Canvas Width', 2),
	0xf552 : ('Canvas Height', 2),
	0xf553 : ('F553', 4),
	0xf554 : ('Stream Flags', 2),
	# missing
	0xf559 : ('Font File Name', V),
	0xf55a : ('F55A', V),
	0xf55b : ('View Point', 4),
	0xf55c : ('Page List', V),
	0xf55d : ('Font Face Name', V),
	# missing
	0xf56c : ('Jump To', 8),
	# missing
	0xf573 : ('Ruled Line', 10),
	0xf575 : ('Ruby Align', 2),
	0xf576 : ('Ruby Overhang', 2),
	0xf577 : ('Empty Dots Position', 2),
	0xf578 : ('Empty Dots Code', V),
	0xf579 : ('Empty Line Position', 2),
	0xf57a : ('Empty Line Mode', 2),
	0xf57b : ('Child Page Tree', 4),
	0xf57c : ('Parent Page Tree', 4),
	0xf581 : ('Italic', 0),
	0xf582 : ('Italic', 0),
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
	# missing
	0xf5b3 : ('Tate', 0),
	0xf5b4 : ('Tate', 0),
	0xf5b5 : ('Nekase', 0),
	0xf5b6 : ('Nekase', 0),
	0xf5b7 : ('Begin Sup', 0),
	0xf5b8 : ('End Sup', 0),
	0xf5b9 : ('Begin Sub', 0),
	0xf5ba : ('End Sub', 0),
	# missing
	0xf5c1 : ('Begin Emp Line', 0),
	0xf5c2 : ('F5C2', 0),
	0xf5c3 : ('Begin Draw Char', 2),
	0xf5c4 : ('End Draw Char', 0),
	# missing
	0xf5c8 : ('Koma Auto Spacing', 2),
	# missing
	0xf5ca : ('Space', 2),
	# missing
	0xf5d1 : ('Koma Plot', V),
	0xf5d2 : ('EOL', 0),
	0xf5d4 : ('Wait', 2),
	0xf5d6 : ('Sound Stop', 0),
	0xf5d7 : ('Move Obj', 14),
	0xf5d8 : ('Book Font', 4),
	0xf5d9 : ('Koma Plot Text', 8),
	# missing
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

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.key = 0
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

		self.stream_size = 0
		self.stream_started = False
		self.stream_read = False

	def read_header(self):
		data = self.data

		self.version = read(data, 8, '<H')
		self.key = read(data, 0xa, '<H')
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
		add_pgiter(self.page, 'Metadata', 'lrf', 0, self.data[start:end], self.parent)

	def get_thumbnail_type(self, typ):
		if typ == 0x11:
			return "JPEG"
		elif typ == 0x12:
			return "PNG"
		elif typ == 0x13:
			return "BMP"
		elif typ == 0x14:
			return "GIF"
		return "unknown"

	def read_thumbnail(self):
		start = self.header_size + self.metadata_size
		end = start + self.thumbnail_size
		typ = self.get_thumbnail_type(self.thumbnail_type)
		add_pgiter(self.page, 'Thumbnail (%s)' % typ, 'lrf', 0, self.data[start:end], self.parent)

	def read_stream(self, start, length, parent):
		add_pgiter(self.page, 'Stream', 'lrf', 0, self.data[start:start + length], parent)
		self.stream_read = True

	def read_object_tag(self, n, start, end, parent):
		if self.stream_started and not self.stream_read:
			self.read_stream(start, self.stream_size, parent)
			return start + self.stream_size

		(tag, off) = rdata(self.data, start, '<H')
		name = 'Tag %x' % tag
		length = None
		if lrf_tags.has_key(tag):
			(name, length) = lrf_tags[tag]

		# try to find the next tag
		if length is None:
			pos = off
			while self.data[pos] != chr(0xf5) and pos < end:
				pos += 1
			if pos < end:
				pos -= 1
			elif pos <= off:
				return end
			else: # not found
				return end
			length = pos - off

		if tag == 0xf504:
			self.stream_size = read(self.data, off, '<I')
			print('stream size = %s' % self.stream_size)
		elif tag == 0xf505:
			self.stream_started = True
		elif tag == 0xf506:
			self.stream_started = False
			self.stream_read = False

		if start + length <= end:
			add_pgiter(self.page, '%s (%d)' % (name, n), 'lrf', 0, self.data[start:off + length], parent)
		else:
			return end

		return off + length

	def read_object_tags(self, start, end, parent):
		n = 0
		pos = self.read_object_tag(n, start, end, parent)
		while pos < end:
			n += 1
			pos = self.read_object_tag(n, pos, end, parent)

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
		self.read_object_tags(start, start + length, objiter)

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

lrf_ids = {
	'header': add_header,
	'idxentry': add_index_entry
}

def open(buf, page, parent):
	reader = lrf_parser(buf, page, parent)
	reader.read()

# vim: set ft=python ts=4 sw=4 noet:
