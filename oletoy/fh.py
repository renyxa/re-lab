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

import sys,struct,tree,zlib,fhparse,gtk,gobject
from utils import *

ver = {0x31:5,0x32:7,0x33:8,0x34:9,0x35:10,0x36:11,'mcl':-1}

def fh_save (page, fname):
	model = page.view.get_model()
	f = open(fname,'w')
	endptr = 0
	iter1 = model.get_iter_first()
	iter1 = model.iter_next(iter1) # 'FH Header'
	value = model.get_value(iter1,3)
	f.write(value[:len(value)-4])
	epos = len(value)-16
#	endptr += len(value)-4
	iter2 = model.iter_next(iter1) # 'FH Decompressed data'
	value = ''
	clist = {}
	for i in range(model.iter_n_children(iter2)-1):
		citer = model.iter_nth_child(iter2,i)
		value += model.get_value(citer,3)
		rname = model.get_value(citer,0)
		clist[i] = rname[0:len(rname)-5]

	citer = model.iter_nth_child(iter2,i+1) # 'FH Tail'
	value += model.get_value(citer,3)
	output = zlib.compress(value,1)
	clen = struct.pack(">L",len(output)+12)

	f.write(clen)
	f.write(output)
	endptr += 4 + len(output) + 8
	
	dictsize = struct.pack('>h', len(page.dict))
	f.write(dictsize)
	f.write('\x02\x04') # points to some random record ID?
	endptr += 4
	cntlist = {}
#	for k, v in page.dict.items():  # not sure if FH pays attention to dict items sequence
#		f.write(struct.pack('>h',k))
#		f.write(v[0])
#		f.write('\x00')
#		cntlist[v[0]] = k
#		endptr += 3 + len(v[0])
	iter3 = model.iter_next(iter2) # 'FH Dictionary'
	for i in range(model.iter_n_children(iter3)):
		citer = model.iter_nth_child(iter3,i)
		value = model.get_value(citer,3)
		k = value[0:2]
		v = value[2:]
		f.write(k)
		f.write(v)
		v = v[:(len(v)-1)]
		cntlist[v] = k
		endptr += 3 + len(v)

	size = struct.pack('>L', model.iter_n_children(iter2)-1) # don't count tail
	f.write(size)
	endptr += 4
	for i in range(len(clist)):
		v = cntlist[clist[i]]
		f.write(v)
	endptr += len(clist)*2
	f.write('FlateDecode\x00\xFF\xFF\xFF\xFF\x1c\x09\x0a\x00\x04')
	endptr += 16
	f.write(struct.pack(">L",endptr))
	f.seek(epos)
	f.write(struct.pack(">L",endptr))
	f.close()


def fh_open (buf,page,parent=None):
	piter = add_pgiter(page,"FH file","fh","file",buf,parent)
	page.dictmod = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING)
	offset = buf.find('AGD')
	page.version = ver[ord(buf[offset+3])]
	size = struct.unpack('>L', buf[offset+8:offset+12])[0]
	print 'Version:\t',page.version
	print 'Offset: \t%x'%offset
	print 'Size:\t\t%x'%size
	add_pgiter(page,"FH Header","fh","header",buf[:offset+12],piter)

	if page.version > 8:
		output = zlib.decompress(buf[offset+14:offset+14+size],-15)
	else:
		output = buf[offset+12:offset+size]

	doc = fhparse.FHDoc(output,page,piter)
	offset = offset + size
	offset = doc.parse_dict(buf,offset)
	doc.parse_list(buf,offset)
	doc.parse_agd()


def v8dict(buf,offset,parent,page):
	dictsize = struct.unpack('>h', buf[offset:offset+2])[0]
	lastkey = struct.unpack('>h', buf[offset+2:offset+4])[0]
	offset += 4
	print 'Dict size:\t%u, Last record: %04x'%(dictsize,lastkey)
	flag = 0
	keypaths = {"":None}
	items = {}
	for i in range(dictsize):
		key = struct.unpack('>h', buf[offset:offset+2])[0]
		key2 = struct.unpack('>h', buf[offset+2:offset+4])[0]
		offset += 4
		k = 0
		while ord(buf[offset+k]) != 0:
			k+=1
		value = buf[offset:offset+k]
		offset += k+1
		k = 0
		while flag != 2:
			while ord(buf[offset+k]) != 0:
				k+=1
			flag += 1
			k+=1
		flag = 0
		unkn = buf[offset:offset+k]
		offset+=k
		niter = page.model.append(parent,None)
		page.model.set_value(niter,0,"%04x %s"%(key,value))
		page.model.set_value(niter,1,("fh","dval"))
		page.model.set_value(niter,2,len(value)+len(unkn)+4)
		page.model.set_value(niter,3,buf[offset-len(value)-len(unkn)-5:offset])
		page.model.set_value(niter,6,page.model.get_string_from_iter(niter))


		items[key] = (value,unkn)
		piter = None
		if keypaths.has_key(key2):
			piter = keypaths[key2]
		d_iter = page.dictmod.append(piter,None)
		keypaths[key] = d_iter
		page.dictmod.set_value(d_iter,0,"%04x"%key)
		page.dictmod.set_value(d_iter,1,value)
		page.dictmod.set_value(d_iter,2,d2hex(unkn))

	return offset,items
