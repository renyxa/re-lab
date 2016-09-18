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

def id2txt(value):
	assert value < 0xffff
	return '0x%x' % value

def ref2txt(value):
	if value == 0xffff:
		return 'none'
	else:
		return '0x%x' % value

def index2txt(value):
	if value == 0xffff:
		return 'none'
	else:
		return '%d' % value

def off2txt(value):
	if value == 0xffffffff:
		return 'none'
	else:
		return '%d' % value

wt602_section_names = {
	10: 'Used fonts',
	11: 'Tabs',
	12: 'ToC?',
	14: 'Index content',
	16: 'Frames', # this includes tables and headers+footers
	18: 'Strings',
	19: 'Index',
	20: 'Color table',
	21: 'Fields',
	22: 'Character styles',
	23: 'Paragraph styles',
	24: 'Text flows',
	25: 'Text info',
	26: 'List styles',
	27: 'Text',
	33: 'Changes',
}

def handle_text_infos(page, data, parent, parser):
	(count, off) = rdata(data, 0, '<I')
	if count == 0:
		return
	(size, off) = rdata(data, off, '<I')
	off += 2
	start = off

	# read the linked list
	offsets = []
	text_lengths = []
	for i in range(0, count):
		next = off + size
		(link, off) = rdata(data, off, '<i')
		offsets.append(link / size)
		off += 10
		(tl, off) = rdata(data, off, '<H')
		text_lengths.append(tl)
		off = next
	off += 8
	(last, off) = rdata(data, off, '<I')

	# determine the actual position and text range of each entry
	positions = [None for i in range(count)]
	texts = [(0, 0) for i in range(count)]
	pos = 0
	text_pos = text_lengths[pos]
	positions[pos] = 1
	texts[pos] = (0, text_lengths[pos])
	for i in range(1, count):
		pos += offsets[pos]
		if positions[pos]:
			break
		positions[pos] = i + 1
		text_start = text_pos
		text_pos += text_lengths[pos]
		texts[pos] = (text_start, text_pos)
		if pos == last:
			break

	# add entries
	text_section = parser.sections[27]
	text_data = parser.data[text_section[0] + 4:text_section[1]]
	off = start
	for i in range(0, count):
		pos = ''
		if positions[i]:
			mark_last = ''
			if i == last:
				mark_last = '*'
			pos = ' (%d%s)' % (positions[i], mark_last)
		text = ''
		length = texts[i][1] - texts[i][0]
		if length > 0:
			maxlen = 10
			end = texts[i][0] + min(length, maxlen)
			text = ' "%s"' % text_data[texts[i][0]:end]
			if length > maxlen:
				text += '...'
		add_pgiter(page, 'Info %d%s%s' % (i, pos, text), 'wt602', 'text_info', data[off:off + size], parent)
		off += size

def handle_strings(page, data, parent, parser = None):
	# NOTE: This seems to be a serialized hash map.
	add_pgiter(page, 'Header', 'wt602', 'string_header', data[:0x10], parent)
	(datasize, off) = rdata(data, 0, '<I')
	off = 0x10
	dataiter = add_pgiter(page, 'Data', 'wt602', 0, data[off:datasize + 0x10], parent)
	i = 0
	while off < datasize + 0x10:
		start = off
		(length, off) = rdata(data, off + 4, '<H')
		off = start + length
		add_pgiter(page, 'String %d' % i, 'wt602', 'string_entry', data[start:off], dataiter)
		i += 1
	add_pgiter(page, 'Hash map', 'wt602', 'string_map', data[off:], parent)

def handle_colormap(page, data, parent, parser = None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, 'Color %d' % i, 'wt602', 'color', data[off:off + size], parent)
		off += size

def _handle_styles(page, data, parent, parser, attrset_id, attrset_size, style_id):
	off = 8
	(count, off) = rdata(data, off, '<H')
	ids = []
	off = len(data) - 2 * count
	start_ids = off - 2
	while off < len(data):
		(id, off) = rdata(data, off, '<H')
		ids.append(id)
	off = 8
	start_styles = off + 2 + attrset_size * count
	attrsiter = add_pgiter(page, 'Attr. sets', 'wt602', 'container', data[off:start_styles], parent)
	off += 2
	for (n, id) in zip(range(0, count), ids):
		add_pgiter(page, 'Attr. set %d (ID: %s)' % (n, id2txt(id)), 'wt602', attrset_id, data[off:off + attrset_size], attrsiter)
		off += attrset_size
	assert(off == start_styles)
	descsiter = add_pgiter(page, 'Styles', 'wt602', 'container', data[off:start_ids], parent)
	off += 2
	n = 0
	while off < start_ids:
		add_pgiter(page, 'Style %d' % n, 'wt602', style_id, data[off:off + 6], descsiter)
		off += 6
		n += 1
	# assert(off == start_ids)
	add_pgiter(page, 'ID map', 'wt602', 'attrset_ids', data[start_ids:], parent)

def handle_char_styles(page, data, parent, parser = None):
	_handle_styles(page, data, parent, parser, 'attrset', 28, 'style')

def handle_para_styles(page, data, parent, parser = None):
	_handle_styles(page, data, parent, parser, 'attrset_para', 46, 'style_para')

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

def handle_text_flows(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(entry_size, off) = rdata(data, off, '<H')
	off += 6
	for i in range(0, count):
		add_pgiter(page, 'Flow %d' % i, 'wt602', 'text_flow', data[off:off + entry_size], parent)
		off += entry_size
	if off < len(data):
		add_pgiter(page, 'Trailer', 'wt602', '', data[off:], parent)

def handle_frames(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	entry_size = 204
	defiter = add_pgiter(page, 'Definitions', 'wt602', '', data[off:off + count * entry_size], parent)
	datalens = []
	for i in range(0, count):
		add_pgiter(page, 'Frame %d' % i, 'wt602', 'frame', data[off:off + entry_size], defiter)
		(datalen, off) = rdata(data, off, '<I') # TODO: maybe only <H?
		datalens.append(datalen)
		off += entry_size - 4
	dataiter = add_pgiter(page, 'Data', 'wt602', '', data[off:], parent)
	for i in range(0, count):
		end = off + datalens[i] + 4
		add_pgiter(page, 'Data %d' % i, 'wt602', 'frame_data', data[off:end], dataiter)
		off = end

def handle_index(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, 'Index entry %d' % i, 'wt602', 'index_entry', data[off:off + size], parent)
		off += size

def handle_index_content(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, 'Entry %d' % i, 'wt602', 'index_content_entry', data[off:off + size], parent)
		off += size

def handle_changes(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, 'Change %d' % i, 'wt602', 'change', data[off:off + size], parent)
		off += size

def handle_fields(page, data, parent, parser=None):
	off = 0x10
	i = 0
	while off < len(data):
		start = off
		(size, off) = rdata(data, off + 4, '<I')
		add_pgiter(page, 'Field %d' % i, 'wt602', 'field', data[start:start + size], parent)
		off = start + size
		i += 1

wt602_section_handlers = {
	10: (None, 'fonts'),
	11: (handle_tabs, 'tabs'),
	14: (handle_index_content, 'index'),
	16: (handle_frames, 'frames'),
	18: (handle_strings, 'strings'),
	19: (handle_index, 'index'),
	20: (handle_colormap, 'colormap'),
	21: (handle_fields, 'fields'),
	22: (handle_char_styles, 'styles'),
	23: (handle_para_styles, 'styles'),
	24: (handle_text_flows, 'text_flows'),
	25: (handle_text_infos, 'text_infos'),
	27: (None, 'text'),
	33: (handle_changes, 'changes'),
}

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class wt602_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

		self.header_len = 0x72
		self.sections = []

	def parse(self):
		self.parse_header()
		self.parse_offset_table()
		for i in range(0, len(self.sections)):
			self.parse_section(i)

	def parse_header(self):
		add_pgiter(self.page, 'Header', 'wt602', 'header', self.data[0:self.header_len], self.parent)

	def parse_offset_table(self):
		off = self.header_len - 4
		(table_size, off) = rdata(self.data, off, '<I')
		start = off
		offiter = add_pgiter(self.page, 'Offset table', 'wt602', 'offsets',
				self.data[start:start + table_size], self.parent)
		offsets = []
		for i in range(0, table_size / 4):
			(cur, off) = rdata(self.data, off, '<I')
			if cur < start:
				offsets.append(0)
			else:
				offsets.append(cur + start)
		offsets.append(len(self.data))
		for i in reversed(range(0, len(offsets))):
			if offsets[i] == 0:
				offsets[i] = offsets[i + 1]
		self.sections = zip(offsets[0:len(offsets) - 1], offsets[1:])

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

def add_fonts(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', c, 0, 4, '<I')
	i = 0
	while i < c:
		off += 2
		(name, off) = rdata(data, off, '32s')
		add_iter(hd, 'Name %d' % i, name[0:name.find('\0')], off - 32, 32, '32s')
		i += 1

def add_header(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Header size', c, 0, 4, '<I')
	off += 0x6a
	(size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset table size', size, off - 4, 4, '<I')

def add_offsets(hd, size, data):
	off = 0
	i = 0
	while off + 4 <= size:
		(offset, off) = rdata(data, off, '<I')
		name = key2txt(i, wt602_section_names, 'Section %d' % i)
		add_iter(hd, name, offset, off - 4, 4, '<I')
		i += 1

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

def add_string(hd, size, data, off, name, fmt):
	fmtlen = struct.calcsize(fmt)
	(length, off) = rdata(data, off, fmt)
	add_iter(hd, '%s length' % name, length, off - fmtlen, fmtlen, fmt)
	(text, off) = rdata(data, off, '%ds' % length)
	add_iter(hd, name, unicode(text, 'cp1250'), off - length, length, '%ds' % length)
	return off

def add_long_string(hd, size, data, off, name):
	return add_string(hd, size, data, off, name, '<H')

def add_text_info(hd, size, data):
	(next, off) = rdata(data, 0, '<i')
	add_iter(hd, 'Offset to next', next, off - 4, 4, '<i')
	flag_map = {0x8: 'start flow', 0x20: 'index mark start/stop?', 0x100: 'paragraph break'}
	flag_index = {0x8: 'Flow', 0x20: 'Index'}
	(flags, off) = rdata(data, off, '<H')
	add_iter(hd, 'Flags', '%s' % bflag2txt(flags, flag_map), off - 2, 2, '<H')
	change_flag_map = {0x20: 'delete', 0x40: 'insert'}
	(change_flags, off) = rdata(data, off, '<H')
	add_iter(hd, 'Change flags?', '%s' % bflag2txt(change_flags, change_flag_map), off - 2, 2, '<H')
	(index, off) = rdata(data, off, '<H')
	index_names = [v for (k, v) in flag_index.iteritems() if k & flags != 0]
	assert len(index_names) <= 1
	if len(index_names) == 0:
		index_str = 'Index'
	else:
		index_str = '%s index' % index_names[0]
	add_iter(hd, index_str, index2txt(index), off - 2, 2, '<H')
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set ref', ref2txt(attrset), off - 2, 2, '<H')
	(attribs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Changed attributes', '%s' % get_char_style(attribs), off - 2, 2, '<H')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Length', length, off - 2, 2, '<H')
	(seqno, off) = rdata(data, off, '<I')
	add_iter(hd, 'Seq. number?', seqno, off - 4, 4, '<I')

def add_text_infos(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Entries', count, 0, 4, '<I')
	(sz, off) = rdata(data, off, '<I')
	add_iter(hd, 'Entry size', sz, off - 4, 4, '<I')
	off = size - 8
	(first, off) = rdata(data, off, '<I')
	add_iter(hd, 'First entry?', first, off - 4, 4, '<I')
	(last, off) = rdata(data, off, '<I')
	add_iter(hd, 'Last entry', last, off - 4, 4, '<I')

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
	add_iter(hd, 'Inter-column line', key2txt(column_line, line_map), off - 2, 2, '<H')

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

def add_string_header(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length of data', length, off - 4, 4, '<I')
	(last, off) = rdata(data, off, '<I')
	add_iter(hd, 'Last entry length', last, off - 4, 4, '<I')

def add_string_entry(hd, size, data):
	flags_map = {0x70: 'Used', 0xa0: 'Unused'}
	(flags, off) = rdata(data, 0, '<B')
	add_iter(hd, 'Flags?', key2txt(flags, flags_map), off - 1, 1, '<B')
	off += 3
	(length, off) = rdata(data, off, '<I')
	add_iter(hd, 'Entry length', length, off - 4, 4, '<I')
	(plength, off) = rdata(data, off, '<I')
	if flags == 0xa0:
		plength -= 0x10000000
	add_iter(hd, 'Preceding entry length', plength, off - 4, 4, '<I')
	if flags == 0x70:
		off += 6
		off = add_long_string(hd, size, data, off, 'String')
		add_iter(hd, 'Padding', '', off, size, '%ds' % (size - off))

def add_string_map(hd, size, data):
	off = 0
	i = 0
	while off + 4 <= size:
		(offset, off) = rdata(data, off, '<I')
		if offset != 0xffffffff:
			add_iter(hd, 'Offset for hash %d' % i, offset, off - 4, 4, '<I')
		i += 1

def add_styles(hd, size, data):
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
		add_iter(hd, 'ID of attr. set %d' % n, id2txt(id), off - 2, 2, '<H')
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

def add_text_flows(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Entry length', length, off - 2, 2, '<H')

def add_text_flow(hd, size, data):
	off = 2
	(index, off) = rdata(data, off, '<I') # TODO: or <H?
	add_iter(hd, 'Start index', index, off - 4, 4, '<I')

def add_frames(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')

def add_frame(hd, size, data):
	off = 0xc
	(sid, off) = rdata(data, off, '<H')
	add_iter(hd, 'Shape ID', id2txt(sid), off - 2, 2, '<H')
	kind_map = {0x8: 'text', 0xb: 'image', 0xd: 'table', 0xe: 'group', 0xf: 'form control', 0x11: 'shape'}
	(kind, off) = rdata(data, off, '<B')
	add_iter(hd, 'Kind', key2txt(kind, kind_map), off - 1, 1, '<B')
	off += 5
	(above, off) = rdata(data, off, '<H')
	add_iter(hd, 'Is above', ref2txt(above), off - 2, 2, '<H')
	(below, off) = rdata(data, off, '<H')
	add_iter(hd, 'Is below', ref2txt(below), off - 2, 2, '<H')
	off += 8
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
	add_iter(hd, 'Left text frame margin', '%.2f cm' % to_cm(left_border), off - 4, 4, '<I')
	(top_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top text frame margin', '%.2f cm' % to_cm(top_border), off - 4, 4, '<I')
	(right_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Right text frame margin', '%.2f cm' % to_cm(right_border), off - 4, 4, '<I')
	(bottom_border, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom text frame margin', '%.2f cm' % to_cm(bottom_border), off - 4, 4, '<I')
	off += 24
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Text frame height', '%.2f cm' % to_cm(height), off - 4, 4, '<I')
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Text frame width', '%.2f cm' % to_cm(width), off - 4, 4, '<I')
	off += 0x30
	wrap_map = {0: 'run-through', 1: 'none', 2: 'parallel'}
	(wrap, off) = rdata(data, off, '<B')
	add_iter(hd, 'Wrap', key2txt(wrap, wrap_map), off - 1, 1, '<B')
	off += 3
	(border_line, off) = rdata(data, off, '<B') # TODO: border line is probably only 1B; change elsewhere
	add_iter(hd, 'Border line', key2txt(border_line, line_map), off - 1, 1, '<B')
	off += 0x13
	(group, off) = rdata(data, off, '<H')
	add_iter(hd, 'Group', key2txt(group & 1, {0: 'none'}, group & 0xfe), off - 2, 2, '<H')
	off += 2
	(border_color, off) = rdata(data, off, '<B') # TODO: apparently color palette index is only 1B; change elsewhere
	add_iter(hd, 'Border color', border_color, off - 1, 1, '<B')
	(shading_color, off) = rdata(data, off, '<B')
	add_iter(hd, 'Shading color', shading_color, off - 1, 1, '<B')
	off += 2
	page_map = {0: 'first', 1: 'odd', 2: 'even', 3: 'all'}
	(page, off) = rdata(data, off, '<B')
	add_iter(hd, 'On page', key2txt(page & 0x3, page_map), off - 1, 1, '<B')
	add_iter(hd, 'Not on first', bool(page & 0x4), off - 1, 1, '<B')

def add_frame_data(hd, size, data):
	off = 4
	type_map = {
		0x1: 'rectangle',
		0x14: 'line',
		0xba: 'compound brackets',
	}
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Shape type', key2txt(typ, type_map), off - 2, 2, '<H')
	off += 6
	(tagslen, off) = rdata(data, off, '<H')
	add_iter(hd, 'Length of tag list', tagslen, off - 2, 2, '<H')
	end = off + tagslen
	assert end <= size
	tag_map = {
	}
	while off < end:
		off += 2
		(tag, off) = rdata(data, off, '<B')
		add_iter(hd, 'Tag', key2txt(tag, tag_map), off - 1, 1, '<B')
		off += 3

def add_object_header(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')

def add_index(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Entries', count, 0, 4, '<I')
	(sz, off) = rdata(data, off, '<H')
	add_iter(hd, 'Entry size', sz, off - 2, 2, '<H')

def add_index_content_entry(hd, size, data):
	off = 12
	(offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of name', offset, off - 4, 4, '<I') # in strings data
	off += 12
	(eid, off) = rdata(data, off, '<H')
	add_iter(hd, 'ID', eid, off - 2, 2, '<H')

def add_index_entry(hd, size, data):
	(prev, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Preceded by', ref2txt(prev), off - 2, 2, '<H')
	(next, off) = rdata(data, off, '<H')
	add_iter(hd, 'Followed by', ref2txt(next), off - 2, 2, '<H')
	off += 4
	(eid, off) = rdata(data, off, '<H')
	add_iter(hd, 'Entry ref', ref2txt(eid), off - 2, 2, '<H')

def add_change(hd, size, data):
	off = 0x14
	(offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Comment string offset', off2txt(offset), off - 4, 4, '<I')

def add_changes(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Changes', count, 0, 4, '<I')
	(sz, off) = rdata(data, off, '<H')
	add_iter(hd, 'Record size', sz, off - 2, 2, '<H')

def add_fields(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length', length, off - 4, 4, '<I')
	(last, off) = rdata(data, off, '<I')
	add_iter(hd, 'Last field length?', last, off - 4, 4, '<I')

def add_field(hd, size, data):
	type_map = {
		# gap
		0x3: 'Footnote mark',
		0x4: 'Page number',
		0x5: 'Chapter number',
		0x6: 'Time',
		0x7: 'Date',
		0x8: 'Print time',
		0x9: 'Print date',
		0xa: 'Title',
		0xb: 'Topic',
		0xc: 'Author',
		0xd: 'Keywords',
		0xe: 'Comment',
		0xf: 'Template name',
		0x10: 'Application name',
		0x11: 'Footnote ref?',
		0x12: 'File name',
		0x13: 'Column sum',
		0x14: 'Row sum',
		0x15: 'HTML tag',
		0x16: 'HTML entity',
		0x17: 'Link',
		0x18: 'Comment/note',
		0x19: 'Symbol',
		0x1a: 'AutoText',
		# gap
		0x1d: 'Name',
		0x1e: 'Next record',
		0x1f: 'Form text',
		0x20: 'Form checkbox',
		0x21: 'Form list',
		0x22: 'Page count',
		0x23: 'Page number/count',
	}
	(typ, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 4, 4, '<I')
	(length, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length', length, off - 4, 4, '<I')
	(prev, off) = rdata(data, off, '<I')
	add_iter(hd, 'Prev. field length?', prev, off - 4, 4, '<I')

	# parse type-specific content
	if typ == 0x3:
		off += 12
		(mark, off) = rdata(data, off, '<I')
		add_iter(hd, 'Mark string offset', mark, off - 4, 4, '<I')
		(number, off) = rdata(data, off, '<I')
		add_iter(hd, 'Mark number?', number, off - 4, 4, '<I')
	elif typ == 0x15:
		off += 4
		(tag, off) = rdata(data, off, '<I')
		add_iter(hd, 'Tag string offset', tag, off - 4, 4, '<I')
	elif typ == 0x16:
		off += 4
		(entity, off) = rdata(data, off, '<I')
		add_iter(hd, 'Entity string offset', entity, off - 4, 4, '<I')
	elif typ == 0x17:
		off += 4
		(title, off) = rdata(data, off, '<I')
		add_iter(hd, 'Title string offset', title, off - 4, 4, '<I')
		(url, off) = rdata(data, off, '<I')
		add_iter(hd, 'URL string offset', url, off - 4, 4, '<I')
		(attrs, off) = rdata(data, off, '<I')
		add_iter(hd, 'Attributes string offset', attrs, off - 4, 4, '<I')
	elif typ == 0x18:
		(text, off) = rdata(data, off, '<I')
		add_iter(hd, 'Text string offset', text, off - 4, 4, '<I')
		(comment, off) = rdata(data, off, '<I')
		add_iter(hd, 'Comment string offset', comment, off - 4, 4, '<I')
	elif typ == 0x19:
		off += 8
		(char, off) = rdata(data, off, '<H')
		add_iter(hd, 'Character', char, off - 2, 2, '<H')
		script_map = {0: 'Western', 2: 'Cyrillic', 3: 'Central European', 4: 'Baltic', 5: 'Greek', 6: 'Turkish'}
		(script, off) = rdata(data, off, '<H')
		add_iter(hd, 'Script', key2txt(script, script_map), off - 2, 2, '<H')
	elif typ == 0x1a:
		(name, off) = rdata(data, off, '<I')
		add_iter(hd, 'Name string offset', name, off - 4, 4, '<I')
		(content, off) = rdata(data, off, '<I')
		add_iter(hd, 'Content string offset', content, off - 4, 4, '<I')

wt602_ids = {
	'attrset': add_attrset,
	'attrset_para': add_attrset_para,
	'attrset_ids': add_attrset_ids,
	'change': add_change,
	'changes': add_changes,
	'color': add_color,
	'colormap': add_colormap,
	'container': add_container,
	'field' : add_field,
	'fields' : add_fields,
	'fonts' : add_fonts,
	'frame': add_frame,
	'frame_data': add_frame_data,
	'frames': add_frames,
	'index': add_index,
	'index_content_entry': add_index_content_entry,
	'index_entry': add_index_entry,
	'style': add_style,
	'style_para': add_style_para,
	'header': add_header,
	'object_header': add_object_header,
	'offsets': add_offsets,
	'tab_stop': add_tab_stop,
	'tabs': add_tabs,
	'tabs_def': add_tabs_def,
	'text_flow': add_text_flow,
	'text_flows': add_text_flows,
	'text_info': add_text_info,
	'text_infos': add_text_infos,
	'string_entry': add_string_entry,
	'string_header': add_string_header,
	'string_map': add_string_map,
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
