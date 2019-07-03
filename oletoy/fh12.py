# Copyright (C) 2007-2013,	Valek Filippov (frob@df.ru)
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
from utils import *

class ZoneHeader:
        def __init__(self,version):
                self.version = version
                self.dataSize = 0
                self.type = -1
        def parse(self, buf, off):
                self.dataSize = struct.unpack(">I",buf[off:off+4])[0]
                if self.dataSize == 0xFFFFFFFF:
                        return
                self.type = struct.unpack(">H",buf[off+4:off+6])[0]

# tool
def HeaderStyleSize (buf,off,header):
        if header.version==1:
                dtSz = struct.unpack(">H",buf[off+8:off+10])[0]
                return 10+dtSz+2
        return 8
def HeaderGroupSize (buf,off,header):
        if header.version>1:
                return 18
        offset=off+8
        dtSz = struct.unpack(">H",buf[offset:offset+2])[0]
        offset += (2+dtSz)+8
        dtSz = struct.unpack(">H",buf[offset:offset+2])[0]
        offset += (2+dtSz)
        return offset-off

# generic
def String(buf,off,header):
        len = header.dataSize+2 if header.version==1 else header.dataSize-2
        return len,"String"

# list of zone
def Root(buf,off,header): # the main group
	return 24 if header.version==1 else 34,"Root"

def Group (buf,off,header):
        if header.version==1:
                id_num = struct.unpack(">H",buf[off+18:off+20])[0]
                return 20+id_num*2,"Group"
        sSz=struct.unpack(">H",buf[off+10:off+12])[0]
        id_num = struct.unpack(">H",buf[off+18+sSz:off+20+sSz])[0]
        return 20+sSz+id_num*2,"Group"
def ListStyle(buf,off,header):
        if header.version==1:
                hdr_len = struct.unpack(">H",buf[off+8:off+10])[0]
                id_num = struct.unpack(">H",buf[off+10:off+12])[0]
                return hdr_len+id_num*2,"ListStyle"
        else:
                id_num = struct.unpack(">H",buf[off+6:off+8])[0]
                return 12+id_num*2,"ListStyle"

# shape
def JoinGroup(buf,off,header):
	return HeaderGroupSize(buf,off,header)+8,"JoinGroup"
def TransformGroup(buf,off,header):
	return HeaderGroupSize(buf,off,header)+30,"TransformGroup"
def Rectangle (buf,off,header):
        subZone=[]
        len=HeaderGroupSize(buf,off,header)
        len+=4+(6 if header.version>1 else 0)+8
        matrixSize=struct.unpack(">I",buf[off+len:off+len+4])[0]
        if matrixSize:
                subZone.append(("transform","Transform",off+len+4,matrixSize))
        len+=matrixSize+4
	return len+4,"Rectangle",subZone
def Oval (buf,off,header):
        subZone=[]
        len=HeaderGroupSize(buf,off,header)
        len+=4+(6 if header.version>1 else 0)+8
        matrixSize=struct.unpack(">I",buf[off+len:off+len+4])[0]
        if matrixSize:
                subZone.append(("transform","Transform",off+len+4,matrixSize))
        len+=matrixSize+4
	return len,"Oval"
def Line (buf,off,header):
        len=HeaderGroupSize(buf,off,header)
        len+=4+(6 if header.version>1 else 0)+8
	return len,"Line"
def Path (buf,off,header):
        subZone=[]
        len=HeaderGroupSize(buf,off,header)
        len+=4+(6 if header.version>1 else 0)+2
        N=struct.unpack(">H",buf[off+len:off+len+2])[0]
        len+=2
        for i in range(0,N):
                subZone.append(("pt%d"%i,"PathPoint",off+len,16))
                len+=16
	return len,"Path",subZone
def Text (buf,off,header):
        subZone=[]
        offset=off+HeaderGroupSize(buf,off,header)
        if header.version==1:
                N = struct.unpack(">I",buf[offset:offset+4])[0]
                subZone.append(("flags","TextFlags",offset+4,3*(N//2)))
                offset+=4+3*(N//2)
                offset+=4
                textSz = struct.unpack(">I",buf[offset:offset+4])[0]
                subZone.append(("text","TextString",offset+4,textSz))
                offset+=4+textSz
                offset+=8+26 # dim + transform
                offset+=8+8+2 # spacing + scaling
                nPLC=struct.unpack(">H",buf[offset:offset+2])[0]
                offset+=2;
                for i in range(0,nPLC):
                        subZone.append(("plc%d"%i,"TextPLC",offset,18))
                        offset+=18
        else: # or header.dataSize-18+notelen,"Text"
                offset+=14+8+26 # unkn+dim+transform
                offset+=14 # justify+unknown
                dataSize=struct.unpack(">H",buf[offset:offset+2])[0]
                offset+=2
                textSz=struct.unpack(">H",buf[offset:offset+2])[0]
                offset+=2+54
                subZone.append(("unknown","TextUnknown",offset,dataSize-22-80-54));
                offset+=dataSize-22-80-54
                subZone.append(("text","TextString",offset,textSz))
                offset+=textSz
	return offset-off,"Text",subZone

def BackgroundPicture (buf,off,header):
        len=HeaderGroupSize(buf,off,header)
        len+=28
        len+=struct.unpack(">I",buf[off+len:off+len+4])[0]+4
	return len,"BackgroundPicture"
def Picture (buf,off,header):
	return HeaderGroupSize(buf,off,header)+58,"Picture"

# style
def ColorRGB(buf,off,header):
	return HeaderStyleSize(buf,off,header)+12,"ColorRGB"

def ColorGrey(buf,off,header):
	return HeaderStyleSize(buf,off,header)+(4 if header.version==1 else 10),"ColorGrey"

def ColorCMY(buf,off,header):
	return HeaderStyleSize(buf,off,header)+(8 if header.version==1 else 14),"ColorCMY"

def ColorPantone(buf,off,header):
	return HeaderStyleSize(buf,off,header)+22,"ColorPantone"

def LineStyle (buf,off,header):
	return HeaderStyleSize(buf,off,header)+(12 if header.version==1 else 18),"LineStyle"

def PatternLine (buf,off,header):
	return HeaderStyleSize(buf,off,header)+22,"PatternLine"

def FillStyle (buf,off,header):
        return HeaderStyleSize(buf,off,header)+(3 if header.version==1 else 8),"FillStyle"

def GradientLinear(buf,off,header):
	return HeaderStyleSize(buf,off,header)+(8 if header.version==1 else 12),"GradientLinear"

def GradientRadial(buf,off,header):
	return HeaderStyleSize(buf,off,header)+(4 if header.version==1 else 14),"GradientRadial"

def PatternFill (buf,off,header):
	return HeaderStyleSize(buf,off,header)+14,"PatternFill"

def TileStyle (buf,off,header):
	return HeaderStyleSize(buf,off,header)+54,"TileStyle"

def PSStyle(buf,off,header):
        len=HeaderStyleSize(buf,off,header)
        stringSz = ord(buf[off+len])
        return len+1+stringSz,"PSStyle"

def PSLine (buf,off,header):
	return header.dataSize-4,"PSFill"

def PSFill (buf,off,header):
	return header.dataSize-4,"PSLine"

def Dash(buf,off,header):
        return header.dataSize+2 if header.version==1 else header.dataSize-2, "Dash"

# other
def Data (buf,off,header):
	# this can be a note, a picture, depend on the group type
	rlen = struct.unpack(">I",buf[off+6:off+10])[0]
	return rlen+10,"Data"

# v1

rec_types1 = {
	0x0002:ListStyle,
	0x0003:String,
	0x0fa1:Root,
	0x0fa2:Group,

	0x1005:TransformGroup,
	0x1006:Text,
        0x1007:BackgroundPicture,
	0x1008:JoinGroup,

	0x106a:ColorRGB,
	0x106b:ColorGrey,
	0x106c:ColorCMY,

	0x10cd:FillStyle,
	0x10ce:LineStyle,
        0x10cf:PSStyle,
	0x10d0:GradientLinear,
	0x10d1:GradientRadial,

	0x1131:Rectangle,
	0x1132:Oval,
	0x1134:Path,
	0x1135:Line,

	0x1195:Dash,
}

rec_types2 = {
	0x0005:ListStyle,
	0x0006:String,
	0x1389:Root,
	0x138a:Group,
	0x138b:Data, # can be a note, a picture, ...

	0x13ed:TransformGroup,
	0x13ee:Text,
	0x13f0:JoinGroup,
	0x13f8:Picture,

	0x1452:ColorRGB,
	0x1453:ColorGrey,
	0x1454:ColorCMY,
	0x1455:ColorPantone,

	0x14b5:FillStyle,
	0x14b6:LineStyle,
	0x14b7:GradientLinear,
	0x14b8:GradientRadial,

	0x14c9:PSFill,
	0x14ca:PSLine,

	0x14d3:PatternFill,
	0x14d4:PatternLine,
	0x14dd:TileStyle,

	0x1519:Rectangle,
	0x151a:Oval,
	0x151c:Path,
	0x151d:Line,

	0x157d:Dash,
}

def fh_open (buf,page,parent=None,mode=1):
	if buf[0:4] == "FHD2":
		page.version = 2
		hdrlen = 0x100
		rec_types = rec_types2
	elif buf[0:4] == "acf3":
		page.version = 1
		hdrlen = 0x80
		rec_types = rec_types1
	off = 0
	piter = add_pgiter(page,"FH12 file","fh12","file",buf,parent)
	add_pgiter(page,"FH%d Header"%page.version,"fh12","header",buf[0:hdrlen],piter)
	off = hdrlen
        if page.version == 2:
                rlen=0x78
                add_pgiter(page,"PrintInfo","fh12","printInfo",buf[off:off+rlen],piter)
                off += rlen
	lim = len(buf)
	rid = 1
	while off < lim:
                header=ZoneHeader(page.version)
                header.parse(buf,off)
                if header.type==-1:
			print('Complete!')
			break
		if header.type in rec_types:
                        res=rec_types[header.type](buf,off,header)
                        rlen=rtype=0
                        subList=[]
                        if len(res)==2:
                                rlen,rtype=res
                        elif len(res)==3:
                                rlen,rtype,subList=res
                        if rlen > 4:
                                data=buf[off:off+rlen]
				reciter = add_pgiter(page,"Z%d\t%s"%(rid,rtype),"fh12",rtype,data,piter)
                                for i in range(0,len(subList)):
                                        subName,subType,subOff,subLen=subList[i]
                                        subData=buf[subOff:subOff+subLen]
                                        add_pgiter(page,subName,"fh12",subType,subData,reciter)
			off += rlen
                        rid += 1
		else:
			print("Unknown","%02x%02x"%(rid,header.dataSize),"%02x"%header.type)
			add_pgiter(page,"[%02x] Unknown %02x"%(rid,header.type),"fh12","%02x"%header.type,buf[off:off+1000],piter)
			off += 1000

# DATA

# tool
def HeaderStyleHdl(hd,size,data):
        if hd.version==1:
                add_iter(hd, "unkn", "", 6, 2, "txt")
                dtSz = struct.unpack(">H",data[8:10])[0]
                add_iter(hd, "data", "", 8, 2+dtSz, "txt")
                id = struct.unpack(">H",data[10+dtSz:12+dtSz])[0]
                add_iter(hd, "label", "Z%d"%id if id!=0 else "",10+dtSz,2,"txt")
                return 10+dtSz+2
        id = struct.unpack(">H",data[6:8])[0]
        add_iter(hd, "label", "Z%d"%id if id!=0 else "", 6,2,"txt")
        return 8
def HeaderShapeHdl(hd,size,data):
        off=6
        if hd.version>1:
                id = struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "note", "Z%d"%id if id!=0 else "",off,2,"txt")
                off+=2
                add_iter(hd, "unkn0", "", off, 2, "txt")
                off+=2
                id = struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "layer", id ,off,2,">H")
                off+=2
                add_iter(hd, "unkn1", "", off, 2, "txt")
                off+=2
                val = struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "x?", val/256., off, 2, ">h")
                off+=2
                val = struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "y?", val/256., off, 2, ">h")
                off+=2
                return off
        add_iter(hd, "unkn0", "", off, 2, "txt")
        off+=2
        dtSz=struct.unpack(">H",data[off:off+2])[0]
        if dtSz>0:
                (n, endOff) = rdata(data, off+3, '%ds'%(dtSz-1))
                add_iter(hd, "note", n, off, 2+dtSz, "txt")
        else:
                add_iter(hd, "note", "", off, 2, "txt")
        off+=2+dtSz
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "layer", id,off,2,">H")
        off+=2
        add_iter(hd, "unkn1", "", off, 4, "txt")
        off+=4
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "rect", "Z%d"%id if id!=0 else "",off,2,"txt")
        off+=2
        dtSz = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "screenMode", "", off, 2+dtSz, "txt")
        off+=2+dtSz
        return off

#
def StringHdl(hd,size,data,what):
        stringSz = ord(data[6]) if size > 6 else 0
        if stringSz > 0:
                (n, endOff) = rdata(data, 7, '%ds'%stringSz)
                add_iter(hd, "val", n,7,stringSz,"txt")
        elif stringSz < 0 and size>7:
                print("Can not read a string")
                add_iter(hd, "val", "###",7,size-7,"txt")
def TextStringHdl(hd,size,data,what):
        (n, endOff) = rdata(data, 0, '%ds'%size)
        add_iter(hd, "val", unicode(n,"mac-roman"),0,size,"txt")
fontType_ids={
        0: "default",
        1: "heavy",
        2: "oblique",
        3: "outline",
        4: "shadow",
        5: "fillAndStroke", #v2
        0x78: "char", #v2
        0x79: "zoom" #v2
}
def TextPLCHdl(hd,size,data,what):
        off=0
        id=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "font[id]", "Z%d" %id if id else "", off, 2, "txt")
        off+=2
        id=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "color[id]", "Z%d" %id if id else "", off, 2, "txt")
        off+=2
        val=struct.unpack(">i",data[off:off+4])[0]
        add_iter(hd, "fontSize", val/65536.,off,4,">i")
        off+=4
        val=struct.unpack(">i",data[off:off+4])[0]
        if val==-2:
                add_iter(hd, "leading", "solid",off,4,">i")
        elif val==-1:
                add_iter(hd, "leading", "auto",off,4,">i")
        elif val>=0:
                add_iter(hd, "leading", val/65536.,off,4,">i")
        else:
                add_iter(hd, "leading", "##%x"%val,off,4,">i")
        off+=4
        cPos=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "cPos", cPos,off,2,">H")
        off+=2
        val=struct.unpack(">H",data[off:off+2])[0]
        idtxt=""
        if val&1:
                idtxt+="bold,"
        if val&2:
                idtxt+="italic,"
        add_iter (hd, "flag1", "0x%02x (%s)"%(val,idtxt),off,2,">H")
        off+=2
        val=struct.unpack(">H",data[off:off+2])[0]
        idtxt = "Unknown"
        if val in fontType_ids:
                idtxt = fontType_ids[val]
        add_iter (hd, "type", "0x%02x (%s)"%(val,idtxt),off,2,">H")
        off+=2
pathType_ids={
        0: "default",
        1: "connector",
        2: "curve"
}
def PathPointHdl(hd,size,data,what):
        off=0
        val=struct.unpack(">H",data[off:off+2])[0]
        idtxt = "Unknown"
        if val in pathType_ids:
                idtxt = pathType_ids[val]
        add_iter (hd, "type", "0x%02x (%s)"%(val,idtxt),off,2,">H")
        off+=2
        val=struct.unpack(">H",data[off:off+2])[0]
        idtxt = ""
        if val&0x100:
                idtxt+="no[autoCurv],";
        add_iter (hd, "flag", "0x%02x (%s)"%(val,idtxt),off,2,">H")
        off+=2
        for pt in range(1,6+1):
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter (hd, "coord%d"%pt, val/10.,off,2,">h")
                off+=2

def TransformHdl(hd,size,data,what,off=0):
        if size!=26:
                return
        val=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "flag", "%02x"%val, off, 2, "txt")
        off +=2
        for i in range(1,4+1):
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd, "rot%d"%i, val/65536., off, 4, ">i")
                off+=4
        for i in range(1,2+1):
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd, "translate%d"%i, val/65536./10., off, 4, ">i")
                off+=4

def RootHdl(hd,size,data,what):
        if hd.version==1:
                add_iter(hd, "header", "",6,10,"txt")
                hdr_len=10
                numTypes=7
                typeArray = ('main', 'groupStyle', 'fillStyle', 'lineStyle', 'colStyle', 'dashStyle', 'colStyle2')
        else:
                hdr_len=6
                numTypes=9
                typeArray = ('main', 'colStyle', 'fillStyle', 'lineStyle', 'groupStyle2', 'fillStyle2', 'lineStyle2', 'dashStyle', 'colStyle2')
        for i in range(1,numTypes+1):
                val = struct.unpack(">H",data[hdr_len+2*i-2:hdr_len+2*i])[0]
                if val!=0:
                        add_iter(hd, typeArray[i-1], "Z%d" %val, 2*i-2, 2, "txt")
                else:
                        add_iter(hd, typeArray[i-1], "", 2*i-2, 2, "txt")
        if hd.version==2:
                add_iter(hd, "unkn", "", 24, 10, "txt")

def GroupHdl(hd,size,data,what):
        if hd.version==1:
                add_iter(hd, "header", "",6,12,"txt")
                off=20
        else:
                add_iter(hd, "header", "",6,4,"txt")
                sSz=struct.unpack(">H",data[10:12])[0]
                add_iter (hd, "unkData", "",10,2+sSz,"txt")
                off=12+sSz
                x=struct.unpack(">h",data[off:off+2])[0]/10.
                y=struct.unpack(">h",data[off+2:off+4])[0]/10.
                add_iter(hd, "dim", "%fx%f" % (x,y), off, 4, "txt")
                add_iter(hd, "unkn1", "", off+4,2,"txt")
                off+=8
        id_num = struct.unpack(">H",data[off-2:off])[0]
        add_iter(hd, "N=", id_num, off-2,2, ">H")

        for i in range(1,id_num+1):
                val=struct.unpack(">H",data[off+2*i-2:off+2*i])[0]
                add_iter(hd, "%d"%i, "Z%d" %val, off+2*i-2, 2, "txt")

def ListStyleHdl(hd,size,data,what):
        if hd.version==1:
                add_iter(hd, "unkn0", "", 6, 2, "txt")
                off = struct.unpack(">H",data[8:10])[0]
                id_num = struct.unpack(">H",data[10:12])[0]
                if off>12:
                        add_iter(hd, "unkn1", "", 12, off-12, "txt")
        else:
                id_num = struct.unpack(">H",data[6:8])[0]
                add_iter(hd, "unkn0", "", 8, 4, "txt")
                off=12
        for i in range(1,id_num+1):
                val = struct.unpack(">H",data[off+2*i-2:off+2*i])[0]
                add_iter(hd, "%d"%i, "Z%d" %val, off+2*i-2, 2, "txt")

def ColorRGBHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        val=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "r", "#%x"%val, off, 2, "txt")
        val=struct.unpack(">H",data[off+2:off+4])[0]
        add_iter(hd, "g", "#%x"%val, off+2, 2, "txt")
        val=struct.unpack(">H",data[off+4:off+6])[0]
        add_iter(hd, "b", "#%x"%val, off+4, 2, "txt")
        val=struct.unpack(">H",data[off+6:off+8])[0]
        add_iter(hd, "id", val, off+6, 2, ">H")
        val=struct.unpack(">H",data[off+8:off+10])[0]
        add_iter(hd, "unk0", val, off+8, 2, ">H")
        val=struct.unpack(">H",data[off+10:off+12])[0]
        add_iter(hd, "unk1", val, off+10, 2, ">H")

def ColorGreyHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        if hd.version >1:
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "r", "#%x"%val, off, 2, "txt")
                val=struct.unpack(">H",data[off+2:off+4])[0]
                add_iter(hd, "g", "#%x"%val, off+2, 2, "txt")
                val=struct.unpack(">H",data[off+4:off+6])[0]
                add_iter(hd, "b", "#%x"%val, off+4, 2, "txt")
                off+=6
        val=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "parent[id]", "Z%d" %val if val else "", off+2, 2, "txt")
        val=struct.unpack(">H",data[off+2:off+4])[0]
        add_iter(hd, "tint", "%f"%(val/65536.), off+2, 2, "txt")

def ColorCMYKHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        if hd.version >1:
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "r", "#%x"%val, off, 2, "txt")
                val=struct.unpack(">H",data[off+2:off+4])[0]
                add_iter(hd, "g", "#%x"%val, off+2, 2, "txt")
                val=struct.unpack(">H",data[off+4:off+6])[0]
                add_iter(hd, "b", "#%x"%val, off+4, 2, "txt")
                off+=6
        val=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "c", "#%x"%val, off, 2, "txt")
        val=struct.unpack(">H",data[off+2:off+4])[0]
        add_iter(hd, "m", "#%x"%val, off+2, 2, "txt")
        val=struct.unpack(">H",data[off+4:off+6])[0]
        add_iter(hd, "y", "#%x"%val, off+4, 2, "txt")
        val=struct.unpack(">H",data[off+6:off+8])[0]
        add_iter(hd, "k", "#%x"%val, off+6, 2, "txt")

def ColorPantoneHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        val=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "r", "#%x"%val, off, 2, "txt")
        val=struct.unpack(">H",data[off+2:off+4])[0]
        add_iter(hd, "g", "#%x"%val, off+2, 2, "txt")
        val=struct.unpack(">H",data[off+4:off+6])[0]
        add_iter(hd, "b", "#%x"%val, off+4, 2, "txt")

        add_iter(hd, "unkn", "", off+6, 16, "txt")

join_ids={
        0: "default",
        1: "bevel",
        2: "round"
}
cap_ids={
        0: "default",
        1: "round",
        2: "square"
}
def LineStyleHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        if hd.version>1:
                add_iter(hd, "unkn", "", off, 4, "txt")
                off+=4
        id=struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "color[id]", "Z%d" %id if id else "", off, 2, "txt")
        off+=2
        if what=="LineStyle":
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "dash[id]", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
        else:
                add_iter(hd, "pattern", "", off, 8, "txt")
                off+=8
        val=struct.unpack(">i",data[off:off+4])[0]
        add_iter(hd, "mitter", val/65536., off, 4, ">i")
        off+=4
        if hd.version==1:
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "width", val/10., off, 2, ">h")
                off+=2
        else:
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd, "width", val/65536./10., off, 4, ">i")
                off+=4
        if what=="LineStyle":
                val=struct.unpack(">b",data[off:off+1])[0]
                idtxt = "Unknown"
                if val in join_ids:
                        idtxt = join_ids[val]
                add_iter (hd, "join", "0x%02x (%s)"%(val,idtxt),off,1,">b")
                off+=1
                val=struct.unpack(">b",data[off:off+1])[0]
                idtxt = "Unknown"
                if val in cap_ids:
                        idtxt = cap_ids[val]
                add_iter (hd, "cap", "0x%02x (%s)"%(val,idtxt),off,1,">b")
                off+=1

def DashHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        if hd.version>1:
                add_iter(hd, "unkn", "", off, 4, "txt")
                off+=4
        id_num = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "N", id_num, off+2, 2, ">H")
        off+=2
        for i in range(1,id_num+1):
                val = struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "%d"%i, val/10., off, 2, ">h")
                off += 2

gradType_ids={
        1: "linear",
        2: "logarithm"
}
def FillStyleHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        if hd.version>1:
                add_iter(hd, "unkn", "", off, 4, "txt")
                off+=4
        if what=="TileStyle":
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "group[id]", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
                add_iter(hd, "unkn1", "", off, 8, "txt")
                off+=8
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd, "scaleX", val/65536., off, 4, ">i")
                off+=4
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd, "scaleY", val/65536., off, 4, ">i")
                off+=4
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "decalX", val/10., off, 2, ">h")
                off+=2
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "decalY", val/10., off, 2, ">h")
                off+=2
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "angle", val/10., off, 2, ">h")
                off+=2
                for i in range(1,4+1):
                        val=struct.unpack(">i",data[off:off+4])[0]
                        add_iter(hd, "rot%d"%i, val/65536., off, 4, ">i")
                        off+=4
                for i in range(1,2+1):
                        val=struct.unpack(">i",data[off:off+4])[0]
                        add_iter(hd, "trans%d"%i, val/65536./10., off, 4, ">i")
                        off+=4
        else:
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "color[id]", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
        if what=="GradientLinear" or what=="GradientRadial":
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "color2[id]", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
        if what=="GradientLinear":
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "angle", val/10., off, 2, ">h")
                off+=2
                val=struct.unpack(">b",data[off:off+1])[0]
                idtxt = "Unknown"
                if val in gradType_ids:
                        idtxt = gradType_ids[val]
                add_iter (hd, "gradType", "0x%02x (%s)"%(val,idtxt),off,1,">b")
                off+=1
        elif what=="GradientRadial" and hd.version>1:
                add_iter(hd, "unkn1", "", off, 6, "txt")
                off+=6
        elif what=="PatternFill":
                add_iter(hd, "pattern", "", off, 8, "txt")
                off+=8
        if hd.version==1:
                if what!="GradientRadial":
                        val=struct.unpack(">b",data[off:off+1])[0]
                        add_iter(hd, "overprint", "true" if val==1 else "false", off, 1, "txt")
                        off+=1
        elif what=="FillStyle":
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "overprint", "true" if val==1 else "false", off, 2, "txt")
                off+=2

def PSHdl(hd,size,data,what):
        off = HeaderStyleHdl(hd,size,data)
        if hd.version==1:
                stringSz=ord(data[off]);
                off+=1
        else:
                stringSz=size-12
                add_iter(hd, "unkn", "", off, 4, "txt")
                off+=4
        if stringSz > 0:
                (n, endOff) = rdata(data, off, '%ds'%stringSz)
                add_iter(hd, "val", n,off,stringSz,"txt")
        elif stringSz < 0:
                print("Can not read a PS string")
                add_iter(hd, "val", "###",off,size-off,"txt")

def JoinGroupHdl(hd,size,data,what):
        off = HeaderShapeHdl(hd,size,data)
        val=struct.unpack(">i",data[off:off+4])[0]
        add_iter(hd, "distance", val/65536., off, 4, ">i")
        off += 4
        for i in range(1,2+1):
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "child%d"%i, "Z%d" %id if id else "", off, 2, "txt")
                off+=2
def TransformGroupHdl(hd,size,data,what):
        off = HeaderShapeHdl(hd,size,data)
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "child", "Z%d"%id if id!=0 else "",off,2,"txt")
        off +=2
        add_iter(hd, "unkn", "", off, 2, "txt")
        off +=2
        TransformHdl(hd,26,data,what,off)
        off += 26
def BackgroundPictureHdl(hd,size,data,what):
        off = HeaderShapeHdl(hd,size,data)
        add_iter(hd, "unkn", "", off, 28, "txt")
        off +=28
        val = struct.unpack(">I",data[off:off+4])[0]
        add_iter(hd, "pictSize", val, off, 4, ">I")
        if val>0:
                add_iter(hd, "picture", val, off+4, val, ">I")
        off += 4+val
def PictureHdl(hd,size,data,what):
        off = HeaderShapeHdl(hd,size,data)
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "data", "Z%d"%id if id!=0 else "",off,2,"txt")
        off +=2
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "name", "Z%d"%id if id!=0 else "",off,2,"txt")
        off +=2
        add_iter(hd, "unkn1", "", off, 2, "txt")
        off +=2
        for i in range(1,2+1):
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "size%d"%i, val, off, 2, ">h")
                off+=2
        add_iter(hd, "unkn2", "", off, 4, "txt")
        off +=4
        TransformHdl(hd,26,data,what,off)
        off +=26
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "color", "Z%d"%id if id!=0 else "",off,2,"txt")
        off +=2
        for i in range(1,4+1):
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "dim%d"%i, val, off, 2, ">h")
                off+=2
        for i in range(1,4+1):
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd, "dimA%d"%i, val, off, 2, ">h")
                off+=2

def ShapeHdl(hd,size,data,what):
        off = HeaderShapeHdl(hd,size,data)
        canHaveMatrix=True
        hasDimension=True
        if what=="Path":
                canHaveMatrix=hasDimension=False
        elif what=="Line":
                canHaveMatrix=False
        if hd.version>1:
                id = struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "group", "Z%d"%id if id!=0 else "",off,2,"txt")
                off +=2
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "fillStyle", "Z%d"%id if id!=0 else "",off,2,"txt")
        off +=2
        id = struct.unpack(">H",data[off:off+2])[0]
        add_iter(hd, "lineStyle", "Z%d"%id if id!=0 else "",off,2,"txt")
        off +=2
        if hd.version>1:
                add_iter(hd, "unk", "", off, 4, "txt")
                off+=4
        if hasDimension:
                for i in range(1,4+1):
                        val=struct.unpack(">h",data[off:off+2])[0]
                        add_iter(hd, "dim%d"%i, val/10., off, 2, ">h")
                        off+=2
        if canHaveMatrix:
                off += 4+struct.unpack(">I",data[off:off+4])[0]
        if what=="Rectangle":
                for i in range(1,2+1):
                        val=struct.unpack(">h",data[off:off+2])[0]
                        add_iter(hd, "corner%d"%i, val/10., off, 2, ">h")
                        off+=2
        elif what=="Path":
                val=struct.unpack(">H",data[off:off+2])[0]
                idtxt=""
                if val&1:
                        idtxt+="closed,";
                if val&2:
                        idtxt+="even/odd,";
                add_iter(hd, "type", "0x%02x (%s)"%(val,idtxt), off, 2, ">H")
                off+=2
                N=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "N", N, off, 2, ">H")
                off+=2+16*N

justifyType_ids={
        0: "left",
        1: "center",
        2: "right",
        3: "all"
}
def TextHdl(hd,size,data,what):
        off = HeaderShapeHdl(hd,size,data)
        if hd.version==1:
                N=struct.unpack(">I",data[off:off+4])[0]
                add_iter(hd,"N",N,off,4,">I")
                off+=4+3*(N//2) # N + unknown flag
                add_iter(hd,"unkn","",off,4,"txt")
                off+=4
                txtSize=struct.unpack(">I",data[off:off+4])[0]
                add_iter(hd,"N[txt]",txtSize,off,4,">I")
                off+=4+txtSize
        else:
                add_iter(hd,"unkn","",off,14,"txt")
                off+=14
        for i in range(0,4):
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter(hd,"coord%d"%i,val/10., off, 2, ">h")
                off+=2
        if hd.version>1:
                val=struct.unpack(">h",data[off:off+2])[0]
                add_iter (hd, "f0", val,off,2,">h")
                off+=2
        TransformHdl(hd,26,data,what,off)
        off +=26
        if hd.version==1:
                for i in range(0,2):
                        val=struct.unpack(">i",data[off:off+4])[0]
                        add_iter(hd,"spacing%d"%i,val/10./65536., off, 4, ">i")
                        off+=4
                for i in range(0,2):
                        val=struct.unpack(">i",data[off:off+4])[0]
                        add_iter(hd,"scaling%d"%i,val/65536., off, 4, ">i")
                        off+=4
                val=struct.unpack(">b",data[off:off+1])[0]
                add_iter (hd, "f0", val,off,1,">b")
                off+=1
        val=struct.unpack(">b",data[off:off+1])[0]
        idtxt = "Unknown"
        if val in justifyType_ids:
                idtxt = justifyType_ids[val]
        add_iter (hd, "justify", "0x%02x (%s)"%(val,idtxt),off,1,">b")
        off+=1
        if hd.version==1:
                NPLC=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd,"N[plc]",txtSize,off,2,">H")
                off+=2+18*NPLC
        else:
                add_iter(hd,"unkn1","",off,11,"txt")
                off+=11
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd,"dSz?",val,off,2,">H")
                off+=2
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd,"textSz",val,off,2,">H")
                off+=2
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd,"textPos",val,off,2,">H")
                off+=2
                add_iter(hd,"unkn2","",off,6,"txt")
                off+=6
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "font", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd, "fontSize", val/65536.,off,4,">i")
                off+=4
                val=struct.unpack(">I",data[off:off+4])[0]
                if val==0xFFFE0000:
                        add_iter(hd, "leading", "solid",off,4,">I")
                elif val==0xFFFF0000:
                        add_iter(hd, "leading", "auto",off,4,">I")
                else:
                        add_iter(hd, "leading", val/65536.,off,4,">I")
                off+=4
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "f1", val,off,2,">H")
                off+=2
                val=struct.unpack(">H",data[off:off+2])[0]
                idtxt=""
                if val&1:
                        idtxt+="bold,"
                if val&2:
                        idtxt+="italic,"
                add_iter (hd, "flag1", "0x%02x (%s)"%(val,idtxt),off,2,">H")
                off+=2
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "color", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
                val=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "f2", val,off,2,">H")
                off+=2
                val=struct.unpack(">H",data[off:off+2])[0]
                idtxt = "Unknown"
                if val+1 in fontType_ids:
                        idtxt = fontType_ids[val+1]
                add_iter (hd, "type", "0x%02x (%s)"%(val,idtxt),off,2,">H")
                off+=2
                id=struct.unpack(">H",data[off:off+2])[0]
                add_iter(hd, "color2", "Z%d" %id if id else "", off, 2, "txt")
                off+=2
                add_iter(hd,"unkn3","",off,8,"txt")
                off+=8
                for i in range(0,2):
                        val=struct.unpack(">i",data[off:off+4])[0]
                        add_iter(hd,"spacing%d"%i,val/10./65536., off, 4, ">i")
                        off+=4
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd,"scaling",val/65536., off, 4, ">i")
                off+=4
                val=struct.unpack(">i",data[off:off+4])[0]
                add_iter(hd,"baseline",val/65536., off, 4, ">i")
                off+=4


fh12_ids = {
        "BackgroundPicture":BackgroundPictureHdl,
        "ColorCMY":ColorCMYKHdl,
        "ColorGrey":ColorGreyHdl,
        "ColorPantone":ColorPantoneHdl,
        "ColorRGB":ColorRGBHdl,
        "Dash":DashHdl,
        "FillStyle":FillStyleHdl,
        "GradientLinear":FillStyleHdl,
        "GradientRadial":FillStyleHdl,
        "Group":GroupHdl,
        "JoinGroup":JoinGroupHdl,
        "Line":ShapeHdl,
        "LineStyle":LineStyleHdl,
        "ListStyle":ListStyleHdl,
        "Oval":ShapeHdl,
        "Path":ShapeHdl,
        "PathPoint":PathPointHdl,
        "PatternLine":LineStyleHdl,
        "PatternFill":FillStyleHdl,
        "Picture":PictureHdl,
        "PSFill":PSHdl,
        "PSLine":PSHdl,
        "PSStyle":PSHdl,
        "Rectangle":ShapeHdl,
        "Root":RootHdl,
        "String":StringHdl,
        "Text":TextHdl,
        "TextPLC":TextPLCHdl,
        "TextString":TextStringHdl,
        "TileStyle":FillStyleHdl,
        "Transform":TransformHdl,
        "TransformGroup":TransformGroupHdl
}
