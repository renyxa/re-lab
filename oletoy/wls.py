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

class wls_parser(object):

	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		data = self.data
		n = 0
		off = 0
		while off < len(data):
			(size, off) = rdata(data, off, '<h')
			if size < 0:
				size = -size
			if off + size > len(data):
				break
			add_pgiter(self.page, 'Record %d' % n, 'wls', '', data[off - 2:off + size], self.parent)
			off += size
			n += 1
		if off < len(data):
			add_pgiter(self.page, 'Trailer', 'wls', '', data[off:], self.parent)

wls_ids = {
}

def parse(page, data, parent):
	parser = wls_parser(page, data, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
