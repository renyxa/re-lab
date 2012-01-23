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
import inflate
import vsdchunks,vsdstream4
import ole
import ctypes
from utils import *

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')

class pointer:
	type = 0
	address = 0
	offset = 0
	length = 0
	format = 0
	shift = 0
	path = '' # here I'm going to store path to TreeStore row with this pointer
	data = '' # here I'm going to store content of suitable part of vsd file

class chunk:
    type = 0    #dword
    IX = 0        #dword
    list = 0   #dword
    length = 0  #dword
    level = 0   #word
    unkn3 = 0   #byte
    data = ''

streamtype = {
	0:'Empty ptr',\
	0x0a:'Prompt    ',0xd:'VBA Project',
	0x14:'Trailer', 0x15:'Page      ', 0x16:'Colors  ',0x18:'Fonts     ',\
	0x1a:'Styles    ',0x1d:'Stencils ', 0x1e:'Stncl Page', 0x1f:'VBA Data Part',\
	0x23:'Icon        ',0x27:'Pages      ',0x29:'Windows   ',0x2a:'Window    ',0x2e:'EventList',\
	0x2f:'EventItem',0x31:'Document',0x32:'NameList',0x33:'Name    ',\
	0x46:'PageSheet        ',0x47:'ShapeType="Group"',0x48:'ShapeType="Shape"', 0x4a:'StyleSheet    ',\
	0x4d:'ShapeType="Guide"',0x4e:'ShapeType="Foreign"',0x4f:'DocSheet',
	0xc9:'NameIDX    ',
	0xd1:'SolutionXML',
	0xd7:'FontFace',0xd8:'FontFaces'}

def hdr (hd, data):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Sig", 1, data[0:0x12],2,0,3,0x12,4,"txt")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Version", 1, "%d"%ord(data[0x1a]),2,0x1a,3,1,4,"<B")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "Size", 1, "0x%02x"%struct.unpack("<I",data[0x1c:0x20]),2,0x1c,3,4,4,"<I")

def parse (page, data, parent):
		ver_offset = 0x1a
		size_offset = 0x1c
		trlr_offset = 0x24

		model = page.model
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Header")
		model.set_value(iter1,1,("vsd","hdr"))
		model.set_value(iter1,2,0x24)
		model.set_value(iter1,3,data[0:0x24])
		model.set_value(iter1,6,model.get_string_from_iter(iter1))

		version = ord(data[ver_offset])
		page.version = version
		print "Version: %d"%version
		print "Size: %02x"%struct.unpack("<I",data[size_offset:size_offset+4])[0]
		if version > 6:
		  lenhdr2 = 74
		else:
		  lenhdr2 = 4  
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Header part2")
		model.set_value(iter1,1,("vsd","hdr2"))
		model.set_value(iter1,2,0x36)
		model.set_value(iter1,3,data[0x36:0x36+lenhdr2])
		model.set_value(iter1,6,model.get_string_from_iter(iter1))

		
		tr_pntr = pointer()
		if version < 6:
			pdata = data[trlr_offset:trlr_offset+16]
			plen = 16
			[tr_pntr.type] = struct.unpack('<h', pdata[0:2])
			[tr_pntr.format] = struct.unpack('<h', pdata[2:4])
			[tr_pntr.address] = struct.unpack('<L', pdata[4:8])
			[tr_pntr.offset] = struct.unpack('<L', pdata[8:12])
			[tr_pntr.length] = struct.unpack('<L', pdata[12:16])
		else:
			pdata = data[trlr_offset:trlr_offset+18]
			plen = 18
			[tr_pntr.type] = struct.unpack('<L', pdata[0:4])
			[tr_pntr.address] = struct.unpack('<L', pdata[4:8])
			[tr_pntr.offset] = struct.unpack('<L', pdata[8:12])
			[tr_pntr.length] = struct.unpack('<L', pdata[12:16])
			[tr_pntr.format] = struct.unpack('<h', pdata[16:18])

		if tr_pntr.format&2 == 2 : #compressed
			res = inflate.inflate(tr_pntr, data)
			tr_pntr.shift = 4
		else:
			res = data[tr_pntr.offset:tr_pntr.offset+tr_pntr.length]
			tr_pntr.shift = 0
		tr_pntr.data = res
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"Trailer\t\t  %04x\t"%(tr_pntr.length))
		model.set_value(iter1,1,("vsd","pntr",tr_pntr.type))
		model.set_value(iter1,2,plen)
		model.set_value(iter1,3,pdata)
		model.set_value(iter1,4,tr_pntr)
		model.set_value(iter1,6,model.get_string_from_iter(iter1))
		if tr_pntr.format != 0:
			model.set_value(iter1,7,"%02x"%tr_pntr.format)

		iter2 = model.append(iter1,None)
		model.set_value(iter2,0,"[Data referenced by trailer]")
		model.set_value(iter2,1,("vsd","str5"))
		model.set_value(iter2,2,len(res))
		model.set_value(iter2,3,res)
		model.set_value(iter2,6,model.get_string_from_iter(iter2))
		model.set_value(iter2,5,"#96dfcf")

		try:
		  ptr_search (page, data, version, iter1)
		except:
		  print "ptr_search failed in trailer"
		  
def ptr_search (page, data, version, parent):
	model = page.model
	namelist = 0
	fontlist = 0
	childlist = 0
	ptr = model.get_value (parent,4)
	shift = ptr.shift
	pdata = ptr.data
	vbaflag = 0
	if ptr.type == 0xd:
	  vbaflag = 1
	  vbadata = ""
	if version > 5:
		[offset] = struct.unpack ('<L', pdata[shift:shift+4])
		if offset >= len(pdata):
			return 0
		num =  struct.unpack ('<L', pdata[offset+shift:offset+shift+4])[0]
		offset = offset+8+shift
	else:
		num = struct.unpack ('<H', pdata[0xa+shift:0xa+shift+2])[0]
		offset = 0xa+shift+2
		if ptr.type == 0x14:
			num = struct.unpack ('<H', pdata[0x82+shift:0x82+shift+2])[0]
			offset = 0x82+shift+2
		if ptr.type == 0x1d:
			num = struct.unpack ('<H', pdata[0x1e+shift:0x1e+shift+2])[0]
			offset = 0x1e+shift+2
		if ptr.type == 0x1e:
			num = struct.unpack ('<H', pdata[0x36+shift:0x36+shift+2])[0]
			offset = 0x36+shift+2

	for i in range(num):
		pntr = pointer()
		if version < 6:
			plen = 16
			npdata = pdata[offset+i*plen:offset+i*plen+16]
			[pntr.type] = struct.unpack ('<h', npdata[0:2])
			[pntr.format] = struct.unpack ('<h', npdata[2:4])
			[pntr.address] = struct.unpack ('<L', npdata[4:8])
			[pntr.offset] = struct.unpack ('<L', npdata[8:12])
			[pntr.length] = struct.unpack ('<L', npdata[12:16])
		else:
			plen = 18
			npdata = pdata[offset+i*plen:offset+i*plen+18]
			[pntr.type] = struct.unpack ('<L', npdata[0:4])
			[pntr.address] = struct.unpack ('<L', npdata[4:8])
			[pntr.offset] = struct.unpack ('<L', npdata[8:12])
			[pntr.length] = struct.unpack ('<L', npdata[12:16])
			[pntr.format] = struct.unpack ('<h', npdata[16:18])
		itername = '%02x\t %02x\t%04x'%(pntr.type,childlist,pntr.length)
		name2 = "%02x"%pntr.type
		if pntr.type == 0:
			namelist += 1
			fontlist += 1
			childlist +=1
		else:
		  idx = " %02x"%childlist
		  if streamtype.has_key (pntr.type):
			  if pntr.type == 0x33:
				idx = "%02x"%namelist
				namelist += 1
			  else:
				if pntr.type == 0xd7:
				  idx = " %02x"%fontlist
				  fontlist += 1
				else:
				  idx = " %02x"%childlist
				  childlist +=1
			  if (pntr.type == 0x15 and pntr.format&1 == 0):
				itername = "Page BG   "+idx+'\t%04x'%(pntr.length)
			  else:
			    itername = streamtype[pntr.type]+idx+'\t%04x'%(pntr.length)
			  name2 = streamtype[pntr.type]
		  else:
			  childlist +=1
			  if vsdchunks.chunktype.has_key(pntr.type):
				itername = vsdchunks.chunktype[pntr.type]+idx+'\t%04x'%(pntr.length)

		  if pntr.format&2 == 2 : #compressed
			  res = inflate.inflate(pntr, data)
			  pntr.shift = 4
		  else:
			  res = data[pntr.offset:pntr.offset+pntr.length]
			  pntr.shift = 0
		  pntr.data = res
		  iter1 = model.append(parent,None)
		  model.set_value(iter1,0,itername)
		  model.set_value(iter1,1,("vsd","pntr",pntr.type))
		  model.set_value(iter1,2,plen)
		  model.set_value(iter1,3,npdata)
		  model.set_value(iter1,4,pntr)
		  model.set_value(iter1,6,model.get_string_from_iter(iter1))
		  if pntr.format != 0:
			model.set_value(iter1,7,"%02x"%pntr.format)
		  if len(res) > 0:
			  iter2 = model.append(iter1,None)
			  model.set_value(iter2,0,"[Data referenced by %s]"%name2)
			  if pntr.format >>4 == 4:
				model.set_value(iter2,1,("vsd","str4",pntr.type))
			  else:
				model.set_value(iter2,1,("vsd","str"))
			  model.set_value(iter2,2,len(res))
			  model.set_value(iter2,3,res)
			  model.set_value(iter2,6,model.get_string_from_iter(iter2))
			  model.set_value(iter2,5,"#96dfcf")
			  if vbaflag == 1:
				vbadata += res[4:len(res)]
  #			print "ptr type/fmt %02x %02x"%(pntr.type,pntr.format)
  
		  if (pntr.format>>4 == 5 and pntr.type != 0x16) or pntr.type == 0x40:
			  if pntr.type == 0x1e:
				model.set_value(iter2,1,("vsd","str4",pntr.type)) # it's not a stream4, but...
			  try:
				ptr_search (page, data, version, iter1)
			  except:
				print "ptr_search failed in %02x"%pntr.type
		  if pntr.type == 0x16:
			  get_colors (page, res, version, iter1)
		  if pntr.format >>4 == 0xd or pntr.format >>4 == 0xc:
			  vsdchunks.parse (model, version, iter1, pntr)
	if vbaflag == 1:
	  ole.open (vbadata, page, parent)

def get_colors (page, data, version, parent):
	model = page.model
	clrnum = ord(data[6])
	for i in range(clrnum):
		r = ord(data[8+i*4])
		g = ord(data[9+i*4])
		b = ord(data[10+i*4])
		a = ord(data[11+i*4])
		iter1 = model.append(parent, None)
		txt = "Color #%02x: %02x%02x%02x %02x"%(i,r,g,b,a)
		clr = "#%02x%02x%02x"%(r,g,b)
		model.set (iter1, 0, txt,1,("vsd","clr"),2,4,3,data[8+i*4:12+i*4],5,clr,6,model.get_string_from_iter(iter1))

def collect_chunks (model,parent):
  value = ""
  for i in range(model.iter_n_children(parent)):
	citer = model.iter_nth_child(parent,i)
	value += model.get_value(citer,3)
	value += collect_chunks (model,citer)
  return value
  
def collect_strD (model, parent):
  value = ""
  miter = model.iter_nth_child(parent,1)
  if miter != None:
	value += model.get_value(miter,3)
	value += collect_chunks (model,miter)
  else:
	print 'None iter?'
  return value
  

def collect_str5 (model, parent, offset):
  value = ""
  ptr_array = ""
  ptr_count = 0
  
  for i in range(model.iter_n_children(parent)-1):
	citer = model.iter_nth_child(parent,i+1)
	ctype = struct.unpack("<H",model.get_value(citer,3)[16:18])[0]
	if ctype >> 4 == 4:
	  res = model.get_value(model.iter_nth_child(citer,0),3)
	  ptype = model.get_value(citer,3)[0:4]
	  ptr_array += ptype + "\x00"*4+struct.pack("<I",offset)+struct.pack("<I",len(res))+"\x40\x00"
	  ptr_count += 1
	  value += res
	  offset += len(res)
	if ctype >> 4 == 0xd:
	  res = collect_strD (model,citer)
	  ptype = model.get_value(citer,3)[0:4]
	  pfmt = (struct.unpack("<H",model.get_value(citer,3)[16:18])[0])&0xFD
	  ptr_array += ptype + "\x00"*4+struct.pack("<I",offset)+struct.pack("<I",len(res))+struct.pack("<H",pfmt)
	  ptr_count += 1
	  value += res
	  offset += len(res)
	if ctype >> 4 == 0x5:
	  res,rpal = collect_str5 (model,citer,offset)
	  ptype = model.get_value(citer,3)[0:4]
	  pfmt = (struct.unpack("<H",model.get_value(citer,3)[16:18])[0])&0xFD
	  ptr_array += ptype + "\x00"*4+struct.pack("<I",offset+len(res)-rpal)+struct.pack("<I",rpal)+struct.pack("<H",pfmt)
	  ptr_count += 1
	  value += res
	  offset += len(res)
	
  value += "\x18"+"\x00"*23 +struct.pack("<I",ptr_count)+"\x00"*4+ptr_array
  ptrarlen = 32+len(ptr_array)
  return value,ptrarlen

def collect_vd (model, parent):
	hdr = model.get_value(model.iter_nth_child(parent,0),3)[0:0x1c]
	hdr2 = model.get_value(model.iter_nth_child(parent,1),3)
	offset = 0x24+18+len(hdr2)
	trailiter = model.iter_nth_child(parent,2)
	res, ptrarlen = collect_str5 (model, trailiter, offset)
	tr_ptr = '\x14'+'\x00'*7+ struct.pack("<I",0x24+18+len(hdr2)+len(res)-ptrarlen)+struct.pack("<I",ptrarlen)+'\x50\x00'
	value = hdr + struct.pack("<I",len(res)+18+0x24+len(hdr2)) + "\x00\x84\x01\x00" + tr_ptr + hdr2 + res
	return value

def dump_tree (model, parent, outfile):
	ntype = model.get_value(parent,1)
	name = model.get_value(parent,0)
	if name != 'VisioDocument':
	  value = model.get_value(parent,3)
	else: # VisioDocument
	  value = collect_vd (model, parent)

	child = cgsf.gsf_outfile_new_child(outfile,name,0)
	cgsf.gsf_output_write (child,len(value),value)
	cgsf.gsf_output_close (child)

def save (page, fname):
	model = page.view.get_model()
	cgsf.gsf_init()
	output = cgsf.gsf_output_stdio_new (fname)
	outfile = cgsf.gsf_outfile_msole_new (output);
	iter1 = model.get_iter_first()
	while None != iter1:
	  dump_tree(model, iter1, outfile)
	  iter1 = model.iter_next(iter1)
	cgsf.gsf_output_close(outfile)
	cgsf.gsf_shutdown()

