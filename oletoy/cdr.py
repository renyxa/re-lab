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

def add_iter (hd,name,value,offset,length,vtype):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype)

fill_types = {0:"Transparency",1:"Solid",2:"Gradient"}
clr_models = {0:"Invalid",1:"Pantone",2:"CMYK",3:"CMYK255",4:"CMY", 5:"RGB",
							6:"HSB",7:"HLS",8:"BW",9:"Gray",10:"YIQ255",11:"LAB",12:'Unknown0xc',
							13:'Unknown0xd',14:'Unknown0xe',15:'Unknown0xf',16:'Unknown0x10',
							17:'CMYK255',18:'Unknown0x12',19:'Unknown0x13',20:'Registration Color'}

bmp_clr_models = ('Invalid', 'RGB', 'CMY', 'CMYK255', 'HSB', 'Gray', 'Mono',
								'HLS', 'PAL8', 'Unknown9', 'RGB', 'LAB')
outl_corn_type =('Normal', 'Rounded', 'Cant')
outl_caps_type =('Normal', 'Rounded', 'Out Square')
fild_pal_type = {0:'Transparent', 1:'Solid', 2:'Gradient',6:'Postscript',7:'Pattern', 0xb:'Texture'} # FIXME! names are guessed by frob
fild_grad_type = ('Unknown', 'Linear', 'Radial', 'Conical', 'Squared') #FIXME! gussed
#loda_type_func = {0xa:loda_outl,0x14:loda_fild,0x1e:loda_coords,0x68:loda_stlt, 0x2af8:loda_polygone,0x3e8:loda_name,
#									0x2efe:loda_rot	#, 0x7d0:loda_palt, 0x1f40:loda_lens, 0x1f45:loda_contnr
#									}


def fild (hd,size,data):
	add_iter (hd,"Fill ID","%02x"%struct.unpack('<I', data[0:4])[0],0,4,"<I")
	fill_type = struct.unpack('<h', data[4:6])[0]
	ft_txt = "%d"%fill_type
	if fill_types.has_key(fill_type):
		ft_txt += " "+fill_types[fill_type]
	add_iter (hd,"Fill Type", ft_txt,4,2,"txt")
	if fill_type > 0:
		clr_model = struct.unpack('<h', data[8:0xa])[0]
		clrm_txt = "%d"%clr_model
		if clr_models.has_key(clr_model):
			clrm_txt += " " + clr_models[clr_model]
		add_iter (hd, "Color Model", clrm_txt,8,2,"txt")
		add_iter (hd, "Color", "%02x"%struct.unpack('<i', data[0x10:0x14])[0],0x10,4,"<i")

def ftil (hd,size,data):
	for i in range(6):
		[var] = struct.unpack('<d', chunk.data[i*8:i*8+8]) 
		add_iter(hd,'Var%d'%i,var,i*8,8,"<d")

loda_types = {0:"Layer",1:"Rectangle",2:"Ellipse",3:"Line/Curve",4:"Text",5:"Bitmap",20:"Polygon"}

def loda (hd,size,data):
	n_args = struct.unpack('<i', data[4:8])[0]
	s_args = struct.unpack('<i', data[8:0xc])[0]
	s_types = struct.unpack('<i', data[0xc:0x10])[0]
	l_type = struct.unpack('<i', data[0x10:0x14])[0]
	add_iter (hd, "# of args", n_args,4,4,"<i")
	add_iter (hd, "Start of args", s_args,8,4,"<i")
	add_iter (hd, "Start of arg types", s_types,0xc,4,"<i")
	t_txt = "%02x"%l_type
	if loda_types.has_key(l_type):
		t_txt += " " + loda_types[l_type]
	add_iter (hd, "Type", t_txt,0x10,2,"txt")

def trfd (hd,size,data):
	start = 32
	if hd.version == 13:
		start = 40
	if hd.version == 5:
		start = 18
	add_iter (hd, "x0", "%u"%(struct.unpack('<d', data[start+16:start+24])[0]/10000),start+16,8,"<d")
	add_iter (hd, "y0", "%u"%(struct.unpack('<d', data[start+40:start+48])[0]/10000),start+40,8,"<d")
	for i in (0,1,3,4):                     
		var = struct.unpack('<d', data[start+i*8:start+8+i*8])[0]
		add_iter (hd, "var%d"%(i+1), "%f"%var,start+i*8,8,"<d")

cdr_ids = {"fild":fild,"ftil":ftil,"trfd":trfd,"loda":loda}

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
