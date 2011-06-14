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
#

import sys,struct
import gobject
import gtk
import tree
import hexdump
import inflate
import vsdchunks

class pointer:
	type = 0
	address = 0
	offset = 0
	length = 0
	format = 0
	shift = 0
	path = '' # here I'm going to store path to TreeStore row with this pointer
	data = '' # here I'm going to store content of suitable part of vsd file


streamtype = {
	0:'Empty ptr',\
	0x14:'Trailer', 0x15:'Page    ', 0x16:'Colors  ',0x18:'Fonts   ',0x1a:'Styles  ',0x1d:'Stencils', 0x1e:'Stncl Pg',\
	0x23:'Icon    ',0x27:'Pages   ',0x29:'Windows ',0x2a:'Window  ',0x2e:'EventList',0x2f:'EventItem',\
	0x31:'Document',0x32:'NameList',0x33:'Name    ',\
	0xd7:'FontFace',0xd8:'FontFaces'}


def parse (model, data, parent):
		ver_offset = 0x1a
		size_offset = 0x1c
		trlr_offset = 0x24

		version = ord(data[ver_offset])
		print "Version: %d"%version
		print "Size: %02x"%struct.unpack("<I",data[size_offset:size_offset+4])[0]

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
		model.set_value(iter1,0,"Trailer\t\t  %08x\t  %04x\t  %04x\t  %02x\t"%(tr_pntr.address,tr_pntr.offset,tr_pntr.length,tr_pntr.format))
		model.set_value(iter1,1,("vsd","pntr",tr_pntr.type))
		model.set_value(iter1,2,plen)
		model.set_value(iter1,3,pdata)
		model.set_value(iter1,4,tr_pntr)

		iter2 = model.append(iter1,None)
		model.set_value(iter2,0,"<Data referenced by trailer>")
		model.set_value(iter2,1,0)
		model.set_value(iter2,2,len(res))
		model.set_value(iter2,3,res)

		ptr_search (model, data, version, iter1)

def ptr_search (model, data, version, parent):
#	try:
		# ver 6 and up for now
		namelist = 0
		fontlist = 0
		ptr = model.get_value (parent,4)
		shift = ptr.shift
		pdata = ptr.data
		
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

			itername = '%02x       \t%08x\t%04x\t%04x\t%02x'%(pntr.type,pntr.address,pntr.offset,pntr.length,pntr.format)
			name2 = "%02x"%pntr.type
			if streamtype.has_key (pntr.type):
				
				idx = ""
				if pntr.type == 0x33:
				  idx = "%02x"%namelist
				  namelist += 1
				if pntr.type == 0xd7:
				  idx = " %02x"%fontlist
				  fontlist += 1
				itername = streamtype[pntr.type]+idx+'\t%08x\t%04x\t%04x\t%02x'%(pntr.address,pntr.offset,pntr.length,pntr.format)
				name2 = streamtype[pntr.type]
			else:
				if vsdchunks.chunktype.has_key(pntr.type):
					itername = vsdchunks.chunktype[pntr.type]+'\t%08x\t%04x\t%04x\t%02x'%(pntr.address,pntr.offset,pntr.length,pntr.format)

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

			if len(res) > 0:
				iter2 = model.append(iter1,None)
				model.set_value(iter2,0,"<Data referenced by %s>"%name2)
				model.set_value(iter2,1,0)
				model.set_value(iter2,2,len(res))
				model.set_value(iter2,3,res)

#			print "ptr type/fmt %02x %02x"%(pntr.type,pntr.format)

			if (pntr.format>>4 == 5 and pntr.type != 0x16) or pntr.type == 0x40:
				ptr_search (model, data, version, iter1)
				
			if pntr.format >>4 == 0xd:
				vsdchunks.parse (model, version, iter1, pntr)
#	except:
#		print "Failed at ptr_search"

def getcolors(doc,citer):
##    print 'Color entries were found.'
    colors = doc.colors
    pntr = doc.model.get_value(citer,0)["pointer"]
    res = pntr.data
    clrnum = ord(res[6])
    for i in range(clrnum):
        clr = vsdoc.color()
        clr.r = ord(res[8+i*4])
        clr.g = ord(res[9+i*4])
        clr.b = ord(res[10+i*4])
        clr.a = 0
        colors.append(clr)
## small addition for Colors
        cpntr = vsdoc.pointer()
        iter = doc.model.append(pntr.path,(cpntr,'Colors'))
        itername = 'Color: %02x'%i+'\tRGB: #%02x%02x%02x'%(clr.r,clr.g,clr.b) 
        folder = { "name": itername, "pointer": cpntr }
        doc.model.set_value(iter, 0, folder)
        doc.model.set_value(iter, 1, folder["name"])
        cpntr.path = iter
        cpntr.data = res[8+i*4:11+i*4]
        
    for i in range(len(colors)):
        clr = colors[i]
##        print ' IX=%u  RGB=#%02x%02x%02x'%(i, clr.r,clr.g,clr.b)

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

def getfonts(doc,iter):
##    print 'Font entries were found...'
    fonts = doc.fonts
    pntr = doc.model.get_value(iter,0)["pointer"]
    # for Visio 2k/2k2 this pntr.data is type D stream (made of chunks)
    # for Visio 2k3 this pntr->children are FontEntries
    if doc.version == 6:
        chunks.chunk_parse(doc,pntr)
        fiter = doc.model.iter_nth_child(iter, 0)
        for i in range(doc.model.iter_n_children(fiter)):
            fntiter = doc.model.iter_nth_child(fiter, i)
            fpntr = doc.model.get_value(fntiter,0)["pointer"]
            fitername = doc.model.get_value(fntiter,0)["name"]
            fname = fpntr.data[25:len(fpntr.data)]
            [fn] = struct.unpack('<h',fpntr.data[4:6])
            cntr = fname.find('\00')
            fonts[fn] = fname[0:cntr]
            fitername = fitername + '   \t'+fname
            doc.model.set_value(fntiter,1,fitername)

    if doc.version == 11: ## check for font substitution
        num = 0
        fiter = doc.model.iter_nth_child(iter, 0)
        for i in range(doc.model.iter_n_children(fiter)):
            fntiter = doc.model.iter_nth_child(fiter, i)
            fpntr = doc.model.get_value(fntiter,0)["pointer"]
            fname = unicode(fpntr.data[8:72],'utf-16').encode('utf-8')
            cntr = fname.find('\00')
            fonts[i] = fname[0:cntr]
            fitername = fitername + '   \t'+fname
            doc.model.set_value(fntiter,1,fitername)
            print 'Font ID: %u'%(i),' Font name: ',fname[0:cntr]

        for i in range(doc.model.iter_n_children(iter)):
            child = doc.model.iter_nth_child(iter,i)        
            childptr = doc.model.get_value(child,0)["pointer"]
            if childptr.type == 0x3f:
            # looking for font idx substitution
                fidx = doc.model.iter_nth_child(doc.model.iter_nth_child(child,0),1)
                fidxpntr = doc.model.get_value(fidx,0)["pointer"]
                print 'Found fidxptr! T/A/O/L/F: %02x \t%07x \t%04x \t%04x \t%02x'%(fidxpntr.type,fidxpntr.address,fidxpntr.offset,fidxpntr.length,fidxpntr.format)
                print 'Data length: ',len(fidxpntr.data)
                length = len(fidxpntr.data)
                if length > 10:
                    [f]= struct.unpack('<L',fidxpntr.data[10:14])
                    if f > 4:
                        shift = 10
                    else:
                        shift = 14
                    for i in range((length-shift)/4):
                        [fn] = struct.unpack('<L',fidxpntr.data[shift+i*4:shift+i*4+4])
##                        print 'Substitution (fn/length/i): ', fn,length,i
                        doc.fonts[fn] = doc.fonts[length+i]



