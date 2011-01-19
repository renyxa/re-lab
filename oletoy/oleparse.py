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


import sys,struct
import gobject
import gtk
import tree
import hexdump
import pub
import pubblock
import escher
import quill
import vsd
import gsf

def open(src,model):
	infile = gsf.InfileMSOle(src)
	iter = None
	get_children(model,infile,iter)
	return

def get_children(model,infile,parent):
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
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,infname)
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,infchild.size())
		model.set_value(iter1,3,data)
		if (infname == "EscherStm" or infname == "EscherDelayStm") and infchild.size()>0:
			escher.parse (model,data,iter1)
		if infname == "CONTENTS": # assuming no atttempt to parse something else
			quill.parse (model,data,iter1)
		if infname == "Contents": # assuming no atttempt to parse something else
			pub.parse (model,data,iter1)
		if infname == "VisioDocument":
			vsd.parse (model, data, iter1) 
		if (infchild.num_children()>0):
			get_children(model,infchild,iter1)
	return


txt_id = {0xFF:'TextBlock'} # fake id used to mark text as text
