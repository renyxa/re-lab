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

import struct

from utils import add_iter, add_pgiter, ins_pgiter, rdata

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

def get_or_default(dictionary, key, default):
	if dictionary.has_key(key):
		return dictionary[key]
	return default

class lzss_error:
	pass

def lzss_decompress(data, big_endian=True, offset_bits=12, length_bits=4, text_length=None):
	buffer = []
	length = len(data)

	class SlidingWindow(object):

		def __init__(self, size, fill=' '):
			self.data = [fill for i in range(size)]
			self.begin = 0
			self.end = 1
			self.growing = True

		def push(self, byte):
			self.data[self.end] = byte
			self._advance()

		def copy_out(self, offset, length):
			pos = self.begin
			pos = self._advance_pos(pos, offset)
			out = []
			if self.growing and pos + length > self.end:
				for i in range(length):
					out.append(self.data[pos])
			else:
				for i in range(length):
					out.append(self.data[pos])
					pos = self._advance_pos(pos)
			self._push(out)
			return out

		def _push(self, bytes):
			for b in bytes:
				self.data[self.end] = b
				self._advance()

		def _advance(self):
			self.end = self._advance_pos(self.end)
			if self.end == self.begin:
				self.growing = False
			if not self.growing:
				self.begin = self._advance_pos(self.begin)

		def _advance_pos(self, pos, inc=1):
			if inc == 0:
				return pos
			return (pos + inc) % len(self.data)

	class BitStream(object):

		MASKS = [0x1, 0x3, 0x7, 0xf, 0x1f, 0x3f, 0x7f, 0xff]

		def __init__(self, data):
			self.data = data
			self.pos = 0
			self.current = None
			self.available = 0

			assert len(self.data) > 0

		def read(self, bits, big_endian=False):
			assert bits <= 32

			if bits == 0:
				return 0

			p = [0, 0, 0, 0]

			if big_endian:
				i = (bits - 1) / 8

				over = bits % 8
				if over > 0:
					p[i] = self._read_bits(over)
					bits -= over
					i -= 1
				assert bits % 8 == 0

				while 8 <= bits:
					p[i] = self._read_byte()
					bits -= 8
					i -= 1
				assert bits == 0

			else:
				i = 0

				while 8 <= bits:
					p[i] = self._read_byte()
					bits -= 8
					i += 1
				assert bits < 8

				if 0 < bits:
					p[i] = self._read_bits(bits)

			val = p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24)
			return val

		def at_eos(self):
			return self.at_last_byte() and self.available == 0

		def at_last_byte(self):
			if self._at_end():
				return True

			self._fill()
			return self._at_end()

		def _at_end(self):
			return self.pos == len(self.data) - 1

		def _read_u8(self):
			b = self.data[self.pos]
			self.pos += 1
			return b

		def _fill(self):
			if self.available == 0:
				self.current = ord(self._read_u8())
				self.available = 8
			assert self.available > 0

		def _read_byte(self):
			return self._read_bits(8)

		def _read_bits(self, bits):
			assert bits <= 8

			if bits == 0:
				return 0

			value = 0

			self._fill()

			if bits <= self.available:
				value = self._read_available_bits(bits)
			else:
				bits -= self.available
				value = self._read_available_bits(self.available)
				self._fill()
				value <<= bits
				value |= self._read_available_bits(bits)

			return value

		def _read_available_bits(self, bits):
			assert bits <= self.available

			current = self.current
			if bits < self.available:
				current >>= self.available - bits
			self.available -= bits

			return self.MASKS[bits - 1] & current

	stream = BitStream(data)
	window = SlidingWindow(1 << offset_bits, ' ')

	def finished():
		if text_length == None:
			return stream.at_last_byte()
		else:
			return len(buffer) >= text_length

	while not finished():
		encoded = stream.read(1, big_endian)
		if encoded == 0:
			offset = int(stream.read(offset_bits, big_endian))
			length = int(stream.read(length_bits, big_endian)) + 3
			buffer.extend(window.copy_out(offset, length))
		else:
			c = chr(stream.read(8, big_endian))
			buffer.append(c)
			window.push(c)

	return ''.join(buffer)

imp_version = 0
# default for v.2
imp_file_header_size = 20
imp_color_mode = 1
imp_dirname_length = 0

imp_resource_map = {}

def get_formats():
	# I assume this crap is there as a workaround for a buggy device,
	# not because someone thought it would be a good idea...
	if imp_color_mode == 2:
		return ('<H', '<I', '<I')
	return ('>H', '>I', '>H')

class imp_parser(object):

	def __init__(self, data, page, parent):
		self.data = data
		self.page = page
		self.parent = parent
		self.files = 0
		self.directory_begin = 0
		self.directory_end = 0
		self.compressed = False
		self.window_bits = 14
		self.length_bits = 3
		self.text_length = None

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
		global imp_color_mode

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
		off += 4
		(flags, off) = rdata(self.data, off, '>I')
		imp_color_mode = (int(flags) & (0x3 << 4)) >> 4

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

		text_begin = 0
		text_end = 0
		text_pos = 0
		begin = 0
		for i in range(self.files):
			(length, off) = rdata(data, begin + 8, '>I')
			(typ, off) = rdata(data, off, '4s')
			end = begin + int(length) + 20
			if typ == '    ':
				# defer processing of text file till we know details about compression etc.
				text_begin = begin
				text_end = end
				text_pos = i
			else:
				self.parse_file(data[begin:end], i, typ, fileiter)
			begin = end

		self.parse_text(data[text_begin:text_end], text_pos, fileiter)

	def parse_file(self, data, n, typ, parent):
		fileiter = add_pgiter(self.page, 'File %d (type %s)' % (n, typ), 'imp', 0, data, parent)
		add_pgiter(self.page, 'Header', 'imp', 'imp_file_header', data[0:20], fileiter)

		filedata = data[20:len(data)]
		if imp_resource_map.has_key(typ):
			self.parse_resource(filedata, typ, fileiter)
		elif typ == '!!sw':
			self.parse_sw(filedata, typ, fileiter)
		else:
			add_pgiter(self.page, 'Content', 'imp', 0, data[20:len(data)], fileiter)

	def parse_resource(self, data, typ, parent):
		add_pgiter(self.page, 'Resource header', 'imp', 'imp_resource_header', data[0:32], parent)
		version = int(read(data, 0, '>H'))
		offset = int(read(data, 10, '>I'))
		res_data = data[32:offset]
		idx_data = data[offset:len(data)]
		resiter = add_pgiter(self.page, 'Records', 'imp', 0, res_data, parent)
		idxiter = add_pgiter(self.page, 'Index', 'imp', 0, idx_data, parent)

		idx = self.parse_resource_index(idx_data, idxiter, version)
		for i in idx.keys():
			res = idx[i]
			resdata = data[res[0]:res[0] + res[1]]
			imp_resource_map[typ](self, i, resdata, typ, version, resiter)

	def parse_resource_index(self, data, parent, version):
		index = {}

		off = 0
		i = 0
		entrylen = 12
		if version == 2:
			entrylen = 16
		if imp_color_mode == 2:
			entrylen += 2

		while off + entrylen <= len(data):
			add_pgiter(self.page, 'Entry %d' % i, 'imp', 'imp_resource_index_v%d' % version, data[off:off + entrylen], parent)
			if imp_color_mode == 2:
				(idx, off) = rdata(data, off, '<I')
				(length, off) = rdata(data, off, '<I')
				(start, off) = rdata(data, off, '<I')
			else:
				(idx, off) = rdata(data, off, '>H')
				(length, off) = rdata(data, off, '>I')
				if version == 2:
					off += 4
				(start, off) = rdata(data, off, '>I')
			index[int(idx)] = (int(start), int(length))
			off += 2
			i += 1

		# assert off == len(data)

		return index

	def parse_compression(self, rid, data, typ, version, parent):
		if rid == 0x64:
			add_pgiter(self.page, 'Resource 0x64', 'imp', 'imp_resource_0x64', data, parent)
			off = 6
			(window_bits, off) = rdata(data, off, '>H')
			(length_bits, off) = rdata(data, off, '>H')
			self.window_bits = int(window_bits)
			self.length_bits = int(length_bits)

		elif rid == 0x65:
			resiter = add_pgiter(self.page, 'Resource 0x65', 'imp', 0, data, parent)
			count = len(data) / 10
			recbegin = 0
			for j in range(count):
				recid = 'imp_resource_0x65'
				if j == count - 1:
					recid = 'imp_resource_0x65_last'
					self.text_length = int(read(data, recbegin, '>I'))
				recdata = data[recbegin:recbegin + 10]
				add_pgiter(self.page, 'Record %d' % j, 'imp', recid, recdata, resiter)
				recbegin += 10

	def parse_sw(self, data, index, parent):
		add_pgiter(self.page, 'Resource header', 'imp', 'imp_resource_header', data[0:32], parent)

		off = int(read(data, 10, '>I'))

		reciter = add_pgiter(self.page, 'Records', 'imp', 0, data[32:off], parent)
		idxiter = add_pgiter(self.page, 'Index', 'imp', 0, data[off:len(data)], parent)

		i = 0
		entrylen = 16
		if imp_color_mode == 2:
			entrylen = 18

		while off + entrylen <= len(data):
			add_pgiter(self.page, 'Entry %d' % i, 'imp', 'imp_sw_index', data[off:off + entrylen], idxiter)
			if imp_color_mode == 2:
				(seq, off) = rdata(data, off, '<I')
				(length, off) = rdata(data, off, '<I')
				(start, off) = rdata(data, off, '<I')
			else:
				(seq, off) = rdata(data, off, '>H')
				(length, off) = rdata(data, off, '>I')
				(start, off) = rdata(data, off, '>I')
			recdata = data[int(start):int(start) + int(length)]
			off += 2
			(typ, off) = rdata(data, off, '4s')
			add_pgiter(self.page, 'Record %d (typ %s)' % (i, typ), 'imp', 'imp_sw_record', recdata, reciter)
			i += 1

	def parse_anct(self, rid, data, typ, version, parent):
		if rid == 0 or rid == 1:
			(fmtH, fmtI, fmtId) = get_formats()

			(count, off) = rdata(data, 0, fmtI)
			view = 'large'
			if rid == 1:
				view = 'small'
			tagiter = add_pgiter(self.page, 'Tags for %s view' % view,  'imp', 'imp_anct', data, parent)
			off = 0
			if int(count) > 0:
				for j in range(int(count)):
					add_pgiter(self.page, 'Tag %d' % j, 'imp', 'imp_anct_tag', data[off:off + 8], tagiter)
					off += 8

	def parse_bgcl(self, rid, data, typ, version, parent):
		if rid == 0x80:
			add_pgiter(self.page, 'Background color', 'imp', 'imp_bgcl', data, parent)

	def parse_bpgz(self, rid, data, typ, version, parent):
		if version == 1:
			self.parse_page_info(rid, data, typ, parent)
		else:
			# TODO: rev. eng. this
			pass

	def parse_bpos(self, rid, data, typ, version, parent):
		pass

	def parse_devm(self, rid, data, typ, version, parent):
		pass

	def parse_elnk(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'External link 0x%x' % rid, 'imp', 'imp_elnk', data, parent)

	def parse_ests(self, rid, data, typ, version, parent):
		if rid == 1:
			add_pgiter(self.page, 'CSS x-sbp-orphan-pull', 'imp', 'imp_ests_orphan_pull', data, parent)
		elif rid == 2:
			add_pgiter(self.page, 'CSS x-sbp-widow-push', 'imp', 'imp_ests_widow_push', data, parent)
		else:
			add_pgiter(self.page, 'Unknown (0x%x)' % rid, 'imp', 0, data, parent)

	def parse_fidt(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Form input data 0x%x' % rid, 'imp', 'imp_fidt', data, parent)

	def parse_fitm(self, rid, data, typ, version, parent):
		pass

	def parse_form(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Resource 0x%x' % rid, 'imp', 'imp_form', data, parent)

	def parse_frdt(self, rid, data, typ, version, parent):
		pass

	def parse_gif(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Image 0x%x' % rid, 'imp', 0, data, parent)

	def parse_hfpz(self, rid, data, typ, version, parent):
		assert version == 1
		self.parse_page_info(rid, data, typ, parent)

	def parse_hrle(self, rid, data, typ, version, parent):
		ruleiter = add_pgiter(self.page, 'Horizontal rules', 'imp', 0, data, parent)

		n = 0
		begin = 0
		while begin + 12 <= len(data):
			add_pgiter(self.page, 'Rule %d' % n, 'imp', 'imp_hrle', data[begin:begin + 12], ruleiter)
			n += 1
			begin += 12

	def parse_hyp2(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Resource 0x%x' % rid, 'imp', 'imp_hyp2', data, parent)

	def parse_imrn(self, rid, data, typ, version, parent):
		n = 0
		off = 0
		size = 32
		if imp_color_mode == 2:
			# FIXME: this does not work. Apparently some records can be
			# 36 bytes long.
			size += 2

		while off + size <= len(data):
			add_pgiter(self.page, 'Image %d' % n, 'imp', 'imp_imrn', data[off:off + size], parent)
			n += 1
			off += size

	def parse_jpeg(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Image 0x%x' % rid, 'imp', 0, data, parent)

	def parse_lnks(self, rid, data, typ, version, parent):
		lnkiter = add_pgiter(self.page, 'Links', 'imp', 0, data, parent)

		n = 0
		begin = 0
		size = 34
		if imp_color_mode == 2:
			size += 2
		while begin + size <= len(data):
			add_pgiter(self.page, 'Link %d' % n, 'imp', 'imp_lnks', data[begin:begin + size], lnkiter)
			n += 1
			begin += size

	def parse_mrgn(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Record 0x%x' % rid, 'imp', 'imp_mrgn', data, parent)

	def parse_pc31(self, rid, data, typ, version, parent):
		pass

	def parse_pcz0(self, rid, data, typ, version, parent):
		if version == 1:
			n = 0
			off = 0
			size = 46
			while off + size <= len(data):
				add_pgiter(self.page, 'Image position %d' % n, 'imp', 'imp_pcz0', data[off:off + size], parent)
				n += 1
				off += size

	def parse_pcz1(self, rid, data, typ, version, parent):
		n = 0
		off = 0
		size = 30
		while off + size <= len(data):
			add_pgiter(self.page, 'Border position %d' % n, 'imp', 'imp_pcz1', data[off:off + size], parent)
			n += 1
			off += size

	def parse_pinf(self, rid, data, typ, version, parent):
		if rid == 0 or rid == 1:
			view = 'large'
			if rid == 1:
				view = 'small'
			add_pgiter(self.page, 'Page info for %s view' % view,  'imp', 'imp_pinf', data, parent)

	def parse_pic2(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Image 0x%x' % rid, 'imp', 0, data, parent)

	def parse_png(self, rid, data, typ, version, parent):
		add_pgiter(self.page, 'Image 0x%x' % rid, 'imp', 0, data, parent)

	def parse_ppic(self, rid, data, typ, version, parent):
		if rid == 0 or rid == 1:
			view = 'large'
			if rid == 1:
				view = 'small'
			add_pgiter(self.page, 'Picture info for %s view' %view, 'imp', 'imp_ppic', data, parent)

	def parse_str2(self, rid, data, typ, version, parent):
		if rid == 0x8001:
			add_pgiter(self.page, 'String run index', 'imp', 0, data, parent)
		elif rid >= 0x8002:
			add_pgiter(self.page, 'String run %x' % rid, 'imp', 'imp_str2', data, parent)

	def parse_strn(self, rid, data, typ, version, parent):
		striter = add_pgiter(self.page, 'String runs', 'imp', 0, data, parent)
		off = 0
		n = 0
		while off + 8 <= len(data):
			add_pgiter(self.page, 'Run %d' % n, 'imp', 'imp_strn', data[off:off + 8], striter)
			off += 8
			n += 1

	def parse_styl(self, rid, data, typ, version, parent):
		if rid == 0x80:
			n = 0
			off = 0
			size = 46
			while off + size <= len(data):
				add_pgiter(self.page, 'Style %d' % n, 'imp', 'imp_styl', data[off:off + size], parent)
				off += size
				n += 1

	def parse_tabl(self, rid, data, typ, version, parent):
		if rid == 0x80:
			tablesiter = add_pgiter(self.page, 'Tables', 'imp', 0, data, parent)

			n = 0
			off = 0
			size = 24
			if imp_color_mode == 2:
				size += 4

			while off + size <= len(data):
				add_pgiter(self.page, 'Table %d' % n, 'imp', 'imp_tabl', data[off:off + size], tablesiter)
				off += size
				n += 1

	def parse_tcel(self, rid, data, typ, version, parent):
		cellsiter = add_pgiter(self.page, 'Table cells 0x%x' % rid, 'imp', 0, data, parent)

		if version == 1:
			n = 0
			begin = 0
			while begin + 26 <= len(data):
				add_pgiter(self.page, 'Cell %d' % n, 'imp', 'imp_tcel_v1', data[begin:begin + 26], cellsiter)
				n += 1
				begin += 26

	def parse_tgnt(self, rid, data, typ, version, parent):
		pass

	def parse_trow(self, rid, data, typ, version, parent):
		rowsiter = add_pgiter(self.page, 'Table Rows 0x%x' % rid, 'imp', 0, data, parent)

		if version == 1:
			n = 0
			begin = 0
			while begin + 16 <= len(data):
				add_pgiter(self.page, 'Row %d' % n, 'imp', 'imp_trow_v1', data, rowsiter)
				n += 1
				begin += 16

	def parse_page_info(self, rid, data, typ, parent):
		def read_block(off, fmt, size):
			count = int(read(data, off, fmt))
			end = off + struct.calcsize(fmt) + count * size
			return (count, end, (off, end))

		def add_block_iter(title, span, parent, callback='imp_page_info_block_i'):
			return add_pgiter(self.page, title, 'imp', callback, data[span[0]:span[1]], parent)

		def add_record_iters(title, span, size, callback, parent, count_size = 4):
			n = 0
			off = span[0] + count_size
			while off + size <= span[1] and off + size <= len(data):
				add_pgiter(self.page, title + ' %d' % n, 'imp', callback, data[off:off + size], parent)
				n += 1
				off += size

		if imp_color_mode == 2:
			# TODO: figure out how this looks in grayscale mode.
			# Apparently there are more changes than just switching from
			# big to little endian...
			return

		off = 6

		(geometries_n, off, geometries) = read_block(off, '>H', 8)
		geometries_iter = add_block_iter('Line geometries', geometries, parent, 'imp_page_info_block_h')
		add_record_iters('Line geometry', geometries, 8, 'imp_page_info_geometry', geometries_iter, 2)

		(indexes_n, off, indexes) = read_block(off, '>I', 4)
		indexes_iter = add_block_iter('Page indexes', indexes, parent)
		add_record_iters('Page index', indexes, 4, 'imp_page_info_page_index', indexes_iter)

		(pages_n, off, pages) = read_block(off, '>I', 8)
		pages_iter = add_block_iter('Page spans', pages, parent)
		add_record_iters('Page', pages, 8, 'imp_page_info_page', pages_iter)

		pgsiter = add_pgiter(self.page, 'Pages', 'imp', 0, data[off:len(data)], parent)
		for i in range(pages_n):
			try:
				begin = off
				off += 8
				(regions_n, off, regions) = read_block(off, '>I', 20)
				(lines_n, off, lines) = read_block(off, '>I', 3)

				line_index_begin = off
				line_indexes = []

				n = 0
				while n < lines_n:
					(record, off) = rdata(data, off, 'B')
					if int(record) & 0x80:
						n += 1
						line_indexes.append((off - 1, off))
					elif int(record) & 0xc0:
						(rec, off) = rdata(data, off, 'B')
						n += 1
						line_indexes.append((off - 2, off))
					else:
						(count, off) = rdata(data, off, 'B')
						n += int(count)
						line_indexes.append((off - 2, off))

				line_index_data = data[line_index_begin:off]

				(borders_n, off, borders) = read_block(off, '>I', 4)
				(images_n, off, images) = read_block(off, '>I', 4)

				pgiter = add_pgiter(self.page, 'Page %d' % i, 'imp', 0, data[begin:off], pgsiter)
				regions_iter = add_block_iter('Page regions', regions, pgiter)
				add_record_iters('Page region', regions, 20, 'imp_page_info_page_region', regions_iter)
				lines_iter = add_block_iter('Lines', lines, pgiter)
				add_record_iters('Line', lines, 3, 'imp_page_info_line', lines_iter)
				add_pgiter(self.page, 'Line index', 'imp', 'imp_page_info_line_index', line_index_data, lines_iter)
				borders_iter = add_block_iter('Borders', borders, pgiter)
				add_record_iters('Border', borders, 4, 'imp_page_info_border', borders_iter)
				images_iter = add_block_iter('Images', images, pgiter)
				add_record_iters('Image', images, 4, 'imp_page_info_image', images_iter)
			except struct.error:
				pgiter = add_pgiter(self.page, 'Page %d' % i, 'imp', 0, data[begin:len(data)], pgsiter)
				return

	def parse_text(self, data, n, parent):
		fileiter = ins_pgiter(self.page, 'File %d (type Text)' % n, 'imp', 0, data, parent, n)
		add_pgiter(self.page, 'Header', 'imp', 'imp_file_header', data[0:20], fileiter)

		filedata = data[20:len(data)]
		if not self.compressed:
			textiter = add_pgiter(self.page, 'Text', 'imp', 'imp_text', filedata, fileiter)
		else:
			dataiter = add_pgiter(self.page, 'Compressed text', 'imp', 0, filedata, fileiter)
			uncompressed = lzss_decompress(filedata, True, self.window_bits, self.length_bits, self.text_length)
			textiter = add_pgiter(self.page, 'Text', 'imp', 'imp_text', uncompressed, dataiter)

imp_resource_map = {
	'!!cm': imp_parser.parse_compression,
	'AncT': imp_parser.parse_anct,
	'BGcl': imp_parser.parse_bgcl,
	'BPgz': imp_parser.parse_bpgz,
	'BPgZ': imp_parser.parse_bpgz,
	'BPos': imp_parser.parse_bpos,
	'Devm': imp_parser.parse_devm,
	'eLnk': imp_parser.parse_elnk,
	'GIF ': imp_parser.parse_gif,
	'ESts': imp_parser.parse_ests,
	'FIDt': imp_parser.parse_fidt,
	'FItm': imp_parser.parse_fitm,
	'Form': imp_parser.parse_form,
	'FrDt': imp_parser.parse_frdt,
	'HfPz': imp_parser.parse_hfpz,
	'HfPZ': imp_parser.parse_hfpz,
	'HRle': imp_parser.parse_hrle,
	'Hyp2': imp_parser.parse_hyp2,
	'ImRn': imp_parser.parse_imrn,
	'JPEG': imp_parser.parse_jpeg,
	'Lnks': imp_parser.parse_lnks,
	'Mrgn': imp_parser.parse_mrgn,
	'Pc31': imp_parser.parse_pc31,
	'Pcz0': imp_parser.parse_pcz0,
	'PcZ0': imp_parser.parse_pcz0,
	'Pcz1': imp_parser.parse_pcz1,
	'PcZ1': imp_parser.parse_pcz1,
	'PIC2': imp_parser.parse_pic2,
	'pInf': imp_parser.parse_pinf,
	'PNG ': imp_parser.parse_png,
	'PPic': imp_parser.parse_ppic,
	'StR2': imp_parser.parse_str2,
	'StRn': imp_parser.parse_strn,
	'Styl': imp_parser.parse_styl,
	'Tabl': imp_parser.parse_tabl,
	'TCel': imp_parser.parse_tcel,
	'TGNt': imp_parser.parse_tgnt,
	'TRow': imp_parser.parse_trow,
}

def add_imp_anct(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()

	count = read(data, 0, fmtI)
	add_iter(hd, 'Count of anchor tags', count, 0, 4, fmtI)

def add_imp_anct_tag(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()

	(page, off) = rdata(data, 0, fmtI)
	add_iter(hd, 'Page number', page, off - 4, 4, fmtI)
	(offset, off) = rdata(data, off, fmtI)
	add_iter(hd, 'Offset to anchor tag in text', offset, off - 4, 4, fmtI)

def add_imp_bgcl(hd, size, data):
	off = 2
	(red, off) = rdata(data, off, 'B')
	add_iter(hd, 'Red', '0x%x' % int(red), off - 1, 1, 'B')
	(bgred, off) = rdata(data, off, 'B')
	add_iter(hd, 'Red color set', '%s' % (int(bgred) == 0), off - 1, 1, 'B')
	(green, off) = rdata(data, off, 'B')
	add_iter(hd, 'Green', '0x%x' % int(green), off - 1, 1, 'B')
	(bggreen, off) = rdata(data, off, 'B')
	add_iter(hd, 'Green color set', '%s' % (int(bggreen) == 0), off - 1, 1, 'B')
	(blue, off) = rdata(data, off, 'B')
	add_iter(hd, 'Blue', '0x%x' % int(blue), off - 1, 1, 'B')
	(bgblue, off) = rdata(data, off, 'B')
	add_iter(hd, 'Blue color set', '%s' % (int(bgblue) == 0), off - 1, 1, 'B')

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

def add_imp_elnk(hd, size, data):
	fmt = '%ds' % size
	(target, off) = rdata(data, 0, fmt)
	add_iter(hd, 'Target', target, 0, size, fmt)

def add_imp_ests_orphan_pull(hd, size, data):
	pass

def add_imp_ests_widow_push(hd, size, data):
	pass

def add_imp_fidt(hd, size, data):
	pass

def add_imp_file_header(hd, size, data):
	(name, off) = rdata(data, 0, '4s')
	add_iter(hd, 'File name', name, 0, 4, '4s')
	off += 4
	(size, off) = rdata(data, off, '>I')
	add_iter(hd, 'File size', size, off - 4, 4, '>I')
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'File type', typ, off - 4, 4, '4s')

def add_imp_form(hd, size, data):
	pass

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

	(flags, off) = rdata(data, off, '>I')
	imp_zoom_states = ('Both', 'Small', 'Large')
	imp_color_modes = ('Unknown', 'Color VGA', 'Grayscale Half-VGA')
	zoom = int(flags) & 0x3
	color_mode = (int(flags) & (0x3 << 4)) >> 4
	flags_str = 'zoom = %s, color mode = %s' % (imp_zoom_states[zoom], imp_color_modes[color_mode])
	add_iter(hd, 'Flags', flags_str, off - 4, 4, '>I')

	off += 4
	assert off == 0x30

def add_imp_hrle(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()

	(size, off) = rdata(data, 0, fmtH)
	add_iter(hd, 'Size', size, off - 2, 2, fmtH)

	(width, off) = rdata(data, off, fmtH)
	width_str = width
	if (int(width) & 0x8000):
		width_str = '%d %%' % (0xffff - int(width))
	add_iter(hd, 'Width', width_str, off - 2, 2, fmtH)

	(align, off) = rdata(data, off, fmtH)
	align_map = {0xfffe: 'left', 0xffff: 'right', 1: 'center', 0xfffd: 'justify'}
	align_str = get_or_default(align_map, int(align), 'unknown')
	add_iter(hd, 'Alignment', align_str, off - 2, 2, fmtH)

	off += 2
	(offset, off) = rdata(data, off, fmtI)
	add_iter(hd, 'Offset into text', offset, off - 4, 4, fmtI)

def add_imp_hyp2(hd, size, data):
	pass

def add_imp_imrn(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()
	idlen = struct.calcsize(fmtId)

	off = 8
	(width, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Width', width, off - 2, 2, fmtH)
	(height, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Height', height, off - 2, 2, fmtH)
	off += 6
	if imp_color_mode == 2:
		off += 2
	(offset, off) = rdata(data, off, fmtI)
	add_iter(hd, 'Offset into text', offset, off - 4, 4, fmtI)
	off += 4
	(typ, off) = rdata(data, off, '4s')
	typ_str = typ
	if imp_color_mode == 2:
		typ_str = ''.join([c for c in reversed(typ)])
	add_iter(hd, 'Type', typ_str, off - 4, 4, '4s')
	(iid, off) = rdata(data, off, fmtId)
	add_iter(hd, 'Image ID', '0x%x' % iid, off - idlen, idlen, fmtId)
	assert off == size

def add_imp_lnks(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()
	idlen = struct.calcsize(fmtId)

	(start, off) = rdata(data, 0, fmtI)
	add_iter(hd, "Offset of the link's start", start, off - 4, 4, fmtI)
	(end, off) = rdata(data, off, fmtI)
	add_iter(hd, "Offset of the link's end", end, off - 4, 4, fmtI)

	toc = int(start) == 0x7fffffff and int(end) == 0xffffffff
	internal = False
	(typ, off) = rdata(data, off, fmtI)
	typ_str = 'unknown'
	if int(typ) == 0xffffffff:
		typ_str = 'internal'
		internal = True
	elif int(typ) == 0xfffffffc:
		typ_str = 'external'
	elif toc:
		typ_str = 'table of contents'
	add_iter(hd, 'Type', typ_str, off - 4, 4, fmtI)

	off += 4
	(target, off) = rdata(data, off, fmtI)
	add_iter(hd, "Offset of the link's target", target, off - 4, 4, fmtI)
	off += 6
	(rid, off) = rdata(data, off, fmtId)
	rid_str = '0x%x' % rid
	if toc or internal:
		rid_str = 'internal'
		assert int(rid) == 0
	add_iter(hd, 'Resource ID of ext. link', rid_str, off - idlen, idlen, fmtId)
	off += 6

	assert off == size

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

def add_imp_mrgn(hd, size, data):
	pass

def add_imp_page_info_block_h(hd, size, data):
	count = read(data, 0, '>H')
	add_iter(hd, 'Count', count, 0, 2, '>H')

def add_imp_page_info_block_i(hd, size, data):
	count = read(data, 0, '>I')
	add_iter(hd, 'Count', count, 0, 4, '>I')

def add_imp_page_info_border(hd, size, data):
	number = read(data, 0, '>I')
	add_iter(hd, 'Number of border record in Pcz1 or PcZ1', number, 0, 4, '>I')

def add_imp_page_info_geometry(hd, size, data):
	(left, off) = rdata(data, 0, '>H')
	add_iter(hd, 'Offset from left edge', left, off - 2, 2, '>H')

	(top, off) = rdata(data, off, '>H')
	top_str = top
	top_title = 'Offset from previous line'
	if int(top) == 0x8000:
		top_str = 0
		top_title = 'Offset from top edge'
	elif int(top) & 0x8000:
		top_str = 0xffff - int(top)
		top_title = 'Offset from top edge'
	add_iter(hd, top_title, top_str, off - 2, 2, '>H')

	(width, off) = rdata(data, off, '>H')
	add_iter(hd, 'Width', width, off - 2, 2, '>H')
	(height, off) = rdata(data, off, '>H')
	add_iter(hd, 'Height', height, off - 2, 2, '>H')

def add_imp_page_info_image(hd, size, data):
	number = read(data, 0, '>I')
	add_iter(hd, 'Number of image record in Pcz0 or PcZ0', number, 0, 4, '>I')

def add_imp_page_info_line(hd, size, data):
	(flags, off) = rdata(data, 0, 'B')
	add_iter(hd, 'Flags', int(flags) & 0xf0, off - 1, 1, 'B')
	(lower, off) = rdata(data, off, 'B')
	offset = ((int(flags) & 0xf) << 8) | int(lower)
	add_iter(hd, 'Offset into page record', offset, off - 1, 1, 'B')
	(count, off) = rdata(data, off, 'B')
	add_iter(hd, 'Number of characters', count, off - 1, 1, 'B')

def add_imp_page_info_line_index(hd, size, data):
	off = 0
	while off < size:
		(record, off) = rdata(data, off, 'B')
		if int(record) & 0x80:
			rid = int(record) & 0x7f
			add_iter(hd, 'Line geometry for a single line', '%d' % rid, off - 1, 1, 'B')
		elif int(record) & 0xc0:
			(rec, off) = rdata(data, off, 'B')
			rid = ((int(record) & 0xf) << 8) | int(rec)
			add_iter(hd, 'Line geometry for a single line', '%d' % rid, off - 2, 2, '>H')
		else:
			add_iter(hd, 'Line geometry for N lines', record, off - 1, 1, 'B')
			(count, off) = rdata(data, off, 'B')
			add_iter(hd, 'Number of lines', count, off - 1, 1, 'B')

def add_imp_page_info_page(hd, size, data):
	(first, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Offset into text of first character of page', first, off - 4, 4, '>I')
	(last, off) = rdata(data, off, '>I')
	add_iter(hd, 'Offset into text of last character of page', last, off - 4, 4, '>I')

def add_imp_page_info_page_index(hd, size, data):
	offset = read(data, 0, '>I')
	add_iter(hd, 'Offset to page record', offset, 0, 4, '>I')

def add_imp_page_info_page_region(hd, size, data):
	off = 4
	(top, off) = rdata(data, off, '>I')
	add_iter(hd, 'Screen top', top, off - 4, 4, '>I')
	(right, off) = rdata(data, off, '>I')
	add_iter(hd, 'Screen right', right, off - 4, 4, '>I')
	(bottom, off) = rdata(data, off, '>I')
	add_iter(hd, 'Screen bottom', bottom, off - 4, 4, '>I')
	(left, off) = rdata(data, off, '>I')
	add_iter(hd, 'Screen left', left, off - 4, 4, '>I')

def add_imp_pcz0(hd, size, data):
	off = 4
	(horizontal, off) = rdata(data, off, '>I')
	add_iter(hd, 'Horizontal offset', horizontal, off - 4, 4, '>I')
	(vertical, off) = rdata(data, off, '>I')
	add_iter(hd, 'Vertical offset', vertical, off - 4, 4, '>I')
	(width, off) = rdata(data, off, '>I')
	add_iter(hd, 'Width', width, off - 4, 4, '>I')
	(height, off) = rdata(data, off, '>I')
	add_iter(hd, 'Height', height, off - 4, 4, '>I')
	off += 2
	(pos, off) = rdata(data, off, '>I')
	add_iter(hd, 'Position in text', pos, off - 4, 4, '>I')
	off += 4
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'Type', typ, off - 4, 4, '4s')
	off += 4
	(rid, off) = rdata(data, off, '>H')
	add_iter(hd, 'Resource ID', '0x%x' % rid, off - 2, 2, '>H')
	off += 6
	assert off == 46

def add_imp_pcz1_v1(hd, size, data):
	off = 4
	(left, off) = rdata(data, off, '>I')
	add_iter(hd, 'Left position', left, off - 4, 4, '>I')
	(top, off) = rdata(data, off, '>I')
	add_iter(hd, 'Top position', top, off - 4, 4, '>I')
	(width, off) = rdata(data, off, '>I')
	add_iter(hd, 'Width', width, off - 4, 4, '>I')
	(height, off) = rdata(data, off, '>I')
	add_iter(hd, 'Height', height, off - 4, 4, '>I')
	off += 10
	assert off == 30

def add_imp_pcz1_v2(hd, size, data):
	pass

def add_imp_pinf(hd, size, data):
	off = 4
	(last, off) = rdata(data, off, '>H')
	add_iter(hd, 'Last page', last, off - 2, 2, '>H')
	(images, off) = rdata(data, off, '>H')
	add_iter(hd, 'Count of images', images, off - 2, 2, '>H')

def add_imp_ppic(hd, size, data):
	off = 2
	(borders, off) = rdata(data, off, '>I')
	add_iter(hd, 'Count of cell and table borders', borders, off - 4, 4, '>I')
	(has_borders, off) = rdata(data, off, '>I')
	has_borders_str = get_or_default({0: False, 0x64: True}, int(has_borders), 'unknown')
	add_iter(hd, 'Has any borders?', has_borders_str, off - 4, 4, '>I')
	(pictures, off) = rdata(data, off, '>I')
	add_iter(hd, 'Count of pictures', pictures, off - 4, 4, '>I')
	(has_pictures, off) = rdata(data, off, '>I')
	has_pictures_str = get_or_default({0: False, 0x64: True}, int(has_pictures), 'unknown')
	add_iter(hd, 'Has any pictures?', has_pictures_str, off - 4, 4, '>I')

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
	bit_pos_map = {0x1: 7, 0x2: 6, 0x4: 5, 0x8: 4, 0x10: 3, 0x20: 2, 0x40: 1, 0x80: 0}
	(bit_pos, off) = rdata(hd, off, '>H')
	bit_pos_val = get_or_default(bit_pos_map, int(bit_pos), 0)
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

def add_imp_str2(hd, size, data):
	(offset, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Offset into text', offset, off - 4, 4, '>I')
	(style, off) = rdata(data, off, '>I')
	add_iter(hd, 'Style', style, off - 4, 4, '>I')

def add_imp_strn(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()

	(offset, off) = rdata(data, 0, fmtI)
	add_iter(hd, 'Offset into text', offset, off - 4, 4, fmtI)
	(style, off) = rdata(data, off, fmtI)
	add_iter(hd, 'Style', style, off - 4, 4, fmtI)

def add_imp_styl(hd, size, data):
	off = 2
	(fmtH, fmtI, fmtId) = get_formats()

	(decoration, off) = rdata(data, off, fmtH)
	decoration_map = {0: 'none', 1: 'subscript', 2: 'superscript', 4: 'line-through'}
	decoration_str = get_or_default(decoration_map, int(decoration), 'unknown')
	add_iter(hd, 'Text decoration', decoration_str, off - 2, 2, fmtH)

	off += 2

	(font_family, off) = rdata(data, off, fmtH)
	font_family_map = {0x14: 'serif', 0x15: 'sans-serif', 3: 'smallfont', 4: 'monospace'}
	font_family_str = get_or_default(font_family_map, int(font_family), 'unknown')
	add_iter(hd, 'Font family', font_family_str, off - 2, 2, fmtH)

	(font_style, off) = rdata(data, off, fmtH)
	font_style_map = {0: 'regular', 1: 'bold', 2: 'italic', 3: 'bold italic', 4: 'underlined', 5: 'bold underlined', 6: 'italic underlined'}
	font_style_str = get_or_default(font_style_map, int(font_style), 'unknown')
	add_iter(hd, 'Text style', font_style_str, off - 2, 2, fmtH)

	(font_size, off) = rdata(data, off, fmtH)
	font_size_map = {1: 'xx-small', 2: 'x-small', 3: 'small', 4: 'medium', 5: 'large', 6: 'x-large', 7: 'xx-large'}
	font_size_str = get_or_default(font_size_map, int(font_size), 'unknown')
	add_iter(hd, 'Font size', font_size_str, off - 2, 2, fmtH)

	(text_align, off) = rdata(data, off, fmtH)
	text_align_map = {0: 'none', 0xfffe: 'left', 0xffff: 'right', 1: 'center', 0xfffd: 'justify'}
	text_align_str = get_or_default(text_align_map, int(text_align), 'unknown')
	add_iter(hd, 'Text alignment', text_align_str, off - 2, 2, fmtH)

	# TODO: parse colors
	# (text_color, off) = rdata(data, off, fmtH)
	off += 3
	# (bg_color, off) = rdata(data, off, fmtH)
	off += 3

	(margin_top, off) = rdata(data, off, fmtH)
	margin_top_str = margin_top
	if int(margin_top) == 0xffff:
		margin_top_str = 'not defined'
	add_iter(hd, 'Top margin', margin_top_str, off - 2, 2, fmtH)

	(text_indent, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Text indent', text_indent, off - 2, 2, fmtH)
	(margin_right, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Right margin', margin_right, off - 2, 2, fmtH)
	(margin_left, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Left margin', margin_left, off - 2, 2, fmtH)

	off += 2

	(columns, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Number of columns', columns, off - 2, 2, fmtH)

	off += 14
	assert off == 46

def get_index_formats():
	(dummy, fmtI, fmtId) = get_formats()
	return (fmtI, fmtId)

def add_imp_resource_index(hd, size, data, v2=False):
	(fmt, idfmt) = get_index_formats()

	(idx, off) = rdata(data, 0, idfmt)
	add_iter(hd, 'Resource ID', '0x%x' % int(idx), 0, off, idfmt)
	(length, off) = rdata(data, off, fmt)
	add_iter(hd, 'Record length', length, off - 4, 4, fmt)
	if v2:
		off += 4
	(start, off) = rdata(data, off, fmt)
	add_iter(hd, 'Offset to start of record', start, off - 4, 4, fmt)

def add_imp_resource_index_v1(hd, size, data):
	add_imp_resource_index(hd, size, data)

def add_imp_resource_index_v2(hd, size, data):
	add_imp_resource_index(hd, size, data, True)

def add_imp_sw_index(hd, size, data):
	(fmt, idfmt) = get_index_formats()

	(seq, off) = rdata(data, 0, idfmt)
	add_iter(hd, 'Sequence number', seq, 0, struct.calcsize(idfmt), idfmt)
	(length, off) = rdata(data, off, fmt)
	add_iter(hd, 'Length of item', length, off - 4, 4, fmt)
	(offset, off) = rdata(data, off, fmt)
	add_iter(hd, 'Offset to beginning of item', offset, off - 4, 4, fmt)
	off += 2
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'File type', typ, off - 4, 4, '4s')

def add_imp_sw_record(hd, size, data):
	pass

def add_imp_tabl(hd, size, data):
	(fmtH, fmtI, fmtId) = get_formats()

	(align, off) = rdata(data, 0, fmtH)
	align_map = {0xfffa: 'not specified', 0xfffe: 'left', 0xffff: 'right', 1: 'center', 0xfffd: 'justify'}
	align_str = get_or_default(align_map, int(align), 'unknown')
	add_iter(hd, 'Text alignment', align_str, off - 2, 2, fmtH)

	(width, off) = rdata(data, off, fmtH)
	w = int(width)
	if w == 0xffff:
		width_str = 'not specified'
	elif (w & 0x8000) != 0:
		width_str = "%d %%" % (0xffff - w)
	else:
		width_str = w
	add_iter(hd, 'Width', width_str, off - 2, 2, fmtH)

	(border, off) = rdata(data, off, fmtH)
	border_map = {0: 'single', 0xffff: 'double'}
	border_str = get_or_default(border_map, int(border), 'unknown')
	add_iter(hd, 'Border', border_str, off - 2, 2, fmtH)

	(cellspacing, off) = rdata(data, off, fmtH)
	cellspacing_str = cellspacing
	if int(cellspacing) == 0xffff:
		cellspacing_str = 'not set'
	add_iter(hd, 'Cell spacing', cellspacing_str, off - 2, 2, fmtH)

	(cellpadding, off) = rdata(data, off, fmtH)
	cellpadding_str = cellpadding
	if int(cellpadding) == 0xffff:
		cellpadding_str = 'not set'
	add_iter(hd, 'Cell padding', cellpadding_str, off - 2, 2, fmtH)

	if imp_color_mode == 2:
		off += 2

	(caption, off) = rdata(data, off, fmtI)
	caption_map = {1: 'yes', 0xffffffff: 'no'}
	caption_str = get_or_default(caption_map, int(caption), 'unknown')
	add_iter(hd, 'Caption present?', caption_str, off - 4, 4, fmtI)

	(caption_length, off) = rdata(data, off, fmtI)
	add_iter(hd, 'Caption length', caption_length, off - 4, 4, fmtI)

	off += 2

	(list_style, off) = rdata(data, off, fmtH)

	(rowsid, off) = rdata(data, off, fmtH)
	add_iter(hd, 'Rows ID', "0x%x" % rowsid, off - 2, 2, fmtH)

	if imp_color_mode == 2:
		off += 2

	assert off == size

def add_imp_tcel_v1(hd, size, data):
	off = 6
	(typ, off) = rdata(data, off, '>H')
	typ_map = {0xfffa: 'table', 0xfffc: 'definition list'}
	typ_str = get_or_default(typ_map, int(typ), 'unknown')
	add_iter(hd, 'Cell type', typ_str, off - 2, 2, '>H')

	(align, off) = rdata(data, off, '>H')
	align_map = {0xfffa: 'middle', 0xfffc: 'top', 0xfffb: 'bottom'}
	align_str = get_or_default(align_map, int(align), 'unknown')
	add_iter(hd, 'Vertical alignment', align_str, off - 2, 2, '>H')

	(width, off) = rdata(data, off, '>H')
	width_str = width
	if int(width) == 0:
		width_str = 'not set'
	add_iter(hd, 'Width', width_str, off - 2, 2, '>H')

	(height, off) = rdata(data, off, '>H')
	height_str = height
	if int(height) == 0:
		height_str = 'not set'
	add_iter(hd, 'Height', height_str, off - 2, 2, '>H')

	(offset, off) = rdata(data, off, '>I')
	add_iter(hd, 'Offset into text', offset, off - 4, 4, '>I')

	(length, off) = rdata(data, off, '>I')
	add_iter(hd, 'Length of cell content', length, off - 4, 4, '>I')

	(bgcolor, off) = rdata(data, off, '>I')
	if int(bgcolor) == 0xffffffff:
		bgcolor_str = 'not set'
	else:
		bgcolor_str = '#%x' % (int(bgcolor) & 0xffffff)
	add_iter(hd, 'Background color', bgcolor_str, off - 4, 4, '>I')

def add_imp_tcel_v2(hd, size, data):
	pass

def add_imp_text(hd, size, data):
	control_char_map = {
		0xa: 'End of document',
		0xb: 'Start of element',
		0xd: 'Line break',
		0xe: 'Start of table',
		0xf: 'Image',
		0x13: 'End of cell',
		0x14: 'Horizontal rule',
		0x15: 'Start/End of header content',
		0x15: 'Start/End of footer content',
	}

	begin = None

	for off in range(len(data)):
		c = data[off]
		o = ord(c)
		if control_char_map.has_key(o):
			if begin != None:
				add_iter(hd, 'Text', data[begin:off], begin, off - begin, '%ds' % (off - begin))
			begin = None
			control_char = get_or_default(control_char_map, o, '')
			add_iter(hd, control_char, '0x%x' % o, off, 1, 'B')
		elif begin == None:
			begin = off

	assert begin == None

def add_imp_trow_v1(hd, size, data):
	(typ, off) = rdata(data, 0, '>I')
	typ_map = {0xfffafffa: 'table', 0xfffffffc: 'definition list'}
	typ_str = get_or_default(typ_map, int(typ), 'unknown')
	add_iter(hd, 'Row type', typ_str, 0, 4, '>I')

	(border, off) = rdata(data, off, '>H')
	border_map = {0: 'single', 0xffff: 'double'}
	border_str = get_or_default(border_map, int(border), 'unknown')
	add_iter(hd, 'Border', border_str, off - 2, 2, '>H')

	(celid, off) = rdata(data, off, '>H')
	add_iter(hd, 'Cell ID', '0x%x' % celid, off - 2, 2, '>H')

	(offset, off) = rdata(data, off, '>I')
	add_iter(hd, 'Offset into text', offset, off - 4, 4, '>I')

	(length, off) = rdata(data, off, '>I')
	add_iter(hd, 'Length of row content', length, off - 4, 4, '>I')

def add_imp_trow_v2(hd, size, data):
	(typ, off) = rdata(data, 0, '>H')
	typ_map = {0xfffe: 'table', 0xff81: 'list'}
	typ_str = get_or_default(typ_map, int(typ), 'unknown')
	add_iter(hd, 'Row type', typ_str, 0, 2, '>H')

	# the rest seems to be pretty much random :-( I've even seen two
	# consecutive builds of the same source produce records with
	# different length...

imp_ids = {
	'imp_anct' : add_imp_anct,
	'imp_anct_tag' : add_imp_anct_tag,
	'imp_bgcl': add_imp_bgcl,
	'imp_directory': add_imp_directory,
	'imp_directory_entry': add_imp_directory_entry,
	'imp_elnk': add_imp_elnk,
	'imp_ests_orphan_pull': add_imp_ests_orphan_pull,
	'imp_ests_widow_push': add_imp_ests_widow_push,
	'imp_fidt': add_imp_fidt,
	'imp_file_header': add_imp_file_header,
	'imp_form': add_imp_form,
	'imp_header': add_imp_header,
	'imp_hrle': add_imp_hrle,
	'imp_hyp2': add_imp_hyp2,
	'imp_imrn': add_imp_imrn,
	'imp_lnks': add_imp_lnks,
	'imp_metadata': add_imp_metadata,
	'imp_mrgn': add_imp_mrgn,
	'imp_page_info_block_h': add_imp_page_info_block_h,
	'imp_page_info_block_i': add_imp_page_info_block_i,
	'imp_page_info_border': add_imp_page_info_border,
	'imp_page_info_geometry': add_imp_page_info_geometry,
	'imp_page_info_image': add_imp_page_info_image,
	'imp_page_info_line': add_imp_page_info_line,
	'imp_page_info_line_index': add_imp_page_info_line_index,
	'imp_page_info_page': add_imp_page_info_page,
	'imp_page_info_page_index': add_imp_page_info_page_index,
	'imp_page_info_page_region': add_imp_page_info_page_region,
	'imp_pcz0': add_imp_pcz0,
	'imp_pcz1_v1': add_imp_pcz1_v1,
	'imp_pcz1_v2': add_imp_pcz1_v2,
	'imp_pinf': add_imp_pinf,
	'imp_ppic': add_imp_ppic,
	'imp_resource_0x64': add_imp_resource_0x64,
	'imp_resource_0x65': add_imp_resource_0x65,
	'imp_resource_0x65_last': add_imp_resource_0x65_last,
	'imp_resource_header': add_imp_resource_header,
	'imp_resource_index_v1': add_imp_resource_index_v1,
	'imp_resource_index_v2': add_imp_resource_index_v2,
	'imp_str2': add_imp_str2,
	'imp_strn': add_imp_strn,
	'imp_styl': add_imp_styl,
	'imp_sw_index' : add_imp_sw_index,
	'imp_sw_record' : add_imp_sw_record,
	'imp_tabl': add_imp_tabl,
	'imp_tcel_v1': add_imp_tcel_v1,
	'imp_tcel_v2': add_imp_tcel_v2,
	'imp_text': add_imp_text,
	'imp_trow_v1': add_imp_trow_v1,
	'imp_trow_v2': add_imp_trow_v2,
}

def open(buf, page, parent):
	parser = imp_parser(buf, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
