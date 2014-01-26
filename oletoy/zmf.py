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
		self._parse_group(self.data, self.parent)

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

zmf4_objects = {
	# gap
	0xa: "Object 0xa",
	# gap
	0xc: "Object 0xc",
	# gap
	0xe: "Bitmap?",
	# gap
	0x10: "Object 0x10",
	0x11: "Object 0x11",
	0x12: "Object 0x12",
	# gap
	0x1e: "Preview bitmap?",
	# gap
	0x21: "Start of page",
	0x22: "Master page?",
	0x23: "End of page",
	0x24: "Start of layer",
	0x25: "End of layer",
	0x26: "View",
	0x27: "Document settings",
	0x28: "Stylesheet?",
	# gap
	0x32: "Rectangle",
	0x33: "Ellipse",
	0x34: "Polygon",
	# gap
	0x36: "Polyline",
	# gap
	0x3a: "Object 0x3a",
	0x3b: "Table",
	# gap
	0x41: "Start of bar code?",
	0x42: "End of bar code?",
}

# defined later
zmf4_handlers = {}

class ZMF4Parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.preview_offset = 0

	def parse(self):
		content = self.parse_header()
		self.parse_content(content)

	def parse_header(self):
		(offset, off) = rdata(self.data, 0x20, '<I')
		(preview, off) = rdata(self.data, off, '<I')
		if int(preview) != 0:
			self.preview_offset = int(preview) - int(offset)
			assert self.preview_offset == 0x20 # this is what I see in all files
		data = self.data[0:int(offset)]
		add_pgiter(self.page, 'Header', 'zmf', 'zmf4_header', data, self.parent)
		return offset

	def parse_content(self, begin):
		data = self.data[begin:]
		content_iter = add_pgiter(self.page, 'Content', 'zmf', 0, data, self.parent)
		if self.preview_offset == 0:
			self._parse_group(data, content_iter)
		else:
			self._parse_group(data[0:self.preview_offset], content_iter)
			(typ, off) = rdata(data, self.preview_offset, '2s')
			# TODO: possibly there are other types?
			assert typ == 'BM'
			(size, off) = rdata(data, off, '<I')
			assert int(size) < len(data)
			add_pgiter(self.page, 'Bitmap data', 'zmf', 'zmf4_bitmap',
					data[self.preview_offset:self.preview_offset + int(size)], content_iter)
			self._parse_group(data[self.preview_offset + int(size):], content_iter)

	def parse_object(self, data, parent, typ, callback):
		self._do_parse_object(data, parent, typ, callback)

	def _parse_object(self, data, parent):
		off = 4
		(typ, off) = rdata(data, off, '<H')
		if zmf4_handlers.has_key(int(typ)):
			(handler, callback) = zmf4_handlers[int(typ)]
			handler(self, data, parent, typ, callback)
		else:
			self._do_parse_object(data, parent, typ, 'zmf4_obj')

	def _do_parse_object(self, data, parent, typ, callback):
		if zmf4_objects.has_key(typ):
			obj = zmf4_objects[typ]
		else:
			obj = 'Unknown object 0x%x' % typ
		return add_pgiter(self.page, obj, 'zmf', callback, data, parent)

	def _parse_group(self, data, parent):
		off = 0
		while off + 4 <= len(data):
			length = int(read(data, off, '<I'))
			if off + length <= len(data):
				self._parse_object(data[off:off + length], parent)
			off += length

zmf4_handlers = {
	0x27: (ZMF4Parser.parse_object, 'zmf4_obj_doc_settings'),
	0x32: (ZMF4Parser.parse_object, 'zmf4_obj_rectangle'),
	0x33: (ZMF4Parser.parse_object, 'zmf4_obj_ellipse'),
	0x36: (ZMF4Parser.parse_object, 'zmf4_obj_polyline'),
}

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

def add_zmf4_bitmap(hd, size, data):
	(typ, off) = rdata(data, 0, '2s')
	add_iter(hd, 'Signature', typ, off - 2, 2, '2s')
	(size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')

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

def _zmf4_obj_common(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<H')
	if zmf4_objects.has_key(typ):
		obj = zmf4_objects[typ]
	else:
		obj = 'Unknown object 0x%x' % typ
	add_iter(hd, 'Type', obj, off - 2, 2, '<I')
	return off

def add_zmf4_obj(hd, size, data):
	_zmf4_obj_common(hd, size, data)

def add_zmf4_obj_doc_settings(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x44
	(width, off) = rdata(data, off, '<I')
	# Note: maximum possible page size is 40305.08 x 28500 mm. Do not ask me why...
	add_iter(hd, 'Page width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page height', height, off - 4, 4, '<I')
	off = 0x88
	# The page is placed on a much bigger canvas
	# NOTE: it seems that positions are in respect to canvas, not to page.
	(cwidth, off) = rdata(data, off, '<I')
	add_iter(hd, 'Canvas width', cwidth, off - 4, 4, '<I')
	(cheight, off) = rdata(data, off, '<I')
	add_iter(hd, 'Canvas height', cheight, off - 4, 4, '<I')
	(left, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of left side of page', left, off - 4, 4, '<I')
	(top, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of top side of page', top, off - 4, 4, '<I')
	(right, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of right side of page', right, off - 4, 4, '<I')
	(bottom, off) = rdata(data, off, '<I')
	add_iter(hd, 'Offset of bottom side of page', bottom, off - 4, 4, '<I')

def add_zmf4_obj_ellipse(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x1c
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Height', height, off - 4, 4, '<I')

def add_zmf4_obj_polyline(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x5c
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of points', count, off - 4, 4, '<I')
	(closed, off) = rdata(data, off, '<I')
	add_iter(hd, 'Closed?', bool(closed), off - 4, 4, '<I')
	i = 1
	while i <= count:
		(x, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d X' % i, x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d Y' % i, y, off - 4, 4, '<I')
		i += 1

def add_zmf4_obj_rectangle(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x1c
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Height', height, off - 4, 4, '<I')
	(x1, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top left corner X', x1, off - 4, 4, '<I')
	(y1, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top left corner Y', y1, off - 4, 4, '<I')
	(x2, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top right corner X', x2, off - 4, 4, '<I')
	(y2, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top right corner Y', y2, off - 4, 4, '<I')
	(x3, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right corner X', x3, off - 4, 4, '<I')
	(y3, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right corner Y', y3, off - 4, 4, '<I')
	(x4, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom left corner X', x4, off - 4, 4, '<I')
	(y4, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom left corner Y', y4, off - 4, 4, '<I')
	(closed, off) = rdata(data, off, '<I')
	add_iter(hd, 'Closed?', bool(closed), off - 4, 4, '<I')

zmf_ids = {
	'zmf2_header': add_zmf2_header,
	'zmf2_object_header': add_zmf2_object_header,
	'zmf4_bitmap': add_zmf4_bitmap,
	'zmf4_header': add_zmf4_header,
	'zmf4_obj': add_zmf4_obj,
	'zmf4_obj_doc_settings': add_zmf4_obj_doc_settings,
	'zmf4_obj_ellipse': add_zmf4_obj_ellipse,
	'zmf4_obj_polyline': add_zmf4_obj_polyline,
	'zmf4_obj_rectangle': add_zmf4_obj_rectangle,
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
