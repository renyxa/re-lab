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

from utils import *

def little_endian(fmt):
	return '<' + fmt

def big_endian(fmt):
	return '>' + fmt

def rfract(data, off, fmt):
	(fpart, off) = rdata(data, off, fmt('H'))
	(ipart, off) = rdata(data, off, fmt('h'))
	return (ipart + fpart / float(0x10000), off)

def dim2in(dim):
	return dim / 72.0

def deobfuscate(value, seed, n):
	assert n in [1, 2]
	if n == 1:
		assert value >> 8 == 0
		mask = 0xff
	else:
		assert value >> 16 == 0
		mask = 0xffff
	return (((value + seed) & 0xffff) - (((value & seed) << 1) & 0xffff) + (1 << 16)) & mask

VERSION_3_3 = 0x3f
VERSION_4 = 0x41
VERSION_6 = 0x43

def handle_collection(handler, size):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = 0
		while off + size <= len(data):
			(entry, off) = rdata(data, off, '%ds' % size)
			handler(page, entry, parent, fmt, version, i)
			i += 1
	return hdl

def add_length(hd, size, data, fmt, version, offset, name="Length"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, name, length, off - 4, 4, fmt('I'))
	return off

def add_pcstr4(hd, size, data, offset, fmt, name="Name"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, '%s length' % name, length, off - 4, 4, fmt('I'))
	(pstring, off) = rdata(data, off, '%ds' % length)
	string = pstring[0:pstring.find('\0')]
	add_iter(hd, name, string, off - length, length, '%ds' % length)
	return off

def add_page_header(hd, size, data, offset, fmt):
	(records_offset, off) = rdata(data, offset, fmt('I'))
	records_size = size - off - records_offset - 4
	add_iter(hd, 'Records offset', records_offset, off - 4, 4, fmt('I'))
	add_iter(hd, 'Settings', '', off, records_offset, '%ds' % (records_offset - off))
	add_iter(hd, 'Records', '', off + records_offset, records_size, '%ds' % (records_size))
	(settings_blocks_count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Settings blocks count', settings_blocks_count, off - 2, 2, fmt('H'))
	(idx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Index?', idx, off - 1, 1, fmt('B'))
	(cidx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Creation index', cidx, off - 1, 1, fmt('B'))
	return off, records_offset, settings_blocks_count

def add_page_bbox(hd, size, data, offset, fmt, parent=None):
	off = offset
	off += 2
	(top, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Top offset (in.)', dim2in(top), off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(left, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Left offset (in.)', dim2in(left), off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(bottom, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Bottom offset (in.)', dim2in(bottom), off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(right, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Right offset (in.)', dim2in(right), off - 2, 2, fmt('H'), parent=parent)
	return off

def add_margins(hd, size, data, offset, fmt, parent=None):
	(top, off) = rdata(data, offset, fmt('H'))
	add_iter(hd, 'Top margin (in.)', dim2in(top), off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(bottom, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Bottom margin (in.)', dim2in(bottom), off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(left, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Left margin (in.)', dim2in(left), off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(right, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Right margin (in.)', dim2in(right), off - 2, 2, fmt('H'), parent=parent)
	return off

def add_page_columns(hd, size, data, offset, fmt, parent=None):
	(col, off) = rdata(data, offset, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'), parent=parent)
	off += 4
	(gut, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Gutter width (in.)', dim2in(gut), off - 2, 2, fmt('H'), parent=parent)
	return off

def add_record(hd, size, data, fmt, version):
	add_length(hd, size, data, fmt, version, 0)

char_format_map = {0x1: 'bold', 0x2: 'italic', 0x4: 'underline'}

align_map = {0: 'left', 1: 'center', 2: 'right', 3: 'justified', 4: 'forced'}

# if 'keep lines together' is enabled, then 'all lines' is used (or Start/End if 'all lines' disabled)
para_flags_map = {0x1: 'keep with next', 0x2: 'lock to baseline grid', 0x8: 'keep lines together', 0x10: 'all lines'}

if __name__ == '__main__':
	def test_deobfuscate(seed, value, n, expected):
		assert deobfuscate(value, seed, n) == expected

	test_deobfuscate(0, 0, 1, 0)
	test_deobfuscate(0xa132, 0x31, 1, 0x3)
	test_deobfuscate(0xa132, 0xa133, 2, 0x1)
	test_deobfuscate(0x7236, 0x35, 1, 0x3)
	test_deobfuscate(0x7236, 0x34, 1, 0x2)

# vim: set ft=python sts=4 sw=4 noet:
