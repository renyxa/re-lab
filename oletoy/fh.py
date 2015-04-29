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
				if a in page.appdoc.recs:
					at = page.appdoc.recs[a][1]
				else:
					at = "%02x"%a
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,at,shift,6,"txt")
			shift+=4
			L,rid = read_recid(data,offset+shift)
			shift += L
		else:
			add_iter (hd,rname,at,shift,8,"txt")
			shift+=8

def hdTString(hd,data,page):
	offset = 0
	num = struct.unpack('>h', data[offset+2:offset+4])[0]
	offset = 0x14
	for i in range(num):
		L,rid1 = read_recid(data,offset)
		elemtype,typestr = get_typestr(page,rid1)
		iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset,L,">H")
		offset += L

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
			L,rid = read_recid(data,offset+shift)
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
				t,r = read_recid(page.model.get_value(itr,3),0xc)
				typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
			elif itrtype in page.dict:
				typestr = " -> (%s)"%(page.dict[itrtype])
		except:
			pass
	return elemtype,typestr

def hdTFOnPath(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	L,rid1 = read_recid(data,offset+8)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset+8,L,">H")
	offset += L
	L,rid1 = read_recid(data,offset+8)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset+8,L,">H")
	offset += L+8
	for i in range(3):
		L,rid1 = read_recid(data,offset+8)
		elemtype,typestr = get_typestr(page,rid1)
		iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset+8,L,">H")
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
			L,rid = read_recid(data,offset+shift)
			shift += L
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8


def hdFHTail(hd,data,page):
	offset = 0
	L,recid = read_recid(data,0)
	add_iter (hd,'Block ID',"%02x"%recid,offset,L,">H")
	offset += L
	L,recid = read_recid(data,offset)
	add_iter (hd,'PropLst ID',"%02x"%recid,offset,L,">H")
	offset += L
	L,recid = read_recid(data,offset)
	if recid in page.appdoc.recs:
		at = page.appdoc.recs[recid][1]
	else:
		at = "%02x"%recid
	add_iter (hd,"Default Font ??",at,offset,L,">HH")
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


def hdParagraph(hd,data,page):
	offset = 0
	num = struct.unpack('>h', data[offset+2:offset+4])[0]
	offset = 6
	L,rid1 = read_recid(data,offset)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset,L,">H")
	offset += L
	L,rid1 = read_recid(data,offset)
	elemtype,typestr = get_typestr(page,rid1)
	iter = add_iter (hd,'Rfr',"%02x (%s)%s"%(rid1,elemtype,typestr),offset,L,">H")
	offset += L
	for i in range(num):
		numchar = struct.unpack(">H",data[offset:offset+2])[0]
		L,rid1 = read_recid(data,offset+2)
		elemtype,typestr = get_typestr(page,rid1)
		iter = add_iter (hd,'Rfr',"Start char: %d, Style: %02x (%s)%s"%(numchar,rid1,elemtype,typestr),offset,L,">H",offset2=offset+2,length2=2)
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
	L,recid = read_recid(data,2)
	if L == 4:
		recid = 0x1ff00 - recid
	add_iter (hd,'Graphic Style ID',"%02x"%recid,2,2,">H")
	shift = offset + 22
	numpts = struct.unpack('>h', data[offset+20:offset+22])[0]
	for i in range(numpts):
		ptype = ord(data[shift+1+i*27])
		add_iter (hd,'Type %d'%i,"%d (%s)"%(ptype,pts_types[ptype]),shift+i*27+1,1,"B")
		x1 = struct.unpack('>H', data[shift+i*27+3:shift+i*27+5])[0] - 1692
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>H', data[shift+i*27+7:shift+i*27+9])[0] - 1584
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'X %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'Y %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift +=8
		x1 = struct.unpack('>H', data[shift+i*27+3:shift+i*27+5])[0] - 1692
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>H', data[shift+i*27+7:shift+i*27+9])[0] - 1584
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'\tXh1 %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'\tYh1 %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift +=8
		x1 = struct.unpack('>H', data[shift+i*27+3:shift+i*27+5])[0] - 1692
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>H', data[shift+i*27+7:shift+i*27+9])[0] - 1584
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'\tXh2 %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'\tYh2 %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift -=16


def hdArrowPath(hd,data,page):
	offset = 0
	shift = offset + 30
	numpts = struct.unpack('>h', data[offset+20:offset+22])[0]
	for i in range(numpts):
		ptype = ord(data[shift+1+i*27])
		add_iter (hd,'Type %d'%i,"%d (%s)"%(ptype,pts_types[ptype]),shift+i*27+1,1,"B")
		x1 = struct.unpack('>h', data[shift+i*27+3:shift+i*27+5])[0]
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>h', data[shift+i*27+7:shift+i*27+9])[0]
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'X %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'Y %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift +=8
		x1 = struct.unpack('>h', data[shift+i*27+3:shift+i*27+5])[0]
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>h', data[shift+i*27+7:shift+i*27+9])[0]
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'\tXh1 %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'\tYh1 %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift +=8
		x1 = struct.unpack('>h', data[shift+i*27+3:shift+i*27+5])[0]
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>h', data[shift+i*27+7:shift+i*27+9])[0]
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'\tXh2 %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'\tYh2 %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift -=16
	

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
				if a in page.appdoc.recs:
					at = page.appdoc.recs[a][1]
				else:
					at = "%02x"%a
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,at,shift,6,"txt")
			shift+=4
			L,rid = read_recid(data,offset+shift)
			shift += L
		else:
			add_iter (hd,rname,at,shift,8,"txt")
			shift+=8

def hdLinearFill(hd,data,page):
	offset = 0
	# 2-4 -- angle1
	# 11 -- overprint
	# 16-20 -- X
	# 20-24 -- Y
	# 24-28 -- <->1
	# 28-30 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 30-32 -- repeat
	pass

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
	pass

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
	pass 

def hdLensFill(hd,data,page):
	offset = 0
	# 39: 0 -- Transparency, 1 -- Magnify, 2 -- Lighten, 3 -- Darken, 4 -- Invert, 5 -- Monochrome
	# Transparency
	# 8-10.10-12 -- Opacity
	# 26-30 -- X
	# 30-34 -- Y
	# 37: 1 -- CenterPoint, 2 -- ObjOnly, 4 -- Snapshot (flags)
	# Magnify
	# 8-10.10-12 -- mag.coeff
	pass

def hdBendFilter(hd,data,page):
	offset = 0
	# 0-2  -- Size
	# 2-4.4-6 -- X
	# 6-8.8-10 -- Y
	pass

def hdBlock (hd,data,page):
		off = 0
		if page.version == 10:
			flags =  struct.unpack('>h', data[off:off+2])[0]
			res = 2
			for i in range(21):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))

				res += L
			res += 1
			for i in range(2):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
		elif page.version == 8:
			res = 0
			for i in range(12):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res += 14
		elif page.version < 8:
			res = 0
			for i in range(11):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res += 10
			for i in range(3):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
		else:
			# FIXME! ver11 starts with size==7
			res = 0
			for i in range(12):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res += 14
			for i in range(3):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			res +=1
			for i in range(4):
				L,rid1 = read_recid(data,off+res)
				elemtype = page.dict[page.reclist[rid1-1]]
				typestr = ""
				if "List" in elemtype:
					try:
						itr = page.model.iter_nth_child(page.diter,rid1-1)
						itrtype = struct.unpack(">H",page.model.get_value(itr,3)[0xa:0xc])[0]
						if itrtype == 0:
							t,r = read_recid(page.model.get_value(itr,3),0xc)
							typestr = " -> (%s)"%(page.dict[page.reclist[r-1]])
						elif itrtype in page.dict:
							typestr = " -> (%s)"%(page.dict[itrtype])
					except:
						pass
				iter = add_iter (hd,'List Elem',"%02x (%s)%s"%(rid1,elemtype,typestr),off+res,L,">H")
				hd.model.set (iter, 7,("fh goto",rid1-1))
				res += L
			# verify for v9
			if page.version < 10:
				res -= 6


def hdPropLst(hd,data,page):
	off = 0
	size = struct.unpack('>h', data[off+2:off+4])[0]
	res = 8
	for i in range(size):
		L1,rid1 = read_recid(data,off+res)
		res += L1
		L2,rid2 = read_recid(data,off+res)
		res += L2
		if rid1 in page.appdoc.recs:
			at = page.appdoc.recs[rid1][1]
		else:
			at = "%02x"%rid1
		add_iter (hd,at,"%02x"%rid2,res-L1-L2,L1+L2,">HH")


def hdImageImport(hd,data,page):
	offset = 0
	L1,gr_style = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,L1,">H")
	offset += L1
	L2,attr = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%attr,offset,L2,">H")
	offset += L2+8
	L3,attr = read_recid(data,offset)
	add_iter (hd,'Format Name',"%02x"%attr,offset,L3,">H")
	offset += L3
	L4,attr = read_recid(data,offset)
	add_iter (hd,'DataList',"%02x"%attr,offset,L4,">H")
	offset += L4
	L5,attr = read_recid(data,offset)
	add_iter (hd,'FileDescriptor',"%02x"%attr,offset,L5,">H")
	offset += L5
	L6,attr = read_recid(data,offset)
	add_iter (hd,'Xform',"%02x"%attr,offset,L6,">H")
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
	L1,gr_style = read_recid(data,offset)
	offset += L1
	mode = ord(data[offset+7])
	lmtxt = 'Normal'
	if mode&0x10 == 0x10:
		lmtxt = 'Wire'
	if mode&0x1 == 1:
		lmtxt += ' Locked'
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,L1,">H")
	add_iter (hd,'View mode',lmtxt,L1+7,1,"txt")
	L2,attr = read_recid(data,offset+10)
	add_iter (hd,'List',"%02x"%attr,offset+10,L2,"txt")
	offset += L2
	L3,name = read_recid(data,offset+10)
	if name in page.appdoc.recs:
		at = page.appdoc.recs[name][1]
	else:
		at = "%02x"%name

	add_iter (hd,'Layer name',at,offset+10,L3,"B")
	offset += L3
	vis = ""
	vval = ord(data[offset+11])
	if vval&1:
		vis += "Show "
	if vval&2:
		vis += "Print "
	if vval&8:
		vis += "Guides"
	add_iter (hd,'Visibility',vis,offset+11,1,"B")


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
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	xform = struct.unpack('>H', data[offset+16:offset+18])[0]
	x1 = struct.unpack('>H', data[offset+18:offset+20])[0] - 1692
	x1f = struct.unpack('>H', data[offset+20:offset+22])[0]
	y1 = struct.unpack('>H', data[offset+22:offset+24])[0] - 1584
	y1f = struct.unpack('>H', data[offset+24:offset+26])[0]
	x2 = struct.unpack('>H', data[offset+26:offset+28])[0] - 1692
	x2f = struct.unpack('>H', data[offset+28:offset+30])[0]
	y2 = struct.unpack('>H', data[offset+30:offset+32])[0] - 1584
	y2f = struct.unpack('>H', data[offset+32:offset+34])[0]
	if page.version > 4:
		rtlt = struct.unpack('>H', data[offset+34:offset+36])[0]
		rtltf = struct.unpack('>H', data[offset+36:offset+38])[0]
		rtll = struct.unpack('>H', data[offset+38:offset+40])[0]
		rtllf = struct.unpack('>H', data[offset+40:offset+42])[0]
	if page.version > 10:
		rtrt = struct.unpack('>H', data[offset+42:offset+44])[0]
		rtrtf = struct.unpack('>H', data[offset+44:offset+46])[0]
		rtrr = struct.unpack('>H', data[offset+46:offset+48])[0]
		rtrrf = struct.unpack('>H', data[offset+48:offset+50])[0]
		rbrb = struct.unpack('>H', data[offset+50:offset+52])[0]
		rbrbf = struct.unpack('>H', data[offset+52:offset+54])[0]
		rbrr = struct.unpack('>H', data[offset+54:offset+56])[0]
		rbrrf = struct.unpack('>H', data[offset+56:offset+58])[0]
		rblb = struct.unpack('>H', data[offset+58:offset+60])[0]
		rblbf = struct.unpack('>H', data[offset+60:offset+62])[0]
		rbll = struct.unpack('>H', data[offset+62:offset+64])[0]
		rbllf = struct.unpack('>H', data[offset+64:offset+66])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	add_iter (hd,'XForm',"%02x"%xform,16,2,">h")
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),18,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),22,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),26,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),30,4,"txt")
	if page.version > 10:
		add_iter (hd,'Rad TopLeft (Top)',"%.4f"%(rtlt+rtltf/65536.),34,4,"txt")
		add_iter (hd,'Rad TopLeft (Left)',"%.4f"%(rtll+rtllf/65536.),38,4,"txt")
		add_iter (hd,'Rad TopRight (Top)',"%.4f"%(rtrt+rtrtf/65536.),42,4,"txt")
		add_iter (hd,'Rad TopRight (Right)',"%.4f"%(rtrr+rtrrf/65536.),46,4,"txt")
		add_iter (hd,'Rad BtmRight (Btm)',"%.4f"%(rbrb+rbrbf/65536.),50,4,"txt")
		add_iter (hd,'Rad BtmRight (Right)',"%.4f"%(rbrr+rbrrf/65536.),54,4,"txt")
		add_iter (hd,'Rad BtmLeft (Btm)',"%.4f"%(rblb+rblbf/65536.),58,4,"txt")
		add_iter (hd,'Rad BtmLeft (Left)',"%.4f"%(rbll+rbllf/65536.),62,4,"txt")
	elif page.version > 4:
		add_iter (hd,'Rad X',"%d"%rtlt,34,2,">h")
		add_iter (hd,'Rad Y',"%d"%rtll,38,2,">h")
		

def hdOval(hd,data,page):
	offset = 0
	L,gr_style = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%gr_style,offset,L,">H")
	offset += L
	L,layer = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%layer,offset,L,">h")
	offset += L
	L,xform = read_recid(data,offset+12)
	add_iter (hd,'XForm',"%02x"%xform,offset+12,L,">h")
	offset += L
	x1 = struct.unpack('>H', data[offset+12:offset+14])[0] - 1692
	x1f = struct.unpack('>H', data[offset+14:offset+16])[0]
	y1 = struct.unpack('>H', data[offset+16:offset+18])[0] - 1584
	y1f = struct.unpack('>H', data[offset+18:offset+20])[0]
	x2 = struct.unpack('>H', data[offset+20:offset+22])[0] - 1692
	x2f = struct.unpack('>H', data[offset+22:offset+24])[0]
	y2 = struct.unpack('>H', data[offset+24:offset+26])[0] - 1584
	y2f = struct.unpack('>H', data[offset+26:offset+28])[0]
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),offset+12,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),offset+16,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),offset+20,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),offset+24,4,"txt")
	if page.version > 10:
		arc1 = struct.unpack('>H', data[offset+28:offset+30])[0]
		arc1f = struct.unpack('>H', data[offset+30:offset+32])[0]
		arc2 = struct.unpack('>H', data[offset+32:offset+34])[0]
		arc2f = struct.unpack('>H', data[offset+34:offset+36])[0]
		clsd = ord(data[offset+36])
		add_iter (hd,'Arc <>',"%.4f"%(arc1+arc1f/65536.),offset+28,4,"txt")
		add_iter (hd,'Arc ()',"%.4f"%(arc2+arc2f/65536.),offset+32,4,"txt")
		add_iter (hd,'Closed',clsd,offset+36,1,"B")

def hdGroup(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	if data[offset+2:offset+4] == '\xFF\xFF':
		xform = struct.unpack('>H', data[offset+16:offset+18])[0]
		add_iter (hd,'XForm',"%02x"%xform,16,2,">h")

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
		if a in page.appdoc.recs:
			at = page.appdoc.recs[a][1]
		else:
			at = "%02x"%a
		if v in page.appdoc.recs:
			vt = page.appdoc.recs[v][1]
		else:
			vt = "%02x"%v
		add_iter (hd,at,vt,off-4,4,">HH")


def hdAttributeHolder(hd,data,page):
	offset = 0
	L,parent = read_recid(data,offset)
	add_iter (hd,'Parent',"%02x"%parent,offset,L,">H")
	offset += L
	L,attr = read_recid(data,offset)
	add_iter (hd,'Attr ID',"%02x"%attr,offset,L,">H")


def hdBasicFill(hd,data,page):
	offset = 0
	L,clr = read_recid(data,offset)
	add_iter (hd,'Color',"%02x"%clr,offset,L,"txt")
	offset += L
	overprint = ord(data[offset+2])


def hdBasicLine(hd,data,page):
	offset = 0
	L,clr = read_recid(data,offset)
	add_iter (hd,'Color',"%02x"%clr,offset,L,"txt")
	offset += L
	L,dash = read_recid(data,offset)
	add_iter (hd,'Line Pattern',"%02x"%dash,offset,L,"txt")
	offset += L
	L,larr = read_recid(data,offset)
	add_iter (hd,'Start Arrow',"%02x"%larr,offset,L,"txt")
	offset += L
	L,rarr = read_recid(data,offset)
	add_iter (hd,'End Arrow',"%02x"%rarr,offset,L,"txt")
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
		l,rid = read_recid(data,offset)
		add_iter (hd,'List Elem',"%02x (%s)"%(rid,page.dict[page.reclist[rid-1]]),offset,l,">H")
		offset += l


def hdCompositePath(hd,data,page):
	offset = 0
	res,rid1 = read_recid(data,offset)
	add_iter (hd,'Graphic Style',"%02x"%rid1,offset,res,">H")
	L,rid2 = read_recid(data,offset+res)
	add_iter (hd,'Parent',"%02x"%rid2,offset+res,L,">H")
	res += L
	L,rid3 = read_recid(data,offset+8+res)
	add_iter (hd,'List of paths',"%02x"%rid3,offset+res+8,L,">H")


def hdProcessColor(hd,data,page):
	offset = 0
	ustr1 = struct.unpack('>H', data[offset:offset+2])[0]
	if ustr1 in page.appdoc.recs:
		at = page.appdoc.recs[ustr1][1]
	else:
		at = "%02x"%ustr1
	add_iter (hd,'Name',at,0,2,">H")
	offset = 14
	cmpntnames = ["K","C","M","Y"]
	for i in range(4):
		cmpnt = struct.unpack(">H",data[offset+i*2:offset+i*2+2])[0]/256
		add_iter (hd,cmpntnames[i],"%d"%cmpnt,offset+i*2,2,">H")


def hdColor6(hd,data,page):
	offset = 0
	pal = struct.unpack('>H', data[offset:offset+2])[0]
	if pal == 3:
		ustroff = 0xe
	else:
		ustroff = 2
	ustr1 = struct.unpack('>H', data[offset+ustroff:offset+ustroff+2])[0]
	add_iter (hd,"Palette",key2txt(pal,palette,"Unkn %02x"%pal),0,2,">h")
	if ustr1 in page.appdoc.recs:
		at = page.appdoc.recs[ustr1][1]
	else:
		at = "%02x"%ustr1
	add_iter (hd,'Name',at,ustroff,2,">H")
	if pal == 4:  # CMYK
		offset = 14
		if page.version > 9:
			offset += 2
		cmpntnames = ["C","M","Y","K"]
		for i in range(4):
			cmpnt = struct.unpack(">I",data[offset+i*4:offset+i*4+4])[0]/256
			add_iter (hd,cmpntnames[i],"%d"%cmpnt,offset+i*4,4,">I")
			


def hdSpotColor6(hd,data,page):
	offset = 0
	pal = struct.unpack('>H', data[offset:offset+2])[0]
	ustr1 = struct.unpack('>H', data[offset+2:offset+4])[0]
	add_iter (hd,"Palette",key2txt(pal,palette,"Unkn %02x"%pal),0,2,">h")
	if ustr1 in page.appdoc.recs:
		at = page.appdoc.recs[ustr1][1]
	else:
		at = "%02x"%ustr1
	add_iter (hd,'Name',at,2,2,">H")


hdp = {
	"AGDFont":hdAGDFont,
	"ArrowPath":hdArrowPath,
	"AttributeHolder":hdAttributeHolder,
	"BasicFill":hdBasicFill,
	"BasicLine":hdBasicLine,
	"BrushList":hdList,
	"Block":hdBlock,
	"Color6":hdColor6,
	"CompositePath":hdCompositePath,
	"FHTail":hdFHTail,
	"GraphicStyle":hdGraphicStyle,
	"Group":hdGroup,
	"ImageImport":hdImageImport,
	"Layer":hdLayer,
	"List":hdList,
	"MList":hdList,
	"Oval":hdOval,
	"Path":hdPath,
	"Paragraph":hdParagraph,
	"ProcessColor":hdProcessColor,
	"PropLst":hdPropLst,
	"Rectangle":hdRectangle,
	"SpotColor6":hdSpotColor6,
	"TintColor6":hdSpotColor6,
	"TFOnPath":hdTFOnPath,
	"TextColumn":hdTFOnPath,
	"TextInPath":hdTFOnPath,
	"TEffect":hdTEffect,
	"TString":hdTString,
	"VDict":hdTEffect,
	"VMpObj":hdVMpObj,
	"Xform":hdXform,
	}


def read_recid(data,off):
	if data[off:off+2] == '\xFF\xFF' or data[off:off+2] == '\xFF\xFE':
		rid = struct.unpack('>i', data[off:off+4])[0]
		l = 4
	else:
		rid = struct.unpack('>h', data[off:off+2])[0]
		l = 2
	return l,rid

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
		"PathTextLineInfo":self.PathTextLineInfo,
		"PatternFill":self.PatternFill,
		"PatternLine":self.PatternLine,
		"PerspectiveEnvelope":self.PerspectiveEnvelope,
		"PerspectiveGrid":self.PerspectiveGrid,
		"PolygonFigure":self.PolygonFigure,
		"Procedure":self.Procedure,
		"ProcessColor":self.ProcessColor, # fh5
		"PropLst":self.PropLst,
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
			l = 4
		else:
			rid = struct.unpack('>h', self.data[off:off+2])[0]
			l = 2
		return l,rid

	def AGDSelection(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length=4*size+8
		return length

	def ArrowPath(self,off,recid,mode=0):
		# version 8 'reserves' place for points
		# actual number of points is at offset 20
		if self.version > 8:
			size =  struct.unpack('>h', self.data[off+20:off+22])[0]
		else:
			size = struct.unpack('>h', self.data[off:off+2])[0]
		res=size*27+30
		if self.version < 5:
			res -= 4
		return res

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
		L,rid1 = self.read_recid(off+8+res)
		self.edges.append((recid,rid1))
		res += L
		return res+8

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
		size = struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		res += 6  # size and 2 words
		return res+size*10

	def Data(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
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

	def DisplayText(self,off,recid,mode=0):
		# ver < 5
		adj = 0
		size1 = struct.unpack('>h', self.data[off+0x7a:off+0x7c])[0]
		size2 = struct.unpack('>h', self.data[off+0x7c:off+0x7e])[0]
		if size2 == 0:
			adj = 18
		elif size2 == size1:
			size2 = 1
		return 0x86+size1+1+size2*30+adj

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
		L,rid = self.read_recid(off+res+8)
		self.edges.append((recid,rid))
		res += L
		L,rid = self.read_recid(off+res+8)
		self.edges.append((recid,rid))
		res += L
		if self.version < 5:
			res -= 4
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
		res += L+8
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
		shift = 0
		if rid != 0:
			shift += 4
		for i in range(3):
			L,rid = self.read_recid(off+res)
			self.edges.append((recid,rid))
			res += L
		if self.version > 9:
			shift += 37
		elif self.version == 9:
			shift += 35  # Tutorial_1_start.fh9
		elif self.version == 8:
			shift += 32  # suo.fh8
		elif self.version < 8:
			shift += 28
		return shift+res

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
		self.recs[recid] = ("str",self.data[off+4:off+4+length])
		return 4*(size+1)

	def MQuickDict(self,off,recid,mode=0):
		size =  struct.unpack('>h', self.data[off+0:off+2])[0]
		return 7 + size*4
	
	def MString(self,off,recid,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length = struct.unpack('>H', self.data[off+2:off+4])[0]
		self.recs[recid] = ("str",self.data[off+4:off+4+length])
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
			length=24
		res,rid = self.read_recid(off)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+res)
		self.edges.append((recid,rid))
		res += L
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

	def PathTextLineInfo(self,off,recid,mode=0):
		# FIXME!
		# SHOULD BE VARIABLE, just have no idea about base and multiplier
		length= 46
		return length

	def PatternFill(self,off,recid,mode=0):
		return 10

	def Path(self,off,recid,mode=0):
		size =  struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		self.edges.append((recid,rid))
		L,rid = self.read_recid(off+2+res)
		self.edges.append((recid,rid))
		res += L
		if self.version > 8:
			size = struct.unpack('>h', self.data[off+16+res:off+18+res])[0]
		length = 18 + res + 27*size
		if self.version < 5:
			length = 14 + res + 27*size
			
		return length

	def PatternLine(self,off,recid,mode=0):
		# 0-2 -- link to Color
		# 2-10 -- bitmap of the pattern
		# 10-14 -- mitter?
		# 14-16 -- width?
		length= 22
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
		L,rid = self.read_recid(off+12+res)
		self.edges.append((recid,rid))
		res += L
		if self.version < 5:
			length -= 4
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
					if -1 < res <= len(self.data)-offset:
						uid = ""
						if self.dictitems[i] in ("ImageImport","polygonFigure","Extrusion","Layer","Rectangle","Oval","ClipGroup","Group","CompositePath"):
							uid = "(%02x)"%(struct.unpack(">H",self.data[offset+6:offset+8])[0])
						elif self.dictitems[i] == "Path":
							uid = "(%02x)"%(struct.unpack(">H",self.data[offset+8:offset+10])[0])
						elif self.dictitems[i] == "TextColumn":
							uid = "(%02x)"%(struct.unpack(">H",self.data[offset+14:offset+16])[0])
						niter = add_pgiter(self.page,"[%02x] %s %s"%(j,self.dictitems[i],uid),"fh",self.dictitems[i],self.data[offset:offset+res],self.diter)
						self.page.model.set_value(niter,4,(j-1,offset))
						offset += res
						if uid != "":
							print self.dictitems[i],uid
						self.nodes[j] = (self.dictitems[i],niter)
					else:
						add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
						for k in range(10):
							try:
								add_pgiter(self.page,"!!! %s"%self.dictitems[self.reclist[i+k]],"fh","unknown","",self.diter)
							except:
								print "kk",k
						print "Failed on record %d (%s)"%(j,self.dictitems[i]),res
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
