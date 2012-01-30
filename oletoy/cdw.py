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
import gobject
import gtk
import tree
import hexdump
from utils import *


def parse_lastrec (page, data,parent):
	# parse last record (something like 'Content')
	add_pgiter(page,"Hdr","cdw",0,data[:0xf],parent)
	
	# don't know what's where to look for version differences
	# so, wild guess based on small number of files
	shift = 0
	if ord(data[0xd])> 6:
		shift = 1
	off = 0xf
	chtype = data[off+4:off+6]
	try:
		while chtype != "\x00\x00":
			off_st = off
			tflag = ord(data[off+0xd+shift])
			if tflag == 1:
				tlen = struct.unpack("<H",data[off+0xe+shift:off+0x10+shift])[0]
				tdata = data[off+0x10+shift:off+0x10+tlen+shift]
				off += tlen+16+shift
			elif tflag == 2:
				tlen = struct.unpack("<I",data[off+0xe+shift:off+0x12+shift])[0]
				tdata = unicode(data[off+0x12+shift:off+0x12+tlen*2+shift],"utf-16")
				off += tlen*2+18+shift
			else:
				tdata = "%04x"%(struct.unpack("<H",data[off+0xe+shift:off+0x10+shift])[0])
				off += 16+shift
			if chtype == "\x1f\x4f":
				recid_len = struct.unpack("<I",data[off:off+4])[0]
				recs = ""
				for i in range(recid_len):
					recs += "%02x "%(struct.unpack("<I",data[off+4+i*4:off+8+i*4])[0])
				recs = recs[:len(recs)-1]
				off += (recid_len+1)*4
			
			elif chtype == "\x7f\x57":
				recid_len = ord(data[off])
				recs = ""
				for i in range(recid_len):
					recs += "%02x"%(struct.unpack("<H",data[off+1+i*2:off+3+i*2])[0])
				off += recid_len*2+1
			chtype = data[off+4:off+6]
			add_pgiter(page,"%s (%s)"%(tdata,recs),"cdw",0,data[off_st:off],parent)
	except:
		print 'Failed in parseing last record'


def open (data,page):
	f_iter = add_pgiter(page,"CDW file","cdw",0,data)
	add_pgiter(page,"Header","cdw",0,data[:0x18],f_iter)
	tr_off = struct.unpack("<I",data[0x8:0xc])[0]
	tr_num = struct.unpack("<I",data[0xc:0x10])[0]
	tr_iter = add_pgiter(page,"Trailer","cdw",0,data[tr_off:],f_iter)
	for i in range(tr_num):
		rec_off = struct.unpack("<I",data[tr_off+i*6:tr_off+i*6+4])[0]
		rec_len = struct.unpack("<H",data[tr_off+i*6+4:tr_off+i*6+6])[0]
		rec_iter = add_pgiter(page,"Rec %02x [%02x]"%(i,rec_off),"cdw",0,data[rec_off:rec_off+rec_len],tr_iter)

	parse_lastrec(page,data[rec_off:rec_off+rec_len],rec_iter)
