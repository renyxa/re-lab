# Copyright (C) 2013 David Tardon (dtardon@redhat.com)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 or later of the GNU General Public
# License as published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA
#

# Parser of SoftBook .imp format

# reverse-engineered specification: http://www.chromakinetics.com/REB1200/imp_format.htm

from utils import add_iter, add_pgiter, rdata

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

def read_cstring(data, offset):
	begin = offset
	while offset < len(data) and data[offset] != chr(0):
		offset += 1
	# include the \0
	if offset < len(data):
		offset += 1
	return (data[begin:offset], offset, offset - begin)

class imp_parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		self.parent = add_pgiter(self.page, 'IMP', 'lrf', 0, self.data, self.parent)
		self.parse_header()

	def parse_header(self):
		add_pgiter(self.page, 'Header', 'imp', 'imp_header', self.data[0:48], self.parent)
		metadata_end = 0
		remaining = read(self.data, 0x16, '>H')
		add_pgiter(self.page, 'Metadata', 'imp', 'imp_metadata', self.data[49:24 + remaining], self.parent)

IMP_ZOOM_STATES = ('Both', 'Small', 'Large')

def add_imp_header(hd, size, data):
	(version, off) = rdata(data, 0, '>H')
	add_iter(hd, 'Version', version, off - 2, 2, '>H')
	(sig, off) = rdata(data, off, '8s')
	add_iter(hd, 'Signature', sig, off - 8, 8, '8s')
	off += 8
	(count, off) = rdata(data, off, '>H')
	add_iter(hd, 'Number of files', count, off - 2, 2, '>H')
	(dirname_len, off) = rdata(data, off, '>H')
	add_iter(hd, 'Length of dir. name', dirname_len, off - 2, 2, '>H')
	(remaining, off) = rdata(data, off, '>H')
	add_iter(hd, 'Remaining bytes of header', remaining, off - 2, 2, '>H')
	off += 8
	(compression, off) = rdata(data, off, '>I')
	add_iter(hd, 'Compressed?', compression != 0, off - 4, 4, '>I')
	(encryption, off) = rdata(data, off, '>I')
	add_iter(hd, 'Encrypted?', encryption != 0, off - 4, 4, '>I')
	(zoom, off) = rdata(data, off, '>I')
	zoom_str = 'Unknown'
	if int(zoom) < 3:
		zoom_str = IMP_ZOOM_STATES[int(zoom)]
	add_iter(hd, 'Zoom state', zoom_str, off - 4, 4, '>I')
	off += 4
	assert off == 30

def add_imp_metadata(hd, size, data):
	(ident, off, length) = read_cstring(data, 0)
	add_iter(hd, 'ID', ident, off - length, length, '%ds' % length)
	(category, off, length) = read_cstring(data, off)
	add_iter(hd, 'Category', category, off - length, length, '%ds' % length)
	(subcategory, off, length) = read_cstring(data, off)
	add_iter(hd, 'Subcategory', subcategory, off - length, length, '%ds' % length)
	(title, off, length) = read_cstring(data, off)
	add_iter(hd, 'Title', title, off - length, length, '%ds' % length)
	(last_name, off, length) = read_cstring(data, off)
	add_iter(hd, 'Last name', last_name, off - length, length, '%ds' % length)
	(middle_name, off, length) = read_cstring(data, off)
	add_iter(hd, 'Middle name', middle_name, off - length, length, '%ds' % length)
	(first_name, off, length) = read_cstring(data, off)
	add_iter(hd, 'First name', first_name, off - length, length, '%ds' % length)

imp_ids = {
	'imp_header': add_imp_header,
	'imp_metadata': add_imp_metadata,
}

def open(buf, page, parent):
	parser = imp_parser(buf, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
