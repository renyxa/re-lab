# Copyright (C) 2007,2010,2011	Valek Filippov (frob@df.ru)
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
import tree, gtk, gobject
import ole, escher, rx2

def hex2d(data):
	res = ''
	data = data.replace(" ","")
	for i in range(len(data)/2):
		num = int(data[i*2:i*2+2],16)
		res += struct.pack("B",num)
	return res

def cmdfind(model,path,iter,(page,data)):
	if page.type[0:3] == "CDR" and model.iter_n_children(iter)>0:
		return
	buf = model.get_value(iter,3)
	test = 0
	while test < len(buf):
		test = buf.find(data,test+1)
		if test != -1:
			s_iter = page.search.append(None,None)
			page.search.set_value(s_iter,0,model.get_string_from_iter(iter))
			page.search.set_value(s_iter,1,test)
			page.search.set_value(s_iter,2,"%04x (%s)"%(test,model.get_value(iter,0)))
		else:
			return

def parse (cmd, entry, page):
	if cmd[0] == "$":
		pos = cmd.find("@")
		if pos != -1:
			chtype = cmd[1:pos]
			chaddr = cmd[pos+1:]
		else:
			chtype = cmd[1:4]
			chaddr = "0"
		print "Command: ",chtype,chaddr
		
		treeSelection = page.view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1 == None:
			page.view.set_cursor_on_cell(0)
			treeSelection = page.view.get_selection()
			model, iter1 = treeSelection.get_selected()
		buf = model.get_value(iter1,3)

		if "ole" == chtype.lower():
			if buf[int(chaddr,16):int(chaddr,16)+8] == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
				ole.open (buf[int(chaddr,16):],page,iter1)
			else:
				print "OLE stream not found at ",chaddr
		elif "esc" == chtype.lower():
			escher.parse (model,buf[int(chaddr,16):],iter1)
		elif "rx2" == chtype.lower():
			newL = struct.unpack('>I', buf[int(chaddr,16)+4:int(chaddr,16)+8])[0]
			rx2.parse (model,buf[int(chaddr,16):int(chaddr,16)+newL],0,iter1)
	elif cmd[0] == "?":
		ctype = cmd[1]
		carg = cmd[2:]
		if ctype == 'x' or ctype == 'X':
			data = hex2d(carg)
		elif ctype == 'a' or ctype == 'A':
			data = carg
		elif ctype == 'u' or ctype == 'U':
			data = carg.encode("utf-16")[2:]
		model = page.view.get_model()
		page.search = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING)
		model.foreach(cmdfind,(page,data))
		page.show_search(carg)

