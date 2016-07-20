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

from utils import add_iter, add_pgiter, rdata, d2hex, key2txt

offset_tags = {
	0x1: 'Bitmap',
	0x3: 'Comment',
	0xff: 'EOF',
}

# defined later
stream_parsers = {}

class bmi_parser:
	def __init__(self, data, page=None, parent=None):
		self.page = page
		self.data = data
		self.parent = parent
		self.palette_len = 0
		self.offsets = {}

	def size(self):
		if self.offsets.has_key(0xff):
			return self.offsets[0xff]
		else:
			return len(self.data)

	def parse(self):
		assert self.page
		header_len = self.parse_header()
		add_pgiter(self.page, 'Header', 'bmi', 'header', self.data[0:header_len], self.parent)
		# parse streams
		offsets = self.offsets.items()
		offsets.sort(key = lambda v: v[1])
		count = len(offsets)
		offsets.append((-1, self.size()))
		for i in range(0, count):
			tag = offsets[i][0]
			start = offsets[i][1]
			end = offsets[i + 1][1]
			if stream_parsers.has_key(tag):
				stream_parsers[tag](self, start, end - start)
			elif tag != 0xff:
				add_pgiter(self.page, 'Unknown', 'bmi', '', self.data[start:end], self.parent)

	def parse_header(self):
		(palette, off) = rdata(self.data, 0xd, '<H')
		(depth, off) = rdata(self.data, off, '<H')
		off += 2
		(count, off) = rdata(self.data, off, '<H')
		if bool(palette):
			self.palette_len = 4 * (1 << depth)
			off += self.palette_len
		for i in range(0, count):
			(tag, off) = rdata(self.data, off, '<H')
			(self.offsets[tag], off) = rdata(self.data, off, '<I')
		return off

	def parse_bitmap(self, offset, length):
		bmpiter = add_pgiter(self.page, offset_tags[0x1], 'bmi', '', self.data[offset:offset + length], self.parent)
		uncompressed_data = bytearray()
		data_start = offset + 16 + self.palette_len
		add_pgiter(self.page, 'Header', 'bmi', 'bitmap_header', self.data[offset:data_start], bmpiter)
		rawiter = add_pgiter(self.page, 'Raw data', 'bmi', 0, self.data[data_start:data_start + length], bmpiter)
		i = 1
		off = data_start
		while off < offset + length:
			(blen, off) = rdata(self.data, off, '<H')
			off += 1
			blockiter = add_pgiter(self.page, 'Block %d' % i, 'bmi', 'block',
				self.data[off - 3:off + blen], rawiter)
			compressed = self.data[off:off + length]
			add_pgiter(self.page, 'Compressed data', 'bmi', 0, compressed, blockiter)
			try:
				uncompressed = zlib.decompress(compressed)
				add_pgiter(self.page, 'Uncompressed data', 'bmi', 0, uncompressed, blockiter)
				uncompressed_data.extend(uncompressed)
			except zlib.error:
				print('decompression of block %d failed' % i)
			i += 1
			off += blen
		add_pgiter(self.page, 'Data', 'bmi', 0, str(uncompressed_data), bmpiter)

	def parse_comment(self, offset, length):
		add_pgiter(self.page, offset_tags[0x3], 'bmi', 'comment', self.data[offset:offset + length], self.parent)

stream_parsers = {
	0x1: bmi_parser.parse_bitmap,
	0x3: bmi_parser.parse_comment,
}

def _add_palette(hd, size, data, off, color_depth):
	items = 1 << color_depth
	length = 4 * items
	palette_iter = add_iter(hd, 'Color palette', '', off, length, '%ds' % length)
	for i in range(0, items):
		(color, off) = rdata(data, off, '3s')
		add_iter(hd, 'Color %d (RGB)' % (i + 1), d2hex(color), off - 3, 3, '3s', parent=palette_iter)
		off += 1
	return off

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
	add_iter(hd, 'Palette mode', bool(palette), off - 2, 2, '<H')
	(depth, off) = rdata(data, off, '<H')
	add_iter(hd, 'Color depth', depth, off - 2, 2, '<H')
	off += 2
	(count, off) = rdata(data, off, '<H')
	add_iter(hd, 'Number of offsets', count, off - 2, 2, '<H')
	if palette == 1:
		off = _add_palette(hd, size, data, off, depth)
	for i in range(1, count + 1):
		(tag, off) = rdata(data, off, '<H')
		add_iter(hd, 'Offset tag %d' % i, key2txt(tag, offset_tags), off - 2, 2, '<H')
		(offset, off) = rdata(data, off, '<I')
		add_iter(hd, 'Offset to %s' % key2txt(tag, offset_tags), offset, off - 4, 4, '<I')
	return

def add_comment(hd, size, data):
	off = 2
	(comment_len, off) = rdata(data, off, '<I')
	add_iter(hd, 'Comment length', comment_len, off - 4, 4, '<I')
	off += 2
	(comment, off) = rdata(data, off, '%ds' % (comment_len - 1)) # skip trailing 0
	off += 1
	add_iter(hd, 'Comment', comment, off - comment_len, comment_len, '%ds' % comment_len)

def add_bitmap_header(hd, size, data):
	(width, off) = rdata(data, 0, '<H')
	add_iter(hd, 'Pixel width', width, off - 2, 2, '<H')
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'Pixel height', height, off - 2, 2, '<H')
	(depth, off) = rdata(data, off, '<H')
	add_iter(hd, 'Color depth', depth, off - 2, 2, '<H')
	off += 4
	(dsize, off) = rdata(data, off, '<I')
	add_iter(hd, 'Size of uncompressed data', dsize, off - 4, 4, '<I')
	(block_size, off) = rdata(data, off, '<H')
	add_iter(hd, 'Max. size of uncompressed block', block_size, off - 2, 2, '<H')
	if off < size:
		_add_palette(hd, size, data, off, depth)

bmi_ids = {
	'bitmap_header': add_bitmap_header,
	'block': add_block,
	'comment': add_comment,
	'header': add_header,
}

def get_size(data):
	parser = bmi_parser(data)
	parser.parse_header()
	return parser.size()

def open(data, page, parent):
	parser = bmi_parser(data, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
