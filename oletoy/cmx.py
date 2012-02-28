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

import sys,struct
import gobject
import gtk
from utils import *

# CMX header
def cont (hd,size,data):
	off = 0
	# "{Corel Binary Meta File}"
	add_iter (hd, "ID", data[0:24],0,32,"txt")
	off += 32
	# "Windows 3.1" or "Macintosh"
	add_iter (hd, "OS", data[off:off+11],off,16,"txt")
	off += 16
	# byte order: "2" - LE, "4" - BE
	bo = data[off]
	add_iter (hd, "Byte Order", data[off:off+4],off,4,"<I")
	off += 4
	# coord size: "2" - 16 bits, "4" - 32 bits
	add_iter (hd, "Coord Size", data[off:off+2],off,2,"<H")
	off += 2

cmx_ids = {"cont":cont}

