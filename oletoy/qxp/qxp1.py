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

def add_header(hd, size, data, dummy, version):
    off = 0
    version_map = {0x1c: '???', 0x20: '1.10'}
    (ver, off) = rdata(data, off, '>H')
    add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, '>H')
    (ver, off) = rdata(data, off, '>H')
    add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, '>H')
    return (None, size)

def parse_record(page, data, offset, parent, version, name):
	(length, off) = rdata(data, offset, '>I')
	add_pgiter(page, name, 'qxp1', ('record', version), data[off - 4:off + length], parent)
	return off + length

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

def parse_pages(page, data, offset, parent, version):
	pass

def handle_document(page, data, parent, dummy, version, hdr):
	off = 0
	off = parse_formats(page, data, off, parent, version, 'Character formats', 'char_format', 16)
	off = parse_formats(page, data, off, parent, version, 'Paragraph formats', 'para_format', 150)
	off = parse_record(page, data, off, parent, version, 'Unknown') # ???
	pagesiter = add_pgiter(page, 'Pages', 'qxp1', (), data[off:], parent)
	return parse_pages(page, data, off, pagesiter, version)

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

def add_para_format(hd, size, data, version, dummy):
	pass

ids = {
	'char_format': add_char_format,
	'para_format': add_para_format,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
