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

from utils import add_iter, add_pgiter, bflag2txt, key2txt, rdata

### General utils

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

def find_var(data, offset):
	"""Seek to the end of a variable-length number."""
	class bad_format:
		pass
	if len(data) <= offset:
		raise bad_format()
	off = offset
	c = ord(data[off])
	while off < len(data) and c & 0x80:
		off += 1
		c = ord(data[off])
	if c & 0x80:
		raise bad_format()
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

### Compression

# The compression method (as I currently understand it)
#
# Compressed data are broken sequences of literals and references into
# previously uncompressed data. A reference consists of offset (taken
# backwards from the end of uncompressed data) and length. They are
# recongized by the first byte, as follows:
# + xxxxxx00 - a literal run
#   - If it is ffffnn00, nn is the number of bytes that contain the
#     count, minus 1. These bytes are in little endian order. This is in
#     turn followed by count + 1 literals.
#   - Otherwise, the upper six bits contain the count. Again, this is
#     followed by count + 1 literals.
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
		self.custom = False
		self.size = parser.size
		self.visualizer = 'iwa_%s' % name

	def __call__(self, data, off, start, end):
		return result(self.parser(data, off), self, start, end)

def parse_bool(data, off):
	return bool(read_var(data, off)[0])

def parse_int64(data, off):
	return read_var(data, off)[0]

def parse_sint64(data, off):
	val = read_var(data, off)[0]
	mod = val % 2
	return (val + mod) / 2 * (1, -1)[mod]

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

def flags(bits={}):
	class _flags:
		def __init__(self, parser):
			self.parser = parser

		def __call__(self, data, off):
			i = self.parser(data, off)
			return bflag2txt(i, bits)

	return primitive(varlen(_flags(parse_int64)), 'flags')

bool_ = primitive(varlen(parse_bool), 'bool')
int64 = primitive(varlen(parse_int64), 'int64')
sint64 = primitive(varlen(parse_sint64), 'sint64')
fixed32 = primitive(fixed(4, '<I'), 'fixed32')
sfixed32 = primitive(fixed(4, '<i'), 'sfixed32')
fixed64 = primitive(fixed(8, '<Q'), 'fixed64')
sfixed64 = primitive(fixed(8, '<q'), 'sfixed64')
float_ = primitive(fixed(4, '<f'), 'float')
double_ = primitive(fixed(8, '<d'), 'double')

class bytes_:
	def __init__(self, visualizer='iwa_field'):
		self.primitive = False
		self.structured = False
		self.custom = False
		self.visualizer = visualizer

	def __call__(self, data, off, start, end):
		return result(data[off:end], self, start, end)

string = bytes_('iwa_string')

def custom(handler, wrapped=bytes_()):
	if isinstance(wrapped, dict):
		wrapped = message(wrapped)
	wrapped.custom = handler
	return wrapped

class packed:
	def __init__(self, item):
		self.item = item
		self.primitive = False
		self.structured = False
		self.custom = False
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
		self.custom = False
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
				self.custom = False
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

def handle_tile_row_defs(parser, page, data, parent):
	off = find_var(data, 0)
	off = find_var(data, off)
	parser.tile_row_data = data[off:]
	parser.tile_row_iter = parent

def handle_tile_row_offsets(parser, page, data, parent):
	parser.tile_row_offsets = {}
	off = find_var(data, 0)
	off = find_var(data, off)
	n = 0
	while off + 2 <= len(data):
		(offset, off) = rdata(data, off, '<H')
		if offset != 0xffff:
			parser.tile_row_offsets[offset] = n
		n += 1

def handle_tile_row(parser, page, data, parent):
	data = parser.tile_row_data
	offsets = sorted(parser.tile_row_offsets.keys())
	for (start, end) in zip(offsets, offsets[1:] + [len(data)]):
		add_pgiter(page, 'Column %d' % parser.tile_row_offsets[start], 'iwa', 'iwa_tile_row', data[start:end], parser.tile_row_iter)
	parser.tile_row_data = ''
	parser.tile_row_offsets = {}

FUNCTIONS = {
	6: 'ADDRESS',
	7: 'AND',
	8: 'AREAS',
	20: 'CLEAN',
	22: 'COLUMN',
	52: 'FALSE',
	62: 'IF',
	65: 'INT',
	69: 'ISBLANK',
	70: 'ISERROR',
	71: 'ISEVEN',
	72: 'ISODD',
	96: 'NOT',
	97: 'NOW',
	102: 'OR',
	156: 'TRUE',
	168: 'SUM',
	235: 'IFERROR',
	264: 'DEC2HEX',
}

MESSAGES = {
	'Animation': {
		1: ('Kind', string),
		2: ('Type', string),
		3: ('Animation duration', double_),
		4: ('Direction', int64), # TODO: identify directions
		5: ('Animation delay', double_),
	},
	'Bezier': {1: ('Bezier element',)},
	'Bezier element': {
		1: ('Type', enum({1: 'M', 2: 'L', 4: 'C', 5: 'Z'})),
		2: ('Coords', {1: ('X', float_), 2: ('Y', float_)}),
	},
	'Character properties': {
		1: ('Bold', bool_),
		2: ('Italic', bool_),
		3: ('Font size', float_),
		5: ('Font name', string),
		7: ('Font color', 'Color'),
		10: ('Superscript', enum({0: 'None', 1: 'Super', 2: 'Sub'})),
		11: ('Underline', bool_),
		12: ('Strikethru', bool_),
		13: ('Capitalization', enum({0: 'None', 1: 'All caps', 2: 'Small caps', 3: 'Title'})),
		14: ('Baseline shift', float_),
		16: ('Ligatures', enum({0: 'None', 1: 'Default', 2: 'All'})),
		18: ('Outline color', 'Color'),
		19: ('Outline', float_),
		21: ('Text shadow', 'Shadow'),
		23: ('Strikethru color', 'Color'),
		26: ('Text background', 'Color'),
		27: ('Tracking', float_),
	},
	'Color': {1: ('Type?', int64), 3: ('Red', float_), 4: ('Green', float_), 5: ('Blue', float_), 6: ('Alpha', float_)},
	'Columns': {
		1: ('Equal columns', {
			1: ('Number of columns', int64),
			2: ('Spacing', float_),
		}),
		2: ('Columns', {
			1: ('First column width', float_),
			2: ('Column', {
				1: ('Spacing', float_),
				2: ('Width', float_),
			}),
		}),
	},
	'Custom format': {
		1: ('Format name', string),
		3: ('Format', { # TODO: I think this is the same type as 6: Format
			18: ('Format string', string),
		}),
	},
	'Drawable shape': {1: ('Shape',), 2: ('Text ref', 'Ref')},
	'Fill': {
		1: ('Color',),
		2: ('Gradient',),
		3: ('Image', {
			2: ('Type', enum({0: 'original size', 1: 'stretch', 2: 'tile', 3: 'scale to fill', 4: 'scale to fit'})),
			3: ('Color'),
			4: ('Size',),
			6: ('File ref', 'Ref'),
		}),
	},
	'Format': {
		1: ('Type', enum({
			1: 'automatic',
			256: 'number',
			257: 'currency',
			258: 'percentage',
			259: 'scientific',
			260: 'text',
			261: 'date & time',
			262: 'fraction',
			263: 'checkbox',
			264: 'stepper',
			265: 'slider',
			266: 'pop-up menu',
			267: 'star rating',
			268: 'duration',
			269: 'numeral system',
			270: 'custom number',
			271: 'custom text',
			272: 'custom date & time',
		})),
		2: ('Decimal places', int64),
		3: ('Currency code', string),
		4: ('Negative style', enum({0: '-1', 1: 'red 1', 2: '(1)', 3: 'red (1)'})),
		5: ('Show thousands separator', bool_),
		6: ('Use accounting style', bool_),
		7: ('Duration style', enum({0: 'punctuation', 1: 'abbreviations', 2: 'words'})),
		8: ('Numeral base', int64),
		9: ('Digits', int64),
		10: ('Negative numbers representation', enum({0: 'two\'s-complement', 1: 'minus sign'})),
		11: ('Fraction accuracy', int64),
		14: ('Date format', string),
		15: ('High duration unit', flags({1: 'wk', 2: 'day', 4: 'hr', 8: 'min', 16: 'sec', 32: 'ms'})),
		16: ('Low duration unit', flags({1: 'wk', 2: 'day', 4: 'hr', 8: 'min', 16: 'sec', 32: 'ms'})),
		17: ('Custom format ID', int64),
		21: ('Min. value', double_),
		22: ('Max. value', double_),
		23: ('Increment', double_),
		24: ('Format', enum({256: 'number', 257: 'currency', 258: 'percentage', 259: 'scientific', 262: 'fraction', 269: 'numeral system'})),
		25: ('Slider orientation?', int64),
		26: ('Slider position?', int64),
		38: ('Pop-up start with', enum({0: 'blank', 1: 'first item'})),
	},
	'Formula': {
		1: ('Token array', { # formula is saved in RPN
			1: ('Token', {
				1: ('Type', enum({
					1: '+', 2: '-', 3: '*', 4: '/', 5: '^', 7: '>', 8: '>=', 9: '<', 10: '<=', 11: '=', 12: '<>', # infix ops
					13: '-', 14: '+', # prefix ops
					15: '%', # postfix op
					16: 'function',
					17: 'double', 19: 'string', # literals
					23: 'missing argument',
					25: '()',
					29: 'range',
					34: 'argument?', 35: 'argument pair?',
					36: 'address'
				})),
				2: ('Function', enum(FUNCTIONS)),
				3: ('Number of arguments', int64),
				4: ('Double', double_),
				6: ('String', string),
				10: ('Optional', bool_),
				26: ('Column', {1: ('Column', sint64), 2: ('Absolute', bool_),}),
				27: ('Row', {1: ('Row', sint64), 2: ('Absolute', bool_),}),
			}),
		}),
	},
	'Geometry': {
		1: ('Position',),
		2: ('Size',),
		3: ('Flags', flags({1: 'disable h. autosize', 2: 'disable v. autosize', 4: 'flip h.'})),
		4: ('Angle', float_),
	},
	'Gradient': {
		1: ('Type', enum({0: 'linear', 1: 'radial'})),
		2: ('Gradient stop', {1: ('Color',), 2: ('Fraction', float_), 3: ('Inflection', float_)}),
		3: ('Opacity', float_),
		5: ('Angle', {2: ('Angle', float_)}),
	},
	'IWA file': {
		1: ('First Object ID', int64),
		2: ('Name', string),
		3: ('Path', string),
		6: ('Reference', {1: ('File object', int64), 2: ('Object', int64), 3: ('Field?', int64)})
	},
	'Other file': {1: ('ID', int64), 3: ('Path', string), 5: ('Template', string)},
	'Padding': {1: ('Left', float_), 2: ('Top', float_), 3: ('Right', float_), 4: ('Bottom', float_),},
	'Paragraph properties': {
		1: ('Alignment', enum({0: 'Left', 1: 'Right', 2: 'Center', 3: 'Justify', 4: 'Cell'})),
		3: ('Decimal character', string),
		4: ('Default tab stops', float_),
		6: ('Text background', 'Color'),
		7: ('First line indent', float_),
		8: ('Hyphenate', bool_),
		9: ('Keep lines together', bool_),
		10: ('Keep with next', bool_),
		11: ('Left indent', float_),
		13: ('Line spacing', {
			1: ('Type', enum({0: 'lines', 1: 'at least', 2: 'exactly', 4: 'between'})),
			2: ('Amount', float_)
		}),
		14: ('Page break before', bool_),
		15: ('Border type', enum({0: 'None', 1: 'Top', 2: 'Bottom', 3: 'Top and bottom', 4: 'All'})),
		17: ('Paragraph rule offset', 'Position'),
		19: ('Right indent', float_),
		20: ('Space after', float_),
		21: ('Space before', float_),
		25: ('Tabs', {
			1: ('Tab stop', {
				1: ('Pos', float_),
				2: ('Alignment', enum({0: 'Left', 1: 'Center', 2: 'Right', 3: 'Decimal'})),
				3: ('Leader', string),
			})
		}),
		26: ('Widow control', bool_),
		32: ('Paragraph stroke', 'Stroke'),
		40: ('List style ref', 'Ref'),
		42: ('Following paragraph style ref', 'Ref'),
	},
	'Paragraph style': {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Character properties',),
		12: ('Paragraph properties',),
	},
	'Path': {
		3: ('Point path', {
			1: ('Type', enum({1: 'Right arrow', 10: 'Double arrow', 100: 'Star'})),
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
		8: ('Editable path', {
			1: ('Points', {
				1: ('Point', {
					1: ('Control point 1', 'Position'),
					2: ('Control point 2', 'Position'),
					3: ('Control point 3', 'Position'),
				}),
				2: ('Closed?', bool_),
			}),
			2: ('Size',),
		}),
	},
	'Position': {1: ('X', float_), 2: ('Y', float_)},
	'Ref': {1: ('Ref', int64)},
	'Reflection': {1: ('Transparency', float_)},
	'Shadow': {
		1: ('Color',),
		2: ('Angle', float_),
		3: ('Offset', float_),
		4: ('Blur', int64),
		5: ('Opacity', float_),
		7: ('Type', enum({0: 'drop', 1: 'contact', 2: 'curved'})),
		9: ('Contact shadow', {2: ('Perspective', float_)}),
		10: ('Curved shadow', {1: ('Balance', float_)}),
	},
	'Shape': {
		1: ('Shape placement',),
		2: ('Graphic style ref', 'Ref'),
		3: ('Path',),
	},
	'Shape placement': {
		1: ('Geometry',),
		2: ('Parent ref', 'Ref'),
		5: ('Locked', bool_),
		6: ('Comment ref', 'Ref'),
		7: ('Aspect ratio locked', bool_),
		8: ('Description', string),
	},
	'Size': {1: ('Width', float_), 2: ('Height', float_)},
	'Stroke': {
		1: ('Color',),
		2: ('Width', float_),
		3: ('Cap', enum({0: 'butt', 1: 'round'})),
		4: ('Join', enum({0: 'miter'})),
		5: ('Miter limit', float_),
		6: ('Stroke', {
			3: ('Number of elements', int64),
			4: ('Pattern element', float_),
		}),
		7: ('Texture', {2: ('Name', string)}),
		8: ('Picture frame', {2: ('Name', string), 3: ('Scale', float_)}),
	},
	'Style info': {1: ('UI name', string), 2: ('Name', string), 3: ('Parent', 'Ref'), 5: ('Stylesheet', 'Ref')},
	'Style name association': {1: ('Name', string), 2: ('Ref', 'Ref')},
	'Text address': {1: ('Start', int64), 2: ('Style ref', 'Ref')},
}

COMMON_OBJECTS = {
	210: ('View State',),
	212: ('Annotation', {1: ('Author', string)}),
	213: ('Annotation Author Storage', {1: ('Annotation ref', 'Ref')}),
	401: ('Stylesheet', {
		1: ('Style ref', 'Ref'),
		2: ('Style name association',),
		3: ('Parent ref', 'Ref'),
		5: ('Parent association', {1: ('Parent ref', 'Ref'), 2: ('Style ref', 'Ref')}),
	}),
	2001: ('Text', {
		2: ('Stylesheet ref', 'Ref'),
		3: ('Text', string),
		5: ('Paragraphs', {1: ('Paragraph', 'Text address')}),
		6: ('List levels', {1: ('List level', {1: ('Start', int64), 2: ('Level', int64)})}),
		7: ('List styles', {1: ('List style', {2: ('List style ref', 'Ref')})}),
		8: ('Spans', {1: ('Span', 'Text address')}),
		9: ('Fields', {1: ('Field', {1: ('Index', int64), 2: ('Replacement ref', 'Ref')})}),
		11: ('Links', {1: ('Link', 'Text address')}),
		12: ('Layouts', {1: ('Layout', 'Text address')}),
		14: ('List numbers', { 1: ('List number', { 1: ('Start', int64), 2: ('Start from', int64)})}),
		16: ('Footnotes', {1: ('Footnote', {1: ('Index', int64), 2: ('Ref',)})}),
		17: ('Sections', {1: ('Section', {1: ('Start', int64), 2: ('Section ref', 'Ref')})}),
		19: ('Languages', {1: ('Span', {1: ('Start', int64), 2: ('Language', string)})}),
		20: ('Change IDs?', {1: ('Change ID', {1: ('Start', int64), 2: ('UUID', string)})}),
		21: ('Changes', {1: ('Change', {1: ('Start', int64), 2: ('Change ref', 'Ref')})}),
		23: ('Comments', {1: ('Comment', {1: ('Start', int64), 2: ('Text comment ref', 'Ref')})}),
	}),
	2004: ('Footnote mark', {}),
	2008: ('Footnote', {2: ('Text ref', 'Ref')}),
	2011: ('Drawable shape',),
	2013: ('Text comment', {1: ('Comment ref', 'Ref')}),
	2014: ('Sticky note', {
		1: ('Drawable shape',),
		2: ('Comment ref', 'Ref'),
	}),
	2021: ('Character style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties', 'Character properties'),
	}),
	2022: ('Paragraph style',),
	2023: ('List style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('List label type', enum({0: 'none', 1: 'image',  2: 'bullet', 3: 'number'})),
		12: ('Text indent', float_),
		13: ('List label indent', float_),
		14: ('List label geometry', {1: ('Scale', float_), 2: ('Align', float_)}),
		15: ('Number format', enum({0: '1.', 1: '`(1)', 2: '1)', 3: 'I.', 4: '`(I)', 5: 'I)', 6: 'i.', 7: '`(i)', 8: 'i)', 9: 'A.', 10: '`(A)', 11: 'A)', 12: 'a.', 13: '`(a)', 14: 'a)'})),
		16: ('Bullet', string),
		17: ('Image', {3: ('Image Ref', 'Ref')}),
		21: ('Bullet color', 'Color'),
		25: ('Tiered', bool_),
	}),
	2024: ('Layout style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties', {
			7: ('Columns',),
			9: ('Layout margins', 'Padding'),
		}),
	}),
	2025: ('Graphic style', {
		1: ('Style', {
			1: ('Style info',),
			10: ('Number of properties', int64),
			11: ('Properties', {
				1: ('Fill',),
				2: ('Border', 'Stroke'),
				3: ('Opacity', float_),
				4: ('Shadow',),
				5: ('Reflection',),
			}),
		}),
		10: ('Number of properties', int64),
		11: ('Layout properties', {
			1: ('Shrink text to fit', bool_),
			2: ('Vertical alignment', enum({0: 'Top', 1: 'Center', 2: 'Bottom'})),
			4: ('Columns',),
			6: ('Text inset', {1: ('A side', float_), 2: ('A side', float_), 3: ('A side', float_), 4: ('A side', float_)}),
			10: ('Paragraph style ref', 'Ref'),
		}),
	}),
	2026: ('ToC style', {
		1: ('Paragraph style',),
	}),
	2032: ('Link', {
		2: ('Href', string),
	}),
	2043: ('Slide number', {}),
	2052: ('ToC entry', {
		4: ('Text', string),
		5: ('Paragraph style ref', 'Ref'),
	}),
	2060: ('Change', {
		3: ('Time?', {1: ('Time?', double_)}),
		4: ('UUID', string),
	}),
	2062: ('Change author?', {
		2: ('Author ref', 'Ref'),
	}),
	2240: ('Table of contents', {
		1: ('Drawable shape',),
		3: ('Entry ref', 'Ref')
	}),
	2241: ('ToC field', {1: ('Info', {1: ('ToC ref', 'Ref')})}),
	3005: ('Image', {
		1: ('Shape placement',),
		3: ('Media style ref', 'Ref'),
		4: ('Size',),
		5: ('Mask ref', 'Ref'),
		9: ('Natural size', 'Size'),
		10: ('Alpha mask path', 'Bezier'),
		11: ('File ref?', 'Ref'),
		13: ('File ref?', 'Ref'),
		15: ('Filtered ref', 'Ref'),
	}),
	3006: ('Mask', {
		1: ('Mask placement', 'Shape placement',),
		2: ('Masking shape path source', 'Path'),
	}),
	3007: ('Movie', {
		1: ('Shape placement',),
		3: ('Start frame', float_),
		4: ('End frame', float_),
		5: ('Poster frame', float_),
		7: ('Volume', float_),
		14: ('Main movie ref', 'Ref'),
		15: ('Poster image ref', 'Ref'),
		16: ('Audio-only image ref', 'Ref'),
		19: ('Style ref', 'Ref'),
		20: ('Size',),
		24: ('Repeat', enum({0: 'none', 1: 'loop', 2: 'loop back and forth'})),
	}),
	3008: ('Group', {1: ('Shape placement',), 2: ('Shape ref', 'Ref')}),
	3009: ('Connection line', {1: ('Shape',), 2: ('Shape 1 ref', 'Ref'), 3: ('Shape 2 ref', 'Ref')}),
	3016: ('Media style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties',{
			1: ('Border', 'Stroke'),
			2: ('Opacity?', float_),
			3: ('Shadow',),
			4: ('Reflection',),
		}),
	}),
	3056: ('Comment', {
		1: ('Text', string),
		2: ('Modification time?', {1: ('Timestamp', double_)}),
		3: ('Author ref', 'Ref')
	}),
	4000: ('Calculation Engine', {
		3: ('A ref', 'Ref'),
		5: ('Language', string),
	}),
	4004: ('Sort', {
		3: ('Criterion', 'Formula'),
	}),
	5021: ('Chart info', {
		1: ('Shape placement',),
		10000: ('Chart model', {
			7: ('Chart data', {
				1: ('Chart row name', string),
				2: ('Chart column name', string),
				3: ('Chart row data', {1: ('Number', {1: ('Number', double_)})}),
			}),
		}),
	}),
	6000: ('Tabular info', {
		1: ('Shape placement',),
		2: ('Tabular model ref', 'Ref'),
		3: ('A ref', 'Ref'),
	}),
	6001: ('Tabular model', {
		1: ('UUID', string),
		3: ('Table style ref', 'Ref'),
		4: ('Grid', {
			1: ('Row headers?', {2: ('Row headers ref', 'Ref')}),
			2: ('Column headers ref', 'Ref'),
			3: ('Cells', {1: ('Tile', {2: ('Tile ref', 'Ref')})}),
			4: ('Simple text list ref', 'Ref'),
			5: ('Cell style list ref', 'Ref'),
			6: ('Formula list ref', 'Ref'),
			11: ('Format list ref', 'Ref'),
			12: ('Invalid formula list ref', 'Ref'),
			16: ('Menu list ref', 'Ref'),
			17: ('Paragraph text list ref', 'Ref'),
			18: ('Conditional format list ref', 'Ref'),
			19: ('Comment list ref', 'Ref'),
			20: ('A data list ref', 'Ref'),
		}),
		6: ('Number of rows', int64),
		7: ('Number of columns', int64),
		8: ('Name', string),
		9: ('Number of header rows', int64),
		10: ('Number of header columns', int64),
		11: ('Number of footer rows', int64),
		12: ('Header rows frozen?', bool_),
		13: ('Header columns frozen?', bool_),
		17: ('Default column width?', double_),
		18: ('A cell style ref', 'Ref'),
		19: ('A cell style ref', 'Ref'),
		20: ('A cell style ref', 'Ref'),
		21: ('A cell style ref', 'Ref'),
		24: ('A paragraph style ref', 'Ref'),
		25: ('A paragraph style ref', 'Ref'),
		26: ('A paragraph style ref', 'Ref'),
		27: ('A paragraph style ref', 'Ref'),
		30: ('Table Name paragraph style ref', 'Ref'),
		36: ('A graphic style ref', 'Ref'),
		38: ('Filter ref', 'Ref'),
		41: ('Hidden rows', int64),
		42: ('Hidden columns', int64),
		45: ('Sort', {1: ('Sort ref', 'Ref')}),
		47: ('Merged cells', {
			2: ('Ranges', {
				2: ('Next ID?', int64),
				3: ('Range', {
					1: ('ID?', int64),
					2: ('Formula',),
				}),
			}),
		}),
	}),
	6002: ('Tile', {
		1: ('Last column', int64),
		2: ('Last row', int64),
		3: ('Number of cells', int64),
		4: ('Number of rows', int64),
		5: ('Row', custom(handle_tile_row, {
			1: ('Row', int64),
			2: ('Number of cells', int64),
			3: ('Definitions', custom(handle_tile_row_defs)),
			4: ('Definition offsets', custom(handle_tile_row_offsets, bytes_('iwa_tile_offsets'))),
		})),
	}),
	6003: ('Table style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties', {
			2: ('Alternating rows', {1: ('Color',)}),
			22: ('Fit row height', bool_),
			32: (None, {
				1: ('Count', int64),
				3: (None, {
					1: ('A stroke', 'Stroke'),
					2: ('A stroke', 'Stroke'),
					3: ('A stroke', 'Stroke'),
				}),
			}),
			33: ('Gridlines in body rows', bool_),
			34: ('Gridlines in body columns', bool_),
			38: ('Table outline', bool_),
			41: ('Default cell font', string),
			42: ('Gridlines in header rows', bool_),
			43: ('Gridlines in header columns', bool_),
			44: ('Gridlines in footer rows', bool_),
			46: ('A stroke', 'Stroke'),
			47: ('A stroke', 'Stroke'), # related to table outline
			48: ('A stroke', 'Stroke'),
			49: ('A stroke', 'Stroke'),
			50: ('A stroke', 'Stroke'), # related to table outline
			51: ('A stroke', 'Stroke'),
			52: ('A stroke', 'Stroke'),
			53: ('A stroke', 'Stroke'),
			54: ('A stroke', 'Stroke'),
			55: ('A stroke', 'Stroke'), # related to table outline
			56: ('A stroke', 'Stroke'),
			57: ('A stroke', 'Stroke'),
			58: ('A stroke', 'Stroke'), # related to table outline
			59: ('A stroke', 'Stroke'), # related to table outline
			60: ('A stroke', 'Stroke'),
			61: ('A stroke', 'Stroke'),
		})
	}),
	6004: ('Cell style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties', {
		1: ('Fill',),
			10: ('Top border', 'Stroke'),
			11: ('Right border', 'Stroke'),
			12: ('Bottom border', 'Stroke'),
			13: ('Left border', 'Stroke'),
		}),
	}),
	6005: ('Data list', {
		1: ('Type', enum({1: 'simple text', 2: 'number format', 3: 'formula', 4: 'cell style', 5: 'invalid formula', 6: 'custom format', 7: 'menu', 8: 'paragraph text', 9: 'conditional format', 10: 'comment',})),
		2: ('Next ID', int64),
		3: ('Entry', {
			1: ('ID', int64),
			2: ('Type?', int64),
			3: ('Text', string),
			4: ('Style ref', 'Ref'),
			5: ('Formula',),
			6: ('Format',),
			8: ('Custom format',),
			9: ('Text entry ref', 'Ref'),
			10: ('Comment ref', 'Ref'),
		}),
	}),
	6006: ('Headers', {
		2: ('Header', {
			1: ('Row/Column', int64),
			2: ('Size', float_),
			3: ('Hidden', bool_),
			4: ('Number of cells', int64),
		}),
	}),
	6008: (None, {3: ('A ref', 'Ref')}),
	6010: ('Conditional format', {
		1: ('Number of rules', int64),
		2: ('Rule', {
			1: ('Rule formula', {1: ('Formula',)}),
			2: ('Cell style ref', 'Ref'),
			3: ('Paragraph style ref', 'Ref'),
		}),
	}),
	6206: ('Menu choices', {
		2: ('Choice', {
			1: ('Type', enum({1: 'empty', 5: 'text'})),
			5: ('Text value', {
				1: ('Text', string),
			}),
		}),
	}),
	6218: ('Text entry', {1: ('Text ref', 'Ref')}),
	6220: ('Filter', {
		3: ('Rule', {1: ('Filter formula', {1: ('Formula',)})}),
	}),
	11006: ('Object index', {
		1: ('Active object ref?', int64),
		3: ('IWA file',),
		4: ('Other file',),
	}),
}

KEYNOTE_OBJECTS = {
	1: ('Document', {
		2: ('Presentation ref', 'Ref'),
		3: ('Document info', {
			1: ('Annotations', {4: ('Language', string), 7: ('Annotation Author Storage Ref', 'Ref')}),
			3: ('Language', string),
			4: ('Calculation Engine Ref', 'Ref'),
			5: ('View State Ref', 'Ref'),
			6: (None, 'Ref'),
			7: ('Custom format data list ref?', 'Ref'),
			9: ('Template', string)
		})
	}),
	2: ('Presentation', {
		2: ('Theme ref?', 'Ref'),
		3: ('Slide list', {1: ('Slide list ref', 'Ref')}),
		4: ('Size',),
		5: ('Stylesheet ref', 'Ref')
	}),
	4: ('Slide list', {
		1: ('Slide list ref', 'Ref'),
		2: ('Slide ref', 'Ref'),
	}),
	5: ('Slide', {
		1: ('Style ref', 'Ref'),
		2: ('Build ref', 'Ref'),
		3: ('Build chunk', {1: ('Parent build ref', 'Ref'), 2: ('Order?', int64)}),
		4: ('Transition', {
			2: ('Transition attributes', {
				6: ('Animation auto?', bool_),
				8: ('Animation',),
				10: ('Number of particles', int64),
				11: ('Type', int64),
			}),
		}),
		5: ('Title placeholder ref', 'Ref'),
		6: ('Body placeholder ref', 'Ref'),
		7: ('Shape ref', 'Ref'),
		17: ('Master ref', 'Ref'),
		20: ('Slide number placeholder ref', 'Ref'),
		27: ('Notes ref', 'Ref'),
		42: (None, 'Ref'),
	}),
	7: ('Placeholder', {
		1: ('Drawable shape',),
		2: ('Type', enum({1: 'Slide number', 2: 'Slide title', 3: 'Slide body'})),
	}),
	8: ('Build', {
		1: ('Info ref', 'Ref'),
		2: ('Mode?', string),
		4: ('Style', {
			6: ('Animation delay automatic after?', double_),
			18: ('Animation',),
		}),
	}),
	9: ('Slide style', {
		1: ('Style info',),
		10: ('Number of properties', int64),
		11: ('Properties', {
			1: ('Background', 'Fill'),
		}),
	}),
	10: ('Theme?', {
		1: ('Theme info', {
			1: ('Theme stylesheet ref', 'Ref'),
			3: ('Name', string),
			5: (None, 'Ref'),
		}),
		2: ('Slide list ref', 'Ref'),
		3: ('Group UUID', string),
	}),
	15: ('Notes', {1: ('Text ref', 'Ref')}),
	19: ('Style name map', {
		1: ('Style name association',),
		2: ('Theme ref?', 'Ref'),
	}),
	20: (None, {
		1: ('Group UUID', string),
		2: ('Style name map ref', 'Ref'),
		3: ('Slide ref', 'Ref'),
	}),
}

NUMBERS_OBJECTS = {
	1: ('Document', {}),
}

PAGES_OBJECTS = {
	10000: ('Document', {
		4: ('Text body ref', 'Ref'),
		7: ('Document settings ref', 'Ref'),
		30: ('Page width', float_),
		31: ('Page height', float_),
		32: ('Left page margin', float_),
		33: ('Right page margin', float_),
		34: ('Top page margin', float_),
		35: ('Bottom page margin', float_),
		36: ('Header top margin', float_),
		37: ('Footer bottom margin', float_),
		38: ('Scale', float_),
		42: ('Page orientation', enum({0: 'Portrait', 1: 'Landscape'})),
		44: ('Paper size', string),
	}),

	10011: ('Section', {
		17: ('Match previous section', bool_),
		23: ('Left page h&f ref?', 'Ref'),
		24: ('Right page h&f ref?', 'Ref'),
		25: ('Both pages h&f ref', 'Ref'),
		28: ('Hide h&f on first page', bool_),
	}),
	10012: ('Document settings', {
		1: ('Type', enum({0: 'Page layout', 1: 'Word processing'})),
		2: ('Include headers', bool_),
		3: ('Include footers', bool_),
		9: ('Hyphenation', bool_),
		10: ('Ligatures', bool_),
		30: ('Note type', enum({0: 'Footnotes', 1: 'Document endnotes', 2: 'Section endnotes'})),
		31: ('Note format', enum({0: '1', 1: 'i', 2: '*'})),
		32: ('Note numbering', enum({0: 'Document', 1: 'Page', 2: 'Section'})),
		33: ('Space between notes', int64),
	}),
	10143: ('Header & footer', {
		1: ('Header text ref', 'Ref'),
		2: ('Footer text ref', 'Ref'),
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
# There are several global dicts that contain specifications of the data:
# * *_OBJECTS dicts contain names and message types of objects. The key is
#   the object type. Most of the objects (I suppose everything in the
#   range 200-9999) are shared among all 3 applications; these are defined
#   in COMMON_OBJECTS. The application-specific objects, which can be
#   defined in overlapping ranges, are defined in KEYNOTE_OBJECTS,
#   NUMBERS_OBJECTS and PAGES_OBJECTS.
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

	def __init__(self, data, page, parent, objects):
		self.data = data
		self.page = page
		self.parent = parent
		self.objects = objects
		self.tile_row_data = None
		self.tile_row_iter = None
		self.tile_row_offsets = {}

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
				if self.objects.has_key(obj_type):
					obj_name = self.objects[obj_type][0]
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
			1: ('Object type', int64),
			2: (None, packed(int64)),
			3: ('Data size', int64),
			5: ('References', packed(int64)),
			6: ('File ID', int64),
		}
	)})

	def _parse_header(self, off, length):
		return self._HEADER_MSG(self.data, off, off, off + length)

	def _parse_object(self, off, length, desc):
		return desc(self.data, off, off, off + length)

	def _add_pgiter(self, name, obj, start, end, parent, field=False):
		if obj.desc.primitive:
			name = '%s = %s' % (name, obj.value)
		if obj.desc.visualizer:
			visualizer = obj.desc.visualizer
		elif field:
			visualizer = 'iwa_field'
		else:
			visualizer = ''
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
					self._add_pgiter(n, e, e.start, e.end, it, True)
		if obj.desc.custom:
			obj.desc.custom(self, self.page, self.data[start:end], it)

	def _desc(self, obj_type):
		desc = None
		if self.objects.has_key(obj_type):
			if len(self.objects[obj_type]) > 1 and self.objects[obj_type][1]:
				desc1 = self.objects[obj_type][1]
				if isinstance(desc1, str):
					if MESSAGES.has_key(desc1):
						desc = MESSAGES[desc1]
				else:
					desc = desc1
			elif self.objects[obj_type][0]:
				name = self.objects[obj_type][0]
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
	add_iter(hd, 'Field', field_num, 0, off, '%ds' % off)
	add_iter(hd, 'Wire type', key2txt(wire_type, wire_type_map), 0, off, '%ds' % off)
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

def add_flags(hd, size, data):
	off = add_field(hd, size, data)
	i = parse_int64(data, off)
	add_iter(hd, 'Flags', '0x%x' % i, off, size - off, '%ds' % (size - off))

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

def add_tile_offsets(hd, size, data):
	off = add_field(hd, size, data)
	n = 0
	while off + 2 <= size:
		(offset, off) = rdata(data, off, '<H')
		offset_str = offset
		if offset == 0xffff:
			offset_str = 'none'
		add_iter(hd, 'Column %d' % n, offset_str, off - 2, 2, '<H')
		n += 1

def add_tile_row(hd, size, data):
	# The IDs point to appropriate data lists (c.f. table model)
	off = 2
	type_map = {0: 'empty', 2: 'number', 3: 'simple text', 5: 'date', 6: 'formula', 7: 'duration', 9: 'paragraph text'}
	(typ, off) = rdata(data, off, '<B')
	add_iter(hd, 'Cell type', key2txt(typ, type_map), off - 1, 1, '<B')
	off += 1
	flags_set = {
		0x2: 'style', 0x4: 'format', 0x8: 'formula',
		0x10: 'simple text', 0x20: 'number', 0x40: 'date',
		0x200: 'paragraph text',
		0xc00: 'conditional format',
		0x1000: 'comment',
	}
	(flags, off) = rdata(data, off, '<H')
	add_iter(hd, 'Flags', bflag2txt(flags, flags_set), off - 2, 2, '<H')
	off += 6

	# NOTE: the order is rather experimental; I originally thought the items are sorted by numeric value of the flag,
	# but apparently that's not the case. Sigh...
	if flags & 0x2:
		(style, off) = rdata(data, off, '<I')
		add_iter(hd, 'Style ID', style, off - 4, 4, '<I')
	if flags & 0xc00:
		(fmt, off ) = rdata(data, off, '<I')
		add_iter(hd, 'Conditional format ID', fmt, off - 4, 4, '<I')
		off += 4
	if flags & 0x4:
		(fmt, off ) = rdata(data, off, '<I')
		add_iter(hd, 'Format ID', fmt, off - 4, 4, '<I')
	if flags & 0x8:
		(formula, off ) = rdata(data, off, '<I')
		add_iter(hd, 'Formula ID', formula, off - 4, 4, '<I')
	if flags & 0x10:
		(text, off) = rdata(data, off, '<I')
		add_iter(hd, 'Simple text ID', text, off - 4, 4, '<I')
	if flags & 0x1000:
		(comment, off) = rdata(data, off, '<I')
		add_iter(hd, 'Comment ID', comment, off - 4, 4, '<I')
	if flags & 0x20:
		(value, off) = rdata(data, off, '<d')
		value_str = value
		if typ == 7:
			value_str = '%.1f s' % value
		add_iter(hd, 'Value', value_str, off - 8, 8, '<d')
	if flags & 0x40:
		(date, off) = rdata(data, off, '<d')
		add_iter(hd, 'Date', date, off - 8, 8, '<d')
	if flags & 0x200:
		(text, off) = rdata(data, off, '<I')
		add_iter(hd, 'Paragraph text ID', text, off - 4, 4, '<I')

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
	'iwa_flags': add_flags,
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

	'iwa_tile_offsets': add_tile_offsets,
	'iwa_tile_row': add_tile_row,
}

### Entry point

def detect(package):
	names = package.namelist()
	if "Index/MasterSlide.iwa" in names:
		return "Keynote"
	# I see no way to differentiate Pages and Numbers document just from
	# the structure. Luckily, the app-specific object numbers for these
	# two are in distinct ranges.
	return "Pages/Numbers"

def open(data, page, parent, subtype):
	objects = COMMON_OBJECTS.copy()
	if subtype == "Keynote":
		objects.update(KEYNOTE_OBJECTS)
	else:
		objects.update(NUMBERS_OBJECTS)
		objects.update(PAGES_OBJECTS)

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
	parser = IWAParser(uncompressed_data, page, parent, objects)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
