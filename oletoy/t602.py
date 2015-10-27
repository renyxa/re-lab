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

from utils import add_iter, add_pgiter, key2txt, rdata

controls = {
	'HE': 'Header',
	'FO': 'Footer',
	'LH': 'Line height',
	'MT': 'Top margin',
	'MB': 'Bottom margin',
	'PL': 'Page length',
}

class parser:
	def __init__(self, page, data, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		off = 0
		header = True
		while off < len(self.data):
			eol = self.data.find("\r\n", off)
			if eol > 0:
				end = eol + 2
			else:
				end = len(self.data)
			data = self.data[off:end]
			off = end
			if header and data[0] != '@':
				header = False
			if header:
				add_pgiter(self.page, key2txt(data[1:3], controls, 'Control'), 't602', 'control', data, self.parent)
			else:
				add_pgiter(self.page, 'Paragraph', 't602', 'paragraph', data, self.parent)

def add_control(hd, size, data):
	off = 1
	(name, off) = rdata(data, off, '2s')
	add_iter(hd, 'Name', key2txt(name, controls), off - 2, 2, '2s')
	if data[-1] == '\x1a':
		end = len(data) - 1
	else:
		end = len(data) - 2
	off += 1
	if off < end:
		value = data[off:end]
		line_height_map = {'6': '1', '4': '1.5', '3': '2'}
		if name == 'LH':
			value = key2txt(value.strip(), line_height_map)
		add_iter(hd, 'Value', value, off, end - off, '%ds' % (end - off))
	off = end
	add_iter(hd, 'End of control', data[off:], off, len(data) - off, '%ds' % (len(data) - off))

def add_paragraph(hd, size, data):
	pass

ids = {
	'control': add_control,
	'paragraph': add_paragraph,
}

def parse(data, page, parent):
	p = parser(page, data, parent)
	p.parse()

# vim: set ft=python ts=4 sw=4 noet:
