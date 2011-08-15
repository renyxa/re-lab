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
import oleparse

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
