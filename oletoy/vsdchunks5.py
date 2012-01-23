# Copyright (C) 2007-2012,	Valek Filippov (frob@df.ru)
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
import datetime
import vsd,vsdblock
from utils import *

def List (hd, size, value):
	shl = struct.unpack("<I",value[8:8+4])[0]
	add_iter(hd,"SubHdrLen","%2x"%shl,8,4,"<I")
	ch_list_len = struct.unpack("<H",value[0xc:0xc+2])[0]
	add_iter(hd,"ChldLstLen", "%2x"%ch_list_len,0xc,2,"<H")
	add_iter(hd,"SubHdr","",0xc,shl,"txt")

def Shape (hd, size, value):
	add_iter (hd, "Parent", "%2x"%struct.unpack("<H",value[0xe:0x10])[0],0xe,2,"<H")
	add_iter (hd, "Master", "%2x"%struct.unpack("<H",value[0x10:0x12])[0],0x10,2,"<H")
	add_iter (hd, "MasterShape", "%2x"%struct.unpack("<H",value[0x12:0x14])[0],0x12,2,"<H")
	add_iter (hd, "FillStyle", "%2x"%struct.unpack("<H",value[0x16:0x18])[0],0x16,2,"<H")
	add_iter (hd, "LineStyle", "%2x"%struct.unpack("<H",value[0x18:0x1a])[0],0x18,2,"<H")
	add_iter (hd, "TextStyle", "%2x"%struct.unpack("<H",value[0x1a:0x1c])[0],0x1a,2,"<H")

def NameID (hd, size, value):
	numofrec = struct.unpack("<H",value[12:12+2])[0]
	add_iter (hd, "#ofRecords","%2x"%numofrec,12,2,"<H")
	for i in range(numofrec):
		n1 = struct.unpack("<H",value[14+i*4:16+i*4])[0]
		n2 = struct.unpack("<H",value[16+i*4:18+i*4])[0]
		add_iter (hd, "Rec #%d"%i,"%2x %2x"%(n1,n2),14+i*4,4,"txt")

