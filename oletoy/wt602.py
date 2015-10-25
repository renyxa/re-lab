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

def values(d, default='unknown'):
	def lookup(val):
		return key2txt(val, d, default)
	return lookup

WT602_SECTION_COUNT = 37
wt602_section_names = {
	10: 'Used fonts',
	11: 'Tabs',
	16: 'Frames', # this includes tables and headers+footers
	19: 'Named styles',
	21: 'Color table',
	22: 'Character styles',
	23: 'Paragraph styles',
	24: 'Footnotes',
	25: 'List styles',
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
	add_pgiter(page, 'Header', 'wt602', '', data[2:off], parent)
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
	add_pgiter(page, 'Trailer', 'wt602', '', data[off:], parent)

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

def handle_char_styles(page, data, parent, parser = None):
	off = 8
	(count, off) = rdata(data, off, '<H')
	ids = []
	off = len(data) - 2 * count
	start_ids = off - 2
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		ids.append(id)
	off = 8
	fmt_size = 28
	start_styles = off + 2 + fmt_size * count
	attrsiter = add_pgiter(page, 'Attr. sets', 'wt602', 'container', data[off:start_styles], parent)
	off += 2
	for (n, id) in zip(range(0, count), ids):
		add_pgiter(page, 'Attr. set %d (ID: %d)' % (n, id), 'wt602', 'attrset', data[off:off + fmt_size], attrsiter)
		off += fmt_size
	assert(off == start_styles)
	descsiter = add_pgiter(page, 'Styles', 'wt602', 'container', data[off:start_ids], parent)
	off += 2
	n = 0
	while off < start_ids:
		add_pgiter(page, 'Style %d' % n, 'wt602', 'style', data[off:off + 6], descsiter)
		off += 6
		n += 1
	# assert(off == start_ids)
	add_pgiter(page, 'ID map', 'wt602', 'attrset_ids', data[start_ids:], parent)

def handle_para_styles(page, data, parent, parser = None):
	off = 8
	(count, off) = rdata(data, off, '<H')
	ids = []
	off = len(data) - 2 * count
	start_ids = off - 2
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		ids.append(id)
	off = 8
	fmt_size = 46
	start_styles = off + 2 + fmt_size * count
	attrsiter = add_pgiter(page, 'Attr. sets', 'wt602', 'container', data[off:start_styles], parent)
	off += 2
	for (n, id) in zip(range(0, count), ids):
		add_pgiter(page, 'Attr. set %d (ID: %d)' % (n, id), 'wt602', 'attrset_para', data[off:off + fmt_size], attrsiter)
		off += fmt_size
	assert(off == start_styles)
	descsiter = add_pgiter(page, 'Styles', 'wt602', 'container', data[off:start_ids], parent)
	off += 2
	n = 0
	while off < start_ids:
		add_pgiter(page, 'Style %d' % n, 'wt602', 'style_para', data[off:off + 6], descsiter)
		off += 6
		n += 1
	# assert(off == start_ids)
	add_pgiter(page, 'ID map', 'wt602', 'attrset_ids', data[start_ids:], parent)

def handle_tabs(page, data, parent, parser=None):
	off = 0
	(count, off) = rdata(data, off, '<H')
	tab_size = 16
	off += 8
	for i in range(0, count):
		add_pgiter(page, 'Tabs %d' % i, 'wt602', 'tabs_def', data[off:off + tab_size], parent)
		off += tab_size
	stops_iter = add_pgiter(page, 'Tab stops', 'wt602', 'container', data[off:], parent)
	(stops, off) = rdata(data, off, '<H')
	for i in range(0, stops):
		end = off + 4 * (i + 1)
		add_pgiter(page, 'Tab stops %d' % i, 'wt602', 'tab_stop', data[off:end], stops_iter)
		off = end

def handle_footnotes(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	entry_size = 24 # FIXME: a guess
	off += 8
	for i in range(0, count):
		add_pgiter(page, 'Footnote %d' % i, 'wt602', '', data[off:off + entry_size], parent)
		off += entry_size
	if off < len(data):
		add_pgiter(page, 'Trailer', 'wt602', '', data[off:], parent)

def handle_frames(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	entry_size = 204 # FIXME: a guess
	for i in range(0, count):
		add_pgiter(page, 'Frame %d' % i, 'wt602', 'frame', data[off:off + entry_size], parent)
		off += entry_size
	add_pgiter(page, 'Trailer', 'wt602', 'frame_trailer', data[off:], parent)

wt602_section_handlers = {
	10: (handle_fonts, 'fonts'),
	11: (handle_tabs, 'tabs'),
	16: (handle_frames, 'frames'),
	19: (handle_styles, 'styles'),
	21: (handle_colormap, 'colormap'),
	22: (handle_char_styles, 'char_styles'),
	23: (handle_para_styles, 'para_styles'),
	24: (handle_footnotes, 'footnotes'),
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
		name = key2txt(n, wt602_section_names, 'Section %d' % n)
		func = key2txt(n, wt602_section_handlers, None)
		adder = 0
		if end > begin:
			handler = None
			if func != None:
				(handler, adder) = func
			sectiter = add_pgiter(self.page, name, 'wt602', adder, self.data[begin:end], self.parent)
			if handler != None:
				handler(self.page, self.data[begin:end], sectiter, self)

def to_cm(val):
	return val / 20.0 * 0.353 / 10

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
		name = key2txt(i, wt602_section_names, 'Section %d' % i)
		add_iter(hd, name, offset, off - 4, 4, '<I')

def get_char_style(flags):
	names = {
		0x1: 'font size',
		0x2: 'bold',
		0x4: 'italic',
		0x8: 'underline type',
		0x10: 'position',
		0x20: 'transform',
		0x40: 'color',
		0x80: 'font',
		0x100: 'letter spacing',
		0x200: 'shaded',
		0x400: 'line-through type',
		0x800: 'outline',
	}
	return bflag2txt(flags, names)

line_map = {
	0: '1pt',
	1: 'hairline',
	2: '0.5pt', 3: '1pt', 4: '2pt', 5: '4pt', 6: '6pt', 7: '8pt', 8: '12pt',
	9: 'double', 10: 'double, inner thicker', 11: 'double, outer thicker'
}

def get_para_flags(flags):
	names = {0x8: 'page break', 0x100: 'paragraph break'}
	return bflag2txt(flags, names)

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
	add_iter(hd, 'Changed attributes', '%s' % get_char_style(attribs), off - 2, 2, '<H')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Length', length, off - 2, 2, '<H')

def add_text_infos(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Entries', count, 0, 4, '<I')
	off = size - 4
	(spans, off) = rdata(data, off, '<I')
	add_iter(hd, 'Span count', spans, off - 4, 4, '<I')

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
	(lang, off) = rdata(data, off, '<H')
	# MS lang ID, just a few useful entries here
	lang_map = values({0x0: 'default', 0x0405: 'cs-CZ', 0x0409: 'en-US', 0x0415: 'pl-PL', 0x0809: 'en-GB'})
	add_iter(hd, 'Language code', lang_map(lang), off - 2, 2, '<H')

def add_attrset_para(hd, size, data):
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
	(tabs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Tabs', tabs, off - 2, 2, '<H')
	(column_gap, off) = rdata(data, off, '<H')
	add_iter(hd, 'Column gap', '%.2fcm' % to_cm(column_gap), off - 2, 2, '<H')
	(columns, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of columns', columns, off - 2, 2, '<H')
	(top, off) = rdata(data, off, '<H')
	add_iter(hd, 'Top margin', '%.2fpt' % (top / 20.0), off - 2, 2, '<H')
	(bottom, off) = rdata(data, off, '<H')
	add_iter(hd, 'Bottom margin', '%.2fpt' % (bottom / 20.0), off - 2, 2, '<H')
	(shading, off) = rdata(data, off, '<H')
	shading_map = values({
		0: 'none', 5: 'vertical lines', 6: 'raster',
		12: '100%', 16: '50%', 18: '25%', 19: '0%'
	})
	add_iter(hd, 'Shading type', shading_map(shading), off - 2, 2, '<H')
	(border_line, off) = rdata(data, off, '<H')
	add_iter(hd, 'Border line', key2txt(border_line, line_map), off - 2, 2, '<H')
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
	off += 4
	(section_height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Section height', '%.2fcm' % to_cm(section_height), off - 2, 2, '<H')
	(section_inc, off) = rdata(data, off, '<H')
	add_iter(hd, 'Section increment', '%.2fcm' % to_cm(section_inc), off - 2, 2, '<H')
	off += 4
	(column_line, off) = rdata(data, off, '<H')
	add_iter(hd, 'Inter-column line', line_map(column_line), off - 2, 2, '<H')

def add_style(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Changed attributes', '%s' % get_char_style(attribs), off - 2, 2, '<H')
	off += 2
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set', attrset, off - 2, 2, '<H')

def add_style_para(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<H')
	# add_iter(hd, 'Changed attributes', '%s' % get_para_style(attribs), off - 2, 2, '<H')
	off += 2
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set', attrset, off - 2, 2, '<H')

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

def add_char_styles(hd, size, data):
	off = 6
	(style, off) = rdata(data, off, '<H')
	add_iter(hd, 'Active style?', style, off - 2, 2, '<H')

def add_para_styles(hd, size, data):
	off = 6
	(style, off) = rdata(data, off, '<H')
	add_iter(hd, 'Active style?', style, off - 2, 2, '<H')

def add_text(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length', length, 0, 4, '<I')
	fmt = '<%ds' % length
	text = read(data[off:], 0, fmt)
	add_iter(hd, 'Text', text, off, length, fmt)

def add_container(hd, size, data):
	(count, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Count', count, off - 2, 2, '<H')

def add_attrset_ids(hd, size, data):
	off = 0
	(count, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of attr. sets', count, off - 2, 2, '<H')
	n = 0
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		add_iter(hd, 'ID of attr. set %d' % n, id, off - 2, 2, '<H')
		n += 1

def add_tabs(hd, size, data):
	off = 0
	(count, off) = rdata(data, off, '<H') # or is it 4 bytes?
	add_iter(hd, 'Number of tabs', count, off - 2, 2, '<H')

def add_tabs_def(hd, size, data):
	off = 4
	(stops, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of stops?', stops, off - 2, 2, '<H')

def add_tab_stop(hd, size, data):
	i = 0
	off = 0
	while off < len(data):
		(skip, off) = rdata(data, off, '<H')
		add_iter(hd, 'Skip %d' % i, '%.2fcm' % to_cm(skip), off - 2, 2, '<H')
		(align, off) = rdata(data, off, '<B')
		align_map = values({0: 'left', 1: 'center', 2: 'right', 3: 'number'})
		add_iter(hd, 'Alignment %d' % i, align_map(align), off - 1, 1, '<B')
		(fill, off) = rdata(data, off, '<B')
		fill_map = values({0: 'none', ord('-'): 'dashes', ord('_'): 'underlines', ord('.'): 'dots'})
		add_iter(hd, 'Fill %d' % i, fill_map(fill), off - 1, 1, '<B')
		i += 1

def add_footnotes(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')

def add_frames(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')

def add_frame(hd, size, data):
	off = 0x20
	anchor_map = {
		0x0: 'fixed', 0x1: 'fixed on page',
		0x2: 'floating with paragraph', 0x3: 'floating with column',
		# 0xy: 'floating with character',
		0x4: 'repeated in document', 0x8: 'repeated in chapter',
	}
	anchor_flags = {0x10: 'resize with text', 0x40: 'lock size and position',}
	(anchor, off) = rdata(data, off, '<B')
	add_iter(hd, 'Anchor type', key2txt(anchor & 0xf, anchor_map), off - 1, 1, '<B')
	add_iter(hd, 'Flags', bflag2txt(anchor & 0xf0, anchor_flags), off - 1, 1, '<B')
	off += 3
	# extents
	(left, off) = rdata(data, off, '<I') # TODO: maybe it's <H?
	add_iter(hd, 'Left', '%.2f cm' % to_cm(left), off - 4, 4, '<I')
	(top, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top', '%.2f cm' % to_cm(top), off - 4, 4, '<I')
	(right, off) = rdata(data, off, '<I')
	add_iter(hd, 'Right', '%.2f cm' % to_cm(right), off - 4, 4, '<I')
	(bottom, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom', '%.2f cm' % to_cm(bottom), off - 4, 4, '<I')
	# extents with padding
	(left_padding, off) = rdata(data, off, '<I')
	add_iter(hd, 'Left with padding', '%.2f cm' % to_cm(left_padding), off - 4, 4, '<I')
	(top_padding, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top with padding', '%.2f cm' % to_cm(top_padding), off - 4, 4, '<I')
	(right_padding, off) = rdata(data, off, '<I')
	add_iter(hd, 'Right with padding', '%.2f cm' % to_cm(right_padding), off - 4, 4, '<I')
	(bottom_padding, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom with padding', '%.2f cm' % to_cm(bottom_padding), off - 4, 4, '<I')
	# borders
	(left_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Left border width', '%.2f cm' % to_cm(left_border), off - 4, 4, '<I')
	(top_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top border width', '%.2f cm' % to_cm(top_border), off - 4, 4, '<I')
	(right_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Right border width', '%.2f cm' % to_cm(right_border), off - 4, 4, '<I')
	(bottom_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom border width', '%.2f cm' % to_cm(bottom_border), off - 4, 4, '<I')
	off += 24
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Content height?', '%.2f cm' % to_cm(height), off - 4, 4, '<I')
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Content width?', '%.2f cm' % to_cm(width), off - 4, 4, '<I')
	off += 0x30
	wrap_map = {0: 'run-through', 1: 'none', 2: 'parallel'}
	(wrap, off) = rdata(data, off, '<B')
	add_iter(hd, 'Wrap', key2txt(wrap, wrap_map), off - 1, 1, '<B')
	off += 3
	(border_line, off) = rdata(data, off, '<B') # TODO: border line is probably only 1B; change elsewhere
	add_iter(hd, 'Border line', key2txt(border_line, line_map), off - 1, 1, '<B')
	off += 0x17
	(border_color, off) = rdata(data, off, '<B') # TODO: apparently color palette index is only 1B; change elsewhere
	add_iter(hd, 'Border color', border_color, off - 1, 1, '<B')
	(shading_color, off) = rdata(data, off, '<B')
	add_iter(hd, 'Shading color', shading_color, off - 1, 1, '<B')
	off += 2
	page_map = {0: 'first', 1: 'odd', 2: 'even', 3: 'all'}
	(page, off) = rdata(data, off, '<B')
	add_iter(hd, 'On page', key2txt(page & 0x3, page_map), off - 1, 1, '<B')
	add_iter(hd, 'Not on first', bool(page & 0x4), off - 1, 1, '<B')

def add_frame_trailer(hd, size, data):
	pass

def add_object_header(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')

wt602_ids = {
	'attrset': add_attrset,
	'attrset_para': add_attrset_para,
	'attrset_ids': add_attrset_ids,
	'char_styles': add_char_styles,
	'color': add_color,
	'colormap': add_colormap,
	'container': add_container,
	'font' : add_font,
	'fonts' : add_fonts,
	'footnotes' : add_footnotes,
	'frame': add_frame,
	'frame_trailer': add_frame_trailer,
	'frames': add_frame,
	'style': add_style,
	'style_para': add_style_para,
	'styles': add_styles,
	'header': add_header,
	'object_header': add_object_header,
	'offsets': add_offsets,
	'para_styles': add_para_styles,
	'span_text': add_span_text,
	'tab_stop': add_tab_stop,
	'tabs': add_tabs,
	'tabs_def': add_tabs_def,
	'text_info': add_text_info,
	'text_infos': add_text_infos,
	'style_header': add_style_header,
	'styles': add_styles,
	'text': add_text,
}

def parse(page, data, parent):
	parser = wt602_parser(page, data, parent)
	parser.parse()

def parse_object(page, data, parent):
	add_pgiter(page, 'Header', 'wt602', 'object_header', data[0:4], parent)
	add_pgiter(page, 'Content', 'wt602', '', data[4:], parent)

# vim: set ft=python ts=4 sw=4 noet:
