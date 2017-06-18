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

import traceback
from utils import *
from qxp import *

box_flags_map = {
	0x80: 'h. flip',
	0x100: 'v. flip',
}

def _read_name(data, offset=0):
	(n, off) = rdata(data, offset, '64s')
	return n[0:n.find('\0')]

def handle_para_style(page, data, parent, fmt, version, index):
	name = _read_name(data)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('para_style', fmt, version), data, parent)

def handle_char_style(page, data, parent, fmt, version, index):
	name = _read_name(data)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('char_style', fmt, version), data, parent)

def handle_hj(page, data, parent, fmt, version, index):
	name = _read_name(data, 0x30)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('hj', fmt, version), data, parent)

def handle_dash_stripe(page, data, parent, fmt, version, index):
	name = _read_name(data, 0xb0)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('dash_stripe', fmt, version), data, parent)

def handle_list(page, data, parent, fmt, version, index):
	name = _read_name(data, 0)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('list', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp4', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp4', ('para_format', fmt, version), data, parent)

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	objiter = add_pgiter(page, '[%d]' % index, 'qxp4', ('object', hd), data[offset:offset + 1], parent)
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, obj_flags_map), off - 1, 1, fmt('B'))
	off += 1
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index', color, off - 2, 2, fmt('H'))
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'))
	(idx, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Index/ID?', idx, off - 2, 2, fmt('H'))
	off += 2
	(block, off) = rdata(data, off, fmt('I'))
	blockiter = add_iter(hd, 'Starting block of text chain', hex(block), off - 4, 4, fmt('I'))
	(rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Rotation angle', '%.2f deg' % rot, off - 4, 4, fmt('i'))
	(skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Skew?', '%.2f deg' % skew, off - 4, 4, fmt('i'))
	# Text boxes with the same link ID are linked.
	(lid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Link ID', hex(lid), off - 4, 4, fmt('I'))
	(gradient_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Gradient ID?', hex(gradient_id), off - 4, 4, fmt('I'))
	off += 8
	(flags, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Flags', bflag2txt(flags, box_flags_map), off - 2, 2, fmt('H'))
	content_type_map = {0: 'None', 2: 'Objects?', 3: 'Text', 4: 'Picture'}
	(content_type, off) = rdata(data, off, fmt('B'))
	content_type = obfctx.deobfuscate(content_type, 1)
	add_iter(hd, 'Content type', key2txt(content_type, content_type_map), off - 1, 1, fmt('B'))
	obfctx = obfctx.next_shift(content_type)
	hd.model.set(blockiter, 1, hex(obfctx.deobfuscate(block & 0xffff, 2)))
	shape_types_map = {
		1: 'Line',
		2: 'Orthogonal line',
		4: 'Bezier line',
		5: 'Rectangle',
		6: 'Rounded rectangle',
		7: 'Freehand',
		8: 'Beveled rectangle',
		9: 'Oval',
		11: 'Bezier',
	}
	(shape, off) = rdata(data, off, fmt('B'))
	shape = obfctx.deobfuscate(shape, 1)
	add_iter(hd, 'Shape type', key2txt(shape, shape_types_map), off - 1, 1, fmt('B'))
	off = add_dim(hd, off + 4, data, off, fmt, 'Line width') # also used for frames
	off += 6
	(gap_color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Gap color index', gap_color, off - 1, 1, fmt('B'))
	off += 1
	(gap_shade, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Gap shade', '%.2f%%' % (gap_shade / float(1 << 16) * 100), off - 2, 2, fmt('H'))
	off += 2
	(arrow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Arrowheads type', arrow, off - 1, 1, fmt('B'))
	off += 1
	(line_style, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Line style', key2txt(line_style, line_style_map), off - 1, 1, fmt('B'))
	off += 1
	off += 48
	off = add_dim(hd, off + 4, data, off, fmt, 'Y1')
	off = add_dim(hd, off + 4, data, off, fmt, 'X1')
	off = add_dim(hd, off + 4, data, off, fmt, 'Y2')
	off = add_dim(hd, off + 4, data, off, fmt, 'X2')
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	off += 20

	if content_type == 2:
		(count, off) = rdata(data, off, fmt('I'))
		add_iter(hd, '# of objects', count, off - 4, 4, fmt('I'))
		off += 4
		(listlen, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Length of index list', listlen, off - 4, 4, fmt('I'))
		listiter = add_iter(hd, 'Index list', '', off, listlen, '%ds' % listlen)
		for i in range(1, count + 1):
			(idx, off) = rdata(data, off, fmt('I'))
			add_iter(hd, 'Index %d' % i, idx, off - 4, 4, fmt('I'), parent=listiter)

	# off += 109
	# (toff, off) = rdata(data, off, fmt('I'))
	# add_iter(hd, 'Offset into text', toff, off - 4, 4, fmt('I'))
	# off += 32
	# (columns, off) = rdata(data, off, fmt('H'))
	# add_iter(hd, '# of columns', columns, off - 2, 2, fmt('H'))

	# update object title and size
	if content_type == 2:
		type_str = 'Group'
	else:
		type_str = "%s / %s" % (key2txt(shape, shape_types_map), key2txt(content_type, content_type_map))
	page.model.set_value(objiter, 0, "[%d] %s [%d]" % (index, type_str, idx))
	page.model.set_value(objiter, 2, off - offset)
	page.model.set_value(objiter, 3, data[offset:off])
	return (obfctx.next(), off)

def handle_doc(page, data, parent, fmt, version, obfctx, nmasters):
	off = 0
	i = 1
	m = 0
	while off < len(data):
		start = off
		try:
			(size, off) = rdata(data, off + 2, fmt('I'))
			npages_map = {1: 'Single', 2: 'Facing'}
			(npages, off) = rdata(data, off, fmt('H'))
			if size & 0xffff == 0:
				add_pgiter(page, 'Tail', 'qxp4', (), data[start:], parent)
				break
			off = start + 6 + size + 16 + npages * 12
			(name_len, off) = rdata(data, off, fmt('I'))
			(name, _) = rcstr(data, off)
			off += name_len
			pname = '[%d] %s%s page' % (i, key2txt(npages, npages_map), ' master' if m < nmasters else '')
			if len(name) != 0:
				pname += ' "%s"' % name
			(objs, off) = rdata(data, off, fmt('I'))
			pgiter = add_pgiter(page, pname, 'qxp4', ('page', fmt, version, obfctx), data[start:off], parent)
			objs = obfctx.deobfuscate(objs & 0xffff, 2)
			obfctx = obfctx.next_rev()
			for j in range(0, objs):
				(obfctx, off) = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
			i += 1
			m += 1
		except:
			traceback.print_exc()
			add_pgiter(page, 'Tail', 'qxp4', (), data[start:], parent)
			break

handlers1 = {
	2: ('Print settings',),
	3: ('Page setup',),
	6: ('Fonts', None, 'fonts'),
	7: ('Physical fonts',),
	8: ('Colors', None, 'colors'),
	9: ('Paragraph styles', handle_collection(handle_para_style, 244)),
	10: ('Character styles', handle_collection(handle_char_style, 140)),
	11: ('H&Js', handle_collection(handle_hj, 112)),
	12: ('Dashes & Stripes', handle_collection(handle_dash_stripe, 252)),
	13: ('Lists', handle_collection(handle_list, 324)),
	14: ('Index?', None, 'index'),
}

handlers2 = {
	0: ('Character formats', handle_collection(handle_char_format, 64)),
	2: ('Paragraph formats', handle_collection(handle_para_format, 100)),
}

def handle_document(page, data, parent, fmt, version, obfctx, nmasters):
	off = 0
	i = 1
	handlers = handlers1
	while off < len(data) and i < 15:
		name, hdl, hid = 'Record %d' % i, None, 'record'
		if handlers.has_key(i):
			name = handlers[i][0]
			if len(handlers[i]) > 1:
				hdl = handlers[i][1]
			if len(handlers[i]) > 2:
				hid = handlers[i][2]
		(length, off) = rdata(data, off, fmt('I'))
		record = data[off - 4:off + length]
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp4', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		if i == 14:
			(count2, _) = rdata(data, off, fmt('I'))
		off += length
		i += 1
	base = i
	doc_idx = i + count2 + 4
	handlers = handlers2
	while off < len(data) and i < doc_idx:
		name, hdl, hid = 'Record %d' % i, None, 'record'
		idx = i - base - count2
		if handlers.has_key(idx):
			name = handlers[idx][0]
			if len(handlers[idx]) > 1:
				hdl = handlers[idx][1]
			if len(handlers[idx]) > 2:
				hid = handlers[idx][2]
		(length, off) = rdata(data, off, fmt('I'))
		record = data[off - 4:off + length]
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp4', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		off += length
		i += 1
	doc = data[off:]
	dociter = add_pgiter(page, "[%d] Document" % i, 'qxp4', (), doc, parent)
	handle_doc(page, doc, dociter, fmt, version, obfctx, nmasters)

def add_header(hd, size, data, fmt, version):
	off = add_header_common(hd, size, data, fmt)
	off += 22
	(pages, off) = rdata(data, off, fmt('H'))
	pagesiter = add_iter(hd, 'Number of pages?', pages, off - 2, 2, fmt('H'))
	off += 8
	off = add_margins(hd, size, data, off, fmt)
	off = add_dim(hd, size, data, off, fmt, 'Gutter width')
	off = add_dim(hd, size, data, off, fmt, 'Top offset')
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off += 5
	(mpages, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of master pages', mpages, off - 1, 1, fmt('B'))
	off += 4
	(inc, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation increment', hex(inc), off - 2, 2, fmt('H'))
	off += 44
	(seed, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation seed', hex(seed), off - 2, 2, fmt('H'))
	sign = lambda x: 1 if x & 0x8000 == 0 else -1
	hd.model.set(pagesiter, 1, deobfuscate(pages, seed, 2) + sign(seed))
	off += 14
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off = add_dim(hd, size, data, off, fmt, 'Top offset')
	off += 68
	(lines, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of lines', lines, off - 2, 2, fmt('H'))
	(texts, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of text boxes', texts, off - 2, 2, fmt('H'))
	(pictures, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of picture boxes', pictures, off - 2, 2, fmt('H'))
	off += 102
	(counter, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Object counter/last id?', counter, off - 4, 4, fmt('I'))
	return (Header(seed, inc, mpages, pictures), size)

def add_picture(hd, size, data, fmt, version):
	off = 0
	(sz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Size', sz, off - 4, 4, fmt('I'))
	(sz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Size', sz, off - 4, 4, fmt('I'))
	off += 4
	(w, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Picture width', w, off - 2, 2, fmt('H'))
	(h, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Picture height', h, off - 2, 2, fmt('H'))
	off = 50
	add_iter(hd, 'Bitmap', '', off, sz, '%ds' % sz)

def _add_name(hd, size, data, offset=0, name="Name"):
	(n, off) = rdata(data, offset, '64s')
	add_iter(hd, name, n[0:n.find('\0')], off - 64, 64, '64s')
	return off

def add_colors(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	off += 14
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of colors (with different models)?', count, off - 2, 2, fmt('H'))
	off += 8
	(end, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Data end offset?', end, off - 2, 2, fmt('H'))

def add_para_style(hd, size, data, fmt, version):
	off = _add_name(hd, size, data)

def add_char_style(hd, size, data, fmt, version):
	off = _add_name(hd, size, data)

def add_hj(hd, size, data, fmt, version):
	off = 4
	(sm, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Smallest word', sm, off - 1, 1, fmt('B'))
	(min_before, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Minimum before', min_before, off - 1, 1, fmt('B'))
	(min_after, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Minimum after', min_after, off - 1, 1, fmt('B'))
	(hyprow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Hyphens in a row', 'unlimited' if hyprow == 0 else hyprow, off - 1, 1, fmt('B'))
	off = add_dim(hd, size, data, off, fmt, 'Hyphenation zone')
	justify_single_map = {0: 'Disabled', 0x80: 'Enabled'}
	(justify_single, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Don't justify single word", key2txt(justify_single, justify_single_map), off - 1, 1, fmt('B'))
	off += 1
	autohyp_map = {0: 'Disabled', 1: 'Enabled'}
	(autohyp, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Auto hyphenation', key2txt(autohyp, autohyp_map), off - 1, 1, fmt('B'))
	breakcap_map = {0: 'Disabled', 1: 'Enabled'}
	(breakcap, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Don't break capitalized words", key2txt(breakcap, breakcap_map), off - 1, 1, fmt('B'))
	off = 0x28
	off = add_dim(hd, size, data, off, fmt, 'Flush zone')
	off = _add_name(hd, size, data, 0x30)

def add_char_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
	off += 4
	(font, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Font index', font, off - 2, 2, fmt('H'))
	(flags, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 4, 4, fmt('I'))
	(fsz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Font size, pt', fsz, off - 4, 4, fmt('I'))
	off += 2
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index', color, off - 2, 2, fmt('H'))

def add_para_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
	off += 4
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, para_flags_map), off - 1, 1, fmt('B'))
	off += 2
	(align, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Alignment", key2txt(align, align_map), off - 1, 1, fmt('B'))
	(caps_lines, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Drop caps line count", caps_lines, off - 1, 1, fmt('B'))
	(caps_chars, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Drop caps char count", caps_chars, off - 1, 1, fmt('B'))
	(start, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Min. lines to remain", start, off - 1, 1, fmt('B'))
	(end, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Min. lines to carry over", end, off - 1, 1, fmt('B'))
	(hj, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'H&J index', hj, off - 2, 2, fmt('H'))
	off += 2
	off = add_dim(hd, size, data, off, fmt, 'Left indent')
	off = add_dim(hd, size, data, off, fmt, 'First line')
	off = add_dim(hd, size, data, off, fmt, 'Right indent')
	(lead, off) = rdata(data, off, fmt('I'))
	if lead == 0:
		add_iter(hd, 'Leading', 'auto', off - 4, 4, fmt('I'))
	else:
		off = add_dim(hd, size, data, off - 4, fmt, 'Leading')
	off = add_dim(hd, size, data, off, fmt, 'Space before')
	off = add_dim(hd, size, data, off, fmt, 'Space after')

def add_dash_stripe(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, 0xb0)

def add_list(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, 0)

def add_index(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of entries', count, off - 4, 4, fmt('I'))
	for i in range(0, count):
		(entry, off) = rdata(data, off, '8s')
		add_iter(hd, 'Entry %d' % i, '', off - 8, 8, '8s')

def add_page(hd, size, data, fmt, version, obfctx):
	off = 0
	(counter, off) = rdata(data, off, fmt('H'))
	# This contains number of objects ever saved on the page
	add_iter(hd, 'Object counter / next object ID?', counter, off - 2, 2, fmt('H'))
	(off, records_offset, settings_blocks_count) = add_page_header(hd, size, data, off, fmt)
	settings_block_size = (records_offset - 4) / settings_blocks_count
	for i in range(0, settings_blocks_count):
		block_iter = add_iter(hd, 'Settings block %d' % (i + 1), '', off, settings_block_size, '%ds' % settings_block_size)
		off = add_page_bbox(hd, size, data, off, fmt, block_iter)
		(id, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'ID?', hex(id), off - 4, 4, fmt('I'), parent=block_iter)
		hd.model.set(block_iter, 1, hex(id))
		off += 4
		(master_ind, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Master page index', '' if master_ind == 0xffff else master_ind, off - 2, 2, fmt('H'), parent=block_iter)
		off += 6
		(ind, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Index/Order', ind, off - 2, 2, fmt('H'), parent=block_iter)
		off += 2
		off = add_margins(hd, size, data, off, fmt, block_iter)
		off = add_page_columns(hd, size, data, off, fmt, block_iter)
		off += 4
	off += settings_blocks_count * 12 + 16
	off = add_pcstr4(hd, size, data, off, fmt)
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Number of objects', obfctx.deobfuscate(objs & 0xffff, 2), off - 4, 4, fmt('I'))

ids = {
	'char_format': add_char_format,
	'char_style': add_char_style,
	'dash_stripe': add_dash_stripe,
	'hj': add_hj,
	'index': add_index,
	'list': add_list,
	'fonts': add_fonts,
	'colors': add_colors,
	'object': add_saved,
	'page': add_page,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'picture': add_picture,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
