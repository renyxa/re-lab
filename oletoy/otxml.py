# Copyright (C) 2007-2013	Valek Filippov (frob@df.ru)
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

import sys,struct,gtk
from utils import *

def open (buf,page,parent):
	print("Probably XML",page.model.get_value(parent,0))
        if buf[0:2] == '\xff\xfe':
            buf = unicode(buf[2:], 'utf_16le')
        elif buf[0:2] == '\xfe\xff':
            buf = unicode(buf[2:], 'utf_16be')
	t = buf.split("<")
	piter = parent
	citer = []

	for i in range(len(t)-1):
		foo = t[i+1].split()
		if len(foo) > 0:
			bar = foo[0]
		else:
			bar = foo[:-1]
		
		if bar[0] == "?":
			id = bar[1:]
		else:
			id = bar
		
		if id[-1] == ">":
			id = id[:-1]
		else:
			id = id.replace(">",": ")
		
		data = "<"+t[i+1].replace("\x0d\x0a","")  # all from tag start till next tag

		if bar[0] != "/":
			if t[i+1][-2:-1] != "/":
				d = data.split(">")
				niter = add_pgiter (page,id,"xml","",d[0]+">",piter)
				if len(d)>1 and len(d[1]) > 0:
					add_pgiter (page,id,"xml","sub",d[1],niter)
				citer.append(piter)
				piter = niter
			else:
				niter = add_pgiter (page,id,"xml","",data,piter)
		else:
			piter = citer.pop()

	return "xml"
