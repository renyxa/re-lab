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

def uncompress(data):
	result = []

	def append_ref(offset, length):
		assert offset < len(result)
		if offset > length:
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
		c = ord(data[off])
		off += 1
		typ = c & 0x3

		if typ == 0: # literals
			if c == 0xf0:
				length = ord(data[off]) + 1
				off += 1
			else:
				length = (c >> 2) + 1
			result.extend(data[off:off + length])
			off += length
		elif typ == 1: # near reference
			length = ((c >> 2) & 0x7) + 4
			high = c >> 5
			low = ord(data[off])
			offset = (high << 8) | low
			off += 1
			append_ref(offset, length)
		elif typ == 2: # far reference
			length = (c >> 2) + 1
			offset = ord(data[off]) | (ord(data[off + 1]) << 8)
			off += 2
			append_ref(offset, length)
		else:
			print("unknown type at offset 0x%x inside block" % (off + 4))
			assert False

	assert uncompressed_length == len(result)

	return result

def open(data, page, parent):
	(length, off) = rdata(data, 0, '<I')
	length = int(length) >> 8
	n = 0
	while off < len(data):
		block = data[off:off + length]
		uncompressed = uncompress(block)
		blockiter = add_pgiter(page, 'Block %d' % n, 'iwa', 0, block, parent)
		add_pgiter(page, 'Uncompressed', 'iwa', 0, uncompressed, blockiter)

		n += 1
		off += length
		if off < len(data):
			(length, off) = rdata(data, off, '<I')

# vim: set ft=python sts=4 sw=4 noet:
