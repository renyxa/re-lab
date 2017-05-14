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

import struct
from utils import *

def little_endian(fmt):
	return '<' + fmt

def big_endian(fmt):
	return '>' + fmt

def dim2in(dim):
	return dim / 72.0

VERSION_3_3 = 0x3f
VERSION_4 = 0x41
VERSION_6 = 0x43

def collect_group(data,name,buf,fmt,off,grp_id):
	grplen = struct.unpack(fmt('H'),buf[off+0x400*(grp_id-1):off+0x400*(grp_id-1)+2])[0]
	data += buf[off+0x400*(grp_id-1)+2:off+0x400*(grp_id+grplen-1)-4]
	nxt = struct.unpack(fmt('i'),buf[off+0x400*(grp_id+grplen-1)-4:off+0x400*(grp_id+grplen-1)])[0]
	name += " %02x-%02x"%(grp_id,grp_id+grplen-1)
	if nxt > 0:
		data,name = collect_block(data,name,buf,fmt,off,nxt)
	elif nxt < 0:
		nxt = abs(nxt)
		data,name = collect_group(data,name,buf,fmt,off,nxt)
	return data,name


def collect_block(data,name,buf,fmt,off,blk_id):
	data += buf[off+0x400*(blk_id-1):off+0x400*blk_id-4]
	name += " %02x"%blk_id
	nxt = struct.unpack(fmt('i'),buf[off+0x400*blk_id-4:off+0x400*blk_id])[0]
	if nxt > 0:
		data,name = collect_block(data,name,buf,fmt,off,nxt)
	elif nxt < 0:
		nxt = abs(nxt)
		data,name = collect_group(data,name,buf,fmt,off,nxt)
	return data,name

def _read_name(data, offset=0):
	(n, off) = rdata(data, offset, '64s')
	return n[0:n.find('\0')]

def _read_name33(data, offset=0):
	end = data.find('\0', offset)
	return (data[offset:offset + end], end + 1)

def _handle_list(handler, size):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = 0
		while off + size <= len(data):
			(entry, off) = rdata(data, off, '%ds' % size)
			handler(page, entry, parent, fmt, version, i)
			i += 1
	return hdl

def _handle_list_named33(handler, name_offset):
	def hdl(page, data, parent, fmt, version):
		off = 0
		i = 0
		while off + name_offset < len(data):
			(name, end) = _read_name33(data, off + name_offset)
			if (end - off) % 2 == 1:
				end += 1
			(entry, off) = rdata(data, off, '%ds' % (end - off))
			handler(page, entry, parent, fmt, version, i, name)
			i += 1
	return hdl

def handle_para_style(page, data, parent, fmt, version, index):
	name = _read_name(data)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', ('para_style', fmt, version), data, parent)

def handle_char_style(page, data, parent, fmt, version, index):
	name = _read_name(data)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', ('char_style', fmt, version), data, parent)

def handle_hj(page, data, parent, fmt, version, index):
	name = _read_name(data, 0x30)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', ('hj', fmt, version), data, parent)

def handle_dash_stripe(page, data, parent, fmt, version, index):
	name = _read_name(data, 0xb0)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', ('dash_stripe', fmt, version), data, parent)

def handle_list(page, data, parent, fmt, version, index):
	name = _read_name(data, 0)
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', ('list', fmt, version), data, parent)

def handle_char_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp5', ('char_format', fmt, version), data, parent)

def handle_para_format(page, data, parent, fmt, version, index):
	add_pgiter(page, '[%d]' % index, 'qxp5', ('para_format', fmt, version), data, parent)

def handle_para_style33(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', '', data, parent)

def handle_hj33(page, data, parent, fmt, version, index, name):
	add_pgiter(page, '[%d] %s' % (index, name), 'qxp5', '', data, parent)

# TODO: It might work better to split the handling of different versions
# into separate classes (at least at points where the following version
# changed significantly, e.g., 3.3 vs 4.0). And also split the hexview
# callbacks.
v3_3_handlers = {
	2: ('Print settings',),
	3: ('Page setup',),
	5: ('Fonts', None, 'fonts'),
	6: ('Physical fonts',),
	7: ('Colors',),
	9: ('Paragraph styles', _handle_list_named33(handle_para_style33, 306)),
	10: ('H&Js', _handle_list_named33(handle_hj33, 48)),
	12: ('Character formats', _handle_list(handle_char_format, 46)),
	13: ('Paragraph formats', _handle_list(handle_para_format, 256)),
}

v4_handlers = {
	2: ('Print settings',),
	3: ('Page setup',),
	6: ('Fonts', None, 'fonts'),
	7: ('Physical fonts',),
	8: ('Colors',),
	9: ('Paragraph styles', _handle_list(handle_para_style, 244)),
	10: ('Character styles', _handle_list(handle_char_style, 140)),
	11: ('H&Js', _handle_list(handle_hj, 112)),
	12: ('Dashes & Stripes', _handle_list(handle_dash_stripe, 252)),
	13: ('Lists', _handle_list(handle_list, 324)),
	38: ('Character formats', _handle_list(handle_char_format, 64)),
	40: ('Paragraph formats', _handle_list(handle_para_format, 100)),
}

handler_map = {
	VERSION_3_3 : v3_3_handlers,
	VERSION_4 : v4_handlers,
}

def handle_document(page, data, parent, fmt, version):
	handlers = handler_map[version] if handler_map.has_key(version) else {}
	off = 0
	i = 1
	while off < len(data):
		name, hdl, hid = 'Record %d' % i, None, 'record'
		if handlers.has_key(i):
			name = handlers[i][0]
			if len(handlers[i]) > 1:
				hdl = handlers[i][1]
			if len(handlers[i]) > 2:
				hid = handlers[i][2]
		(length, off) = rdata(data, off, fmt('I'))
		record = data[off - 4:off + length]
		reciter = add_pgiter(page, "[%d] %s" % (i, name), 'qxp5', (hid, fmt, version), record, parent)
		if hdl:
			hdl(page, record[4:], reciter, fmt, version)
		off += length
		i += 1

def open_v5(page, buf, parent, fmt, version):
	chains = []
	tblocks = {}
	stories = {}
	pictures = []
	rlen = 0x100

	def read_header():
		off = 0xe0
		(pictures, off) = rdata(buf, off, fmt('H'))
		return pictures

	def read_story_blocks(pos, length, offset):
		start = (pos - 1) * rlen
		if rlen - 4 - offset >= length:
			cur = length
			rem = 0
		else:
			cur = rlen - 4 - offset
			rem = length - cur
		data = buf[start + offset:start + offset + cur]
		if rem > 0:
			(nxt, off) = rdata(buf, start + rlen - 4, fmt('i'))
			assert nxt > 0
			return data + read_story_blocks(nxt, rem, 0)
		return data

	def parse_story(pos, story):
		start = (pos - 1) * rlen
		off = start + 4
		(length, off) = rdata(buf, off, fmt('I'))
		data = read_story_blocks(pos, length, off - start)
		off = 0
		while off < len(data):
			(block, off) = rdata(data, off, fmt('I'))
			if version < VERSION_4:
				(sz, fm) = (2, fmt('H'))
			else:
				(sz, fm) = (4, fmt('I'))
			(tlen, off) = rdata(data, off, fm)
			tblocks[block] = ""
			story.append((block, tlen))

	# parse blocks
	blockiter = add_pgiter(page, "Blocks", "qxp5", (), buf[0:len(buf)], parent)

	last_data = 2
	off = 0
	i = 1
	big = False
	nexts = {}
	try:
		pict_count = read_header()
		while off < len(buf):
			start = off
			count = 1
			if tblocks.has_key(i):
				text = buf[start:start+rlen]
				add_pgiter(page, "[%02x] Text" % i, "qxp5", (), text, blockiter)
				tblocks[i] = text
				off += rlen
			else:
				if big:
					(count, off) = rdata(buf, off, fmt('H'))
				off = start + rlen * count - 4
				(nxt, off) = rdata(buf, off, fmt('i'))
				nextbig = nxt < 0
				if nxt < 0:
					nxt = abs(nxt)
				if big:
					n = "%02x-%02x [%02x]"%(i,i+count-1,nxt)
				else:
					n = "%02x [%02x]"%(i,nxt)
				block = buf[start:start+rlen*count]
				add_pgiter(page, n, "qxp5", (), block, blockiter)
				if nexts.has_key(i):
					chain = nexts[i]
				else: # a new chain starts here
					chain = len(chains)
					chains.append([])
					if chain > last_data + pict_count:
						stories[chain] = []
						parse_story(i, stories[chain])
					elif chain > last_data:
						pictures.append(chain)
				chains[chain].append(block)
				big = nextbig
				nexts[nxt] = chain
			i += count
	except:
		print "failed in qxp loop at block %d (offset %d)" % (i, start)

	# reconstruct data streams from chains of blocks
	pid = 1
	tid = 1
	stream_name_map = {0: "Header", 1: "Unknown", 2: "Document"}
	stream_map = {0: 'header', 1: '', 2: ''}
	for (pos, chain) in enumerate(chains):
		stream = ""
		for block in chain:
			start = 2 if len(block) > rlen else 0
			stream += block[start:len(block) - 4]
		if stream_name_map.has_key(pos):
			name = stream_name_map[pos]
			vis = (stream_map[pos], fmt)
		elif pos in pictures:
			name = "Picture %d" % pid
			vis = ('picture', fmt, version)
			pid += 1
		else:
			name = "Text %d" % tid
			text = ""
			for block in stories[pos]:
				text += tblocks[block[0]][0:block[1]]
			vis = ('text', fmt, version, text)
			tid += 1
		streamiter = ins_pgiter(page, name, "qxp5", vis, stream, parent, pos)
		if pos == 2:
			handle_document(page, stream, streamiter, fmt, version)

def _add_length(hd, size, data, fmt, version, offset, name="Length"):
	(length, off) = rdata(data, offset, fmt('I'))
	add_iter(hd, name, length, off - 4, 4, fmt('I'))
	return off

def add_header(hd, size, data, fmt, version):
	off = 2
	proc_map = {'II': 'Intel', 'MM': 'Motorola'}
	(proc, off) = rdata(data, off, '2s')
	add_iter(hd, 'Processor', key2txt(proc, proc_map), off - 2, 2, '2s')
	(sig, off) = rdata(data, off, '3s')
	add_iter(hd, 'Signature', sig, off - 3, 3, '3s')
	lang_map = {0x33: 'English', 0x61: 'Korean'}
	(lang, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Language', key2txt(lang, lang_map), off - 1, 1, fmt('B'))
	version_map = {
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
	off += 208
	(lines, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of lines', lines, off - 2, 2, fmt('H'))
	(texts, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of text boxes', texts, off - 2, 2, fmt('H'))
	(pictures, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of picture boxes', pictures, off - 2, 2, fmt('H'))

def add_text(hd, size, data, fmt, version, text):
	off = 0
	(length, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Text length', length, off - 4, 4, fmt('I'))
	(blocks_len, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length of blocks spec', blocks_len, off - 4, 4, fmt('I'))
	blockiter = add_iter(hd, 'Blocks spec', '', off, blocks_len, '%ds' % blocks_len)
	i = 0
	begin = off
	while off < begin + blocks_len:
		(block, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Block %d' % i, block, off - 4, 4, fmt('I'), parent=blockiter)
		if version < VERSION_4:
			(sz, fm) = (2, fmt('H'))
		else:
			(sz, fm) = (4, fmt('I'))
		(tlen, off) = rdata(data, off, fm)
		add_iter(hd, 'Block %d text length' % i, tlen, off - sz, sz, fm, parent=blockiter)
		i += 1
	(formatting_len, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length of formatting spec', formatting_len, off - 4, 4, fmt('I'))
	formattingiter = add_iter(hd, 'Formatting spec', '', off, formatting_len, '%ds' % formatting_len)
	i = 0
	begin = off
	while off < begin + formatting_len:
		if version < VERSION_4:
			(sz, fm) = (2, fmt('H'))
		else:
			(sz, fm) = (4, fmt('I'))
		(format_ind, off) = rdata(data, off, fm)
		add_iter(hd, 'Format %d index' % i, format_ind, off - sz, sz, fm, parent=formattingiter)
		(tlen, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Format %d text length' % i, tlen, off - 4, 4, fmt('I'), parent=formattingiter)
		i += 1
	(paragraphs_len, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Length of paragraphs spec', paragraphs_len, off - 4, 4, fmt('I'))
	paragraphiter = add_iter(hd, 'Paragraphs spec', '', off, paragraphs_len, '%ds' % paragraphs_len)
	i = 0
	begin = off
	while off < begin + paragraphs_len:
		if version < VERSION_4:
			(sz, fm) = (2, fmt('H'))
		else:
			(sz, fm) = (4, fmt('I'))
		(style_ind, off) = rdata(data, off, fm)
		add_iter(hd, 'Paragraph %d style index' % i, style_ind, off - sz, sz, fm, parent=paragraphiter)
		(tlen, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Paragraph %d text length' % i, tlen, off - 4, 4, fmt('I'), parent=paragraphiter)
		i += 1

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

def add_record(hd, size, data, fmt, version):
	_add_length(hd, size, data, fmt, version, 0)

def _add_name(hd, size, data, offset=0, name="Name"):
	(n, off) = rdata(data, offset, '64s')
	add_iter(hd, name, n[0:n.find('\0')], off - 64, 64, '64s')
	return off

def add_fonts(hd, size, data, fmt, version):
	off = _add_length(hd, size, data, fmt, version, 0)
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
	if version < VERSION_4:
		(uses, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
		off += 2
	else:
		(uses, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
		off += 4
		(font, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Font index', font, off - 2, 2, fmt('H'))
	flags_map = {0x1: 'bold', 0x2: 'italic', 0x4: 'underline'}
	(flags, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Format flags', bflag2txt(flags, flags_map), off - 4, 4, fmt('I'))
	(fsz, off) = rdata(data, off, fmt('I'))
	add_iter(hd, 'Font size, pt', fsz, off - 4, 4, fmt('I'))
	off += 2
	(color, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Color index?', color, off - 2, 2, fmt('H'))

def add_para_format(hd, size, data, fmt, version):
	off = 0
	if version < VERSION_4:
		(uses, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Use count', uses, off - 2, 2, fmt('H'))
		off += 3
	else:
		(uses, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Use count', uses, off - 4, 4, fmt('I'))
		off += 4
		# if 'keep lines together' is enabled, then 'all lines' is used (or Start/End if 'all lines' disabled)
		flags_map = {0x1: 'keep with next', 0x2: 'lock to baseline grid', 0x8: 'keep lines together', 0x10: 'all lines'}
		(flags, off) = rdata(data, off, fmt('B'))
		add_iter(hd, 'Flags', bflag2txt(flags, flags_map), off - 1, 1, fmt('B'))
		off += 2
	align_map = {0: 'Left', 1: 'Center', 2: 'Right', 3: 'Justified', 4: 'Forced'}
	(align, off) = rdata(data, off, fmt('B'))
	add_iter(hd, "Alignment", key2txt(align, align_map), off - 1, 1, fmt('B'))
	if version < VERSION_4:
		return # Not checked yet
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

qxp5_ids = {
	'char_format': add_char_format,
	'char_style': add_char_style,
	'dash_stripe': add_dash_stripe,
	'header': add_header,
	'hj': add_hj,
	'list': add_list,
	'fonts': add_fonts,
	'para_format': add_para_format,
	'para_style': add_para_style,
	'picture': add_picture,
	'record': add_record,
	'text': add_text,
}

def call_v5(hd, size, data, args):
	if len(args) > 1 and qxp5_ids.has_key(args[0]):
		f = qxp5_ids[args[0]]
		if len(args) == 2:
			f(hd, size, data, args[1], 0)
		elif len(args) == 3:
			f(hd, size, data, args[1], args[2])
		else:
			f(hd, size, data, args[1], args[2], args[3])

def open (page,buf,parent):
	if buf[2:4] == 'II':
		fmt = little_endian
	elif buf[2:4] == 'MM':
		fmt = big_endian
	else:
		print "unknown format '%s', assuming big endian" % buf[2:4]
		fmt = big_endian

	# see header version_map
	(version, off) = rdata(buf, 8, fmt('H'))
	if version < VERSION_6:
		open_v5(page, buf, parent, fmt, version)
		return "QXP5"
	else:
		rlen = 0x400
		off = 0
		parent = add_pgiter(page,"File","qxp","file",buf,parent)
	
		add_pgiter(page,"01","qxp","block01",buf[off:off+rlen],parent)
		
		lstlen1 = struct.unpack(fmt('I'),buf[off+rlen+0x14:off+rlen+0x18])[0]
		lstlen2 = struct.unpack(fmt('I'),buf[off+rlen+0x18:off+rlen+0x1c])[0]
		lstlen3 = struct.unpack(fmt('I'),buf[off+rlen+0x1c:off+rlen+0x20])[0]
		lstlen4 = struct.unpack(fmt('I'),buf[off+rlen+0x20:off+rlen+0x24])[0]
		txtlstlen = struct.unpack(fmt('I'),buf[off+rlen+0x24:off+rlen+0x28])[0]
		lst = []
		txtlstoff = 0x28+lstlen1++lstlen2+lstlen3+lstlen4
		for i in range(lstlen1/4):
			lst.append(struct.unpack(fmt('I'),buf[off+rlen+0x28+i*4:off+rlen+0x2c+i*4])[0])
		for i in lst:
			# collect chain of blocks
			data = buf[off+rlen*(i-1):off+rlen*i-4]
			name = "%02x"%i
			nxt = struct.unpack(fmt('i'),buf[off+rlen*i-4:off+rlen*i])[0]
			if nxt > 0:
				# collect next single block
				data,name = collect_block(data,name,buf,fmt,off,nxt)
			elif nxt < 0:
				# collect chain of blocks
				data,name = collect_group(data,name,buf,fmt,off,abs(nxt))
			add_pgiter(page,name,"qxp","block%02x"%i,data,parent)

		
		for j in range(txtlstlen/4):
			i = struct.unpack(fmt('I'),buf[off+rlen+txtlstoff+j*4:off+rlen+txtlstoff+j*4+4])[0]
			data = buf[off+rlen*(i-1):off+rlen*i]
			name = "TXT %02x"%i
			add_pgiter(page,name,"qxp","txtblock%02x"%i,data,parent)
		return "QXP6"
	
# vim: set ft=python sts=4 sw=4 noet:
