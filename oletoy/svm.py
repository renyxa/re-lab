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

#
# Based on SPEC from Inge Wallin/Pierre Ducroquet
#

import struct

def Line (hd, size, value):
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "X", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Y", 1, struct.unpack("<i",value[10:14])[0],2,10,3,4,4,"<i")

def Rect (hd, size, value):
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "X1", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Y1", 1, struct.unpack("<i",value[10:14])[0],2,10,3,4,4,"<i")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "X2", 1, struct.unpack("<i",value[14:18])[0],2,14,3,4,4,"<i")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Y2", 1, struct.unpack("<i",value[18:22])[0],2,18,3,4,4,"<i")

def TextArray (hd, size, value):
	Line (hd, size, value)
	txtlen =  struct.unpack("<H",value[14:16])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Txt Len", 1, txtlen,2,8,3,2,4,"<H")
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "Text", 1, value[16:16+txtlen],2,16,3,txtlen,4,"txt")
	offset = 16 + txtlen
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "n1?", 1, "%02x"%struct.unpack("<H",value[offset:offset+2]),2,offset,3,2,4,"<H")
	offset += 2
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "n2?", 1, "%02x"%struct.unpack("<H",value[offset:offset+2]),2,offset,3,2,4,"<H")
	offset += 2
	dxarr = struct.unpack("<I",value[offset:offset+4])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "DX array len", 1, dxarr,2,offset,3,4,4,"<I")
	offset += 4
	for i in range(dxarr):
		iter1 = hd.model.append(None, None)
		hd.model.set (iter1, 0, "  dx %d"%i, 1, struct.unpack("<I",value[offset:offset+4])[0],2,offset,3,4,4,"<I")
		offset += 4
	
svm_ids = {0x67:Rect,0x81:Rect,0x71:TextArray}

svm_actions = { 0x0:"NULL",
0x64:"Pixel", 0x65:"Point", 0x66:"Line", 0x67:"Rect", 0x68:"RoundRect",
0x69:"Ellipse", 0x6A:"Arc", 0x6B:"Pie", 0x6C:"Chord", 0x6D:"Polyline",
0x6E:"Polygon", 0x6F:"Polypolygon",
0x70:"Text", 0x71:"TextArray", 0x72:"StretchText", 0x73:"TextRect",
0x74:"BMP", 0x75:"BMPScale", 0x76:"BMPScalePart", 0x77:"BMPEx",
0x78:"BMPExScale", 0x79:"BMPExScalePart", 0x7A:"Mask", 0x7B:"MaskScale",
0x7C:"MaskScalePart", 0x7D:"Gradient", 0x7E:"Hatch", 0x7F:"Wallpaper",
0x80:"ClipRegion", 0x81:"ISectRectClipRegion", 0x82:"ISectRegionClipRegion",
0x83:"MoveClipRegion", 0x84:"LineColor", 0x85:"FillColor", 0x86:"TextColor",
0x87:"TextFillColor", 0x88:"TextAlign", 0x89:"MapMode", 0x8A:"Font",
0x8B:"Push", 0x8C:"Pop", 0x8D:"RasterOp", 0x8E:"Transparent", 0x8F:"EPS",
0x90:"RefPoint", 0x91:"TextLineColor", 0x92:"TextLine",
0x93:"FloatTransparent", 0x94:"GradientEx", 0x95:"LayoutMode",
0x96:"TextLanguage", 0x97:"OverlineColor",
0x200:"Comment"}

def open (buf,page,parent):
	offset = 0
	iter1 = page.model.append(parent,None)
	page.model.set_value(iter1,0,'Signature')
	page.model.set(iter1,1,("svm",-2),2,6,3,buf[0:6])
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	offset += 6

	[hver] = struct.unpack("<h",buf[offset:offset+2])
	[hsize] = struct.unpack("<I",buf[offset+2:offset+6])
	iter1 = page.model.append(parent,None)
	page.model.set(iter1,0,'Header')
	page.model.set(iter1,1,("svm",-1),2,6+hsize,3,buf[offset:offset+6+hsize])
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	offset += 6 + hsize

	while offset < len(buf):
		[cmd] = struct.unpack("<h",buf[offset:offset+2])
		[ver] = struct.unpack("<h",buf[offset+2:offset+4])
		[size] = struct.unpack("<I",buf[offset+4:offset+8])
		cmdname = "Cmd %02x"%cmd
		if cmd in svm_actions:
			cmdname = svm_actions[cmd]+ " "*(21-len(svm_actions[cmd]))
		iter1 = page.model.append(parent,None)
		page.model.set(iter1,0,cmdname,1,("svm",cmd),2,size+8,3,buf[offset:offset+size+8])
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += size + 8
