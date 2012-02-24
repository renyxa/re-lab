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

def List (hd, size, value):
	if hd.version < 6:
		vsdchunks5.List(hd,size,value)
		return
	shl = struct.unpack("<I",value[19:19+4])[0]
	add_iter(hd,"SubHdrLen", "%2x"%shl,19,4,"<I")
	ch_list_len = struct.unpack("<I",value[23:23+4])[0]
	add_iter(hd, "ChldLstLen", "%2x"%ch_list_len,23,4,"<I")
	add_iter(hd,"SubHdr","",27,shl,"txt")

	ch_list = ""
	for i in range(ch_list_len/4):
		ch_list += "%02x "%struct.unpack("<I",value[27+shl+i*4:31+shl+i*4])[0]
	if ch_list != "":
		add_iter(hd,"ChldList",ch_list,27+shl,ch_list_len,"txt")
	else:
		add_iter(hd,"ChldList","[empty]",27+shl,ch_list_len,"txt")

def Text (hd, size, value):
	# no support for LangID for v.6
	if hd.version == 11:
		txt = unicode(value[0x1b:],'utf-16').encode('utf-8')
		fmt = "utxt"
	else:
		txt = value[0x1b:]
		fmt = "txt"
	add_iter(hd, "Text", txt,0x1b,len(value)-8,fmt)

def Page (hd, size, value):
	List (hd, size, value)
	add_iter(hd, "BG Page", "%x"%struct.unpack("<I",value[27:27+4])[0],27,4,"<I")
	add_iter(hd, "ViewScale?", struct.unpack("<d",value[45:45+8])[0],45,8,"<d")
	add_iter(hd, "ViewCntrX", struct.unpack("<d",value[53:53+8])[0],53,8,"<d")
	add_iter(hd, "ViewCntrY", struct.unpack("<d",value[61:61+8])[0],61,8,"<d")

def Shape (hd, size, value):
	List (hd, size, value)
	if hd.version < 6:
		vsdchunks5.Shape(hd,size,value)
		return
	add_iter(hd,"Parent","%2x"%struct.unpack("<I",value[0x1d:0x21])[0],0x1d,4,"<I")
	add_iter(hd,"Master","%2x"%struct.unpack("<I",value[37:37+4])[0],37,4,"<I")
	add_iter(hd,"MasterShape","%2x"%struct.unpack("<I",value[45:45+4])[0],45,4,"<I")
	add_iter(hd,"FillStyle","%2x"%struct.unpack("<I",value[53:53+4])[0],53,4,"<I")
	add_iter(hd,"LineStyle","%2x"%struct.unpack("<I",value[61:61+4])[0],61,4,"<I")
	add_iter(hd,"TextStyle","%2x"%struct.unpack("<I",value[69:69+4])[0],69,4,"<I")

def XForm (hd, size, value):
	add_iter(hd,"PinX","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"PinY","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"Width","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"Height","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	add_iter(hd,"LocPinX","%.2f"%struct.unpack("<d",value[56:64]),56,8,"<d")
	add_iter(hd,"LocPinY","%.2f"%struct.unpack("<d",value[65:73]),65,8,"<d")
	add_iter(hd,"Angle","%.2f"%struct.unpack("<d",value[74:82]),74,8,"<d")
	add_iter(hd,"FlipX","%2x"%ord(value[82]),82,1,"<I")
	add_iter(hd,"FlipY","%2x"%ord(value[83]),83,1,"<I")
	add_iter(hd,"ResizeMode","%2x"%ord(value[84]),84,1,"<I")
	if len(value)>0x58: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x58)

def XForm1D (hd, size, value):
	add_iter(hd,"BeginX","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"BeginY","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"EndX","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"EndY","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	if len(value)>0x39: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x39)

def TxtXForm (hd, size, value):
	add_iter(hd,"TxtPinX","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"TxtPinY","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"TxtWidth","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"TxtHeight","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	add_iter(hd,"TxtLocPinX","%.2f"%struct.unpack("<d",value[56:64]),56,8,"<d")
	add_iter(hd,"TxtLocPinY","%.2f"%struct.unpack("<d",value[65:73]),65,8,"<d")
	add_iter(hd,"TxtAngle","%.2f"%struct.unpack("<d",value[74:82]),74,8,"<d")
	if len(value)>0x58: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x58)

def MoveTo (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	if len(value)>0x27: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x27)

def ArcTo (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"A","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	if len(value)>0x30: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x30)

def InfLine (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"A","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"B","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	if len(value)>0x39: # both 6 and 11 ???
		vsdblock.parse(hd, size, value, 0x39)

def EllArcTo (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"A","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"B","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	add_iter(hd,"C","%.2f"%struct.unpack("<d",value[56:64]),56,8,"<d")
	add_iter(hd,"D","%.2f"%struct.unpack("<d",value[65:73]),65,8,"<d")
	if len(value)>0x4b: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x4b)

def Ellipse (hd, size, value):
	add_iter(hd,"Center X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Center Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"Right X","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"Right Y","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	add_iter(hd,"Top X","%.2f"%struct.unpack("<d",value[56:64]),56,8,"<d")
	add_iter(hd,"Top Y","%.2f"%struct.unpack("<d",value[65:73]),65,8,"<d")
	if len(value)>0x4b: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x4b)

def NameID (hd, size, value):
	if hd.version < 6:
		vsdchunks5.NameID(hd,size,value)
		return

	numofrec = struct.unpack("<I",value[19:19+4])[0]
	add_iter(hd,"#ofRecords","%2x"%numofrec,19,4,"<I")
	for i in range(numofrec):
		n1 = struct.unpack("<I",value[23+i*13:27+i*13])[0]
		n2 = struct.unpack("<I",value[27+i*13:31+i*13])[0]
		n3 = struct.unpack("<I",value[31+i*13:35+i*13])[0]
		flag = ord(value[35+i*13])
		add_iter(hd,"Rec #%d"%i,"%2x %2x %2x %2x"%(n1,n2,n3,flag),23+i*13,13,"txt")

linecaps = {0:"Round (SVG: Round)", 1:"Square (SVG: Butt)",2:"Extended (SVG: Square)"}

def Line (hd, size, value):
	add_iter(hd,"Weight","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"LineClrID","%2x"%ord(value[28]),28,1,"B")
	add_iter(hd,"LineClr","%02x%02x%02x"%(ord(value[29]),ord(value[30]),ord(value[31])),29,3,"clr")
	add_iter(hd,"LineXparency","%d %%"%(ord(value[32])/2.55),32,1,"B")
	add_iter(hd,"LinePatternID","%2x"%ord(value[33]),33,1,"B")
	add_iter(hd,"Rounding","%.2f"%struct.unpack("<d",value[35:43]),35,8,"<d")
	add_iter(hd,"EndArrSize","%2x"%ord(value[43]),43,1,"B")
	add_iter(hd,"BeginArrow","%2x"%ord(value[44]),44,1,"B")
	add_iter(hd,"EndArrow","%2x"%ord(value[45]),45,1,"B")
	lc = ord(value[46])
	lc_txt = "%2x "%lc
	if linecaps.has_key(lc):
		lc_txt += linecaps[lc]
	add_iter(hd,"LineCap",lc_txt,46,1,"txt")
	add_iter(hd,"BeginArrSize","%2x"%ord(value[47]),47,1,"B")
	if len(value)>0x36: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x36)

def Fill (hd, size, value):
	add_iter(hd,"FillFG","%2x"%ord(value[19]),19,1,"B")
	add_iter(hd,"FillFGClr","%02x%02x%02x"%(ord(value[20]),ord(value[21]),ord(value[22])),20,3,"clr")
	add_iter(hd,"FillFGXparency","%d %%"%(ord(value[23])/2.55),23,1,"B")
	add_iter(hd,"FillBG","%2x"%ord(value[24]),24,1,"B")
	add_iter(hd,"FillBGClr","%02x%02x%02x"%(ord(value[25]),ord(value[26]),ord(value[27])),25,3,"clr")
	add_iter(hd,"FillBGXparency","%d %%"%(ord(value[28])/2.55),28,1,"B")
	add_iter(hd,"FillPattern","%2x"%ord(value[29]),29,1,"B")
	add_iter(hd,"ShdwFG","%2x"%ord(value[30]),30,1,"B")
	add_iter(hd,"ShdwFGClr","%02x%02x%02x"%(ord(value[31]),ord(value[32]),ord(value[33])),31,3,"clr")
	add_iter(hd,"ShdwFGXparency","%d %%"%(ord(value[34])/2.56),34,1,"B")
	add_iter(hd,"ShdwBG","%2x"%ord(value[35]),35,1,"B")
	add_iter(hd,"ShdwBGClr","%02x%02x%02x"%(ord(value[36]),ord(value[37]),ord(value[38])),36,3,"clr")
	add_iter(hd,"ShdwBGXparency","%d %%"%(ord(value[39])/2.55),39,1,"B")
	add_iter(hd,"ShdwPattern","%2x"%ord(value[40]),40,1,"B")
	add_iter(hd,"ShdwType","%2x"%ord(value[0x29]),0x29,1,"B")
	if hd.version == 11:
		add_iter(hd,"ShdwOffsetX","%.2f"%struct.unpack("<d",value[0x2b:0x33]),0x2b,8,"<d")
		add_iter(hd,"ShdwOffsetY","%.2f"%struct.unpack("<d",value[0x34:0x3c]),0x34,8,"<d")
		add_iter(hd,"ShdwObliqueAngle","%.2f"%struct.unpack("<d",value[0x3d:0x45]),0x3d,8,"<d")
		add_iter(hd,"ShdwScaleFactor","%.2f"%struct.unpack("<d",value[0x45:0x4d]),0x45,8,"<d")
	if hd.version == 6 and len(value)>0x2c:
		vsdblock.parse(hd, size, value, 0x2c)
	elif len(value)>0x50 and hd.version == 11:
		vsdblock.parse(hd, size, value, 0x50)

def Char (hd, size, value):
	add_iter(hd,"Num of Chars","%d"%struct.unpack("<I",value[0x13:0x17]),0x13,4,"<I")
	add_iter(hd,"FontID","0x%02x"%struct.unpack("<H",value[0x17:0x19]),0x17,2,"<H")
	add_iter(hd,"ColorID","0x%02x"%ord(value[0x19]),0x19,1,"B")
	add_iter(hd,"Color","%02x%02x%02x"%(ord(value[0x1a]),ord(value[0x1b]),ord(value[0x1c])),0x1a,3,"clr")
	add_iter(hd,"Transparency","%d%%"%(ord(value[0x1d])*100/256),0x1d,1,"B")

	flags1 = ord(value[0x1e])
	ftxt = ""
	if flags1&1 == 1:
		ftxt += "bold "
	if flags1&2== 2:
		ftxt += "italic "
	if flags1&4 == 4:
		ftxt += "undrline "
	if flags1&8 == 8:
		ftxt += "smcaps "
	add_iter(hd,"Font Mods1",ftxt,0x1e,1,"txt")

	flags2 = ord(value[0x1f])
	ftxt = ""
	if flags2&1 == 1:
		ftxt += "allcaps "
	if flags2&2== 2:
		ftxt += "initcaps "
	add_iter(hd,"Font Mods2",ftxt,0x1f,1,"txt")
	
	flags3 = ord(value[0x20])
	ftxt = ""
	if flags3&1 == 1:
		ftxt += "superscript "
	if flags3&2== 2:
		ftxt += "subscript "
	add_iter(hd,"Font Mods3",ftxt,0x20,1,"txt")
	add_iter(hd,"Scale","%d%%"%(struct.unpack("<h",value[0x21:0x23])[0]/100.),0x21,2,"<h")
	add_iter(hd,"FontSize","%.2f pt"%(72*struct.unpack("<d",value[0x25:0x2d])[0]),0x25,8,"<d")

	flags4 = ord(value[0x2d])
	ftxt = ""
	if flags4&1 == 1:
		ftxt += "dblunder "
	if flags4&2== 2:
		ftxt += "overline "
	if flags4&20 == 20:
		ftxt += "dblstrike "
	add_iter(hd,"Font Mods4",ftxt,0x2d,1,"txt")
	add_iter(hd,"Spacing","%d pt"%(struct.unpack("<h",value[0x2e:0x30])[0]/200.),0x2e,2,"<h")
	if hd.version == 11:
		add_iter(hd,"AsianFont","%d"%ord(value[0x38]),0x38,1,"B")
		add_iter(hd,"ComplexScriptFont","%d"%ord(value[0x3a]),0x3a,1,"B")
		add_iter(hd,"LocalizeFont","%d"%ord(value[0x3c]),0x3c,1,"B")
		add_iter(hd,"ComplexScriptSize","%d%%"%(struct.unpack("<d",value[0x3e:0x46])[0]*100),0x3e,8,"<d")
		add_iter(hd,"LangID","%d"%struct.unpack("<I",value[0x58:0x5c]),0x58,4,"<I")
		if len(value)>0x6b and hd.version == 11:
			vsdblock.parse(hd, size, value, 0x6b)
	elif hd.version == 6 and len(value)>0x36:
		vsdblock.parse(hd, size, value, 0x36)


def Para (hd, size, value):
	add_iter(hd,"Num of Chars","%d"%struct.unpack("<I",value[0x13:0x17]),0x13,4,"<I")
	add_iter(hd,"IndFirst","%.2f"%struct.unpack("<d",value[0x18:0x20]),0x18,8,"<d")
	add_iter(hd,"IndLeft","%.2f"%struct.unpack("<d",value[0x21:0x29]),0x21,8,"<d")
	add_iter(hd,"IndRight","%.2f"%struct.unpack("<d",value[0x2a:0x32]),0x2a,8,"<d")
	add_iter(hd,"SpLine","%d%%"%(struct.unpack("<d",value[0x33:0x3b])[0]*100),0x33,8,"<d")
	add_iter(hd,"SpBefore","%d pt"%round(struct.unpack("<d",value[0x3c:0x44])[0]*72),0x3c,8,"<d")
	add_iter(hd,"SpAfter","%d pt"%round(struct.unpack("<d",value[0x45:0x4d])[0]*72),0x45,8,"<d")
	add_iter(hd,"HAlign","%d"%ord(value[0x4d]),0x4d,1,"B")
	add_iter(hd,"Bullet","%d"%ord(value[0x4e]),0x4e,1,"B")
	add_iter(hd,"BulletFont","%d"%struct.unpack("<H",value[0x53:0x55]),0x53,2,"<H")
	add_iter(hd,"LocBulletFont","%d"%ord(value[0x55]),0x55,1,"B")
	add_iter(hd,"BulletSize","%d%%"%(struct.unpack("<d",value[0x57:0x5f])[0]*100),0x57,8,"<d")
	add_iter(hd,"TxtPosAfterBullet","%.2f"%struct.unpack("<d",value[0x60:0x68]),0x60,8,"<d")
	add_iter(hd,"Flags","%d"%struct.unpack("<I",value[0x68:0x6c]),0x68,4,"<I")
	if hd.version == 6 and len(value)>0x5c:
		vsdblock.parse(hd, size, value, 0x5c)
	elif len(value)>0x8e and hd.version == 11:
		vsdblock.parse(hd, size, value, 0x8e)


def TextBlock (hd, size, value):
	add_iter(hd,"LeftMargin","%.2f"%round(struct.unpack("<d",value[0x14:0x1c])[0]*72),0x14,8,"<d")
	add_iter(hd,"RightMargin","%.2f"%round(struct.unpack("<d",value[0x1d:0x25])[0]*72),0x1d,8,"<d")
	add_iter(hd,"TopMargin","%.2f"%round(struct.unpack("<d",value[0x26:0x2e])[0]*72),0x26,8,"<d")
	add_iter(hd,"BottomMargin","%.2f"%round(struct.unpack("<d",value[0x2f:0x37])[0]*72),0x2f,8,"<d")
	add_iter(hd,"VAlign","%d"%ord(value[0x37]),0x37,1,"B")
	add_iter(hd,"TxtBG CLR Id","%d"%ord(value[0x38]),0x38,1,"B")
	add_iter(hd,"TxtBG Trans","%d"%round(ord(value[0x3c])*100/256.),0x3c,1,"B")
	add_iter(hd,"DefTabStop","%.2f"%struct.unpack("<d",value[0x3e:0x46]),0x3e,8,"<d")
	add_iter(hd,"TxtDirection","%d"%ord(value[0x52]),0x52,1,"B")
	if hd.version == 6 and len(value)>0x5a:
		vsdblock.parse(hd, size, value, 0x5a)
	elif len(value)>0x6f and hd.version == 11:
		vsdblock.parse(hd, size, value, 0x6f)

#0x92
def PageProps (hd, size, value):
	add_iter(hd,"PageWidth","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"PageHeight","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"ShdwOffsetX","%.2f"%struct.unpack("<d",value[38:46]),38,8,"<d")
	add_iter(hd,"ShdwOffsetY","%.2f"%struct.unpack("<d",value[47:55]),47,8,"<d")
	add_iter(hd,"PageScale","%.2f"%struct.unpack("<d",value[56:64]),56,8,"<d")
	add_iter(hd,"DrawingScale","%.2f"%struct.unpack("<d",value[65:73]),65,8,"<d")
	add_iter(hd,"DrawingSizeType","%2x"%ord(value[73]),82,1,"B")
	add_iter(hd,"DrawingScaleType","%2x"%ord(value[74]),83,1,"B")
	add_iter(hd,"ShdwObliqueAngle","%.2f"%struct.unpack("<d",value[0x61:0x69]),0x61,8,"<d")
	add_iter(hd,"ShdwScaleFactor","%.2f"%struct.unpack("<d",value[0x69:0x71]),0x69,8,"<d")
	if len(value)>0x9b:
		vsdblock.parse(hd, size, value, 0x96)


def StyleProps (hd, size, value):
	add_iter(hd,"Use Line",ord(value[0x13]),0x13,1,"<B")
	add_iter(hd,"Use Fill",ord(value[0x14]),0x14,1,"<B")
	add_iter(hd,"Use Text",ord(value[0x15]),0x15,1,"<B")
	add_iter(hd,"Hidden",ord(value[0x16]),0x16,1,"<B")
	if len(value)>0x1a:
		vsdblock.parse(hd, size, value, 0x1a)


def LayerIX (hd, size, value):
	if len(value)>0x34: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x34)


def Control (hd, size, value):
	add_iter(hd,"X","%.3f"%struct.unpack("<d",value[0x14:0x1c]),0x14,8,"<d")
	add_iter(hd,"Y","%.3f"%struct.unpack("<d",value[0x1d:0x25]),0x1d,8,"<d")
	add_iter(hd,"XDyn","%.3f"%struct.unpack("<d",value[0x26:0x2e]),0x26,84,8,"<d")
	add_iter(hd,"YDyn","%.3f"%struct.unpack("<d",value[0x2f:0x37]),0x2f,8,"<d")
	add_iter(hd,"XCon",ord(value[0x37]),0x37,1,"<B")
	add_iter(hd,"YCon",ord(value[0x38]),0x38,1,"<B")
	add_iter(hd,"CanGlue",ord(value[0x39]),0x39,1,"<B")
	if len(value)>0x42: # 11
		vsdblock.parse(hd, size, value, 0x42)


def PageLayout (hd, size, value):
	add_iter(hd,"LineToNodeX","%.3f"%struct.unpack("<d",value[0x1d:0x25]),0x1d,8,"<d")
	add_iter(hd,"LineToNodeY","%.3f"%struct.unpack("<d",value[0x26:0x2e]),0x26,8,"<d")
	add_iter(hd,"BlockSizeX","%.3f"%struct.unpack("<d",value[0x2f:0x37]),0x2f,8,"<d")
	add_iter(hd,"BlockSizeY","%.3f"%struct.unpack("<d",value[0x38:0x40]),0x38,8,"<d")
	add_iter(hd,"AvenueSizeX","%.3f"%struct.unpack("<d",value[0x41:0x49]),0x41,8,"<d")
	add_iter(hd,"AvenueSizeY","%.3f"%struct.unpack("<d",value[0x4a:0x52]),0x4a,8,"<d")
	add_iter(hd,"LineToLineX","%.3f"%struct.unpack("<d",value[0x53:0x5b]),0x53,8,"<d")
	add_iter(hd,"LineToLineY","%.3f"%struct.unpack("<d",value[0x5c:0x64]),0x5c,8,"<d")
	add_iter(hd,"LineJumpFactorX","%.3f"%struct.unpack("<d",value[0x64:0x6c]),0x64,8,"<d")
	add_iter(hd,"LineJumpFactorY","%.3f"%struct.unpack("<d",value[0x6c:0x74]),0x6c,8,"<d")


def Polyline (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	sdflag = value[0x26:0x2a]
	sdtext = 'No'
	if sdflag == '\x8b\x02\x00\x00':
		sdtext = 'Yes'
	add_iter(hd,"Use Shape Data",sdtext,0x26,4,"<I")
	add_iter(hd,"ShapeData Id","%02x"%struct.unpack("<I",value[0x2a:0x2e]),0x2a,4,"<I")
	if len(value)>0x30:
		vsdblock.parse(hd, size, value, 0x30)


def NURBS (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"Knot","%.2f"%struct.unpack("<d",value[37:45]),37,8,"<d")
	add_iter(hd,"Weight","%.2f"%struct.unpack("<d",value[45:53]),45,8,"<d")
	add_iter(hd,"KnotPrev","%.2f"%struct.unpack("<d",value[53:61]),53,8,"<d")
	add_iter(hd,"WeightPrev","%.2f"%struct.unpack("<d",value[61:69]),61,8,"<d")
	sdflag = value[0x46:0x4a]
	sdtext = 'No'
	if sdflag == '\x8a\x02\x00\x00':
		sdtext = 'Yes'
	add_iter(hd,"Use Shape Data",sdtext,0x46,4,"<d")
	add_iter(hd,"ShapeData Id","%02x"%struct.unpack("<I",value[0x4a:0x4e]),0x4a,4,"<I")
	if len(value)>80:
		vsdblock.parse(hd, size, value, 80)

nd_types = {0x80:"Polyline",0x82:"NURBS"}

def ShapeData (hd, size, value):
	nd_type = ord(value[19])
	nd_str = "%02x "%nd_type
	if nd_types.has_key(nd_type):
		nd_str += "("+nd_types[nd_type]+")"
	add_iter(hd,"Type",nd_str,19,1,"b")
	if nd_type == 0x80:
		xType = ord(value[0x23])
		yType = ord(value[0x24])
		add_iter(hd,"xType",xType,0x23,1,"b")
		add_iter(hd,"yType",yType,0x24,1,"b")
		[num_pts] = struct.unpack("<I",value[0x25:0x29])
		add_iter(hd,"# of pts",num_pts,0x25,4,"<I")
		for i in range(num_pts):
			add_iter(hd,"x%d"%(i+1),"%.2f"%struct.unpack("<d",value[0x29+i*16:0x31+i*16]),0x29+i*16,8,"<d")
			add_iter(hd,"y%d"%(i+1),"%.2f"%struct.unpack("<d",value[0x31+i*16:0x39+i*16]),0x31+i*16,8,"<d")
	if nd_type == 0x82:
		add_iter(hd,"knotLast","%.2f"%struct.unpack("<d",value[0x23:0x2b]),0x23,8,"<d")
		add_iter(hd,"degree","%.2f"%struct.unpack("<h",value[0x2b:0x2d]),0x2b,2,"<h")
		xType = ord(value[0x2d])
		yType = ord(value[0x2e])
		add_iter(hd,"xType",xType,0x2d,1,"b")
		add_iter(hd,"yType",yType,0x2e,1,"b")
		[num_pts] = struct.unpack("<I",value[0x2f:0x33])
		add_iter(hd,"# of pts",num_pts,0x2f,4,"<I")
		for i in range(num_pts):
			add_iter(hd,"x%d"%(i+1),"%.2f"%struct.unpack("<d",value[0x33+i*32:0x3b+i*32]),0x33+i*32,8,"<d")
			add_iter(hd,"y%d"%(i+1),"%.2f"%struct.unpack("<d",value[0x3b+i*32:0x43+i*32]),0x3b+i*32,8,"<d")
			add_iter(hd,"knot%d"%(i+1),"%.2f"%struct.unpack("<d",value[0x43+i*32:0x4b+i*32]),0x43+i*32,8,"<d")
			add_iter(hd,"weight%d"%(i+1),"%.2f"%struct.unpack("<d",value[0x4b+i*32:0x53+i*32]),0x4b+i*32,8,"<d")


bits = {1:'noFill',2:'noLine',4:'noShow',8:'noSnap',32:'noQuickDrag'}

def Geometry (hd, size, value):
	flags = ord(value[19])
	for i in (1,2,4,8,32):
		res = 'No'
		if flags&i:
			res = 'Yes'
		add_iter(hd,bits[i],res,19,1,"txt")
	if len(value)>0x16:
		vsdblock.parse(hd, size, value, 0x16)


def ShapeStencil (hd, size, value):
	add_iter(hd,"ID?","%02x"%struct.unpack("<I",value[0x13:0x17]),0x13,4,"<I")
	add_iter(hd,"var1?","%.2f"%struct.unpack("<d",value[0x17:0x1f]),0x17,8,"<d")
	add_iter(hd,"var2?","%.2f"%struct.unpack("<d",value[0x1f:0x27]),0x1f,8,"<d")
	add_iter(hd,"var3?","%.2f"%struct.unpack("<d",value[0x27:0x2f]),0x27,8,"<d")
	add_iter(hd,"var4?","%.2f"%struct.unpack("<d",value[0x2f:0x37]),0x2f,8,"<d")

def TextField (hd, size, value):
	fmt = ord(value[0x1a])
	tdiff = struct.unpack("<d",value[0x1b:0x23])[0]
	dlen = 8
	dfmt = "<d"
	if fmt == 0x28:
		dt = datetime.datetime(1899,12,30)+datetime.timedelta(tdiff)
		dname = "Date"
	elif fmt == 0xe8:
		dt = struct.unpack("<I",value[0x1b:0x1f])[0]
		dname = "Name ID"
		dlen = 4
		dfmt = "<I"
	else:
		dt = "%.2f"%tdiff
		dname = "Value"
	fmtidtype = ord(value[0x24])
	if fmtidtype == 0xe8:
		fmtid = struct.unpack("<I",value[0x25:0x29])[0]
		fmtname = "Format ID"
		fmtlen = 4
		fmtfmt = "<I"
	add_iter(hd,dname,dt,0x1b,dlen,dfmt)
	add_iter(hd,fmtname,fmtid,0x25,fmtlen,fmtfmt)
	dtype = struct.unpack("<H",value[0x2d:0x2f])[0]
	add_iter(hd,"Type",dtype,0x2d,2,"<H")
	add_iter(hd,"UICat","0x%02x"%ord(value[0x2f]),0x2f,1,"B")
	add_iter(hd,"UICod","0x%02x"%ord(value[0x30]),0x30,1,"B")
	add_iter(hd,"UIFmt","0x%02x"%ord(value[0x31]),0x31,1,"B")
	if hd.version == 6 and len(value)>0x37:
		vsdblock.parse(hd, size, value, 0x37)
	elif len(value)>0x49:
		vsdblock.parse(hd, size, value, 0x49)


def SplineStart (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"Knot","%.2f"%struct.unpack("<d",value[0x25:0x2d]),0x25,8,"<d")
	add_iter(hd,"Knot2","%.2f"%struct.unpack("<d",value[0x2d:0x35]),0x2d,8,"<d")
	add_iter(hd,"Knot3","%.2f"%struct.unpack("<d",value[0x35:0x3d]),0x35,8,"<d")
	add_iter(hd,"Degree","%d"%struct.unpack("<h",value[0x3d:0x3f]),0x3d,2,"<h")
	if len(value)>0x41:
		vsdblock.parse(hd, size, value, 0x41)


def SplineKnot (hd, size, value):
	add_iter(hd,"X","%.2f"%struct.unpack("<d",value[20:28]),20,8,"<d")
	add_iter(hd,"Y","%.2f"%struct.unpack("<d",value[29:37]),29,8,"<d")
	add_iter(hd,"Knot","%.2f"%struct.unpack("<d",value[0x25:0x2d]),0x25,8,"<d")
	if len(value)>0x2f:
		vsdblock.parse(hd, size, value, 0x2f)


def FrgnType (hd, size, value):
	add_iter(hd,"ImgOffsetX","%.2f"%struct.unpack("<d",value[0x14:0x1c]),0x14,8,"<d")
	add_iter(hd,"ImgOffsetY","%.2f"%struct.unpack("<d",value[0x1d:0x25]),0x1d,8,"<d")
	add_iter(hd,"ImgWidth","%.2f"%struct.unpack("<d",value[0x26:0x2e]),0x26,8,"<d")
	add_iter(hd,"ImgHeight","%.2f"%struct.unpack("<d",value[0x2f:0x37]),0x2f,8,"<d")
	[ftype] = struct.unpack("<h",value[0x37:0x39])
	add_iter(hd,"Type ??","%d"%ftype,0x37,2,"<h")
	add_iter(hd,"MapMode","%d"%struct.unpack("<h",value[0x39:0x3b]),0x39,2,"<h")
	if ftype == 4:
		add_iter(hd,"ExtentX","%d"%struct.unpack("<h",value[0x3b:0x3d]),0x3b,2,"<h")
		add_iter(hd,"ExtentY","%d"%struct.unpack("<h",value[0x3d:0x3f]),0x3d,2,"<h")
	if len(value)>0x51:
		vsdblock.parse(hd, size, value, 0x51)


chnk_func = {
	0xe:Text,
	0x15:Page,
	0x28:ShapeStencil,
	0xd:List,0x2c:List,
	0x46:Shape,0x47:Shape, 0x48:Shape, 0x4a:Shape, 0x4e:Shape,0x4f:Shape,
	0x64:List,0x65:List,0x66:List,0x67:List,0x68:List,0x69:List,0x6a:List,0x6b:List,0x6c:List,
	0x6d:List,0x6e:List,0x6f:List,0x70:List,0x71:List,0x72:List,0x76:List,
	0x85:Line,0x86:Fill,0x87:TextBlock,0x89:Geometry,
	0x8a:MoveTo,0x8b:MoveTo,0x8c:ArcTo,0x8d:InfLine,
	0x8f:Ellipse,0x90:EllArcTo,
	0x92:PageProps,0x93:StyleProps,
	0x94:Char,0x95:Para,0x98:FrgnType,0x9b:XForm,0x9c:TxtXForm,0x9d:XForm1D,
	0xa1:TextField,0xa5:SplineStart,0xa6:SplineKnot,0xa8:LayerIX,0xaa:Control,
	0xc0:PageLayout,0xc1:Polyline,0xc3:NURBS, 0xc9:NameID,
	0xd1:ShapeData
}

def parse(model, version, parent, pntr):
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
		try:
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
					offset+=4
				else:
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

			if chunktype.has_key(chnk.type):
				itername = '%-24s'%chunktype[chnk.type]+'(IX: %02x  Len: %02x Lvl: %u)'%(chnk.IX, chnk.length,chnk.level)
			else:
				itername = 'Type: %02x \t\tI/L List/Level/u3: %02x/%02x  %02x %02x %02x'%(chnk.type,chnk.IX,chnk.length,chnk.list,chnk.level,chnk.unkn3)
				print "!!! --------------- !!!",'%02x'%chnk.type,'%02x'%chnk.level
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
			model.set_value(iter1,1,("vsd","chnk",chnk.type))
			model.set_value(iter1,2,len(ptr.data))
			model.set_value(iter1,3,ptr.data)
			model.set_value(iter1,4,ptr)
			model.set_value(iter1,6,model.get_string_from_iter(iter1))

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

		except:
			name = model.get_value(parent,0)
			print 'Something wrong with chunks',name,'%x'%offset
			offset = offset + 4 #ch_hdr_len, probably with +4 it will "autorecover" in some cases of underestimated trailer
	return
