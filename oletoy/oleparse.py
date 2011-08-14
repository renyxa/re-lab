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


import sys,struct
import gobject
import gtk
import tree
import hexdump
import pub, pubblock, escher, quill
import vsd, xls, ppt, vba
import ctypes

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')

def open(buf,page,iter=None):
	cgsf.gsf_init()
	src = cgsf.gsf_input_memory_new (buf,len(buf),False)
	infile = cgsf.gsf_infile_msole_new(src)
	type = get_children(page,infile,iter,"OLE")
	cgsf.gsf_shutdown()
	return type

def get_children(page,infile,parent,type):
	for i in range(cgsf.gsf_infile_num_children(infile)):
		infchild = cgsf.gsf_infile_child_by_index(infile,i)
		infname = ctypes.string_at(cgsf.gsf_infile_name_by_index(infile,i))
		if ord(infname[0]) < 32: 
			infname = infname[1:]
		if infname == "dir":
			infuncomp = cgsf.gsf_input_uncompress(infchild)
			chsize = cgsf.gsf_input_size(infuncomp)
			data = ctypes.string_at(cgsf.gsf_input_read(infuncomp,chsize,None),chsize)
		else:
			chsize = cgsf.gsf_input_size(infchild)
			data = ""
			res = ""
			pos = -1
			inc = 1024
			while cgsf.gsf_input_tell(infchild) < chsize:
				if pos == cgsf.gsf_input_tell(infchild):
					if inc == 1:
						break
					else:
						inc = inc/2
				else:
					pos = cgsf.gsf_input_tell(infchild)
				res = ctypes.string_at(cgsf.gsf_input_read(infchild,inc,None),inc)
				if pos != cgsf.gsf_input_tell(infchild):
					data += res
			
		if infname == "VBA":
			type = "VBA"
		iter1 = page.model.append(parent,None)
		page.model.set_value(iter1,0,infname)
		page.model.set_value(iter1,1,(type,0))
		page.model.set_value(iter1,2,chsize)
		page.model.set_value(iter1,3,data)
		if (infname == "EscherStm" or infname == "EscherDelayStm"): # and infchild.size()>0:
			escher.parse (page.model,data,iter1)
		if infname == "CONTENTS": # assuming no attempt to parse something else
			quill.parse (page.model,data,iter1)
		if infname == "Contents": # assuming no attempt to parse something else
			type = "PUB"
			pub.parse (page.model,data,iter1)
		if infname == "VisioDocument":
			type = "VSD"
			page.model.set_value(iter1,1,("OLE",1))
			vsd.parse (page, data, iter1)
		if infname == "Book" or infname == "Workbook":
			type = xls.parse (page, data, iter1)
		if infname == "PowerPoint Document" or infname == "Pictures":
			type = "PPT"
			ppt.parse (page, data, iter1)
		if type == "VBA" and infname == "dir":
			print 'Parse vba'
			vba.parse (page, data, iter1)
		if (cgsf.gsf_infile_num_children(infchild)>0):
			get_children(page,infchild,iter1,type)
	return type


txt_id = {0xFF:'TextBlock'} # fake id used to mark text as text
