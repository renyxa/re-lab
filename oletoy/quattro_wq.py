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

# import of QuattroPro wq1 and wq2 files
import binascii
import sys,struct
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from utils import *

class QWQDoc():
	def __init__(self,data,page,parent):
		self.data = data
		self.parent=parent
		self.version = -1
		if page != None:
			self.page = page
			self.version = page.version

		self.chuncks={
			"BOF": self.BOF,
			"FormulaCell": self.FormulaCell,
			"GraphSetup": self.GraphSetup,
			"GraphName": self.GraphName,
			"FontUser": self.FontUser,
			"GraphStruct1":self.GraphStruct1,
			"GraphStruct2":self.GraphStruct2,
			"GraphFieldPos":self.GraphFieldPos,
			"GraphField":self.GraphField,
			"Typeb7":self.Typeb7,
			"SerieAnalyze": self.SerieAnalyze,
			"Typed4": self.Typed4,
			"CellStyle": self.CellStyle,
			"ListString0": self.ListString0,
		}
		self.chunkNames = {
			0: "BOF",
			1: "EOF",
			2: "CalcMode",
			3: "CalcOrder",
			4: "SplitWinTyp",
			5: "SplitWinSyn",
			6: "SheetSize",
			7: "WindowRec", #wq1
			8: "ColWidth", # wq1
			0xb: "FieldName",
			0xc: "BlankCell",
			0xd: "IntCell",
			0xe: "FloatCell",
			0xf: "StringCell",
			0x10: "FormulaCell",
			0x18: "DataTableRg",
			0x19: "QueryRg",
			0x1a: "PrintRg",
			0x1b: "SortRg",
			0x1c: "FillRg",
			0x1d: "PrimSortRg",
			0x20: "DistRg",
			0x23: "SecSortRg",
			0x24: "Protection",
			0x25: "Header",
			0x26: "Footer",
			0x27: "PrintSetup",
			0x28: "PrintMargin",
			0x29: "LabelFormat",
			0x2a: "PrintBorders",
			0x2d: "GraphSetup",
			0x2e: "GraphName",
			0x2f: "ItCount",
			0x30: "PrintFormat",
			0x33: "FormulaCellRes",
			#
			0x64: "HiddenCol",
			0x66: "RgUnknA0",
			0x67: "RgUnknA1",
			0x69: "RgUnknA2",

			0x96: "ColListCell",
			0x97: "DbName",
			0x98: "DbVar",
			# 99, 9a
			0x9b: "FontUser",
			0x9c: "ColListCellSelect", # a subset of the list of cell
			0x9d: "CellProp",
			# 9e
			0x9f: "RgUnknB0",
			0xa0: "RgUnknB1",
			0xa1: "RgUnknB2",
			0xa2: "GraphStruct1",
			0xa3: "GraphStruct2",
			0xa4: "GraphFieldPos",
			0xa5: "GraphField",
			0xb5: "RgUnknC0",
			0xb6: "RgUnknC1",
			0xb7: "Typeb7",
			0xb8: "Chart3D",
			# b9, bb-bf
			0xc1: "ShadowColor",
			# c0-c1,c4-c5,cb-ce
			0xc9: "StyleUser",
			0xca: "ChartBubble",
			0xcb: "SerieAnalyze",
			# d0, d4, d6-d7
			0xd1: "ListString0",
			0xd4: "Typed4",
			0xd8: "CellStyle",

			# wq2
			0xdc: "SpreadOpen",
			0xdd: "SpreadClose",
			0xde: "SpreadName",
			# df
			0xe0: "RowSize",
			0xe2: "ColSize",
			0xe3: "SpreadSize",
			# e3-e8 ea-eb
		}
		self.chunkHds = {
			"BOF":self.hdBOF,
			"CalcMode":self.hdByte, # 1|ff
			"CalcOrder":self.hdByte, # 0
			"SplitWinTyp":self.hdByte, # 0|ff
			"SplitWinSyn":self.hdByte, # 0|ff
			"SheetSize":self.hdSheetSize,
			"WindowRec":self.hdWindowRec,
			"ColWidth":self.hdColWidth,
			"FieldName":self.hdFieldName,
			"BlankCell":self.hdBlankCell,
			"IntCell":self.hdIntCell,
			"FloatCell":self.hdFloatCell,
			"StringCell":self.hdStringCell,
			"FormulaCell":self.hdFloatCell,
			"FormulaHeader":self.hdFormulaHeader,
			"Formula":self.hdFormula,
			"FormulaCells":self.hdFormulaCells,
			"DataTableRg":self.hdRange6,
			"QueryRg":self.hdRange6,
			"PrintRg":self.hdRange2,
			"SortRg":self.hdRange2,
			"FillRg":self.hdRange2,
			"PrimSortRg":self.hdRange2,
			"DistRg":self.hdRange4,
			"SecSortRg":self.hdRange2,
			"Protection":self.hdByte, # 0
			"Header":self.hdString,
			"Footer":self.hdString,
			"PrintSetup":self.hdByte, # unsure
			"PrintMargin":self.hdPrintMargin,
			"LabelFormat":self.hdByte, # 27
			"PrintBorders":self.hdRange4, # top: 0,1 and lelf heading: 2,3
			"GraphSetup":self.hdGraphSetup,
			"GraphName":self.hdGraphName,
			"GraphDef0":self.hdGraphDef0,
			"GraphDef1":self.hdGraphDef1,
			"GraphDef2":self.hdGraphDef2,
			"GraphDef3":self.hdGraphDef3,
			"GraphDef4":self.hdGraphDef4,
			"GraphString":self.hdCString,
			"ItCount":self.hdByte, # 1
			"PrintFormat":self.hdByte, # 0|1|ff
			"FormulaCellRes":self.hdFormulaCellRes,

			"HiddenCol":self.hdHiddenCol,
			"RgUnknA0":self.hdRange4,
			"RgUnknA1":self.hdRange6,
			"RgUnknA2":self.hdRange10,

			"ColListCell":self.hdColListCell,
			"DbName":self.hdDbName,
			"DbVar":self.hdDbVar,
			"Type99":self.hdByte,
			"Type9a":self.hd2Int, # 0|28,0|2|4
			"FontUserDef":self.hdFontUserDef,
			"ColListCellSelect":self.hdColListCell,
			"CellProp":self.hdCellProp,
			# 9e unsure size 16 or 17, often 0*,9c,75,00,88,3c,...
			"RgUnknB0":self.hdRange2,
			"RgUnknB1":self.hdRange2,
			"RgUnknB2":self.hdRange2,
			"GraphStruct1":self.hdTypeaHeader,
			"GraphStruct1Data":self.hdGraphStruct1Data,
			"GraphStruct2":self.hdTypeaHeader,
			"GraphStruct2Data":self.hdGraphStruct2Data,
			"GraphFieldPos":self.hdTypeaHeader,
			"GraphFieldPosData":self.hdGraphFieldPosData,
			"GraphField":self.hdTypeaHeader,
			"GraphFieldData":self.hdGraphFieldData,
			"RgUnknC0":self.hdRange20,
			"RgUnknC1":self.hdRange2,
			# b7Data unsure, often 00000000000000007b14ae47e17a403f0500
			"Chart3D":self.hdByte, # 10:bar, 11:ribbon, 12: step, 13: area
			"Typeb9":self.hdCString, # many followed by a byte 0
			"Typebb":self.hdInt, # 64
			"Typebc":self.hdByte,
			"Typebd":self.hdInt, # 4
			"Typebe":self.hdByte,
			"Typebf":self.hdByte,
			"Typec0":self.hdByte,
			"ShadowColor":self.hd16Int,
			"Typec4":self.hdByte,
			"Typec5":self.hdInt, # 0
			"StyleUser":self.hdStyleUser,
			"ChartBubble":self.hdByte, #e
			"SerieAnalyze":self.hdCString,
			"SerieAnalyzeData":self.hdSerieAnalyzeData,
			"Typecc":self.hdUInt, # [08][0348][01][04]
			"Typecd":self.hdInt, # 2a
			"Typece":self.hdInt, # c : related to CellStyle?
			#TODO  d0
			"ListString0":self.hdListString0,
			"ListString0Def":self.hdListString0Def,
			"Typed4":self.hdTyped4,
			"Typed4End":self.hdTyped4End,
			"Coord":self.hdCoord,
			"Typed6":self.hdTyped6, # some chart/picture name + 1 int?
			"Typed7":self.hdTyped7, # some chart/picture name + 2 int?
			"CellStyle":self.hdCellStyle, # v2
			"CellStyleDef":self.hdCellStyleDef, # v1

			# wq2
			"SpreadOpen":self.hdInt,
			"SpreadName":self.hdCString,
			"Typedf":self.hdInt, # 20|7f
			"RowSize":self.hdRowSize,
			"ColSize":self.hdColSize,
			"SpreadSize":self.hdSpreadSize,
			"Typee4":self.hd16Int,
			"Typee5":self.hd16Int,
			"Typee6":self.hdTypee6,
			"Typee7":self.hdTypee6,
			"Typee8":self.hdByte,
			"Typeea":self.hd9Int, # the f5,f8 is probably a uint
			"Typeeb":self.hd9Int, # same structure as Typeeb
		}
		self.unseenA5Data=0

	def BOF(self,length,off):
		version=struct.unpack('<H', self.data[off:off+2])[0]
		if version==0x5120:
			self.version=self.page.version=1
		elif version==0x5121:
			self.version=self.page.version=2
	def FormulaCell(self,length,offset):
		subZone=[]
		off=0
		if self.version==1:
			off+=1
		off += 4
		if self.version>1:
			off+=2
		off += 8
		if length<=off:
			return subZone
		limitPos=[0,0,0,0]
		hSz=0
		for i in range(3):
			limitPos[3 if i==0 else i]=struct.unpack('<H', self.data[offset+off+hSz:offset+off+2+hSz])[0]+2
			hSz+=2
			if i==1 and self.version>1:
				limitPos[2]=limitPos[3]
				break
		limitPos[0]=hSz
		subZone.append(("FormulaHeader","FormulaHeader",offset+off,hSz))
		for i in range(3):
			if limitPos[i]!=limitPos[i+1]:
				what=["formula","cells","cells[double]"]
				subZone.append((what[i],"Formula" if i==0 else "FormulaCells",offset+off+limitPos[i],limitPos[i+1]-limitPos[i]))
		return subZone
	def GraphSetup(self,length,offset):
		return self.GraphName(length,offset,False)
	def GraphName(self,length,offset,hasName=True):
		subZone=[]
		off=16 if hasName else 0 # name
		if self.version==1: # 26 position
			off+=4*26
		else:
			off+=6*26
		subZone.append(("data","GraphDef0",offset+off,49)) # list of some bytes
		off+=49
		for i in range(10): # line1, line2, xtitle, ytitle, serie1-serie6
			len=40 if i<4 else 20
			subZone.append(("string%d"%i,"GraphString",offset+off,len))
			off+=len
		subZone.append(("data1","GraphDef1",offset+off,46)) # list of some int
		off+=46
		for i in range(6):
			subZone.append(("font%d"%i,"FontUserDef",offset+off,8))
			off+=8
		subZone.append(("data2","GraphDef2",offset+off,33))
		off+=33
		subZone.append(("string10","GraphString",offset+off,40))
		off+=40
		# byte 0: position 0: right, 1: bottom
		subZone.append(("data3","GraphDef3",offset+off,49))
		off+=49
		if length>off:
			subZone.append(("data4","GraphDef4",offset+off,length-off))
		return subZone
	def FontUser(self,length,offset):
		subZone=[]
		N=length//8
		off=0
		for i in range(N):
			subZone.append(("font%d"%i,"FontUserDef",offset+off,8))
			off+=8
		if length>off:
			subZone.append(("unknown","FontUserData",offset+off,length-off))
		return subZone
	def GraphStruct1(self,length,offset):
		subZone=[]
		off=18
		subZone.append(("data","GraphStruct1Data",offset+off,length-off)) # size 35
		return subZone
	def GraphStruct2(self,length,offset):
		subZone=[]
		off=18
		N=(length-off)//60
		for i in range(N):
			subZone.append(("data%d"%i,"GraphStruct2Data",offset+off,60))
			off+=60
		if off!=length:
			subZone.append(("data","GraphStruct2End",offset+off,length-off))
		return subZone
	def GraphFieldPos(self,length,offset):
		subZone=[]
		off=18
		subZone.append(("data","GraphFieldPosData",offset+off,length-off))
		return subZone
	def GraphField(self,length,offset):
		subZone=[]
		off=18
		if self.unseenA5Data:
			# if the a5 zone is too big, it can be splitted in many a5 zone, so...
			subZone.append(("data","GraphFieldDataUn",offset+off,self.unseenA5Data))
			off+=self.unseenA5Data
			self.unseenA5Data=0
		while off+3<length:
			sSz = struct.unpack('<H', self.data[offset+off+2:offset+off+4])[0]
			if off+4+sSz>length:
				self.unseenA5Data=off+4+sSz-length
				subZone.append(("data","GraphFieldDataUn",offset+off,length-off))
				return subZone
			subZone.append(("data","GraphFieldData",offset+off,4+sSz))
			off+=4+sSz
		return subZone
	def Typeb7(self,length,offset):
		off=0
		coordLen=4 if self.version==1 else 6
		subZone=[]
		for i in range(4):
			subZone.append(("coord%d"%(i+1),"Coord",offset+off,coordLen))
			off+=coordLen
		subZone.append(("data","Typeb7Data",offset+off,length-off)) # unsure about this one
		return subZone
	def SerieAnalyze(self,length,offset):
		subZone=[]
		off=0
		off+=16
		for i in range(7):
			subZone.append(("data%d"%i,"SerieAnalyzeData",offset+off,8))
			off+=8
		return subZone
	def Typed4(self,length,offset):
		off=0
		off+=6
		coordLen=4 if self.version==1 else 6
		subZone=[]
		subZone.append(("coord0","Coord",offset+off,coordLen))
		off+=coordLen+26
		for i in range(8):
			subZone.append(("coord%d"%(i+1),"Coord",offset+off,coordLen))
			off+=coordLen
		subZone.append(("data","Typed4End",offset+off,length-off))
		return subZone
	def CellStyle(self,length,offset):
		if self.version>1:
			return []
		subZone=[]
		N=length//12
		off=0
		for i in range(N):
			subZone.append(("cell%d"%i,"CellStyleDef",offset+off,12))
			off+=12
		if length>off:
			subZone.append(("unknown","CellStyleData",offset+off,length-off))
		return subZone
	def ListString0(self,length,offset):
		off=0
		subZone=[]
		N = struct.unpack('<H', self.data[offset+off:offset+off+2])[0]
		off+=2
		for i in range(N):
			subZone.append(("string%d"%i,"ListString0Def",offset+off,14))
			off+=14
		if length>off:
			subZone.append(("unknown","ListString0Data",offset+off,length-off))
		return subZone
	## main parsing
	def parse(self):
		off = 0
		while off < len(self.data) - 2:
			theType = struct.unpack('<H', self.data[off:off+2])[0]
			off += 2
			length = struct.unpack('<H', self.data[off:off+2])[0]
			off += 2
			what="Type%02x"%theType
			subZone=[]
			if theType in self.chunkNames:
				what=self.chunkNames[theType]
			if what in self.chuncks:
				res=self.chuncks[what](length,off)
				if type(res) is list:
					subZone=res
			niter=add_pgiter (self.page,what,"QuattroWq",what,self.data[off:off+length],self.parent)
			for i in range(len(subZone)):
				subName,subType,subOff,subLen=subZone[i]
				subData=self.data[subOff:subOff+subLen]
				add_pgiter(self.page,subName,"QuattroWq",subType,subData,niter)
			off += length

	## local parsing
	align_map = { # in text zone
		ord('\''): "default",
		ord('\\'): "left",
		ord('^'): "center",
		ord('\"'): "right",
	}
	align2_map={
		0:"",
		1:"left,",
		2:"right,",
		3:"center,"
	}
	border_map={
		0:"",
		1:"w=1",
		2:"double",
		3:"w=2"
	}
	borderOrderMap={
		0:"T",
		1:"L",
		2:"B",
		3:"R"
	}
	background_map={
		0:"",
		1:"back[grey],",
		2:"back[black],",
		3:"##back[color]=3,",
	}
	input_map={
		0:"",
		1:"labels[only]",
		2:"dates[only]",
		3:"##input=3",
	}
	format_map={
		0:"fixed",
		1:"scientific",
		2:"currency",
		3:"percent",
		4:"decimal",
		5:"date",
		6:"unknown",
		7:"special"
	}
	formatSub_map={
		0:"bool",
		1:"number",
		2:"date=%d %B %y",
		3:"date=%d %B",
		4:"date=%B %y",
		5:"txt",
		6:"txt[hidden]",
		7:"time=%I:%M:%S%p",
		8:"time=%I:%M%p",
		9:"date=%m/%d/%y",
		10:"date=%m/%d",
		11:"time=%H:%M:%S",
		12:"time=%H:%M",
		13:"text",
		14:"##form=7c",
		15:"automatic"
	}
	def update_view2(self,hd,model,iter):
		key=model.get_value(iter,1)[1]
		if key in self.chunkHds:
			self.chunkHds[key](hd,model.get_value(iter,3))
	def checkFinish(self,hd,data,off,name):
		if len(data)>off:
			extra=len(data)-off
			add_iter (hd,"##extra",binascii.hexlify(data[off:off+extra]), off, extra, "txt")
			print("%s: Find unexpected data"%name)
	def readCoord(self,data,beg,num):
		what=""
		off=0
		for i in range(num):
			if i!=0:
				what += "x"
			what+="%d"%struct.unpack('<h', data[beg+off:beg+off+2])[0]
			off+=2
		return what,off

	def hdBOF(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		what="%04x"%val
		if val==0x5120:
			what=1
		elif val==0x5121:
			what=2
		add_iter (hd,"version",what,off,2,'<H')

	def hdByte(self,hd,data):
		off=0
		val=struct.unpack('<b', data[off:off+1])[0]
		what=val
		add_iter (hd,"val",what,off,1,'<b')
		off += 1
		self.checkFinish(hd,data,off,"hdByte")

	def hdInt(self,hd,data,num=1):
		off=0
		for i in range(num):
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off += 2
		self.checkFinish(hd,data,off,"hdInt")
	def hd2Int(self,hd,data):
		self.hdInt(hd,data,2)
	def hd9Int(self,hd,data):
		self.hdInt(hd,data,9)
	def hd16Int(self,hd,data):
		self.hdInt(hd,data,16)
	def hdUInt(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"val","%02x"%val,off,2,'<H')
		off+=2
		self.checkFinish(hd,data,off,"hdUInt")
	def hdCoord(self,hd,data):
		off=0
		what,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		add_iter (hd,"val",what,off,l,'txt')
		off+=l
		self.checkFinish(hd,data,off,"hdCoord")

	def hdSheetSize(self,hd,data):
		off=0
		what,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		add_iter (hd,"min",what,off,l,'txt')
		off+=l
		what,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		add_iter (hd,"max",what,off,l,'txt')
		off+=l

	def hdWindowRec(self,hd,data):
		off=0
		what,l=self.readCoord(data, off, 2)
		add_iter (hd,"select",what,off,l,'txt')
		off += l
		for i in range(17):
			col=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,col,off,2,'<H')
			off+=2
		self.checkFinish(hd,data,off,"hdWindowRec")

	def hdColWidth(self,hd,data):
		off=0
		col=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"col",col,off,2,'<H')
		off+=2
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"val",val,off,1,'<B')
		off+=1
	def hdColSize(self,hd,data):
		off=0
		col=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"col",col,off,1,'<B')
		off+=1
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"val",val/20.,off,2,'<H')
		off+=2
	def hdRowSize(self,hd,data):
		off=0
		row=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"row",row,off,1,'<B')
		off+=1
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"val",val/20.,off,2,'<H')
		off+=2
	def hdSpreadSize(self,hd,data): # maybe spread default font size
		off=0
		spread=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"spread",spread,off,2,'<H')
		off+=2
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"val",val,off,1,'<B')
		off+=1

	def hdFieldName(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		add_iter(hd,"val",data[off:off+sSz],off,sSz,'txt')
		off+=15
		what,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		add_iter (hd,"min",what,off,l,'txt')
		off+=l
		what,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		add_iter (hd,"max",what,off,l,'txt')
		off+=l
		if self.version>1:
			val=struct.unpack('<h', data[off:off+2])[0] # 0 or 100
			add_iter (hd,"f0",val,off,2,'<h')
			off+=2
		self.checkFinish(hd,data,off,"hdFieldName")

	def getFileFormat(self,val):
		if val==0xFF:
			return "_"
		typ=(val>>4)&7
		digits=val&0xF
		if typ<5:
			if digits:
				return "%s,digits=%d"%(self.format_map[typ],digits)
			else:
				return self.format_map[typ]
		if typ==5:
			if digits==4:
				return "date=%m/%d/%y"
			if digits==5:
				return "date=%m/%d"
		if typ==7:
			return self.formatSub_map[digits]
		return "##form=%02x"%val

	def readCellHeader(self,hd,data,off):
		if self.version==1:
			fmt=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"fmt",self.getFileFormat(fmt),off,1,'<B')
			off+=1
		col=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"col",col,off,1,'<B')
		off+=1
		sheet=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sheet",sheet,off,1,'<B')
		off+=1
		row=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"row",row,off,2,'<H')
		off+=2
		if self.version>1:
			fmt=struct.unpack('>H', data[off:off+2])[0]
			add_iter (hd,"fmt","_" if fmt==0xFFF else fmt,off,2,'>H')
			off+=2
		return off

	def hdBlankCell(self,hd,data):
		off=self.readCellHeader(hd,data,0)

	def hdIntCell(self,hd,data):
		off=self.readCellHeader(hd,data,0)
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"val",val,off,2,'<H')
		off+=2

	def hdFloatCell(self,hd,data):
		off=self.readCellHeader(hd,data,0)
		val=struct.unpack('<d', data[off:off+8])[0]
		add_iter (hd,"val",val,off,8,'<d')
		off+=8

	def hdStringCell(self,hd,data,hasAlign=True):
		off=self.readCellHeader(hd,data,0)
		if hasAlign:
			align=struct.unpack('<B', data[off:off+1])[0]
			what="%02x"%align
			if align in self.align_map:
				what=self.align_map[align]
			add_iter (hd,"align",what,off,1,'<B')
			off+=1
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		add_iter(hd,"val",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
		off+=sSz
	def hdFormulaCellRes(self,hd,data):
		self.hdStringCell(hd,data,False)
	def hdFormulaHeader(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"size",val,off,2,'<H')
		off+=2
		limitPos=[0,val]
		for i in range(2):
			limitPos[i]=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"endPos%d"%i,limitPos[i],off,2,'<H')
			off+=2
			if self.version>1:
				break;
	functions_map={
		3:"=[end]", # end of formula
		4:"()",
		8:"-[unary]",
		9:"+",

		10:"-",
		11:"*",
		12:"/",
		13:"^",
		14:"==",
		15:"<>",
		16:"<=",
		17:">=",
		18:"<",
		19:">",

		20:"And",
		21:"Or",
		22:"Not",
		23:"+[unary]",
		24:"&",
		31:"NA", # 0-ary, checkme
		32:"NA", # 0-ary
		33:"Abs",
		34:"Int",
		35:"Sqrt",
		36:"Log10",
		37:"Ln",
		38:"Pi",
		39:"Sin",

		40:"Cos",
		41:"Tan",
		42:"Atan2",
		43:"Atan",
		44:"Asin",
		45:"Acos",
		46:"Exp",
		47:"Mod",
		49:"IsNa",
		50:"IsError",
		51:"False",
		52:"True",
		53:"Rand",
		54:"Date",
		55:"Now",
		56:"PMT",
		57:"PV",
		58:"FV",
		59:"If",

		60:"Day",
		61:"Month",
		62:"Year",
		63:"Round",
		64:"Time",
		65:"Hour",
		66:"Minute",
		67:"Second",
		68:"IsNumber",
		69:"IsText",
		70:"Len",
		71:"Value",
		72:"Text",
		73:"Mid",
		74:"Char",
		75:"Ascii",
		76:"Find",
		77:"DateValue",
		78:"TimeValue",
		79:"CellPointer",

		85:"VLookUp",
		86:"NPV",
		89:"IRR",
		90:"HLookUp",
		91:"DSum",
		92:"DAvg",
		93:"DCnt",
		94:"DMin",
		95:"DMax",
		96:"DVar",
		97:"DStd",
		98:"Index",
		99:"Columns",

		100:"Rows",
		101:"Rept",
		102:"Upper",
		103:"Lower",
		104:"Left",
		105:"Right",
		106:"Replace",
		107:"Proper",
		108:"Cell",
		109:"Trim",
		111:"T",
		112:"IsNonText",
		113:"Exact",
		116:"Rate",
		117:"Term",
		118:"CTerm",
		119:"SLN",

		120:"SYD",
		121:"DDB",

		143:"Not",
	}
	functions_N_map={
		48:"Choose",

		80:"Sum",
		81:"Average",
		82:"Count",
		83:"Min",
		84:"Max",
		87:"Var",
		88:"StDev",

		141:"And",
		142:"Or",
	}
	def hdFormula(self,hd,data):
		off=0
		numCell=0
		numDCell=0
		while off<len(data):
			wh=struct.unpack('<B', data[off:off+1])[0]
			off+=1
			if wh==0:
				val=struct.unpack('<d', data[off:off+8])[0]
				add_iter (hd,"double",val,off-1,1+8,'txt')
				off+=8
			elif wh==1:
				add_iter (hd,"cell",numCell,off-1,1,'txt')
				numCell+=1
			elif wh==2:
				if self.version==1:
					add_iter (hd,"cell[list]",numDCell,off-1,1,'txt')
					numDCell+=2
				else:
					add_iter (hd,"cell[list]",numCell,off-1,1,'txt')
					numCell+=1
			elif wh==5:
				val=struct.unpack('<h', data[off:off+2])[0]
				add_iter (hd,"int",val,off-1,1+2,'txt')
				off+=2
			elif wh==6:
				sSz=struct.unpack('<B', data[off:off+1])[0]
				add_iter(hd,"txt",str(data[off+1:off+1+sSz],"cp437"),off-1,2+sSz,'txt')
				off+=1+sSz
			elif wh in self.functions_map:
				add_iter (hd,"func",self.functions_map[wh],off-1,1,'txt')
			elif wh in self.functions_N_map:
				arity=struct.unpack('<B', data[off:off+1])[0]
				add_iter (hd,"func","%s[%d]"%(self.functions_N_map[wh],arity),off-1,2,'txt')
				off+=1
			else:
				print("hdFormula: Find unexpected type=%d"%wh)
				off-=1
				break
			if wh==3: # sometimes, there can be some text after the end=, some comment?
				if off<len(data):
					extra=len(data)-off
					add_iter (hd,"comment",str(data[off:off+extra],"cp437"), off, extra, "txt")
					off=len(data)
				break

		self.checkFinish(hd,data,off,"hdFormula")

	def hdFormulaCells(self,hd,data):
		off=0
		if self.version==1:
			N=len(data)//4
			for i in range(N):
				what=""
				for c in range(2):
					val=struct.unpack('<H', data[off:off+2])[0]
					off+=2
					if (val&0x8000)==0: # absolute
						what += "%d"%val
					elif (val&0x80): # relative
						what += "R%d"%((val&0xFF)-0x100)
					else:
						what += "R%d"%(val&0xFF)
					if c==0:
						what += "x"
				add_iter (hd,"cell%d"%i,what,off-4,4,'txt')
		else:
			n=0
			while off<len(data):
				typ=struct.unpack('<H', data[off:off+2])[0]
				add_iter (hd,"type%d"%n,"%02x"%typ,off,2,'txt')
				off+=2
				numVal=2 if typ==0x1000 else 1
				what=""
				for cell in range(numVal):
					for c in range(3):
						val=struct.unpack('<H', data[off:off+2])[0]
						off+=2
						if (val&0x8000)==0: # absolute
							what += "%d"%val
						else:
							val = val&0x3fff
							if val>0x1000:
								val -= 0x2000
							what += "R%d"%val
						if c!=2:
							what += "x"
					if cell==0 and numVal==2:
						what += "<->"
				add_iter (hd,"cell%d"%n,what,off-6,6,'txt')
				n+=1
				if typ&0xEFFF:
					break
		self.checkFinish(hd,data,off,"hdFormulaCells")
	def hdRange(self,hd,data,num):
		off=0
		for i in range(num):
			what,l=self.readCoord(data, off, 2 if self.version==1 else 3)
			add_iter (hd,"r%d"%i,what,off,l,'txt')
			off+=l
		if len(data)>off:
			val=struct.unpack('<b', data[off:off+1])[0]
			add_iter (hd,"val",val,off,1,'<b')
			off+=1
		self.checkFinish(hd,data,off,"hdRange")
	def hdRange2(self,hd,data):
		self.hdRange(hd,data,2)
	def hdRange4(self,hd,data):
		self.hdRange(hd,data,4)
	def hdRange6(self,hd,data):
		self.hdRange(hd,data,6)
	def hdRange10(self,hd,data):
		self.hdRange(hd,data,10)
	def hdRange20(self,hd,data):
		self.hdRange(hd,data,20)

	def hdString(self,hd,data):
		add_iter(hd,"val",str(data.rstrip('\0'),"cp437"),0,len(data),'txt')
	def hdCString(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz==255:
			add_iter(hd,"val","_",off,len(data)-1,'txt')
		else:
			add_iter(hd,"val",str(data[off:off+sSz],"cp437"),off,sSz,'txt')

	def hdStyleUser(self,hd,data):
		off=0
		if self.version>1:
			sSz=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"sSz",sSz,off,1,'<B')
			off+=1
			if sSz>15:
				sSz=15
			add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
			off=16
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"id",val,off,2,'<H')
		off+=2
		if self.version>1:
			for i in range(4): # small int
				val=struct.unpack('<b', data[off:off+1])[0]
				add_iter (hd,"f%d"%i,val,off,1,'<b')
				off+=1
		val=struct.unpack('<H', data[off:off+2])[0]
		what=""
		if val&1:
			what+="b:"
		if val&2:
			what+="it:"
		if val&8:
			what+="underline:"
		add_iter (hd,"flags","%02x[%s]"%(val,what),off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"fId",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"size",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"color",val,off,2,'<H')
		off+=2
		if self.version==1:
			val=struct.unpack('<H', data[off:off+2])[0] #-1
			add_iter (hd,"fl","_" if val==0xFFFF else "%02x"%val,off,2,'<H')
			off+=2
			sSz=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"sSz",sSz,off,1,'<B')
			off+=1
			if sSz>15:
				sSz=15
			add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
			off+=16
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"f1",val,off,2,'<H') # 1
			off+=2
			for i in range(4):
				val=struct.unpack('<B', data[off:off+1])[0]
				what="%02x[%s]"%(val,self.border_map[val&3])
				add_iter (hd,"bord%s"%self.borderOrderMap[i],what,off,1,'<B')
				off+=1
			val=struct.unpack('<B', data[off:off+1])[0]
			what="%02x[%s]"%(val,self.background_map[val&3])
			add_iter (hd,"background",what,off,1,'<B')
			off+=1
			val=struct.unpack('<B', data[off:off+1])[0]
			what="%02x[%s]"%(val,self.align2_map[val&3])
			add_iter (hd,"align",what,off,1,'<B')
			off+=1
			val=struct.unpack('<B', data[off:off+1])[0]
			what="%02x[%s]"%(val,self.input_map[val&3])
			add_iter (hd,"input",what,off,1,'<B')
			off+=1
			fmt=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"fmt",self.getFileFormat(fmt),off,1,'<B')
			off+=1
			for i in range(3):
				val=struct.unpack('<B', data[off:off+1])[0]
				add_iter (hd,"f%d"%(i+2),val,off,1,'<B')
				off+=1
		else:
			val=struct.unpack('<B', data[off:off+1])[0]
			what=""
			for i in range(4):
				bType=(val>>(2*i))&3
				if bType:
					what+="%s=[%s],"%(self.borderOrderMap[i],self.border_map[bType])
			add_iter (hd,"borders",what,off,1,'<B')
			off+=1
			val=struct.unpack('<B', data[off:off+1])[0] # 8|10|18
			add_iter (hd,"f4",val,off,1,'<B')
			off+=1
			val=struct.unpack('<B', data[off:off+1])[0]
			what="%02x[%s]"%(val,self.background_map[val&3])
			add_iter (hd,"background",what,off,1,'<B')
			off+=1
			fmt=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"fmt",self.getFileFormat(fmt),off,1,'<B')
			off+=1
			for i in range(2):
				val=struct.unpack('<B', data[off:off+1])[0]
				add_iter (hd,"f%d"%(i+5),val,off,1,'<B')
				off+=1

	def hdListString0(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",val,off,2,'<H')
		off+=2
	def hdListString0Def(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz>9:
			sSz=9
		add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
		off=10
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"id",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] #0
		add_iter (hd,"f0",val,off,2,'<H')
		off+=2

	def hdCellStyle(self,hd,data):
		if self.version==1:
			return
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"id[parent]","_" if val==0xFF0F else val,off,2,'<H') # 1/2
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"id",val,off,2,'<H') # 1/2
		off+=2
		for i in range(4):
			val=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"f%d"%i,val,off,1,'<B')
			off+=1
		fl=struct.unpack('<H', data[off:off+2])[0]
		what=""
		if fl&1:
			what+="b:"
		if fl&2:
			what+="it:"
		if fl&8:
			what+="underline:"
		add_iter (hd,"fl","%s[%02x]"%(what,fl),off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"fId",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"size",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"color",val,off,2,'<H')
		off+=2
		val=struct.unpack('<B', data[off:off+1])[0]
		what=""
		for i in range(4):
			bType=(val>>(2*i))&3
			if bType:
				what+="%s=[%s],"%(self.borderOrderMap[i],self.border_map[bType])
		add_iter (hd,"borders",what,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0] # 8|10|18
		add_iter (hd,"f4",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		what="%02x[%s]"%(val,self.background_map[val&3])
		add_iter (hd,"background",what,off,1,'<B')
		off+=1
		fmt=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"fmt",self.getFileFormat(fmt),off,1,'<B')
		off+=1
		for i in range(2):
			val=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"f%d"%(i+5),val,off,1,'<B')
			off+=1

	def hdCellStyleDef(self,hd,data):
		if self.version>1:
			return
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"id",val,off,2,'<H') # 1/2
		off+=2
		fl=struct.unpack('<H', data[off:off+2])[0]
		what=""
		if fl&1:
			what+="b:"
		if fl&2:
			what+="it:"
		if fl&8:
			what+="underline:"
		add_iter (hd,"fl","%s[%02x]"%(what,fl),off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"fId",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"size",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"color",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"fl1","%02x"%val,off,2,'<H')
		off+=2

	def hdPrintMargin(self,hd,data):
		off=0
		for i in range(5):
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val/256.,off,2,'<h')
			off+=2

	def hdGraphSetup(self,hd,data,off=0):
		pos,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		pos1,l1=self.readCoord(data, off+l, 2 if self.version==1 else 3)
		add_iter (hd,"XSerie","%s->%s"%(pos,pos1),off,l+l1,'txt')
		off+=l+l1
		actOff=off
		wh=""
		for i in range(6):
			pos,l=self.readCoord(data, off, 2 if self.version==1 else 3)
			pos1,l1=self.readCoord(data, off+l, 2 if self.version==1 else 3)
			wh+="%s->%s,"%(pos,pos1)
			off+=l+l1
		add_iter (hd,"data[series]",wh,actOff,off-actOff,'txt')
		actOff=off
		wh=""
		for i in range(6):
			pos,l=self.readCoord(data, off, 2 if self.version==1 else 3)
			pos1,l1=self.readCoord(data, off+l, 2 if self.version==1 else 3)
			wh+="%s->%s,"%(pos,pos1)
			off+=l+l1
		add_iter (hd,"label[series]",wh,actOff,off-actOff,'txt')
	def hdGraphName(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz>15:
			sSz=15
		add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
		off=16
		hdGraphSetup(self,hd,data,off)
	def hdGraphDef0(self,hd,data):
		off=0
		val=struct.unpack('<B', data[off:off+1])[0]
		# 2D: 0:xy, 1:bar, 2:pie, 3:area, 4:line, 5:stack bar, 6:column, 7:High-Low, 8:rotated bar, 9:txt
		# bubble: 0:normal
		# 3D: 1:normal
		add_iter (hd,"type",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"grid",val,off,1,'<B') # 0: none, 1:horizontal, 2: vertical, 3:both
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"use[color]",val,off,1,'<B') # 0: no, ff:yes
		off+=1
		add_iter (hd,"unknown",binascii.hexlify(data[off:off+6]), off, 6, "txt")
		off+=6
		wh=""
		for i in range(6):
			val=struct.unpack('<B', data[off:off+1])[0] # 0:center,1:left,2:above,3:right,4:below,5:none
			wh+="%d,"%val
			off+=1
		add_iter (hd,"align[series]",wh,off-6,6,'txt')
		for i in range(2):
			wh="X" if i==0 else "Y"
			val=struct.unpack('<b', data[off:off+1])[0] # 0 or ff
			add_iter (hd,"scale%s"%wh,"automatic" if val==0 else "manual",off,1,'<b')
			off+=1
			for j in range(2):
				val=struct.unpack('<d', data[off:off+8])[0]
				add_iter (hd,"%s%s"%("low" if j==0 else "high",wh),val,off,8,'txt')
				off+=8
		self.checkFinish(hd,data,off,"hdGraphDef0")
	def hdGraphDef1(self,hd,data):
		off=0
		for i in range(2):
			fmt=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"fmtX" if i==0 else "fmtY",self.getFileFormat(fmt),off,1,'<B')
			off+=1
		for i in range(2):
			val=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"num[tickX]" if i==0 else "num[tickY]",val,off,1,'<B')
			off+=1
		for i in range(2):
			val=struct.unpack('<B', data[off:off+1])[0] # 0=yes,255=no
			add_iter (hd,"display[scaleX]" if i==0 else "display[scaleY]",val,off,1,'<B')
			off+=1
		wh=""
		for i in range(6):
			val=struct.unpack('<H', data[off:off+2])[0]
			wh+="%d,"%val
			off+=2
		add_iter (hd,"pattern[series]",wh,off-12,12,'<H')
		for i in range(3): # 3 color ?
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"f%d"%(i+3),val,off,2,'<H')
			off+=2
		wh=""
		for i in range(6):
			val=struct.unpack('<H', data[off:off+2])[0]
			wh+="%d,"%val
			off+=2
		add_iter (hd,"color[series]",wh,off-12,12,'<H')
		for i in range(4): # 3 color +DI?
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"f%d"%(i+6),val,off,2,'<H')
			off+=2
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"color[background]",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"f10",val,off,1,'<B')
		off+=1
		self.checkFinish(hd,data,off,"hdGraphDef1")
	def hdGraphDef2(self,hd,data):
		off=0
		add_iter (hd,"unkn0",binascii.hexlify(data[off:off+2]), off, 2, "txt")
		off+=2
		wh=""
		for i in range(6):
			val=struct.unpack('<b', data[off:off+1])[0] # 0: primary, 1:secondary
			off+=1
			wh+="%d:"%val
			val=struct.unpack('<b', data[off:off+1])[0] # 0: default, 1:bar, 2:line
			wh+="%d,"%val
			off+=1
		add_iter (hd,"yAxis/override[series]",wh,off-12,12,'<H')
		val=struct.unpack('<b', data[off:off+1])[0] # 0 or ff
		add_iter (hd,"scaleY2","automatic" if val==0 else "manual",off,1,'<b')
		off+=1
		for i in range(2):
			val=struct.unpack('<d', data[off:off+8])[0]
			add_iter (hd,"%sY2"%("low" if i==0 else "high"),val,off,8,'txt')
			off+=8
		fmt=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"fmtY2",self.getFileFormat(fmt),off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"f0",val,off,1,'<B')
		off+=1
		self.checkFinish(hd,data,off,"hdGraphDef2")
	def hdGraphDef3(self,hd,data):
		off=0
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"Text[position]",val,off,1,'<B') # 0: bottom, 1: right, 2:none
		off+=1
		for i in range(3):
			wh=["title","legend","graph"]
			val=struct.unpack('<B', data[off:off+1])[0]
			 # 0: box,1:double line, 2:thick-line, 3 shadow, 4: 3d, 5:rnd rectangle, 6:none,7:sculpted
			add_iter (hd,"%s[outline]"%wh[i],val,off,1,'<B')
			off+=1
		for i in range(3):
			wh="X" if i==0 else ("Y" if i==1 else "Y2")
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"f0%s"%wh,"%02x"%val,off,2,'<H')
			off+=2
			val=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"axis%s[mode]"%wh,val,off,1,'<B') # 0: normal, 1: log
			off+=1
			val=struct.unpack('<d', data[off:off+8])[0]
			add_iter (hd,"increment%s"%wh,val,off,8,'txt')
			off+=8
		val=struct.unpack('<B', data[off:off+1])[0]
		# 0: solid, 1: dotted, 2:center-line, 3:dashed, 4:heavy solid, 5: heavy dotted, 6:heavy centered, 7: heavy dashed
		add_iter (hd,"style[gridline]",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"color[grid]",val,off,1,'<B')
		off+=1
		add_iter (hd,"unkn1",binascii.hexlify(data[off:off+10]), off, 10, "txt")
		off+=10
		self.checkFinish(hd,data,off,"hdGraphDef3")
	def hdGraphDef4(self,hd,data):
		off=0
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"tickX[alternate]",val,off,1,'<B')
		off+=1
		add_iter (hd,"unkn1",binascii.hexlify(data[off:off+2]), off, 2, "txt")
		off+=2
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"use[depth]",val,off,1,'<B') # 0: no, ff:yes
		off+=1
		add_iter (hd,"unkn2",binascii.hexlify(data[off:off+24]), off, 24, "txt")
		off+=24
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"bar[width]",val,off,2,'<H') # in percent
		off+=2
		for i in range(4): # pos0,1: graph position, pos2,3: series label
			pos,l=self.readCoord(data, off, 2)
			add_iter (hd,"pos%d"%i,pos,off,l,'txt')
			off+=l
		add_iter (hd,"unkn3",binascii.hexlify(data[off:off+9]), off, 9, "txt")
		off+=9
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"color[fill]",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"f0",val,off,1,'<B')
		off+=1
		pos,l=self.readCoord(data, off, 2 if self.version==1 else 3)
		pos1,l1=self.readCoord(data, off+l, 2 if self.version==1 else 3)
		add_iter (hd,"pos","%s->%s"%(pos,pos1),off,l+l1,'txt')
		off+=l+l1
		self.checkFinish(hd,data,off,"hdGraphDef4")

	def hdHiddenCol(self,hd,data):
		off=0
		for i in range(8): # list of flag, 1 by column
			val=struct.unpack('>I', data[off:off+4])[0]
			add_iter (hd,"fl%d"%i,"%04x"%val,off,4,'>I')
			off+=4
	def hdDbName(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"val",val,off,2,'<H') # 1/2
		off+=2
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
		off += sSz
		if self.version==1: # unsure, can be also len(data)=16
			for i in range(2):
				val=struct.unpack('<H', data[off:off+2])[0]
				add_iter (hd,"f%d"%i,val,off,2,'<H') # 0
				off+=2
	def hdDbVar(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if self.version==1 and sSz>15:
			sSz=15
		add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,sSz,'txt')
		if self.version==1:
			off=16
			for i in range(2):
				what,l=self.readCoord(data, off, 2)
				add_iter (hd,"r%d"%i,what,off,l,'txt')
				off+=l
			sSz=struct.unpack('<B', data[off:off+1])[0] # 1
			add_iter (hd,"f0",sSz,off,1,'<B')
			off+=1
		else: # never seem, so probably do not exist
			off += sSz
			self.checkFinish(hd,data,off,"hdDbVar")
	def hdFontUserDef(self,hd,data):
		off=0
		fl=struct.unpack('<H', data[off:off+2])[0]
		what=""
		if fl&1:
			what+="b:"
		if fl&2:
			what+="it:"
		if fl&8:
			what+="underline:"
		add_iter (hd,"fl","%s[%02x]"%(what,fl),off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"fId",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"size",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"color",val,off,2,'<H')
		off+=2
	def hdColListCell(self,hd,data):
		N=len(data)//6
		off=0
		for i in range(N):
			val=struct.unpack('<H', data[off:off+2])[0]
			what,l=self.readCoord(data, off+2, 2)
			add_iter (hd,"col%d"%val,what,off,l+2,'txt')
			off+=l+2
		self.checkFinish(hd,data,off,"hdCellProp")
	def hdCellProp(self,hd,data):
		off=0
		fmt=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"fmt",self.getFileFormat(fmt),off,1,'<B')
		off+=1
		what,l=self.readCoord(data, off, 2)
		add_iter (hd,"pos",what,off,l,'txt')
		off+=l
		fl=struct.unpack('<B', data[off:off+1])[0]
		what=self.align2_map[(fl>>6)&3]
		for i in range(2):
			bType=(fl>>(2*i))&3
			if bType:
				what+="bord%s=[%s],"%(self.borderOrderMap[i],self.border_map[bType])
		what+=self.background_map[(fl>>4)&3]
		add_iter (hd,"style",what,off,1,'<B')
		off+=1
		id=struct.unpack('<B', data[off:off+1])[0]
		what="_"
		if id&0x80:
			what="Ce%d"%(id&0x7f)
		elif id:
			what=""
			if id&0x7c:
				what+="Fo"%(id>>2)
			if id&3:
				what+=":%d" % (id&3)
		add_iter (hd,"style2",what,off,1,'<B')
		off+=1
	def hdGraphStruct1Data(self,hd,data):
		off=0
	def hdTypeaHeader(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz==255:
			add_iter(hd,"name","",off,15,'txt')
		else:
			if sSz>15:
				sSz=15
			add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,15,'txt')
		off=16
		val=struct.unpack('<h', data[off:off+2])[0] # 100
		add_iter (hd,"f0",val,off,2,'<h')
		off+=2
	def hdGraphStruct2Data(self,hd,data):
		off=0
	def hdGraphFieldPosData(self,hd,data):
		off=0
		N=len(data)//2
		for i in range(N):
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"depl%d"%i,"_" if val==0xFFFF else val,off,2,'<H')
			off+=2
		self.checkFinish(hd,data,off,"hdGraphFieldPosData")
	def hdGraphFieldData(self,hd,data):
		off=0
	def hdSerieAnalyzeData(self,hd,data):
		off=0
		for i in range(4): # f1=7,f2(2 bytes)=256
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off+=2
		self.checkFinish(hd,data,off,"hdSerieAnalyzeData")

	def hdTyped4(self,hd,data):
		off=0
		for i in range(3): # f0=0|1
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off+=2
		off+=4 if self.version==1 else 6
		for i in range(13): # f7=f8=100, f9-f12 big number(ie. 8dedb5a0f7c6b03e)
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%(i+3),val,off,2,'<h')
			off+=2
	def hdTyped4End(self,hd,data):
		off=0
		for i in range(5): # 0
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off+=2
		if self.version>1:
			for i in range(5): # 0
				val=struct.unpack('<H', data[off:off+2])[0]
				add_iter (hd,"f%d"%(i+5),"%02x"%val,off,2,'<H')
				off+=2
		self.checkFinish(hd,data,off,"hdTyped4End")
	def hdTyped6(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz==255:
			add_iter(hd,"name","",off,15,'txt')
		else:
			if sSz>15:
				sSz=15
			add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,15,'txt')
		off=16
		val=struct.unpack('<h', data[off:off+2])[0] # 100
		add_iter (hd,"f0",val,off,2,'<h')
		off+=2
		self.checkFinish(hd,data,off,"hdTyped6")
	def hdTyped7(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz==255:
			add_iter(hd,"name","",off,15,'txt')
		else:
			if sSz>15:
				sSz=15
			add_iter(hd,"name",str(data[off:off+sSz],"cp437"),off,15,'txt')
		off=16
		for i in range(2): # 100, 0
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off+=2
		self.checkFinish(hd,data,off,"hdTyped7")
	def hdTypee6(self,hd,data):
		off=0
		for i in range(10):
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off+=2
		val=struct.unpack('<B', data[off:off+2])[0] # 0
		add_iter (hd,"f10",val,off,2,'<B')
		off+=1
		self.checkFinish(hd,data,off,"hdTypee6")
def wq_open(page, data, parent):
	page.appdoc = QWQDoc(data,page,parent)
	page.appdoc.parse()

