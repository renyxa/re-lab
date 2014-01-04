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

# Started from partial spec here: 
# http://www.russotto.net/chm/itolitlsformat.html

import struct
from utils import *

def open (buf,page,parent,off=0):
	add_pgiter(page,"LIT Header","lit","header",buf[off:off+0x28],parent)
	off += 0x10
	cnt = struct.unpack("<I",buf[off:off+4])[0]
	off += 4
	hdrlen = struct.unpack("<I",buf[off:off+4])[0]
	off += 0x14
	add_pgiter(page,"Header section","lit","hdrsect",buf[off:off+hdrlen],parent)
	maxoff = off
	for i in range(cnt):
		entoff = struct.unpack("<I",buf[off:off+4])[0]  # claimed to be 8 bytes int
		off += 8
		entlen = struct.unpack("<I",buf[off:off+4])[0]  # claimed to be 8 bytes int
		off += 8
		if entoff+entlen > maxoff:
			maxoff = entoff+entlen
		add_pgiter(page,"Section #%d"%i,"lit","sect%d"%i,buf[entoff:entoff+entlen],parent)
	
	add_pgiter(page,"Tail","lit","tail",buf[maxoff:],parent)

