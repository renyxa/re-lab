# Copyright (C) 2017 David Tardon (dtardon@redhat.com)
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

from collections import namedtuple
import traceback
import qxp

from utils import *
from qxp import *

color_map = {
	0: 'White',
	1: 'Black',
	2: 'Red',
	3: 'Green',
	4: 'Blue',
	5: 'Cyan',
	6: 'Magenta',
	7: 'Yellow',
}

shade_map = {
	0: '0%',
	1: '10%',
	2: '20%',
	3: '40%',
	4: '60%',
	5: '80%',
	6: 'Solid'
}

def bool2txt(value):
	return key2txt(value, {0: 'No', 1: 'Yes'})

def dim2txt(value):
	return '%.2f pt / %.2f in' % (value, dim2in(value))

def add_sizes(hd, data, offset, version, names):
	off = offset
	for name in names:
		(i, off) = rdata(data, off, '>H')
		add_iter(hd, name, '%d pt' % i, off - 2, 2, '>H')
	def adjust(val):
		return float(val - 0x8000) / 0x10000
	for name in names:
		(a, off) = rdata(data, off, '>H')
		add_iter(hd, '%s adjustment' % name, '%.2f pt' % adjust(a), off - 2, 2, '>H')
	return off

def add_size(hd, data, offset, version, name):
	return add_sizes(hd, data, offset, version, (name,))

def add_header(hd, size, data, dummy, version):
	off = 0
	version_map = {0x1c: '???', 0x20: '1.10'}
	(ver, off) = rdata(data, off, '>H')
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, '>H')
	(ver, off) = rdata(data, off, '>H')
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, '>H')
	off += 120
	(measure, off) = rdata(data, off, '>B')
	add_iter(hd, 'Measure', key2txt(measure, measure_map), off - 1, 1, '>B')
	(auto_hyph, off) = rdata(data, off, '>B')
	add_iter(hd, 'Auto hyphenation', key2txt(auto_hyph, {0: 'Off', 1: 'On'}), off - 1, 1, '>B')
	flags_map = {
		0x4: 'fract. widths',
		0x80: 'auto kerning',
		0x200: 'typesetting mode',
	}
        header=qxp.Header('macroman','true')
	(flags, off) = rdata(data, off, '>H')
	hyphens = (flags >> 11) & 0x7
	add_iter(hd, 'Hyphens in a row', 'unlimited' if hyphens == 0 else hyphens, off - 2, 1, '>B')
	add_iter(hd, 'Flags', bflag2txt(flags & 0x7e7, flags_map), off - 2, 2, '>H')
	add_iter(hd, 'Auto page insertion', key2txt((flags >> 3) & 0x03, page_ins_map), off - 2, 2, '>H')
	off += 5
	(double, off) = rdata(data, off, '>B')
	add_iter(hd, 'Double sided', bool2txt(double), off - 1, 1, '>B')
	off += 1
	(smallest, off) = rdata(data, off, '>B')
	add_iter(hd, 'Smallest word', smallest, off - 1, 1, '>B')
	(break_after, off) = rdata(data, off, '>B')
	add_iter(hd, 'Break after', break_after, off - 1, 1, '>B')
	(break_cap, off) = rdata(data, off, '>B')
	add_iter(hd, 'Break capitalized words', key2txt(break_cap, {0: 'Yes', 1: 'No'}), off - 1, 1, '>B')
	off += 16
	(header.pages, off) = rdata(data, off, '>H')
	add_iter(hd, '# of pages', header.pages, off - 2, 2, '>H')
	# NOTE: the height and width are 2 pts greater than they should be
	off = add_size(hd, data, off, version, 'Page height')
	off = add_size(hd, data, off, version, 'Page width')
	off = add_size(hd, data, off, version, 'Top margin')
	off = add_size(hd, data, off, version, 'Bottom margin')
	off = add_size(hd, data, off, version, '%s margin' % ('Inside' if double else 'Left'))
	off = add_size(hd, data, off, version, '%s margin' % ('Outside' if double else 'Right'))
	off += 6
	(spaces, off) = rdata(data, off, '>B')
	add_iter(hd, 'Spaces', spaces / 2, off - 1, 1, '>B')
	(overall, off) = rdata(data, off, '>B')
	add_iter(hd, 'Overall', overall / 2, off - 1, 1, '>B')
	off += 16
	off = add_sfloat_perc(hd, data, off, big_endian, 'Default auto leading')
	Header = namedtuple('Header', ('pages',))
	return (header, size)

def parse_formats(page, data, offset, parent, version, name, hdl, size):
	(length, off) = rdata(data, offset, '>I')
	end = off + length
	reciter = add_pgiter(page, name, 'qxp2', ('record', version), data[offset:end], parent)
	i = 0
	while off < end:
		add_pgiter(page, '[%d]' % i, 'qxp2', (hdl, version), data[off:off + size], reciter)
		off += size
		i += 1
	return end

def parse_record(page, data, offset, parent, fmt, version, name):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, name, 'qxp2', ('record', fmt, version), data[off - 4:off + length], parent)
	return off + length

def _read_name2(data, offset, fmt):
	rstr = read_c_str if fmt() == LITTLE_ENDIAN else read_pascal_str
	(name, off) = rstr(data, offset)
	if (off - offset) % 2 == 1:
		off += 1
	return name, off

def handle_hj(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('hj', fmt, version), data, parent)

def _parse_collection_named(page, data, offset, end, parent, fmt, version, handler, name_offset, init=0):
	i = init
	off = offset
	while off < end:
		start = off
		(name, off) = _read_name2(data, off + name_offset, fmt)
		handler(page, data[start:off], parent, fmt, version, i, name)
		i += 1
	return off

def parse_colors(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Colors', 'qxp2', ('colors', fmt, version), data[off - 4:off + length], parent)
	off += 1
	(count, off) = rdata(data, off, fmt('B'))
	off += 32
	for i in range(0, count):
		start = off
		(index, off) = rdata(data, off, fmt('B'))
		off += 47
		(name, off) = _read_name2(data, off, fmt)
		add_pgiter(page, '[%d] %s' % (index, name), 'qxp2', ('color', fmt, version), data[start:off], reciter)
	return offset + 4 + length

def parse_fonts(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, 'Fonts', 'qxp2', ('fonts', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_hjs(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'H&Js', 'qxp2', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_collection_named(page, data, off, off + length, reciter, fmt, version, handle_hj, 48)

def parse_para_styles(page, data, offset, parent, fmt, version, encoding):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Paragraph styles', 'qxp2', ('record', fmt, version), data[off - 4:off + length], parent)
	end = off + length
	while off < end:
		start = off
		off += 164
		(idx, off) = rdata(data, off, fmt('H'))
		off += 6
		(name, off) = _read_name2(data, off, fmt)
		add_pgiter(page, '[%d] %s' % (idx, name), 'qxp2', ('para_style', fmt, version, encoding), data[start:off], reciter)
	return end

def add_box(hd, data, offset, version, name):
	return add_sizes(hd, data, offset, version, ['%s %s' % (name, c) for c in ('Y1', 'X1', 'Y2', 'X2')])

def add_frame(hd, data, offset, version):
	off = add_size(hd, data, offset, version, 'Frame size')
	(shade, off) = rdata(data, off, '>B')
	add_iter(hd, 'Frame shade', key2txt(shade, shade_map), off - 1, 1, '>B')
	(color, off) = rdata(data, off, '>B')
	add_iter(hd, 'Frame color', key2txt(color, color_map), off - 1, 1, '>B')
	(style, off) = rdata(data, off, '>B')
	add_iter(hd, 'Frame style', key2txt(style, frame_style_map), off - 1, 1, '>B')
	return off

def _add_name2(hd, size, data, offset, fmt, title='Name'):
	(name, off) = _read_name2(data, offset, fmt)
	add_iter(hd, title, name, offset, off - offset, '%ds' % (off - offset))
	return off

def add_hj(hd, size, data, fmt, version):
	off = add_hj_common(hd, size, data, 0, fmt, version)
	off += 4
	_add_name2(hd, size, data, off, fmt)
        
def add_colors(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	off += 1
	(count, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of colors', count, off - 1, 1, fmt('B'))

def add_color_comp(hd, data, offset, fmt, name, parent=None):
	return add_sfloat_perc(hd, data, offset, fmt, name, parent=parent)

color_model_map = {
	0: 'HSB',
	1: 'RGB',
	2: 'CMYK',
}

def add_color(hd, size, data, fmt, version):
	off = 0
	(index, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Index', index, off - 1, 1, fmt('B'))
	(spot_color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Spot color', 'Black' if spot_color == 0x2d else 'index %d' % spot_color, off - 1, 1, fmt('B'))
	off = add_color_comp(hd, data, off, fmt, 'Red')
	off = add_color_comp(hd, data, off, fmt, 'Green')
	off = add_color_comp(hd, data, off, fmt, 'Blue')
	off = add_color_comp(hd, data, off, fmt, 'C')
	off = add_color_comp(hd, data, off, fmt, 'M')
	off = add_color_comp(hd, data, off, fmt, 'Y')
	off = add_color_comp(hd, data, off, fmt, 'K')
        off += 8
	off = add_color_comp(hd, data, off, fmt, 'H')
	off = add_color_comp(hd, data, off, fmt, 'S')
	off = add_color_comp(hd, data, off, fmt, 'L')
	off = add_color_comp(hd, data, off, fmt, 'A')
	off += 16
	_add_name2(hd, size, data, off, fmt)

def add_line(hd, data, offset, version, content, content_iter):
	# NOTE: the coords are shifted by +1
	off = add_box(hd, data, offset, version, 'Line')
	off = add_size(hd, data, off, version, 'Width')
	(line_style, off) = rdata(data, off, '>B')
	add_iter(hd, 'Line style', key2txt(line_style, line_style_map), off - 1, 1, '>B')
	endcaps_map = {0: 'None', 1: 'Right', 2: 'Left', 3: 'Right arrow', 4: 'Left arrow', 5: 'Both'}
	(endcaps, off) = rdata(data, off, '>B')
	add_iter(hd, 'Endcaps', key2txt(endcaps, endcaps_map), off - 1, 1, '>B')
	off += 3
	return content, off

def add_text(hd, data, offset, version, content, content_iter):
	off = add_frame(hd, data, offset, version)
	(col, off) = rdata(data, off, '>B')
	add_iter(hd, '# of columns', col, off - 1, 1, '>B')
	off = add_dim(hd, 4, data, off, big_endian, 'Gutter width')
	off = add_dim(hd, 4, data, off, big_endian, 'Text inset')
	off += 2
	(next_index, off) = rdata(data, off, '>H')
	add_iter(hd, 'Next linked list index', next_index, off - 2, 2, '>H')
	(something, off) = rdata(data, off, '>I')
	add_iter(hd, 'Something link-related', hex(something), off - 4, 4, '>I')
	if something:
		hd.model.set(content_iter, 0, 'Index in linked list')
		hd.model.set(content_iter, 1, content)
	off += 1
	if something == 0:
		off += 3
	if content == 0:
		off += 12
	return content if something == 0 else 0, off

def add_picture(hd, data, offset, version, content, content_iter):
	off = add_frame(hd, data, offset, version)
	off += 5
	off = add_fract_perc(hd, data, off, big_endian, 'Scale across')
	off = add_fract_perc(hd, data, off, big_endian, 'Scale down')
	off = add_dim(hd, 4, data, off, big_endian, 'Text outset')
	off += 12
	(radius, off) = rfract(data, off, big_endian)
	radius /= 2
	add_iter(hd, 'Corner radius', dim2txt(radius), off - 4, 4, '4s')
	return content, off + 5+10

def parse_object(page, data, offset, parent, version, index):
	off = offset
	hd = HexDumpSave(off)
	objiter = add_pgiter(page, '', 'qxp2', ('object', hd), data[offset:], parent)
	type_map = {
		0xfd: 'Text(master)',
		3: 'Text',
		0: 'Line',
		1: 'Orthogonal line',
		3: 'Text',
		11: 'Rectangle',
		12: 'Rounded rectangle',
		13: 'Ellipse',
	}
	parser_map = {
		0xfd: add_text,
		0: add_line,
		1: add_line,
		3: add_text,
		11: add_picture,
		12: add_picture,
		13: add_picture,
	}
	(typ, off) = rdata(data, off, '>B')
	type_str = key2txt(typ, type_map)
	add_iter(hd, 'Type', type_str, off - 1, 1, '>B')
	(transparent, off) = rdata(data, off, '>B')
	add_iter(hd, 'Transparent', bool2txt(transparent), off - 1, 1, '>B')
	(content, off) = rdata(data, off, '>H')
	content_iter = add_iter(hd, 'Content index', hex(content), off - 2, 2, '>H')
	flags_map = {0x80: 'locked?'}
	(flags, off) = rdata(data, off, '>B')
	add_iter(hd, 'Flags?', bflag2txt(flags, flags_map), off - 1, 1, '>B')
	off += 1
	# NOTE: the coords for lines are shifted by +1
	off = add_box(hd, data, off, version, 'Bounding box')
	(toff, off) = rdata(data, off, '>I')
	add_iter(hd, 'Offset into text', toff >> 8, off - 4, 3, '3s')
	# Saw 0x10, 0x20 and 0x30 here. 0x20 is the default
	add_iter(hd, 'Offset flags?', hex(toff & 0xff), off - 1, 1, '1s')
	off += 8
	(link_id, off) = rdata(data, off, '>I')
	add_iter(hd, 'Link ID', hex(link_id), off - 4, 4, '>I')
	(shade, off) = rdata(data, off, '>B')
	add_iter(hd, 'Shade', key2txt(shade, shade_map), off - 1, 1, '>B')
	(color, off) = rdata(data, off, '>B')
	add_iter(hd, 'Color', key2txt(color, color_map), off - 1, 1, '>B')
	if parser_map.has_key(typ):
		(content, off) = parser_map[typ](hd, data, off, version, content, content_iter)
	(last, off) = rdata(data, off, '>B')
	add_iter(hd, 'Last object', key2txt(last, {0: 'No', 1: '???', 2: 'Yes'}), off - 1, 1, '>B')
	page.model.set_value(objiter, 0, '[%d] %s' % (index, type_str))
	page.model.set_value(objiter, 2, off - offset)
	page.model.set_value(objiter, 3, data[offset:off])
	return (last == 2, content, typ == 3 or typ==0xfd, off)

def add_page_prefix(hd, data, offset, version):
	(number, sect_start, off) = add_section(hd, data, offset, big_endian, version)
	off += 8
	return (number, off, sect_start)

def add_page_tail(hd, data, offset, version, index, name, start, page, parent):
	(empty, off) = rdata(data, offset, '>B')
	add_iter(hd, 'Empty', key2txt(empty, {1: 'No', 2: 'Yes'}), off - 1, 1, '>B')
	page.model.set_value(parent, 0, '[%d] %s' % (index, name))
	page.model.set_value(parent, 2, off - start)
	page.model.set_value(parent, 3, data[start:off])
	return empty == 2, off

def parse_page(page, data, offset, parent, version, i):
	off = offset
	hd = HexDumpSave(off)
	pageiter = add_pgiter(page, '', 'qxp2', ('page', hd), data[offset:], parent)
	(index, off, section_start) = add_page_prefix(hd, data, off, version)
        if i==1:
                name = 'Right master'
        elif i==2:
                name = 'Left master'
        else:
	        name = 'Page'
	if section_start:
		name += '*'
	(empty, off) = add_page_tail(hd, data, off, version, index, name, offset, page, pageiter)
	return (pageiter, empty, off)

def parse_pages(page, data, offset, parent, version, npages):
	off = offset
	texts = []
	pictures = []
	# ATM I assume there are fixed 2 master pages
	for i in range(1, npages + 3):
		(pageiter, empty, off) = parse_page(page, data, off, parent, version, i)
		last = empty
		j = 1
		while not last and off < len(data):
			(last, content, text, off) = parse_object(page, data, off, pageiter, version, j)
			if content != 0:
				if text:
					texts.append(content)
				else:
					pictures.append(content)
			j += 1
	return (texts, pictures)

def handle_document(page, data, parent, fmt, version, hdr):
	off = 0
        off = parse_fonts(page, data, off, parent, fmt, version)
	off = parse_colors(page, data, off, parent, fmt, version)
	off = parse_para_styles(page, data, off, parent, fmt, version, hdr.encoding)
	off = parse_hjs(page, data, off, parent, fmt, version)
	off = parse_formats(page, data, off, parent, version, 'Character formats', 'char_format', 16)
	off = parse_formats(page, data, off, parent, version, 'Paragraph formats', 'para_format', 150)
	pagesiter = add_pgiter(page, 'Pages', 'qxp2', (), data[off:], parent)
	try:
		return parse_pages(page, data, off, pagesiter, version, hdr.pages)
	except:
		traceback.print_exc()
		return ((), ())

def add_record(hd, size, data, version, dummy):
	(length, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Length', length, off - 4, 4, '>I')

def _add_char_format(hd, size, data, off, version, dummy):
	(font, off) = rdata(data, off, '>H')
	add_iter(hd, 'Font index', font, off - 2, 2, '>H')
	(sz, off) = rdata(data, off, '>H')
	add_iter(hd, 'Font size', '%.1d' % (sz / 4.0), off - 2, 2, '>H')
	(flags, off) = rdata(data, off, '>H')
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 2, 2, '>H')
	(scale, off) = rdata(data, off, '>H')
	add_iter(hd, 'Scale', '%.0f%%' % (scale * 100.0 / 0x800), off - 2, 2, '>H')
	(color, off) = rdata(data, off, '>B')
	add_iter(hd, 'Color', key2txt(color, color_map), off - 1, 1, '>B')
	(shade, off) = rdata(data, off, '>B')
	add_iter(hd, 'Shade', key2txt(shade, shade_map), off - 1, 1, '>B')
	(track, off) = rdata(data, off, '>H')
	add_iter(hd, 'Track amount', '%.2f' % (track / 2.0), off - 2, 2, '>H')
        return off+2

def add_char_format(hd, size, data, version, dummy):
	off = 0
	(uses, off) = rdata(data, off, '>H')
	add_iter(hd, 'Use count', uses, off - 2, 2, '>H')
        _add_char_format(hd, size, data, off, version, dummy)

def _add_tab(hd, size, data, offset, version, parent=None):
	type_map = {0: 'left', 1: 'center', 2: 'right', 3: 'align'}
	(typ, off) = rdata(data, offset, '>B')
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 1, 1, '>B', parent=parent)
	(fill_char, off) = rdata(data, off, '1s')
	add_iter(hd, 'Fill char', fill_char, off - 1, 1, '1s', parent=parent)
	(pos, off) = rdata(data, off, '>i')
	if pos == -1:
		add_iter(hd, 'Position', 'not defined', off - 4, 4, '>i', parent=parent)
	else:
		off = add_dim(hd, size, data, off - 4, big_endian, 'Position', parent)
	if parent:
		if pos == -1:
			hd.model.set(parent, 1, 'not defined')
		else:
			pos = rfract(data, off - 4, big_endian)[0]
			hd.model.set(parent, 1, "%s / '%s' / %s"  % (key2txt(typ, type_map), fill_char, dim2txt(pos)))
	return off

def _add_para_format(hd, size, data, off, version, dummy):
	off += 1
	(align, off) = rdata(data, off, '>B')
	add_iter(hd, "Alignment", key2txt(align, align_map), off - 1, 1, '>B')
	off += 2
	off = add_dim(hd, size, data, off, big_endian, 'Left indent')
	off = add_dim(hd, size, data, off, big_endian, 'First line')
	off = add_dim(hd, size, data, off, big_endian, 'Right indent')
	(lead, off) = rdata(data, off, '>I')
	if lead == 0:
		add_iter(hd, 'Leading', 'auto', off - 4, 4, '>I')
	else:
		off = add_dim(hd, size, data, off - 4, big_endian, 'Leading')
	off = add_dim(hd, size, data, off, big_endian, 'Space before')
	off = add_dim(hd, size, data, off, big_endian, 'Space after')
	for i in range(0, 20):
		tabiter = add_iter(hd, 'Tab %d' % (i + 1), '', off, 6, '6s')
		off = _add_tab(hd, size, data, off, version, tabiter)
        return off

def add_para_format(hd, size, data, version, dummy):
	off = 0
	(uses, off) = rdata(data, off, '>H')
	add_iter(hd, 'Use count', uses, off - 2, 2, '>H')
	off = _add_para_format(hd, size, data, off, version, dummy)

def add_para_style(hd, size, data, fmt, version, encoding):
        off = 0
	off = _add_char_format(hd, size, data, off, version, '')
	off = _add_para_format(hd, size, data, off, version, '')
	off += 10
	_add_name2(hd, size, data, off, fmt)

ids = {
	'char_format': add_char_format,
	'color': add_color,
	'colors': add_colors,
	'fonts': add_fonts,
	'hj': add_hj,
	'object': add_saved,
	'page': add_saved,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
