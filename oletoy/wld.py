# Copyright (C) 2007,2010-2012	Valek Filippov (frob@df.ru)
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

import sys,struct,gtk,gobject
from utils import *

def open(buf,page,parent):
	iter1 = page.model.append(None, None)
	page.model.set_value(iter1, 0, "File")
	page.model.set_value(iter1, 1, 0)
	page.model.set_value(iter1, 2, len(buf))
	page.model.set_value(iter1, 3, buf)

	off = struct.unpack("<I",buf[4:8])[0]
	add_pgiter(page,"\"mcfg\" [%04x]"%off,"cdr2","rec",buf[off:off+275],iter1)
	off += 275

	i = 0
	while off < len(buf)-4:
		size = struct.unpack("<I",buf[off:off+4])[0]
		off += 4
		data = buf[off:off+size]
		#page, name, ftype, stype, data, parent = None
		add_pgiter(page,"rec %02x [%04x]"%(i,off),"cdr2","rec",data,iter1)
		off += size
		i += 1
