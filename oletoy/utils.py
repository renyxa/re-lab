# Copyright (C) 2007-2013	Valek Filippov (frob@df.ru)
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

import sys,struct,base64
import gtk

ms_charsets = {0:"Latin", 1:"System default", 2:"Symbol", 77:"Apple Roman",
	128:"Japanese Shift-JIS",129:"Korean (Hangul)",130:"Korean (Johab)",
	134:"Chinese Simplified GBK",136:"Chinese Traditional BIG5",
	161:"Greek",162:"Turkish",163:"Vietnamese",177:"Hebrew",178:"Arabic",
	186:"Baltic",204:"Cyrillic",222:"Thai",238:"Latin II (Central European)",
	255:"OEM Latin I"}

def add_iter (hd,name,value,offset,length,vtype,offset2=0,length2=0,parent=None,tip=None):
	iter = hd.model.append(parent, None)
	hd.model.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype,5,offset2,6,length2,8,tip)
	return iter

def add_tip (hd,iter,text):
	hd.model.set (iter, 8, text)

def pgiter(page, name, ftype, stype, data, iter1,coltype=None):
	page.model.set_value(iter1,0,name)
	page.model.set_value(iter1,1,(ftype,stype))
	if data != None:
		page.model.set_value(iter1,2,len(data))
		page.model.set_value(iter1,3,data)
	if coltype !=None:
		page.model.set_value(iter1,7,coltype)
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))

def add_pgiter (page, name, ftype, stype, data, parent = None, coltype = None):
	iter1 = page.model.append (parent,None)
	pgiter(page, name, ftype, stype, data, iter1, coltype)
	return iter1

def prep_pgiter (page, name, ftype, stype, data, parent = None, coltype=None):
	iter1 = page.model.prepend (parent,None)
	pgiter(page, name, ftype, stype, data, iter1,coltype)
	return iter1

def ins_pgiter (page, name, ftype, stype, data, parent = None, pos = 0):
	# modify to insert into parent at 'pos'
	iter1 = page.model.insert (parent,pos)
	pgiter(page, name, ftype, stype, data, iter1)
	return iter1

def rdata (data,off,fmt):
	fmtlen = struct.calcsize(fmt)
	return struct.unpack(fmt,data[off:off+fmtlen])[0],off+fmtlen

def hex2d(data):
	res = ''
	data = data.replace(" ","")
	for i in range(len(data)/2):
		num = int(data[i*2:i*2+2],16)
		res += struct.pack("B",num)
	return res

def d2hex(data,space="",ln=0):
	s = ""
	for i in range(len(data)):
		s += "%02x%s"%(ord(data[i]),space)
		if ln != 0 and (i % ln) == 0:
			s += "\n"
			
	return s

def key2txt(key,data,txt="Unknown"):
	if key in data:
		return data[key]
	else:
		return txt

def bflag2txt(flag,data,txt=""):
	if flag != 0:
		for i in (1,2,4,8,0x10,0x20,0x40,0x80):
			if flag&i == i:
				txt += key2txt(i,data,"") + "/"
		if len(txt) > 0:
			txt = txt[:len(txt)-1]
	return txt

def dib2bmp(data,strict=0):
	flag = struct.unpack("<I",data[:4])[0]
	if flag != 0x28:
		print "Doesn't look like DIB, sir..."
		if strict:
			return 0
	size = len(data)+14
	bpp = ord(data[14])
	if bpp == 1:
		bsize = size - 0x3e
	else:
		bsize = struct.unpack("<I",data[0x14:0x18])[0]
	return "BM"+struct.pack("<I",size) + "\x00"*4+struct.pack("<I",size-bsize)+data

def b64decode (page,data,parent):
	decdata = base64.b64decode(data)
	add_pgiter (page, "[Base64decoded]", "base64", "", decdata, parent)

def bup2 (string, offlen):
	t = ""
	t2 = ""
	r = []
	string = string.replace(" ","")
	for i in string:
		t += bin(int(i,16))[2:].zfill(4)
		t2 += bin(int(i,16))[2:].zfill(4) + "."
	for i,j in offlen:
		try:
			r.append(int(t[int(i):int(i)+int(j)],2))
		except:
			pass
	return t2[:-1],r


def disp_expose (da,event,pixbuf,scale=1):
	ctx = da.window.cairo_create()
	ctx.scale(scale,scale)
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()

