#!/usr/bin/env python
import sys,struct,zlib

def add_iter (hd,name,value,offset,length,vtype):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype)

def d2hex(data):
	hex = ''
	for i in range(len(data)):
		hex += "%02x"%ord(data[i])
	return hex


vmp_rec = {0x0321:"Name?",
0x065b:"?",
0x15e3:"Txt Align", # 0 left, 1 right, 2 center, 3 justify, 
0x15ea:"?",
0x15f2:"?",
0x15f9:"?",
0x1604:"?",
0x160b:"?",
0x1614:"?",
0x161c:"Spc % Letter Max",
0x1624:"Spc % Word Max",
0x162b:"?",
0x1634:"Spc % Letter Min",
0x163c:"Spc % Word Min",
0x1644:"?",
0x164c:"Spc % Letter Opt",
0x1654:"Spc % Word Opt",
0x165c:"?",
0x1664:"?",
0x166b:"?",
0x1674:"?",
0x167c:"?",
0x1684:"ParaSpc Below",
0x168c:"ParaSpc Above",
0x1691:"TabTable ID",
0x169c:"BaseLn Shift" ,
0x16a2:"?",
0x16aa:"?",
0x16b1:"?",
0x16b9:"Txt Color ID",
0x16c1:"Font ID",
0x16c9:"?",
0x16d4:"Hor Scale %",
0x16dc:"Leading",
0x16e3:"Leading Type", # 0 +, 1 =, 2 % 
0x16ec:"Rng Kern %",
0x16f1:"?",
0x16fb:"?",
0x1729:"?",
0x1734:"?",
0x1739:"?",
0x1743:"?",
0x1749:"?",
0x1c24:"?",
0x1c2c:"?",
0x1c34:"?",
0x1c3c:"?",
0x1c43:"?",
0x1c4c:"?",
0x1c51:"?",
0x1c71:"?",
0x1c7c:"?",
0x1c84:"?",
0x1c89:"?",
	}


def hdVMpObj(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if vmp_rec.has_key(rec):
			rname = vmp_rec[rec]
		else:
			rname = 'Unkn rec %04x'%rec
		if rname == "?":
			rname = 'Unkn rec %04x'%rec
		if key == 2:
			add_iter (hd,rname,d2hex(data[shift+4:shift+6]),shift,6,"txt")
			shift+=6
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8

	

def hdAGDFont(hd,data,page):
	offset = 0
	fsize = struct.unpack('>H', data[offset+26:offset+28])[0]
	fstyle = ord(data[offset+21])
	fstxt = 'Plain'
	if fstyle == 1:
		fstxt = 'Bold'
	if fstyle == 2:
		fstxt = 'Italic'
	if fstyle == 3:
		fstxt = 'BoldItalic'
	add_iter (hd,'Font Style',fstxt,21,1,"B")
	add_iter (hd,'Font Size',fsize,26,2,">h")

def hdLinearFill(hd,data,page):
	offset = 0
	# 2-4 -- angle1
	# 11 -- overprint
	# 16-20 -- X
	# 20-24 -- Y
	# 24-28 -- <->1
	# 28-30 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 30-32 -- repeat

def hdNewRadialFill(hd,data,page):
	offset = 0
	# 2-6 -- X
	# 6-10 -- Y
	# 15 -- overprint
	# 22-24 -- angle1
	# 26-30 -- <-> Hndl1
	# 30-32 -- angle2
	# 34-38 -- <-> Hndl2
	# 38-40 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 40-42 -- repeat

def hdNewContourFill(hd,data,page):
	offset = 0
	# 2-6 -- X
	# 6-10 -- Y
	# 10-12 -- Taper
	# 15 -- overprint
	# 18-20 -- link to ColorList
	# 20-22 -- link to GraphicStyle
	# 22-24 -- angle1
	# 26-30 -- <-> Hndl1
	# 31 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 32-34 -- repeat

def hdLensFill(hd,data,page):
	offset = 0
	# 39: 0 -- Transparency, 1 -- Magnify, 2 -- Lighten, 3 -- Darken, 4 -- Invert, 5 -- Monochrome
	# Transparency
	# 8-10.10-12 -- Opacity
	# 26-30 -- X
	# 30-34 -- Y
	# 37: 1 -- CenterPoint, 2 -- ObjOnly, 4 -- Snapshot (flags)
	# Magnify
	# 8-10.10-12 -- mag.coeff
	
def hdBendFilter(hd,data,page):
	offset = 0
	# 0-2  -- Size
	# 2-4.4-6 -- X
	# 6-8.8-10 -- Y


def hdLayer(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	mode = ord(data[offset+9])
	lmtxt = 'Normal'
	if mode&0x10 == 0x10:
		lmtxt = 'Wire'
	if mode&0x1 == 1:
		lmtxt += ' Locked'
	visib = ord(data[offset+17])
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'View mode',lmtxt,offset+9,1,"txt")
	add_iter (hd,'Visible',visib,offset+17,1,"B")

def hdRectangle(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	xform = struct.unpack('>H', data[offset+16:offset+18])[0]
	x1 = struct.unpack('>H', data[offset+18:offset+20])[0] - 1692
	x1f = struct.unpack('>H', data[offset+20:offset+22])[0]
	y1 = struct.unpack('>H', data[offset+22:offset+24])[0] - 1584
	y1f = struct.unpack('>H', data[offset+24:offset+26])[0]
	x2 = struct.unpack('>H', data[offset+26:offset+28])[0] - 1692
	x2f = struct.unpack('>H', data[offset+28:offset+30])[0]
	y2 = struct.unpack('>H', data[offset+30:offset+32])[0] - 1584
	y2f = struct.unpack('>H', data[offset+32:offset+34])[0]
	rtlt = struct.unpack('>H', data[offset+34:offset+36])[0]
	rtltf = struct.unpack('>H', data[offset+36:offset+38])[0]
	rtll = struct.unpack('>H', data[offset+38:offset+40])[0]
	rtllf = struct.unpack('>H', data[offset+40:offset+42])[0]
	rtrt = struct.unpack('>H', data[offset+42:offset+44])[0]
	rtrtf = struct.unpack('>H', data[offset+44:offset+46])[0]
	rtrr = struct.unpack('>H', data[offset+46:offset+48])[0]
	rtrrf = struct.unpack('>H', data[offset+48:offset+50])[0]
	rbrb = struct.unpack('>H', data[offset+50:offset+52])[0]
	rbrbf = struct.unpack('>H', data[offset+52:offset+54])[0]
	rbrr = struct.unpack('>H', data[offset+54:offset+56])[0]
	rbrrf = struct.unpack('>H', data[offset+56:offset+58])[0]
	rblb = struct.unpack('>H', data[offset+58:offset+60])[0]
	rblbf = struct.unpack('>H', data[offset+60:offset+62])[0]
	rbll = struct.unpack('>H', data[offset+62:offset+64])[0]
	rbllf = struct.unpack('>H', data[offset+64:offset+66])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	add_iter (hd,'XForm',"%02x"%xform,16,2,">h")
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),18,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),22,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),26,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),30,4,"txt")
	add_iter (hd,'Rad TopLeft (Top)',"%.4f"%(rtlt+rtltf/65536.),34,4,"txt")
	add_iter (hd,'Rad TopLeft (Left)',"%.4f"%(rtll+rtllf/65536.),38,4,"txt")
	add_iter (hd,'Rad TopRight (Top)',"%.4f"%(rtrt+rtrtf/65536.),42,4,"txt")
	add_iter (hd,'Rad TopRight (Right)',"%.4f"%(rtrr+rtrrf/65536.),46,4,"txt")
	add_iter (hd,'Rad BtmRight (Btm)',"%.4f"%(rbrb+rbrbf/65536.),50,4,"txt")
	add_iter (hd,'Rad BtmRight (Right)',"%.4f"%(rbrr+rbrrf/65536.),54,4,"txt")
	add_iter (hd,'Rad BtmLeft (Btm)',"%.4f"%(rblb+rblbf/65536.),58,4,"txt")
	add_iter (hd,'Rad BtmLeft (Left)',"%.4f"%(rbll+rbllf/65536.),62,4,"txt")

def hdOval(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	xform = struct.unpack('>H', data[offset+16:offset+18])[0]
	x1 = struct.unpack('>H', data[offset+18:offset+20])[0] - 1692
	x1f = struct.unpack('>H', data[offset+20:offset+22])[0]
	y1 = struct.unpack('>H', data[offset+22:offset+24])[0] - 1584
	y1f = struct.unpack('>H', data[offset+24:offset+26])[0]
	x2 = struct.unpack('>H', data[offset+26:offset+28])[0] - 1692
	x2f = struct.unpack('>H', data[offset+28:offset+30])[0]
	y2 = struct.unpack('>H', data[offset+30:offset+32])[0] - 1584
	y2f = struct.unpack('>H', data[offset+32:offset+34])[0]
	arc1 = struct.unpack('>H', data[offset+34:offset+36])[0]
	arc1f = struct.unpack('>H', data[offset+36:offset+38])[0]
	arc2 = struct.unpack('>H', data[offset+38:offset+40])[0]
	arc2f = struct.unpack('>H', data[offset+40:offset+42])[0]
	clsd = ord(data[offset+42])
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	add_iter (hd,'XForm',"%02x"%xform,16,2,">h")
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),18,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),22,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),26,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),30,4,"txt")
	add_iter (hd,'Arc <>',"%.4f"%(arc1+arc1f/65536.),34,4,"txt")
	add_iter (hd,'Arc ()',"%.4f"%(arc2+arc2f/65536.),38,4,"txt")
	add_iter (hd,'Closed',clsd,42,1,"B")

def hdGroup(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	xform = struct.unpack('>H', data[offset+16:offset+18])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	add_iter (hd,'XForm',"%02x"%xform,16,2,">h")

def hdBasicLine(hd,data,page):
	offset = 0
	clr = struct.unpack('>H', data[offset:offset+2])[0] # link to color chunk????
	dash = struct.unpack('>H', data[offset+2:offset+4])[0] # link to linepat chunk
	larr = struct.unpack('>H', data[offset+4:offset+6])[0] # link to arrowpat chunk
	rarr = struct.unpack('>H', data[offset+6:offset+8])[0] # link to arrowpat chunk

	mit = struct.unpack('>H', data[offset+8:offset+10])[0]
	mitf = struct.unpack('>H', data[offset+10:offset+12])[0]
	w = struct.unpack('>H', data[offset+12:offset+14])[0]
	overprint = ord(data[offset+17])
	join = ord(data[offset+18]) # 0 - angle, 1 - round, 2 - square
	cap = ord(data[offset+19]) # 0 - none, 1 - round, 2 - square
	add_iter (hd,'Miter',"%.4f"%(mit+mitf/65536.),8,4,"txt")
	add_iter (hd,'Width',w,12,2,">H")

def hdList(hd,data,page):
	offset = 0
	ltype = struct.unpack('>H', data[offset+10:offset+12])[0]
	ltxt = "%02x"%ltype
	if page.dict.has_key(ltype):
		ltxt += " (%s)"%page.dict[ltype][0]
		add_iter (hd,'List Type',ltxt,10,2,">H")

def hdColor6(hd,data,page):
	offset = 0
	ustr1 = struct.unpack('>H', data[offset+2:offset+4])[0]
	ustr2 = struct.unpack('>H', data[offset+14:offset+16])[0]
	add_iter (hd,'Name1?',"%02x"%ustr1,2,2,">h")
	add_iter (hd,'Name2?',"%02x"%ustr2,14,2,">h")

hdp = {'Rectangle':hdRectangle,"BasicLine":hdBasicLine,"Oval":hdOval,"Group":hdGroup,"AGDFont":hdAGDFont,'Layer':hdLayer,
			"List":hdList,"MList":hdList,"BrushList":hdList,
			"Color6":hdColor6,"SpotColor6":hdColor6,"TintColor6":hdColor6,
			"VMpObj":hdVMpObj,}


class parser:
	def  __init__(self):
		self.version = 0
		self.data = None
		self.iter = None

def CustomProc(parser,offset,key):
	length=48
	return length


def TFOnPath(parser,offset,key):
	[num] = struct.unpack('>h', parser.data[offset+4:offset+6])
	shift = 26
	for i in range(num):
		[key] = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])
		if key == 2:
			shift+=6
		else:
			shift+=8
	return shift

def SwfImport(parser,offset,key):
	length= 43
	return length

def FWSharpenFilter(parser,offset,key):
	length= 16
	return length

def RadialFill(parser,offset,key):
	length= 16
	return length

def PatternFill(parser,offset,key):
	length= 10
	return length

def PatternLine(parser,offset,key):
	# 0-2 -- link to Color
	# 2-10 -- bitmap of the pattern
	# 10-14 -- mitter?
	# 14-16 -- width?
	length= 22
	return length

def PSLine(parser,offset,key):
	# 0-2 -- link to Color
	# 2-4 -- link to UString with PS commands
	# 4-6 width
	length= 8
	return length


def PathTextLineInfo(parser,offset,key):
# SHOULD BE VARIABLE, just have no idea about base and multiplier
	length= 46
	return length

def Envelope(parser,offset,key):
	[type] = struct.unpack('>h', parser.data[offset+20:offset+22])
	length= 204 # 'type = 5'
	if type == 8:
		length = 297
	return length

def CalligraphicStroke(parser,offset,key):
	length= 16
	return length

def PolygonFigure(parser,offset,key):
	length= 53
	return length

def BendFilter(parser,offset,key):
	length= 10
	return length

def FWFeatherFilter(parser,offset,key):
	length= 8
	return length

def ExpandFilter(parser,offset,key):
	length= 14
	return length

def TransformFilter(parser,offset,key):
	length= 39
	return length

def NewContourFill(parser,offset,key):
	length= 34
	return length

def CharacterFill(parser,offset,key):
	length= 0
	return length

def ConeFill(parser,offset,key):
	length= 34
	return length

def TileFill(parser,offset,key):
	length= 32
	return length

def DuetFilter(parser,offset,key):
	length= 14
	return length

def FWBlurFilter(parser,offset,key):
	length= 12
	return length

def FWGlowFilter(parser,offset,key):
	length= 22 #was 38
	return length

def ConnectorLine(parser,offset,key):
	length= 166
	return length

def OpacityFilter(parser,offset,key):
	length= 4
	return length

def RaggedFilter(parser,offset,key):
	length= 16
	return length

def NewRadialFill(parser,offset,key):
	length= 43
	return length
	
def SketchFilter(parser,offset,key):
	length= 11
	return length
	
def BrushTip(parser,offset,key):
	[type] = struct.unpack('>h', parser.data[offset:offset+2])
	length= 62
	if parser.version == 11:
		length=66 
	if parser.version == 10:
		length =62
	return length
	
def Brush(parser,offset,key):
	length=4
	return length
	
def UString(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	length=4*(size+1)
	return length

def Xform(parser,offset,key):
	length=4
	var1 = ord(parser.data[offset])
	var2 = ord(parser.data[offset+1])

	if var1 == 3:
		if var2 == 0xf0 or var2 == 0x60:
			length = 52
		elif var2 == 0x90: #03 90
			length = 36
		elif var2 == 0xb0 or var2 == 0xd0:
			length = 44 # 03 b0, 03 d0
			
	if var1 == 0x31: # 31 90
		if var2 == 0x90:
			length = 12
	if var1 == 0x33: 
		if var2 == 0x90: # 33 90
			length = 20
		if var2 == 0xd0: # 33 d0
			length = 28
		if var2 == 0xf0: # 33 f0
			length = 44
	if var1 == 0x32: # 32 90
		length = 12
		if var2 == 0xb0: # 32 b0
			length = 20
	if var1 == 0x01 and var2 == 0x90: # 01 90
		length = 28


	return length
	
def SymbolClass(parser,offset,key):
	length=10
	return length

def SymbolInstance(parser,offset,key):
	var1 = ord(parser.data[offset+0xe])
	var2 = ord(parser.data[offset+0xf])
	
	length=24 # was 32
	if (var1 == 0x0b or var1==3) and var2 == 0x90:
		length=32
	elif var1 == 3 and var2 == 0xf0:
		length=40
	elif var1 == 0x23 and var2 == 0x90:
		length=28
	return length

def MasterPageSymbolInstance(parser,offset,key):
	# has 0x34 90
	length=18
	return length

def MasterPageLayerInstance(parser,offset,key):
# has 0x33 90
	length=26
	return length

def PerspectiveGrid(parser,offset,key):
	i = 0
	while ord(parser.data[offset+i]) != 0:
		i += 1
	length=59+i
	return length
	
def MpObject(parser,offset,key):
	length=4   #!!!! just to set to non-zero!!!!
	return length
	
def MString(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	length=4*(size+1)
	return length

def MList(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset+2:offset+4])
	length=size*2+12
	return length
	
def MDict(parser,offset,key):
	length=4   #!!!! just to set to non-zero!!!!
	return length

def DateTime(parser,offset,key):
	length=14
	return length

def MasterPageElement(parser,offset,key):
	length=14
	return length

def MasterPageDocMan(parser,offset,key):
	length=4
	return length

def MasterPageSymbolClass(parser,offset,key):
	length=12
	return length

def MasterPageLayerElement(parser,offset,key):
	length=14
	return length

def MQuickDict(parser,offset,key):
	length=407
	return length

def FHDocHeader(parser,offset,key):
	length=4   #!!!! just to set to non-zero!!!!
	return length

def Block(parser,offset,key):
	length=53 #really? was 49
	if parser.version == 10:
		length =49
	if parser.version == 9:
		length = 47
	return length

def Element(parser,offset,key):
	length=4   #!!!! just to set to non-zero!!!!
	return length

def BrushList(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset+2:offset+4])
	length= size*2+12
	return length
	
def VMpObj(parser,offset,key):
	[num] = struct.unpack('>h', parser.data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', parser.data[offset+shift+2:offset+shift+4])[0]
		if not vmp_rec.has_key(rec):
			print 'Unknown VMpObj record: %04x'%rec
		
		if key == 2:
			shift+=6
		else:
			shift+=8
	
	return shift

def TextInPath(parser,offset,key):
	[num] = struct.unpack('>h', parser.data[offset+4:offset+6])
	shift = 20
	for i in range(num):
		[key] = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])
		if key == 2:
			shift+=6
		else:
			shift+=8
	return shift

def ImageFill(parser,offset,key):
	length=6
	return length

def AGDFont(parser,offset,key):
	[num] = struct.unpack('>h', parser.data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		[key] = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])
		if key == 2:
			shift+=6
		else:
			shift+=8
	return shift

def FileDescriptor(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset+9:offset+11])
	#length=51 # can be 67
	length=11+size
	return length
	
def TabTable(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	length = 4+size*6
	return length
	
def SymbolLibrary(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset+2:offset+4])
	length= size*2+18
	return length

def PropLst(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset+2:offset+4])
##	if size == 0:
##		length=10
##	else:
	length=8+4*size
	#hexprint(data,offset,length,key)
	return length
	
def Procedure(parser,offset,key):
	length = 4 #!!!! just to set non-zero !!!
	return length

def TEffect(parser,offset,key):
	length = 14
	return length


def Color6(parser,offset,key):
	length=28
	var = ord(parser.data[offset+1])
	if var == 4:
		length=32
	if var == 7:
		length=44

	if parser.version < 10:
		length-=2
	return length

def Data(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	length= 6+size*4
	return length
	
def MName(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	length=4*(size+1)
	return length

def List(parser,offset,key):
	var = ord(parser.data[offset+1])
	if var ==0x3c:
		length=16
	else:
		[size] = struct.unpack('>h', parser.data[offset+2:offset+4])
		length=12+2*size
	return length
	
def LinePat(parser,offset,key):
	[numstrokes] = struct.unpack('>h', parser.data[offset:offset+2])
	length=10+numstrokes*4
	if numstrokes == 0:
		length = 28 # for Ver8, to skip 1st 14 bytes of 0s
	return length
	
def ElemList(parser,offset,key):
	length = 4 #!!!! just to set it to non-zero !!!!
	return length

def ElemPropLst(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset+2:offset+4])
	length= 10 + 4*size
	return length
		
def Figure(parser,offset,key):
	length = 4	#!!!! just to set it to non-zero !!!!
	return length

def StylePropLst(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset+2:offset+4])
	length= size*4+10
	return length
	
def SpotColor6(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	[name_idx] = struct.unpack('>h', parser.data[offset+2:offset+4])
	length = 28 + size*4
	if parser.version < 10:
		length = 38
	return length

def BasicLine(parser,offset,key):
	##length=20 ##ver10
	length= 20 ##ver11
	return length
	
def BasicFill(parser,offset,key):
	length=6
	return length
	
def Guides(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset:offset+2])
	length=22 + size*8
	return length
	
def Path(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset:offset+2])
	length=128
	[var]=struct.unpack('>h', parser.data[offset+20:offset+22])
	length = 22 + 27*var
	if size==0:
		var=ord(parser.data[offset+15])
		length = 16 + 27*var

	if parser.data[offset+4:offset+6] == '\xFF\xFF':
		[var]=struct.unpack('>h', parser.data[offset+22:offset+24])
		length = 24 + 27*var
		#length += 6
	return length

def Collector(parser,offset,key):
	length = 4 #!!!! just to set it to non-zero !!!!
	return length

def Rectangle(parser,offset,key):
##	var=ord(parser.data[offset+1])
##	length=36 #?ver.10?
##	length=42 #?ver.10?
	length=0x4b #?ver11?
	if parser.version == 10:
		length = 42
##	if var == 0xc:
##		length = 69
##	length = 69 #?ver.11?
	return length

def Layer(parser,offset,key):
	length=20 
#	if ord(parser.data[offset+1])==0:
#	  length=17
	return length

def ArrowPath(parser,offset,key):
	size =  ord(parser.data[offset+21])
	length=size*27+30
	return length

def VDict(parser,offset,key):
	[num] = struct.unpack('>h', parser.data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		[key] = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])
		if key == 2:
			shift+=6
		else:
			shift+=8
	return shift

def Group(parser,offset,key):
	length=16
	if parser.data[offset+2:offset+4] == '\xFF\xFF':
		length = 18
	return length

def Oval(parser,offset,key):
	if parser.version > 10:
		length=44
	else:
		length=34 
	return length

def MultiColorList(parser,offset,key):
	[num]= struct.unpack('>h', parser.data[offset:offset+2])
	length=6+num*10
	if parser.version == 10:
		length=10+num*10
	return length
	
def ContourFill(parser,offset,key):
	[num]= struct.unpack('>h', parser.data[offset+0:offset+2])
	[size]= struct.unpack('>h', parser.data[offset+2:offset+4])
	length = 0
	while num !=0:
		length = length +10+size*2
		[num]= struct.unpack('>h', parser.data[offset+0+length:offset+2+length])
		[size]= struct.unpack('>h', parser.data[offset+2+length:offset+4+length])
	length = length +10+size*2
	if parser.version == 10:
		 length = 18
	return length

def ClipGroup(parser,offset,key):
	length=16
	return length

def NewBlend(parser,offset,key):
	length=44
	return length

def BrushStroke(parser,offset,key):
	length=6
	return length

def GraphicStyle(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset+2:offset+4])
	length=10+size*4
	return length

def ContentFill(parser,offset,key):
	length=0 # was 2
	return length

def CompositePath(parser,offset,key):
	length=14
	if parser.data[offset+2:offset+4] == '\xFF\xFF':
		length = 16
	return length

def AttributeHolder(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset+0:offset+2])
	length=4 #was 2
	if size == 0:
		length=4
	return length

def FWShadowFilter(parser,offset,key):
	length=22
	return length

def FWBevelFilter(parser,offset,key):
	length=30
	return length

def FilterAttributeHolder(parser,offset,key):
	length=6
	return length

def Extrusion(parser,offset,key):
	size= ord(parser.data[offset+0x60])
	length=98 # "size" == 2
	if size == 3:
		length = 114
	if size == 19:
		length = 110
	print size,"%02x"%key,"%02x"%offset
	return length
	
def LinearFill(parser,offset,key):
	length=32 # was 54
	return length

def GradientMaskFilter(parser,offset,key):
	length=2
	return length

def DataList(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset:offset+2])
	length=10+size*2
	return length

def ImageImport(parser,offset,key):
	length=55  # was 87
	if ord(parser.data[offset+55]) != 0:  # 0-terminated string?
		length = 58
	return length

def TextBlok(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset:offset+2])
	length=4+size*4
	return length

def Paragraph(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset+2:offset+4])
	length=10 + 24*size # was 38
	return length

def TString(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset+2:offset+4])
	length=20+size*2
	return length

def LineTable(parser,offset,key):
	[size]= struct.unpack('>h', parser.data[offset+2:offset+4])
	length=4+size*50
	return length

def TextColumn(parser,offset,key):
	[num] = struct.unpack('>h', parser.data[offset+4:offset+6])
	shift = 26
	for i in range(num):
		[key] = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])
		if key == 2:
			shift+=6
		else:
			shift+=8
	return shift

def RadialFillX(parser,offset,key):
	#length=52
	length=20
	if parser.version == 10:
		length = 16
	return length

def TaperedFillX(parser,offset,key):
#	[size] = struct.unpack('>h', parser.data[offset:offset+2]) #!!!! quick-n-dirty
	length=16
	if parser.version == 10:
		length = 12
	return length

def TintColor6(parser,offset,key):
	length=38
	return length

def TaperedFill(parser,offset,key):
	length=12
	return length

def LensFill(parser,offset,key):
	length=40
	return length

def PerspectiveEnvelope(parser,offset,key):
	length=177
	return length

def MultiBlend(parser,offset,key):
	[size] = struct.unpack('>h', parser.data[offset:offset+2])
	length=52 + size*6
	return length
