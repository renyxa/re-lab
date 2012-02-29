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
import gobject
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
		if master_ids.has_key(idx_rid):
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
	if spot_ids.has_key(spot):
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


def rclr (hd,size,data):
	off = 0
	# records count
	rnum = struct.unpack("<H",data[off:off+2])[0]
	add_iter (hd, "Rec. count", rnum,off,2,"<H")
	off += 2 #
	for i in range(rnum):
		# tag type
		while off < len(data):
			ttype = ord(data[off])
			if ttype != 0xff:
				add_iter (hd, "Tag type", ttype,off,1,"B")
				off += 1
				# tag size
				tsize = struct.unpack("<H",data[off:off+2])[0]
				add_iter (hd, "Tag size", tsize,off,2,"<H")
				off += 2
				if ttype == 1:
					# Colour Model
					cm = ord(data[off])
					add_iter (hd, "Colour Model", cm,off,1,"B")
					off += 1
					# Palette Type
					add_iter (hd, "Palette Type", ord(data[off]),off,1,"B")
					off += 1
				else:
					add_iter (hd, "Tag data", "",off,tsize-3,"<H")
					off += tsize-3
			else:
				off += 1
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



cmx_ids = {
	"cont":cont,
	"ixlr":ixlr,"ixtl":ixtl,"ixpg":ixpg,"ixmr":ixmr,
	"rscr":rscr,"rclr":rclr}

