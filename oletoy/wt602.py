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

import struct

from utils import add_iter, add_pgiter, rdata

wt602_sections = (
	'Section 0',
	'Section 1',
	'Section 2',
	'Section 3',
	'Section 4',
	'Section 5',
	'Section 6',
	'Section 7',
	'Section 8',
	'Section 9',
	'Section 10',
	'Section 11',
	'Section 12',
	'Section 13',
	'Section 14',
	'Section 15',
	'Section 16',
	'Section 17',
	'Section 18',
	'Section 19',
	'Section 20',
	'Section 21',
	'Section 22',
	'Section 23',
	'Section 24',
	'Section 25',
	'Section 26',
	'Text',
	'Section 28',
	'Section 29',
	'Section 30',
	'Section 31',
	'Section 32',
	'Section 33',
	'Section 34',
	'Section 35',
	'Section 36',
)

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class wt602_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

		self.sections = [(0, 0) for i in range(0, len(wt602_sections))]

	def parse(self):
		self.parse_header()
		self.parse_offset_table()

	def parse_header(self):
		add_pgiter(self.page, 'Header', 'wt602', 'header', self.data[0:0x72], self.parent)

	def parse_offset_table(self):
		offiter = add_pgiter(self.page, 'Offset table', 'wt602', 0,
				self.data[0x72:0x72 + 4 * len(wt602_sections)], self.parent)
		begin = 0
		end = 0
		idx = 0
		off = 0x72
		for i in range(0, len(wt602_sections)):
			add_pgiter(self.page, wt602_sections[i], 'wt602', 0, self.data[off:off + 4], offiter)
			(cur, off) = rdata(self.data, off, '<I')
			if cur != 0:
				end = cur
				if i != 0:
					self.sections[idx] = (begin, end)
				begin = cur
				idx = i
		print('table = %s' % self.sections)

def add_header(hd, size, data):
	(c, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', c, 0, 4, '<I')

wt602_ids = {
	'header': add_header,
}

def parse(page, data, parent):
	parser = wt602_parser(page, data, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
