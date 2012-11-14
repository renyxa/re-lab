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


def PageProps (hd, size, value):
	for i in range(6):
		add_iter (hd, "x%d"%i, "%.2f"%struct.unpack("<d",value[i*9+1:i*9+9]),i*9+1,8,"<d")
	for i in range(4):
		add_iter(hd,"x%d"%(i+6),"%2d"%ord(value[i+54]),i+54,1,"B")

def TextBlock (hd, size, value):
	for i in range(4):
		add_iter (hd, "x%d"%i, "%.2f"%struct.unpack("<d",value[i*9+1:i*9+9]),i*9+1,8,"<d")
	for i in range(2):
		add_iter(hd,"x%d"%(i+6),"%2d"%ord(value[i+36]),i+36,1,"B")

def XForm (hd, size, value):
	for i in range(7):
		add_iter (hd, "x%d"%i, "%.2f"%struct.unpack("<d",value[i*9+1:i*9+9]),i*9+1,8,"<d")

def TxtXForm (hd, size, value):
	for i in range(7):
		add_iter (hd, "x%d"%i, "%.2f"%struct.unpack("<d",value[i*9+2:i*9+10]),i*9+2,8,"<d")

def MoveTo (hd, size, value):
	off = 0
	if ord(value[0]) < 32:
		off += 1
	for i in range(2):
		add_iter (hd, "x%d"%i, "%.2f"%struct.unpack("<d",value[i*9+1+off:i*9+9+off]),i*9+1+off,8,"<d")

def LineTo (hd, size, value):
	for i in range(2):
		add_iter (hd, "x%d"%i, "%.2f"%struct.unpack("<d",value[i*9+1:i*9+9]),i*9+1,8,"<d")


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

chnk_func = {
#	0xe:Text,
#	0x15:Page,
#	0x19:Font,
#	0x28:ShapeStencil,
#	0xd:List,0x2c:List,
#	0x46:Shape,0x47:Shape, 0x48:Shape, 0x4a:Shape,0x4d:Shape, 0x4e:Shape,0x4f:Shape,
#	0x64:List,0x65:List,0x66:List,0x67:List,0x68:List,0x69:List,0x6a:List,0x6b:List,0x6c:List,
#	0x6d:List,0x6e:List,0x6f:List,0x70:List,0x71:List,0x72:List,0x76:List,
#	0x85:Line,0x86:Fill,
	0x87:TextBlock,
#	0x89:Geometry,
	0x8a:MoveTo,
	0x8b:LineTo,
#	0x8c:ArcTo,0x8d:InfLine,
#	0x8f:Ellipse,0x90:EllArcTo,
	0x92:PageProps,
#	0x93:StyleProps,
#	0x94:Char,0x95:Para,0x98:FrgnType,
	0x9b:XForm,0x9c:TxtXForm,
#	0x9d:XForm1D,
#	0xa1:TextField,0xa5:SplineStart,0xa6:SplineKnot,0xa8:LayerIX,0xaa:Control,
#	0xc0:PageLayout,0xc1:Polyline,0xc3:NURBS, 0xc9:NameID,
#	0xd1:ShapeData
}
