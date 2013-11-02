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
	return 30,"r0039"

def r003f(buf,off,id0,id1):
	# XForm/Rotate?
	return 30,"r003f"

def r0fa1(buf,off,id0,id1):
	return 24,"r0fa1"

def r0fa2(buf,off,id0,id1):
	id_num = struct.unpack(">H",buf[off+18:off+20])[0]
	return 20+id_num*2,"r0fa2"

def r1005(buf,off,id0,id1):
	return 50,"r1005"

def r1006(buf,off,id0,id1):
	num1 = struct.unpack(">I",buf[off+20:off+24])[0]
	off2 = 24+num1
	num2 = struct.unpack(">I",buf[off+off2:off+off2+4])[0]
	off3 = off2+4+num2
	num3 = struct.unpack(">I",buf[off+off3:off+off3+4])[0]
	return off3+4+num3+90,"Text"

def r1008(buf,off,id0,id1):
	return 28,"r1008"

def r106a(buf,off,id0,id1):
	return 24,"Color RGB?"

def r106b(buf,off,id0,id1):
	return 16,"Color Grey?"

def r106c(buf,off,id0,id1):
	return 20,"Color CMYK?"

def r10cd(buf,off,id0,id1):
	# 0x0a >H FIll Name
	# 0x0c >H Id of the color rec
	return 15,"Basic Fill"

def r10ce(buf,off,id0,id1):
	return 24,"Basic Line"

def r10d0(buf,off,id0,id1):
	return 20,"r10d0"

def r10d1(buf,off,id0,id1):
	# Radial fill?
	return 16,"r10d1"

def r1131(buf,off,id0,id1):
	# 0x14 >H Fill ID
	# 0x16 >H Stroke ID
	# 0x18 >H Left pts*10
	# 0x1a >H Top
	# 0x1c >H Right
	# 0x1e >H Bottom
	# corner radius?
	return 32,"Rectangle"

def r1132(buf,off,id0,id1):
	# same as rectangle
	return 32,"Ellipse"

def r1134(buf,off,id0,id1): # path?
	num1 = struct.unpack(">H",buf[off+26:off+28])[0]
	return 28+num1*16,"Path"

def r1135(buf,off,id0,id1):
	# Fill ID, Line ID, L, T, B, R
	return 32,"Line"


def ZeroPad(buf,off,id0,id1):
	return 4,"Padding"

rec_types = {
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
	0x0fa2:r0fa2,
	0x1005:r1005,
	0x1006:r1006,
	0x1008:r1008,
	0x106a:r106a,
	0x106b:r106b,
	0x106c:r106c,
	0x10cd:r10cd,
	0x10ce:r10ce,
	0x10d0:r10d0,
	0x10d1:r10d1,
	0x1131:r1131,
	0x1132:r1132,
	0x1134:r1134,
	0x1135:r1135,
	0x1195:LinePat,
}

def fh_open (buf,page,parent=None,mode=1):
#	piter = add_pgiter(page,"FH12 file","fh","file",buf,parent)
	piter = parent
	off = 0
	add_pgiter(page,"FH12 Header","fh12","header",buf[0:0x80],piter)
	off = 0x80
	lim = len(buf)
	rid = 1
	while off < lim:
		id0 = struct.unpack(">H",buf[off:off+2])[0]
		id1 = struct.unpack(">H",buf[off+2:off+4])[0]
		if id0 == 0xFFFF and id1 == 0xFFFF:
			print 'Complete!'
			break
		id2 = struct.unpack(">H",buf[off+4:off+6])[0]
		# part of the whole thing
#		if (id1&0xFF == 0x19 or id1&0xFF == 0x1b or id1&0xFF == 0x09 or id1&0xFF == 0x0b) and id2 != 0x03:
#			rlen = 16
#			rtype = "%02x %04x"%(id1,id2)
#			add_pgiter(page,"[%02x] %s"%(rid,rtype),"fh12",rtype,buf[off:off+rlen],piter)
#			off += rlen
		if id2 in rec_types:
			rlen,rtype = rec_types[id2](buf,off,id0,id1)
			if rlen > 4:
				ridtxt = "[%02x]"%rid
				if id2&0xff30 == 0x30:
					ridtxt = ""
				add_pgiter(page,"%s\t%s"%(ridtxt,rtype),"fh12",rtype,buf[off:off+rlen],piter)
			off += rlen
		else:
			print "Unknown","%02x%02x"%(id0,id1),"%02x"%id2
			add_pgiter(page,"[%02x] Unknown %02x"%(rid,id2),"fh12","%02x"%id2,buf[off:off+1000],piter)
			off += 1000
		if rlen > 4 and not id2&0xFF30==0x30:
			rid += 1
