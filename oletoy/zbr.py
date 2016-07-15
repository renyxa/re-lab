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
	0x2: 'Page',
	0x3: 'Layer',
	0xc: 'Start array',
	0xd: 'End array',
}

# defined later
obj_handlers = {}

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

def _add_obj_list(view, data, offset):
	off = offset
	while off + 2 < len(data):
		(typ, _) = rdata(data, off, '<I')
		off = view.add_pgiter('Object', add_obj, data, off, len(data) - off)
		if typ == 0xd:
			break
	return off

def add_obj_empty(view, data, offset):
	return offset

def add_obj_page(view, data, offset):
	off = offset + 65
	return _add_obj_list(view, data, off)

def add_obj_layer(view, data, offset):
	return len(data) - offset

obj_handlers = {
	0x2: add_obj_page,
	0x3: add_obj_layer,
	0xc: add_obj_empty,
	0xd: add_obj_empty,
}

def parse_header(page, data, offset, parent):
	add_pgiter(page, 'Header', 'zbr', 'header', data[0:104], parent)
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
