# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
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
from math import ceil

win_types = {0x15:'Drawing',0x1d:'Stencil'}

def EventItem (hd, size, value):
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "ID", 1, "%d"%struct.unpack("<I",value[4:8]),2,4,3,4,4,"<d")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "EventCode", 1, "%d"%struct.unpack("<h",value[8:10]),2,4,3,4,4,"<d")
# + 2 bytes of 'Action' and/or 'Enabled'
# + 2 \0\0 terminated strings -- 1st is for 'Target', 2nd -- 'TargetArgs'


def StencilPage (hd, size, value):
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "UniqueID", 1, "",2,0x16,3,8,4,"txt")
	iter1 = hd.model.append(None, None)
	base_id = "%02X%02X%02X%02X-"%(ord(value[0x3f]),ord(value[0x3e]),ord(value[0x3d]),ord(value[0x3c]))
	base_id += "%02X%02X-%02X%02X-"%(ord(value[0x39]),ord(value[0x38]),ord(value[0x3b]),ord(value[0x3a]))
	base_id += "%02X%02X-%02X%02X"%(ord(value[0x24]),ord(value[0x25]),ord(value[0x26]),ord(value[0x27]))
	base_id += "%02X%02X%02X%02X"%(ord(value[0x28]),ord(value[0x29]),ord(value[0x2a]),ord(value[0x2b]))
	hd.model.set (iter1, 0, "BaseID", 1, base_id,2,0x24,3,8,4,"txt")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Pattern Flags", 1, "%02x"%struct.unpack("<I",value[0x34:0x38]),2,0x34,3,4,4,"<I")



def Window (hd, size, value):
	iter1 = hd.model.append(None, None)
	[type] = struct.unpack("<I",value[6:10])
	if type in win_types:
		type = win_types[type]
	else:
		type = "%02x"%type
	hd.model.set (iter1, 0, "WinType", 1, type,2,6,3,4,4,"txt")

	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "WinLeft", 1, "%d"%struct.unpack("<h",value[0x12:0x14]),2,0x12,3,2,4,"<h")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "WinTop", 1, "%d"%struct.unpack("<h",value[0x14:0x16]),2,0x14,3,2,4,"<h")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "WinWidth", 1, "%d"%struct.unpack("<h",value[0x16:0x18]),2,0x16,3,2,4,"<h")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "WinHeight", 1, "%d"%struct.unpack("<h",value[0x18:0x1a]),2,0x18,3,2,4,"<h")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "ViewScale", 1, "%.2f"%struct.unpack("<d",value[0x22:0x2a]),2,0x22,3,8,4,"<d")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "ViewCenterX", 1, "%.2f"%struct.unpack("<d",value[0x2a:0x32]),2,0x2a,3,8,4,"<d")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "ViewCenterY", 1, "%.2f"%struct.unpack("<d",value[0x32:0x3a]),2,0x32,3,8,4,"<d")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Snap Settings", 1, "%d"%struct.unpack("<I",value[0x56:0x5a]),2,0x56,3,4,4,"<I")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Glue Settings", 1, "%d"%struct.unpack("<I",value[0x5a:0x5e]),2,0x5a,3,4,4,"<I")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Snap Extentions", 1, "%d"%struct.unpack("<I",value[0x5e:0x62]),2,0x62,3,4,4,"<I")

def NameList (hd, size, value):
	off = struct.unpack("<h",value[-2:])[0]
	off = int(4*ceil(off/4.))
	nnum = struct.unpack("<h",value[-4:-2])[0]
	# instead of passing thru compressed flag, test for size
	ltest = struct.unpack("<i",value[0:4])[0]
	shift = 0
	if ltest+4 == len(value):
		shift = 4
	add_iter (hd,"Rec offset (aligned)",off,len(value)-2,2,"<h")
	add_iter (hd,"# of names",nnum,len(value)-4,2,"<h")
	for i in reversed(xrange(nnum)):
		curoff = off+shift+i*4+2
		noff = struct.unpack("<h",value[curoff:curoff+2])[0]+shift
		noff = int(4*ceil(noff/4.))
		nid = struct.unpack("<h",value[noff:noff+2])[0]
		endpos  = value[noff+2:].find('\x00')
		add_iter (hd,"Name %x"%(nnum-i-1),"%s"%value[noff+2:noff+2+endpos],noff+2,endpos,"txt")

def NameIDXv123 (hd, size, value):
	off = 0  # compressed streams?
	i = 0
	while off < len(value):
		v1 = struct.unpack("<h",value[off:off+2])[0]
		v2 = struct.unpack("<h",value[off+2:off+4])[0]
		add_iter (hd,"Name %s"%i,"%x %x"%(v1,v2),off,4,"txt")
		off += 4
		i += 1


def NameIDX (hd, size, value):
	# instead of passing thru compressed flag, test for size
	ltest = struct.unpack("<i",value[0:4])[0]
	shift = 0
	if ltest+4 == len(value):
		shift = 4
	if hd.version >5:
		recnum = struct.unpack("<i",value[shift:shift+4])[0]
		add_iter (hd,"Rec #",recnum,shift,4,"<i")
		for i in range(recnum):
			v1 = struct.unpack("<i",value[shift+4+i*13:shift+8+i*13])[0]
			v2 = struct.unpack("<i",value[shift+8+i*13:shift+12+i*13])[0]
			v3 = struct.unpack("<i",value[shift+12+i*13:shift+16+i*13])[0]
			v4 = ord(value[shift+16+i*13])
			add_iter (hd,"Name %s"%i,"%x %x %x %x"%(v1,v2,v3,v4),shift+4+i*13,13,"txt")
	else:
		recnum = struct.unpack("<h",value[shift:shift+2])[0]
		add_iter (hd,"Rec #",recnum,shift,2,"<h")
		for i in range(recnum):
			v1 = struct.unpack("<h",value[shift+2+i*4:shift+4+i*4])[0]
			v2 = struct.unpack("<h",value[shift+4+i*4:shift+6+i*4])[0]
			add_iter (hd,"Name %s"%i,"%x %x"%(v1,v2),shift+6+i*4,4,"txt")


def FontFace (hd, size, value):
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Flags", 1, "%d"%struct.unpack("<i",value[0x4:0x8]),2,0x4,3,4,4,"<i")
	facename = unicode(value[0x8:0x48],"utf-16")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Name", 1, facename,2,0x8,3,0x40,4,"txt")
	ur1 = struct.unpack("<i",value[0x48:0x4c])[0]
	ur2 = struct.unpack("<i",value[0x4c:0x50])[0]
	ur3 = struct.unpack("<i",value[0x50:0x54])[0]
	ur4 = struct.unpack("<i",value[0x54:0x58])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "UnicodeRanges", 1, "%d %d %d %d"%(ur1,ur2,ur3,ur4),2,0x48,3,0x10,4,"txt")
	cs1 = struct.unpack("<i",value[0x58:0x5c])[0]
	cs2 = struct.unpack("<i",value[0x5c:0x60])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "CharSets", 1, "%d %d"%(cs1,cs2),2,0x58,3,0x8,4,"txt")
	panos = ""
	for i in range(10):
		panos += "%d "%ord(value[0x60+i])
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Panos", 1, panos,2,0x60,3,0xa,4,"txt")

stream_func = {0x1e:StencilPage,0x2a:Window,0x2f:EventItem,0x32:NameList,0x34:NameIDXv123,0xc9:NameIDX,0xd7:FontFace}
