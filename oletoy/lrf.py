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

	def read_object(self, idxoff, parent):
		data = self.data
		(oid, off) = rdata(data, idxoff, '<I')
		(start, off) = rdata(data, off, '<I')
		(end, off) = rdata(data, off, '<I')
		otp = read(data, start + 6, '<H')

		otype = otp
		if lrf_object_types.has_key(otp):
			otype = lrf_object_types[otp]

		add_pgiter(self.page, 'Object %x (%s)' % (oid, otype), 'lrf', 0, data[start:start + end], parent)

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
