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

	def tip(self):
		return 'seed: %x' % self.seed

color_model_map = {
	0: 'HSB',
	1: 'RGB',
	2: 'CMYK',
}

type_map = {
	0: 'Line',
	1: 'Orthogonal line',
	3: 'Text',
	11: 'Group',
	12: 'Rectangle / Picture',
	13: 'Cornered rectangle / Picture',
	14: 'Oval / Picture',
	15: 'Bezier / Picture',
}

v31_type_to_shape_content_map = {
	0: (0, 2),
	1: (1, 2),
	3: (2, 3),
	11: (2, 1),
	12: (2, 5),
	13: (3, 5),
	14: (4, 5),
	15: (5, 5),
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

def _read_name2(data, offset, fmt):
	rstr = read_c_str if fmt() == LITTLE_ENDIAN else read_pascal_str
	(name, off) = rstr(data, offset)
	if (off - offset) % 2 == 1:
		off += 1
	return name, off

def handle_hj(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('hj', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, encoding, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('para_format', fmt, version, encoding), data, parent)

def _parse_collection(page, data, offset, end, parent, fmt, version, encoding, handler, size):
	i = 0
	off = offset
	while off < end:
		if encoding:
			handler(page, data[off:off + size], parent, fmt, version, encoding, i)
		else:
			handler(page, data[off:off + size], parent, fmt, version, i)
		off += size
		i += 1
	return off

def _parse_collection_named(page, data, offset, end, parent, fmt, version, handler, name_offset, init=0):
	i = init
	off = offset
	while off < end:
		start = off
		(name, off) = _read_name2(data, off + name_offset, fmt)
		handler(page, data[start:off], parent, fmt, version, i, name)
		i += 1
	return off

def parse_record(page, data, offset, parent, fmt, version, name):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, name, 'qxp33', ('record', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_fonts(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, 'Fonts', 'qxp33', ('fonts', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_physical_fonts(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, 'Physical fonts', 'qxp33', ('physical_fonts', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_colors(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Colors', 'qxp33', ('colors', fmt, version), data[off - 4:off + length], parent)
	off += 1
	(count, off) = rdata(data, off, fmt('B'))
	off += 32
	for i in range(0, count):
		start = off
		(index, off) = rdata(data, off, fmt('B'))
		off += 49
		(name, off) = _read_name2(data, off, fmt)
		add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', ('color', fmt, version), data[start:off], reciter)
	return offset + 4 + length

def parse_para_styles(page, data, offset, parent, fmt, version, encoding):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Paragraph styles', 'qxp33', ('record', fmt, version), data[off - 4:off + length], parent)
	end = off + length
	while off < end:
		start = off
		off += 298
		(idx, off) = rdata(data, off, fmt('H'))
		off += 6
		(name, off) = _read_name2(data, off, fmt)
		add_pgiter(page, '[%d] %s' % (idx, name), 'qxp33', ('para_style', fmt, version, encoding), data[start:off], reciter)
	return off

def parse_hjs(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'H&Js', 'qxp33', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_collection_named(page, data, off, off + length, reciter, fmt, version, handle_hj, 48)

def parse_tools_prefs(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	toolsiter = add_pgiter(page, 'Tools preferences', 'qxp33', ('tools_prefs', fmt, version), data[off - 4:off + length], parent)
	add_pgiter(page, 'Orthogonal line', 'qxp33', (), data[off:off + 34], toolsiter)
	off += 34
	add_pgiter(page, 'Line', 'qxp33', (), data[off:off + 34], toolsiter)
	off += 34
	add_pgiter(page, 'Text', 'qxp33', (), data[off:off + 72], toolsiter)
	off += 72
	add_pgiter(page, 'Rectangle', 'qxp33', (), data[off:off + 72], toolsiter)
	off += 72
	add_pgiter(page, 'Cornered rectangle', 'qxp33', (), data[off:off + 72], toolsiter)
	off += 72
	add_pgiter(page, 'Oval', 'qxp33', (), data[off:off + 72], toolsiter)
	off += 72
	add_pgiter(page, 'Bezier', 'qxp33', (), data[off:off + 74], toolsiter)
	off += 74
	add_pgiter(page, 'Zoom', 'qxp33', ('tool_zoom', fmt, version), data[off:off + 12], toolsiter)
	off += 12
	return off

def parse_char_formats(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Character formats', 'qxp33', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_collection(page, data, off, off + length, reciter, fmt, version, None, handle_char_format, 46)

def parse_para_formats(page, data, offset, parent, fmt, version, encoding):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Paragraph formats', 'qxp33', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_collection(page, data, off, off + length, reciter, fmt, version, encoding, handle_para_format, 256)

def _add_corner_radius(hd, data, off, fmt):
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	return off

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
	add_iter(hd, 'Type', key2txt(typ, type_map, typ), off - 1, 1, fmt('B'), tip=obfctx.tip())
	(color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Color index', color, off - 1, 1, fmt('B'))
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'))
	(content, off) = rdata(data, off, fmt('I'))
	content = obfctx.deobfuscate(content & 0xffff, 2)
	content_iter = add_iter(hd, 'Content index?', hex(content), off - 4, 4, fmt('I'), tip=obfctx.tip())
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', qxpbflag2txt(flags, obj_flags_map, fmt), off - 1, 1, fmt('B'))
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
	if version >= VERSION_3_3:
		(content_type, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Content type?', key2txt(content_type, content_type_map), off - 1, 1, fmt('B'))
		(shape, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Shape type', key2txt(shape, shape_types_map), off - 1, 1, fmt('B'))
		off = _add_corner_radius(hd, data, off, fmt)
	else:
		shape, content_type = v31_type_to_shape_content_map[typ]
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
	(style, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Frame style', key2txt(style, frame_style_map), off - 1, 1, fmt('B'))
	return off

def add_gradient(hd, data, offset, fmt):
	off = offset
	gr_iter = add_iter(hd, 'Gradient', '', off, 34, '%ds' % 34)
        (gradient_length, off) = rdata(data, off, fmt('I')) 
	add_iter(hd, 'length', gradient_length, off - 4, 4, fmt('I'))
        endOffset=off+gradient_length
	off += 6
	(xt, off) = rdata(data, off, '4s')
	add_iter(hd, 'Extension mark?', 'Cool Blends XTension' if xt == 'QXCB' else xt, off - 4, 4, '4s', parent=gr_iter)
	(typ, off) = rdata(data, off, fmt('H'))
	typ = typ & 0xff
	add_iter(hd, 'Type', key2txt(typ, gradient_type_map), off - 2, 2, fmt('H'), parent=gr_iter)
	off += 4
	(color2, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Second color index', color2, off - 1, 1, fmt('B'), parent=gr_iter)
	off += 1
	(gr_shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (gr_shade * 100), off - 4, 4, fmt('i'), parent=gr_iter)
	(angle, off) = rfract(data, off, fmt)
	add_iter(hd, 'Angle', '%.2f deg' % angle, off - 4, 4, fmt('i'), parent=gr_iter)
	off += 4
	return endOffset

def add_bezier_data(hd, data, offset, fmt, name='Bezier data'):
	off = offset
	(bezier_data_length, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '%s length' % name, bezier_data_length, off - 4, 4, fmt('I'))
	end_off = off + bezier_data_length
	bezier_iter = add_iter(hd, name, '', off, bezier_data_length, '%ds' % bezier_data_length)
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

def add_runaround(hd, data, offset, fmt):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, 'Runaround length', length, off - 4, 4, fmt('I'))
	runiter = add_iter(hd, 'Runaround', '', off, length, '%ds' % length)
	off = add_dim(hd, off + 4, data, off, fmt, 'Top', runiter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Left', runiter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Bottom', runiter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Right', runiter)
	return off

def add_text_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	hd.model.set(header.content_iter, 0, "Starting block of text chain")
	off = add_frame(hd, data, off, fmt)
	off = add_dim(hd, off + 4, data, off, fmt, 'Runaround %s' % ('top' if header.shape == 2 else 'outset'))
	(rid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Runaround ID', hex(rid), off - 4, 4, fmt('I'))
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
	(next_index, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Next linked list index?', next_index, off - 4, 4, fmt('I'))
	(id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Some link-related ID?', hex(id), off - 4, 4, fmt('I'))
	off += 4
	if header.shape == 5:
		off = add_bezier_data(hd, data, off, fmt)
	if header.content_index == 0 or toff == 0:
		off += 4
		(fid, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'File info ID', hex(fid), off - 4, 4, fmt('I'))
		off += 4
		if fid != 0:
			off = add_file_info(hd, data, off, fmt)
		if header.content_index == 0:
			off += 12
	if rid != 0:
		off = add_runaround(hd, data, off, fmt)
	header.linked_text_offset = toff
	# Run Text Around All Sides not supported by qxp33
	return off

def add_picture_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	hd.model.set(header.content_iter, 0, "Picture block?")
	off = add_frame(hd, data, off, fmt)
	off = add_dim(hd, off + 4, data, off, fmt, 'Runaround %s' % ('top' if header.shape == 2 else 'outset'))
        
	if version >= VERSION_3_3:
		(rid, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Runaround ID', hex(rid), off - 4, 4, fmt('I'))
		off += 2
		(fid, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'FileInfo ID', hex(fid), off - 4, 4, fmt('I'))
		off += 14
	else:
		rid = 0
		off += 4
		if header.typ == 13:
			off = _add_corner_radius(hd, data, off, fmt)
			corners_map = {0: 'Beveled', 1: 'Rounded', 2: 'Concave'}
			(corners, off) = rdata(data, off, fmt('B'))
			add_iter(hd, 'Corners', key2txt(corners, corners_map), off - 1, 1, fmt('B'))
		elif header.typ == 15:
			(bid, off) = rdata(data, off, fmt('I'))
			add_iter(hd, 'Bezier ID?', hex(bid), off - 4, 4, fmt('I'))
			off += 1
		else:
			off += 5
                off += 1
		(fid, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'FileInfo ID', hex(fid), off - 4, 4, fmt('I'))
		off += 14
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
	(uid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'UnknownId',"%x"%uid, off - 4, 4, fmt('I'))
	off += 4
	if header.shape == 5:
		off = add_bezier_data(hd, data, off, fmt)
	if fid != 0:
		off = add_file_info(hd, data, off, fmt)
	if rid != 0:
		off = add_runaround(hd, data, off, fmt)
        if uid != 0:
	        (length, off) = rdata(data, off, fmt('I'))
	        add_iter(hd, 'Unknown data length', length, off - 4, 4, fmt('I'))
	        off += length
		#if cid != 0:
		#	off = add_bezier_data(hd, data, off, fmt, 'Clip path')
	return off

def add_empty_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt)
	off = add_dim(hd, off + 4, data, off, fmt, 'Runaround %s' % ('top' if header.shape == 2 else 'outset'))
	(rid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Runaround ID', hex(rid), off - 4, 4, fmt('I'))
	off += 74
	if header.shape == 5:
		off = add_bezier_data(hd, data, off, fmt)
	if rid != 0:
		off = add_runaround(hd, data, off, fmt)
	return off

def add_line(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_dim(hd, off + 4, data, off, fmt, 'Line width')
	(line_style, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Line style', key2txt(line_style, line_style_map), off - 1, 1, fmt('B'))
	(arrow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Arrowheads type', key2txt(arrow, arrow_map), off - 1, 1, fmt('B'))
	# qxp33 doesn't support custom runaround margins for lines and "Manual" type
	return off

def add_group(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off += 10
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '# of objects', count, off - 2, 2, fmt('H'))
	off += 2
	(listlen, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length of index list', listlen, off - 4, 4, fmt('I'))
	listiter = add_iter(hd, 'Index list', '', off, listlen, '%ds' % listlen)
	for i in range(1, count + 1):
		(idx, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Index %d' % i, idx, off - 4, 4, fmt('I'), parent=listiter)
	return off

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	objiter = add_pgiter(page, '[%d]' % index, 'qxp33', ('object', hd), data[offset:], parent)

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

def handle_page(page, data, offset, parent, fmt, version, index, master):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	pageiter = add_pgiter(page, 'Page', 'qxp33', ('page', hd), data[offset:offset + 110], parent)

	(counter, off) = rdata(data, off, fmt('H'))
	# This contains number of objects ever saved on the page
	add_iter(hd, 'Object counter / next object ID?', counter, off - 2, 2, fmt('H'))
	(off, settings_block_size, settings_blocks_count) = add_page_header(hd, off + 8, data, off, fmt)
	def _add_settings(name, offset):
		block_iter = add_iter(hd, name, '', offset, settings_block_size, '%ds' % settings_block_size)
		return add_page_settings(hd, settings_block_size, data, offset, fmt, version, block_iter)
	assert settings_blocks_count in (1, 2)
	if settings_blocks_count == 1:
		off = _add_settings('Page settings', off)
	elif settings_blocks_count == 2:
		off = _add_settings('Left page settings', off)
		off = _add_settings('Right page settings', off)
	for i in range(0, 2*settings_blocks_count + 2 + (1 if fmt() == LITTLE_ENDIAN else 0)):
                # for each blocks in range(settings_blocks_count+1):
                #      'Data%d'%(2*i) often empty ie sz=4, 'Data%d'%(2*i+1) often empty ie sz=0,
                #       but not always(search for 4PAN1T.E1.qxd)
                # windows file are followed by 4 bytes: unsure if this is also a data block or a int
		(length, off) = rdata(data, off, fmt('I'))
                if length==0:
		        add_iter(hd, 'Data%d'%i, length, off - 4, 4, fmt('I'))
                else:
                        add_pgiter(page, 'Data%d'%i, 'qxp4', '', data[off - 4:off+length], pageiter)
		off += length
	if fmt() == LITTLE_ENDIAN:
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
	pname = '[%d] %s%s page' % (index, key2txt(settings_blocks_count, npages_map), ' master' if master else '')
	if len(name) != 0:
		pname += ' "%s"' % name
	page.model.set_value(pageiter, 0, pname)
	page.model.set_value(pageiter, 2, off - offset)
	page.model.set_value(pageiter, 3, data[offset:off])
	return objs, pageiter, off

def parse_pages(page, data, offset, parent, fmt, version, obfctx, npages, nmasters):
	texts = set()
	pictures = set()
	off = offset
	master = True
	n = 0
	i = 1
	while n < npages + nmasters:
		start = off
		try:
			(objs, pgiter, off) = handle_page(page, data, start, parent, fmt, version, i, master)
			for j in range(0, objs):
				(header, off) = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
				if header.content_index and not header.linked_text_offset:
					if header.content_type == 3:
						texts.add(header.content_index)
					elif header.content_type == 5:
						pictures.add(header.content_index)
				obfctx = obfctx.next()
			if master and i == nmasters:
				master = False
				i = 0
			i += 1
			n += 1
		except:
			traceback.print_exc()
			break
	return texts, pictures, off

def handle_document(page, data, parent, fmt, version, hdr):
	obfctx = ObfuscationContext(hdr.seed, hdr.inc)
	off = 0
	off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	off = parse_record(page, data, off, parent, fmt, version, 'Print settings')
	off = parse_record(page, data, off, parent, fmt, version, 'Page setup')
	off = parse_record(page, data, off, parent, fmt, version, 'Dictionary')
	off = parse_fonts(page, data, off, parent, fmt, version)
	if version >= VERSION_3_3:
		off = parse_physical_fonts(page, data, off, parent, fmt, version)
	off = parse_colors(page, data, off, parent, fmt, version)
	off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	off = parse_para_styles(page, data, off, parent, fmt, version, hdr.encoding)
	off = parse_hjs(page, data, off, parent, fmt, version)
	off = parse_tools_prefs(page, data, off, parent, fmt, version)
	off = parse_char_formats(page, data, off, parent, fmt, version)
	off = parse_para_formats(page, data, off, parent, fmt, version, hdr.encoding)
	off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	pagesstart = off
	pagesiter = add_pgiter(page, 'Pages', 'qxp33', (), data[off:], parent)
	(texts, pictures, off) = parse_pages(page, data, off, pagesiter, fmt, version, obfctx, hdr.pages, hdr.masters)
        try:
	        page.model.set_value(pagesiter, 2, off - pagesstart)
	        page.model.set_value(pagesiter, 3, data[pagesstart:off])
	        (fonts, off) = parse_tracking_index(page, data, off, parent, fmt, version)
	        (kernings, off) = parse_tracking(page, data, off, parent, fmt, version, fonts)
	        off = parse_kerning_spec(page, data, off, parent, fmt, version)
	        for (i, font) in reversed(sorted(zip(kernings, fonts))):
		        if i == 0:
			        break
		        off = parse_kerning(page, data, off, parent, fmt, version, hdr.encoding, i, font)
	        off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	        off = parse_hyph_exceptions(page, data, off, parent, fmt, version, hdr.encoding)
	        if off < len(data):
		        add_pgiter(page, 'Tail', 'qxp4', (), data[off:], parent)
        except:
		traceback.print_exc()
	return texts, pictures

def add_header(hd, size, data, fmt, version):
	(header, off) = add_header_common(hd, size, data, fmt)
        if version==VERSION_3_3 and header.bigEndian:
                off += 14
                (fl,off)=rdata(data, off, fmt('B'))
	        add_iter(hd, 'Flags', "%x"%fl, off - 1, 1, fmt('B'))
                header.indexSize=4 if (fl&0x80)==0x80 else 2
                off += 37
        elif version==VERSION_3_1 and not header.bigEndian:
                off += 14
                (fl,off)=rdata(data, off, fmt('B'))
	        add_iter(hd, 'Flags', "%x"%fl, off - 1, 1, fmt('B'))
                header.indexSize=4 if (fl&0x1)==1 else 2
                off += 37
        else:
	        off += 52
	(header.pages, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of pages', header.pages, off - 2, 2, fmt('H'))
	off += 8
	off = add_margins(hd, size, data, off, fmt)
	(col, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'))
	off = add_dim(hd, size, data, off, fmt, 'Gutter width')
	off += 12
	(hmeasure, off) = rdata(data, off, '>B')
	add_iter(hd, 'H. measure', key2txt(hmeasure, measure_map), off - 1, 1, '>B')
	(vmeasure, off) = rdata(data, off, '>B')
	add_iter(hd, 'V. measure', key2txt(vmeasure, measure_map), off - 1, 1, '>B')
	(auto_ins, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Auto page insertion', key2txt(auto_ins, page_ins_map), off - 1, 1, fmt('B'))
	(framing, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Framing', key2txt(framing, framing_map), off - 1, 1, fmt('B'))
	off += 5
	(header.masters, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of master pages', header.masters, off - 1, 1, fmt('B'))
	off += 1
	(snap, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Snap distance', '%d pt' % snap, off - 1, 1, fmt('B'))
	off += 4
	off = add_fract_perc(hd, data, off, fmt, 'Auto leading')
	off = add_dim(hd, size, data, off, fmt, 'Greek below')
	off += 4
	off = add_dim(hd, size, data, off, fmt, 'Baseline grid start')
	off = add_dim(hd, size, data, off, fmt, 'Baseline grid increment')
	off += 8
	(above, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Break above', above, off - 2, 2, fmt('H'))
	off += 22
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off = add_dim(hd, size, data, off, fmt, 'Top offset')
	off += 4
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off = add_dim(hd, size, data, off, fmt, 'Bottom offset')
	off += 12
	off = add_dim(hd, size, data, off, fmt, 'Auto kern above')
	off = add_fract_perc(hd, data, off, fmt, 'Superscript offset')
	off = add_fract_perc(hd, data, off, fmt, 'Superscript v. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Superscript h. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Subscript offset')
	off = add_fract_perc(hd, data, off, fmt, 'Subscript v. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Subscript h. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Superior v. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Superior h. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Small caps v. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Small caps h. scale')
	off = add_fract_perc(hd, data, off, fmt, 'Flex space width')
	off += 4
	(lines, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of lines', lines, off - 2, 2, fmt('H'))
	(texts, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of text boxes', texts, off - 2, 2, fmt('H'))
	(header.pictures, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of picture boxes', header.pictures, off - 2, 2, fmt('H'))
	off += 6
	(header.seed, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation seed', hex(header.seed), off - 2, 2, fmt('H'))
	(header.inc, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation increment', hex(header.inc), off - 2, 2, fmt('H'))
	off += 28
	off = add_fract_perc(hd, data, off, fmt, 'Overprint limit')
	off = add_dim(hd, size, data, off, fmt, 'Auto amount')
	off = add_dim(hd, size, data, off, fmt, 'Indeterminate')
	tflags_map = {
		0x1: 'absolute',
		0x2: 'ignore white',
		0x4: 'process trap',
	}
	(tflags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Trapping flags', qxpbflag2txt(tflags, tflags_map, fmt), off - 1, 1, fmt('B'))
	return (header, size)

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
	(scale, off) = rfract(data, off, fmt)
	add_iter(hd, 'Scale', '%.2f%%' % (scale * 100), off - 4, 4, '4s')
	(color, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Color index', color, off - 1, 1, fmt('B'))
	off += 1
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, '4s')
	(kern, off) = rfract(data, off, fmt)
	add_iter(hd, 'Kern', kern, off - 4, 4, '4s') # unit: 1/200 em space
	(track, off) = rfract(data, off, fmt)
	add_iter(hd, 'Track amount', track, off - 4, 4, '4s')
	off = add_sfloat_perc(hd, data, off, fmt, 'Baseline shift')
	(control, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Control char(s)?', key2txt(control, {0: 'No'}, 'Yes'), off - 1, 1, fmt('B'))

def _add_para_format(hd, size, data, off, fmt, version, encoding):
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', qxpbflag2txt(flags, para_flags_map, fmt), off - 1, 1, fmt('B'))
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
	off += 2
	(hj, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'H&J index', hj, off - 1, 1, fmt('B'))
	off += 1
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
		add_iter(hd, 'Color index', color, off - 1, 1, fmt('B'), parent=ruleiter)
		(shade, off) = rfract(data, off, fmt)
		add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'), parent=ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From left', ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From right', ruleiter)
		(roff, off) = rfract(data, off, fmt)
		add_iter(hd, 'Offset', '%.2f%%' % (roff * 100), off - 4, 4, fmt('i'), parent=ruleiter)
	off += 8
	for i in range(0, 20):
		tabiter = add_iter(hd, 'Tab %d' % (i + 1), '', off, 8, '8s')
		off = add_tab(hd, size, data, off, fmt, version, encoding, tabiter)
	return off

def add_para_format(hd, size, data, fmt, version, encoding):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
	off = _add_para_format(hd, size, data, off, fmt, version, encoding)
	(style, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Style', style2txt(style), off - 1, 1, fmt('B'))

def add_para_style(hd, size, data, fmt, version, encoding):
	off = 0x28
	off = _add_para_format(hd, size, data, off, fmt, version, encoding)
	off += 10
	(idx, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Index', idx, off - 2, 2, fmt('H'))
	off += 6
	_add_name2(hd, size, data, off, fmt)

def add_hj(hd, size, data, fmt, version):
	off = add_hj_common(hd, size, data, 0, fmt, version)
	off += 4
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

def add_tool_zoom(hd, size, data, fmt, version):
	add_view_scale(hd, data, 0, fmt, version)

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
	'tool_zoom': add_tool_zoom,
}

# vim: set ft=python sts=4 sw=4 noet:
