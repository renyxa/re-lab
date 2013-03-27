# Copyright (C) 2007,2010-2013	Valek Filippov (frob@df.ru)
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

import sys,struct,math
from utils import *

def hdr1item (page,data,parent,offset=0):
	off = 0
	h1chend = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	h1ch = []
	h1citer = add_pgiter(page,"Header 2","vrpm","hdr2",data[:h1chend],parent,"%02x  "%offset)
	ind = 0
	while off < h1chend - 4:
		v = struct.unpack(">I",data[off:off+4])[0]
		if v != 0:
			h1ch.append((v,ind))
		off += 4
		ind += 1
	off += 4
	for i in h1ch:
		add_pgiter(page,"Block %s"%i[1],"vrpm","hdr2ch",data[off:i[0]],h1citer,"%02x  "%(offset+off))
		off = i[0]
	if i[1] < 4:
		# assumption that Graph would be here always
		add_pgiter(page,"Block 4","vrpm","hdr2tail",data[off:],h1citer,"%02x  "%(offset+off))


def vprm (page, data, parent, offset=0):
	sig = data[:16]
	add_pgiter(page,"Signature","vrpm","sign",data[:16],parent,"%02x  "%offset)
	off = 16
	ptr = struct.unpack(">I",data[off:off+4])[0]
	off += 4

	hdr1end = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	hdr1 = []
	while off < hdr1end:
		v = struct.unpack(">I",data[off:off+4])[0]
		if v != 0:
			hdr1.append(v)
		off += 4
	#add_pgiter (page, name, ftype, stype, data, parent = None, coltype = None)
	h1iter = add_pgiter(page,"Header 1","vrpm","hdr1",data[20:hdr1end],parent,"%02x  "%(offset+20))
	for i in hdr1:
		hdr1item (page,data[off:i],h1iter,(offset+off))
		off = i
	hdr1item (page,data[off:ptr],h1iter,(offset+off))

	off = ptr
	off2 = ptr
	v1 = struct.unpack(">I",data[off:off+4])[0] # ??? "allways" 8
	hdraend = struct.unpack(">I",data[off2+4:off2+8])[0]
	haiter = add_pgiter(page,"Header A","vrpm","hdra",data[off:off+hdraend],parent,"%02x  "%(offset+off))
	off2 += hdraend
	hdrbend = off+struct.unpack(">I",data[off2:off2+4])[0]
	hdrb = []
	off2 += 4
	while off2 < hdrbend:
		v = struct.unpack(">I",data[off2:off2+4])[0]
		if v != 0:
			hdrb.append(v+off)
		off2 += 4
	hbiter = add_pgiter(page,"Header B","vrpm","hdrb",data[off+hdraend:off+hdrbend],parent,"%02x  "%(offset+off+hdraend))
	for i in hdrb:
		v1 = struct.unpack(">h",data[off2:off2+2])[0]
		v2 = struct.unpack(">h",data[off2+2:off2+4])[0]
		v3 = ord(data[off2+16])
		add_pgiter(page,"Block %02x %02x %02x"%(v1,v2,v3),"vrpm","hdrbch",data[off2:i],hbiter,"%02x  "%(offset+off2))
		off2 = i
	v1 = struct.unpack(">h",data[off2:off2+2])[0]
	v2 = struct.unpack(">h",data[off2+2:off2+4])[0]
	v3 = ord(data[off2+16])
	add_pgiter(page,"Block %02x %02x %02x"%(v1,v2,v3),"vrpm","hdrbch",data[off2:],hbiter,"%02x  "%(offset+off2))


def parse (page, data, parent,align=4.):
	off = 0
	while off < len(data):
		fourcc = data[off:off+4]
		off += 4
		l = struct.unpack(">I",data[off:off+4])[0]
		if align:
			length = int(math.ceil(l/align)*align)
		else:
			length = l
		off += 4
		if fourcc == "SSTY":
			iname = fourcc+" %s"%(data[off:off+16])
		elif fourcc == "VVST":
			n = struct.unpack(">H",data[off+0x19:off+0x1b])[0]
			if ord(data[off+0x18]) == 0x3f:
				f = "[Voice %s]"%n
			else:
				f = "[DrumKit %s]"%n
			iname = fourcc+f+" %s"%(data[off:off+16])
		else:
			iname = "%s"%fourcc
		
		citer = add_pgiter(page,iname,"yep",fourcc,data[off:off+length],parent)
		if fourcc == "VPRM":
			vprm (page, data[off:off+length], citer)
		if fourcc == "IPIT":
			parse (page, data[off:off+length], citer)
			
		off += length
	page.view.get_column(1).set_title("Offset")
	return "YEP"
