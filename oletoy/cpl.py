# Copyright (C) 2007,2010,2011	Valek Filippov (frob@df.ru)
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


# Corel palettes

import sys,struct,gtk,gobject
from utils import *

def open(buf,page,parent):
	iter = add_pgiter(page,"Sig","cpl","sig",buf[0:2],parent)
	num = struct.unpack("<H",buf[2:4])[0]
	iter = add_pgiter(page,"# of Entries (%d)"%num,"cpl","num",buf[2:4],parent)
	off = 4
	piter = add_pgiter(page,"Entries","cpl","","",parent)
	for i in range(num):
		type = ord(buf[off])
		subtype = ord(buf[off+2])
		c = ord(buf[off+8])
		m = ord(buf[off+9])
		y = ord(buf[off+10])
		k = ord(buf[off+11])
		nlen = ord(buf[off+12])
		n = buf[off+13:off+13+nlen]
		off += 13+nlen
		clr = "%02x %02x %02x %02x"%(c,m,y,k)
		iter = add_pgiter(page,"%d\t(%02x/%02x)\t%s\t%s"%(i+1,type,subtype,clr,n),"cpl","pal",buf[off:off+13+nlen],piter)
