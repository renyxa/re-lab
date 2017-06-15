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

def _read_name2(data, offset=0, end=0):
	off = data.find('\0', offset)
	name = data[offset:off]
	off += 1
	if (off - offset) % 2 == 1:
		off += 1
	return (name, off)

def _handle_collection_named(handler, name_offset):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = 0
		while off + name_offset < len(data):
			(name, end) = _read_name2(data, off + name_offset)
			(entry, off) = rdata(data, off, '%ds' % (end - off))
			handler(page, entry, parent, fmt, version, i, name)
			i += 1
	return hdl

def handle_para_style(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('para_style', fmt, version), data, parent)

def handle_hj(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('hj', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('para_format', fmt, version), data, parent)

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	start = offset
	def handle_gradient(offset):
		(gradient_id, _) = rdata(data, start + 24, fmt('I'))
		if gradient_id != 0:
			return offset + 34
		return offset

	off = offset
	(typ, off) = rdata(data, off, fmt('B'))
	typ = obfctx.deobfuscate(typ, 1)
	if typ == 0: # line
		off += 61
	if typ == 1: # orthogonal line
		off += 61
	elif typ == 3: # rectangle[text] / beveled-corner[text] / rounded-corner[text] / oval[text] / bezier[text] / line[text]
		off += 34
		(frame, off) = rdata(data, off, fmt('B'))
		off += 88
		(eh, off) = rdata(data, off, fmt('I'))
		off += 4
		if frame == 5:
			(length, off) = rdata(data, off, fmt('I')) # length of bezier data
			off += length
		if eh == 0: # TODO: this is a wild guess
			off += 12
		off += 12
		off = handle_gradient(off)
	elif typ == 5: # rectangle[none]
		off += 147
		off = handle_gradient(off)
	elif typ == 6: # beveled-corner[none] / rounded-corner[none]
		off += 147
		off = handle_gradient(off)
	elif typ == 7: # oval[none]
		off += 147
		off = handle_gradient(off)
	elif typ == 11: # group
		off += 81
	# rectangle[image], beveled-corner[image] / rounded-corner[image], oval[image], bezier[image]
	elif typ in [12, 13, 14, 15]:
		(bid, off) = rdata(data, off + 19, fmt('I'))
		off += 124
		if typ == 15:
			(length, off) = rdata(data, off, fmt('I')) # length of bezier data
			off += length
		if bid != 0:
			(length, off) = rdata(data, off, fmt('I')) # length of bitmap data
			off += length
		off = handle_gradient(off)
	add_pgiter(page, '[%d]' % index, 'qxp33', ('object', fmt, version, obfctx), data[start:off], parent)
	return off

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
				add_pgiter(page, 'Tail', 'qxp33', (), data[start:], parent)
				break
			off = start + 6 + size + 16 + npages * 12
			(name_len, off) = rdata(data, off, fmt('I'))
			(name, _) = rcstr(data, off)
			off += name_len
			(objs, off) = rdata(data, off, fmt('I'))
			pname = '[%d] %s%s page' % (i, key2txt(npages, npages_map), ' master' if m < nmasters else '')
			if len(name) != 0:
				pname += ' "%s"' % name
			pgiter = add_pgiter(page, pname, 'qxp33', ('page', fmt, version), data[start:off], parent)
			for j in range(1, objs + 1):
				off = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
				obfctx = obfctx.next()
			i += 1
			m += 1
		except:
			traceback.print_exc()
			add_pgiter(page, 'Tail', 'qxp33', (), data[start:], parent)
			break

handlers = {
	2: ('Print settings',),
	3: ('Page setup',),
	5: ('Fonts', None, 'fonts'),
	6: ('Physical fonts',),
	7: ('Colors', None, 'colors'),
	9: ('Paragraph styles', _handle_collection_named(handle_para_style, 306)),
	10: ('H&Js', _handle_collection_named(handle_hj, 48)),
	12: ('Character formats', handle_collection(handle_char_format, 46)),
	13: ('Paragraph formats', handle_collection(handle_para_format, 256)),
}

def handle_document(page, data, parent, fmt, version, obfctx, nmasters):
	off = 0
	i = 1
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
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp33', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		off += length
		i += 1
	doc = data[off:]
	dociter = add_pgiter(page, "[%d] Document" % i, 'qxp33', (), doc, parent)
	handle_doc(page, doc, dociter, fmt, version, obfctx, nmasters)

color_model_map = {
	0: 'HSB',
	1: 'RGB',
	2: 'CMYK',
}

box_types_map = {
	2: 'Rectangle',
	3: 'With corners',
	4: 'Oval',
	5: 'Freehand',
}

box_corners_map = {
	0: 'Default / Rounded',
	2: 'Beveled',
	4: 'Concave',
}

content_types_map = {
	2: 'None',
	3: 'Text',
	4: 'None',
	5: 'Picture',
}

obj_flags_map = {
	1: 'No color?',
	0x4: 'lock',
	0x10: 'suppress printout',
	0x20: 'no runaround?',
}

line_style_map = {
	0: 'Solid',
	1: 'Dotted',
	2: 'Dotted 2',
	3: 'Dash Dot',
	4: 'All Dots',
	0x80: 'Double',
	0x81: 'Thin-Thick',
	0x82: 'Thick-Thin',
	0x83: 'Thin-Thick-Thin',
	0x84: 'Thick-Thin-Thick',
	0x85: 'Triple'
}

def _add_name2(hd, size, data, offset, title='Name'):
	(name, off) = _read_name2(data, offset, size)
	add_iter(hd, title, name, offset, off - offset, '%ds' % (off - offset))
	return off

def add_char_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
	off += 2
	(flags, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 4, 4, fmt('I'))
	(fsz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Font size, pt', fsz, off - 4, 4, fmt('I'))
	off += 2
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index', color, off - 1, 1, fmt('B'))

def _add_para_format(hd, size, data, off, fmt, version):
	(flags, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Flags', bflag2txt(flags, para_flags_map), off - 2, 2, fmt('H'))
	off += 1
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
	for rule in ('above', 'below'):
		ruleiter = add_iter(hd, 'Rule %s' % rule, '', off, 22, '22s')
		off = add_dim(hd, size, data, off, fmt, 'Width', parent=ruleiter)
		(line_style, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Style', key2txt(line_style, line_style_map), off - 1, 1, fmt('B'), parent=ruleiter)
		(color, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Color index?', color, off - 1, 1, fmt('B'), parent=ruleiter)
		(shade, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Shade', '%.2f%%' % (shade / float(1 << 16) * 100), off - 2, 2, fmt('H'), parent=ruleiter)
		off += 2
		off = add_dim(hd, size, data, off, fmt, 'From left', ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From right', ruleiter)
		(roff, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Offset', '%.2f%%' % (roff / float(1 << 16) * 100), off - 2, 2, fmt('H'), parent=ruleiter)
		off += 2
	off += 8
	for i in range(0, 20):
		tabiter = add_iter(hd, 'Tab %d' % (i + 1), '', off, 8, '8s')
		type_map = {0: 'left', 1: 'center', 2: 'right', 3: 'align on / decimal'}
		(typ, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Type', key2txt(typ, type_map), off - 1, 1, fmt('B'), parent=tabiter)
		(align_char, off) = rdata(data, off, '1s')
		add_iter(hd, 'Align at char', align_char, off - 1, 1, '1s', parent=tabiter)
		(fill_char, off) = rdata(data, off, '1s')
		add_iter(hd, 'Fill char', fill_char, off - 1, 1, '1s', parent=tabiter)
		off += 1
		(pos, off) = rdata(data, off, fmt('i'))
		if pos == -1:
			add_iter(hd, 'Position', 'not defined', off - 4, 4, fmt('i'), parent=tabiter)
		else:
			off = add_dim(hd, size, data, off - 4, fmt, 'Position', tabiter)
	return off

def add_para_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
	_add_para_format(hd, size, data, off, fmt, version)

def add_para_style(hd, size, data, fmt, version):
	off = 0x28
	_add_para_format(hd, size, data, off, fmt, version)
	off += 18
	_add_name2(hd, size, data, off)

def add_hj(hd, size, data, fmt, version):
	off = 48
	_add_name2(hd, size, data, off)

def add_fonts(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of fonts', count, off - 2, 2, fmt('H'))
	i = 0
	while i < count:
		(index, off) = rdata(data, off, fmt('H'))
		(name, off) = rcstr(data, off)
		(full_name, off) = rcstr(data, off)
		font_len = 2 + len(name) + len(full_name) + 2
		font_iter = add_iter(hd, 'Font %d' % i, '%d, %s' % (index, name), off - font_len, font_len, '%ds' % font_len)
		add_iter(hd, 'Font %d index' % i, index, off - font_len, 2, fmt('H'), parent=font_iter)
		add_iter(hd, 'Font %d name' % i, name, off - font_len + 2, len(name) + 1, '%ds' % (len(name) + 1), parent=font_iter)
		add_iter(hd, 'Font %d full name' % i, full_name, off - font_len + 2 + len(name) + 1, len(full_name) + 1, '%ds' % (len(full_name) + 1), parent=font_iter)
		i += 1

def add_color_comp(hd, data, offset, fmt, name, parent=None):
	(c, off) = rdata(data, offset, fmt('H'))
	f = c / float(0x10000)
	perc = f * 100
	add_iter(hd, name, '%.1f%%' % perc, off - 2, 2, fmt('H'), parent=parent)
	return off

def add_colors(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	off += 1
	(count, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of colors', count, off - 1, 1, fmt('B'))
	off += 32
	i = 0
	while i < count:
		start_off = off
		color_iter = add_iter(hd, 'Color %d' % i, '', start_off, 1, '%ds' % 1)
		(index, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Index', index, off - 1, 1, fmt('B'), parent=color_iter)
		(spot_color, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Spot color', 'Black' if spot_color == 0x2d else 'index %d' % spot_color, off - 1, 1, fmt('B'), parent=color_iter)
		off = add_color_comp(hd, data, off, fmt, 'Red', color_iter)
		off = add_color_comp(hd, data, off, fmt, 'Green', color_iter)
		off = add_color_comp(hd, data, off, fmt, 'Blue', color_iter)
		off += 27
		(model, off) = rdata(data, off, fmt('B')) # probably doesn't matter and used only for UI
		add_iter(hd, 'Selected color model', key2txt(model, color_model_map), off - 1, 1, fmt('B'), parent=color_iter)
		off += 1
		(disable_spot_color, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Disable Spot color', disable_spot_color, off - 1, 1, fmt('B'), parent=color_iter)
		off += 12
		(name, off) = rcstr(data, off)
		add_iter(hd, 'Name', name, off - (len(name) + 1), len(name) + 1, '%ds' % (len(name) + 1), parent=color_iter)
		if off % 2 == 1:
			off += 1
			add_iter(hd, 'Padding', '', off - 1, 1, '1s', parent=color_iter)
		length = off - start_off
		hd.model.set (color_iter, 0, '%d, %s' % (index, name), 3, length, 4, '%ds' % length)
		i += 1

def add_page(hd, size, data, fmt, version):
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
	off += settings_blocks_count * 12 + 16
	off = add_pcstr4(hd, size, data, off, fmt)
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of objects', objs, off - 4, 4, fmt('I'))

def add_object(hd, size, data, fmt, version, obfctx):
	(typ, off) = rdata(data, 0, fmt('B'))
	add_iter(hd, 'Type', obfctx.deobfuscate(typ, 1), off - 1, 1, fmt('B'))
	(color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Color index', color, off - 1, 1, fmt('B'))
	off += 4
	(text, off) = rdata(data, off, fmt('H'))
	textiter = add_iter(hd, 'Starting block of text chain', hex(obfctx.deobfuscate(text, 2)), off - 2, 2, fmt('H'))
	off += 2
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, obj_flags_map), off - 1, 1, fmt('B'))
	off += 1
	(rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Rotation angle', '%.2f deg' % rot, off - 4, 4, fmt('i'))
	(skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Skew', '%.2f deg' % skew, off - 4, 4, fmt('i'))
	# Text boxes with the same link ID are linked.
	(lid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Link ID', hex(lid), off - 4, 4, fmt('I'))
	(gradient_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Gradient ID?', hex(gradient_id), off - 4, 4, fmt('I'))
	off += 5
	(corner, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Corner type', key2txt(corner, box_corners_map), off - 1, 1, fmt('B'))
	(content, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Content type?', key2txt(content, content_types_map), off - 1, 1, fmt('B'))
	(shape, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Shape type', key2txt(shape, box_types_map), off - 1, 1, fmt('B'))
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	if gradient_id != 0:
		gr_iter = add_iter(hd, 'Gradient', '', off, 34, '%ds' % 34)
		off += 20
		(color2, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Second color index', color2, off - 1, 1, fmt('B'), parent=gr_iter)
		off += 13
	off = add_dim(hd, size, data, off, fmt, 'Y1')
	off = add_dim(hd, size, data, off, fmt, 'X1')
	off = add_dim(hd, size, data, off, fmt, 'Y2')
	off = add_dim(hd, size, data, off, fmt, 'X2')
	off = add_dim(hd, size, data, off, fmt, 'Line width') # also used for frames
	(line_style, off) = rdata(data, off, fmt('B')) # looks like frames in 3.3 support only Solid
	add_iter(hd, 'Line style', key2txt(line_style, line_style_map), off - 1, 1, fmt('B'))
	(arrow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Arrowheads type', arrow, off - 1, 1, fmt('B'))
	off += 2
	(frame_color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Frame color index', frame_color, off - 1, 1, fmt('B'))
	off += 9
	(toff, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Offset into text', toff, off - 4, 4, fmt('I'))
	if toff > 0:
		hd.model.set(textiter, 0, "Index in linked list?")
	# TODO: separate objects
	if size > 112:
		off = 0x5e
		(pic_skew, off) = rfract(data, off, fmt)
		add_iter(hd, 'Picture skew', '%.2f deg' % pic_skew, off - 4, 4, fmt('i'))
		(pic_rot, off) = rfract(data, off, fmt)
		add_iter(hd, 'Picture angle', '%.2f deg' % pic_rot, off - 4, 4, fmt('i'))
		off = add_dim(hd, size, data, off, fmt, 'Offset accross')
		off -= 4
		(text_rot, off) = rfract(data, off, fmt)
		add_iter(hd, 'Text angle', '%.2f deg' % text_rot, off - 4, 4, fmt('i'))
		off = add_dim(hd, size, data, off, fmt, 'Offset down')
		off -= 4
		(text_skew, off) = rfract(data, off, fmt)
		add_iter(hd, 'Text skew', '%.2f deg' % text_skew, off - 4, 4, fmt('i'))
		(col, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'))

ids = {
	'char_format': add_char_format,
	'fonts': add_fonts,
	'colors': add_colors,
	'hj': add_hj,
	'object': add_object,
	'page': add_page,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
