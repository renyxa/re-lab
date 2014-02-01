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


import sys,struct,subprocess
import gtk
import tree
import hexdump
import pub, pubblock, escher, quill
import vsd, xls, ppt, vba, doc, qpw, ppp, vsd2, pm6
import wt602
import zmf
from utils import *

ropen = ""

def cdir_to_treeiter(page,parent,cdir,dircache):
	dirspl = cdir.split("/")
	pn = parent
	pnn = ""
	for i in dirspl:
		jn = pnn+"/"+i
		if not jn in dircache.keys():
			pn = add_pgiter(page,i,"ole",jn,"",pn)
			dircache[jn] = pn
		pnn = jn


def my_open (buf,page,parent=None):
	dircache = {}
	vbaiter = None
	docdata = ""
	docdataiter = None
	tbliter = None
	dirflag=0
	try:
		gsfout = subprocess.check_output(["gsf", "list", page.fname])
		print gsfout
		print "-----------------"
		for i in gsfout.split("\n")[1:-1]:
			if i[0] == "f":
				fullname = i.split()[2]
				if "/" in fullname:
					fns = fullname.split("/")
					cdir = "/".join(fns[:-1])
					fn = fns[-1]
				else:
					fn = fullname
					cdir = ""
				if ord(fn[0]) < 32: 
					fn = fn[1:]
				pn = None
				if cdir:
					cdir_to_treeiter(page,parent,cdir,dircache)
					pn = dircache["/"+cdir]
				data = subprocess.check_output(["gsf", "cat", page.fname,fullname])

				iter1 = add_pgiter(page,fn,"ole",fn,data,pn)


				if (fn == "EscherStm" or fn == "EscherDelayStm"): # and infchild.size()>0:
					ftype = "escher"
					page.model.set_value(iter1,1,("escher",dirflag))
					escher.parse (page.model,data,iter1,"pub") # currently I don't parse it automagically for MSDOC
				if fn == "CONTENTS":
					if data[6:11] == "WT602":
						ftype = "wt602"
						page.model.set_value(iter1,1,("wt602",dirflag))
						wt602.parse (page,data,iter1)
					else:
						ftype = "quill"
						page.model.set_value(iter1,1,("quill",dirflag))
						quill.parse (page,data,iter1)
				if fn == "Contents":
					if data[:2] == "\xe8\xac": # take signature into account
						ftype = "pub"
						page.model.set_value(iter1,1,("pub",dirflag))
						pub.parse (page,data,iter1)
				if fn == "VisioDocument":
					ftype = "vsd"
					page.model.set_value(iter1,1,("vsd",dirflag)) # level = 1?
					vsd.parse (page, data, iter1)
				if fn == "PageMaker":
					ftype = "pm"
					page.model.set_value(iter1,1,("pm",dirflag))
					pm6.open (page, data, iter1)
				if fn == "WordDocument":
					ftype = "doc"
					page.model.set_value(iter1,1,("doc",dirflag)) #level = 1
					doc.parse (page, data, iter1)
				if fn == "1Table" or fn == "0Table":
					doc.parse_table (page, data, iter1,docdata,docdataiter)
				if fn == "Data" and page.type == "DOC":
					docdataiter = iter1
					docdata = data
				if fn == "Book" or fn == "Workbook":
					page.model.set_value(iter1,1,("xls",dirflag))
					ftype = xls.parse (page, data, iter1)
				if fn == "PowerPoint Document" or fn == "Pictures":
					ftype = "ppt"
					page.model.set_value(iter1,1,("ppt",dirflag))
					ppt.parse (page, data, iter1)
				if fn == "NativeContent_MAIN":
					ftype = "qpw"
					page.model.set_value(iter1,1,("qpw",dirflag))
					qpw.parse (page, data, iter1)
				if fn == "Signature" and data[:4] == '\x60\x67\x01\x00':
					ftype = "ppp"  #PagePlus OLE version (9.x?)
				if (fn == "contents" or fn == "SCFFPreview") and ftype == "ppp":
					ppp.parse(page,data,iter1,fn)
		
				# I've no idea if this is really the signature, but it is
				# present in all files I've seen so far
				if fn == "Header" and data[0xc:0xf] == 'xV4':
					ftype = 'zmf'
					zmf.zmf2_open(page, data, iter1, fn)
				if fn[-4:] == '.zmf':
					ftype = 'zmf'
					zmf.zmf2_open(page, data, iter1, fn)
		
				if fn == "VBA":
					page.type = "vba"
					ftype = "vba"
				if ftype == "vba" and fn == "dir":
					page.model.set_value(iter1,1,("vba",dirflag))
					vbaiter = iter1
					vbadata = data
				if vbaiter != None:
					vba.parse (page, vbadata, vbaiter)

	except subprocess.CalledProcessError:
		print "Failed to run gsf. Please install libgsf."
		return

	ftype = "TEST"
	return ftype

def gsf_open(src,page,iter=None):
	inp = gsf.InputMemory(src,False)
	infile = gsf.InfileMSOle(inp)
	ftype = gsf_get_children(page,infile,iter,"ole")
	return ftype


try:
	import gsf
	ropen = gsf_open
	print "Found libgsf python bindings"
except:
	print 'libgsf python bindings were not found'
	ropen = my_open

objtype_ids = {0:"Unknown",1:"Storage",2:"Stream",5:"Root Storage"}

prop_set_ids = {
	1:"CodePage",
	2:"Title",
	3:"Subject",
	4:"Author",
	5:"Keywords",
	6:"Comments",
	7:"Template",
	8:"Last Author",
	9:"Rev Number",
	10:"Edit Time",
	11:"Last Printed",
	12:"Create DTM",
	13:"Last Save DTM",
	14:"Page Count",
	15:"Word Count",
	16:"Char Count",
	17:"Thumbnail",
	18:"App Name",
	19:"Doc Security"
}

prop_types = {
	0x0000:"EMPTY",
	0x0001:"NULL",
	0x0002:"I2",
	0x0003:"I4",
	0x0004:"R4",
	0x0005:"R8",
	0x0006:"CY",
	0x0007:"DATE",
	0x0008:"BSTR",
	0x000A:"ERROR",
	0x000B:"BOOL",
	0x000E:"DECIMAL",
	0x0010:"I1",
	0x0011:"UI1",
	0x0012:"UI2",
	0x0013:"UI4",
	0x0014:"I8",
	0x0015:"UI8",
	0x0016:"INT",
	0x0017:"UINT",
	0x001E:"LPSTR",
	0x001F:"LPWSTR",
	0x0040:"FILETIME",
	0x0041:"BLOB",
	0x0042:"STREAM",
	0x0043:"STORAGE",
	0x0044:"STREAMED_Object",
	0x0045:"STORED_Object",
	0x0046:"BLOB_Object",
	0x0047:"CF",
	0x0048:"CLSID",
	0x0049:"VERSIONED_STREAM",
	0x1002:"VECTOR_I2",
	0x1003:"VECTOR_I4",
	0x1004:"VECTOR_R4",
	0x1005:"VECTOR_R8",
	0x1006:"VECTOR_CY",
	0x1007:"VECTOR_DATE",
	0x1008:"VECTOR_BSTR",
	0x100A:"VECTOR_ERROR",
	0x100B:"VECTOR_BOOL",
	0x100C:"VECTOR_VARIANT",
	0x1010:"VECTOR_I1",
	0x1011:"VECTOR_UI1",
	0x1012:"VECTOR_UI2",
	0x1013:"VECTOR_UI4",
	0x1014:"VECTOR_I8",
	0x1015:"VECTOR_UI8",
	0x101E:"VECTOR_LPSTR",
	0x101F:"VECTOR_LPWSTR",
	0x1040:"VECTOR_FILETIME",
	0x1047:"VECTOR_CF",
	0x1048:"VECTOR_CLSID",
	0x2002:"ARRAY_I2",
	0x2003:"ARRAY_I4",
	0x2004:"ARRAY_R4",
	0x2005:"ARRAY_R8",
	0x2006:"ARRAY_CY",
	0x2007:"ARRAY_DATE",
	0x2008:"ARRAY_BSTR",
	0x200A:"ARRAY_ERROR",
	0x200B:"ARRAY_BOOL",
	0x200C:"ARRAY_VARIANT",
	0x200E:"ARRAY_DECIMAL",
	0x2010:"ARRAY_I1",
	0x2011:"ARRAY_UI1",
	0x2012:"ARRAY_UI2",
	0x2013:"ARRAY_UI4",
	0x2016:"ARRAY_INT",
	0x2017:"ARRAY_UINT"
}


def gsf_get_children(page,infile,parent,ftype,dirflag=0):
	vbaiter = None
	docdata = ""
	docdataiter = None
	tbliter = None
	for i in range(infile.num_children()):
		infchild = infile.child_by_index(i)

		infname = infile.name_by_index(i)
		chsize = infchild.size()
#		print "Name ", infname, dirflag

		if ord(infname[0]) < 32: 
			infname = infname[1:]


		if infname == "dir":
			infuncomp = infchild.uncompress()
			data = infuncomp.read(infuncomp.size())
		else:
			data = infchild.read(chsize)
			
		iter1 = add_pgiter (page, infname, "ole", dirflag, data)
			
		if (infname == "EscherStm" or infname == "EscherDelayStm") and chsize>0:
			ftype = "escher"
			page.model.set_value(iter1,1,("escher",dirflag))
			escher.parse (page.model,data,iter1,"pub") # currently I don't parse it automagically for MSDOC
		if infname == "CONTENTS":
			if data[6:11] == "WT602":
				ftype = "wt602"
				page.model.set_value(iter1,1,("wt602",dirflag))
				wt602.parse (page,data,iter1)
			else:
				ftype = "quill"
				page.model.set_value(iter1,1,("quill",dirflag))
				quill.parse (page,data,iter1)
		if infname == "Contents":
			if data and data[:2] == "\xe8\xac": # take signature into account
				ftype = "pub"
				page.model.set_value(iter1,1,("pub",dirflag))
				pub.parse (page,data,iter1)
		if infname == "VisioDocument":
			ftype = "vsd"
			page.model.set_value(iter1,1,("vsd",dirflag)) # level = 1?
		# choose vsd or vsd2
			vsd.parse (page, data, iter1)
		if infname == "PageMaker":
			ftype = "pm"
			page.model.set_value(iter1,1,("pm",dirflag))
			pm6.open (page, data, iter1)
		if infname == "WordDocument":
			ftype = "doc"
			page.model.set_value(iter1,1,("doc",dirflag)) #level = 1
			doc.parse (page, data, iter1)
		if infname == "1Table" or infname == "0Table":
			page.wtable = iter1
		if infname == "Data":
			page.wdata = iter1

		if infname == "Book" or infname == "Workbook":
			page.model.set_value(iter1,1,("xls",dirflag))
			ftype = xls.parse (page, data, iter1)
		if infname == "PowerPoint Document" or infname == "Pictures" and data != None:
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

		# I've no idea if this is really the signature, but it is
		# present in all files I've seen so far
		if infname == "Header" and data[0xc:0xf] == 'xV4':
			ftype = 'zmf'
			zmf.zmf2_open(page, data, iter1, infname)
		if infname[-4:] == '.zmf':
			ftype = 'zmf'
			zmf.zmf2_open(page, data, iter1, infname)

		if infname == "VBA":
			page.type = ftype
			ftype = "vba"
		if ftype == "vba" and infname == "dir":
			page.model.set_value(iter1,1,("vba",dirflag))
			vbaiter = iter1
			vbadata = data
		if (infile.num_children()>0):
			page.model.set_value(iter1,1,(ftype,1))
			gsf_get_children(page,infchild,iter1,ftype,0)

	if vbaiter != None:
		vba.parse (page, vbadata, vbaiter)

	return ftype


def ole_open (buf,page,iter=None):
	return ropen(buf,page,iter)


def cfb_hdr (hd,data):
	off = 0
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "HdrSig",2,off,3,8,4,"txt")
	off += 8
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "HdrCLSID",2,off,3,16,4,"txt")
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
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Reserved",2,off,3,6,4,"txt")
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
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Dir Entry Name",1, name, 2,0,3,0x40,4,"txt")
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
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "CLSID",2,off,3,0x10,4,"txt")
	off += 16
	stbits = struct.unpack("<I",data[off:off+4])[0]
	add_iter (hd,"State Bits",stbits,off,4,"<I")
	off += 4
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Cr. Time",2,off,3,8,4,"txt")
	off += 8
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Mod. Time",2,off,3,8,4,"txt")
	off += 8
	startloc = struct.unpack("<I",data[off:off+4])[0]
	add_iter (hd,"Start Sec Location",startloc,off,4,"<I")
	off += 4
	stsize = struct.unpack("<Q",data[off:off+8])[0]
	add_iter (hd,"Stream Size",stsize,off,8,"<Q")
	off += 8


def cfb_mdir (hd,data):
	cfb_fat (hd,data)
	return

def cfb_difat (hd,data):
	return

def cfb_fat (hd,data):
	for i in range(len(data)/4):
		nxt = struct.unpack("<I",data[i*4:i*4+4])[0]
		add_iter (hd,"%02x"%i,"%02x"%nxt,i*4,4,"<I")
	return


cfb_ids = {"hdr":cfb_hdr,"dir":cfb_dir,"mdir":cfb_mdir,"difat":cfb_difat,"fat":cfb_fat}

def dump_tree (model, path, parent, f):
	value = ""
	for i in range(model.iter_n_children(parent)):
		value += model.get_value(model.iter_nth_child(parent,i),3)
	f.write(value)


def save (page,fname):
	model = page.model
	f = open(fname,'wb')
	print "ff",model
	model.foreach (dump_tree, f)
	f.close()


def parse_dir(page,buf,parent):
	off = 0
	mdirstart = -1
	mdirsize = -1
	while off < len(buf):
		namelen = struct.unpack("<H",buf[off+0x40:off+0x42])[0]
		name = unicode(buf[off:off+namelen],"utf-16")
		add_pgiter (page,name,"cfb","dir",buf[off:off+0x80],parent)
		if name == "Root Entry\x00":
			mdirstart = struct.unpack("<I",buf[off+0x74:off+0x78])[0]
			mdirsize = struct.unpack("<Q",buf[off+0x78:off+0x80])[0]
		off += 0x80
	return mdirstart,mdirsize

def take_chain(chains,idx):
	chain = []
	chain.append(idx)
	while 1:
		try:
			off = idx*4
			idx = struct.unpack("<I",chains[off:off+4])[0]
			if idx == 0xfffffffe:
				return chain
			else:
				chain.append(idx)
		except:
			print "Failed in take_chain"
			return chain

# to debug libgsf, implement CFB
def parse (buf,page,iter=None):
	#check for signature again
	if buf[:8] != "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
		print "No OLE signature found"
		return

	oiter = add_pgiter (page,"CFB","cfb",None,buf)
	majver = struct.unpack("<H",buf[0x1a:0x1c])[0]
	dirsec = {}
	minidirsec = {}
	minidata = {}

	if majver == 3:
		hdrsize = 512
	else:
		hdrsize = 4096
	add_pgiter (page,"CF Header","cfb","hdr",buf[0:hdrsize],oiter)
	ndirsec = struct.unpack("<I",buf[0x28:0x2c])[0]
	nfatsec = struct.unpack("<I",buf[0x2c:0x30])[0]
	dirsecloc = struct.unpack("<I",buf[0x30:0x34])[0]
	minisecloc = struct.unpack("<I",buf[0x3c:0x40])[0]
	nminisec = struct.unpack("<I",buf[0x44:0x48])[0]
	ndifatsec = struct.unpack("<I",buf[0x48:0x4c])[0]

	off = 0x4c
	fatlist = {}
	
	# FIXME! no parsing for DIFAT sectors at the moment
	while off < hdrsize:
		difat = struct.unpack("<I",buf[off:off+4])[0]
		fatlist[difat] = "fat"
		off += 4
		if difat == 0xffffffff:
			off = hdrsize

	chains = ""
	for i in fatlist:
		chains += buf[(i+1)*hdrsize:(i+2)*hdrsize]

	chain = take_chain(chains,dirsecloc)
	for i in chain:
		dirsec[i] = "dir"

	minichains = ""
	mdirchain = take_chain(chains,minisecloc)
	for i in mdirchain:
		minidirsec[i] = "mdir"

	i = 0
	while off < len(buf):
		sname = "Sector %02x"%i
		if dirsec.has_key(i):
			sname += " (Dir)"
			diriter = add_pgiter (page,sname,"cfb","",buf[off:off+hdrsize],oiter)
			m1,m2 = parse_dir(page,buf[off:off+hdrsize],diriter)
			if m1 != -1:
				mdirstart = m1
				mdirsize = m2
				mdatachain = take_chain(chains,mdirstart)
				for j in mdatachain:
					minidata[j] = "mdata"
				
		elif minidirsec.has_key(i):
			sname += " (MiniDir)"
			add_pgiter (page,sname,"cfb","mdir",buf[off:off+hdrsize],oiter)
		elif fatlist.has_key(i):
			sname += " (FAT)"
			add_pgiter (page,sname,"cfb","fat",buf[off:off+hdrsize],oiter)
			chains += buf[off:off+hdrsize]
		elif minidata.has_key(i):
			sname += " (MiniData)"
			add_pgiter (page,sname,"cfb","mdata",buf[off:off+hdrsize],oiter)
		else:
			add_pgiter (page,sname,"cfb",4,buf[off:off+hdrsize],oiter)
		i += 1
		off += hdrsize

	return "cfb"
