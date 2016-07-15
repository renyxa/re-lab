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

# An overview of the file structure is available here:
# http://www.fileformat.info/format/zbr/egff.htm . There are also sample
# files available from the same page.

import uniview
from utils import add_iter, add_pgiter, rdata, key2txt

obj_names = {
	0x1: 'Point',
	0x2: 'Page',
	0x3: 'Layer',
	0x4: 'Line',
	# gap
	0x6: 'Text',
	0x7: 'Ellipse',
	0x8: 'Rectangle',
	# gap
	0xc: 'Start array',
	0xd: 'End array',
}

# defined later
obj_handlers = {}

def _add_string(view, data, offset, name):
	(length, off) = rdata(data, offset, '<I')
	view.add_iter('%s length' % name, length, off - 4, 4, '<I')
	if length > 1:
		(text, off) = rdata(data, off, '%ds' % (length - 1))
		view.add_iter(name, unicode(text, 'cp1250'), off - length + 1, length, '%ds' % length)
	else:
		view.add_iter(name, '', off, 1, '1s')
	return off + 1

def add_obj(view, data, offset, length):
	(obj, off) = rdata(data, offset, '<H')
	view.add_iter('Type', key2txt(obj, obj_names), off - 2, 2, '<H')
	if obj_names.has_key(obj):
		view.set_label(obj_names[obj])
	if obj_handlers.has_key(obj):
		off = obj_handlers[obj](view, data, off)
	else:
		off = offset + length
	view.set_length(off - offset)
	return off

def _add_obj_list(view, data, offset, length=None):
	off = offset
	while off + 2 <= len(data):
		(typ, _) = rdata(data, off, '<H')
		off = view.add_pgiter('Object', add_obj, data, off, len(data) - off)
		if typ == 0xd:
			break
	return off

def _add_point_list(view, data, offset):
	return view.add_pgiter('Points', _add_obj_list, data, offset)

def add_style(view, data, offset, length):
	off = offset + 16
	if view.context.version == 2:
		off += 2
	(fill_color, off) = rdata(data, off, '<I')
	view.add_iter('Fill color', '#%x' % fill_color, off - 4, 4, '<I')
	return offset + length

def _add_obj_shape(view, data, offset):
	(x, off) = rdata(data, offset, '<I')
	# Points in the point list are relative to origin
	view.add_iter('Origin X', x, off - 4, 4, '<I')
	(y, off) = rdata(data, off, '<I')
	view.add_iter('Origin Y', y, off - 4, 4, '<I')
	(slen, off) = rdata(data, off, '<I')
	view.add_iter('Style length', slen, off - 4, 4, '<I')
	off = view.add_pgiter('Style', add_style, data, off, slen)
	if view.context.version == 4:
		off += 37
	(x1, off) = rdata(data, off, '<I')
	view.add_iter('Bounding box X1', x1, off - 4, 4, '<I')
	(y1, off) = rdata(data, off, '<I')
	view.add_iter('Bounding box Y1', y1, off - 4, 4, '<I')
	(x2, off) = rdata(data, off, '<I')
	view.add_iter('Bounding box X2', x2, off - 4, 4, '<I')
	(y2, off) = rdata(data, off, '<I')
	view.add_iter('Bounding box Y2', y2, off - 4, 4, '<I')
	off += 4
	return off

def add_obj_empty(view, data, offset):
	return offset

def add_obj_page(view, data, offset):
	off = offset + 17
	(dimX, off) = rdata(data, off, '<I')
	view.add_iter('A dimension?', dimX, off - 4, 4, '<I')
	(dimY, off) = rdata(data, off, '<I')
	view.add_iter('A dimension?', dimY, off - 4, 4, '<I')
	# As with ZMF, the page is placed on a canvas and all dimensions are
	# relative to the canvas.
	(left_margin, off) = rdata(data, off, '<i')
	view.add_iter('Left page margin?', left_margin, off - 4, 4, '<i')
	(top_margin, off) = rdata(data, off, '<i')
	view.add_iter('Top page margin?', top_margin, off - 4, 4, '<i')
	(right_margin, off) = rdata(data, off, '<i')
	view.add_iter('Right page margin?', right_margin, off - 4, 4, '<i')
	(bottom_margin, off) = rdata(data, off, '<i')
	view.add_iter('Bottom page margin?', bottom_margin, off - 4, 4, '<i')
	(width, off) = rdata(data, off, '<I')
	view.add_iter('Page width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	view.add_iter('Page height', height, off - 4, 4, '<I')
	(cwidth, off) = rdata(data, off, '<I')
	view.add_iter('Canvas width?', cwidth, off - 4, 4, '<I')
	(cheight, off) = rdata(data, off, '<I')
	view.add_iter('Canvas height?', cheight, off - 4, 4, '<I')
	off += 8
	return _add_obj_list(view, data, off)

def add_obj_layer(view, data, offset):
	off = _add_string(view, data, offset, 'Name')
	off += 6
	if view.context.version == 4:
		off += 2
	off = _add_obj_list(view, data, off)
	return off

def add_obj_point(view, data, offset):
	(x, off) = rdata(data, offset, '<i')
	view.add_iter('X', x, off - 4, 4, '<i')
	(y, off) = rdata(data, off, '<i')
	view.add_iter('Y', y, off - 4, 4, '<i')
	type_map = {1: 'Line point?', 2: 'Curve point?', 3: 'Curve control point?',}
	(typ, off) = rdata(data, off, '<B')
	view.add_iter('Type?', key2txt(typ, type_map), off - 1, 1, '<B')
	return off

def add_obj_line(view, data, offset):
	off = _add_obj_shape(view, data, offset)
	off = _add_point_list(view, data, off)
	return off

def add_obj_ellipse(view, data, offset):
	off = _add_obj_shape(view, data, offset)
	off += 32
	off = _add_point_list(view, data, off)
	return off

def add_obj_rectangle(view, data, offset):
	off = _add_obj_shape(view, data, offset)
	# TODO: It's not clear if the dims are relative to canvas or to the
	# shape's origin. All rectangles I've seen've had offset (0, 0).
	(tl_x, off) = rdata(data, off, '<i')
	view.add_iter('Top left corner X', tl_x, off - 4, 4, '<i')
	(tl_y, off) = rdata(data, off, '<i')
	view.add_iter('Top left corner Y', tl_y, off - 4, 4, '<i')
	(tr_x, off) = rdata(data, off, '<i')
	view.add_iter('Top right corner X', tr_x, off - 4, 4, '<i')
	(tr_y, off) = rdata(data, off, '<i')
	view.add_iter('Top right corner Y', tr_y, off - 4, 4, '<i')
	(br_x, off) = rdata(data, off, '<i')
	view.add_iter('Bottom right corner X', br_x, off - 4, 4, '<i')
	(br_y, off) = rdata(data, off, '<i')
	view.add_iter('Bottom right corner Y', br_y, off - 4, 4, '<i')
	(bl_x, off) = rdata(data, off, '<i')
	view.add_iter('Bottom left corner X', bl_x, off - 4, 4, '<i')
	(bl_y, off) = rdata(data, off, '<i')
	view.add_iter('Bottom left corner Y', bl_y, off - 4, 4, '<i')
	off += 4
	off = _add_point_list(view, data, off)
	return off

def add_text_style(view, data, offset, length):
	off = offset + 0x12
	# TODO: This is just a guess. But I don't see any length anywhere.
	(font, off) = rdata(data, off, '32s')
	view.add_iter('Font name', font[0:font.find('\0')], off - 32, 32, '32s')
	return offset + length

def add_obj_text(view, data, offset):
	off = _add_obj_shape(view, data, offset)
	off += 32
	(tslen, off) = rdata(data, off, '<I')
	view.add_iter('Text style length', tslen, off - 4, 4, '<I')
	off = view.add_pgiter('Text style', add_text_style, data, off, tslen)
	off = _add_string(view, data, off, 'Text')
	off = _add_point_list(view, data, off)
	return off

obj_handlers = {
	0x1: add_obj_point,
	0x2: add_obj_page,
	0x3: add_obj_layer,
	0x4: add_obj_line,
	0x6: add_obj_text,
	0x7: add_obj_ellipse,
	0x8: add_obj_rectangle,
	0xc: add_obj_empty,
	0xd: add_obj_empty,
}

def parse_header(page, data, offset, parent):
	add_pgiter(page, 'Header', 'zbr', 'header', data[0:104], parent)
	(page.version, off) = rdata(data, 2, '<H')
	return 104

def parse_preview(page, data, offset, parent):
	off = offset
	previter = add_pgiter(page, 'Preview bitmap', 'zbr', 0, data[off:off + 5264], parent)
	add_pgiter(page, 'DIB palette', 'zbr', 'palette', data[off:off + 64], previter)
	off += 64
	dibiter = add_pgiter(page, 'DIB data', 'zbr', 0, data[off:off + 5200], previter)
	return off + 5200

def parse_configuration(page, data, offset, parent):
	(length, off) = rdata(data, offset, '<I')
	length = int(length)
	data = data[off - 4:off + length]
	confiter = add_pgiter(page, 'Configuration', 'zbr', 'configuration', data, parent)
	add_pgiter(page, 'Local configuration', 'zbr', 'config_local', data[4:], confiter)
	return off + length

def parse_palette(page, data, offset, parent):
	(length, off) = rdata(data, offset, '<I')
	length = int(length)
	data = data[off - 4:off + length]
	palette_iter = add_pgiter(page, 'Color Palette', 'zbr', 'color_palette', data, parent)
	add_pgiter(page, 'Palette', 'zbr', 'palette', data[4:], palette_iter)
	return off + length

def parse_objects(page, data, offset, parent):
	objsiter = add_pgiter(page, 'Objects', 'zbr', 0, data[offset:], parent)
	view = uniview.PageView(page, 'zbr', objsiter, page)
	off = view.add_pgiter('Object', add_obj, data, offset)
	if off < len(data):
		add_pgiter(page, 'Trailer', 'zbr', '', data[off:], parent)

def _add_length(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length', length, 0, 4, '<I')

def add_color_palette(hd, size, data):
	_add_length(hd, size, data)

def add_configuration(hd, size, data):
	_add_length(hd, size, data)

def add_header(hd, size, data):
	(sig, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Signature', '0x%x' % sig, off - 2, 2, '<H')
	(version, off) = rdata(data, off, '<H')
	add_iter(hd, 'Version', version, off - 2, 2, '<H')
	(comment, off) = rdata(data, off, '100s')
	add_iter(hd, 'Comment', comment, off - 100, 100, '100s')
	assert off == 104

def add_palette(hd, size, data):
	n = 0
	off = 0
	while off + 4 <= size:
		(blue, off) = rdata(data, off, 'B')
		(green, off) = rdata(data, off, 'B')
		(red, off) = rdata(data, off, 'B')
		off += 1
		add_iter(hd, 'Color %d' % n, 'rgb(%d, %d, %d)' % (red, green, blue), off - 4, 4, '<I')
		n += 1
	assert off == size

zbr_ids = {
	'header': add_header,
	'color_palette': add_color_palette,
	'configuration': add_configuration,
	'palette': add_palette,
}

def open(data, page, parent):
	off = parse_header(page, data, 0, parent)
	off = parse_preview(page, data, off, parent)
	off = parse_configuration(page, data, off, parent)
	off = parse_palette(page, data, off, parent)
	parse_objects(page, data, off, parent)

# vim: set ft=python sts=4 sw=4 noet:
