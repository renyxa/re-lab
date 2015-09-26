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

import struct

from utils import add_iter, add_pgiter, rdata

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

obfuscation_map = {}

def deobfuscate(data, orig_pos):
	def get_obfuscation_map(pos):
		def obfuscate_byte(byte, pos):
			def usub(a, b):
				if a >= b:
					return a - b
				else:
					return 0x100 - b + a
			def uadd(a, b):
				return (a + b) & 0xff
			val = byte
			base = (val & 0x60) << 1
			val = usub(base, val)
			val = usub(0xb9, val)
			mask = 0x1
			for i in range(0, 5):
				v = byte & mask
				p = pos & mask
				if p != 0:
					if v == 0:
						val = uadd(val, p)
					else:
						val = usub(val, p)
				mask = mask << 1
			mask = 0x60
			p = pos & mask
			if p != 0:
				val = uadd(val, p)
				val = uadd(val, base)
			return val
		if not obfuscation_map.has_key(pos):
			d = {}
			for b in range(0, 0x100):
				d[chr(obfuscate_byte(b, pos))] = chr(b)
			assert(len(d) == 0x100)
			obfuscation_map[pos] = d
		return obfuscation_map[pos]
	def packed(bytes):
		bytestring = ''
		for b in bytes:
			bytestring += struct.pack('<B', ord(b))
		return bytestring
	new_data = []
	pos = orig_pos
	for b in data:
		new_data.append(get_obfuscation_map(pos)[b])
		pos += 1
	return packed(new_data)

WLS_RECORDS = {
	0x38: ('Sheet def?', 'sheet_def'),
	0x70: ('Column width', 'column_width'),
	0xac: ('Text attributes', 'text_attrs'),
	0xb7: ('Text cell', 'text_cell'),
	0xb9: ('Formula cell', 'formula_cell'),
	0xbc: ('Page setup', 'page_setup'),
	# 0xbc: ('Empty cell', None), # TODO: clearly the code is either
	# continued in lower bits of the 'flags' byte or the flags modify
	# its meaning
	0xbe: ('Number cell', 'number_cell'),
	0xc3: ('Row height', 'row_height'),
	0xc4: ('Start something (sheet?)', None),
	0xc5: ('End something (sheet?)', None),
	0xc7: ('Page header', 'page_header_footer'),
	0xc8: ('Page footer', 'page_header_footer'),
	0xc9: ('Number of sheets', 'sheet_count'),
	0xca: ('Tab', 'tab'),
	0xd3: ('Named range', 'named_range'),
	0xdb: ('Cell style', 'cell_style'),
}

# I assume this is actually one list, but I'm not sure enough...
WLS_FUNCTIONS_FIXED = {
	0xa: 'Na',
	0x13: 'Pi',
	0x22: 'True',
	0x23: 'False',
	0x26: 'Not',
	0x41: 'Date',
	0x4a: 'Now',
	0x75: 'Exact',
	0xdd: 'Today',
}

WLS_FUNCTIONS_VAR = {
	0x0: 'Count',
	0x1: 'If',
	0x4: 'Sum',
	0x6: 'Min',
	0x7: 'Max',
	0xe: 'Fixed',
	0x24: 'And',
	0x25: 'Or',
	0x7c: 'Find',
}

class wls_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		data = self.data
		n = 0
		off = 0
		typ = None
		flags = 0
		while off + 1 < len(data):
			start = off
			(size, off) = rdata(data, off, '<h')
			# NOTE on compression: a consecutive sequence of records of
			# the same type is saved in a compressed form. The first
			# record is always complete; the following ones drop common
			# suffix. The base for determining common suffix is
			# accumulated result of previous writes, i.e., the bytes of
			# the current record are compared to the base, then the
			# bytes of the base are overwritten by current record. In
			# addition, it seems that the base is filled with 0 to the
			# right, so a record that ends with a number of 0 can still
			# be compressed, even if it's longer than any previous
			# record in the sequence.
			# Illustrative example: A sequence of strings "abcd", "ab",
			# "d", "ab" is saved as "abcd", ("", 2), ("d", 0), ("a", 1).
			# The comparison base changes as follows: None, "abcd",
			# "abcd", "dbcd".
			compressed = size < 0
			if size < 0:
				size = -size
			end = off + size
			assert(end >= off)
			if end > len(data):
				break
			if compressed:
				(compressed_size, off) = rdata(data, off, '<H')
			else:
				# NOTE: this would read nonsense if size == 0, but that should never happen
				(typ, off) = rdata(data, off, '<B')
				(flags, off) = rdata(data, off, '<B')
			recdata = data[start:end]
			assert(typ)
			rec = get_or_default(WLS_RECORDS, typ, ('Record %x' % typ, None))
			rec_str = '[%d] %s' % (n, rec[0])
			if flags != 0:
				rec_str += ' (flags %x)' % flags
			if compressed and compressed_size > 0:
				rec_str += ', compressed'
			if typ == 0xb7:
				# in text cells, the text is not obfuscated
				content = recdata[0:4] + deobfuscate(recdata[4:0xc], 4) + recdata[0xc:]
			else:
				content = recdata[0:4] + deobfuscate(recdata[4:], 4)
			handler = rec[1]
			if not handler:
				handler = 'record'
			reciter = add_pgiter(self.page, rec_str, 'wls', handler, content, self.parent)
			if size > 2:
				add_pgiter(self.page, 'Obfuscated', 'wls', '', recdata, reciter)
			off = end
			n += 1
		if off < len(data):
			add_pgiter(self.page, 'Trailer', 'wls', '', data[off:], self.parent)

def format_row(number):
	return '%d' % (number + 1)

def format_column(number):
	assert number >= 0
	assert number <= 0xff
	low = number % 26
	high = number / 26
	if high > 0:
		row = chr(0x40 + high)
	else:
		row = ''
	return row + chr(0x40 + low + 1)

def record_wrapper(wrapped):
	def wrapper(hd, size, data):
		off = 0
		(sz, off) = rdata(data, off, '<h')
		add_iter(hd, 'Size', abs(sz), off - 2, 2, '<h')
		compressed = 0
		if sz > 0:
			(typ, off) = rdata(data, off, '<B')
			add_iter(hd, 'Type', typ, off - 1, 1, '<B')
			(flags, off) = rdata(data, off, '<B')
			add_iter(hd, 'Flags', '0x%x' % flags, off - 1, 1, '<B')
		else:
			(compressed, off) = rdata(data, off, '<H')
			add_iter(hd, 'Compressed bytes', compressed, off - 2, 2, '<H')
		if wrapped:
			try:
				wrapped(hd, size, data, off)
			except struct.error, e:
				if compressed == 0:
					raise e
	return wrapper

def add_string(hd, size, data, off, name, fmt):
	fmtlen = struct.calcsize(fmt)
	(length, off) = rdata(data, off, fmt)
	add_iter(hd, '%s length' % name, length, off - fmtlen, fmtlen, fmt)
	(text, off) = rdata(data, off, '%ds' % length)
	add_iter(hd, name, unicode(text, 'cp1250'), off - length, length, '%ds' % length)
	return off

def add_short_string(hd, size, data, off, name):
	return add_string(hd, size, data, off, name, '<B')

def add_long_string(hd, size, data, off, name):
	return add_string(hd, size, data, off, name, '<H')

def add_cell(hd, size, data, off):
	(row, off) = rdata(data, off, '<H')
	add_iter(hd, 'Row', format_row(row), off - 2, 2, '<H')
	(col, off) = rdata(data, off, '<B')
	add_iter(hd, 'Column', format_column(col), off - 1, 1, '<B')
	off += 1
	(style, off) = rdata(data, off, '<H')
	add_iter(hd, 'Style', style, off - 2, 2, '<H')
	return off

def add_number_cell(hd, size, data, off):
	off = add_cell(hd, size, data, off)
	(val, off) = rdata(data, off, '<d')
	add_iter(hd, 'Value', val, off - 8, 8, '<d')

def add_text_cell(hd, size, data, off):
	off = add_cell(hd, size, data, off)
	add_long_string(hd, size, data, off, 'Text')

def add_tab(hd, size, data, off):
	add_short_string(hd, size, data, off, 'Name')

def add_row_height(hd, size, data, off):
	(row, off) = rdata(data, off, '<H')
	add_iter(hd, 'Row', format_row(row), off - 2, 2, '<H')
	off += 4
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Height', '%.2fpt' % (height / 20.0), off - 2, 2, '<H')

def add_column_width(hd, size, data, off):
	(first, off) = rdata(data, off, '<B')
	add_iter(hd, 'First column', format_column(first), off - 1, 1, '<B')
	off += 1
	(last, off) = rdata(data, off, '<B')
	add_iter(hd, 'Last column', format_column(last), off - 1, 1, '<B')
	off += 1
	(width, off) = rdata(data, off, '<H')
	# the conversion factor to pt seems to be something around 275
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

def add_sheet_def(hd, size, data, off):
	(offset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Offset of something (sheet?)', offset, off - 2, 2, '<H')
	off += 4
	add_short_string(hd, size, data, off, 'Name')

def add_page_header_footer(hd, size, data, off):
	add_short_string(hd, size, data, off, 'Text')

def add_page_setup(hd, size, data, off):
	def format_cm(val):
		return '%.2f cm' % (2.54 * val)

	(first_page_num, off) = rdata(data, off, '<I')
	add_iter(hd, 'First page number', first_page_num, off - 4, 4, '<I')
	off += 4
	(scale, off) = rdata(data, off, '<I')
	add_iter(hd, 'Scale', '%d%%' % scale, off - 4, 4, '<I')
	(fit_vert, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of pages vertically', fit_vert, off - 4, 4, '<I')
	(fit_hor, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of pages horizontally', fit_hor, off - 4, 4, '<I')
	(top, off) = rdata(data, off, '<f')
	add_iter(hd, 'Top margin', format_cm(top), off - 4, 4, '<f')
	(bottom, off) = rdata(data, off, '<f')
	add_iter(hd, 'Bottom margin', format_cm(bottom), off - 4, 4, '<f')
	(left, off) = rdata(data, off, '<f')
	add_iter(hd, 'Left margin', format_cm(left), off - 4, 4, '<f')
	(right, off) = rdata(data, off, '<f')
	add_iter(hd, 'Right margin', format_cm(right), off - 4, 4, '<f')
	(header, off) = rdata(data, off, '<f')
	add_iter(hd, 'Header height', format_cm(header), off - 4, 4, '<f')
	(footer, off) = rdata(data, off, '<f')
	add_iter(hd, 'Footer height', format_cm(footer), off - 4, 4, '<f')
	off += 0x1c
	(range_start_col, off) = rdata(data, off, '<H')
	add_iter(hd, 'Range start column', format_column(range_start_col), off - 2, 2, '<H')
	(range_start_row, off) = rdata(data, off, '<B')
	add_iter(hd, 'Range start row', format_row(range_start_row), off - 1, 1, '<B')
	off += 1
	(range_end_col, off) = rdata(data, off, '<H')
	add_iter(hd, 'Range end column', format_column(range_end_col), off - 2, 2, '<H')
	(range_end_row, off) = rdata(data, off, '<B')
	add_iter(hd, 'Range end row', format_row(range_end_row), off - 1, 1, '<B')

def add_sheet_count(hd, size, data, off):
	(count, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number', count, off - 2, 2, '<H')

def add_named_range(hd, size, data, off):
	off += 3
	(name_length, off) = rdata(data, off, '<B')
	add_iter(hd, 'Name length', name_length, off - 1, 1, '<B')
	off += 0xa
	(name, off) = rdata(data, off, '%ds' % name_length)
	add_iter(hd, 'Name', name, off - name_length, name_length, '<%ds' % name_length)
	off += 0xf
	(start_row, off) = rdata(data, off, '<H')
	add_iter(hd, 'Start row', format_row(start_row), off - 2, 2, '<H')
	(end_row, off) = rdata(data, off, '<H')
	add_iter(hd, 'End row', format_row(end_row), off - 2, 2, '<H')
	(start_column, off) = rdata(data, off, '<B')
	add_iter(hd, 'Start column', format_column(start_column), off - 1, 1, '<B')
	(end_column, off) = rdata(data, off, '<B')
	add_iter(hd, 'End column', format_column(end_column), off - 1, 1, '<B')

def add_formula_cell(hd, size, data, off):
	rel_map = {0: 'none', 1: 'column', 2: 'row', 3: 'row and column'}
	def add_address(off):
		(row, off) = rdata(data, off, '<H')
		add_iter(hd, 'Row', format_row(row & 0x3fff), off - 2, 2, '<H')
		rel = (row >> 14) & 0x3
		add_iter(hd, 'Relative', get_or_default(rel_map, rel, 'unknown'), off - 1, 1, '<B')
		(col, off) = rdata(data, off, '<B')
		add_iter(hd, 'Column', format_column(col), off - 1, 1, '<B')
		return off

	off = add_cell(hd, size, data, off)
	off += 0xe
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Length', length, off - 2, 2, '<H')
	opcode_map = {
		0x3: '+', 0x4: '-', 0x5: '*', 0x6: '/', # binary
		0x13: '-', 0x17: 'string', 0x19: 'something', 0x1d: 'bool', 0x1e: 'integer', 0x1f: 'double', # unary
		0x22: 'function with variable number of args', 0x24: 'address', 0x25: 'range',
		0x41: 'function with fixed number of args', 0x42: 'function with variable number of args',
		# TODO: what's the difference between 0x24 and 0x44?
		0x44: 'address',
		0x5a: 'sheet address',
	}
	while off < size:
		(opcode, off) = rdata(data, off, '<B')
		add_iter(hd, 'Opcode', get_or_default(opcode_map, opcode, 'unknown'), off - 1, 1, '<B')
		if opcode == 0x17:
			off = add_short_string(hd, size, data, off, 'Text')
		elif opcode == 0x19:
			off += 3
		elif opcode == 0x1d:
			(val, off) = rdata(data, off, '<B')
			add_iter(hd, 'Value', bool(val), off - 1, 1, '<B')
		elif opcode == 0x1e:
			(val, off) = rdata(data, off, '<h')
			add_iter(hd, 'Value', val, off - 2, 2, '<h')
		elif opcode == 0x1f:
			(val, off) = rdata(data, off, '<d')
			add_iter(hd, 'Value', val, off - 8, 8, '<d')
		elif opcode == 0x24:
			off = add_address(off)
		elif opcode == 0x25:
			(start_row, off) = rdata(data, off, '<H')
			add_iter(hd, 'Start row', format_row(start_row & 0x3fff), off - 2, 2, '<H')
			start_rel = (start_row >> 14) & 0x3
			add_iter(hd, 'First address relative', get_or_default(rel_map, start_rel, 'unknown'), off - 1, 1, '<B')
			(end_row, off) = rdata(data, off, '<H')
			add_iter(hd, 'End row', format_row(end_row & 0x3fff), off - 2, 2, '<H')
			end_rel = (end_row >> 14) & 0x3
			add_iter(hd, 'Second address relative', get_or_default(rel_map, end_rel, 'unknown'), off - 1, 1, '<B')
			(start_column, off) = rdata(data, off, '<B')
			add_iter(hd, 'Start column', format_column(start_column), off - 1, 1, '<B')
			(end_column, off) = rdata(data, off, '<B')
			add_iter(hd, 'End column', format_column(end_column), off - 1, 1, '<B')
		elif opcode == 0x41:
			(fname, off) = rdata(data, off, '<H')
			add_iter(hd, 'Function', get_or_default(WLS_FUNCTIONS_FIXED, fname, 'unknown'), off - 2, 2, '<H')
		elif opcode == 0x22 or opcode == 0x42:
			(argc, off) = rdata(data, off, '<B')
			add_iter(hd, 'Number of arguments', argc, off - 1, 1, '<B')
			(fname, off) = rdata(data, off, '<H')
			add_iter(hd, 'Function', get_or_default(WLS_FUNCTIONS_VAR, fname, 'unknown'), off - 2, 2, '<H')
		elif opcode == 0x44:
			off = add_address(off)
		elif opcode == 0x5a:
			off += 14
			off = add_address(off)

def convert_flags(flags, names):
	"""Convert a number representing a set of flags into names.

	The names dict maps a bit to a name. Bits are counted from 0.
	"""
	ret = []
	for b in xrange(0, sorted(names.keys())[-1] + 1):
		if flags & 0x1:
			if names.has_key(b):
				ret.append(names[b])
			else:
				ret.append('unknown')
		flags = flags >> 1
	if flags: # more flags than we have names for
		ret.append('unknowns')
	return ret

def print_flags(flags, names):
	return ' + '.join(convert_flags(flags, names))

def get_text_flags(flags):
	names = {
		1: 'italic',
		3: 'line through',
	}
	return print_flags(flags, names)

def add_text_attrs(hd, size, data, off):
	(size, off) = rdata(data, off, '<H')
	add_iter(hd, 'Font size', '%d pt' % (size / 20), off - 2, 2, '<H')
	(flags, off) = rdata(data, off, '<H')
	add_iter(hd, 'Flags?', get_text_flags(flags), off - 2, 2, '<H')
	(color, off) = rdata(data, off, '<H')
	if color == 0x7fff:
		color_str = "default"
	else:
		color_str = '%d' % color
	# I can see no record that'd look like a palette, though. Maybe it is implicit?
	add_iter(hd, 'Color index', color_str, off - 2, 2, '<H')
	font_weight_map = {400: 'normal', 700: 'bold'}
	(font_weight, off) = rdata(data, off, '<H')
	add_iter(hd, 'Font weight', get_or_default(font_weight_map, font_weight, 'unknown'), off - 2, 2, '<H')
	off += 2
	(underline, off) = rdata(data, off, '<B')
	add_iter(hd, 'Underline', bool(underline), off - 1, 1, '<B')
	(line_through, off) = rdata(data, off, '<B')
	add_iter(hd, 'Line-through?', line_through, off - 1, 1, '<B')
	off += 2
	add_short_string(hd, size, data, off, 'Font name')

def add_cell_style(hd, size, data, off):
	(attrs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Text attributes', attrs, off - 2, 2, '<H')
	off += 4
	halign_map = {0: 'generic', 1: 'left', 2: 'center', 3: 'right', 4: 'repeat', 5: 'paragraph', 6: 'selection center'}
	valign_map = {0: 'top', 1: 'center', 2: 'bottom', 3: 'paragraph'}
	(align, off) = rdata(data, off, '<B')
	add_iter(hd, 'Vertical alignment', get_or_default(valign_map, (align >> 4), 'unknown'), off - 1, 1, '<B')
	add_iter(hd, 'Wrap text', bool(align & 0x8), off - 1, 1, '<B')
	add_iter(hd, 'Horizontal alignment', get_or_default(halign_map, (align & 0x7), 'unknown'), off - 1, 1, '<B')
	orient_map = {0x10: 'horizontal', 0x12: 'vertical 90 degrees', 0x13: 'vertical 270 degrees'}
	(orient, off) = rdata(data, off, '<B')
	add_iter(hd, 'Text orientation?', get_or_default(orient_map, orient, 'unknown'), off - 1, 1, '<B')
	(color, off) = rdata(data, off, '<B')
	# TODO: verify this
	add_iter(hd, 'Color index', color - 0x80, off - 1, 1, '<B')
	(pattern, off) = rdata(data, off, '<B')
	add_iter(hd, 'Fill pattern?', pattern, off - 1, 1, '<B')
	off += 6 # border type and color, seems completely chaotic

wls_ids = {
	'record': record_wrapper(None),
	'text_attrs': record_wrapper(add_text_attrs),
	'cell_style': record_wrapper(add_cell_style),
	'column_width': record_wrapper(add_column_width),
	'formula_cell': record_wrapper(add_formula_cell),
	'named_range': record_wrapper(add_named_range),
	'number_cell': record_wrapper(add_number_cell),
	'page_setup': record_wrapper(add_page_setup),
	'page_header_footer': record_wrapper(add_page_header_footer),
	'row_height': record_wrapper(add_row_height),
	'sheet_count': record_wrapper(add_sheet_count),
	'sheet_def': record_wrapper(add_sheet_def),
	'text_cell': record_wrapper(add_text_cell),
	'tab': record_wrapper(add_tab),
}

def parse(page, data, parent):
	parser = wls_parser(page, data, parent)
	parser.parse()

if __name__ == '__main__':
	def test_deobfuscate(byte, pos, expected):
		got = deobfuscate([chr(byte)], pos)
		if got != [expected]:
			print("expected '%s' (%x), got %x" % (expected, ord(expected), ord(got[0])))
		assert(got == [expected])
	test_deobfuscate(0x5f, 6, '`')
	test_deobfuscate(0x60, 6, 'a')
	test_deobfuscate(0x5d, 6, 'b')
	test_deobfuscate(0x67, 6, 'h')
	test_deobfuscate(0x68, 6, 'i')
	test_deobfuscate(0x7f, 6, '@')
	test_deobfuscate(0x82, 6, 'O')

	test_deobfuscate(0x5f, 7, 'a')
	test_deobfuscate(0x68, 7, 'h')
	test_deobfuscate(0x67, 7, 'i')
	test_deobfuscate(0x7f, 7, 'A')

	test_deobfuscate(0xa9, 0x10, ' ')
	test_deobfuscate(0xb8, 0x10, '/')
	test_deobfuscate(0x99, 0x10, '0')
	test_deobfuscate(0xa8, 0x10, '?')
	test_deobfuscate(0x89, 0x10, '@')
	test_deobfuscate(0x98, 0x10, 'O')
	test_deobfuscate(0x79, 0x10, 'P')
	test_deobfuscate(0x88, 0x10, '_')
	test_deobfuscate(0x69, 0x10, '`')
	test_deobfuscate(0x78, 0x10, 'o')
	test_deobfuscate(0x59, 0x10, 'p')
	test_deobfuscate(0x66, 0x10, '}')

	test_deobfuscate(0x69, 0x11, 'a')
	test_deobfuscate(0x6c, 0x11, 'b')
	test_deobfuscate(0x72, 0x11, 'h')

	test_deobfuscate(0x97, 0x1e, '@')

	test_deobfuscate(0x39, 0x20, '`')
	test_deobfuscate(0x3a, 0x20, 'a')
	test_deobfuscate(0x3b, 0x20, 'b')
	test_deobfuscate(0x19, 0x20, '@')
	test_deobfuscate(0x1a, 0x20, 'A')

# vim: set ft=python ts=4 sw=4 noet:
