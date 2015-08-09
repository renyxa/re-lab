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

# Description of the wire format: https://developers.google.com/protocol-buffers/docs/encoding
# Note: this is rather simplified parser, tailored to the purpose of
# displaying the complete structure and values.

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
		self.visualizer = 'iwa_%s' % name

	def __call__(self, data, off, start, end):
		return result(self.parser(data, off), self, start, end)

def parse_bool(data, off):
	return bool(read_var(data, off)[0])

def parse_int64(data, off):
	return read_var(data, off)[0]

def parse_sint64(data, off):
	return read_var(data, off)[0]

def enum(values={}):
	class _enum:
		def __init__(self, parser):
			self.parser = parser

		def __call__(self, data, off):
			i = self.parser(data, off)
			if values.has_key(i):
				return values[i]
			return 'Unknown'

	return primitive(varlen(_enum(parse_int64)), 'enum')

bool_ = primitive(varlen(parse_bool), 'bool')
int64 = primitive(varlen(parse_int64), 'int64')
sint64 = primitive(varlen(parse_sint64), 'sint64')
fixed32 = primitive(fixed(4, '<I'), 'fixed32')
sfixed32 = primitive(fixed(4, '<i'), 'sfixed32')
fixed64 = primitive(fixed(8, '<Q'), 'fixed64')
sfixed64 = primitive(fixed(8, '<q'), 'sfixed64')
float_ = primitive(fixed(4, '<f'), 'float')
double_ = primitive(fixed(8, '<d'), 'double')

class string_:
	def __init__(self):
		self.primitive = False
		self.structured = False
		self.visualizer = 'iwa_string'

	def __call__(self, data, off, start, end):
		return result(data[off:end], self, start, end)

string = string_()

class packed:
	def __init__(self, item):
		self.item = item
		self.primitive = False
		self.structured = False
		if item.name:
			self.visualizer = 'iwa_packed_%s' % item.name
		else:
			self.visualizer = None

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
	def __init__(self, desc=None):
		if desc:
			self.desc = desc
		else:
			self.desc = {}
		self.primitive = False
		self.structured = True
		self.visualizer = None

	def __call__(self, data, off, start, end):
		msg = {}
		while off < end:
			stt = off
			(key, off) = read_var(data, off)
			field_num = key >> 3
			wire_type = key & 0x7
			stt_data = off
			visualizer = None
			if wire_type == 0:
				off = find_var(data, off)
				visualizer = 'iwa_varint'
			elif wire_type == 1:
				off += 8
				visualizer = 'iwa_64bit'
			elif wire_type == 2:
				(length, off) = read_var(data, off)
				stt_data = off
				off += length
			elif wire_type == 3 or wire_type == 4:
				pass
			elif wire_type == 5:
				off += 4
				visualizer = 'iwa_32bit'
			else:
				raise self.unknown_type()
			if not msg.has_key(field_num):
				msg[field_num] = []
			desc = self._desc(field_num, wire_type == 2, visualizer)
			msg[field_num].append(desc(data, stt_data, stt, off))
		if off != end:
			raise self.bad_format()
		return result(msg, self, start, end)

	class unknown_type:
		pass

	class bad_format:
		pass

	def _desc(self, field, structured, visualizer):
		class generic_desc:
			def __init__(self):
				self.primitive = False
				self.structured = False
				self.visualizer = None

			def __call__(self, data, off, start, end):
				if structured: # try to parse as a message
					try:
						desc = message()
						return desc(data, off, start, end)
					except:
						pass
				return result(data[start:end], self, start, end)

		desc = None

		if self.desc.has_key(field):
			global MESSAGES
			if len(self.desc[field]) > 1 and self.desc[field][1]:
				desc1 = self.desc[field][1]
				if isinstance(desc1, str):
					if MESSAGES.has_key(desc1):
						desc = MESSAGES[desc1]
				else:
					desc = desc1
			elif self.desc[field][0]:
				name = self.desc[field][0]
				if MESSAGES.has_key(name):
					desc = MESSAGES[name]
			if isinstance(desc, dict):
				desc = message(desc)

		if not desc:
			desc = generic_desc()
		if not desc.visualizer:
			desc.visualizer = visualizer

		return desc

### File parser

MESSAGES = {
	'Bezier': {1: ('Bezier element',)},
	'Bezier element': {
		1: ('Type', enum({1: 'M', 2: 'L', 5: 'C'})),
		2: ('Coords', {1: ('X', float_), 2: ('Y', float_)}),
	},
	'Character properties': {
		1: ('Bold', bool_),
		2: ('Italic', bool_),
		3: ('Font size', float_),
		7: ('Font color', 'Color'),
	},
	'Color': {1: ('Type?', int64), 3: ('Red', float_), 4: ('Green', float_), 5: ('Blue', float_), 6: ('Alpha', float_)},
	'Drawable shape': {1: ('Shape',), 2: ('Text ref', 'Ref')},
	'Geometry': {1: ('Position',), 2: ('Size',)},
	'IWA file': {
		1: ('First Object ID', int64),
		2: ('Kind', string), 3: ('Path', string),
		6: ('Reference', {1: ('File object', int64), 2: ('Object', int64), 3: ('Field?', int64)})
	},
	'Other file': {1: ('Number', int64), 3: ('Path', string), 5: ('Template', string)},
	'Paragraph properties': {
		40: ('List style ref', 'Ref'),
	},
	'Path': {
		3: ('Point path', {
			1: ('Type', enum({0: 'Right arrow', 10: 'Double arrow', 100: 'Star'})),
			2: ('Point', 'Position'),
			3: ('Size',)
		}),
		4: ('Scalar path', {
			1: ('Type', enum({0: 'Rounded rectangle', 1: 'Regular polygon'})),
			2: ('Value', float_),
			3: ('Size',)
		}),
		5: ('Bezier path', {2: ('Size',), 3: ('Bezier',)}),
		6: ('Callout2 path', {
			1: ('Size',),
			2: ('Tail position', 'Position'),
			3: ('Tail size', float_),
			4: ('Corner radius', float_),
			5: ('Tail at center', bool_),
		}),
		7: ('Connection path', {
			1: (None, {
				2: ('Size',),
				3: ('Bezier',),
			}),
		}),
	},
	'Position': {1: ('X', float_), 2: ('Y', float_)},
	'Ref': {1: ('Ref', int64)},
	'Shape': {
		1: ('Shape placement',),
		2: ('Graphic style ref', 'Ref'),
		3: ('Path',),
	},
	'Shape placement': {1: ('Geometry',), 2: ('Slide ref', 'Ref')},
	'Size': {1: ('Width', float_), 2: ('Height', float_)},
	'Style info': {1: ('UI name', string), 2: ('Name', string), 3: ('Parent', 'Ref'), 5: ('Stylesheet', 'Ref')},
	'Text address': {1: ('Start', int64), 2: ('Style ref', 'Ref')},
}

OBJECTS = {
	1: ('Document', {
		2: ('Presentation ref', 'Ref'),
		3: (None, {
			1: ('Annotations', {4: ('Language', string), 7: ('Annotation Author Storage Ref', 'Ref')}),
			3: ('Language', string),
			4: ('Calculation Engine Ref', 'Ref'),
			5: ('View State Ref', 'Ref'),
			6: (None, 'Ref'),
			7: ('Data List Ref', 'Ref'),
			9: ('Template', string)
		})
	}),
	2: ('Presentation', {
		2: (None, 'Ref'),
		4: ('Size',),
		5: ('Stylesheet ref', 'Ref')
	}),
	4: ('Master slide?', {
		2: ('Master slide ref', 'Ref'),
	}),
	5: ('Slide', {
		1: ('Style ref', 'Ref'),
		7: ('Drawable ref', 'Ref'),
		17: ('Master ref', 'Ref'),
	}),
	7: ('Placeholder', {
		1: (None, {
			1: (None, {
				1: (None, {
					1: ('Geometry',),
					2: ('Slide ref', 'Ref'),
				}),
				2: ('Graphic style ref', 'Ref'),
				3: ('Path',),
			}),
			2: ('Text ref', 'Ref'),
		}),
		2: ('Type', enum({1: 'Slide number', 2: 'Slide title', 3: 'Slide body'})),
	}),
	9: ('Slide style', {1: ('Style info',), 11: ('Properties',)}),
	10: (None, {
		1: (None, {
			1: ('Theme stylesheet ref', 'Ref'),
			3: ('Theme?', string),
			5: (None, 'Ref'),
		}),
	}),
	210: ('View State',),
	212: ('Annotation', {1: ('Author', string)}),
	213: ('Annotation Author Storage', {1: ('Annotation ref', 'Ref')}),
	401: ('Stylesheet', {
		1: (None, 'Ref'),
		2: (None, {
			1: ('Name', string),
			2: ('Ref', 'Ref'),
		}),
		3: ('Parent ref', 'Ref')
	}),
	2001: ('Text', {
		2: ('Stylesheet ref', 'Ref'),
		3: ('Text', string),
		5: ('Paragraphs', {1: ('Paragraph', 'Text address')}),
		8: ('Spans', {1: ('Span', 'Text address')}),
	}),
	2011: ('Drawable shape',),
	2014: ('Sticky note', {
		1: ('Drawable shape',),
		2: (None, 'Ref'),
	}),
	2021: ('Character style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties', 'Character properties'),
	}),
	2022: ('Paragraph style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Character properties',),
		12: ('Paragraph properties',)
	}),
	2023: ('List style', {1: ('Style info',), 10: ('Number of properties', int64),}),
	2025: ('Graphic style', {1: ('Style info',), 10: ('Number of properties', int64), 11: ('Properties',)}),
	3008: ('Group', {1: ('Shape placement',), 2: ('Shape ref', 'Ref')}),
	3009: ('Connection line', {1: ('Shape',), 2: ('Shape 1 ref', 'Ref'), 3: ('Shape 2 ref', 'Ref')}),
	3016: ('Image style', {1: ('Style info',), 10: ('Number of properties', int64), 11: ('Properties',)}),
	3056: (None, {3: ('Author ref', 'Ref')}),
	4000: ('Calculation Engine',),
	6003: ('Table style', {1: ('Style info',), 10: ('Number of properties', int64), 11: ('Properties',)}),
	6004: ('Cell style', {1: ('Style info',), 10: ('Number of properties', int64), 11: ('Properties',)}),
	6005: ('Data List',),
	6008: (None, {3: (None, 'Ref')}),
	11006: ('Object index', {
		1: ('Active object ref?', int64),
		3: ('IWA file',),
		4: ('Other file',),
	}),
}

# Parser for internal IWA files.
#
# Because the underlying Google Protobuf format does not retain info
# about nested messages (a message is represented in the same way as a
# string or binary data), the parser tries to detect them. This might
# lead to false positives.
#
# It is possible to set name and type to interesting pieces of content.
# There are two global dicts that contain specifications of the data:
# * OBJECTS dict contains names and message types of objects. The key is
#   the object type.
# * MESSAGES dict contains message types for commonly used sub-messages.
#   The key is the name of the message.
# The value for both of them is a dict, mapping a field number to its
# name and type. The name and type are passed as a list; name is the
# first element, type the second. If there is no good name for the
# field, name should be None. Type is optional; if it is not given, the
# parser tries to look up name in MESSAGES and use that type. Similarly,
# if the type is a string, the parser again tries to look up the real
# type in MESSAGES.
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
			obj_id = None
			if hdr.value.has_key(1):
				obj_id = hdr.value[1][0].value
			obj_type = None
			if hdr.value.has_key(2):
				if hdr.value[2][0].value.has_key(1):
					obj_type = hdr.value[2][0].value[1][0].value
				if hdr.value[2][0].value.has_key(3):
					data_len = hdr.value[2][0].value[3][0].value
			obj_data = self.data[obj_start:off + hdr_len + data_len]
			obj_name = None
			if obj_type:
				if OBJECTS.has_key(obj_type):
					obj_name = OBJECTS[obj_type][0]
				if not obj_name:
					obj_name = 'Object %d' % obj_type
			else:
				obj_name = 'Object'
			if obj_id:
				obj_name = '%s (%d)' % (obj_name, obj_id)
			objiter = add_pgiter(self.page, '[%d] %s' % (obj_num, obj_name), 'iwa', 'iwa_object', obj_data, self.parent)
			self._add_pgiter('Header', hdr, off, off + hdr_len, objiter)
			off += hdr_len
			if data_len > 0:
				desc = self._desc(obj_type)
				data = self._parse_object(off, data_len, desc)
				self._add_pgiter('Data', data, off, off + data_len, objiter)
				off += data_len
			obj_num += 1

	_HEADER_MSG = message({1: ('ID', int64), 2: ('Data info',
		{
			1: ('Object type?', int64),
			2: (None, packed(int64)),
			3: ('Data size', int64),
			5: ('References', packed(int64))
		}
	)})

	def _parse_header(self, off, length):
		return self._HEADER_MSG(self.data, off, off, off + length)

	def _parse_object(self, off, length, desc):
		return desc(self.data, off, off, off + length)

	def _add_pgiter(self, name, obj, start, end, parent):
		if obj.desc.primitive:
			name = '%s = %s' % (name, obj.value)
		if obj.desc.visualizer:
			visualizer = obj.desc.visualizer
		else:
			visualizer = 'iwa_field'
		it = add_pgiter(self.page, name, 'iwa', visualizer, self.data[start:end], parent)
		if obj.desc.structured:
			for (k, v) in obj.value.iteritems():
				single = len(v) == 1
				for (i, e) in zip(xrange(len(v)), iter(v)):
					if single:
						n = '%d' % k
					else:
						n = "%d[%d]" % (k, i)
					if obj.desc.desc.has_key(k):
						if obj.desc.desc[k][0]:
							n = '%s: %s' % (n, obj.desc.desc[k][0])
					self._add_pgiter(n, e, e.start, e.end, it)

	def _desc(self, obj_type):
		desc = None
		if OBJECTS.has_key(obj_type):
			if len(OBJECTS[obj_type]) > 1 and OBJECTS[obj_type][1]:
				desc1 = OBJECTS[obj_type][1]
				if isinstance(desc1, str):
					if MESSAGES.has_key(desc1):
						desc = MESSAGES[desc1]
				else:
					desc = desc1
			elif OBJECTS[obj_type][0]:
				name = OBJECTS[obj_type][0]
				if MESSAGES.has_key(name):
					desc = MESSAGES[name]
			if isinstance(desc, dict):
				desc = message(desc)
		if not desc:
			desc = message()
		return desc

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

def add_field(hd, size, data):
	(key, off) = read_var(data, 0)
	field_num = key >> 3
	wire_type = key & 0x7
	wire_type_map = {0: 'Varint', 1: '64-bit', 2: 'Length-delimited', 3: 'Start group', 4: 'End group', 5: '32-bit'}
	wire_type_str = get_or_default(wire_type_map, wire_type, 'Unknown')
	add_iter(hd, 'Field', field_num, 0, off, '%ds' % off)
	add_iter(hd, 'Wire type', wire_type_str, 0, off, '%ds' % off)
	if wire_type == 2:
		len_off = off
		(length, off) = read_var(data, off)
		add_iter(hd, 'Length', length, len_off, off - len_off, '%ds' % (off - len_off))
	return off

def add_32bit(hd, size, data):
	off = add_field(hd, size, data)
	f32 = read(data, off, '<I')
	s32 = read(data, off, '<i')
	f = read(data, off, '<f')
	add_iter(hd, 'Fixed32', f32, off, off + 4, '<I')
	add_iter(hd, 'Signed fixed32', s32, off, off + 4, '<i')
	add_iter(hd, 'Float', f, off, off + 4, '<f')

def add_64bit(hd, size, data):
	off = add_field(hd, size, data)
	f64 = read(data, off, '<Q')
	s64 = read(data, off, '<q')
	d = read(data, off, '<d')
	add_iter(hd, 'Fixed64', f64, off, off + 8, '<Q')
	add_iter(hd, 'Signed fixed64', s64, off, off + 8, '<q')
	add_iter(hd, 'Double', d, off, off + 8, '<d')

def add_bool(hd, size, data):
	off = add_field(hd, size, data)
	b = parse_bool(data, off)
	add_iter(hd, 'Bool', b, off, size - off, '%ds' % (size - off))

def add_enum(hd, size, data):
	off = add_field(hd, size, data)
	i = parse_int64(data, off)
	add_iter(hd, 'Enum value', i, off, size - off, '%ds' % (size - off))

def add_int64(hd, size, data):
	off = add_field(hd, size, data)
	i = parse_int64(data, off)
	add_iter(hd, 'Int', i, off, size - off, '%ds' % (size - off))

def add_sint64(hd, size, data):
	off = add_field(hd, size, data)
	s = parse_sint64(data, off)
	add_iter(hd, 'Signed int', s, off, size - off, '%ds' % (size - off))

def add_fixed32(hd, size, data):
	off = add_field(hd, size, data)
	f32 = read(data, off, '<I')
	add_iter(hd, 'Fixed32', f32, off, off + 4, '<I')

def add_sfixed32(hd, size, data):
	off = add_field(hd, size, data)
	s32 = read(data, off, '<i')
	add_iter(hd, 'Signed fixed32', s32, off, off + 4, '<i')

def add_fixed64(hd, size, data):
	off = add_field(hd, size, data)
	f64 = read(data, off, '<Q')
	add_iter(hd, 'Fixed64', f64, off, off + 8, '<Q')

def add_sfixed64(hd, size, data):
	off = add_field(hd, size, data)
	s64 = read(data, off, '<q')
	add_iter(hd, 'Signed fixed64', s64, off, off + 8, '<q')

def add_float(hd, size, data):
	off = add_field(hd, size, data)
	f = read(data, off, '<f')
	add_iter(hd, 'Float', f, off, off + 4, '<f')

def add_double(hd, size, data):
	off = add_field(hd, size, data)
	d = read(data, off, '<d')
	add_iter(hd, 'Double', d, off, off + 8, '<d')

def add_packed(hd, size, data, parser, p16=False):
	off = add_field(hd, size, data)
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
	off = add_field(hd, size, data)
	obj = string(data, off, 0, size)
	add_iter(hd, 'String', obj.value, off, size - off, '%ds' % (size - off))

def add_varint(hd, size, data):
	off = add_field(hd, size, data)
	i = parse_int64(data, off)
	s = parse_sint64(data, off)
	b = parse_bool(data, off)
	add_iter(hd, 'Int', i, off, size - off, '%ds' % (size - off))
	add_iter(hd, 'Signed int', s, off, size - off, '%ds' % (size - off))
	add_iter(hd, 'Bool', b, off, size - off, '%ds' % (size - off))

iwa_ids = {
	'iwa_32bit': add_32bit,
	'iwa_64bit': add_64bit,
	'iwa_bool': add_bool,
	'iwa_compressed_block': add_iwa_compressed_block,
	'iwa_double': add_double,
	'iwa_enum': add_enum,
	'iwa_field': add_field,
	'iwa_fixed32': add_fixed32,
	'iwa_fixed64': add_fixed64,
	'iwa_float': add_float,
	'iwa_int64': add_int64,
	'iwa_object': add_iwa_object,
	'iwa_packed_bool': add_packed_bool,
	'iwa_packed_int64': add_packed_int64,
	'iwa_packed_sint64': add_packed_sint64,
	'iwa_packed_fixed32': add_packed_fixed32,
	'iwa_packed_sfixed32': add_packed_sfixed32,
	'iwa_packed_fixed64': add_packed_fixed64,
	'iwa_packed_sfixed64': add_packed_sfixed64,
	'iwa_packed_float': add_packed_float,
	'iwa_packed_double': add_packed_double,
	'iwa_sfixed32': add_sfixed32,
	'iwa_sfixed64': add_sfixed64,
	'iwa_sint64': add_sint64,
	'iwa_string': add_string,
	'iwa_varint': add_varint,
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
		uncompressed = uncompress(block[4:])
		uncompressed_data.extend(uncompressed)

		n += 1
		off += length

	uncompressed_data = str(uncompressed_data)
	parser = IWAParser(uncompressed_data, page, parent)
	parser.parse()

# vim: set ft=python sts=4 sw=4 noet:
