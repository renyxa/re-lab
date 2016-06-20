# Copyright (C) 2016 David Tardon (dtardon@redhat.com)
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

import zlib

from utils import add_iter, add_pgiter, rdata

class bmi_parser:
	def __init__(self, data, page=None, parent=None):
		self.page = page
		self.data = data
		self.parent = parent
		self.size = 0
		self.data_start = 0

	def parse(self):
		assert self.page
		self.parse_header()
		add_pgiter(self.page, 'Header', 'bmi', 'header', self.data[0:self.data_start], self.parent)
		self.parse_data()

	def parse_header(self):
		self.data_start = 0x87
		size_off = 0x35
		(palette, off) = rdata(self.data, 0xd, '<H')
		if palette == 1:
			self.data_start += 2 * 256 * 4
			size_off += 256 * 4
		(self.size, off) = rdata(self.data, size_off, '<I')

	def parse_data(self):
		uncompressed_data = bytearray()
		off = self.data_start
		rawiter = add_pgiter(self.page, 'Raw data', 'bmi', 0, self.data[off:], self.parent)
		i = 1
		while off < len(self.data):
			(length, off) = rdata(self.data, off, '<H')
			off += 1
			blockiter = add_pgiter(self.page, 'Block %d' % i, 'bmi', 'block',
				self.data[off - 3:off + length], rawiter)
			compressed = self.data[off:off + length]
			add_pgiter(self.page, 'Compressed data', 'bmi', 0, compressed, blockiter)
			try:
				uncompressed = zlib.decompress(compressed)
				add_pgiter(self.page, 'Uncompressed data', 'bmi', 0, uncompressed, blockiter)
				uncompressed_data.extend(uncompressed)
			except zlib.error:
				print('decompression of block %d failed' % i)
			i += 1
			off += length
		add_pgiter(self.page, 'Data', 'bmi', 0, str(uncompressed_data), self.parent)

def add_block(hd, size, data):
	(length, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Length', length, off - 2, 2, '<H')

def add_header(hd, size, data):
	(sig, off) = rdata(data, 0, '9s')
	add_iter(hd, 'Signature', sig, off - 9, 9, '9s')
	(width, off) = rdata(data, off, '<H')
	add_iter(hd, 'Pixel width', width, off - 2, 2, '<H')
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Pixel height', height, off - 2, 2, '<H')
	(palette, off) = rdata(data, off, '<H')
	add_iter(hd, 'Palette mode?', bool(palette), off - 2, 2, '<H')
	(depth, off) = rdata(data, off, '<H')
	add_iter(hd, 'Color depth', depth, off - 2, 2, '<H')
	off += 4
	if palette == 1:
		palette_iter = add_iter(hd, 'Color palette', '', off, 1024, '1024s')
		for i in range(0, 256):
			(color, off) = rdata(data, off, '<I')
			add_iter(hd, 'Color %d?' % (i + 1), '%x' % color, off - 4, 4, '<I', parent=palette_iter)
	off += 0x20
	(fsize, off) = rdata(data, off, '<I')
	add_iter(hd, 'File size', fsize, off - 4, 4, '<I')
	off += 2
	(comment_len, off) = rdata(data, off, '<H')
	add_iter(hd, 'Comment length?', comment_len, off - 2, 2, '<H')
	off += 4
	# Note: the comment could also be fixed-size (48 bytes?)
	(comment, off) = rdata(data, off, '%ds' % (comment_len - 1)) # skip trailing 0
	off += 1
	add_iter(hd, 'Comment', comment, off - comment_len, comment_len, '%ds' % comment_len)
	off += 8
	# Note: this suggests that the file has a more complicated
	# structure... Perhaps it can save multiple sizes of the image?
	(width, off) = rdata(data, off, '<H')
	add_iter(hd, 'Pixel width (again)', width, off - 2, 2, '<H')
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Pixel height (again)', height, off - 2, 2, '<H')
	(depth, off) = rdata(data, off, '<H')
	add_iter(hd, 'Color depth (again)', depth, off - 2, 2, '<H')
	off += 4
	(dsize, off) = rdata(data, off, '<I')
	add_iter(hd, 'Size of data', dsize, off - 4, 4, '<I')
	if palette == 1:
		palette_iter = add_iter(hd, 'Color palette (again)', '', off, 1024, '1024s')
		for i in range(0, 256):
			(color, off) = rdata(data, off, '<I')
			add_iter(hd, 'Color %d?' % (i + 1), '%x' % color, off - 4, 4, '<I', parent=palette_iter)

bmi_ids = {
	'block': add_block,
	'header': add_header,
}

def get_size(data):
	parser = bmi_parser(data)
	parser.parse_header()
	return parser.size

def open(data, page, parent):
	parser = bmi_parser(data, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
