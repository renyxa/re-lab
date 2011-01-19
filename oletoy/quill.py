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
import pubblock

def parse_fdpc (model,data,offset,fdpciter):
	[num] = struct.unpack('<H', data[offset:offset+2])
	for i in range (num):
		[toff] = struct.unpack('<I', data[offset+8+i*4:offset+12+i*4])
		[tflag] = struct.unpack('<H', data[offset+8+num*4+i*2:offset+8+2+num*4+i*2])
		iter1 = model.append(fdpciter,None)
		model.set_value(iter1,0,"[%02x] %02x"%(toff,tflag))
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,4)
		model.set_value(iter1,3,data[offset+8+i*4:offset+12+i*4])
		[nlen] = struct.unpack('<I', data[offset+tflag:offset+tflag+4])
		pubblock.parse (model,data[offset+tflag+4:offset+tflag+nlen],iter1,0,0)
	return

def parse_syid (model,data,offset,syiditer,txtiter,j):
	try:
		[num] = struct.unpack('<I', data[offset+4:offset+8])
		i = 0
		for i in range(num):
			[id] = struct.unpack('<I', data[offset+8+i*4:offset+12+i*4])
			iter = model.append(syiditer,None)
			model.set(iter,0,"TXid: %02x"%id,1,0,2,4,3,data[offset+8+i*4:offset+12+i*4])
		return i+j
	except:
		print "Failed in parse_syid"

def parse_stsh (model,data,parent,flag):
	[num] = struct.unpack('<I', data[4:8])
	[off1] = struct.unpack('<I', data[20:24])
	i = 1
	while off1 < len(data):
		if i == num:
			off2 = len(data)
		else:
			[off2] = struct.unpack('<I', data[20+i*4:24+i*4])
#		print "Offsets: %d %02x %02x"%(i,off1,off2)
		if flag == "1": # and i/2.>i/2:
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"Ch %02x Pr %02x"%(i,struct.unpack("<H",data[20+off1:20+off1+2])[0]))
			model.set_value(iter1,1,0)
			model.set_value(iter1,2,2)
			model.set_value(iter1,3,data[20+off1:20+off1+2])
			[dlen] = struct.unpack('<I', data[20+off1+2:20+off1+6])
			pubblock.parse (model,data[20+off1+6:20+off1+dlen+2],iter1,i)
			off1 += dlen+2
			if off1 < off2:
				iter = model.append(iter1,None)
				model.set_value(iter,0,"Ps")
				model.set_value(iter,1,0)
				model.set_value(iter,2,off2-off1)
				model.set_value(iter,3,data[20+off1:20+off2])
		else:
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"Ch %02x"%i)
			model.set_value(iter1,1,0)
			model.set_value(iter1,2,off2-off1)
			model.set_value(iter1,3,data[20+off1:20+off2])
		off1 = off2
		i += 1

def parse_strs(model,data,parent,txtiter):
	[num] = struct.unpack('<I', data[0:4])
	tstart = 0
	for i in range(num):
		[nlen] = struct.unpack('<I',data[12+i*4:16+i*4])
		iter1 = model.append(txtiter,None)
		model.set_value(iter1,0,"TX %02x length (%02x)"%(i,nlen))
		model.set_value(iter1,1,("global"," ",0xff))
		model.set_value(iter1,2,nlen*2-2)
		model.set_value(iter1,3,model.get_value(txtiter,3)[tstart:tstart+nlen*2-2])
		tstart += nlen*2
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"TX %02x length (0x%02x)"%(i,nlen))
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,4)
		model.set_value(iter1,3,data[12+i*4:16+i*4])

def parse_tcd(model,data,parent,txtiter):
	[num] = struct.unpack('<I', data[0:4])
	for i in range(num+1):
		[nlen] = struct.unpack('<I',data[12+i*4:16+i*4])
		iter1 = model.append(parent,None)
		model.set_value(iter1,0,"TX %02x end offset (0x%02x)"%(i,nlen*2))
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,4)
		model.set_value(iter1,3,data[12+i*4:16+i*4])

def parse_pl(model,data,parent):
	try:
		[num] = struct.unpack('<I', data[0:4])
		off = 12
		for i in range(num):
			[nlen] = struct.unpack('<I',data[off:off+4])
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"PL %02x"%i)
			model.set_value(iter1,1,0)
			model.set_value(iter1,2,nlen)
			model.set_value(iter1,3,data[off:off+nlen])
			pubblock.parse (model,data[off+4:off+nlen],iter1,i)
			off += nlen
	except:
		print "Failed at PL parsing"

def parse_font(model,data,parent):
		[num] = struct.unpack('<I', data[4:8])
		for i in range(num):
			[off] = struct.unpack('<I', data[20+i*4:24+i*4])
			[nlen] = struct.unpack('<H', data[20+off:20+off+2])
			fname = unicode(data[20+off+2:20+off+2+nlen*2],"utf-16")
			[fid] = struct.unpack('<I', data[20+off+2+nlen*2:20+off+2+nlen*2+4])
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"(%02x) %s"%(fid,fname))
			model.set_value(iter1,1,0)
			model.set_value(iter1,2,nlen*2+4)
			model.set_value(iter1,3,data[20+off:20+off+nlen*2+6])

def parse_mcld(model,data,parent):
		[num] = struct.unpack('<I', data[4:8])
		off = num*4 + 8
		for i in range(num):
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"(%02x) %02x"%(i,struct.unpack("<I",data[8+i*4:12+i*4])[0]))
			model.set_value(iter1,1,0)
			model.set_value(iter1,2,4)
			model.set_value(iter1,3,data[8+i*4:12+i*4])
			iter2 = model.append(iter1,None)
			[nlen] = struct.unpack("<I",data[off:off+4])
			model.set_value(iter2,0,"Hdr")
			model.set_value(iter2,1,0)
			model.set_value(iter2,2,nlen)
			model.set_value(iter2,3,data[off:off+nlen])
			pubblock.parse (model,data[off+4:off+nlen],iter2,i,0)
			off += nlen
			[num2] = struct.unpack('<I', data[off:off+4])
			off += 4
			for k in range(num2):
				[nlen2] = struct.unpack('<I', data[off:off+4])
				iter3 = model.append(iter1,None)
				model.set_value(iter3,0,"Ch %02x"%k)
				model.set_value(iter3,1,0)
				model.set_value(iter3,2,nlen2)
				model.set_value(iter3,3,data[off:off+nlen2])
				pubblock.parse (model,data[off+4:off+nlen2],iter3,k,0)
				off += nlen2


def parse (model,data,parent):
	off = 0
	iter1 = model.append(parent,None)
	model.set_value(iter1,0,"Header")
	model.set_value(iter1,1,0)
	model.set_value(iter1,2,32)
	model.set_value(iter1,3,data[off:off+32])
	[ch_num] = struct.unpack('<H', data[off+26:off+28])
	off += 32
	txtiter = None
	txtnum = -1
	txtid = 0
	for i in range(ch_num):
		[doffset] = struct.unpack('<I', data[off+16:off+20])
		[dlen] = struct.unpack('<I', data[off+20:off+24])
		name = data[off+2:off+6]+"/"+data[off+12:off+16]+str(struct.unpack('<H', data[off+6:off+8])[0])+" [%02x:%02x]"%(doffset,doffset+dlen)
		iter1 = model.append(parent,None)
		if name[0:4] == "TEXT":
			txtiter = iter1 # assume for now that I won't have "TEXT/TEXT<num>" with <num> greater than 0
		if name[0:4] == "FDPC" or name[0:4] == "FDPP":
			parse_fdpc (model,data,doffset,iter1) # we can have more than one "FDPC/FDPCx"
		if name[0:4] == "SYID":
			txtid = parse_syid(model,data,doffset,iter1,txtiter,txtid)
		if name[0:4] == "STSH":
			parse_stsh (model,data[doffset:doffset+dlen],iter1,name[9]) #STSH/STSH1 looks slightly different
		if name[0:4] == "STRS":
			parse_strs (model,data[doffset:doffset+dlen],iter1,txtiter)
		if name[0:4] == "TCD ":
			parse_tcd (model,data[doffset:doffset+dlen],iter1,txtiter)
		if name[0:4] == "PL  ":
			parse_pl (model,data[doffset:doffset+dlen],iter1)
		if name[0:4] == "FONT":
			parse_font (model,data[doffset:doffset+dlen],iter1)
		if name[0:4] == "MCLD":
			parse_mcld (model,data[doffset:doffset+dlen],iter1)

		model.set_value(iter1,0,name)
		model.set_value(iter1,1,0)
		model.set_value(iter1,2,dlen)
		model.set_value(iter1,3,data[doffset:doffset+dlen])
		off += 24
