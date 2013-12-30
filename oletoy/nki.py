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

import struct,zlib
from utils import *

def open (page,buf,parent):
	niter = page.model.append(parent,None)
	page.model.set(niter,0,"Header",1,("nki","hdr"),2,170,3,buf[0:170])

	i = 170
	flag = 0

	while i < len(buf):
		ntype = buf[i:i+4]
		nlen = struct.unpack("<I",buf[i+14:i+18])[0]
		l = 22
		if ntype == "\x54\xac\x70\x5e":
			for j in range(nlen):
				num = struct.unpack("<H",buf[i+l:i+l+2])[0]
				l += num
		elif ntype == "\x0a\xf8\xcc\x16":
			nlen2 = struct.unpack("<I",buf[i+19:i+23])[0]
			nlen3 = struct.unpack("<I",buf[i+23:i+27])[0]
			l += nlen2+9+nlen3
		elif ntype == "\x3c\xe6\x16\x49":
			l += 175
			flag = 1
		else:
			l += nlen
		niter = page.model.append(parent,None)
		page.model.set(niter,0,"%s [%d]"%(d2hex(ntype),i),1,("nki","1k"),2,l,3,buf[i:i+l])
		i += l

		if flag:
			l = i
			i = len(buf)

	niter = page.model.append(parent,None)
	output = zlib.decompress(buf[l:])
	page.model.set(niter,0,"XML [%d]"%(l),1,("nki","xml"),2,len(output),3,output)

