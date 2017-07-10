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

class ObfuscationContext:
	def __init__(self, seed, inc):
		assert seed & 0xffff == seed
		assert inc & 0xffff == inc
		self.seed = seed
		self.inc = inc

	def next(self):
		return ObfuscationContext((self.seed + self.inc) & 0xffff, self.inc)

	def deobfuscate(self, value, n):
		return deobfuscate(value, self.seed, n)

color_model_map = {
	0: 'HSB',
	1: 'RGB',
	2: 'CMYK',
}

shape_types_map = {
	0: 'Line',
	1: 'Orthogonal line',
	2: 'Rectangle',
	3: 'Cornered rectangle',
	4: 'Oval',
	5: 'Bezier / Freehand',
}

box_flags_map = {
	0x80: 'h. flip',
	0x100: 'v. flip',
	0x200: 'beveled',
	0x400: 'concave',
}

content_type_map = {
	1: 'Objects?', # used by group
	2: 'None',
	3: 'Text',
	4: 'None',
	5: 'Picture',
}

# qxp33 doesn't support custom dashes & stripes
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

def _read_name2(data, offset, fmt):
	rstr = read_c_str if fmt() == LITTLE_ENDIAN else read_pascal_str
	(name, off) = rstr(data, offset)
	if (off - offset) % 2 == 1:
		off += 1
	return name, off

def _handle_collection(handler, size, init=0):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = init
		while off + size <= len(data):
			(entry, off) = rdata(data, off, '%ds' % size)
			handler(page, entry, parent, fmt, version, i)
			i += 1
	return hdl

def _handle_collection_named(handler, name_offset, init=0):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = init
		while off + name_offset < len(data):
			(name, end) = _read_name2(data, off + name_offset, fmt)
			(entry, off) = rdata(data, off, '%ds' % (end - off))
			handler(page, entry, parent, fmt, version, i, name)
			i += 1
	return hdl

def handle_colors(page, data, parent, fmt, version):
	(count, off) = rdata(data, 1, fmt('B'))
	off += 32
	for i in range(0, count):
		start = off
		(index, off) = rdata(data, off, fmt('B'))
		off += 49
		(name, off) = _read_name2(data, off, fmt)
		add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('color', fmt, version), data[start:off], parent)

def handle_para_style(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('para_style', fmt, version), data, parent)

def handle_hj(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('hj', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('para_format', fmt, version), data, parent)

class ObjectHeader(object):
	def __init__(self, typ, shape, link_id, content_index, content_type, content_iter):
		self.linked_text_offset = None
		self.typ = typ
		self.shape = shape
		self.link_id = link_id
		self.content_index = content_index
		self.content_type = content_type
		self.content_iter = content_iter

def add_object_header(hd, data, offset, fmt, version, obfctx):
	off = offset

	(typ, off) = rdata(data, off, fmt('B'))
	typ = obfctx.deobfuscate(typ, 1)
	add_iter(hd, 'Type', typ, off - 1, 1, fmt('B'))
	(color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Color index', color, off - 1, 1, fmt('B'))
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'))
	(content, off) = rdata(data, off, fmt('I'))
	content = obfctx.deobfuscate(content & 0xffff, 2)
	content_iter = add_iter(hd, 'Content index?', hex(content), off - 2, 2, fmt('H'))
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, obj_flags_map), off - 1, 1, fmt('B'))
	off += 1
	(rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Rotation angle', '%.2f deg' % rot, off - 4, 4, fmt('i'))
	(skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Skew', '%.2f deg' % skew, off - 4, 4, fmt('i'))
	# Text boxes with the same link ID are linked.
	(link_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Link ID', hex(link_id), off - 4, 4, fmt('I'))
	(gradient_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Gradient ID?', hex(gradient_id), off - 4, 4, fmt('I'))
	off += 4
	(flags2, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Flags (corners, flip)', bflag2txt(flags2, box_flags_map), off - 2, 2, fmt('H'))
	(content_type, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Content type?', key2txt(content_type, content_type_map), off - 1, 1, fmt('B'))
	(shape, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Shape type', key2txt(shape, shape_types_map), off - 1, 1, fmt('B'))
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	if gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	off = add_dim(hd, off + 4, data, off, fmt, 'Y1')
	off = add_dim(hd, off + 4, data, off, fmt, 'X1')
	off = add_dim(hd, off + 4, data, off, fmt, 'Y2')
	off = add_dim(hd, off + 4, data, off, fmt, 'X2')

	return ObjectHeader(typ, shape, link_id, content, content_type, content_iter), off

def add_frame(hd, data, offset, fmt):
	off = offset
	off = add_dim(hd, off + 4, data, off, fmt, 'Frame width')
	# looks like frames in 3.3 support only Solid style
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Frame shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'))
	(frame_color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Frame color index', frame_color, off - 1, 1, fmt('B'))
	return off

def add_gradient(hd, data, offset, fmt):
	off = offset
	gr_iter = add_iter(hd, 'Gradient', '', off, 34, '%ds' % 34)
	off += 10
	(xt, off) = rdata(data, off, '4s')
	add_iter(hd, 'Extension mark?', 'Cool Blends XTension' if xt == 'QXCB' else xt, off - 4, 4, '4s', parent=gr_iter)
	(typ, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Type', key2txt(typ, gradient_type_map), off - 1, 1, fmt('B'), parent=gr_iter)
	off += 5
	(color2, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Second color index', color2, off - 1, 1, fmt('B'), parent=gr_iter)
	off += 1
	(gr_shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (gr_shade * 100), off - 4, 4, fmt('i'), parent=gr_iter)
	(angle, off) = rfract(data, off, fmt)
	add_iter(hd, 'Angle', '%.2f deg' % angle, off - 4, 4, fmt('i'), parent=gr_iter)
	off += 4
	return off

def add_bezier_data(hd, data, offset, fmt):
	off = offset
	(bezier_data_length, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier data length', bezier_data_length, off - 4, 4, fmt('I'))
	end_off = off + bezier_data_length
	bezier_iter = add_iter(hd, 'Bezier data', '', off, bezier_data_length, '%ds' % bezier_data_length)
	off += 2
	off = add_dim(hd, off + 4, data, off, fmt, 'Start Y', parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Start X', parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'End Y', parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'End X', parent=bezier_iter)
	i = 1
	while off < end_off:
		off = add_dim(hd, off + 4, data, off, fmt, 'Y%d' % i, parent=bezier_iter)
		off = add_dim(hd, off + 4, data, off, fmt, 'X%d' % i, parent=bezier_iter)
		i += 1
	return off

def add_text_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	hd.model.set(header.content_iter, 0, "Starting block of text chain")
	off = add_frame(hd, data, off, fmt)
	off += 1
	off = add_dim(hd, off + 4, data, off, fmt, 'Runaround %s' % ('top' if header.shape == 2 else 'outset'))
	off += 4
	(toff, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Offset into text', toff, off - 4, 4, fmt('I'))
	if toff > 0:
		hd.model.set(header.content_iter, 0, "Index in linked list?")
	off += 2
	(text_flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Text flags (first baseline minimum, ...)', bflag2txt(text_flags, text_flags_map), off - 1, 1, fmt('B'))
	off += 1
	off = add_dim(hd, off + 4, data, off, fmt, 'Gutter width')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset top')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset left')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset right')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset bottom')
	(text_rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Text angle', '%.2f deg' % text_rot, off - 4, 4, fmt('i'))
	(text_skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Text skew', '%.2f deg' % text_skew, off - 4, 4, fmt('i'))
	(col, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of columns', col, off - 1, 1, fmt('B'))
	(vert, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Vertical alignment', key2txt(vert, vertical_align_map), off - 1, 1, fmt('B'))
	off = add_dim(hd, off + 4, data, off, fmt, 'Inter max (for Justified)')
	off = add_dim(hd, off + 4, data, off, fmt, 'First baseline offset')
	(next_index, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Next linked list index?', next_index, off - 2, 2, fmt('H'))
	off += 2
	(id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Some link-related ID?', hex(id), off - 4, 4, fmt('I'))
	off += 4
	if header.shape == 5:
		off = add_bezier_data(hd, data, off, fmt)
	if header.content_index == 0:
		off += 24
	else:
		if toff == 0:
			off += 12
			if next_index > 0:
				off += 4
	header.linked_text_offset = toff
	# Run Text Around All Sides not supported by qxp33
	return off

def add_picture_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	hd.model.set(header.content_iter, 0, "Picture block?")
	off = add_frame(hd, data, off, fmt)
	off += 1
	off = add_dim(hd, off + 4, data, off, fmt, 'Runaround %s' % ('top' if header.shape == 2 else 'outset'))
	off += 24
	(pic_rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Picture angle', '%.2f deg' % pic_rot, off - 4, 4, fmt('i'))
	(pic_skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Picture skew', '%.2f deg' % pic_skew, off - 4, 4, fmt('i'))
	off = add_dim(hd, off + 4, data, off, fmt, 'Offset accross')
	off = add_dim(hd, off + 4, data, off, fmt, 'Offset down')
	# scale values are different when picture is not empty, not sure why
	off = add_fract_perc(hd, data, off, fmt, 'Scale accross')
	off = add_fract_perc(hd, data, off, fmt, 'Scale down')
	off += 21
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Picture flags', bflag2txt(flags, picture_flags_map), off - 1, 1, fmt('B'))
	off += 8
	if header.shape == 5:
		off = add_bezier_data(hd, data, off, fmt)
	return off

def add_empty_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt)
	off += 1
	off = add_dim(hd, off + 4, data, off, fmt, 'Runaround %s' % ('top' if header.shape == 2 else 'outset'))
	off += 78
	if header.shape == 5:
		off = add_bezier_data(hd, data, off, fmt)
	return off

def add_line(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_dim(hd, off + 4, data, off, fmt, 'Line width')
	(line_style, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Line style', key2txt(line_style, line_style_map), off - 1, 1, fmt('B'))
	(arrow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Arrowheads type', arrow, off - 1, 1, fmt('B'))
	# qxp33 doesn't support custom runaround margins for lines and "Manual" type
	return off

def add_group(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off += 10
	(count, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of objects?', count, off - 4, 4, fmt('I'))
	(listlen, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length of index list?', listlen, off - 4, 4, fmt('I'))
	listiter = add_iter(hd, 'Index list', '', off, listlen, '%ds' % listlen)
	for i in range(1, count + 1):
		(idx, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Index %d' % i, idx, off - 4, 4, fmt('I'), parent=listiter)
	return off

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	objiter = add_pgiter(page, '[%d]' % index, 'qxp33', ('object', hd), data[offset:offset + 1], parent)

	(header, off) = add_object_header(hd, data, off, fmt, version, obfctx)

	# typ == 0: # line
	# typ == 1: # orthogonal line
	# typ == 3: # rectangle[text] / beveled-corner[text] / rounded-corner[text] / oval[text] / bezier[text] / freehand[text]
	# typ == 5: # rectangle[none]
	# typ == 6: # beveled-corner[none] / rounded-corner[none]
	# typ == 7: # oval[none]
	# typ == 8: # bezier[none] / freehand[none]
	# typ == 11: # group
	# typ == 12: # rectangle[image]
	# typ == 13: # beveled-corner[image] / rounded-corner[image]
	# typ == 14: # oval[image]
	# typ == 15: # bezier[image] / freehand[image]
	text = None
	if header.typ in [0, 1]:
		off = add_line(hd, data, off, fmt, version, obfctx, header)
	elif header.typ == 3:
		off = add_text_box(hd, data, off, fmt, version, obfctx, header)
	elif header.typ in [5, 6, 7, 8]:
		off = add_empty_box(hd, data, off, fmt, version, obfctx, header)
	elif header.typ == 11:
		off = add_group(hd, data, off, fmt, version, obfctx, header)
	elif header.typ in [12, 13, 14, 15]:
		off = add_picture_box(hd, data, off, fmt, version, obfctx, header)

	if header.typ == 11:
		type_str = 'Group'
	else:
		type_str = "%s (%s)" % (key2txt(header.shape, shape_types_map), key2txt(header.content_type, content_type_map))
	# update object title and size
	page.model.set_value(objiter, 0, "[%d] %s" % (index, type_str))
	page.model.set_value(objiter, 2, off - offset)
	page.model.set_value(objiter, 3, data[offset:off])
	return (header, off)

def handle_page(page, data, offset, parent, fmt, version, index, nmasters):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	pageiter = add_pgiter(page, 'Page', 'qxp33', ('page', hd), data[offset:offset + 110], parent)

	(counter, off) = rdata(data, off, fmt('H'))
	# This contains number of objects ever saved on the page
	add_iter(hd, 'Object counter / next object ID?', counter, off - 2, 2, fmt('H'))
	(off, records_offset, settings_blocks_count) = add_page_header(hd, off + 8, data, off, fmt)
	settings_block_size = (records_offset - 4) / settings_blocks_count
	for i in range(0, settings_blocks_count):
		block_iter = add_iter(hd, 'Settings block %d' % (i + 1), '', off, settings_block_size, '%ds' % settings_block_size)
		off = add_page_bbox(hd, off + 16, data, off, fmt, block_iter)
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
		off = add_margins(hd, off + 16, data, off, fmt, block_iter)
		off = add_page_columns(hd, off + 8, data, off, fmt, block_iter)
	off += settings_blocks_count * 12 + 12
	if fmt() == LITTLE_ENDIAN:
		off += 4
		(name, off) = add_pcstr4(hd, data, off, fmt)
	else:
		(name_data_length, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Name data length', name_data_length, off - 4, 4, fmt('I'))
		(name, _) = add_pascal_str(hd, data, off)
		off += name_data_length
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Number of objects', objs, off - 4, 4, fmt('I'))

	# update object title and size
	npages_map = {1: 'Single', 2: 'Facing'}
	pname = '[%d] %s%s page' % (index, key2txt(settings_blocks_count, npages_map), ' master' if index - 1 < nmasters else '')
	if len(name) != 0:
		pname += ' "%s"' % name
	page.model.set_value(pageiter, 0, pname)
	page.model.set_value(pageiter, 2, off - offset)
	page.model.set_value(pageiter, 3, data[offset:off])
	return objs, pageiter, off

def handle_doc(page, data, parent, fmt, version, obfctx, nmasters):
	texts = set()
	pictures = set()
	off = 0
	i = 1
	while off < len(data):
		start = off
		try:
			stop = rdata(data, off, fmt('I'))[0]
			if stop == 0x9e:
				add_pgiter(page, 'Tail', 'qxp33', (), data[start:], parent)
				break
			(objs, pgiter, off) = handle_page(page, data, start, parent, fmt, version, i, nmasters)
			for j in range(0, objs):
				(header, off) = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
				if header.content_index and not header.linked_text_offset:
					if header.content_type == 3:
						texts.add(header.content_index)
					elif header.content_type == 5:
						pictures.add(header.content_index)
				obfctx = obfctx.next()
			i += 1
		except:
			traceback.print_exc()
			add_pgiter(page, 'Tail', 'qxp33', (), data[start:], parent)
			break
	return texts, pictures

handlers = {
	2: ('Print settings',),
	3: ('Page setup',),
	5: ('Fonts', None, 'fonts'),
	6: ('Physical fonts', None, 'physical_fonts'),
	7: ('Colors', handle_colors, 'colors'),
	9: ('Paragraph styles', _handle_collection_named(handle_para_style, 306, 1)),
	10: ('H&Js', _handle_collection_named(handle_hj, 48)),
	12: ('Character formats', _handle_collection(handle_char_format, 46)),
	13: ('Paragraph formats', _handle_collection(handle_para_format, 256)),
}

def handle_document(page, data, parent, fmt, version, hdr):
	obfctx = ObfuscationContext(hdr.seed, hdr.inc)
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
	return handle_doc(page, doc, dociter, fmt, version, obfctx, hdr.masters)

def add_header(hd, size, data, fmt, version):
	off = add_header_common(hd, size, data, fmt)
	off += 52
	(pages, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of pages', pages, off - 2, 2, fmt('H'))
	off += 8
	off = add_margins(hd, size, data, off, fmt)
	(col, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'))
	off = add_dim(hd, size, data, off, fmt, 'Gutter width')
	off += 21
	(mpages, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of master pages', mpages, off - 1, 1, fmt('B'))
	off += 58
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off = add_dim(hd, size, data, off, fmt, 'Top offset')
	off += 4
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off = add_dim(hd, size, data, off, fmt, 'Bottom offset')
	off += 24
	(lines, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of lines', lines, off - 2, 2, fmt('H'))
	off += 40
	(texts, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of text boxes', texts, off - 2, 2, fmt('H'))
	(pictures, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of picture boxes', pictures, off - 2, 2, fmt('H'))
	off += 6
	(seed, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation seed', '%x' % seed, off - 2, 2, fmt('H'))
	(inc, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation increment', '%x' % inc, off - 2, 2, fmt('H'))
	return (Header(seed, inc, mpages, pictures), size)

def _add_name2(hd, size, data, offset, fmt, title='Name'):
	(name, off) = _read_name2(data, offset, fmt)
	add_iter(hd, title, name, offset, off - offset, '%ds' % (off - offset))
	return off

def add_char_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
	(font, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Font index', font, off - 2, 2, fmt('H'))
	(flags, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 2, 2, fmt('H'))
	off = add_dim(hd, size, data, off, fmt, 'Font size')
	off += 4
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
	off += 2
	(hj, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'H&J index', hj, off - 2, 2, fmt('H'))
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
		(shade, off) = rfract(data, off, fmt)
		add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'), parent=ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From left', ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From right', ruleiter)
		(roff, off) = rfract(data, off, fmt)
		add_iter(hd, 'Offset', '%.2f%%' % (roff * 100), off - 4, 4, fmt('i'), parent=ruleiter)
	off += 4
	for i in range(0, 20):
		tabiter = add_iter(hd, 'Tab %d' % (i + 1), '', off, 8, '8s')
		off = add_tab(hd, size, data, off, fmt, version, tabiter)
	return off

def add_para_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
	off = _add_para_format(hd, size, data, off, fmt, version)
	(style, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Style', style2txt(style), off - 2, 2, fmt('H'))

def add_para_style(hd, size, data, fmt, version):
	off = 0x28
	_add_para_format(hd, size, data, off, fmt, version)
	off += 18
	_add_name2(hd, size, data, off, fmt)

def add_hj(hd, size, data, fmt, version):
	off = 48
	_add_name2(hd, size, data, off, fmt)

def add_color_comp(hd, data, offset, fmt, name, parent=None):
	return add_sfloat_perc(hd, data, offset, fmt, name, parent=parent)

def add_colors(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	off += 1
	(count, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of colors', count, off - 1, 1, fmt('B'))

def add_color(hd, size, data, fmt, version):
	off = 0
	(index, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Index', index, off - 1, 1, fmt('B'))
	(spot_color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Spot color', 'Black' if spot_color == 0x2d else 'index %d' % spot_color, off - 1, 1, fmt('B'))
	off = add_color_comp(hd, data, off, fmt, 'Red')
	off = add_color_comp(hd, data, off, fmt, 'Green')
	off = add_color_comp(hd, data, off, fmt, 'Blue')
	off += 27
	(model, off) = rdata(data, off, fmt('B')) # probably doesn't matter and used only for UI
	add_iter(hd, 'Selected color model', key2txt(model, color_model_map), off - 1, 1, fmt('B'))
	off += 1
	(disable_spot_color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Disable Spot color', disable_spot_color, off - 1, 1, fmt('B'))
	off += 12
	_add_name2(hd, size, data, off, fmt)

ids = {
	'char_format': add_char_format,
	'fonts': add_fonts,
	'color': add_color,
	'colors': add_colors,
	'hj': add_hj,
	'object': add_saved,
	'page': add_saved,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'physical_fonts': add_physical_fonts,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
