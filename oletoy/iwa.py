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

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

def read_var(data, offset):
	"""Read a variable length number."""

	assert len(data) > offset

	cs = []
	off = offset
	c = ord(data[off])
	while off < len(data) and c & 0x80:
		cs.append(c & ~0x80)
		off += 1
		c = ord(data[off])
	cs.append(c)
	off += 1

	assert cs != []

	n = 0
	for c in reversed(cs):
		n = n << 7
		n += c

	return (n, off)

# The compression method (as I currently understand it)
#
# Compressed data are broken sequences of literals and references into
# previously uncompressed data. A reference consists of offset (taken
# backwards from the end of uncompressed data) and length. They are
# recongized by the first byte, as follows:
# + xxxxxx00 - a literal run
#   - In case this is not ffffxx00, this byte is followed by a single
#   byte containing count. This is in turn followed by count + 1
#   literals.
#   - If it is ffffnn00, nn is the number of bytes that contain the
#     count, minus 1. These bytes are in little endian order. Again,
#     this is followed by count + 1 literals.
# + hhhnnn01 - a "near" reference
#   - This is followed by another byte containing lower bits of offset
#     minus 1. The hhh bits of reference form higher bits of offset.
#     nnn bits are length - 4.
# + nnnnnn10 - a "far" reference
#   - This is followed by two bytes containing offset, in little endian
#     order. The nnnnnn bits of reference are length - 1.

def uncompress(data):
	result = bytearray()

	def append_ref(offset, length):
		assert offset <= len(result)
		if offset >= length:
			start = len(result) - offset
			result.extend(result[start:start + length])
		else:
			# The run of literals is inserted repeatedly
			i = len(result) - offset
			while length > 0:
				result.append(result[i])
				i += 1
				length -= 1

	off = 0
	(uncompressed_length, off) = read_var(data, off)

	while off < len(data):
		# print('at offset %x:' % (off + 4))
		c = ord(data[off])
		off += 1
		typ = c & 0x3

		if typ == 0: # literals
			if (c & 0xf0) == 0xf0:
				count = (c >> 2) & 0x3
				length = ord(data[off]) + 1
				off += 1
				i = 1
				while i <= count:
					b = ord(data[off])
					length += (b << i * 8)
					i += 1
					off += 1
			else:
				length = (c >> 2) + 1
			# print('  literal run: length = %x' % length)
			result.extend(data[off:off + length])
			off += length
		elif typ == 1: # near reference
			length = ((c >> 2) & 0x7) + 4
			high = c >> 5
			low = ord(data[off])
			offset = (high << 8) | low
			off += 1
			# print('  near ref: offset = %x, length = %x' % (offset, length))
			append_ref(offset, length)
		elif typ == 2: # far reference
			length = (c >> 2) + 1
			offset = ord(data[off]) | (ord(data[off + 1]) << 8)
			off += 2
			# print('  far ref: offset = %x, length = %x' % (offset, length))
			append_ref(offset, length)
		else:
			print("unknown type at offset 0x%x inside block" % (off + 4))
			assert False

	assert uncompressed_length == len(result)

	return result

class IWAParser(object):

    def __init__(self, data, page, parent):
	self.data = data
	self.page = page
	self.parent = parent

    def parse(self):
	off = 0
	i = 0
	while off < len(self.data):
	    obj_start = off
	    (off, length) = self._parse_header(off)
	    header_data = self.data[obj_start:off]
	    reflist_data = []
	    unknown1_data = []

	    # TODO: maybe the reflist is allowed even if there is no content?
	    if length > 0:
		c = int(read(self.data, off, '<B'))
		if c & 0xf0 == 0x20:
		    start = off
		    off = self._parse_reflist(off)
		    reflist_data = self.data[start:off]

		c = int(read(self.data, off, '<B'))
		if c & 0xf0 == 0x30:
		    start = off
		    off = self._parse_unknown1(off)
		    unknown1_data = self.data[start:off]

	    objiter = add_pgiter(self.page, 'Object %d' % i, 'iwa', 0, self.data[obj_start:off + length], self.parent)
	    add_pgiter(self.page, 'Header', 'iwa', 'iwa_object_header', header_data, objiter)
	    if len(reflist_data) > 0:
		# TODO: what does this mean, exactly? Should it perhaps be a part of header?
		add_pgiter(self.page, 'List of references', 'iwa', 'iwa_reflist', reflist_data, objiter)
	    if len(unknown1_data) > 0:
		add_pgiter(self.page, 'Unknown optional block', 'iwa', 0, unknown1_data, objiter)

	    if length > 0:
		off = self._parse_content(off, length, objiter)

	    i += 1

	# assert off == len(self.data)

    def _parse_header(self, offset):
	(tag, off) = read_var(self.data, offset)
	(eight, off) = rdata(self.data, off, '<B')
	assert int(eight) == 0x8
	(oid, off) = read_var(self.data, off)
	(twelve, off) = rdata(self.data, off, '<B')
	assert int(twelve) == 0x12
	(xtag, off) = read_var(self.data, off)
	(eight, off) = rdata(self.data, off, '<B')
	assert int(eight) == 0x8
	(xid, off) = read_var(self.data, off)
	(twelve, off) = rdata(self.data, off, '<B')
	assert int(twelve) == 0x12
	(more, off) = rdata(self.data, off, '5s')
	assert ord(more[0]) == 0x3
	assert ord(more[1]) == 0x1
	assert ord(more[2]) == 0x0
	assert ord(more[3]) == 0x5
	assert ord(more[4]) == 0x18
	(length, off) = read_var(self.data, off)
	return (off, length)

    def _parse_reflist(self, offset):
	(c, off) = rdata(self.data, offset, '<B')
	assert int(c) & 0xf0 == 0x20
	(length, off) = read_var(self.data, off)
	return off + int(length)

    def _parse_unknown1(self, offset):
	# FIXME: this is just a band-aid for what I see in some files.
	(c, off) = rdata(self.data, offset, '<B')
	assert int(c) & 0xf0 == 0x30
	(length, off) = read_var(self.data, off)
	return off + int(length)

    def _parse_content(self, offset, length, parent):
	add_pgiter(self.page, 'Content', 'iwa', 0, self.data[offset:offset + length], parent)
	return offset + length

def add_iwa_compressed_block(hd, size, data):
	(length, off) = rdata(data, 1, '<H')
	add_iter(hd, 'Compressed length', length, off - 2, 2, '<H')
	off += 1
	var_off = off
	(ulength, off) = read_var(data, off)
	add_iter(hd, 'Uncompressed length', ulength, var_off, off - var_off, '%ds' % (off - var_off))

def add_iwa_object_header(hd, size, data):
    orig = 0
    (tag, off) = read_var(data, 0)
    add_iter(hd, 'Tag ID', tag, orig, off - orig, '%ds' % (off - orig))
    off += 1
    orig = off
    (oid, off) = read_var(data, off)
    add_iter(hd, 'Object ID', oid, orig, off - orig, '%ds' % (off - orig))
    off += 1
    orig = off
    (xtag, off) = read_var(data, off)
    add_iter(hd, 'Tag ID', xtag, orig, off - orig, '%ds' % (off - orig))
    off += 1
    orig = off
    (ref, off) = read_var(data, off)
    add_iter(hd, 'ID / Reference???', ref, orig, off - orig, '%ds' % (off - orig))
    off += 1
    off += 5
    orig = off
    (length, off) = read_var(data, off)
    add_iter(hd, 'Length of content', length, orig, off - orig, '%ds' % (off - orig))

def add_iwa_reflist(hd, size, data):
    (flags, off) = rdata(data, 0, '<B')
    add_iter(hd, 'Flags???', '0x%x' % flags, off - 1, 1, '<B')
    orig = off
    (length, off) = read_var(data, off)
    add_iter(hd, 'Length', length, orig, off - orig, '%ds' % (off - orig))

    i = 0
    end = off + int(length)
    while off < end:
	orig = off
	(ref, off) = read_var(data, off)
	add_iter(hd, 'Reference %d' % i, ref, orig, off - orig, '%ds' % (off - orig))
	i += 1

iwa_ids = {
	'iwa_compressed_block': add_iwa_compressed_block,
	'iwa_object_header': add_iwa_object_header,
	'iwa_reflist': add_iwa_reflist,
}

def open(data, page, parent):
	n = 0
	off = 0
	uncompressed_data = bytearray()

	while off < len(data):
		off += 1
		(length, off) = rdata(data, off, '<H')
		off += 1

		block = data[off - 4:off + int(length)]
		blockiter = add_pgiter(page, 'Block %d' % n, 'iwa', 'iwa_compressed_block', block, parent)
		uncompressed = uncompress(block[4:])
		uncompressed_data.extend(uncompressed)
		add_pgiter(page, 'Uncompressed', 'iwa', 0, str(uncompressed), blockiter)

		n += 1
		off += length

	uncompressed_data = str(uncompressed_data)
	dataiter = add_pgiter(page, 'Uncompressed', 'iwa', 0, uncompressed_data, parent)
	parser = IWAParser(uncompressed_data, page, dataiter)
	parser.parse()

# vim: set ft=python sts=4 sw=4 noet:
