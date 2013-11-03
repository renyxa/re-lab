# Copyright (C) 2007-2013,	Valek Filippov (frob@df.ru)
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

import struct
from utils import *

def LinePat(buf,off,id0,id1):
	return id1+2,"LinePat"

def List(buf,off,id0,id1):
	hdr_len = struct.unpack(">H",buf[off+8:off+10])[0]
	id_num = struct.unpack(">H",buf[off+10:off+12])[0]
	return hdr_len+id_num*2,"List"

def String(buf,off,id0,id1):
	return id1+2,"String"

def r0019(buf,off,id0,id1):
	return 30,"r0019"

def r0029(buf,off,id0,id1):
	return 34,"r0029"

def r0030(buf,off,id0,id1):
	return 34,"r0030"

def r0036(buf,off,id0,id1):
	return 30,"r0036"

def r0039(buf,off,id0,id1):
	# Xform/Scale
	return 30,"r0039"

def r003f(buf,off,id0,id1):
	# XForm/Rotate-Skew
	return 30,"r003f"

def r0fa1(buf,off,id0,id1):
	return 24,"r0fa1"

def Group (buf,off,id0,id1):
	id_num = struct.unpack(">H",buf[off+18:off+20])[0]
	return 20+id_num*2,"Group"

def r1005(buf,off,id0,id1):
	# related to group
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	return 50+notelen,"r1005"

def Text (buf,off,id0,id1):
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	off += notelen
	num1 = struct.unpack(">I",buf[off+20:off+24])[0]
	off2 = 24+num1
	num2 = struct.unpack(">I",buf[off+off2:off+off2+4])[0]
	off3 = off2+4+num2
	num3 = struct.unpack(">I",buf[off+off3:off+off3+4])[0]
	return off3+4+num3+90+notelen,"Text"

def r1008(buf,off,id0,id1):
	return 28,"r1008"

def r106a(buf,off,id0,id1):
	return 24,"Color RGB"

def r106b(buf,off,id0,id1):
	return 16,"Color Grey"

def r106c(buf,off,id0,id1):
	return 20,"Color CMY"

def BasicFill (buf,off,id0,id1):
	# 0x0a >H FIll Name
	# 0x0c >H Id of the color rec
	return 15,"BasicFill"

def BasicLine (buf,off,id0,id1):
	return 24,"BasicLine"

def r10d0(buf,off,id0,id1):
	return 20,"r10d0"

def r10d1(buf,off,id0,id1):
	# Radial fill?
	return 16,"r10d1"

def Rectangle (buf,off,id0,id1):
	# 0x08 >H note length
	# 0x0a >H layer ID
	# 0x14 >H Fill ID
	# 0x16 >H Stroke ID
	# 0x18 >H Left pts*10
	# 0x1a >H Top
	# 0x1c >H Right
	# 0x1e >H Bottom
	# corner radius?
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	return 32+notelen,"Rectangle"

def Oval (buf,off,id0,id1):
	# same as rectangle
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	return 32+notelen,"Oval"

def Path (buf,off,id0,id1): # path?
	# Path flags 0x19, 0x1b, 0x09, 0x0b
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	off += notelen
	num1 = struct.unpack(">H",buf[off+26:off+28])[0]
	return 28+num1*16+notelen,"Path"

def Line (buf,off,id0,id1):
	# Fill ID, Line ID, L, T, B, R
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	return 32+notelen,"Line"


def ZeroPad(buf,off,id0,id1):
	# bad idea, roundrect has 8 zeros, then radii
	# no indication in rect for it
	return 4,"Padding"

rec_types1 = {
	0x0000:ZeroPad,
	0x0002:List,
	0x0003:String,
	0x0019:r0019,
	0x0029:r0029,
	0x0030:r0030,
	0x0036:r0036,
	0x0039:r0039,
	0x003f:r003f,
	0x0fa1:r0fa1,
	0x0fa2:Group,
	0x1005:r1005,
	0x1006:Text,
	0x1008:r1008,
	0x106a:r106a,
	0x106b:r106b,
	0x106c:r106c,
	0x10cd:BasicFill,
	0x10ce:BasicLine,
	0x10d0:r10d0,
	0x10d1:r10d1,
	0x1131:Rectangle,
	0x1132:Oval,
	0x1134:Path,
	0x1135:Line,
	0x1195:LinePat,
}

def r2_1389 (buf,off,id0,id1):
	return 34,"r1389"

def r2_138a (buf,off,id0,id1):
	rlen = struct.unpack(">H",buf[off+34:off+36])[0]
	return 36+rlen*2,"r138a"

def r2_13ed (buf,off,id0,id1):
	return 48,"r13ed"

def r2_1452 (buf,off,id0,id1):
	return 20,"Color RGB"

def r2_1453(buf,off,id0,id1):
	return 18,"Color Grey"

def r2_1454(buf,off,id0,id1):
	return 22,"Color CMY"

def r2_14b5 (buf,off,id0,id1):
	return 16,"BasicFill"

def r2_14b6 (buf,off,id0,id1):
	return 26,"BasicLine"

def r2_14b7 (buf,off,id0,id1):
	return 20,"r14b7"

def r2_14b8 (buf,off,id0,id1):
	return 18,"r14b8"  # or 22

def r2_14c9 (buf,off,id0,id1):
	return 12,"r14c9"

def r2_14ca (buf,off,id0,id1):
	return 12,"r14ca"

def r2_14d3 (buf,off,id0,id1):
	return 22,"r14d3"

def r2_14d4 (buf,off,id0,id1):
	return 30,"r14d4"

def r2_14dd (buf,off,id0,id1):
	return 54,"r14dd" # or 58 or 62

def r2_1519 (buf,off,id0,id1):
	return 36,"Rectangle"

def r2_151a (buf,off,id0,id1):
	return 36,"Oval"

def r2_151c(buf,off,id0,id1):
	rlen = struct.unpack(">H",buf[off+30:off+32])[0]
	return 32+rlen*16,"Path"

def r2_151d (buf,off,id0,id1):
	return 36,"Line"

def r2_157d (buf,off,id0,id1):
	num = struct.unpack(">H",buf[off+12:off+14])[0]
	return 14+num*2,"LinePat"

def r2_List(buf,off,id0,id1):
	rlen = struct.unpack(">H",buf[off+6:off+8])[0]
	return 12+rlen*2,"List"

def r2_String(buf,off,id0,id1):
	return 7+ord(buf[off+6]),"String"

def r2_Text (buf,off,id0,id1):
	notelen = struct.unpack(">H",buf[off+8:off+10])[0]
	off += notelen
	num1 = struct.unpack(">H",buf[off+138:off+140])[0]
	num2 = struct.unpack(">H",buf[off+140:off+142])[0]
	if num2 != 0:
		if not num1-1 == num2:
			num1 += 22*num2-11
		else:
			num1 += 11
	return 160+notelen+num1+1,"Text"


rec_types2 = {
	0x0000:ZeroPad,
	0x0005:r2_List,
	0x0006:r2_String,
	0x0019:r0019,
	0x0029:r0029,
	0x0030:r0030,
	0x0036:r0036,
	0x0039:r0039,
	0x003f:r003f,
	0x1389:r2_1389,
	0x138a:r2_138a,
	0x13ed:r2_13ed, # like r1005
	0x13ee:r2_Text,
	0x1452:r2_1452,
	0x1453:r2_1453,
	0x1454:r2_1454,
	0x14b5:r2_14b5,
	0x14b6:r2_14b6,
	0x14b7:r2_14b7,
	0x14b8:r2_14b8,
	0x14c9:r2_14c9,
	0x14ca:r2_14ca,
	0x14d3:r2_14d3,
	0x14d4:r2_14d4,
	0x14dd:r2_14dd,
	0x1519:r2_1519,
	0x151a:r2_151a,
	0x151c:r2_151c,
	0x151d:r2_151d,
	0x157d:r2_157d,
}

def fh_open (buf,page,parent=None,mode=1):
#	piter = add_pgiter(page,"FH12 file","fh","file",buf,parent)
	piter = parent
	off = 0
	if buf[0:4] == "FHD2":
		page.version = 2
		hdrlen = 0x178
		rec_types = rec_types2
		ftype = "fh02"
	elif buf[0:4] == "acf3":
		page.version = 1
		hdrlen = 0x80
		rec_types = rec_types1
		ftype = "fh01"
	add_pgiter(page,"FH%d Header"%page.version,ftype,"header",buf[0:hdrlen],piter)
	off = hdrlen
	lim = len(buf)
	rid = 1
	while off < lim:
		id0 = struct.unpack(">H",buf[off:off+2])[0]
		id1 = struct.unpack(">H",buf[off+2:off+4])[0]
		if id0 == 0xFFFF and id1 == 0xFFFF:
			print 'Complete!'
			break
		id2 = struct.unpack(">H",buf[off+4:off+6])[0]
		if id2 in rec_types:
			rlen,rtype = rec_types[id2](buf,off,id0,id1)
			if rlen > 4:
				ridtxt = "[%02x]"%rid
				if id2&0xff30 == 0x30:
					ridtxt = ""
				add_pgiter(page,"%s\t%s"%(ridtxt,rtype),ftype,rtype,buf[off:off+rlen],piter)
			off += rlen
		else:
			print "Unknown","%02x%02x"%(id0,id1),"%02x"%id2
			add_pgiter(page,"[%02x] Unknown %02x"%(rid,id2),ftype,"%02x"%id2,buf[off:off+1000],piter)
			off += 1000
		if rlen > 4 and not id2&0xFF30==0x30:
			rid += 1
