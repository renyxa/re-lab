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
import vsd, xls, ppt
import gsf

def open(src,page,iter=None):
	infile = gsf.InfileMSOle(src)
	type = get_children(page,infile,iter)
	return type

def get_children(page,infile,parent):
	type = "OLE"
	for i in range(infile.num_children()):
		infchild = infile.child_by_index(i)
		infname = infile.name_by_index(i)
		if ord(infname[0]) < 32: 
			infname = infname[1:]
		#itername = infname + ' \t(Size: %x)'%infchild.size()
		print " ",infname
		if infname == "dir":
			infuncomp = infchild.uncompress()
			data = infuncomp.read(infuncomp.size())
		else:
			data = infchild.read(infchild.size())
		iter1 = page.model.append(parent,None)
		page.model.set_value(iter1,0,infname)
		page.model.set_value(iter1,1,0)
		page.model.set_value(iter1,2,infchild.size())
		page.model.set_value(iter1,3,data)
		if (infname == "EscherStm" or infname == "EscherDelayStm") and infchild.size()>0:
			escher.parse (page.model,data,iter1)
		if infname == "CONTENTS": # assuming no atttempt to parse something else
			quill.parse (page.model,data,iter1)
		if infname == "Contents": # assuming no atttempt to parse something else
			type = "PUB"
			pub.parse (page.model,data,iter1)
		if infname == "VisioDocument":
			type = "VSD"
			vsd.parse (page, data, iter1)
		if infname == "Book" or infname == "Workbook":
			type = xls.parse (page, data, iter1)
		if infname == "PowerPoint Document" or infname == "Pictures":
			type = "PPT"
			ppt.parse (page, data, iter1)
		if (infchild.num_children()>0):
			get_children(page,infchild,iter1)
	return type


txt_id = {0xFF:'TextBlock'} # fake id used to mark text as text
