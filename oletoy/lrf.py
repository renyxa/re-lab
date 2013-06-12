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

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class lrf_parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.version = 0
		self.root_oid = 0
		self.object_count = 0
		self.object_index_offset = 0
		self.plane_stream_oid = 0
		self.gif_size = 0

	def read_header(self):
		data = self.data

		self.version = read(data, 8, '<H')
		self.object_count = read(data, 0x10, '<Q')
		self.object_index_offset = read(data, 0x18, '<Q')
		self.plane_stream_oid = read(data, 0x44, '<I')
		if (self.version > 800):
			self.gif_size = read(data, 0x50, '<I')
			header_size = 0x4e
		else:
			header_size = 0x54

		add_pgiter(self.page, 'Header', 'lrf', 'header', data[0:header_size], self.parent)

	def read_gif(self):
		# add_pgiter(self.page, 'GIF image', 'lrf', 0, self.strm.buf[self.strm.off:self.gif_size], self.parent)
		pass

	def read_object(self, idxoff, parent):
		data = self.data
		(oid, off) = rdata(data, idxoff, '<I')
		(start, off) = rdata(data, off, '<I')
		(end, off) = rdata(data, off, '<I')
		add_pgiter(self.page, 'Object %s' % oid, 'lrf', 0, data[start:start + end], parent)

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
			add_pgiter(self.page, 'Entry %s' % (oid), 'lrf', 'idxentry', data[off:off + 16], idxiter)
			self.read_object(off, objiter)

	def read(self):
		parent = self.parent
		self.parent = add_pgiter(self.page, 'File', 'lrf', 0, self.data, parent)
		self.read_header()
		if (self.version > 800):
			self.read_gif()
		self.read_objects()

def add_header(hd, size, data):
	add_iter(hd, 'Version', read(data, 8, '<H'), 8, 2, '<H')
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
