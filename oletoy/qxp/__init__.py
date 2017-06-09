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
from qxp import dim2in
import qxp
import qxp33
import qxp4

class ObfuscationContext:
	def __init__(self, seed, inc):
		self.seed = seed
		self.inc = inc

	def next(self):
		return ObfuscationContext((self.seed + self.inc) & 0xffff, self.inc)

	def deobfuscate(self, value, n):
		return qxp.deobfuscate(value, self.seed, n)

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

def handle_document(page, data, parent, fmt, version, obfctx):
	hdl_map = {qxp.VERSION_3_3: qxp33.handle_document, qxp.VERSION_4: qxp4.handle_document}
	if hdl_map.has_key(version):
		hdl_map[version](page, data, parent, fmt, version, obfctx)

def open_v5(page, buf, parent, fmt, version):
	chains = []
	tblocks = {}
	stories = {}
	tstarts = {}
	pictures = []
	rlen = 0x100

	def read_header():
		if version < qxp.VERSION_4:
			off = 0x108
			(pictures, off) = rdata(buf, off, fmt('H'))
			off += 6
			(seed, off) = rdata(buf, off, fmt('H'))
			(inc, off) = rdata(buf, off, fmt('H'))
		else:
			off = 0xe0
			(pictures, off) = rdata(buf, off, fmt('H'))
			(seed, off) = rdata(buf, 0x80, fmt('H'))
			(incseed, off) = rdata(buf, 0x52, fmt('H'))
			inc = qxp.deobfuscate(0xffff, incseed, 2)
		return (pictures, seed, inc)

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
			if version < qxp.VERSION_4:
				(sz, fm) = (2, fmt('H'))
			else:
				(sz, fm) = (4, fmt('I'))
			(tlen, off) = rdata(data, off, fm)
			tblocks[block] = ""
			story.append((block, tlen))

	add_pgiter(page, 'Header', 'qxp5', ('header', fmt), buf[0:512], parent)

	# parse blocks
	blockiter = add_pgiter(page, "Blocks", "qxp5", (), buf[512:len(buf)], parent)

	off = 512
	i = 3
	last_data = 0
	big = False
	nexts = {}
	try:
		(pict_count, seed, inc) = read_header()
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
						tstarts[chain] = i
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
	for (pos, chain) in enumerate(chains):
		stream = ""
		for block in chain:
			start = 2 if len(block) > rlen else 0
			stream += block[start:len(block) - 4]
		if pos == 0:
			name = 'Document'
			vis = ''
		elif pos in pictures:
			name = "Picture %d" % pid
			vis = ('picture', fmt, version)
			pid += 1
		elif stories.has_key(pos):
			name = "Text %d [%x]" % (tid, tstarts[pos])
			text = ""
			for block in stories[pos]:
				text += tblocks[block[0]][0:block[1]]
			vis = ('text', fmt, version, text)
			tid += 1
		streamiter = ins_pgiter(page, name, "qxp5", vis, stream, parent, pos + 1)
		if pos == 0:
			handle_document(page, stream, streamiter, fmt, version, ObfuscationContext(seed, inc))

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
	if ver < qxp.VERSION_4:
		off = 0x40
		(pages, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Number of pages', pages, off - 2, 2, fmt('H'))
		off = 0x4c
		off = qxp.add_margins(hd, size, data, off, fmt)
		(col, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Number of columns', col, off - 2, 2, fmt('H'))
		off += 2
		(gut, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Gutter width (in.)', dim2in(gut), off - 2, 2, fmt('H'))
		off = 0xb0
		off += 2
		(left, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Left offset (in.)', dim2in(left), off - 2, 2, fmt('H'))
		off += 2
		(top, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Top offset (in.)', dim2in(top), off - 2, 2, fmt('H'))
		off = 0xbc
		off += 2
		(left, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Left offset (in.)', dim2in(left), off - 2, 2, fmt('H'))
		off += 2
		(bottom, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Bottom offset (in.)', dim2in(bottom), off - 2, 2, fmt('H'))
	else:
		(seed, off) = rdata(data, 0x80, fmt('H'))
		off = 0x22
		(pages, off) = rdata(data, off, fmt('H'))
		sign = lambda x: 1 if x & 0x8000 == 0 else -1
		pagesiter = add_iter(hd, 'Number of pages?', qxp.deobfuscate(pages, seed, 2) + sign(seed), off - 2, 2, fmt('H'))
		off += 10
		off = qxp.add_margins(hd, size, data, off, fmt)
		off += 2
		(gut, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Column gutter width (in.)', dim2in(gut), off - 2, 2, fmt('H'))
		off += 2
		(top, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Top offset (in.)', dim2in(top), off - 2, 2, fmt('H'))
		off += 2
		(left, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Left offset (in.)', dim2in(left), off - 2, 2, fmt('H'))
		off = 0x52
		(incseed, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Obfuscation increment', hex(qxp.deobfuscate(0xffff, incseed, 2)), off - 2, 2, fmt('H'))
		off += 44
		off += 2 # We already read the seed
		add_iter(hd, 'Obfuscation seed', hex(seed), off - 2, 2, fmt('H'))
		off = 0x90
		off += 2
		(left, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Left offset (in.)', dim2in(left), off - 2, 2, fmt('H'))
		off += 2
		(top, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Top offset (in.)', dim2in(top), off - 2, 2, fmt('H'))
	off = 0xdc
	(lines, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of lines', lines, off - 2, 2, fmt('H'))
	if ver < qxp.VERSION_4:
		off += 40
	(texts, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of text boxes', texts, off - 2, 2, fmt('H'))
	(pictures, off) = rdata(data, off, fmt('H'))
	add_iter(hd, 'Number of picture boxes', pictures, off - 2, 2, fmt('H'))
	if ver < qxp.VERSION_4:
		off += 6
		(seed, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Obfuscation seed', '%x' % seed, off - 2, 2, fmt('H'))
		(inc, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Obfuscation increment', '%x' % inc, off - 2, 2, fmt('H'))
	if ver >= qxp.VERSION_4:
		off = 0x148
		(counter, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Object counter/last id?', counter, off - 4, 4, fmt('I'))

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
		if version < qxp.VERSION_4:
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
		if version < qxp.VERSION_4:
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
		if version < qxp.VERSION_4:
			(sz, fm) = (2, fmt('H'))
		else:
			(sz, fm) = (4, fmt('I'))
		(style_ind, off) = rdata(data, off, fm)
		add_iter(hd, 'Paragraph %d style index' % i, style_ind, off - sz, sz, fm, parent=paragraphiter)
		(tlen, off) = rdata(data, off, fmt('I'))
		add_iter(hd, 'Paragraph %d text length' % i, tlen, off - 4, 4, fmt('I'), parent=paragraphiter)
		i += 1
	add_iter(hd, 'Gargbage?', '', off, size - off, '%ds' % (size - off))

qxp5_ids = {
	'header': add_header,
	'text': add_text,
}

def call(hd, size, data, cid, args):
	ids_map = {'qxp33': qxp33.ids, 'qxp4': qxp4.ids, 'qxp5': qxp5_ids}
	if ids_map.has_key(cid):
		ids = ids_map[cid]
		if len(args) > 1 and ids.has_key(args[0]):
			f = ids[args[0]]
			if len(args) == 2:
				f(hd, size, data, args[1], 0)
			elif len(args) == 3:
				f(hd, size, data, args[1], args[2])
			else:
				f(hd, size, data, args[1], args[2], args[3])

def open (page,buf,parent):
	if buf[2:4] == 'II':
		fmt = qxp.little_endian
	elif buf[2:4] == 'MM':
		fmt = qxp.big_endian
	else:
		print "unknown format '%s', assuming big endian" % buf[2:4]
		fmt = qxp.big_endian

	# see header version_map
	(version, off) = rdata(buf, 8, fmt('H'))
	if version < qxp.VERSION_6:
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
