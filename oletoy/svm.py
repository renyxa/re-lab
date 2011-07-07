# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
#
# Based on SPEC from Inge Wallin/Pierre Ducroquet
#

import struct

def Line (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, struct.unpack("<i",value[10:14])[0],2,10,3,4,4,"<i")

def Rect (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X1", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y1", 1, struct.unpack("<i",value[10:14])[0],2,10,3,4,4,"<i")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X2", 1, struct.unpack("<i",value[14:18])[0],2,14,3,4,4,"<i")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y2", 1, struct.unpack("<i",value[18:22])[0],2,18,3,4,4,"<i")

def TextArray (hd, size, value):
	Line (hd, size, value)
	txtlen =  struct.unpack("<H",value[14:16])[0]
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Txt Len", 1, txtlen,2,8,3,2,4,"<H")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Text", 1, value[16:16+txtlen],2,16,3,txtlen,4,"txt")
	offset = 16 + txtlen
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "n1?", 1, "%02x"%struct.unpack("<H",value[offset:offset+2]),2,offset,3,2,4,"<H")
	offset += 2
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "n2?", 1, "%02x"%struct.unpack("<H",value[offset:offset+2]),2,offset,3,2,4,"<H")
	offset += 2
	dxarr = struct.unpack("<I",value[offset:offset+4])[0]
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "DX array len", 1, dxarr,2,offset,3,4,4,"<I")
	offset += 4
	for i in range(dxarr):
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "  dx %d"%i, 1, struct.unpack("<I",value[offset:offset+4])[0],2,offset,3,4,4,"<I")
		offset += 4
	
svm_ids = {0x67:Rect,0x81:Rect,0x71:TextArray}

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
	page.model.set(iter1,0,'Header')
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
		offset += 2
		iter1 = page.model.append(None,None)
		page.model.set(iter1,0,cmdname,1,("svm",cmd),2,size+6,3,buf[offset:offset+size+6])
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += size + 6
