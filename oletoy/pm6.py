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

import struct
from utils import *

recs = {
	0x01:("0x01", 10),
	0x04:("0x04", 104),
	0x05:("Pages", 472),
	0x09:("TxtProps [9]", 16),
	0x0b:("Paragraphs", 80),
	0x0c:("TxtStyles", 164),
	0x0d:("Text", 1),
	0x0e:("TIFF ?", 1),
	0x0f:("WMF ?", 1),
	0x10:("0x10", 332),
	0x11:("0x11", 4),
	0x12:("0x12", 298), # FIXME!
	0x13:("Fonts", 144),
	0x14:("Styles", 334),
	0x15:("Colors", 210),
	0x18:("0x18", 2496),  # FIXME!
	0x1a:("TextBlock", 36),
	0x19:("Shapes", 258),  # 136 in ver6?
	0x1b:("TxtProps [1B]", 0x40), # most likely 0x18
	0x1c:("Chars", 30),
	0x1f:("0x1f", 62),
	0x21:("0x21", 32), # FIXME!
	0x24:("ImgProps [24]", 1),
	0x25:("0x25", 562),
	0x28:("XForms", 26),
	0x29:("0x29", 1),  # two dwords of str lengths, than two strings
	0x2a:("0x2a", 192), # FIXME!
	0x2d:("0x2a", 192), # FIXME!
	0x2e:("0x2e", 1),
	0x2f:("Masters", 508),
	0x31:("Layers", 46),
}

fonts_dir = []

eflag = ">"

unkn_records = []  # for deduplication of warnings on unknown records

def chars (page, data, size, parent):
	rlen = 30
	for i in range(size):
		tlen = struct.unpack("<H",data[i*rlen:i*rlen+2])[0]
		add_pgiter(page,"Length: %d"%tlen,"pm","char",data[i*rlen:i*rlen+rlen],parent)


def fonts (page, data, size, parent):
	global fonts_dir
	rlen = 94
	if page.version < 5:
		rlen = 144
	for i in range(size):
		pos = data[i*rlen:].find("\x00")
		cname = data[i*rlen:i*rlen+pos]
		add_pgiter(page,"%s"%cname,"pm","font",data[i*rlen:i*rlen+rlen],parent)
		fonts_dir.append(cname)


def colors (page, data, size, parent):
	rlen = 210
	if page.version < 5:
		rlen = 64
	for i in range(size):
		pos = data[i*rlen:].find("\x00")
		cname = data[i*rlen:i*rlen+pos]
		add_pgiter(page,"%s"%cname,"pm","color",data[i*rlen:i*rlen+rlen],parent)


def pages (page, data, size, parent):
	rlen = 472
	if page.version < 5:
		rlen = 286
	for i in range(size):
		id1 = struct.unpack("<H",data[i*rlen:i*rlen+2])[0]
		id2 = struct.unpack("<H",data[i*rlen+2:i*rlen+4])[0]
		id3 = struct.unpack("<H",data[i*rlen+4:i*rlen+6])[0]
		side = "(R)"
		if page.version > 4:
			lr = ord(data[i*rlen+0x1bc])
			if lr == 1:
				side = "(L)"
		add_pgiter(page,"Page %02x, %02x %02x %s"%(id2,id1, id3,side),"pm","page",data[i*rlen:i*rlen+rlen],parent)


sh_types = {
	0x1:"Text",
	0x2:"Image",
	0x3:"Line",
	0x4:"Rect",
	0x5:"Ellipse",
	0x6:"Bitmap",
	0xa:"Metafile",  # vector img?
	0xc:"Polygon",
	0xe:"Group",
}


def shapes (page, data, size, parent):
	rlen = 258
	if page.version == 6:
		rlen = 136
	elif page.version == 5:
		rlen = 78
	elif page.version < 5:
		rlen = 58
	for i in range(size):
		type_id = ord(data[i*rlen])
		flag = "%02x"%(ord(data[i*rlen+1]))
		shapeid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		ttxt = key2txt(type_id,sh_types,"%02x"%type_id)
		if type_id == 0xe:
			subtype = ord(data[i*rlen+0x28])
			if subtype == 2:
				ttxt += " (start)"
			else:
				ttxt += " (end)"
		add_pgiter(page,"%s %s %04x"%(ttxt,flag,shapeid),"pm","shape",data[i*rlen:i*rlen+rlen],parent)


def paras (page, data, size, parent):
	rlen = 80
	for i in range(size):
		tlen = struct.unpack("<H",data[i*rlen:i*rlen+2])[0]
		add_pgiter(page,"%02x"%tlen,"pm","para",data[i*rlen:i*rlen+rlen],parent)
		# 0x2 0x1c  keep with next offset[0x3] lines
		# 0x2 &40 -- include in ToC
		# 0x5 -- dictionary
		# 0x6: dword -- style id  (& 55 at 0x2)
		# 0xa: word -- left indent pts*20
		# 0xc: word -- first indent pts*20
		# 0xe: word -- right indent pts*20
		# 0x10: word -- before indent pts*20
		# 0x12: word -- after indent pts*20
		# 0x14: word -- auto above pts*10
		# 0x16: word -- auto leading %
		# 0x18: word -- word space MIN
		# 0x1a: word -- word space MAX
		# 0x1c: word -- word space Desired
		# 0x1e: word -- letter space MIN
		# 0x20: word -- letter space MAX
		# 0x22: word -- letter space Desired
		# 0x27 &2 -- leading method = top of caps
		# 0x28 &1 -- keep lines together, &20 -- widow control, &80 -- orphan control
		# 0x29 &4 -- pg break before, &8 -- column break before
		# 0x2c -- rule above paragraph


def styles (page, data, size, parent):
	rlen = 334
	noff = 276
	if page.version < 5:
		rlen = 320
		noff = 262
	for i in range(size):
		styleid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		pos = data[i*rlen+noff:].find("\x00")
		cname = data[i*rlen+noff:i*rlen+noff+pos]
		add_pgiter(page,"%02x %s"%(styleid,cname),"pm","style",data[i*rlen:i*rlen+rlen],parent)


def xforms (page, data, size, parent):
	rlen = 26
	for i in range(size):
		xformid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		add_pgiter(page,"XForm %02x"%(xformid),"pm","xform",data[i*rlen:i*rlen+rlen],parent)


def masters (page, data, size, parent):
	rlen = 508
	for i in range(size):
		masterid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		pos = data[i*rlen:].find("\x00")
		cname = data[i*rlen:i*rlen+pos]
		add_pgiter(page,"%02x %s"%(masterid,cname),"pm","layer",data[i*rlen:i*rlen+rlen],parent)


def layers (page, data, size, parent):
	rlen = 46
	for i in range(size):
		layerid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		pos = data[i*rlen:].find("\x00")
		cname = data[i*rlen:i*rlen+pos]
		add_pgiter(page,"%02x %s"%(layerid,cname),"pm","layer",data[i*rlen:i*rlen+rlen],parent)


def txtblks (page, data, size, parent):
	rlen = 36
	for i in range(size):
		txtblkid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		items = ""
		for j in range(6):
			items += "%02x "%struct.unpack("<H",data[i*rlen+j*2:i*rlen+2+j*2])[0]
		add_pgiter(page,"Txt %02x [%s]"%(txtblkid,items[:-1]),"pm","txtblock",data[i*rlen:i*rlen+rlen],parent)


recfuncs = {
	0x05:pages,
	0x0b:paras,
	0x13:fonts,
	0x14:styles,
	0x15:colors,
	0x19:shapes,
	0x1a:txtblks,
	0x1c:chars,
	0x28:xforms,
	0x2f:masters,
	0x31:layers,
} 


def hd_header (hd,data,page):
	endian = "Big"
	if eflag == "<":
		endian = "Little"
	add_iter (hd,'Endian:',endian,6,2,">H")
	tr_len = struct.unpack("%sH"%eflag,data[0x2e:0x30])[0]
	add_iter (hd,'ToC length:',"%d"%tr_len,0x2e,2,"%sH"%eflag)
	tr_off = struct.unpack("%sI"%eflag,data[0x30:0x34])[0]
	add_iter (hd,'ToC offset:',"%d"%tr_off,0x30,4,"%sI"%eflag)


def hd_shape_text(hd, data, page):
	txtblk_id = struct.unpack("%sI"%eflag,data[0x20:0x24])[0]
	add_iter (hd,'Txt block ID:',"0x%02x"%txtblk_id,0x20,4,"%sI"%eflag)
	

def hd_shape_rect_oval(hd, data, page):
	# 0x01: &20 lock position
	# 0x02: &2 no xparent BG, &4 - non-printing
	
	# 0x04: word fill clr ID
	fclrid = "0x%s"%d2hex(data[4:6])
	add_iter (hd,'Fill Clr ID:',fclrid,4,2,"%sH"%eflag)

	# 0x06: word for Xs in twips
	# 0x08: word for Ys in twips
	# 0x0a: word for Xe in twips
	# 0x0c: word for Ye in twips
	xs = struct.unpack("%sh"%eflag,data[6:8])[0]
	add_iter (hd,'X start (inches):',xs/1440.,6,2,"%sh"%eflag)
	ys = struct.unpack("%sh"%eflag,data[8:0xa])[0]
	add_iter (hd,'Y start (inches):',ys/1440.,8,2,"%sh"%eflag)
	xe = struct.unpack("%sh"%eflag,data[0xa:0xc])[0]
	add_iter (hd,'X end (inches):',xe/1440.,0xa,2,"%sh"%eflag)
	ye = struct.unpack("%sh"%eflag,data[0xc:0xe])[0]
	add_iter (hd,'Y end (inches):',ye/1440.,0xc,2,"%sh"%eflag)
	
	# 0x0e: frame text wrap option
	# 0x0f: frame text flow option 1/2/8
	# 0x10: word frame standoff left pts*20
	# 0x12: word frame standoff right pts*20
	# 0x14: word frame standoff top pts*20
	# 0x16: word frame standoff bottom pts*20
	# 0x1c: dword xform ID
	
	# 0x20: stroke type
	# 0-single, 1-dbl fine, 2-thick/fine, 3-fine/thick,
	# 4-triple fine, 5-dashes, 6-dots, 7-diamonds, 
	#
	# 0x21: &1 reverse
	# 0x23: stroke width*5
	# 0x26: fill type 2-solid, 3-|, 4-|| etc
	# 0x27: rounded corners (num -- degree)
	# 0x28: word stroke clr ID
	# 0x2a: &1 overprint
	# 0x2c: word? stroke tint %
	# 0x34: frame inset pts*20
	# 0x3b: frame halign: 0-left,1-center,2-right
	# 0x3c: frame valign: 0-top,1-center,2-bottom
	# 0x3d: 1-size frame to fit content,2-scale content to fit frame
	# 0x3e: frame maintain aspect ratio 
	# 0x90: fill tint %
	# 0xda ?
	# 0xdc: group ID


def hd_shape (hd,data,page):
	sh_type = ord(data[0])
	ttxt = key2txt(sh_type,sh_types,"%02x"%sh_type)
	add_iter (hd,'Type:',ttxt,0,1,"%sB"%eflag)
	if sh_type in (4,5):
		hd_shape_rect_oval(hd, data, page)
	elif sh_type == 1:
		hd_shape_text(hd, data, page)


def hd_char (hd, data, page):
	# 0x2: word -- font id starting from 0
	# 0x4: word -- fontsize*10
	# 0x6: word -- lead pts*10
	# 0x8: clr id starting from 0
	# 0xa: &1 - bold, &2 - italic, &4 - underline
	# 0xb: &1 - strikethru, &2 - sup, &4 - sub, &8 - allcaps
	# 0xb: &10 - smallcaps
	# 0xc: word (ffff -- "normal") -- Horscale%*10
	# 0xe: track (127 none, 2 very loose, 1 loose, 0 normal, ff tight, fe very tight)
	# 0xf: &8 -- no break
	# 0x10:
	# 0x12: word SmallCaps%*10
	# 0x14: word sup/sub size%*10
	# 0x16: word sub pos%*10
	# 0x18: word sup pos%*10
	# 0x1a: word baseline shift*20
	# 0x1c: word tint %
	char_len = struct.unpack("%sh"%eflag,data[0:2])[0]
	add_iter (hd,'Length:',"%d"%char_len,0,2,"%sh"%eflag)

	fnt_id = struct.unpack("%sh"%eflag,data[2:4])[0]
	fnt_name = fonts_dir[fnt_id]
	add_iter (hd,'Font:',"%s [0x%02x]"%(fnt_name,fnt_id),2,2,"%sh"%eflag)

	fnt_size = struct.unpack("%sh"%eflag,data[4:6])[0]/10.
	add_iter (hd,'Font size:',"%.1f"%fnt_size,4,2,"%sh"%eflag)


def hd_xform (hd,data,page):
	# 0x8: flip FL
	rot = struct.unpack("%si"%eflag,data[0:4])[0]/1000.
	add_iter (hd,'Rotation (deg):',"%d"%rot,0,4,"%sI"%eflag)
	skew = struct.unpack("%si"%eflag,data[4:8])[0]/1000.
	add_iter (hd,'Skew (deg):',"%d"%skew,4,4,"%sI"%eflag)
	for i in range(6):
		v = struct.unpack("%sh"%eflag,data[10+i*2:12+i*2])[0]
		add_iter (hd,'Var%d (inches):'%i,v/1440.,10+i*2,2,"%sh"%eflag)
	xformnum = struct.unpack("%sI"%eflag,data[22:26])[0]
	add_iter (hd,'Num of transforms:',"%d"%xformnum,22,4,"%sI"%eflag)
	

hd_ids = {
	"header":hd_header,
	"shape":hd_shape,
	"char":hd_char,
	"xform":hd_xform,
}

def parse_trailer(page,data,tr_off,tr_len,parent,eflag,tr,grp=0):
#	offsets = []
	for i in range(tr_len):
		rid1 = ord(data[tr_off+1])
		size = struct.unpack("%sH"%eflag,data[tr_off+2:tr_off+4])[0]
		off = struct.unpack("%sI"%eflag,data[tr_off+4:tr_off+8])[0]
		tr_off += 10
		if grp == 0 and (rid1 > 0 or size == 0):
			flag2 = ord(data[tr_off])
			rid2 = ord(data[tr_off + 1])
			tr_off += 6
			triter = add_pgiter(page,"%02x %04x %08x %02x %02x"%(rid1,size,off,flag2,rid2),"pm","tr_rec",data[tr_off-16:tr_off],parent)
			if rid1 == 1:
				parse_trailer(page,data,off,size,triter,eflag,tr,off)
		else:
			triter = add_pgiter(page,"%02x %04x %08x"%(rid1,size,off),"pm","tr_rec",data[tr_off-10:tr_off],parent)
			if grp == 0:
				parse_trailer(page,data,off,size,triter,eflag,tr)
		tr.append((rid1,size,off,grp))
	return tr

def open (page,buf,parent,off=0):
	global eflag,unkn_records
	add_pgiter(page,"PM Header","pm","header",buf[0:0x36],parent)
	eflag = "<"
	if buf[6:8] == "\x99\xff":
		eflag = ">"
	tr_len = struct.unpack("%sH"%eflag,buf[0x2e:0x30])[0]
	tr_off = struct.unpack("%sI"%eflag,buf[0x30:0x34])[0]
	off += 0x36
	triter = add_pgiter(page,"Trailer","pm","trailer",buf[tr_off:tr_off+tr_len*16],parent)
	tr = []
	# BIPU version detection
#	vd1 = ord(buf[0xa])
#	vd2 = ord(buf[0x10])
#	if vd1 == 1:
#		page.version = 4
#	elif vd1 == 6:
#		page.version = 5
#	elif vd2 == 5:
#		page.version = 6.5
#	else:
#		page.version = 6.5  # 7 seems to be the same

# BIPU version detection v2
	vd = ord(buf[0x2a])
	if vd == 0x2a:
		page.version = 4
	elif vd == 0x2f:
		page.version = 5
	elif vd == 0x32:
		page.version = 6
	elif vd == 0x33:
		page.version = 6.5
	else:
		print "Unknown version byte: %02x"%(vd)
		page.version = 6.5  # 7 seems to be the same, fallback to the latest for now

	print 'Version:',page.version
	
	# FIXME! need to modify treatment of grouped records
	parse_trailer(page,buf,tr_off,tr_len,triter,eflag,tr)
	start = 0x36
	rec_id = 0
	size = 0
	for (rec,size,off,grp) in tr:
		if off != 0 and rec > 1 and size != 0:
			if rec in recs:
				rlen = size*recs[rec][1]
				rname = recs[rec][0]
			else:
				if not rec in unkn_records:
					print "Unknown record: %02x"%rec
					unkn_records.append(rec)
				rlen = size*800
				rname = "%02x"%rec
			citer = add_pgiter(page,"[%02x] %s %02x [%04x]"%(rec_id,rname,size,off),"pm",rname,buf[off:off+rlen],parent)
			if rec in recfuncs:
				recfuncs[rec](page,buf[off:off+rlen],size,citer)
		if grp == 0:
			rec_id += 1
	page.type = "PM"
