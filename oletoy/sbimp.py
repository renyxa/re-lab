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
		if typ in imp_resource_types:
			self.parse_resource(filedata, typ, fileiter)
		elif typ == '!!sw':
			self.parse_sw(filedata, typ, fileiter)

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
		elif typ == 'AncT':
			self.parse_anct(data, idx, resiter)
		elif typ == 'BGcl':
			self.parse_bgcl(data, idx, resiter)
		elif typ in ['BPgz', 'BPgZ']:
			self.parse_bpgz(data, idx, resiter, typ == 'BPgZ')
		elif typ == 'BPos':
			self.parse_bpos(data, idx, resiter)
		elif typ == 'eLnk':
			self.parse_elnk(data, idx, resiter)
		elif typ == 'ESts':
			self.parse_ests(data, idx, resiter)
		elif typ in ['HfPz', 'HfPZ']:
			self.parse_hfpz(data, idx, resiter, typ == 'HfPZ')
		elif typ == 'HRle':
			self.parse_hrle(data, idx, resiter)
		elif typ == 'ImRn':
			self.parse_imrn(data, idx, resiter)
		elif typ == 'Lnks':
			self.parse_lnks(data, idx, resiter)
		elif typ == 'Mrgn':
			self.parse_mrgn(data, idx, resiter)
		elif typ in ['Pcz0', 'PcZ0']:
			self.parse_pcz0(data, idx, resiter, typ == 'PcZ0')
		elif typ in ['Pcz1', 'PcZ1']:
			self.parse_pcz1(data, idx, resiter, typ == 'PcZ1')
		elif typ == 'pInf':
			self.parse_pinf(data, idx, resiter)
		elif typ == 'PPic':
			self.parse_ppic(data, idx, resiter)
		elif typ == 'StR2':
			self.parse_str2(data, idx, resiter)
		elif typ == 'StRn':
			self.parse_strn(data, idx, resiter)
		elif typ == 'Styl':
			self.parse_styl(data, idx, resiter)
		elif typ == 'Tabl':
			self.parse_tabl(data, idx, resiter)
		elif typ == 'TCel':
			self.parse_tcel(data, idx, resiter)
		elif typ == 'TRow':
			self.parse_trow(data, idx, resiter)

	def parse_resource_index(self, data, parent):
		index = {}

		off = 0
		i = 0
		entrylen = 12
		if imp_color_mode == 2:
			entrylen = 14

		while off + entrylen <= len(data):
			add_pgiter(self.page, 'Entry %d' % i, 'imp', 'imp_resource_index', data[off:off + entrylen], parent)
			if imp_color_mode == 2:
				(idx, off) = rdata(data, off, '<I')
				(length, off) = rdata(data, off, '<I')
				(start, off) = rdata(data, off, '<I')
			else:
				(idx, off) = rdata(data, off, '>H')
				(length, off) = rdata(data, off, '>I')
				(start, off) = rdata(data, off, '>I')
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
				off = 6
				(window_bits, off) = rdata(resdata, off, '>H')
				(length_bits, off) = rdata(resdata, off, '>H')
				self.window_bits = int(window_bits)
				self.length_bits = int(length_bits)

			elif i == 0x65:
				resiter = add_pgiter(self.page, 'Resource 0x65', 'imp', 0, resdata, parent)
				count = len(resdata) / 10
				recbegin = 0
				for j in range(count):
					recid = 'imp_resource_0x65'
					if j == count - 1:
						recid = 'imp_resource_0x65_last'
						self.text_length = int(read(resdata, recbegin, '>I'))
					recdata = resdata[recbegin:recbegin + 10]
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

	def parse_anct(self, data, index, parent):
		for i in index.keys():
			res = index[i]
			resdata = data[res[0]:res[0] + res[1]]

			if i == 0 or i == 1:
				(count, off) = rdata(resdata, 0, '>I')
				view = 'large'
				if i == 1:
					view = 'small'
				tagiter = add_pgiter(self.page, 'Tags for %s view' % view,  'imp', 'imp_anct', resdata, parent)
				if int(count) > 0:
					for j in range(int(count)):
						add_pgiter(self.page, 'Tag %d' % j, 'imp', 'imp_anct_tag', resdata[off:off + 8], parent)
						off += 8

	def parse_bgcl(self, data, index, parent):
		pass

	def parse_bpgz(self, data, index, parent, large):
		pass

	def parse_bpos(self, data, index, parent):
		pass

	def parse_elnk(self, data, index, parent):
		pass

	def parse_ests(self, data, index, parent):
		pass

	def parse_hfpz(self, data, index, parent, large):
		pass

	def parse_hrle(self, data, index, parent):
		pass

	def parse_imrn(self, data, index, parent):
		pass

	def parse_lnks(self, data, index, parent):
		pass

	def parse_mrgn(self, data, index, parent):
		pass

	def parse_pcz0(self, data, index, parent, large):
		pass

	def parse_pcz1(self, data, index, parent, large):
		pass

	def parse_pinf(self, data, index, parent):
		pass

	def parse_ppic(self, data, index, parent):
		pass

	def parse_str2(self, data, index, parent):
		pass

	def parse_strn(self, data, index, parent):
		pass

	def parse_styl(self, data, index, parent):
		pass

	def parse_tabl(self, data, index, parent):
		pass

	def parse_tcel(self, data, index, parent):
		pass

	def parse_trow(self, data, index, parent):
		pass

	def parse_text(self, data, n, parent):
		fileiter = ins_pgiter(self.page, 'File %d (type Text)' % n, 'imp', 0, data, parent, n)
		add_pgiter(self.page, 'Header', 'imp', 'imp_file_header', data[0:20], fileiter)

		filedata = data[20:len(data)]
		if not self.compressed:
			add_pgiter(self.page, 'Text', 'imp', 0, filedata, fileiter)
		else:
			textiter = add_pgiter(self.page, 'Compressed text', 'imp', 0, filedata, fileiter)
			uncompressed = lzss_decompress(filedata, True, self.window_bits, self.length_bits, self.text_length)
			add_pgiter(self.page, 'Text', 'imp', 0, uncompressed, textiter)

def add_imp_anct(hd, size, data):
	count = read(data, 0, '>I')
	add_iter(hd, 'Count of anchor tags', count, 0, 4, '>I')

def add_imp_anct_tag(hd, size, data):
	(offset, off) = rdata(data, 0, '>I')
	add_iter(hd, 'Offset to anchor tag in text', offset, 0, 4, '>I')
	(page, off) = rdata(data, off, '>I')
	add_iter(hd, 'Page number', page, off - 4, 4, '>I')

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

imp_zoom_states = ('Both', 'Small', 'Large')
imp_color_modes = ('Unknown', 'Color VGA', 'Grayscale Half-VGA')

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
	zoom = int(flags) & 0x3
	flags_str = 'zoom = %s, color mode = %s' % (imp_zoom_states[zoom], imp_color_modes[color_mode])
	add_iter(hd, 'Flags', flags_str, off - 4, 4, '>I')
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

def get_index_formats():
	# I assume this crap is there as a workaround for a buggy device,
	# not because someone thought it would be a good idea...
	if imp_color_mode == 2:
		return ('<I', '<I')
	return ('>I', '>H')

def add_imp_resource_index(hd, size, data):
	(fmt, idfmt) = get_index_formats()

	(idx, off) = rdata(data, 0, idfmt)
	add_iter(hd, 'Resource ID', '0x%x' % int(idx), 0, off, idfmt)
	(length, off) = rdata(data, off, fmt)
	add_iter(hd, 'Record length', length, off - 4, 4, fmt)
	(start, off) = rdata(data, off, fmt)
	add_iter(hd, 'Offset to start of record', start, off - 4, 4, fmt)

def add_imp_sw_index(hd, size, data):
	(fmt, idfmt) = get_index_formats()

	(seq, off) = rdata(data, 0, fmt)
	add_iter(hd, 'Sequence number', seq, 0, seq, fmt)
	(length, off) = rdata(data, off, fmt)
	add_iter(hd, 'Length of item', length, off - 4, 4, fmt)
	(offset, off) = rdata(data, off, fmt)
	add_iter(hd, 'Offset to beginning of item', offset, off - 4, 4, fmt)
	off += 2
	(typ, off) = rdata(data, off, '4s')
	add_iter(hd, 'File type', typ, off - 4, 4, '4s')

def add_imp_sw_record(hd, size, data):
	pass

imp_ids = {
	'imp_anct' : add_imp_anct,
	'imp_anct_tag' : add_imp_anct_tag,
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
	'imp_sw_index' : add_imp_sw_index,
	'imp_sw_record' : add_imp_sw_record,
}

def open(buf, page, parent):
	parser = imp_parser(buf, page, parent)
	parser.parse()

# vim: set ft=python ts=4 sw=4 noet:
