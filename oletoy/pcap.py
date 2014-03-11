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

def open (page,buf,parent,off=0):
	add_pgiter(page,"PCAP Header","pcap","header",buf[0:0x18],parent)
	off = 0x18
	cnt = 0
	while off < len(buf)- 16:
		# ts = buf[off:off+4]
		off += 4
		# tms = buf[off:off+4]
		off += 4
		size = struct.unpack("<I",buf[off:off+4])[0]
		off += 4
		#osize = [off:off+4]
		off += 4
		pdata = buf[off:off+size]
		add_pgiter(page,"Packet %d"%cnt,"pcap","packet",buf[off-16:off+16+size],parent)
		off += size
		cnt += 1
