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

import sys,struct,gtk,gobject
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
		if types.has_key(type):
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
	if types.has_key(name):
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
				print str_hex, str_asc
			except:
				print "Something failed"
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
	if types.has_key(type):
		offset = types[type](page,buf,offset,name,parent)
	else:
		print "Unknown key:\t",name,type
		p_unkn(page,buf,offset,name,parent)
	return offset
	

def abr_open (buf,page,parent):
	f_iter = add_pgiter(page,"File","abr","",buf,parent)
	add_pgiter(page,"Hdr","abr","hdr",buf[0:28],f_iter)
	off = 28
	while off < len(buf): 
		off  = parse_entry(page,buf,off,f_iter)
