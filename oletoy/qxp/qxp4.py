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

import copy
import traceback
from collections import OrderedDict, namedtuple
from utils import *
from qxp import *

box_flags_map = {
	0x80: 'h. flip',
	0x100: 'v. flip',
}

shape_types_map = {
	1: 'Line',
	2: 'Orthogonal line',
	4: 'Bezier line',
	5: 'Rectangle',
	6: 'Rounded rectangle',
	7: 'Concave rectangle',
	8: 'Beveled rectangle',
	9: 'Oval',
	11: 'Bezier',
}

content_type_map = {
	0: 'None',
	2: 'Objects?',
	3: 'Text',
	4: 'Picture'
}

frame_bitmap_style_map = {
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

dash_stripe_type_map = {
	0: 'Dash',
	1: 'Stripe'
}

dash_unit_map = {
	0: 'Points',
	1: 'Times width'
}

miter_map = {
	0: 'Miter',
	1: 'Round',
	2: 'Bevel'
}

endcap_map = {
	0: 'Butt',
	1: 'Round',
	2: 'Protecting rect',
	3: 'Stretch to corners'
}

text_path_align_map = {
	0: 'Ascent',
	1: 'Center',
	2: 'Baseline',
	3: 'Descent'
}

text_path_line_align_map = {
	0: 'Top',
	1: 'Center',
	2: 'Bottom'
}

color_flags_map = {
	0x2: 'disable spot color',
	0x4: 'read-only',
	0x8: 'all plates', # set for Registration color
	0x40: 'template?', # set for some strange empty blocks
}

halftone_map = {
	0: 'Process Black',
	1: 'Process Cyan',
	2: 'Process Magenta',
	3: 'Process Yellow',
	4: 'Process Black'
}

def idx2txt(value):
	if value == 0xffff:
		return 'none'
	else:
		return value

class ObfuscationContext:
	def __init__(self, seed, inc):
		assert seed & 0xffff == seed
		assert inc & 0xffff == inc
		self.seed = seed
		self.inc = inc

	def next(self, block):
		self.seed = (self.seed + self.inc) & 0xffff
		self.inc = self._shift(self.inc, block & 0xf)

	def next_rev(self):
		self.seed = (self.seed + 0xffff - self.inc) & 0xffff

	def next_shift(self, shift):
		self.seed = self._shift(self.seed, shift)

	def _shift(self, value, shift):
		# This is a modified rotation. The lower bits in the old value
		# are moved into the higher bits in the new value, with the
		# following modifications:
		# 1. the higher bit of the old value is added
		# 2. all bits higher than the lowest 1 are filled with 1, e.g.,
		#	 0b0010 changes into 0b1110.
		mask = 0xffff >> (16 - shift)
		def fill(val):
			r = shift
			v = val
			# find the lowest '1'
			while v & 1 == 0 and r > 0:
				v >>= 1
				r -= 1
			s = shift - r
			m = (0xffff >> s) << s
			return (val | m) & mask
		highinit = value & mask
		high = fill(highinit | (value >> 15)) << (16 - shift)
		return high | (value >> shift)

	def deobfuscate(self, value, n):
		return deobfuscate(value, self.seed, n)

	def tip(self):
		return 'seed: %x / inc: %x' % (self.seed, self.inc)

def _read_name(data, fmt, offset=0):
	(n, off) = rdata(data, offset, '64s')
	return n[0:n.find('\0')] if fmt() == LITTLE_ENDIAN else read_pascal_str(data, offset)[0]

def handle_para_style(page, data, parent, fmt, version, index):
	name = _read_name(data, fmt)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('para_style', fmt, version), data, parent)

def handle_char_style(page, data, parent, fmt, version, index):
	name = _read_name(data, fmt)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('char_style', fmt, version), data, parent)

def handle_hj(page, data, parent, fmt, version, index):
	name = _read_name(data, fmt, 0x30)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('hj', fmt, version), data, parent)

def handle_dash_stripe(page, data, parent, fmt, version, index):
	(id, _) = rdata(data, 0xa8, fmt('H'))
	name = _read_name(data, fmt, 0xb0)
	add_pgiter(page, '[%d] %s' % (id, name), 'qxp4', ('dash_stripe', fmt, version), data, parent)

def handle_list(page, data, parent, fmt, version, index):
	name = _read_name(data, fmt)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('list', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp4', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp4', ('para_format', fmt, version), data, parent)

def _parse_list(page, data, offset, end, parent, fmt, version, handler, size, init=0):
	i = init
	off = offset
	while off < end:
		handler(page, data[off:off + size], parent, fmt, version, i)
		off += size
		i += 1
	return off

def parse_record(page, data, offset, parent, fmt, version, name):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, name, 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_fonts(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, 'Fonts', 'qxp4', ('fonts', fmt, version), data[off - 4:off + length], parent)
	return off + length

def parse_physical_fonts(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, 'Physical fonts', 'qxp4', ('physical_fonts', fmt, version), data[off - 4:off + length], parent)
	return off + length

class ColorBlock:
	def __init__(self, start, padding=0, is_unused=False, name='Block'):
		self.length = 0
		self.start = start
		self.padding = padding
		self.is_unused = is_unused
		self.name = name

ColorsHeader = namedtuple('ColorsHeader', ['first_block_ind', 'last_block_ind'])

def parse_color_block_spec(hd, data, offset, record_offset, fmt, name):
	off = offset
	spec_iter = add_iter(hd, '%s spec' % (name), '', off, 4, '4s')
	(info, off) = rdata(data, off, fmt('I'))
	start = info & 0xFFFFFFF
	padding = (info >> 28) & 0x7
	is_unused = (info >> 31) == 1
	add_iter(hd, 'Start offset', start, off - 4, 4, fmt('I'), parent=spec_iter)
	add_iter(hd, 'Padding length', padding, off - 4, 4, fmt('I'), parent=spec_iter)
	add_iter(hd, 'Start', '', record_offset + start + 4, 1, '1s', parent=spec_iter)
	hd.model.set(spec_iter, 1, '%d, pad. %d%s, %s' % (start, padding, ', unused?' if is_unused else '', hex(info)))
	return ColorBlock(record_offset + start + 4, padding, is_unused, name), off

def add_color_block_ind(hd, data, offset, fmt, name):
	(ind, off) = rdata(data, offset, fmt('H'))
	add_iter(hd, name, 'None (0)' if ind == 0 else ind, off - 2, 2, fmt('H'))
	return ind, off

def parse_colors_header_block(page, data, parent, fmt, version, block):
	off = block.start
	hd = HexDumpSave(off)
	add_pgiter(page, 'Header', 'qxp4', ('colors_header_block', hd), data[off:off + block.length], parent)
	off += 4
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of colors', count, off - 2, 2, fmt('H'))
	off += 10
	(first_block, off) = add_color_block_ind(hd, data, off, fmt, 'Index of first block')
	(last_block, off) = add_color_block_ind(hd, data, off, fmt, 'Index of last block')
	return ColorsHeader(first_block, last_block)

def parse_color_name(page, data, parent, fmt, version, block):
	off = block.start
	hd = HexDumpSave(off)
	add_pgiter(page, 'Name', 'qxp4', ('color_name', hd), data[off:off + block.length], parent)
	off += 4
	name_len = block.length - 4
	(name, off) = rdata(data, off, '%ds' % name_len)
	add_iter(hd, 'Name', name, off - name_len, name_len, '%ds' % name_len)
	return name

def parse_color_data(page, data, parent, fmt, version, block):
	off = block.start
	hd = HexDumpSave(off)
	add_pgiter(page, 'Color data?', 'qxp4', ('color_data', hd), data[off:off + block.length], parent)

def parse_rgb_data(page, data, parent, fmt, version, block):
	off = block.start
	hd = HexDumpSave(off)
	add_pgiter(page, 'RGB', 'qxp4', ('color_rgb', hd), data[off:off + block.length], parent)
	off += 4
	off += 12
	off = add_sfloat_perc(hd, data, off, fmt, 'Red')
	off = add_sfloat_perc(hd, data, off, fmt, 'Green')
	off = add_sfloat_perc(hd, data, off, fmt, 'Blue')

def parse_color(page, data, parent, fmt, version, main_block, blocks):
	off = main_block.start
	hd = HexDumpSave(off)
	iter = add_pgiter(page, 'C', 'qxp4', ('color', hd), data[off:off + main_block.length], parent)
	off += 4
	(prev_block_ind, off) = add_color_block_ind(hd, data, off, fmt, 'Index of prev color main block')
	(next_block_ind, off) = add_color_block_ind(hd, data, off, fmt, 'Index of next color main block')
	off += 4
	(name_block_ind, off) = add_color_block_ind(hd, data, off, fmt, 'Index of name block')
	name = parse_color_name(page, data, iter, fmt, version, blocks[name_block_ind])
	off += 9
	(model, off) = rdata(data, off, '3s')
	add_iter(hd, 'Selected color model', model, off - 3, 3, '3s')
	(data_block_ind, off) = add_color_block_ind(hd, data, off, fmt, 'Index of color data block')
	parse_color_data(page, data, iter, fmt, version, blocks[data_block_ind])
	off += 6
	(id, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'ID', id, off - 2, 2, fmt('H'))
	off += 10
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, color_flags_map), off - 1, 1, fmt('B'))
	off += 3
	(halftone, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Halftone', key2txt(halftone, halftone_map), off - 2, 2, fmt('H'))
	off += 48
	off = add_sfloat_perc(hd, data, off, fmt, 'LAB L')
	off = add_sfloat_perc(hd, data, off, fmt, 'LAB A')
	off = add_sfloat_perc(hd, data, off, fmt, 'LAB B')
	(rgb_block_ind, off) = add_color_block_ind(hd, data, off, fmt, 'Index of RGB data block')
	if rgb_block_ind != 0:
		parse_rgb_data(page, data, iter, fmt, version, blocks[rgb_block_ind])
	# update title
	page.model.set_value(iter, 0, "[%d] %s" % (id, 'Color?' if name == '' else name))
	return next_block_ind

def parse_colors(page, data, offset, parent, fmt, version):
	hd = HexDumpSave(offset)
	(length, off) = rdata(data, offset, fmt('I'))
	iter = add_pgiter(page, 'Colors', 'qxp4', ('colors', hd), data[off - 4:off + length], parent)
	off += 14
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of blocks', count, off - 2, 2, fmt('H'))
	off += 4
	(length, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length?', length, off - 4, 4, fmt('I'))
	(end, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Data end offset?', end, off - 4, 4, fmt('I'))
	off += 8
	blocks = OrderedDict()
	for i in range(1, count + 1):
		block_name = '[%d] %s' % (i, 'Header block' if i == 1 else 'Block')
		(block, off) = parse_color_block_spec(hd, data, off, offset, fmt, block_name)
		blocks[i] = block
	blocks_iter = add_pgiter(page, 'Blocks', 'qxp4', ('color_blocks', fmt, version), data[blocks[1].start:offset + end + 4], iter)
	for i, block in blocks.iteritems():
		next_start = offset + end + 4 if i == count else blocks[i + 1].start
		block.length = next_start - block.start - block.padding
		add_pgiter(page, block.name, 'qxp4', ('color_block', fmt, version), data[block.start:block.start + block.length], blocks_iter)
	header = parse_colors_header_block(page, data, iter, fmt, version, blocks[1])
	curr_block_ind = header.first_block_ind
	while curr_block_ind != 0:
		curr_block_ind = parse_color(page, data, iter, fmt, version, blocks[curr_block_ind], blocks)
	return offset + 4 + length

def parse_para_styles(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	stylesiter = add_pgiter(page, 'Paragraph styles', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	size = 244
	i = 1
	tabs = 0
	while off < offset + length + 4:
		handle_para_style(page, data[off:off + size], stylesiter, fmt, version, i)
		if rdata(data, off + 0x5a, fmt('H'))[0] != 0:
			tabs += 1
		off += size
		i += 1
	return (tabs, off)

def parse_char_styles(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Character styles', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_list(page, data, off, off + length, reciter, fmt, version, handle_char_style, 140, 1)

def parse_hjs(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'H&Js', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_list(page, data, off, off + length, reciter, fmt, version, handle_hj, 112, 0)

def parse_dashes(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Dashes & stripes', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_list(page, data, off, off + length, reciter, fmt, version, handle_dash_stripe, 252, 0)

def parse_lists(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Lists', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_list(page, data, off, off + length, reciter, fmt, version, handle_list, 324, 0)

def parse_index(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	(count, off) = rdata(data, off, fmt('I'))
	add_pgiter(page, 'Index', 'qxp4', ('index', fmt, version), data[off - 8:off - 4 + length], parent)
	return (count, off - 4 + length)

def parse_char_formats(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Character formats', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_list(page, data, off, off + length, reciter, fmt, version, handle_char_format, 64, 0)

def parse_para_formats(page, data, offset, parent, fmt, version):
	(length, off) = rdata(data, offset, fmt('I'))
	reciter = add_pgiter(page, 'Paragraph formats', 'qxp4', ('record', fmt, version), data[off - 4:off + length], parent)
	return _parse_list(page, data, off, off + length, reciter, fmt, version, handle_para_format, 100, 0)

def parse_tabs(page, data, offset, parent, fmt, version, title):
	(length, off) = rdata(data, offset, fmt('I'))
	add_pgiter(page, title, 'qxp4', ('tabs', fmt, version), data[off - 4:off + length], parent)
	return off + length

def _add_tabs_spec(hd, size, data, offset, fmt, version, parent):
	off = offset
	off += 2
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '# of tabs', count, off - 2, 2, fmt('H'), parent=parent)
	if parent:
		hd.model.set(parent, 1, count)
	(id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'ID?', hex(id), off - 4, 4, fmt('I'), parent=parent)
	return off

def parse_tabs_spec(page, data, offset, parent, fmt, version):
	hd = HexDumpSave(offset)
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, 'Length', length, off - 4, 4, fmt('I'))
	size = off + length
	add_pgiter(page, 'Tabs spec', 'qxp4', ('tabs_spec', hd), data[off - 4:size], parent)
	i = 1
	while off < size:
		speciter = add_iter(hd, 'Tabs spec %d' % i, '', off, 8, '8s')
		off = _add_tabs_spec(hd, size, data, off, fmt, version, speciter)
		i += 1
	return (i - 1, off)

class ObjectHeader(object):
	def __init__(self, id, shape, link_id, ole_id, gradient_id, content_index, content_type, content_iter):
		self.linked_text_offset = None
		self.next_linked_index = None
		self.id = id
		self.shape = shape
		self.link_id = link_id
		self.ole_id = ole_id
		self.gradient_id = gradient_id
		self.content_index = content_index
		self.content_type = content_type
		self.content_iter = content_iter

def add_object_header(hd, data, offset, fmt, version, obfctx):
	off = offset

	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', qxpbflag2txt(flags, obj_flags_map, fmt), off - 1, 1, fmt('B'))
	off += 1
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index', color, off - 2, 2, fmt('H'))
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'))
	(idx, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Index/ID?', idx, off - 2, 2, fmt('H'))
	off += 2
	(content, off) = rdata(data, off, fmt('I'))
	content_iter = add_iter(hd, 'Content index', hex(content), off - 4, 4, fmt('I'))
	(rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Rotation angle', '%.2f deg' % rot, off - 4, 4, fmt('i'))
	(skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Skew', '%.2f deg' % skew, off - 4, 4, fmt('i'))
	# Text boxes with the same link ID are linked.
	(link_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Link ID', hex(link_id), off - 4, 4, fmt('I'))
	(ole_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'OLE ID?', hex(ole_id), off - 4, 4, fmt('I'))
	(gradient_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Gradient ID?', hex(gradient_id), off - 4, 4, fmt('I'))
	off += 4
	(flags, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Flags', bflag2txt(flags, box_flags_map), off - 2, 2, fmt('H'))
	(content_type, off) = rdata(data, off, fmt('B'))
	content_type = obfctx.deobfuscate(content_type, 1)
	add_iter(hd, 'Content type', key2txt(content_type, content_type_map), off - 1, 1, fmt('B'), tip=obfctx.tip())
	obfctx.next_shift(content_type)
	content = obfctx.deobfuscate(content & 0xffff, 2)
	hd.model.set(content_iter, 1, hex(content))
	add_tip(hd, content_iter, obfctx.tip())
	(shape, off) = rdata(data, off, fmt('B'))
	shape = obfctx.deobfuscate(shape, 1)
	add_iter(hd, 'Shape type', key2txt(shape, shape_types_map), off - 1, 1, fmt('B'), tip=obfctx.tip())

	return ObjectHeader(idx, shape, link_id, ole_id, gradient_id, content, content_type, content_iter), off

def add_gradient(hd, data, offset, fmt):
	off = offset
	gr_iter = add_iter(hd, 'Gradient', '', off, 40, '%ds' % 40)
	off += 16
	(xt, off) = rdata(data, off, '4s')
	add_iter(hd, 'Extension mark?', 'Cool Blends XTension' if xt == 'QXCB' else xt, off - 4, 4, '4s', parent=gr_iter)
	(typ, off) = rdata(data, off, fmt('H'))
	typ = typ & 0xff
	add_iter(hd, 'Type', key2txt(typ, gradient_type_map), off - 2, 2, fmt('H'), parent=gr_iter)
	off += 4
	(color2, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Second color index', color2, off - 2, 2, fmt('H'), parent=gr_iter)
	(gr_shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (gr_shade * 100), off - 4, 4, fmt('i'), parent=gr_iter)
	(angle, off) = rfract(data, off, fmt)
	add_iter(hd, 'Angle', '%.2f deg' % angle, off - 4, 4, fmt('i'), parent=gr_iter)
	off += 4
	return off

def add_coords(hd, data, offset, fmt):
	off = offset
	off = add_dim(hd, off + 4, data, off, fmt, 'Y1')
	off = add_dim(hd, off + 4, data, off, fmt, 'X1')
	off = add_dim(hd, off + 4, data, off, fmt, 'Y2')
	off = add_dim(hd, off + 4, data, off, fmt, 'X2')
	return off

def add_frame(hd, data, offset, fmt, name='Frame'):
	off = add_dim(hd, offset + 4, data, offset, fmt, '%s width' % name)
	(frame_shade, off) = rfract(data, off, fmt)
	add_iter(hd, '%s shade' % name, '%.2f%%' % (frame_shade * 100), off - 4, 4, fmt('i'))
	(frame_color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '%s color index' % name, frame_color, off - 2, 2, fmt('H'))
	(gap_color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Gap color index', gap_color, off - 2, 2, fmt('H'))
	(gap_shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Gap shade', '%.2f%%' % (gap_shade * 100), off - 4, 4, fmt('i'))
	(arrow, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Arrowheads type', key2txt((arrow >> 2) & 7, arrow_map), off - 1, 1, fmt('B'))
	(bmp_frame, off) = rdata(data, off, fmt('B')) # only for rectangles
	add_iter(hd, 'Is bitmap frame', key2txt(bmp_frame, {0: 'No', 1: 'Yes'}), off - 1, 1, fmt('B'))
	(frame_style, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '%s style' % name, 'D&S index %d' % frame_style if bmp_frame == 0 else key2txt(frame_style, frame_bitmap_style_map), off - 2, 2, fmt('H'))
	return off

def add_runaround(hd, data, offset, fmt, parent=None):
	type_map = {
		0: 'None',
		1: 'Item',
		2: 'Picture bounds',
		5: 'Non-white areas',
		7: 'Same as clipping',
		8: 'Auto image',
	}
	(typ, off) = rdata(data, offset, fmt('B'))
	add_iter(hd, 'Runaround type', key2txt(typ, type_map), off - 1, 1, fmt('B'))
	(edges, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Outside edges only', key2txt(edges, {0: 'Yes', 1: 'No'}), off - 1, 1, fmt('B'))
	(invert, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Invert', key2txt(invert, {0: 'No', 1: 'Yes'}), off - 1, 1, fmt('B'))
	off += 1
	off = add_dim(hd, off + 4, data, off, fmt, 'Noise')
	off = add_dim(hd, off + 4, data, off, fmt, 'Top')
	off = add_dim(hd, off + 4, data, off, fmt, 'Left')
	off = add_dim(hd, off + 4, data, off, fmt, 'Bottom')
	off = add_dim(hd, off + 4, data, off, fmt, 'Right')
	off = add_dim(hd, off + 4, data, off, fmt, 'Smoothness')
	(rid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Runaround-related ID?', hex(rid), off - 4, 4, fmt('i'))
	(restrict, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Restrict to box', key2txt(restrict, {0: 'No', 4: 'Yes'}), off - 1, 1, fmt('B'))
	off += 3
	off = add_fract_perc(hd, data, off, fmt, 'Threshold')
	return off

def add_bezier(hd, data, offset, fmt):
	off = offset
	(bezier_data_length, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier data length', bezier_data_length, off - 4, 4, fmt('I'))
	if bezier_data_length != 0:
		off = add_bezier_data(hd, bezier_data_length, data, off, fmt)
	return off

def add_bezier_data(hd, size, data, offset, fmt):
	off = offset
	bezier_iter = add_iter(hd, 'Bezier data', '', off, size, '%ds' % size)
	off += 2
	(components_count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of components', components_count, off - 2, 2, fmt('H'), parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Box Y1', parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Box X1', parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Box Y2', parent=bezier_iter)
	off = add_dim(hd, off + 4, data, off, fmt, 'Box X2', parent=bezier_iter)
	components_offsets = []
	for i in range(1, components_count + 1):
		(component_offset, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Component %d offset' % i, component_offset, off - 4, 4, fmt('I'), parent=bezier_iter)
		components_offsets.append(component_offset)
	for comp in range(1, components_count + 1):
		off = offset + components_offsets[comp - 1]
		off += 2
		(count, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Component %d number of points' % comp, count, off - 2, 2, fmt('H'), parent=bezier_iter)
		off = add_dim(hd, off + 4, data, off, fmt, 'Component %d Box Y1' % comp, parent=bezier_iter)
		off = add_dim(hd, off + 4, data, off, fmt, 'Component %d Box X1' % comp, parent=bezier_iter)
		off = add_dim(hd, off + 4, data, off, fmt, 'Component %d Box Y2' % comp, parent=bezier_iter)
		off = add_dim(hd, off + 4, data, off, fmt, 'Component %d Box X2' % comp, parent=bezier_iter)
		for i in range(1, count + 1):
			off = add_dim(hd, off + 4, data, off, fmt, 'Component %d Y%d' % (comp, i), parent=bezier_iter)
			off = add_dim(hd, off + 4, data, off, fmt, 'Component %d X%d' % (comp, i), parent=bezier_iter)
	off = offset + size
	return off

def add_linked_text_offset(hd, data, offset, fmt, header):
	off = offset
	hd.model.set(header.content_iter, 0, "Starting block of text chain")
	(toff, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Offset into text', toff, off - 4, 4, fmt('I'))
	if toff > 0:
		hd.model.set(header.content_iter, 0, "Index in linked list?")
	header.linked_text_offset = toff
	return off

def add_next_linked_text_settings(hd, data, offset, fmt, header):
	off = offset
	(next_index, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Next linked list index?', next_index, off - 4, 4, fmt('I'))
	(id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Some link-related ID?', hex(id), off - 4, 4, fmt('I'))
	header.next_linked_index = next_index
	return off

def add_text_settings(hd, data, offset, fmt, header):
	off = offset
	(text_flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Text flags (first baseline minimum, ...)', bflag2txt(text_flags, text_flags_map), off - 1, 1, fmt('B'))
	off += 1
	off = add_dim(hd, off + 4, data, off, fmt, 'Gutter width')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset top')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset left')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset right')
	off = add_dim(hd, off + 4, data, off, fmt, 'Text inset bottom')
	(text_rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Text angle', '%.2f deg' % text_rot, off - 4, 4, fmt('i'))
	(text_skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Text skew', '%.2f deg' % text_skew, off - 4, 4, fmt('i'))
	(col, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of columns', col, off - 1, 1, fmt('B'))
	(vert, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Vertical alignment', key2txt(vert, vertical_align_map), off - 1, 1, fmt('B'))
	off += 2
	off = add_dim(hd, off + 4, data, off, fmt, 'Inter max (for Justified)')
	off = add_dim(hd, off + 4, data, off, fmt, 'First baseline offset')
	return off

def add_text_path_settings(hd, data, offset, fmt, header):
	off = offset
	(skew, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Skew characters', key2txt(skew, {0: 'No', 1: 'Yes'}), off - 1, 1, fmt('B'))
	(rot, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Rotate characters', key2txt(rot, {0: 'No', 1: 'Yes'}), off - 1, 1, fmt('B'))
	(align, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Align text', key2txt(align, text_path_align_map), off - 1, 1, fmt('B'))
	(line_align, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Align with line', key2txt(line_align, text_path_line_align_map), off - 1, 1, fmt('B'))
	return off

def add_picture_settings(hd, data, offset, fmt, header):
	off = offset
	off += 1
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Picture flags', bflag2txt(flags, picture_flags_map), off - 1, 1, fmt('B'))
	off += 22
	(pic_rot, off) = rfract(data, off, fmt)
	add_iter(hd, 'Picture angle', '%.2f deg' % pic_rot, off - 4, 4, fmt('i'))
	(pic_skew, off) = rfract(data, off, fmt)
	add_iter(hd, 'Picture skew', '%.2f deg' % pic_skew, off - 4, 4, fmt('i'))
	off = add_dim(hd, off + 4, data, off, fmt, 'Offset accross')
	off = add_dim(hd, off + 4, data, off, fmt, 'Offset down')
	off = add_fract_perc(hd, data, off, fmt, 'Scale accross')
	off = add_fract_perc(hd, data, off, fmt, 'Scale down')
	return off

def add_ole_object(hd, data, offset, fmt, header, page, parent):
	off = offset
	if header.ole_id != 0:
		(length, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'OLE object length', length, off - 4, 4, fmt('I'))
		oledata = data[off:off + length]
		oleiter = add_pgiter(page, 'OLE object', 'qxp', '', oledata, parent)
		import ole
		ole.ole_open(oledata, page, oleiter)
		add_iter(hd, 'OLE object', "", off, length, '%ds' % length)
		off += length
	else:
		off += 4
	return off

def add_text_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt)
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	off = add_coords(hd, data, off, fmt)
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	off += 20
	if header.gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	off = add_linked_text_offset(hd, data, off, fmt, header)
	off += 2
	off = add_text_settings(hd, data, off, fmt, header)
	off = add_next_linked_text_settings(hd, data, off, fmt, header)
	off += 12
	if header.content_index == 0:
		off += 28
	else:
		if header.linked_text_offset == 0:
			off += 12
	return off

def add_picture_box(hd, data, offset, fmt, version, obfctx, header, page, parent):
	off = offset
	hd.model.set(header.content_iter, 0, "Picture block")
	off = add_frame(hd, data, off, fmt)
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	off = add_coords(hd, data, off, fmt)
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	off += 16
	off = add_ole_object(hd, data, off, fmt, header, page, parent)
	if header.gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	off = add_picture_settings(hd, data, off, fmt, header)
	off += 8
	off += 24
	off += 44
	if header.content_index != 0 and header.ole_id == 0:
		(ilen, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Image data length', ilen, off - 4, 4, fmt('I'))
		off += ilen
	return off

def add_empty_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt)
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	off = add_coords(hd, data, off, fmt)
	(corner_radius, off) = rfract(data, off, fmt)
	corner_radius /= 2
	add_iter(hd, 'Corner radius', '%.2f pt / %.2f in' % (corner_radius, dim2in(corner_radius)), off - 4, 4, fmt('i'))
	off += 20
	if header.gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	return off

def add_line(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt, 'Line')
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	off = add_coords(hd, data, off, fmt)
	off += 24
	return off

def add_line_text(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt, 'Line')
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	off = add_coords(hd, data, off, fmt)
	off += 24
	off = add_linked_text_offset(hd, data, off, fmt, header)
	off += 44
	off = add_next_linked_text_settings(hd, data, off, fmt, header)
	off += 4
	off = add_text_path_settings(hd, data, off, fmt, header)
	off += 4
	if header.content_index == 0:
		off += 28
	else:
		if header.linked_text_offset == 0:
			off += 12
	return off

def add_bezier_line(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt, 'Line')
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	(bz_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier ID?', hex(bz_id), off - 4, 4, fmt('I'))
	off += 36
	off = add_bezier(hd, data, off, fmt)
	return off

def add_bezier_line_text(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt, 'Line')
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	(bz_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier ID?', hex(bz_id), off - 4, 4, fmt('I'))
	off += 36
	off = add_linked_text_offset(hd, data, off, fmt, header)
	off += 44
	off = add_next_linked_text_settings(hd, data, off, fmt, header)
	off += 4
	off = add_text_path_settings(hd, data, off, fmt, header)
	off += 4
	off = add_bezier(hd, data, off, fmt)
	if header.content_index == 0:
		off += 28
	else:
		if header.linked_text_offset == 0:
			off += 12
	return off

def add_bezier_empty_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt)
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	(bz_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier ID?', hex(bz_id), off - 4, 4, fmt('I'))
	off += 36
	if header.gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	off = add_bezier(hd, data, off, fmt)
	return off

def add_bezier_text_box(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off = add_frame(hd, data, off, fmt)
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	(bz_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier ID?', hex(bz_id), off - 4, 4, fmt('I'))
	off += 36
	if header.gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	off = add_linked_text_offset(hd, data, off, fmt, header)
	off += 2
	off = add_text_settings(hd, data, off, fmt, header)
	off = add_next_linked_text_settings(hd, data, off, fmt, header)
	off += 12
	off = add_bezier(hd, data, off, fmt)
	if header.content_index == 0:
		off += 16
	off += 12
	return off

def add_bezier_picture_box(hd, data, offset, fmt, version, obfctx, header, page, parent):
	off = offset
	hd.model.set(header.content_iter, 0, "Picture block")
	off = add_frame(hd, data, off, fmt)
	off += 4
	off = add_runaround(hd, data, off, fmt)
	off += 4
	(bz_id, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Bezier ID?', hex(bz_id), off - 4, 4, fmt('I'))
	off += 32
	off = add_ole_object(hd, data, off, fmt, header, page, parent)
	if header.gradient_id != 0:
		off = add_gradient(hd, data, off, fmt)
	off = add_picture_settings(hd, data, off, fmt, header)
	off += 76
	off = add_bezier(hd, data, off, fmt)
	if header.content_index != 0 and header.ole_id == 0:
		(ilen, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Image data length', ilen, off - 4, 4, fmt('I'))
		off += ilen
	return off

def add_group(hd, data, offset, fmt, version, obfctx, header):
	off = offset
	off += 68
	off = add_coords(hd, data, off, fmt)
	off += 24
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '# of objects', count, off - 2, 2, fmt('H'))
	off += 6
	(listlen, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length of index list', listlen, off - 4, 4, fmt('I'))
	listiter = add_iter(hd, 'Index list', '', off, listlen, '%ds' % listlen)
	for i in range(1, count + 1):
		(idx, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Index %d' % i, idx, off - 4, 4, fmt('I'), parent=listiter)
	return off

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	objiter = add_pgiter(page, '[%d]' % index, 'qxp4', ('object', hd), data[offset:], parent)

	(header, off) = add_object_header(hd, data, off, fmt, version, obfctx)

	if header.content_type == 0:
		if header.shape in [1, 2]:
			off = add_line(hd, data, off, fmt, version, obfctx, header)
		elif header.shape in [4]:
			off = add_bezier_line(hd, data, off, fmt, version, obfctx, header)
		elif header.shape in [11]:
			off = add_bezier_empty_box(hd, data, off, fmt, version, obfctx, header)
		else:
			off = add_empty_box(hd, data, off, fmt, version, obfctx, header)
	elif header.content_type == 2:
		off = add_group(hd, data, off, fmt, version, obfctx, header)
	elif header.content_type == 3:
		if header.shape in [1, 2]:
			off = add_line_text(hd, data, off, fmt, version, obfctx, header)
		elif header.shape in [4]:
			off = add_bezier_line_text(hd, data, off, fmt, version, obfctx, header)
		elif header.shape in [11]:
			off = add_bezier_text_box(hd, data, off, fmt, version, obfctx, header)
		else:
			off = add_text_box(hd, data, off, fmt, version, obfctx, header)
	elif header.content_type == 4:
		if header.shape in [11]:
			off = add_bezier_picture_box(hd, data, off, fmt, version, obfctx, header, page, objiter)
		else:
			off = add_picture_box(hd, data, off, fmt, version, obfctx, header, page, objiter)

	# update object title and size
	if header.content_type == 2:
		type_str = 'Group'
	else:
		type_str = "%s / %s" % (key2txt(header.shape, shape_types_map), key2txt(header.content_type, content_type_map))
	page.model.set_value(objiter, 0, "[%d] %s [%d]" % (index, type_str, header.id))
	page.model.set_value(objiter, 2, off - offset)
	page.model.set_value(objiter, 3, data[offset:off])
	obfctx.next(header.content_index)
	return header, off

def handle_page(page, data, offset, parent, fmt, version, obfctx, index, master):
	off = offset
	hd = HexDumpSave(offset)
	# the real size is determined at the end
	pageiter = add_pgiter(page, 'Page', 'qxp4', ('page', hd), data[offset:offset + 110], parent)

	(counter, off) = rdata(data, off, fmt('H'))
	# This contains number of objects ever saved on the page
	add_iter(hd, 'Object counter / next object ID?', counter, off - 2, 2, fmt('H'))
	(off, settings_block_size, settings_blocks_count) = add_page_header(hd, off + 8, data, off, fmt)
	def _add_settings(name, offset):
		block_iter = add_iter(hd, name, '', offset, settings_block_size, '%ds' % settings_block_size)
		return add_page_settings(hd, settings_block_size, data, offset, fmt, version, block_iter)
	assert settings_blocks_count in (1, 2)
	if settings_blocks_count == 1:
		off = _add_settings('Page settings', off)
	elif settings_blocks_count == 2:
		off = _add_settings('Left page settings', off)
		off = _add_settings('Right page settings', off)
	for i in range(0, settings_blocks_count + 1):
		(length, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Length?', length, off - 4, 4, fmt('I'))
		off += length
		off += 4
	if fmt() == LITTLE_ENDIAN:
		off += 4
		(name, off) = add_pcstr4(hd, data, off, fmt)
	else:
		(name_data_length, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Name data length', name_data_length, off - 4, 4, fmt('I'))
		(name, _) = add_pascal_str(hd, data, off)
		off += name_data_length
	(objs, off) = rdata(data, off, fmt('I'))
	objs = obfctx.deobfuscate(objs & 0xffff, 2)
	add_iter(hd, 'Number of objects', objs, off - 4, 4, fmt('I'), tip=obfctx.tip())

	# update object title and size
	npages_map = {1: 'Single', 2: 'Facing'}
	pname = '[%d] %s%s page' % (index, key2txt(settings_blocks_count, npages_map), ' master' if master else '')
	if len(name) != 0:
		pname += ' "%s"' % name
	page.model.set_value(pageiter, 0, pname)
	page.model.set_value(pageiter, 2, off - offset)
	page.model.set_value(pageiter, 3, data[offset:off])
	return objs, pageiter, off

def parse_template(page, data, offset, parent, fmt, version, index):
	class DummyObfuscationContext:
		def next(self, block):
			pass
		def next_rev(self):
			pass
		def next_shift(self, shift):
			pass
		def deobfuscate(self, value, n):
			return value
		def tip(self):
			return ''
	(length, off) = rdata(data, offset, fmt('I'))
	end = off + length
	reciter = add_pgiter(page, 'Template', 'qxp4', ('record', fmt, version), data[off - 4:end], parent)
	(header, off) = handle_object(page, data, off, reciter, fmt, version, DummyObfuscationContext(), 0)
	# update object title and size
	type_str = "%s / %s" % (key2txt(header.shape, shape_types_map), key2txt(header.content_type, content_type_map))
	page.model.set_value(reciter, 0, "[%d] %s" % (index, type_str))
	return end

def handle_pages(page, data, parent, fmt, version, obfctx, nmasters):
	texts = set()
	pictures = set()
	off = 0
	master = True
	i = 1
	while off < len(data):
		start = off
		try:
			stop = rdata(data, off, fmt('I'))[0]
			if stop == 0x9e:
				add_pgiter(page, 'Tail', 'qxp4', (), data[start:], parent)
				break
			(objs, pgiter, off) = handle_page(page, data, start, parent, fmt, version, obfctx, i, master)
			obfctx.next_rev()
			for j in range(0, objs):
				(header, off) = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
				if header.content_index and not header.linked_text_offset:
					if header.content_type == 3:
						texts.add(header.content_index)
					elif header.content_type == 4:
						pictures.add(header.content_index)
			if i == nmasters:
				master = False
				i = 0
			i += 1
		except:
			traceback.print_exc()
			add_pgiter(page, 'Tail', 'qxp4', (), data[start:], parent)
			break
	return texts, pictures

def handle_document(page, data, parent, fmt, version, hdr):
	obfctx = ObfuscationContext(hdr.seed, hdr.inc)
	off = parse_record(page, data, 0, parent, fmt, version, 'Unknown')
	off = parse_record(page, data, off, parent, fmt, version, 'Print settings')
	off = parse_record(page, data, off, parent, fmt, version, 'Page setup')
	off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	off = parse_fonts(page, data, off, parent, fmt, version)
	off = parse_physical_fonts(page, data, off, parent, fmt, version)
	off = parse_colors(page, data, off, parent, fmt, version)
	(tabs, off) = parse_para_styles(page, data, off, parent, fmt, version)
	# NOTE: it appears tabs records are saved in the reverse order of
	# use by styles. I.e., the first tabs record belongs to the last
	# style that has tabs set.
	for i in range(0, tabs):
		off = parse_tabs(page, data, off, parent, fmt, version, 'Style tabs %d' % i)
	off = parse_char_styles(page, data, off, parent, fmt, version)
	off = parse_hjs(page, data, off, parent, fmt, version)
	off = parse_dashes(page, data, off, parent, fmt, version)
	off = parse_lists(page, data, off, parent, fmt, version)
	tmplstart = off
	tmpliter = add_pgiter(page, 'Templates', 'qxp4', (), data[off:], parent)
	(count, off) = parse_index(page, data, off, tmpliter, fmt, version)
	for i in range(1, count):
		if fmt() == LITTLE_ENDIAN:
			off = parse_template(page, data, off, tmpliter, fmt, version, i)
		else:
			off = parse_record(page, data, off, tmpliter, fmt, version, '[%d] Template' % i)
	off = parse_record(page, data, off, tmpliter, fmt, version, '[%d] Unknown' % count)
	page.model.set_value(tmpliter, 2, off - tmplstart)
	page.model.set_value(tmpliter, 3, data[tmplstart:off])
	off = parse_char_formats(page, data, off, parent, fmt, version)
	(tabs, off) = parse_tabs_spec(page, data, off, parent, fmt, version)
	for i in range(0, tabs):
		off = parse_tabs(page, data, off, parent, fmt, version, 'Format tabs %d' % i)
	off = parse_para_formats(page, data, off, parent, fmt, version)
	off = parse_record(page, data, off, parent, fmt, version, 'Unknown')
	pagesiter = add_pgiter(page, "Pages", 'qxp4', (), data[off:], parent)
	return handle_pages(page, data[off:], pagesiter, fmt, version, obfctx, hdr.masters)

def add_header(hd, size, data, fmt, version):
	(header, off) = add_header_common(hd, size, data, fmt)
	doctype_map = {'BK': 'Book', 'DC': 'Document', 'LB': 'Library', 'TP': 'Template'}
	(doctype, off) = rdata(data, off, '2s')
	add_iter(hd, 'Document type', key2txt(doctype, doctype_map), off - 2, 2, '2s')
	off += 20
	(pages, off) = rdata(data, off, fmt('H'))
	pagesiter = add_iter(hd, 'Number of pages?', pages, off - 2, 2, fmt('H'))
	off += 8
	off = add_margins(hd, size, data, off, fmt)
	off = add_dim(hd, size, data, off, fmt, 'Gutter width')
	off = add_dim(hd, size, data, off, fmt, 'Top offset')
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off += 5
	(header.masters, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Number of master pages', header.masters, off - 1, 1, fmt('B'))
	off += 4
	(header.inc, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation increment', hex(header.inc), off - 2, 2, fmt('H'))
	off += 44
	(header.seed, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Obfuscation seed', hex(header.seed), off - 2, 2, fmt('H'))
	sign = lambda x: 1 if x & 0x8000 == 0 else -1
	hd.model.set(pagesiter, 1, deobfuscate(pages, header.seed, 2) + sign(header.seed))
	off += 14
	off = add_dim(hd, size, data, off, fmt, 'Left offset')
	off = add_dim(hd, size, data, off, fmt, 'Top offset')
	off += 68
	(lines, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of lines', lines, off - 2, 2, fmt('H'))
	(texts, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of text boxes', texts, off - 2, 2, fmt('H'))
	(header.pictures, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of picture boxes', header.pictures, off - 2, 2, fmt('H'))
	off += 102
	(counter, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Object counter/last id?', counter, off - 4, 4, fmt('I'))
	return (header, size)

def _add_name(hd, size, data, fmt, offset=0, name="Name"):
	n = _read_name(data, fmt, offset)
	off = offset + 64
	add_iter(hd, name, n, off - 64, 64, '64s')
	return off

def add_hj(hd, size, data, fmt, version):
	off = 4
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
	off = 0x28
	off = add_dim(hd, size, data, off, fmt, 'Flush zone')
	off = _add_name(hd, size, data, fmt, 0x30)

def _add_char_format(hd, size, data, offset, fmt, version):
	off = offset
	(font, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Font index', font, off - 2, 2, fmt('H'))
	(flags, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 2, 2, fmt('H'))
	off = add_dim(hd, size, data, off, fmt, 'Font size')
	(scale, off) = rfract(data, off, fmt)
	add_iter(hd, 'Scale', '%.2f%%' % (scale * 100), off - 4, 4, '4s')
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index', color, off - 2, 2, fmt('H'))
	scale_type_map = {0: 'Horizontal', 1: 'Vertical'}
	(scale_type, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Scale type', key2txt(scale_type, scale_type_map), off - 2, 2, fmt('H'))
	(shade, off) = rfract(data, off, fmt)
	add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, '4s')
	off += 4
	(track, off) = rfract(data, off, fmt)
	add_iter(hd, 'Track amount', track, off - 4, 4, '4s')
	off = add_dim(hd, size, data, off, fmt, 'Baseline shift')
	(control, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Control char(s)?', key2txt(control, {0: 'No'}, 'Yes'), off - 1, 1, fmt('B'))

def add_char_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
	(style, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Style', style2txt(style), off - 2, 2, fmt('H'))
	off += 2
	_add_char_format(hd, size, data, off, fmt, version)

def add_char_style(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, fmt)
	off += 8
	(parent, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Based on', style2txt(parent), off - 2, 2, fmt('H'))
	(index, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Index', index, off - 2, 2, fmt('H'))
	off += 8
	_add_char_format(hd, size, data, off, fmt, version)

def _add_para_format(hd, size, data, offset, fmt, version):
	off = offset
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', qxpbflag2txt(flags, para_flags_map, fmt), off - 1, 1, fmt('B'))
	off += 2
	(align, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Alignment", key2txt(align, align_map), off - 1, 1, fmt('B'))
	(caps_lines, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Drop caps line count", caps_lines, off - 1, 1, fmt('B'))
	(caps_chars, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Drop caps char count", caps_chars, off - 1, 1, fmt('B'))
	(start, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Min. lines to remain", start, off - 1, 1, fmt('B'))
	(end, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Min. lines to carry over", end, off - 1, 1, fmt('B'))
	(hj, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'H&J index', hj, off - 2, 2, fmt('H'))
	off += 2
	off = add_dim(hd, size, data, off, fmt, 'Left indent')
	off = add_dim(hd, size, data, off, fmt, 'First line')
	off = add_dim(hd, size, data, off, fmt, 'Right indent')
	(lead, off) = rdata(data, off, fmt('I'))
	if lead == 0:
		add_iter(hd, 'Leading', 'auto', off - 4, 4, fmt('I'))
	else:
		off = add_dim(hd, size, data, off - 4, fmt, 'Leading')
	off = add_dim(hd, size, data, off, fmt, 'Space before')
	off = add_dim(hd, size, data, off, fmt, 'Space after')
	off += 4
	for rule in ('above', 'below'):
		ruleiter = add_iter(hd, 'Rule %s' % rule, '', off, 24, '24s')
		off = add_dim(hd, size, data, off, fmt, 'Width', parent=ruleiter)
		(line_style, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Style', 'D&S index %d' % line_style, off - 2, 2, fmt('H'), parent=ruleiter)
		(color, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Color index?', color, off - 2, 2, fmt('H'), parent=ruleiter)
		(shade, off) = rfract(data, off, fmt)
		add_iter(hd, 'Shade', '%.2f%%' % (shade * 100), off - 4, 4, fmt('i'), parent=ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From left', ruleiter)
		off = add_dim(hd, size, data, off, fmt, 'From right', ruleiter)
		(roff, off) = rfract(data, off, fmt)
		add_iter(hd, 'Offset', '%.2f%%' % (roff * 100), off - 4, 4, fmt('i'), parent=ruleiter)
	(tabs, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Tabs index?', idx2txt(tabs), off - 2, 2, fmt('H'))

def add_para_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
	(style, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Style', style2txt(style), off - 2, 2, fmt('H'))
	off += 2
	off = _add_para_format(hd, size, data, off, fmt, version)

def add_para_style(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, fmt)
	off += 8
	(parent, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Based on', style2txt(parent), off - 2, 2, fmt('H'))
	(next, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Next style?', style2txt(next), off - 2, 2, fmt('H'))
	off += 8
	(char, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Character style', style2txt(char), off - 2, 2, fmt('H'))
	off += 2
	speciter = add_iter(hd, 'Tabs spec', '', off, 8, '8s')
	off = _add_tabs_spec(hd, size, data, off, fmt, version, speciter)
	_add_para_format(hd, size, data, off, fmt, version)

def add_dash_stripe(hd, size, data, fmt, version):
	seglen = 0xa8
	segiter = add_iter(hd, 'Segment lengths', '', 0, seglen, '%ds' % seglen)
	off = seglen
	(id, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'ID', id, off - 2, 2, fmt('H'))
	(typ, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Type', key2txt(typ, dash_stripe_type_map), off - 1, 1, fmt('B'))
	(custom, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Is created by user?', key2txt(custom, {0: 'No', 1: 'Yes'}), off - 1, 1, fmt('B'))
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of segments', count, off - 2, 2, fmt('H'))
	# looks like some default stripes use Points, but pattern length is 1.0, so it is the same as %
	# in UI they always displayed in % and this flag is changed too when duplicating
	(unit, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Unit', key2txt(unit, dash_unit_map), off - 1, 1, fmt('B'))
	is_points = unit == 0
	(stretch, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Stretch to corners', key2txt(stretch, {0: 'No', 1: 'Yes'}), off - 1, 1, fmt('B'))
	off = _add_name(hd, size, data, fmt, off)
	off = 0xf4
	if is_points:
		off = add_dim(hd, size, data, off, fmt, 'Pattern length')
	else:
		(length, off) = rfract(data, off, fmt)
		add_iter(hd, 'Pattern length', length, off - 4, 4, fmt('i'))
	(miter, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Miter style', key2txt(miter, miter_map), off - 2, 2, fmt('H'))
	(endcap, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Endcap style', key2txt(endcap, endcap_map), off - 2, 2, fmt('H'))
	off = 0
	for i in range(1, count + 1):
		if is_points:
			off = add_dim(hd, size, data, off, fmt, '[%d]' % i, segiter)
		else:
			off = add_fract_perc(hd, data, off, fmt, '[%d]' % i, segiter)
	if off < seglen:
		add_iter(hd, 'Unused', '', off, seglen - off, '%ds' % (seglen - off), parent=segiter)

def add_list(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, fmt, 0)
	off += 3
	flags_map = {0x80: 'alphabetical'}
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, flags_map), off - 1, 1, fmt('B'))
	i = 1
	while off < size:
		(style, off) = rdata(data, off, fmt('H'))
		if style == 0xffff:
			off -= 2
			break
		styleiter = add_iter(hd, 'Style %d' % i, style, off - 2, 8, '8s')
		add_iter(hd, 'Style', idx2txt(style), off - 2, 2, fmt('H'), parent=styleiter)
		(level, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Level', level + 1, off - 1, 1, fmt('B'), parent=styleiter)
		numbering_map = {0: 'Text only', 1: 'Text...Page#', 2: 'Page#...Text'}
		(numbering, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Numbering', key2txt(numbering, numbering_map), off - 1, 1, fmt('B'), parent=styleiter)
		off += 2
		(fmtstyle, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Format as style', idx2txt(fmtstyle), off - 2, 2, fmt('H'), parent=styleiter)
		i += 1
	if off < size:
		add_iter(hd, 'Unset styles', '', off, size - off, '%ds' % (size - off))

def add_index(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of entries', count, off - 4, 4, fmt('I'))
	for i in range(0, count):
		entryiter = add_iter(hd, 'Entry %d' % i, '', off, 8, '8s')
		off += 2
		(content, off) = rdata(data, off, '<H')
		add_iter(hd, 'Content type', key2txt(content, content_type_map), off - 2, 2, fmt('H'), parent=entryiter)
		(id, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'ID?', hex(id), off - 4, 4, fmt('I'), parent=entryiter)
		hd.model.set(entryiter, 1, key2txt(content, content_type_map))

def add_tabs(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	i = 1
	while off < size:
		tabiter = add_iter(hd, 'Tab %d' % i, '', off, 8, '8s')
		off = add_tab(hd, size, data, off, fmt, version, tabiter)
		i += 1

ids = {
	'char_format': add_char_format,
	'char_style': add_char_style,
	'dash_stripe': add_dash_stripe,
	'hj': add_hj,
	'index': add_index,
	'list': add_list,
	'fonts': add_fonts,
	'colors': add_saved,
	'colors_header_block': add_saved,
	'color_name': add_saved,
	'color_data': add_saved,
	'color_rgb': add_saved,
	'color': add_saved,
	'object': add_saved,
	'page': add_saved,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'physical_fonts': add_physical_fonts,
	'record': add_record,
	'tabs': add_tabs,
	'tabs_spec': add_saved,
}

# vim: set ft=python sts=4 sw=4 noet:
