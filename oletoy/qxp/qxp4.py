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
from qxp import *

def _read_name(data, offset=0):
	(n, off) = rdata(data, offset, '64s')
	return n[0:n.find('\0')]

def handle_para_style(page, data, parent, fmt, version, index):
	name = _read_name(data)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('para_style', fmt, version), data, parent)

def handle_char_style(page, data, parent, fmt, version, index):
	name = _read_name(data)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('char_style', fmt, version), data, parent)

def handle_hj(page, data, parent, fmt, version, index):
	name = _read_name(data, 0x30)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('hj', fmt, version), data, parent)

def handle_dash_stripe(page, data, parent, fmt, version, index):
	name = _read_name(data, 0xb0)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('dash_stripe', fmt, version), data, parent)

def handle_list(page, data, parent, fmt, version, index):
	name = _read_name(data, 0)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp4', ('list', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp4', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp4', ('para_format', fmt, version), data, parent)

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	return (obfctx, offset)

def handle_doc(page, data, parent, fmt, version, obfctx):
	off = 0
	i = 1
	while off < len(data):
		start = off
		(typ, off) = rdata(data, off + 2, fmt('H'))
		if typ == 0x44:
			tname = 'Single'
			vid = 'page'
			off += 98
		elif typ == 0x84:
			tname = 'Facing'
			vid = 'facing_page'
			off += 174
		else:
			add_pgiter(page, 'Tail', 'qxp4', (), data[start:], parent)
			break
		(name_len, off) = rdata(data, off, fmt('I'))
		(name, _) = rcstr(data, off)
		off += name_len
		pname = '[%d] %s page' % (i, tname)
		if len(name) != 0:
			pname += ' "%s"' % name
		(objs, off) = rdata(data, off, fmt('I'))
		pgiter = add_pgiter(page, pname, 'qxp4', (vid, fmt, version, obfctx), data[start:off], parent)
		objs = obfctx.deobfuscate(objs & 0xffff, 2)
		obfctx = obfctx.next()
		for j in range(1, objs + 1):
			(obfctx, off) = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
		i += 1


handlers1 = {
	2: ('Print settings',),
	3: ('Page setup',),
	6: ('Fonts', None, 'fonts'),
	7: ('Physical fonts',),
	8: ('Colors',),
	9: ('Paragraph styles', handle_collection(handle_para_style, 244)),
	10: ('Character styles', handle_collection(handle_char_style, 140)),
	11: ('H&Js', handle_collection(handle_hj, 112)),
	12: ('Dashes & Stripes', handle_collection(handle_dash_stripe, 252)),
	13: ('Lists', handle_collection(handle_list, 324)),
	14: ('Index?', None, 'index'),
}

handlers2 = {
	0: ('Character formats', handle_collection(handle_char_format, 64)),
	2: ('Paragraph formats', handle_collection(handle_para_format, 100)),
}

def handle_document(page, data, parent, fmt, version, obfctx):
	off = 0
	i = 1
	handlers = handlers1
	while off < len(data) and i < 15:
		name, hdl, hid = 'Record %d' % i, None, 'record'
		if handlers.has_key(i):
			name = handlers[i][0]
			if len(handlers[i]) > 1:
				hdl = handlers[i][1]
			if len(handlers[i]) > 2:
				hid = handlers[i][2]
		(length, off) = rdata(data, off, fmt('I'))
		record = data[off - 4:off + length]
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp4', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		if i == 14:
			(count2, _) = rdata(data, off, fmt('I'))
		off += length
		i += 1
	base = i
	doc_idx = i + count2 + 4
	handlers = handlers2
	while off < len(data) and i < doc_idx:
		name, hdl, hid = 'Record %d' % i, None, 'record'
		idx = i - base - count2
		if handlers.has_key(idx):
			name = handlers[idx][0]
			if len(handlers[idx]) > 1:
				hdl = handlers[idx][1]
			if len(handlers[idx]) > 2:
				hid = handlers[idx][2]
		(length, off) = rdata(data, off, fmt('I'))
		record = data[off - 4:off + length]
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp4', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		off += length
		i += 1
	doc = data[off:]
	dociter = add_pgiter(page, "[%d] Document" % i, 'qxp4', (), doc, parent)
	handle_doc(page, doc, dociter, fmt, version, obfctx)

def add_picture(hd, size, data, fmt, version):
	off = 0
	(sz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Size', sz, off - 4, 4, fmt('I'))
	(sz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Size', sz, off - 4, 4, fmt('I'))
	off += 4
	(w, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Picture width', w, off - 2, 2, fmt('H'))
	(h, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Picture height', h, off - 2, 2, fmt('H'))
	off = 50
	add_iter(hd, 'Bitmap', '', off, sz, '%ds' % sz)

def _add_name(hd, size, data, offset=0, name="Name"):
	(n, off) = rdata(data, offset, '64s')
	add_iter(hd, name, n[0:n.find('\0')], off - 64, 64, '64s')
	return off

def add_para_style(hd, size, data, fmt, version):
	off = _add_name(hd, size, data)

def add_char_style(hd, size, data, fmt, version):
	off = _add_name(hd, size, data)

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
	off += 2
	(hyp_zone, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Hyphenation zone (in.)', dim2in(hyp_zone), off - 2, 2, fmt('H'))
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
	off = 0x2a
	(flush_zone, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Flush zone (in.)', dim2in(flush_zone), off - 2, 2, fmt('H'))
	off = _add_name(hd, size, data, 0x30)

def add_char_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
	off += 4
	(font, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Font index', font, off - 2, 2, fmt('H'))
	(flags, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 4, 4, fmt('I'))
	(fsz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Font size, pt', fsz, off - 4, 4, fmt('I'))
	off += 2
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index?', color, off - 2, 2, fmt('H'))

def add_para_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
	off += 4
	(flags, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Flags', bflag2txt(flags, para_flags_map), off - 1, 1, fmt('B'))
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
	off += 4
	(left_indent, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Left indent (in.)', dim2in(left_indent), off - 2, 2, fmt('H'))
	off += 2
	(first_line, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'First line (in.)', dim2in(first_line), off - 2, 2, fmt('H'))
	off += 2
	(right_indent, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Right indent (in.)', dim2in(right_indent), off - 2, 2, fmt('H'))
	off += 2
	(lead, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Leading (pt)', 'auto' if lead == 0 else lead, off - 2, 2, fmt('H'))
	off += 2
	(space_before, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Space before (in.)', dim2in(space_before), off - 2, 2, fmt('H'))
	off += 2
	(space_after, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Space after (in.)', dim2in(space_after), off - 2, 2, fmt('H'))

def add_dash_stripe(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, 0xb0)

def add_list(hd, size, data, fmt, version):
	off = _add_name(hd, size, data, 0)

def add_fonts(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of fonts', count, off - 2, 2, fmt('H'))
	i = 0
	while i < count:
		(index, off) = rdata(data, off, fmt('I'))
		(name, off) = rcstr(data, off)
		(full_name, off) = rcstr(data, off)
		font_len = 4 + len(name) + len(full_name) + 2
		font_iter = add_iter(hd, 'Font %d' % i, '%d, %s' % (index, name), off - font_len, font_len, '%ds' % font_len)
		add_iter(hd, 'Font %d index' % i, index, off - font_len, 4, fmt('I'), parent=font_iter)
		add_iter(hd, 'Font %d name' % i, name, off - font_len + 4, len(name), '%ds' % len(name), parent=font_iter)
		add_iter(hd, 'Font %d full name' % i, full_name, off - font_len + 4 + len(name), len(full_name), '%ds' % len(full_name), parent=font_iter)
		i += 1

def add_index(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of entries', count, off - 4, 4, fmt('I'))
	for i in range(0, count):
		(entry, off) = rdata(data, off, '8s')
		add_iter(hd, 'Entry %d' % i, '', off - 8, 8, '8s')

def add_object(hd, size, data, fmt, version, obfctx):
	off = 8
	(index, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Index/ID?', index, off - 2, 2, fmt('H'))
	(text, off) = rdata(data, off, fmt('I'))
	# TODO: the value is obfuscated somehow
	add_iter(hd, 'Starting block of text chain?', text, 4, off - 4, 4, fmt('I'))
	(rotf, off) = rdata(data, off, fmt('H'))
	(roti, off) = rdata(data, off, fmt('h'))
	rot = roti + rotf / float(0x10000) # TODO: or maybe 0xffff? I don't remember...
	add_iter(hd, 'Rotation angle', '%.2f deg' % rot, off - 4, 4, fmt('i'))
	off += 4
	# Text boxes with the same link ID are linked.
	(lid, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Link ID', hex(lid), off - 4, 4, fmt('I'))
	off += 14
	(typ, off) = rdata(data, 0, fmt('B'))
	add_iter(hd, 'Type?', obfctx.deobfuscate(typ, 1), off - 1, 1, fmt('B'))
	# Follows another obfuscated byte
	off += 109
	(toff, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Offset into text', toff, off - 4, 4, fmt('I'))
	off += 32
	(columns, off) = rdata(data, off, fmt('H'))
	add_iter(hd, '# of columns', columns, off - 2, 2, fmt('H'))

def add_page(hd, size, data, fmt, version, obfctx):
	off = 0
	(counter, off) = rdata(data, off, fmt('H'))
	# This contains number of objects ever saved on the page
	add_iter(hd, 'Object counter / next object ID?', counter, off - 2, 2, fmt('H'))
	(typ, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Page type', 'single', off - 2, 2, fmt('H'))
	off += 4
	(idx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Index', idx, off - 1, 1, fmt('B'))
	(cidx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Creation index', cidx, off - 1, 1, fmt('B'))
	off += 6
	(width, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Width (in.)', dim2in(width), off - 4, 4, fmt('I'))
	(height, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Height (in.)', dim2in(height), off - 4, 4, fmt('I'))
	off = 48
	off = add_margins(hd, size, data, off, fmt)
	off = add_page_columns(hd, size, data, off, fmt)
	off = 102
	off = add_pcstr4(hd, size, data, off, fmt)
	print("seed: %x, inc: %x" % (obfctx.seed, obfctx.inc))
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Number of objects', obfctx.deobfuscate(objs & 0xffff, 2), off - 4, 4, fmt('I'))

def add_facing_page(hd, size, data, fmt, version, obfctx):
	off = 0
	(counter, off) = rdata(data, off, fmt('H'))
	# This contains number of objects ever saved on the page
	add_iter(hd, 'Object counter / next object ID?', counter, off - 2, 2, fmt('H'))
	(typ, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Page type', 'facing', off - 2, 2, fmt('H'))
	off += 4
	(idx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Index', idx, off - 1, 1, fmt('B'))
	(cidx, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Creation index', cidx, off - 1, 1, fmt('B'))
	off += 6
	(width, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Width (in.)', dim2in(width), off - 4, 4, fmt('I'))
	(height, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Height (in.)', dim2in(height), off - 4, 4, fmt('I'))
	off = 48
	off = add_margins(hd, size, data, off, fmt)
	off = add_page_columns(hd, size, data, off, fmt)
	off = 178
	off = add_pcstr4(hd, size, data, off, fmt)
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Number of objects', obfctx.deobfuscate(objs & 0xffff, 2), off - 4, 4, fmt('I'))

ids = {
	'char_format': add_char_format,
	'char_style': add_char_style,
	'dash_stripe': add_dash_stripe,
	'facing_page': add_facing_page,
	'hj': add_hj,
	'index': add_index,
	'list': add_list,
	'fonts': add_fonts,
	'object': add_object,
	'page': add_page,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'picture': add_picture,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
