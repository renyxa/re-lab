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
	0x0d:("TextBlock", 1),
	0x0e:("TIFF ?", 1),
	0x0f:("WMF ?", 1),
	0x10:("0x10", 332),
	0x11:("0x11", 4),
	0x13:("Fonts", 94),
	0x14:("Styles", 334),
	0x15:("Colors", 210),
	0x18:("0x18", 2496),  # FIXME!
	0x19:("Shapes", 258),  # 136 in ver6?
	0x1b:("TxtProps [1B]", 0x40), # most likely 0x18
	0x1c:("Chars", 30),
	0x1f:("0x1f", 62),
	0x24:("ImgProps [24]", 1),
	0x25:("0x25", 562),
	0x28:("XForms", 26),
	0x29:("0x29", 1),  # two dwords of str lengths, than two strings
	0x2a:("0x2a", 192), # FIXME!
	0x2e:("0x2e", 1),
	0x2f:("Templates", 508),
	0x31:("Layers", 46),
}


def chars (page, data, size, parent):
	rlen = 30
	for i in range(size):
		tlen = struct.unpack("<H",data[i*rlen:i*rlen+2])[0]
		add_pgiter(page,"%d"%tlen,"pm","char",data[i*rlen:i*rlen+rlen],parent)
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


def fonts (page, data, size, parent):
	for i in range(size):
		pos = data[i*94:].find("\x00")
		cname = data[i*94:i*94+pos]
		add_pgiter(page,"%s"%cname,"pm","font",data[i*94:i*94+94],parent)


def colors (page, data, size, parent):
	for i in range(size):
		pos = data[i*210:].find("\x00")
		cname = data[i*210:i*210+pos]
		add_pgiter(page,"%s"%cname,"pm","color",data[i*210:i*210+210],parent)


def pages (page, data, size, parent):
	rlen = 472
	for i in range(size):
		id1 = struct.unpack("<H",data[i*rlen:i*rlen+2])[0]
		id2 = struct.unpack("<H",data[i*rlen+2:i*rlen+4])[0]
		id3 = struct.unpack("<H",data[i*rlen+4:i*rlen+6])[0]
		lr = ord(data[i*rlen+0x1bc])
		side = "(R)"
		if lr == 1:
			side = "(L)"
		add_pgiter(page,"%02x%02x%02x %s"%(id1,id2,id3,side),"pm","page",data[i*rlen:i*rlen+rlen],parent)


sh_types = {
	0x1:"Text",
	0x2:"Image",
	0x3:"Line",
	0x4:"Rect",
	0x5:"Ellipse",
	0xc:"Polygon",
	0xe:"Group",
}


def shape_rect():
	pass
	# 0x01: &20 lock position
	# 0x02: &2 no xparent BG, &4 - non-printing
	# 0x04: word fill clr ID
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


def shapes (page, data, size, parent):
	rlen = 258
#	if len(data)/size < 258:
#		rlen = 136  # is that version specific?
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
	for i in range(size):
		styleid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		pos = data[i*rlen+276:].find("\x00")
		cname = data[i*rlen+276:i*rlen+276+pos]
		add_pgiter(page,"%02x %s"%(styleid,cname),"pm","style",data[i*rlen:i*rlen+rlen],parent)


def xforms (page, data, size, parent):
	# 0x0: dword? rotation degree*1000
	# 0x4: dword? skew degree*1000
	# 0x8: flip FL
	rlen = 26
	for i in range(size):
		xformid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		add_pgiter(page,"%02x"%(xformid),"pm","xform",data[i*rlen:i*rlen+rlen],parent)


def layers (page, data, size, parent):
	rlen = 46
	for i in range(size):
		layerid = struct.unpack("<I",data[i*rlen+rlen-4:i*rlen+rlen])[0]
		pos = data[i*rlen:].find("\x00")
		cname = data[i*rlen:i*rlen+pos]
		add_pgiter(page,"%02x %s"%(layerid,cname),"pm","layer",data[i*rlen:i*rlen+rlen],parent)



recfuncs = {
	0x05:pages,
	0x0b:paras,
	0x13:fonts,
	0x14:styles,
	0x15:colors,
	0x19:shapes,
	0x1c:chars,
	0x28:xforms,
	0x31:layers,
} 



def parse_trailer(page,data,tr_off,tr_len,parent,eflag,tr,grp=0):
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
				parse_trailer(page,data,off,size,triter,eflag,tr,1)
		else:
			triter = add_pgiter(page,"%02x %04x %08x"%(rid1,size,off),"pm","tr_rec",data[tr_off-10:tr_off],parent)
			if grp == 0:
				parse_trailer(page,data,off,size,triter,eflag,tr)
		tr.append((rid1,size,off))
	return tr

def open (page,buf,parent,off=0):
	add_pgiter(page,"PM Header","pm","header",buf[0:0x36],parent)
	eflag = "<"
	if buf[6:8] == "\x99\xff":
		eflag = ">"
	tr_len = struct.unpack("%sH"%eflag,buf[0x2e:0x30])[0]
	tr_off = struct.unpack("%sI"%eflag,buf[0x30:0x34])[0]
	off += 0x36
	triter = add_pgiter(page,"Trailer","pm","trailer",buf[tr_off:tr_off+tr_len*16],parent)
	tr = []
	# FIXME! need to modify treatment of grouped records
	parse_trailer(page,buf,tr_off,tr_len,triter,eflag,tr)
	start = 0x36
	rec_id = 0
	size = 0
	for (rec,size,off) in tr:
		if off != 0 and rec != 0 and size != 0:
			if rec in recs:
				rlen = size*recs[rec][1]
				rname = recs[rec][0]
			else:
				print "Unknown record: %02x"%rec
				rlen = size*800
				rname = "%02x"%rec
			citer = add_pgiter(page,"[%02x] %s %02x [%04x]"%(rec_id,rname,size,off),"pm",rname,buf[off:off+rlen],parent)
			if rec in recfuncs:
				recfuncs[rec](page,buf[off:off+rlen],size,citer)
		rec_id += 1
