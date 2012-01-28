# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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
import tree
import hexdump
from utils import *

def open (data,page):
	f_iter = add_pgiter(page,"CDW file","cdw",0,data)
	add_pgiter(page,"Header","cdw",0,data[:0x18],f_iter)
	tr_off = struct.unpack("<I",data[0x8:0xc])[0]
	tr_num = struct.unpack("<I",data[0xc:0x10])[0]
	tr_iter = add_pgiter(page,"Trailer","cdw",0,data[tr_off:],f_iter)
	for i in range(tr_num):
		rec_off = struct.unpack("<I",data[tr_off+i*6:tr_off+i*6+4])[0]
		rec_len = struct.unpack("<H",data[tr_off+i*6+4:tr_off+i*6+6])[0]
		add_pgiter(page,"Rec %02x [%02x]"%(i,rec_off),"cdw",0,data[rec_off:rec_off+rec_len],tr_iter)
