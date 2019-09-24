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

import sys,struct,zlib
import gtk
from utils import *

def firewrk_mkbs (page, buf, parent=None):
	piters = []
	if parent:
		piters.append(parent)
	spl = buf.split("{")
	ind = 0
	while len(spl) > 1:
		name = spl[0]
		value = spl[1]
		print(ind,name,value,len(spl),"%02x"%(len(buf)-len(" ".join(spl))),"%d%%"%(100-100*len(" ".join(spl))/len(buf))) 
		ind += 1
		spl.remove(name)
		spl.remove(value)
		flag = 0
		if name[3] == "s":
			print("STR",name)
			vlen = struct.unpack(">H",value[:2])[0]*2
			while vlen > len(value[2:]):
				rval = spl[0]
				value += "{"+rval
				spl.remove(rval)
				flag = 1
		if "}" in value:
			pos = value.find("}")
			v = ""
			if name[3] == "s":
				v = value[2:pos+flag].decode('utf-16-be')
			elif len(value[:pos]):
				v = str(value[:pos])
			add_pgiter(page,"%s [%s]"%(name,v),"mk*s","",value[:pos+flag],parent)
			if not flag:
				if pos+1 < len(value):
					cnt = value.count("}")
					if cnt > 1:
						for i in range(cnt-1):
							piters.pop()
						parent = piters[-1]
					spl.insert(0,value[pos+cnt:])
				else:
					parent = piters.pop()
		else:
			parent = add_pgiter(page,name,"mk*s","","",parent)
			spl.insert(0,value)
			piters.append(parent)

def open (page, buf, parent=None):
	if buf[:8] != "\x89PNG\x0d\x0a\x1a\x0a":
		print('No PNG signature')
		return
	if parent:
		page.model.set_value(parent,1,("escher","odraw","Blip"))
	add_pgiter(page,"Signature","png","sig",buf[:8],parent)
	off = 8
	while off < len(buf):
		chlen = struct.unpack(">I",buf[off:off+4])[0]
		chtype = buf[off+4:off+8]
		off += 8
		chdata = buf[off:off+chlen]
		off += chlen
		chcrc = struct.unpack(">I",buf[off:off+4])[0]
		off += 4
		chiter = add_pgiter(page,chtype,"png",chtype,buf[off-12-chlen:off],parent)
		if chtype[0] > 0x60: # private chunk
			zipoff = -1
			if (len(chdata) > 12 and chdata[0] == '\x78'):
				zipoff = 0
			elif (chdata[:4] == "\xfa\xce\xca\xfe" and len(chdata) > 0x4c and chdata[0x4c] == '\x78'): 
				zipoff = 0x4c
			# probably deflated
			if zipoff > -1:
				try:
					decobj = zlib.decompressobj()
					output = decobj.decompress(chdata[zipoff:])
					add_pgiter (page,"[Decompressed data]","",0,output,chiter)
					tail = decobj.unused_data
					if len(tail) > 0:
						add_pgiter (page,"[Tail]","",0,tail,chiter)
				except:
					print("Failed to decompress")

