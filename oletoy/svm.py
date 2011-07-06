# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
#
# Based on SPEC from Inge Wallin/Pierre Ducroquet
#

import struct

def Line (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, struct.unpack("<I",value[0:4])[0],2,0,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, struct.unpack("<I",value[4:8])[0],2,4,3,4,4,"<I")

def Rect (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X1", 1, struct.unpack("<I",value[0:4])[0],2,0,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y1", 1, struct.unpack("<I",value[4:8])[0],2,4,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X2", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y2", 1, struct.unpack("<I",value[12:16])[0],2,12,3,4,4,"<I")

svm_ids = {0x67:Rect}

svm_actions = { 0x0:"NULL",
0x64:"PIXEL", 0x65:"POINT", 0x66:"LINE", 0x67:"RECT", 0x68:"ROUNDRECT",
0x69:"ELLIPSE", 0x6A:"ARC", 0x6B:"PIE", 0x6C:"CHORD", 0x6D:"POLYLINE",
0x6E:"POLYGON", 0x6F:"POLYPOLYGON",
0x70:"TEXT", 0x71:"TEXTARRAY", 0x72:"STRETCHTEXT", 0x73:"TEXTRECT",
0x74:"BMP", 0x75:"BMPSCALE", 0x76:"BMPSCALEPART", 0x77:"BMPEX",
0x78:"BMPEXSCALE", 0x79:"BMPEXSCALEPART", 0x7A:"MASK", 0x7B:"MASKSCALE",
0x7C:"MASKSCALEPART", 0x7D:"GRADIENT", 0x7E:"HATCH", 0x7F:"WALLPAPER",
0x80:"CLIPREGION", 0x81:"ISECTRECTCLIPREGION", 0x82:"ISECTREGIONCLIPREGION",
0x83:"MOVECLIPREGION", 0x84:"LINECOLOR", 0x85:"FILLCOLOR", 0x86:"TEXTCOLOR",
0x87:"TEXTFILLCOLOR", 0x88:"TEXTALIGN", 0x89:"MAPMODE", 0x8A:"FONT",
0x8B:"PUSH", 0x8C:"POP", 0x8D:"RASTEROP", 0x8E:"TRANSPARENT", 0x8F:"EPS",
0x90:"REFPOINT", 0x91:"TEXTLINECOLOR", 0x92:"TEXTLINE",
0x93:"FLOATTRANSPARENT", 0x94:"GRADIENTEX", 0x95:"LAYOUTMODE",
0x96:"TEXTLANGUAGE", 0x97:"OVERLINECOLOR",
0x200:"COMMENT"}

def open (buf,page):
	offset = 0
	iter1 = page.model.append(None,None)
	page.model.set_value(iter1,0,'Signature')
	page.model.set(iter1,1,("svm",-2),2,6,3,buf[0:6])
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	offset += 6

	[hver] = struct.unpack("<h",buf[offset:offset+2])
	[hsize] = struct.unpack("<I",buf[offset+2:offset+6])
	iter1 = page.model.append(None,None)
	page.model.set_value(iter1,0,'Header               \t%02x %02x'%(hver,hsize))
	page.model.set(iter1,1,("svm",-1),2,6+hsize,3,buf[offset:offset+6+hsize])
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	offset += 6 + hsize

	while offset < len(buf):
		[cmd] = struct.unpack("<h",buf[offset:offset+2])
		[ver] = struct.unpack("<h",buf[offset+2:offset+4])
		[size] = struct.unpack("<I",buf[offset+4:offset+8])
		cmdname = "Cmd %02x"%cmd
		if svm_actions.has_key(cmd):
			cmdname = svm_actions[cmd]+ " "*(21-len(svm_actions[cmd]))
		offset += 8
		iter1 = page.model.append(None,None)
		page.model.set_value(iter1,0,cmdname + '\t%02x %02x'%(ver,size))
		page.model.set(iter1,1,("svm",cmd),2,size,3,buf[offset:offset+size])
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += size
