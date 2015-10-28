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
	'CT': 'Encoding',
	'HE': 'Header',
	'FO': 'Footer',
	'LH': 'Line height',
	'LM': 'Left margin',
	'MT': 'Top margin',
	'MB': 'Bottom margin',
	'PL': 'Page length',
	'RM': 'Right margin',
	'TB': 'Tabs',
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
			elif data[0] == '.':
				add_pgiter(self.page, 'Command', 't602', 'command', data, self.parent)
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
		encoding_map = {'0': 'KEYBCS2', '1': 'LATIN2', '2': 'KOI8CS'}
		line_height_map = {'6': '1', '4': '1.5', '3': '2'}
		if name == 'CT':
			value = key2txt(value.strip(), encoding_map)
		elif name == 'LH':
			value = key2txt(value.strip(), line_height_map)
		add_iter(hd, 'Value', value, off, end - off, '%ds' % (end - off))
	off = end
	add_iter(hd, 'End of control', data[off:], off, len(data) - off, '%ds' % (len(data) - off))

def add_paragraph(hd, size, data):
	fmt = {
		0x2: 'Switch bold',
		0x4: 'Switch italics',
		0xa: 'Line break',
		0xf: 'Switch wide',
		0x10: 'Switch high',
		0x13: 'Switch underline',
		0x14: 'Switch subscript',
		0x16: 'Switch superscript',
		0x1a: 'End of file',
		0x1d: 'Switch big',
	}
	off = 0
	mark = 0
	while off < len(data):
		(c, off) = rdata(data, off, '<B')
		if c < 0x20:
			if off - mark > 1:
				length = off - mark - 1
				add_iter(hd, 'Text', data[mark:off - 1], mark, length, '%ds' % length)
			mark = off
			if c == 0xd and off == len(data) - 1:
				add_iter(hd, 'End of paragraph', data[-2:], off - 1, 2, '2s')
				off += 1
			else:
				add_iter(hd, key2txt(c, fmt), '', off - 1, 1, '<B')

def add_command(hd, size, data):
	command_map = {'pa': 'Page break'}
	start = 1
	end = data.find('\r\n', start)
	length = end - start
	(name, off) = rdata(data, start, '%ds' % length)
	add_iter(hd, 'Name', key2txt(name, command_map), start, length, '%ds' % length)
	add_iter(hd, 'End of command', data[off:], off, len(data) - off, '%ds' % (len(data) - off))

ids = {
	'command': add_command,
	'control': add_control,
	'paragraph': add_paragraph,
}

def parse(data, page, parent):
	p = parser(page, data, parent)
	p.parse()

# vim: set ft=python ts=4 sw=4 noet:
