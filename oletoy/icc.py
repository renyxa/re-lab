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
import gtk
from utils import *

def header (hd,size,data):
	pass

def element (hd,size,data):
	pass

def parse (page, data, parent):
	off = 0
	add_pgiter(page,"Header","icc","hdr",data[0:0x80],parent)
	off = 0x80
	num = struct.unpack(">I",data[off:off+4])[0]
	ttiter = add_pgiter(page,"Tag Table","icc","tagtable",data[off:off+4],parent)
	off += 4
	eliter = add_pgiter(page,"Elements","icc","elems",data[off+num*12:],parent)

	for i in range(num):
		toff = struct.unpack(">I",data[off+4:off+8])[0]
		tlen = struct.unpack(">I",data[off+8:off+12])[0]
		add_pgiter(page,"%s [%02x %02x]"%(data[off:off+4],toff,tlen),"icc","tag",data[off:off+12],ttiter)
		off += 12
		add_pgiter(page,data[off:off+4],"icc","elem",data[toff:toff+tlen],eliter)
