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

class ZMF2Parser(object):

	def __init__(self, data, page, parent, parser):
		self.data = data
		self.page = page
		self.parent = parent
		self.parser = parser

	def parse(self):
		length = int(read(self.data, 0, '<I'))
		if length <= len(self.data):
			self._parse_file(self.data[0:length], self.parent)

	def parse_bitmap_db_doc(self, data, parent):
		pass

	def parse_text_styles_doc(self, data, parent):
		pass

	def parse_doc(self, data, parent):
		off = self._parse_header(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_dimensions(data, off, parent)
		off += 4 # something
		off = self._parse_object(data, off, parent)
		off += 4 # something
		off = self._parse_object(data, off, parent, 'Color palette')
		off += 0x4c # something
		off = self._parse_object(data, off, parent, 'Document')

	def parse_pages_doc(self, data, parent):
		pass

	def _parse_file(self, data, parent):
		# TODO: this is probably set of flags
		(typ, off) = rdata(data, 4, '<H')
		if typ == 0x4:
			objiter = add_pgiter(self.page, 'Compressed block', 'zmf', 'zmf2_compressed_block', data, parent)
			off += 10
			(size, off) = rdata(data, off, '<I')
			assert off == 0x14
			assert off + int(size) <= len(data)
			end = off + int(size)
			compressed = data[off:end]
			compiter = add_pgiter(self.page, 'Compressed data', 'zmf', 0, compressed, objiter)
			try:
				content = zlib.decompress(compressed)
				cntiter = add_pgiter(self.page, 'Data', 'zmf', 0, content, compiter)
				self.parser(self, content, cntiter)
			except zlib.error:
				print("decompression failed")
			if end < len(data):
				add_pgiter(self.page, 'Tail', 'zmf', 0, data[end:], objiter)
		else:
			add_pgiter(self.page, 'Block', 'zmf', 'zmf2_block', data, parent)

	def _parse_header(self, data, offset, parent):
		base_length = 0x4c
		layer_name_length = int(read(data, 0x38, '<I'))
		length = base_length + layer_name_length
		add_pgiter(self.page, 'Header', 'zmf', 'zmf2_doc_header', data[offset:length], parent)
		return length

	def _parse_object(self, data, offset, parent, name='Unknown object'):
		off = offset
		(size, off) = rdata(data, offset, '<I')
		objiter = add_pgiter(self.page, name, 'zmf', 0, data[offset:offset + int(size)], parent)

		# TODO: this is highly speculative
		(typ, off) = rdata(data, off, '<I')
		(subtyp, off) = rdata(data, off, '<I')
		if typ == 4 and subtyp == 3:
			header_size = 0x14
		elif typ == 4 and subtyp == 4:
			header_size = 0x14
		elif typ == 8 and subtyp == 5:
			header_size = 0x1c
		else:
			header_size = 0
		if header_size != 0:
			add_pgiter(self.page, 'Header', 'zmf', 'zmf2_obj_header', data[offset:offset + header_size], objiter)

		# TODO: parse content

		return offset + int(size)

	def _parse_dimensions(self, data, offset, parent):
		off = offset
		(size, off) = rdata(data, offset, '<I')
		add_pgiter(self.page, 'Dimensions', 'zmf', 'zmf2_doc_dimensions', data[offset:offset + int(size)], parent)
		return offset + int(size)

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
	0x12: "Text",
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
	0x34: "Polygon / Star",
	# gap
	0x36: "Polyline",
	# gap
	0x3a: "Text frame",
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
		obj_str = obj
		if len(data) >= 0x1c:
			(oid, off) = rdata(data, 0x18, '<I')
			if int(oid) != 0xffffffff:
				obj_str = '%s (0x%x)' % (obj, oid)
		return add_pgiter(self.page, obj_str, 'zmf', callback, data, parent)

	def _parse_group(self, data, parent):
		off = 0
		while off + 4 <= len(data):
			length = int(read(data, off, '<I'))
			if off + length <= len(data):
				self._parse_object(data[off:off + length], parent)
			off += length

zmf4_handlers = {
	0x12: (ZMF4Parser.parse_object, 'zmf4_obj_text'),
	0x27: (ZMF4Parser.parse_object, 'zmf4_obj_doc_settings'),
	0x32: (ZMF4Parser.parse_object, 'zmf4_obj_rectangle'),
	0x33: (ZMF4Parser.parse_object, 'zmf4_obj_ellipse'),
	0x34: (ZMF4Parser.parse_object, 'zmf4_obj_polygon'),
	0x36: (ZMF4Parser.parse_object, 'zmf4_obj_polyline'),
	0x3a: (ZMF4Parser.parse_object, 'zmf4_obj_text_frame'),
	0x3b: (ZMF4Parser.parse_object, 'zmf4_obj_table'),
}

def add_zmf2_header(hd, size, data):
	off = 10
	(version, off) = rdata(data, off, '<H')
	add_iter(hd, 'Version', version, off - 2, 2, '<H')
	(sig, off) = rdata(data, off, '<I')
	add_iter(hd, 'Signature', '0x%x' % sig, off - 4, 4, '<I')

def add_zmf2_block(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Type', typ, off - 2, 2, '<H')

def add_zmf2_compressed_block(hd, size, data):
	add_zmf2_block(hd, size, data)
	off = 0x10
	(data_size, off) = rdata(data, off, '<I')
	add_iter(hd, 'Size of data', data_size, off - 4, 4, '<I')

def add_zmf2_doc_header(hd, size, data):
	off = 8
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Total number of objects', count, off - 4, 4, '<I')
	off = 0x28
	(lr_margin, off) = rdata(data, off, '<I')
	add_iter(hd, 'Left & right page margin?', lr_margin, off - 4, 4, '<I')
	(tb_margin, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top & bottom page margin?', tb_margin, off - 4, 4, '<I')
	off += 8
	(strlen, off) = rdata(data, off, '<I')
	add_iter(hd, 'String length', strlen, off - 4, 4, '<I')
	layer_len = int(strlen) - 1
	(layer, off) = rdata(data, off, '%ds' % layer_len)
	add_iter(hd, 'Default layer name?', unicode(layer, 'cp1250'), off - layer_len, layer_len + 1, '%ds' % layer_len)

def add_zmf2_doc_dimensions(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	off += 8
	(cwidth, off) = rdata(data, off, '<I')
	add_iter(hd, 'Canvas width', cwidth, off - 4, 4, '<I')
	(cheight, off) = rdata(data, off, '<I')
	add_iter(hd, 'Canvas height', cheight, off - 4, 4, '<I')
	off += 4
	(tl_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page top left X', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page top left Y', tl_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page bottom right X', br_x, off - 4, 4, '<I')
	(br_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page bottom right Y', br_y, off - 4, 4, '<I')

def add_zmf2_obj_header(hd, size, data):
	(size, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Size', size, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<I')
	add_iter(hd, 'Type', typ, off - 4, 4, '<I')
	(subtyp, off) = rdata(data, off, '<I')
	add_iter(hd, 'Subtype', subtyp, off - 4, 4, '<I')
	if typ == 4 and subtyp == 3:
		off += 4
		(obj_type, off) = rdata(data, off, '<I')
		add_iter(hd, 'Object type', obj_type, off - 4, 4, '<I')
	elif typ == 4 and subtyp == 4:
		off += 4
		(count, off) = rdata(data, off, '<I')
		add_iter(hd, 'Number of subobjects', count, off - 4, 4, '<I')
	elif typ == 8 and subtyp == 5:
		off += 8
		(count, off) = rdata(data, off, '<I')
		add_iter(hd, 'Number of subobjects', count, off - 4, 4, '<I')

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
	if size >= 0x1c:
		off = 0x18
		(oid, off) = rdata(data, off, '<I')
		if int(oid) == 0xffffffff:
			oid_str = 'none'
		else:
			oid_str = '0x%x' % oid
		add_iter(hd, 'ID', oid_str, off - 4, 4, '<I')
	return off

def _zmf4_obj_bbox(hd, size, data, off):
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Height', height, off - 4, 4, '<I')
	(x1, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: top left corner X', x1, off - 4, 4, '<I')
	(y1, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: top left corner Y', y1, off - 4, 4, '<I')
	(x2, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: top right corner X', x2, off - 4, 4, '<I')
	(y2, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: top right corner Y', y2, off - 4, 4, '<I')
	(x3, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: bottom right corner X', x3, off - 4, 4, '<I')
	(y3, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: bottom right corner Y', y3, off - 4, 4, '<I')
	(x4, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: bottom left corner X', x4, off - 4, 4, '<I')
	(y4, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bounding box: bottom left corner Y', y4, off - 4, 4, '<I')
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
	off = _zmf4_obj_bbox(hd, size, data, off)
	(closed, off) = rdata(data, off, '<I')
	add_iter(hd, 'Closed?', bool(closed), off - 4, 4, '<I')

def add_zmf4_obj_polygon(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0xc
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of points', count, off - 4, 4, '<I')
	off += 12
	(width, off) = rdata(data, off, '<I')
	add_iter(hd, 'Width', width, off - 4, 4, '<I')
	(height, off) = rdata(data, off, '<I')
	add_iter(hd, 'Height', height, off - 4, 4, '<I')
	i = 1
	while i <= count:
		(x, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d X' % i, x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d Y' % i, y, off - 4, 4, '<I')
		i += 1

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
	off = _zmf4_obj_bbox(hd, size, data, off)
	(closed, off) = rdata(data, off, '<I')
	add_iter(hd, 'Closed?', bool(closed), off - 4, 4, '<I')

def add_zmf4_obj_table(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x1c
	off = _zmf4_obj_bbox(hd, size, data, off)
	off += 8
	(rows, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of rows', rows, off - 4, 4, '<I')
	(cols, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of columns', cols, off - 4, 4, '<I')
	off += 12

	i = 1
	while i <= rows * cols:
		off += 4
		(text, off) = rdata(data, off, '<I')
		add_iter(hd, 'Cell %d text reference' % i, '0x%x' % text, off - 4, 4, '<I')
		off += 12
		i += 1

def add_zmf4_obj_text(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x3c
	(count, off) = rdata(data, off, '<I')
	add_iter(hd, 'Length', count, off - 4, 4, '<I')
	off += 8
	length = 2 * int(count)
	(text, off) = rdata(data, off, '%ds' % length)
	add_iter(hd, 'Text', unicode(text, 'utf-16le'), off - length, length, '%ds' % length)

def add_zmf4_obj_text_frame(hd, size, data):
	_zmf4_obj_common(hd, size, data)
	off = 0x1c
	_zmf4_obj_bbox(hd, size, data, off)
	off = 0x88
	(text, off) = rdata(data, off, '<I')
	add_iter(hd, 'Text reference', '0x%x' % text, off - 4, 4, '<I')

zmf_ids = {
	'zmf2_header': add_zmf2_header,
	'zmf2_block': add_zmf2_block,
	'zmf2_compressed_block': add_zmf2_compressed_block,
	'zmf2_doc_header': add_zmf2_doc_header,
	'zmf2_doc_dimensions': add_zmf2_doc_dimensions,
	'zmf2_obj_header': add_zmf2_obj_header,
	'zmf4_bitmap': add_zmf4_bitmap,
	'zmf4_header': add_zmf4_header,
	'zmf4_obj': add_zmf4_obj,
	'zmf4_obj_doc_settings': add_zmf4_obj_doc_settings,
	'zmf4_obj_ellipse': add_zmf4_obj_ellipse,
	'zmf4_obj_polygon': add_zmf4_obj_polygon,
	'zmf4_obj_polyline': add_zmf4_obj_polyline,
	'zmf4_obj_rectangle': add_zmf4_obj_rectangle,
	'zmf4_obj_table': add_zmf4_obj_table,
	'zmf4_obj_text': add_zmf4_obj_text,
	'zmf4_obj_text_frame': add_zmf4_obj_text_frame,
}

def zmf2_open(page, data, parent, fname):
	file_map = {
		'BitmapDB.zmf': ZMF2Parser.parse_bitmap_db_doc,
		'TextStyles.zmf': ZMF2Parser.parse_text_styles_doc,
		'Callisto_doc.zmf': ZMF2Parser.parse_doc,
		'Callisto_pages.zmf': ZMF2Parser.parse_pages_doc,
	}
	if fname == 'Header':
		add_pgiter(page, 'Header', 'zmf', 'zmf2_header', data, parent)
	elif file_map.has_key(fname):
		if data != None:
			parser = ZMF2Parser(data, page, parent, file_map[fname])
			parser.parse()

def zmf4_open(data, page, parent):
	parser = ZMF4Parser(data, page, parent)
	parser.parse()

# vim: set ft=python sts=4 sw=4 noet:
