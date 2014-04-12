# Copyright (C) 2007,2010-2014	Valek Filippov (frob@df.ru)
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

rectypes = {1:"Background",2:"FaceName",3:"Version",4:"ID",\
			5:"Overlay",6:"Polygon",7:"Symbol",8:"Text",9:"Color",\
			10:"ColorFlag",11:"Preview (DIB)",14:"View",15:"OldGrid",16:"CurrOverlay",\
			17:"Visible",18:"Comment",19:"Info",20:"Bitmap",21:"Font",\
			22:"Grid",23:"OverlayName",24:"Dimensions",25:"Resolution",\
			26:"Ruler",27:"Page",28:"Pattern",29:"Locked",30:"Gradient",\
			31:"TextHdr",32:"Band",33:"SymbolVersion",34:"TextPara",\
			35:"ColorTable",36:"TextExtra",37:"MaxLinkID",\
			44:"ChartSkipSymbols",
			51:"Multichunk OBJ",52:"DataChunk",56:"Layer",
			60:"Group",
			254:"EOF",255:"RecordVersion"}


shapetypes = {
		0:'0 (Elliptic Arc)',
		1:'1 (Polygon)',
		2:'2 (Group)',
		3:'3 (Ellipse)',
		5:'5 (Scale line)',
		6:'6 (Line)',
		8:'8 (Polyline)',
		9:'9 (Pie)',
		10:'10 (Rectangle)',
		11:'11 (RoundRect)',
		13:'13 (Ellipse)',
		14:'14 (Arc)',
		15:'15 (Parabolic Line)',
		16:'16 (Quadratic Curve)',
		17:'17 (Connect)',
		18:'18 (Parabolic Line)',
		19:'19 (Quadratic Spline)',
		20:'20 (Polygon)',
		22:'22 (Bitmap ?)',
		23:'23 (Freeline)',
		24:'24 (Bezier)',
		25:'25 (Rich Text Block)',
		26:'26 (Virtual Bitmap)',
		27:'27 (Clip Path)',
		28:'28 (Tiled Clip Path)',
		29:'29 (Text on Curve?)',}

def sym5_connect:
	# 0x2b -- num of connected symbols
	pass

def symbolversion(page,rdata):
	page.version = struct.unpack('<H', rdata[0:2])[0]


def symbol5(hd,rdata):
		#1,1,2-2,2-2-2-2,2,2,2,1-1-1-1,2,4,4)
		(stype,flags,posx,posy,boxx,boxy,boxdx,boxdy,angle,xscale,yscale,color1,color2,color3,color4,handle,rnext,prev) =struct.unpack("<BBhhhhhhHHHBBBBHII",rdata[0:34])
		if shapetypes.has_key(stype):
			shtype = shapetypes[stype]
		else:
			shtype = stype
		# Name, Value, Offset, Length, Type
		leaves = [
		('Type',shtype,0,1,"B"),
		('Flags',flags,1,1,"B"),
		('Pos X',posx,2,2,"<h"),
		('Pos Y',posy,4,2,"<h"),
		('Box X',boxx,6,2,"<h"),
		('Box Y',boxy,8,2,"<h"),
		('Box dX',boxdx,10,2,"<h"),
		('Box dY',boxdy,12,2,"<h"),
		('Angle',angle,14,2,"<H"),
		('XScale',xscale,16,2,"<H"),
		('YScale',yscale,18,2,"<H"),
		('Color ',"#%02x%02x%02x%02x"%(color1,color2,color3,color4),20,4,"BBBB"),
		('Handle',handle,24,2,"<H"),
		('Next',rnext,26,4,"<I"),
		('Prev',prev,30,4,"<I")]

		for i in leaves:
			add_iter(hd,"%s"%(i[0]),"%s"%(i[1]),i[2],i[3],i[4])


def hd_symbol (hd,rdata,page):
	if page.version == 5:
		symbol5(hd,rdata)

recfuncs = {7:hd_symbol}

def open (page,buf,parent,off=0):
	symversion = 0
	offset = off
	while offset < len(buf):
		rlength = ord(buf[offset])
		offset += 1
		if rlength == 0xff:
			rlength = struct.unpack('<H', buf[offset:offset+2])[0]
			offset += 2
		rtype = ord(buf[offset])
		offset += 1
		rdata = ""
		if rtype == 20 or (rtype > 96 and rtype < 160):
			rdata = buf[offset:offset+rlength]
		else:
			while len(rdata) < rlength:
				tv = buf[offset]
				offset+=1
				if ord(tv) == 0xff:
					vlen = ord(buf[offset])
					offset += 1
					vval = buf[offset]
					offset += 1
					for i in range(vlen):
						rdata = rdata + vval
				else:
					rdata = rdata + tv
		rname = rtype
		if rectypes.has_key(rtype):
			rname = rectypes[rtype]
		else:
			print "DRW: unknown record type",rtype
		if rtype == 4: # ID
			rname += " [%s]"%rdata[:0x10]
		if rtype == 7: # Symbol
			stype = ord(rdata[0])
			sname = " (%02x)"%stype
			if stype in shapetypes.keys():
				sname = " " +shapetypes[stype]
			rname += sname
		riter = add_pgiter(page, rname, "drw",rtype,rdata,parent) 
		if rtype == 33:
			symbolversion(page,rdata)


