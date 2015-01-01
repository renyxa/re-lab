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

# reverse-engineered specification: http://doc.the-ebook.org/LrfFormat
# (2013)

import struct
import zlib

import otxml
from utils import add_iter, add_pgiter, rdata

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

def read_unistr(data, off, bytelen):
	text = u''
	end = off + bytelen
	while off < end:
		(c, off) = rdata(data, off, '<H')
		text += unichr(c)
	return text

lrf_object_types = {
	0x1: 'Page Tree',
	0x2: 'Page',
	0x3: 'Header',
	0x4: 'Footer',
	0x5: 'Page Atr',
	0x6: 'Block',
	0x7: 'Block Atr',
	0x8: 'Mini Page',
	0x9: 'Block List',
	0xa: 'Text',
	0xb: 'Text Atr',
	0xc: 'Image',
	0xd: 'Canvas',
	0xe: 'Paragraph Atr',
	0x11: 'Image Stream',
	0x12: 'Import',
	0x13: 'Button',
	0x14: 'Window',
	0x15: 'Pop Up Win',
	0x16: 'Sound',
	0x17: 'Plane Stream',
	0x19: 'Font',
	0x1a: 'Object Info',
	0x1c: 'Book Atr',
	0x1d: 'Simple Text',
	0x1e: 'Toc',
}

lrf_thumbnail_types = {
	0x11: "JPEG",
	0x12: "PNG",
	0x13: "BMP",
	0x14: "GIF",
}

# defined later
lrf_tags = {}

def read(data, offset, fmt):
	return rdata(data, offset, fmt)[0]

class lrf_parser(object):

	class stream_state:

		def __init__(self):
			self.stream_flags = 0
			self.stream_size = 0
			self.stream_started = False
			self.stream_read = False

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.pseudo_encryption_key = 0
		self.version = 0
		self.header_size = 0
		self.root_oid = 0
		self.object_count = 0
		self.object_index_offset = 0
		self.toc_oid = None
		self.toc_offset = 0
		self.metadata_size = 0
		self.thumbnail_type = None
		self.thumbnail_size = 0

		self.stream_level = 1
		self.stream_states = []
		self.object_type = None

	def open_stream_level(self):
		if (self.stream_level > len(self.stream_states)):
			self.stream_states.append(self.stream_state())
		assert(self.stream_level == len(self.stream_states))

	def close_stream_level(self):
		self.stream_states.pop(-1)
		assert(len(self.stream_states) >= 0)
		assert(self.stream_level > 0)

	def is_in_stream(self):
		if len(self.stream_states) == self.stream_level:
			return self.stream_states[-1].stream_started and not self.stream_states[-1].stream_read
		return False

	def read_header(self):
		data = self.data

		self.version = read(data, 8, '<H')
		self.pseudo_encryption_key = read(data, 0xa, '<H')
		self.object_count = read(data, 0x10, '<Q')
		self.object_index_offset = read(data, 0x18, '<Q')
		(self.toc_oid, off) = rdata(data, 0x44, '<I')
		(self.toc_offset, off) = rdata(data, off, '<I')
		(self.metadata_size, off) = rdata(data, off, '<H')
		if (self.version > 800):
			(self.thumbnail_type, off) = rdata(data, off, '<H')
			(self.thumbnail_size, off) = rdata(data, off, '<I')

		self.header_size = off

		add_pgiter(self.page, 'Header', 'lrf', 'header', data[0:off], self.parent)

	def read_toc(self):
		data = self.data
		off = self.toc_offset
		(oid, off) = rdata(data, off, '<I')
		assert(oid == self.toc_oid)
		(start, off) = rdata(data, off, '<I')
		(length, off) = rdata(data, off, '<I')
		end = start + length
		add_pgiter(self.page, 'TOC', 'lrf', 0, data[start:end], self.parent)

	def read_metadata(self):
		start = self.header_size
		end = start + self.metadata_size
		metadata = self.data[start:end]
		metaiter = add_pgiter(self.page, 'Metadata', 'lrf', 'compressed_stream', metadata, self.parent)
		(uncompressed_size, off) = rdata(metadata, 0, '<I')
		try:
			content = zlib.decompress(metadata[off:])
			assert len(content) == uncompressed_size
			otxml.open(content, self.page, metaiter)
		except zlib.error:
			pass

	def read_thumbnail(self):
		start = self.header_size + self.metadata_size
		end = start + self.thumbnail_size
		typ = "Unknown"
		if lrf_thumbnail_types.has_key(self.thumbnail_type):
			typ = lrf_thumbnail_types[self.thumbnail_type]
		add_pgiter(self.page, 'Thumbnail (%s)' % typ, 'lrf', 0, self.data[start:end], self.parent)

	def decrypt_stream(self, data):
		declen = len(data)
		keybyte = ((declen % self.pseudo_encryption_key) + 0x0f) & 0xff
		if self.object_type == 0x11 or self.object_type == 0x17 or self.object_type == 0x19:
			if declen > 0x400:
				declen = 0x400
		decdata = map(lambda c : chr((ord(c) ^ keybyte) & 0xff), data[0:declen])
		decdata.append(data[declen:len(data)])
		return ''.join(decdata)

	def read_stream(self, data, parent):
		callback = 0
		if self.stream_states[-1].stream_flags == 0x100:
			callback = 'compressed_stream'
		strmiter = add_pgiter(self.page, 'Stream', 'lrf', callback, data, parent)
		# data = self.decrypt_stream(self.data[start:start + length])
		# add_pgiter(self.page, '[Unobfuscated]', 'lrf', 0, data, strmiter)

		content = data
		content_name = 'Content'
		# TODO: This is speculative. I think that actually the lower
		# byte contains type (e.g., image types, ToC, tags) and only the
		# higher byte is flags (or flag). It seems that 0x1 means
		# 'compressed'.
		if self.stream_states[-1].stream_flags == 0x100:
			(uncompressed_size, off) = rdata(data, 0, '<I')
			try:
				content = zlib.decompress(data[off:])
				content_name = 'Uncompressed content'
				assert len(content) == uncompressed_size
			except zlib.error:
				pass
		cntiter = add_pgiter(self.page, content_name, 'lrf', 0, content, strmiter)
		self.stream_level += 1
		# There are streams that do not contain tags. Maybe only text
		# streams contain tags.
		if len(content) > 1 and ord(content[1]) == 0xf5:
			self.read_object_tags(content, cntiter)
		self.stream_level -= 1
		self.stream_states[-1].stream_read = True

	def read_object_tag(self, n, data, start, parent):
		end = len(data)
		if self.is_in_stream():
			stream_end = start + self.stream_states[-1].stream_size
			self.read_stream(data[start:stream_end], parent)
			return stream_end

		callback = 'tag'
		(tag, off) = rdata(data, start, '<H')
		name = 'Tag 0x%x' % tag
		length = None
		if ((tag & 0xff00) >> 8) == 0xf5:
			if lrf_tags.has_key(tag):
				(name, length, f) = lrf_tags[tag]

		# try to find the next tag
		if length is None:
			pos = off
			while data[pos] != chr(0xf5) and pos < end:
				pos += 1
			if pos < end:
				pos -= 1
			elif pos <= off:
				return end
			else: # not found
				return end
			length = pos - off

		if tag == 0xf504:
			self.open_stream_level()
			self.stream_states[-1].stream_size = read(data, off, '<I')
		elif tag == 0xf505:
			self.open_stream_level()
			self.stream_states[-1].stream_started = True
		elif tag == 0xf554:
			self.open_stream_level()
			self.stream_states[-1].stream_flags = read(data, off, '<H')
		elif tag == 0xf506:
			self.close_stream_level()

		if off + length <= end:
			add_pgiter(self.page, '%s (%d)' % (name, n), 'lrf', callback, data[start:off + length], parent)
		else:
			return end

		return off + length

	def read_object_tags(self, data, parent):
		n = 0
		pos = self.read_object_tag(n, data, 0, parent)
		while pos < len(data):
			n += 1
			pos = self.read_object_tag(n, data, pos, parent)

	def read_object(self, idxoff, parent):
		data = self.data
		(oid, off) = rdata(data, idxoff, '<I')
		(start, off) = rdata(data, off, '<I')
		(length, off) = rdata(data, off, '<I')
		otp = read(data, start + 6, '<H')

		otype = otp
		if lrf_object_types.has_key(otp):
			otype = lrf_object_types[otp]

		objiter = add_pgiter(self.page, 'Object 0x%x (%s)' % (oid, otype), 'lrf', 0, data[start:start + length], parent)
		self.object_type = otype
		self.read_object_tags(data[start:start + length], objiter)
		self.object_type = None

	def read_objects(self):
		data = self.data

		idxstart = self.object_index_offset
		idxend = idxstart + self.object_count * 16

		objstart = read(data, idxstart + 4, '<I')
		last_obj = idxend - 16
		(last_obj_offset, offset) = rdata(data, last_obj + 4, '<I')
		last_obj_len = read(data, offset, '<I')
		objend = last_obj_offset + last_obj_len

		objiter = add_pgiter(self.page, 'Objects', 'lrf', 0, data[objstart:objend], self.parent)
		idxiter = add_pgiter(self.page, 'Object index', 'lrf', 0, data[idxstart:idxend], self.parent)
		for i in range(self.object_count):
			off = idxstart + 16 * i
			oid = read(data, off, '<I')
			add_pgiter(self.page, 'Entry 0x%x' % (oid), 'lrf', 'idxentry', data[off:off + 16], idxiter)
			self.read_object(off, objiter)

	def read(self):
		parent = self.parent
		self.parent = add_pgiter(self.page, 'File', 'lrf', 0, self.data, parent)
		self.read_header()
		self.read_metadata()
		if (self.version > 800):
			self.read_thumbnail()
		# self.read_toc()
		self.read_objects()

def chop_tag_f500(hd, size, data):
	(oid, off) = rdata(data, 2, '<I')
	add_iter(hd, 'Object ID', '0x%x' % oid, off - 4, 4, '<I')
	(typ, off) = rdata(data, off, '<H')
	add_iter(hd, 'Type', get_or_default(lrf_object_types, typ, 'Unknown'), off - 2, 2, '<H')

def chop_tag_f502(hd, size, data):
	pass

def chop_tag_f503(hd, size, data):
	(oid, off) = rdata(data, 2, '<I')
	add_iter(hd, 'Target ID', '0x%x' % oid, off - 4, 4, '<I')

def chop_tag_f504(hd, size, data):
	(sz, off) = rdata(data, 2, '<I')
	add_iter(hd, 'Size', sz, off - 4, 4, '<I')

def chop_tag_f507(hd, size, data):
	pass

def chop_tag_f508(hd, size, data):
	pass

def chop_tag_f509(hd, size, data):
	pass

def chop_tag_f50a(hd, size, data):
	pass

def chop_tag_f50b(hd, size, data):
	pass

def chop_tag_f50d(hd, size, data):
	pass

def chop_tag_f50e(hd, size, data):
	pass

def chop_tag_f511(hd, size, data):
	(sz, off) = rdata(data, 2, '<H')
	# TODO: interpret the size
	add_iter(hd, 'Size', sz, 2, off - 2, '<H')

def chop_tag_f512(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	# TODO: interpret the width
	add_iter(hd, 'Width', width, 2, off - 2, '<H')

def chop_tag_f513(hd, size, data):
	(escapement, off) = rdata(data, 2, '<H')
	# TODO: interpret the escapement
	add_iter(hd, 'Escapement', escapement, 2, off - 2, '<H')

def chop_tag_f514(hd, size, data):
	(orient, off) = rdata(data, 2, '<H')
	# TODO: interpret the orientation
	add_iter(hd, 'Orientation', orient, 2, off - 2, '<H')

def chop_tag_f515(hd, size, data):
	(weight, off) = rdata(data, 2, '<H')
	# TODO: interpret the weight
	add_iter(hd, 'Weight', weight, 2, off - 2, '<H')

def chop_tag_f516(hd, size, data):
	(length, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Length', length, 2, off - 2, '<H')
	name = read_unistr(data, off, length)
	add_iter(hd, 'Name', name, off, length, 's')

def chop_tag_f517(hd, size, data):
	pass

def chop_tag_f518(hd, size, data):
	pass

def chop_tag_f519(hd, size, data):
	(space, off) = rdata(data, 2, '<H')
	# TODO: interpret the space
	add_iter(hd, 'Space', space, 2, off - 2, '<H')

def chop_tag_f51a(hd, size, data):
	(space, off) = rdata(data, 2, '<H')
	# TODO: interpret the space
	add_iter(hd, 'Space', space, 2, off - 2, '<H')

def chop_tag_f51b(hd, size, data):
	(skip, off) = rdata(data, 2, '<H')
	# TODO: interpret the skip
	add_iter(hd, 'Skip', skip, 2, off - 2, '<H')

def chop_tag_f51c(hd, size, data):
	(space, off) = rdata(data, 2, '<H')
	# TODO: interpret the space
	add_iter(hd, 'Space', space, 2, off - 2, '<H')

def chop_tag_f51d(hd, size, data):
	(indent, off) = rdata(data, 2, '<H')
	# TODO: interpret the indent
	add_iter(hd, 'Indent', indent, 2, off - 2, '<H')

def chop_tag_f51e(hd, size, data):
	(skip, off) = rdata(data, 2, '<H')
	# TODO: interpret the skip
	add_iter(hd, 'Skip', skip, 2, off - 2, '<H')

def chop_tag_f521(hd, size, data):
	pass

def chop_tag_f522(hd, size, data):
	(height, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Height', height, off - 2, 2, '<H')

def chop_tag_f523(hd, size, data):
	pass

def chop_tag_f524(hd, size, data):
	pass

def chop_tag_f525(hd, size, data):
	(height, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Height', height, off - 2, 2, '<H')

def chop_tag_f526(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

def chop_tag_f527(hd, size, data):
	pass

def chop_tag_f528(hd, size, data):
	(height, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Height', height, off - 2, 2, '<H')

def chop_tag_f529(hd, size, data):
	(mode, off) = rdata(data, 2, '<H')
	# TODO: interpret mode
	add_iter(hd, 'Mode', '0x%x' % mode, off - 2, 2, '<H')
	(iid, off) = rdata(data, 4, '<I')
	add_iter(hd, 'Image ID', iid, off - 4, 4, '>I')

def chop_tag_f52a(hd, size, data):
	(empty, off) = rdata(data, 2, '<H')
	empty_map = {0: 'empty', 1: 'show'}
	empty_str = get_or_default(empty_map, int(empty), 'unknown')
	add_iter(hd, 'Empty', empty_str, off - 2, 2, '<H')

def chop_tag_f52b(hd, size, data):
	(pos, off) = rdata(data, 2, '<H')
	pos_map = {0: 'any', 1: 'upper', 2: 'lower'}
	pos_str = get_or_default(pos_map, int(pos), 'unknown')
	add_iter(hd, 'Position', pos_str, off - 2, 2, '<H')

def chop_tag_f52c(hd, size, data):
	pass

def chop_tag_f52d(hd, size, data):
	pass

def chop_tag_f52e(hd, size, data):
	(mode, off) = rdata(data, 2, '<H')
	mode_map = {0: 'none', 1: 'square', 2: 'curve'}
	mode_str = get_or_default(mode_map, int(mode), 'unknown')
	add_iter(hd, 'Mode', mode_str, off - 2, 2, '<H')

def chop_tag_f531(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

def chop_tag_f532(hd, size, data):
	(height, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Height', height, off - 2, 2, '<H')

def chop_tag_f533(hd, size, data):
	(rule, off) = rdata(data, 2, '<H')
	rule_map = {0x12: 'horizontal adjustable', 0x14: 'horizontal fixed',
			0x21: 'vertical adjustable', 0x22: 'block adjustable',
			0x41: 'vertical fixed', 0x44: 'block fixed'}
	rule_str = get_or_default(rule_map, int(rule), 'unknown')
	add_iter(hd, 'Rule', rule_str, off - 2, 2, '<H')

def chop_tag_f534(hd, size, data):
	pass

def chop_tag_f535(hd, size, data):
	(layout, off) = rdata(data, 2, '<H')
	layout_map = {0x41: 'top-to-bottom right-to-left', 0x34: 'left-to-right top-to-bottom'}
	layout_str = get_or_default(layout_map, int(layout), 'unknown')
	add_iter(hd, 'Layout', layout_str, off - 2, 2, '<H')

def chop_tag_f536(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

def chop_tag_f537(hd, size, data):
	pass

def chop_tag_f538(hd, size, data):
	pass

def chop_tag_f539(hd, size, data):
	pass

def chop_tag_f53a(hd, size, data):
	pass

def chop_tag_f53c(hd, size, data):
	(align, off) = rdata(data, 2, '<H')
	align_map = {1: 'start', 4: 'center', 8: 'end'}
	align_str = get_or_default(align_map, int(align), 'unknown')
	add_iter(hd, 'Align', align_str, off - 2, 2, '<H')

def chop_tag_f53d(hd, size, data):
	pass

def chop_tag_f53e(hd, size, data):
	pass

def chop_tag_f541(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

def chop_tag_f542(hd, size, data):
	(height, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Height', height, off - 2, 2, '<H')

def chop_tag_f544(hd, size, data):
	pass

def chop_tag_f545(hd, size, data):
	pass

def chop_tag_f546(hd, size, data):
	pass

def chop_tag_f547(hd, size, data):
	pass

def chop_tag_f548(hd, size, data):
	(pos, off) = rdata(data, 2, '<H')
	pos_map = {1: 'bottom left', 2: 'bottom right', 3: 'top right', 4: 'top left', 5: 'base'}
	pos_str = get_or_default(pos_map, int(pos), 'unknown')
	add_iter(hd, 'Position', pos_str, off - 2, 2, '<H')

def chop_tag_f549(hd, size, data):
	off = 6
	(oid, off) = rdata(data, off, '<I')
	add_iter(hd, 'Object ID', '0x%x' % oid, off - 4, 4, '<I')

def chop_tag_f54a(hd, size, data):
	pass

def chop_tag_f54b(hd, size, data):
	pass

def chop_tag_f54c(hd, size, data):
	pass

def chop_tag_f54e(hd, size, data):
	pass

def chop_tag_f551(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Width', width, off - 2, 2, '<H')

def chop_tag_f552(hd, size, data):
	(height, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Height', height, off - 2, 2, '<H')

def chop_tag_f553(hd, size, data):
	pass

def chop_tag_f554(hd, size, data):
	(flags, off) = rdata(data, 2, '<H')
	# TODO: interpret the flags
	add_iter(hd, 'Flags', '0x%x' % flags, off - 2, 2, '<H')

def chop_tag_f555(hd, size, data):
	pass

def chop_tag_f556(hd, size, data):
	pass

def chop_tag_f557(hd, size, data):
	pass

def chop_tag_f558(hd, size, data):
	pass

def chop_tag_f559(hd, size, data):
	pass

def chop_tag_f55a(hd, size, data):
	pass

def chop_tag_f55b(hd, size, data):
	pass

def chop_tag_f55c(hd, size, data):
	(count, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Page count', count, off - 2, 2, '<H')
	i = 0
	while i != int(count):
		(pid, off) = rdata(data, off, '<I')
		add_iter(hd, 'Page %d' % i, '0x%x' % pid, off - 4, 4, '<I')
		i += 1

def chop_tag_f55d(hd, size, data):
	pass

def chop_tag_f55e(hd, size, data):
	pass

def chop_tag_f561(hd, size, data):
	pass

def chop_tag_f56c(hd, size, data):
	pass

def chop_tag_f56d(hd, size, data):
	pass

def chop_tag_f575(hd, size, data):
	(align, off) = rdata(data, 2, '<H')
	# TODO: interpret the align
	add_iter(hd, 'Align', '0x%x' % align, off - 2, 2, '<H')

def chop_tag_f576(hd, size, data):
	(overhang, off) = rdata(data, 2, '<H')
	overhang_map = {0: 'none', 1: 'auto'}
	overhang_str = get_or_default(overhang_map, int(overhang), 'unknown')
	add_iter(hd, 'Overhang', overhang_str, off - 2, 2, '<H')

def chop_tag_f577(hd, size, data):
	(pos, off) = rdata(data, 2, '<H')
	pos_map = {1: 'before', 2: 'after'}
	pos_str = get_or_default(pos_map, int(pos), 'unknown')
	add_iter(hd, 'Position', pos_str, off - 2, 2, '<H')

def chop_tag_f578(hd, size, data):
	(code, off) = rdata(data, 2, '<I')
	# TODO: interpret the code
	add_iter(hd, 'Code', '0x%x' % code, off - 4, 4, '<I')

def chop_tag_f579(hd, size, data):
	(pos, off) = rdata(data, 2, '<H')
	pos_map = {1: 'before', 2: 'after'}
	pos_str = get_or_default(pos_map, int(pos), 'unknown')
	add_iter(hd, 'Position', pos_str, off - 2, 2, '<H')

def chop_tag_f57a(hd, size, data):
	(mode, off) = rdata(data, 2, '<H')
	mode_map = {0x0: 'none', 0x10: 'solid', 0x20: 'dashed', 0x30: 'double', 0x40: 'dotted'}
	mode_str = get_or_default(mode_map, int(mode), 'unknown')
	add_iter(hd, 'Mode', mode_str, off - 2, 2, '<H')

def chop_tag_f57b(hd, size, data):
	(tid, off) = rdata(data, 2, '<I')
	add_iter(hd, 'Page tree', '0x%x' % tid, off - 4, 4, '<I')

def chop_tag_f57c(hd, size, data):
	(oid, off) = rdata(data, 2, '<I')
	add_iter(hd, 'ID', '0x%x' % oid, off - 4, 4, '<I')

def chop_tag_f5a1(hd, size, data):
	pass

def chop_tag_f5a5(hd, size, data):
	pass

def chop_tag_f5a7(hd, size, data):
	pass

def chop_tag_f5c3(hd, size, data):
	pass

def chop_tag_f5c5(hd, size, data):
	pass

def chop_tag_f5c6(hd, size, data):
	pass

def chop_tag_f5c8(hd, size, data):
	pass

def chop_tag_f5ca(hd, size, data):
	pass

def chop_tag_f5cb(hd, size, data):
	pass

def chop_tag_f5cc(hd, size, data):
	(length, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Length', length, 2, off - 2, '<H')
	text = read_unistr(data, off, length)
	add_iter(hd, 'Text', text, off, length, 's')

def chop_tag_f5d1(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Width', width, 2, off - 2, '<H')
	(height, off) = rdata(data, off, '<H')
	add_iter(hd, 'height', height, 2, off - 2, '<H')
	(oid, off) = rdata(data, off, '<I')
	add_iter(hd, 'Object ID', '0x%x' % oid, off - 4, 4, '<I')
	(adjustment, off) = rdata(data, off, '<H')
	adjustment_map = {1: 'top', 2: 'center', 3: 'baseline', 4: 'bottom'}
	adjustment_str = get_or_default(adjustment_map, int(adjustment), 'unknown')
	add_iter(hd, 'Adjustment', adjustment_str, off - 2, 2, '<H')

def chop_tag_f5d4(hd, size, data):
	(time, off) = rdata(data, 2, '<H')
	add_iter(hd, 'Time', time, off - 2, 2, '<H')

def chop_tag_f5d7(hd, size, data):
	pass

def chop_tag_f5d8(hd, size, data):
	pass

def chop_tag_f5d9(hd, size, data):
	pass

def chop_tag_f5da(hd, size, data):
	(replay, off) = rdata(data, 2, '<H')
	replay_map = {1: 'replay', 2: 'noreplay'}
	replay_str = get_or_default(replay_map, int(replay), 'unknown')
	add_iter(hd, 'Replay', replay_str, off - 2, 2, '<H')

def chop_tag_f5db(hd, size, data):
	pass

def chop_tag_f5dc(hd, size, data):
	pass

def chop_tag_f5dd(hd, size, data):
	(space, off) = rdata(data, 2, '<H')
	# TODO: interpret the space
	add_iter(hd, 'Space', space, 2, off - 2, '<H')

def chop_tag_f5f1(hd, size, data):
	(width, off) = rdata(data, 2, '<H')
	# TODO: interpret the width
	add_iter(hd, 'Width', width, 2, off - 2, '<H')

def chop_tag_f5f2(hd, size, data):
	pass

def chop_tag_f5f3(hd, size, data):
	pass

def chop_tag_f5f4(hd, size, data):
	pass

def chop_tag_f5f5(hd, size, data):
	pass

def chop_tag_f5f6(hd, size, data):
	pass

def chop_tag_f5f7(hd, size, data):
	pass

def chop_tag_f5f8(hd, size, data):
	pass

def chop_tag_f5f9(hd, size, data):
	pass

# variable length
V = None

lrf_tags = {
	0xf500 : ('Object Start', 6, chop_tag_f500),
	0xf501 : ('Object End', 0, None),
	0xf502 : ('Object Info Link', 4, chop_tag_f502),
	0xf503 : ('Link', 4, chop_tag_f503),
	0xf504 : ('Stream Size', 4, chop_tag_f504),
	0xf505 : ('Stream Start', 0, None),
	0xf506 : ('Stream End', 0, None),
	0xf507 : ('Odd Header ID', 4, chop_tag_f507),
	0xf508 : ('Even Header ID', 4, chop_tag_f508),
	0xf509 : ('Odd Footer ID', 4, chop_tag_f509),
	0xf50a : ('Even Footer ID', 4, chop_tag_f50a),
	0xf50b : ('Contained Objects List', 4, chop_tag_f50b),
	0xf50d : ('F50D', V, chop_tag_f50d),
	0xf50e : ('F50E', 2, chop_tag_f50e),
	0xf511 : ('Font Size', 2, chop_tag_f511),
	0xf512 : ('Font Width', 2, chop_tag_f512),
	0xf513 : ('Font Escapement', 2, chop_tag_f513),
	0xf514 : ('Font Orientation', 2, chop_tag_f514),
	0xf515 : ('Font Weight', 2, chop_tag_f515),
	0xf516 : ('Font Facename', V, chop_tag_f516),
	0xf517 : ('Text Color', 4, chop_tag_f517),
	0xf518 : ('Text Bg Color', 4, chop_tag_f518),
	0xf519 : ('Word Space', 2, chop_tag_f519),
	0xf51a : ('Letter Space', 2, chop_tag_f51a),
	0xf51b : ('Base Line Skip', 2, chop_tag_f51b),
	0xf51c : ('Line Space', 2, chop_tag_f51c),
	0xf51d : ('Par Indent', 2, chop_tag_f51d),
	0xf51e : ('Par Skip', 2, chop_tag_f51e),
	0xf521 : ('Top Margin', 2, chop_tag_f521),
	0xf522 : ('Header Height', 2, chop_tag_f522),
	0xf523 : ('Header Space', 2, chop_tag_f523),
	0xf524 : ('Odd Side Margin', 2, chop_tag_f524),
	0xf525 : ('Page Height', 2, chop_tag_f525),
	0xf526 : ('Page Width', 2, chop_tag_f526),
	0xf527 : ('Footer Space', 2, chop_tag_f527),
	0xf528 : ('Footer Height', 2, chop_tag_f528),
	0xf529 : ('Background Image', 6, chop_tag_f529),
	0xf52a : ('Set Empty View', 2, chop_tag_f52a),
	0xf52b : ('Page Position', 2, chop_tag_f52b),
	0xf52c : ('Even Side Margin', 2, chop_tag_f52c),
	0xf52d : ('F52D', 4, chop_tag_f52d),
	0xf52e : ('Frame Mode', 2, chop_tag_f52e),
	0xf531 : ('Block Width', 2, chop_tag_f531),
	0xf532 : ('Block Height', 2, chop_tag_f532),
	0xf533 : ('Block Rule', 2, chop_tag_f533),
	0xf534 : ('Background Color', 4, chop_tag_f534),
	0xf535 : ('Layout', 2, chop_tag_f535),
	0xf536 : ('Frame Width', 2, chop_tag_f536),
	0xf537 : ('Frame Color', 4, chop_tag_f537),
	0xf538 : ('Top Skip', 2, chop_tag_f538),
	0xf539 : ('Side Margin', 2, chop_tag_f539),
	0xf53a : ('Bottom Skip', 2, chop_tag_f53a),
	0xf53c : ('Align', 2, chop_tag_f53c),
	0xf53d : ('Column', 2, chop_tag_f53d),
	0xf53e : ('Column Sep', 2, chop_tag_f53e),
	0xf541 : ('Mini Page Height', 2, chop_tag_f541),
	0xf542 : ('Mini Page Width', 2, chop_tag_f542),
	0xf544 : ('F544', 4, chop_tag_f544),
	0xf545 : ('F545', 4, chop_tag_f545),
	0xf546 : ('Location Y', 2, chop_tag_f546),
	0xf547 : ('Location X', 2, chop_tag_f547),
	0xf548 : ('Content Position', 2, chop_tag_f548),
	0xf549 : ('Put Object', 8, chop_tag_f549),
	0xf54a : ('Image Rect', 8, chop_tag_f54a),
	0xf54b : ('Image Size', 4, chop_tag_f54b),
	0xf54c : ('Image Stream', 4, chop_tag_f54c),
	0xf54d : ('F54D', 0, None),
	0xf54e : ('Page Div', 12, chop_tag_f54e),
	0xf551 : ('Canvas Width', 2, chop_tag_f551),
	0xf552 : ('Canvas Height', 2, chop_tag_f552),
	0xf553 : ('F553', 4, chop_tag_f553),
	0xf554 : ('Stream Flags', 2, chop_tag_f554),
	0xf555 : ('Comment', V, chop_tag_f555),
	0xf556 : ('F556', V, chop_tag_f556),
	0xf557 : ('F557', 2, chop_tag_f557),
	0xf558 : ('F558', 2, chop_tag_f558),
	0xf559 : ('Font File Name', V, chop_tag_f559),
	0xf55a : ('F55A', V, chop_tag_f55a),
	0xf55b : ('View Point', 4, chop_tag_f55b),
	0xf55c : ('Page List', V, chop_tag_f55c),
	0xf55d : ('Font Face Name', V, chop_tag_f55d),
	0xf55e : ('F55E', 2, chop_tag_f55e),
	0xf561 : ('Button Flags', 2, chop_tag_f561),
	0xf562 : ('Begin Base Button', 0, None),
	0xf563 : ('End Base Button', 0, None),
	0xf564 : ('Begin Focus In Button', 0, None),
	0xf565 : ('End Focus In Button', 0, None),
	0xf566 : ('Begin Push Button', 0, None),
	0xf567 : ('End Push Button', 0, None),
	0xf568 : ('Begin Up Button', 0, None),
	0xf569 : ('End Up Button', 0, None),
	0xf56a : ('Begin Button Actions', 0, None),
	0xf56b : ('End Button Actions', 0, None),
	0xf56c : ('Jump To', 8, chop_tag_f56c),
	0xf56d : ('Send Message', V, chop_tag_f56d),
	0xf56e : ('Close Window', 0, None),
	0xf571 : ('F571', 0, None),
	0xf572 : ('F572', 0, None),
	0xf573 : ('Ruled Line', 10, None),
	0xf575 : ('Ruby Align', 2, chop_tag_f575),
	0xf576 : ('Ruby Overhang', 2, chop_tag_f576),
	0xf577 : ('Empty Dots Position', 2, chop_tag_f577),
	0xf578 : ('Empty Dots Code', V, chop_tag_f578),
	0xf579 : ('Empty Line Position', 2, chop_tag_f579),
	0xf57a : ('Empty Line Mode', 2, chop_tag_f57a),
	0xf57b : ('Child Page Tree', 4, chop_tag_f57b),
	0xf57c : ('Parent Page Tree', 4, chop_tag_f57c),
	0xf581 : ('Begin Italic', 0, None),
	0xf582 : ('End Italic', 0, None),
	0xf5a1 : ('Begin P', 4, chop_tag_f5a1),
	0xf5a2 : ('End P', 0, None),
	0xf5a5 : ('Koma Gaiji', V, chop_tag_f5a5),
	0xf5a6 : ('Koma Emp Dot Char', 0, None),
	0xf5a7 : ('Begin Button', 4, chop_tag_f5a7),
	0xf5a8 : ('End Button', 0, None),
	0xf5a9 : ('Begin Ruby', 0, None),
	0xf5aa : ('End Ruby', 0, None),
	0xf5ab : ('Begin Ruby Base', 0, None),
	0xf5ac : ('End Ruby Base', 0, None),
	0xf5ad : ('Begin Ruby Text', 0, None),
	0xf5ae : ('End Ruby Text', 0, None),
	0xf5b1 : ('Begin Koma Yokomoji', 0, None),
	0xf5b2 : ('End Koma Yokomoji', 0, None),
	0xf5b3 : ('Begin Tate', 0, None),
	0xf5b4 : ('End Tate', 0, None),
	0xf5b5 : ('Begin Nekase', 0, None),
	0xf5b6 : ('End Nekase', 0, None),
	0xf5b7 : ('Begin Sup', 0, None),
	0xf5b8 : ('End Sup', 0, None),
	0xf5b9 : ('Begin Sub', 0, None),
	0xf5ba : ('End Sub', 0, None),
	0xf5bb : ('Begin Preformatted', 0, None),
	0xf5bc : ('End Preformatted', 0, None),
	0xf5bd : ('Begin Emp Dots', 0, None),
	0xf5be : ('End Emp Dots', 0, None),
	0xf5c1 : ('Begin Emp Line', 0, None),
	0xf5c2 : ('End Emp Line', 0, None),
	0xf5c3 : ('Begin Draw Char', 2, chop_tag_f5c3),
	0xf5c4 : ('End Draw Char', 0, None),
	0xf5c5 : ('F5C5', 2, chop_tag_f5c5),
	0xf5c6 : ('Begin Box', 2, chop_tag_f5c6),
	0xf5c7 : ('End Box', 0, None),
	0xf5c8 : ('Koma Auto Spacing', 2, chop_tag_f5c8),
	0xf5c9 : ('F5C9', 0, None),
	0xf5ca : ('Space', 2, chop_tag_f5ca),
	0xf5cb : ('F5CB', V, chop_tag_f5cb),
	0xf5cc : ('Text', V, chop_tag_f5cc),
	0xf5d1 : ('Koma Plot', 12, chop_tag_f5d1),
	0xf5d2 : ('EOL', 0, None),
	0xf5d4 : ('Wait', 2, chop_tag_f5d4),
	0xf5d6 : ('Sound Stop', 0, None),
	0xf5d7 : ('Move Obj', 14, chop_tag_f5d7),
	0xf5d8 : ('Book Font', 4, chop_tag_f5d8),
	0xf5d9 : ('Koma Plot Text', 8, chop_tag_f5d9),
	0xf5da : ('Set Wait Prop', 2, chop_tag_f5da),
	0xf5db : ('F5DB', 2, chop_tag_f5db),
	0xf5dc : ('F5DC', 2, chop_tag_f5dc),
	0xf5dd : ('Char Space', 2, chop_tag_f5dd),
	0xf5f1 : ('Line Width', 2, chop_tag_f5f1),
	0xf5f2 : ('Line Color', 4, chop_tag_f5f2),
	0xf5f3 : ('Fill Color', 4, chop_tag_f5f3),
	0xf5f4 : ('Line Mode', 2, chop_tag_f5f4),
	0xf5f5 : ('Move To', 4, chop_tag_f5f5),
	0xf5f6 : ('Line To', 4, chop_tag_f5f6),
	0xf5f7 : ('Draw Box', 4, chop_tag_f5f7),
	0xf5f8 : ('Draw Ellipse', 4, chop_tag_f5f8),
	0xf5f9 : ('Run', 6, chop_tag_f5f9),
}

def add_compressed_stream(hd, size, data):
	(length, off) = rdata(data, 0, '<I')
	add_iter(hd, 'Uncompressed length', length, off - 4, 4, '<I')

def add_header(hd, size, data):
	add_iter(hd, 'Version', read(data, 8, '<H'), 8, 2, '<H')
	add_iter(hd, 'Pseudo Enc. Key', read(data, 0xa, '<H'), 0xa, 2, '<H')
	add_iter(hd, 'Number of objects', read(data, 0x10, '<Q'), 0x10, 8, '<Q')

def add_index_entry(hd, size, data):
	add_iter(hd, 'Offset', read(data, 4, '<I'), 4, 4, '<I')
	add_iter(hd, 'Length', read(data, 8, '<I'), 8, 4, '<I')

def add_tag(hd, size, data):
	(tag, off) = rdata(data, 0, '<H')
	desc = get_or_default(lrf_tags, tag, ('Unknown', 0))
	add_iter(hd, 'Tag', desc[0], off - 2, 2, '<H')
	if desc[1] != 0:
		desc[2](hd, size, data)

lrf_ids = {
	'header': add_header,
	'idxentry': add_index_entry,
	'compressed_stream': add_compressed_stream,
	'tag': add_tag,
}

def open(buf, page, parent):
	reader = lrf_parser(buf, page, parent)
	reader.read()

# vim: set ft=python ts=4 sw=4 noet:
