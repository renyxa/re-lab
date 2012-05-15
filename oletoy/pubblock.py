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
from utils import *

block_types = {
	0x01:"Shape",
	0x10:"Table",
	0x30:"Logo",
	0x43:"Page",0x44:"Document",0x46:"BorderArt",0x4b:"Printers",0x4c:"Rulers",
	0x5c:"ColorSchemes",
	0x60:'PageName', 0x63:"Cells",0x66:"FileName",0x6c:"Fonts",0x8a:"Page Fmt"}

# parses semi-standard "block" structures in MS Pub files.
def parse (page,data,parent,i,j=-1):
	model = page.model
	off = 0
	value = None
	try:
#	if 1:
		while off < len(data) - 2:
			id = ord(data[off])
			type = ord(data[off+1])
			name = "ID: %02x  Type: %02x"%(id,type)
#			print "ID: %02x  Type: %02x Off: %02x"%(id,type,off)
			off+=2
			dlen = -1
			if type < 5 or type == 8 or type == 0xa:
				value = None
				dlen = 0
			if type == 0x78:	
				value = None
				dlen = 0
				name = "(%02x) ID78"%j
			if type == 0x10 or type == 0x12 or type == 0x18 or type == 0x19 or type == 0x1a:
				value = data[off:off+2]
				dlen = 2
				name += " (%02d)"%struct.unpack("<H",value)[0]
			if type == 0x20:
				value = data[off:off+4]
				dlen = 4
				v = struct.unpack("<I",value)[0]
				if v > 12700 and v < 220370400:
					# couldn't be EMU if less than 1 point or more than 241 inch
					name += " (%.2f pt)"%(v/12700.)
				else:
					name += " (%02d)"%v

			if type == 0x48:
				value = data[off:off+24]
				off += 24
				dlen = 0

			if type == 0x22 or type == 0x58 or type == 0x68 or type == 0x70:
				value = data[off:off+4]
				dlen = 4
				if type != 0x70:
					name += " (%02d)"%struct.unpack("<I",value)[0]
				else:
					name += " (0x%02x)"%struct.unpack("<I",value)[0]
				
				if id == 5 and type == 0x68:
					pname = model.get_value(parent,0)
					model.set_value(parent,0,pname+"\t\t%02x"%struct.unpack("<i",value)[0])
			if type == 0x38:
				value = data[off:off+16]
				dlen = 16
				name += " ()"
			if type == 0xb or type == 0x7 or type == 0x28:
				value = data[off:off+8]
				dlen = 8
				name += " ()"

			if type == 0xb8:
				value = data[off:off+4]
				dlen = 4
				name += " (offset 0x%04x)"%struct.unpack("<i",value)[0]

				id2_iter = model.iter_nth_child(parent,0)
				id2_value = struct.unpack("<H",model.get_value(id2_iter,3))[0]
				if block_types.has_key(id2_value):
					btype = block_types[id2_value]
				else:
					btype = "%02x"%id2_value
				if model.get_value(parent,0)[0:7] != "Block A":
					model.set_value(parent,0,"(%02x) Type: %s"%(j,btype))

			if type == 0x80 or type == 0x82 or type == 0x88 or type == 0x8a or type == 0x90 or type == 0x98 or type == 0xa0:
				[dlen] = struct.unpack('<i', data[off:off+4])
				value = data[off:off+dlen]
			if type == 0xc0:
				[dlen] = struct.unpack('<i', data[off:off+4])
				value = data[off+4:off+dlen]
				if dlen > 4:
					try:
						name += " %s"%unicode(value,'utf-16')
					except:
						name += value
						print "UCode failed",model.get_string_from_iter(parent)
			if type == 0xFF: # current len just to pass parsing
				value = ord(data[off+1])
				dlen = 1
			j += 1
			if dlen == -1:
				print "Unknown type %02x at block %d %d %02x"%(type,i,j,off),
				iter1 = add_pgiter (page,"Unkn block","pub",0,"",parent)
				model.set_value(iter1,5,"#FF0000")
				print "Path",model.get_string_from_iter(iter1)
				return
			else:
				if type != 0x78 or j > 0xFF:
					iter1 = add_pgiter (page,name,"pub",0,value,parent)
					if dlen > 4 and type != 0xc0 and type != 0x38 and type != 0x28:
						parse (page,data[off+4:off+dlen],iter1,i,j-2)
					off += dlen
	except:
		print "Failed at parsing block %d "%i,"val: ",value," off: ",off,model.get_string_from_iter(parent)
