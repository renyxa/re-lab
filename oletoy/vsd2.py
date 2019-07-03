# Copyright (C) 2007-2011,		Valek Filippov (frob@df.ru)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 or later of the GNU General Public
# License as published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA	02110-1301
# USA
#

import sys,struct
import gtk
import tree
import hexdump
import inflate
import vsdchunks,vsdstream4
import ole
import ctypes
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
		0x76:'SmartTagList',
		0xcb:"0xCB list"}

chunktype = {
		0x0a:'Prompt',
		0x0c:'FrgnData ',
		0x0d:'OLE_List ',
		0x0e:'Text IX  ',
		0x10:'Data1    ',
		0x11:'Data2    ',
		0x12:'Data3    ',
		0x14:'Trailer',
		0x15:'Page     ',
		0x16:'Colors',
		0x18:'FontList',
		0x19:'Font ',
		0x1a:'Styles   ',
		0x1d:'Stencils ',
		0x1e:'Stncl Page',
		0x1f:'OLE_Data ',
		0x23:'Icon     ',
		0x27:'Pages ',
		0x28:'Shape Stencil',
		0x29:'Windows ',
		0x2a:'Window ',
		0x2c:'NameList ',
		0x2d:'Name     ',
		0x2e:'EventList',
		0x2f:'EventItem',
		0x31:'Document ',
		0x32:'NameList',
		0x33:'Name ',
		0x42:'UniqueID',
		0x46:'PageSheet',
		0x47:'ShapeType="Group"',
		0x48:'ShapeType="Shape"',
		0x4a:'StyleSheet',
		0x4d:'ShapeType="Guide"',
		0x4e:'ShapeType="Foreign"',
		0x4f:'DocSheet ',
		0x64:'ScratchList',
		0x65:'ShapeList',
		0x66:'FieldList',
		0x67:'UserDefList',
		0x68:'PropList ',
		0x69:'CharList ',
		0x6a:'ParaList ',
		0x6b:'TabsDataList',
		0x6c:'GeomList ',
		0x6d:'CustPropsList',
		0x6e:'ActIdList',
		0x6f:'LayerList',
		0x70:'CtrlList ',
		0x71:'CPntsList',
		0x72:'CnnectList',
		0x73:'HypelLnkList',
		0x76:'SmartTagLst',
		0x83:'ShapeID  ',
		0x84:'Event    ',
		0x85:'Line     ',
		0x86:'Fill     ',
		0x87:'TextBlock',
		0x88:'Tabs Data',
		0x89:'Geometry ',
		0x8a:'MoveTo   ',
		0x8b:'LineTo   ',
		0x8c:'ArcTo    ',
		0x8d:'InfinLine',
		0x8f:'Ellipse  ',
		0x90:'EllpArcTo',
		0x92:'PageProps',
		0x93:'StyleProps',
		0x94:'Char IX ',
		0x95:'ParaIX  ',
		0x96:'Tabs Data',
		0x97:'Tabs Data',
		0x98:'FrgnType',
		0x99:'ConnectPts',
		0x9b:'XForm   ',
		0x9c:'TxtXForm',
		0x9d:'XForm1D ',
		0x9e:'Scratch ',
		0xa0:'Protection',
		0xa1:'TextFields',
		0xa2:'Control ',
		0xa3:'Help    ',
		0xa4:'Misc    ',
		0xa5:'SplineStart',
		0xa6:'SplineKnot',
		0xa7:'LayerMem',
		0xa8:'LayerIX ',
		0xa9:'Act ID  ',
		0xaa:'Control ',
		0xb4:'User-defined',
		0xb5:'Tabs Data',
		0xb6:'CustomProps',
		0xb7:'RulerGrid',
		0xb9:'ConnectionPnts',
		0xba:'ConnectionPnts',
		0xbb:'ConnectionPnts',
		0xbc:'DocProps',
		0xbd:'Image   ',
		0xbe:'Group   ',
		0xbf:'Layout  ',
		0xc0:'PageLayout',
		0xc1:'PolylineTo',
		0xc3:'NURBSTo ',
		0xc4:'Hyperlink',
		0xc5:'Reviewer',
		0xc6:'Annotation',
		0xc7:'SmartTagDef',
		0xc8:'PrintProps',
		0xc9:'NameIDX ',
		0xd1:'Shape Data',
		0xd7:'FontFace',
		0xd8:'FontFaces'
		}

class chunk:
	def __init__(self):
		type = 0		#dword
		IX = 0				#dword
		list = 0	 #dword
		length = 0	#dword
		level = 0	 #word
		unkn3 = 0	 #byte
		hdrlen = 0
		data = ''

	def read_hdr (self,data,offset,version):
		if version > 5:
			self.type,self.IX,self.list,self.length,self.level,self.unkn3 = struct.unpack('<LLLLHB', data[offset:offset+19])
			self.hdrlen = 19
		else:
			self.type,self.IX,self.level,self.unkn3,self.list,self.length = struct.unpack('<HHBBHL', data[offset:offset+12])
			self.hdrlen = 12
		if self.IX == 0xffffffff:
			self.IX = -1

	def get_size (self,data,offset,version):
		trailer = 0
		if self.list != 0 or self.type in chunklist:
			trailer = 8
		if(11 == version): #/* separators were found only in Visio2k3 atm.  trailer means that there is a separator too. */
			if self.list or	(2 == self.level and 0x55 == self.unkn3) or\
				(2 == self.level and 0x54 == self.unkn3 and 0xaa == self.type) or\
				(3 == self.level and 0x50 != self.unkn3) or\
				self.type in (0x64,0x65,0x66,0x69,0x6a,0x6b,0x6f,0x71,0xa9,0xb4,0xb6,0xb9,0xc7) or\
				(0x2c == self.type and self.unkn3 in (0x50,0x54)):
				trailer = trailer + 4
		if 11 == version and self.type in (0x1f,0xc9,0x2d,0xd1):
			trailer = 0
		return self.hdrlen+trailer+self.length

class pointer:
	def __init__(self):
		type = 0
		address = 0
		offset = 0
		length = 0
		format = 0
		shift = 0
		data = ''
		hex = ''

	def read (self,data,ptrdata,offset,version):
		if version < 6:
			self.type,self.format,self.address,self.offset,self.length = struct.unpack('<hhLLL', ptrdata[offset:offset+16])
			self.hex = ptrdata[offset:offset+16]
		else:
			self.type,self.address,self.offset,self.length,self.format = struct.unpack('<LLLLh', ptrdata[offset:offset+18])
			self.hex = ptrdata[offset:offset+18]
		if self.format&2 == 2 : #compressed
			res = inflate.inflate(self, data)
			self.shift = 4
		else:
			res = data[self.offset:self.offset+self.length]
			self.shift = 0
		self.data = res
#		print "rp: %x %x %x %x %x"%(self.type,self.address,self.offset,self.length,self.format)

	def parse_str80 (self,page,data,parent):
		off = 0
		iter1 = ""
		iter2 = ""
		iter3 = ""
		while off < len(self.data) - 19:
			ch = chunk()
			ch.read_hdr(self.data,off,page.version)
			size = ch.get_size(self.data,off,page.version)
			if ch.level == 0:
				iter1 = add_pgiter(page,key2txt(ch.type,chunktype,"%02x"%ch.type)+"\t%02x"%ch.IX,"vsd2",ch.type,self.data[off:off+size],parent)
			elif ch.level == 1:
				iter2 = add_pgiter(page,key2txt(ch.type,chunktype,"%02x"%ch.type)+"\t%02x"%ch.IX,"vsd2",ch.type,self.data[off:off+size],iter1)
			elif ch.level == 2:
				iter3 = add_pgiter(page,key2txt(ch.type,chunktype,"%02x"%ch.type)+"\t%02x"%ch.IX,"vsd2",ch.type,self.data[off:off+size],iter2)
			elif ch.level == 3:
				add_pgiter(page,key2txt(ch.type,chunktype,"%02x"%ch.type)+"\t%02x"%ch.IX,"vsd2",ch.type,self.data[off:off+size],iter3)
			off += size
#			if len(self.data) - off < 19:
#				print "Bang",ch.level,page.model.get_path(parent),page.model.get_path(iter1)

	def parse_str40 (self,page,data,parent):
#		print "ptr40 %02x %02x %02x %02x %02x"%(self.type,self.address,self.offset,self.length,self.format)
		off = 0
		if self.format&2:
			off = 4
		iter1 = add_pgiter(page,key2txt(self.type,chunktype,"Unkn %02x"%self.type)+" (ptr)","vsd2","str40ptr",self.hex,parent)
		page.model.set_value(iter1,7,"%02x"%self.format)
		if len(self.data) > 0:
			iter2 = add_pgiter(page,key2txt(self.type,chunktype,"%02x"%self.type)+" (data)","vsd24",self.type,self.data,iter1)

		if self.format&0x10:
			chnklen = struct.unpack("<I",self.data[off:off+4])[0]
			listlen = struct.unpack("<I",self.data[off+chnklen-4:off+chnklen])[0]
			add_pgiter(page,"Hdr "+key2txt(self.type,chunktype,"%02x"%self.type),"vsd24",self.type,self.data[off:off+chnklen],iter2)
			off += chnklen
			numptr = struct.unpack("<I",self.data[off:off+4])[0]
			off += 8
			for i in range(numptr):
				ptr = pointer()
				ptr.read(data,self.data,off,page.version)
				ptr.parse(page,data,iter2)
				if page.version > 5:
					off += 18
				else:
					off += 16

	def get_colors (self,page, data,parent):
		model = page.model
		clrnum = ord(data[6])
		for i in range(clrnum):
				r = ord(data[8+i*4])
				g = ord(data[9+i*4])
				b = ord(data[10+i*4])
				a = ord(data[11+i*4])
				iter1 = model.append(parent, None)
				txt = "Color #%02x: %02x%02x%02x %02x"%(i,r,g,b,a)
				clr = "#%02x%02x%02x"%(r,g,b)
				model.set (iter1, 0, txt,1,("vsd","clr"),2,4,3,data[8+i*4:12+i*4],5,clr,6,model.get_string_from_iter(iter1))


	def parse (self,page,data,parent):
		# 0x80 -- chunk + list + collection of chunks
		# 0x40 -- one chunk
		# 0x20 -- empty?
		# 0x10 -- array of pointers
		# 0x0* -- depends on ptr type
		if self.format&0x20 == 0x20:
			return
		elif self.type == 0x16: #colors
			iter1 = add_pgiter(page,key2txt(self.type,chunktype,"Unkn %02x"%self.type)+" (ptr)","vsd2",self.type,self.data,parent)
			page.model.set_value(iter1,7,"%02x"%self.format)
			self.get_colors (page,self.data,iter1)
		elif self.format&0x80 == 0x80:
			iter1 = add_pgiter(page,key2txt(self.type,chunktype,"Unkn %02x"%self.type)+" (ptr)","vsd2",self.type,self.data,parent)
			page.model.set_value(iter1,7,"%02x"%self.format)
			self.parse_str80 (page,data,iter1)  # don't need data
		elif self.format&0x40 == 0x40:
				self.parse_str40 (page,data,parent)
		elif self.format != 0:
			# need to parse as 4,5 or 8 based on pointer.type
			if self.type in chunklist:
				self.format += 0x10
#				print '!!!',page.model.get_path(parent),chunklist[self.type],"123","%02x"%self.format,chunklist[self.type]
			self.parse_str40 (page,data,parent)

def parse (page, data, parent):
	ver_offset = 0x1a
	size_offset = 0x1c
	trlr_offset = 0x24
	add_pgiter(page,"Header","vsd2","hdr",data[0:0x24],parent)

	version = ord(data[ver_offset])
	page.version = version
	print("Version: %d"%version)
	print("Size: %02x"%struct.unpack("<I",data[size_offset:size_offset+4])[0])

	if version > 6:
		lenhdr2 = 74
	else:
		lenhdr2 = 4
	add_pgiter(page,"Header part2","vsd2","hdr2",data[0x36:0x36+lenhdr2],parent)

	if 1: #try:
		tr_pntr = pointer()
		tr_pntr.read(data,data,trlr_offset,version)
		tr_pntr.parse(page,data,parent)
#	except:
#		print "Failed in VSD2 parse"
