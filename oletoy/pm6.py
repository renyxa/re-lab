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

def val2txt(value, unit='%', default='normal', scale=.1):
	return '%.1f%s' % (value * scale, unit) if value != ~0 else default

def twip2txt(value):
	return '%.2f in' % (value / 1440.)

recs = {
	0x01:("0x01", 10),
	0x04:("Print Ops?", 104),
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

unkn_records = []  # for deduplication of warnings on unknown records

def chars (page, data, size, parent):
	rlen = 30
	for i in range(size):
		tlen = struct.unpack("<H",data[i*rlen:i*rlen+2])[0]
		add_pgiter(page,"Length: %d"%tlen,"pm","char",data[i*rlen:i*rlen+rlen],parent)


def fonts (page, data, size, parent):
	rlen = 94
	if page.version < 5:
		rlen = 144
	for i in range(size):
		pos = data[i*rlen:].find("\x00")
		cname = data[i*rlen:i*rlen+pos]
		add_pgiter(page,"%s"%cname,"pm","font",data[i*rlen:i*rlen+rlen],parent)
		page.fonts_dir.append(cname)


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
		add_pgiter(page,"Length : %d"%tlen,"pm","para",data[i*rlen:i*rlen+rlen],parent)
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
	if page.eflag == "<":
		endian = "Little"
	add_iter (hd,'Endian',endian,6,2,">H")
	tr_len = struct.unpack("%sH"%page.eflag,data[0x2e:0x30])[0]
	add_iter (hd,'ToC length',"%d"%tr_len,0x2e,2,"%sH"%page.eflag)
	tr_off = struct.unpack("%sI"%page.eflag,data[0x30:0x34])[0]
	add_iter (hd,'ToC offset',"%d"%tr_off,0x30,4,"%sI"%page.eflag)


def hd_shape_text(hd, data, page):
	off = 6
	(xs, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox X start',twip2txt(xs),off-2,2,"%sh"%page.eflag)
	(ys, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox Y start',twip2txt(ys),off-2,2,"%sh"%page.eflag)
	(xe, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox X end',twip2txt(xe),off-2,2,"%sh"%page.eflag)
	(ye, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox Y end',twip2txt(ye),off-2,2,"%sh"%page.eflag)
	off += 14
	(xform_id, off) = rdata(data, off, "%sI"%page.eflag)
	add_iter (hd,'Xform Id',"0x%02x"%xform_id,off-4,4,"%sI"%page.eflag)
	(txtblk_id, off) = rdata(data, off, "%sI"%page.eflag)
	add_iter (hd,'Txt block ID',"0x%02x"%txtblk_id,off-4,4,"%sI"%page.eflag)
	off += 218
	(shapenum, off) = rdata(data, off, "%sI"%page.eflag)
	add_iter (hd,'Shape Id',"%d"%shapenum,0xfe,4,"%sI"%page.eflag)
	

def hd_shape_rect_oval(hd, data, page,sh_type):
	# 0x01: &20 lock position
	# 0x02: &2 no xparent BG, &4 - non-printing
	off = 2
	(fovr, off) = rdata(data, off, '%sH' % page.eflag)
	add_iter (hd,'Fill Overprint',hex(fovr),off-2,2,"%sH"%page.eflag)
	# 0x04: word fill clr ID
	(fclrid, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Fill Clr ID',"0x%02x"%fclrid,off-2,2,"%sH"%page.eflag)
	# 0x06: word for Xs in twips
	# 0x08: word for Ys in twips
	# 0x0a: word for Xe in twips
	# 0x0c: word for Ye in twips
	(xs, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox X start',twip2txt(xs),off-2,2,"%sh"%page.eflag)
	(ys, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox Y start',twip2txt(ys),off-2,2,"%sh"%page.eflag)
	(xe, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox X end',twip2txt(xe),off-2,2,"%sh"%page.eflag)
	(ye, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Bbox Y end',twip2txt(ye),off-2,2,"%sh"%page.eflag)
	off += 14
	(xform_id, off) = rdata(data, off, "%sI"%page.eflag)
	add_iter (hd,'Xform Id',"0x%02x"%xform_id,off-4,4,"%sI"%page.eflag)
	(stroke_type, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Stroke Type',"0x%02x"%stroke_type,off-2,2,"%sh"%page.eflag)
	off += 1
	(stroke_width, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Stroke Width (pt)',stroke_width/5.0,off-2,2,"%sh"%page.eflag)
	off += 1
	(fill_type, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Fill Type',"0x%02x"%fill_type,off-2,2,"%sh"%page.eflag)
	(stroke_color, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Stroke Color',"0x%02x"%stroke_color,off-2,2,"%sh"%page.eflag)
	(sovr, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter (hd,'Stroke Overprint',hex(sovr),off-2,2,"%sh"%page.eflag)
	(stint, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter (hd,'Stroke Tint',hex(stint),off-2,2,"%sh"%page.eflag)
	if sh_type == 12: # Polygon
		(lineset, off) = rdata(data, off, "%sh"%page.eflag)
		add_iter (hd,'LineSet Seq Number',"0x%02x"%lineset,off-2,2,"%sh"%page.eflag)
		off += 8
		(closed, off) = rdata(data, off, '%sh' % page.eflag)
		add_iter (hd,'Closed Marker',hex(closed),off-2,2,"%sh"%page.eflag)
		off += 167
	else:
		off += 178
	(ftint, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter (hd,'Fill Tint',hex(ftint),off-2,2,"%sh"%page.eflag)
	off += 28
	(shapenum, off) = rdata(data, off, "%sI"%page.eflag)
	add_iter (hd,'Shape Id',"%d"%shapenum,off-4,4,"%sI"%page.eflag)

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
	add_iter (hd,'Type',ttxt,0,1,"%sB"%page.eflag)
	if sh_type in (3,4,5,6,12):
		hd_shape_rect_oval(hd, data, page,sh_type)
	elif sh_type == 1:
		hd_shape_text(hd, data, page)


def hd_char (hd, data, page):
	off = 0
	(char_len, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Length',"%d"%char_len,off - 2,2,"%sh"%page.eflag)
	(fnt_id, off) = rdata(data, off, "%sh"%page.eflag)
	fnt_name = page.fonts_dir[fnt_id]
	add_iter (hd,'Font',"%s [0x%02x]"%(fnt_name,fnt_id),off - 2,2,"%sh"%page.eflag)
	(fnt_size, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Font size',"%.1f"%(fnt_size/10.),off - 2,2,"%sh"%page.eflag)
	(leading, off) = rdata(data, off, "%sh" % page.eflag)
	add_iter (hd, 'Leading', val2txt(leading, 'pt', 'auto'), off - 2, 2, "%sh" % page.eflag)
	(fnt_color, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Font color',"0x%02x"%fnt_color,off - 2,2,"%sh"%page.eflag)
	fmt_flags = {
		0x1: 'bold',
		0x2: 'italic',
		0x4: 'underline',
		0x8: 'outline',
		0x10: 'shadow',
		0x100: 'strike-through',
		0x200: 'superscript',
		0x400: 'subscript',
		0x800: 'all caps',
		0x1000: 'small caps',
		}
	(fmt, off) = rdata(data, 10, '%sh' % page.eflag)
	add_iter (hd, 'Format', bflag2txt(fmt, fmt_flags), off - 2, 2, '%sh' % page.eflag)
	(hscale, off) = rdata(data, off, "%sh" % page.eflag)
	add_iter (hd, 'Horiz. scale', val2txt(hscale), off - 2, 2, "%sh" % page.eflag)
	track_map = {-2: 'very tight', -1: 'tight', 0: 'normal', 1: 'loose', 2: 'very loose', 0x7f: 'none',}
	(track, off) = rdata(data, off, 'B')
	add_iter(hd, 'Track', key2txt(track, track_map), off - 1, 1, 'B')
	(line_end, off) = rdata(data, off, 'b')
	add_iter(hd, 'Line end', key2txt(line_end, {0: 'break', 8: 'no break'}), off - 1, 1, 'b')
	(kerning, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Kerning (em)',"%d"%(kerning/1000.),off - 2,2,"%sh"%page.eflag)
	(scsize, off) = rdata(data, off, "%sh" % page.eflag)
	add_iter (hd, 'Small caps size', val2txt(scsize), off - 2, 2, "%sh" % page.eflag)
	(super_sub_size, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Super/SubScript Size (percent)',"%d"%(super_sub_size/10.),off - 2,2,"%sh"%page.eflag)
	(sub_pos, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'SubScript Position (percent)',"%d"%(sub_pos/10.), off - 2,2,"%sh"%page.eflag)
	(super_pos, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'SuperScript Position (percent)',"%d"%(super_pos/10.), off - 2,2,"%sh"%page.eflag)
	(shift, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Baseline shift', '%.1d pt' % (shift / 20.), off - 2, 2, '%sh' % page.eflag)
	(tint, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Tint', '%d%%' % tint, off - 2, 2, '%sh' % page.eflag)

def add_rule(hd, data, offset, eflag, parent):
	flags_bits = {
		0x1: 'enabled',
		0x2: 'width of text',
		0x4: 'align next para to grid',
	}
	(flags, off) = rdata(data, offset, '%sH' % eflag)
	add_iter(hd, 'Flags', bflag2txt(flags, flags_bits), off - 2, 2, '%sh' % eflag, parent=parent)
	style_map = {
		0: 'single',
		1: 'double',
		2: 'double (upper thicker)',
		3: 'double (lower thicker)',
		4: 'triple',
		5: 'dashed',
		6: 'dotted (square dot)',
		7: 'dotted (round dot)',
	}
	(style, off) = rdata(data, off, 'B')
	add_iter(hd, 'Stroke style', key2txt(style, style_map), off - 1, 1, 'B', parent=parent)
	(transp, off) = rdata(data, off, 'B')
	add_iter(hd, 'Transparent b/g', key2txt(transp, {0: 'yes', 1: 'no'}), off - 1, 1, 'B', parent=parent)
	(width, off) = rdata(data, off, '%sI' % eflag)
	add_iter(hd, 'Stroke width', '%.1f pt' % (width / 1280.), off - 4, 4, '%sI' % eflag, parent=parent)
	(color, off) = rdata(data, off, '%sH' % eflag)
	add_iter(hd, 'Stroke color', hex(color), off - 2, 2, '%sH' % eflag, parent=parent)
	(tint, off) = rdata(data, off, '%sH' % eflag)
	add_iter(hd, 'Tint', '%d%%' % tint, off - 2, 2, '%sH' % eflag, parent=parent)
	(left_indent, off) = rdata(data, off, "%sh"%eflag)
	add_iter (hd,'Left indent',twip2txt(left_indent),off-2,2,"%sh"%eflag, parent=parent)
	(right_indent, off) = rdata(data, off, "%sh"%eflag)
	add_iter (hd,'Right indent',twip2txt(right_indent),off-2,2,"%sh"%eflag, parent=parent)
	(top, off) = rdata(data, off, '%sh' % eflag)
	add_iter(hd, 'Distance above baseline', val2txt(top, ' in', 'auto', 1/1440.), off - 2, 2, '%sH' % eflag, parent=parent)
	return off

def hd_para(hd, data, page):
	off = 0
	(para_len, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Length',"%d"%para_len,off-2,2,"%sh"%page.eflag)
	flags_bits = {
		0x1: 'pair kerning',
		0x8: 'hyphenate',
		0x40: 'include in ToC',
	}
	(flags, off) = rdata(data, off, 'B')
	add_iter(hd, 'Flags', bflag2txt(flags, flags_bits), off - 1, 1, 'B')
	align_map = {0: 'left', 1: 'right', 2: 'center', 3: 'justify', 4: 'force justify',}
	(align, off) = rdata(data, off, 'B')
	add_iter(hd, 'Align', key2txt(align, align_map), off - 1, 1, 'B')
	off += 6
	(left_indent, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Left Indent',twip2txt(left_indent),off-2,2,"%sh"%page.eflag)
	(first_indent, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'First Indent',twip2txt(first_indent),off-2,2,"%sh"%page.eflag)
	(right_indent, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Right Indent',twip2txt(right_indent),off-2,2,"%sh"%page.eflag)
	(before_indent, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Space before',twip2txt(before_indent),off-2,2,"%sh"%page.eflag)
	(after_indent, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Space after',twip2txt(after_indent),off-2,2,"%sh"%page.eflag)
	(kerning, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Pair kerning auto above', '%.1f pt' % (kerning / 10.), off - 2, 2, '%sh' % page.eflag)
	(auto_lead, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Auto leading', '%d%%' % auto_lead, off - 2, 2, '%sh' % page.eflag)
	(wmin, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Min. word spacing', '%d%%' % wmin, off - 2, 2, '%sh' % page.eflag)
	(wmax, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Max. word spacing', '%d%%' % wmax, off - 2, 2, '%sh' % page.eflag)
	(wdes, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Desired word spacing', '%d%%' % wdes, off - 2, 2, '%sh' % page.eflag)
	(lmin, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Min. letter spacing', '%d%%' % lmin, off - 2, 2, '%sh' % page.eflag)
	(lmax, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Max. letter spacing', '%d%%' % lmax, off - 2, 2, '%sh' % page.eflag)
	(ldes, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Desired letter spacing', '%d%%' % ldes, off - 2, 2, '%sh' % page.eflag)
	(zone, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Hyphenation zone', twip2txt(zone), off - 2, 2, '%sh' % page.eflag)
	(hyphens, off) = rdata(data, off, 'B')
	add_iter(hd, '# of consecutive hyphens', 'no limit' if hyphens == 0 else hyphens, off - 1, 1, 'B')
	leading_map = {0: 'proportional', 1: 'baseline', 2: 'top of caps',}
	(leading, off) = rdata(data, off, 'B')
	add_iter(hd, 'Leading', key2txt(leading, leading_map), off - 1, 1, 'B')
	opts_bits = {
		0x1: 'keep together',
		0x400: 'page break before',
	}
	(opts, off) = rdata(data, off, '%sh' % page.eflag)
	add_iter(hd, 'Options', bflag2txt(opts & 0x401, opts_bits), off - 2, 2, '%sh' % page.eflag)
	add_iter(hd, 'Keep with next', (opts >> 1) & 3, off - 2, 2, '%sh' % page.eflag)
	add_iter(hd, 'Widows', (opts >> 4) & 3, off - 2, 2, '%sh' % page.eflag)
	add_iter(hd, 'Orphans', (opts >> 7) & 3, off - 2, 2, '%sh' % page.eflag)
	(grid_size, off) = rdata(data, off, '%sH' % page.eflag)
	add_iter(hd, 'Grid size', '%.1f pt' % (grid_size / 10.), off - 2, 2, '%sh' % page.eflag)
	aboveiter = add_iter(hd, 'Rule above paragraph', '', off, 18, '18s')
	off = add_rule(hd, data, off, page.eflag, aboveiter)
	belowiter = add_iter(hd, 'Rule below paragraph', '', off, 18, '18s')
	off = add_rule(hd, data, off, page.eflag, belowiter)

def hd_xform (hd, data, page):
	# 0x8: flip FL
	off = 0
	(rot, off) = rdata(data, off, "%si"%page.eflag)
	add_iter (hd,'Rotation (deg)',"%d"%(rot/1000.),off-4,4,"%sI"%page.eflag)
	(skew, off) = rdata(data, off, "%si"%page.eflag)
	add_iter (hd,'Skew (deg)',"%d"%(skew/1000.),off-4,4,"%sI"%page.eflag)
	off += 2
	(v, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'X start',twip2txt(v),off-2,2,"%sh"%page.eflag)
	(v, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Y start',twip2txt(v),off-2,2,"%sh"%page.eflag)
	(v, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'X end',twip2txt(v),off-2,2,"%sh"%page.eflag)
	(v, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Y end',twip2txt(v),off-2,2,"%sh"%page.eflag)
	(v, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Rotating Point X',twip2txt(v),off-2,2,"%sh"%page.eflag)
	(v, off) = rdata(data, off, "%sh"%page.eflag)
	add_iter (hd,'Rotating Point Y',twip2txt(v),off-2,2,"%sh"%page.eflag)
	(xformnum, off) = rdata(data, off, "%sI"%page.eflag)
	add_iter (hd,'Xform-Shape ID',"%d"%xformnum,off-4,4,"%sI"%page.eflag)


def hd_color (hd, data, page):
	mods = {0x18:"RGB",0x8:"CMYK",0x10:"HLS"}
	type_id ="Spot"
	mod_id = ord(data[0x22])
	add_iter (hd,'Model',key2txt(mod_id,mods),0x22,1,"%sB"%page.eflag)
	
	tid = ord(data[0x21])
	if tid&1:
		type_id = "Process"
	if tid&0x20:
		type_id = "Tint"
	add_iter (hd,'Type',type_id,0x21,1,"%sB"%page.eflag)
	if ord(data[0x20])&0x80:
		add_iter (hd,'Overprint',"",0x20,1,"%sB"%page.eflag)
		
	if mod_id == 0x18:
		r,g,b = ord(data[0x26]),ord(data[0x27]),ord(data[0x28])
		add_iter (hd,'Color [RGB]',"%d %d %d"%(r,g,b),0x26,3,"clr")
	elif mod_id == 0x8 or mod_id == 0x10:
		c = struct.unpack("%sH"%page.eflag,data[0x26:0x28])[0]/655.
		m = struct.unpack("%sH"%page.eflag,data[0x28:0x2a])[0]/655.
		y = struct.unpack("%sH"%page.eflag,data[0x2a:0x2c])[0]/655.
		k = struct.unpack("%sH"%page.eflag,data[0x2c:0x2e])[0]/655.
		add_iter (hd,'Color [CMYK]',"%d%% %d%% %d%% %d%%"%(c,m,y,k),0x26,8,"clr")
		

hd_ids = {
	"header":hd_header,
	"shape":hd_shape,
	"char":hd_char,
	"para":hd_para,
	"xform":hd_xform,
	"color":hd_color,
}

def parse_trailer(page,data,tr_off,tr_len,parent,eflag,tr,grp=0):
#	offsets = []
	for i in range(tr_len):
		rid1 = ord(data[tr_off+1])
		size = struct.unpack("%sH"%page.eflag,data[tr_off+2:tr_off+4])[0]
		off = struct.unpack("%sI"%page.eflag,data[tr_off+4:tr_off+8])[0]
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
	global unkn_records
	page.fonts_dir = []
	add_pgiter(page,"PM Header","pm","header",buf[0:0x36],parent)
	page.eflag = "<"
	if buf[6:8] == "\x99\xff":
		page.eflag = ">"
	tr_len = struct.unpack("%sH"%page.eflag,buf[0x2e:0x30])[0]
	tr_off = struct.unpack("%sI"%page.eflag,buf[0x30:0x34])[0]
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
		print("Unknown version byte: %02x"%(vd))
		page.version = 6.5  # 7 seems to be the same, fallback to the latest for now

	print('Version:',page.version)
	
	# FIXME! need to modify treatment of grouped records
	parse_trailer(page,buf,tr_off,tr_len,triter,page.eflag,tr)
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
					print("Unknown record: %02x"%rec)
					unkn_records.append(rec)
				rlen = size*800
				rname = "%02x"%rec
			citer = add_pgiter(page,"[%02x] %s %02x [%04x]"%(rec_id,rname,size,off),"pm",rname,buf[off:off+rlen],parent)
			if rec in recfuncs:
				recfuncs[rec](page,buf[off:off+rlen],size,citer)
		if grp == 0:
			rec_id += 1
	page.type = "PM"
