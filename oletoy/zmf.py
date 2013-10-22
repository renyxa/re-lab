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

class ZMF2Parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent

	def parse(self):
		fileiter = add_pgiter(self.page, 'ZMF', 'zmf', 0, self.data, self.parent)
		self._parse_group(self.data, fileiter)

	def parse_object(self, data, parent):
		objiter = add_pgiter(self.page, 'Object', 'zmf', 'zmf2_object', data, parent)
		# TODO: this seems to fit, but it is not enough... I see two
		# nested objects in all files, with a lot of opaque data inside
		# the inner one. Maybe it is compressed?
		add_pgiter(self.page, 'Header', 'zmf', 'zmf2_object_header', data[0:16], objiter)
		# TODO: this is probably set of flags
		(typ, off) = rdata(data, 4, '<H')
		if typ == 0x4:
			self._parse_group(data[16:], objiter)
		else:
			add_pgiter(self.page, 'Data', 'zmf', 0, data[16:], objiter)

	def _parse_group(self, data, parent):
		off = 0
		while off + 4 <= len(data):
			length = int(read(data, off, '<I'))
			if off + length <= len(data):
				self.parse_object(data[off:off + length], parent)
			off += length

class ZMF4Parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.fileiter = None

	def parse(self):
		self.fileiter = add_pgiter(self.page, 'ZMF', 'zmf', 0, self.data, self.parent)
		content = self.parse_header()
		self.parse_content(content)

	def parse_header(self):
		offset = int(read(self.data, 0x20, '<I'))
		data = self.data[0:offset]
		add_pgiter(self.page, 'Header', 'zmf', 'zmf4_header', data, self.fileiter)
		return offset

	def parse_content(self, begin):
		data = self.data[begin:]
		content_iter = add_pgiter(self.page, 'Content', 'zmf', 0, data, self.fileiter)
		self._parse_group(data, content_iter)

	def parse_object(self, data, parent):
		objiter = add_pgiter(self.page, 'Object', 'zmf', 'zmf4_object', data, parent)
		add_pgiter(self.page, 'Header', 'zmf', 'zmf4_object_header', data[0:32], objiter)
		off = 4
		# TODO: this is probably set of flags
		(typ, off) = rdata(data, off, '<I')
		if typ == 0xc or typ == 0xd:
			self._parse_group(data[32:], objiter)
		else:
			add_pgiter(self.page, 'Data', 'zmf', 0, data[32:], objiter)

	def _parse_group(self, data, parent):
		off = 0
		while off + 4 <= len(data):
			length = int(read(data, off, '<I'))
			if off + length <= len(data):
				self.parse_object(data[off:off + length], parent)
			off += length

def add_zmf2_header(hd, size, data):
	off = 10
	(version, off) = rdata(data, off, '<H')
	add_iter(hd, 'Version', version, off - 2, 2, '<H')
	(sig, off) = rdata(data, off, '<I')
	add_iter(hd, 'Signature', '0x%x' % sig, off - 4, 4, '<I')

def add_zmf2_object_header(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Type', typ, off - 2, 2, '<H')

def add_zmf4_header(hd, size, data):
	off = 8
	(sig, off) = rdata(data, off, '<I')
	add_iter(hd, 'Signature', '0x%x' % sig, off - 4, 4, '<I')
	(version, off) = rdata(data, off, '<I')
	add_iter(hd, 'Version', version, off - 4, 4, '<I')
	off += 12
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Count of objects', count, off - 4, 4, '<I')
	(content, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start of content', content, off - 4, 4, '<I')
	(preview, off) = rdata(data, off, '<I')
	add_iter(hd, 'Start of preview bitmap', preview, off - 4, 4, '<I')
	off += 16
	(size, off) = rdata(data, off, '<I')
	add_iter(hd, 'File size', size, off - 4, 4, '<I')

def add_zmf4_object_header(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<I')
	add_iter(hd, 'Type', typ, off - 4, 4, '<I')

zmf_ids = {
	'zmf2_header': add_zmf2_header,
	'zmf2_object_header': add_zmf2_object_header,
	'zmf4_header': add_zmf4_header,
	'zmf4_object_header': add_zmf4_object_header,
}

def zmf2_open(page, data, parent, fname):
	if fname == 'Header':
		add_pgiter(page, 'Header', 'zmf', 'zmf2_header', data, parent)
	elif fname in ('BitmapDB.zmf', 'TextStyles.zmf', 'Callisto_doc.zmf', 'Callisto_pages.zmf'):
		if data != None:
			parser = ZMF2Parser(data, page, parent)
			parser.parse()

def zmf4_open(data, page, parent):
	parser = ZMF4Parser(data, page, parent)
	parser.parse()

# vim: set ft=python sts=4 sw=4 noet:
