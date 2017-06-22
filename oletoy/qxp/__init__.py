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

import traceback
from utils import *
from qxp import dim2in, add_dim
import qxp
import qxp33
import qxp4

class ObfuscationContext:
	def __init__(self, seed, inc):
		assert seed & 0xffff == seed
		assert inc & 0xffff == inc
		self.seed = seed
		self.inc = inc

	def next(self):
		return ObfuscationContext((self.seed + self.inc) & 0xffff, self.inc)

	def next_rev(self):
		return ObfuscationContext((self.seed + 0xffff - self.inc) & 0xffff, self.inc)

	def next_shift(self, shift):
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
		highinit = self.seed & mask
		high = fill(highinit | (self.seed >> 15)) << (16 - shift)
		return ObfuscationContext(high | (self.seed >> shift), self.inc)

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

def parse_chain(buf, idx, rlen, fmt):
	blocks = []
	big = False
	nxt = idx
	while nxt > 0:
		off = (nxt - 1) * rlen
		count = 1
		if big:
			(count, off) = rdata(buf, off, fmt('H'))
		start = off
		off = (nxt - 1 + count) * rlen - 4
		(nxt, off) = rdata(buf, off, fmt('i'))
		big = nxt < 0
		if nxt < 0:
			nxt = abs(nxt)
		blocks.append(buf[start:off - 4])
	return ''.join(blocks)

def open_v5(page, buf, parent, fmt, version):
	rlen = 0x100

	header_hdl_map = {qxp.VERSION_3_3: qxp33.add_header, qxp.VERSION_4: qxp4.add_header}
	header_hdl = header_hdl_map[version] if header_hdl_map.has_key(version) else add_header
	header = qxp.HexDumpSave(0)
	(hdr, off) = header_hdl(header, 512, buf, fmt, version)
	add_pgiter(page, 'Header', 'qxp5', ('header', header), buf[0:off], parent)

	doc_hdl_map = {qxp.VERSION_3_3: qxp33.handle_document, qxp.VERSION_4: qxp4.handle_document}
	doc = parse_chain(buf, 3, rlen, fmt)
	dociter = add_pgiter(page, 'Document', 'qxp5', '', doc, parent)
	texts = []
	pictures = []
	if doc_hdl_map.has_key(version):
		(texts, pictures) = doc_hdl_map[version](page, doc, dociter, fmt, version, ObfuscationContext(hdr.seed, hdr.inc), hdr.masters)

	for text in texts:
		try:
			data = parse_chain(buf, text, rlen, fmt)
			hd = qxp.HexDumpSave(0)
			blocks = add_text_info(hd, len(data), data, fmt, version)
			textiter = add_pgiter(page, 'Text info [%x]' % text, 'qxp5', ('text_info', hd), data, parent)
			for (block, length) in blocks:
				add_pgiter(page, 'Text [%x]' % block, 'qxp5', ('text', length), buf[(block - 1)* rlen:block * rlen], textiter)
		except:
			traceback.print_exc()

	for picture in pictures:
		try:
			data = parse_chain(buf, picture, rlen, fmt)
			add_pgiter(page, 'Picture [%x]' % picture, 'qxp5', ('picture', len(data)), data)
		except:
			traceback.print_exc()

def add_header(hd, size, data, fmt, version):
	off = qxp.add_header_common(hd, size, data, fmt)
	return (qxp.Header(), size)

def add_text_info(hd, size, data, fmt, version):
	blocks = []
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
		blocks.append((block, tlen))
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
	return blocks

def add_text(hd, size, data, length, dummy):
	(text, off) = rdata(data, 0, '%ds' % length)
	add_iter(hd, 'Text', text, off - length, length, '%ds' % length)

qxp5_ids = {
	'header': qxp.add_saved,
	'text': add_text,
	'text_info': qxp.add_saved,
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
