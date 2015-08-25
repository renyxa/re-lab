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

wt602_sections = (
	'Section 0',
	'Section 1',
	'Section 2',
	'Section 3',
	'Section 4',
	'Section 5',
	'Section 6',
	'Section 7',
	'Section 8',
	'Section 9',
	'Used fonts',
	'Section 11',
	'Section 12',
	'Section 13',
	'Section 14',
	'Section 15',
	'Headers & Footers', # Or is it? Adding a table adds this sectioni too. So does a frame.
	'Section 17',
	'Styles',
	'Section 19',
	'Section 20',
	'Fields',
	'Hard formats',
	'Section 23',
	'Section 24',
	'Text info',
	'Section 26',
	'Text',
	'Section 28',
	'Section 29',
	'Section 30',
	'Section 31',
	'Section 32',
	'Section 33',
	'Section 34',
	'Section 35',
	'Section 36',
)

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

wt602_section_handlers = (
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	(handle_fonts, 'fonts'),
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	(handle_styles, 'styles'),
	None,
	None,
	None,
	None,
	None,
	None,
	(handle_text_infos, 'text_infos'),
	None,
	(None, 'text'),
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
	None,
)

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class wt602_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

		self.sections = [(0, 0) for i in range(0, len(wt602_sections))]

	def parse(self):
		self.parse_header()
		self.parse_offset_table()
		for i in range(0, len(wt602_sections)):
			self.parse_section(i)

	def parse_header(self):
		add_pgiter(self.page, 'Header', 'wt602', 'header', self.data[0:0x72], self.parent)

	def parse_offset_table(self):
		offiter = add_pgiter(self.page, 'Offset table', 'wt602', 0,
				self.data[0x72:0x72 + 4 * len(wt602_sections)], self.parent)
		begin = 0
		end = 0
		idx = 0
		off = 0x72
		for i in range(0, len(wt602_sections)):
			add_pgiter(self.page, wt602_sections[i], 'wt602', 0, self.data[off:off + 4], offiter)
			(cur, off) = rdata(self.data, off, '<I')
			if cur != 0:
				end = cur
				if i != 0:
					self.sections[idx] = (begin + 0x72, end + 0x72)
				begin = cur
				idx = i

	def parse_section(self, n):
		(begin, end) = self.sections[n]
		name = wt602_sections[n]
		func = wt602_section_handlers[n]
		adder = 0
		if end > begin:
			handler = None
			if func != None:
				(handler, adder) = func
			sectiter = add_pgiter(self.page, name, 'wt602', adder, self.data[begin:end], self.parent)
			if handler != None:
				handler(self.page, self.data[begin:end], sectiter, self)

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
	names = {1: 'bold', 2: 'italic', 3: 'underline'}
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
	add_iter(hd, 'Format', '%s' % get_char_format(attribs), off - 2, 2, '<H')
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
	'font' : add_font,
	'fonts' : add_fonts,
	'header': add_header,
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
