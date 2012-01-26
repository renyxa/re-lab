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
from utils import *

pub98_types = {0x15:"Document",
	0x5:"Shape",0x8:"Text block",
	0x14:"Page",0x28:"(pub2k3 0x4a)",
	0x29:"Printers",0x47:"ColorSchemes"}


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
#	try:
	if 1:
		hdrsize = struct.unpack("<H",data[2:4])[0]
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Header")
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,hdrsize)
		model.set_value(iter1,3,data[0:hdrsize])
		if hdrsize == 0x22:
			parse98 (page,data,parent)
			return
		blocks = {}
		reorders = []
		off = hdrsize
	# Parse the 1st block after header
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Block A [%02x]"%off)
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,dlen)
		model.set_value(iter1,3,data[off:off+dlen])
		pubblock.parse (model,data[off+4:off+dlen],iter1,0)
	# Parse the dummy list block (the 2nd after header)
		[off] = struct.unpack('<I', data[0x1e:0x22])
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Block B [%02x]"%off)
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,dlen)
		model.set_value(iter1,3,data[off:off+dlen])
		pubblock.parse (model,data[off+4:off+dlen],iter1,1)
	# Parse the list of blocks block
		off = struct.unpack('<I', data[0x1a:0x1e])[0]
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Trailer   [%02x]"%(off))
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,dlen)
		model.set_value(iter1,3,data[off:off+dlen])
		pubblock.parse (model,data[off+4:off+dlen],iter1,2)
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
						iter1 = model.append(blocks[parid],None)
						if pubblock.block_types.has_key(type):
							name = "(%02x) %s"%(j,pubblock.block_types[type])
						else:
							name = "(%02x) Type: %02x"%(j,type)
						model.set_value(iter1,0,name)
						model.set_value(iter1,1,0)
						model.set_value(iter1,2,dlen)
						model.set_value(iter1,3,data[offset:offset+dlen])
						pubblock.parse (model,data[offset+4:offset+dlen],iter1,i+3)
						blocks[k+255] = iter1
					else:
						reorders.append(k+255)
				else:
					iter1 = model.append(parent,None)
					if pubblock.block_types.has_key(type):
						name = "(%02x) %s"%(j,pubblock.block_types[type])
					else:
						name = "(%02x) Type: %02x"%(j,type)
					model.set_value(iter1,0,name)
					model.set_value(iter1,1,0)
					model.set_value(iter1,2,dlen)
					model.set_value(iter1,3,data[offset:offset+dlen])
					pubblock.parse (model,data[offset+4:offset+dlen],iter1,i+3)
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
					iter1 = model.append(blocks[parid],None)
					if pubblock.block_types.has_key(type):
						name = "(%02x) %s"%(j,pubblock.block_types[type])
					else:
						name = "(%02x) Type: %02x"%(j,type)
					model.set_value(iter1,0,name)
					model.set_value(iter1,1,0)
					model.set_value(iter1,2,dlen)
					model.set_value(iter1,3,data[offset:offset+dlen])
					pubblock.parse (model,data[offset+4:offset+dlen],iter1,i)
				else:
					print "Failed to add reordered item %02x"%parid
		return
#	except:
#		print "Failed in parsing Contents"

