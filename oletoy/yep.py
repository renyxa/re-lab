# Copyright (C) 2007,2010-2013	Valek Filippov (frob@df.ru)
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

import sys,struct,math
from utils import *
from midi import *

# returns size of the RIFF-based tree starting from 'parent'
def get_parent_size (page, parent):
	size = 8 # fourcc + chunk size
	for i in range(page.model.iter_n_children(parent)):
		citer = page.model.iter_nth_child(parent, i)
		size += len(page.model.get_value(citer,3)) + 8 # data size plus child fourcc and chunk size dwords
	return size

# collects tree under 'parent' inserting fourcc-s and chunk sizes
def collect_tree (page, parent):
	ctdata = ""
	if page.model.iter_n_children(parent) > 0:
		for i in range(page.model.iter_n_children(parent)):
			citer = page.model.iter_nth_child(parent, i)
			cdata = page.model.get_value(citer,3)
			clen = len(cdata)
			name = page.model.get_value(citer,1)[1]
			if name[:5] == "IPIT/":
				name = name[5:]
				pos = cdata.find("\x00")
				if pos != -1:
					clen = pos
			ctdata += name + struct.pack(">I",clen)+cdata
		return page.model.get_value(parent,1)[1]+struct.pack(">I",len(ctdata))+ctdata
	else:
		ctdata = page.model.get_value(parent,3)
		name = page.model.get_value(parent,1)[1]
		clen = len(ctdata)
		if name == "SSTY":
			pos = ctdata.rfind("\x00\xFF\x2F\x00")
			if pos != -1:
				clen = pos + 4
		return name+struct.pack(">I",clen)+ctdata


# collects tree in VPRM, skips "vdblock" and "prtshdr"
def collect_vprm (page, parent):
	data = ""
	for i in range(page.model.iter_n_children(parent)):
		citer = page.model.iter_nth_child(parent, i)
		itype = page.model.get_value(citer,1)[1]
		if itype != "vdblock" and itype != "prtshdr":
			data += page.model.get_value(citer,3)
		if page.model.iter_n_children(citer) > 0:
			data += collect_vprm (page, citer)
	return data

# saves YEP file
def save (page, fname):
	data = ""
	iter1 = page.model.get_iter_first()
	while None != iter1:
		if page.model.get_value(iter1,1)[1] != "VPRM":
			data += collect_tree (page, iter1)
		else:
			tdata = collect_vprm (page, iter1)
			data += page.model.get_value(iter1,1)[1] + struct.pack(">I",len(tdata))+tdata
		iter1 = page.model.iter_next(iter1)
	f = open(fname,"wb")
	f.write(data)
	f.close()

def p1s0 (hd, data):
	offset = 3
	x = 255-ord(data[offset])
	add_iter(hd,"Voice - Master Volume",x,offset,1,"B")

def p1s1 (hd, data):
	offset = 0
	x = 255-ord(data[offset])
	add_iter(hd,"Element Volume",x,offset,1,"B")

def bank (hd, data):
	offset = 2
	x = ord(data[offset])
	add_iter(hd,"Key Range - High note",key2txt(x,pitches),offset,1,"B")

	offset = 3
	x = ord(data[offset])
	add_iter(hd,"Key Range - Low note",key2txt(x,pitches),offset,1,"B")

	offset = 61
	x = 128-ord(data[offset])
	add_iter(hd,"Envelope - Attack",x,offset,1,"B")

	offset = 62
	x = 127-ord(data[offset])
	add_iter(hd,"Envelope - Decay",x,offset,1,"B")

	offset = 63
	x = 127-ord(data[offset])
	add_iter(hd,"Envelope - Sustain",x,offset,1,"B")

	offset = 65
	x = 127-ord(data[offset])
	add_iter(hd,"Envelope - Release",x,offset,1,"B")

	offset = 69
	x = 255-ord(data[offset])
	add_iter(hd,"Envelope - Decay Level",x,offset,1,"B")

	offset = 70
	x = 255-ord(data[offset])
	add_iter(hd,"Envelope - Sus Level",x,offset,1,"B")

	offset = 91
	x = ord(data[offset])/16
	add_iter(hd,"Velocity Sens - Level",x,offset,1,"B")

	offset = 141
	x = ord(data[offset])
	add_iter(hd,"Filter - Resonance",x,offset,1,"B")

	
def hdra(hd,data):
	off = 0
	var0 = struct.unpack(">I",data[off:off+4])[0]
	add_iter(hd,"Offset A",var0,off,4,">I")
	off += 4
	size = struct.unpack(">I",data[off:off+4])[0]
	add_iter(hd,"Offset B",size,off,4,">I")
	off += 4
	ind = 0
	while off < size:
		item_s = struct.unpack(">h",data[off:off+2])[0]
		item_e = struct.unpack(">h",data[off+2:off+4])[0]
		add_iter(hd,"Sample group %02x"%ind,"%02x %02x"%(item_s,item_e),off,2,">h")
		off += 4
		ind += 1

def hdrbch (hd, data):
	offset = 12
	x = 255-ord(data[offset])
	add_iter(hd,"Volume",x,offset,1,"B")
	
	offset = 13
	x = ord(data[offset])-64
	add_iter(hd,"Panorama",x,offset,1,"B")

	offset = 16
	x = ord(data[offset])
	add_iter(hd,"Tuning Center Key-Note",key2txt(x,pitches),offset,1,"B")

	offset = 17
	x = ord(data[offset])        
	if x >=32:
                x = ord(data[offset])-128
	add_iter(hd,"Tuning Coarse",x,offset,1,"B")

	offset = 18
	x = ord(data[offset])        
	if x >=64:
                x = ord(data[offset])-256
	add_iter(hd,"Tuning Fine",x,offset,1,"B")
	
	
vprmfunc = {"p1s0":p1s0, "p1s1":p1s1, "bank":bank, "hdra":hdra, "hdrbch":hdrbch}

def hdr1item (page,data,parent,offset=0):
	off = 0
	# size of the "main header for level2 block
	# i.e. 'offset to the "elements header"'
	h1off0 = struct.unpack(">I",data[off:off+4])[0]
	if h1off0 != 0x24:
		print "ATTENTION! YEP: size of VPRM header2 is not 0x24, it's %02x"%h1off0
	off += 4
	vdtxt = "Drumkit"
	if ord(data[0x21]) == 0x3f:
		vdtxt = "Voice"
	vdidx = ord(data[0x23])
	h1citer = add_pgiter(page,"%s Block %d"%(vdtxt,vdidx),"vprm","vdblock",data,parent,"%02x  "%offset)
	add_pgiter(page,"V/Dk Header","vprm","vbhdr",data[:h1off0],h1citer,"%02x  "%offset)
	# offset to the list of offsets of elements
	h1off1 = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	# this offset is used in Drumkits only
	h1off2 = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	# seems to be 0s allways in files we have
	h1off3 = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	# offset to the graph
	h1off4 = struct.unpack(">I",data[off:off+4])[0]
	off += 4

	# parse 'elements header'
	p1iter = add_pgiter(page,"Elements Header","vprm","prtshdr",data[h1off0:h1off1],h1citer,"%02x  "%(offset+h1off0))
	# first dozen in 'Elements header'
	add_pgiter(page,"Common settings","vprm","p1s0",data[h1off0:h1off0+12],p1iter,"%02x  "%(offset+h1off0))
	off = h1off0+12
	# number of elements for voice/drumkit
	p1num = struct.unpack(">I",data[off:off+4])[0]
	add_pgiter(page,"Num of sequences","vprm","p1num",data[off:off+4],p1iter,"%02x  "%(offset+off))
	off += 4
	# FIXME! Guessing that number of dozens would match with number of elements
	elements = {}
	for i in range(p1num):
		add_pgiter(page,"PH seq%d"%(i+1),"vprm","p1s%d"%(i+1),data[off:off+12],p1iter,"%02x  "%(offset+off))
		pid = ord(data[off+12])
		elements[pid] = 1
		off += 12
		if off > h1off1:
			print "ATTENTION! YEP: not enough bytes for 'dozens'..."
	
	# parse list of offsets to elements
	poffs = []
	# FIXME!  No validation that we do not cross the 1st offset to elements
	# FIXME! assumption that number of offsets would match number of unique IDs in "dozens"
	for i in range(len(elements)):
		poffs.append(struct.unpack(">I",data[h1off1+i*4:h1off1+i*4+4])[0])
	p2iter = add_pgiter(page,"Elements offsets","vprm","poffs",data[h1off1:h1off1+p1num*4],h1citer,"%02x  "%(offset+h1off1))

	# parse elements
	ind = 0
	try:
		for i in poffs:
			off = i
			# number of Key Banks
			elnum = ord(data[off+4])
			piter = add_pgiter(page,"Element %d"%ind,"vprm","elemhdr",data[off:off+176],h1citer,"%02x  "%(offset+off))
			off += 176
			ind += 1
			# collect Key Banks
			# FIXME! we do not check for data bonds in the loop here
			for j in range(elnum):
				add_pgiter(page,"Key Bank %d"%j,"vprm","bank",data[off:off+180],piter,"%02x  "%(offset+off))
				off += 180
	except:
		print "Failed in parsing elements","%02x"%i,sys.exc_info()

	# add drumkit's "h1off2" block
	# FIXME!  Bold assumption that "h1off3 is 'reserved'
	if vdtxt == "Drumkit":
		diter = add_pgiter(page,"Drumkit block","vprm","dkblock",data[h1off2:h1off4],h1citer,"%02x  "%(offset+h1off2))

	# add graph
	diter = add_pgiter(page,"Graph","vprm","graph",data[h1off4:],h1citer,"%02x  "%(offset+h1off4))
	
def vprm (page, data, parent, offset=0):
	sig = data[:16]
	add_pgiter(page,"Signature","vprm","sign",data[:16],parent,"%02x  "%offset)
	off = 16
	ptr = struct.unpack(">I",data[off:off+4])[0]
	add_pgiter(page,"Offset to samples","vprm","offsmpl",data[off:off+4],parent,"%02x  "%(offset+off))
	off += 4

	hdr1end = struct.unpack(">I",data[off:off+4])[0]
	h1iter = add_pgiter(page,"Voices","vprm","voices",data[20:hdr1end],parent,"%02x  "%(offset+off))
	off += 4
	hdr1 = []
	while off < hdr1end:
		v = struct.unpack(">I",data[off:off+4])[0]
		if v != 0:
			hdr1.append(v)
		off += 4
	for i in hdr1:
		hdr1item (page,data[off:i],h1iter,(offset+off))
		off = i
	hdr1item (page,data[off:ptr],h1iter,(offset+off))

	off = ptr
	off2 = ptr
	v1 = struct.unpack(">I",data[off:off+4])[0] # ??? "allways" 8
	hdraend = struct.unpack(">I",data[off2+4:off2+8])[0]
	smplsiter = add_pgiter(page,"Samples","vprm","samples","",parent,"%02x  "%(offset+off))
	haiter = add_pgiter(page,"List of Sample groups","vprm","hdra",data[off:off+hdraend],smplsiter,"%02x  "%(offset+off))
	slist = []
	shdrsize = struct.unpack(">I",data[off:off+4])[0]
	shdrlen = struct.unpack(">I",data[off+4:off+8])[0]
	tmpoff = off + shdrsize
	while tmpoff < off+shdrlen:
		ss = struct.unpack(">H",data[tmpoff:tmpoff+2])[0]
		se = struct.unpack(">H",data[tmpoff+2:tmpoff+4])[0]
		slist.append((ss,se))
		tmpoff += 4
	off2 += hdraend
	hdrbend = off+struct.unpack(">I",data[off2:off2+4])[0]
	hbiter = add_pgiter(page,"Samples Offsets","vprm","samples",data[off+hdraend:hdrbend],smplsiter,"%02x  "%(offset+off+hdraend))
	hdrb = []
	off2 += 4
	while off2 < hdrbend:
		v = struct.unpack(">I",data[off2:off2+4])[0]
		if v != 0:
			hdrb.append(v+off)
		off2 += 4
	hdrb.append(len(data))
	ind = 0
	for i in slist:
		siter = add_pgiter(page,"Sample %d"%ind,"vprm","sample","",smplsiter,"%02x  "%(offset+off2))
		for j in range(i[0],i[1]+1):
				bend = hdrb[j]
				v3 = ord(data[off2+9])
				v4 = ord(data[off2+8])
				add_pgiter(page,"Block %04x %02x-%02x [%s - %s]"%(j,v3,v4,pitches[v3],pitches[v4]),"vprm","hdrbch",data[off2:bend],siter,"%02x  "%(offset+off2))
				off2 = bend
		ind += 1

def parse (page, data, parent,align=4.,prefix=""):
	off = 0
	vvstgrpiter = None
	sstygrpiter = None
	while off < len(data):
		piter = parent
		fourcc = data[off:off+4]
		off += 4
		l = struct.unpack(">I",data[off:off+4])[0]
		if align:
			length = int(math.ceil(l/align)*align)
		else:
			length = l
		off += 4
		if fourcc == "SSTY":
			iname = fourcc+" %s"%(data[off:off+16])
			if sstygrpiter == None:
				sstygrpiter = add_pgiter(page,"SSTYs","vprm","dontsave","",parent,"%02x  "%(off+off))
			piter = sstygrpiter
		elif fourcc == "VVST":
			n = struct.unpack(">H",data[off+0x19:off+0x1b])[0]
			if ord(data[off+0x18]) == 0x3f:
				f = "[Voice %s]"%n
			else:
				f = "[DrumKit %s]"%n
			iname = fourcc+f+" %s"%(data[off:off+16])
			if vvstgrpiter == None:
				vvstgrpiter = add_pgiter(page,"VVSTs","vprm","dontsave","",parent,"%02x  "%(off+off))
			piter = vvstgrpiter
		else:
			iname = "%s"%fourcc
		
		citer = add_pgiter(page,iname,"yep","%s%s"%(prefix,fourcc),data[off:off+length],piter)
		if fourcc == "VPRM":
			vprm (page, data[off:off+length], citer)
		if fourcc == "IPIT":
			parse (page, data[off:off+length], citer, 4., "IPIT/")
			
		off += length
	page.view.get_column(1).set_title("Offset")
	return "YEP"
