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

def d2hex(data):
	return "%02x%02x%02x%02x"%(ord(data[0]),ord(data[1]),ord(data[2]),ord(data[3]))

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

def loda_outl (hd,data,offset,l_type):
	add_iter (hd, "[0x0a] Outl ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_fild (hd,data,offset,l_type):
	add_iter (hd, "[0x14] Fild ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_stlt (hd,data,offset,l_type):
	add_iter (hd, "[0x68] Stlt ID",d2hex(data[offset:offset+4]),offset,4,"txt")

def loda_rot(hd,data,offset,l_type):
	[rot] = struct.unpack('<L', data[offset:offset+4])
	add_iter (hd, "[0x2efe] Rotate","%u"%round(rot/1000000.0,2),offset,4,"txt")

def loda_name(hd,data,offset,l_type):
	if hd.version > 12:
		layrname = unicode(data[offset:],'utf-16').encode('utf-8')
	else:
		layrname = data[offset:]
	add_iter (hd,"[0x3e8] Layer name",layrname,offset,len(data[offset:]),"txt")

def loda_polygon (hd,data,offset,l_type):
	num = struct.unpack('<L', data[offset+4:offset+8])[0]
	add_iter (hd,"[0x2af8] # of angles",num,offset,4,"<I")
	for i in range(4):
		[varX] = struct.unpack('<L', data[offset+0x10+i*8:offset+0x14+i*8])
		[varY] = struct.unpack('<L', data[offset+0x14+i*8:offset+0x18+i*8])
		if varX > 0x7FFFFFFF:
			varX = varX - 0x100000000
		if varY > 0x7FFFFFFF:
			varY = varY - 0x100000000
		add_iter (hd,"[0x2af8] X%u/Y%u"%(i,i),"%u/%u mm"%(round(varX/10000.0,2),round(varY/10000.0,2)),offset+0x10+i*8,8,"txt")

def loda_coords124 (hd,data,offset,l_type):
# rectangle or ellipse or text
	x1 = struct.unpack('<L', data[offset:offset+4])[0]
	y1 = struct.unpack('<L', data[offset+4:offset+8])[0]
	if x1 > 0x7FFFFFFF:
		x1 -= 0x100000000
	if y1 > 0x7FFFFFFF:
		y1 -= 0x100000000
	add_iter (hd,"[0x1e] x1/y1","%u/%u mm"%(round(x1/10000.0,2),round(y1/10000.0,2)),offset,8,"txt")

	if l_type == 1:
		R1 = struct.unpack('<L', data[offset+8:offset+12])[0]
		R2 = struct.unpack('<L', data[offset+12:offset+16])[0]
		R3 = struct.unpack('<L', data[offset+16:offset+20])[0]
		R4 = struct.unpack('<L', data[offset+20:offset+24])[0]
		add_iter (hd,"[0x1e] R1 R2 R3 R4","%u %u %u %u mm"%(round(R1/10000.0,2),round(R2/10000.0,2),round(R3/10000.0,2),round(R4/10000.0,2)),offset+8,16,"txt")

	if l_type == 2:
		a1 = struct.unpack('<L', data[offset+8:offset+12])[0]
		a2 = struct.unpack('<L', data[offset+12:offset+16])[0]
		a3 = struct.unpack('<L', data[offset+16:offset+20])[0]
		add_iter (hd,"[0x1e] Start/End/Rot angles","%u %u %u"%(round(a1/1000000.0,2),round(a2/1000000.0,2),round(a3/1000000.0,2)),offset+8,12,"txt")

def loda_coords3 (hd,data,offset,l_type):
	[pointnum] = struct.unpack('<L', data[offset:offset+4])
	for i in range (pointnum):
		x = struct.unpack('<L', data[offset+4+i*8:offset+8+i*8])[0]
		y = struct.unpack('<L', data[offset+8+i*8:offset+12+i*8])[0]
		Type = ord(data[offset+4+pointnum*8+i])
		NodeType = ''
		# FIXME! Lazy to learn dictionary right now, will fix later
		if Type&2 == 2:
			NodeType = '    Char. start'
		if Type&4 == 4:
			NodeType = NodeType+'  Can modify'
		if Type&8 == 8:
			NodeType = NodeType+'  Closed path'
		if Type&0x10 == 0 and Type&0x20 == 0:
			NodeType = NodeType+'  Discontinued'
		if Type&0x10 == 0x10:
			NodeType = NodeType+'  Smooth'
		if Type&0x20 == 0x20:
			NodeType = NodeType+'  Symmetric'
		if Type&0x40 == 0 and Type&0x80 == 0:
			NodeType = NodeType+'  START'
		if Type&0x40 == 0x40 and Type&0x80 == 0:
			NodeType = NodeType+'  Line'
		if Type&0x40 == 0 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Curve'
		if Type&0x40 == 0x40 and Type&0x80 == 0x80:
			NodeType = NodeType+'  Arc'
		if x > 0x7FFFFFFF:
			x -= 0x100000000
		if y > 0x7FFFFFFF:
			y -= 0x100000000
		add_iter (hd,"[0x1e] X%u/Y%u/Type"%(i+1,i+1),"%u/%u mm"%(round(x/10000.0,2),round(y/10000.0,2))+NodeType,offset+4+i*8,9,"txt")



def loda_coords (hd,data,offset,l_type):
	if l_type < 5 and l_type != 3:
		loda_coords124 (hd,data,offset,l_type)
	elif l_type == 3:
		loda_coords3 (hd,data,offset,l_type)

loda_types = {0:"Layer",1:"Rectangle",2:"Ellipse",3:"Line/Curve",4:"Text",5:"Bitmap",20:"Polygon"}
loda_type_func = {0xa:loda_outl,0x14:loda_fild,0x1e:loda_coords,
									0x68:loda_stlt, 0x2af8:loda_polygon,
									0x3e8:loda_name,
									0x2efe:loda_rot	#, 0x7d0:loda_palt, 0x1f40:loda_lens, 0x1f45:loda_contnr
									}

def loda (hd,size,data):
	n_args = struct.unpack('<i', data[4:8])[0]
	s_args = struct.unpack('<i', data[8:0xc])[0]
	s_types = struct.unpack('<i', data[0xc:0x10])[0]
	l_type = struct.unpack('<i', data[0x10:0x14])[0]
	add_iter (hd, "# of args", n_args,4,4,"<i")
	add_iter (hd, "Start of args offsets", "%02x"%s_args,8,4,"<i")
	add_iter (hd, "Start of arg types", "%02x"%s_types,0xc,4,"<i")
	t_txt = "%02x"%l_type
	if loda_types.has_key(l_type):
		t_txt += " " + loda_types[l_type]
	add_iter (hd, "Type", t_txt,0x10,2,"txt")

	a_txt = ""
	t_txt = ""
	for i in range(n_args,0,-1):
		a_txt += " %04x"%struct.unpack('<L',data[s_args+i*4-4:s_args+i*4])[0]
		t_txt += " %04x"%struct.unpack('<L',data[s_types+(n_args-i)*4:s_types+(n_args-i)*4+4])[0]
	add_iter (hd, "Args offsets",a_txt,s_args,n_args*4,"txt")
	add_iter (hd, "Args types",t_txt,s_types,n_args*4,"txt")

	if loda_types.has_key(l_type):
		for i in range(n_args, 0, -1):
			[offset] = struct.unpack('<L',data[s_args+i*4-4:s_args+i*4])
			[argtype] = struct.unpack('<L',data[s_types + (n_args-i)*4:s_types + (n_args-i)*4+4])
			if loda_type_func.has_key(argtype):
				loda_type_func[argtype](hd,data,offset,l_type)
			else:
				print 'Unknown argtype: %x'%argtype                             

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
