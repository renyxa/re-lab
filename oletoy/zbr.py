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

from utils import add_iter, add_pgiter, rdata

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

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
	return len(data)

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
