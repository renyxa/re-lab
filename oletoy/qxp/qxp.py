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

LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'

def little_endian(fmt=''):
	return LITTLE_ENDIAN + fmt

def big_endian(fmt=''):
	return BIG_ENDIAN + fmt

def rsfloat(data, off, fmt):
	(num, off) = rdata(data, off, fmt('H'))
	f = num / float(0x10000)
	return f, off

def rfract(data, off, fmt):
	if fmt() == LITTLE_ENDIAN:
		(fpart, off) = rsfloat(data, off, fmt)
		(ipart, off) = rdata(data, off, fmt('h'))
	else:
		(ipart, off) = rdata(data, off, fmt('h'))
		(fpart, off) = rsfloat(data, off, fmt)
	return (ipart + fpart, off)

def read_c_str(data, offset):
	off = data.find('\0', offset)
	s = data[offset:off]
	off += 1
	return s, off

def read_pascal_str(data, offset):
	(length, off) = rdata(data, offset, 'B')
	s = data[off:off + length]
	off += length
	return s, off

def dim2in(dim):
	return dim / 72.0

def style2txt(value):
	if value == 0:
		return 'No style'
	else:
		return value

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

class Header:
	def __init__(self, seed=0, inc=0, masters=0, pictures=0):
		self.seed = seed
		self.inc = inc
		self.masters = masters
		self.pictures = pictures

obj_flags_map = {
	1: 'no color?',
	0x4: 'lock',
	0x10: 'suppress printout',
	0x20: 'no item runaround?',
	0x40: 'user-edited runaround path?', # used for picture in qxp33
}

def add_length(hd, size, data, fmt, version, offset, name="Length"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, name, length, off - 4, 4, fmt('I'))
	return off

def add_pcstr4(hd, data, offset, fmt, name="Name"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, '%s length' % name, length, off - 4, 4, fmt('I'))
	(pstring, off) = rdata(data, off, '%ds' % length)
	string = pstring[0:pstring.find('\0')]
	add_iter(hd, name, string, off - length, length, '%ds' % length)
	return string, off

def add_pascal_str(hd, data, offset, name="Name"):
	(string, off) = read_pascal_str(data, offset)
	length = off - offset
	add_iter(hd, name, string, offset, length, '%ds' % length)
	return string, off

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

def add_sfloat_perc(hd, data, offset, fmt, name, parent=None):
	(f, off) = rsfloat(data, offset, fmt)
	perc = f * 100
	add_iter(hd, name, '%.1f%%' % perc, off - 2, 2, fmt('H'), parent=parent)
	return off

def add_fract_perc(hd, data, offset, fmt, name, parent=None):
	(f, off) = rfract(data, offset, fmt)
	add_iter(hd, name, '%.2f%%' % (f * 100), off - 4, 4, fmt('i'), parent=parent)
	return off

def add_fonts(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of fonts', count, off - 2, 2, fmt('H'))
	for i in range(0, count):
		start = off
		font_iter = add_iter(hd, 'Font %d' % i, '', off, 2, '2s')
		(index, off) = rdata(data, off, fmt('h'))
		add_iter(hd, 'Index in font list', index, off - 2, 2, fmt('h'), parent=font_iter)
		if version >= VERSION_4:
			off += 2
		rstr = read_c_str if fmt() == LITTLE_ENDIAN else read_pascal_str
		(name, off) = rstr(data, off)
		add_iter(hd, 'Name', name, off - len(name) - 1, len(name) + 1, '%ds' % (len(name) + 1), parent=font_iter)
		(full_name, off) = rstr(data, off)
		add_iter(hd, 'Full name', full_name, off - len(full_name) - 1, len(full_name) + 1, '%ds' % (len(full_name) + 1), parent=font_iter)
		hd.model.set(font_iter, 1, "%d, %s" % (index, name), 3, off - start, 4, '%ds' % (off - start))

def add_physical_fonts(hd, size, data, fmt, version):
	def add_name(off, title, parent):
		(name, off) = rcstr(data, off)
		sz = len(name) + 1
		add_iter(hd, title, name, off - sz, sz, '%ds' % sz, parent=parent)
		return off
	off = add_length(hd, size, data, fmt, version, 0)
	off += 12
	i = 0
	while off < size:
		start = off
		font_iter = add_iter(hd, 'Font %d' % i, '', off, 2, '2s')
		(index, off) = rdata(data, off, fmt('h'))
		add_iter(hd, 'Index in font list', index, off - 2, 2, fmt('h'), parent=font_iter)
		off += 12
		off = add_name(off, 'Bold name', font_iter)
		off = add_name(off, 'Italic name', font_iter)
		off = add_name(off, 'Bold italic name', font_iter)
		if version >= VERSION_4:
			off += 17
		i += 1
		hd.model.set(font_iter, 1, "%d" % index, 3, off - start, 4, '%ds' % (off - start))

def add_saved(hd, size, data, saved, dummy):
	saved.show(hd)

def add_header_common(hd, size, data, fmt):
	off = 2
	proc_map = {'II': 'Intel', 'MM': 'Motorola'}
	(proc, off) = rdata(data, off, '2s')
	add_iter(hd, 'Processor', key2txt(proc, proc_map), off - 2, 2, '2s')
	(sig, off) = rdata(data, off, '3s')
	add_iter(hd, 'Signature', sig, off - 3, 3, '3s')
	lang_map = {0x33: 'English', 0x61: 'Korean'}
	(lang, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Language', key2txt(lang, lang_map), off - 1, 1, fmt('B'))
	version_map = {
		0x3e: '3.1',
		0x3f: '3.3',
		0x41: '4',
		0x42: '5',
		0x43: '6',
		0x44: '7?',
		0x45: '8',
	}
	(ver, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, fmt('H'))
	(ver, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, fmt('H'))
	return off

def add_tab(hd, size, data, offset, fmt, version, parent=None):
	type_map = {0: 'left', 1: 'center', 2: 'right', 3: 'align'}
	(typ, off) = rdata(data, offset, fmt('B'))
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 1, 1, fmt('B'), parent=parent)
	subtype_map = {1: 'decimal', 2: 'comma'}
	(subtype, off) = rdata(data, off, fmt('B'))
	if subtype_map.has_key(subtype):
		add_iter(hd, 'Subtype', key2txt(subtype, subtype_map), off - 1, 1, fmt('B'), parent=parent)
	else:
		add_iter(hd, 'Align at char', chr(subtype), off - 1, 1, '1s', parent=parent)
	(fill_char, off) = rdata(data, off, '1s')
	add_iter(hd, 'Fill char', fill_char, off - 1, 1, '1s', parent=parent)
	off += 1
	(pos, off) = rdata(data, off, fmt('i'))
	if pos == -1:
		add_iter(hd, 'Position', 'not defined', off - 4, 4, fmt('i'), parent=parent)
	else:
		off = add_dim(hd, size, data, off - 4, fmt, 'Position', parent)
	if parent:
		if pos == -1:
			hd.model.set(parent, 1, 'not defined')
		else:
			if typ == 3:
				subtype_str = ' @ %s' % (key2txt(subtype, subtype_map) if subtype_map.has_key(subtype) else "'%s'" % chr(subtype))
			else:
				subtype_str = ''
			pos = rfract(data, off - 4, fmt)[0]
			pos_str = '%.2f pt / %.2f in' % (pos, dim2in(pos))
			hd.model.set(parent, 1, "%s%s / '%s' / %s"  % (key2txt(typ, type_map), subtype_str, fill_char, pos_str))
	return off

char_format_map = {
	0x1: 'bold',
	0x2: 'italic',
	0x4: 'underline',
	0x8: 'outline',
	0x10: 'shadow',
	0x20: 'superscript',
	0x40: 'subscript',
	0x100: 'superior',
	0x200: 'strike thru',
	0x400: 'all caps',
	0x800: 'small caps',
	0x1000: 'word underline',
}

align_map = {0: 'left', 1: 'center', 2: 'right', 3: 'justified', 4: 'forced'}

vertical_align_map = {0: 'Top', 1: 'Center', 2: 'Right', 3: 'Justified'}

# first baseline minimum:
# 0x20: 'Ascent', 0x28: 'Cap height', 0x38: 'Cap + Accent'
text_flags_map = {
	0x08: 'cap height',
	0x10: 'accent',
	0x20: 'ascent',
	0x40: 'run text around all sides',
}

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

picture_flags_map = {
	0x4: 'suppress printout',
}

gradient_type_map = {
	0x10: 'Linear',
	0x18: 'Mid-Linear',
	0x19: 'Rectangular',
	0x1a: 'Diamond',
	0x1b: 'Circular',
	0x1c: 'Full Circular',
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
