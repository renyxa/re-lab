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

import struct,gtk,gobject
from utils import *

types = {
	0x0402:"Font Name",
	0x040d:"Copyright",
	0x040e:"Font Description",
	0x0425:"Trademark",
	0x0426:"Author",
	0x0429:"Font Widht",
	0x042d:"Font License",
	0x042e:"Font URL",
	0x0468:"Version",
	0x04fd:"Kern lists",
	0x05dc:"Glyph Name",
	0x0600:"Font Info",
	0x7d1:"0x7d1 START", # temporary ID
	0x07ea:"Kerning Table",
	0x84fc:"OT features",
}

#add_pgiter(page,iname,"yep","%s%s"%(prefix,fourcc),data[off:off+length],parent)

def open(page, data, parent):
	off = 0
	add_pgiter(page,"Header","vfb","hdr",data[:0x36],parent)
	off += 0x36
	chlen = struct.unpack("<H",data[off:off+2])[0]
	add_pgiter(page,"???","vfb","hdr2",data[off:off+chlen+2],parent)
	off += 2+chlen
	gniter = None
	ktiter = None
	#try:
	if 1:
		while off < len(data):
			chtype = struct.unpack("<H",data[off:off+2])[0]
			chlen = struct.unpack("<H",data[off+2:off+4])[0]
			if chtype == 0x5dc:
				if not gniter:
					gniter = add_pgiter(page,"Glyph Names","vfb","dontsave","",parent)
				add_pgiter(page,key2txt(chtype,types,"%02x"%chtype),"vfb",chtype,data[off:off+chlen+4],gniter)
			elif chtype == 0x4fd:
				if not ktiter:
					ktiter = add_pgiter(page,"Kern Lists","vfb","dontsave","",parent)
				add_pgiter(page,key2txt(chtype,types,"%02x"%chtype),"vfb",chtype,data[off:off+chlen+4],ktiter)
			elif chtype == 0x84fc:
				# redefine length
				chlen = struct.unpack("<I",data[off+2:off+6])[0]
				add_pgiter(page,key2txt(chtype,types,"%02x"%chtype),"vfb",chtype,data[off:off+chlen+6],parent)
				# shift offset
				off += 2
			elif chtype == 0x7d1:
				add_pgiter(page,"%s 0x%02x"%(key2txt(chtype,types,"%02x"%chtype),ord(data[off+10])),"vfb",chtype,data[off:off+chlen+4],parent)
			else:
				add_pgiter(page,key2txt(chtype,types,"%02x"%chtype),"vfb",chtype,data[off:off+chlen+4],parent)
			off += 4+chlen
#	except:
#		print 'Failed at %02x'%off
	return "VFB"
