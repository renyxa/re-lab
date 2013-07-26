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
import zlib

from utils import add_iter, add_pgiter, rdata

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

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

			for i in range(1, len(self.records)):
				self.parse_data_record(i, self.data[self.records[i]:self.get_record_end(i)], reciter)

	def parse_header(self):
		(count, off) = rdata(self.data, 76, '>H')
		hdriter = add_pgiter(self.page, 'Header', 'pdb', 0, self.data[0:76 + 4 * count], self.parent)
		offiter = add_pgiter(self.page, 'Offset table', 'pdb', 0, self.data[76:76 + 4 * count], hdriter)

		for i in range(0, count):
			add_pgiter(self.page, 'Offset %d' % i, 'pdb', 0, self.data[off:off + 8], offiter)
			(record, off) = rdata(self.data, off, '>I')
			off += 4
			self.records.append(record)

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
		self.compression = None

	def parse_index_record(self, data, parent):
		pass

	def parse_data_record(self, n, data, parent):
		pass

class isilo3_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(isilo3_parser, self).__init__(data, page, parent)
		self.compression = None

	def parse_index_record(self, data, parent):
		pass

	def parse_data_record(self, n, data, parent):
		pass

class palmdoc_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(palmdoc_parser, self).__init__(data, page, parent)
		self.compression = None

	def parse_index_record(self, data, parent):
		pass

	def parse_data_record(self, n, data, parent):
		pass

class plucker_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(plucker_parser, self).__init__(data, page, parent)
		self.compression = None

	def parse_index_record(self, data, parent):
		pass

	def parse_data_record(self, n, data, parent):
		pass

class tealdoc_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(tealdoc_parser, self).__init__(data, page, parent)
		self.compression = None

	def parse_index_record(self, data, parent):
		pass

	def parse_data_record(self, n, data, parent):
		pass

class ztxt_parser(pdb_parser):

	def __init__(self, data, page, parent):
		super(ztxt_parser, self).__init__(data, page, parent)
		self.compression = None

	def parse_index_record(self, data, parent):
		pass

	def parse_data_record(self, n, data, parent):
		pass

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

pdb_ids = {
	"ereader_index": add_ereader_index,
}

pdb_types = {
	'DataPlkr': plucker_parser,
	'PNRdPPrs': ereader_parser,
	'SDocSilX': isilo3_parser,
	'TEXtREAd': palmdoc_parser,
	'TEXtTlDc': tealdoc_parser,
	'ToGoToGo': isilo_parser,
	'zTXTGPlm': ztxt_parser,
}

def open(buf, page, parent, pdbtype):
	if pdb_types.has_key(pdbtype):
		parser = pdb_types[pdbtype](buf, page, parent)
		parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
