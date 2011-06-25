# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
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

import struct


def sl_8bytes(hd, data, shift, offset, blk_off):
	value = struct.unpack("<d",data[offset+blk_off:offset+blk_off+8])[0]
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tieee754", 1, value,2,shift+offset+blk_off,3,8,4,"<d")
	return blk_off+8

def sl_2bytes(hd, data, shift, offset, blk_off):
	value = struct.unpack("<h",data[offset+blk_off:offset+blk_off+2])[0]
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tword", 1, value,2,shift+offset+blk_off,3,2,4,"<h")
	return blk_off+2

def sl_1byte(hd, data, shift, offset, blk_off):
	value = ord(data[offset+blk_off])
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tbyte", 1, value,2,shift+offset+blk_off,3,1,4,"<b")
	return blk_off+1

names75 = {0:'PinX',1:'PinY',2:'Width',3:'Height',4:'LocPinX',5:'LocPinY',
						6:'Angle',7:'FlipX',8:'FlipY',9:'ResizeMode',10:'BeginX',
						11:'BeginY',12:'EndX',13:'EndY',14:"LineWeight",
15:"LineColor",16:"LinePattern",17:"FillForegnd",18:"FillBkgnd",
19:"FillPattern",20:"TextDirection",21:"TextContainer",22:"TextGeometry",}

def sl_names75(hd, data, shift, offset, blk_off):
	value = ord(data[offset+blk_off])
	nm_str = "%02x"%value
	if names75.has_key(value):
		nm_str += " ("+names75[value]+")"
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tname75", 1, nm_str,2,shift+offset+blk_off,3,4,4,"<I")
	return blk_off+4

fnames79 = {0x83:"RGB",0x9f:"Polyline",0xa1:"NURBS",0xd3:"BOUND",0xdb:"THEME",
		0xdd:"SHADE", 0xdf:"LUMDIFF",0xe3:"THEMEGUARD",0xe5:"THEMERESTORE",}

def sl_funcs79(hd, data, shift, offset, blk_off):
	nargs = struct.unpack("<I",data[offset+blk_off:offset+blk_off+4])[0]
	fid = ord(data[offset+blk_off+4])
	nm_str = "# of args: %i "%nargs
	if fnames79.has_key(fid):
		nm_str += "("+fnames79[fid]+")" 
	else:
		nm_str += "%02x"%fid
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tfunc79", 1, nm_str,2,shift+offset+blk_off,3,8,4,"<d")
	return blk_off+8

def sl_funcs7a(hd, data, shift, offset, blk_off):
	fid = ord(data[offset+blk_off])
	if fnames79.has_key(fid):
		nm_str = fnames79[fid]
	else:
		nm_str = "%02x"%fid
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tfunc7a", 1, nm_str,2,shift+offset+blk_off,3,4,4,"<I")
	return blk_off+4

def sl_str(hd, data, shift, offset, blk_off):
	slen = ord(data[offset+blk_off])
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "\tstring", 1, unicode(data[offset+blk_off+1:offset+blk_off+3+slen*2],"utf-16"),2,shift+offset+blk_off,3,3+slen*2,4,"txt")
	return blk_off+3+slen*2

def get_slice (hd, data, shift, offset, blk_off):
	blk_func = ord(data[offset+blk_off])
	if blk_func > 0x19 and blk_func < 0x60:  #
		blk_off = sl_8bytes(hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x61:
		blk_off = sl_1byte(hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x62:
		blk_off = sl_2bytes(hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x75:
		blk_off = sl_names75 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x7b or blk_func == 0x81:
		blk_off = sl_funcs79 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x7a or blk_func == 0x80:
		blk_off = sl_funcs7a (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x60:
		blk_off = sl_str (hd,data,shift,offset,blk_off+1)  #may require 'version' to check for 6 vs 11
	else:
		blk_off += 1 # bad idea, but just to skip unknowns
	return blk_off

def parse (hd, size, value,shift):
	# offset -- where we are in the buffer
	# shift -- what to add to hd iter
	# blk_off -- offset inside the block
	offset = 0
	blk_id = 0
	data = value[shift:]
	
	while offset < len(data):
		[blk_len] = struct.unpack("<I",data[offset:offset+4])
		if blk_len == 0:
			blk_len = 4  # 4 bytes "trailer" at the end of chunk
		else:
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "Blk #%d Length"%blk_id, 1, blk_len,2,shift+offset,3,4,4,"<d")
			blk_id += 1
			blk_off = 4
			blk_type = ord(data[offset+blk_off])
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "\tBlk Type", 1, blk_type,2,shift+offset+blk_off,3,1,4,"<b")
			blk_off = 5
			blk_idx = ord(data[offset+blk_off]) # which cell in the shapesheet this formula is for
			iter1 = hd.hdmodel.append(None, None)
			hd.hdmodel.set (iter1, 0, "\tBlk IDX", 1, blk_idx,2,shift+offset+blk_off,3,1,4,"<b")
			blk_off = 6
			if blk_type == 2:
				while blk_off < blk_len:
					blk_off = get_slice(hd, data, shift, offset, blk_off)

		offset += blk_len
