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
	end = data.find('\0', offset)
	return (data[offset:offset + end], end + 1)

def _handle_collection_named(handler, name_offset):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = 0
		while off + name_offset < len(data):
			(name, end) = _read_name(data, off + name_offset)
			if (end - off) % 2 == 1:
				end += 1
			(entry, off) = rdata(data, off, '%ds' % (end - off))
			handler(page, entry, parent, fmt, version, i, name)
			i += 1
	return hdl

def handle_para_style(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', '', data, parent)

def handle_hj(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp33', '', data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp33', ('para_format', fmt, version), data, parent)

def handle_object(page, data, offset, parent, fmt, version, obfctx, index):
	off = offset
	(typ, off) = rdata(data, off, fmt('B'))
	typ = obfctx.deobfuscate(typ, 1)
	if typ == 3:
		off += 123
		(eh, off) = rdata(data, off, fmt('I'))
		off += 4
		if eh == 0: # TODO: this is a wild guess
			off += 12
	add_pgiter(page, '[%d]' % index, 'qxp33', ('object', fmt, version, obfctx), data[offset:off], parent)
	return off

def handle_doc(page, data, parent, fmt, version, obfctx):
	off = 0
	i = 1
	while off < len(data):
		start = off
		(typ, off) = rdata(data, off + 2, fmt('H'))
		if typ == 0x40:
			tname = 'Single'
			vid = 'page'
			off += 94
		elif typ == 0x7c:
			tname = 'Facing'
			vid = 'facing_page'
			off += 166
		else:
			add_pgiter(page, 'Tail', 'qxp33', (), data[start:], parent)
			break
		(name_len, off) = rdata(data, off, fmt('I'))
		(name, _) = rcstr(data, off)
		off += name_len
		(objs, off) = rdata(data, off, fmt('I'))
		pname = '[%d] %s page' % (i, tname)
		if len(name) != 0:
			pname += ' "%s"' % name
		pgiter = add_pgiter(page, pname, 'qxp33', (vid, fmt, version), data[start:off], parent)
		for j in range(1, objs + 1):
			off = handle_object(page, data, off, pgiter, fmt, version, obfctx, j)
			obfctx = obfctx.next()
		i += 1

handlers = {
	2: ('Print settings',),
	3: ('Page setup',),
	5: ('Fonts', None, 'fonts'),
	6: ('Physical fonts',),
	7: ('Colors',),
	9: ('Paragraph styles', _handle_collection_named(handle_para_style, 306)),
	10: ('H&Js', _handle_collection_named(handle_hj, 48)),
	12: ('Character formats', handle_collection(handle_char_format, 46)),
	13: ('Paragraph formats', handle_collection(handle_para_format, 256)),
}

def handle_document(page, data, parent, fmt, version, obfctx):
	off = 0
	i = 1
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
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp33', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		off += length
		i += 1
	doc = data[off:]
	dociter = add_pgiter(page, "[%d] Document" % i, 'qxp33', (), doc, parent)
	handle_doc(page, doc, dociter, fmt, version, obfctx)

def add_char_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
	off += 2
	(flags, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Format flags', bflag2txt(flags, char_format_map), off - 4, 4, fmt('I'))
	(fsz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Font size, pt', fsz, off - 4, 4, fmt('I'))
	off += 2
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index?', color, off - 2, 2, fmt('H'))

def add_para_format(hd, size, data, fmt, version):
	off = 0
	(uses, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
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

def add_fonts(hd, size, data, fmt, version):
	off = add_length(hd, size, data, fmt, version, 0)
	(count, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of fonts', count, off - 2, 2, fmt('H'))
	i = 0
	while i < count:
		(index, off) = rdata(data, off, fmt('H'))
		(name, off) = rcstr(data, off)
		(full_name, off) = rcstr(data, off)
		font_len = 2 + len(name) + len(full_name) + 2
		font_iter = add_iter(hd, 'Font %d' % i, '%d, %s' % (index, name), off - font_len, font_len, '%ds' % font_len)
		add_iter(hd, 'Font %d index' % i, index, off - font_len, 2, fmt('H'), parent=font_iter)
		add_iter(hd, 'Font %d name' % i, name, off - font_len + 2, len(name) + 1, '%ds' % (len(name) + 1), parent=font_iter)
		add_iter(hd, 'Font %d full name' % i, full_name, off - font_len + 2 + len(name) + 1, len(full_name) + 1, '%ds' % (len(full_name) + 1), parent=font_iter)
		i += 1

def add_page(hd, size, data, fmt, version):
	off = 16
	(width, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Width (in.)', dim2in(width), off - 2, 2, fmt('H'))
	off += 2
	(height, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Height (in.)', dim2in(height), off - 2, 2, fmt('H'))
	off = 48
	off = add_margins(hd, size, data, off, fmt)
	# maybe 4 bytes?
	(col, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'))
	off += 4
	(gut, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Gutter width (in.)', dim2in(gut), off - 2, 2, fmt('H'))
	off = 98
	off = add_pcstr4(hd, size, data, off, fmt)
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of objects', objs, off - 4, 4, fmt('I'))

def add_facing_page(hd, size, data, fmt, version):
	off = 16
	(width, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Width (in.)', dim2in(width), off - 2, 2, fmt('H'))
	off += 2
	(height, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Height (in.)', dim2in(height), off - 2, 2, fmt('H'))
	off = 48
	off = add_margins(hd, size, data, off, fmt)
	# maybe 4 bytes?
	(col, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'))
	off += 4
	(gut, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Gutter width (in.)', dim2in(gut), off - 2, 2, fmt('H'))
	off = 170
	off = add_pcstr4(hd, size, data, off, fmt)
	(objs, off) = rdata(data, off, fmt('I'))
	add_iter(hd, '# of objects', objs, off - 4, 4, fmt('I'))

def add_object(hd, size, data, fmt, version, obfctx):
	(typ, off) = rdata(data, 0, fmt('B'))
	add_iter(hd, 'Type', obfctx.deobfuscate(typ, 1), off - 1, 1, fmt('B'))
	off += 5
	(text, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Text', obfctx.deobfuscate(text, 2), off - 2, 2, fmt('H'))
	off += 66
	(toff, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Offset into text', toff, off - 4, 4, fmt('I'))

ids = {
	'char_format': add_char_format,
	'facing_page': add_facing_page,
	'fonts': add_fonts,
	'object': add_object,
	'page': add_page,
	'para_format': add_para_format,
	'record': add_record,
}

# vim: set ft=python sts=4 sw=4 noet:
