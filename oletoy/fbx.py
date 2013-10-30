# Copyright (C) 2007-2013	Valek Filippov (frob@df.ru)
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

import struct
from utils import *




def parse_block(page,buf,off,noff,parent):
	iters = [parent]
	p2 = parent
	while off < noff:
		nboff = struct.unpack("<I",buf[off:off+4])[0]
		propnum = struct.unpack("<I",buf[off+4:off+8])[0]
		proplen = struct.unpack("<I",buf[off+8:off+12])[0]
		namelen = ord(buf[off+12])
		if namelen > 0:
			name = buf[off+13:off+13+namelen]
			piter = add_pgiter(page,"%s"%name,"fbx","record",buf[off:off+13+namelen+proplen],parent)
			if propnum == 0:
				iters.append(piter)
				parent = piter
		else:
			try:
				iters.pop()
				parent = iters[-1]
			except:
				parent = p2
		off+=13+namelen+proplen


def open (buf,page,parent,off=0):
	add_pgiter(page,"FBX Header","fbx","header",buf[0:23],parent)
	off += 23
	ver = struct.unpack("<I",buf[off:off+4])[0]/1000.
	add_pgiter(page,"FBX Version: %s"%ver,"fbx","version",buf[off:off+4],parent)
	off += 4
	bid = 0
	while off < len(buf):
		noff = struct.unpack("<I",buf[off:off+4])[0]
		if noff != 0:
			piter = add_pgiter(page,"Block %d"%bid,"fbx","block",buf[off:noff],parent)
			parse_block(page,buf,off,noff,piter)
			off = noff
			bid += 1
		else:
			break
	add_pgiter(page,"Tail","fbx","tail",buf[off:],parent)
	
