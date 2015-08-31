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

def values(d, default='unknown'):
	def lookup(val):
		return get_or_default(d, val, default)
	return lookup

WT602_SECTION_COUNT = 37
wt602_section_names = {
	10: 'Used fonts',
	16: 'Headers & Footers', # Or is it? Adding a table adds this sectioni too. So does a frame.
	19: 'Styles',
	21: 'Color table',
	22: 'Character formats',
	23: 'Paragraph formats',
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

def handle_char_formats(page, data, parent, parser = None):
	off = 8
	(count, off) = rdata(data, off, '<H')
	ids = []
	off = len(data) - 2 * count
	start_ids = off - 2
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		ids.append(id)
	off = 10
	fmt_size = 28
	attrsiter = add_pgiter(page, 'Attr. sets', 'wt602', '', data[off:off + fmt_size * count], parent)
	for (n, id) in zip(range(0, count), ids):
		add_pgiter(page, 'Attr. set %d (ID: %d)' % (n, id), 'wt602', 'attrset', data[off:off + fmt_size], attrsiter)
		off += fmt_size
	descsiter = add_pgiter(page, 'Formats', 'wt602', 'formats', data[off:start_ids], parent)
	off += 2
	n = 0
	while off < start_ids:
		add_pgiter(page, 'Format %d' % n, 'wt602', 'format', data[off:off + 6], descsiter)
		off += 6
		n += 1
	add_pgiter(page, 'ID map', 'wt602', 'attrset_ids', data[start_ids:], parent)

def handle_para_formats(page, data, parent, parser = None):
	off = 8
	(count, off) = rdata(data, off, '<H')
	ids = []
	off = len(data) - 2 * count
	start_ids = off - 2
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		ids.append(id)
	off = 10
	# FIXME: just a guess
	fmt_size = 30
	attrsiter = add_pgiter(page, 'Attr. sets', 'wt602', '', data[off:off + fmt_size * count], parent)
	for (n, id) in zip(range(0, count), ids):
		add_pgiter(page, 'Attr. set %d (ID: %d)' % (n, id), 'wt602', 'attrset_para', data[off:off + fmt_size], attrsiter)
		off += fmt_size
	descsiter = add_pgiter(page, 'Formats', 'wt602', 'formats', data[off:start_ids], parent)
	off += 2
	n = 0
	while off < start_ids:
		add_pgiter(page, 'Format %d' % n, 'wt602', 'format_para', data[off:off + 6], descsiter)
		off += 6
		n += 1
	add_pgiter(page, 'ID map', 'wt602', 'attrset_ids', data[start_ids:], parent)

wt602_section_handlers = {
	10: (handle_fonts, 'fonts'),
	19: (handle_styles, 'styles'),
	21: (handle_colormap, 'colormap'),
	22: (handle_char_formats, 'char_formats'),
	23: (handle_para_formats, 'para_formats'),
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
		7: 'font',
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
	off += 4
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set ID', attrset, off - 2, 2, '<H')
	(attribs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Changed attributes', '%s' % get_char_format(attribs), off - 2, 2, '<H')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Length', length, off - 2, 2, '<H')

def add_text_infos(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, 0, 4, '<I')

def add_attrset(hd, size, data):
	off = 0
	(font_size, off) = rdata(data, off, '<H')
	add_iter(hd, 'Font size', '%dpt' % font_size, off - 2, 2, '<H')
	(bold, off) = rdata(data, off, '<H')
	add_iter(hd, 'Bold', bool(bold), off - 2, 2, '<H')
	(italic, off) = rdata(data, off, '<H')
	add_iter(hd, 'Italic', bool(italic), off - 2, 2, '<H')
	(underline, off) = rdata(data, off, '<H')
	underline_map = values({0: 'none', 1: 'single', 2: 'words', 3: 'double'})
	add_iter(hd, 'Underline type', underline_map(underline), off - 2, 2, '<H')
	(position, off) = rdata(data, off, '<H')
	position_map = values({0: 'normal', 1: 'superscript', 2: 'subscript'})
	add_iter(hd, 'Position', position_map(position), off - 2, 2, '<H')
	(transform, off) = rdata(data, off, '<H')
	transform_map = values({0: 'none', 1: 'capitalize', 2: 'uppercase'})
	add_iter(hd, 'Transform', transform_map(transform), off - 2, 2, '<H')
	(color, off) = rdata(data, off, '<H')
	add_iter(hd, 'Color', color, off - 2, 2, '<H')
	(font, off) = rdata(data, off, '<H')
	add_iter(hd, 'Font', font, off - 2, 2, '<H')
	(spacing, off) = rdata(data, off, '<H')
	add_iter(hd, 'Letter spacing', '%d%%' % (100 + spacing), off - 2, 2, '<H')
	(shaded, off) = rdata(data, off, '<H')
	add_iter(hd, 'Shaded', bool(shaded), off - 2, 2, '<H')
	(line_through, off) = rdata(data, off, '<H')
	line_through_map = values({0: 'none', 1: 'single'})
	add_iter(hd, 'Line-through type', line_through_map(line_through), off - 2, 2, '<H')
	(outline, off) = rdata(data, off, '<H')
	outline_map = values({0: 'none', 1: 'outline', 2: 'embossed', 3: 'engraved'})
	add_iter(hd, 'Outline type', outline_map(outline), off - 2, 2, '<H')

def add_attrset_para(hd, size, data):
	def to_cm(val):
		return val / 20.0 * 0.353 / 10
	off = 0
	(alignment, off) = rdata(data, off, '<H')
	alignment_map = values({0: 'left', 1: 'center', 2: 'right', 3: 'justify'})
	add_iter(hd, 'Alignment', alignment_map(alignment), off - 2, 2, '<H')
	(left, off) = rdata(data, off, '<H')
	add_iter(hd, 'Left indent', '%.2fcm' % to_cm(left), off - 2, 2, '<H')
	(right, off) = rdata(data, off, '<H')
	add_iter(hd, 'Right indent', '%.2fcm' % to_cm(right), off - 2, 2, '<H')
	(first_line, off) = rdata(data, off, '<H')
	add_iter(hd, 'First line indent', '%.2fcm' % to_cm(first_line), off - 2, 2, '<H')
	off += 6
	(top, off) = rdata(data, off, '<H')
	add_iter(hd, 'Top margin', '%.2fpt' % (top / 20.0), off - 2, 2, '<H')
	(bottom, off) = rdata(data, off, '<H')
	add_iter(hd, 'Bottom margin', '%.2fpt' % (bottom / 20.0), off - 2, 2, '<H')
	off += 2
	(border_width, off) = rdata(data, off, '<H')
	border_width_map = values({
		0: '1pt',
		1: 'hairline',
		2: '0.5pt', 3: '1pt', 4: '2pt', 5: '4pt', 6: '6pt', 7: '8pt', 8: '12pt',
		9: 'double', 10: 'double, inner 2x', 11: 'double, outer 2x'
	})
	add_iter(hd, 'Border width', border_width_map(border_width), off - 2, 2, '<H')
	(border, off) = rdata(data, off, '<H')
	# TODO: complete
	border_map = values({
		0: 'none', 1: 'all', 2: 'top', 3: 'bottom', 4: 'top + bottom',
		5: 'left', 6: 'right', 7: 'left + right', 8: 'top + left'
	})
	add_iter(hd, 'Border type', border_map(border), off - 2, 2, '<H')
	off += 4
	(line_height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Line height', '%d%%' % line_height, off - 2, 2, '<H')

def add_format(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Changed attributes', '%s' % get_char_format(attribs), off - 2, 2, '<H')
	off += 2
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set', attrset, off - 2, 2, '<H')

def add_format_para(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<H')
	# add_iter(hd, 'Changed attributes', '%s' % get_para_format(attribs), off - 2, 2, '<H')
	off += 2
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set', attrset, off - 2, 2, '<H')

def add_formats(hd, size, data):
	(count, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Number of formats', count, off - 2, 2, '<H')

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

def add_char_formats(hd, size, data):
	off = 6
	(style, off) = rdata(data, off, '<H')
	add_iter(hd, 'Active format?', style, off - 2, 2, '<H')
	(count, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of formats', count, off - 2, 2, '<H')

def add_para_formats(hd, size, data):
	off = 6
	(style, off) = rdata(data, off, '<H')
	add_iter(hd, 'Active format?', style, off - 2, 2, '<H')
	(count, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of formats', count, off - 2, 2, '<H')

def add_text(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length', length, 0, 4, '<I')
	fmt = '<%ds' % length
	text = read(data[off:], 0, fmt)
	add_iter(hd, 'Text', text, off, length, fmt)

def add_attrset_ids(hd, size, data):
	off = 0
	(count, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of attr. sets', count, off - 2, 2, '<H')
	n = 0
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		add_iter(hd, 'ID of attr. set %d' % n, id, off - 2, 2, '<H')
		n += 1

wt602_ids = {
	'attrset': add_attrset,
	'attrset_para': add_attrset_para,
	'attrset_ids': add_attrset_ids,
	'char_formats': add_char_formats,
	'color': add_color,
	'colormap': add_colormap,
	'font' : add_font,
	'fonts' : add_fonts,
	'format': add_format,
	'format_para': add_format_para,
	'formats': add_formats,
	'header': add_header,
	'offsets': add_offsets,
	'para_formats': add_para_formats,
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
