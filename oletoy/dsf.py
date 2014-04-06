# Copyright (C) 2007,2010-2014	Valek Filippov (frob@df.ru)
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

import struct,zlib
from utils import *

def parse_dsf_toc(page, data, toc, dsfditer):
	off = 0
	while off < len(data):
		chtype = ord(data[off])
		chid = ord(data[off+1])
		shift = 2
		if chid == 0x80:
			chid = ord(data[off+2])
			shift = 3
		chlen = struct.unpack("<I",toc[chid*4-4:chid*4])[0]
		add_pgiter(page,"Chunk %x [%02x]"%(chid,chtype),"dsf","chunk",data[off+shift:off+shift+chlen],dsfditer)
		off += shift+chlen

def open (page,buf,parent,off=0):
	add_pgiter(page,"DSF Header","dsf","header",buf[0:0x10],parent)
	decobj = zlib.decompressobj()
	output1 = decobj.decompress(buf[0x10:])
	tail = decobj.unused_data
	dsfditer = add_pgiter(page,"DSF Data","dsf","data",output1,parent)

	decobj2 = zlib.decompressobj()
	output2 = decobj2.decompress(tail)
	tail2 = decobj2.unused_data
	add_pgiter(page,"DSF ToC","dsf","toc",output2,parent)
	parse_dsf_toc(page, output1, output2, dsfditer)
	add_pgiter(page,"DSF Tail","dsf","tail",tail2,parent)

