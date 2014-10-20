# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
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
import vsd,vsdblock,vsdchunks5
from utils import *


chunknoshift = {
		0x15:'Page',\
		0x18:'FontList',\
		0x1a:'Styles',\
		0x46:'PageSheet',\
		0x47:'ShapeType="Group"',\
		0x48:'ShapeType="Shape"',\
		0x4a:'StyleSheet',\
		0x4d:'ShapeType="Guide"',\
		0x4e:'ShapeType="Foreign"',\
		0x4f:'DocSheet'}

chunklist = {
		0xd:'OleList',\
		0x2c:'NameList',\
		0x64:'ScratchList',\
		0x65:'ShapeList',\
		0x66:'FieldList',
		0x67:'UserDefList',\
		0x68:'PropList',\
		0x69:'CharList',\
		0x6a:'ParaList',\
		0x6b:'TabsDataList',\
		0x6c:'GeomList',\
		0x6d:'CustPropsList',\
		0x6e:'ActIdList',\
		0x6f:'LayerList',\
		0x70:'CtrlList',\
		0x71:'CPntsList',
		0x72:'CnnectList',\
		0x73:'HypelLnkList',\
		0x76:'SmartTagList'}

chunktype = {
		0x0a:'Prompt',\
		0x0c:'FrgnData ',\
		0x0d:'OLE_List ',\
		0x0e:'Text IX  ',\
		0x10:'Data1    ',\
		0x11:'Data2    ',\
		0x12:'Data3    ',\
		0x15:'Page     ',\
		0x18:'FontList',\
		0x19:'Font ',\
		0x1a:'Styles   ',\
		0x1f:'OLE_Data ',\
		0x23:'Icon     ',\
		0x28:'Shape Stencil',\
		0x2c:'NameList ',\
		0x2d:'Name     ',\
		0x31:'Document ',\
		0x34:'NameIDX(v123) ',\
		0x42:'UniqueID',\
		0x46:'PageSheet',\
		0x47:'ShapeType="Group"',\
		0x48:'ShapeType="Shape"',\
		0x4a:'StyleSheet',\
		0x4d:'ShapeType="Guide"',\
		0x4e:'ShapeType="Foreign"',\
		0x4f:'DocSheet ',\
		0x64:'ScratchList',\
		0x65:'ShapeList',\
		0x66:'FieldList',\
		0x67:'UserDefList',\
		0x68:'PropList ',\
		0x69:'CharList ',\
		0x6a:'ParaList ',\
		0x6b:'TabsDataList',\
		0x6c:'GeomList ',\
		0x6d:'CustPropsList',\
		0x6e:'ActIdList',\
		0x6f:'LayerList',\
		0x70:'CtrlList ',\
		0x71:'CPntsList',\
		0x72:'CnnectList',\
		0x73:'HypelLnkList',\
		0x76:'SmartTagLst',\
		0x83:'ShapeID  ',\
		0x84:'Event    ',\
		0x85:'Line     ',
		0x86:'Fill     ',\
		0x87:'TextBlock',\
		0x88:'Tabs Data',\
		0x89:'Geometry ',\
		0x8a:'MoveTo   ',\
		0x8b:'LineTo   ',\
		0x8c:'ArcTo    ',\
		0x8d:'InfinLine',\
		0x8f:'Ellipse  ',\
		0x90:'EllpArcTo',\
		0x92:'PageProps',\
		0x93:'StyleProps',\
		0x94:'Char IX ',\
		0x95:'ParaIX  ',\
		0x96:'Tabs Data',\
		0x97:'Tabs Data',\
		0x98:'FrgnType',\
		0x99:'ConnectPts',\
		0x9b:'XForm   ',\
		0x9c:'TxtXForm',\
		0x9d:'XForm1D ',\
		0x9e:'Scratch ',\
		0xa0:'Protection',\
		0xa1:'TextFields',\
		0xa2:'Control ',\
		0xa3:'Help    ',\
		0xa4:'Misc    ',\
		0xa5:'SplineStart',\
		0xa6:'SplineKnot',\
		0xa7:'LayerMem',\
		0xa8:'LayerIX ',\
		0xa9:'Act ID  ',\
		0xaa:'Control ',\
		0xb4:'User-defined',\
		0xb5:'Tabs Data',\
		0xb6:'CustomProps',\
		0xb7:'RulerGrid',\
		0xb9:'ConnectionPoints',\
		0xba:'ConnectionPoints',\
		0xbb:'ConnectionPoints',\
		0xbc:'DocProps',\
		0xbd:'Image   ',\
		0xbe:'Group   ',\
		0xbf:'Layout  ',\
		0xc0:'PageLayout',\
		0xc1:'PolylineTo',\
		0xc3:'NURBSTo ',\
		0xc4:'Hyperlink',\
		0xc5:'Reviewer',\
		0xc6:'Annotation',\
		0xc7:'SmartTagDef',\
		0xc8:'PrintProps',\
		0xc9:'NameIDX ',\
		0xd1:'Shape Data'}

def List (hd, size, value, off = 19):
	return
	if hd.version < 6:
		vsdchunks5.List(hd,size,value)
		return
	shl = struct.unpack("<I",value[off:off+4])[0]
	add_iter(hd,"SubHdrLen", "%2x"%shl,off,4,"<I")
	ch_list_len = struct.unpack("<I",value[off+4:off+8])[0]
	add_iter(hd, "ChldLstLen", "%2x"%ch_list_len,off+4,4,"<I")
	add_iter(hd,"SubHdr"," ",off+8,shl,"txt")

#	ch_list = ""
#	for i in range(ch_list_len/4):
#		ch_list += "%02x "%struct.unpack("<I",value[off+8+shl+i*4:off+12+shl+i*4])[0]
#	if ch_list != "":
#		add_iter(hd,"ChldList",ch_list,off+8+shl,ch_list_len,"txt")
#	else:
#		add_iter(hd,"ChldList","[empty]",off+8+shl,ch_list_len,"txt")

def Font (hd, size, value, off = 19):
	charset = ord(value[off+2])
	chtxt = key2txt(charset,ms_charsets,"%02x"%charset)
	add_iter(hd, "Charset", chtxt,off+2,1,"<B")
	fontname = unicode(value[off+6:])
	add_iter(hd, "Font name", fontname,off+6,len(fontname),"txt")


def Text (hd, size, value, off = 19):
	# no support for LangID for v.6
	if hd.version == 11:
		txt = unicode(value[off+8:],'utf-16').encode('utf-8')
		fmt = "utxt"
	else:
		txt = value[0x1b:]
		fmt = "txt"
	add_iter(hd, "Text", txt,off+8,len(value)-8,fmt)

def Page (hd, size, value, off = 19):
	List (hd, size, value, off)
	add_iter(hd, "BG Page", "%x"%struct.unpack("<I",value[off+8:off+8+4])[0],off+8,4,"<I")
	add_iter(hd, "ViewScale?", struct.unpack("<d",value[off+26:off+26+8])[0],off+26,8,"<d")
	add_iter(hd, "ViewCntrX", struct.unpack("<d",value[off+34:off+34+8])[0],off+34,8,"<d")
	add_iter(hd, "ViewCntrY", struct.unpack("<d",value[off+42:off+42+8])[0],off+42,8,"<d")

def Shape (hd, size, value, off = 19):
	List (hd, size, value, off)
#	if hd.version < 6:
#		vsdchunks5.Shape(hd,size,value,off)
#		return
	add_iter(hd,"Parent","%2x"%struct.unpack("<I",value[off+10:off+10+4])[0],off+10,4,"<I")
	add_iter(hd,"Master","%2x"%struct.unpack("<I",value[off+18:off+18+4])[0],off+18,4,"<I")
	add_iter(hd,"MasterShape","%2x"%struct.unpack("<I",value[off+26:off+26+4])[0],off+26,4,"<I")
	add_iter(hd,"FillStyle","%2x"%struct.unpack("<I",value[off+34:off+34+4])[0],off+34,4,"<I")
	add_iter(hd,"LineStyle","%2x"%struct.unpack("<I",value[off+42:off+42+4])[0],off+42,4,"<I")
	add_iter(hd,"TextStyle","%2x"%struct.unpack("<I",value[off+50:off+50+4])[0],off+50,4,"<I")

def XForm (hd, size, value, off = 19):
	add_iter(hd,"PinX","%.2f"%struct.unpack("<d",value[off+1:off+1 +8]),off+1,8,"<d")
	add_iter(hd,"PinY","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"Width","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"Height","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"LocPinX","%.2f"%struct.unpack("<d",value[off+37:off+37+8]),off+37,8,"<d")
	add_iter(hd,"LocPinY","%.2f"%struct.unpack("<d",value[off+46:off+46+8]),off+46,8,"<d")
	add_iter(hd,"Angle","%.2f"%struct.unpack("<d",value[off+55:off+55+8]),off+55,8,"<d")
	add_iter(hd,"FlipX","%2x"%ord(value[off+63]),off+63,1,"<I")
	add_iter(hd,"FlipY","%2x"%ord(value[off+64]),off+64,1,"<I")
	add_iter(hd,"ResizeMode","%2x"%ord(value[off+65]),off+65,1,"<I")
	if len(value)>off+69: # both 6 and 11
		vsdblock.parse(hd, size, value, off+69)

def XForm1D (hd, size, value, off = 19):
	add_iter(hd,"BeginX","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"BeginY","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"EndX","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"EndY","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	if len(value)>off+38: # both 6 and 11
		vsdblock.parse(hd, size, value, off+38)

def ConnPts (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"var1","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"var2","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	if len(value)>off+0x30: # 11
		vsdblock.parse(hd, size, value, off+0x30)


def TxtXForm (hd, size, value, off = 19):
	add_iter(hd,"TxtPinX","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"TxtPinY","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"TxtWidth","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"TxtHeight","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"TxtLocPinX","%.2f"%struct.unpack("<d",value[off+37:off+37+8]),off+37,8,"<d")
	add_iter(hd,"TxtLocPinY","%.2f"%struct.unpack("<d",value[off+46:off+46+8]),off+46,8,"<d")
	add_iter(hd,"TxtAngle","%.2f"%struct.unpack("<d",value[off+55:off+55+8]),off+55,8,"<d")
	if len(value)>off+69: # both 6 and 11
		vsdblock.parse(hd, size, value, off+69)

def Misc (hd, size, value, off = 19):
	if len(value)>off+45: # 11, probably v6 too
		vsdblock.parse(hd, size, value, off+45)


def MoveTo (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	if len(value)>off+20: # both 6 and 11
		vsdblock.parse(hd, size, value, off+20)

def ArcTo (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"A","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	if len(value)>off+29: # both 6 and 11
		vsdblock.parse(hd, size, value, off+29)

def InfLine (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"A","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"B","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	if len(value)>off+38: # both 6 and 11 ???
		vsdblock.parse(hd, size, value, off+38)

def EllArcTo (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"A","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"B","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"C","%.2f"%struct.unpack("<d",value[off+37:off+37+8]),off+37,8,"<d")
	add_iter(hd,"D","%.2f"%struct.unpack("<d",value[off+46:off+46+8]),off+46,8,"<d")
	if len(value)>off+56: # both 6 and 11
		vsdblock.parse(hd, size, value, off+56)

def Ellipse (hd, size, value, off = 19):
	add_iter(hd,"Center X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Center Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"Right X","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"Right Y","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"Top X","%.2f"%struct.unpack("<d",value[off+37:off+37+8]),off+37,8,"<d")
	add_iter(hd,"Top Y","%.2f"%struct.unpack("<d",value[off+46:off+46+8]),off+46,8,"<d")
	if len(value)>off+56: # both 6 and 11
		vsdblock.parse(hd, size, value, off+56)

def NameID (hd, size, value, off = 19):
#	if hd.version < 6:
#		vsdchunks5.NameID(hd,size,value,off)
#		return

	numofrec = struct.unpack("<I",value[off:off+4])[0]
	add_iter(hd,"#ofRecords","%2x"%numofrec,off,4,"<I")
	for i in range(numofrec):
		n1 = struct.unpack("<I",value[off+4+i*13:off+4+4+i*13])[0]
		n2 = struct.unpack("<I",value[off+8+i*13:off+8+4+i*13])[0]
		n3 = struct.unpack("<I",value[off+12+i*13:off+12+4+i*13])[0]
		flag = ord(value[off+16+i*13])
		add_iter(hd,"Rec #%d"%i,"%2x %2x %2x %2x"%(n1,n2,n3,flag),off+4+i*13,13,"txt")

linecaps = {0:"Round (SVG: Round)", 1:"Square (SVG: Butt)",2:"Extended (SVG: Square)"}

def Line (hd, size, value, off = 19):
	add_iter(hd,"Weight","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"LineClrID","%2x"%ord(value[off+9]),off+9,1,"B")
	add_iter(hd,"LineClr","%02x%02x%02x"%(ord(value[off+10]),ord(value[off+11]),ord(value[off+12])),off+10,3,"clr")
	add_iter(hd,"LineXparency","%d %%"%(ord(value[off+13])/2.55),off+13,1,"B")
	add_iter(hd,"LinePatternID","%2x"%ord(value[off+14]),off+14,1,"B")
	add_iter(hd,"Rounding","%.2f"%struct.unpack("<d",value[off+16:off+16+8]),off+16,8,"<d")
	add_iter(hd,"EndArrSize","%2x"%ord(value[off+24]),off+24,1,"B")
	add_iter(hd,"BeginArrow","%2x"%ord(value[off+25]),off+25,1,"B")
	add_iter(hd,"EndArrow","%2x"%ord(value[off+26]),off+26,1,"B")
	lc = ord(value[off+27])
	lc_txt = "%2x "%lc
	if linecaps.has_key(lc):
		lc_txt += linecaps[lc]
	add_iter(hd,"LineCap",lc_txt,off+27,1,"txt")
	add_iter(hd,"BeginArrSize","%2x"%ord(value[off+28]),off+28,1,"B")
	if len(value)>off+35: # both 6 and 11
		vsdblock.parse(hd, size, value, off+35)

def Fill (hd, size, value, off = 19):
	add_iter(hd,"FillFG","%2x"%ord(value[off]),off,1,"B")
	add_iter(hd,"FillFGClr","%02x%02x%02x"%(ord(value[off+1]),ord(value[off+2]),ord(value[off+3])),off+1,3,"clr")
	add_iter(hd,"FillFGXparency","%d %%"%(ord(value[off+4])/2.55),off+4,1,"B")
	add_iter(hd,"FillBG","%2x"%ord(value[off+5]),off+5,1,"B")
	add_iter(hd,"FillBGClr","%02x%02x%02x"%(ord(value[off+6]),ord(value[off+7]),ord(value[off+8])),off+6,3,"clr")
	add_iter(hd,"FillBGXparency","%d %%"%(ord(value[off+9])/2.55),off+9,1,"B")
	add_iter(hd,"FillPattern","%2x"%ord(value[off+10]),off+10,1,"B")
	add_iter(hd,"ShdwFG","%2x"%ord(value[off+11]),off+11,1,"B")
	add_iter(hd,"ShdwFGClr","%02x%02x%02x"%(ord(value[off+12]),ord(value[off+13]),ord(value[off+14])),off+12,3,"clr")
	add_iter(hd,"ShdwFGXparency","%d %%"%(ord(value[off+15])/2.56),off+15,1,"B")
	add_iter(hd,"ShdwBG","%2x"%ord(value[off+16]),off+16,1,"B")
	add_iter(hd,"ShdwBGClr","%02x%02x%02x"%(ord(value[off+17]),ord(value[off+18]),ord(value[off+19])),off+19,3,"clr")
	add_iter(hd,"ShdwBGXparency","%d %%"%(ord(value[off+20])/2.55),off+20,1,"B")
	add_iter(hd,"ShdwPattern","%2x"%ord(value[off+21]),off+21,1,"B")
	add_iter(hd,"ShdwType","%2x"%ord(value[off+22]),off+22,1,"B")
	if hd.version == 11:
		add_iter(hd,"ShdwOffsetX","%.2f"%struct.unpack("<d",value[off+24:off+24+4]),off+24,8,"<d")
		add_iter(hd,"ShdwOffsetY","%.2f"%struct.unpack("<d",value[off+33:off+33+4]),off+33,8,"<d")
		add_iter(hd,"ShdwObliqueAngle","%.2f"%struct.unpack("<d",value[off+42:off+42+4]),off+42+4,8,"<d")
		add_iter(hd,"ShdwScaleFactor","%.2f"%struct.unpack("<d",value[off+50:off+50+4]),off+50,8,"<d")
	if hd.version == 6 and len(value)>off+25:
		vsdblock.parse(hd, size, value, off+25)
	elif len(value)>off+61 and hd.version == 11:
		vsdblock.parse(hd, size, value, off+61)

def Char (hd, size, value, off = 19):
	add_iter(hd,"Num of Chars","%d"%struct.unpack("<I",value[off:off+4]),off,4,"<I")
	add_iter(hd,"FontID","0x%02x"%struct.unpack("<H",value[off+4:off+4+2]),off+4,2,"<H")
	add_iter(hd,"ColorID","0x%02x"%ord(value[off+6]),off+6,1,"B")
	add_iter(hd,"Color","%02x%02x%02x"%(ord(value[off+7]),ord(value[off+8]),ord(value[off+9])),off+7,3,"clr")
	add_iter(hd,"Transparency","%d%%"%(ord(value[off+10])*100/256),off+10,1,"B")

	flags1 = ord(value[off+11])
	ftxt = ""
	if flags1&1 == 1:
		ftxt += "bold "
	if flags1&2== 2:
		ftxt += "italic "
	if flags1&4 == 4:
		ftxt += "undrline "
	if flags1&8 == 8:
		ftxt += "smcaps "
	add_iter(hd,"Font Mods1",ftxt,off+11,1,"txt")

	flags2 = ord(value[off+12])
	ftxt = ""
	if flags2&1 == 1:
		ftxt += "allcaps "
	if flags2&2== 2:
		ftxt += "initcaps "
	add_iter(hd,"Font Mods2",ftxt,off+12,1,"txt")
	
	flags3 = ord(value[off+13])
	ftxt = ""
	if flags3&1 == 1:
		ftxt += "superscript "
	if flags3&2== 2:
		ftxt += "subscript "
	add_iter(hd,"Font Mods3",ftxt,off+12,1,"txt")
	add_iter(hd,"Scale","%d%%"%(struct.unpack("<h",value[off+13:off+13+2])[0]/100.),off+13,2,"<h")
	add_iter(hd,"FontSize","%.2f pt"%(72*struct.unpack("<d",value[off+18:off+18+8])[0]),off+18,8,"<d")

	flags4 = ord(value[off+26])
	ftxt = ""
	if flags4&1 == 1:
		ftxt += "dblunder "
	if flags4&2== 2:
		ftxt += "overline "
	if flags4&20 == 20:
		ftxt += "dblstrike "
	add_iter(hd,"Font Mods4",ftxt,off+26,1,"txt")
	add_iter(hd,"Spacing","%d pt"%(struct.unpack("<h",value[off+27:off+27+2])[0]/200.),off+27,2,"<h")
	if hd.version == 11:
		add_iter(hd,"AsianFont","%d"%ord(value[off+37]),off+37,1,"B")
		add_iter(hd,"ComplexScriptFont","%d"%ord(value[off+39]),off+39,1,"B")
		add_iter(hd,"LocalizeFont","%d"%ord(value[off+41]),off+41,1,"B")
		add_iter(hd,"ComplexScriptSize","%d%%"%(struct.unpack("<d",value[off+43:off+43+8])[0]*100),off+43,8,"<d")
		add_iter(hd,"LangID","%d"%struct.unpack("<I",value[off+69:off+69+4]),off+69,4,"<I")
		if len(value)>off+88 and hd.version == 11:
			vsdblock.parse(hd, size, value, off+88)
	elif hd.version == 6 and len(value)>off+35:
		vsdblock.parse(hd, size, value, off+35)


def Para (hd, size, value, off = 19):
	add_iter(hd,"Num of Chars","%d"%struct.unpack("<I",value[off:off+4]),off,4,"<I")
	add_iter(hd,"IndFirst","%.2f"%struct.unpack("<d",value[off+5:off+5+8]),off+5,8,"<d")
	add_iter(hd,"IndLeft","%.2f"%struct.unpack("<d",value[off+14:off+14+8]),off+14,8,"<d")
	add_iter(hd,"IndRight","%.2f"%struct.unpack("<d",value[off+23:off+23+8]),off+23,8,"<d")
	add_iter(hd,"SpLine","%d%%"%(struct.unpack("<d",value[off+32:off+32+8])[0]*100),off+32,8,"<d")
	add_iter(hd,"SpBefore","%d pt"%round(struct.unpack("<d",value[off+41:off+41+8])[0]*72),off+41,8,"<d")
	add_iter(hd,"SpAfter","%d pt"%round(struct.unpack("<d",value[off+50:off+50+8])[0]*72),off+50,8,"<d")
	add_iter(hd,"HAlign","%d"%ord(value[off+58]),off+58,1,"B")
	add_iter(hd,"Bullet","%d"%ord(value[off+59]),off+59,1,"B")
	add_iter(hd,"BulletFont","%d"%struct.unpack("<H",value[off+64:off+64+2]),off+64,2,"<H")
	add_iter(hd,"LocBulletFont","%d"%ord(value[off+66]),off+66,1,"B")
	add_iter(hd,"BulletSize","%d%%"%(struct.unpack("<d",value[off+68:off+68+8])[0]*100),off+68,8,"<d")
	add_iter(hd,"TxtPosAfterBullet","%.2f"%struct.unpack("<d",value[off+77:off+77+8]),off+77,8,"<d")
	add_iter(hd,"Flags","%d"%struct.unpack("<I",value[off+85:off+85+4]),off+85,4,"<I")
	if hd.version == 6 and len(value)>off+73:
		vsdblock.parse(hd, size, value, off+73)
	elif len(value)>off+123 and hd.version == 11:
		vsdblock.parse(hd, size, value, off+123)


def TextBlock (hd, size, value, off = 19):
	add_iter(hd,"LeftMargin","%.2f"%round(struct.unpack("<d",value[off+1:off+1+8])[0]*72),off+1,8,"<d")
	add_iter(hd,"RightMargin","%.2f"%round(struct.unpack("<d",value[off+10:off+10+8])[0]*72),off+10,8,"<d")
	add_iter(hd,"TopMargin","%.2f"%round(struct.unpack("<d",value[off+19:off+19+8])[0]*72),off+19,8,"<d")
	add_iter(hd,"BottomMargin","%.2f"%round(struct.unpack("<d",value[off+28:off+28+8])[0]*72),off+28,8,"<d")
	add_iter(hd,"VAlign","%d"%ord(value[off+36]),off+36,1,"B")
	add_iter(hd,"TxtBG CLR Id","%d"%ord(value[off+37]),off+37,1,"B")
	add_iter(hd,"TxtBG Trans","%d"%round(ord(value[off+41])*100/256.),off+41,1,"B")
	add_iter(hd,"DefTabStop","%.2f"%struct.unpack("<d",value[off+43:off+43+8]),off+43,8,"<d")
	add_iter(hd,"TxtDirection","%d"%ord(value[off+63]),off+63,1,"B")
	if hd.version == 6 and len(value)>off+71:
		vsdblock.parse(hd, size, value, off+71)
	elif len(value)>off+92 and hd.version == 11:
		vsdblock.parse(hd, size, value, off+92)

#0x92
def PageProps (hd, size, value, off = 19):
	add_iter(hd,"PageWidth","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"PageHeight","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"ShdwOffsetX","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"ShdwOffsetY","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"PageScale","%.2f"%struct.unpack("<d",value[off+37:off+37+8]),off+37,8,"<d")
	add_iter(hd,"DrawingScale","%.2f"%struct.unpack("<d",value[off+46:off+46+8]),off+46,8,"<d")
	add_iter(hd,"DrawingSizeType","%2x"%ord(value[off+54]),off+54,1,"B")
	add_iter(hd,"DrawingScaleType","%2x"%ord(value[off+55]),off+55,1,"B")
	add_iter(hd,"ShdwObliqueAngle","%.2f"%struct.unpack("<d",value[off+78:off+78+8]),off+78,8,"<d")
	add_iter(hd,"ShdwScaleFactor","%.2f"%struct.unpack("<d",value[off+86:off+86+8]),off+86,8,"<d")
	if len(value)>off+136:
		vsdblock.parse(hd, size, value, off+136)


def StyleProps (hd, size, value, off = 19):
	add_iter(hd,"Use Line",ord(value[off]),off,1,"<B")
	add_iter(hd,"Use Fill",ord(value[off+1]),off+1,1,"<B")
	add_iter(hd,"Use Text",ord(value[off+2]),off+2,1,"<B")
	add_iter(hd,"Hidden",ord(value[off+3]),off+3,1,"<B")
	if len(value)>off+7:
		vsdblock.parse(hd, size, value, off+7)


def LayerIX (hd, size, value, off = 19):
	add_iter(hd,"ClrID","0x%02x"%ord(value[off+8]),off+8,1,"<B")
	if ord(value[off+8]) != 255:
		add_iter(hd,"Colour",d2hex(value[off+9:off+9+3]),off+9,3,"clr")
	add_iter(hd,"Transparency","%d%%"%(ord(value[off+12])*100/255),off+12,1,"<B")	
	add_iter(hd,"Visible","%d"%ord(value[off+14]),off+14,1,"<B")
	add_iter(hd,"Print","%d"%ord(value[off+15]),off+15,1,"<B")
	add_iter(hd,"Active","%d"%ord(value[off+16]),off+16,1,"<B")
	add_iter(hd,"Lock","%d"%ord(value[off+17]),off+17,1,"<B")
	add_iter(hd,"Snap","%d"%ord(value[off+18]),off+18,1,"<B")
	add_iter(hd,"Glue","%d"%ord(value[off+19]),off+19,1,"<B")
	if len(value)>off+33: # both 6 and 11
		vsdblock.parse(hd, size, value, off+33)


def Control (hd, size, value, off = 19):
	add_iter(hd,"X","%.3f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.3f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"XDyn","%.3f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"YDyn","%.3f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"XCon",ord(value[off+36]),off+36,1,"<B")
	add_iter(hd,"YCon",ord(value[off+37]),off+37,1,"<B")
	add_iter(hd,"CanGlue",ord(value[off+38]),off+38,1,"<B")
	if len(value)>off+47: # 11
		vsdblock.parse(hd, size, value, off+47)


def PageLayout (hd, size, value, off = 19):
	add_iter(hd,"LineToNodeX","%.3f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"LineToNodeY","%.3f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"BlockSizeX","%.3f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	add_iter(hd,"BlockSizeY","%.3f"%struct.unpack("<d",value[off+37:off+37+8]),off+37,8,"<d")
	add_iter(hd,"AvenueSizeX","%.3f"%struct.unpack("<d",value[off+46:off+46+8]),off+46,8,"<d")
	add_iter(hd,"AvenueSizeY","%.3f"%struct.unpack("<d",value[off+55:off+55+8]),off+55,8,"<d")
	add_iter(hd,"LineToLineX","%.3f"%struct.unpack("<d",value[off+64:off+64+8]),off+64,8,"<d")
	add_iter(hd,"LineToLineY","%.3f"%struct.unpack("<d",value[off+73:off+73+8]),off+73,8,"<d")
	add_iter(hd,"LineJumpFactorX","%.3f"%struct.unpack("<d",value[off+81:off+81+8]),off+81,8,"<d")
	add_iter(hd,"LineJumpFactorY","%.3f"%struct.unpack("<d",value[off+89:off+89+8]),off+89,8,"<d")


def Polyline (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	sdflag = value[off+19:off+19+4]
	sdtext = 'No'
	if sdflag == '\x8b\x02\x00\x00':
		sdtext = 'Yes'
	add_iter(hd,"Use Shape Data",sdtext,off+19,4,"<I")
	add_iter(hd,"ShapeData Id","%02x"%struct.unpack("<I",value[off+23:off+23+4]),off+23,4,"<I")
	if len(value)>off+29:
		vsdblock.parse(hd, size, value, off+29)


def NURBS (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"Knot","%.2f"%struct.unpack("<d",value[off+18:off+18+8]),off+18,8,"<d")
	add_iter(hd,"Weight","%.2f"%struct.unpack("<d",value[off+26:off+26+8]),off+26,8,"<d")
	add_iter(hd,"KnotPrev","%.2f"%struct.unpack("<d",value[off+34:off+34+8]),off+34,8,"<d")
	add_iter(hd,"WeightPrev","%.2f"%struct.unpack("<d",value[off+42:off+42+8]),off+42,8,"<d")
	sdflag = value[off+51:off+51+4]
	sdtext = 'No'
	if sdflag == '\x8a\x02\x00\x00':
		sdtext = 'Yes'
	add_iter(hd,"Use Shape Data",sdtext,off+51,4,"<d")
	add_iter(hd,"ShapeData Id","%02x"%struct.unpack("<I",value[off+55:off+55+4]),off+55,4,"<I")
	if len(value)>off+61:
		vsdblock.parse(hd, size, value, off+61)

nd_types = {0x80:"Polyline",0x82:"NURBS"}

def ShapeData (hd, size, value, off = 19):
	nd_type = ord(value[off])
	nd_str = "%02x "%nd_type
	if nd_types.has_key(nd_type):
		nd_str += "("+nd_types[nd_type]+")"
	add_iter(hd,"Type",nd_str,off,1,"b")
	if nd_type == 0x80:
		xType = ord(value[off+16])
		yType = ord(value[off+17])
		add_iter(hd,"xType",xType,off+16,1,"b")
		add_iter(hd,"yType",yType,off+17,1,"b")
		num_pts = struct.unpack("<I",value[off+18:off+18+4])[0]
		add_iter(hd,"# of pts",num_pts,off+18,4,"<I")
		for i in range(num_pts):
			add_iter(hd,"x%d"%(i+1),"%.2f"%struct.unpack("<d",value[off+22+i*16:off+22+8+i*16]),off+22+i*16,8,"<d")
			add_iter(hd,"y%d"%(i+1),"%.2f"%struct.unpack("<d",value[off+30+i*16:off+30+8+i*16]),off+30+i*16,8,"<d")
	if nd_type == 0x82:
		add_iter(hd,"knotLast","%.2f"%struct.unpack("<d",value[off+16:off+16+8]),off+16,8,"<d")
		add_iter(hd,"degree","%.2f"%struct.unpack("<h",value[off+24:off+24+2]),off+24,2,"<h")
		xType = ord(value[off+26])
		yType = ord(value[off+27])
		add_iter(hd,"xType",xType,off+26,1,"b")
		add_iter(hd,"yType",yType,off+27,1,"b")
		num_pts = struct.unpack("<I",value[off+28:off+28+4])[0]
		add_iter(hd,"# of pts",num_pts,off+28,4,"<I")
		for i in range(num_pts):
			add_iter(hd,"x%d"%(i+1),"%.2f"%struct.unpack("<d",value[off+32+i*32:off+32+8+i*32]),off+32+i*32,8,"<d")
			add_iter(hd,"y%d"%(i+1),"%.2f"%struct.unpack("<d",value[off+40+i*32:off+40+8+i*32]),off+40+i*32,8,"<d")
			add_iter(hd,"knot%d"%(i+1),"%.2f"%struct.unpack("<d",value[off+48+i*32:off+48+8+i*32]),off+48+i*32,8,"<d")
			add_iter(hd,"weight%d"%(i+1),"%.2f"%struct.unpack("<d",value[off+56+i*32:off+56+8+i*32]),off+56+i*32,8,"<d")


bits = {1:'noFill',2:'noLine',4:'noShow',8:'noSnap',32:'noQuickDrag'}

def Geometry (hd, size, value, off = 19):
	flags = ord(value[off])
	for i in (1,2,4,8,32):
		res = 'No'
		if flags&i:
			res = 'Yes'
		add_iter(hd,bits[i],res,off,1,"txt")
	if len(value)>off+3:
		vsdblock.parse(hd, size, value, off+3)

def ShapeStencil (hd, size, value, off = 19):
	add_iter(hd,"ID?","%02x"%struct.unpack("<I",value[off:off+4]),off,4,"<I")
	add_iter(hd,"var1?","%.2f"%struct.unpack("<d",value[off+4:off+4+8]),off+4,8,"<d")
	add_iter(hd,"var2?","%.2f"%struct.unpack("<d",value[off+12:off+12+8]),off+12,8,"<d")
	add_iter(hd,"var3?","%.2f"%struct.unpack("<d",value[off+20:off+20+8]),off+20,8,"<d")
	add_iter(hd,"var4?","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")

def TextField (hd, size, value, off = 19):
	fmt = ord(value[off+7])
	tdiff = struct.unpack("<d",value[off+8:off+8+8])[0]
	dlen = 8
	dfmt = "<d"
	if fmt == 0x28:
		dt = datetime.datetime(1899,12,30)+datetime.timedelta(tdiff)
		dname = "Date"
	elif fmt == 0xe8:
		dt = struct.unpack("<I",value[off+8:off+8+4])[0]
		dname = "Name ID"
		dlen = 4
		dfmt = "<I"
	else:
		dt = "%.2f"%tdiff
		dname = "Value"
	fmtidtype = ord(value[off+17])
	if fmtidtype == 0xe8:
		fmtid = struct.unpack("<I",value[off+18:off+18+4])[0]
		fmtname = "Format ID"
		fmtlen = 4
		fmtfmt = "<I"
	add_iter(hd,dname,dt,off+8,dlen,dfmt)
	add_iter(hd,fmtname,fmtid,off+18,fmtlen,fmtfmt)
	dtype = struct.unpack("<H",value[off+26:off+26+2])[0]
	add_iter(hd,"Type",dtype,off+26,2,"<H")
	add_iter(hd,"UICat","0x%02x"%ord(value[off+28]),off+28,1,"B")
	add_iter(hd,"UICod","0x%02x"%ord(value[off+29]),off+29,1,"B")
	add_iter(hd,"UIFmt","0x%02x"%ord(value[off+30]),off+30,1,"B")
	if hd.version == 6 and len(value)>off+36:
		vsdblock.parse(hd, size, value, off+36)
	elif len(value)>off+54 and hd.version == 11:
		vsdblock.parse(hd, size, value, off+54)


def SplineStart (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"Knot","%.2f"%struct.unpack("<d",value[off+18:off+18+8]),off+18,8,"<d")
	add_iter(hd,"Knot2","%.2f"%struct.unpack("<d",value[off+26:off+26+8]),off+26,8,"<d")
	add_iter(hd,"Knot3","%.2f"%struct.unpack("<d",value[off+34:off+34+8]),off+34,8,"<d")
	add_iter(hd,"Degree","%d"%struct.unpack("<h",value[off+42:off+42+2]),off+42,2,"<h")
	if len(value)>off+46:
		vsdblock.parse(hd, size, value, off+46)


def SplineKnot (hd, size, value, off = 19):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"Knot","%.2f"%struct.unpack("<d",value[off+18:off+18+8]),off+18,8,"<d")
	if len(value)>off+28:
		vsdblock.parse(hd, size, value, off+28)


def FrgnType (hd, size, value, off = 19):
	add_iter(hd,"ImgOffsetX","%.2f"%struct.unpack("<d",value[off+1:off+1+8]),off+1,8,"<d")
	add_iter(hd,"ImgOffsetY","%.2f"%struct.unpack("<d",value[off+10:off+10+8]),off+10,8,"<d")
	add_iter(hd,"ImgWidth","%.2f"%struct.unpack("<d",value[off+19:off+19+8]),off+19,8,"<d")
	add_iter(hd,"ImgHeight","%.2f"%struct.unpack("<d",value[off+28:off+28+8]),off+28,8,"<d")
	ftype = struct.unpack("<h",value[off+36:off+36+2])[0]
	add_iter(hd,"Type ??","%d"%ftype,off+36,2,"<h")
	add_iter(hd,"MapMode","%d"%struct.unpack("<h",value[off+38:off+38+2]),off+38,2,"<h")
	if ftype == 4:
		add_iter(hd,"ExtentX","%d"%struct.unpack("<h",value[off+40:off+40+2]),off+40,2,"<h")
		add_iter(hd,"ExtentY","%d"%struct.unpack("<h",value[off+42:off+42+2]),off+42,2,"<h")
	if len(value)>off+62:
		vsdblock.parse(hd, size, value, off+62)


chnk_func = {
	0xe:Text,
	0x15:Page,
	0x19:Font,
	0x28:ShapeStencil,
	0xd:List,0x2c:List,
	0x34:NameID, #0x34 is used in v2,v3
	0x46:Shape,0x47:Shape, 0x48:Shape, 0x4a:Shape,0x4d:Shape, 0x4e:Shape,0x4f:Shape,
	0x64:List,0x65:List,0x66:List,0x67:List,0x68:List,0x69:List,0x6a:List,0x6b:List,0x6c:List,
	0x6d:List,0x6e:List,0x6f:List,0x70:List,0x71:List,0x72:List,0x76:List,
	0x85:Line,0x86:Fill,0x87:TextBlock,0x89:Geometry,
	0x8a:MoveTo,0x8b:MoveTo,0x8c:ArcTo,0x8d:InfLine,
	0x8f:Ellipse,0x90:EllArcTo,
	0x92:PageProps,0x93:StyleProps,
	0x94:Char,0x95:Para,0x98:FrgnType,0x99:ConnPts,0x9b:XForm,0x9c:TxtXForm,0x9d:XForm1D,
	0xa1:TextField,0xa4:Misc,0xa5:SplineStart,0xa6:SplineKnot,0xa8:LayerIX,0xaa:Control,
	0xc0:PageLayout,0xc1:Polyline,0xc3:NURBS, 0xc9:NameID,
	0xd1:ShapeData
}

def v5parse(page,version,parent,ptr):
	if version > 2:
		data = ptr.data[12:]
	else:
		data = ptr.data
	num = struct.unpack("<H",data[len(data)-4:len(data)-2])[0]
	loff = len(data)-4-num*4
	chend = loff
	shift = 0
	for i in range(num):
		chtype = struct.unpack("<H",data[loff+i*4+shift:loff+i*4+2+shift])[0]
		if chtype == 0:
			shift += 2
			chtype = struct.unpack("<H",data[loff+i*4+shift:loff+i*4+2+shift])[0]
		choff = struct.unpack("<H",data[loff+i*4+2+shift:loff+i*4+4+shift])[0]
		if choff%4:
			choff += 4 - choff%4
#		print "%02x %02x %02x"%(choff,chend,chtype)
		chdata = data[choff:chend]
		chend = choff
		
		if chunktype.has_key(chtype):
			name = '%-24s'%chunktype[chtype]+'(Len: %02x)'%len(chdata)
		else:
			name = "Unkn %02x"%chtype
		prep_pgiter(page,name,"vsdv%d"%version,"chnk %s"%chtype,chdata,parent)

def parse(page, version, parent, pntr):
	model = page.model
	offset = 0
	tmppntr = vsd.pointer()
	tmppntr2 = vsd.pointer()
	olelist = None
	oledata = ""
	path = parent
	path0 =  parent
	path1 =  parent
	path2 =  parent
	level = 0
	while offset < len(pntr.data):
#		try:
			chnk = vsd.chunk()
			if version<6:
				ch_hdr_len = 12
				trailer = 0
				[chnk.type] = struct.unpack('<h', pntr.data[offset:offset+2])
				if chnk.type == 0:
					 offset+=12
				else:
					[chnk.IX] = struct.unpack('<h', pntr.data[offset+2:offset+4])
					if chnk.IX == 0xffff:
						chnk.IX = -1
					chnk.level = ord(pntr.data[offset+4])
					chnk.unkn3 = ord(pntr.data[offset+5])
					[chnk.list] = struct.unpack('<h', pntr.data[offset+6:offset+8])
					[chnk.length] = struct.unpack('<L', pntr.data[offset+8:offset+12])
##				print 'T/IX/Lvl/Unk3/Lst/Len: %x %x %x %x %x %x'%(chnk.type,chnk.IX,chnk.level,chnk.unkn3,chnk.list,chnk.length),'DL/O: %x %x'%(len(pntr.data),offset)
			else:
				ch_hdr_len = 19
				[chnk.type] = struct.unpack('<L', pntr.data[offset:offset+4])
				if chnk.type == 0:
					# somehow failed with trailer?
					print "HERE"
					offset+=4
					[chnk.type] = struct.unpack('<L', pntr.data[offset:offset+4])

				[chnk.IX] = struct.unpack('<L', pntr.data[offset+4:offset+8])
				if chnk.IX == 0xffffffff:
					chnk.IX = -1
				[chnk.list] = struct.unpack('<L', pntr.data[offset+8:offset+12])
				[chnk.length] = struct.unpack('<L', pntr.data[offset+12:offset+16])
				[chnk.level] = struct.unpack('<h', pntr.data[offset+16:offset+18])
				chnk.unkn3 = ord(pntr.data[offset+18])
				trailer = 0
				
				if (chnk.list != 0) or (chnk.type == 0x71) or (chnk.type==0x70):
					trailer = 8
				if (0x64 == chnk.type or 0x6f == chnk.type or 0x6b == chnk.type or 0x6a == chnk.type or 0x69 == chnk.type or 0x66 == chnk.type or 0x65 == chnk.type or 0x2c == chnk.type):
					trailer = 8
				
				if(11 == version): #/* separators were found only in Visio2k3 atm.  trailer means that there is a separator too. */
					if 0 != chnk.list or\
						(2 == chnk.level and 0x51 == chnk.unkn3) or\
						(2 == chnk.level and 0x55 == chnk.unkn3) or\
						(2 == chnk.level and 0x54 == chnk.unkn3 and 0xaa == chnk.type) or\
						(3 == chnk.level and 0x50 != chnk.unkn3) or\
						(0x6f == chnk.type or 0x65 == chnk.type or 0x66 == chnk.type or 0x69 == chnk.type or 0x6a == chnk.type or 0x6b == chnk.type or 0x71 == chnk.type) or\
						(0x64 == chnk.type or 0xc7 == chnk.type or 0xb4 == chnk.type or 0xb6 == chnk.type or 0xb9 == chnk.type or 0xa9 == chnk.type) or\
						(0x2c == chnk.type and (0x50 == chnk.unkn3 or 0x54 == chnk.unkn3)):
						trailer = trailer + 4
				if(11 == version and (0x1f == chnk.type or 0xc9 == chnk.type or 0x2d == chnk.type or 0xd1 == chnk.type)):
					trailer = 0
# for data collection to verify rules
			chlistflag = 0
			if chnk.list > 0:
				chlistflag = 1

#			print chnk.type,"%02x"%chnk.type,chnk.level,chlistflag,"%02x"%chnk.unkn3,trailer
			
			if level==0:
				level=chnk.level
			ptr = vsd.pointer()
			ptr.data = pntr.data[offset:offset+ch_hdr_len+chnk.length+trailer]
			offset = offset + ch_hdr_len+ chnk.length+trailer

			debflag = 0
			if chunktype.has_key(chnk.type):
				itername = '%-24s'%chunktype[chnk.type]+'(IX: %02x  Len: %02x Lvl: %u)'%(chnk.IX, chnk.length,chnk.level)
			else:
				itername = 'Type: %02x \t\tI/L List/Level/u3: %02x/%02x  %02x %02x %02x'%(chnk.type,chnk.IX,chnk.length,chnk.list,chnk.level,chnk.unkn3)
				print "!!! --------------- !!!",'%02x'%chnk.type,'%02x'%chnk.level,
				debflag = 1
			if chnk.level ==0:
				path = path0
			if chnk.level ==1:
				path = path0
			if chnk.level == 2:
				path = path1
			if chnk.level == 3:
				path = path2
				
#			ptr.path = path			
			iter1 = model.append(path, None)
			model.set_value(iter1,0,itername)
			if version > 5:
				model.set_value(iter1,1,("vsd","chnk",chnk.type))
			else:
				model.set_value(iter1,1,("vsdv%d"%version,"chnk %s"%chnk.type))
			model.set_value(iter1,2,len(ptr.data))
			model.set_value(iter1,3,ptr.data)
			model.set_value(iter1,4,ptr)
			model.set_value(iter1,6,model.get_string_from_iter(iter1))
			if debflag:
				print model.get_string_from_iter(iter1)

			if version < 6 and chunklist.has_key(chnk.type):
				v5parse(page,version,iter1,ptr)

			if chnk.type == 0xd: #OLE_List
				olelist = model.append(iter1, None)
				olenum = chnk.list
				oledata = ""
			if chnk.type == 0x1f: #OLE_Data
				oledata += ptr.data[ch_hdr_len:]
				olenum -= 1
				if olenum == 0:
					model.set_value(olelist,0,"Collected OLE data")
					model.set_value(olelist,1,("vsd","chnk",0)) # fix to run OLE parse?
					model.set_value(olelist,2,len(oledata))
					model.set_value(olelist,3,oledata)
					model.set_value(olelist,5,"#96dfcf")
					model.set_value(olelist,6,model.get_string_from_iter(olelist))
					olelist = None
					oledata = ""
					

			if chnk.level ==0:
				path0 = iter1
			if chnk.level ==1:
				path1 = iter1
			if chnk.level == 2:
				path2 = iter1

#		except:
#			name = model.get_value(parent,0)
#			print 'Something wrong with chunks',name,'%x'%offset
#			offset = offset + 4 #ch_hdr_len, probably with +4 it will "autorecover" in some cases of underestimated trailer
	return
