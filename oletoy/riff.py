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

# primitive parser for YEP-like files
def parse (page, data, parent):
	off = 0
	while off < len(data):
		fourcc = data[off:off+4]
		off += 4
		length = int(math.ceil(struct.unpack(">I",data[off:off+4])[0]/4.)*4)
		off += 4
		add_pgiter(page,"%s"%fourcc,"yep",fourcc,data[off:off+length],parent)
		off += length

# RIFF with lists

def parse2 (page, data, parent):
	off = 0
	if data[0:4] == "RIFF":
		dsize = struct.unpack("<I",data[4:8])
		if data[8:12] == "MGX ":
			off = 12
	liter = parent
	while off < len(data)-8:
		fourcc = data[off:off+4]
		length = struct.unpack("<I",data[off+4:off+8])[0]
		if fourcc == "LIST":
			off += 8
			listname = data[off:off+4]
			niter = add_pgiter(page,"%s"%listname,"riff",listname,data[off:off+length+8],liter)
			parse2(page,data[off+4:off+length],niter)
		else:
			niter = add_pgiter(page,"%s"%fourcc,"riff",fourcc,data[off:off+length+8],liter)
			off += 8
		off += length
