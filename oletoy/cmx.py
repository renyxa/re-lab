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
	# version major: "1" - 16 bits, "2" - 32 bits
	add_iter (hd, "Version maj", data[off:off+4],off,4,"<I")
	off += 4
	# version minor: "0"
	add_iter (hd, "Version min", data[off:off+4],off,4,"<I")
	off += 4
	# coord units: 0x23 - mm, 0x40 - inches
	add_iter (hd, "Coord Units", struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	# precision factor
	add_iter (hd, "Precision", struct.unpack("<d",data[off:off+8])[0],off,8,"<d")
	off += 8
	# not used "Option", "FrgnKey", "Capability"
	add_iter (hd, "Not used", "",off,12,"txt")
	off += 12
	# index section offset
	add_iter (hd, "Idx Section Offset", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# info section offset
	add_iter (hd, "Info Section Offset", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# Thumbnail section offset
	add_iter (hd, "Thumbnail Section Offset", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# min X coord in the file
	add_iter (hd, "Min X coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# max Y coord in the file
	add_iter (hd, "Max Y coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# max X coord in the file
	add_iter (hd, "Max X coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# min Y coord in the file
	add_iter (hd, "Min Y coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# num of instructions in pages
	add_iter (hd, "# of instructions", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# reserved
	add_iter (hd, "Reserved", "",off,64,"txt")
	off += 64


	

	
	
	

cmx_ids = {"cont":cont}

