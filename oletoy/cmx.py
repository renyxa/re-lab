# Copyright (C) 2007,2010-2012	Valek Filippov (frob@df.ru)
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

import sys,struct
import gtk
from utils import *


# FIXME! spec claims it could be BigEndian if packed like RIFX

master_ids = {
	1:"Master Index Table",
	2:"Page Index Table",
	3:"Master Layer Table",
	4:"Procedure Index Table",
	5:"Bitmap Index Table",
	6:"Arrow Index Table",
	7:"Font Index Table",
	8:"Embedded File Index Table",
	10:"Thumbnail Section",
	15:"Outline Description Section",
	16:"Line Style Description Section",
	17:"Arrowheads Description Section",
	18:"Screen Description Section",
	19:"Pen Description Section",
	20:"Dot-Dash Description Section",
	21:"Color Description Section",
	22:"Color Correction Section",
	23:"Preview Box Section"
}

spot_ids = {
	0:"Default",
	1:"Dot",
	2:"Line",
	3:"User-defined"
}

clr_models = {
	0:"Invalid",
	1:"Pantone",
	2:"CMYK",
	3:"CMYK255",
	4:"CMY",
	5:"RGB",
	6:"HSB",
	7:"HLS",
	8:"BW",
	9:"Gray",
	10:"YIQ255",
	11:"LAB"
}

pal_types = {
	0:"Invalid",
	1:"Trumatch",
	2:"Pantone Process",
	3:"Pantone Spot",
	4:"Image",
	5:"User",
	6:"Custom Fixed"
}

cmds = {
	0x02:"Comment",
	0x09:"BeginPage",
	0x0A:"EndPage",
	0x0B:"BeginLayer",
	0x0C:"EndLayer",
	0x0D:"BeginGroup",
	0x0E:"EndGroup",
	0x11:"BeginProcedure",
	0x12:"EndSection",
	0x14:"BeginTextStream",
	0x15:"EndTextStream",
	0x16:"BeginEmbedded",
	0x17:"EndEmbedded",
	0x41:"DrawChars",
	0x42:"Ellipse",
	0x43:"PolyCurve",
	0x44:"Rectangle",
	0x45:"DrawImage",
	0x46:"BeginTextObject",
	0x47:"EndTextObject",
	0x48:"BeginTextGroup",
	0x49:"EndTextGroup",
	0x55:"SetCharStyle",
	0x56:"SimpleWideText",
	0x58:"AddClippingRegion",
	0x59:"RemoveLastClippingRegion",
	0x5A:"ClearClipping",
	0x5B:"PushMappingMode",
	0x5C:"PopMappingMode",
	0x5D:"SetGlobalTransfo",
	0x5E:"AddGlobalTransform",
	0x5F:"RestoreLastGlobalTransfo",
	0x62:"TextFrame",
	0x63:"BeginParagraph",
	0x64:"EndParagraph",
	0x65:"CharInfo",
	0x66:"Characters",
	0x67:"PushTint",
	0x68:"PopTint",
	0x6F:"JumpAbsolute",
}

# Used for rott
outline_spec = {
	0x01:"None",
	0x02:"Solid",
	0x04:"Dot-Dash",
	0x10:"Behind fill",
	0x20:"Scale pen"
	}

# Used for rott
outline_cap = {
	0:"Mitter Cap",1:"Round Cap",2:"Square Cap"
	}

outline_join = {
	0:"Mitter Join",0x10:"Round Join",0x20:"Bevel Join"
}

# Master Idx Table
def ixmr (hd,size,data):
	off = 0
	# Master ID
	mid = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Master ID", mid,off,2,"<H")
	off += 2
	# Max obj ID/table size
	size = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Size", size,off,2,"<H")
	off += 2
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2
	for i in range(rnum):
		idx_rid = struct.unpack("<H",data[off:off+2])[0]
		idtxt = "Unknown"
		if idx_rid in master_ids:
			idtxt = master_ids[idx_rid]
		add_iter (hd, "Idx Record ID", "0x%02x (%s)"%(idx_rid,idtxt),off,2,"<H")
		off += 2
		roff = struct.unpack("<i",data[off:off+4])[0]
		add_iter (hd, "Section Offset", roff,off,4,"<i")
		off += 4

# Page Idx Table
def ixpg (hd,size,data):
	off = 0
	# page records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2
	for i in range(rnum):
		size = struct.unpack("<H",data[off:off+2])[0]
		add_iter (hd, "Size", size,off,2,"<H")
		off += 2
		poff = struct.unpack("<i",data[off:off+4])[0]
		add_iter (hd, "Page Offset", poff,off,4,"<i")
		off += 4
		loff = struct.unpack("<i",data[off:off+4])[0]
		add_iter (hd, "Layer Offset", loff,off,4,"<i")
		off += 4
		toff = struct.unpack("<i",data[off:off+4])[0]
		add_iter (hd, "Thumbnail Offset", toff,off,4,"<i")
		off += 4
		roff = struct.unpack("<i",data[off:off+4])[0]
		add_iter (hd, "RefList Offset", roff,off,4,"<i")
		off += 4
		off += size - 16
		

# Layer Table
def ixtl (hd,size,data):
	off = 0
	# layer records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2
	# size
	size = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Size", size,off,2,"<H")
	off += 2
	# type
	ltype = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Type", ltype,off,2,"<H")
	off += 2
	# table offset
	loff = struct.unpack("<i",data[off:off+4])[0]
	add_iter (hd, "Offset", loff,off,4,"<i")


# Layer Idx Table
def ixlr (hd,size,data):
	off = 0
	# layer records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2
	# page number
	pnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Page number", pnum,off,2,"<H")
	off += 2
	# layer records
	for i in range(rnum):
		llen = struct.unpack("<H",data[off:off+2])[0]
		add_iter (hd, "Layer data size", llen,off,2,"<H")
		off += 2
		loff = struct.unpack("<i",data[off:off+4])[0]
		add_iter (hd, "Layer data offset", loff,off,4,"<i")
		off += 4
		namelen = struct.unpack("<H",data[off:off+2])[0]
		add_iter (hd, "Name Length", namelen,off,2,"<H")
		off += 2
		name = data[off:off+namelen]
		add_iter (hd, "Layer name", name,off,namelen,"txt")
		off += namelen


# Screen description
def rscr (hd,size,data):
	# FIXME! Tags!
	off = 0
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2
	# tag type
	ttype = ord(data[off])
	add_iter (hd, "Tag type", ttype,off,1,"B")
	off += 1
	# tag size
	tsize = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Tag size", tsize,off,2,"<H")
	off += 2
	# spot
	spot = struct.unpack("<H",data[off:off+2])[0]
	sptxt = "Unknown"
	if spot in spot_ids:
		sptxt = spot_ids[spot]
	add_iter (hd, "Spot", "0x%02x (%s)"%(spot,sptxt),off,2,"<H")
	off += 2
	# "Frequency" (lines per inch)
	lpi = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Lines per inch", lpi,off,2,"<H")
	off += 2
	# User func ???
	uf = struct.unpack("<I",data[off:off+4])[0]
	add_iter (hd, "User function", uf,off,4,"<I")
	off += 4
	# Angle
	ang = struct.unpack("<I",data[off:off+4])[0]
	add_iter (hd, "Angle", ang/1000000,off,4,"<I")
	off += 4
	# Overprint
	add_iter (hd, "Overprint", ord(data[off]),off,1,"B")

def clr_desc(hd,data,cm,off,parent):
	if cm == 1:
		pid = struct.unpack("<H",data[0:2])[0]
		pdens = struct.unpack("<H",data[2:4])[0]
		add_iter (hd, "Pantone ID", pid,off,2,"<H",0,0,parent)
		add_iter (hd, "Pantone Dencity", pdens,off+2,2,"<H",0,0,parent)
	elif cm == 2 or cm == 3 or cm == 4:
		add_iter (hd, "CMY(K) 100/255", d2hex(data[0:4]),off,4,"txt",0,0,parent)
	elif cm == 5:
		add_iter (hd, "RGB", d2hex(data[0:3]),off,3,"rgb",0,0,parent)
# FIXME! add other palletes

def rclr (hd,size,data):
	off = 0
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2 #
	for i in range(rnum):
		# tag type
		titer = add_iter (hd, "Color ref#%02x"%i, None,off,0,"")
		while off < len(data):
			ttype = ord(data[off])
			if ttype != 0xff:
				off += 1
				# tag size
				tsize = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Tag type/size", "%02x/%02x"%(ttype,tsize),off,3,"<BH",0,0,titer)
				off += 2
				if ttype == 1:
					# Colour Model
					cm = ord(data[off])
					add_iter (hd, "Colour Model", "%02x (%s)"%(cm,key2txt(cm,clr_models)),off,1,"B",0,0,titer)
					off += 1
					# Palette Type
					pt = ord(data[off])
					add_iter (hd, "Palette Type", "%02x (%s)"%(pt,key2txt(pt,pal_types)),off,1,"B",0,0,titer)
					off += 1
				elif ttype == 2:
					clr_desc(hd,data[off:],cm,off,titer)
					off += tsize-3
				else:
					add_iter (hd, "Tag data", "",off,tsize-3,"<H",0,0,titer)
					off += tsize-3
			else:
				off += 1
				break

def rott (hd,size,data):
	off = 0
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2 #
	for i in range(rnum):
		# tag type
		titer = add_iter (hd, "Outline ref#%02x"%i, None,off,0,"")
		while off < len(data):
			ttype = ord(data[off])
			off += 1
			if ttype != 0xff:
				# tag size
				tsize = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Tag type/size", "%02x/%02x"%(ttype,tsize),off-1,3,"<BH",0,0,titer)
				off += 2
				spec = ord(data[off])
				add_iter (hd, "Spec", "%02x (%s)"%(spec,key2txt(spec,outline_spec)),off,1,"B",0,0,titer)
				cj = ord(data[off+1])
				c = key2txt(cj,outline_cap)
				c += "/"+key2txt(cj&0xF0,outline_join)
				add_iter (hd, "Cap/Join", "%02x (%s)"%(cj,c),off+1,1,"B",0,0,titer)
				off += 2
			else:
				break

def rpen (hd,size,data):
	off = 0
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2 #
	for i in range(rnum):
		# tag type
		titer = add_iter (hd, "Pen ref#%02x"%i, None,off,0,"")
		while off < len(data):
			ttype = ord(data[off])
			off += 1
			if ttype != 0xff:
				# tag size
				tsize = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Tag type/size", "%02x/%02x"%(ttype,tsize),off-1,3,"<BH",0,0,titer)
				off += 2
				w = struct.unpack("<I",data[off:off+4])[0]
				add_iter (hd, "Width", w,off,4,"<I",0,0,titer)
				off += 4
				a = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Aspect", a,off,2,"<H",0,0,titer)
				off += 2
				a = struct.unpack("<I",data[off:off+4])[0]
				add_iter (hd, "Angle", a,off,4,"<I",0,0,titer)
				off += 4
				xft = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "XForm type", xft,off,2,"<H",0,0,titer)
				off += 2
				# Type: 1 - Identity, 2 - General
				if xft == 2:
					for j in range(6):
						v = struct.unpack("<d",data[off:off+8])[0]
						add_iter (hd, "m%d"%j, v,off,8,"<d",0,0,titer)
						off += 8
			else:
				break

def rotl (hd,size,data):
	off = 0
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2 #
	for i in range(rnum):
		# tag type
		titer = add_iter (hd, "Outline ref#%02x"%i, None,off,0,"")
		while off < len(data):
			ttype = ord(data[off])
			off += 1
			if ttype != 0xff:
				# tag size
				tsize = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Tag type/size", "%02x/%02x"%(ttype,tsize),off-1,3,"<BH",0,0,titer)
				off += 2
				lst = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Line style#", lst,off,2,"<H",0,0,titer)
				off += 2
				scr = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Screen#", scr,off,2,"<H",0,0,titer)
				off += 2
				clr = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Color#", clr,off,2,"<H",0,0,titer)
				off += 2
				arr = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Arrow#", arr,off,2,"<H",0,0,titer)
				off += 2
				pen = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Pen#", pen,off,2,"<H",0,0,titer)
				off += 2
				dot = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Dash-dot#", dot,off,2,"<H",0,0,titer)
				off += 2
			else:
				break

# CMX header
def cont (hd,size,data):
	off = 0
	# "{Corel Binary Meta File}"
	add_iter (hd, "ID", data[0:24],0,32,"txt")
	off += 32
	# "Windows 3.1" or "Macintosh"
	add_iter (hd, "OS", data[off:off+11],off,16,"txt")
	off += 16
	# byte order: "2" - LE, "4" - BE
	bo = data[off]
	add_iter (hd, "Byte Order", data[off:off+4],off,4,"<I")
	off += 4
	# coord size: "2" - 16 bits, "4" - 32 bits
	add_iter (hd, "Coord Size", data[off:off+2],off,2,"<H")
	off += 2
	# version major: "1" - 16 bits, "2" - 32 bits
	add_iter (hd, "Version maj", data[off:off+4],off,4,"<I")
	off += 4
	# version minor: "0"
	add_iter (hd, "Version min", data[off:off+4],off,4,"<I")
	off += 4
	# coord units: 0x23 - mm, 0x40 - inches
	add_iter (hd, "Coord Units", struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	# precision factor
	add_iter (hd, "Precision", struct.unpack("<d",data[off:off+8])[0],off,8,"<d")
	off += 8
	# not used "Option", "FrgnKey", "Capability"
	add_iter (hd, "Not used", "",off,12,"txt")
	off += 12
	# index section offset
	add_iter (hd, "Idx Section Offset", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# info section offset
	add_iter (hd, "Info Section Offset", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# Thumbnail section offset
	add_iter (hd, "Thumbnail Section Offset", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# min X coord in the file
	add_iter (hd, "Min X coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# max Y coord in the file
	add_iter (hd, "Max Y coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# max X coord in the file
	add_iter (hd, "Max X coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# min Y coord in the file
	add_iter (hd, "Min Y coord", struct.unpack("<i",data[off:off+4])[0],off,4,"<i")
	off += 4
	# num of instructions in pages
	add_iter (hd, "# of instructions", struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	# reserved
	add_iter (hd, "Reserved", "",off,64,"txt")
	off += 64

grps = {
	0x16:0,0xd:0,0xb:0,0x9:0,0x63:0,0x11:0,0x48:0,0x46:0,0x14:0,
	0x17:1,0xe:1,0xc:1,0xa:1,0x64:1,0x12:1,0x49:1,0x47:1,0x15:1
	}

def parse_page(page,data,old_offset,f_iter):
	offset = 0
	corr = 0
	p_iter = f_iter
#	print "CMX parse page"
	while offset < len(data) - 4:
		csize = struct.unpack("<h",data[offset:offset+2])[0]
		if csize < 0:
			csize = struct.unpack("<I",data[offset+2:offset+6])[0]
			corr = 4;
		ctype = struct.unpack("<h",data[offset+corr+2:offset+corr+4])[0]
		if ctype < 0:
			ctype = - ctype
		c_iter = add_pgiter(page,"%s (%d)"%(key2txt(ctype,cmds),ctype),"cmx","page",data[offset+corr+4:offset+csize],p_iter)
		if ctype in grps:
			if grps[ctype] == 1:
				# Ends
				p_iter = t_iter
			else:
				t_iter = p_iter
				p_iter = c_iter
		# JumpAbsolute
		if ctype == 0x6f:
			# CMX version 1
			# new_offset = struct.unpack("<I",data[offset+corr+4:offset+corr+8])[0]
			# CMX version 2
			new_offset = struct.unpack("<I",data[offset+corr+7:offset+corr+11])[0]
			offset = new_offset - old_offset
		else:
			offset += csize

cmx_ids = {
	"cont":cont,
	"ixlr":ixlr,"ixtl":ixtl,"ixpg":ixpg,"ixmr":ixmr,
	"rscr":rscr,"rclr":rclr,"rotl":rotl,"rott":rott,
	"rpen":rpen}

