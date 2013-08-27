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

# specification of the Palm Database Format:
# http://wiki.mobileread.com/wiki/PDB (2013)

import struct
import zlib

from utils import add_iter, add_pgiter, rdata

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class lz77_error:
	pass

"""Handler of LZ77 compression method, as used by PalmDoc."""
def lz77_decompress(data):
	buffer = []
	length = len(data)

	i = 0
	while i != length:
		c = data[i]
		o = ord(c)

		if o == 0 or (o >= 0x9 and o <= 0x7f):
			buffer.extend(c)
			i += 1

		elif o >= 1 and o <= 8:
			end = i + c
			if end >= length:
				raise lz77_error
			while i != end:
				cc = data[i]
				buffer.extend(cc)
			i += 1

		elif o >= 0x80 and o <= 0xbf:
			i += 1
			byte1 = o & 0x3f
			byte2 = ord(data[i])
			combined = (byte1 << 8) | byte2
			distance = (combined & 0xfff8) >> 3
			length = (combined & 0x7) + 3

			if distance > len(buffer):
				raise lz77_error
			if distance == 0:
				raise lz77_error

			if length < distance:
				buffer.append(buffer[len(buffer) - distance:length])
			else:
				repeated = buffer[len(buffer) - distance]
				buffer.append([repeated for j in range(length)])

			i += 1

		else:
			buffer.extend(' ')
			buffer.extend(chr(o ^ 0x80))
			i += 1

	return buffer

class pdb_parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = add_pgiter(page, 'PDB', 'pdb', 0, data, parent)
		self.records = []

	def get_record_end(self, n):
		if len(self.records) > n + 1:
			return self.records[n + 1]
		else:
			return len(self.data)

	def parse(self):
		self.parse_header()

		begin = 76 + 4 * len(self.records)
		reciter = add_pgiter(self.page, "Records", 'pdb', 0, self.data[begin:], self.parent)

		if len(self.records) > 0:
			self.parse_index_record(self.data[self.records[0]:self.get_record_end(0)], reciter)

			self.parsing_data_records(self.data[self.records[1]:len(self.data)], len(self.records) - 1)
			for i in range(1, len(self.records)):
				self.parse_data_record(i, self.data[self.records[i]:self.get_record_end(i)], reciter)

	def parse_header(self):
		(count, off) = rdata(self.data, 76, '>H')
		hdriter = add_pgiter(self.page, 'Header', 'pdb', 'pdb_header', self.data[0:76 + 4 * count], self.parent)
		offiter = add_pgiter(self.page, 'Offset table', 'pdb', 0, self.data[76:76 + 4 * count], hdriter)

		for i in range(0, count):
			add_pgiter(self.page, 'Offset %d' % i, 'pdb', 'pdb_offset', self.data[off:off + 8], offiter)
			(record, off) = rdata(self.data, off, '>I')
			off += 4
			self.records.append(record)

	def parsing_data_records(self, data, count):
		pass

# specification: http://wiki.mobileread.com/wiki/EReader (2013)
class ereader_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(ereader_parser, self).__init__(data, page, parent)
		self.compression = None

	def parse_index_record(self, data, parent):
		add_pgiter(self.page, 'Index', 'pdb', 'ereader_index', data, parent)
		self.compression = read(data, 0, '>H')

	def parse_data_record(self, n, data, parent):
		reciter = add_pgiter(self.page, "Record %d" % n, 'pdb', 0, data, parent)
		if self.compression == 4:
			unscrambled = [(chr(ord(b) ^ 0xa5)) for b in data]
			add_pgiter(self.page, "Uncompressed", 'pdb', 0, unscrambled, reciter)

class isilo_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(isilo_parser, self).__init__(data, page, parent)

	def parse_index_record(self, data, parent):
		add_pgiter(self.page, 'Index', 'pdb', 'isilo_index', data, parent)

	def parse_data_record(self, n, data, parent):
		add_pgiter(self.page, "Record %d" % n, 'pdb', 0, data, parent)

class isilo3_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(isilo3_parser, self).__init__(data, page, parent)

	def parse_index_record(self, data, parent):
		add_pgiter(self.page, 'Index', 'pdb', 'isilo3_index', data, parent)

	def parse_data_record(self, n, data, parent):
		add_pgiter(self.page, "Record %d" % n, 'pdb', 0, data, parent)

# specification: http://wiki.mobileread.com/wiki/PalmDOC (2013)
class palmdoc_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(palmdoc_parser, self).__init__(data, page, parent)

	def parse_index_record(self, data, parent):
		add_pgiter(self.page, 'Index', 'pdb', 'palmdoc_index', data, parent)
		self.compression = read(data, 0, '>H')

	def parse_data_record(self, n, data, parent):
		reciter = add_pgiter(self.page, "Text %d" % n, 'pdb', 0, data, parent)
		if self.compression == 2:
			uncompressed = lz77_decompress(data)
			add_pgiter(self.page, "Uncompressed", 'pdb', 0, uncompressed, reciter)

# specification: http://www.fifi.org/doc/plucker/manual/DBFormat.html
# (2013)

plucker_type = (
	'Text',
	'Compressed text',
	'Image',
	'Compressed image',
	'Mailto',
	'URL handling',
	'URL data',
	'Compressed URL data',
	'External bookmarks',
	'Default category',
	'Metadata',
)

class plucker_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(plucker_parser, self).__init__(data, page, parent)
		self.version = 0
		self.reserved_records = {}

	def parse_index_record(self, data, parent):
		reciter = add_pgiter(self.page, 'Index', 'pdb', 'plucker_index', data, parent)
		off = 2
		(self.version, off) = rdata(data, off, '>H')
		(records, off) = rdata(data, off, '>H')
		for i in range(int(records)):
			(name, off) = rdata(data, off, '>H')
			(ident, off) = rdata(data, off, '>H')
			self.reserved_records[ident] = name
			record_data = data[off - 4:off]
			add_pgiter(self.page, 'Reserved record %d' % i, 'pdb', 'plucker_record_index', record_data, reciter)

	def parse_data_record(self, n, data, parent):
		(para, off) = rdata(data, 2, '>H')
		off += 2
		(typ, off) = rdata(data, off, 'B')
		typ_str = None
		if int(typ) < len(plucker_type):
			typ_str = ' (%s)' % plucker_type[int(typ)]
		reciter = add_pgiter(self.page, 'Record %d%s' % (n, typ_str), 'pdb', 'plucker_record', data, parent)

		if typ == 0 or typ == 1:
			# read para headers
			off = 8
			paraiter = add_pgiter(self.page, 'Paragraphs', 'pdb', 0, data[off:off + 4 * int(para)], reciter)
			for i in range(int(para)):
				(size, off) = rdata(data, off, '>H')
				(attrs, off) = rdata(data, off, '>H')
				add_pgiter(self.page, 'Paragraph %d' % i, 'pdb', 'plucker_para', data[off - 4:off], paraiter)

			text = data[off:len(data)]

			if typ == 0:
				add_pgiter(self.page, 'Text', 'pdb', 0, text, reciter)
			elif typ == 1:
				if self.version == 1:
					uncompressed = lz77_decompress(text)
					add_pgiter(self.page, 'Text', 'pdb', 0, uncompressed, reciter)
				elif self.version == 2:
					uncompressed = zlib.decompress(text)
					add_pgiter(self.page, 'Text', 'pdb', 0, uncompressed, reciter)

# specification: http://wiki.mobileread.com/wiki/TealDoc (2013)
class tealdoc_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(tealdoc_parser, self).__init__(data, page, parent)

	def parse_index_record(self, data, parent):
		add_pgiter(self.page, 'Index', 'pdb', 'tealdoc_index', data, parent)

	def parse_data_record(self, n, data, parent):
		reciter = add_pgiter(self.page, "Record %d" % n, 'pdb', 0, data, parent)
		if self.compression == 2:
			uncompressed = lz77_decompress(data)
			add_pgiter(self.page, "Uncompressed", 'pdb', 0, uncompressed, reciter)

class tomeraider3_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(tomeraider3_parser, self).__init__(data, page, parent)

	def parse_index_record(self, data, parent):
		add_pgiter(self.page, 'Index', 'pdb', 'tomeraider3_index', data, parent)

	def parse_data_record(self, n, data, parent):
		add_pgiter(self.page, "Record %d" % n, 'pdb', 0, data, parent)

# specification: http://gutenpalm.sourceforge.net/ztxt_format.php (2013)
class ztxt_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(ztxt_parser, self).__init__(data, page, parent)
		self.version = 0
		self.record_count = 0
		self.record_size = 0
		self.text_length = 0
		self.compression = 0

	def parse_index_record(self, data, parent):
		off = 0
		(self.version, off) = rdata(data, off, '>H')
		(self.record_count, off) = rdata(data, off, '>H')
		(self.text_length, off) = rdata(data, off, '>I')
		(self.record_size, off) = rdata(data, off, '>H')
		off += 8
		(self.compression, off) = rdata(data, off, 'B')
		add_pgiter(self.page, 'Index', 'pdb', 'ztxt_index', data, parent)

	def parse_data_record(self, n, data, parent):
		add_pgiter(self.page, "Record %d" % n, 'pdb', 0, data, parent)

def add_ereader_index(hd, size, data):
	(compression, off) = rdata(data, 0, '>H')
	add_iter(hd, 'Compression', compression, 0, 2, '>H')

	# There are two different headers created by applications
	if len(data) == 132:
		pass
	elif len(data) == 202:
		off += 6
		(first_nontext, off) = rdata(data, off, '>H')
		add_iter(hd, 'First non-text record', first_nontext, off - 2, 2, '>H')
		off = 0x6e
		(chapters, off) = rdata(data, off, '>H') # ???
		add_iter(hd, 'Number of chapters in TOC', chapters, off - 2, 2, '>H')

def add_isilo_index(hd, size, data):
	pass

def add_isilo3_index(hd, size, data):
	pass

def add_palmdoc_index(hd, size, data):
	(compression_value, off) = rdata(data, 0, '>H')
	if compression_value == 1:
		compression = 'None'
	elif compression_value == 2:
		compression = 'LZ77'
	else:
		compression = 'Unknown'
	add_iter(hd, 'Compression', compression, 0, 2, '>H')

	off += 2
	(length, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Text length', length, off - 4, 4, '>I')
	(count, off) = rdata(data, off, '>H')
	add_iter(hd, 'Record count', count, off - 2, 2, '>H')
	(size, off) = rdata(data, off, '>H')
	add_iter(hd, 'Max. record size', size, off - 2, 2, '>H')

def add_pdb_header(hd, size, data):
	(name, off) = rdata(data, 0, '32s')
	add_iter(hd, 'Name', name, 0, 32, '32s')
	off += 2
	(version, off) = rdata(data, off, '>H')
	add_iter(hd, 'Version', version, off - 2, 2, '>H')
	(cdate, off) = rdata(data, off, '>I')
	add_iter(hd, 'Creation date', cdate, off - 4, 4, '>I')
	(mdate, off) = rdata(data, off, '>I')
	add_iter(hd, 'Modification date', mdate, off - 4, 4, '>I')
	off += 8
	(appinfo, off) = rdata(data, off, '>I')
	add_iter(hd, 'AppInfo offset', appinfo, off - 4, 4, '>I')
	off += 4
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'Type', typ, off - 4, 4, '4s')
	(creator, off) = rdata(data, off, '4s')
	add_iter(hd, 'Creator', creator, off - 4, 4, '4s')
	off += 8
	(records, off) = rdata(data, off, '>H')
	add_iter(hd, 'Number of records', records, off - 2, 2, '>H')

def add_pdb_offset(hd, size, data):
	(offset, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Offset', offset, 0, 4, '>I')
	(ident, off) = rdata(data, off, '>I')
	add_iter(hd, 'ID', ident, off - 4, 4, '>I')

def add_plucker_index(hd, size, data):
	(uid, off) = rdata(data, 0, '>H')
	add_iter(hd, 'Record ID', uid, off - 2, 2, '>H')
	(version, off) = rdata(data, off, '>H')
	if version == 1:
		compression = 'LZ77'
	elif version == 2:
		compression = 'Zlib'
	else:
		compression = 'Unknown'
	add_iter(hd, 'Compression', compression, off - 2, 2, '>H')
	(records, off) = rdata(data, off, '>H')
	add_iter(hd, 'Reserved records', records, off - 2, 2, '>H')

def add_plucker_para(hd, size, data):
	(size, off) = rdata(data, 0, '>H')
	add_iter(hd, 'Size', size, off - 2, 2, '>H')
	(attrs, off) = rdata(data, off, '>H')
	add_iter(hd, 'Attributes', attrs, off - 2, 2, '>H')

def add_plucker_record_index(hd, size, data):
	(name, off) = rdata(data, 0, '>H')
	(ident, off) = rdata(data, off, '>H')
	add_iter(hd, 'ID', ident, off - 2, 2, '>H')
	if name == 0:
		title = 'home.html'
	elif name == 1:
		title = 'external bookmarks'
	elif name == 2:
		title = 'URL handling'
	elif name == 3:
		title = 'default category'
	elif name == 4:
		title = 'additional metadata'
	else:
		title = 'Unknown'
	add_iter(hd, 'Name', title, off - 2, 2, '>H')

def add_plucker_record(hd, size, data):
	(ident, off) = rdata(data, 0, '>H')
	add_iter(hd, 'UID', ident, off - 2, 2, '>H')
	(paragraphs, off) = rdata(data, off, '>H')
	add_iter(hd, 'Paragraphs', paragraphs, off - 2, 2, '>H')
	(size, off) = rdata(data, off, '>H')
	add_iter(hd, 'Size of data', size, off - 2, 2, '>H')
	(typ, off) = rdata(data, off, 'B')
	typ_str = 'Unknown'
	if int(typ) < len(plucker_type):
		typ_str = plucker_type[int(typ)]
	add_iter(hd, 'Type', typ_str, off - 1, 1, 'B')

def add_tealdoc_index(hd, size, data):
	(compression_value, off) = rdata(data, 0, '>H')
	if compression_value == 1:
		compression = 'None'
	elif compression_value == 2:
		compression = 'LZ77'
	else:
		compression = 'Unknown'
	add_iter(hd, 'Compression', compression, 0, 2, '>H')

	off += 2
	(length, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Text length', length, off - 4, 4, '>I')
	(count, off) = rdata(data, off, '>H')
	add_iter(hd, 'Record count', count, off - 2, 2, '>H')
	(size, off) = rdata(data, off, '>H')
	add_iter(hd, 'Max. record size', size, off - 2, 2, '>H')

def add_tomeraider3_index(hd, size, data):
	pass

def add_ztxt_index(hd, size, data):
	off = 0
	(version, off) = rdata(data, off, '>H')
	add_iter(hd, 'Version', version, off - 2, 2, '>H')
	(count, off) = rdata(data, off, '>H')
	add_iter(hd, 'Record count', count, off - 2, 2, '>H')
	(length, off) = rdata(data, off, '>I')
	add_iter(hd, 'Text size', length, off - 4, 4, '>I')
	(size, off) = rdata(data, off, '>H')
	add_iter(hd, 'Record size', size, off - 2, 2, '>H')
	off += 8
	(compression, off) = rdata(data, off, 'B')
	if compression == 1:
		mode = 'Random access'
	elif compression == 2:
		mode = 'Nonuniform'
	else:
		mode = 'Unknown'
	add_iter(hd, 'Compression mode', mode, off - 1, 1, 'B')

pdb_ids = {
	'ereader_index': add_ereader_index,
	'isilo_index': add_isilo_index,
	'isilo3_index': add_isilo3_index,
	'palmdoc_index': add_palmdoc_index,
	'pdb_header': add_pdb_header,
	'pdb_offset': add_pdb_offset,
	'plucker_index': add_plucker_index,
	'plucker_para': add_plucker_para,
	'plucker_record_index': add_plucker_record_index,
	'plucker_record': add_plucker_record,
	'tealdoc_index': add_tealdoc_index,
	'tomeraider3_index': add_tomeraider3_index,
	'ztxt_index': add_ztxt_index,
}

pdb_types = {
	'DataPlkr': plucker_parser,
	'PNRdPPrs': ereader_parser,
	'SDocSilX': isilo3_parser,
	'TEXtREAd': palmdoc_parser,
	'TEXtTlDc': tealdoc_parser,
	'ToGoToGo': isilo_parser,
	'TR3DTR3C': tomeraider3_parser,
	'zTXTGPlm': ztxt_parser,
}

def open(buf, page, parent, pdbtype):
	if pdb_types.has_key(pdbtype):
		parser = pdb_types[pdbtype](buf, page, parent)
		parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
