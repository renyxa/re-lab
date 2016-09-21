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

from utils import add_iter, add_pgiter, bflag2txt, d2hex, key2txt, rdata

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

def off2txt(value, hd):
	if value == 0xffffffff:
		return 'none'
	else:
		if hd:
			return '%d (%s)' % (value, key2txt(value, hd.context.strings, ''))
		else:
			return '%d' % value

def preview(text):
	maxlen = 10
	result = '"%s"' % text[0:min(len(text), maxlen)]
	if len(text) > maxlen:
		result += '...'
	return result

wt602_section_names = {
	# gap
	6: 'View settings?',
	# gap
	8: 'Footnotes?',
	# gap
	10: 'Used fonts',
	11: 'Tabs',
	12: 'Named styles',
	13: 'Chapters',
	14: 'Index',
	# gap
	16: 'Frames', # this includes tables and headers+footers
	# gap
	18: 'Strings',
	19: 'Blocks',
	20: 'Color table',
	21: 'Fields',
	22: 'Character styles',
	23: 'Paragraph styles',
	24: 'Text flows',
	25: 'Text info',
	26: 'Numberings',
	27: 'Text',
	28: 'HTML properties',
	# gap
	31: 'Section styles',
	32: 'Data source',
	33: 'Changes',
	# gap
}

frame_kind_map = {
	# gap
	0x8: 'Text',
	# gap
	0xb: 'Image',
	# gap
	0xd: 'Table',
	0xe: 'Group',
	0xf: 'Form control',
	0x10: 'Barcode',
	0x11: 'Shape',
}

form_control_map = {
	1: 'Checkbox',
	2: 'Radio',
	3: 'Submit',
	4: 'Reset',
	5: 'Text',
	6: 'Textarea',
	7: 'Select',
	8: 'Password',
	9: 'Hidden',
}

shape_map = {
	0x1: 'Rectangle',
	0x2: 'Rounded rectangle',
	0x3: 'Ellipse',
	0x4: 'Rhombus',
	0x5: 'Triangle',
	0x6: 'Right triangle',
	0x7: 'Rhomboid',
	0x8: 'Trapezoid',
	0x9: 'Hexagon',
	0xa: 'Octagon',
	0xb: 'Cross',
	0xc: 'Five-pointed star',
	0xd: 'Right arrow',
	# gap
	0xf: 'Pentagonal arrow',
	# gap
	0x10: 'Cube',
	# gap
	0x13: 'Arc',
	0x14: 'Line',
	0x15: 'Plaque',
	0x16: 'Can',
	0x17: 'Ring',
	# gap
	0x35: 'Ribbon down',
	0x36: 'Ribbon up',
	0x37: 'Double arrow',
	0x38: 'Pentagon',
	0x39: 'Prohibition',
	0x3a: 'Eight-pointed star',
	0x3b: '16-pointed star',
	0x3c: '32-pointed star',
	# gap
	0x40: 'Wave',
	0x41: 'Folded corner',
	0x42: 'Left arrow',
	0x43: 'Down arrow',
	0x44: 'Up arrow',
	0x45: 'Bidir. horiz. arrow',
	0x46: 'Bidir. vert. arrow',
	0x47: 'Explosion 1',
	0x48: 'Explosion 2',
	0x49: 'Thunderbolt',
	0x4a: 'Heart',
	# gap
	0x4c: 'Four-ended arrow',
	0x4d: 'Rect. with left arrow',
	0x4e: 'Rect. with right arrow',
	0x4f: 'Rect. with up arrow',
	0x50: 'Rect. with down arrow',
	0x51: 'Rect. with horiz. arrows',
	0x52: 'Rect. with vert. arrows',
	0x53: 'Rect. with all-dir. arrows',
	# gap
	0x54: 'Slanted edges',
	0x55: 'Left bracket',
	0x56: 'Right bracket',
	0x57: 'Left compound bracket',
	0x58: 'Right compound bracket',
	0x59: 'Left and up arrow',
	0x5a: 'Up-bended arrow',
	0x5b: 'Bended arrow',
	0x5c: '24-pointed star',
	0x5d: 'Striped arrow',
	0x5e: 'Wedged arrow',
	0x5f: 'Bended band',
	# gap
	0x60: 'Smile',
	0x61: 'Vert. scroll',
	0x62: 'Horiz. scroll',
	0x63: 'Round arrow',
	# gap
	0x65: 'U-shaped arrow',
	# gap
	0x6b: 'Bended ribbon down',
	0x6c: 'Bended ribbon up',
	# gap
	0xb6: 'Three-ended arrow',
	0xb7: 'Sun',
	0xb8: 'Moon',
	0xb9: 'Brackets',
	0xba: 'Compound brackets',
	0xbb: 'Four-pointed star',
	0xbc: 'Double wave',
}

def _handle_linked_list(page, data, parent, parser, entry_id):
	(count, off) = rdata(data, 0, '<I')
	(entry_size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, '[%d]' % i, 'wt602', entry_id, data[off:off + entry_size], parent)
		off += entry_size

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
			pos = ' %d%s' % (positions[i], mark_last)
		text = ''
		if texts[i][1] - texts[i][0] > 0:
			text = ' ' + preview(text_data[texts[i][0]:texts[i][1]])
		add_pgiter(page, '[%d]%s%s' % (i, pos, text), 'wt602', 'text_info', data[off:off + size], parent)
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
		offset = start - 0x10
		assert parser.strings.has_key(offset)
		string = preview(parser.strings[offset])
		add_pgiter(page, '[%d] Off %d: %s' % (i, offset, string), 'wt602', 'string_entry', data[start:off], dataiter)
		i += 1
	add_pgiter(page, 'Hash map', 'wt602', 'string_map', data[off:], parent)

def handle_colormap(page, data, parent, parser = None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, '[%d]' % i, 'wt602', 'color', data[off:off + size], parent)
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
		add_pgiter(page, '[%d] (ID: %s)' % (n, id2txt(id)), 'wt602', attrset_id, data[off:off + attrset_size], attrsiter)
		off += attrset_size
	assert(off == start_styles)
	descsiter = add_pgiter(page, 'Styles', 'wt602', 'container', data[off:start_ids], parent)
	off += 2
	n = 0
	while off < start_ids:
		add_pgiter(page, '[%d]' % n, 'wt602', style_id, data[off:off + 6], descsiter)
		off += 6
		n += 1
	# assert(off == start_ids)
	add_pgiter(page, 'ID map', 'wt602', 'attrset_ids', data[start_ids:], parent)

def handle_char_styles(page, data, parent, parser = None):
	_handle_styles(page, data, parent, parser, 'attrset', 28, 'style')

def handle_para_styles(page, data, parent, parser = None):
	_handle_styles(page, data, parent, parser, 'attrset_para', 46, 'style_para')

def handle_section_styles(page, data, parent, parser = None):
	_handle_styles(page, data, parent, parser, 'attrset_section', 58, 'style_section')

def handle_tabs(page, data, parent, parser=None):
	off = 0
	(count, off) = rdata(data, off, '<I')
	(tab_size, off) = rdata(data, off, '<H')
	tabs_end = count * tab_size + 12
	tabsiter = add_pgiter(page, 'Defs', 'wt602', 'linked_list', data[0:tabs_end], parent)
	stop_counts = []
	for i in range(0, count):
		start = off
		off += 8
		(stops, off) = rdata(data, off, '<H')
		stops_str = ''
		if stops > 0:
			stops_str = ' (Stops index: %d)' % len(stop_counts)
			stop_counts.append(stops)
		add_pgiter(page, '[%d]%s' % (i, stops_str), 'wt602', 'tabs_def', data[start:start + tab_size], tabsiter)
		off = start + tab_size
	stops_iter = add_pgiter(page, 'Stops', 'wt602', '', data[off:], parent)
	off += 6
	i = 0
	for stops in stop_counts:
		end = off + 4 * stops
		add_pgiter(page, '[%d]' % i, 'wt602', 'tab_stop', data[off:end], stops_iter)
		off = end
		i += 1

def handle_text_flows(page, data, parent, parser=None):
	_handle_linked_list(page, data, parent, parser, 'text_flow')

def handle_frames(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	entry_size = 204
	defiter = add_pgiter(page, 'Definitions', 'wt602', '', data[off:off + count * entry_size], parent)
	data_offsets = []
	kinds = []
	# The structure of the frame data is mostly the same for all kinds,
	# but there's a block that is specific to each kind. So we need to
	# dispatch each kind using a separate id. And we then need the same
	# thing for the extra data records, which are different for each
	# kind (and sometimes they are different even for a single kind,
	# e.g., form controls).
	kind_ids = {}
	controls = {}
	for i in range(0, count):
		start = off
		off += 4
		(data_off, off) = rdata(data, off, '<I')
		data_offsets.append(data_off)
		off += 6
		(kind, off) = rdata(data, off, '<H')
		kinds.append(kind)
		if frame_kind_map.has_key(kind):
			kind_ids[i] = (('%s' % frame_kind_map[kind]).lower().replace(' ', '_'))
		label = key2txt(kind, frame_kind_map)
		if kind == 0xf:
			off += 0x5c
			(controls[i], off) = rdata(data, off, '<H')
			label += ': ' + key2txt(controls[i], form_control_map)
		kid = 'frame'
		if kind_ids.has_key(i):
			kid + '_' + kind_ids[i]
		add_pgiter(page, '[%d] %s' % (i, label), 'wt602', kid, data[start:start + entry_size], defiter)
		off = start + entry_size
	dataiter = add_pgiter(page, 'Data', 'wt602', '', data[off:], parent)
	assert off == data_offsets[0]
	assert len(data_offsets) == count
	data_offsets.append(len(data))
	i = 0
	for (start, end, kind) in zip(data_offsets[0:-1], data_offsets[1:], kinds):
		name = ''
		if kind == 0xf:
			(offset, off) = rdata(data, start + 4, '<I')
			name = ' ' + key2txt(offset, parser.strings, '')
		elif kind == 0x11: # shape
			(typ, off) = rdata(data, start + 4, '<H')
			name = ' ' + key2txt(typ, shape_map, '')
		kid = ''
		if kind_ids.has_key(i):
			kid = 'frame_data_' + kind_ids[i]
		if controls.has_key(i):
			kid += '_' + form_control_map[controls[i]].lower()
		add_pgiter(page, '[%d]%s' % (i, name), 'wt602', kid, data[start:end], dataiter)
		i += 1

def handle_blocks(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, '[%d]' % i, 'wt602', 'block', data[off:off + size], parent)
		off += size

def handle_index(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, '[%d]' % i, 'wt602', 'index_entry', data[off:off + size], parent)
		off += size

def handle_changes(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, '[%d]' % i, 'wt602', 'change', data[off:off + size], parent)
		off += size

def handle_fields(page, data, parent, parser=None):
	off = 0x10
	i = 0
	while off < len(data):
		start = off
		(size, off) = rdata(data, off + 4, '<I')
		add_pgiter(page, '[%d]' % i, 'wt602', 'field', data[start:start + size], parent)
		off = start + size
		i += 1

def handle_chapters(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(size, off) = rdata(data, off, '<H')
	for i in range(0, count):
		add_pgiter(page, '[%d]' % i, 'wt602', 'chapter', data[off:off + size], parent)
		off += size

def handle_named_styles(page, data, parent, parser=None):
	(count, off) = rdata(data, 0, '<I')
	(length, off) = rdata(data, off, '<H')
	for i in range(0, count):
		start = off
		end = start + length
		off += 8
		(string, off) = rdata(data, off, '<I')
		assert parser.strings.has_key(string)
		add_pgiter(page, '[%d] %s' % (i, parser.strings[string]), 'wt602', 'named_style', data[start:end], parent)
		off = end

def handle_numberings(page, data, parent, parser=None):
	_handle_linked_list(page, data, parent, parser, 'numbering')

wt602_section_handlers = {
	6: (None, 'view_settings'),
	8: (None, 'footnotes'),
	10: (None, 'fonts'),
	11: (handle_tabs, ''),
	12: (handle_named_styles, 'linked_list'),
	13: (handle_chapters, 'chapters'),
	14: (handle_index, 'index'),
	16: (handle_frames, 'frames'),
	18: (handle_strings, 'strings'),
	19: (handle_blocks, 'linked_list'),
	20: (handle_colormap, 'colormap'),
	21: (handle_fields, 'fields'),
	22: (handle_char_styles, 'styles'),
	23: (handle_para_styles, 'styles'),
	24: (handle_text_flows, 'linked_list'),
	25: (handle_text_infos, 'text_infos'),
	26: (handle_numberings, 'linked_list'),
	27: (None, 'text'),
	28: (None, 'html'),
	31: (handle_section_styles, 'styles'),
	32: (None, 'datasource'),
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
		self.strings = {}

	def parse(self):
		self.parse_header()
		self.parse_offset_table()
		self._collect_strings()
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

	def _collect_strings(self):
		(begin, end) = self.sections[18]
		if end > begin:
			(datasize, off) = rdata(self.data, begin, '<I')
			off = begin + 0x10
			while off < begin + datasize + 0x10:
				start = off
				off += 4
				(length, off) = rdata(self.data, off, '<H')
				off += 12
				(slen, off) = rdata(self.data, off, '<H')
				(string, off) = rdata(self.data, off, '%ds' % slen)
				string = unicode(string, 'cp1250')
				self.strings[start - begin - 0x10] = string
				off = start + length

def to_cm(val):
	return val / 20.0 * 0.353 / 10

def _add_list_links(hd, data):
	(prev, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Previous index', index2txt(prev), off - 2, 2, '<H')
	(next, off) = rdata(data, off, '<H')
	add_iter(hd, 'Next index', index2txt(next), off - 2, 2, '<H')
	return off

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

char_style_flags = {
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
	0x1000: 'language',
}

para_style_flags = {
	0x1: 'alignment',
	0x2: 'left indent',
	0x4: 'right indent',
	0x8: 'first indent',
	0x10: 'tabs',
	# gap
	0x80: 'top margin',
	0x100: 'bottom margin',
	0x200: 'shading type',
	0x400: 'border line',
	0x800: 'border type',
	0x1000: 'numbering level',
	0x2000: 'multi-level',
	0x4000: 'line height',
	0x8000: 'hyphenation',
	0x10000: 'border padding',
	# gap
	0x80000: 'numbering?',
	0x100000: 'skip number?',
	# gap
	0x400000: 'border color',
	0x800000: 'shading color',
	# gap
	# 0x8000000: ''
}

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
	flag_map = {0x8: 'start flow', 0x20: 'block change', 0x100: 'paragraph break'}
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
	add_iter(hd, 'Changed attributes', bflag2txt(attribs, char_style_flags), off - 2, 2, '<H')
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
	(level, off) = rdata(data, off, '<H')
	add_iter(hd, 'Numbering level', level, off - 2, 2, '<H')
	multi_map = {0: 'None', 1: 'Legal (1.1)', 2: 'Outline (I,A,)'}
	(multi, off) = rdata(data, off, '<H')
	add_iter(hd, 'Multi-level numbering type', key2txt(multi, multi_map), off - 2, 2, '<H')
	(line_height, off) = rdata(data, off, '<H')
	hyphen_map = {0: 'None', 1: 'All lines', 2: 'Skip 1 line', 3: 'Skip 2 lines'}
	add_iter(hd, 'Line height', '%d%%' % line_height, off - 2, 2, '<H')
	(hyphen, off) = rdata(data, off, '<H')
	add_iter(hd, 'Hyphenation', key2txt(hyphen, hyphen_map), off - 2, 2, '<H')
	off += 2
	(section_height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Section height', '%.2fcm' % to_cm(section_height), off - 2, 2, '<H')
	(section_inc, off) = rdata(data, off, '<H')
	add_iter(hd, 'Section increment', '%.2fcm' % to_cm(section_inc), off - 2, 2, '<H')
	(numbering, off) = rdata(data, off, '<H')
	add_iter(hd, 'Numbering index?', numbering, off - 2, 2, '<H')
	off += 2
	(column_line, off) = rdata(data, off, '<H')
	add_iter(hd, 'Inter-column line', key2txt(column_line, line_map), off - 2, 2, '<H')

def add_attrset_section(hd, size, data):
	off = 10
	(column_gap, off) = rdata(data, off, '<H')
	add_iter(hd, 'Column gap', '%.2fcm' % to_cm(column_gap), off - 2, 2, '<H')
	(columns, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of columns', columns, off - 2, 2, '<H')
	off += 20
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Height', '%.2fcm' % to_cm(height), off - 2, 2, '<H')
	(inc, off) = rdata(data, off, '<H')
	add_iter(hd, 'Increment', '%.2fcm' % to_cm(inc), off - 2, 2, '<H')
	off += 4
	(column_line, off) = rdata(data, off, '<H')
	add_iter(hd, 'Inter-column line', key2txt(column_line, line_map), off - 2, 2, '<H')
	off += 4
	(color, off) = rdata(data, off, '<H')
	add_iter(hd, 'Color index', color, off - 2, 2, '<H')

def add_style(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attributes', bflag2txt(attribs, char_style_flags), off - 2, 2, '<H')
	off += 2
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set', attrset, off - 2, 2, '<H')

def add_style_para(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Attributes', bflag2txt(attribs, para_style_flags), off - 4, 4, '<I')
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Attribute set', attrset, off - 2, 2, '<H')

def add_style_section(hd, size, data):
	off = 0
	(attribs, off) = rdata(data, off, '<H')
	# add_iter(hd, 'Changed attributes', '%s' % get_section_style(attribs), off - 2, 2, '<H')
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

def add_tabs_def(hd, size, data):
	off = _add_list_links(hd, data)
	off += 4
	(stops, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of stops', stops, off - 2, 2, '<H')

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

def add_text_flow(hd, size, data):
	off = _add_list_links(hd, data)
	off += 4
	(index, off) = rdata(data, off, '<H')
	add_iter(hd, 'Start index', index, off - 2, 2, '<H')

def add_frames(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')

def _add_frame_header(hd, size, data, offset):
	off = offset + 4
	(data_off, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra data offset', data_off, off - 4, 4, '<I')
	off += 4
	(sid, off) = rdata(data, off, '<H')
	add_iter(hd, 'Shape ID', id2txt(sid), off - 2, 2, '<H')
	(kind, off) = rdata(data, off, '<H')
	add_iter(hd, 'Kind', key2txt(kind, frame_kind_map), off - 2, 2, '<H')
	off += 4
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
	return off

def _add_frame_trailer(hd, size, data, offset):
	wrap_map = {0: 'run-through', 1: 'none', 2: 'parallel'}
	(wrap, off) = rdata(data, offset, '<B')
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
	return off

def _add_frame_text_margins(hd, size, data, offset):
	(left_border, off) = rdata(data, offset, '<I')
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
	return off

def add_frame(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off += 0x60
	_add_frame_trailer(hd, size, data, off)

def add_frame_text(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off = _add_frame_text_margins(hd, size, data, off)
	off += 48
	_add_frame_trailer(hd, size, data, off)

def add_frame_image(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	(left_crop, off) = rdata(data, off, '<I')
	add_iter(hd, 'Left crop', '%.2f cm' % to_cm(left_crop), off - 4, 4, '<I')
	(top_crop, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top crop', '%.2f cm' % to_cm(top_crop), off - 4, 4, '<I')
	(right_crop, off) = rdata(data, off, '<I')
	add_iter(hd, 'Right crop', '%.2f cm' % to_cm(right_crop), off - 4, 4, '<I')
	(bottom_crop, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom crop', '%.2f cm' % to_cm(bottom_crop), off - 4, 4, '<I')
	off += 80
	_add_frame_trailer(hd, size, data, off)

def add_frame_table(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off += 0x60
	_add_frame_trailer(hd, size, data, off)

def add_frame_group(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off += 0x60
	_add_frame_trailer(hd, size, data, off)

def add_frame_form_control(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off += 40
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Control type', key2txt(typ, form_control_map), off - 2, 2, '<H')
	off += 2
	if typ in (1, 2):
		(checked, off) = rdata(data, off, '<H')
		add_iter(hd, 'Checked', bool(checked), off - 2, 2, '<H')
		off += 50
	elif typ in (5, 8, 9):
		off += 6
		(length, off) = rdata(data, off, '<H')
		add_iter(hd, 'Max length', length, off - 2, 2, '<H')
		(width, off) = rdata(data, off, '<H')
		add_iter(hd, 'Width', width, off - 2, 2, '<H')
		off += 42
	elif typ == 6:
		formatting_map = {0: 'Off', 1: 'Virtual', 2: 'Physical'}
		(formatting, off) = rdata(data, off, '<H')
		add_iter(hd, 'Text formatting', key2txt(formatting, formatting_map), off - 2, 2, '<H')
		off += 6
		(width, off) = rdata(data, off, '<H')
		add_iter(hd, 'Width', width, off - 2, 2, '<H')
		(lines, off) = rdata(data, off, '<H')
		add_iter(hd, 'Lines', lines, off - 2, 2, '<H')
		off += 40
	elif typ == 7:
		(sel, off) = rdata(data, off, '<H')
		add_iter(hd, 'Multiple selection', sel == 3, off - 2, 2, '<H')
		off += 8
		(lines, off) = rdata(data, off, '<H')
		add_iter(hd, 'Number of lines', lines, off - 2, 2, '<H')
		off += 40
	else:
		off += 52

	_add_frame_trailer(hd, size, data, off)

def add_frame_barcode(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off += 0x60
	_add_frame_trailer(hd, size, data, off)

def add_frame_shape(hd, size, data):
	off = _add_frame_header(hd, size, data, 0)
	off = _add_frame_text_margins(hd, size, data, off)
	off += 48
	_add_frame_trailer(hd, size, data, off)

def add_frame_data_text(hd, size, data):
	pass

def add_frame_data_image(hd, size, data):
	off = size - 64
	format_map = {0x4: 'GIF', 0xd: 'JPEG'}
	(format, off) = rdata(data, off, '<H')
	add_iter(hd, 'Image format', key2txt(format, format_map), off - 2, 2, '<H')
	off += 2
	mapping_flags = {0x1: 'ISMAP', 0x2: 'USEMAP'}
	(mapping, off) = rdata(data, off, '<H')
	add_iter(hd, 'Image mapping', bflag2txt(mapping & 0xf, mapping_flags), off - 2, 2, '<H')
	off += 14
	(typ, off) = rdata(data, off, '<B')
	assert typ in (5, 6)
	add_iter(hd, 'Use in form', typ == 6, off - 1, 1, '<B')
	off += 3
	(path, off) = rdata(data, off, '<I')
	add_iter(hd, 'Path string', off2txt(path, hd), off - 4, 4, '<I')
	if typ == 5:
		(alt, off) = rdata(data, off, '<I')
		add_iter(hd, 'Alt. text string', off2txt(alt, hd), off - 4, 4, '<I')
		(url, off) = rdata(data, off, '<I')
		add_iter(hd, 'URL link string', off2txt(url, hd), off - 4, 4, '<I')
		(uname, off) = rdata(data, off, '<I')
		add_iter(hd, 'USEMAP name string', off2txt(uname, hd), off - 4, 4, '<I')
		(attrs, off) = rdata(data, off, '<I')
		add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')
	else:
		(name, off) = rdata(data, off, '<I')
		add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
		(action, off) = rdata(data, off, '<I')
		add_iter(hd, 'Action string', off2txt(action, hd), off - 4, 4, '<I')
		(fmt, off) = rdata(data, off, '<I')
		add_iter(hd, 'Data format string', off2txt(fmt, hd), off - 4, 4, '<I')
		(attrs, off) = rdata(data, off, '<I')
		add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')
		(method, off) = rdata(data, off, '<I')
		add_iter(hd, 'Method string', off2txt(method, hd), off - 4, 4, '<I')

def add_frame_data_table(hd, size, data):
	pass

def add_frame_data_group(hd, size, data):
	pass

def _add_frame_data_form_text_field(hd, size, data):
	off = 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	off += 4
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')
	(value, off) = rdata(data, off, '<I')
	add_iter(hd, 'Value string', off2txt(value, hd), off - 4, 4, '<I')

def add_frame_data_form_control_checkbox(hd, size, data):
	off = 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	(value, off) = rdata(data, off, '<I')
	add_iter(hd, 'Value string', off2txt(value, hd), off - 4, 4, '<I')
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')

def add_frame_data_form_control_radio(hd, size, data):
	off = 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	(value, off) = rdata(data, off, '<I')
	add_iter(hd, 'Value string', off2txt(value, hd), off - 4, 4, '<I')
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')

def add_frame_data_form_control_submit(hd, size, data):
	off = 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	(label, off) = rdata(data, off, '<I')
	add_iter(hd, 'Label string', off2txt(label, hd), off - 4, 4, '<I')
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')
	(action, off) = rdata(data, off, '<I')
	add_iter(hd, 'Action string', off2txt(action, hd), off - 4, 4, '<I')
	(format, off) = rdata(data, off, '<I')
	add_iter(hd, 'Data format string', off2txt(format, hd), off - 4, 4, '<I')
	(method, off) = rdata(data, off, '<I')
	add_iter(hd, 'Method string', off2txt(method, hd), off - 4, 4, '<I')

def add_frame_data_form_control_reset(hd, size, data):
	off = 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	(label, off) = rdata(data, off, '<I')
	add_iter(hd, 'Label string', off2txt(label, hd), off - 4, 4, '<I')
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')

def add_frame_data_form_control_text(hd, size, data):
	_add_frame_data_form_text_field(hd, size, data)

def add_frame_data_form_control_textarea(hd, size, data):
	_add_frame_data_form_text_field(hd, size, data)

def add_frame_data_form_control_select(hd, size, data):
	off = 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	# NOTE: The values and displayed values strings are a concatenation
	# of items, each ended by <Tab>. There can be an extra tab preceding
	# an item in the displayed values string; that means the item is
	# selected.
	(values, off) = rdata(data, off, '<I')
	add_iter(hd, 'Values string', off2txt(values, hd), off - 4, 4, '<I')
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')
	(displayed, off) = rdata(data, off, '<I')
	add_iter(hd, 'Displayed values string', off2txt(displayed, hd), off - 4, 4, '<I')

def add_frame_data_form_control_password(hd, size, data):
	_add_frame_data_form_text_field(hd, size, data)

def add_frame_data_form_control_hidden(hd, size, data):
	_add_frame_data_form_text_field(hd, size, data)

def add_frame_data_barcode(hd, size, data):
	pass

def add_frame_data_shape(hd, size, data):
	off = 4
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Shape type', key2txt(typ, shape_map), off - 2, 2, '<H')
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

def add_index_entry(hd, size, data):
	off = 12
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	off += 12
	(eid, off) = rdata(data, off, '<H')
	add_iter(hd, 'ID', eid, off - 2, 2, '<H')

def add_block(hd, size, data):
	(prev, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Preceded by', ref2txt(prev), off - 2, 2, '<H')
	(next, off) = rdata(data, off, '<H')
	add_iter(hd, 'Followed by', ref2txt(next), off - 2, 2, '<H')
	type_map = {0x1f: 'Index entry', 0x4b: 'Named block', 0xe8: 'Selection', 0xeb: 'Selection',}
	(typ, off) = rdata(data, off, '<I')
	add_iter(hd, 'Entry type?', key2txt(typ, type_map), off - 4, 4, '<I')
	if typ == 0x1f:
		(eid, off) = rdata(data, off, '<H')
		add_iter(hd, 'Entry ref', ref2txt(eid), off - 2, 2, '<H')
		off += 2
	elif typ == 0x4b:
		(title, off) = rdata(data, off, '<I')
		add_iter(hd, 'Block name string', off2txt(title, hd), off - 4, 4, '<I')
	elif typ in (0xe8, 0xeb):
		(title, off) = rdata(data, off, '<I')
		add_iter(hd, 'Selection name string', off2txt(title, hd), off - 4, 4, '<I')
	else:
		pass
	(start, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start index?', start, off - 4, 4, '<I')
	(end, off) = rdata(data, off, '<I')
	add_iter(hd, 'End index?', end, off - 4, 4, '<I')

def add_change(hd, size, data):
	off = 16
	(author, off) = rdata(data, off, '<I')
	add_iter(hd, 'Author string', off2txt(author, hd), off - 4, 4, '<I')
	(offset, off) = rdata(data, off, '<I')
	add_iter(hd, 'Comment string', off2txt(offset, hd), off - 4, 4, '<I')

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
		0x2: 'DB merge',
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
	if typ == 0x2:
		off += 8
		(col, off) = rdata(data, off, '<I')
		add_iter(hd, 'Column', off2txt(col, hd), off - 4, 4, '<I')
	elif typ == 0x3:
		off += 12
		(mark, off) = rdata(data, off, '<I')
		add_iter(hd, 'Mark string', off2txt(mark, hd), off - 4, 4, '<I')
		(number, off) = rdata(data, off, '<I')
		add_iter(hd, 'Mark number?', number, off - 4, 4, '<I')
	elif typ == 0x15:
		off += 4
		(tag, off) = rdata(data, off, '<I')
		add_iter(hd, 'Tag string', off2txt(tag, hd), off - 4, 4, '<I')
	elif typ == 0x16:
		off += 4
		(entity, off) = rdata(data, off, '<I')
		add_iter(hd, 'Entity string', off2txt(entity, hd), off - 4, 4, '<I')
	elif typ == 0x17:
		off += 4
		(title, off) = rdata(data, off, '<I')
		add_iter(hd, 'Title string', off2txt(title, hd), off - 4, 4, '<I')
		(url, off) = rdata(data, off, '<I')
		add_iter(hd, 'URL string', off2txt(url, hd), off - 4, 4, '<I')
		(attrs, off) = rdata(data, off, '<I')
		add_iter(hd, 'Attributes string', off2txt(attrs, hd), off - 4, 4, '<I')
	elif typ == 0x18:
		(text, off) = rdata(data, off, '<I')
		add_iter(hd, 'Text string', off2txt(text, hd), off - 4, 4, '<I')
		(comment, off) = rdata(data, off, '<I')
		add_iter(hd, 'Comment string', off2txt(comment, hd), off - 4, 4, '<I')
	elif typ == 0x19:
		off += 8
		(char, off) = rdata(data, off, '<H')
		add_iter(hd, 'Character', char, off - 2, 2, '<H')
		script_map = {0: 'Western', 2: 'Cyrillic', 3: 'Central European', 4: 'Baltic', 5: 'Greek', 6: 'Turkish'}
		(script, off) = rdata(data, off, '<H')
		add_iter(hd, 'Script', key2txt(script, script_map), off - 2, 2, '<H')
	elif typ == 0x1a:
		(name, off) = rdata(data, off, '<I')
		add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
		(content, off) = rdata(data, off, '<I')
		add_iter(hd, 'Content string', off2txt(content, hd), off - 4, 4, '<I')

def add_chapter(hd, size, data):
	off = 0
	(pagenum, off) = rdata(data, off, '<H')
	add_iter(hd, 'First page number', pagenum, off - 2, 2, '<H')
	chapnum_map = {0x7ffe: 'Increment'}
	(chapnum, off) = rdata(data, off, '<H')
	add_iter(hd, 'Chapter number', key2txt(chapnum, chapnum_map, '%d' % chapnum), off - 2, 2, '<H')
	(current, off) = rdata(data, off, '<H')
	add_iter(hd, 'Current chapter number', current, off - 2, 2, '<H')
	(flow, off) = rdata(data, off, '<H')
	add_iter(hd, 'Flow index?', flow, off - 2, 2, '<H')
	off += 16
	(thickness, off) = rdata(data, off, '<H')
	add_iter(hd, 'Footnote line thickness', key2txt(thickness, line_map), off - 2, 2, '<H')
	off += 2
	(line, off) = rdata(data, off, '<H')
	add_iter(hd, 'Footnote line length', '%d%%' % line, off - 2, 2, '<H')
	(color, off) = rdata(data, off, '<H')
	add_iter(hd, 'Footnote line color index', color, off - 2, 2, '<H')

def add_chapters(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, 0, 4, '<I')
	(sz, off) = rdata(data, off, '<H')
	add_iter(hd, 'Entry size', sz, off - 2, 2, '<H')

def add_footnotes(hd, size, data):
	off = 6
	numbering_map = {0: 'Page', 1: 'Chapter', 2: 'Document'}
	(numbering, off) = rdata(data, off, '<H')
	add_iter(hd, 'Numbering restarts at', key2txt(numbering, numbering_map), off - 2, 2, '<H')

def add_named_style(hd, size, data):
	off = _add_list_links(hd, data)
	off += 4
	(name, off) = rdata(data, off, '<I')
	add_iter(hd, 'Name string', off2txt(name, hd), off - 4, 4, '<I')
	(attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Character attr. set ref', ref2txt(attrset), off - 2, 2, '<H')
	(attrs, off) = rdata(data, off, '<H')
	add_iter(hd, 'Character attributes', bflag2txt(attrs, char_style_flags), off - 2, 2, '<H')
	(para_attrset, off) = rdata(data, off, '<H')
	add_iter(hd, 'Paragraph attr. set ref', ref2txt(para_attrset), off - 2, 2, '<H')
	off += 2
	(para_attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Paragraph attributes', bflag2txt(para_attrs, para_style_flags), off - 4, 4, '<I')
	following_map = {0xffff: 'the same'}
	(following, off) = rdata(data, off, '<H')
	add_iter(hd, 'Style of following paragraph', key2txt(following, following_map, '%s' % following), off - 2, 2, '<H')
	(parent, off) = rdata(data, off, '<H')
	add_iter(hd, 'Parent style', index2txt(parent), off - 2, 2, '<H')

def add_linked_list(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Count', count, off - 4, 4, '<I')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Entry length', length, off - 2, 2, '<H')
	off += count * length
	off += 2
	(first, off) = rdata(data, off, '<H')
	add_iter(hd, 'First index', index2txt(first), off - 2, 2, '<H')
	(last, off) = rdata(data, off, '<H')
	add_iter(hd, 'Last index', index2txt(last), off - 2, 2, '<H')

def add_numbering(hd, size, data):
	off = _add_list_links(hd, data)
	type_map = {3: 'Ordered', 7: 'Unordered'} # TODO: flags?
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 2, 2, '<H')
	(width, off) = rdata(data, off, '<H')
	add_iter(hd, 'Width', '%.2fcm' % to_cm(width), off - 2, 2, '<H')
	if typ == 3:
		num_type_map = {1: '1', 2: 'a', 3: 'A', 4: 'I', 5: 'i'}
		(num_type, off) = rdata(data, off, '<H')
		add_iter(hd, 'Numbering type?', key2txt(num_type, num_type_map), off - 2, 2, '<H')
		off += 2
		(fmt, off) = rdata(data, off, '<I')
		add_iter(hd, 'Number format string', off2txt(fmt, hd), off - 4, 4, '<I')
		(start, off) = rdata(data, off, '<I')
		add_iter(hd, 'Start value', start, off - 4, 4, '<I')
	elif typ == 7:
		(font, off) = rdata(data, off, '<H')
		add_iter(hd, 'Font index', font, off - 2, 2, '<H')
		(char, off) = rdata(data, off, '<H')
		add_iter(hd, 'Bullet char', char, off - 2, 2, '<H')
		(color, off) = rdata(data, off, '<H')
		add_iter(hd, 'Bullet color index', color, off - 2, 2, '<H')

def add_html(hd, size, data):
	(base, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Base URL string', off2txt(base, hd), off - 4, 4, '<I')
	(image, off) = rdata(data, off, '<I')
	add_iter(hd, 'Background image string', off2txt(image, hd), off - 4, 4, '<I')
	(attrs, off) = rdata(data, off, '<I')
	add_iter(hd, 'Extra HTML attrs string', off2txt(attrs, hd), off - 4, 4, '<I')
	(css_file, off) = rdata(data, off, '<I')
	add_iter(hd, 'CSS file', off2txt(css_file, hd), off - 4, 4, '<I')
	off += 36
	css_flags = {0x2: 'export CSS', 0x4: 'use external file'}
	(css, off) = rdata(data, off, '<I')
	add_iter(hd, 'CSS flags', bflag2txt(css, css_flags), off - 4, 4, '<I')
	off += 4
	(bgcolor_set, off) = rdata(data, off, '<B')
	add_iter(hd, 'Set background color', bool(bgcolor_set), off - 1, 1, '<B')
	(text_color_set, off) = rdata(data, off, '<B')
	add_iter(hd, 'Set text color', bool(text_color_set), off - 1, 1, '<B')
	(alink_color_set, off) = rdata(data, off, '<B')
	add_iter(hd, 'Set active link color', bool(alink_color_set), off - 1, 1, '<B')
	(vlink_color_set, off) = rdata(data, off, '<B')
	add_iter(hd, 'Set visited link color', bool(vlink_color_set), off - 1, 1, '<B')
	(link_color_set, off) = rdata(data, off, '<B')
	add_iter(hd, 'Set link color', bool(link_color_set), off - 1, 1, '<B')
	off += 3
	(bgcolor, off) = rdata(data, off, '3s')
	add_iter(hd, 'Background color', d2hex(bgcolor), off - 3, 3, '3s')
	off += 1
	(text_color, off) = rdata(data, off, '3s')
	add_iter(hd, 'Text color', d2hex(text_color), off - 3, 3, '3s')
	off += 1
	(alink_color, off) = rdata(data, off, '3s')
	add_iter(hd, 'Active link color', d2hex(alink_color), off - 3, 3, '3s')
	off += 1
	(vlink_color, off) = rdata(data, off, '3s')
	add_iter(hd, 'Visited link color', d2hex(vlink_color), off - 3, 3, '3s')
	off += 1
	(link_color, off) = rdata(data, off, '3s')
	add_iter(hd, 'Link color', d2hex(link_color), off - 3, 3, '3s')
	off += 1

def add_view_settings(hd, size, data):
	view_map = {0: 'Continuous', 1: 'Pages', 2: 'Outline', 3: 'HTML'}
	(view, off) = rdata(data, 0, '<I')
	add_iter(hd, 'View', key2txt(view, view_map), off - 4, 4, '<I')

def add_datasource(hd, size, data):
	off = 8
	src_map = {1: 'CSV', 6: 'WLS/XLS'}
	(src, off) = rdata(data, off, '<I')
	add_iter(hd, 'Source type?', key2txt(src, src_map), off - 4, 4, '<I')
	off = add_long_string(hd, size, data, off, 'Path')
	off += 4
	if src == 6:
		off = add_long_string(hd, size, data, off, 'Sheet')
		off += 4
	(columns, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of columns', columns, off - 2, 2, '<H')
	for i in range(1, columns + 1):
		off = add_long_string(hd, size, data, off, 'Column %d name' % i)

wt602_ids = {
	'attrset': add_attrset,
	'attrset_para': add_attrset_para,
	'attrset_ids': add_attrset_ids,
	'attrset_section': add_attrset_section,
	'block': add_block,
	'change': add_change,
	'changes': add_changes,
	'chapter': add_chapter,
	'chapters': add_chapters,
	'color': add_color,
	'colormap': add_colormap,
	'container': add_container,
	'datasource': add_datasource,
	'field' : add_field,
	'fields' : add_fields,
	'fonts' : add_fonts,
	'footnotes' : add_footnotes,
	'frame': add_frame,
	'frame_text': add_frame_text,
	'frame_image': add_frame_image,
	'frame_table': add_frame_table,
	'frame_group': add_frame_group,
	'frame_form_control': add_frame_form_control,
	'frame_barcode': add_frame_barcode,
	'frame_shape': add_frame_shape,
	'frame_data_text': add_frame_data_text,
	'frame_data_image': add_frame_data_image,
	'frame_data_table': add_frame_data_table,
	'frame_data_group': add_frame_data_group,
	'frame_data_form_control_checkbox': add_frame_data_form_control_checkbox,
	'frame_data_form_control_radio': add_frame_data_form_control_radio,
	'frame_data_form_control_submit': add_frame_data_form_control_submit,
	'frame_data_form_control_reset': add_frame_data_form_control_reset,
	'frame_data_form_control_text': add_frame_data_form_control_text,
	'frame_data_form_control_textarea': add_frame_data_form_control_textarea,
	'frame_data_form_control_select': add_frame_data_form_control_select,
	'frame_data_form_control_password': add_frame_data_form_control_password,
	'frame_data_form_control_hidden': add_frame_data_form_control_hidden,
	'frame_data_barcode': add_frame_data_barcode,
	'frame_data_shape': add_frame_data_shape,
	'frames': add_frames,
	'html': add_html,
	'index': add_index,
	'index_entry': add_index_entry,
	'linked_list': add_linked_list,
	'style': add_style,
	'style_para': add_style_para,
	'style_section': add_style_section,
	'header': add_header,
	'numbering': add_numbering,
	'object_header': add_object_header,
	'offsets': add_offsets,
	'tab_stop': add_tab_stop,
	'tabs_def': add_tabs_def,
	'text_flow': add_text_flow,
	'text_info': add_text_info,
	'text_infos': add_text_infos,
	'named_style': add_named_style,
	'string_entry': add_string_entry,
	'string_header': add_string_header,
	'string_map': add_string_map,
	'styles': add_styles,
	'text': add_text,
	'view_settings': add_view_settings,
}

def parse(page, data, parent):
	parser = wt602_parser(page, data, parent)
	page.context = parser
	parser.parse()

def parse_object(page, data, parent):
	add_pgiter(page, 'Header', 'wt602', 'object_header', data[0:4], parent)
	add_pgiter(page, 'Content', 'wt602', '', data[4:], parent)

# vim: set ft=python ts=4 sw=4 noet:
