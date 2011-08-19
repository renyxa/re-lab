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

import sys,struct
import gobject
import gtk
import tree
import hexdump
import inflate
import ctypes

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')


charsets = {0:"Latin", 1:"System default", 2:"Symbol", 77:"Apple Roman",
	128:"Japanese Shift-JIS",129:"Korean (Hangul)",130:"Korean (Johab)",
	134:"Chinese Simplified GBK",136:"Chinese Traditional BIG5",
	161:"Greek",162:"Turkish",163:"Vietnamese",177:"Hebrew",178:"Arabic",
	186:"Baltic",204:"Cyrillic",222:"Thai",238:"Latin II (Central European)",
	255:"OEM Latin I"}

escapement = {0:"None", 1:"Superscript", 2:"Subscript"}

underline = {0:"None",1:"Single",2:"Double",0x21:"Single accounting",0x22:"Double accounting"}

def add_hditer (hd,name,value,offset,length,vtype):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype)

def add_pgiter (page, name, ftype, stype, data, parent = None):
	iter1 = page.model.append (parent,None)
	page.model.set_value(iter1,0,name)
	page.model.set_value(iter1,1,(ftype,stype))
	page.model.set_value(iter1,2,len(data))
	page.model.set_value(iter1,3,data)
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	return iter1

def parse (page, data, parent):
	offset = 0
	type = "DOC"
	add_pgiter (page,"Base","doc","base",data[0:0x20],parent)
	offset += 0x20
	csw = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgW","doc","fibRgW",data[offset:offset+2+csw*2],parent)
	offset += 2+csw*2
	cslw = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgLw","doc","fibRgLw",data[offset:offset+2+cslw*4],parent)
	offset += 2+cslw*4
	cbRgFcLcb = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgFcLcbBlob","doc","fibRgFcLcbBlob",data[offset:offset+2+cbRgFcLcb*8],parent)
	offset += 2+cbRgFcLcb*8
	cswNew = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgCswNew","doc","fibRgCswNew",data[offset:offset+2+cswNew*2],parent)


def dump_tree (model, parent, outfile):
	ntype = model.get_value(parent,1)
	name = model.get_value(parent,0)
	if ntype[1] == 0:
	  child = cgsf.gsf_outfile_new_child(outfile,name,0)
	  value = model.get_value(parent,3)
	  if name[:6] == "Module":
		piter = model.iter_nth_child(parent,0)
		data = model.get_value(piter,3)
		srcoff = model.get_value(piter,1)[2]
		off = 0
		value = value[:srcoff]
		while  off + 4094 < len(data):
		  value += "\x30\x00"+data[off:off+4094]
		  off += 4094
		if off < len(data):
		  res = inflate.deflate(data[off:],1)
		  flag = 0xb000+len(res)
		  value += struct.pack("<H",flag)+res
	  cgsf.gsf_output_write (child,len(value),value)

	else: # Directory
	  child = cgsf.gsf_outfile_new_child(outfile,name,1)

	  for i in range(model.iter_n_children(parent)):
		piter = model.iter_nth_child(parent,i)
		dump_tree (model, piter, child)

	cgsf.gsf_output_close (child)


def save (page, fname):
	model = page.view.get_model()
	cgsf.gsf_init()
	output = cgsf.gsf_output_stdio_new (fname)
	outfile = cgsf.gsf_outfile_msole_new (output);
	iter1 = model.get_iter_first()
	while None != iter1:
	  dump_tree(model, iter1, outfile)
	  iter1 = model.iter_next(iter1)
	cgsf.gsf_output_close(outfile)
	cgsf.gsf_shutdown()

