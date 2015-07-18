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

### General utils

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

def find_var(data, offset):
	"""Seek to the end of a variable-length number."""
	assert len(data) > offset
	off = offset
	c = ord(data[off])
	while off < len(data) and c & 0x80:
		off += 1
		c = ord(data[off])
	off += 1
	return off

def read_var(data, offset):
	"""Read a variable length number."""

	assert len(data) > offset

	cs = []
	off = offset
	c = ord(data[off])
	while off < len(data) and c & 0x80:
		cs.append(c & ~0x80)
		off += 1
		c = ord(data[off])
	cs.append(c)
	off += 1

	assert cs != []

	n = 0
	for c in reversed(cs):
		n = n << 7
		n += c

	return (n, off)

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

### Compression

# The compression method (as I currently understand it)
#
# Compressed data are broken sequences of literals and references into
# previously uncompressed data. A reference consists of offset (taken
# backwards from the end of uncompressed data) and length. They are
# recongized by the first byte, as follows:
# + xxxxxx00 - a literal run
#   - In case this is not ffffxx00, this byte is followed by a single
#   byte containing count. This is in turn followed by count + 1
#   literals.
#   - If it is ffffnn00, nn is the number of bytes that contain the
#     count, minus 1. These bytes are in little endian order. Again,
#     this is followed by count + 1 literals.
# + hhhnnn01 - a "near" reference
#   - This is followed by another byte containing lower bits of offset
#     minus 1. The hhh bits of reference form higher bits of offset.
#     nnn bits are length - 4.
# + nnnnnn10 - a "far" reference
#   - This is followed by two bytes containing offset, in little endian
#     order. The nnnnnn bits of reference are length - 1.

def uncompress(data):
	result = bytearray()

	def append_ref(offset, length):
		assert offset <= len(result)
		if offset >= length:
			start = len(result) - offset
			result.extend(result[start:start + length])
		else:
			# The run of literals is inserted repeatedly
			i = len(result) - offset
			while length > 0:
				result.append(result[i])
				i += 1
				length -= 1

	off = 0
	(uncompressed_length, off) = read_var(data, off)

	while off < len(data):
		# print('at offset %x:' % (off + 4))
		c = ord(data[off])
		off += 1
		typ = c & 0x3

		if typ == 0: # literals
			if (c & 0xf0) == 0xf0:
				count = (c >> 2) & 0x3
				length = ord(data[off]) + 1
				off += 1
				i = 1
				while i <= count:
					b = ord(data[off])
					length += (b << i * 8)
					i += 1
					off += 1
			else:
				length = (c >> 2) + 1
			# print('  literal run: length = %x' % length)
			result.extend(data[off:off + length])
			off += length
		elif typ == 1: # near reference
			length = ((c >> 2) & 0x7) + 4
			high = c >> 5
			low = ord(data[off])
			offset = (high << 8) | low
			off += 1
			# print('  near ref: offset = %x, length = %x' % (offset, length))
			append_ref(offset, length)
		elif typ == 2: # far reference
			length = (c >> 2) + 1
			offset = ord(data[off]) | (ord(data[off + 1]) << 8)
			off += 2
			# print('  far ref: offset = %x, length = %x' % (offset, length))
			append_ref(offset, length)
		else:
			print("unknown type at offset 0x%x inside block" % (off + 4))
			assert False

	assert uncompressed_length == len(result)

	return result

### Protocol buffers parser

class result:
	def __init__(self, value, desc, start, end):
		self.value = value
		self.desc = desc
		self.start = start
		self.end = end

class varlen:
	def __init__(self, parser):
		self.size = None
		self.parser = parser

	def __call__(self, data, off):
		return self.parser(data, off)

class fixed:
	def __init__(self, size, fmt):
		self.size = size
		self.fmt = fmt

	def __call__(self, data, off):
		return rdata(data, off, self.fmt)[0]

class primitive:
	def __init__(self, parser, name):
		self.parser = parser
		self.name = name # A hack to get showing of packed arrays working
		self.primitive = True
		self.structured = False
		self.size = parser.size
		self.visualizer = 0

	def __call__(self, data, off, start, end):
		return result(self.parser(data, off), self, start, end)

def parse_bool(data, off):
	return bool(read_var(data, off)[0])

def parse_int64(data, off):
	return read_var(data, off)[0]

def parse_sint64(data, off):
	return read_var(data, off)[0]

bool_ = primitive(varlen(parse_bool), 'bool')
int64 = primitive(varlen(parse_int64), 'int64')
sint64 = primitive(varlen(parse_sint64), 'sint64')
fixed32 = primitive(fixed(4, '<I'), 'fixed32')
sfixed32 = primitive(fixed(4, '<i'), 'sfixed32')
fixed64 = primitive(fixed(8, '<Q'), 'fixed64')
sfixed64 = primitive(fixed(8, '<q'), 'sfixed64')
float_ = primitive(fixed(4, '<f'), 'float')
double_ = primitive(fixed(8, '<d'), 'double')

class string:
	def __init__(self):
		self.primitive = False
		self.structured = False
		self.visualizer = 'string'

	def __call__(self, data, off, start, end):
		return result(data[off:end], self, start, end)

class packed:
	def __init__(self, item):
		self.item = item
		self.primitive = False
		self.structured = False
		if item.name:
			self.visualizer = 'packed_%s' % item.name
		else:
			self.visualizer = 0

	def __call__(self, data, off, start, end):
		values = []
		extents = []
		while off < end:
			if self.item.size == None:
				orig = off
				off = find_var(data, off)
				values.append(self.item.parser(data, orig))
				extents.append((orig, off))
			else:
				values.append(self.item.parser(data, off))
				extents.append((off, off + self.item.size))
				off += self.item.size
		return self._result(values, extents, self, start, end)

	def _result(self, values, extents, desc, start, end):
		r = result(values, desc, start, end)
		r.extents = extents
		return r

class message:
	def __init__(self, desc):
		if desc:
			self.desc = desc
		else:
			self.desc = {}
		self.primitive = False
		self.structured = True
		self.visualizer = 0

	def __call__(self, data, off, start, end):
		msg = {}
		while off < end:
			stt = off
			(key, off) = read_var(data, off)
			field_num = key >> 3
			wire_type = key & 0x7
			stt_data = off
			if wire_type == 0:
				off = find_var(data, off)
			elif wire_type == 1:
				off += 8
			elif wire_type == 2:
				(length, off) = read_var(data, off)
				stt_data = off
				off += length
			elif wire_type == 3 or wire_type == 4:
				print("unexpected type: group")
			elif wire_type == 5:
				off += 4
			if not msg.has_key(field_num):
				msg[field_num] = []
			if self.desc.has_key(field_num):
				# print("parsing field %d at %d in [%d, %d) as %s" %
						# (field_num, stt_data, stt, off, self.desc[field_num][1]))
				msg[field_num].append(self.desc[field_num][1](data, stt_data, stt, off))
			else:
				# print("parsing generic field %d of size %d at %d in [%d, %d)" %
						# (field_num, off - stt_data, stt_data, stt, off))
				msg[field_num].append(self._result(data[stt_data:off], stt, off))
		return result(msg, self, start, end)

	def _result(self, values, start, end):
		r = result(values, None, start, end)
		class empty:
			pass
		r.desc = empty()
		r.desc.primitive = False
		r.desc.structured = False
		r.desc.visualizer = 0
		return r

### File parser

MESSAGES = {}

class IWAParser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		off = 0
		obj_num = 0
		while off < len(self.data):
			obj_start = off
			(hdr_len, off) = read_var(self.data, off)
			hdr = self._parse_header(off, hdr_len)
			data_len = 0
			if hdr.value.has_key(2):
				if hdr.value[2][0].value.has_key(3):
					data_len = hdr.value[2][0].value[3][0].value
			obj_data = self.data[obj_start:off + hdr_len + data_len]
			objiter = add_pgiter(self.page, 'Object %d' % obj_num, 'iwa', 'iwa_object', obj_data, self.parent)
			self._add_pgiter('Header', hdr, off, off + hdr_len, objiter)
			off += hdr_len
			if data_len > 0:
				data = self._parse_object(off, data_len)
				self._add_pgiter('Data', data, off, off + data_len, objiter)
				off += data_len
			obj_num += 1

	_HEADER_MSG = message({2: ('Data info', message(
		{
			1: ('Object type?', int64),
			3: ('Data size', int64),
			5: ('Object IDs', packed(int64))
		}
	))})

	def _parse_header(self, off, length):
		return self._HEADER_MSG(self.data, off, off, off + length)

	def _parse_object(self, off, length):
		r = result(None, off, off, off + length)
		class empty:
			pass
		r.desc = empty()
		r.desc.structured = False
		r.desc.primitive = False
		r.desc.visualizer = 0
		return r

	def _add_pgiter(self, name, obj, start, end, parent):
		if obj.desc.primitive:
			name = '%s = %s' % (name, obj.value)
		it = add_pgiter(self.page, name, 'iwa', obj.desc.visualizer, self.data[start:end], parent)
		if obj.desc.structured:
			for (k, v) in obj.value.iteritems():
				single = len(v) == 1
				for (i, e) in zip(xrange(len(v)), iter(v)):
					if single:
						n = '%d' % k
					else:
						n = "%d[%d]" % (k, i)
					if obj.desc.desc.has_key(k):
						n = '%s: %s' % (n, obj.desc.desc[k][0])
					self._add_pgiter(n, e, e.start, e.end, it)

### Data view callbacks

def add_iwa_compressed_block(hd, size, data):
	(length, off) = rdata(data, 1, '<H')
	add_iter(hd, 'Compressed length', length, off - 2, 2, '<H')
	off += 1
	var_off = off
	(ulength, off) = read_var(data, off)
	add_iter(hd, 'Uncompressed length', ulength, var_off, off - var_off, '%ds' % (off - var_off))

def add_iwa_object(hd, size, data):
	(length, off) = read_var(data, 0)
	add_iter(hd, 'Header length', length, 0, off, '%ds' % off)

def add_packed(hd, size, data, parser, p16=False):
	off = find_var(data, 0) # skip key
	len_off = off
	(length, off) = read_var(data, off)
	add_iter(hd, 'Length', length, len_off, off - len_off, '%ds' % (off - len_off))
	obj = parser(data, off, 0, size)
	i = 0
	for (v, e) in zip(obj.value, obj.extents):
		add_iter(hd, 'Value %d' % i, v, e[0], e[1] - e[0], '%ds' % (e[1] - e[0]))
		i += 1

def add_packed_bool(hd, size, data):
	add_packed(hd, size, data, packed(bool_))

def add_packed_int64(hd, size, data):
	add_packed(hd, size, data, packed(int64))

def add_packed_sint64(hd, size, data):
	add_packed(hd, size, data, packed(sint64))

def add_packed_fixed32(hd, size, data):
	add_packed(hd, size, data, packed(fixed32))

def add_packed_sfixed32(hd, size, data):
	add_packed(hd, size, data, packed(sfixed32))

def add_packed_fixed64(hd, size, data):
	add_packed(hd, size, data, packed(fixed64))

def add_packed_sfixed64(hd, size, data):
	add_packed(hd, size, data, packed(sfixed64))

def add_packed_float(hd, size, data):
	add_packed(hd, size, data, packed(float_))

def add_packed_double(hd, size, data):
	add_packed(hd, size, data, packed(double_))

def add_string(hd, size, data):
	off = find_var(data, 0) # skip key
	len_off = off
	(length, off) = read_var(data, off)
	add_iter(hd, 'Length', length, len_off, off - len_off, '%ds' % (off - len_off))
	obj = string(data, off, 0, size)
	add_iter(hd, 'String', off, size - off, '%ds' % (size - off))

iwa_ids = {
	'iwa_compressed_block': add_iwa_compressed_block,
	'iwa_object': add_iwa_object,
	'packed_bool': add_packed_bool,
	'packed_int64': add_packed_int64,
	'packed_sint64': add_packed_sint64,
	'packed_fixed32': add_packed_fixed32,
	'packed_sfixed32': add_packed_sfixed32,
	'packed_fixed64': add_packed_fixed64,
	'packed_sfixed64': add_packed_sfixed64,
	'packed_float': add_packed_float,
	'packed_double': add_packed_double,
	'string': add_string,
}

### Entry point

def open(data, page, parent):
	n = 0
	off = 0
	uncompressed_data = bytearray()

	while off < len(data):
		off += 1
		(length, off) = rdata(data, off, '<H')
		off += 1

		block = data[off - 4:off + int(length)]
		blockiter = add_pgiter(page, 'Block %d' % n, 'iwa', 'iwa_compressed_block', block, parent)
		uncompressed = uncompress(block[4:])
		uncompressed_data.extend(uncompressed)
		add_pgiter(page, 'Uncompressed', 'iwa', 0, str(uncompressed), blockiter)

		n += 1
		off += length

	uncompressed_data = str(uncompressed_data)
	dataiter = add_pgiter(page, 'Uncompressed', 'iwa', 0, uncompressed_data, parent)
	parser = IWAParser(uncompressed_data, page, dataiter)
	parser.parse()

# vim: set ft=python sts=4 sw=4 noet:
