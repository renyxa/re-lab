# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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
import gobject
import gtk
import tree
import hexdump
import pubblock
import ctypes
from utils import *

pub98_types = {0x15:"Document",
	0x2:"Image",0x4:"Line",0x5:"Shape",0x6:"Shape2",0x7:"Ellipse",0x8:"Text block",0xa:"Table",0xb:"Bookmark",
	0xf:"Group",
	0x21:"ImgData",0x54:"Filename",
	0x14:"Page",0x28:"(pub2k3 0x4a)",
	0x29:"Printers",0x47:"ColorSchemes"}

def pub98anchor (hd,size,data):
	add_iter(hd,"Xs",struct.unpack("<i",data[6:0xa])[0]/12700.,6,4,"<I")
	add_iter(hd,"Ys",struct.unpack("<i",data[0xa:0xe])[0]/12700.,0xa,4,"<I")
	add_iter(hd,"Xe",struct.unpack("<i",data[0xe:0x12])[0]/12700.,0xe,4,"<I")
	add_iter(hd,"Ye",struct.unpack("<i",data[0x12:0x16])[0]/12700.,0x12,4,"<I")

def pub98image (hd,size,data):
	pub98anchor (hd,size,data)

def pub98line (hd,size,data):
	pub98anchor (hd,size,data)

def pub98shape (hd,size,data):
	pub98anchor (hd,size,data)

def pub98ellipse (hd,size,data):
	pub98anchor (hd,size,data)

def pub98text (hd,size,data):
	pub98anchor (hd,size,data)
	add_iter(hd,"Txt ID",struct.unpack("<i",data[0x58:0x5c])[0],0x58,4,"<I")

def pub98group (hd,size,data):
	pub98anchor (hd,size,data)

def pub98doc (hd,size,data):
	add_iter(hd,"Width",struct.unpack("<I",data[0x14:0x18])[0]/12700.,0x14,4,"<I")
	add_iter(hd,"Height",struct.unpack("<I",data[0x18:0x1c])[0]/12700.,0x18,4,"<I")

pub98_ids = {
	0x02:pub98image,
	0x04:pub98line,
	0x05:pub98shape,
	0x06:pub98shape,
	0x07:pub98ellipse,
	0x08:pub98text,
	0x0f:pub98group,
	0x15:pub98doc
}

# parse "Contents" part of the pub98/pub2k
def parse98 (page,data,parent):
	try:
		tr_start = struct.unpack("<I",data[0x16:0x1a])[0]
		add_pgiter (page,"Blocks A/B","pub",0,data[0x22:tr_start],parent)
		blocks = {}
		reorder = []
		n_blocks = struct.unpack("<H",data[tr_start:tr_start+2])[0]
		tr_end = tr_start + n_blocks*10+2
		tr_iter = add_pgiter (page,"Trailer","pub",0,data[tr_start:tr_end],parent)
		block_c_end = struct.unpack("<I",data[tr_start+18:tr_start+22])[0]
		add_pgiter (page,"Num of blocks (%02x)"%n_blocks,"pub",0,data[tr_start:tr_start+2],tr_iter)
		doc_iter = add_pgiter (page,"Document Blocks","pub",0,data[block_c_end:],parent)
		off = tr_start+2
		for i in range(n_blocks):
			fmt1 = ord(data[off+i*10])
			fmt2 = ord(data[off+i*10+1])
			blk_id = struct.unpack("<H",data[off+i*10+2:off+i*10+4])[0]
			par_id = struct.unpack("<H",data[off+i*10+4:off+i*10+6])[0]
			blk_offset = struct.unpack("<I",data[off+i*10+6:off+i*10+10])[0]
			add_pgiter (page,"Ptr %02x\t[Fmt: %02x %02x ID: %02x Parent: %02x Offset: %02x]"%(i,fmt1,fmt2,blk_id,par_id,blk_offset),"pub",0,data[off+i*10:off+i*10+10],tr_iter)
			blocks[blk_id] = [blk_offset,par_id]
			reorder.append(blk_id)
			if i > 0:
				blocks[prev_id].append(blk_offset)
			prev_id = blk_id

		blocks[prev_id].append(len(data))
		p_iter = doc_iter
		for i in reorder:
			start = blocks[i][0]
			end = blocks[i][2]
			par = blocks[i][1]
			b_type = struct.unpack("<H",data[start:start+2])[0]
			if pub98_types.has_key(b_type):
				b_txt = pub98_types[b_type]
			else:
				b_txt = "%02x"%b_type
			if blocks.has_key(par):
				p_iter = blocks[par][3]
			blocks[i].append(add_pgiter (page,"Block %02x (%s)"%(i,b_txt),"pub98",b_type,data[start:end],p_iter))
	except:
		print 'Failed in parsing pub98/2k "Contents"'


# parse "Contents" part of the OLE container
def parse(page,data,parent):
	model = page.model
	try:
#	if 1:
		hdrsize = struct.unpack("<H",data[2:4])[0]
		add_pgiter (page,"Header","pub",0,data[0:hdrsize],parent)
		if hdrsize == 0x22:
			parse98 (page,data,parent)
			return
		blocks = {}
		reorders = []
		off = hdrsize
	# Parse the 1st block after header
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = add_pgiter (page,"Block A [%02x]"%off,"pub",0,data[off:off+dlen],parent)
		pubblock.parse (page,data[off+4:off+dlen],iter1,0)
	# Parse the dummy list block (the 2nd after header)
		[off] = struct.unpack('<I', data[0x1e:0x22])
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = add_pgiter (page,"Block B [%02x]"%off,"pub",0,data[off:off+dlen],parent)
		pubblock.parse (page,data[off+4:off+dlen],iter1,1)
	# Parse the list of blocks block
		off = struct.unpack('<I', data[0x1a:0x1e])[0]
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = add_pgiter (page,"Trailer [%02x]"%off,"pub",0,data[off:off+dlen],parent)
		pubblock.parse (page,data[off+4:off+dlen],iter1,2)
		list_iter = model.iter_nth_child(iter1,2)
		j = 255
		for k in range (model.iter_n_children(list_iter)):
	#		print "Parse block %d"%i
			curiter = model.iter_nth_child(list_iter,k)
			test = model.get_value(curiter,0)
			if test[len(test)-4:] != "ID78":
				opts = ""
				parid = None
				for i in range (model.iter_n_children(curiter)):
					child = model.iter_nth_child(curiter,i)
					id = model.get_value(child,0)[4:6]
					if id == "02":
						type = struct.unpack("<H",model.get_value(child,3))[0]
					if id == "04":
						offset = struct.unpack("<I",model.get_value(child,3))[0]
					if id == "05":
						[parid] = struct.unpack("<I",model.get_value(child,3))
				[dlen] = struct.unpack('<I', data[offset:offset+4])
				if parid != None:
					if blocks.has_key(parid):
						if pubblock.block_types.has_key(type):
							name = "(%02x) %s"%(j,pubblock.block_types[type])
						else:
							name = "(%02x) Type: %02x"%(j,type)
						iter1 = add_pgiter (page,name,"pub",0,data[offset:offset+dlen],blocks[parid])
						pubblock.parse (page,data[offset+4:offset+dlen],iter1,i+3)
						blocks[k+255] = iter1
					else:
						reorders.append(k+255)
				else:
					if pubblock.block_types.has_key(type):
						name = "(%02x) %s"%(j,pubblock.block_types[type])
					else:
						name = "(%02x) Type: %02x"%(j,type)
					iter1 = add_pgiter (page,name,"pub",0,data[offset:offset+dlen],parent)
					pubblock.parse (page,data[offset+4:offset+dlen],iter1,i+3)
					blocks[k+255] = iter1
			j += 1
		for k in reorders:
			curiter = model.iter_nth_child(list_iter,k)
			for i in range (model.iter_n_children(curiter)):
				child = model.iter_nth_child(curiter,i)
				id = model.get_value(child,0)[4:6]
				if id == "02":
					type = struct.unpack("<H",model.get_value(child,3))[0]
				if id == "04":
					offset = struct.unpack("<I",model.get_value(child,3))[0]
				if id == "05":
					[parid] = struct.unpack("<I",model.get_value(child,3))
				[dlen] = struct.unpack('<I', data[offset:offset+4])
				if blocks.has_key(parid):
					if pubblock.block_types.has_key(type):
						name = "(%02x) %s"%(j,pubblock.block_types[type])
					else:
						name = "(%02x) Type: %02x"%(j,type)
					iter1 = add_pgiter (page,name,"pub",0,data[offset:offset+dlen],blocks[parid])
					pubblock.parse (page,data[offset+4:offset+dlen],iter1,i)
				else:
					print "Failed to add reordered item %02x"%parid
		return
	except:
		print "Failed in parsing Contents"

def collect_ec(model,parent):
	res = ""
	value = model.get_value(parent,3)
	if model.iter_n_children(parent):
		res += value[:8]
		for i in range(model.iter_n_children(parent)):
			citer = model.iter_nth_child(parent, i)
			res += collect_ec(model,citer)
	else:
		res += value
	return res

def collect_escher(model,citer):
	res = ""
	tmp = ""
	for i in range(model.iter_n_children(citer)):
		gciter = model.iter_nth_child(citer, i)
		name = model.get_value(gciter,0)
		value = model.get_value(gciter,3)
		res += value[:8]
		tmp += value
		for j in range(model.iter_n_children(gciter)):
			ggciter = model.iter_nth_child(gciter, j)
			res += collect_ec(model,ggciter)

		if len(res) < len(tmp):
			res += tmp[len(res):]

	return res

def dump_tree (model, parent, outfile,cgsf):
	ntype = model.get_value(parent,1)
	name = model.get_value(parent,0)
	value = model.get_value(parent,3)

	if name == 'Quill':
		child = cgsf.gsf_outfile_new_child(outfile,name,1)
		cgsf.gsf_output_write (child,len(value),value)
		citer = model.iter_nth_child(parent, 0)
		gname = model.get_value(citer,0)
		gvalue = model.get_value(citer,3)
		gchild = cgsf.gsf_outfile_new_child(child,gname,1)
		cgsf.gsf_output_write (gchild,len(gvalue),gvalue)
		for i in range(model.iter_n_children(citer)):
			gciter = model.iter_nth_child(citer, i)
			ggname = model.get_value(gciter,0)
			ggvalue = model.get_value(gciter,3)
			ggchild = cgsf.gsf_outfile_new_child(gchild,ggname,0)
			cgsf.gsf_output_write (ggchild,len(ggvalue),ggvalue)
			cgsf.gsf_output_close (ggchild)
		cgsf.gsf_output_close (gchild)

	elif name =="Escher":
		child = cgsf.gsf_outfile_new_child(outfile,name,1)
		cgsf.gsf_output_write (child,len(value),value)
		for i in range(model.iter_n_children(parent)):
			citer = model.iter_nth_child(parent, i)
			name = model.get_value(citer,0)
			if name == "EscherStm":
				value = collect_escher(model,citer)
			else:
				value = model.get_value(citer,3)
			gchild = cgsf.gsf_outfile_new_child(child,name,0)
			cgsf.gsf_output_write (gchild,len(value),value)
			cgsf.gsf_output_close (gchild)

	else: # Quill/Escher
		child = cgsf.gsf_outfile_new_child(outfile,name,0)
		cgsf.gsf_output_write (child,len(value),value)

	cgsf.gsf_output_close (child)




def save (page, fname):
	model = page.view.get_model()
	cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')
	cgsf.gsf_init()
	output = cgsf.gsf_output_stdio_new (fname)
	outfile = cgsf.gsf_outfile_msole_new (output);
	iter1 = model.get_iter_first()
	while None != iter1:
	  dump_tree(model, iter1, outfile,cgsf)
	  iter1 = model.iter_next(iter1)
	cgsf.gsf_output_close(outfile)
	cgsf.gsf_shutdown()
