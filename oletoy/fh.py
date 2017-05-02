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

import sys,struct,tree,zlib,gtk,gobject
from utils import *


# 3 - rgb
# 4 - cmyk
# 7 - pantone solid uncoated/mate
# 9 - hexachrome

palette = {
	3:"RGB",
	4:"CMYK",
	7:"Pantone",
	9:"Hexachrome",
}

agd_rec = {
	0x0e11:("FontName","recid"),
	0x0e1b:("Style",">I"),
	0x0e24:("Size",">I")
}

vmp_rec = {
	0x0321:("Name","recid"),
	0x065b:("uid","?"),
	0x15e3:("Txt Align","enum(txtalign)"), # 0 left, 1 right, 2 center, 3 justify,
	0x15ea:("?","?"),
	0x15f2:("?","?"),
	0x15f9:("?","?"),
	0x1604:("?","?"),
	0x160b:("?","?"),
	0x1614:("?","?"),
	0x161c:("Spc % Letter Max","?"),
	0x1624:("Spc % Word Max","?"),
	0x162b:("?","?"),
	0x1634:("Spc % Letter Min","?"),
	0x163c:("Spc % Word Min","?"),
	0x1644:("?","?"),
	0x164c:("Spc % Letter Opt","?"),
	0x1654:("Spc % Word Opt","?"),
	0x165c:("?","?"),
	0x1664:("?","?"),
	0x166b:("?","?"),
	0x1674:("?","?"),
	0x167c:("?","?"),
	0x1684:("ParaSpc Below","?"),
	0x168c:("ParaSpc Above","?"),
	0x1691:("TabTable ID","?"),
	0x169c:("BaseLn Shift" ,"?"),
	0x16a2:("?","?"),
	0x16aa:("?","?"),
	0x16b1:("TEffect ID","?"),  # teffect ID
	0x16b9:("Txt Color ID","?"),
	0x16c1:("Font ID","?"),
	0x16c9:("?","?"),
	0x16d4:("Hor Scale %","?"),
	0x16dc:("Leading","?"),
	0x16e3:("Leading Type","enum(leadtypes)"), # 0 +, 1 =, 2 %
	0x16ec:("Rng Kern %","?"),
	0x16f1:("?","?"),
	0x16fb:("?","?"),
	0x1729:("?","?"),
	0x1734:("Font Size","?"),
	0x1739:("Font Name","?"), # id of ustring w font name
	0x1743:("?","?"),
	0x1749:("Next style?","?"),
	0x1c7c:("Page Start X","?"),
	0x1c84:("Page Start Y","?"),
	0x1c24:("Page Start X","?"), # page start X?  same for 1c7c
	0x1c2c:("Page Start Y","?"), # page start Y?  same for 1c84
	0x1c34:("Page W","?"),
	0x1c3c:("Page H","?"),
	0x1c43:("?","?"),
	0x1c4c:("?","?"),
	0x1c51:("?","?"),
	0x1c71:("?","?"), # guides ID?
	0x1c7c:("?","?"),
	0x1c84:("?","?"),
	0x1c89:("?","?"), # Group ID?
	}

teff_rec = {
	0x1302:("Display Border",""),
	0x130c:("Inset B",""),
	0x131c:("Dimension H",""),
	0x134c:("Dimension L",""),
	0x1354:("Inset L",""),
	0x13ac:("Inset R",""),
	0x13dc:("Dimension T",""),
	0x13e4:("Inset T",""),
	0x140c:("Dimension W",""),
	0x1369:("LineTable","recid"),
	0x1a91:("Effect Name","?"),
	0x1ab9:("Underline Clr ID",""),  # underline color ID
	0x1ac1:("Underline Dash ID",""),  # underline dash ID
	0x1acc:("Underline Position","?"), #"BG Width", #2.2
	0x1ad4:("Stroke Width","?"), #2.2
#	0x1adb:"Count",
	}

def readid (data,off=0):
	# temporary add FFFE
	if data[off:off+2] == '\xFF\xFF':
		rid = 0x1ff00 - rdata(data,off+2,">H")[0]
		l = 4
	else:
		rid = rdata(data,off,">H")[0]
		l = 2
	return l,rid

def getName (id, page):
	if id in page.appdoc.recs:
		return "%s"%page.appdoc.recs[id][1]
	return "%02x[Name]"%id

def getZone (id, page):
	if id==0:
		return "_"
	type,str=get_typestr(page,id)
	return "%02x[%s]"%(id,type if str=="" else str)

def hdVMpObj(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if key == 2:
			at = d2hex(data[shift+4:shift+6])
		else:
			at = d2hex(data[shift+4:shift+8])
		if rec in vmp_rec:
			rname = vmp_rec[rec][0]
			if vmp_rec[rec][1] == "recid":
				a = readid(data,shift+4)[1]
				at = getName(a,page)
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,at,shift,6,"txt")
			shift+=4
			L,rid,fmt = read_recid(data,offset+shift)
			shift += L
		else:
			add_iter (hd,rname,at,shift,8,"txt")
			shift+=8

def hdTString(hd,data,page):
	offset = 0
	num = struct.unpack('>h', data[offset+2:offset+4])[0]
	offset = 0x14
	for i in range(num):
		L,rid1,fmt = read_recid(data,offset)
		elemtype,typestr = get_typestr(page,rid1)
		iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset,L,fmt)
		offset += L

def hdRadialFill(hd,data,page):
	offset = 0
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color0", "%02x"%rid, offset, L, fmt)
	offset+=L
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color1", "%02x"%rid, offset, L, fmt)
	offset+=L
	val = struct.unpack('>i', data[offset:offset+4])[0]
	add_iter (hd,'cX',val/65536.,offset,4,">i")
	offset+=4
	val = struct.unpack('>i', data[offset:offset+4])[0]
	add_iter (hd,'cY',val/65536.,offset,4,">i")
	offset+=4
	for i in range(2): # 0
		val = struct.unpack('>h', data[offset:offset+2])[0]
		add_iter (hd,"f%d"%i,val,offset,2,">h")
		offset+=2

def hdTaperedFill (hd,data,page):
	offset=0
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color0", "%02x"%rid, offset, L, fmt)
	offset+=L
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color1", "%02x"%rid, offset, L, fmt)
	offset+=L
	val=struct.unpack('>i', data[offset:offset+4])[0]
	add_iter(hd, "angle", val/65536., offset, 4, ">i")
	offset+=4
	val=struct.unpack('>i', data[offset:offset+4])[0]
	add_iter(hd, "f0", val, offset, 4, ">i")
	offset+=4

def hdTaperedFillX (hd,data,page):
	offset=0
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color0", "%02x"%rid, offset, L, fmt)
	offset+=L
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color1", "%02x"%rid, offset, L, fmt)
	offset+=L
	val=struct.unpack('>i', data[offset:offset+4])[0]
	add_iter(hd, "angle", val/65536., offset, 4, ">i")
	offset+=4
	for i in range(0,2):
		val=struct.unpack('>i', data[offset:offset+4])[0]
		add_iter(hd, "f%d"%i, val, offset, 4, ">i")
		offset+=4
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "MultiColor", "%02x"%rid, offset, L, fmt)
	offset+=L

def hdTEffect(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if teff_rec.has_key(rec):
			rname = teff_rec[rec][0]
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,d2hex(data[shift+4:shift+6]),shift,6,"txt")
			shift+=4
			L,rid,fmt = read_recid(data,offset+shift)
			shift += L
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8

def get_typestr(page, id):
	elemtype = page.dict[page.reclist[id-1]]
	typestr = ""
	if "List" in elemtype:
		try:
			itr = page.model.iter_nth_child(page.diter,id-1)
			itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
			if itrtype == 0:
				t,r,fmt = read_recid(page.model.get_value(itr,3),0xc)
				typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
			elif itrtype in page.dict:
				typestr = " -> (%s)"%(page.dict[itrtype])
		except:
			pass
	return elemtype,typestr

def hdTFOnPath(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	L,rid1,fmt = read_recid(data,offset+8)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset+8,L,fmt)
	offset += L
	L,rid1,fmt = read_recid(data,offset+8)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset+8,L,fmt)
	offset += L+8
	for i in range(3):
		L,rid1,fmt = read_recid(data,offset+8)
		elemtype,typestr = get_typestr(page,rid1)
		iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset+8,L,fmt)
		offset += L
	offset -= 18
	shift = 26
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if teff_rec.has_key(rec):
			rname = teff_rec[rec][0]
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,d2hex(data[shift+4:shift+6]),shift,6,"txt")
			shift+=4
			L,rid,fmt = read_recid(data,offset+shift,fmt)
			shift += L
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8

def hdTileFill(hd,data,page):
	offset = 0
	L,recid,fmt = read_recid(data,offset)
	add_iter (hd,'XForm ID',"%02x"%recid,offset,L,fmt)
	offset += L
	L,recid,fmt = read_recid(data,offset)
	add_iter (hd,'Group ID',"%02x"%recid,offset,L,fmt)
	offset += L
	offset += 8
	x1 = cnvrt22(data[offset:offset+4])
	add_iter (hd,'X1',x1*100,offset,4,">HH")
	offset += 4
	y1 = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Y1',y1*100,offset,4,">HH")
	offset += 4
	x2 = cnvrt22(data[offset:offset+4])
	add_iter (hd,'X2',x2,offset,4,">HH")
	offset += 4
	y2 = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Y2',y2,offset,4,">HH")
	offset += 4
	ang = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Angle',ang,offset,4,">HH")


def hdFilterAttributeHolder(hd,data,page):
	offset = 0
	offset += 2
	L,recid,fmt = read_recid(data,offset)
	add_iter (hd,'Filter ID',"%02x"%recid,offset,L,fmt)
	offset += L
	L,recid,fmt = read_recid(data,offset)
	add_iter (hd,'GraphicStyle ID',"%02x"%recid,offset,L,fmt)


def hdFHTail(hd,data,page):
	offset = 0
	L,recid,fmt = read_recid(data,0)
	add_iter (hd,'Block ID',"%02x"%recid,offset,L,fmt)
	offset += L
	L,recid,fmt = read_recid(data,offset)
	add_iter (hd,'PropLst ID',"%02x"%recid,offset,L,fmt)
	offset += L
	L,recid,fmt = read_recid(data,offset)
	add_iter (hd,"Default Font ??",getName(recid,page),offset,L,fmt)
	x1 = struct.unpack('>H', data[0x1a:0x1c])[0]
	x1f = struct.unpack('>H', data[0x1c:0x1e])[0]
	y1 = struct.unpack('>H', data[0x1e:0x20])[0]
	y1f = struct.unpack('>H', data[0x20:0x22])[0]
	x2 = struct.unpack('>H', data[0x32:0x34])[0]
	x2f = struct.unpack('>H', data[0x34:0x36])[0]
	y2 = struct.unpack('>H', data[0x36:0x38])[0]
	y2f = struct.unpack('>H', data[0x38:0x3a])[0]
	add_iter (hd,'Page Max X',"%.4f"%((x1+x1f/65536.)/72.),0x1a,4,"txt")
	add_iter (hd,'Page Max Y',"%.4f"%((y1+y1f/65536.)/72.),0x1e,4,"txt")
	add_iter (hd,'Page W',"%.4f"%((x2+x2f/65536.)/72.),0x32,4,"txt")
	add_iter (hd,'Page H',"%.4f"%((y2+y2f/65536.)/72.),0x36,4,"txt")


def hdFWBlurFilter(hd,data,page):
	offset = 0
	offset += 3
	add_iter (hd,'Basic (1)/Gaussian (0)',ord(data[offset]),offset,1,"B")
	offset += 1
	brad = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Radius (Basic)',brad,offset,4,">I")
	offset += 4
	grad = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Radius (Gaussian)',grad,offset,4,">HH")


def hdFWGlowFilter(hd,data,page):
	offset = 0
	l,rid,fmt = read_recid(data,0)
	add_iter (hd,'Color',getName(rid,page),0,l,fmt)
	offset += l
	offset += 3
	add_iter (hd,'Inner',ord(data[offset]),offset,1,"B")
	offset += 1
	w = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Width',w,offset,4,">HH")
	offset += 4
	offset += 2
	cntrst = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Contrast',cntrst,offset,2,">H")
	offset += 2
	sm = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Smoothness',sm,offset,4,">HH")
	offset += 4
	dstr = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Distribution? <|>',dstr,offset,2,">H")


def hdFWShadowFilter(hd,data,page):
	offset = 0
	l,rid,fmt = read_recid(data,0)
	add_iter (hd,'Color',getName(rid,page),0,l,fmt)
	offset += l
	offset += 2
	add_iter (hd,'Knock out',ord(data[offset]),offset,1,"B")
	offset += 1
	add_iter (hd,'Inner',not(ord(data[offset])),offset,1,"B")
	offset += 1
	d = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Distribution? <|>',d,offset,4,">HH")
	offset += 4
	offset += 2
	cntrst = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Contrast',cntrst,offset,2,">H")
	offset += 2
	sm = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Smoothness',sm,offset,4,">HH")
	offset += 4
	offset += 2
	ang = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Angle',ang,offset,2,">H")



def hdParagraph(hd,data,page):
	offset = 0
	num = struct.unpack('>h', data[offset+2:offset+4])[0]
	offset = 6
	L,rid1,fmt = read_recid(data,offset)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset,L,fmt)
	offset += L
	L,rid1,fmt = read_recid(data,offset)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset,L,fmt)
	offset += L
	for i in range(num):
		numchar = struct.unpack(">H",data[offset:offset+2])[0]
		L,rid1,fmt = read_recid(data,offset+2)
		elemtype,typestr = get_typestr(page,rid1)
		iter = add_iter (hd,'Rfr',"Start char: %d, Style: %02x (%s)%s"%(numchar,rid1,elemtype,typestr),offset,L,fmt,offset2=offset+2,length2=2)
		offset += L + 22

def hdHaftone(hd,data,page):
	offset = 0
	# 0-2 -- link to MName with "Screen" string
	# 2-4.4-6 -- angle
	# 6-8 -- Frequency

pts_types = {0:"corner",1:"connector",2:"curve"}
def hdPath(hd,data,page):
	offset = 0
	# 15 -- flatness
	# 19 -- 0 no Even/Odd no Closed, 1 closed, 2 Even/Odd, 3 Even/Odd + Closed
	# ptype+1 -- 0x1b -- automatic, 0x9 -- no authomatic

	#0x1ff00 - recid
	L,recid,fmt = read_recid(data,2)
	if L == 4:
		recid = 0x1ff00 - recid
	add_iter (hd,'Graphic Style ID',"%02x"%recid,2,2,">H")
	shift = offset + 18
	if page.version > 3:
		offset += 4
		shift += 4
	numpts = struct.unpack('>H', data[offset+16:offset+18])[0]
	add_iter (hd, "N", numpts, offset+16, 2, ">H");

def hdArrowPath(hd,data,page):
	offset = 0 if hd.version<=8 else 20
	numpts = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd, "N", numpts, offset, 2, ">H");
	offset += 2
	if hd.version <=8:
		offset += 20
	if hd.version > 3:
		offset += 4

def hdPathPoint(hd,data,page):
	ptype = ord(data[1])
	ptext = "Unknown"
	if ptype in pts_types:
		ptext = pts_types[ptype]
	add_iter (hd,'Type',"%d (%s)"%(ptype,ptext),1,1,"B")
	for pt in range(3):
		shift =pt*8
		x = struct.unpack('>i', data[shift+3:shift+7])[0]
		y = struct.unpack('>i', data[shift+7:shift+11])[0]
		add_iter (hd,'X%d'%pt,"%.4f"%(x/65536.),shift+3,4,"txt")
		add_iter (hd,'Y%d'%pt,"%.4f"%(y/65536.),shift+7,4,"txt")

def hdPathText(hd,data,page):
	off=0
	for i in range(2):
		l,rid,fmt = read_recid(data,off)
		add_iter (hd,"elemProp" if i== 0 else "layer",getZone(rid,page),off,l,fmt)
		off+=l
	for i in range(4):
		val = struct.unpack('>H', data[off:off+2])[0]
		add_iter (hd,"txtSize" if i==1 else "f%d"%i,val,off,2,">H")
		off += 2
	for i in range(2):
		l,rid,fmt = read_recid(data,off)
		type,str=get_typestr(page,rid)
		add_iter (hd,"text" if i== 0 else "form",getZone(rid,page),off,l,fmt)
		off+=l

def hdAGDFont(hd,data,page):
	offset = 0
	num = struct.unpack('>h', data[offset+4:offset+6])[0]
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if key == 2:
			at = d2hex(data[shift+4:shift+6])
		else:
			at = d2hex(data[shift+4:shift+8])
		if rec in agd_rec:
			rname = agd_rec[rec][0]
			if agd_rec[rec][1] == "recid":
				a = readid(data,shift+4)[1]
				at = getName(a,page)
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,at,shift,6,"txt")
			shift+=4
			L,rid,fmt = read_recid(data,offset+shift)
			shift += L
		else:
			add_iter (hd,rname,at,shift,8,"txt")
			shift+=8

def hdLinearFill(hd,data,page):
	offset = 0
	res,rid,fmt = read_recid(data,offset)
	add_iter (hd,"Color 1","%02x"%rid,0,res,fmt)
	L,rid,fmt = read_recid(data,offset+res)
	add_iter (hd,"Color 2","%02x"%rid,res,L,fmt)
	res += L
	hndl = struct.unpack(">H",data[res:res+2])[0]
	add_iter (hd,"Handle 1 (ang)",hndl,res,2,">H")
	res += 4
	res += 4
	ovrp = struct.unpack(">H",data[res:res+2])[0]
	add_iter (hd,"Overprint",ovrp,res,2,">H")
	res += 4
	L,rid,fmt = read_recid(data,res)
	add_iter (hd,"MultiClr Lst","%02x"%rid,res,2,fmt)
	res += L
	res += 1
	X = struct.unpack(">I",data[res:res+4])[0]
	add_iter (hd,"Start X",X/167772.16,res,4,">I")
	res += 4
	Y = struct.unpack(">I",data[res:res+4])[0]
	add_iter (hd,"Start Y",Y/167772.16,res,4,">I")
	res += 4
	W = struct.unpack(">I",data[res:res+4])[0]
	add_iter (hd,"Handle 1 |<->|",W/167772.16,res,4,">I")
	res += 4
	# 0 normal, 1 repeat, 2 reflect, 3 autosize
	add_iter (hd,"Type",ord(data[res]),res,1,"B")
	res += 1
	R = struct.unpack(">H",data[res:res+2])[0]
	add_iter (hd,"Repeat",R,res,2,">H")

def hdLinePat(hd,data,page):
	offset=0
	N = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,"N",N,offset,2,">H")
	offset+=2
	for i in range(0,4): # f0=f2=f3=0, f1=N
		val = struct.unpack(">H",data[offset:offset+2])[0]
		add_iter (hd,"f%d"%i,val,offset,2,">H")
		offset+=2
	for i in range(0,N):
		val = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter (hd,"pat%d"%i,val/65536.,offset,4,">I")
		offset+=4

def hdMultiColorList(hd,data,page):
	offset = 0
	lstlen = struct.unpack(">H",data[offset:offset+2])[0]
	offset += 4
	for i in range(lstlen):
		l,rid,fmt = read_recid(data,offset)
		piter = add_iter (hd,'Color %d'%(i+1),getName(rid,page),offset,l,fmt)
		offset += l
		prcnt = int(cnvrt22(data[offset:offset+4])*100)
		add_iter (hd,'%',prcnt,offset,4,">HH",parent=piter)
		offset += 4
		unkn = int(cnvrt22(data[offset:offset+4])*100)
		add_iter (hd,'??',unkn,offset,4,">HH",parent=piter)
		offset += 4


def hdNewRadialFill(hd,data,page):
	offset = 0
	# 2-6 -- X
	# 6-10 -- Y
	# 15 -- overprint
	# 22-24 -- angle1
	# 26-30 -- <-> Hndl1
	# 30-32 -- angle2
	# 34-38 -- <-> Hndl2
	# 38-40 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 40-42 -- repeat
	if page.version > 10:
		l,rid,fmt = read_recid(data,0)
		add_iter (hd,'Color 1',getName(rid,page),0,l,fmt)
		offset += l
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,'Color 2',getName(rid,page),offset,l,fmt)
		offset += l
		x = cnvrt22(data[offset:offset+4])
		add_iter (hd,'X (%)',int(x*100),offset,4,">HH")
		offset += 4
		y = cnvrt22(data[offset:offset+4])
		add_iter (hd,'Y (%)',int(y*100),offset,4,">HH")
		offset += 4
		offset += 8
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,'MultiColorList',getName(rid,page),offset,l,fmt)
		offset += l
		offset += 2
		handleang = struct.unpack(">H",data[offset:offset+2])[0]
		add_iter (hd,'Handle 1 Angle',handleang,offset,2,">H")
		offset += 2
		offset += 2
		hndlwide = cnvrt22(data[offset:offset+4])
		add_iter (hd,'Handle 1 Wide (%)',int(100*hndlwide),offset,4,">HH")
		offset += 4
		handleang = struct.unpack(">H",data[offset:offset+2])[0]
		add_iter (hd,'Handle 2 Angle',handleang,offset,2,">H")
		offset += 2
		offset += 2
		hndlwide = cnvrt22(data[offset:offset+4])
		add_iter (hd,'Handle 2 Wide (%)',int(100*hndlwide),offset,4,">HH")
		offset += 4
		# 0 normal, 1 repeat, 2 reflect, 3 autosize
		add_iter (hd,"Type",ord(data[offset+1]),offset+1,1,"B")


def hdNewBlend(hd,data,page):
	offset = 0
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Graphic Style',getName(rid,page),0,l,fmt)
	offset += l
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Parent',getName(rid,page),offset,l,fmt)
	offset += l
	offset += 8
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'List (Content)',getName(rid,page),offset,l,fmt)
	offset += l
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'List (Path 1)',getName(rid,page),offset,l,fmt)
	offset += l
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'List (Path 2)',getName(rid,page),offset,l,fmt)
	offset += l
	offset += 2
	steps = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Steps',steps,offset,2,">H")
	offset += 2
	offset += 4
	rng1 = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Range start (%)',rng1,offset,4,">HH")
	offset += 4
	rng2 = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Range end (%)',rng2,offset,4,">HH")
	offset += 4


def hdNewContourFill(hd,data,page):
	offset = 0
	# 2-6 -- X
	# 6-10 -- Y
	# 10-12 -- Taper
	# 15 -- overprint
	# 18-20 -- link to ColorList
	# 20-22 -- link to GraphicStyle
	# 22-24 -- angle1
	# 26-30 -- <-> Hndl1
	# 31 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 32-34 -- repeat
	if page.version > 10:
		l,rid,fmt = read_recid(data,0)
		add_iter (hd,'Color 1',getName(rid,page),0,l,fmt)
		offset += l
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,'Color 2',getName(rid,page),offset,l,fmt)
		offset += l
		x = cnvrt22(data[offset:offset+4])
		add_iter (hd,'X (%)',int(x*100),offset,4,">HH")
		offset += 4
		y = cnvrt22(data[offset:offset+4])
		add_iter (hd,'Y (%)',int(y*100),offset,4,">HH")
		offset += 4
		taper = struct.unpack(">H",data[offset:offset+2])[0]
		add_iter (hd,'Taper',taper,offset,2,">H")
		offset += 2
		offset += 6
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,'MultiColorList',getName(rid,page),offset,l,fmt)
		offset += l
		offset += 2
		handleang = struct.unpack(">H",data[offset:offset+2])[0]
		add_iter (hd,'Handle Angle',handleang,offset,2,">H")
		offset += 2
		offset += 2
		hndlwide = cnvrt22(data[offset:offset+4])
		add_iter (hd,'Handle Wide (%)',int(100*hndlwide),offset,4,">HH")
		offset += 4


def hdLensFill(hd,data,page):
	offset = 0
	l,rid,fmt = read_recid(data,0)
	add_iter (hd,'Color',getName(rid,page),0,l,fmt)
	mode = ord(data[l+0x25])
	modes = {0:"Transparency",1:"Magnify",2:"Lighten",3:"Darken",4:"Invert",5:"Monochrome"}
	add_iter (hd,'Mode',modes[mode],0x25+l,1,"B")
	if mode == 0:
		offset = l+6
		opc = cnvrt22(data[offset:offset+4])
		add_iter (hd,'Opacity',opc,offset,4,">HH")
		offset+=4
#		offset+=16
#		x = cnvrt22(data[offset:offset+4])
#		add_iter (hd,'X',x,offset,4,">HH")
#		offset+=4
#		y = cnvrt22(data[offset:offset+4])
#		add_iter (hd,'Y',y,offset,4,">HH")
#		offset+=4
		# Transparency
		# 37: 1 -- CenterPoint, 2 -- ObjOnly, 4 -- Snapshot (flags)
	# Magnify
	# 8-10.10-12 -- mag.coeff
	pass

def hdBendFilter(hd,data,page):
	offset = 0
	size = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Size',size,offset,2,">H")
	offset += 2
	x = cnvrt22(data[offset:offset+4])
	add_iter (hd,'X',x,offset,4,">HH")
	offset += 4
	y = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Y',y,offset,4,">HH")

def hdBlock (hd,data,page):
		off = 0
		if page.version == 10:
			flags =  struct.unpack('>h', data[off:off+2])[0]
			res = 2
			for i in range(21):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))

				res += L
			res += 1
			for i in range(2):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
		elif page.version == 8:
			res = 0
			for i in range(12):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res += 14
		elif page.version < 8:
			res = 0
			for i in range(11):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res += 10
			for i in range(3):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
		else:
			# FIXME! ver11 starts with size==7
			res = 0
			for i in range(12):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res += 14
			for i in range(3):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res +=1
			for i in range(4):
				L,rid1,fmt = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r,fmt1 = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,fmt)
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			# verify for v9
			if page.version < 10:
				res -= 6

def hdBrush (hd,data,page):
	offset = 0
	L,name,fmt = read_recid(data,offset,fmt)
	add_iter (hd,'Name',getName(name,page),offset,L,fmt)
	offset += L
	L,name,fmt = read_recid(data,offset)
	add_iter (hd,'List',getName(name,page),offset,L,fmt)


def hdBrushStroke (hd,data,page):
	offset = 0
	L,name,fmt = read_recid(data,offset)
	add_iter (hd,'Brush ID',getName(name,page),offset,L,fmt)
	offset += L
	w = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Width',w,offset,L,">HH")


def hdBrushTip (hd,data,page):
	btiptype = {0:"Fixed",1:"Random",2:"Variable",3:"Flare"}
	offset = 0
	L,name,fmt = read_recid(data,offset)
	add_iter (hd,'SymbolClass',getName(name,page),offset,L,fmt)
	offset += L
	oop = bool(struct.unpack(">I",data[offset:offset+4])[0])
	add_iter (hd,'Orient on Path',oop,offset,4,">I")
	offset += 4
	cnt = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Count',cnt,offset,4,">I")
	offset += 4
	scltype = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Scaling Type',btiptype[scltype],offset,4,">I")
	offset += 4
	scltype = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Angle Type',btiptype[scltype],offset,4,">I")
	offset += 4
	scltype = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Offset Type',btiptype[scltype],offset,4,">I")
	offset += 4
	scltype = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Spacing Type',btiptype[scltype],offset,4,">I")
	offset += 4
	oop = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter (hd,'Paint (0)/Spray (1)',oop,offset,4,">I")
	offset += 4
	sclmin = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Scaling Min',sclmin,offset,4,">HH")
	offset += 4
	sclmax = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Scaling Max',sclmax,offset,4,">HH")
	offset += 4
	amin = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Angle Min',amin,offset,4,">HH")
	offset += 4
	amax = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Angle Max',amax,offset,4,">HH")
	offset += 4
	omin = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Offset Min',omin,offset,4,">HH")
	offset += 4
	omax = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Offset Max',omax,offset,4,">HH")
	offset += 4
	spcmin = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Spacing Min',spcmin,offset,4,">HH")
	offset += 4
	spcmax = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Spacing Max',spcmax,offset,4,">HH")
	offset += 4
	fcrn = bool(struct.unpack(">I",data[offset:offset+4])[0])
	add_iter (hd,'Fold Corners',fcrn,offset,4,">I")


def hdPropLst(hd,data,page):
	off = 0
	size = struct.unpack('>h', data[off+2:off+4])[0]
	res = 8
	for i in range(size):
		L1,rid1,fmt = read_recid(data,off+res)
		res += L1
		L2,rid2,fmt1 = read_recid(data,off+res)
		res += L2
		add_iter (hd,getName(rid1,page),"%02x"%rid2,res-L1-L2,L1+L2,">HH")

def hdElemPropLst(hd,data,page):
	off = 0
	size = struct.unpack('>h', data[off+2:off+4])[0]
	res = 6
	L,attr,fmt = read_recid(data,off+res)
	add_iter (hd,'Style',getZone(attr,page),off+res,L,fmt)
	res += L
	L,name,fmt = read_recid(data,off+res)
	add_iter (hd,'Parent',getZone(name,page),off+res,L,fmt)
	res += L
	for i in range(size):
		L1,rid1,fmt = read_recid(data,off+res)
		res += L1
		L2,rid2,fmt1 = read_recid(data,off+res)
		res += L2
		add_iter (hd,getName(rid1,page),getZone(rid2,page),res-L1-L2,L1+L2,">HH")

def hdStylePropLst(hd,data,page):
	off = 0
	size = struct.unpack('>h', data[off+2:off+4])[0]
	res = 6
	L,attr,fmt = read_recid(data,off+res)
	add_iter (hd,'Parent',getZone(attr,page),off+res,L,fmt)
	res += L
	L,name,fmt = read_recid(data,off+res)
	add_iter (hd,'Name',getName(name,page),off+res,L,fmt)
	res += L
	for i in range(size):
		L1,rid1,fmt = read_recid(data,off+res)
		res += L1
		L2,rid2,fmt1 = read_recid(data,off+res)
		res += L2
		add_iter (hd,getName(rid1,page),getZone(rid2,page),res-L1-L2,L1+L2,">HH")

def hdSymbolClass (hd,data,page):
	offset = 0
	L,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Name',getName(rid,page),offset,L,fmt)
	offset += L
	L,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Group ID',getName(rid,page),offset,L,fmt)
	offset += L
	L,rid,fmt = read_recid(data,offset)
	add_iter (hd,'DateTime ID',getName(rid,page),offset,L,fmt)
	offset += L
	L,rid,fmt = read_recid(data,offset)
	add_iter (hd,'SymbolLibrary ID',getName(rid,page),offset,L,fmt)
	offset += L
	L,rid,fmt = read_recid(data,offset)
	add_iter (hd,'List ID',getName(rid,page),offset,L,fmt)
	offset += L


def hdImageImport(hd,data,page):
	offset = 0
	L1,gr_style,fmt = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,L1,fmt)
	offset += L1
	L2,attr,fmt = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%attr,offset,L2,fmt)
	offset += L2+4
	if page.version > 3:
		offset += 4
	if page.version > 8:
		L3,attr,fmt = read_recid(data,offset)
		add_iter (hd,'Format Name',"%02x"%attr,offset,L3,fmt)
		offset += L3
	L4,attr,fmt = read_recid(data,offset)
	add_iter (hd,'DataList',"%02x"%attr,offset,L4,fmt)
	offset += L4
	L5,attr,fmt = read_recid(data,offset)
	add_iter (hd,'FileDescriptor',"%02x"%attr,offset,L5,fmt)
	offset += L5
	L6,attr,fmt = read_recid(data,offset)
	add_iter (hd,'Xform',"%02x"%attr,offset,L6,fmt)
	offset += L6+8
	x = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Actual Image W',"%.2f"%x,offset,4,">HH")
	offset += 4
	x = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Actual Image H',"%.2f"%x,offset,4,">HH")
	offset += 4+6
	w = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Orig Image W ?',"%d"%w,offset,2,">H")
	offset += 2
	h = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Orig Image H ?',"%d"%h,offset,2,">H")
	offset += 2+4
	w = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Orig Image W ?',"%d"%w,offset,2,">H")
	offset += 2
	h = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter (hd,'Orig Image H ?',"%d"%h,offset,2,">H")


def hdLayer(hd,data,page):
	offset = 0
	L1,gr_style,fmt = read_recid(data,offset)
	add_iter (hd,'Graphic Style',getZone(gr_style,page),0,L1,fmt)
	offset += L1
	if page.version > 3:
		offset += 4
	mode = ord(data[offset+3])
	lmtxt = 'Normal'
	if mode&0x10 == 0x10:
		lmtxt = 'Wire'
	if mode&0x1 == 1:
		lmtxt += ' Locked'
	add_iter (hd,'View mode',lmtxt,offset+3,1,"txt")
	L2,attr,fmt = read_recid(data,offset+6)
	add_iter (hd,'List',"%02x"%attr,offset+6,L2,"txt")
	offset += L2
	L3,name,fmt = read_recid(data,offset+6)
	add_iter (hd,'Layer name',getName(name,page),offset+6,L3,fmt)
	offset += L3
	vis = ""
	vval = ord(data[offset+7])
	if vval&1:
		vis += "Show "
	if vval&2:
		vis += "Print "
	if vval&8:
		vis += "Guides"
	add_iter (hd,'Visibility',vis,offset+7,1,"B")


def xform_calc(var1,var2):
	a5 = not (var1&0x20)/0x20
	a4 = not (var1&0x10)/0x10
	a2 = (var1&0x4)/0x4
	a1 = (var1&0x2)/0x2
	a0 = (var1&0x1)/0x1
	b6 = (var2&0x40)/0x40
	b5 = (var2&0x20)/0x20
	if a2:
		return 0,()
	xlen = (a5+a4+a1+a0+b6+b5)*4
	return xlen,(a4,b6,b5,a5,a0,a1)


def hdXform(hd,data,page):
	offset = 0
	if page.version < 9:
		x =[1,1,1,1,1,1]
		len1 = 1
	else:
		var1 = ord(data[offset])
		var2 = ord(data[offset+1])
		len1,x = xform_calc(var1,var2)
	offset += 2
	if len1 > 0:
		if x[0]:
			m11 = cnvrt22(data[offset:offset+4])
			add_iter (hd,'m11',"%.2f"%m11,offset,4,">HH")
			offset += 4
		else:
			m11 = 1
			add_iter (hd,'m11',"%.2f"%m11,offset,0,">HH")
		if x[1]:
			m21 = cnvrt22(data[offset:offset+4])
			add_iter (hd,'m21',"%.2f"%m21,offset,4,">HH")
			offset += 4
		else:
			m21 = 0
			add_iter (hd,'m21',"%.2f"%m21,offset,0,">HH")
		if x[2]:
			m12 = cnvrt22(data[offset:offset+4])
			add_iter (hd,'m12',"%.2f"%m12,offset,4,">HH")
			offset += 4
		else:
			m12 = 0
			add_iter (hd,'m12',"%.2f"%m12,offset,0,">HH")
		if x[3]:
			m22 = cnvrt22(data[offset:offset+4])
			add_iter (hd,'m22',"%.2f"%m22,offset,4,">HH")
			offset += 4
		else:
			m22 = 1
			add_iter (hd,'m22',"%.2f"%m22,offset,0,">HH")
		if x[4]:
			m13 = cnvrt22(data[offset:offset+4])
			add_iter (hd,'m13',"%.2f"%m13,offset,4,">HH")
			offset += 4
		else:
			m13 = 0
			add_iter (hd,'m13',"%.2f"%m13,offset,0,">HH")
		if x[5]:
			m23 = cnvrt22(data[offset:offset+4])
			add_iter (hd,'m23',"%.2f"%m23,offset,4,">HH")
		else:
			m23 = 0
			add_iter (hd,'m23',"%.2f"%m23,offset,0,">HH")


def hdRectangle(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	if page.version > 3:
		offset += 4
	offset += 4
	xform = struct.unpack('>H', data[offset+8:offset+10])[0]
	add_iter (hd,'XForm',"%02x"%xform,offset+8,2,">h")
	x1 = struct.unpack('>H', data[offset+10:offset+12])[0] - 1692
	x1f = struct.unpack('>H', data[offset+12:offset+14])[0]
	y1 = struct.unpack('>H', data[offset+14:offset+16])[0] - 1584
	y1f = struct.unpack('>H', data[offset+16:offset+18])[0]
	x2 = struct.unpack('>H', data[offset+18:offset+20])[0] - 1692
	x2f = struct.unpack('>H', data[offset+20:offset+22])[0]
	y2 = struct.unpack('>H', data[offset+22:offset+24])[0] - 1584
	y2f = struct.unpack('>H', data[offset+24:offset+26])[0]
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),offset+10,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),offset+14,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),offset+18,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),offset+22,4,"txt")
	rtlt = struct.unpack('>H', data[offset+26:offset+28])[0]
	rtltf = struct.unpack('>H', data[offset+28:offset+30])[0]
	rtll = struct.unpack('>H', data[offset+30:offset+32])[0]
	rtllf = struct.unpack('>H', data[offset+32:offset+34])[0]
	if page.version > 10:
		rtrt = struct.unpack('>H', data[offset+34:offset+36])[0]
		rtrtf = struct.unpack('>H', data[offset+36:offset+38])[0]
		rtrr = struct.unpack('>H', data[offset+38:offset+40])[0]
		rtrrf = struct.unpack('>H', data[offset+40:offset+42])[0]
		rbrb = struct.unpack('>H', data[offset+42:offset+44])[0]
		rbrbf = struct.unpack('>H', data[offset+44:offset+46])[0]
		rbrr = struct.unpack('>H', data[offset+46:offset+48])[0]
		rbrrf = struct.unpack('>H', data[offset+48:offset+50])[0]
		rblb = struct.unpack('>H', data[offset+50:offset+52])[0]
		rblbf = struct.unpack('>H', data[offset+52:offset+54])[0]
		rbll = struct.unpack('>H', data[offset+54:offset+56])[0]
		rbllf = struct.unpack('>H', data[offset+56:offset+58])[0]
	if page.version > 10:
		add_iter (hd,'Rad TopLeft (Top)',"%.4f"%(rtlt+rtltf/65536.),offset+26,4,"txt")
		add_iter (hd,'Rad TopLeft (Left)',"%.4f"%(rtll+rtllf/65536.),offset+30,4,"txt")
		add_iter (hd,'Rad TopRight (Top)',"%.4f"%(rtrt+rtrtf/65536.),offset+34,4,"txt")
		add_iter (hd,'Rad TopRight (Right)',"%.4f"%(rtrr+rtrrf/65536.),offset+38,4,"txt")
		add_iter (hd,'Rad BtmRight (Btm)',"%.4f"%(rbrb+rbrbf/65536.),offset+42,4,"txt")
		add_iter (hd,'Rad BtmRight (Right)',"%.4f"%(rbrr+rbrrf/65536.),offset+46,4,"txt")
		add_iter (hd,'Rad BtmLeft (Btm)',"%.4f"%(rblb+rblbf/65536.),offset+50,4,"txt")
		add_iter (hd,'Rad BtmLeft (Left)',"%.4f"%(rbll+rbllf/65536.),offset+54,4,"txt")
	else:
		add_iter (hd,'Rad X',"%d"%rtlt,offset+26,2,">h")
		add_iter (hd,'Rad Y',"%d"%rtll,offset+30,2,">h")


def hdOval(hd,data,page):
	offset = 0
	L,gr_style,fmt = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%gr_style,offset,L,fmt)
	offset += L
	L,layer,fmt = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%layer,offset,L,fmt)
	offset += L
	if page.version > 3:
		offset += 4
	offset += 4
	L,xform,fmt = read_recid(data,offset+4)
	add_iter (hd,'XForm',"%02x"%xform,offset+4,L,fmt)
	offset += L
	x1 = struct.unpack('>H', data[offset+4:offset+6])[0] - 1692
	x1f = struct.unpack('>H', data[offset+6:offset+8])[0]
	y1 = struct.unpack('>H', data[offset+8:offset+10])[0] - 1584
	y1f = struct.unpack('>H', data[offset+10:offset+12])[0]
	x2 = struct.unpack('>H', data[offset+12:offset+14])[0] - 1692
	x2f = struct.unpack('>H', data[offset+14:offset+16])[0]
	y2 = struct.unpack('>H', data[offset+16:offset+18])[0] - 1584
	y2f = struct.unpack('>H', data[offset+18:offset+20])[0]
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),offset+4,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),offset+8,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),offset+12,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),offset+16,4,"txt")
	if page.version > 10:
		arc1 = struct.unpack('>H', data[offset+20:offset+22])[0]
		arc1f = struct.unpack('>H', data[offset+22:offset+24])[0]
		arc2 = struct.unpack('>H', data[offset+24:offset+26])[0]
		arc2f = struct.unpack('>H', data[offset+26:offset+28])[0]
		clsd = ord(data[offset+36])
		add_iter (hd,'Arc <>',"%.4f"%(arc1+arc1f/65536.),offset+20,4,"txt")
		add_iter (hd,'Arc ()',"%.4f"%(arc2+arc2f/65536.),offset+24,4,"txt")
		add_iter (hd,'Closed',clsd,offset+28,1,"B")

def hdGroup(hd,data,page):
	offset = 0
	res,gr_style,fmt = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%gr_style,offset,res,fmt)
	offset += res;
	res,layer,fmt = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%layer,offset,res,fmt)
	offset += res + 4;
	if page.version > 3:
		offset += 4
	res,mlist,fmt = read_recid(data,offset)
	add_iter (hd,'MList',"%02x"%mlist,offset,res,fmt)
	offset += res
	res,xform,fmt = read_recid(data,offset)
	add_iter (hd,'XForm',"%02x"%xform,offset,res,fmt)

def hdGraphicStyle(hd,data,page):
	off = 2
	size = struct.unpack('>H', data[off:off+2])[0]
	off = 6
	parent = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'Parent',"%02x"%parent,off,2,">H")
	off += 2
	attrid = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'Attr ID',"%02x"%attrid,off,2,">H")
	off += 2
	for i in range(size):
		a = struct.unpack('>H', data[off:off+2])[0]
		off += 2
		v = struct.unpack('>H', data[off:off+2])[0]
		off += 2
		add_iter (hd,getName(a,page),getName(v,page),off-4,4,">HH")


def hdAttributeHolder(hd,data,page):
	offset = 0
	L,parent,fmt = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%parent,offset,L,fmt)
	offset += L
	L,attr,fmt = read_recid(data,offset)
	add_iter (hd,'Attr ID',"%02x"%attr,offset,L,fmt)


def hdBasicFill(hd,data,page):
	offset = 0
	L,clr,fmt = read_recid(data,offset)
	add_iter (hd,'Color',"%02x"%clr,offset,L,fmt)
	offset += L
	overprint = ord(data[offset+2])


def hdBasicLine(hd,data,page):
	offset = 0
	L,clr,fmt = read_recid(data,offset)
	add_iter (hd,'Color',getZone(clr,page),offset,L,fmt)
	offset += L
	L,dash,fmt = read_recid(data,offset)
	add_iter (hd,'Line Pattern',getZone(dash,page),offset,L,fmt)
	offset += L
	L,larr,fmt = read_recid(data,offset)
	add_iter (hd,'Start Arrow',getZone(larr,page),offset,L,fmt)
	offset += L
	L,rarr,fmt = read_recid(data,offset)
	add_iter (hd,'End Arrow',getZone(rarr,page),offset,L,fmt)
	offset += L
	mit = struct.unpack('>H', data[offset:offset+2])[0]
	mitf = struct.unpack('>H', data[offset+2:offset+4])[0]
	w = struct.unpack('>H', data[offset+4:offset+6])[0]
	overprint = ord(data[offset+7])
	join = ord(data[offset+8]) # 0 - angle, 1 - round, 2 - square
	cap = ord(data[offset+9]) # 0 - none, 1 - round, 2 - square
	# FIXME! add iters for overprint/join/cap
	add_iter (hd,'Miter',"%.4f"%(mit+mitf/65536.),offset,4,"txt")
	add_iter (hd,'Width',w,offset+4,2,">H")

def hdList(hd,data,page):
	offset = 0
	ltype = struct.unpack('>H', data[offset+10:offset+12])[0]
	ltxt = "%02x"%ltype
	if page.dict.has_key(ltype):
		ltxt += " (%s)"%page.dict[ltype]
		add_iter (hd,'List Type',ltxt,10,2,">H")
	size = struct.unpack('>h', data[offset+2:offset+4])[0]
	offset = 12
	for i in range(size):
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,'List Elem',"%02x (%s)"%(rid,page.dict[page.reclist[rid-1]]),offset,l,fmt)
		offset += l

def hdCustomProc(hd,data,page):
	off = 0
	N = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'N',N,off,2,">H")
	off += 2
	l,rid,fmt = read_recid(data,off)
	add_iter (hd,"id",getName(rid,page),off,l,fmt)
	off += l
	for i in range(2):
		val = struct.unpack('>H', data[off:off+2])[0]
		add_iter (hd,"f%d"%i,val,off,2,">H")
		off += 2

def hdData(hd,data,page):
	off = 0
	size = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'block[size]',size,off,2,">H")
	off += 2
	size = struct.unpack('>I', data[off:off+4])[0]
	add_iter (hd,'size[data]',size,off,4,">I")
	off += 4
	add_iter (hd,'data',"",off,size,"txt")
	off+=size

def hdDataList(hd,data,page):
	offset = 0
	N = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'N',N,offset,2,">H")
	offset += 2
	dSz = struct.unpack('>I', data[offset:offset+4])[0]
	add_iter (hd,'dataSize',dSz,offset,4,">I")
	offset += 4
	for i in range(2):
		val=struct.unpack('>H', data[offset:offset+2])[0]
		add_iter(hd, "f%d"%i, val, offset, 2, ">H")
		offset+=2
	for i in range(N):
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,"id%d"%i,"%02x"%rid,offset,l,fmt)
		offset += l

justifyType_ids={
	0: "left",
	1: "center",
	2: "right",
	3: "all",
	4: "topDown"
}
def hdDisplayText(hd,data,page):
	offset = 0
	val = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'f0',val,offset,2,">H")
	offset += 2
	for i in range(2):
		l,rid,fmt = read_recid(data,offset)
		add_iter (hd,'graphicStyle' if i==0 else 'parent',getZone(rid,page),offset,l,fmt)
		offset += l
	for i in range(2):
		val=struct.unpack('>H', data[offset:offset+2])[0]
		add_iter(hd, "f%d"%(i+1), val, offset, 2, ">H")
		offset+=2
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'formId',getZone(rid,page),offset,l,fmt)
	offset += l
	add_iter (hd,'unknown1',"",offset,16,"txt")
	offset += 16
	for i in range(4):
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,"dim%d"%i,val/65536.,offset,4,">i")
		offset+=4
	for i in range(4):
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,"dimA%d"%i,val/65536.,offset,4,">i")
		offset+=4
	add_iter (hd,'unknown2',"",offset,16,"txt")
	offset += 16
	val = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'textLength',val,offset,2,">H")
	offset += 2
	val = struct.unpack('>b', data[offset:offset+1])[0]
	idtxt = 'Unknown'
	if justifyType_ids.has_key(val):
		idtxt = justifyType_ids[val]
	add_iter (hd, "justify", "0x%02x (%s)"%(val,idtxt),offset,1,">b")
	offset += 1
	val = struct.unpack('>b', data[offset:offset+1])[0] # always 0?
	add_iter (hd,'f3',val,offset,1,">b")
	offset += 1

def hdFileDescriptor(hd,data,page):
	off = 0
	for i in range(2):
		l,rid,fmt = read_recid(data,off)
		add_iter (hd,"id%d"%i,"%02x"%rid,off,l,fmt)
		off += l
	for i in range(5): # f4=1
		val=struct.unpack('>b', data[off:off+1])[0]
		add_iter(hd, "f%d"%i, val, off, 1, ">b")
		off+=1
	dtSz = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'data[size]',dtSz,off,2,">H")
	off += 2
	if hd.version>3:
		return
	(n, endOff) = rdata(data, off, '%ds'%4)
	add_iter (hd,'type',n,off,4,"txt")
	off +=4
	add_iter (hd,'unknown',"",off,dtSz-4,"txt")

def hdGuides(hd,data,page):
	off = 0
	size = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'block[size]',size,off,2,">H")
	off += 2
	l,rid,fmt = read_recid(data,off)
	add_iter (hd,"elem",getZone(rid,page),off,l,fmt)
	off += l
	l,rid,fmt = read_recid(data,off)
	add_iter (hd,"layer",getZone(rid,page),off,l,fmt)
	off += l
	if hd.version > 3:
		for i in range(2):
			val=struct.unpack('>h', data[off:off+2])[0]
			add_iter (hd,"f%d"%i,size,off,2,">h")
			off += 2
	add_iter (hd,'unknown',"",off,12+4*size,"txt")

def hdHalftone(hd,data,page):
	off = 0
	l,rid,fmt = read_recid(data,off)
	add_iter (hd,"id",getName(rid,page),off,l,fmt)
	off += l
	for i in range(2):
		val = struct.unpack('>i', data[off:off+4])[0]
		add_iter (hd,'angle' if i==0 else 'ruling',val/65536.,off,4,">i")
		off+=4

def hdString(hd,data,page):
	off = 0
	size = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'block[size]',size,off,2,">H")
	off += 2
	size = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'string[size]',size,off,2,">H")
	off += 2
	(n, endOff) = rdata(data, off, '%ds'%size)
	add_iter (hd,'name',unicode(n,"mac-roman"),off,size,"txt")
	off +=size

def hdDictVal(hd,data,page):
	offset=0
	key = struct.unpack('>h', data[offset:offset+2])[0]
	add_iter (hd,'key',key,offset,2,">h")
	offset+=2
	if hd.version <= 8:
		key = struct.unpack('>h', data[offset:offset+2])[0]
		add_iter (hd,'key2',key,offset,2,">h")
		offset+=2
	(n, endOff) = rdata(data, offset, '%ds'%(len(data)-offset))
	pos = n.find("\x00")
	if pos!=-1:
		n=n[:pos]
	add_iter (hd,'name',n,offset,len(data)-offset,"txt")

def hdTextChar(hd,data,page):
	offset=0
	val = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'offset',val,offset,2,">H")
	offset+=2
	flags = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,"flags","%02x"%flags,offset,2,">H")
	offset+=2
	if flags&1:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'xPos',val/65536.,offset,4,">i")
		offset+=4
	if flags&2:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'kerning',val/65536.,offset,4,">i")
		offset+=4
	if flags&4:
		L,rid,fmt = read_recid(data,offset)
		add_iter (hd,'fontName',getName(rid,page),offset,L,fmt)
		offset += L
	if flags&8:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'fontSize',val/65536.,offset,4,">i")
		offset+=4
	if flags&0x10:
		val=struct.unpack(">I",data[offset:offset+4])[0]
		if val==0xFFFE0000:
			add_iter(hd, "leading", "solid",offset,4,">I")
		elif val==0xFFFF0000:
			add_iter(hd, "leading", "auto",offset,4,">I")
		else:
			add_iter(hd, "leading", val/65536.,offset,4,">I")
		offset+=4
	if flags&0x20:
		val = struct.unpack('>I', data[offset:offset+4])[0]
		itext=""
		if val&1:
			itext+="bold,"
		if val&2:
			itext+="italic,"
		add_iter (hd,'fontStyle',"0x%02x(%s)"%(val,itext),offset,4,">I")
		offset+=4
	if flags&0x40:
		L,rid,fmt = read_recid(data,offset)
		add_iter (hd,'color',getZone(rid,page),offset,L,fmt)
		offset += L
	if flags&0x80:
		L,rid,fmt = read_recid(data,offset)
		add_iter (hd,'textEffects',getZone(rid,page),offset,L,fmt)
		offset += L
	if flags&0x100:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'letter[spacing]',val/65536.,offset,4,">i") # in point
		offset+=4
	if flags&0x200:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'word[spacing]',val/65536.,offset,4,">i") # in point
		offset+=4
	if flags&0x400:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'x[scaling]',val/65536.,offset,4,">i") # in percent
		offset+=4
	if flags&0x800:
		val = struct.unpack('>i', data[offset:offset+4])[0]
		add_iter (hd,'baseline[shift]',val/65536.,offset,4,">i")
		offset+=4

def hdTextEffs(hd,data,page):
	off=0
	N = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'N',N,off,2,">H")
	off+=2
	for i in range(2):
		l,rid,fmt = read_recid(data,off)
		add_iter (hd,"name" if i== 0 else "name[short]",getName(rid,page),off,l,fmt)
		off+=l
	val = struct.unpack('>H', data[off:off+2])[0] # 0|1
	add_iter (hd,'f0',val,off,2,">H")
	off+=2
	for i in range(5): # fl0=0|1000,fl1=0|6,fl3=0|4f7e
		val = struct.unpack('>H', data[off:off+2])[0] # 0|1000
		add_iter (hd,"fl%d"%i,"%x"%val,off,2,">H")
		off+=2
	val = struct.unpack('>H', data[off:off+2])[0] # N
	add_iter (hd,'N1',val,off,2,">H")
	off+=2
	val = struct.unpack('>H', data[off:off+2])[0] # 0
	add_iter (hd,'f1',val,off,2,">H")
	off+=2
	if N==0:
		return
	val = struct.unpack('>H', data[off:off+2])[0] # 4
	add_iter (hd,'f2',val,off,2,">H")
	off+=2

def hdTextEffsData(hd,data,page):
	off=0
	val = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'key',val,off,2,">H")
	off+=2
	val = struct.unpack('>H', data[off:off+2])[0]
	add_iter (hd,'type',val,off,2,">H")
	off+=2
	# key=2,type=7 last is a colorId

def hdTextPara(hd,data,page):
	offset=0
	val = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'offset',val,offset,2,">H")
	offset+=2
	# todo

def hdTextString(hd,data,page):
	(n, endOff) = rdata(data, 0, '%ds'%len(data))
	pos = n.find("\x00")
	if pos!=-1:
		n=n[:pos]
	add_iter (hd,'text',unicode(n,"mac-roman"),0,len(data),"txt")

def hdCompositePath(hd,data,page):
	offset = 0
	res,rid1,fmt = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%rid1,offset,res,fmt)
	L,rid2,fmt = read_recid(data,offset+res)
	add_iter (hd,'Parent',"%02x"%rid2,offset+res,L,fmt)
	res += L
	if page.version > 3:
		res += 4
	res += 4
	L,rid3,fmt = read_recid(data,offset+res)
	add_iter (hd,'List of paths',"%02x"%rid3,offset+res,L,fmt)


def hdProcessColor(hd,data,page):
	offset = 0
	ustr1 = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'Name',getName(ustr1,page),0,2,">H")
	offset = 14
	cmpntnames = ["K","C","M","Y"]
	for i in range(4):
		cmpnt = struct.unpack(">H",data[offset+i*2:offset+i*2+2])[0]/256
		add_iter (hd,cmpntnames[i],"%d"%cmpnt,offset+i*2,2,">H")

def hdCalligraphicStroke (hd,data,page):
	offset = 0
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Color',getName(rid,page),offset,l,fmt)
	offset += l
	ang = cnvrt22(data[offset:offset+4])
	add_iter (hd,'Angle',ang,offset,4,">HH")
	offset += 4
	w = cnvrt22(data[offset:offset+4])
	add_iter (hd,'W',w,offset,4,">HH")
	offset += 4
	h = cnvrt22(data[offset:offset+4])
	add_iter (hd,'H',h,offset,4,">HH")
	offset += 4
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Path',getName(rid,page),offset,l,fmt)

def hdColor6(hd,data,page):
	offset = 0
	pal = struct.unpack('>H', data[offset:offset+2])[0]
	if pal == 3:
		ustroff = 0xe
	else:
		ustroff = 2
	ustr1 = struct.unpack('>H', data[offset+ustroff:offset+ustroff+2])[0]
	add_iter (hd,"Palette",key2txt(pal,palette,"Unkn %02x"%pal),0,2,">h")
	add_iter (hd,'Name',getName(ustr1,page),ustroff,2,">H")
	if pal == 4:  # CMYK
		offset = 14
		if page.version > 9:
			offset += 2
		cmpntnames = ["C","M","Y","K"]
		for i in range(4):
			cmpnt = struct.unpack(">I",data[offset+i*4:offset+i*4+4])[0]/256
			add_iter (hd,cmpntnames[i],"%d"%cmpnt,offset+i*4,4,">I")


def hdPantoneColor(hd,data,page):
	offset = 0
	L,rid,fmt = read_recid(data,offset)
	add_iter(hd, "Color0", "%02x"%rid, offset, L, fmt)
	offset+=L
	r = struct.unpack(">H",data[offset:offset+2])[0]/256
	g = struct.unpack(">H",data[offset+2:offset+4])[0]/256
	b = struct.unpack(">H",data[offset+4:offset+6])[0]/256
	add_iter (hd,'RGB',"%d %d %d"%(r,g,b),offset,6,">HHH")
	offset+=6
	add_iter (hd,'unknown', '', offset,28,"txt")
	offset+=28

def hdSpotColor(hd,data,page):
	offset = 0
	ustr1 = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,'Name',getName(ustr1,page),2,2,">H")
	cmpntnames = ["R","G","B"]
	for i in range(3):
		cmpnt = struct.unpack('>H', data[offset+4+i*2:offset+6+i*2])[0]/256
		add_iter (hd,cmpntnames[i],"%d"%cmpnt,offset+i*2+4,2,">H")

def hdTintColor6(hd,data,page):
	offset = 0
	pal = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,"Palette",key2txt(pal,palette,"Unkn %02x"%pal),0,2,">h")
	l,rid,fmt = read_recid(data,2)
	add_iter (hd,'Name',getName(rid,page),2,l,fmt)
	r = struct.unpack(">H",data[offset+2+l:offset+2+l+2])[0]/256
	g = struct.unpack(">H",data[offset+2+l+2:offset+2+l+4])[0]/256
	b = struct.unpack(">H",data[offset+2+l+4:offset+2+l+6])[0]/256
	add_iter (hd,'RGB',"%d %d %d"%(r,g,b),l+2,6,">HHH")
	offset += 8+l+6
	l,rid,fmt = read_recid(data,offset)
	add_iter (hd,'Tint of',"%02x"%rid,offset,l,fmt)
	offset += l
	tint = struct.unpack(">H",data[offset:offset+2])[0]*100./0xffff
	add_iter (hd,'Tint',"%.0f%%"%tint,offset,2,">H")


def hdSpotColor6(hd,data,page):
	offset = 0
	pal = struct.unpack('>H', data[offset:offset+2])[0]
	ustr1 = struct.unpack('>H', data[offset+2:offset+4])[0]
	add_iter (hd,"Palette",key2txt(pal,palette,"Unkn %02x"%pal),0,2,">h")
	add_iter (hd,'Name',getName(ustr1,page),2,2,">H")

def hdTransformFilter(hd,data,page):
	offset = 0
	cp = struct.unpack('>H', data[offset:offset+2])[0]
	add_iter (hd,"Copies",cp,offset,2,">h")
	offset += 2
	xsc = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Scale X",xsc,offset,4,">h")
	offset += 4
	ysc = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Scale Y",ysc,offset,4,">h")
	offset += 4
	xsk = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Skew X",xsk,offset,4,">h")
	offset += 4
	ysk = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Skew Y",ysk,offset,4,">h")
	offset += 4
	rot = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Rotate",rot,offset,4,">h")
	offset += 4
	xof = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Offset X",xof,offset,4,">h")
	offset += 4
	yof = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Offset Y",yof,offset,4,">h")
	offset += 4
	xc = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Center X",xc,offset,4,">h")
	offset += 4
	yc = cnvrt22(data[offset:offset+4])
	add_iter (hd,"Center Y",yc,offset,4,">h")
	offset += 4
	uni = bool(ord(data[offset]))
	add_iter (hd,"Uniform Scale",uni,offset,1,"B")


hdp = {
	"AGDFont":hdAGDFont,
	"ArrowPath":hdArrowPath,
	"ArrowPathPoint":hdPathPoint,
	"AttributeHolder":hdAttributeHolder,
	"BasicFill":hdBasicFill,
	"BasicLine":hdBasicLine,
	"BendFilter":hdBendFilter,
	"Block":hdBlock,
	"Brush":hdBrush,
	"BrushList":hdList,
	"BrushTip":hdBrushTip,
	"BrushStroke":hdBrushStroke,
	"CalligraphicStroke":hdCalligraphicStroke,
	"ClipGroup":hdGroup,
	"Color6":hdColor6,
	"CompositePath":hdCompositePath,
	"CustomProc":hdCustomProc,
	"Data":hdData,
	"DataList":hdDataList,
	"DisplayText":hdDisplayText,
	"ElemPropLst":hdElemPropLst,
	"FileDescriptor":hdFileDescriptor,
	"FilterAttributeHolder":hdFilterAttributeHolder,
	"FHTail":hdFHTail,
	"FWBlurFilter":hdFWBlurFilter,
	"FWGlowFilter":hdFWGlowFilter,
	"FWShadowFilter":hdFWShadowFilter,
	"GraphicStyle":hdGraphicStyle,
	"Group":hdGroup,
	"Guides":hdGuides,
	"Halftone":hdHalftone,
	"ImageImport":hdImageImport,
	"Layer":hdLayer,
	"LensFill":hdLensFill,
	"LinearFill":hdLinearFill,
	"LinePat":hdLinePat,
	"List":hdList,
	"MList":hdList,
	"MName":hdString,
	"MString":hdString,
	"MultiColorList":hdMultiColorList,
	"NewBlend":hdNewBlend,
	"NewContourFill":hdNewContourFill,
	"NewRadialFill":hdNewRadialFill,
	"Oval":hdOval,
	"PantoneColor":hdPantoneColor,
	"Path":hdPath,
	"PathPoint":hdPathPoint,
	"PathText":hdPathText,
	"Paragraph":hdParagraph,
	"ProcessColor":hdProcessColor,
	"PropLst":hdPropLst,
	"RadialFill":hdRadialFill,
	"Rectangle":hdRectangle,
	"SpotColor":hdSpotColor,
	"SpotColor6":hdSpotColor6,
	"StylePropLst":hdStylePropLst,
	"SymbolClass":hdSymbolClass,
	"TaperedFill":hdTaperedFill,
	"TaperedFillX":hdTaperedFillX,
	"TileFill":hdTileFill,
	"TintColor":hdSpotColor,
	"TintColor6":hdTintColor6,
	"TFOnPath":hdTFOnPath,
	"TextChar":hdTextChar,
	"TextColumn":hdTFOnPath,
	"TextEffs":hdTextEffs,
	"TextEffsData":hdTextEffsData,
	"TextInPath":hdTFOnPath,
	"TextPara":hdTextPara,
	"TextString":hdTextString,
	"TEffect":hdTEffect,
	"TString":hdTString,
	"TransformFilter":hdTransformFilter,
	"VDict":hdTEffect,
	"VMpObj":hdVMpObj,
	"Xform":hdXform,
	"dval":hdDictVal,
	}


def read_recid(data,off):
	if data[off:off+2] == '\xFF\xFF' or data[off:off+2] == '\xFF\xFE':
		rid = struct.unpack('>i', data[off:off+4])[0]
		return 4,rid,">I"
	rid = struct.unpack('>h', data[off:off+2])[0]
	return 2,rid,">H"

class Xform():
	scaleX = 1
	skewV = 0
	skewH = 0
	scaleY = 1
	dX = 0
	dy = 0

class FHDoc():
	def __init__(self,data,page,parent):
		self.data = data
		self.iter = parent
		self.dictitems = {}
		self.dictitems["FHTail"] = "FHTail"
		if page != None:
			self.page = page
			self.version = page.version
			self.diter = add_pgiter(page,"FH Data","fh","data",self.data,self.iter)
		self.page.diter = self.diter
		self.reclist = []
		self.recs = {}
		# for graph
		self.nodes = {}
		self.edges = []

		self.chunks = {
		"FHTail":self.fhtail, # false record for parsing purposes
		"AGDFont":self.AGDFont,
		"AGDSelection":self.AGDSelection,
		"ArrowPath":self.ArrowPath,
		"AttributeHolder":self.AttributeHolder,
		"BasicFill":self.BasicFill,
		"BasicLine":self.BasicLine,
		"BendFilter":self.BendFilter,
		"Block":self.Block,
		"BrushList":self.BrushList,
		"Brush":self.Brush,
		"BrushStroke":self.BrushStroke,
		"BrushTip":self.BrushTip,
		"CalligraphicStroke":self.CalligraphicStroke,
		"CharacterFill":self.CharacterFill,
		"ClipGroup":self.ClipGroup,
		"Collector":self.Collector,
		"Color6":self.Color6,
		"CompositePath":self.CompositePath,
		"ConeFill":self.ConeFill,
		"ConnectorLine":self.ConnectorLine,
		"ContentFill":self.ContentFill,
		"ContourFill":self.ContourFill,
		"CustomProc":self.CustomProc,
		"DataList":self.DataList,
		"Data":self.Data,
		"DateTime":self.DateTime,
		"DisplayText":self.DisplayText,
		"DuetFilter":self.DuetFilter,
		"Element":self.Element,
		"ElemList":self.ElemList,
		"ElemPropLst":self.ElemPropLst,
		"Envelope":self.Envelope,
		"ExpandFilter":self.ExpandFilter,
		"Extrusion":self.Extrusion,
		"FHDocHeader":self.FHDocHeader,
		"Figure":self.Figure,
		"FileDescriptor":self.FileDescriptor,
		"FilterAttributeHolder":self.FilterAttributeHolder,
		"FWBevelFilter":self.FWBevelFilter,
		"FWBlurFilter":self.FWBlurFilter,
		"FWFeatherFilter":self.FWFeatherFilter,
		"FWGlowFilter":self.FWGlowFilter,
		"FWShadowFilter":self.FWShadowFilter,
		"FWSharpenFilter":self.FWSharpenFilter,
		"GradientMaskFilter":self.GradientMaskFilter,
		"GraphicStyle":self.GraphicStyle,
		"Group":self.Group,
		"Guides":self.Guides,
		"Halftone":self.Halftone,
		"ImageFill":self.ImageFill,
		"ImageImport":self.ImageImport,
		"Import":self.Import,
		"Layer":self.Layer,
		"LensFill":self.LensFill,
		"LinearFill":self.LinearFill,
		"LinePat":self.LinePat,
		"LineTable":self.LineTable,
		"List":self.List,
		"MasterPageDocMan":self.MasterPageDocMan,
		"MasterPageElement":self.MasterPageElement,
		"MasterPageLayerElement":self.MasterPageLayerElement,
		"MasterPageLayerInstance":self.MasterPageLayerInstance,
		"MasterPageSymbolClass":self.MasterPageSymbolClass,
		"MasterPageSymbolInstance":self.MasterPageSymbolInstance,
		"MDict":self.MDict,
		"MList":self.MList,
		"MName":self.MName,
		"MpObject":self.MpObject,
		"MQuickDict":self.MQuickDict,
		"MString":self.MString,
		"MultiBlend":self.MultiBlend,
		"MultiColorList":self.MultiColorList,
		"NewBlend":self.NewBlend,
		"NewContourFill":self.NewContourFill,
		"NewRadialFill":self.NewRadialFill,
		"OpacityFilter":self.OpacityFilter,
		"Oval":self.Oval,
		"PantoneColor":self.PantoneColor,
		"Paragraph":self.Paragraph,
		"Path":self.Path,
		"PathText":self.PathText,
		"PathTextLineInfo":self.PathTextLineInfo,
		"PatternFill":self.PatternFill,
		"PatternLine":self.PatternLine,
		"PerspectiveEnvelope":self.PerspectiveEnvelope,
		"PerspectiveGrid":self.PerspectiveGrid,
		"PolygonFigure":self.PolygonFigure,
		"Procedure":self.Procedure,
		"ProcessColor":self.ProcessColor, # fh5
		"PropLst":self.PropLst,
		"PSFill":self.PSFill,
		"PSLine":self.PSLine,
		"RadialFill":self.RadialFill,
		"RadialFillX":self.RadialFillX,
		"RaggedFilter":self.RaggedFilter,
		"Rectangle":self.Rectangle,
		"SketchFilter":self.SketchFilter,
		"SpotColor":self.SpotColor,
		"SpotColor6":self.SpotColor6,
		"StylePropLst":self.StylePropLst,
		"SwfImport":self.SwfImport,
		"SymbolClass":self.SymbolClass,
		"SymbolInstance":self.SymbolInstance,
		"SymbolLibrary":self.SymbolLibrary,
		"TabTable":self.TabTable,
		"TaperedFill":self.TaperedFill,
		"TaperedFillX":self.TaperedFillX,
		"TEffect":self.TEffect,
		"TextBlok":self.TextBlok,
		"TextColumn":self.TextColumn,
		"TextEffs":self.TextEffs, # ver3 for TEffect?
		"TextInPath":self.TextInPath,
		"TFOnPath":self.TFOnPath,
		"TileFill":self.TileFill,
		"TintColor":self.TintColor,
		"TintColor6":self.TintColor6,
		"TransformFilter":self.TransformFilter,
		"TString":self.TString,
		"UString":self.UString,
		"VDict":self.VDict,
		"VMpObj":self.VMpObj,
		"Xform":self.Xform
	}

	def read_recid(self,off):
		if self.data[off:off+2] == '\xFF\xFF' or self.data[off:off+2] == '\xFF\xFE':
			rid = struct.unpack('>i', self.data[off:off+4])[0]
			return 4,rid
		rid = struct.unpack('>h', self.data[off:off+2])[0]
		return 2,rid

	def AGDSelection(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length=4*size+8
		return length

	def ArrowPath(self,off,recid,mode=0):
		subZone=[]
		# version 8 'reserves' place for points
		# actual number of points is at offset 20
		if self.version > 8:
			size =  struct.unpack('>h', self.data[off+20:off+22])[0]
		else:
			size = struct.unpack('>h', self.data[off:off+2])[0]
		res=30
		if self.version < 5:
			res -= 4
		for i in range(size):
			subZone.append(("point%d"%i,"PathPoint",off+res,27))
			res += 27
		return res, subZone

	def AttributeHolder(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		return res+L

	def BasicFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+4

	def BasicLine(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+18

	def BendFilter(self,off,recid,mode=0):
		return 10

	def Block(self,off,recid,mode=0):
		if self.version == 10:
			flags =  struct.unpack('>h', self.data[off:off+2])[0]
			res = 2
			for i in range(21):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
			res += 1
			for i in range(2):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
		elif self.version == 8:
			res = 0
			for i in range(12):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
			res += 14
		elif self.version < 8:
			res = 0
			for i in range(11):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
			res += 10
			for i in range(3):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
		else:
			# FIXME! ver11 starts with size==7
			res = 0
			for i in range(12):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
			res += 14
			for i in range(3):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
			res +=1
			for i in range(4):
				L,rid1 = self.read_recid(off+res)
				self.edges.append((recid,rid1))
				res += L
			# verify for v9
			if self.version < 10:
				res -= 6
		return res

	def Brush(self,off,recid,mode=0):
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		return res

	def BrushList(self,off,recid,mode=0):
		size =  struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 12
		for i in range(size):
			L,rid1 = self.read_recid(off+res)
			self.edges.append((recid,rid1))
			res += L
		return res

	def BrushStroke(self,off,recid,mode=0):
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		res += 2
		return res

	def BrushTip(self,off,recid,mode=0):
		type = struct.unpack('>h', self.data[off:off+2])[0]
		length= 60
		if self.version == 11:
			length=64
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		return length+res

	def CalligraphicStroke(self,off,recid,mode=0):
		# rec_id1
		# 12 bytes ??
		# rec_id2
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		res += 12
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		return res

	def CharacterFill(self,off,recid,mode=0):
		# Warning! Flag?
		return 0

	def ClipGroup(self,off,recid,mode=0):
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		L,rid1 = self.read_recid(off+8+res)
		self.edges.append((recid,rid1))
		res += L
		return res+10

	def Collector(self,off,recid,mode=0):
		# FIXME! don't have test files for this one
		return 4


	def Color6(self,off,recid,mode=0):
		length=24
		var = ord(self.data[off+1])
		if var == 4:
			length=28
		if var == 7:
			length=40
		if var == 9:
			length=48
		if self.version < 10:
			length-=2
		res,rid1 = self.read_recid(off+2)
		self.edges.append((recid,rid1))
		L,rid = self.read_recid(off+12+res)
		self.edges.append((recid,rid))
		return res+length+L

	def CompositePath(self,off,recid,mode=0):
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		res += 4
		if self.version > 4:
			res += 4
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		return res

	def ConeFill(self,off,recid,mode=0):
		res,rid1 = self.read_recid(off)
		self.edges.append((recid,rid1))
		L,rid1 = self.read_recid(off+res)
		self.edges.append((recid,rid1))
		res += L
		L,rid1 = self.read_recid(off+16+res)
		self.edges.append((recid,rid1))
		res += L
		return res+30

	def ConnectorLine(self,off,recid,mode=0):
		num = struct.unpack('>h', self.data[off+20:off+22])[0]
		length= 58+num*27
		return length

	def ContentFill(self,off,recid,mode=0):
		# FIXME! Flag?
		return 0

	def ContourFill(self,off,recid,mode=0):
		if self.version > 9:
			length = 24
		else:
			num = struct.unpack('>h', self.data[off+0:off+2])[0]
			size= struct.unpack('>h', self.data[off+2:off+4])[0]
			length = 0
			while num !=0:
				length = length +10+size*2
				num = struct.unpack('>h', self.data[off+0+length:off+2+length])[0]
				size= struct.unpack('>h', self.data[off+2+length:off+4+length])[0]
			length = length +10+size*2
		return length

	def CustomProc(self,off,recid,mode=0):
		# size (w)
		# rec_id (name?)
		# 2 words ??
		# records (10 bytes each)
		subZone=[]
		size = struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		res += 6  # size and 2 words
		for i in range(size):
			subZone.append((i,"CustomProcData",off+res,10))
			res += 10
		return res,subZone

	def Data(self,off,recid,mode=0):
		size = struct.unpack('>H', self.data[off:off+2])[0]
		length= 6+size*4
		return length

	def DataList(self,off,recid,mode=0):
		size= struct.unpack('>h', self.data[off:off+2])[0]
		res = 10
		for i in range(size):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		return res

	def DateTime(self,off,recid,mode=0):
		return 14

	def DT_fh3_styles(self,off,offset):
		offset += 2
		flags = struct.unpack(">h", self.data[off+offset:off+offset+2])[0]
		offset += 2
		if flags & 1:  # 2.2 float
			offset += 4
		if flags & 2: # 2.2 kerning
			offset += 4
		if flags & 4: # font name rec_id
			if self.data[off+offset:off+offset+2] == "\xff\xff":
				offset += 2
			offset += 2
		if flags & 8: # font size
			offset += 4
		if flags & 0x10:
			offset += 4
		if flags & 0x20: # font style bytes
			offset += 4
		if flags & 0x40: # font clr rec_id
			if self.data[off+offset:off+offset+2] == "\xff\xff":
				offset += 2
			offset += 2
		if flags & 0x80: # font TextEffs rec_id
			if self.data[off+offset:off+offset+2] == "\xff\xff":
				offset += 2
			offset += 2
		if flags & 0x100: # ???
			offset += 4
		if flags & 0x200: # ???
			offset += 4
		if flags & 0x400: # para hor.scale
			offset += 4
		if flags & 0x800: # baseline shift
			offset += 4
		if flags >= 0x1000:
			print "NEW FLAG IN DISPLAY TEXT!"
		return offset

	def DisplayText(self,off,recid,mode=0):
		# ver < 5
		subZone=[]
		txtlen = struct.unpack('>H', self.data[off+0x4c:off+0x4e])[0]
		offset = 0x50
		while True:
			cOffset=struct.unpack(">h", self.data[off+offset:off+offset+2])[0]
			newOffset = self.DT_fh3_styles(off,offset)
			subZone.append(("TextChar","TextChar",off+offset,newOffset-offset))
			offset=newOffset
			if cOffset>=txtlen:
				break
		while True:
			pOffset=struct.unpack(">h", self.data[off+offset:off+offset+2])[0]
			subZone.append(("TextPara","TextPara",off+offset,30))
			offset += 30
			if pOffset >= txtlen:
				break
		if txtlen>0:
			subZone.append(("TextString","TextString",off+offset,txtlen))
		return offset+1+txtlen,subZone

	def DuetFilter(self,off,recid,mode=0):
		return 14

	def Element(self,off,recid,mode=0):
		return 4

	def ElemList(self,off,recid,mode=0):
		return 4

	def ElemPropLst(self,off,recid,mode=0):
		# FIXME! one more read_recid @6 ?
		if self.version > 8:
			size = struct.unpack('>h', self.data[off+2:off+4])[0]
		else:
			# v8 seems to reserve space
			size = struct.unpack('>h', self.data[off:off+2])[0]
		res = 10
		if size != 0:
			for i in range(size*2):
				l,rid = self.read_recid(off+res)
				self.edges.append((recid,rid))
				res += l
		return res

	def Envelope (self,off,recid,mode=0):
		# 2 bytes ??
		# rec_id1, rec_id2
		# 14 bytes ??
		# #ofpts (w)
		# rec_id3
		# 19 bytes ??
		# #ofdwords ?? (w)
		# 4*#ofdwords ??
		# 27*#ofpts
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+2+res)
		self.edges.append((recid,rid))
		res += L
		num = struct.unpack('>h', self.data[off+res+16:off+res+18])[0]
		L,rid = self.read_recid(off+res+18)
		self.edges.append((recid,rid))
		res += L
		num2 = struct.unpack('>h', self.data[off+res+37:off+res+39])[0]
		length = 39+res+num2*4+num*27
		return length

	def ExpandFilter(self,off,recid,mode=0):
		return 14

	def Extrusion(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		var1 = ord(self.data[off+0x60])
		var2 = ord(self.data[off+0x61])
		length= res + 92 + self.xform_calc(var1,var2)[0] +2
		return length

	def Figure (self,off,recid,mode=0):
		return 4

	def FHDocHeader(self,off,recid,mode=0):
		# FIXME!
		return 4

	def FilterAttributeHolder(self,off,recid,mode=0):
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+2+res)
		self.edges.append((recid,rid))
		res += L
		return res+2

	def FWSharpenFilter(self,off,recid,mode=0):
		# FIXME! recid
		return 16

	def FileDescriptor(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		size = struct.unpack('>h', self.data[off+5+res:off+7+res])[0]
		res += 7+size
		return res

	def FWBevelFilter(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+28

	def FWBlurFilter(self,off,recid,mode=0):
		# FIXME! recid
		return 12

	def FWFeatherFilter(self,off,recid,mode=0):
		#FIXME! recid
		return 8

	def FWGlowFilter(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+20

	def FWShadowFilter(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+20

	def GradientMaskFilter(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res

	def GraphicStyle(self,off,recid,mode=0):
		size = 2*struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 6
		for i in range(2+size):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		return res

	def Group(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		if self.version > 4:
			L,rid = self.read_recid(off+res+8)
			self.edges.append((recid,rid))
			res += L
			L,rid = self.read_recid(off+res+8)
			self.edges.append((recid,rid))
			res += L
		return res+8

	def Guides(self,off,recid,mode=0):
		size =  struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+2+res)
		self.edges.append((recid,rid))
		res += L
		res += 18 + size*8
		if self.version < 5:
			res -= 4
		return res

	def Halftone(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+8

	def ImageFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		#FIXME! more recid?
		return 4+res

	def ImageImport(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L+4
		if self.version > 3:
			res += 4
		if self.version > 8:
			# Format Name
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		shift = 0
		for i in range(3):  # DataList, FileDsecriptor, XForm
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		shift += 8
		# Size W/H
		shift += 8
		# skip 6
		shift += 6
		# Size W/H
		shift += 4
		# skip 4
		shift += 4
		# Size W/H
		shift += 4
		# skip format name string
		if self.version > 8:
			till0 = 0
			while ord(self.data[off+shift+res+till0]) != 0:
				till0 += 1
			shift += till0+1
		if self.version > 10:
			shift += 2
		return shift+res

	def Import(self, off,recid,mode=0):
		return 34;

	def Layer(self,off,recid,mode=0):
		length=14
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+10+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+12+res)
		self.edges.append((recid,rid))
		res += L
		if self.version < 5:
			length -= 4
		return length+res

	def LensFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		return res+38

	def LinearFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+12+res)
		self.edges.append((recid,rid))
		res += L
		return res+28

	def LinePat(self,off,recid,mode=0):
		numstrokes = struct.unpack('>h', self.data[off:off+2])[0]
		res = 10+numstrokes*4
		if numstrokes == 0 and self.version == 8:
			res = 28 # for Ver8, to skip 1st 14 bytes of 0s
		return res

	def LineTable(self,off,recid,mode=0):
		# dw ??
		# "size" (dw)
		# records of 48 bytes + rec_id
		size= struct.unpack('>h', self.data[off+2:off+4])[0]
		if self.version < 10:
			size= struct.unpack('>h', self.data[off:off+2])[0]
		res = 0
		for i in range(size):
			L,rid = self.read_recid(off+52+i*48+res)
			self.edges.append((recid,rid))
			res += L
		return res+4+size*48

	def List(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 12
		for i in range(size):
			l,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += l
		if self.version < 9: # verify for others
			size2 = struct.unpack('>h', self.data[off:off+2])[0]
			res += (size2-size)*2
#		if self.version == 5:
#			res = 32 # probably alignment
		return res

	def MasterPageElement(self,off,recid,mode=0):
		return 14

	def MasterPageDocMan(self,off,recid,mode=0):
		return 4

	def MasterPageLayerElement(self,off,recid,mode=0):
		return 14

	def MasterPageLayerInstance(self,off,recid,mode=0):
		var1 = ord(self.data[off+0xe])
		var2 = ord(self.data[off+0xf])
		length=14 + self.xform_calc(var1,var2)[0]+2 +2
		return length

	def MasterPageSymbolClass(self,off,recid,mode=0):
		return 12

	def MasterPageSymbolInstance(self,off,recid,mode=0):
		var1 = ord(self.data[off+0xe])
		var2 = ord(self.data[off+0xf])
		length=14 + self.xform_calc(var1,var2)[0]+2 +2
		return length

	def MList(self,off,recid,mode=0):
		return self.List(off,recid,mode)

	def MName(self,off,recid,mode=0):
		size = struct.unpack('>H', self.data[off:off+2])[0]
		length = struct.unpack('>H', self.data[off+2:off+4])[0]
		self.recs[recid] = ("str",unicode(self.data[off+4:off+4+length],"mac-roman"))
		return 4*(size+1)

	def MQuickDict(self,off,recid,mode=0):
		size =  struct.unpack('>h', self.data[off+0:off+2])[0]
		return 7 + size*4

	def MString(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length = struct.unpack('>H', self.data[off+2:off+4])[0]
		self.recs[recid] = ("str",unicode(self.data[off+4:off+4+length],"mac-roman"))
		return 4*(size+1)

	def MDict(self,off,recid,mode=0):
		# "xx xx xx" -- size
		# (rec_id1,rec_id2)*size
		size =  struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 6
		for i in range(size):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		return res

	def MpObject (self,off,recid,mode=0):
		return 4

	def MultiBlend(self,off,recid,mode=0):
		# "size??" (dw)
		# rec_id1, rec_id2
		# 8 bytes ??
		# rec_id3, rec_id4, rec_id5
		# 32 bytes ??
		# size*6 ??  FIXME!
		size = struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+2+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+10+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+10+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+10+res)
		self.edges.append((recid,rid))
		res += L
		return 42 + size*6 + res

	def MultiColorList(self,off,recid,mode=0):
		num= struct.unpack('>h', self.data[off:off+2])[0]
		res = 0
		for i in range(num):
				L,rid = self.read_recid(off+4+i*8+res)
				self.edges.append((recid,rid))
				res += L
		return num*8+res+4

	def NewBlend(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+8+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+8+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+8+res)
		self.edges.append((recid,rid))
		res += L
		return res+34

	def NewContourFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+14+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+14+res)
		self.edges.append((recid,rid))
		res += L
		return res+28

	def NewRadialFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+16+res)
		self.edges.append((recid,rid))
		res += L
		return res+39

	def OpacityFilter(self,off,recid,mode=0):
		return 4

	def Oval(self,off,recid,mode=0):
		if self.version > 10:
			length=38
		elif self.version > 3:
			length=28
		else:
			length=26
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		if self.version > 3:
			L,rid = self.read_recid(off+12+res)
			self.edges.append((recid,rid))
			res += L
		return length+res


	def PantoneColor(self,off,recid,mode=0):
		# version 5 and earlier
		return 38

	def Paragraph(self,off,recid,mode=0):
		if self.version > 7:
			size= struct.unpack('>h', self.data[off+2:off+4])[0]
			res = 6
			for i in range(2):
				L,rid = self.read_recid(off+res)
				self.edges.append((recid,rid))
				res += L
			for i in range(size):
				L,rid = self.read_recid(off+res+2)
				res += L + 22
		else:
			trsize = struct.unpack('>h', self.data[off:off+2])[0]
			size2 = struct.unpack('>h', self.data[off+2:off+4])[0]
			recs = struct.unpack('>h', self.data[off+4:off+6])[0]
			res = 6
			for i in range(4):
				L,rid = self.read_recid(off+res)
				self.edges.append((recid,rid))
				res += L
			res += 20
			res += recs*24
			if size2 > 1:
				for i in range(size2):
					L,rid = self.read_recid(off+res)
					self.edges.append((recid,rid))
					res += L
				res += 20
			elif recs > 0:
				res += trsize+1
		return res

	def PathText(self,off,recid,mode=0):
		res=off
		for i in range(2):
			l,rid = self.read_recid(res+2)
			res+=l
		res+=8
		for i in range(2):
			l,rid = self.read_recid(res+2)
			res+=l
		return res-off
	def PathTextLineInfo(self,off,recid,mode=0):
		# FIXME!
		# SHOULD BE VARIABLE, just have no idea about base and multiplier
		length= 46
		return length

	def PatternFill(self,off,recid,mode=0):
		return 10

	def Path(self,off,recid,mode=0):
		subZone = []
		size =  struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+2+res)
		self.edges.append((recid,rid))
		res += L
		if self.version > 8:
			size = struct.unpack('>h', self.data[off+16+res:off+18+res])[0]
		res += 18
		if self.version < 5:
			res -= 4
		for i in range(size):
			subZone.append(("point%d"%i,"PathPoint",off+res,27))
			res += 27
		return res, subZone

	def PatternLine(self,off,recid,mode=0):
		# 0-2 -- link to Color
		# 2-10 -- bitmap of the pattern
		# 10-14 -- mitter?
		# 14-16 -- width?
		length= 22
		return length

	def PSFill(self,off,recid,mode=0):
		length= 4
		return length

	def PSLine(self,off,recid,mode=0):
		# 0-2 -- link to Color
		# 2-4 -- link to UString with PS commands
		# 4-6 width
		length= 8
		return length

	def PerspectiveEnvelope(self,off,recid,mode=0):
		return 177

	def PerspectiveGrid(self,off,recid,mode=0):
		i = 0
		while ord(self.data[off+i]) != 0:
			i += 1
		length=59+i
		return length

	def PolygonFigure(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+12+res)
		self.edges.append((recid,rid))
		res += L
		return res+47

	def Procedure (self,off,recid,mode=0):
		return 4

	def ProcessColor (self,off,recid,mode=0):
		return 22

	def PropLst(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 8
		for i in range(2*size):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		if self.version < 9: # verify for others
			size2 = struct.unpack('>h', self.data[off:off+2])[0]
			for i in range(2*(size2-size)):
				L,rid = self.read_recid(off+res)
				res += L
		return res

	def RadialFill(self,off,recid,mode=0):
		return 16

	def RadialFillX(self,off,recid,mode=0):
		# v11 rec_id from 0x10
		length=20
		res,rid = self.read_recid(off+20)
		self.edges.append((recid,rid))
		return length+res


	def RaggedFilter(self,off,recid,mode=0):
		return 16

	def Rectangle(self,off,recid,mode=0):
		length=69 #?ver11?
		if self.version < 11:
			length = 36
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		if self.version > 3:
			L,rid = self.read_recid(off+12+res)
			self.edges.append((recid,rid))
			res += L
		if self.version < 5:
			length -= 2
		return length+res

	def SketchFilter(self,off,recid,mode=0):
		return 11

	def SpotColor(self,off,recid,mode=0):
		# 1st seen in ver5
		return 26


	def SpotColor6(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		shift,recid1 = self.read_recid(off+2)
		self.edges.append((recid,recid1))
		print "SPC6",recid,recid1
		res = 26 + size*4 + shift
#		FIXME! verify it
		if self.version < 10:
			res -= 2
		return res

	def SwfImport(self,off,recid,mode=0):
		#FIXME! recid
		return 43

	def StylePropLst(self,off,recid,mode=0):
		if self.version > 8:
			size = struct.unpack('>h', self.data[off+2:off+4])[0]
		else:
			# v8 seems to reserve space
			size = struct.unpack('>h', self.data[off:off+2])[0]
		res = 6
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		for i in range(size*2):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		return res

	def SymbolClass(self,off,recid,mode=0):
		res = 0
		for i in range(5):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		return res

	def SymbolInstance(self,off,recid,mode=0):
		shift = 0
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+res+8)
		self.edges.append((recid,rid))
		res += L
		var1 = ord(self.data[off+res+8])
		var2 = ord(self.data[off+res+9])
		return 10 + res + self.xform_calc(var1,var2)[0]

	def SymbolLibrary(self,off,recid,mode=0):
		size =  struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 12
		for i in range(size+3):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		return res

	def TabTable(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		res = 4+size*6
		if self.version < 10:
			res = 4+size*2
		return res

	def TaperedFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		return 8+res

	def TaperedFillX(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		# dword for angle
		res += L+12
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		return res

	def TEffect(self,off,recid,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 8
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			rec = struct.unpack('>h', self.data[off+shift+2:off+shift+4])[0]
			if not rec in teff_rec:
				print 'Unknown TEffect record: %04x'%rec
			if key == 2:
				shift+=4
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L
			else:
				shift+=8
		return shift

	def TextEffs(self,off,recid,mode=0):
		subZone=[]
		# ver 3 only?
		num = struct.unpack('>h', self.data[off:off+2])[0] # or @0x12
		if num==0:
			return 0x16
		shift = 0x18
		for i in range(num):
			begShift=shift
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			rec = struct.unpack('>h', self.data[off+shift+2:off+shift+4])[0]
			if rec == 7:
				shift += 12
				key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
				if key == 0:
					shift += 4
			else:
				shift += 16
			subZone.append(("TextEffsData","TextEffsData",off+begShift,shift-begShift))
		return shift,subZone


	def TextBlok(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length = struct.unpack('>H', self.data[off+2:off+4])[0]
		#FIXME! have more data after string
		self.recs[recid] = ("str",unicode(self.data[off+4:off+4+length*2],"utf-16be"))
		return 4+size*4

	def TextColumn(self,off,recid,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		res = 8
		for i in range(2):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		res += 8  # FIXME! check if those are recIDs
		for i in range(3):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L

		for i in range(num):
			key = struct.unpack('>h', self.data[off+res:off+res+2])[0]
			if key == 2:
				res+=4
				L,rid = self.read_recid(off+res)
				self.edges.append((recid,rid))
				res += L
			else:
				res+=8
		return res

	def TFOnPath(self,off,recid,mode=0):
		# "xx yy zz xx"
		# "00 00"
		# rec_id1
		# 8 bytes ??
		# rec_id2, rec_id3, rec_id4
		# zz records
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 10
		L,rid = self.read_recid(off+shift)
		self.edges.append((recid,rid))
		shift += L
		shift += 8
		L,rid = self.read_recid(off+shift)
		self.edges.append((recid,rid))
		shift += L
		L,rid = self.read_recid(off+shift)
		self.edges.append((recid,rid))
		shift += L
		L,rid = self.read_recid(off+shift)
		self.edges.append((recid,rid))
		shift += L
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			if key == 2:
				shift+=4
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L
			else:
				shift+=8
		return shift

	def TextInPath(self,off,recid,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		if self.version > 7:
			shift = 8
			for i in range(5):
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L
			# hack. no other way so far.
			if self.data[off+shift:off+shift+4] == "\xFF\xFF\xFF\xFF":
				shift+=2
			for i in range(3):
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L

			for i in range(num):
				key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
				if key == 2:
					shift+=4
					L,rid = self.read_recid(off+shift)
					self.edges.append((recid,rid))
					shift += L
				else:
					shift+=8
		else:
			shift = 20
			for i in range(3):
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L
			if not num%2: #FIXME!
				num -= 1
			for i in range(num):
				key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
				if key == 2:
					shift+=4
					L,rid = self.read_recid(off+shift)
					self.edges.append((recid,rid))
					shift += L
				else:
					shift+=8
		return shift

	def TileFill(self,off,recid,mode=0):
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		return res+28

	def TintColor(self,off,recid,mode=0):
		# 1st seen in ver 5
		return 20

	def TintColor6(self,off,recid,mode=0):
		shift = 16
		if self.version < 8:
			shift = 14
		res,rid = self.read_recid(off+shift)
		self.edges.append((recid,rid))
		if self.version < 10:
			res -= 2
		return res+36

	def TransformFilter(self,off,recid,mode=0):
		return 39

	def TString(self,off,recid,mode=0):
		size= struct.unpack('>h', self.data[off+2:off+4])[0]
		res=20
		for i in range(size):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		if self.version < 9: # verify for others
			size2 = struct.unpack('>h', self.data[off:off+2])[0]
			res += (size2-size)*2

		return res

	def UString(self,off,recid,mode=0):
		size = struct.unpack('>H', self.data[off:off+2])[0]
		length = struct.unpack('>H', self.data[off+2:off+4])[0]
		res=4*(size+1)
		self.recs[recid] = ("str",unicode(self.data[off+4:off+4+length*2],"utf-16be"))
		if mode == 0:
			return res

	def VDict(self,off,recid,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 8
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			if key == 2:
				shift+=4
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L
			else:
				shift+=8
		return shift

	def AGDFont (self,off,recid,mode=0):
		res = self.VMpObj(off,recid,mode)
		return res

	def VMpObj (self,off,recid,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 8
		# FIXME!
		# ver 9: 00 36 00 23 00 22 00 36  ++18 bytes before usual structures start
#		mod = struct.unpack('>h', self.data[off:off+2])[0]
#		if mod == 0x36:
#			shift += 18
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			rec = struct.unpack('>h', self.data[off+shift+2:off+shift+4])[0]
# Activate for debug
#			if not rec in vmp_rec:
#				print 'Unknown VMpObj record: %04x'%rec
			if key == 2:
				shift+=4
				L,rid = self.read_recid(off+shift)
				self.edges.append((recid,rid))
				shift += L
			else:
				shift+=8

		return shift


	def xform_calc(self,var1,var2):
		a5 = not (var1&0x20)/0x20
		a4 = not (var1&0x10)/0x10
		a2 = (var1&0x4)/0x4
		a1 = (var1&0x2)/0x2
		a0 = (var1&0x1)/0x1
		b6 = (var2&0x40)/0x40
		b5 = (var2&0x20)/0x20
		if a2:
			return 0,()
		xlen = (a5+a4+a1+a0+b6+b5)*4
		return xlen,(a4,b6,b5,a5,a0,a1)

	def Xform(self,off,recid,mode=0):
		var1 = ord(self.data[off])
		var2 = ord(self.data[off+1])
		len1,x = self.xform_calc(var1,var2)
		var1 = ord(self.data[off+len1+2])
		var2 = ord(self.data[off+len1+3])
		len2,x = self.xform_calc(var1,var2)
		length = len1+len2+4
		if self.version < 9:
			length = 52
		return length

	def fhtail(self,off,recid,mode=0):
		print "FH Tail!"
		L1,recid1 = self.read_recid(off)
		L2,recid2 = self.read_recid(off+L1)
		L3,recid3 = self.read_recid(off+L1+L2)
		self.edges.append((recid,recid1))
		self.edges.append((recid,recid2))
		self.edges.append((recid,recid3))
		if self.version > 8:
			L4,recid4 = self.read_recid(off+L1+L2+L3+100)
			self.edges.append((recid,recid4))
		return len(self.data) - off

	def parse_agd_iter (self, step=500, offset=0, start=0, num=-1):
		j = start
		self.page.view.freeze_child_notify()
		for i in self.reclist[start:]:
			j += 1
			if j%5000 == 0:
				print j
			if self.dictitems[i] in self.chunks:
				#try:
				if 1:
					res = self.chunks[self.dictitems[i]](offset,j)
					subList=[]
					if type(res) is int:
						rLen=res
					else:
						rLen,subList=res
					if -1 < rLen <= len(self.data)-offset:
						uid = ""
						if self.dictitems[i] in ("ImageImport","polygonFigure","Extrusion","Layer","Rectangle","Oval","ClipGroup","Group","CompositePath"):
							uid = "(%02x)"%(struct.unpack(">H",self.data[offset+6:offset+8])[0])
						elif self.dictitems[i] == "Path":
							uid = "(%02x)"%(struct.unpack(">H",self.data[offset+8:offset+10])[0])
						elif self.dictitems[i] == "TextColumn":
							uid = "(%02x)"%(struct.unpack(">H",self.data[offset+14:offset+16])[0])
						niter = add_pgiter(self.page,"[%02x] %s %s"%(j,self.dictitems[i],uid),"fh",self.dictitems[i],self.data[offset:offset+rLen],self.diter)
						self.page.model.set_value(niter,4,(j-1,offset))
						offset += rLen
						if uid != "":
							print self.dictitems[i],uid
						self.nodes[j] = (self.dictitems[i],niter)
						for i in range(len(subList)):
							subName,subType,subOff,subLen=subList[i]
							subData=self.data[subOff:subOff+subLen]
							add_pgiter(self.page,subName,"fh",subType,subData,niter)
					else:
						add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
						for k in range(10):
							try:
								add_pgiter(self.page,"!!! %s"%self.dictitems[self.reclist[i+k]],"fh","unknown","",self.diter)
							except:
								print "kk",k
						print "Failed on record %d (%s)"%(j,self.dictitems[i]),rLen
						print "Next is",self.dictitems[self.reclist[j+1]]
						return
				#except:
				#	add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
				#	print "Failed on record %d (%s)"%(j,self.dictitems[i])
				#	print "Next is",self.dictitems[self.reclist[j+1]]
				#	return

			else:
					print "Unknown record type: %s (%02x)"%(self.dictitems[i],j)
					add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
					if j < len(self.reclist):
						add_pgiter(self.page,"!!! %s"%self.dictitems[self.reclist[j]],"fh","unknown","",self.diter)
					return
			if (j % step) == 0:
				self.page.view.thaw_child_notify()
				yield True
				self.page.view.freeze_child_notify()

		self.page.view.thaw_child_notify()
		# stop idle_add()
		yield False

	def parse_agd(self,off=0,start=0):
		if start == 0:
			self.reclist.append("FHTail")
		loader = self.parse_agd_iter(500,off,start)
		gobject.idle_add(loader.next)

	def parse_list(self,data,offset):
		size = struct.unpack('>L', data[offset:offset+4])[0]
		print '# of items:\t%u'%size
		offset+= 4
		for i in range(size):
			key = struct.unpack('>h', data[offset:offset+2])[0]
			offset+= 2
			self.reclist.append(key)
		self.page.reclist = self.reclist

	def parse_dict (self,data,offset):
		dictsize = struct.unpack('>h', data[offset:offset+2])[0]
		print 'Dict size:\t%u'%dictsize
		dictiter = add_pgiter(self.page,"FH Dictionary","fh","dict","",self.iter)
		offset+=4
		if self.version > 8:
			for i in range(dictsize):
				key = struct.unpack('>h', data[offset:offset+2])[0]
				k = 0
				while ord(data[offset+k+2]) != 0:
					k+=1
				value = data[offset+2:offset+k+2]
				add_pgiter(self.page,"%04x %s"%(key,value),"fh","dval",data[offset:offset+k+3],dictiter)
				offset = offset+k+3
				self.dictitems[key] = value
		else:
			for i in range(dictsize):
				key = struct.unpack('>h', data[offset:offset+2])[0]
				key2 = struct.unpack('>h', data[offset+2:offset+4])[0]
				k = 0
				while ord(data[offset+k+4]) != 0:
					k+=1
				value = data[offset+4:offset+4+k]
				f = 0
				while f != 2:
					if ord(data[offset+k+5]) == 0:
						f += 1
					k+=1
				add_pgiter(self.page,"%04x %s"%(key,value),"fh","dval",data[offset:offset+k+5],dictiter)
				offset += k+5
				self.dictitems[key] = value

		self.page.dict = self.dictitems
		return offset

#---------------------------------------------------------------#

ver = {0x31:5,0x32:7,0x33:8,0x34:9,0x35:10,0x36:11,'mcl':-1}


def fh_save (page, fname):
	model = page.view.get_model()
	f = open(fname,'w')
	endptr = 0
	iter1 = model.get_iter_first()
	iter1 = model.iter_next(iter1) # 'FH Header'
	value = model.get_value(iter1,3)
	f.write(value[:len(value)-4])
	epos = len(value)-16
#	endptr += len(value)-4
	iter2 = model.iter_next(iter1) # 'FH Decompressed data'
	value = ''
	clist = {}
	for i in range(model.iter_n_children(iter2)-1):
		citer = model.iter_nth_child(iter2,i)
		value += model.get_value(citer,3)
		rname = model.get_value(citer,0)
		clist[i] = rname[0:len(rname)-5]

	citer = model.iter_nth_child(iter2,i+1) # 'FH Tail'
	value += model.get_value(citer,3)
	output = zlib.compress(value,1)
	clen = struct.pack(">L",len(output)+12)

	f.write(clen)
	f.write(output)
	endptr += 4 + len(output) + 8

	dictsize = struct.pack('>h', len(page.dict))
	f.write(dictsize)
	f.write('\x02\x04') # points to some random record ID?
	endptr += 4
	cntlist = {}
#	for k, v in page.dict.items():  # not sure if FH pays attention to dict items sequence
#		f.write(struct.pack('>h',k))
#		f.write(v[0])
#		f.write('\x00')
#		cntlist[v[0]] = k
#		endptr += 3 + len(v[0])
	iter3 = model.iter_next(iter2) # 'FH Dictionary'
	for i in range(model.iter_n_children(iter3)):
		citer = model.iter_nth_child(iter3,i)
		value = model.get_value(citer,3)
		k = value[0:2]
		v = value[2:]
		f.write(k)
		f.write(v)
		v = v[:(len(v)-1)]
		cntlist[v] = k
		endptr += 3 + len(v)

	size = struct.pack('>L', model.iter_n_children(iter2)-1) # don't count tail
	f.write(size)
	endptr += 4
	for i in range(len(clist)):
		v = cntlist[clist[i]]
		f.write(v)
	endptr += len(clist)*2
	f.write('FlateDecode\x00\xFF\xFF\xFF\xFF\x1c\x09\x0a\x00\x04')
	endptr += 16
	f.write(struct.pack(">L",endptr))
	f.seek(epos)
	f.write(struct.pack(">L",endptr))
	f.close()

typecodes = {
	"02 ca":"Preview",
	"01 46":"Date (?)",
	"01 28":"Time (?)",
	"08 0a":"AGD",
	}

def read1c(buf,page,parent,off):
	flag = ord(buf[off])
	if flag != 0x1c:
		print "FH: not an 0x1c flag in v10+"
		return len(buf)
	t1 = ord(buf[off+1])
	t2 = ord(buf[off+2])
	t3 = ord(buf[off+3])
	t4 = ord(buf[off+4])
	if t3&0x80 != 0:
		size = struct.unpack(">L",buf[off+5:off+9])[0]+4
	else:
		size = t4
	tname = "%02x %02x"%(t1,t2)
	if typecodes.has_key(tname):
		tname = typecodes[tname]
	else:
		tname += " %02x"%t3
	add_pgiter(page,"Type %s"%tname,"fh","%02x %02x %02x"%(t1,t2,t3),buf[off:off+5+size],parent)

	return off+5+size


def fh_open (buf,page,parent=None,mode=1):
	if mode:
		offset = buf.find('AGD')
		page.version = ver[ord(buf[offset+3])]
	else:
		offset = 0
		page.version = ord(buf[2])-48
	size = struct.unpack('>L', buf[offset+8:offset+12])[0]
	print 'Version:\t',page.version
	print 'Offset: \t%x'%offset
	print 'Size:\t\t%x'%size

	if page.version > 8:
		output = zlib.decompress(buf[offset+14:offset+14+size],-15)
	else:
		output = buf[offset+12:offset+size]
	if page.version > 9:
		off = 0
		while off < len(buf):
			off = read1c(buf,page,parent,off)

	piter = add_pgiter(page,"FH file","fh","file",buf,parent)
	page.dictmod = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)

	page.appdoc = FHDoc(output,page,piter)
	offset = offset + size
	offset = page.appdoc.parse_dict(buf,offset)
	try:
		page.appdoc.parse_list(buf,offset)
		page.appdoc.parse_agd()
		return "FH"
	except:
		print "Failed in FH parsing"
