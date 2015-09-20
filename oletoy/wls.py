# Copyright (C) 2015 David Tardon (dtardon@redhat.com)
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

import struct

from utils import add_iter, add_pgiter, rdata

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

obfuscation_map = {}

def deobfuscate(data, orig_pos):
	def get_obfuscation_map(pos):
		def obfuscate_byte(byte, pos):
			def usub(a, b):
				if a >= b:
					return a - b
				else:
					return 0x100 - b + a
			def uadd(a, b):
				return (a + b) & 0xff
			val = byte
			base = (val & 0x60) << 1
			val = usub(base, val)
			val = usub(0xb9, val)
			mask = 0x1
			for i in range(0, 5):
				v = byte & mask
				p = pos & mask
				if p != 0:
					if v == 0:
						val = uadd(val, p)
					else:
						val = usub(val, p)
				mask = mask << 1
			mask = 0x60
			p = pos & mask
			if p != 0:
				val = uadd(val, p)
				val = uadd(val, base)
			return val
		if not obfuscation_map.has_key(pos):
			d = {}
			for b in range(0, 0x100):
				d[chr(obfuscate_byte(b, pos))] = chr(b)
			assert(len(d) == 0x100)
			obfuscation_map[pos] = d
		return obfuscation_map[pos]
	def packed(bytes):
		bytestring = ''
		for b in bytes:
			bytestring += struct.pack('<B', ord(b))
		return bytestring
	new_data = []
	pos = orig_pos
	for b in data:
		new_data.append(get_obfuscation_map(pos)[b])
		pos += 1
	return packed(new_data)

WLS_RECORDS = {
	0x70: ('Column width', 'column_width'),
	0xb7: ('Text cell', 'text_cell'),
	0xb9: ('Formula cell', None),
	0xbe: ('Number cell', 'number_cell'),
	0xc3: ('Row height', 'row_height'),
	0xc4: ('Start something', None), # I don't know what this 'something' means yet .-)
	0xc5: ('End something', None),
	0xca: ('Tab', 'tab'),
}

class wls_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		data = self.data
		n = 0
		off = 0
		typ = None
		flags = 0
		index = 0
		while off + 1 < len(data):
			start = off
			(size, off) = rdata(data, off, '<h')
			seq = size < 0
			if size < 0:
				size = -size
				index += 1
			end = off + size
			assert(end >= off)
			if end > len(data):
				break
			if not seq:
				# NOTE: this would read nonsense if size == 0, but that should never happen
				(typ, off) = rdata(data, off, '<B')
				(flags, off) = rdata(data, off, '<B')
				index = 0
				if end < len(data):
					(next_size, off) = rdata(data, end, '<h')
					seq = next_size < 0
			recdata = data[start:end]
			assert(typ)
			rec = get_or_default(WLS_RECORDS, typ, ('Record %x' % typ, None))
			rec_str = '[%d] %s' % (n, rec[0])
			if flags != 0:
				rec_str += ' (flags %x)' % flags
			if seq:
				rec_str += ' [%d]' % index
			content = recdata[0:4] + deobfuscate(recdata[4:], 4)
			handler = rec[1]
			if not handler:
				handler = 'record'
			reciter = add_pgiter(self.page, rec_str, 'wls', handler, content, self.parent)
			if size > 2:
				add_pgiter(self.page, 'Obfuscated', 'wls', '', recdata, reciter)
			off = end
			n += 1
		if off < len(data):
			add_pgiter(self.page, 'Trailer', 'wls', '', data[off:], self.parent)

def add_record(hd, size, data):
	off = 0
	(size, off) = rdata(data, off, '<h')
	add_iter(hd, 'Size', size, off - 2, 2, '<h')
	(typ, off) = rdata(data, off, '<B')
	add_iter(hd, 'Type', typ, off - 1, 1, '<B')
	(flags, off) = rdata(data, off, '<B')
	add_iter(hd, 'Flags', '0x%x' % flags, off - 1, 1, '<B')
	return off

def add_number_cell(hd, size, data):
	off = add_record(hd, size, data)
	off += 6
	(val, off) = rdata(data, off, '<d')
	add_iter(hd, 'Value', val, off - 8, 8, '<d')

def add_text_cell(hd, size, data):
	off = add_record(hd, size, data)
	off += 6
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Content length', length, off - 2, 2, '<H')

def add_tab(hd, size, data):
	off = add_record(hd, size, data)
	(length, off) = rdata(data, off, '<B')
	add_iter(hd, 'Name length', length, off - 1, 1, '<B')
	(name, off) = rdata(data, off, '%ds' % length)
	add_iter(hd, 'Name', name, off - length, length, '%ds' % length)

def add_row_height(hd, size, data):
	off = add_record(hd, size, data)
	(row, off) = rdata(data, off, '<H') # TODO: maybe this is <I?
	add_iter(hd, 'Row', row, off - 2, 2, '<H')
	off += 4
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Height', '%.2fpt' % (height / 20.0), off - 2, 2, '<H')

def add_column_width(hd, size, data):
	off = add_record(hd, size, data)
	(first, off) = rdata(data, off, '<H')
	add_iter(hd, 'First column', first, off - 2, 2, '<H')
	(last, off) = rdata(data, off, '<H')
	add_iter(hd, 'Last column', last, off - 2, 2, '<H')
	(width, off) = rdata(data, off, '<H')
	# the conversion factor to pt seems to be something around 275
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

wls_ids = {
	'record': add_record,
	'column_width': add_column_width,
	'number_cell': add_number_cell,
	'row_height': add_row_height,
	'text_cell': add_text_cell,
	'tab': add_tab,
}

def parse(page, data, parent):
	parser = wls_parser(page, data, parent)
	parser.parse()

if __name__ == '__main__':
	def test_deobfuscate(byte, pos, expected):
		got = deobfuscate([chr(byte)], pos)
		if got != [expected]:
			print("expected '%s' (%x), got %x" % (expected, ord(expected), ord(got[0])))
		assert(got == [expected])
	test_deobfuscate(0x5f, 6, '`')
	test_deobfuscate(0x60, 6, 'a')
	test_deobfuscate(0x5d, 6, 'b')
	test_deobfuscate(0x67, 6, 'h')
	test_deobfuscate(0x68, 6, 'i')
	test_deobfuscate(0x7f, 6, '@')
	test_deobfuscate(0x82, 6, 'O')

	test_deobfuscate(0x5f, 7, 'a')
	test_deobfuscate(0x68, 7, 'h')
	test_deobfuscate(0x67, 7, 'i')
	test_deobfuscate(0x7f, 7, 'A')

	test_deobfuscate(0xa9, 0x10, ' ')
	test_deobfuscate(0xb8, 0x10, '/')
	test_deobfuscate(0x99, 0x10, '0')
	test_deobfuscate(0xa8, 0x10, '?')
	test_deobfuscate(0x89, 0x10, '@')
	test_deobfuscate(0x98, 0x10, 'O')
	test_deobfuscate(0x79, 0x10, 'P')
	test_deobfuscate(0x88, 0x10, '_')
	test_deobfuscate(0x69, 0x10, '`')
	test_deobfuscate(0x78, 0x10, 'o')
	test_deobfuscate(0x59, 0x10, 'p')
	test_deobfuscate(0x66, 0x10, '}')

	test_deobfuscate(0x69, 0x11, 'a')
	test_deobfuscate(0x6c, 0x11, 'b')
	test_deobfuscate(0x72, 0x11, 'h')

	test_deobfuscate(0x97, 0x1e, '@')

	test_deobfuscate(0x39, 0x20, '`')
	test_deobfuscate(0x3a, 0x20, 'a')
	test_deobfuscate(0x3b, 0x20, 'b')
	test_deobfuscate(0x19, 0x20, '@')
	test_deobfuscate(0x1a, 0x20, 'A')

# vim: set ft=python ts=4 sw=4 noet:
