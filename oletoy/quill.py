# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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

import sys,struct
import gtk
import tree
import hexdump
import pubblock
from utils import *

def val2pctxt(val):
	return '%.1f%%' % (val / 10.0)

def emu2pt(val):
	return val * 72 / 914400

def emu2pttxt(val):
	return '%.1fpt' % emu2pt(val)

def fdpc (hd, size, data):
	offset = 0
	num = struct.unpack('<H', data[offset:offset+2])[0]
	add_iter (hd, "num", num,0,2,"<H")
	offset = 8
	for i in range(num):
		txt_off = struct.unpack('<I', data[offset+i*4:offset+i*4+4])[0]
		fmt_off = struct.unpack('<H', data[offset+i*2+num*4:offset+i*2+num*4+2])[0]
		add_iter (hd, "txt/format offsets %d"%i, "%02x / %02x"%(txt_off,fmt_off),offset+i*4,4,"txt",offset+i*2+num*4,2)

sub_ids = {"FDPC":fdpc,"FDPP":fdpc}

def parse_fdpc (page,data,offset,fdpciter):
	text_pos = {1: 'superscript', 2: 'subscript',}
	locale_id = {
		1029: 'Czech',
		1033: 'English (US)',
	}
	underline = {
		0x401: 'single',
		0x402: 'words only',
		0x403: 'double',
		0x404: 'dotted',
		0x406: 'thick',
		0x407: 'dash',
		0x409: 'dot dash',
		0x40a: 'dot dot dash',
		0x40b: 'wave',
		0x410: 'thick wave',
		0x411: 'thick dot',
		0x412: 'thick dash',
		0x413: 'thick dot dash',
		0x414: 'thick dot dot dash',
		0x415: 'long dash',
		0x416: 'thick long dash',
		0x417: 'double wave',
	}

	names = {
		0x2: 'Bold 1',
		0x3: 'Italic 1',
		0x4: 'Outline',
		0x5: 'Shadow',
		0xc: 'Text size 1',
		0xf: 'Text position',
		0x12: 'Locale ID',
		0x13: 'Small caps',
		0x14: 'All caps',
		0x16: 'Emboss',
		0x17: 'Engrave',
		0x18: 'Pair kerning',
		0x1b: 'Kerning',
		0x1e: 'Underline',
		0x1f: 'Tracking',
		0x20: 'Scaling',
		0x24: 'Font?',
		0x37: 'Bold 2',
		0x38: 'Italic 2',
		0x39: 'Text size 2',
	}

	displays = {
		0xc: emu2pttxt,
		0xf: text_pos,
		0x12: locale_id,
		0x18: emu2pttxt,
		0x1b: emu2pttxt,
		0x1e: underline,
		0x1f: val2pctxt,
		0x20: val2pctxt,
	}

	parsers = {
		0x24: pubblock.block_descs({0x0: 'Font index?',}),
	}

	descs = pubblock.block_descs(names, displays, parsers)

	model = page.model
	[num] = struct.unpack('<H', data[offset:offset+2])
	for i in range (num):
		[toff] = struct.unpack('<I', data[offset+8+i*4:offset+12+i*4])
		[tflag] = struct.unpack('<H', data[offset+8+num*4+i*2:offset+8+2+num*4+i*2])
		iter1 = add_pgiter (page,"[%02x] %02x"%(toff,tflag),"quill","fdpc",data[offset+8+i*4:offset+12+i*4],fdpciter)
		[nlen] = struct.unpack('<I', data[offset+tflag:offset+tflag+4])
		pubblock.parse (page,data[offset+tflag+4:offset+tflag+nlen],iter1,0,0,None,descs)
	return

def parse_syid (page,data,offset,syiditer,txtiter,j):
	model = page.model
	try:
		[num] = struct.unpack('<I', data[offset+4:offset+8])
		i = 0
		for i in range(num):
			[id] = struct.unpack('<I', data[offset+8+i*4:offset+12+i*4])
			iter = model.append(syiditer,None)
			model.set(iter,0,"TXid: %02x"%id,1,("quill","syid"),2,4,3,data[offset+8+i*4:offset+12+i*4])
		return i+j
	except:
		print "Failed in parse_syid"

def parse_stsh (page,data,parent,flag):
	model = page.model
	[num] = struct.unpack('<I', data[4:8])
	[off1] = struct.unpack('<I', data[20:24])
	i = 1
	while off1 < len(data):
		if i == num:
			off2 = len(data)
		else:
			[off2] = struct.unpack('<I', data[20+i*4:24+i*4])
#		print "Offsets: %d %02x %02x"%(i,off1,off2)
		if flag == "1": # and i/2.>i/2:
			iter1 = add_pgiter (page,"Ch %02x Pr %02x"%(i,struct.unpack("<H",data[20+off1:20+off1+2])[0]),"quill","stsh",data[20+off1:20+off1+2],parent)
			[dlen] = struct.unpack('<I', data[20+off1+2:20+off1+6])
			pubblock.parse (page,data[20+off1+6:20+off1+dlen+2],iter1,i)
			off1 += dlen+2
			if off1 < off2:
				add_pgiter (page,"Ps","quill",0,data[20+off1:20+off2],iter1)
		else:
			add_pgiter (page,"Ch %02x"%i,"quill",0,data[20+off1:20+off2],parent)
		off1 = off2
		i += 1

def parse_strs(page,data,parent,txtiter):
	model = page.model
	[num] = struct.unpack('<I', data[0:4])
	tstart = 0
	for i in range(num):
		[nlen] = struct.unpack('<I',data[12+i*4:16+i*4])
		iter1 = add_pgiter (page,"TX %02x length (0x%02x)"%(i,nlen),"global",0,model.get_value(txtiter,3)[tstart:tstart+nlen*2-2],txtiter)
		model.set_value(iter1,1,("global"," ",0xff))
		tstart += nlen*2
		add_pgiter (page,"TX %02x length (0x%02x)"%(i,nlen),"quill","strs",data[12+i*4:16+i*4],parent)


def parse_tcd(page,data,parent,txtiter):
	model = page.model
	[num] = struct.unpack('<I', data[0:4])
	for i in range(num+1):
		[nlen] = struct.unpack('<I',data[12+i*4:16+i*4])
		add_pgiter (page,"TX %02x end offset (0x%02x)"%(i,nlen*2),"quill","tcd",data[12+i*4:16+i*4],parent)

def parse_pl(page,data,parent):
	model = page.model
	try:
		[num] = struct.unpack('<I', data[0:4])
		off = 12
		for i in range(num):
			[nlen] = struct.unpack('<I',data[off:off+4])
			iter1 = add_pgiter (page,"PL %02x"%i,"quill","pl",data[off:off+nlen],parent)
			pubblock.parse (page,data[off+4:off+nlen],iter1,i)
			off += nlen
	except:
		print "Failed at PL parsing"

def parse_font(page,data,parent):
	model = page.model
	[num] = struct.unpack('<I', data[4:8])
	for i in range(num):
		[off] = struct.unpack('<I', data[20+i*4:24+i*4])
		[nlen] = struct.unpack('<H', data[20+off:20+off+2])
		fname = unicode(data[20+off+2:20+off+2+nlen*2],"utf-16")
		[fid] = struct.unpack('<I', data[20+off+2+nlen*2:20+off+2+nlen*2+4])
		add_pgiter (page,"(%02x) %s"%(fid,fname),"quill","font",data[20+off:20+off+nlen*2+6],parent)

def parse_mcld(page,data,parent):
	model = page.model
	[num] = struct.unpack('<I', data[4:8])
	off = num*4 + 8
	for i in range(num):
		iter1 = add_pgiter (page,"(%02x) %02x"%(i,struct.unpack("<I",data[8+i*4:12+i*4])[0]),"quill",0,data[8+i*4:12+i*4],parent)
		[nlen] = struct.unpack("<I",data[off:off+4])
		iter2 = add_pgiter (page,"Hdr","quill",0,data[off:off+nlen],iter1)
		pubblock.parse (page,data[off+4:off+nlen],iter2,i,0)
		off += nlen
		[num2] = struct.unpack('<I', data[off:off+4])
		off += 4
		for k in range(num2):
			[nlen2] = struct.unpack('<I', data[off:off+4])
			iter3 = add_pgiter (page,"Ch %02x"%k,"quill",0,data[off:off+nlen2],iter1)
			pubblock.parse (page,data[off+4:off+nlen2],iter3,k,0)
			off += nlen2

def parse (page,data,parent):
	model = page.model
	off = 0
	add_pgiter (page,"Header","quill",0,data[off:off+32],parent)
	ch_num = struct.unpack('<H', data[off+26:off+28])[0]
	nxt_chblk = struct.unpack('<I', data[off+28:off+32])[0]
	off += 32
	txtiter = None
	txtnum = -1
	txtid = 0
	while ch_num != 0:
		for i in range(ch_num):
			[doffset] = struct.unpack('<I', data[off+16:off+20])	# offset to "sub-stream" data
			[dlen] = struct.unpack('<I', data[off+20:off+24])			# length of "sub-stream" data
			name = data[off+2:off+6]+"/"+data[off+12:off+16]+str(struct.unpack('<H', data[off+6:off+8])[0])+" [%02x:%02x]"%(doffset,doffset+dlen)
			iter1 = model.append(parent,None)
			if name[0:4] == "TEXT":
				txtiter = iter1 # assume for now that I won't have "TEXT/TEXT<num>" with <num> greater than 0
			if name[0:4] == "FDPC" or name[0:4] == "FDPP":
				parse_fdpc (page,data,doffset,iter1) # we can have more than one "FDPC/FDPCx"
			if name[0:4] == "SYID":
				txtid = parse_syid(page,data,doffset,iter1,txtiter,txtid)
			if name[0:4] == "STSH":
				parse_stsh (page,data[doffset:doffset+dlen],iter1,name[9]) #STSH/STSH1 looks slightly different
			if name[0:4] == "STRS":
				parse_strs (page,data[doffset:doffset+dlen],iter1,txtiter)
			if name[0:4] == "TCD ":
				parse_tcd (page,data[doffset:doffset+dlen],iter1,txtiter)
			if name[0:4] == "PL  ":
				parse_pl (page,data[doffset:doffset+dlen],iter1)
			if name[0:4] == "FONT":
				parse_font (page,data[doffset:doffset+dlen],iter1)
			if name[0:4] == "MCLD":
				parse_mcld (page,data[doffset:doffset+dlen],iter1)
	
			model.set_value(iter1,0,name)
			model.set_value(iter1,1,("quill",name[0:4]))
			model.set_value(iter1,2,dlen)
			model.set_value(iter1,3,data[doffset:doffset+dlen])
			model.set_value(iter1,6,model.get_string_from_iter(iter1))
			off += 24
		if nxt_chblk != 0xffFFffFF:
			off = nxt_chblk
			ch_num = struct.unpack('<H', data[off+2:off+4])[0]
			nxt_chblk = struct.unpack('<I', data[off+4:off+8])[0]
			off += 8
		else:
			ch_num = 0
#	add_pgiter (page,"Tail","quill",0,data[doffset+dlen:],parent)
