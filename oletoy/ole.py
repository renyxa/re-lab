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


import sys,struct
import gobject
import gtk
import tree
import hexdump
import pub, pubblock, escher, quill
import vsd, xls, ppt, vba, doc, qpw, ppp
import ctypes
from utils import *

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')

objtype_ids = {0:"Unknown",1:"Storage",2:"Stream",5:"Root Storage"}

def ole_open (buf,page,iter=None):
	cgsf.gsf_init()
	src = cgsf.gsf_input_memory_new (buf,len(buf),False)
	infile = cgsf.gsf_infile_msole_new(src)
	ftype = get_children(page,infile,iter,"ole")
	cgsf.gsf_shutdown()
	return ftype

def get_children(page,infile,parent,ftype,dirflag=0):
	vbaiter = None
	docdata = ""
	docdataiter = None
	tbliter = None
	for i in range(cgsf.gsf_infile_num_children(infile)):
		infchild = cgsf.gsf_infile_child_by_index(infile,i)
		infname = ctypes.string_at(cgsf.gsf_infile_name_by_index(infile,i))
#		print "Name ", infname, dirflag

		if ord(infname[0]) < 32: 
			infname = infname[1:]
		chsize = cgsf.gsf_input_size(infchild)
		data = ""
		res = ""
		pos = -1
		inc = 1024
		while cgsf.gsf_input_tell(infchild) < chsize:
			if pos == cgsf.gsf_input_tell(infchild):
				if inc == 1:
					break
				else:
					inc = inc/2
			else:
				pos = cgsf.gsf_input_tell(infchild)
			res = ctypes.string_at(cgsf.gsf_input_read(infchild,inc,None),inc)
			if pos != cgsf.gsf_input_tell(infchild):
				data += res
			
		iter1 = page.model.append(parent,None)
		page.model.set_value(iter1,0,infname)
		page.model.set_value(iter1,1,("ole",dirflag))
		page.model.set_value(iter1,2,chsize)
		page.model.set_value(iter1,3,data)
		if (infname == "EscherStm" or infname == "EscherDelayStm"): # and infchild.size()>0:
			ftype = "escher"
			page.model.set_value(iter1,1,("escher",dirflag))
			escher.parse (page.model,data,iter1,"pub") # currently I don't parse it automagically for MSDOC
		if infname == "CONTENTS":
			ftype = "quill"
			page.model.set_value(iter1,1,("quill",dirflag))
			quill.parse (page,data,iter1)
		if infname == "Contents":
			if data[:2] == "\xe8\xac": # take signature into account
				ftype = "pub"
				page.model.set_value(iter1,1,("pub",dirflag))
				pub.parse (page,data,iter1)
		if infname == "VisioDocument":
			ftype = "vsd"
			page.model.set_value(iter1,1,("vsd",dirflag)) # level = 1?
			vsd.parse (page, data, iter1)
		if infname == "WordDocument":
			ftype = "doc"
			page.model.set_value(iter1,1,("doc",dirflag)) #level = 1
			doc.parse (page, data, iter1)
		if infname == "1Table" or infname == "0Table":
			doc.parse_table (page, data, iter1,docdata,docdataiter)
		if infname == "Data" and page.type == "DOC":
			docdataiter = iter1
			docdata = data
		if infname == "Book" or infname == "Workbook":
			page.model.set_value(iter1,1,("xls",dirflag))
			ftype = xls.parse (page, data, iter1)
		if infname == "PowerPoint Document" or infname == "Pictures":
			ftype = "ppt"
			page.model.set_value(iter1,1,("ppt",dirflag))
			ppt.parse (page, data, iter1)
		if infname == "NativeContent_MAIN":
			ftype = "qpw"
			page.model.set_value(iter1,1,("qpw",dirflag))
			qpw.parse (page, data, iter1)
		if infname == "Signature" and data[:4] == '\x60\x67\x01\x00':
			ftype = "ppp"  #PagePlus OLE version (9.x?)
		if (infname == "contents" or infname == "SCFFPreview") and ftype == "ppp":
			ppp.parse(page,data,iter1,infname)

		if infname == "VBA":
			page.type = ftype
			ftype = "vba"
		if ftype == "vba" and infname == "dir":
			page.model.set_value(iter1,1,("vba",dirflag))
			vbaiter = iter1
			vbadata = data
		if (cgsf.gsf_infile_num_children(infchild)>0):
			page.model.set_value(iter1,1,(ftype,1))
			get_children(page,infchild,iter1,ftype,0)

	if vbaiter != None:
		vba.parse (page, vbadata, vbaiter)

	return ftype

def cfb_hdr (hd,data):
	off = 0
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "HdrSig",2,off,3,8,4,"txt")
	off += 8
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "HdrCLSID",2,off,3,16,4,"txt")
	off += 16
	add_iter (hd,"MinVer",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter (hd,"MajVer",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter (hd,"ByteOrder",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter (hd,"Sec. Shift",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter (hd,"Mini Sec. Shift",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Reserved",2,off,3,6,4,"txt")
	off += 6
	add_iter (hd,"# Of Dir Sec.",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"# Of FAT Sec.",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"1st Dir Sec. Loc",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"Transaction Sig.",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"Mini Cut-off Size.",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"1st Mini Sec. Loc",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"# Of Mini Sec.",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"1st DIFAT Loc",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter (hd,"# Of DIFAT Sec.",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4

# +436 DIFAT
	

def cfb_dir (hd,data):
	off = 0x40
	namelen = struct.unpack("<H",data[off:off+2])[0]
	name = unicode(data[0:namelen],"utf-16")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Dir Entry Name",1, name, 2,0,3,0x40,4,"txt")
	add_iter (hd,"NameLen",namelen,off,2,"<H")
	off += 2
	objtype = ord(data[off])
	objname = "%02x"%objtype
	if objtype_ids.has_key(objtype):
		objname += " (%s)"%objtype_ids[objtype]
	add_iter (hd,"Obj Type",objname,off,1,"<B")
	off += 1
	clrflag = ord(data[off])
	add_iter (hd,"Color Flag",clrflag,off,1,"<B")
	off += 1
	lsib = struct.unpack("<i",data[off:off+4])[0]
	add_iter (hd,"Left Sibling",lsib,off,4,"<i")
	off += 4
	rsib = struct.unpack("<i",data[off:off+4])[0]
	add_iter (hd,"Right Sibling",rsib,off,4,"<i")
	off += 4
	child = struct.unpack("<i",data[off:off+4])[0]
	add_iter (hd,"Child ID",child,off,4,"<i")
	off += 4
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "CLSID",2,off,3,0x10,4,"txt")
	off += 16
	stbits = struct.unpack("<I",data[off:off+4])[0]
	add_iter (hd,"State Bits",stbits,off,4,"<I")
	off += 4
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Cr. Time",2,off,3,8,4,"txt")
	off += 8
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Mod. Time",2,off,3,8,4,"txt")
	off += 8
	stsize = struct.unpack("<Q",data[off:off+8])[0]
	add_iter (hd,"Stream Size",stbits,off,8,"<Q")
	off += 8


def cfb_mini (hd,data):
	return

def cfb_difat (hd,data):
	return

ole_ids = {0:cfb_hdr,1:cfb_dir,2:cfb_mini,3:cfb_difat}

def dump_tree (model, path, parent, f):
	value = ""
	for i in range(model.iter_n_children(parent)):
		value += model.get_value(model.iter_nth_child(parent,i),3)
	f.write(value)


def save (page,fname):
	model = page.model
	f = open(fname,'w')
	print "ff",model
	model.foreach (dump_tree, f)
	f.close()


# to debug libgsf, implement CFB
def parse (buf,page,iter=None):
	#check for signature again
	if buf[:8] != "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
		print "No OLE signature found"
		return

	oiter = add_pgiter (page,"CFB","ole",None,buf)
	majver = struct.unpack("<H",buf[0x1a:0x1c])[0]
	if majver == 3:
		hdrsize = 512
	else:
		hdrsize = 4096
	add_pgiter (page,"CF Header","ole",0,buf[0:hdrsize],oiter)
	ndirsec = struct.unpack("<I",buf[0x28:0x2c])[0]
	nfatsec = struct.unpack("<I",buf[0x2c:0x30])[0]
	dirsecloc = struct.unpack("<I",buf[0x30:0x34])[0]
	minisecloc = struct.unpack("<I",buf[0x3c:0x40])[0]
	nminisec = struct.unpack("<I",buf[0x44:0x48])[0]
	difatloc = struct.unpack("<I",buf[0x48:0x4c])[0]
	ndifatsec = struct.unpack("<I",buf[0x48:0x4c])[0]

	off = hdrsize
	i = 1
	while off < len(buf):
		sname = "Sector %02x"%i
		if i == dirsecloc:
			sname += " (Dir)"
			add_pgiter (page,sname,"ole",1,buf[off:off+hdrsize],oiter)
		elif i == minisecloc:
			sname += " (Mini)"
			add_pgiter (page,sname,"ole",2,buf[off:off+hdrsize],oiter)
		elif i == difatloc:
			sname += " (Difat)"
			add_pgiter (page,sname,"ole",3,buf[off:off+hdrsize],oiter)
		else:
			add_pgiter (page,sname,"ole",4,buf[off:off+hdrsize],oiter)
		i += 1
		off += hdrsize

	return "cfb"
