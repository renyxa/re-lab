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

def dim2in(dim):
	return dim / 72.0

def deobfuscate(value, seed):
	assert value >> 16 == 0
	if value >> 8 == 0:
		mask = 0xff
	else:
		mask = 0xffff
	return (value + seed - ((value & seed) << 1)) & mask

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

def add_record(hd, size, data, fmt, version):
	add_length(hd, size, data, fmt, version, 0)

char_format_map = {0x1: 'bold', 0x2: 'italic', 0x4: 'underline'}

align_map = {0: 'left', 1: 'center', 2: 'right', 3: 'justified', 4: 'forced'}

if __name__ == '__main__':
	def test_deobfuscate(seed, value, expected):
		assert deobfuscate(value, seed) == expected

	test_deobfuscate(0, 0, 0)
	test_deobfuscate(0xa132, 0x31, 0x3)
	test_deobfuscate(0xa132, 0xa133, 0x1)
	test_deobfuscate(0x7236, 0x35, 0x3)

# vim: set ft=python sts=4 sw=4 noet:
