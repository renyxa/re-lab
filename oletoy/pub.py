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

# parse "Contents" part of the OLE container
def parse(model,data,parent):
	try:
		blocks = {}
		reorders = []
		[hdrsize] = struct.unpack("<H",data[2:4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Header")
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,hdrsize)
		model.set_value(iter1,3,data[0:hdrsize])
		off = hdrsize
	# Parse the 1st block after header
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Block %d [%02x]"%(0,off))
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,dlen)
		model.set_value(iter1,3,data[off:off+dlen])
		pubblock.parse (model,data[off+4:off+dlen],iter1,0)
	# Parse the dummy list block (the 2nd after header)
		[off] = struct.unpack('<I', data[0x1e:0x22])
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Block %d [%02x]"%(1,off))
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,dlen)
		model.set_value(iter1,3,data[off:off+dlen])
		pubblock.parse (model,data[off+4:off+dlen],iter1,1)
	# Parse the list of blocks block
		off = struct.unpack('<I', data[0x1a:0x1e])[0]
		[dlen] = struct.unpack('<I', data[off:off+4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"List of blocks   [%02x]"%(off))
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
	except:
		print "Failed in parsing Contents"

