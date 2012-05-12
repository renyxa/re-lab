# Copyright (C) 2007-2012,	Valek Filippov (frob@df.ru)
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
from utils import *

def rtf_read (buf,off,page,parent):
	val = ""
	name = ""
	value = ""
	nflag = 0
	flush = 0
	pflag = 0
	name2 = ""

	while off < len(buf):
		ch = buf[off]
		off += 1

		if ord(ch) == 0xd or ord(ch) == 0xa:
			nflag = 0

		if ch == "{":
			nflag = 0
			if not flush:
				piter = add_pgiter (page,name,"rtf",name,value,parent)
				flush = 1
			off = rtf_read(buf,off,page,piter)

		if ch == "}":
			if not flush:
				if name == "pict":
					iter1 = page.model.prepend (parent,None)
					page.model.set_value(iter1,0,name)
					page.model.set_value(iter1,1,("rtf",name))
					page.model.set_value(iter1,2,len(value))
					page.model.set_value(iter1,3,value)
					page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))

				else:
					add_pgiter (page,name,"rtf",name,value,parent)
			return off

		if ch == "\\":
			if name == "" or name == "*":
				nflag = 1
			else:
				nflag = 0

		if nflag and ch !="\\":
			name += ch
		if pflag:
			if ch !="\\":
				name2 += ch
				if name2 == "bin":
					size = struct.unpack(">H",buf[off:off+2])[0]
					value += ch
					add_pgiter (page,name2,"rtf",name,buf[off:off+2+size],parent)
					off += size+2
				else:
					value += ch
			else:
				name2 = ""
				value += ch
		else:
			value += ch
		if name == "pict":
			pflag = 1
		else:
			pflag = 0

def open(buf,page,parent):
	off = 0
	rtf_read (buf[1:],off,page,parent)
	return "RTF"
