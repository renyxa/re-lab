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
#

import sys,struct
from utils import *

def open (page,buf,parent):
	if parent == None:
		parent = add_pgiter(page,"File","chdraw","file",buf,parent)
	off = 0x1c
	add_pgiter(page,"Signature","chdraw","sig",buf[:0x1c],parent)
	while off < len(buf):
		rid = struct.unpack('<H', buf[off:off+2])[0]
		rlen = struct.unpack('<H', buf[off+2:off+4])[0]
		data = buf[off+4:off+4+rlen]
		add_pgiter(page,"Type: %04x"%rid,"chdraw",rid,data,parent)
		off += 4 + rlen
