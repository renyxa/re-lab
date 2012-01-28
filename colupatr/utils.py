#!/usr/bin/env python
# Copyright (C) 2011	Valek Filippov (frob@df.ru)
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

import struct
import gtk, gobject

def hex2d(data):
	res = ''
	data = data.replace(" ","")
	for i in range(len(data)/2):
		num = int(data[i*2:i*2+2],16)
		res += struct.pack("B",num)
	return res

def d2hex(data):
	s = ""
	for i in range(len(data)):
		s += "%02x"%ord(data[i])
	return s

def arg_conv (ctype,carg):
	data = ''
	if ctype.lower() == 'x':
		data = hex2d(carg)
	elif ctype.lower() == 'u':
		data = carg.encode("utf-16")[2:]
	elif ctype.lower() == 'a' or ctype.lower() == 'r':
		data = carg
	return data

def cmd_parse(cmd, app,doc):
	if cmd[0] == "?":
		ctype = cmd[1]
		carg = cmd[2:]
		# convert line to hex or unicode if required
		data = arg_conv(ctype,carg)
		app.search = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING)
		sflag = 0
		p = doc.data.find(data)
		while p !=-1:
			s_iter = app.search.append(None,None)
			app.search.set_value(s_iter,2,"%02x"%p)
			p = doc.data.find(data,p+1)
			sflag = 1
		if sflag:
			app.show_search(carg)


