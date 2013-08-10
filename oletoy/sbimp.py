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

imp_version = 0
# default for v.2
imp_file_header_size = 20
imp_dirname_length = 0

imp_resource_types = frozenset((
	'!!cm',
	'AncT',
	'BGcl',
	'BPgz',
	'BPgZ',
	'BPos',
	'eLnk',
	'ESts',
	'HfPz',
	'HfPZ',
	'HRle',
	'ImRn',
	'Lnks',
	'Mrgn',
	'Pcz0',
	'PcZ0',
	'Pcz1',
	'PcZ1',
	'pInf',
	'PPic',
	'StR2',
	'StRn',
	'Styl',
	'Tabl',
	'TCel',
	'TRow',
))

class imp_parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.files = 0
		self.directory_begin = 0
		self.directory_end = 0
		self.compressed = False

	def parse(self):
		self.parent = add_pgiter(self.page, 'IMP', 'lrf', 0, self.data, self.parent)
		self.parse_header()
		self.parse_directory()
		self.parse_files()

	def parse_header(self):
		add_pgiter(self.page, 'Header', 'imp', 'imp_header', self.data[0:48], self.parent)

		global imp_dirname_length
		global imp_file_header_size
		global imp_version

		(version, off) = rdata(self.data, 0, '>H')
		imp_version = int(version)
		if imp_version == 1:
			imp_file_header_size = 10
		off += 16
		(files, off) = rdata(self.data, off, '>H')
		self.files = int(files)
		(dirname_length, off) = rdata(self.data, off, '>H')
		imp_dirname_length = int(dirname_length)
		(remaining, off) = rdata(self.data, off, '>H')
		self.directory_begin = 24 + int(remaining)
		self.directory_end = self.directory_begin + imp_dirname_length + self.files * imp_file_header_size
		off += 8
		(compression, off) = rdata(self.data, off, '>I')
		self.compressed = int(compression) == 1

		add_pgiter(self.page, 'Metadata', 'imp', 'imp_metadata', self.data[49:self.directory_begin], self.parent)

	def parse_directory(self):
		data = self.data[self.directory_begin:self.directory_end]
		diriter = add_pgiter(self.page, 'Directory', 'imp', 'imp_directory', data, self.parent)
		off = imp_dirname_length

		for i in range(self.files):
			begin = off + i * imp_file_header_size
			end = begin + imp_file_header_size
			add_pgiter(self.page, 'Entry %d' % i, 'imp', 'imp_directory_entry', data[begin:end], diriter)

	def parse_files(self):
		data = self.data[self.directory_end:len(self.data)]
		fileiter = add_pgiter(self.page, 'Files', 'imp', 0, data, self.parent)

		begin = 0
		for i in range(self.files):
			(length, off) = rdata(data, begin + 8, '>I')
			(typ, off) = rdata(data, off, '4s')
			end = begin + int(length) + 20
			self.parse_file(data[begin:end], i, typ, fileiter)
			begin = end

	def parse_file(self, data, n, typ, parent):
		typ_str = typ
		text = False
		if typ == '    ':
			text = True
			typ_str = 'Text'
		fileiter = add_pgiter(self.page, 'File %d (type %s)' % (n, typ_str), 'imp', 0, data, parent)
		add_pgiter(self.page, 'Header', 'imp', 'imp_file_header', data[0:20], fileiter)

		filedata = data[20:len(data)]
		if typ in imp_resource_types:
			self.parse_resource(filedata, typ, fileiter)
		elif text:
			self.parse_text(filedata, fileiter)

	def parse_resource(self, data, typ, parent):
		add_pgiter(self.page, 'Resource header', 'imp', 'imp_resource_header', data[0:32], parent)
		offset = int(read(data, 10, '>I'))
		res_data = data[32:offset]
		idx_data = data[offset:len(data)]
		resiter = add_pgiter(self.page, 'Resources', 'imp', 0, res_data, parent)
		idxiter = add_pgiter(self.page, 'Index', 'imp', 0, idx_data, parent)

		idx = self.parse_resource_index(idx_data, idxiter)
		if typ == '!!cm':
			self.parse_compression(data, idx, resiter)

	def parse_resource_index(self, data, parent):
		index = {}

		off = 0
		i = 0
		# Rev-eng. doc. says 12, but that does not match what I see...
		entrylen = 14
		while off + entrylen <= len(data):
			add_pgiter(self.page, 'Entry %d' % i, 'imp', 'imp_resource_index', data[off:off + entrylen], parent)
			(idx, off) = rdata(data, off, '<I')
			(length, off) = rdata(data, off, '<I')
			(start, off) = rdata(data, off, '<I')
			index[int(idx)] = (int(start), int(length))
			off += 2
			i += 1

		# assert off == len(data)

		return index

	def parse_compression(self, data, index, parent):
		for i in index.keys():
			res = index[i]
			resdata = data[res[0]:res[0] + res[1]]

			if i == 0x64:
				add_pgiter(self.page, 'Resource 0x64', 'imp', 'imp_resource_0x64', resdata, parent)

			elif i == 0x65:
				resiter = add_pgiter(self.page, 'Resource 0x65', 'imp', 0, resdata, parent)
				count = len(resdata) / 10
				recbegin = 0
				for j in range(count):
					recid = 'imp_resource_0x65'
					if j == count - 1:
						recid = 'imp_resource_0x65_last'
					recdata = resdata[recbegin:recbegin + 10]
					add_pgiter(self.page, 'Record %d' % j, 'imp', recid, recdata, resiter)
					recbegin += 10

	def parse_text(self, data, parent):
		if not self.compressed:
			add_pgiter(self.page, 'Text', 'imp', 0, data, parent)

def add_imp_directory(hd, size, data):
	fmt = '%ds' % imp_dirname_length
	name = read(data, 0, fmt)
	add_iter(hd, 'Directory name', name, 0, imp_dirname_length, fmt)

def add_imp_directory_entry(hd, size, data):
	if imp_version == 1:
		(name, off) = rdata(data, 0, '4s')
		add_iter(hd, 'File name', name, 0, 4, '4s')
		off += 2
		(size, off) = rdata(data, off, '>I')
		add_iter(hd, 'File size', size, off - 4, 4, '>I')
	elif imp_version == 2:
		add_imp_file_header(hd, size, data)
	else:
		assert False

def add_imp_file_header(hd, size, data):
	(name, off) = rdata(data, 0, '4s')
	add_iter(hd, 'File name', name, 0, 4, '4s')
	off += 4
	(size, off) = rdata(data, off, '>I')
	add_iter(hd, 'File size', size, off - 4, 4, '>I')
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'File type', typ, off - 4, 4, '4s')

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

def add_imp_resource_0x64(hd, size, data):
	off = 6
	(window, off) = rdata(data, off, '>H')
	add_iter(hd, 'Compression window size', window, off - 2, 2, '>H')
	(lookahead, off) = rdata(data, off, '>H')
	add_iter(hd, 'Look-ahead buffer size', lookahead, off - 2, 2, '>H')

def add_imp_resource_0x65(hd, size, data):
	(uncompressed_pos, off) = rdata(hd, 0, '>I')
	add_iter(hd, 'Byte position in uncompressed data', uncompressed_pos, 0, 4, '>I')
	(compressed_pos, off) = rdata(hd, off, '>I')
	add_iter(hd, 'Byte position in compressed data', compressed_pos, off - 4, 4, '>I')
	bit_pos_map = {
		0x1: 7,
		0x2: 6,
		0x4: 5,
		0x8: 4,
		0x10: 3,
		0x20: 2,
		0x40: 1,
		0x80: 0,
	}
	(bit_pos, off) = rdata(hd, off, '>H')
	bit_pos_val = 0
	if bit_pos_map.has_key(ord(bit_pos)):
		bit_pos_val = bit_pos_map[ord(bit_pos)]
	add_iter(hd, 'Bit position in compressed data', bit_pos_val, off - 2, 2, '>H')

def add_imp_resource_0x65_last(hd, size, data):
	(length, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Length of uncompressed text', length, 0, 4, '>I')

def add_imp_resource_header(hd, size, data):
	(version, off) = rdata(data, 0, '>H')
	add_iter(hd, 'Version', version, off - 2, 2, '>H')
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'File type', typ, off - 4, 4, '4s')
	off += 4
	(offset, off) = rdata(data, off, '>I')
	add_iter(hd, 'Offset to start of index', offset, off - 4, 4, '>I')

def add_imp_resource_index(hd, size, data):
	# Okay, this is just insane... The whole format uses big endian, but
	# the record index items are little endian. I only hope it happened
	# because of a bug in eBook Publisher, not as a conscious decision.
	(idx, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Resource ID', '0x%x' % int(idx), 0, 4, '<I')
	(length, off) = rdata(data, off, '<I')
	add_iter(hd, 'Record length', length, off - 4, 4, '<I')
	(start, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset to start of record', start, off - 4, 4, '<I')

imp_ids = {
	'imp_directory': add_imp_directory,
	'imp_directory_entry': add_imp_directory_entry,
	'imp_file_header': add_imp_file_header,
	'imp_header': add_imp_header,
	'imp_metadata': add_imp_metadata,
	'imp_resource_0x64': add_imp_resource_0x64,
	'imp_resource_0x65': add_imp_resource_0x65,
	'imp_resource_0x65_last': add_imp_resource_0x65_last,
	'imp_resource_header': add_imp_resource_header,
	'imp_resource_index': add_imp_resource_index,
}

def open(buf, page, parent):
	parser = imp_parser(buf, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
