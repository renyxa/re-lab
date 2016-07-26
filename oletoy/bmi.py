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

stream_tags = {
	0x1: 'Bitmap',
	0x3: 'Comment',
	0xff: 'EOF',
}

# defined later
stream_parsers = {}

def add_data(hd, size, data, width, height, depth):
	assert depth in (1, 4, 8, 24)
	bits = (width * depth)
	lsize = bits / 8
	if bits % 8 != 0:
		lsize += 1
	tail = lsize % 4
	padding = 0
	if tail != 0:
		padding = 4 - tail
		lsize += padding
	shift = (8 - min(depth, 8))
	mask = (0xff >> shift) << shift
	off = 0
	for h in range(1, height + 1):
		lineiter = add_iter(hd, 'Line %d' % h, '', off, lsize, '%ds' % lsize)
		i = 1
		while i < width + 1:
			if depth == 24:
				(color, off) = rdata(data, off, '3s')
				add_iter(hd, 'Pixel %d (BGR)' % i, d2hex(color), off - 3, 3, '3s', parent=lineiter)
				i += 1
			else:
				(index, off) = rdata(data, off, '<B')
				for j in range(0, 8 / depth):
					add_iter(hd, 'Pixel %d (index)' % i, (index & mask) >> shift, off - 1, 1, '<B', parent=lineiter)
					index = index << depth
					i += 1
					if i == width + 1:
						break
		if padding > 0:
			add_iter(hd, 'Padding', '', off, padding, '%ds' % padding, parent=lineiter)
			off += padding

class bmi_parser:
	def __init__(self, data, page=None, parent=None):
		self.page = page
		self.data = data
		self.parent = parent
		self.streams = []
		self.eof = None

	def size(self):
		if self.eof:
			return self.eof
		else:
			return len(self.data)

	def parse(self):
		assert self.page
		(off, palette, depth, toc_count) = self.parse_header(0)
		if palette:
			off = self.parse_palette(off, depth)
		off = self.parse_toc(off, toc_count)
		self.parse_streams()

	def parse_size(self):
		(off, depth, toc_count) = self.parse_header(0)
		off = self.parse_palette(off, depth)
		self.parse_toc(off, toc_count)

	def parse_header(self, offset):
		if self.page:
			add_pgiter(self.page, 'Header', 'bmi', 'header', self.data[offset:offset + 0x15], self.parent)
		(palette, off) = rdata(self.data, offset + 0xd, '<H')
		(depth, off) = rdata(self.data, off, '<H')
		off += 2
		(count, off) = rdata(self.data, off, '<H')
		return (off, bool(palette), depth, count)

	def parse_palette(self, offset, depth):
		length = 4 * (1 << depth)
		if self.page:
			add_pgiter(self.page, 'Color palette', 'bmi', 'palette', self.data[offset:offset + length], self.parent)
		return offset + length

	def parse_toc(self, offset, count):
		if self.page:
			add_pgiter(self.page, 'ToC', 'bmi', 'toc', self.data[offset:offset + 6 * count], self.parent)
		offsets = []
		off = offset
		for i in range(0, count):
			(tag, off) = rdata(self.data, off, '<H')
			(start, off) = rdata(self.data, off, '<I')
			if tag == 0xff:
				self.eof = start
			if (tag, start) not in offsets:
				offsets.append((tag, start))
		offsets.sort(key = lambda v: v[1])
		offsets.append((-1, self.size()))
		self.streams = [(x[1], y[1], x[0]) for (x, y) in zip(offsets, offsets[1:])]
		return off

	def parse_streams(self):
		for stream in self.streams:
			start = stream[0]
			end = stream[1]
			tag = stream[2]
			if stream_parsers.has_key(tag):
				stream_parsers[tag](self, stream_tags[tag], start, end - start)
			elif tag != 0xff:
				add_pgiter(self.page, 'Unknown', 'bmi', '', self.data[start:end], self.parent)

	def parse_bitmap(self, name, offset, length):
		bmpiter = add_pgiter(self.page, name, 'bmi', '', self.data[offset:offset + length], self.parent)
		uncompressed_data = bytearray()
		add_pgiter(self.page, 'Header', 'bmi', 'bitmap_header', self.data[offset:offset + 16], bmpiter)
		(width, off) = rdata(self.data, offset, '<H')
		(height, off) = rdata(self.data, off, '<H')
		(depth, off) = rdata(self.data, off, '<H')
		(palette, off) = rdata(self.data, off, '<H')
		off += 8
		if depth <= 8 and bool(palette):
			plen = 4 * (1 << depth)
			add_pgiter(self.page, 'Color palette', 'bmi', 'palette', self.data[off:off + plen], bmpiter)
			off += plen
		rawiter = add_pgiter(self.page, 'Raw data', 'bmi', 0, self.data[off:offset + length], bmpiter)
		i = 1
		while off < offset + length:
			(blen, off) = rdata(self.data, off, '<H')
			off += 1
			blockiter = add_pgiter(self.page, 'Block %d' % i, 'bmi', 'block',
				self.data[off - 3:off + blen], rawiter)
			compressed = self.data[off:off + blen]
			add_pgiter(self.page, 'Compressed data', 'bmi', 0, compressed, blockiter)
			try:
				uncompressed = zlib.decompress(compressed)
				add_pgiter(self.page, 'Uncompressed data', 'bmi', 0, uncompressed, blockiter)
				uncompressed_data.extend(uncompressed)
			except zlib.error:
				print('decompression of block %d failed' % i)
			i += 1
			off += blen
		def parser(hd, size, data):
			return add_data(hd, size, data, width, height, depth)
		add_pgiter(self.page, 'Data', 'bmi', parser, str(uncompressed_data), bmpiter)

	def parse_comment(self, name, offset, length):
		add_pgiter(self.page, name, 'bmi', 'comment', self.data[offset:offset + length], self.parent)

stream_parsers = {
	0x1: bmi_parser.parse_bitmap,
	0x3: bmi_parser.parse_comment,
}

def add_palette(hd, size, data):
	off = 0
	i = 0
	while off + 4 <= size:
		(color, off) = rdata(data, off, '3s')
		add_iter(hd, 'Color %d (BGR)' % (i + 1), d2hex(color), off - 3, 3, '3s')
		off += 1
		i += 1

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

def add_toc(hd, size, data):
	off = 0
	i = 1
	while off + 6 <= size:
		(tag, off) = rdata(data, off, '<H')
		add_iter(hd, 'Stream tag %d' % i, key2txt(tag, stream_tags), off - 2, 2, '<H')
		(offset, off) = rdata(data, off, '<I')
		add_iter(hd, 'Offset to %s' % key2txt(tag, stream_tags), offset, off - 4, 4, '<I')
		i += 1

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
	(palette, off) = rdata(data, off, '<H')
	add_iter(hd, 'Has palette?', bool(palette), off - 2, 2, '<H')
	off += 2
	(dsize, off) = rdata(data, off, '<I')
	add_iter(hd, 'Size of uncompressed data', dsize, off - 4, 4, '<I')
	(block_size, off) = rdata(data, off, '<H')
	add_iter(hd, 'Max. size of uncompressed block', block_size, off - 2, 2, '<H')

bmi_ids = {
	'bitmap_header': add_bitmap_header,
	'block': add_block,
	'comment': add_comment,
	'header': add_header,
	'palette': add_palette,
	'toc': add_toc,
}

def get_size(data):
	parser = bmi_parser(data)
	parser.parse_size()
	return parser.size()

def open(data, page, parent):
	parser = bmi_parser(data, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
