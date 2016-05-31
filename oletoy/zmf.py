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

from utils import add_iter, add_pgiter, rdata, key2txt

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

zmf2_objects = {
	0x3: 'Page',
	0x4: 'Layer',
	0x8: 'Rectangle',
	0x9: 'Image',
	0xa: 'Color',
	0xe: 'Polyline',
	0x10: 'Ellipse',
	0x11: 'Star',
	0x12: 'Polygon',
	0x13: 'Text frame',
	0x14: 'Table',
	0x100: 'Color palette',
	0x201: 'Bitmap definition',
}

# defined later
zmf2_handlers = {}

class ZMF2Parser(object):

	def __init__(self, data, page, parent, parser):
		self.data = data
		self.page = page
		self.parent = parent
		self.parser = parser

	def parse(self):
		if len(self.data) >= 4:
			length = int(read(self.data, 0, '<I'))
			if length <= len(self.data):
				self._parse_file(self.data[0:length], self.parent)

	def parse_bitmap_db_doc(self, data, parent):
		bitmaps_iter = add_pgiter(self.page, 'Bitmaps', 'zmf', 'zmf2_bitmap_db', data, parent)
		off = 4
		i = 1
		while off < len(data):
			off = self._parse_object(data, off, bitmaps_iter, 'Bitmap %d' % i)
			i += 1

	def parse_bitmap_def(self, data, parent):
		add_pgiter(self.page, 'ID', 'zmf', 'zmf2_bitmap_id', data, parent)
		return len(data)

	def parse_text_styles_doc(self, data, parent):
		pass

	def parse_doc(self, data, parent):
		off = self._parse_header(data, 0, parent)
		off = self._parse_object(data, off, parent, 'Default color?')
		off = self._parse_dimensions(data, off, parent)
		off += 4 # something
		off = self._parse_object(data, off, parent)
		off += 4 # something
		off = self._parse_object(data, off, parent, 'Color palette')
		off += 0x4c # something
		off = self._parse_object(data, off, parent, 'Page')

	def parse_pages_doc(self, data, parent):
		pass

	def parse_color_palette(self, data, parent):
		off = self._parse_object(data, 0, parent, 'Color')
		if off < len(data):
			(length, off) = rdata(data, off, '<I')
			add_pgiter(self.page, 'Palette name?', 'zmf', 'zmf2_name', data[off - 4:off + int(length)], parent)
		return off + int(length)

	def parse_color(self, data, parent):
		(length, off) = rdata(data, 0xd, '<I')
		name_str = 'Color'
		if length > 1:
			(name, off) = rdata(data, off, '%ds' % (int(length) - 1))
			name_str += ' (%s)' % unicode(name, 'cp1250')
		add_pgiter(self.page, name_str, 'zmf', 'zmf2_color', data, parent)
		return len(data)

	def parse_ellipse(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Bounding box', 'zmf', 'zmf2_bbox', data[off:off + 0x20], parent)
		return off + 0x20

	def parse_image(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Bounding box', 'zmf', 'zmf2_bbox', data[off:off + 0x20], parent)
		return off + 0x20

	def parse_layer(self, data, parent):
		off = self._parse_object(data, 0, parent, 'Drawable')
		(length, off) = rdata(data, off, '<I')
		add_pgiter(self.page, 'Layer name', 'zmf', 'zmf2_name', data[off - 4:off + int(length)], parent)
		return off + int(length)

	def parse_page(self, data, parent):
		return self._parse_object(data, 0, parent, 'Layer')

	def parse_polygon(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Dimensions', 'zmf', 'zmf2_polygon', data[off:], parent)
		return len(data)

	def parse_polyline(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Points', 'zmf', 'zmf2_points', data[off:], parent)
		return len(data)

	def parse_rectangle(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Bounding box', 'zmf', 'zmf2_bbox', data[off:off + 0x20], parent)
		return off + 0x20

	def parse_star(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Dimensions', 'zmf', 'zmf2_star', data[off:], parent)
		return len(data)

	def parse_table(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Bounding box', 'zmf', 'zmf2_bbox', data[off:off + 0x20], parent)
		off += 0x20
		add_pgiter(self.page, 'Def', 'zmf', 'zmf2_table', data[off:], parent)
		return off

	def parse_text_frame(self, data, parent):
		off = self._parse_object(data, 0, parent)
		off = self._parse_object(data, off, parent)
		off = self._parse_object(data, off, parent)
		add_pgiter(self.page, 'Bounding box', 'zmf', 'zmf2_bbox', data[off:off + 0x20], parent)
		off += 0x20
		(count, off) = rdata(data, off, '<I')

		chars = []
		chars_len = 0
		i = 0
		while i < int(count):
			(length, off) = rdata(data, off, '<I')
			i += 1
			chars.append(data[off - 4:off + int(length)])
			chars_len += 4 + int(length)
			off += int(length)

		charsiter = add_pgiter(self.page, 'Characters', 'zmf', 0, data[off:off + chars_len], parent)
		i = 0
		while i != len(chars):
			add_pgiter(self.page, 'Character %d' % (i + 1), 'zmf', 'zmf2_character', chars[i], charsiter)
			i += 1

		return off

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

	def _parse_object(self, data, offset, parent, name=None, handler=None):
		off = offset
		(size, off) = rdata(data, offset, '<I')

		name_str = name

		# TODO: this is highly speculative
		(typ, off) = rdata(data, off, '<I')
		(subtyp, off) = rdata(data, off, '<I')
		count = 0
		if typ == 4 and subtyp == 3:
			header_size = 0x18
			off += 4
			(obj, off) = rdata(data, off, '<I')
			if not handler and zmf2_handlers.has_key(int(obj)):
				handler = zmf2_handlers[int(obj)]
			if zmf2_objects.has_key(int(obj)):
				name_str = '%s object' % zmf2_objects[int(obj)]
		elif typ == 4 and subtyp == 4:
			header_size = 0x14
			off += 4
			(count, off) = rdata(data, off, '<I')
			name_str = name + 's'
		elif typ == 8 and subtyp == 5:
			header_size = 0x1c
			off += 8
			(count, off) = rdata(data, off, '<I')
		else:
			header_size = 0

		if not name_str:
			name_str = 'Unknown object'

		objiter = add_pgiter(self.page, name_str, 'zmf', 0, data[offset:offset + int(size)], parent)

		if header_size != 0:
			add_pgiter(self.page, 'Header', 'zmf', 'zmf2_obj_header', data[offset:offset + header_size], objiter)

		content_data = data[offset + header_size:offset + int(size)]
		if handler:
			content_offset = handler(self, content_data, objiter)
		elif int(count) > 0:
			content_offset = self._parse_object_list(content_data, objiter, int(count), name)
		else:
			content_offset = 0

		if content_offset < len(content_data):
			add_pgiter(self.page, 'Unknown content', 'zmf', 0, content_data[content_offset:], objiter)

		return offset + int(size)

	def _parse_object_list(self, data, parent, n, name='Object'):
		off = 0
		i = 0
		while i < n:
			off = self._parse_object(data, off, parent, '%s %d' % (name, (i + 1)))
			i += 1
		return off

	def _parse_dimensions(self, data, offset, parent):
		off = offset
		(size, off) = rdata(data, offset, '<I')
		add_pgiter(self.page, 'Dimensions', 'zmf', 'zmf2_doc_dimensions', data[offset:offset + int(size)], parent)
		return offset + int(size)

zmf2_handlers = {
	0x3: ZMF2Parser.parse_page,
	0x4: ZMF2Parser.parse_layer,
	0x8: ZMF2Parser.parse_rectangle,
	0x9: ZMF2Parser.parse_image,
	0xa: ZMF2Parser.parse_color,
	0xe: ZMF2Parser.parse_polyline,
	0x10: ZMF2Parser.parse_ellipse,
	0x11: ZMF2Parser.parse_star,
	0x12: ZMF2Parser.parse_polygon,
	0x13: ZMF2Parser.parse_text_frame,
	0x14: ZMF2Parser.parse_table,
	0x100: ZMF2Parser.parse_color_palette,
	0x201: ZMF2Parser.parse_bitmap_def,
}

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

def _add_zmf2_string(hd, size, data, offset, name):
	(length, off) = rdata(data, offset, '<I')
	add_iter(hd, 'String length', length, off - 4, 4, '<I')
	text_len = int(length) - 1
	if text_len > 1:
		(text, off) = rdata(data, off, '%ds' % text_len)
		add_iter(hd, name, unicode(text, 'cp1250'), off - text_len, text_len + 1, '%ds' % text_len)
	else:
		add_iter(hd, name, '', off, 1, '%ds' % text_len)
	return off + int(length)

def add_zmf2_bbox(hd, size, data):
	(tl_x, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Top left X', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top left Y', tl_y, off - 4, 4, '<I')
	(tr_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top right X', tr_x, off - 4, 4, '<I')
	(tr_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top right Y', tr_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right X', br_x, off - 4, 4, '<I')
	(br_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right Y', br_y, off - 4, 4, '<I')
	(bl_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom left X', bl_x, off - 4, 4, '<I')
	(bl_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom left Y', bl_y, off - 4, 4, '<I')

def add_zmf2_bitmap_db(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Number of bitmaps?', count, off - 4, 4, '<I')

def add_zmf2_bitmap_id(hd, size, data):
	(bid, off) = rdata(data, 0, '<I')
	add_iter(hd, 'ID', bid, off - 4, 4, '<I')

def add_zmf2_character(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Length', length, off - 4, 4, '<I')
	(c, off) = rdata(data, off, '1s')
	add_iter(hd, 'Character', unicode(c, 'cp1250'), off - 1, 1, '1s')

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
	off += 1
	(tl_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page top left X?', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Page top left Y?', tl_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')

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

def add_zmf2_color(hd, size, data):
	off = 0xd
	_add_zmf2_string(hd, size, data, off, 'Name')

def add_zmf2_name(hd, size, data):
	_add_zmf2_string(hd, size, data, 0, 'Name')

def add_zmf2_points(hd, size, data):
	(count, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Number of points', count, off - 4, 4, '<I')
	i = 0
	while i < int(count):
		(x, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d X' % (i + 1), x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d Y' % (i + 1), y, off - 4, 4, '<I')
		off += 8
		i += 1

def add_zmf2_polygon(hd, size, data):
	(tl_x, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Top left X?', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top left Y?', tl_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right X?', br_x, off - 4, 4, '<I')
	(br_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right Y?', br_y, off - 4, 4, '<I')
	(points, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of edges', points, off - 4, 4, '<I')

def add_zmf2_star(hd, size, data):
	(tl_x, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Top left X?', tl_x, off - 4, 4, '<I')
	(tl_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Top left Y?', tl_y, off - 4, 4, '<I')
	(br_x, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right X?', br_x, off - 4, 4, '<I')
	(br_y, off) = rdata(data, off, '<I')
	add_iter(hd, 'Bottom right Y?', br_y, off - 4, 4, '<I')
	(points, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of points', points, off - 4, 4, '<I')
	(angle, off) = rdata(data, off, '<I')
	add_iter(hd, 'Point angle?', angle, off - 4, 4, '<I')

def add_zmf2_table(hd, size, data):
	off = 4
	(rows, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of rows', rows, off - 4, 4, '<I')
	(cols, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of columns', cols, off - 4, 4, '<I')

	off += 8

	for i in range(int(cols)):
		(width, off) = rdata(data, off, '<I')
		add_iter(hd, 'Width of column %d' % (i + 1), width, off - 4, 4, '<I')
		off += 4

	for i in range(int(rows)):
		(height, off) = rdata(data, off, '<I')
		add_iter(hd, 'Height of row %d' % (i + 1), height, off - 4, 4, '<I')
		off += 0x2c
		for j in range(int(cols)):
			(length, off) = rdata(data, off, '<I')
			add_iter(hd, 'String length', length, off - 4, 4, '<I')
			fix = 0
			if int(length) > 0:
				(text, off) = rdata(data, off, '%ds' % int(length))
				add_iter(hd, 'Content', text, off - int(length), int(length), '%ds' % int(length))
				off += 0x29
				fix = 0x29
		off -= fix
		off += 5

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
	(begin, off) = rdata(data, off, '<f')
	add_iter(hd, 'Beginning (rad)', begin, off - 4, 4, '<f')
	(end, off) = rdata(data, off, '<f')
	add_iter(hd, 'Ending (rad)', end, off - 4, 4, '<f')
	(arc, off) = rdata(data, off, '<I')
	add_iter(hd, 'Arc (== not closed)', bool(arc), off - 4, 4, '<I')

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
	if width == height:
		add_iter(hd, 'Radius', width / 2, off - 4, 4, '<I')
	i = 1
	while i <= count:
		(x, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d X' % i, x, off - 4, 4, '<I')
		(y, off) = rdata(data, off, '<I')
		add_iter(hd, 'Point %d Y' % i, y, off - 4, 4, '<I')
		i += 1
	(peaks, off) = rdata(data, off, '<I')
	add_iter(hd, 'Number of peaks', peaks, off - 4, 4, '<I')
	(type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Polygon type?', type, off - 4, 4, '<I')
	sharpness_offsets = {
		3: (0x60, ),
		4: (0x60, 0x68),
		7: (0x58, 0x88),
	}
	if type in sharpness_offsets:
		for sharpness_offset in sharpness_offsets[type]:
			(sharpness, sharpness_offset) = rdata(data, sharpness_offset, '<f')
			add_iter(hd, 'Sharpness?', sharpness, sharpness_offset - 4, 4, '<f')

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
	rectangle_corner_types = {
		1: 'Normal',
		2: 'Round',
		3: 'Round In',
		4: 'Cut'
	}
	(corner_type, off) = rdata(data, off, '<I')
	add_iter(hd, 'Corner type', key2txt(corner_type, rectangle_corner_types), off - 4, 4, '<I')
	(rounding_value, off) = rdata(data, off, '<f')
	add_iter(hd, 'Rounding value (in.)', rounding_value, off - 4, 4, '<f')

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
	'zmf2_bbox': add_zmf2_bbox,
	'zmf2_bitmap_db': add_zmf2_bitmap_db,
	'zmf2_bitmap_id': add_zmf2_bitmap_id,
	'zmf2_block': add_zmf2_block,
	'zmf2_character': add_zmf2_character,
	'zmf2_color': add_zmf2_color,
	'zmf2_compressed_block': add_zmf2_compressed_block,
	'zmf2_doc_header': add_zmf2_doc_header,
	'zmf2_doc_dimensions': add_zmf2_doc_dimensions,
	'zmf2_name': add_zmf2_name,
	'zmf2_points': add_zmf2_points,
	'zmf2_polygon': add_zmf2_polygon,
	'zmf2_star': add_zmf2_star,
	'zmf2_table': add_zmf2_table,
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
