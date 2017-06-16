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

class HexDumpSave:
	def __init__(self, offset):
		self.model = self.Model(offset)

	class Model:
		def __init__(self, offset):
			self.offset = offset
			self.values = []

		def append(self, parent, dummy=None):
			self.values.append([{}, parent])
			return len(self.values) - 1

		def set(self, iter, *args):
			values = self.values[iter][0]
			i = 0
			while i < len(args):
				values[args[i]] = args[i + 1] - self.offset if args[i] == 2 else args[i + 1]
				i += 2

	def show(self, hd):
		iters = [None] * len(self.model.values)
		for i in range(0, len(self.model.values)):
			(vs, p) = self.model.values[i]
			parent = None if p == None else iters[p]
			iter = hd.model.append(parent, None)
			iters[i] = iter
			args = []
			for (idx, val) in vs.items():
				args.append(idx)
				args.append(val)
			hd.model.set(iter, *args)

obj_flags_map = {
	1: 'no color?',
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
	off = add_dim(hd, size, data, offset, fmt, 'Top offset', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Left offset', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Bottom offset', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Right offset', parent=parent)
	return off

def add_margins(hd, size, data, offset, fmt, parent=None):
	off = add_dim(hd, size, data, offset, fmt, 'Top margin', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Bottom margin', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Left margin', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Right margin', parent=parent)
	return off

def add_page_columns(hd, size, data, offset, fmt, parent=None):
	(col, off) = rdata(data, offset, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'), parent=parent)
	off += 2
	off = add_dim(hd, size, data, off, fmt, 'Gutter width', parent=parent)
	return off

def add_record(hd, size, data, fmt, version):
	add_length(hd, size, data, fmt, version, 0)

def add_dim(hd, size, data, offset, fmt, name, parent=None):
	(dim, off) = rfract(data, offset, fmt)
	sz = off - offset
	dim_str = '%.2f pt / %.2f in' % (dim, dim2in(dim))
	add_iter(hd, name, dim_str, off - sz, sz, '%ds' % sz, parent=parent)
	return off

def add_fonts(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of fonts', count, off - 2, 2, fmt('H'))
	for i in range(0, count):
		start = off
		font_iter = add_iter(hd, 'Font %d' % i, '', off, 2, '2s')
		index_fmt = fmt('H') if version < VERSION_4 else fmt('I')
		index_size = struct.calcsize(index_fmt)
		(index, off) = rdata(data, off, index_fmt)
		add_iter(hd, 'Index', index, off - index_size, index_size, index_fmt, parent=font_iter)
		(name, off) = rcstr(data, off)
		add_iter(hd, 'Name', name, off - len(name) - 1, len(name) + 1, '%ds' % (len(name) + 1), parent=font_iter)
		(full_name, off) = rcstr(data, off)
		add_iter(hd, 'Full name', full_name, off - len(full_name) - 1, len(full_name) + 1, '%ds' % (len(full_name) + 1), parent=font_iter)
		hd.model.set(font_iter, 1, "%d, %s" % (index, name), 3, off - start, 4, '%ds' % (off - start))

char_format_map = {0x1: 'bold', 0x2: 'italic', 0x4: 'underline'}

align_map = {0: 'left', 1: 'center', 2: 'right', 3: 'justified', 4: 'forced'}

# if 'keep lines together' is enabled, then 'all lines' is used (or Start/End if 'all lines' disabled)
para_flags_map = {
	0x1: 'keep with next',
	0x2: 'lock to baseline grid',
	0x8: 'keep lines together',
	0x10: 'all lines',
	0x20: 'rule above',
	0x40: 'rule below',
	0x80: 'r. a. length: text',
	0x100: 'r. b. length: text',
}

if __name__ == '__main__':
	def test_deobfuscate(seed, value, n, expected):
		assert deobfuscate(value, seed, n) == expected

	test_deobfuscate(0, 0, 1, 0)
	test_deobfuscate(0xa132, 0x31, 1, 0x3)
	test_deobfuscate(0xa132, 0xa133, 2, 0x1)
	test_deobfuscate(0x7236, 0x35, 1, 0x3)
	test_deobfuscate(0x7236, 0x34, 1, 0x2)

# vim: set ft=python sts=4 sw=4 noet:
