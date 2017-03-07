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

def open_v5(page, buf, parent, fmt):
	chains = []
	tblocks = {}
	stories = {}
	rlen = 0x100

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
			(end, off) = rdata(data, off, fmt('H'))
			# NOTE: this is a speculation
			(start, off) = rdata(data, off, fmt('H'))
			tblocks[block] = ""
			story.append((block, start, end))

	# parse blocks
	blockiter = add_pgiter(page, "Blocks", "qxp5", (), buf[0:len(buf)], parent)

	last_data = 2
	off = 0
	i = 1
	big = False
	nexts = {}
	try:
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
					if chain > last_data:
						stories[chain] = []
						parse_story(i, stories[chain])
				chains[chain].append(block)
				big = nextbig
				nexts[nxt] = chain
			i += count
	except:
		print "failed in qxp loop at block %d (offset %d)" % (i, start)

	# reconstruct data streams from chains of blocks
	pos = 0
	stream_name_map = {0: "Header", 1: "Unknown", 2: "Document"}
	stream_map = {0: 'header', 1: '', 2: ''}
	for chain in chains:
		stream = ''.join(chain)
		if stream_name_map.has_key(pos):
			name = stream_name_map[pos]
		else:
			name = "Text %d" % (pos - last_data)
		if stream_map.has_key(pos):
			vis = (stream_map[pos], fmt)
		else:
			text = ""
			for block in stories[pos]:
				text += tblocks[block[0]][block[1]:block[2]]
			vis = ('text', fmt, text)
		ins_pgiter(page, name, "qxp5", vis, stream, parent, pos)
		pos += 1

	return "QXP5"

def add_header(hd, size, data, fmt):
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
	(ver, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 1, 1, fmt('B'))
	off += 1
	(ver, off) = rdata(data, off, fmt('B'))
	add_iter(hd, 'Version', key2txt(ver, version_map), off - 1, 1, fmt('B'))

def add_text(hd, size, data, fmt, text):
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
		(end, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Block %d end offset' % i, end, off - 2, 2, fmt('H'), parent=blockiter)
		(start, off) = rdata(data, off, fmt('H'))
		add_iter(hd, 'Block %d start offset' % i, start, off - 2, 2, fmt('H'), parent=blockiter)
		i += 1

qxp5_ids = {
	'header': add_header,
	'text': add_text,
}

def open (page,buf,parent):
	if buf[2:4] == 'II':
		fmt = little_endian
	elif buf[2:4] == 'MM':
		fmt = big_endian
	else:
		print "unknown format '%s', assuming big endian" % buf[2:4]
		fmt = big_endian

	# see header version_map
	if ord(buf[8]) < 0x43:
		open_v5 (page,buf,parent,fmt)
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
