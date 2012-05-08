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

import sys,struct,gtk,gobject,zlib
import icc,cmx
from utils import *

ri = {0:"Per", 1:"Rel.clr",2:"Sat",3:"Abs.clr"}

#x19	08	FOCOLTONE
#x19	09	SpectraMaster
#x19	0a	Toyo
#x19	0b	DIC Colors
#x19	11	Spot PANT PrevVer Match Sys Coat Corel 10
#x19	12	Spot PANT PrevVer Match Sys UnCoat Corel 10
#x19	14	Spot PANT PrevVer Metall Clr Unvarn Corel 10
#x19	15	Spot PANT PrevVer Pastel Clr Coat Corel 10
#x19	16	Spot PANT PrevVer Pastel Clr UnCoat Corel 10
#x19	17	HKS Colors
#x19	1a	HKS K
#x19	1b	HKS N
#x19	1c	HKS Z
#x19	1d	HKS E
#x19	1e	Spot PANT PrevVer Metalic Coat
#x19	1f	Spot PANT PrevVer Pastel Coat
#x19	20	Spot PANT PrevVer Pastel UnCoat
#x19	23	Spot PANT PrevVer Solid Matte
#x19	24	Spot PANT PrevVer Solid Coat
#x19	25	Spot PANT PrevVer Solid UnCoat

#0e	22	Proc PANT PrevVer Hexachrome UnCoat
#0e	21	Proc PANT PrevVer Hexachrome Coat
#0e	18	Proc PANT PrevVer Hexachrome UnCoat Corel 10
#0e	0c	Proc PANT PrevVer Hexachrome Coat Corel 10

clr_models = {
	0:"Invalid",
	1:"PANTONE",
	2:"CMYK",
	3:"CMYK255",
	4:"CMY",
	5:"RGB",
	6:"HSB",
	7:"HLS",
	8:"BW",
	9:"Gray",
	10:"YIQ255",
	11:"YIQ",
	12:"LAB",
	14:"PANTONE Hex",
	17:'CMYK', #? verify
	18:'LAB', # AP
	20:'Registration Color',
	21:"Roland/PANTONE", # AP
	22:"User ink",
	25:"Spot",   #AP
	26:"Multi-channel",
	99:"Mixed"
	}

bmp_clr_models = ('Invalid', 'RGB', 'CMY', 'CMYK255', 'HSB', 'Gray', 'Mono',
								'HLS', 'PAL8', 'Unknown9', 'RGB', 'LAB')

outl_corn_type =('Normal', 'Rounded', 'Cant')
outl_caps_type =('Normal', 'Rounded', 'Out Square')
fild_types = {0:'Transparent', 1:'Solid', 2:'Gradient',6:'Postscript',7:'Pattern', 9:'Bitmap', 10:"Full colour",11:'Texture'}
fild_grad_type = ('Unknown', 'Linear', 'Radial', 'Conical', 'Squared')
grad_subtypes = {0:"Line",1:"CW",2:"CCW",3:"Custom"}

wrap_txt_style = {
	0:"Contour Txt Flow Left",
	1:"Contour Txt Flow Right",
	2:"Contour Straddle Txt",
	3:"Square Txt Flow Left",
	4:"Square Txt Flow Right",
	5:"Square Straddle Txt",
	6:"Square Above/Below"
	}

charsets = {
	0:"Latin", #cp1252
	1:"System default",
	2:"Symbol",
	77:"Apple Roman", #cp10000 ?
	128:"Japanese Shift-JIS", #cp932
	129:"Korean (Hangul)", #cp949
	130:"Korean (Johab)", #cp1361
	134:"Chinese Simplified GBK", #cp936
	136:"Chinese Traditional BIG5", #cp950
	161:"Greek", #cp1253
	162:"Turkish", #cp1254
	163:"Vietnamese", #cp1258
	177:"Hebrew", #cp1255
	178:"Arabic", #cp1256
	186:"Baltic", #cp1257
	204:"Cyrillic", #cp1251
	222:"Thai", #cp874
	238:"Latin II (Central European)", #cp1250
	255:"OEM Latin I"
	}

def readfrac(data):
	intp = struct.unpack("<H",data[2:4])[0]
	frp =  struct.unpack("<H",data[0:2])[0]/0xffff
	return intp+frp


def stlt_s0(hd, size, data):
	return

def stlt_s1(hd, size, data):
	return

def stlt_s2(hd, size, data):
	off = 8
	for i in range((len(data)-8)/4):
		fid = struct.unpack("<i",data[off+i*4:off+4+i*4])[0]
		if fid > 5000 or fid < -5000:
			fid /= 10000.
		add_iter(hd,"var %2d"%i,fid,off+i*4,4,"<I")

def stlt_s3(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s4(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s5(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s6(hd, size, data):
	return

def stlt_s7(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s8(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s9(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s10(hd, size, data):
	stlt_s2(hd, size, data)

def stlt_s11(hd, size, data):
	stlt_s2(hd, size, data)

def stlt12_p2(hd, size, data):
	n = struct.unpack("<I",data[0:4])[0]
	if hd.version > 10:
		off = 4 + n*2
	else:
		off = 4 + n +1
	for i in range((len(data)-off)/4):
		fid = d2hex(data[off+i*4:off+4+i*4])
		add_iter(hd,"ID %d"%i,fid,off+i*4,4,"<I")


def arrw (hd, size, data):
	add_iter (hd,"Arrow ID","%02x"%struct.unpack('<I', data[0:4])[0],0,4,"<I")
	add_iter (hd,"???","%02x"%struct.unpack('<I', data[4:8])[0],4,4,"<I")
	pnum = struct.unpack('<H', data[8:10])[0]
	add_iter (hd,"#ofPts","%02x"%pnum,8,2,"<H")
	coff = 8+struct.unpack('<I', data[10:14])[0]
	add_iter (hd,"Pnt Types","",14,pnum,"txt")
	for i in range (pnum):
		x = struct.unpack('<l', data[coff+i*8:coff+4+i*8])[0]
		y = struct.unpack('<l', data[coff+4+i*8:coff+8+i*8])[0]
		Type = ord(data[14+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		add_iter (hd,"X%u/Y%u/Type"%(i+1,i+1),"%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2))+NodeType,coff+i*8,8,"txt")

def bbox (hd,size,data):
	offset = 0
	for i in range(2):
		varX = struct.unpack('<l', data[offset+i*8:offset+4+i*8])[0]
		varY = struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]
		add_iter (hd,"X%u/Y%u"%(i,i),"%u/%u mm"%(round(varX/10000.0,2),round(varY/10000.0,2)),offset+i*8,8,"txt")

def obbx (hd,size,data):
	offset = 0
	for i in range(4):
		varX = struct.unpack('<l', data[offset+i*8:offset+4+i*8])[0]
		varY = struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]
		add_iter (hd,"X%u/Y%u"%(i,i),"%u/%u mm"%(round(varX/10000.0,2),round(varY/10000.0,2)),offset+i*8,8,"txt")

def clr_model(hd,data,offset):
	cmid = struct.unpack('<H', data[offset:offset+2])[0]
	cmod = "%02x  "%cmid
	if clr_models.has_key(cmid):
		cmod += clr_models[cmid]
	cpal = struct.unpack('<H', data[offset+2:offset+4])[0]
	add_iter (hd,"Color Model",cmod,offset,2,"<H")
	add_iter (hd,"Color Palette",cpal,offset+2,2,"<H")
	clr = d2hex(data[offset+8:offset+12])
	add_iter (hd,"  Color",clr,offset+8,4,"<I")

def outl (hd,size,data):
	add_iter (hd,"Outline ID",d2hex(data[0:4]),0,4,"<I")

	lt = 0x4
	ct = 0x6
	jt = 0x8
	lw = 0xc
	st = 0x10
	ang = 0x14
	varo = 0x1c
	lc = 0x4c
	dash = 0x68
	arrw = 0x80

	if hd.version >= 13:
		flag = struct.unpack('<I', data[4:8])[0]
		off = 0
		if flag == 5:
			off = 107
		elif hd.version >= 16:
				off = 51
		lt = 0x18+off
		ct = 0x1a+off
		jt = 0x1c+off
		lw = 0x1e+off
		st = 0x22+off
		ang = 0x24+off
		varo = 0x28+off
		lc = 0x58+off # another place -- 0x55
		dash = 0x74+off
		arrw = 0x8a+off
	elif hd.version < 6:
		lw = 0xa
		st = 0xc
		ang = 0xe
		lc = 0x10
		dash = 0x26
		

	ltype = struct.unpack('<H', data[lt:lt+2])[0]
	ltxt = "Non-scalable"
	if ltype&0x20 == 0x20:
		ltxt = "Scalable"
	if ltype&0x10 == 0x10:
		ltxt += ", Behind fill"
	if ltype&0x80 == 0x80:
		ltxt += ", Share Attrs"
	if ltype&0x4 == 0x4:
		ltxt += ", Dashed"

	add_iter (hd,"Line Type","%02x %s"%(ltype,ltxt),lt,2,"<H")
	add_iter (hd,"Caps Type","%02x"%struct.unpack('<H', data[ct:ct+2])[0],ct,2,"<H")
	add_iter (hd,"Join Type","%02x"%struct.unpack('<H', data[jt:jt+2])[0],jt,2,"<H")
	add_iter (hd,"LineWidth","%.2f mm"%round(struct.unpack('<I', data[lw:lw+4])[0]/10000.0,2),lw,4,"<I")
	add_iter (hd,"Stretch","%02x"%struct.unpack('<H', data[st:st+2])[0],st,2,"<H")
	if hd.version > 5:
		add_iter (hd,"Angle","%.2f"%round(struct.unpack('<i', data[ang:ang+4])[0]/1000000.0,2),ang,4,"<i")
	else:
		add_iter (hd,"Angle","%.2f"%round(struct.unpack('<h', data[ang:ang+2])[0]/1000000.0,2),ang,2,"<h")

	if hd.version > 5:
		for i in range(6):                     
			var = struct.unpack('<d', data[varo+i*8:varo+8+i*8])[0]
			add_iter (hd, "?? var%d"%(i+1), "%f"%var,varo+i*8,8,"<d")
	clr_model(hd,data,lc)
	dnum = struct.unpack('<H', data[dash:dash+2])[0]
	add_iter (hd,"Dash num","%02x"%(dnum/2),dash,2,"<H")
	for i in range(dnum/2):
		add_iter (hd," Dash/Space","%02x/%02x"%(struct.unpack('<H', data[dash+2+i*4:dash+4+i*4])[0],struct.unpack('<H',data[dash+4+i*4:dash+6+i*4])[0]),dash+2+i*4,4,"txt")
	add_iter (hd,"StartArrow ID","%02x"%struct.unpack('<I', data[arrw:arrw+4])[0],arrw,4,"<I")
	add_iter (hd,"EndArrow ID","%02x"%struct.unpack('<I', data[arrw+4:arrw+8])[0],arrw+4,4,"<I")


def font (hd,size,data):
	add_iter (hd,"Font ID","%02x"%struct.unpack('<H', data[0:2])[0],0,2,"<H")
	enc = struct.unpack('<H', data[2:4])[0]
	enctxt = "Unknown"
	if charsets.has_key(enc):
		enctxt = charsets[enc]
	shift = 0
	if hd.version > 5:
		add_iter (hd,"Encoding","%s (%02x)"%(enctxt,enc),2,2,"<H")
		shift = 2
	add_iter (hd,"Flags",d2hex(data[2+shift:18]," "),2+shift,16-shift,"txt")
	fontname = data[18:52]
	if hd.version > 11:
		fontname = unicode(fontname,"utf16")
	add_iter (hd,"FontName",fontname,18,34,"txt")

def user (hd,size,data):
	add_iter (hd,"PS fill ID",d2hex(data[0:2]),0,2,"<H")
	if hd.version > 11:
		psname = unicode(data[2:],"utf16")
		pslen = len(psname)*2
	else:
		psname = unicode(data[2:])
		pslen = len(psname)
	add_iter (hd,"PS fill name",psname,2,pslen,"txt")

def fild (hd,size,data):
	add_iter (hd,"Fill ID",d2hex(data[0:4]),0,4,"<I")
	ftype_off = 4
	if hd.version > 12:
		ftype_off = 12
		v13flag = struct.unpack('<h', data[8:10])[0]
	fill_type = struct.unpack('<h', data[ftype_off:ftype_off+2])[0]
	ft_txt = "%d"%fill_type
	if fild_types.has_key(fill_type):
		ft_txt += " "+fild_types[fill_type]
	add_iter (hd,"Fill Type", ft_txt,ftype_off,2,"txt")
	if fill_type > 0:
		if fill_type == 1:
			clrm_off = 8
			if hd.version > 12:
				clrm_off = 0x1b
			clr_model(hd,data,clrm_off)

		elif fill_type == 2:
			grd_offset = 0x8
			edge_off = 0x1c
			rot_offset = 0x20
			cx_off = 0x24
			cy_off = 0x28
			steps_off = 0x2c
			mode_off = 0x2e
			mid_offset = 0x32
			pal_len = 16
			pal_off = 0
			prcnt_off = 0
			if hd.version >= 13:
				grd_offset = 0x16
				edge_off = 0x28
				rot_offset = 0x2a
				cx_off = 0x2e
				cy_off = 0x32
				steps_off = 0x36
				mode_off = 0x38
				mid_offset = 0x3c
				pal_len = 24
				pal_off = 3
				prcnt_off = 8
				if v13flag >= 0x9e or (hd.version == 16 and v13flag >= 0x96):
					prcnt_off = 29
					pal_len = 45
			grdmode = ord(data[grd_offset])
			midpoint = ord(data[mid_offset])
			rot = struct.unpack('<l', data[rot_offset:rot_offset+4])[0]

			if grdmode < len(fild_grad_type):
				gr_type = "%s"%fild_grad_type[grdmode]
			else:
				gr_type = "Unknown (%X)"%clrmode
			add_iter (hd, "Gradient type",gr_type, grd_offset,1,"B")
			add_iter (hd, "Edge offset",struct.unpack('<h', data[edge_off:edge_off+2])[0], edge_off,2,"<h")
			add_iter (hd, "Rotation",rot/1000000, rot_offset,4,"<l")
			add_iter (hd, "Center X offset",struct.unpack('<i', data[cx_off:cx_off+4])[0], cx_off,4,"<i")
			add_iter (hd, "Center Y offset",struct.unpack('<i', data[cy_off:cy_off+4])[0], cy_off,4,"<i")
			add_iter (hd, "Steps",struct.unpack('<H', data[steps_off:steps_off+2])[0], steps_off,2,"<H")
			stid = struct.unpack('<H', data[mode_off:mode_off+2])[0]
			st = "Unknown"
			if grad_subtypes.has_key(stid):
				st = grad_subtypes[stid]
			add_iter (hd, "Sub-type",st, mode_off,2,"<H")
			add_iter (hd, "Midpoint",midpoint, mid_offset,1,"B")

			pal_num = ord(data[mid_offset+2])
			for i in range(pal_num):
				clr_model(hd,data,mid_offset+6+pal_off+i*pal_len)
				prcnt = ord(data[mid_offset+18+prcnt_off+i*pal_len])
				add_iter (hd, "  Percent","%u"%prcnt,mid_offset+18+prcnt_off+i*pal_len,1,"B")
				
		elif fill_type == 6:
			add_iter (hd,"PS fill ID",d2hex(data[8:10]),8,2,"<H")

		elif fill_type == 7:
			# Pattern
			patt_off = 8
			w_off = 0xc
			h_off = 0x10
			rcp_off = 0x18
			fl_off = 0x1a
			clr1_off = 0x1c
			clr2_off = 0x28
			if hd.version > 12:
				patt_off = 0x16
				w_off = 0x1a
				h_off = 0x1e
				rcp_off = 0x26
				fl_off = 0x28
				clr1_off = 0x2f
				pal_len = 22
				if v13flag == 0x94 or (hd.version > 15 and v13flag == 0x8c):
					pal_len = 43
				clr2_off = clr1_off + pal_len

			add_iter (hd,"Pattern ID", d2hex(data[patt_off:patt_off+4]),patt_off,4,"txt")
			if hd.version < 6:
				w_off = 0xc
				h_off = 0xe
				rcp_off = 0x14 # FIXME!
				fl_off = 0x16 # FIXME!
				clr1_off = 0x18
				clr2_off = 0x24
				add_iter (hd,"Width", struct.unpack("<H",data[w_off:w_off+2])[0]*0.0254,w_off,2,"<I")
				add_iter (hd,"Height", struct.unpack("<H",data[h_off:h_off+2])[0]*0.0254,h_off,2,"<I")

			else:
				add_iter (hd,"Width", struct.unpack("<I",data[w_off:w_off+4])[0]/10000.,w_off,4,"<I")
				add_iter (hd,"Height", struct.unpack("<I",data[h_off:h_off+4])[0]/10000.,h_off,4,"<I")
			add_iter (hd,"R/C Offset %", ord(data[rcp_off]),rcp_off,1,"B")
			flag = ord(data[fl_off])
			ftxt = bflag2txt(flag,{1:"Column",2:"Mirror",4:"Transform with object"})
			add_iter (hd,"Flags", "%02x (%s)"%(flag,ftxt),fl_off,1,"B")

			# Colors (model + color) started at 0x1c and 0x28
			
			clr_model(hd,data,clr1_off)
			clr_model(hd,data,clr2_off)

		elif fill_type == 9:
			# Bitmap pattern fill
			w_off = 0xc
			h_off = 0x10
			rcp_off = 0x18
			fl_off = 0x1a
			patt_off = 0x30
			if hd.version > 12:
				patt_off = 0x16
				w_off = 0x16
				h_off = 0x1a
				rcp_off = 0x22
				fl_off = 0x24
				patt_off = 0x36
			
			add_iter (hd,"Width", struct.unpack("<I",data[w_off:w_off+4])[0]/10000.,w_off,4,"<I")
			add_iter (hd,"Height", struct.unpack("<I",data[h_off:h_off+4])[0]/10000.,h_off,4,"<I")
			add_iter (hd,"R/C Offset %", ord(data[rcp_off]),rcp_off,1,"B")
			flag = ord(data[fl_off])
			ftxt = bflag2txt(flag,{1:"Column",2:"Mirror",4:"Transform with object"})
			add_iter (hd,"Flags", "%02x (%s)"%(flag,ftxt),fl_off,1,"B")
			add_iter (hd,"Image ID",struct.unpack("<I",data[patt_off:patt_off+4])[0],patt_off,4,"<I")

		elif fill_type == 10:
			# Full colour pattern
			if hd.version < 6:
				patt_off = 8
				w_off = 0xa
				h_off = 0xc
				add_iter (hd,"Image ID",struct.unpack("<H",data[patt_off:patt_off+2])[0],patt_off,2,"<H")
				add_iter (hd,"Width", struct.unpack("<H",data[w_off:w_off+2])[0]*0.0254,w_off,2,"<H")
				add_iter (hd,"Height", struct.unpack("<H",data[h_off:h_off+2])[0]*0.0254,h_off,2,"<H")
				
			else:
				w_off = 0xc
				h_off = 0x10
				rcp_off = 0x18
				fl_off = 0x1a
				patt_off = 0x30
				if hd.version > 12:
					w_off = 0x16
					h_off = 0x1a
					rcp_off = 0x22
					fl_off = 0x24
					patt_off = 0x36
				add_iter (hd,"Width", struct.unpack("<I",data[w_off:w_off+4])[0]/10000.,w_off,4,"<I")
				add_iter (hd,"Height", struct.unpack("<I",data[h_off:h_off+4])[0]/10000.,h_off,4,"<I")
				add_iter (hd,"R/C Offset %", ord(data[rcp_off]),rcp_off,1,"B")
				flag = ord(data[fl_off])
				ftxt = bflag2txt(flag,{1:"Column",2:"Mirror",4:"Transform with object"})
				add_iter (hd,"Flags", "%02x (%s)"%(flag,ftxt),fl_off,1,"B")
				add_iter (hd,"Vect ID",struct.unpack("<I",data[patt_off:patt_off+4])[0],patt_off,4,"<I")

		elif fill_type == 11:
			# Texture pattern fill
			if hd.version < 6:
				patt_off = 8
				add_iter (hd,"Image ID",struct.unpack("<H",data[patt_off:patt_off+2])[0],patt_off,2,"<H")
				
			else:
				v1_off = 0xc
				rcp_off = 0x18
				fl_off = 0x1a
				v2_off = 0x20
				imgid_off = 0x30
				bmpres_off = 0x38
				maxtw_off = 0x3a
				
				if hd.version > 12:
					v1_off = 0x1e
					rcp_off = 0x22
					fl_off = 0x24
					v2_off = 0x32
					imgid_off = 0x3e
					bmpres_off = 0x4e
					maxtw_off = 0x50
					if v13flag == 0x18e:
						v1_off = 0x36
						rcp_off = 0x42
						fl_off = 0x44
						v2_off = 0x4a
						imgid_off = 0x56
						bmpres_off = 0x66
						maxtw_off = 0x68
	
				add_iter (hd,"Width",struct.unpack("<I",data[v1_off:v1_off+4])[0]/10000.,v1_off,4,"<I")
				add_iter (hd,"Height",struct.unpack("<I",data[v1_off+4:v1_off+8])[0]/10000.,v1_off+4,4,"<I")
				add_iter (hd,"R/C Offset %", ord(data[rcp_off]),rcp_off,1,"B")
				flag = ord(data[fl_off])
				ftxt = bflag2txt(flag,{1:"Column",2:"Mirror",4:"Transform with object"})
				add_iter (hd,"Flags", "%02x (%s)"%(flag,ftxt),fl_off,1,"B")
				add_iter (hd,"v3",struct.unpack("<I",data[v2_off:v2_off+4])[0]/10000.,v2_off,4,"<I")
				add_iter (hd,"v4",struct.unpack("<I",data[v2_off+4:v2_off+8])[0]/10000.,v2_off+4,4,"<I")
				add_iter (hd,"Image ID",struct.unpack("<I",data[imgid_off:imgid_off+4])[0],imgid_off,4,"<I")
				add_iter (hd,"BMP resolution",struct.unpack("<h",data[bmpres_off:bmpres_off+2])[0],bmpres_off,2,"<h")
				add_iter (hd,"Max tile width",struct.unpack("<h",data[maxtw_off:maxtw_off+2])[0],maxtw_off,2,"<h")

def bmpf (hd,size,data):
	add_iter (hd,"Pattern ID", d2hex(data[0:4]),0,4,"txt")
	bmp = struct.unpack("<I",data[0x18:0x1c])[0]
	bmpoff = struct.pack("<I",len(data)+10-bmp)
	img = 'BM'+struct.pack("<I",len(data)+8)+'\x00\x00\x00\x00'+bmpoff+data[4:]
	pixbufloader = gtk.gdk.PixbufLoader()
	pixbufloader.write(img)
	pixbufloader.close()
	pixbuf = pixbufloader.get_pixbuf()
	imgw=pixbuf.get_width()
	imgh=pixbuf.get_height()
	hd.da = gtk.DrawingArea()
	hd.hbox0.pack_start(hd.da)
	hd.da.connect('expose_event', disp_expose,pixbuf)
	ctx = hd.da.window.cairo_create()
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()
	ctx.stroke()
	hd.da.show()


def guid (hd,size,data):
	# very EXPERIMENTAL
	num1 = struct.unpack('<I', data[0:4])[0]
	num2 = struct.unpack('<I', data[0:4])[0]
	add_iter (hd,"Num 1", num1,0,4,"<I")
	add_iter (hd,"Num 2", num2,4,4,"<I")
	offset = 8
	for i in range(num1):
		piter = add_iter (hd,"Rec %02x"%i, d2hex(data[offset+i*40+12:offset+i*40+16]),offset+40*i,40,"txt")
		add_iter (hd,"\tNums", "%d\t%d"%(struct.unpack("<i",data[offset+i*40+16:offset+i*40+20])[0]/10000,struct.unpack("<i",data[offset+i*40+20:offset+i*40+24])[0]/10000),offset+40*i+16,8,"txt",0,0,piter)
		add_iter (hd,"\tNums", "%d\t%d"%(struct.unpack("<i",data[offset+i*40+24:offset+i*40+28])[0]/10000,struct.unpack("<i",data[offset+i*40+28:offset+i*40+32])[0]/10000),offset+40*i+16,8,"txt",0,0,piter)
		add_iter (hd,"\tNums", "%d\t%d"%(struct.unpack("<i",data[offset+i*40+32:offset+i*40+36])[0]/10000,struct.unpack("<i",data[offset+i*40+36:offset+i*40+40])[0]/10000),offset+40*i+16,8,"txt",0,0,piter)


def bmp (hd,size,data):
	add_iter (hd,"Image ID", struct.unpack('<I', data[0:4])[0],0,4,"txt")
	add_iter (hd,"Hdr 1", "",4,0x24,"txt")
	hlen = struct.unpack('<I', data[0x32:0x36])[0]
	add_iter (hd,"Hdr 2", "",0x28,hlen,"txt")
	add_iter (hd,"\tHdr 2 size", hlen,0x32,4,"<I")
	pal = struct.unpack('<I', data[0x36:0x3a])[0]
	bplt = "Unknown"
	if pal < 12:
		bplt = bmp_clr_models[pal]
	add_iter (hd,"\tPallete (%02x) %s"%(pal,bplt), struct.unpack('<I', data[0x36:0x3a])[0],0x36,4,"<I")
	shift = 0
	if hd.version < 7:
		shift = 4
	imgw = struct.unpack('<I', data[0x3e-shift:0x42-shift])[0]
	add_iter (hd,"\tWidth", imgw,0x3e-shift,4,"<I")
	imgh = struct.unpack('<I', data[0x42-shift:0x46-shift])[0]
	add_iter (hd,"\tHeight", imgh,0x42-shift,4,"<I")
	bpp = struct.unpack('<I', data[0x4a-shift:0x4e-shift])[0]
	add_iter (hd,"\tBPP", bpp,0x4a-shift,4,"<I")
	# for bpp = 1, cdr aligns by 4 bytes, bits after width are crap

	bmpsize = struct.unpack('<I', data[0x52-shift:0x56-shift])[0]
	palsize = 0
	add_iter (hd,"\tSize of BMP data", bmpsize,0x52-shift,4,"<I")
	if bpp < 24 and pal != 5 and pal != 6:
		palsize = struct.unpack('<H', data[0x78:0x7a])[0]
		add_iter (hd,"Palette Size", palsize,0x78,2,"<H")
		add_iter (hd,"Palette", "",0x7a,palsize*3,"txt")
		add_iter (hd,"BMP data", "",0x7a+palsize*3,bmpsize,"<I")
		bmpoff = 0x7a+palsize*3
	else:
		add_iter (hd,"BMP data", "",0x76-shift,bmpsize,"<I")
		bmpoff = 0x76-shift

	img = 'BM'+struct.pack("<I",bmpsize+palsize+54)+'\x00\x00\x00\x00'+struct.pack("<I",54+palsize*3)
	img += '\x28\x00\x00\x00'+struct.pack("<I",imgw)+struct.pack("<I",imgh)+'\x01\x00'
	img += struct.pack("<H",bpp)+'\x00\x00\x00\x00'+struct.pack("<I",bmpsize)+'\x00\x00\x00\x00'+'\x00\x00\x00\x00'
	img += struct.pack("<I",palsize)+'\x00\x00\x00\x00'
	if bpp == 24:
		img += data[bmpoff:]
	else:
		img += data[0x7a:palsize*3] + data[bmpoff:]

	pixbufloader = gtk.gdk.PixbufLoader()
	pixbufloader.write(img)
	pixbufloader.close()
	pixbuf = pixbufloader.get_pixbuf()
	imgw=pixbuf.get_width()
	imgh=pixbuf.get_height()
	hd.da = gtk.DrawingArea()
	hd.hbox0.pack_start(hd.da)
	hd.da.connect('expose_event', disp_expose,pixbuf)
	ctx = hd.da.window.cairo_create()
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()
	ctx.stroke()
	hd.da.show()


def ftil (hd,size,data):
	for i in range(6):
		[var] = struct.unpack('<d', data[i*8:i*8+8]) 
		add_iter(hd,'Var%d'%i,var,i*8,8,"<d")

def loda_outl (hd,data,offset,l_type,length):
	if hd.version > 3:
		iter = add_iter (hd, "[000a] Outl ID",d2hex(data[offset:offset+4]),offset,4,"txt")
		hd.hdmodel.set (iter, 7,("cdr goto",d2hex(data[offset:offset+4])))
	else:
		iter = add_iter (hd, "[000a] Outl","",offset,length,"txt")
		# type/flag:  1 - solid, 2 -- dashed, 0x40 -- behind fill, 0x80 -- scale with image
		add_iter (hd, "\ttype/flag",ord(data[offset]),offset,1,"B",0,0,iter)
		add_iter (hd, "\twidth",struct.unpack("<h",data[offset+1:offset+3])[0]*0.0254,offset+1,2,"<h",0,0,iter)
		add_iter (hd, "\tstretch",struct.unpack("<h",data[offset+3:offset+5])[0],offset+3,2,"<h",0,0,iter)
		add_iter (hd, "\tangle",struct.unpack("<h",data[offset+5:offset+7])[0]/10.,offset+5,2,"<h",0,0,iter)
		add_iter (hd, "\tcolour",d2hex(data[offset+7:offset+12]),offset+7,5,"txt",0,0,iter)
		add_iter (hd, "\tdashes",d2hex(data[offset+19:offset+30]),offset+19,11,"txt",0,0,iter)
		add_iter (hd, "\tjoin type",ord(data[offset+30]),offset+30,1,"B",0,0,iter)
		add_iter (hd, "\tcaps type",ord(data[offset+32]),offset+32,1,"B",0,0,iter)
		if hd.version == 3:
			add_iter (hd, "\tstart arrow",d2hex(data[offset+34:offset+38]),offset+34,4,"txt",0,0,iter)
			add_iter (hd, "\tend arrow",d2hex(data[offset+38:offset+42]),offset+38,4,"txt",0,0,iter)
		else:
			# VERIFY!
			add_iter (hd, "\tstart arrow",d2hex(data[offset+34:offset+36]),offset+34,2,"txt",0,0,iter)
			add_iter (hd, "\tend arrow",d2hex(data[offset+36:offset+38]),offset+36,2,"txt",0,0,iter)

def loda_fild (hd,data,offset,l_type,length):
	if hd.version > 3:
		iter = add_iter (hd, "[0014] Fild ID",d2hex(data[offset:offset+4]),offset,4,"txt")
		hd.hdmodel.set (iter, 7,("cdr goto",d2hex(data[offset:offset+4])))
	else:
		iter = add_iter (hd, "[0014] Fild","",offset,length,"txt")
		ftype = ord(data[offset])
		# 0 - xparent, 1 - solid, 2 - lin grad, 4 - rad grad, 6 - ps, 7 - pattern, a - bitmap/texture/full clr
		add_iter (hd, "\ttype/flag","%02x (%s)"%(ftype,key2txt(ftype,{0:"Xparent",1:"Solid",2:"Linear grad",4:"Radial Grad",6:"PS",7:"Pattern",10:"Bitmap"})),offset,1,"B",0,0,iter)
		if ftype == 1:
			add_iter (hd, "\tcolour",d2hex(data[offset+1:offset+6]),offset+1,5,"txt",0,0,iter)
		elif ftype == 2:
			add_iter (hd, "\trotation",struct.unpack("<h",data[offset+1:offset+3])[0]/10.,offset,2,"<h",0,0,iter)
			add_iter (hd, "\tcolour 1",d2hex(data[offset+3:offset+8]),offset+3,5,"txt",0,0,iter)
			add_iter (hd, "\tcolour 2",d2hex(data[offset+8:offset+13]),offset+8,5,"txt",0,0,iter)
			add_iter (hd, "\tsteps?",struct.unpack("<h",data[offset+18:offset+20])[0],offset+18,2,"<h",0,0,iter)
			add_iter (hd, "\tedge offset",struct.unpack("<h",data[offset+20:offset+22])[0],offset+20,2,"<h",0,0,iter)
		elif ftype == 4:
			add_iter (hd, "\trotation",struct.unpack("<h",data[offset+1:offset+3])[0]/10.,offset,2,"<h",0,0,iter)
			add_iter (hd, "\tcolour 1",d2hex(data[offset+3:offset+8]),offset+3,5,"txt",0,0,iter)
			add_iter (hd, "\tcolour 2",d2hex(data[offset+8:offset+13]),offset+8,5,"txt",0,0,iter)
#			add_iter (hd, "\tsteps?",struct.unpack("<h",data[offset+18:offset+20])[0],offset+18,2,"<h",0,0,iter)
			add_iter (hd, "\tedge offset",struct.unpack("<h",data[offset+20:offset+22])[0],offset+20,2,"<h",0,0,iter)
			add_iter (hd, "\tcenter X offset",struct.unpack("<h",data[offset+22:offset+24])[0],offset+22,2,"<h",0,0,iter)
			add_iter (hd, "\tcenter Y offset",struct.unpack("<h",data[offset+24:offset+26])[0],offset+24,2,"<h",0,0,iter)
		elif ftype == 6:
			add_iter (hd, "\tPS ID (usdn)",d2hex(data[offset+1:offset+3]),offset+1,2,"txt",0,0,iter)
			add_iter (hd, "\tPS options",d2hex(data[offset+3:offset+13]),offset+3,10,"txt",0,0,iter)
		elif ftype == 7:
			add_iter (hd, "\twidth",struct.unpack("<h",data[offset+5:offset+7])[0]*0.0254,offset+5,2,"<h",0,0,iter)
			add_iter (hd, "\theight",struct.unpack("<h",data[offset+7:offset+9])[0]*0.0254,offset+7,2,"<h",0,0,iter)
			add_iter (hd, "\tX tile offset %",struct.unpack("<h",data[offset+9:offset+11])[0],offset+9,2,"<h",0,0,iter)
			add_iter (hd, "\tY tile offset %",struct.unpack("<h",data[offset+11:offset+13])[0],offset+11,2,"<h",0,0,iter)
			add_iter (hd, "\tRow/Col offset %",struct.unpack("<h",data[offset+13:offset+15])[0],offset+13,2,"<h",0,0,iter)
			add_iter (hd, "\tRow/Col (0/1)",ord(data[offset+15]),offset+15,1,"B",0,0,iter)
			add_iter (hd, "\tcolour 1",d2hex(data[offset+16:offset+21]),offset+16,5,"txt",0,0,iter)
			add_iter (hd, "\tcolour 2",d2hex(data[offset+21:offset+26]),offset+21,5,"txt",0,0,iter)
		elif ftype == 10:
			add_iter (hd, "\tImage ID (spnd)",d2hex(data[offset+1:offset+3]),offset+1,2,"txt",0,0,iter)
			add_iter (hd, "\twidth",struct.unpack("<h",data[offset+3:offset+5])[0]*0.0254,offset+3,2,"<h",0,0,iter)
			add_iter (hd, "\theight",struct.unpack("<h",data[offset+5:offset+7])[0]*0.0254,offset+5,2,"<h",0,0,iter)
			add_iter (hd, "\tX tile offset %",struct.unpack("<h",data[offset+9:offset+11])[0],offset+9,2,"<h",0,0,iter)
			add_iter (hd, "\tY tile offset %",struct.unpack("<h",data[offset+11:offset+13])[0],offset+11,2,"<h",0,0,iter)
			add_iter (hd, "\tRow/Col offset %",struct.unpack("<h",data[offset+13:offset+15])[0],offset+13,2,"<h",0,0,iter)
			add_iter (hd, "\tRow/Col (0/1)",ord(data[offset+15]),offset+15,1,"B",0,0,iter)
			add_iter (hd, "\tcolour 1",d2hex(data[offset+16:offset+21]),offset+16,5,"txt",0,0,iter)
			add_iter (hd, "\tcolour 2",d2hex(data[offset+21:offset+26]),offset+21,5,"txt",0,0,iter)


def loda_trfd (hd,data,offset,l_type,length):
	if hd.version > 3:
		add_iter (hd, "[0064] Trfd ID",d2hex(data[offset:offset+4]),offset,4,"txt")
	else:
		add_iter (hd, "[0064] Trafo","",offset,length,"txt")
		t_off = struct.unpack("<h",data[offset+0xa:offset+0xc])[0]
		add_iter (hd, "\tOffset to values","%02x"%t_off,offset+0xa,2,"<h")
		add_iter (hd, "\tvar1",readfrac(data[offset+t_off:offset+t_off+4]),offset+t_off,4,"frac")
		add_iter (hd, "\tvar2",readfrac(data[offset+t_off+4:offset+t_off+8]),offset+t_off+4,4,"frac")
		add_iter (hd, "\tX0",struct.unpack("<i",data[offset+t_off+8:offset+t_off+12])[0]*0.0254,offset+t_off+8,4,"<i")
		add_iter (hd, "\tvar3",readfrac(data[offset+t_off+12:offset+t_off+16]),offset+t_off+12,4,"frac")
		add_iter (hd, "\tvar4",readfrac(data[offset+t_off+16:offset+t_off+20]),offset+t_off+16,4,"frac")
		add_iter (hd, "\tY0",struct.unpack("<i",data[offset+t_off+20:offset+t_off+24])[0]*0.0254,offset+t_off+20,4,"<i")

def loda_stlt (hd,data,offset,l_type,length):
	add_iter (hd, "[00c8] Stlt ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_grad (hd,data,offset,l_type,length):
	startx = struct.unpack('<i', data[offset+8:offset+12])[0]
	starty = struct.unpack('<i', data[offset+12:offset+16])[0]
	endx = struct.unpack('<i', data[offset+16:offset+20])[0]
	endy = struct.unpack('<i', data[offset+20:offset+24])[0]
	sx = round(startx/10000.,2)
	sy = round(starty/10000.,2)
	ex = round(endx/10000.,2)
	ey = round(endy/10000.,2)
	add_iter (hd, "[2eea] Gradient Start X","%.2f  (corr. %.2f)"%(sx,sx+hd.width/2),offset+8,4,"<i")
	add_iter (hd, "[2eea] Gradient Start Y","%.2f  (corr. %.2f)"%(sy,sy+hd.height/2),offset+12,4,"<i")
	add_iter (hd, "[2eea] Gradient End X","%.2f  (corr. %.2f)"%(ex,ex+hd.width/2),offset+16,4,"<i")
	add_iter (hd, "[2eea] Gradient End Y","%.2f  (corr. %.2f)"%(ey,ey+hd.height/2),offset+20,4,"<i")


def loda_rot(hd,data,offset,l_type,length):
	rot = struct.unpack('<l', data[offset:offset+4])[0]
	add_iter (hd, "[2efe] Rotate","%.2f"%round(rot/1000000.0,2),offset,4,"txt")

def loda_rot_center (hd,data,offset,l_type,length):
	rotX = struct.unpack('<l', data[offset:offset+4])[0]
	rotY = struct.unpack('<l', data[offset+4:offset+8])[0]
	rx = round(rotX/10000.0,2)
	ry = round(rotY/10000.0,2)
	add_iter (hd, "[0028] RotCenter X/Y","%.2f/%.2f   (corr. %.2f/%.2f)"%(rx,ry,rx+hd.width/2,ry+hd.height/2),offset,8,"txt")

def loda_name(hd,data,offset,l_type,length):
	if hd.version > 11:
		layrname = unicode(data[offset:],'utf-16')
	else:
		layrname = data[offset:]
	add_iter (hd,"[03e8] Layer name",layrname,offset,len(data[offset:]),"txt")

def loda_polygon (hd,data,offset,l_type,length):
	num = struct.unpack('<L', data[offset+4:offset+8])[0]
	add_iter (hd,"[2af8] # of angles",num,offset+4,4,"<I")
	num = struct.unpack('<L', data[offset+8:offset+0xc])[0]
	add_iter (hd,"[2af8] next point?",num,offset+8,4,"<I")
	var = struct.unpack('<d', data[offset+0x10:offset+0x10+8])[0]
	add_iter (hd,"[2af8] var1 ?",var,offset+0x10,8,"<d")
	var = struct.unpack('<d', data[offset+0x18:offset+0x18+8])[0]
	add_iter (hd,"[2af8] var2 ?",var,offset+0x18,8,"<d")
	
	if hd.version > 6:
		for i in range(2):
			varX = struct.unpack('<l', data[offset+0x18+8+i*8:offset+0x1c+8+i*8])[0]
			varY = struct.unpack('<l', data[offset+0x1c+8+i*8:offset+0x20+8+i*8])[0]
			vx = round(varX/10000.0,2)
			vy = round(varY/10000.0,2)
			add_iter (hd,"[2af8] X%u/Y%u"%(i,i),"%.2f/%.2f mm  (corr. %.2f/%.2f)"%(vx,vy,vx+hd.width/2,vy+hd.height/2),offset+0x18+8+i*8,8,"txt")
	else:
		# FIXME! could be 1 pair
		for i in range(2):
			varX = struct.unpack('<h', data[offset+0x18+8+i*4:offset+0x1a+8+i*4])[0]
			varY = struct.unpack('<h', data[offset+0x1a+8+i*4:offset+0x1c+8+i*4])[0]
			vx = round(varX/10000.0,2)
			vy = round(varY/10000.0,2)
			add_iter (hd,"[2af8] X%u/Y%u"%(i,i),"%.2f/%.2f mm  (corr. %.2f/%.2f)"%(vx,vy,vx+hd.width/2,vy+hd.height/2),offset+0x18+4+i*4,4,"txt")

corner_types = {
	0:"Round",
	1:"Scalloped",
	2:"Clamfered"
	}

def loda_coords124 (hd,data,offset,l_type):
	# rectangle or ellipse or text
	if hd.version > 14:
		x1 = round(struct.unpack('<d', data[offset:offset+8])[0]/10000.,2)
		y1 = round(struct.unpack('<d', data[offset+8:offset+16])[0]/10000.,2)
		add_iter (hd,"[001e] x1/y1","%.2f/%.2f mm  (corr %.2f/%.2f)"%(x1,y1,x1+hd.width/2,y1+hd.height/2),offset,16,"txt")

		if l_type == 1:
			scx = struct.unpack('<d', data[offset+16:offset+24])[0]
			scy = struct.unpack('<d', data[offset+24:offset+32])[0]
			add_iter (hd,"[001e] Scale X/Y","%.2f %.2f "%(round(scx,2),round(scy,2)),offset+16,16,"txt")
			for i in range(4):
				Ri = struct.unpack('<d', data[offset+40+i*24:offset+48+i*24])[0]
				crnscale = ord(data[offset+32+i*24])
				cs = "Yes"
				if crnscale:
					cs = "No"
					Ri = round(Ri/10000.,2)
				ctype = ord(data[offset+48+i*24])
				ct = key2txt(ctype,corner_types)

				add_iter (hd,"[001e] R%d"%(i+1),"Scale with shape: %s"%cs,offset+32+i*24,1,"B")
				add_iter (hd,"[001e] R%d"%(i+1),"%.2f"%Ri,offset+40+i*24,8,"<d")
				add_iter (hd,"[001e] R%d"%(i+1),"Corner type: %s"%ct,offset+48+i*24,1,"B")
	elif hd.version < 6:
		x1 = round(struct.unpack('<h', data[offset:offset+2])[0]*0.0254,2)
		y1 = round(struct.unpack('<h', data[offset+2:offset+4])[0]*0.0254,2)
		add_iter (hd,"[001e] x1/y1","%.2f/%.2f mm  (corr %.2f/%.2f)"%(x1,y1,x1+hd.width/2,y1+hd.height/2),offset,4,"txt")

	else:
		x1 = round(struct.unpack('<l', data[offset:offset+4])[0]/10000.,2)
		y1 = round(struct.unpack('<l', data[offset+4:offset+8])[0]/10000.,2)
		add_iter (hd,"[001e] x1/y1","%.2f/%.2f mm  (corr %.2f/%.2f)"%(x1,y1,x1+hd.width/2,y1+hd.height/2),offset,8,"txt")

		if l_type == 1:
			R1 = struct.unpack('<l', data[offset+8:offset+12])[0]
			R2 = struct.unpack('<l', data[offset+12:offset+16])[0]
			R3 = struct.unpack('<l', data[offset+16:offset+20])[0]
			R4 = struct.unpack('<l', data[offset+20:offset+24])[0]
			add_iter (hd,"[001e] R1 R2 R3 R4","%.2f %.2f %.2f %.2f mm"%(round(R1/10000.0,2),round(R2/10000.0,2),round(R3/10000.0,2),round(R4/10000.0,2)),offset+8,16,"txt")

	if l_type == 2:
		a1 = struct.unpack('<L', data[offset+8:offset+12])[0]
		a2 = struct.unpack('<L', data[offset+12:offset+16])[0]
		a3 = struct.unpack('<L', data[offset+16:offset+20])[0]
		add_iter (hd,"[001e] Start/End Rot angles; Pie flag","%.2f %.2f %.2f"%(round(a1/1000000.0,2),round(a2/1000000.0,2),round(a3/1000000.0,2)),offset+8,12,"txt")

nodetypes = {
	2:"\tChar. start",
	4:"\tCan modify",
	8:"\tClosed path",
	0x10:"\tSmooth",
	0x20:"\tSymmetric"
	}

def loda_coords3 (hd,data,offset,l_type,lt2="001e"):
	pointnum = struct.unpack('<L', data[offset:offset+4])[0]
	poffset = 4
	if hd.version < 7:
		pointnum = struct.unpack('<H', data[offset:offset+2])[0]
		poffset = 4
	if hd.version < 6:
		for i in range (pointnum):
			x = 0.02540164*struct.unpack('<h', data[offset+poffset+i*4:offset+poffset+2+i*4])[0]
			y = 0.02540164*struct.unpack('<h', data[offset+poffset+2+i*4:offset+poffset+4+i*4])[0]
			Type = ord(data[offset+poffset+pointnum*4+i])
			ntype = bflag2txt(Type,nodetypes)
			if Type&0x10 == 0 and Type&0x20 == 0:
				ntype += '  Discontinued'
			if Type&0x40 == 0 and Type&0x80 == 0:
				ntype += '  START'
			if Type&0x40 == 0x40 and Type&0x80 == 0:
				ntype += '  Line'
			if Type&0x40 == 0 and Type&0x80 == 0x80:
				ntype += '  Curve'
			if Type&0x40 == 0x40 and Type&0x80 == 0x80:
				ntype +='  Arc'
			add_iter (hd,"[%s] X%u/Y%u/Type"%(lt2,i+1,i+1),"%.2f/%.2f mm  (corr. %.2f/%.2f)"%(x,y,x+hd.width/2,y+hd.height/2)+ntype,offset+poffset+i*4,4,"txt",offset+poffset+pointnum*4+i,1)
		return pointnum

	for i in range (pointnum):
		x = round(struct.unpack('<l', data[offset+poffset+i*8:offset+poffset+4+i*8])[0]/10000.,2)
		y = round(struct.unpack('<l', data[offset+poffset+4+i*8:offset+poffset+8+i*8])[0]/10000.,2)
		Type = ord(data[offset+poffset+pointnum*8+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		add_iter (hd,"[%s] X%u/Y%u/Type"%(lt2,i+1,i+1),"%.2f/%.2f mm  (corr. %.2f/%.2f)"%(x,y,x+hd.width/2,y+hd.height/2)+NodeType,offset+poffset+i*8,8,"txt",offset+poffset+pointnum*8+i,1)
	return pointnum

def loda_coords5v5 (hd,data,offset,l_type):
	x = round(struct.unpack('<h', data[offset:offset+2])[0]*0.0254,2)
	y = round(struct.unpack('<h', data[offset+2:offset+4])[0]*0.0254,2)
	add_iter (hd,"[001e] X0/Y0","%.2f/%.2f mm  (corr. %.2f/%.2f)"%(x,y,x+hd.width/2,y+hd.height/2),offset,4,"txt")
	offset += 4
	add_iter (hd,"[001e] var1?",struct.unpack("<H",data[offset:offset+2])[0],offset,2,"<H")
	add_iter (hd,"[001e] BPP?",struct.unpack("<H",data[offset+2:offset+4])[0],offset+2,2,"<H")
	add_iter (hd,"[001e] Img Width (px)",struct.unpack("<h",data[offset+4:offset+6])[0],offset+4,2,"<h")
	add_iter (hd,"[001e] Img Height (px)",struct.unpack("<h",data[offset+6:offset+8])[0],offset+6,2,"<h")
	offset += 8
	add_iter (hd,"[001e] Image ID",struct.unpack("<H",data[offset:offset+2])[0],offset,2,"<H")


def loda_coords5 (hd,data,offset,l_type):
	if hd.version < 6:
		loda_coords5v5 (hd,data,offset,l_type)
	else:
		for i in range (4):
			x = round(struct.unpack('<l', data[offset+i*8:offset+4+i*8])[0]/10000.,2)
			y = round(struct.unpack('<l', data[offset+4+i*8:offset+8+i*8])[0]/10000.,2)
			add_iter (hd,"[001e] X%u/Y%u"%(i+1,i+1),"%.2f/%.2f mm  (corr. %.2f/%.2f)"%(x,y,x+hd.width/2,y+hd.height/2),offset+i*8,8,"txt")
		offset += 32
		add_iter (hd,"[001e] var1?",struct.unpack("<H",data[offset:offset+2])[0],offset,2,"<H")
		add_iter (hd,"[001e] BPP?",struct.unpack("<H",data[offset+2:offset+4])[0],offset+2,2,"<H")
		add_iter (hd,"[001e] Img Width (px)",struct.unpack("<I",data[offset+4:offset+8])[0],offset+4,4,"<I")
		add_iter (hd,"[001e] Img Height (px)",struct.unpack("<I",data[offset+8:offset+12])[0],offset+8,4,"<I")
		offset += 16
		add_iter (hd,"[001e] Image ID",struct.unpack("<I",data[offset:offset+4])[0],offset,4,"<I")
		offset += 24
		loda_coords3 (hd,data,offset,l_type)


def loda_coords_poly (hd,data,offset,l_type):
	pn = loda_coords3 (hd,data,offset,l_type)
	x = round(struct.unpack('<l', data[offset+4+pn*9:offset+4+pn*9+4])[0]/10000.,2)
	y = round(struct.unpack('<l', data[offset+4+pn*9+4:offset+4+pn*9+8])[0]/10000.,2)
	add_iter (hd,"[001e] var1/var2 ?","%.2f/%.2f mm  (corr. %.2f/%.2f)"%(x,y,x+hd.width/2,y+hd.height/2),offset+4+pn*9,8,"txt")


def loda_coords_0x25(hd,data,offset,l_type):
	n1 = struct.unpack("<H",data[offset:offset+2])[0]
	n2 = struct.unpack("<H",data[offset+2:offset+4])[0]
	n3 = struct.unpack("<H",data[offset+4:offset+6])[0]
	n4 = struct.unpack("<H",data[offset+6:offset+8])[0]
	numpts = n3 + n4
	add_iter (hd,"[001e] Flags","%02x %02x %02x %02x"%(n1,n2,n3,n4),offset,8,"txt")
	off = offset + 8
	xs = round(struct.unpack('<l', data[off:off+4])[0]/10000.,2)
	ys = round(struct.unpack('<l', data[off+4:off+8])[0]/10000.,2)
	xe = round(struct.unpack('<l', data[off+8:off+12])[0]/10000.,2)
	ye = round(struct.unpack('<l', data[off+12:off+16])[0]/10000.,2)
	add_iter (hd,"[001e] Xs/Ys","%.2f/%.2f mm  (corr. %.2f/%.2f)"%(xs,ys,xs+hd.width/2,ys+hd.height/2),off,8,"txt")
	add_iter (hd,"[001e] Xe/Ye","%.2f/%.2f mm  (corr. %.2f/%.2f)"%(xe,ye,xe+hd.width/2,ye+hd.height/2),off+8,8,"txt")
	off += 16
	for i in range (numpts):
		x = round(struct.unpack('<l', data[off+i*8:off+4+i*8])[0]/10000.,2)
		y = round(struct.unpack('<l', data[off+4+i*8:off+8+i*8])[0]/10000.,2)
		Type = ord(data[off+numpts*8+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		add_iter (hd,"[001e] X%u/Y%u/Type"%(i+1,i+1),"%.2f/%.2f mm  (corr. %.2f/%.2f)"%(x,y,x+hd.width/2,y+hd.height/2)+NodeType,off+i*8,8,"txt",off+numpts*8+i,1)
 

def loda_coords_v3 (hd,data,offset,l_type,length):
	if l_type == 0: # rectangle
		x = struct.unpack("<h",data[offset:offset+2])[0]*0.0254
		y = struct.unpack("<h",data[offset+2:offset+4])[0]*0.0254
		r = struct.unpack("<h",data[offset+4:offset+6])[0]*0.0254
		add_iter (hd,"[001e] X/Y/R","%.2f  %.2f  %.2f"%(x,y,r),offset,6,"<hhh")
	elif l_type == 1: # ellipse
		x = struct.unpack("<h",data[offset:offset+2])[0]*0.0254
		y = struct.unpack("<h",data[offset+2:offset+4])[0]*0.0254
		a1 = struct.unpack("<h",data[offset+4:offset+6])[0]  # /10?
		a2 = struct.unpack("<h",data[offset+6:offset+8])[0]  # /10?
		f = struct.unpack("<h",data[offset+8:offset+10])[0]  # "connect to center" flag
		add_iter (hd,"[001e] X/Y/Ang1/Ang2/Flag","%.2f  %.2f  %.2f %.2f %d"%(x,y,a1,a2,f),offset,10,"<hhhhh")
	elif l_type == 2: # line/curve
#		x = struct.unpack("<H",data[offset:offset+2])[0]*0.0254
#		y = struct.unpack("<H",data[offset+2:offset+4])[0]*0.0254
		add_iter (hd,"[001e] ","",offset,length,"txt")

def loda_coords (hd,data,offset,l_type,length):
	if hd.version < 4:
		loda_coords_v3 (hd,data,offset,l_type,length)
	else:
		if l_type < 5 and l_type != 3:
			loda_coords124 (hd,data,offset,l_type)
		elif l_type == 3:
			loda_coords3 (hd,data,offset,l_type)
		elif l_type == 0x14 or l_type == 0x20:
			loda_coords_poly(hd,data,offset,l_type)
		elif l_type == 0x25:
			loda_coords_0x25(hd,data,offset,l_type)
		elif l_type == 5:
			loda_coords5 (hd,data,offset,l_type)
	# insert calls to specific coords parsing here
		else:
			add_iter (hd,"[001e]","???",offset,length,"txt")


def loda_palt (hd,data,offset,l_type,length):
	clr_model(hd,data,offset)

lens1_subtypes = {
	0:"Opacity",
	1:"Colour Limit",
	2:"Colour Add",
	3:"Inverse",
	4:"Brighten",
	5:"Tinted Greyscale",
	7:"Heat Map",
	8:"Custom Colour Map"}

lens5_types = {
	0:"Uniform",
	1:"Linear grad",
	2:"Radial grad",
	3:"Conical grad",
	4:"Square grad",
	7:"Two Colour Patt",
	9:"Bitmap Patt",
	0xa:"Full Colour Patt",
	0xb:"Texture"
}

lens5_ops = {
	0:"Normal",
	1:"And",
	2:"Or",
	3:"Xor",
	6:"Invert",
	7:"Add",
	8:"Sub",
	9:"Mult",
	0xa:"Div",
	0xb:"If lighter",
	0xc:"If darker",
	0xd:"Texturize",
	0xf:"Hue",
	0x10:"Sat",
	0x11:"Lightness",
	0x12:"Red",
	0x13:"Green",
	0x14:"Blue",
	0x18:"Diff"}

lens5_targets = {0:"Fill",1:"Outl",2:"All"}


def loda_lens (hd,data,offset,l_type,length):
	lens_type = struct.unpack("<I",data[offset:offset+4])[0]
	add_iter (hd," [1f40] Lens Type",lens_type,offset,4,"<I")
	lens_id = d2hex(data[offset+4:offset+8])
	add_iter (hd," [1f40] Lens ID",lens_id,offset+4,4,"txt")

	if lens_type == 1:
		sub_type = struct.unpack("<H",data[offset+8:offset+10])[0]
		add_iter (hd," [1f40] Lens SubType","%02x (%s)"%(sub_type,key2txt(sub_type,lens1_subtypes)),offset+8,2,"<H")
		if sub_type != 3 and sub_type != 5 and sub_type != 8:
			val =  struct.unpack("<h",data[offset+10:offset+12])[0]/10.
			add_iter (hd," [1f40] Value",val,offset+10,2,"<h")
	elif lens_type == 2:
		val = struct.unpack("<h",data[offset+8:offset+10])[0]/10.
		add_iter (hd," [1f40] Magnify Value",value,offset+8,2,"<h")
	elif lens_type == 3:
		val = struct.unpack("<h",data[offset+8:offset+10])[0]/10.
		add_iter (hd," [1f40] Fish Eye Value",value,offset+8,2,"<h")
	elif lens_type == 4:
		add_iter (hd," [1f40] WireFrame","",offset+8,2,"")
	elif lens_type == 5:
		# offsets for version 12
		xy1_off = 0x10  # only for linear?
		xtype_off = 0x28
		xy2_off = 0x2c
		xpar_off = 0x40
		op_off = 0x50
		trg_off = 0x54
		frz_off = 0x58
		fild_off = 0x70
		xt = struct.unpack("<I",data[offset+xtype_off:offset+xtype_off+4])[0]
		add_iter (hd," [1f40] Xparency Type","%02x (%s)"%(xt,key2txt(xt,lens5_types)),offset+xtype_off,4,"<I")
		op = struct.unpack("<I",data[offset+op_off:offset+op_off+4])[0]
		add_iter (hd," [1f40] Xparency Operation","%02x (%s)"%(op,key2txt(op,lens5_ops)),offset+op_off,4,"<I")
		xpar_start = struct.unpack("<d",data[offset+xpar_off:offset+xpar_off+8])[0]
		xpar_end = struct.unpack("<d",data[offset+xpar_off+8:offset+xpar_off+16])[0]
		add_iter (hd," [1f40] Xparency Start","%02d%%"%xpar_start,offset+xpar_off,8,"<d")
		add_iter (hd," [1f40] Xparency End","%02d%%"%xpar_end,offset+xpar_off+8,8,"<d")


def loda_contnr (hd,data,offset,l_type,length):
	add_iter (hd,"[1f45] Spnd ID",d2hex(data[offset:offset+4]),offset,4,"txt")


def loda_mesh (hd,data,offset,l_type,length):
	add_iter (hd,"[4ace]","",offset,len(data),"txt")
	off = 0
	nrow = struct.unpack("<I",data[offset+8:offset+12])[0]
	ncol = struct.unpack("<I",data[offset+12:offset+16])[0]
	add_iter (hd,"[4ace] Num row",nrow,offset+8,4,"<I")
	add_iter (hd,"[4ace] Num col",ncol,offset+12,4,"<I")
	off = 20
	loda_coords3 (hd,data,offset+off,l_type,"4ace set 1")

def loda_wroff (hd,data,offset,l_type):
	add_iter (hd,"[32c8] Txt Wrap Offset (mm)",struct.unpack("<i",data[offset:offset+4])[0]/10000.,offset,4,"<i")

def loda_wrstyle (hd,data,offset,l_type):
	ws = struct.unpack("<I",data[offset:offset+4])[0]
	add_iter (hd,"[32c9] Txt Wrap Style","%d (%s)"%(ws,key2txt(ws,wrap_txt_style)),offset,4,"<I")


loda_types = {
	0:"Layer",
	1:"Rectangle",
	2:"Ellipse",
	3:"Line/Curve",
	4:"Artistic Text",
	5:"Bitmap",
	6:"Paragraph Text",
	0xb:"Grid",
	0xc:"Guides",
	0x11:"Desktop",
	0x14:"Polygon",
	0x20:"Mesh",
	0x25:"Path ??",
	0x26:"B-Spline"
	}

loda_types_v3 = {
	0:"Rectangle",
	1:"Ellipse",
	2:"Line/Curve",
	3:"Text",
	4:"Bitmap", # guess
	0xa:"Grid"
	}

# loda_container 1st 4 bytes -- matches with SPND of the group

loda_type_func = {0xa:loda_outl,0x14:loda_fild,0x1e:loda_coords,
									0x28:loda_rot_center,0x64:loda_trfd,
									0xc8:loda_stlt,#0xc9 loda_description,
									0x3e8:loda_name,
									0x7d0:loda_palt,
									0x1f40:loda_lens,0x1f45:loda_contnr,
									0x2af8:loda_polygon,0x2eea:loda_grad,0x2efe:loda_rot,
									0x32c8:loda_wroff,0x32c9:loda_wrstyle,
									0x4ace:loda_mesh}

def loda_v5 (hd,size,data):
	n_args = struct.unpack('<H', data[2:4])[0]
	s_args = struct.unpack('<H', data[4:6])[0]
	s_types = struct.unpack('<H', data[6:8])[0]
	l_type = struct.unpack('<H', data[8:10])[0]
	add_iter (hd, "# of args", n_args,2,2,"<H")
	add_iter (hd, "Start of args offsets", "%02x"%s_args,4,2,"<H")
	add_iter (hd, "Start of arg types", "%02x"%s_types,6,2,"<H")
	t_txt = "%02x"%l_type
	if hd.version == 3:
		if loda_types_v3.has_key(l_type):
			t_txt += " " + loda_types_v3[l_type]
	else:
		if loda_types.has_key(l_type):
			t_txt += " " + loda_types[l_type]
	add_iter (hd, "Type", t_txt,8,2,"<H")
	a_txt = ""
	t_txt = ""
	for i in range(n_args,0,-1):
		a_txt += " %02x"%struct.unpack('<H',data[s_args+i*2-2:s_args+i*2])[0]
		t_txt += " %02x"%struct.unpack('<H',data[s_types+(n_args-i)*2:s_types+(n_args-i)*2+2])[0]
	add_iter (hd, "Args offsets",a_txt,s_args,n_args*2,"<H")
	add_iter (hd, "Args types",t_txt,s_types,n_args*2,"<H")
	if loda_types.has_key(l_type):
		for i in range(n_args, 0, -1):
			offset = struct.unpack('<H',data[s_args+i*2-2:s_args+i*2])[0]
			length = struct.unpack('<H',data[s_args+i*2:s_args+i*2+2])[0]-offset
			argtype = struct.unpack('<H',data[s_types + (n_args-i)*2:s_types + (n_args-i)*2+2])[0]
			if loda_type_func.has_key(argtype):
				loda_type_func[argtype](hd,data,offset,l_type,length)
			else:
				add_iter (hd,"[%02x]"%(argtype),"???",offset,struct.unpack('<H',data[s_args+i*2:s_args+i*2+2])[0]-offset,"<H")

def loda (hd,size,data):
	if hd.version < 6:
		loda_v5 (hd,size,data)
		return
	n_args = struct.unpack('<I', data[4:8])[0]
	s_args = struct.unpack('<I', data[8:0xc])[0]
	s_types = struct.unpack('<I', data[0xc:0x10])[0]
	l_type = struct.unpack('<I', data[0x10:0x14])[0]
	add_iter (hd, "# of args", n_args,4,4,"<I")
	add_iter (hd, "Start of args offsets", "%02x"%s_args,8,4,"<I")
	add_iter (hd, "Start of arg types", "%02x"%s_types,0xc,4,"<I")
	t_txt = "%02x"%l_type
	if loda_types.has_key(l_type):
		t_txt += " " + loda_types[l_type]

	add_iter (hd, "Type", t_txt,0x10,2,"<I")

	a_txt = ""
	t_txt = ""
	for i in range(n_args+1,0,-1):
		a_txt += " %04x"%struct.unpack('<L',data[s_args+i*4-4:s_args+i*4])[0]
		t_txt += " %04x"%struct.unpack('<L',data[s_types+(n_args-i)*4:s_types+(n_args-i)*4+4])[0]
	add_iter (hd, "Args offsets",a_txt,s_args,n_args*4,"txt")
	add_iter (hd, "Args types",t_txt,s_types,n_args*4,"txt")

	if loda_types.has_key(l_type):
		for i in range(n_args, 0, -1):
			offset = struct.unpack('<L',data[s_args+i*4-4:s_args+i*4])[0]
			length = struct.unpack('<L',data[s_args+i*4:s_args+i*4+4])[0]-offset
			argtype = struct.unpack('<L',data[s_types + (n_args-i)*4:s_types + (n_args-i)*4+4])[0]
			if loda_type_func.has_key(argtype):
				loda_type_func[argtype](hd,data,offset,l_type,length)
			else:
				add_iter (hd,"[%04x]"%(argtype),"???",offset,struct.unpack('<L',data[s_args+i*4:s_args+i*4+4])[0]-offset,"txt")
#				print 'Unknown argtype: %x'%argtype

dtypes = {1:"Push",2:"Zip",3:"Twist"}
dstflags = {0:"None",1:"Smooth",2:"Random",4:"Local"}

def lnkt (hd,size,data):
	n_args = struct.unpack('<i', data[4:8])[0]
	s_args = struct.unpack('<i', data[8:0xc])[0]
	for j in range(n_args):
		start = struct.unpack('<L',data[s_args+j*4:s_args+j*4+4])[0]
		add_iter (hd, "???", "%02x"%struct.unpack('<L',data[start:start+4])[0],start,4,"<I")
		add_iter (hd, "spnd ID1", d2hex(data[start+4:start+8]),start+4,4,"<I")
		add_iter (hd, "spnd ID2", d2hex(data[start+8:start+12]),start+8,4,"<I")

def trfd (hd,size,data):
	n_args = struct.unpack('<i', data[4:8])[0]
	s_args = struct.unpack('<i', data[8:0xc])[0]
	s_types = struct.unpack('<i', data[0xc:0x10])[0]
#	start = 32
#	if hd.version > 12:
#		start = 40
#	if hd.version == 5:
#		start = 18
	for j in range(n_args):
		start = struct.unpack('<L',data[s_args+j*4:s_args+j*4+4])[0]
		if hd.version > 12:
			start +=8
		switch = struct.unpack('<H', data[start:start+2])[0]
		start += 8
		if switch == 8:
			for i in (0,1):                     
				var = struct.unpack('<d', data[start+i*8:start+8+i*8])[0]
				add_iter (hd, "var%d"%(i+1), "%f"%var,start+i*8,8,"<d")
			add_iter (hd, "x0", "%u"%(struct.unpack('<d', data[start+16:start+24])[0]/10000),start+16,8,"<d")
			for i in (3,4):
				var = struct.unpack('<d', data[start+i*8:start+8+i*8])[0]
				add_iter (hd, "var%d"%(i+1), "%f"%var,start+i*8,8,"<d")
			add_iter (hd, "y0", "%u"%(struct.unpack('<d', data[start+40:start+48])[0]/10000),start+40,8,"<d")
		elif switch == 0x10:
			# Distortion type
			dtype = struct.unpack('<H', data[start:start+2])[0]
			dtt = "Unknown"
			if dtypes.has_key(dtype):
				dtt = dtypes[dtype]
			add_iter (hd, "Distortion type", "%02x (%s)"%(dtype,dtt),start,2,"<H")
			
			# Coords of the distortion
			Xd = round(struct.unpack('<i', data[start+2:start+6])[0]/10000.,2)
			Yd = round(struct.unpack('<i', data[start+6:start+10])[0]/10000.,2)
			add_iter (hd, "Distortion Coords", "%.2f/%.2f   (corr. %.2f/%.2f)"%(Xd,Yd,Xd+hd.width/2,Yd+hd.height/2),start+2,8,"<txt")
			
			# Distiortion sub-type
			dstype = struct.unpack('<I', data[start+10:start+14])[0]
			dstt = ""
			if dstype == 0:
				dstt = "None"
			else:
				if dstype&1 == 1:
					dstt = "Smooth "
				if dstype&2 == 2:
					dstt += "Random "
				if dstype&4 == 4:
					dstt = "Local"
			add_iter (hd, "Distortion Subtype", "%02x (%s)"%(dstype,dstt),start+10,4,"<I")
			
			# Options
			dopt1 = struct.unpack('<i', data[start+14:start+18])[0]
			dopt2 = struct.unpack('<i', data[start+18:start+22])[0]
			add_iter (hd, "Distortion Option 1", "%d"%dopt1,start+14,4,"<i")
			add_iter (hd, "Distortion Option 2", "%d"%dopt2,start+18,4,"<i")
		else:
			add_iter (hd, "Unknown Type", "",start,2,"txt")

def disp_expose (da, event,pixbuf):
	ctx = da.window.cairo_create()
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()
	ctx.stroke()

def disp (hd,size,data,page):
	# naive version, not always works as needed
	bmp = struct.unpack("<I",data[0x18:0x1c])[0]
	bmpoff = struct.pack("<I",len(data)+10-bmp)
	img = 'BM'+struct.pack("<I",len(data)+8)+'\x00\x00\x00\x00'+bmpoff+data[4:]
	pixbufloader = gtk.gdk.PixbufLoader()
	pixbufloader.write(img)
	pixbufloader.close()
	pixbuf = pixbufloader.get_pixbuf()
	imgw=pixbuf.get_width()
	imgh=pixbuf.get_height()
	hd.da = gtk.DrawingArea()
	hd.hbox0.pack_start(hd.da)
	hd.da.connect('expose_event', disp_expose,pixbuf)
	ctx = hd.da.window.cairo_create()
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()
	ctx.stroke()
	hd.da.show()

def vpat (hd,size,data):
	add_iter (hd, "Vect ID", struct.unpack("<I",data[0:4])[0],0,4,"<I")

def txsm (hd,size,data):
	# ver16 -- add '40 06' parsing (seems to be different '40 06').
	# 6,7,8 -- 3, 8bidi,9 -- 4
	# 10,11 -- 5; 12 -- 6; 13 -- 8; 14 -- 9; 15 -- b; 16 -- c
	
	off = 0x24
	if hd.version == 15:
		off += 1
	blk_flag1 = struct.unpack('<I', data[off:off+4])[0]
	add_iter (hd, "blk_flag1", blk_flag1,off,4,"<i")
	off += 4
	if blk_flag1 == 1:
		if hd.version > 7:
			add_iter (hd, "txt ID", d2hex(data[off:off+4]),off,4,"<I")
			off += 4
			for i in range(6):
				var = struct.unpack('<d', data[off+i*8:off+8+i*8])[0]
				add_iter (hd, "var%d"%(i+1), "%d"%(var/10000),off+i*8,8,"<d")
			off += 48

			blk_flag2 = struct.unpack('<I', data[off:off+4])[0]
			add_iter (hd, "blk_flag2", blk_flag2,off,4,"<i")
			off += 4
			if blk_flag2:
				for i in range(8):
					var = struct.unpack('<i', data[off+i*4:off+4+i*4])[0]
					add_iter (hd, "v%d"%(i+1), "%d"%var,off+i*4,4,"<i")
				off += 32

		else:
			for i in range(8):
				var = struct.unpack('<h', data[off+i*4:off+4+i*4])[0]
				add_iter (hd, "v%d"%(i+1), "%d"%var,off+i*4,4,"<h")
			off += 32
	elif hd.version <8:
		off += 4

	if hd.version < 8:
		add_iter (hd, "txt ID", d2hex(data[off:off+4]),off,4,"<I")
		off += 4
		for i in range(6):
			var = struct.unpack('<d', data[off+i*8:off+8+i*8])[0]
			add_iter (hd, "var%d"%(i+1), "%d"%(var/10000),off+i*8,8,"<d")
		off += 48

	if hd.version < 15:
		num1 = struct.unpack('<I', data[off:off+4])[0]
		add_iter (hd, "num1", num1,off,4,"<I")
		off += 4
	else:
		off += 12
		num1 = struct.unpack('<I', data[off:off+4])[0]
		add_iter (hd, "num1", num1,off,4,"<I")
		off += 4
	
	if num1 == 0:
		if hd.version > 7:
			off += 4
			if hd.version > 8: #( txsm ver4+)
				off += 2
			if hd.version > 13:
				off += 2
		for i in range(6):
			v = struct.unpack('<i', data[off:off+4])[0]
			add_iter (hd, "v%d"%i,v,off,4,"<i")
			off += 4
		if hd.version < 8:
			off += 8
		num4 = struct.unpack('<I', data[off:off+4])[0]
		add_iter (hd, "num4", num4,off,4,"<I")
		off += 4
	add_iter (hd, "Stlt ID", d2hex(data[off:off+4]),off,4,"txt")
	# skip 1 byte
	off += 5
	if hd.version > 12 and num1 != 0: # skip one more byte for version 13
		off += 1
	num = struct.unpack('<I', data[off:off+4])[0]
	add_iter (hd, "Num of recs (Style)", num,off,4,"<I")
	off += 4
	for i in range(num):
		id = ord(data[off])
		flag1 = ord(data[off+1])
		flag2 = ord(data[off+2])
		if hd.version > 7:
			flag3 = ord(data[off+3]) # seems to be 8 all the time
			add_iter (hd, "fl0 fl1 fl2 fl3 [%d]"%(i*2), "%02x %02x %02x %02x"%(id,flag1,flag2,flag3),off,4,"txt")
			off += 4
		else:
			add_iter (hd, "fl0 fl1 fl2 [%d]"%(i*2), "%02x %02x %02x"%(id,flag1,flag2),off,3,"txt")
			off += 3
			
		if flag2&1 == 1:
			# Font
			enctxt = "Unknown"
			enc = struct.unpack("<H",data[off+2:off+4])[0]
			if charsets.has_key(enc):
				enctxt = charsets[enc]
			add_iter (hd, "\tFont ID, Charset", "%s, %s (%02x)"%(d2hex(data[off:off+2]),enctxt,enc),off,4,"txt")
			off += 4
		if flag2&2 == 2:
			# Bold/Italic etc
			add_iter (hd, "\tFont Style", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
		if flag2&4 == 4:
			# Font Size
			add_iter (hd, "\tFont Size", struct.unpack("<I",data[off:off+4])[0]*72/254000,off,4,"txt")
			off += 4
		if flag2&8 == 8:
			# assumption
			add_iter (hd, "\tRotate", struct.unpack("<i",data[off:off+4])[0]/1000000,off,4,"txt")
			off += 4
		if flag2&0x10 == 0x10:
			# Offset X
			add_iter (hd, "\tOffsetX", struct.unpack("<i",data[off:off+4])[0],off,4,"txt")
			off += 4
		if flag2&0x20 == 0x20:
			# Offset Y
			add_iter (hd, "\tOffsetY", struct.unpack("<i",data[off:off+4])[0],off,4,"txt")
			off += 4
		if flag2&0x40 == 0x40:
			# Fild ID (font colour)
			add_iter (hd, "\tFild ID", d2hex(data[off:off+4]),off,4,"txt")
			off += 4
			if hd.version > 14:
				off += 48 # ftil
		if flag2&0x80 == 0x80:
			# Outl ID (colour of the text outline)
			add_iter (hd, "\tOutl ID", d2hex(data[off:off+4]),off,4,"txt")
			off += 4

		if hd.version > 7:
			if flag3&8 == 8:
				if hd.version > 12:
					tlen = struct.unpack("<I",data[off:off+4])[0]
					txt = unicode(data[off+4:off+4+tlen*2],"utf16")
					add_iter (hd, "\tEncoding", txt,off,4+tlen*2,"txt")
					off += 4 + tlen*2
				else:
					enc = data[off:off+2]
					add_iter (hd, "\tEncoding", enc,off,2,"txt")
					off += 4
			if flag3&0x20 == 0x20:
				flag = ord(data[off])
				add_iter (hd, "\tFild/ftil flag",flag ,off,1,"<B")
				if flag:
					add_iter (hd, "\tFild ID", d2hex(data[off:off+4]),off,4,"txt")
					off += 4
					if hd.version > 14:
						off += 48 # ftil

	num2 = struct.unpack('<I', data[off:off+4])[0]
	add_iter (hd, "Num of 'Char'", num2,off,4,"<I")
	off += 4
#	if num2 > 100:
#		print 'num2 > 100',num2
		
	for i in range(num2):
		if hd.version >= 12:
			add_iter (hd, "Char %u"%i, "%s [%s] %s"%(d2hex(data[off:off+2]),d2hex(data[off+2:off+3]),d2hex(data[off+3:off+8])),off,8,"txt")
			off += 8
		else:
			add_iter (hd, "char %u"%i, "%s [%s] %s"%(d2hex(data[off:off+2]),d2hex(data[off+2:off+3]),d2hex(data[off+3:off+4])),off,4,"txt")
			off += 4
	txtlen = num2
	if hd.version >= 12:
		txtlen = struct.unpack('<I', data[off:off+4])[0]
		add_iter (hd, "Text length", txtlen,off,4,"<I")
		off += 4
	add_iter (hd, "Text", "",off,txtlen,"txt")

def stlt(data,page,parent):
	# FIXME! ver 13 and newer is different
	offset = 4
	d1 = struct.unpack("<I",data[offset:offset+4])[0]
	# this num matches with num of (un)named records in "set 11" below
	add_pgiter(page,"Num of style entries [%d]"%d1,"cdr","stlt_d1",data[offset:offset+4],parent)
	offset += 4

	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"fild list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"%s | %s | %s"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8]),d2hex(data[offset+8:offset+12])),"cdr","stlt_s0",data[offset:offset+12],s_iter)
		offset += 12
		if page.version > 12:
			add_pgiter(page,"\tTrafo?","cdr","stlt_d1",data[offset:offset+48],s_iter)
			offset += 48

	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"outl list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"%s | %s | %s"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8]),d2hex(data[offset+8:offset+12])),"cdr","stlt_s1",data[offset:offset+12],s_iter)
		offset += 12

	size = 60
	if page.version < 10:
		size = 44
	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"font list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s2",data[offset:offset+size],s_iter)
		offset += size

	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"align list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s3",data[offset:offset+12],s_iter)
		offset += 12

	size = 52
	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"interval list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s4",data[offset:offset+size],s_iter)
		offset += size

	size = 152
	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"set5 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s5",data[offset:offset+size],s_iter)
		offset += size

	size = 784
	d2 = struct.unpack("<I",data[offset:offset+4])[0]
	s_iter = add_pgiter(page,"Tabs list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
	offset += 4
	for i in range(d2):
		add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s6",data[offset:offset+size],s_iter)
		offset += size

	bkpoff = offset

	try:
		size = 80
		shift = 0
		if page.version < 10:  # VERIFY in what version it was changed
			size = 72
			shift = -8
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"bullet list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			flag = struct.unpack("<I",data[offset+68+shift:offset+72+shift])[0] # for ver > 10
			if flag:
				inc = 8
			else:
				inc = 0
			if page.version > 12:
				if struct.unpack("<I",data[offset+8:offset+12])[0]:
					inc = 32
				else:
					inc = -24
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s7",data[offset:offset+size+inc],s_iter)
			offset += size + inc

		size = 28
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"Indent list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s (pID %s)"%(d2hex(data[offset:offset+4]),d2hex(data[offset+4:offset+8])),"cdr","stlt_s8",data[offset:offset+size],s_iter)
			offset += size

		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		size = 32
		if page.version > 12:
			size = 36
		s_iter = add_pgiter(page,"Hypen list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s9",data[offset:offset+size],s_iter)
			offset += size

		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		size = 28
		if page.version < 9: # was < 10
			size = 24
		s_iter = add_pgiter(page,"Dropcap list [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s10",data[offset:offset+size],s_iter)
			offset += size

		size = 12
		d2 = struct.unpack("<I",data[offset:offset+4])[0]
		s_iter = add_pgiter(page,"set11 [%u]"%d2,"cdr","stlt_d2",data[offset:offset+4],parent)
		offset += 4
		for i in range(d2):
			add_pgiter(page,"ID %s"%d2hex(data[offset:offset+4]),"cdr","stlt_s11",data[offset:offset+size],s_iter)
			offset += size

	# size after name
	# dword 1:	3		2		1
	# ver <10:	44	24	8
	# ver 10+:	48	28	8

		s_iter = add_pgiter(page,"set12","cdr","","",parent)
		# based on latest idea -- parse to end
	
		while offset < len(data):
			num = struct.unpack("<I",data[offset:offset+4])[0]
			num2 = struct.unpack("<I",data[offset+12:offset+16])[0]
			add_pgiter(page,"num %d ID %s (pID %s) %s"%(num,d2hex(data[offset+4:offset+8]),d2hex(data[offset+8:offset+12]),d2hex(data[offset+12:offset+16])),"cdr","stlt_s12",data[offset:offset+20],s_iter)
			if num == 3:
				asize = 48
			elif num == 2:
				asize = 28
			else: # num == 1
				asize = 8
			offset += 20
			if page.version < 9 and num > 1: # was PV 10
				asize -= 4
			namelen = struct.unpack("<I",data[offset:offset+4])[0]
			if page.version < 12:
				# ended with \0
				# FIXME! I don't know where to take encoding for style names, set Russian just for now
				name = unicode(data[offset+4:offset+4+namelen-1],"cp1251")
			else:
				name = unicode(data[offset+4:offset+4+namelen*2],"utf16")
				namelen *= 2
			add_pgiter(page,"\t[%s]"%name,"cdr","stlt_s12_p2",data[offset:offset+4+namelen+asize],s_iter)
			offset += 4+asize+namelen
	except:
			add_pgiter(page,"Tail","cdr","",data[bkpoff:],parent)
			print "stlt exception, see 'tail'"

cdr_ids = {
	"arrw":arrw,
	"bbox":bbox,
	"bmp ":bmp,
	"bmpf":bmpf,
	"DISP":disp,
	"fild":fild,
	"fill":fild,
	"font":font,
	"ftil":ftil,
	"guid":guid,
	"lnkt":lnkt,
	"lobj":loda,
	"loda":loda,
	"obbx":obbx,
	"outl":outl,
	"trfd":trfd,
	"ttil":ftil,
	"txsm":txsm,
	"user":user,
	"vpat":vpat,
	"stlt_s0":stlt_s0,
	"stlt_s1":stlt_s1,
	"stlt_s2":stlt_s2,
	"stlt_s3":stlt_s3,
	"stlt_s4":stlt_s4,
	"stlt_s5":stlt_s5,
	"stlt_s6":stlt_s6,
	"stlt_s7":stlt_s7,
	"stlt_s8":stlt_s8,
	"stlt_s9":stlt_s9,
	"stlt_s10":stlt_s10,
	"stlt_s11":stlt_s11,
	"stlt_s12_p2":stlt12_p2
	}


def collect_cmpr(model,parent,idx):
	ic = model.iter_n_children(parent)
	blk = []
	data = ""
	cbs = 0
	if ic == 0:
		t = model.get_value(parent,1)[1]
		d = model.get_value(parent,3)
		data = t + struct.pack("<I",idx)+d
		blksize = len(data)-8
		if len(data) & 1:
			data += "\x00"
		blk.append(blksize)
		idx += 1
	else:
		data = "LIST"+struct.pack("<I",idx)+model.get_value(parent,0)
		idx += 1
		for i in range(ic):
			iter = model.iter_nth_child(parent,i)
			lt = model.get_value(iter,0)
			if lt != "CMX1":
				tmpdata, tmpblocks,bs,idx = collect_cmpr(model,iter,idx)
				data += tmpdata
				blk += tmpblocks
				cbs += bs+8
				if cbs & 1:
					cbs += 1
				
		blksize = cbs + 4
		blk.insert(0,blksize)
	return data,blk,blksize,idx

def pack_cmpr(model,parent):
	blocks = []
	data = ""
	idx = 0
	nc = model.iter_n_children(parent)
	for i in range(nc):
		iter = model.iter_nth_child(parent,i)
		tmpdata, tmpblocks, bs, idx = collect_cmpr(model,iter, idx)
		data += tmpdata
		blocks += tmpblocks
	zdata = zlib.compress(data)
	sblocks = ""
	for i in range(len(blocks)):
		sblocks += struct.pack("<I",blocks[i])
	zblk = zlib.compress(sblocks)
	
	res = "cmpr"+struct.pack("<I",len(zdata)+8) + struct.pack("<I",len(data))
	res += struct.pack("<I",len(zblk)+8) + struct.pack("<I",len(blocks)*4)
	res += "CPng\x01\x00\x04\x00"+zdata + "CPng\x01\x00\x04\x00"+ zblk
	if len(res) & 1:
		res += "\x00"
	return "LIST"+struct.pack("<I",len(res))+res


def dump_chunk(model, parent):
	nc = model.iter_n_children(parent)
	tmpbuf = ""
	t = model.get_value(parent,1)[1]
	s = model.get_value(parent,2)
	pad = ""
	if s & 1:
		pad = "\x00"
	s = struct.pack("<I",s)
	lt = model.get_value(parent,0)
	if nc == 0 or lt == "iccp":
		return t+s+model.get_value(parent,3)+pad
	else:
		if lt == "cmpr" and s > 52:
			return pack_cmpr(model,parent)
		else:
			tmpbuf += t + s + lt
			for i in range(nc):
				iter = model.iter_nth_child(parent,i)
				tmpbuf += dump_chunk (model, iter)
			return tmpbuf

def save (page,fname):
	model = page.view.get_model()
	print "Save request. Stub. To be continued..."
#	return
	buf = ""
	if page.version > 6 and page.version < 14:
		parent = model.iter_nth_child(None,0)
		buf += dump_chunk(model,parent)
	s = struct.pack("<I",len(buf)-8)
	buf = buf[0:4] +s +buf[8:]
	f = open(fname,"w")
	f.write(buf)
	f.close()

def cdr_open (buf,page,parent,fmttype="cdr"):
	# Path, Name, ID
	page.dictmod = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
	chunk = record()
	chunk.load (buf,page,parent,0,(),fmttype)

class record:
	fourcc = ''
	offset = 0
	size = 0
	data = ''

	def unpack(self, page, parent, blocksizes=(), fmttype="cdr", offset=12):
		decomp = zlib.decompressobj()
		self.uncmprdata = decomp.decompress(self.data[offset:])
		offset = 0
#		print "------------"
#		print d2hex(self.uncmprdata," ",16)
#		print "------------"
		
##		add_pgiter(page,"Uncompressed data",fmttype,"",self.uncmprdata,parent)
		while offset < len(self.uncmprdata):
			chunk = record()
			chunk.load(self.uncmprdata, page, parent, offset, blocksizes, fmttype)
			offset += 8 + chunk.size

	def cmpr(self,page,parent,fmttype="cdr"):
		cmprsize = struct.unpack('<I', self.data[4:8])[0]
		uncmprsize = struct.unpack('<I', self.data[8:12])[0]
		blcks = struct.unpack('<I', self.data[12:16])[0]
		blcksdata = zlib.decompress(self.data[28+cmprsize:])
		blocksizes = []
		for i in range(0, len(blcksdata), 4):
			blocksizes.append(struct.unpack('<I', blcksdata[i:i+4])[0])

#		print len(blocksizes),blocksizes

		self.unpack(page, parent, blocksizes, "cdr", 28)

	def load(self, buf, page, parent, offset=0, blocksizes=(),fmttype="cdr"):
		self.offset = offset
		self.fourcc = buf[offset:offset+4]
		self.size = struct.unpack('<I', buf[offset+4:offset+8])[0]
		if len(blocksizes):
			self.size = blocksizes[self.size]
		self.data = buf[offset+8:offset+8+self.size]
		if self.size & 1:
			self.size += 1

		# skip garbage
		if self.fourcc != "clo " and self.fourcc != "cloa" and self.fourcc != "clof" and self.fourcc != "cloo":
			if page.version < 16:
				f_iter = add_pgiter(page,self.fourcc,fmttype,self.fourcc,self.data,parent)
			else:
				f_iter = add_pgiter(page,self.fourcc,fmttype,"idx16%s"%self.fourcc,self.data,parent)
		if page.version < 16 and (self.fourcc == "outl" or self.fourcc == "fild" or self.fourcc == "fill" or self.fourcc == "arrw" or self.fourcc == "bmpf"):
			d_iter = page.dictmod.append(None,None)
			page.dictmod.set_value(d_iter,0,page.model.get_string_from_iter(f_iter))
			page.dictmod.set_value(d_iter,2,d2hex(self.data[0:4]))
			page.dictmod.set_value(d_iter,1,self.fourcc)
			if self.fourcc == "fild" or self.fourcc == "fill":
				off = 4
				if page.version > 12:
					off = 12
				t = struct.unpack("<H",self.data[off:off+2])[0]
				ttxt = key2txt(t,fild_types)
				page.dictmod.set_value(d_iter,3,"0x%02x (%s)"%(t,ttxt))
		if page.version < 16 and self.fourcc == 'mcfg':
			page.hd.width = struct.unpack("<I",self.data[4:8])[0]/10000
			page.hd.height = struct.unpack("<I",self.data[8:12])[0]/10000
		if self.fourcc == 'iccd':
			icc.parse(page,self.data,f_iter)
		if self.fourcc == 'pack':
			self.pack(page,f_iter)
		if self.fourcc == 'page' and fmttype == "cmx":
			cmx.parse_page(page,self.data,f_iter)

		if self.fourcc == 'RIFF' or self.fourcc == 'LIST':
			if self.fourcc == 'RIFF' and fmttype == "cdr":
				v = ord(self.data[3])
				if v < 0x21:
					page.version = 3
				elif v < 0x41:
					page.version = v - 48
				else:
					page.version = v - 55
			name = buf[offset+8:offset+12]
			page.model.set_value(f_iter,0,name)
			page.model.set_value(f_iter,1,(fmttype,self.fourcc))

			parent = f_iter
			if name == 'vect':
				chunk = record()
				chunk.load(self.data[16:],page,parent,0,(),"cmx")
			if name == 'stlt' and page.version >= 7:
				try:
#					print 'stlt'
					stlt(self.data,page,parent)
				except:
					print "Something failed in 'stlt'."
			elif name == 'cmpr':
				self.cmpr(page,parent,fmttype)
			else:
				offset += 12
				while offset < self.offset + 8 + self.size:
					chunk = record()
					chunk.load(buf, page, parent, offset, blocksizes, fmttype)
					offset += 8 + chunk.size
		elif page.version == 16:
			try:
				strid = struct.unpack("<i",self.data[:4])[0]
				off1 = struct.unpack("<I",self.data[8:12])[0]
				off2 = off1 + struct.unpack("<I",self.data[4:8])[0]
				if strid != -1:
					ci = page.model.iter_nth_child(None,strid)
					data = page.model.get_value(ci,3)[off1:off2]
					p_iter = add_pgiter(page,"%s [%04x - %04x]"%(self.fourcc,off1,off2),"cdr",self.fourcc,data,ci)
					page.model.set_value(p_iter,8,("path",page.model.get_string_from_iter(f_iter)))
					page.model.set_value(f_iter,8,("path",page.model.get_string_from_iter(p_iter)))

					if self.fourcc == "outl" or self.fourcc == "fild" or self.fourcc == "arrx" or self.fourcc == "bmpf":
						d_iter = page.dictmod.append(None,None)
						page.dictmod.set_value(d_iter,0,page.model.get_string_from_iter(p_iter))
						page.dictmod.set_value(d_iter,2,d2hex(data[0:4]))
						page.dictmod.set_value(d_iter,1,self.fourcc)
						if self.fourcc == "fild":
							off = 4
							if page.version > 12:
								off = 12
							t = struct.unpack("<H",data[off:off+2])[0]
							ttxt = key2txt(t,fild_types)
							page.dictmod.set_value(d_iter,3,"0x%02x (%s)"%(t,ttxt))
					if self.fourcc == 'mcfg':
						if page.version == 6:
							page.hd.width = struct.unpack("<I",data[0x1c:0x20])[0]/10000
							page.hd.height = struct.unpack("<I",data[0x20:0x24])[0]/10000
						elif page.version < 6:
							page.hd.width = struct.unpack("<H",data[0x1c:0x20])[0]*0.0254
							page.hd.height = struct.unpack("<H",data[0x20:0x24])[0]*0.0254
						else:
							page.hd.width = struct.unpack("<I",data[4:8])[0]/10000
							page.hd.height = struct.unpack("<I",data[8:12])[0]/10000
			except:
				print 'Failed in v16 dat'
