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

from utils import add_iter, add_pgiter, rdata

tc6_records = {
	0x1: ('Start sheet?', None),
	0x20: ('Sheet info', 'tc6_sheet_info'),
	0xff: ('End sheet?', None),
}

class tc6_parser:
	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		assert len(self.data) > 0x40
		add_pgiter(self.page, 'Header', 'c602', 'tc6_header', self.data[0:0x40], self.parent)
		off = 0x40
		while off + 3 <= len(self.data):
			(rec, off) = rdata(self.data, off, '<B')
			(length, off) = rdata(self.data, off, '<H')
			if tc6_records.has_key(rec):
				(name, handler) = tc6_records[rec]
			else:
				name = 'Record %x' % rec
				handler = None
			if not handler:
				handler = 'tc6_record'
			add_pgiter(self.page, name, 'c602', handler, self.data[off - 3:off + length], self.parent)
			off += length

class gc6_parser:
	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		pass

def format_row(number):
	return '%d' % (number + 1)

def format_column(number):
	assert number >= 0
	assert number <= 0xff
	low = number % 26
	high = number / 26
	if high > 0:
		row = chr(0x40 + high)
	else:
		row = ''
	return row + chr(0x40 + low + 1)

def add_tc6_header(hd, size, data):
	off = 0
	(ident, off) = rdata(data, off, '35s')
	add_iter(hd, 'Identifier', ident, off - 35, 35, '35s')

def add_record(hd, size, data):
	off = 0
	(typ, off) = rdata(data, off, '<B')
	add_iter(hd, 'Record type', typ, off - 1, 1, '<B')
	(length, off) = rdata(data, off, '<H')
	add_iter(hd, 'Record length', length, off - 2, 2, '<H')
	return off

def add_sheet_info(hd, size, data):
	off = add_record(hd, size, data)
	off += 2
	(left, off) = rdata(data, off, '<B')
	add_iter(hd, 'First column', format_column(left), off - 1, 1, '<B')
	(top, off) = rdata(data, off, '<H')
	add_iter(hd, 'First row', format_row(top), off - 2, 2, '<H')
	(right, off) = rdata(data, off, '<B')
	add_iter(hd, 'Last column', format_column(right), off - 1, 1, '<B')
	(bottom, off) = rdata(data, off, '<H')
	add_iter(hd, 'Last row', format_row(bottom), off - 2, 2, '<H')

c602_ids = {
	'tc6_header': add_tc6_header,
	'tc6_record': add_record,
	'tc6_sheet_info': add_sheet_info,
}

def parse_spreadsheet(data, page, parent):
	parser = tc6_parser(page, data, parent)
	parser.parse()

def parse_chart(data, page, parent):
	parser = gc6_parser(page, data, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
