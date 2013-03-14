# Copyright (C) 2007,2010,2011	Valek Filippov (frob@df.ru)
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

import sys,struct,gtk,gobject
from utils import *

def name_cnvrt(name):
	c1 = name[3]
	c2 = name[2]
	c3 = name[1]
	c4 = name[0]
	return c1+c2+c3+c4

def blk_chunks(page, buf, offset, p_iter):
	ch_len = struct.unpack('<I',buf[offset:offset+4])[0]
	offset += 4
	name = buf[offset:offset+4]
	n0 = ord(name[0])
	n1 = ord(name[1])
	n2 = ord(name[2])
	n3 = ord(name[3])
	if (n0 > 0x2f and n0 < 0x39) or (n0 > 0x60 and n0 < 0x7f) and (n1 > 0x2f and n1 < 0x39) or (n1 > 0x60 and n1 < 0x7f) and (n2 > 0x2f and n2 < 0x39) or (n2 > 0x60 and n2 < 0x7f) and (n3 > 0x2f and n3 < 0x39) or (n3 > 0x60 and n3 < 0x7f):
		ch_name = name_cnvrt(name)
		offset += 4
		ch_data = buf[offset-8:offset+ch_len]

		name = "[%02x] "%offset+ch_name+" (%02x)"%ch_len
		add_pgiter (page, name, "CPT", "BlkChnk", ch_data, p_iter,"[%04x]"%offset)
		offset += ch_len

	else:
		# Hack! Probably it should check against list of chunk names or some flags
		# or use this procedure after some specific chunks (+ flags)
		# currently after 'path' (sometimes with 1 or two additional chunks between
		# 'path' and start of this garbage
		offset += 4
		offset2 = ch_len
		ch_set_off = {}
		ch_set_len = {}
		ch_set_off[0] = ch_len
		ch_set_len[0] = struct.unpack('<I',name)[0]
		i = 1
		while offset < offset2:
			ch_set_off[i] = struct.unpack('<I',buf[offset:offset+4])[0]
			offset += 4
			ch_set_len[i] = struct.unpack('<I',buf[offset:offset+4])[0]
			offset += 4
			i += 1
		ch_name = "___"
		for j in range(i):
			ch_data = buf[ch_set_off[j]:ch_set_off[j]+ch_set_len[j]]
			name="[%02x] "%ch_set_off[j]+ch_name+" (%02x)"%ch_set_len[j]
			add_pgiter (page, name, "CPT", "BlkChnk", ch_data, p_iter,"[%04x]"%offset)
		offset = ch_set_off[j] + ch_set_len[j]

	return offset

def blk_hdr(page, buf, offset, p_iter):
	data = buf[offset:offset+4]
	name = "Width"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Height"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Width?"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Height?"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "BPP"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Unknown 0"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Unknown 1"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Unknown 2"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Chunk area size?"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
#	plt_size = struct.unpack('<I',data)[0]
	name = "Palette size"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+20]
	name = "Unknown 3"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 20
	data = buf[offset:offset+4]
	name = "Chunk area size 2?"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	data = buf[offset:offset+4]
	name = "Unknown 4"
	add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
	offset += 4
	if plt_size > 0:
		data = buf[offset:offset+plt_size]
		name = "Palette"
		add_pgiter (page, name, "CPT", "BlkHdr", data, p_iter,"[%04x]"%offset)
		offset += plt_size

	return offset



def open (buf,page,piter):
	parent = add_pgiter (page, "File CPT", "CPT", "ALL", buf,piter)
	data = buf[0:8]
	name = "CPT Signature"
	offset = 0
	add_pgiter (page, name, "CPT", "Sig", data, parent,"[%04x]"%offset)
	offset = 8
	data = buf[offset:offset+4]
	name = "Color Model"
	add_pgiter (page, name, "CPT", "ClrMod", data, parent,"[%04x]"%offset)
	offset = 12
	data = buf[offset:offset+4]
	name = "Palette Length"
	add_pgiter (page, name, "CPT", "PalLen", data, parent,"[%04x]"%offset)
	offset = 16
	data = buf[offset:offset+8]
	name = "Reserved"
	add_pgiter (page, name, "CPT", "Rsvd", data, parent,"[%04x]"%offset)
	offset = 24
	data = buf[offset:offset+4]
	name = "DPI H"
	add_pgiter (page, name, "CPT", "DPI", data, parent,"[%04x]"%offset)
	offset = 28
	data = buf[offset:offset+4]
	name = "DPI V"
	add_pgiter (page, name, "CPT", "DPI", data, parent,"[%04x]"%offset)
	offset = 32
	data = buf[offset:offset+8]
	name = "Reserved"
	add_pgiter (page, name, "CPT", "Rsvd", data, parent,"[%04x]"%offset)
	offset = 40
	data = buf[offset:offset+4]
	blk_num = struct.unpack('<I',data)[0]
	name = "Blocks Num"
	add_pgiter (page, name, "CPT", "BlkNum", data, parent,"[%04x]"%offset)
	offset = 44
	data = buf[offset:offset+4]
	name = "Unknown"
	add_pgiter (page, name, "CPT", "Unkn", data, parent,"[%04x]"%offset)
	offset = 48
	data = buf[offset:offset+4]
	name = "Flags"
	add_pgiter (page, name, "CPT", "Flags", data, parent,"[%04x]"%offset)
	offset = 52
	data = buf[offset:offset+4]
	blk_off = struct.unpack('<I',data)[0]
	name = "Blocks Offset"
	add_pgiter (page, name, "CPT", "BlkOff", data, parent,"[%04x]"%offset)
	offset = 56
	data = buf[offset:offset+8]
	name = "Reserved"
	add_pgiter (page, name, "CPT", "Rsvd", data, parent,"[%04x]"%offset)
	offset = 60
	data = buf[offset:blk_off - offset]
	name = "Comment"
	add_pgiter (page, name, "CPT", "Cmnt", data, parent,"[%04x]"%offset)

	offset = blk_off
	blk = {}
	for i in range(blk_num):
		try:
			blk1 = struct.unpack('<I',buf[offset:offset+4])[0]
			blk[i] = blk1
			name = "Block #%d offset"%(i)
			add_pgiter (page, name, "CPT", "BlkOffN", buf[offset:offset+4], parent,"[%04x]"%offset)
			offset += 8
		except:
			print "Something wrong with blocks array"
	blk[blk_num] = len(buf)

	for i in range(blk_num):
		try:
			name = "[%02x] Block #%d"%(blk[i],i)
			offset = blk[i]
			iter = add_pgiter (page, name, "CPT", "BlkN", buf[offset:blk[i+1]], parent,"[%04x]"%offset)
			offset = blk_hdr(page,buf,offset,iter)
			while offset < blk[i+1]:
				try:
					offset = blk_chunks(page,buf,offset,iter)
				except:
					print "Something wrong with chunk at offset %02x"%offset
					break
		except:
			print "Something wrong with block %d header"%i

	return "CPT"




