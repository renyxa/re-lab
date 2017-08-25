# Copyright (C) 2017 David Tardon (dtardon@redhat.com)
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

from utils import *

LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'

def little_endian(fmt=''):
	return LITTLE_ENDIAN + fmt

def big_endian(fmt=''):
	return BIG_ENDIAN + fmt

def rsfloat(data, off, fmt):
	(num, off) = rdata(data, off, fmt('H'))
	f = num / float(0x10000)
	return f, off

def rfract(data, off, fmt):
	if fmt() == LITTLE_ENDIAN:
		(fpart, off) = rsfloat(data, off, fmt)
		(ipart, off) = rdata(data, off, fmt('h'))
	else:
		(ipart, off) = rdata(data, off, fmt('h'))
		(fpart, off) = rsfloat(data, off, fmt)
	return (ipart + fpart, off)

def read_c_str(data, offset):
	off = data.find('\0', offset)
	s = data[offset:off]
	off += 1
	return s, off

def read_pascal_str(data, offset):
	(length, off) = rdata(data, offset, 'B')
	s = data[off:off + length]
	off += length
	return s, off

def dim2in(dim):
	return dim / 72.0

def style2txt(value):
	if value == 0:
		return 'No style'
	else:
		return value


def qxpbflag2txt(flag, data, fmt):
	def reverse_bits(x):
		return int(bin(x)[2:].zfill(8)[::-1], 2)
	return bflag2txt(flag if fmt() == LITTLE_ENDIAN else reverse_bits(flag), data)

def deobfuscate(value, seed, n):
	assert n in [1, 2]
	if n == 1:
		assert value >> 8 == 0
		mask = 0xff
	else:
		assert value >> 16 == 0
		mask = 0xffff
	return (((value + seed) & 0xffff) - (((value & seed) << 1) & 0xffff) + (1 << 16)) & mask

VERSION_1 = 0x20
VERSION_3_1_M = 0x39
VERSION_3_1 = 0x3e
VERSION_3_3 = 0x3f
VERSION_4 = 0x41
VERSION_6 = 0x43

class HexDumpSave:
	def __init__(self, offset):
		self.model = self.Model(offset)

	class Model:
		def __init__(self, offset):
			self.offset = offset
			self.values = []

		def append(self, parent, dummy=None):
			self.values.append([{}, parent])
			return len(self.values) - 1

		def set(self, iter, *args):
			values = self.values[iter][0]
			i = 0
			while i < len(args):
				values[args[i]] = args[i + 1] - self.offset if args[i] == 2 else args[i + 1]
				i += 2

	def show(self, hd):
		iters = [None] * len(self.model.values)
		for i in range(0, len(self.model.values)):
			(vs, p) = self.model.values[i]
			parent = None if p == None else iters[p]
			iter = hd.model.append(parent, None)
			iters[i] = iter
			args = []
			for (idx, val) in vs.items():
				args.append(idx)
				args.append(val)
			hd.model.set(iter, *args)

class Header:
	def __init__(self, encoding):
		self.encoding = encoding
		self.seed = 0
		self.inc = 0
		self.pages = 0
		self.masters = 0
		self.pictures = 0

obj_flags_map = {
	1: 'no color?',
	0x4: 'lock',
	0x10: 'suppress printout',
	0x20: 'no item runaround?',
	0x40: 'user-edited runaround path?', # used for picture in qxp33
}

def add_length(hd, size, data, fmt, version, offset, name="Length"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, name, length, off - 4, 4, fmt('I'))
	return off

def add_pcstr4(hd, data, offset, fmt, name="Name"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, '%s length' % name, length, off - 4, 4, fmt('I'))
	(pstring, off) = rdata(data, off, '%ds' % length)
	string = pstring[0:pstring.find('\0')]
	add_iter(hd, name, string, off - length, length, '%ds' % length)
	return string, off

def add_pascal_str(hd, data, offset, name="Name"):
	(string, off) = read_pascal_str(data, offset)
	length = off - offset
	add_iter(hd, name, string, offset, length, '%ds' % length)
	return string, off

def add_page_header(hd, size, data, offset, fmt):
	(settings_length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, 'Page settings length', settings_length, off - 4, 4, fmt('I'))
	(settings_blocks_count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Settings blocks count', settings_blocks_count, off - 2, 2, fmt('H'))
	(idx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Index?', idx, off - 1, 1, fmt('B'))
	(cidx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Creation index', cidx, off - 1, 1, fmt('B'))
	settings_block_size = (settings_length - 4) / settings_blocks_count
	return off, settings_block_size, settings_blocks_count

def add_page_bbox(hd, size, data, offset, fmt, parent=None):
	off = add_dim(hd, size, data, offset, fmt, 'Top offset', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Left offset', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Bottom offset', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Right offset', parent=parent)
	return off

def add_margins(hd, size, data, offset, fmt, parent=None):
	off = add_dim(hd, size, data, offset, fmt, 'Top margin', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Bottom margin', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Left margin', parent=parent)
	off = add_dim(hd, size, data, off, fmt, 'Right margin', parent=parent)
	return off

def add_page_columns(hd, size, data, offset, fmt, parent=None):
	(col, off) = rdata(data, offset, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'), parent=parent)
	off += 2
	off = add_dim(hd, size, data, off, fmt, 'Gutter width', parent=parent)
	return off

def add_section(hd, data, offset, fmt, version, parent=None):
	off = offset
	end = data.find('\0', off, off + 4)
	if end == -1:
		end = off + 4
	prefix = data[off:end]
	add_iter(hd, 'Page number prefix', prefix, off, 4, '4s', parent=parent)
	off += 4
	(number, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Page number', number, off - 2, 2, fmt('H'), parent=parent)
	format_map = {
		1: 'Numeric',
		2: 'Uppercase Roman',
		3: 'Lowercase Roman',
		4: 'Uppercase alphabetic',
		5: 'Lowercase alphabetic',
	}
	(format, off) = rdata(data, off, fmt('b'))
	add_iter(hd, 'Numbering format', key2txt(abs(format), format_map), off - 1, 1, fmt('b'), parent=parent)
	if parent:
		prefix_str = '' if prefix == '' else '%s / ' % prefix
		hd.model.set(parent, 1, '%s%d / %s' % (prefix_str, number, key2txt(abs(format), format_map)))
	return number, format > 0, off

def add_page_settings(hd, size, data, offset, fmt, version, parent=None):
	off = offset
	off = add_page_bbox(hd, off + 16, data, off, fmt, parent)
	(id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'ID?', hex(id), off - 4, 4, fmt('I'), parent=parent)
	off += 4
	(master_ind, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Master page index', '' if master_ind == 0xffff else master_ind, off - 2, 2, fmt('H'), parent=parent)
	off += 2
	(number, section_start, off) = add_section(hd, data, off, fmt, version, parent)
	off += 1
	off = add_margins(hd, off + 16, data, off, fmt, parent)
	off = add_page_columns(hd, off + 8, data, off, fmt, parent)
	if version >= VERSION_4:
		off += 4
	return off

def add_record(hd, size, data, fmt, version):
	add_length(hd, size, data, fmt, version, 0)

def add_dim(hd, size, data, offset, fmt, name, parent=None):
	(dim, off) = rfract(data, offset, fmt)
	sz = off - offset
	dim_str = '%.2f pt / %.2f in' % (dim, dim2in(dim))
	add_iter(hd, name, dim_str, off - sz, sz, '%ds' % sz, parent=parent)
	return off

def add_sfloat_perc(hd, data, offset, fmt, name, parent=None):
	(f, off) = rsfloat(data, offset, fmt)
	perc = f * 100
	add_iter(hd, name, '%.1f%%' % perc, off - 2, 2, fmt('H'), parent=parent)
	return off

def add_fract_perc(hd, data, offset, fmt, name, parent=None):
	(f, off) = rfract(data, offset, fmt)
	add_iter(hd, name, '%.2f%%' % (f * 100), off - 4, 4, fmt('i'), parent=parent)
	return off

def add_fonts(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of fonts', count, off - 2, 2, fmt('H'))
	for i in range(0, count):
		start = off
		font_iter = add_iter(hd, 'Font %d' % i, '', off, 2, '2s')
		(index, off) = rdata(data, off, fmt('h'))
		add_iter(hd, 'Index in font list', index, off - 2, 2, fmt('h'), parent=font_iter)
		if version >= VERSION_4:
			off += 2
		rstr = read_c_str if fmt() == LITTLE_ENDIAN else read_pascal_str
		(name, off) = rstr(data, off)
		add_iter(hd, 'Name', name, off - len(name) - 1, len(name) + 1, '%ds' % (len(name) + 1), parent=font_iter)
		(full_name, off) = rstr(data, off)
		add_iter(hd, 'Full name', full_name, off - len(full_name) - 1, len(full_name) + 1, '%ds' % (len(full_name) + 1), parent=font_iter)
		hd.model.set(font_iter, 1, "%d, %s" % (index, name), 3, off - start, 4, '%ds' % (off - start))

def add_physical_fonts(hd, size, data, fmt, version):
	def add_name(off, title, parent):
		(name, off) = rcstr(data, off)
		sz = len(name) + 1
		add_iter(hd, title, name, off - sz, sz, '%ds' % sz, parent=parent)
		return off
	off = add_length(hd, size, data, fmt, version, 0)
	off += 12
	i = 0
	while off < size:
		start = off
		font_iter = add_iter(hd, 'Font %d' % i, '', off, 2, '2s')
		(index, off) = rdata(data, off, fmt('h'))
		add_iter(hd, 'Index in font list', index, off - 2, 2, fmt('h'), parent=font_iter)
		off += 12
		off = add_name(off, 'Bold name', font_iter)
		off = add_name(off, 'Italic name', font_iter)
		off = add_name(off, 'Bold italic name', font_iter)
		if version >= VERSION_4:
			off += 17
		i += 1
		hd.model.set(font_iter, 1, "%d" % index, 3, off - start, 4, '%ds' % (off - start))

def add_saved(hd, size, data, saved, dummy):
	saved.show(hd)

def add_header_common(hd, size, data, fmt):
	off = 2
	proc_map = {'II': 'Intel', 'MM': 'Motorola'}
	(proc, off) = rdata(data, off, '2s')
	add_iter(hd, 'Processor', key2txt(proc, proc_map), off - 2, 2, '2s')
	(sig, off) = rdata(data, off, '3s')
	add_iter(hd, 'Signature', sig, off - 3, 3, '3s')
	lang_map = {
		0x33: ('English', {'II': 'cp1252', 'MM': 'macroman'}),
		0x61: ('Korean', {'II': 'cp949'}), # TODO: the cp is just an assumption
	}
	(lang, off) = rdata(data, off, fmt('B'))
	(language, encoding_map) = key2txt(lang, lang_map, ('Unknown', {}))
	add_iter(hd, 'Language', language, off - 1, 1, fmt('B'))
	encoding = key2txt(proc, encoding_map, None)
	if not encoding:
		encoding = key2txt(proc, lang_map[0x33][1], None) # Use English as default
	assert encoding
	version_map = {
		0x39: '3.1 Mac',
		0x3e: '3.1',
		0x3f: '3.3',
		0x41: '4',
		0x42: '5',
		0x43: '6',
		0x44: '7?',
		0x45: '8',
	}
	(ver, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, fmt('H'))
	(ver, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 2, 2, fmt('H'))
	return (Header(encoding), off)

def add_tab(hd, size, data, offset, fmt, version, encoding, parent=None):
	type_map = {0: 'left', 1: 'center', 2: 'right', 3: 'align'}
	(typ, off) = rdata(data, offset, fmt('B'))
	add_iter(hd, 'Type', key2txt(typ, type_map), off - 1, 1, fmt('B'), parent=parent)
	subtype_map = {1: 'decimal', 2: 'comma'}
	(subtype, off) = rdata(data, off, fmt('B'))
	if subtype_map.has_key(subtype):
		add_iter(hd, 'Subtype', key2txt(subtype, subtype_map), off - 1, 1, fmt('B'), parent=parent)
	else:
		align_char = unicode(chr(subtype), encoding)
		add_iter(hd, 'Align at char', align_char, off - 1, 1, '1s', parent=parent)
	(fill, off) = rdata(data, off, fmt('H'))
	fill_char = chr(fill & 0xff)
	upper = fill >> 8
	if upper != 0:
		fill_char = chr(upper) + fill_char
	fill_char = unicode(fill_char, encoding)
	add_iter(hd, 'Fill char', fill_char, off - 2, 2, fmt('H'), parent=parent)
	(pos, off) = rdata(data, off, fmt('i'))
	if pos == -1:
		add_iter(hd, 'Position', 'not defined', off - 4, 4, fmt('i'), parent=parent)
	else:
		off = add_dim(hd, size, data, off - 4, fmt, 'Position', parent)
	if parent:
		if pos == -1:
			hd.model.set(parent, 1, 'not defined')
		else:
			if typ == 3:
				subtype_str = ' @ %s' % (key2txt(subtype, subtype_map) if subtype_map.has_key(subtype) else "'%s'" % align_char)
			else:
				subtype_str = ''
			pos = rfract(data, off - 4, fmt)[0]
			pos_str = '%.2f pt / %.2f in' % (pos, dim2in(pos))
			hd.model.set(parent, 1, "%s%s / '%s' / %s"  % (key2txt(typ, type_map), subtype_str, fill_char, pos_str))
	return off

def add_file_info(hd, data, offset, fmt):
	off = offset
	(length, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'File info data length', length, off - 4, 4, fmt('I'))
	return off + length

def add_view_scale(hd, data, offset, fmt, version):
	off = offset
	off = add_fract_perc(hd, data, off, fmt, 'View scale maximum')
	off = add_fract_perc(hd, data, off, fmt, 'View scale minimum')
	off = add_fract_perc(hd, data, off, fmt, 'View scale increment')
	return off

def add_hj_common(hd, size, data, offset, fmt, version):
	off = offset + 4
	(sm, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Smallest word', sm, off - 1, 1, fmt('B'))
	(min_before, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Minimum before', min_before, off - 1, 1, fmt('B'))
	(min_after, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Minimum after', min_after, off - 1, 1, fmt('B'))
	(hyprow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Hyphens in a row', 'unlimited' if hyprow == 0 else hyprow, off - 1, 1, fmt('B'))
	off = add_dim(hd, size, data, off, fmt, 'Hyphenation zone')
	justify_single_map = {0: 'Disabled', 0x80: 'Enabled'}
	(justify_single, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Don't justify single word", key2txt(justify_single, justify_single_map), off - 1, 1, fmt('B'))
	off += 1
	autohyp_map = {0: 'Disabled', 1: 'Enabled'}
	(autohyp, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Auto hyphenation', key2txt(autohyp, autohyp_map), off - 1, 1, fmt('B'))
	breakcap_map = {0: 'Disabled', 1: 'Enabled'}
	(breakcap, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Don't break capitalized words", key2txt(breakcap, breakcap_map), off - 1, 1, fmt('B'))
	def space2txt(val):
		return '%.2d%%' % (100 * val + 100)
	(min, off) = rfract(data, off, fmt)
	add_iter(hd, 'Space minimum', space2txt(min), off - 4, 4, '4s')
	off = add_fract_perc(hd, data, off, fmt, 'Char minimum')
	(opt, off) = rfract(data, off, fmt)
	add_iter(hd, 'Space optimum', space2txt(opt), off - 4, 4, '4s')
	off = add_fract_perc(hd, data, off, fmt, 'Char optimum')
	(max, off) = rfract(data, off, fmt)
	add_iter(hd, 'Space maximum', space2txt(max), off - 4, 4, '4s')
	off = add_fract_perc(hd, data, off, fmt, 'Char maximum')
	off = add_dim(hd, size, data, off, fmt, 'Flush zone')
	return off

def add_kerning_spec(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	i = 1
	while off < size:
		off += 2
		(id, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'ID %d' % i, hex(id), off - 4, 4, fmt('I'))
		off += 4
		i += 1

def add_kerning(hd, size, data, fmt, version, encoding):
	off = add_length(hd, size, data, fmt, version, 0)
	off += 4
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '# of pairs', count, off - 2, 2, fmt('H'))
	for i in range(1, count + 1):
		(pair, off) = rdata(data, off, '2s')
		add_iter(hd, 'Pair %d' % i, unicode(pair, encoding), off - 2, 2, '2s')
		(kerning, off) = rdata(data, off, fmt('h'))
		add_iter(hd, 'Kerning %d' % i, kerning, off - 2, 2, fmt('h'))

def add_hyph_exceptions(hd, size, data, fmt, version, encoding):
	def hyphenate(word, pattern):
		w = ''
		mask = 1
		for c in word:
			w += c
			mask <<= 1
			if mask & pattern != 0:
				w += '-'
		return w
	off = add_length(hd, size, data, fmt, version, 0)
	start = off
	(count, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of words', count, off - 4, 4, fmt('I'))
	off_fmt = fmt('I') if version >= VERSION_4 else fmt('H')
	off_sz = struct.calcsize(off_fmt)
	blocks = []
	i = 1
	while off < start + 4 + 28 * off_sz:
		(block, off) = rdata(data, off, off_fmt)
		if block == 0:
			break
		add_iter(hd, 'Offset to block %d' % i, block, off - off_sz, off_sz, off_fmt)
		blocks.append(start + block)
		i += 1
	blocks.append(size)
	for (i, (block, next_block)) in enumerate(zip(blocks[0:-1], blocks[1:])):
		blockiter = add_iter(hd, 'Block %d' % (i + 1), '', block, next_block - block, '%ds' % (next_block - block))
		off = block + 1
		if version >= VERSION_4:
			off += 2
		words = []
		i = 1
		while True:
			(word, off) = rdata(data, off, off_fmt)
			if word == 0:
				break
			add_iter(hd, 'Offset to word %d' % i, word, off - off_sz, off_sz, off_fmt, parent=blockiter)
			words.append(block + word)
			i += 1
		words.append(next_block)
		for (i, (word, next_word)) in enumerate(zip(words[0:-1], words[1:])):
			worditer = add_iter(hd, 'Word %d' % (i + 1), '', word, next_word - word, '%ds' % (next_word - word), parent=blockiter)
			off = word
			(text, off) = rdata(data, off, '%ds' % (next_word - word - 4))
			add_iter(hd, 'Word', text, word, off - word, '%ds' % (off - word), parent=worditer)
			(hyphens, off) = rdata(data, off, fmt('I'))
			add_iter(hd, 'Hyphenation pattern', hex(hyphens & 0x7fff), off - 4, 4, fmt('I'), parent=worditer)
			hd.model.set(worditer, 1, hyphenate(text, hyphens & 0x7fff))

def parse_tracking_index(page, data, offset, parent, fmt, version):
	hd = HexDumpSave(offset)
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, 'Length', length, off - 4, 4, fmt('I'))
	add_pgiter(page, 'Tracking & kerning index', 'qxp', ('tracking_index', hd), data[off - 4:off + length], parent)
	off += 158
	fonts = []
	i = 1
	while off < offset + length + 4:
		start = off
		(font, off) = rcstr(data, off)
		add_iter(hd, 'Font name %d' % i, font, start, off - start, '%ds' % (off - start))
		fonts.append(font)
		i += 1
	return fonts, off

def parse_tracking(page, data, offset, parent, fmt, version, fonts):
	hd = HexDumpSave(offset)
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, 'Length', length, off - 4, 4, fmt('I'))
	add_pgiter(page, 'Tracking & kerning', 'qxp', ('tracking', hd), data[off - 4:off + length], parent)
	kernings = []
	for (i, font) in enumerate(fonts):
		fontiter = add_iter(hd, '[%d] %s' % (i + 1, font), '', off, 24, '24s')
		for j in range(1, 5):
			(size, off) = rdata(data, off, fmt('B'))
			add_iter(hd, 'Point %d size' % j, size, off - 1, 1, fmt('B'), parent=fontiter)
		for j in range(1, 5):
			(tracking, off) = rdata(data, off, fmt('b'))
			add_iter(hd, 'Point %d tracking' % j, tracking, off - 1, 1, fmt('b'), parent=fontiter)
		off += 8
		(kid, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Kerning ID', kid, off - 4, off, fmt('I'), parent=fontiter)
		kernings.append(kid)
		off += 4
	return (kernings, off)

def parse_kerning_spec(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, 'Kerning spec', 'qxp', ('kerning_spec', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_kerning(page, data, offset, parent, fmt, version, encoding, index, font):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, '[%d] Kerning (%s)' % (index, font), 'qxp', ('kerning', fmt, version, encoding), data[off - 4:off + length], parent)
	return off + length

def parse_hyph_exceptions(page, data, offset, parent, fmt, version, encoding):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Hyphenation exceptions', 'qxp',
			('hyph_exceptions', fmt, version, encoding), data[off - 4:off + length], parent)
	return offset + 4 + length

char_format_map = {
	0x1: 'bold',
	0x2: 'italic',
	0x4: 'underline',
	0x8: 'outline',
	0x10: 'shadow',
	0x20: 'superscript',
	0x40: 'subscript',
	0x100: 'superior',
	0x200: 'strike thru',
	0x400: 'all caps',
	0x800: 'small caps',
	0x1000: 'word underline',
}

align_map = {0: 'left', 1: 'center', 2: 'right', 3: 'justified', 4: 'forced'}

vertical_align_map = {0: 'Top', 1: 'Center', 2: 'Bottom', 3: 'Justified'}

# first baseline minimum:
# 0x20: 'Ascent', 0x28: 'Cap height', 0x38: 'Cap + Accent'
text_flags_map = {
	0x08: 'cap height',
	0x10: 'accent',
	0x20: 'ascent',
	0x40: 'run text around all sides',
}

# if 'keep lines together' is enabled, then 'all lines' is used (or Start/End if 'all lines' disabled)
para_flags_map = {
	0x1: 'keep with next',
	0x2: 'lock to baseline grid',
	0x4: 'incremental leading', # +42 pt, -42 pt
	0x8: 'keep lines together',
	0x10: 'all lines',
	0x20: 'rule above',
	0x40: 'rule below',
	0x80: 'r. a. length: text',
	0x100: 'r. b. length: text',
}

picture_flags_map = {
	0x4: 'suppress printout',
}

gradient_type_map = {
	0x10: 'Linear',
	0x18: 'Mid-Linear',
	0x19: 'Rectangular',
	0x1a: 'Diamond',
	0x1b: 'Circular',
	0x1c: 'Full Circular',
}

line_style_map = {
	0: 'Solid',
	1: 'Dotted',
	2: 'Dotted 2',
	3: 'Dash Dot',
	4: 'All Dots',
	0x80: 'Double',
	0x81: 'Thin-Thick',
	0x82: 'Thick-Thin',
	0x83: 'Thin-Thick-Thin',
	0x84: 'Thick-Thin-Thick',
	0x85: 'Triple'
}

frame_style_map = {
	0x80: 'Solid',
	0x81: 'Double',
	0x82: 'Thin-Thick',
	0x83: 'Thick-Thin',
	0x84: 'Thin-Thick-Thin',
	0x85: 'Thick-Thin-Thick',
	0x86: 'Triple',
	0x5: 'Yearbook',
	0xa: 'Certificate',
	0xd: 'Coupon',
	0xf: 'Deco Shadow',
	0x10: 'Deco Plain',
	0x11: 'Maze',
	0x12: 'Ornate',
	0x13: 'Op Art1',
	0x14: 'Op Art2'
}

arrow_map = {
	0: 'None',
	1: 'Right',
	2: 'Left',
	3: 'Right with tail',
	4: 'Left with tail',
	5: 'Double-sided',
}

page_ins_map = {
	0: 'Off',
	1: 'At end of story',
	2: 'At end of section',
	3: 'At end of document',
}

measure_map = {
	0: 'Inches',
	1: 'Millimeters',
	2: 'Picas / Inches',
	3: 'Picas',
	4: 'Points',
	5: 'Inches Decimal',
	6: 'Ciceros',
	7: 'Centimeters',
	10: 'Agates',
}

framing_map = {
	0: 'Outside',
	1: 'Inside',
}

ids = {
	'hyph_exceptions': add_hyph_exceptions,
	'kerning': add_kerning,
	'kerning_spec': add_kerning_spec,
	'tracking': add_saved,
	'tracking_index': add_saved,
}

if __name__ == '__main__':
	def test_deobfuscate(seed, value, n, expected):
		assert deobfuscate(value, seed, n) == expected

	test_deobfuscate(0, 0, 1, 0)
	test_deobfuscate(0xa132, 0x31, 1, 0x3)
	test_deobfuscate(0xa132, 0xa133, 2, 0x1)
	test_deobfuscate(0x7236, 0x35, 1, 0x3)
	test_deobfuscate(0x7236, 0x34, 1, 0x2)

# vim: set ft=python sts=4 sw=4 noet:
