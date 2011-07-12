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
import gtk,gsf
import tree
import hexdump
import inflate
import vsdchunks,vsdstream4
import oleparse

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


def parse (page, data, parent):
		ver_offset = 0x1a
		size_offset = 0x1c
		trlr_offset = 0x24

		version = ord(data[ver_offset])
		page.hd.version = version
		print "Version: %d"%version
		print "Size: %02x"%struct.unpack("<I",data[size_offset:size_offset+4])[0]

		model = page.model
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
		model.set_value(iter2,1,0)
		model.set_value(iter2,2,len(res))
		model.set_value(iter2,3,res)
		model.set_value(iter2,6,model.get_string_from_iter(iter2))
		model.set_value(iter2,5,"#96afcf")

		ptr_search (page, data, version, iter1)

def ptr_search (page, data, version, parent):
#	try:
		# ver 6 and up for now
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
		[offset] = struct.unpack ('<L', pdata[shift:shift+4])
		if offset >= len(pdata):
			return 0
		[num] =  struct.unpack ('<L', pdata[offset+shift:offset+shift+4])
		offset = offset+8+shift

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
			  if streamtype.has_key (pntr.type):
				  idx = " %02x"%childlist
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
				  itername = streamtype[pntr.type]+idx+'\t%04x'%(pntr.length)
				  name2 = streamtype[pntr.type]
			  else:
				  childlist +=1
  
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
					model.set_value(iter2,1,0)
				  model.set_value(iter2,2,len(res))
				  model.set_value(iter2,3,res)
				  model.set_value(iter2,6,model.get_string_from_iter(iter2))
				  model.set_value(iter2,5,"#96afcf")
				  if vbaflag == 1:
					vbadata += res[4:len(res)]
  #			print "ptr type/fmt %02x %02x"%(pntr.type,pntr.format)
  
			  if (pntr.format>>4 == 5 and pntr.type != 0x16) or pntr.type == 0x40:
				  ptr_search (page, data, version, iter1)
			  
			  if pntr.type == 0x16:
				  get_colors (page, res, version, iter1)
			  if pntr.format >>4 == 0xd:
				  vsdchunks.parse (model, version, iter1, pntr)
		if vbaflag == 1:
		  src = gsf.InputMemory(vbadata,False)
		  oleparse.open (src, page, parent)

  
#	except:
#		print "Failed at ptr_search"

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
		model.set (iter1, 0, txt,1,0,2,4,3,data[8+i*4:12+i*4],5,clr,6,model.get_string_from_iter(iter1))

def getnames(doc, niter):
##    print 'Names were found...',doc.model.iter_n_children(niter)
    names = doc.names
    for i in range(doc.model.iter_n_children(niter)):
            nameiter = doc.model.iter_nth_child(niter, i)
            npntr = doc.model.get_value(nameiter,0)["pointer"]
            nitername = doc.model.get_value(nameiter,0)["name"]
            shift = 4
            if npntr.format&2 == 2 : #compressed
                shift = 8
            if doc.version == 6:
                name = unicode(npntr.data[shift:],'cp1251').encode('utf-8')  ## FIXME! have to check locale in the file
            if doc.version == 11:
                name = unicode(npntr.data[shift:],'utf-16').encode('utf-8')
            cntr = name.find('\00')
            names[i] = name[0:cntr]
##            print 'Name: ',i,name
            nitername = nitername + '   \t'+name
            doc.model.set_value(nameiter,1,nitername)
