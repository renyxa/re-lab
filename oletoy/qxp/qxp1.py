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

from utils import *
from qxp import *

def add_header(hd, size, data, dummy, version):
	off = 0
	version_map = {0x1c: '???', 0x20: '1.10'}
	(ver, off) = rdata(data, off, '>H')
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, '>H')
	(ver, off) = rdata(data, off, '>H')
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, '>H')
	off += 120
	measure_map = {
		0: 'Inches',
		1: 'Millimeters',
		2: 'Picas / Inches',
		3: 'Picas',
		4: 'Points',
		5: 'Inches Decimal',
		6: 'Ciceros',
	}
	(measure, off) = rdata(data, off, '>B')
	add_iter(hd, 'Measure', key2txt(measure, measure_map), off - 1, 1, '>B')
	(auto_hyph, off) = rdata(data, off, '>B')
	add_iter(hd, 'Auto hyphenation', key2txt(auto_hyph, {0: 'Off', 1: 'On'}), off - 1, 1, '>B')
	flags_map = {
		0x4: 'fract. widths',
		0x80: 'auto kerning',
		0x200: 'typesetting mode',
	}
	page_ins_map = {0: 'Off', 1: 'At end of story', 2: 'At end of section', 3: 'At end of document'}
	(flags, off) = rdata(data, off, '>H')
	hyphens = (flags >> 11) & 0x7
	add_iter(hd, 'Hyphens in a row', 'unlimited' if hyphens == 0 else hyphens, off - 2, 1, '>B')
	add_iter(hd, 'Flags', bflag2txt(flags & 0x7e7, flags_map), off - 2, 2, '>H')
	add_iter(hd, 'Auto page insertion', key2txt((flags >> 3) & 0x03, page_ins_map), off - 2, 2, '>H')
	off += 7
	(smallest, off) = rdata(data, off, '>B')
	add_iter(hd, 'Smallest word', smallest, off - 1, 1, '>B')
	(break_after, off) = rdata(data, off, '>B')
	add_iter(hd, 'Break after', break_after, off - 1, 1, '>B')
	(break_cap, off) = rdata(data, off, '>B')
	add_iter(hd, 'Break capitalized words', key2txt(break_cap, {0: 'Yes', 1: 'No'}), off - 1, 1, '>B')
	off += 16
	(pages, off) = rdata(data, off, '>H')
	add_iter(hd, '# of pages', pages, off - 2, 2, '>H')
	off += 30
	(spaces, off) = rdata(data, off, '>B')
	add_iter(hd, 'Spaces', spaces / 2, off - 1, 1, '>B')
	(overall, off) = rdata(data, off, '>B')
	add_iter(hd, 'Overall', overall / 2, off - 1, 1, '>B')
	off += 16
	off = add_sfloat_perc(hd, data, off, big_endian, 'Default auto leading')
	Header = namedtuple('Header', ('pages',))
	return (Header(pages), size)

def parse_formats(page, data, offset, parent, version, name, hdl, size):
	(length, off) = rdata(data, offset, '>I')
	end = off + length
	reciter = add_pgiter(page, name, 'qxp1', ('record', version), data[offset:end], parent)
	i = 0
	while off < end:
		add_pgiter(page, '[%d]' % i, 'qxp1', (hdl, version), data[off:off + size], reciter)
		off += size
		i += 1
	return off

def add_orthogonal_line(hd, data, offset, version):
	off = offset
	return off + 64

def add_line(hd, data, offset, version):
	off = offset
	return off + 64

def add_text(hd, data, offset, version):
	off = offset
	return off + 79

def add_rectangle(hd, data, offset, version):
	off = offset
	return off + 84

def add_rounded_rectangle(hd, data, offset, version):
	off = offset
	return off + 84

def add_ellipse(hd, data, offset, version):
	off = offset
	return off + 84

def parse_object(page, data, offset, parent, version, index):
	off = offset
	hd = HexDumpSave(off)
	objiter = add_pgiter(page, '', 'qxp1', ('object', hd), data[offset:], parent)
	type_map = {
		0: 'Line',
		1: 'Orthogonal line',
		3: 'Text',
		4: 'Rectangle',
		5: 'Rounded rectangle',
		6: 'Ellipse',
	}
	parser_map = {
		0: add_line,
		1: add_orthogonal_line,
		3: add_text,
		4: add_rectangle,
		5: add_rounded_rectangle,
		6: add_ellipse,
	}
	(typ, off) = rdata(data, off, '>B')
	type_str = key2txt(typ, type_map)
	add_iter(hd, 'Type', type_str, off - 1, 1, '>B')
	if parser_map.has_key(typ):
		off = parser_map[typ](hd, data, off, version)
	(last, off) = rdata(data, off, '>B')
	add_iter(hd, 'Last object', key2txt(last, {0: 'No', 1: '???', 2: 'Yes'}), off - 1, 1, '>B')
	page.model.set_value(objiter, 0, '[%d] %s' % (index, type_str))
	page.model.set_value(objiter, 2, off - offset)
	page.model.set_value(objiter, 3, data[offset:off])
	return (last == 2, off)

def add_page_prefix(hd, data, offset, version):
	off = offset + 4
	(index, off) = rdata(data, off, '>H')
	add_iter(hd, 'Index', index, off - 2, 2, '>H')
	off += 9
	return (index, off)

def parse_master(page, data, offset, parent, version):
	off = offset
	hd = HexDumpSave(off)
	pageiter = add_pgiter(page, '', 'qxp1', ('page', hd), data[offset:], parent)
	(index, off) = add_page_prefix(hd, data, off, version)
	(empty, off) = rdata(data, off, '>B')
	off += 81
	add_iter(hd, 'Empty', key2txt(empty, {1: 'No', 2: 'Yes'}), off - 1, 1, '>B')
	page.model.set_value(pageiter, 0, '[%d] Master page' % index)
	page.model.set_value(pageiter, 2, off - offset)
	page.model.set_value(pageiter, 3, data[offset:off])
	return off

def parse_page(page, data, offset, parent, version):
	off = offset
	hd = HexDumpSave(off)
	pageiter = add_pgiter(page, '', 'qxp1', ('page', hd), data[offset:], parent)
	(index, off) = add_page_prefix(hd, data, off, version)
	(empty, off) = rdata(data, off, '>B')
	add_iter(hd, 'Empty', key2txt(empty, {1: 'No', 2: 'Yes'}), off - 1, 1, '>B')
	page.model.set_value(pageiter, 0, '[%d] Page' % index)
	page.model.set_value(pageiter, 2, off - offset)
	page.model.set_value(pageiter, 3, data[offset:off])
	return (pageiter, empty == 2, off)

def parse_pages(page, data, offset, parent, version, npages):
	off = offset
	# ATM I assume there are fixed 2 master pages
	for i in (1, 2):
		off = parse_master(page, data, off, parent, version)
	for i in range(1, npages + 1):
		(pageiter, empty, off) = parse_page(page, data, off, parent, version)
		last = empty
		j = 1
		while not last and off < len(data):
			(last, off) = parse_object(page, data, off, pageiter, version, j)
			j += 1
	return ((), ())

def handle_document(page, data, parent, dummy, version, hdr):
	off = 0
	off = parse_formats(page, data, off, parent, version, 'Character formats', 'char_format', 16)
	off = parse_formats(page, data, off, parent, version, 'Paragraph formats', 'para_format', 150)
	pagesiter = add_pgiter(page, 'Pages', 'qxp1', (), data[off:], parent)
	try:
		return parse_pages(page, data, off, pagesiter, version, hdr.pages)
	except:
		traceback.print_exc()
		return ((), ())

def add_record(hd, size, data, version, dummy):
	(length, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Length', length, off - 4, 4, '>I')

def add_char_format(hd, size, data, version, dummy):
	off = 0
	(uses, off) = rdata(data, off, '>H')
	add_iter(hd, 'Use count', uses, off - 2, 2, '>H')
	(font, off) = rdata(data, off, '>H')
	add_iter(hd, 'Font index', font, off - 2, 2, '>H')
	(sz, off) = rdata(data, off, '>H')
	add_iter(hd, 'Font size', '%.1d' % (sz / 4.0), off - 2, 2, '>H')
	(flags, off) = rdata(data, off, '>H')
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 2, 2, '>H')
	(scale, off) = rdata(data, off, '>H')
	add_iter(hd, 'Scale', '%.0f%%' % (scale * 100.0 / 0x800), off - 2, 2, '>H')
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
	(color, off) = rdata(data, off, '>B')
	add_iter(hd, 'Color', key2txt(color, color_map), off - 1, 1, '>B')
	shade_map = {1: '10%', 2: '20%', 3: '40%', 4: '60%', 5: '80%', 6: 'Solid'}
	(shade, off) = rdata(data, off, '>B')
	add_iter(hd, 'Shade', key2txt(shade, shade_map), off - 1, 1, '>B')
	(track, off) = rdata(data, off, '>H')
	add_iter(hd, 'Track amount', '%.2f' % (track / 2.0), off - 2, 2, '>H')

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
			pos_str = '%.2f pt / %.2f in' % (pos, dim2in(pos))
			hd.model.set(parent, 1, "%s / '%s' / %s"  % (key2txt(typ, type_map), fill_char, pos_str))
	return off

def add_para_format(hd, size, data, version, dummy):
	off = 0
	(uses, off) = rdata(data, off, '>H')
	add_iter(hd, 'Use count', uses, off - 2, 2, '>H')
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

ids = {
	'char_format': add_char_format,
	'para_format': add_para_format,
	'object': add_saved,
	'page': add_saved,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
