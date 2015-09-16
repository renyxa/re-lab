# Copyright (C) 2015 David Tardon (dtardon@redhat.com)
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

import datetime
import struct

from utils import add_iter, add_pgiter, rdata

EPOCH_BEGIN = 978307200

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

class format_error:
	def __init__(self, desc, off):
		self.desc = desc
		self.offset = off

	def what(self):
		return "%s at offset %x" % (self.desc, self.offset)

prop_parsers = None # defined later

def query_parser(data, off):
	(c, off) = rdata(data, off, '>B')
	marker = (c & 0xf0) >> 4
	arg = c & 0xf
	if not prop_parsers.has_key(marker):
		raise format_error('unknown marker arg %x' % marker, off - 1)
	return prop_parsers[marker](data, off, arg)

class record:
	def __init__(self, data, off, arg):
		assert off > 0
		assert arg <= 0xf
		self.data = data
		self.start = off
		self.arg = arg
		self.end = 0
		self.value = None
		self.something_fmt = '>B'

	def parse(self, something_fmt='>B'):
		self.something_fmt = something_fmt
		try:
			self.end = self.do_parse(self.data, self.start, self.arg)
		except format_error, e:
			self.end = e.offset
			raise e
		return self.end

	def show(self, page, parent):
		assert self.end >= self.start
		self.do_show(page, self.data, parent)

	def add_pgiter(self, page, name, callback, data, parent):
		return add_pgiter(page, name, 'plist', callback, data[self.start - 1:self.end], parent)

	def show_values(self, page, name, data, parent, values):
		if not len(values) == 0:
			values_data = data[values[0].start:values[-1].end]
			iter = add_pgiter(page, name, 'plist', '', values_data, parent)
			for v in values:
				v.show(page, iter)

class boolean(record):
	def do_parse(self, data, off, arg):
		self.value = arg
		return off

	def do_show(self, page, data, parent):
		const_map = {8: 'False', 9: 'True'}
		const = get_or_default(const_map, self.value, 'Unknown')
		self.add_pgiter(page, 'Boolean: %s' % const, '', data, parent)

class integer(record):
	def do_parse(self, data, off, width):
		width_map = {0: 'b', 1: 'h', 2: 'i', 3: 'q'}
		if not width_map.has_key(width):
			raise format_error('unknown integer width %x' % width, off - 1)
		(self.value, off) = rdata(data, off, '>%s' % width_map[width])
		return off

	def do_show(self, page, data, parent):
		self.add_pgiter(page, 'Integer: %d' % self.value, '', data, parent)

class real(record):
	def do_parse(self, data, off, width):
		width_map = {2: 'f', 3: 'd'}
		if not width_map.has_key(width):
			raise format_error('unknown real width %x' % width, off - 1)
		(self.value, off) = rdata(data, off, '>%s' % width_map[width])
		return off

	def do_show(self, page, data, parent):
		self.add_pgiter(page, 'Real: %f' % self.value, '', data, parent)

class date(record):
	def do_parse(self, data, off, width):
		width_map = {3: 'd'}
		if not width_map.has_key(width):
			raise format_error('unknown date width %x' % width, off - 1)
		(self.value, off) = rdata(data, off, '>%s' % width_map[width])
		return off

	def do_show(self, page, data, parent):
		date = datetime.datetime.fromtimestamp(EPOCH_BEGIN + self.value)
		self.add_pgiter(page, 'Date: %s' % date.isoformat(), '', data, parent)

def read_int(data, off):
	(c, off) = rdata(data, off, '>B')
	marker = (c & 0xf0) >> 4
	arg = c & 0xf
	assert marker == 1
	parser = integer(data, off, arg)
	off = parser.parse()
	return (parser.value, off)

class data(record):
	def do_parse(self, data, off, length):
		if length == 0xf:
			(length, off) = read_int(data, off)
		(self.value, off) = rdata(data, off, '%ds' % length)
		return off

	def do_show(self, page, data, parent):
		self.add_pgiter(page, 'Data', 'string', data, parent)

class string(record):
	def do_parse(self, data, off, length):
		if length == 0xf:
			(length, off) = read_int(data, off)
		(self.value, off) = rdata(data, off, '%ds' % length)
		return off

	def do_show(self, page, data, parent):
		self.add_pgiter(page, 'String', 'string', data, parent)

class utf16(record):
	def do_parse(self, data, off, length):
		if length == 0xf:
			(length, off) = read_int(data, off)
		(self.value, off) = rdata(data, off, '%ds' % (2 * length))
		return off

	def do_show(self, page, data, parent):
		self.add_pgiter(page, 'UTF-16 string', 'utf16', data, parent)

class array(record):
	def __init__(self, data, off, arg):
		record.__init__(self, data, off, arg)
		self.count = 0
		self.value = []

	def do_parse(self, data, off, count):
		if count == 0xf:
			(count, off) = read_int(data, off)
		self.count = count
		off += count * struct.calcsize(self.something_fmt)
		n = 0
		while n < count and off < len(data):
			parser = query_parser(data, off)
			off = parser.parse(self.something_fmt)
			self.value.append(parser)
			n += 1
		return off

	def do_show(self, page, data, parent):
		iter = self.add_pgiter(page, 'Array', '', data, parent)
		something = data[self.start:self.start + self.count * struct.calcsize(self.something_fmt)]
		add_pgiter(page, 'Something', 'plist', '', something, iter)
		self.show_values(page, 'Values', data, iter, self.value)

class dictionary(record):
	def __init__(self, data, off, arg):
		record.__init__(self, data, off, arg)
		self.count = 0
		keys = []
		values = []
		self.value = (keys, values)

	def do_parse(self, data, off, count):
		if count == 0xf:
			(count, off) = read_int(data, off)
		self.count = count
		off += 2 * count * struct.calcsize(self.something_fmt)
		n = 0
		while n < 2 * count and off < len(data):
			parser = query_parser(data, off)
			off = parser.parse(self.something_fmt)
			self.value[int(n >= count)].append(parser)
			n += 1
		return off

	def do_show(self, page, data, parent):
		iter = self.add_pgiter(page, 'Dictionary', '', data, parent)
		something = data[self.start:self.start + 2 * self.count * struct.calcsize(self.something_fmt)]
		add_pgiter(page, 'Something', 'plist', '', something, iter)
		self.show_values(page, 'Keys', data, iter, self.value[0])
		self.show_values(page, 'Values', data, iter, self.value[1])

prop_parsers = {
	0: boolean,
	1: integer,
	2: real,
	3: date,
	4: data,
	5: string,
	6: utf16,
	0xa: array,
	0xd: dictionary,
}

class plist_parser:
	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.offset_format = '>B'
		self.something_fmt = '>B'
		self.start_trailer = len(data) - 0x20
		self.start_offset_table = 0

	def parse(self):
		add_pgiter(self.page, 'Header', 'plist', 'header', self.data[0:8], self.parent)
		self._parse_trailer()
		props = self.data[8:self.start_offset_table]
		props_iter = add_pgiter(self.page, 'Properties', 'plist', '', props, self.parent)
		self._parse_props(props, 0, props_iter)
		offset_table_cb = 'offset_table_%d' % struct.calcsize(self.offset_format)
		add_pgiter(self.page, 'Offset table', 'plist', offset_table_cb, self.data[self.start_offset_table:self.start_trailer], self.parent)
		add_pgiter(self.page, 'Trailer', 'plist', 'trailer', self.data[self.start_trailer:], self.parent)

	def _parse_props(self, data, off, parent):
		while off < len(data):
			try:
				parser = query_parser(data, off)
				off = parser.parse(self.something_fmt)
			except format_error, e:
				parser.show(self.page, parent) # show at least something
				print(e.what())
				return
			parser.show(self.page, parent)

	def _parse_trailer(self):
		off = self.start_trailer + 6
		format_map = {1: '>B', 2: '>H'}
		(offset_byte_size, off) = rdata(self.data, off, '>B')
		if not format_map.has_key(offset_byte_size):
			raise format_error('unknown offset byte size %x' % offset_byte_size, off - 1)
		self.offset_format = format_map[offset_byte_size]
		(ref_byte_size, off) = rdata(self.data, off, '>B')
		if not format_map.has_key(ref_byte_size):
			raise format_error('unknown dict byte size %x' % ref_byte_size, off - 1)
		self.something_fmt = format_map[ref_byte_size]
		off += 6
		(offset_count, off) = rdata(self.data, off, '>H')
		off += 0xe
		(self.start_offset_table, off) = rdata(self.data, off, '>H')

def add_header(hd, size, data):
	off = 0
	(magic, off) = rdata(data, off, '6s')
	add_iter(hd, 'Magic', magic, off - 6, 6, '6s')
	(version, off) = rdata(data, off, '2s')
	add_iter(hd, 'Version?', version, off - 2, 2, '2s')

def add_offset_table(hd, size, data, fmt):
	fmtsize = struct.calcsize(fmt)
	n = 0
	off = 0
	while off + fmtsize < size:
		(offset, off) = rdata(data, off, fmt)
		add_iter(hd, 'Offset %d' % n, offset, off - fmtsize, fmtsize, fmt)
		n += 1

def add_offset_table_1(hd, size, data):
	add_offset_table(hd, size, data, '>B')

def add_offset_table_2(hd, size, data):
	add_offset_table(hd, size, data, '>H')

def add_trailer(hd, size, data):
	off = 6
	(offset_byte_size, off) = rdata(data, off, '>B')
	add_iter(hd, 'Offset byte size', offset_byte_size, off - 1, 1, '>B')
	(ref_byte_size, off) = rdata(data, off, '>B')
	add_iter(hd, 'Something byte size', ref_byte_size, off - 1, 1, '>B')
	off += 6
	(offset_count, off) = rdata(data, off, '>H')
	add_iter(hd, 'Offset count', offset_count, off - 2, 2, '>H')
	off += 0xe
	(offset_table, off) = rdata(data, off, '>H')
	add_iter(hd, 'Offset table offset', offset_table, off - 2, 2, '>H')

def add_string(hd, size, data):
	off = 0
	(c, off) = rdata(data, off, '>B')
	sz = c & 0xf
	if sz == 0xf:
		(sz, off) = read_int(data, off)
	(string, off) = rdata(data, off, '%ds' % sz)
	add_iter(hd, 'Value', string, off - sz, sz, '%ds' % sz)

def add_utf16(hd, size, data):
	off = 0
	(c, off) = rdata(data, off, '>B')
	sz = c & 0xf
	if sz == 0xf:
		(sz, off) = read_int(data, off)
	sz = 2 * sz
	(utf16, off) = rdata(data, off, '%ds' % sz)
	add_iter(hd, 'Value', unicode(utf16, 'utf-16be'), off - sz, sz, '%ds' % sz)

plist_ids = {
	'header': add_header,
	'offset_table_1': add_offset_table_1,
	'offset_table_2': add_offset_table_2,
	'trailer': add_trailer,
	'string': add_string,
	'utf16': add_utf16,
}

def open(data, page, parent):
	parser = plist_parser(page, data, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
