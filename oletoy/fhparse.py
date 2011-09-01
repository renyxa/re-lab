#!/usr/bin/env python
import sys,struct,zlib

class parser:
	def  __init__(self):
		self.version = 0
		self.data = None
		self.iter = None

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
		if var2 == 0xf0:
			length = 52
		else:
			if var2 == 0x90: #03 90
				length = 36
			else:
				if var2 == 0xb0:
					length = 44 # 03 b0
				else:
					print "WARNING! New Xform second byte: 0x%02x"%var2
					length = var2/4
	if var1 == 0x33: # 33 90
		if var2 == 0x90:
			length = 20
		if var2 == 0xf0:
			length = 44
	if var1 == 0x32: # 32 90
		length = 12
		if var2 == 0xb0: # 32 b0
			length = 20

	return length
	
def SymbolClass(parser,offset,key):
	length=10
	return length

def SymbolInstance(parser,offset,key):
	length=24 # was 32
	return length
	
def PerspectiveGrid(parser,offset,key):
	length=65
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
		[key] = struct.unpack('>h', parser.data[offset+shift:offset+shift+2])
		if key == 2:
			shift+=6
		else:
			shift+=8
	return shift

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
	#[size] = struct.unpack('>h', parser.data[offset+17:offset+19])
	length=51 # can be 67
	return length
	
def TabTable(parser,offset,key):
	length=4
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

def Color6(parser,offset,key):
	length=28
	var = ord(parser.data[offset+1])
	if var == 4:
		length=32
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
	length=22
	return length
	
def Path(parser,offset,key):
	[size] =  struct.unpack('>h', parser.data[offset:offset+2])
	length=128
	[var]=struct.unpack('>h', parser.data[offset+20:offset+22])
	length = 22 + 27*var
	if size==0:
		var=ord(parser.data[offset+15])
		length = 16 + 27*var

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
	return length

def Oval(parser,offset,key):
#	length=34 #ver10?
	length=44 # was 38
	return length

def MultiColorList(parser,offset,key):
	[num]= struct.unpack('>h', parser.data[offset:offset+2])
	length=6+num*10
	return length
	
def CountourFill(parser,offset,key):
	[num]= struct.unpack('>h', parser.data[offset+0:offset+2])
	[size]= struct.unpack('>h', parser.data[offset+2:offset+4])
	length = 0
	while num !=0:
		length = length +10+size*2
		[num]= struct.unpack('>h', parser.data[offset+0+length:offset+2+length])
		[size]= struct.unpack('>h', parser.data[offset+2+length:offset+4+length])
	length = length +10+size*2
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
	length=87
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
	length=18+size*4
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
	length=52
	#hexprint(data,offset,length,key)
	return length

def TaperedFillX(parser,offset,key):
#	[size] = struct.unpack('>h', parser.data[offset:offset+2]) #!!!! quick-n-dirty
	length=58
	#if size == 0x4b:
	   # length=78
	if ver['mcl'] != -1:
		length =  ver['mcl']*10+18
		ver['mcl'] = -1
	#hexprint(data,offset,length,key)
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

