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

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

WT602_SECTION_COUNT = 37
wt602_section_names = {
	10: 'Used fonts',
	16: 'Headers & Footers', # Or is it? Adding a table adds this sectioni too. So does a frame.
	19: 'Styles',
	21: 'Color table',
	22: 'Hard formats',
	26: 'Text info',
	27: 'Text',
}

def handle_fonts(page, data, parent, parser = None):
	(count, off) = rdata(data, 0, '<I')
	for i in range(0, count):
		start = off
		off += 2
		# read font name
		while off < len(data) and data[off] != '\0':
			off += 1
		# read zeros to the next record
		while off < len(data) and data[off] == '\0':
			off += 1
		add_pgiter(page, 'Font %d' % i, 'wt602', 'font', data[start:off], parent)

def handle_text_infos(page, data, parent, parser):
	(count, off) = rdata(data, 0, '<I')
	off += 6
	text_section = parser.sections[27]
	text = parser.data[text_section[0] + 4:text_section[1]]
	text_begin = 0
	for i in range(0, count):
		begin = off
		spaniter = add_pgiter(page, 'Span %d ' %i, 'wt602', 'text_info', data[begin:begin + 28], parent)
		text_length = read(data, begin + 0xe, '<H')
		if text_length > 0:
			add_pgiter(page, 'Text', 'wt602', 'span_text', text[text_begin:text_begin + text_length], spaniter)
			text_begin += text_length
		off += 28

def handle_styles(page, data, parent, parser = None):
	(hdrsize, off) = rdata(data, 0, '<I')
	count = hdrsize / 0x20
	off = 0x10
	hdriter = add_pgiter(page, 'Names', 'wt602', 0, data[:hdrsize + 0x10], parent)
	for i in range(0, count):
		add_pgiter(page, 'Style %d' % i, 'wt602', 'style_header', data[off:off + 0x20], hdriter)
		off += 0x20
	add_pgiter(page, 'Definitions', 'wt602', 0, data[hdrsize + 0x10:], parent)

def handle_colormap(page, data, parent, parser = None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, 'Color %d' % i, 'wt602', 'color', data[off:off + size], parent)
		off += size

wt602_section_handlers = {
	10: (handle_fonts, 'fonts'),
	19: (handle_styles, 'styles'),
	21: (handle_colormap, 'colormap'),
	26: (handle_text_infos, 'text_infos'),
	27: (None, 'text'),
}

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class wt602_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

		self.sections = []

	def parse(self):
		self.parse_header()
		self.parse_offset_table()
		for i in range(0, len(self.sections)):
			self.parse_section(i)

	def parse_header(self):
		add_pgiter(self.page, 'Header', 'wt602', 'header', self.data[0:0x72], self.parent)

	def parse_offset_table(self):
		offiter = add_pgiter(self.page, 'Offset table', 'wt602', 'offsets',
				self.data[0x72:0x72 + 4 * WT602_SECTION_COUNT], self.parent)
		offsets = [0x72]
		off = 0x72
		for i in range(0, WT602_SECTION_COUNT):
			(cur, off) = rdata(self.data, off, '<I')
			if cur == 0:
				offsets.append(offsets[-1])
			else:
				offsets.append(cur + 0x72)
		offsets.append(len(self.data))
		self.sections = zip(offsets[1:len(offsets) - 1], offsets[2:])

	def parse_section(self, n):
		(begin, end) = self.sections[n]
		name = get_or_default(wt602_section_names, n, 'Section %d' % n)
		func = get_or_default(wt602_section_handlers, n, None)
		adder = 0
		if end > begin:
			handler = None
			if func != None:
				(handler, adder) = func
			sectiter = add_pgiter(self.page, name, 'wt602', adder, self.data[begin:end], self.parent)
			if handler != None:
				handler(self.page, self.data[begin:end], sectiter, self)

def add_color(hd, size, data):
	(r, off) = rdata(data, 0, '<B')
	add_iter(hd, 'Red', r, off - 1, 1, '<B')
	(g, off) = rdata(data, off, '<B')
	add_iter(hd, 'Green', g, off - 1, 1, '<B')
	(b, off) = rdata(data, off, '<B')
	add_iter(hd, 'Blue', b, off - 1, 1, '<B')
	(a, off) = rdata(data, off, '<B')
	add_iter(hd, 'Alpha', a, off - 1, 1, '<B')

def add_colormap(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', c, off - 4, 4, '<I')
	(size, off) = rdata(data, off, '<H')
	add_iter(hd, 'Entry size?', size, off - 2, 2, '<H')

def add_font(hd, size, data):
	i = 2
	start = i
	while i < len(data) and data[i] != '\0':
		i += 1
	length = i - start
	add_iter(hd, 'Name', data[start:i], start, length, '<%ds' % length)

def add_fonts(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', c, 0, 4, '<I')

def add_header(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', c, 0, 4, '<I')

def add_offsets(hd, size, data):
	off = 0
	for i in range(0, WT602_SECTION_COUNT):
		(offset, off) = rdata(data, off, '<I')
		name = get_or_default(wt602_section_names, i, 'Section %d' % i)
		add_iter(hd, name, offset, off - 4, 4, '<I')

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

def get_char_format(flags):
	names = {
		0: 'font size',
		1: 'bold',
		2: 'italic',
		3: 'underline type',
		4: 'position',
		5: 'transform',
		6: 'color',
		7: 'font name',
		8: 'letter spacing',
		9: 'shaded',
		10: 'line-through type',
		11: 'outline',
	}
	return print_flags(flags, names)

def get_para_flags(flags):
	names = {3: 'page break', 8: 'paragraph break'}
	return print_flags(flags, names)

def add_text_info(hd, size, data):
	(flags, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Flags', '%x' % flags, off - 2, 2, '<H')
	off += 2
	(para_flags, off) = rdata(data, off, '<H')
	add_iter(hd, 'Text flags', '%s' % get_para_flags(para_flags), off - 2, 2, '<H')
	off += 6
	(attribs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Changed attributes', '%s' % get_char_format(attribs), off - 2, 2, '<H')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Length', length, off - 2, 2, '<H')

def add_text_infos(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, 0, 4, '<I')

def add_span_text(hd, size, data):
	fmt = '%ds' % len(data)
	text = read(data, 0, fmt)
	add_iter(hd, 'Text', text, 0, len(data), fmt)

def add_style_header(hd, size, data):
	(length, off) = rdata(data, 0x12, '<H')
	fmt = '<%ds' % length
	name = read(data, off, fmt)
	add_iter(hd, 'Name', name, off, length, fmt)

def add_styles(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', c / 0x20, 0, 4, '<I')

def add_text(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length', length, 0, 4, '<I')
	fmt = '<%ds' % length
	text = read(data[off:], 0, fmt)
	add_iter(hd, 'Text', text, off, length, fmt)

wt602_ids = {
	'color': add_color,
	'colormap': add_colormap,
	'font' : add_font,
	'fonts' : add_fonts,
	'header': add_header,
	'offsets': add_offsets,
	'span_text': add_span_text,
	'text_info': add_text_info,
	'text_infos': add_text_infos,
	'style_header': add_style_header,
	'styles': add_styles,
	'text': add_text,
}

def parse(page, data, parent):
	parser = wt602_parser(page, data, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
