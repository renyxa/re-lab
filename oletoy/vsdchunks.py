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
import vsd,vsdblock

chunknoshift = {
		0x15:'Page',\
		0x18:'FontFaces',\
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
		0x18:'FontFaces',\
		0x19:'FontFace ',\
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
	iter1 = hd.hdmodel.append(None, None)
	shl = struct.unpack("<I",value[19:19+4])[0]
	hd.hdmodel.set (iter1, 0, "SubHdrLen", 1, "%2x"%shl,2,19,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	ch_list_len = struct.unpack("<I",value[23:23+4])[0]
	hd.hdmodel.set (iter1, 0, "ChldLstLen", 1, "%2x"%ch_list_len,2,23,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "SubHdr", 1, "",2,27,3,shl,4,"txt")
	ch_list = ""
	for i in range(ch_list_len/4):
		ch_list += "%02x "%struct.unpack("<I",value[27+shl+i*4:31+shl+i*4])[0]
	iter1 = hd.hdmodel.append(None, None)
	if ch_list != "":
		hd.hdmodel.set (iter1, 0, "ChldList", 1, ch_list,2,27+shl,3,ch_list_len,4,"txt")
	else:
		hd.hdmodel.set (iter1, 0, "ChldList", 1, "[empty]",2,27+shl,3,ch_list_len,4,"txt")

def Text (hd, size, value):
	# no support for LangID for v.6
	if hd.version == 11:
		txt = unicode(value[0x1b:],'utf-16').encode('utf-8')
	else:
		txt = value[0x1b:]
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Text", 1,txt,2,0x1b,3,len(value)-8,4,"txt")

def Page (hd, size, value):
	List (hd, size, value)
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BG Page", 1,"%d"%struct.unpack("<I",value[27:27+4])[0],2,27,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ViewScale?", 1,struct.unpack("<d",value[45:45+8])[0],2,45,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ViewCntrX", 1, struct.unpack("<d",value[53:53+8])[0],2,53,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ViewCntrY", 1, struct.unpack("<d",value[61:61+8])[0],2,61,3,8,4,"<d")

def Shape (hd, size, value):
	List (hd, size, value)
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Parent", 1, "%2x"%struct.unpack("<I",value[0x1d:0x21])[0],2,0x1d,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Master", 1, "%2x"%struct.unpack("<I",value[37:37+4])[0],2,37,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "MasterShape", 1, "%2x"%struct.unpack("<I",value[45:45+4])[0],2,45,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineStyle", 1, "%2x"%struct.unpack("<I",value[53:53+4])[0],2,53,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillStyle", 1, "%2x"%struct.unpack("<I",value[61:61+4])[0],2,61,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TextStyle", 1, "%2x"%struct.unpack("<I",value[69:69+4])[0],2,69,3,4,4,"<I")

def XForm (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "PinX", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "PinY", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Width", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Height", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LocPinX", 1, "%.2f"%struct.unpack("<d",value[56:64]),2,56,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LocPinY", 1, "%.2f"%struct.unpack("<d",value[65:73]),2,65,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Angle", 1, "%.2f"%struct.unpack("<d",value[74:82]),2,74,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FlipX", 1, "%2x"%ord(value[82]),2,82,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FlipY", 1, "%2x"%ord(value[83]),2,83,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ResizeMode", 1, "%2x"%ord(value[84]),2,84,3,1,4,"<I")
	if len(value)>0x58: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x58)

def XForm1D (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BeginX", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BeginY", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "EndX", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "EndY", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	if len(value)>0x39: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x39)

def TxtXForm (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtPinX", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtPinY", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtWidth", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtHeight", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtLocPinX", 1, "%.2f"%struct.unpack("<d",value[56:64]),2,56,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtLocPinY", 1, "%.2f"%struct.unpack("<d",value[65:73]),2,65,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtAngle", 1, "%.2f"%struct.unpack("<d",value[74:82]),2,74,3,8,4,"<d")
	if len(value)>0x58: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x58)

def MoveTo (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	if len(value)>0x27: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x27)

def ArcTo (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "A", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	if len(value)>0x30: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x30)

def InfLine (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "A", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "B", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	if len(value)>0x39: # both 6 and 11 ???
		vsdblock.parse(hd, size, value, 0x39)

def EllArcTo (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "A", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "B", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "C", 1, "%.2f"%struct.unpack("<d",value[56:64]),2,56,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "D", 1, "%.2f"%struct.unpack("<d",value[65:73]),2,65,3,8,4,"<d")
	if len(value)>0x4b: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x4b)

def Ellipse (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Center X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Center Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Right X", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Right Y", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Top X", 1, "%.2f"%struct.unpack("<d",value[56:64]),2,56,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Top Y", 1, "%.2f"%struct.unpack("<d",value[65:73]),2,65,3,8,4,"<d")
	if len(value)>0x4b: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x4b)

def NameID (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	numofrec = struct.unpack("<I",value[19:19+4])[0]
	hd.hdmodel.set (iter1, 0, "#ofRecords", 1, "%2x"%numofrec,2,19,3,4,4,"<I")
	for i in range(numofrec):
		n1 = struct.unpack("<I",value[23+i*13:27+i*13])[0]
		n2 = struct.unpack("<I",value[27+i*13:31+i*13])[0]
		n3 = struct.unpack("<I",value[31+i*13:35+i*13])[0]
		flag = ord(value[35+i*13])
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "Rec #%d"%i, 1, "%2x %2x %2x %2x"%(n1,n2,n3,flag),2,23+i*13,3,13,4,"txt")

def Line (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Weight", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineClrID", 1, "%2x"%ord(value[28]),2,28,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineClr", 1, "%02x%02x%02x"%(ord(value[29]),ord(value[30]),ord(value[31])),2,29,3,3,4,"clr")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineXparency", 1, "%d %%"%(ord(value[32])/2.56),2,32,3,1,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LinePatternID", 1, "%2x"%ord(value[33]),2,33,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Rounding", 1, "%.2f"%struct.unpack("<d",value[35:43]),2,35,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "EndArrSize", 1, "%2x"%ord(value[43]),2,43,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BeginArrow", 1, "%2x"%ord(value[44]),2,44,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "EndArrow", 1, "%2x"%ord(value[45]),2,45,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineCap", 1, "%2x"%ord(value[46]),2,46,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BeginArrSize", 1, "%2x"%ord(value[47]),2,47,3,1,4,"<I")
	if len(value)>0x36: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x36)

def Fill (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillFG", 1, "%2x"%ord(value[19]),2,19,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillFGClr", 1, "%02x%02x%02x"%(ord(value[20]),ord(value[21]),ord(value[22])),2,20,3,3,4,"clr")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillFGXparency", 1, "%d %%"%(ord(value[23])/2.56),2,23,3,1,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillBG", 1, "%2x"%ord(value[24]),2,24,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillBGClr", 1, "%02x%02x%02x"%(ord(value[25]),ord(value[26]),ord(value[27])),2,25,3,3,4,"clr")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillBGXparency", 1, "%d %%"%(ord(value[28])/2.56),2,28,3,1,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FillPattern", 1, "%2x"%ord(value[29]),2,29,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwFG", 1, "%2x"%ord(value[30]),2,30,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwFGClr", 1, "%02x%02x%02x"%(ord(value[31]),ord(value[32]),ord(value[33])),2,31,3,3,4,"clr")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwFGXparency", 1, "%d %%"%(ord(value[34])/2.56),2,34,3,1,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwBG", 1, "%2x"%ord(value[35]),2,35,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwBGClr", 1, "%02x%02x%02x"%(ord(value[36]),ord(value[37]),ord(value[38])),2,36,3,3,4,"clr")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwBGXparency", 1, "%d %%"%(ord(value[39])/2.56),2,39,3,1,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwPattern", 1, "%2x"%ord(value[40]),2,40,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwType", 1, "%2x"%ord(value[0x29]),2,0x29,3,1,4,"<I")
	if hd.version == 11:
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ShdwOffsetX", 1, "%.2f"%struct.unpack("<d",value[0x2b:0x33]),2,0x2b,3,8,4,"<d")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ShdwOffsetY", 1, "%.2f"%struct.unpack("<d",value[0x34:0x3c]),2,0x34,3,8,4,"<d")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ShdwObliqueAngle", 1, "%.2f"%struct.unpack("<d",value[0x3d:0x45]),2,0x3d,3,8,4,"<d")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ShdwScaleFactor", 1, "%.2f"%struct.unpack("<d",value[0x45:0x4d]),2,0x45,3,8,4,"<d")
	if hd.version == 6 and len(value)>0x2c:
		vsdblock.parse(hd, size, value, 0x2c)
	elif len(value)>0x50 and hd.version == 11:
		vsdblock.parse(hd, size, value, 0x50)

def Char (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Num of Chars", 1, "%d"%struct.unpack("<I",value[0x13:0x17]),2,0x13,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FontID", 1, "%2x"%struct.unpack("<H",value[0x17:0x19]),2,0x17,3,2,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Transparency", 1, "%d%%"%(ord(value[0x1d])*100/256),2,0x1d,3,1,4,"<I")

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
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Font Mods1", 1, ftxt,2,0x1e,3,1,4,"txt")

	flags2 = ord(value[0x1f])
	ftxt = ""
	if flags2&1 == 1:
		ftxt += "allcaps "
	if flags2&2== 2:
		ftxt += "initcaps "
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Font Mods2", 1, ftxt,2,0x1f,3,1,4,"txt")
	
	flags3 = ord(value[0x20])
	ftxt = ""
	if flags3&1 == 1:
		ftxt += "superscript "
	if flags3&2== 2:
		ftxt += "subscript "
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Font Mods3", 1, ftxt,2,0x20,3,1,4,"txt")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Scale", 1, "%d%%"%(struct.unpack("<h",value[0x21:0x23])[0]/100.),2,0x21,3,2,4,"<h")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "FontSize", 1, "%.2f pt"%(72*struct.unpack("<d",value[0x25:0x2d])[0]),2,0x25,3,8,4,"<d")

	flags4 = ord(value[0x2d])
	ftxt = ""
	if flags4&1 == 1:
		ftxt += "dblunder "
	if flags4&2== 2:
		ftxt += "overline "
	if flags4&20 == 20:
		ftxt += "dblstrike "
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Font Mods4", 1, ftxt,2,0x2d,3,1,4,"txt")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Spacing", 1, "%d pt"%(struct.unpack("<h",value[0x2e:0x30])[0]/200.),2,0x2e,3,2,4,"<h")
	if hd.version == 11:
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "AsianFont", 1, "%d"%ord(value[0x38]),2,0x38,3,1,4,"<I")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ComplexScriptFont", 1, "%d"%ord(value[0x3a]),2,0x3a,3,1,4,"<I")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "LocalizeFont", 1, "%d"%ord(value[0x3c]),2,0x3c,3,1,4,"<I")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ComplexScriptSize", 1, "%d%%"%(struct.unpack("<d",value[0x3e:0x46])[0]*100),2,0x3e,3,8,4,"<d")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "LangID", 1, "%d"%struct.unpack("<I",value[0x58:0x5c]),2,0x58,3,4,4,"<I")
		if len(value)>0x6b and hd.version == 11:
			vsdblock.parse(hd, size, value, 0x6b)
	elif hd.version == 6 and len(value)>0x36:
		vsdblock.parse(hd, size, value, 0x36)



def Para (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Num of Chars", 1, "%d"%struct.unpack("<I",value[0x13:0x17]),2,0x13,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "IndFirst", 1, "%.2f"%struct.unpack("<d",value[0x18:0x20]),2,0x18,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "IndLeft", 1, "%.2f"%struct.unpack("<d",value[0x21:0x29]),2,0x21,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "IndRight", 1, "%.2f"%struct.unpack("<d",value[0x2a:0x32]),2,0x2a,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "SpLine", 1, "%d%%"%(struct.unpack("<d",value[0x33:0x3b])[0]*100),2,0x33,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "SpBefore", 1, "%d pt"%round(struct.unpack("<d",value[0x3c:0x44])[0]*72),2,0x3c,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "SpAfter", 1, "%d pt"%round(struct.unpack("<d",value[0x45:0x4d])[0]*72),2,0x45,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "HAlign", 1, "%d"%ord(value[0x4d]),2,0x4d,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Bullet", 1, "%d"%ord(value[0x4e]),2,0x4e,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BulletFont", 1, "%d"%struct.unpack("<H",value[0x53:0x55]),2,0x53,3,2,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LocBulletFont", 1, "%d"%ord(value[0x55]),2,0x55,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BulletSize", 1, "%d%%"%(struct.unpack("<d",value[0x57:0x5f])[0]*100),2,0x57,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtPosAfterBullet", 1, "%.2f"%struct.unpack("<d",value[0x60:0x68]),2,0x60,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Flags", 1, "%d"%struct.unpack("<I",value[0x68:0x6c]),2,0x68,3,4,4,"<I")
	if hd.version == 6 and len(value)>0x5c:
		vsdblock.parse(hd, size, value, 0x5c)
	elif len(value)>0x8e and hd.version == 11:
		vsdblock.parse(hd, size, value, 0x8e)


def TextBlock (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LeftMargin", 1, "%.2f"%round(struct.unpack("<d",value[0x14:0x1c])[0]*72),2,0x14,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "RightMargin", 1, "%.2f"%round(struct.unpack("<d",value[0x1d:0x25])[0]*72),2,0x1d,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TopMargin", 1, "%.2f"%round(struct.unpack("<d",value[0x26:0x2e])[0]*72),2,0x26,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BottomMargin", 1, "%.2f"%round(struct.unpack("<d",value[0x2f:0x37])[0]*72),2,0x2f,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "VAlign", 1, "%d"%ord(value[0x37]),2,0x37,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtBG CLR Id", 1, "%d"%ord(value[0x38]),2,0x38,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtBG Trans", 1, "%d"%round(ord(value[0x3c])*100/256.),2,0x3c,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "DefTabStop", 1, "%.2f"%struct.unpack("<d",value[0x3e:0x46]),2,0x3e,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "TxtDirection", 1, "%d"%ord(value[0x52]),2,0x52,3,1,4,"<I")
	if hd.version == 6 and len(value)>0x5a:
		vsdblock.parse(hd, size, value, 0x5a)
	elif len(value)>0x6f and hd.version == 11:
		vsdblock.parse(hd, size, value, 0x6f)

#0x92
def PageProps (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "PageWidth", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "PageHeight", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwOffsetX", 1, "%.2f"%struct.unpack("<d",value[38:46]),2,38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwOffsetY", 1, "%.2f"%struct.unpack("<d",value[47:55]),2,47,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "PageScale", 1, "%.2f"%struct.unpack("<d",value[56:64]),2,56,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "DrawingScale", 1, "%.2f"%struct.unpack("<d",value[65:73]),2,65,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "DrawingSizeType", 1, "%2x"%ord(value[73]),2,82,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "DrawingScaleType", 1, "%2x"%ord(value[74]),2,83,3,1,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwObliqueAngle", 1, "%.2f"%struct.unpack("<d",value[0x61:0x69]),2,0x61,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShdwScaleFactor", 1, "%.2f"%struct.unpack("<d",value[0x69:0x71]),2,0x69,3,8,4,"<d")

	if len(value)>0x9b:
		vsdblock.parse(hd, size, value, 0x96)

def StyleProps (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Use Line", 1, ord(value[0x13]),2,0x13,3,1,4,"<B")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Use Fill", 1, ord(value[0x14]),2,0x14,3,1,4,"<B")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Use Text", 1, ord(value[0x15]),2,0x15,3,1,4,"<B")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Hidden", 1, ord(value[0x16]),2,0x16,3,1,4,"<B")
	if len(value)>0x1a:
		vsdblock.parse(hd, size, value, 0x1a)
	

def LayerIX (hd, size, value):
	if len(value)>0x34: # both 6 and 11
		vsdblock.parse(hd, size, value, 0x34)

def Control (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.3f"%struct.unpack("<d",value[0x14:0x1c]),2,0x14,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.3f"%struct.unpack("<d",value[0x1d:0x25]),2,0x1d,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "XDyn", 1, "%.3f"%struct.unpack("<d",value[0x26:0x2e]),2,0x26,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "YDyn", 1, "%.3f"%struct.unpack("<d",value[0x2f:0x37]),2,0x2f,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "XCon", 1, ord(value[0x37]),2,0x37,3,1,4,"<B")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "YCon", 1, ord(value[0x38]),2,0x38,3,1,4,"<B")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "CanGlue", 1, ord(value[0x39]),2,0x39,3,1,4,"<B")
	if len(value)>0x42: # 11
		vsdblock.parse(hd, size, value, 0x42)


def PageLayout (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineToNodeX", 1, "%.3f"%struct.unpack("<d",value[0x1d:0x25]),2,0x1d,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineToNodeY", 1, "%.3f"%struct.unpack("<d",value[0x26:0x2e]),2,0x26,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BlockSizeX", 1, "%.3f"%struct.unpack("<d",value[0x2f:0x37]),2,0x2f,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "BlockSizeY", 1, "%.3f"%struct.unpack("<d",value[0x38:0x40]),2,0x38,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "AvenueSizeX", 1, "%.3f"%struct.unpack("<d",value[0x41:0x49]),2,0x41,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "AvenueSizeY", 1, "%.3f"%struct.unpack("<d",value[0x4a:0x52]),2,0x4a,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineToLineX", 1, "%.3f"%struct.unpack("<d",value[0x53:0x5b]),2,0x53,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineToLineY", 1, "%.3f"%struct.unpack("<d",value[0x5c:0x64]),2,0x5c,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineJumpFactorX", 1, "%.3f"%struct.unpack("<d",value[0x64:0x6c]),2,0x64,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "LineJumpFactorY", 1, "%.3f"%struct.unpack("<d",value[0x6c:0x74]),2,0x6c,3,8,4,"<d")


def Polyline (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	sdflag = value[0x26:0x2a]
	sdtext = 'No'
	if sdflag == '\x8b\x02\x00\x00':
		sdtext = 'Yes'
	hd.hdmodel.set (iter1, 0, "Use Shape Data", 1, sdtext,2,0x26,3,4,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShapeData Id", 1, "%02x"%struct.unpack("<I",value[0x2a:0x2e]),2,0x2a,3,4,4,"<I")
	if len(value)>0x30:
		vsdblock.parse(hd, size, value, 0x30)


def NURBS (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Knot", 1, "%.2f"%struct.unpack("<d",value[37:45]),2,37,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Weight", 1, "%.2f"%struct.unpack("<d",value[45:53]),2,45,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "KnotPrev", 1, "%.2f"%struct.unpack("<d",value[53:61]),2,53,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "WeightPrev", 1, "%.2f"%struct.unpack("<d",value[61:69]),2,61,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	sdflag = value[0x46:0x4a]
	sdtext = 'No'
	if sdflag == '\x8a\x02\x00\x00':
		sdtext = 'Yes'
	hd.hdmodel.set (iter1, 0, "Use Shape Data", 1, sdtext,2,0x46,3,4,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShapeData Id", 1, "%02x"%struct.unpack("<I",value[0x4a:0x4e]),2,0x4a,3,4,4,"<I")
	if len(value)>80:
		vsdblock.parse(hd, size, value, 80)

nd_types = {0x80:"Polyline",0x82:"NURBS"}

def ShapeData (hd, size, value):
	nd_type = ord(value[19])
	nd_str = "%02x "%nd_type
	if nd_types.has_key(nd_type):
		nd_str += "("+nd_types[nd_type]+")"
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Type", 1, nd_str,2,19,3,1,4,"<b")
	if nd_type == 0x80:
		xType = ord(value[0x23])
		yType = ord(value[0x24])
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "xType", 1, xType,2,0x23,3,1,4,"<b")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "yType", 1, yType,2,0x24,3,1,4,"<b")
		[num_pts] = struct.unpack("<I",value[0x25:0x29])
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "# of pts", 1, num_pts,2,0x25,3,4,4,"<I")
		for i in range(num_pts):
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "x%d"%(i+1), 1, "%.2f"%struct.unpack("<d",value[0x29+i*16:0x31+i*16]),2,0x29+i*16,3,8,4,"<d")
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "y%d"%(i+1), 1, "%.2f"%struct.unpack("<d",value[0x31+i*16:0x39+i*16]),2,0x31+i*16,3,8,4,"<d")
	if nd_type == 0x82:
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "knotLast", 1, "%.2f"%struct.unpack("<d",value[0x23:0x2b]),2,0x23,3,8,4,"<d")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "degree", 1, "%.2f"%struct.unpack("<h",value[0x2b:0x2d]),2,0x2b,3,2,4,"<h")
		xType = ord(value[0x2d])
		yType = ord(value[0x2e])
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "xType", 1, xType,2,0x2d,3,1,4,"<b")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "yType", 1, yType,2,0x2e,3,1,4,"<b")
		[num_pts] = struct.unpack("<I",value[0x2f:0x33])
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "# of pts", 1, num_pts,2,0x2f,3,4,4,"<I")
		for i in range(num_pts):
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "x%d"%(i+1), 1, "%.2f"%struct.unpack("<d",value[0x33+i*32:0x3b+i*32]),2,0x33+i*32,3,8,4,"<d")
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "y%d"%(i+1), 1, "%.2f"%struct.unpack("<d",value[0x3b+i*32:0x43+i*32]),2,0x3b+i*32,3,8,4,"<d")
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "knot%d"%(i+1), 1, "%.2f"%struct.unpack("<d",value[0x43+i*32:0x4b+i*32]),2,0x43+i*32,3,8,4,"<d")
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "weight%d"%(i+1), 1, "%.2f"%struct.unpack("<d",value[0x4b+i*32:0x53+i*32]),2,0x4b+i*32,3,8,4,"<d")


bits = {1:'noFill',2:'noLine',4:'noShow',8:'noSnap',32:'noQuickDrag'}

def Geometry (hd, size, value):
	flags = ord(value[19])
	for i in (1,2,4,8,32):
		res = 'No'
		if flags&i:
			res = 'Yes'
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, bits[i], 1, res,2,19,3,1,4,"txt")
	if len(value)>0x16:
		vsdblock.parse(hd, size, value, 0x16)


def ShapeStencil (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ID?", 1, "%02x"%struct.unpack("<I",value[0x13:0x17]),2,0x13,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "var1?", 1, "%.2f"%struct.unpack("<d",value[0x17:0x1f]),2,0x17,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "var2?", 1, "%.2f"%struct.unpack("<d",value[0x1f:0x27]),2,0x1f,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "var3?", 1, "%.2f"%struct.unpack("<d",value[0x27:0x2f]),2,0x27,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "var4?", 1, "%.2f"%struct.unpack("<d",value[0x2f:0x37]),2,0x2f,3,8,4,"<d")

def SplineStart (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Knot", 1, "%.2f"%struct.unpack("<d",value[0x25:0x2d]),2,0x25,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Knot2", 1, "%.2f"%struct.unpack("<d",value[0x2d:0x35]),2,0x2d,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Knot3", 1, "%.2f"%struct.unpack("<d",value[0x35:0x3d]),2,0x35,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Degree", 1, "%d"%struct.unpack("<h",value[0x3d:0x3f]),2,0x3d,3,2,4,"<h")
	if len(value)>0x41:
		vsdblock.parse(hd, size, value, 0x41)

def SplineKnot (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "X", 1, "%.2f"%struct.unpack("<d",value[20:28]),2,20,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Y", 1, "%.2f"%struct.unpack("<d",value[29:37]),2,29,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Knot", 1, "%.2f"%struct.unpack("<d",value[0x25:0x2d]),2,0x25,3,8,4,"<d")
	if len(value)>0x2f:
		vsdblock.parse(hd, size, value, 0x2f)


def FrgnType (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ImgOffsetX", 1, "%.2f"%struct.unpack("<d",value[0x14:0x1c]),2,0x14,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ImgOffsetY", 1, "%.2f"%struct.unpack("<d",value[0x1d:0x25]),2,0x1d,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ImgWidth", 1, "%.2f"%struct.unpack("<d",value[0x26:0x2e]),2,0x26,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ImgHeight", 1, "%.2f"%struct.unpack("<d",value[0x2f:0x37]),2,0x2f,3,8,4,"<d")
	[ftype] = struct.unpack("<h",value[0x37:0x39])
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Type ??", 1, "%d"%ftype,2,0x37,3,2,4,"<h")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "MapMode", 1, "%d"%struct.unpack("<h",value[0x39:0x3b]),2,0x39,3,2,4,"<h")
	if ftype == 4:
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ExtentX", 1, "%d"%struct.unpack("<h",value[0x3b:0x3d]),2,0x3b,3,2,4,"<h")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "ExtentY", 1, "%d"%struct.unpack("<h",value[0x3d:0x3f]),2,0x3d,3,2,4,"<h")
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
	0xa5:SplineStart,0xa6:SplineKnot,0xa8:LayerIX,0xaa:Control,
	0xc0:PageLayout,0xc1:Polyline,0xc3:NURBS, 0xc9:NameID,
	0xd1:ShapeData
}

def parse(model, version, parent, pntr):
	offset = 0
	tmppntr = vsd.pointer()
	tmppntr2 = vsd.pointer()
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
