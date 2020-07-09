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

# import of MS Publisher 1 files
import binascii
import pubblock
import sys,struct
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk,Pango, GObject, Gdk

from utils import *

class Publisher1Doc():
	def __init__(self,data,page,parent):
		self.data = data
		self.parent=parent
		self.version = -1
		if page != None:
			self.page = page
			self.version = page.version

		self.chuncks={
			"FontNames":self.FontNames,
			"TextZone":self.TextZone,
			"TextSp0":self.TextSp0,
			"TextSp1":self.TextSp1,
			# zone3 N,N1, offset?
			"Zone":self.Zone,
			"BorderArts":self.BorderArts,
		}
		self.chunkHds = {
			"BorderArt":self.hdBorderArt,
			"BorderArts":self.hdBorderArts,
			"Document":self.hdDocument,
			"FontName":self.hdFontName,
			"FontNames":self.hdFontNames,
			"Header":self.hdHeader,
			"Pages":self.hdPages,
			"PrinterName":self.hdString,
			"Text":self.hdString,
			"TextZone":self.hdTextZone,
			"Zone":self.hdZone,
			"ZoneInfo":self.hdZoneInfo,
			"ZoneRoot":self.hdZoneRoot,
			"ZoneShape":self.hdZoneShape,
			"TextPLC0":self.hdTextPLC,
			"TextPLC1":self.hdTextPLC,
			"TextPLC2":self.hdTextPLC,
			"TextPLC3":self.hdTextPLC,
			"TextPLC4":self.hdTextPLC,
			"TextSp0":self.hdTextSp,
			"TextSp1":self.hdTextSp,
		}
		self.unseenA5Data=0

	mainZoneNameDict={0:"TextZone", 1:"Document", 3:"Pages", 4:"Zone", 5:"FontNames", 6:"BorderArts"}

	def BorderArts(self,length,off):
		subZone=[]
		begOff=off
		N=struct.unpack('<H', self.data[off:off+2])[0]
		off+=2+2 # skip N1
		lastPtr=struct.unpack('<H', self.data[off:off+2])[0]
		off+=2+6 # skip 3, c, -1

		ptrs=[]
		for i in range(N):
			ptr=struct.unpack('<H', self.data[off:off+2])[0]
			off+=2
			if ptr==0xffff:
				continue
			ptrs.append(ptr)
			if ptr==lastPtr:
				break
		for i in range(len(ptrs)-1):
			subZone.append(("BorderArt%d"%i,"BorderArt", 12+ptrs[i], 66))
			off=begOff+12+ptrs[i]
			wmfPos={12+ptrs[i+1]}
			for j in range(8):
				ptr=struct.unpack('<H', self.data[off+50:off+50+2])[0]
				wmfPos.add(12+ptrs[i]+ptr)
				off+=2
			wmfOrderedPos=sorted(wmfPos)
			for j in range(len(wmfOrderedPos)-1):
				subZone.append(("BorderData%d-%d"%(i,wmfOrderedPos[j]-12-ptrs[i]),"wmf", wmfOrderedPos[j], wmfOrderedPos[j+1]-wmfOrderedPos[j]))
		return subZone
	def FontNames(self,length,off):
		subZone=[]
		N=struct.unpack('<H', self.data[off:off+2])[0]
		off+=2+2 # skip N1
		lastPtr=struct.unpack('<H', self.data[off:off+2])[0]
		off+=2+4 # skip f0,f1

		ptrs=[]
		for i in range(N):
			ptr=struct.unpack('<H', self.data[off:off+2])[0]
			off+=2
			ptrs.append(ptr)
			if ptr==lastPtr:
				break
		for i in range(len(ptrs)-1):
			subZone.append(("FontName%d"%i,"FontName", 10+ptrs[i], ptrs[i+1]-ptrs[i]))
		return subZone
	def TextZone(self,length,off):
		subZone=[]
		begPos=off
		off+=10
		for i in range(3): # 0=end pos
			pos=struct.unpack('<I', self.data[off:off+4])[0]
			off+=4
			if pos==0:
				continue
			if i==0:
				subZone.append(("EOF","EOF",pos,0))
			elif i==1:
				subZone.append(("Text","Text",pos,0))
			else:
				subZone.append(("EOF[Text]","Free",pos,0))
		index=[]
		for i in range(3):
			ptr=struct.unpack('<H', self.data[off:off+2])[0]
			off+=2
			index.append(ptr)
		for i in range(2):
			for j in range(index[i],index[i+1]):
				subZone.append(("TextSp%d-%d"%(i,j),"TextSp%d"%i,j*0x200,0x200))
		for i in range(5):
			pos=struct.unpack('<I', self.data[off:off+4])[0]
			off+=4
			if pos==0:
				continue
			subZone.append(("TextPLC%d"%i,"TextPLC%d"%i,pos,0))
		listZone=list(sorted(subZone, key=lambda i: i[2]))
		subZone=[];
		for i in range(len(listZone)-1):
			subName,subType,subOff,subLen=listZone[i]
			if subOff==listZone[i+1][2]:
				continue
			subZone.append((subName,subType,subOff-begPos, listZone[i+1][2]-subOff))
		return subZone
	def TextSp(self,length,off,wh):
		subZone=[]
		begPos=off
		N=struct.unpack('<B', self.data[begPos+0x1ff:begPos+0x200])[0]
		off+=4*(N+1)
		seenOffset={10000000}
		for i in range(N):
			offset=struct.unpack('<B', self.data[off:off+1])[0]
			off+=1
			if offset==0 or offset in seenOffset:
				continue;
			seenOffset.add(offset)
			len=struct.unpack('<B', self.data[begPos+2*offset:begPos+2*offset+1])[0]
			if wh=="TextSpan":
				subZone.append(("%s%x"%(wh,offset),wh,2*offset,1+len))
			else:
				subZone.append(("%s%x"%(wh,offset),wh,2*offset,1+2*len))
		return subZone
	def TextSp0(self,length,off):
		return self.TextSp(length,off,"TextSpan")
	def TextSp1(self,length,off):
		return self.TextSp(length,off,"TextPara")
	def Zone(self,length,off):
		subZone=[]
		begPos=off
		N=struct.unpack('<H', self.data[off:off+2])[0]
		off+=2+2 # skip N1
		parentType=-1
		listChild=[(-1,begPos+length,"eof")]
		idToMainPosChunk={}
		for i in range(N):
			childId=struct.unpack('<H', self.data[off:off+2])[0]
			childDataPos=struct.unpack('<H', self.data[off+4:off+4+2])[0]
			childDataType=struct.unpack('<B', self.data[off+9:off+10])[0]
			off+=10
			if childDataType in [0x81, 0x91, 0xd1]:
				idToMainPosChunk[childId]=childDataPos
		off=begPos+4
		for i in range(N):
			childId=struct.unpack('<H', self.data[off:off+2])[0]
			parentId=struct.unpack('<H', self.data[off+2:off+4])[0]
			childDataPos=struct.unpack('<H', self.data[off+4:off+4+2])[0]
			childDataId=struct.unpack('<h', self.data[off+6:off+6+2])[0]
			childType=struct.unpack('<B', self.data[off+8:off+9])[0]
			childDataType=struct.unpack('<B', self.data[off+9:off+10])[0]
			off+=10
			subZone.append(("ZoneInfo-S%d"%childId,"ZoneInfo", 4+10*i, 10))
			newPos=0
			if childDataType in [0x81, 0x91, 0xd1]: # 91: bitmap, d1: ole data
				newPos=childDataPos
				parentType=childType
				if childType==0 and childDataType==0x81:
					what="ZoneRoot"
				else:
					fType=struct.unpack('<I', self.data[newPos:newPos+4])[0];
					if fType==0x501:
						what="embeddedOLE"
					elif fType in [0x90001,0xa0002]:
						what="wmf"
					elif childType==0 or childDataType==0x81:
						what="ZoneRoot"
					else:
						what="ZoneRoot%02x-%02x"%(childDataType,childType)
			elif childDataType in [0x85, 0x95] and parentId in idToMainPosChunk:
				newPos=idToMainPosChunk[parentId]+childDataPos
				what="ZoneShape"
			else:
				print("Unknown zone 4 type=%02x"%childDataType)
			if newPos!=0:
				listChild.append((childId,newPos-4 if childDataType in [0x81,0x91,0xd1] else newPos,what))
		listChild=sorted(listChild, key=lambda i: i[1])
		for i in range(len(listChild)-1):
			childId,childOff,what=listChild[i]
			if childOff==listChild[i+1][1]:
				continue;
			subZone.append(("%s-S%d"%(what,childId),what, childOff-begPos, listChild[i+1][1]-childOff))
		return subZone
	def parseHeader(self, length, off):
		subZone=[];
		off+=2
		pos=struct.unpack('<H', self.data[off:off+2])[0]
		off+=2
		subZone.append(("PrinterName","PrinterName",pos,0)) # or junk
		off+=4 # 2c6
		pos=struct.unpack('<I', self.data[off:off+4])[0] # end of file
		subZone.append(("EOF","EOF",pos,0))
		off+=4
		for i in range(8):
			pos=struct.unpack('<I', self.data[off:off+4])[0]
			off+=4
			if pos==0:
				continue
			if i in self.mainZoneNameDict.keys():
				subZone.append((self.mainZoneNameDict[i],self.mainZoneNameDict[i],pos,0))
			else:
				subZone.append(("zone%d"%i,"zone%d"%i,pos,0))
		listZone=list(sorted(subZone, key=lambda i: i[2]))
		subZone=[];
		for i in range(len(listZone)-1):
			subName,subType,subOff,subLen=listZone[i]
			if subOff==listZone[i+1][2]:
				continue
			subZone.append((subName,subType,subOff, listZone[i+1][2]-subOff))
		return subZone
	## main parsing
	def parse(self):
		off = 0
		hdrsize = struct.unpack("<H",self.data[2:4])[0]
		if hdrsize != 0x2c:
			print("Unknown header size")
			return
		eof = struct.unpack("<I",self.data[4:8])[0]
		add_pgiter (self.page,"Header","pub1","Header",self.data[0:hdrsize],self.parent)
		subZone=self.parseHeader(hdrsize, 0);
		stack=[]
		for i in range(len(subZone)):
			stack.append(subZone[i]+(self.parent,))
		while len(stack)>0:
			subName,subType,subOff,subLen,parent=stack.pop(0)
			if subLen==0:
				continue
			subData=self.data[subOff:subOff+subLen]
			niter=add_pgiter(self.page,subName,"pub1",subType,subData,parent)

			childZone=[]
			if subType in self.chuncks:
				res=self.chuncks[subType](subLen,subOff)
				if type(res) is list:
					childZone=res
			for j in range(len(childZone)):
				childName,childType,childOff,childLen=childZone[j]
				stack.append((childName,childType,subOff+childOff,childLen,niter))

	## local parsing
	def update_view2(self,hd,model,iter):
		key=model.get_value(iter,1)[1]
		if key in self.chunkHds:
			self.chunkHds[key](hd,model.get_value(iter,3))
	def checkFinish(self,hd,data,off,name):
		if len(data)>off:
			extra=len(data)-off
			add_iter (hd,"##extra",binascii.hexlify(data[off:off+extra]), off, extra, "txt")
			print("%s: Find unexpected data"%name)
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
	def hdUInt(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"val","%02x"%val,off,2,'<H')
		off+=2
		self.checkFinish(hd,data,off,"hdUInt")

	def hdString(self,hd,data):
		add_iter(hd,"val",str(data.partition(b'\0')[0],"cp1250"),0,len(data),'txt')
	def hdCString(self,hd,data):
		off=0
		sSz=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"sSz",sSz,off,1,'<B')
		off+=1
		if sSz==255:
			add_iter(hd,"val","_",off,len(data)-1,'txt')
		else:
			add_iter(hd,"val",str(data[off:off+sSz],"cp1250"),off,sSz,'txt')
	def hdBorderArt(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0] # 1
		add_iter (hd,"type",val,off,2,'<H')
		off+=2
		add_iter(hd,"val",str(data[2:44].partition(b'\0')[0],"cp1250"),2,66,'txt')
		off=44
		dim=""
		for i in range(3):
			val=struct.unpack('<H', data[off:off+2])[0]
			dim += "%d,"%val
			off+=2
		add_iter (hd,"dim",dim,off-6,6,'txt')
		for i in range(8):
			ptr=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"pos%d"%i,ptr,off,2,'<H')
			off+=2
		self.checkFinish(hd,data,off,"hdBorderArt")
	def hdBorderArts(self,hd,data):
		off=0
		N=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",N,off,2,'<H')
		off+=2
		N1=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N1",N1,off,2,'<H')
		off+=2
		lastPtr=struct.unpack('<H', data[off:off+2])[0] # 
		add_iter (hd,"last[ptr]","%02x"%lastPtr,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # 3: type?
		add_iter (hd,"type?",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # c
		add_iter (hd,"header[size]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0] # -1
		add_iter (hd,"f0",val,off,2,'<h')
		off+=2
		for i in range(N):
			ptr=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"ptr%d"%i,"%02x"%ptr,off,2,'<H')
			off+=2
	def hdDocument(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0] # 0x3e
		add_iter (hd,"zone[sz]",val,off,2,'<H')
		off+=2
		ids="" # 1,2[background],4,3[layout]
		for i in range(4):
			val=struct.unpack('<H', data[off:off+2])[0] #
			ids += "S%d,"%val
			off+=2
		add_iter (hd,"ids",ids,off-8,8,'txt')
		for i in range(4): # 230,0,1,0
			val=struct.unpack('<H', data[off:off+2])[0] #
			add_iter (hd,"f%d"%i,val,off,2,'<H')
			off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # default: 0
		add_iter (hd,"page[type]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"page[width]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"page[length]",val,off,2,'<H')
		off+=2
		for i in range(2): # 0,0
			val=struct.unpack('<H', data[off:off+2])[0] #
			add_iter (hd,"g%d"%i,val,off,2,'<H')
			off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # 1: checkme
		add_iter (hd,"paper[type]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"paper[width]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"paper[length]",val,off,2,'<H')
		off+=2
		for i in range(9): # 7,d,0,0,-1,13,2c,0,2d0, maybe some printer parameter
			val=struct.unpack('<h', data[off:off+2])[0] #
			add_iter (hd,"h%d"%i,val,off,2,'<h')
			off+=2
		for i in range(5): # 0
			val=struct.unpack('<h', data[off:off+2])[0] #
			add_iter (hd,"j%d"%i,val,off,2,'<h')
			off+=2
		self.checkFinish(hd,data,off,"hdDocument")
	def hdFontName(self,hd,data):
		off=0
		val=struct.unpack('<B', data[off:off+1])[0] # 0
		add_iter (hd,"f0",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0] # 2|10|12
		add_iter (hd,"f1",val,off,1,'<B')
		off+=1
		add_iter(hd,"val",str(data[2::].partition(b'\0')[0],"cp1250"),2,len(data)-2,'txt')
	def hdFontNames(self,hd,data):
		off=0
		N=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",N,off,2,'<H')
		off+=2
		N1=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N1",N1,off,2,'<H')
		off+=2
		lastPtr=struct.unpack('<H', data[off:off+2])[0] # 2
		add_iter (hd,"last[ptr]","%02x"%lastPtr,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # 2
		add_iter (hd,"type",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # a, maybe header size
		add_iter (hd,"header[sz]",val,off,2,'<H')
		off+=2
		for i in range(N):
			ptr=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"ptr%d"%i,"%02x"%ptr,off,2,'<H')
			off+=2
	def hdHeader(self,hd,data):
		off=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"header[sz]","%02x"%val,off,2,'<H')
		off+=2
		val=struct.unpack('<I', data[off:off+4])[0] # 2c6
		add_iter(hd,"f0","%04x"%val,off,4,'<I')
		off+=4
		pos=struct.unpack('<I', data[off:off+4])[0]
		add_iter(hd,"eof","%04x"%pos,off,4,'<I')
		off+=4
		for i in range(8):
			pos=struct.unpack('<I', data[off:off+4])[0]
			off+=4
			if pos==0:
				continue
			if i in self.mainZoneNameDict.keys():
				add_iter(hd,self.mainZoneNameDict[i],"%04x"%pos,off-4,4,'<I')
			else:
				add_iter(hd,"pos%d"%i,"%04x"%pos,off-4,4,'<I')
		self.checkFinish(hd,data,off,"hdHeader")
	def hdPages(self,hd,data):
		off=0
		N=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",N,off,2,'<H')
		off+=2
		N1=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N1",N1,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # 2
		add_iter (hd,"last[ptr]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # 0
		add_iter (hd,"type",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0] # a, maybe header size
		add_iter (hd,"header[size]",val,off,2,'<H')
		off+=2
		for i in range(N):
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"id%d"%i,"S%d"%val,off,2,'<H') # the shape id
			off+=2
	def hdTextZone(self,hd,data):
		off=0
		for i in range(5): # f0de, 30, 64, 200, 0
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<H')
			off+=2
		pos=struct.unpack('<I', data[off:off+4])[0]
		add_iter(hd,"eof","%04x"%pos,off,4,'<I')
		off+=4
		for i in range(2):
			pos=struct.unpack('<I', data[off:off+4])[0]
			off+=4
			if pos==0:
				continue
			add_iter(hd,"text[pos]" if i==0 else "Text[end,pos]","%04x"%pos,off-4,4,'<I')
		for i in range(3): # 0,0,0 or a,b,c
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"index%d"%i,val,off,2,'<H')
			off+=2
		for i in range(5):
			pos=struct.unpack('<I', data[off:off+4])[0]
			off+=4
			if pos==0:
				continue
			add_iter(hd,"TextPLC%d[pos]"%i,"%04x"%pos,off-4,4,'<I')
	def hdTextPLC(self,hd,data):
		off=0
		N=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",N,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N[max]",val,off,2,'<H')
		off+=2
		dataSz=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"data[sz]",dataSz,off,2,'<H')
		off+=2
		for i in range(6): # 0,0,0,43,8,-1
			val=struct.unpack('<h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,val,off,2,'<h')
			off+=2
		pos=struct.unpack('<I', data[off:off+4])[0]
		add_iter(hd,"pos[text]","%04x"%pos,off,4,'<I')
		off+=4
		if N>0:
			str=""
			for i in range(N):
			     pos=struct.unpack('<I', data[off:off+4])[0]
			     off+=4
			     str += ("%04x,"%pos)
			add_iter (hd,"pos[char]",str,off-4*N,4*N,'txt')
			for i in range(N):
				# plc2: odd data: 0-0-zId-id1-text zone id[in plc3]
				add_iter (hd,"data%d"%i,binascii.hexlify(data[off:off+dataSz]),off,dataSz,"text")
				off+=dataSz
	def hdTextSp(self,hd,data):
		N=struct.unpack('<B', data[0x1ff:0x200])[0]
		add_iter (hd,"N",N,0x1ff,1,'<H')
		off=0
		str=""
		for i in range(1+N):
			pos=struct.unpack('<I', data[off:off+4])[0]
			off+=4
			str += ("%04x,"%pos)
		add_iter (hd,"pos[char]",str,0,4*(N+1),'txt')
		if N>0:
			str=""
			for i in range(N):
			     offset=struct.unpack('<B', data[off:off+1])[0]
			     off+=1
			     str += ("%x,"%offset if offset!=0 else "_,")
			add_iter (hd,"offset",str,4*(N+1),N,'txt')

	def hdZone(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N[max]",val,off,2,'<H')
		off+=2
	def hdZoneInfo(self,hd,data):
		off=0
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"id","S%d"%val,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0]
		add_iter (hd,"id[parent]","" if val==-1 else "S%d"%val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"offset","%02x"%val,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0]
		add_iter (hd,"id[data]","" if val==-1 else val,off,2,'<h') # data Sid for ole, text zone id for text?
		off+=2
		val=struct.unpack('<B', data[off:off+1])[0] # 0: normal 2: a string?
		add_iter (hd,"type",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0] # 81:main|85:sub,offset relative to parent zone
		add_iter (hd,"fl","%01x"%val,off,1,'<B')
		off+=1
		self.checkFinish(hd,data,off,"hdZoneInfo")
	def hdZoneShape(self,hd,data):
		off=0
		typ=struct.unpack('<H', data[off:off+2])[0]
		typeMap={0:"text", 2:"pict", 3:"ole", 4:"line", 5:"rect", 6:"rectOval", 7:"oval"}
		add_iter (hd,"type",typeMap[typ] if typ in typeMap else typ,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0]
		add_iter (hd,"id",val,off,2,'<H')
		off+=2
		for i in range(2):
			dims="";
			for j in range(4):
				val=struct.unpack('<h', data[off:off+2])[0]
				dims+="%d"%val
				if j % 2==0:
					dims+="x"
				elif j==1:
					dims+="<->";
				off+=2
			add_iter (hd,"dim%d"%i,dims,off-8,8,'txt')
		for i in range(2): # col0=first color,col1=background
			val=struct.unpack('<B', data[off:off+1])[0]
			add_iter (hd,"col%d"%i,val,off,1,'<B')
			off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"pattern",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"col[line]",val,off,1,'<B')
		off+=1
		val=struct.unpack('<B', data[off:off+1])[0]
		add_iter (hd,"width[line]",val,off,1,'<B')
		off+=1
		val=struct.unpack('<h', data[off:off+2])[0]
		add_iter (hd,"art[pictId]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0]
		add_iter (hd,"f2",val,off,2,'<H')
		off+=2
		val=struct.unpack('<B', data[off:off+1])[0] # 0
		add_iter (hd,"f3",val,off,1,'<B')
		off+=1
		val=struct.unpack('<H', data[off:off+2])[0] # val&2 means selected, val&8 means shadow, val&10 means symetry(for line), val&20 means arrow start, val&20 means arrow end
		add_iter (hd,"fl","%02x"%val,off,2,'<H')
		off+=2
		if typ==0:
			r = struct.unpack("<B",data[off:off+1])[0]
			off+=1
			g = struct.unpack("<B",data[off:off+1])[0]
			off+=1
			b = struct.unpack("<B",data[off:off+1])[0]
			off+=1
			add_iter (hd,'RGB',"%d %d %d"%(r,g,b),off-3,3,"<BBB")
			for i in range(4): #0,0,78,0 or 78,78,f0,0 or 85,65,78,0
				val=struct.unpack('<H', data[off:off+2])[0]
				add_iter (hd,"g%d"%i,val,off,2,'<H')
				off+=2
			N=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"N",N,off,2,'<H')
			off+=2
			for i in range(N):
				val=struct.unpack('<H', data[off:off+2])[0]
				add_iter (hd,"pos%d"%i,val,off,2,'<H') # some id maybe to text
				off+=2
		elif typ==2 or typ==3:
			x = struct.unpack("<B",data[off:off+1])[0]
			off+=1
			y = struct.unpack("<B",data[off:off+1])[0]
			off+=1
			z = struct.unpack("<B",data[off:off+1])[0]
			off+=1
			add_iter (hd,'dims',"%d %d %d"%(x,y,z),off-3,3,"<BBB")
			for i in range(2): #0
				val=struct.unpack('<H', data[off:off+2])[0]
				add_iter (hd,"g%d"%i,val,off,2,'<H')
				off+=2
			for i in range(2):
				dims="";
				for j in range(4):
					val=struct.unpack('<h', data[off:off+2])[0]
					dims+="%d"%val
					if j % 2==0:
						dims+="x"
					elif j==1:
						dims+="<->";
					off+=2
				add_iter (hd,"dim%d"%(i+2),dims,off-8,8,'txt')
			val=struct.unpack('<H', data[off:off+2])[0] # 5a0
			add_iter (hd,"fl2","%02x"%val,off,2,'<H')
			off+=2
			dims="";
			for j in range(2):
				val=struct.unpack('<h', data[off:off+2])[0]
				dims+="%d"%val
				if j % 2==0:
					dims+="x"
				off+=2
			add_iter (hd,"size",dims,off-8,8,'txt')
			# sometimes followed by fffffffffffffffff8
		# elif typ==1: followed by 000000000000000000000000000000090000000a00
		if len(data)>off:
			extra=len(data)-off
			add_iter (hd,"#extra",binascii.hexlify(data[off:off+extra]), off, extra, "txt")
	def hdZoneRoot(self,hd,data):
		off=0
		val=struct.unpack('<I', data[off:off+4])[0]
		add_iter (hd,"len","%04x"%val,off,4,'<I')
		off+=4
		N=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N",N,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"N[max]",val,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0]
		add_iter (hd,"id",val,off,2,'<H')
		off+=2
		val=struct.unpack('<h', data[off:off+2])[0] # 0
		add_iter (hd,"f0",val,off,2,'<H')
		off+=2
		dims="";
		for i in range(4):
			val=struct.unpack('<h', data[off:off+2])[0] # 0
			dims+="%d,"%val
			off+=2
		add_iter (hd,"margins",dims,off-8,8,'txt') # layout L,R,T,B
		for i in range(2): # layout numbers of rows/columns
			val=struct.unpack('<h', data[off:off+2])[0] # 0
			add_iter (hd,"nums[row]" if i==0 else "nums[col]",val,off,2,'<H')
			off+=2
		val=struct.unpack('<h', data[off:off+2])[0] # 0
		add_iter (hd,"g0",val,off,2,'<H')
		off+=2
		val=struct.unpack('<H', data[off:off+2])[0]
		add_iter (hd,"end[pos]","%02x"%val,off,2,'<H')
		off+=2
		for i in range(N):
			val=struct.unpack('<H', data[off:off+2])[0]
			add_iter (hd,"pos%d"%i,"%02x"%val,off,2,'<H')
			off+=2

def publisher_open(page, data, parent):
	page.appdoc = Publisher1Doc(data,page,parent)
	page.appdoc.parse()

