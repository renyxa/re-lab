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

import sys,struct
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from utils import *

def p_patt(page,buf,offset,name,parent):
# didn't rev.engineered yet
	return offset

def p_desc(page,buf,offset,name,parent):
	# convert 4 bytes as big-endian unsigned long
	[size] = struct.unpack('>L',buf[offset:offset+4])
	return offset+26

def p_long(page,buf,offset,name,parent):
	[size] = struct.unpack('>L',buf[offset:offset+4])
	add_pgiter(page,"%s (long) %d [0x%x]"%(name,size,offset-4),"abr","objc",buf[offset-4:offset+4],parent)
	return offset+4

def p_vlls(page,buf,offset,name,parent):
	[size] = struct.unpack('>L',buf[offset:offset+4])
	offset+=4
	o_iter = add_pgiter(page,"%s (VlLs) %d [0x%x]"%(name,size,offset-8),"abr","objc",buf[offset-8:offset],parent)
	for i in range(size):
		type = buf[offset:offset+4]
		offset+=4
		if type in types:
			offset = types[type](page,buf,offset,type,o_iter)
		else:
			p_unkn(buf,offset,"",o_iter)
	return offset

def p_objc(page,buf,offset,name,parent):
	off = offset
	[objnamelen] = struct.unpack('>L',buf[offset:offset+4])
	offset+=4
	objname = buf[offset:offset+objnamelen*2]
	if len(objname):
		objname = " "
	offset+= objnamelen*2
	[objtypelen] = struct.unpack('>L',buf[offset:offset+4])
	if objtypelen == 0:
		objtypelen = 4
	offset+=4
	typename = buf[offset:offset+objtypelen]
	offset+=objtypelen
	[value] = struct.unpack('>L',buf[offset:offset+4])
	offset+=4
	txt = "%s (Objc) %s %s %.2f [0x%x]"%(name,objname,typename,value,off-4)

	o_iter = add_pgiter(page,txt,"abr","objc",buf[off-4:offset],parent)

	for i in range(value):
		offset = parse_entry(page,buf,offset,o_iter)
	return offset

def p_text(page,buf,offset,name,parent):
	[size] = struct.unpack('>L',buf[offset:offset+4])
	string = ""
	for i in range(size-1):
		string = string + str(buf[offset+4+i*2+1:offset+4+i*2+2])
	add_pgiter(page,"%s (TEXT %d) %s [0x%x]"%(name,size,string,offset-4),"abr","text",buf[offset-4:offset+4+size*2],parent)
	return offset+4+size*2

def p_untf(page,buf,offset,name,parent):
	type = buf[offset:offset+4]
	[value] = struct.unpack('>d', buf[offset+4:offset+4+8])
	add_pgiter(page,"%s (UntF) %.2f [0x%x]"%(name,value,offset-4),"abr","untf",buf[offset-4:offset+12],parent)
	return offset+12

def p_bool(page,buf,offset,name,parent):
	# ord converts 1 byte number
	add_pgiter(page,"%s (bool) %d [0x%x]"%(name,ord(buf[offset:offset+1]),offset-4),"abr","bool",buf[offset-4:offset+1],parent)
	return offset+1

def p_doub(page,buf,offset,name,parent):
	# unpack 8 bytes ieee 754 value to floating point number
	[value] = struct.unpack('>d', buf[offset:offset+8])
	add_pgiter(page,"%s (doub) %.2f [0x%x]"%(name,value,offset-4),"abr","doub",buf[offset-4:offset+8],parent)
	return offset+8

def p_enum(page,buf,offset,name,parent):
	off = offset
	[size1] = struct.unpack('>L', buf[offset:offset+4])
	offset+=4
	if size1 == 0:
		size1 = 4
	name1 = buf[offset:offset+size1]
	offset+=size1
	[size2] = struct.unpack('>L', buf[offset:offset+4])
	if size2 == 0:
		size2 = 4
	offset+=4
	name2 = buf[offset:offset+size2]
	offset+=size2
	add_pgiter(page,"%s (enum) %s %s [0x%x]"%(name,name1,name2,off-4),"abr","enum",buf[off-4:off+8+size1+size2],parent)
	return offset

def p_unkn(page,buf,offset,name,parent):
	# assume 4 bytes value
	# in such case offset+4:offset+8 is next length
	# and offset+8:offset+12 is next enum
	# check for it
	name = buf[offset+8:offset+12]
	if name in types:
		# everything is fine
		[size] = struct.unpack('>L',buf[offset:offset+4])
		return size,offset+4
	else:
#		print "Failed with simple case\n"
		str_hex=""
		str_asc=""
		ml = 15
		for i in range(ml):
			try:
				str_hex+="%02x " % ord(buf[offset+i])
				if ord(buf[offset+i]) < 32 or 126<ord(buf[offset+i]):
					str_asc +='.'
				else:
					str_asc += buf[offset+i]
				print(str_hex, str_asc)
			except:
				print("Something failed")
		return str_hex+" "+str_asc,len(buf)+1


types = {"patt":p_patt,"desc":p_desc,"VlLs":p_vlls,"TEXT":p_text,"Objc":p_objc,\
					"UntF":p_untf,"bool":p_bool, "long":p_long, "doub":p_doub, "enum":p_enum}

def parse_entry(page,buf,offset,parent):
	[nlen] = struct.unpack('>L',buf[offset:offset+4])
	if nlen == 0:
		nlen = 4
	offset = offset + 4
	name = buf[offset:offset+nlen]
	offset = offset + nlen
	type = buf[offset:offset+4]
	offset+=4
	if type in types:
		offset = types[type](page,buf,offset,name,parent)
	else:
		print("Unknown key:\t",name,type)
		p_unkn(page,buf,offset,name,parent)
	return offset

bim_types = {"desc":p_desc
	}

def unpack_samp (data,page,siter):
	top = struct.unpack(">I",data[0x131:0x135])[0]
	left = struct.unpack(">I",data[0x135:0x139])[0]
	bottom = struct.unpack(">I",data[0x139:0x13d])[0]
	right = struct.unpack(">I",data[0x13d:0x141])[0]
	depth = struct.unpack(">H",data[0x141:0x143])[0]
	cmpr = ord(data[143])
	off = 0x144+(bottom-top)*2
	buf = ""
	if cmpr:
		for i in range(bottom-top):
			size = struct.unpack(">H",data[0x144+i*2:0x146+i*2])[0]
			j = 0
			while j < size:
				flag = ord(data[off])
				off += 1
				if flag > 128:
					dlen = 257 - flag
					buf +=  data[off]*dlen
					off += 1
					j += 2
				else:
					dlen = flag + 1
					buf += data[off:off+dlen]
					off += dlen
					j += dlen + 1
	else:
		buf = data[0x144:]
	add_pgiter(page,"Uncmpr","abr","uncsamp",buf,siter)

def read_8bim(buf,page,parent,off):
	tag = buf[off:off+4]
	if tag != "8BIM":
		print("Something wrong with 8BIM offsets")
		return len(buf)
	else:
		off += 4
		btype = buf[off:off+4]
		off += 4
		blen = struct.unpack(">I",buf[off:off+4])[0]
		off += 4
		adj = blen % 4
		if adj != 0:
			blen += 4 - adj
		piter = add_pgiter(page,btype,"abr",btype,buf[off-12:off+blen],parent)
		if btype == "desc":
			buf2 = buf[off-12:off+blen]
			add_pgiter(page,"Hdr","abr","hdr",buf2[0:0x22],piter)
			off2 = 0x22
			while off2 < len(buf2): 
				off2  = parse_entry(page,buf2,off2,piter)
		elif btype == "samp":
			off2 = off
			while off2 < blen:
				slen = struct.unpack(">I",buf[off2:off2+4])[0]
				adj = slen % 4
				if adj != 0:
					slen += 4 - adj
				siter = add_pgiter(page,"Sample [%s]"%buf[off2+4:off2+4+37],"abr","samp",buf[off2:off2+slen+4],piter)
#				try:
				unpack_samp (buf[off2:off2+slen+4],page,siter)
#				except:
#					print 'unpack failed'
				off2 += slen+4
				
		off += blen
		return off



def abr_open (buf,page,parent,ftype):
	f_iter = add_pgiter(page,"File","","",buf,parent)
	off = 0
	if ftype == "bgr":
		add_pgiter(page,"Hdr",ftype,"hdr",buf[0:28],f_iter)
		off = 28
		while off < len(buf): 
			off  = parse_entry(page,buf,off,f_iter)
	else:
		vmaj = struct.unpack(">H",buf[0:2])[0]
		vmin = struct.unpack(">H",buf[2:4])[0]
		add_pgiter(page,"Version %d.%d [0x%x]"%(vmaj,vmin,off),ftype,"vrsn",buf[0:4],f_iter)
		off += 4
		while off < len(buf):
			off = read_8bim(buf,page,f_iter,off)
		
		

