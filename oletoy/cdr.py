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

import sys,struct,gtk,gobject, zlib

def flgs (hd,size,data):
	print 'Check version: ',hd.version

def trfd (hd,size,data):
	start = 32
	if hd.version == 13:
		start = 40
	if hd.version == 5:
		start = 18

	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "x0", 1, "%u"%(struct.unpack('<d', data[start+16:start+24])[0]/10000),2,start+16,3,8,4,"<d")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "y0", 1, "%u"%(struct.unpack('<d', data[start+40:start+48])[0]/10000),2,start+40,3,8,4,"<d")

	for i in (0,1,3,4):                     
		var = struct.unpack('<d', data[start+i*8:start+8+i*8])[0]
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "var%d"%(i+1), 1, "%f"%var,2,start+i*8,3,8,4,"<d")




cdr_ids = {"flgs":flgs,"trfd":trfd}

def cdr_open (buf,page):
	try:
		parse_fourcc (None,buf,page,0)
	except:
		print 'Oops'

def parse_fourcc (parent,buf,page,offset):
	debug = 0
	f_type = buf[offset:offset+4]
	offset +=4
	f_len = struct.unpack('<I', buf[offset:offset+4])[0]
	if f_len & 1:
			f_len += 1
	offset +=4
	f_val = buf[offset:offset+f_len]
	offset += f_len
	if f_type == "vrsn":
		page.version = struct.unpack("<h",f_val)[0]/100

	if f_type == 'RIFF' or f_type == 'LIST':
		if debug:
			f_iter = page.model.append(parent,None)
			page.model.set_value(f_iter,0,f_type)
			page.model.set_value(f_iter,1,("cdr",f_type))
			page.model.set_value(f_iter,2,f_len)
			page.model.set_value(f_iter,3,f_val)
			page.model.set_value(f_iter,6,page.model.get_string_from_iter(f_iter))
			parse_list (f_iter,f_val,page)
		else:
			parse_list (parent,f_val,page)
	else:
		f_iter = page.model.append(parent,None)
		page.model.set_value(f_iter,0,f_type)
		page.model.set_value(f_iter,1,("cdr",f_type))
		page.model.set_value(f_iter,2,f_len)
		page.model.set_value(f_iter,3,f_val)
		page.model.set_value(f_iter,6,page.model.get_string_from_iter(f_iter))
	return offset

def parse_list (parent,data,page):
	lname = data[0:4]
	l_iter = page.model.append(parent,None)
	page.model.set_value(l_iter,0,lname)
	page.model.set_value(l_iter,1,("cdr",lname))
	page.model.set_value(l_iter,2,len(data)-4)
	page.model.set_value(l_iter,3,data[4:])
	page.model.set_value(l_iter,6,page.model.get_string_from_iter(l_iter))
	offset = 0
	if lname == 'cmpr':
		decomp = zlib.decompressobj()
		uncompdata = decomp.decompress(data[0x1c:])
		u_iter = page.model.append(l_iter,None)
		page.model.set_value(u_iter,0,"[Uncompressed data]")
		page.model.set_value(u_iter,1,("cdr","uncomp"))
		page.model.set_value(u_iter,2,len(uncompdata))
		page.model.set_value(u_iter,3,uncompdata)
#		if len(decomp.unconsumed_tail):
#			raise Exception('unconsumed tail in compressed data (%u bytes)' % len(decomp.unconsumed_tail))
		while offset < len(uncompdata) - 8:
			offset = parse_fourcc(l_iter,uncompdata,page,offset)
	elif lname == 'stlt':
		pass
	else:
		while offset < len(data) - 8:
			offset = parse_fourcc(l_iter,data[4:],page,offset)
