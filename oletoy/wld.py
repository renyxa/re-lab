# Copyright (C) 2007,2010-2012	Valek Filippov (frob@df.ru)
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

import sys,struct,gtk,gobject
import cdr
from utils import *

def t2chn (hd, size, data):
	add_iter (hd,"Size","0x%02x"%struct.unpack('<I', data[0:4])[0],0,4,"<I")
	l_type = ord(data[0x20])
	l_off = struct.unpack('<H', data[0x21:0x23])[0]+4
	o_off = struct.unpack('<H', data[0x23:0x25])[0]+4
	f_off = struct.unpack('<H', data[0x25:0x27])[0]+4
	add_iter (hd,"Type","0x%02x (%s)"%(l_type,key2txt(l_type,cdr.loda_types_v3)),0x20,1,"B")
	add_iter (hd,"Offsets","0x%02x/0x%02x/0x%02x"%(l_off,o_off,f_off),0x21,6,"<HHH")
	cdr.loda_type_func[0xa](hd,data,o_off,"",38)
	cdr.loda_type_func[0x14](hd,data,f_off,"",31)
	cdr.loda_type_func[0x1e](hd,data,l_off,l_type,len(data)-l_off)

wld_ids = {
	"t2chn":t2chn,
	}

off_names = {
	0:"mcfg",
	1:"start",
	2:"end",
	3:"type1",
	4:"pattern",
	5:"type2",
	6:"disp",
	7:"dend?",
	11:"type7",
	}

def open(buf,page,parent):
	iter1 = page.model.append(None, None)
	page.model.set_value(iter1, 0, "File")
	page.model.set_value(iter1, 1, 0)
	page.model.set_value(iter1, 2, len(buf))
	page.model.set_value(iter1, 3, buf)

	hiter = add_pgiter(page,"Header","wld","hdr",buf[4:45],iter1)
	offsets = []
	off = 4
	for i in range(7):
		offsets.append(struct.unpack("<I",buf[off+i*4:off+i*4+4])[0])
		offn = key2txt(i,off_names,"OFF %x"%i)
		add_pgiter(page,"%s\t[%04x]"%(offn,offsets[i]),"wld","off",buf[off+i*4:off+i*4+4],hiter)

	flag = ord(buf[32])
	add_pgiter(page,"FLAG [%x]"%flag,"wld","flg",buf[32],hiter)

	off = 33
	for i in range(9):
		offsets.append(struct.unpack("<I",buf[off+i*4:off+i*4+4])[0])
		offn = key2txt(i+7,off_names,"OFF %x"%(i+7))
		add_pgiter(page,"%s\t[%04x]"%(offn,offsets[i+7]),"wld","off",buf[off+i*4:off+i*4+4],hiter)

	add_pgiter(page,"mcfg [%04x]"%offsets[0],"cdr","mcfg",buf[offsets[0]:offsets[1]],iter1)
	diter = add_pgiter(page,"data [%04x]"%offsets[1],"cdr2","rec",buf[offsets[1]:offsets[2]],iter1)
	
	try:
		t1_len = struct.unpack("<H",buf[offsets[3]:offsets[3]+2])[0]
		t1_size = 2+9*t1_len
		t1iter = add_pgiter(page,"type1 [%04x]"%offsets[3],"wld","type",buf[offsets[3]:offsets[3]+t1_size],iter1)
		t1diter = add_pgiter(page,"type1","wld","","",diter)
		for i in range(t1_len):
			t = ord(buf[offsets[3]+i*9+2])  # +2 for num of records
			dw1 = struct.unpack("<I",buf[offsets[3]+i*9+3:offsets[3]+i*9+7])[0]
			dw2 = struct.unpack("<I",buf[offsets[3]+i*9+7:offsets[3]+i*9+11])[0]
			add_pgiter(page,"%d [%04x] [%04x/%04x]"%(t,dw1,dw2,dw2-offsets[1]),"wld","t1rec",buf[offsets[3]+i*9+2:offsets[3]+i*9+11],t1iter)
			# chunk "data"
			rlen = struct.unpack("<I",buf[dw2:dw2+4])[0]+4
			id1 = struct.unpack("<H",buf[dw2+4:dw2+6])[0]
			id2 = struct.unpack("<H",buf[dw2+6:dw2+8])[0]
			id3 = struct.unpack("<H",buf[dw2+8:dw2+10])[0]
			id4 = struct.unpack("<H",buf[dw2+10:dw2+12])[0]
			
			if t == 2:
				add_pgiter(page,"%d [%04x] %04x %04x %04x %04x (%04x)"%(t,dw1,id1,id2,id3,id4,dw2),"wld","t2chn",buf[dw2:dw2+rlen],t1diter)
			elif t == 4:
				add_pgiter(page,"%d [%04x] %04x %04x %04x %04x (%04x)"%(t,dw1,id1,id2,id3,id4,dw2),"wld","t4chn","",t1diter)
			else:
				add_pgiter(page,"%d [%04x] %04x %04x %04x %04x (%04x)"%(t,dw1,id1,id2,id3,id4,dw2),"wld","t1chn",buf[dw2:dw2+rlen],t1diter)
	except:
		print "Something failed in type1"

	try:
		if offsets[4] > 0:
			patt_num = struct.unpack("<H",buf[offsets[4]:offsets[4]+2])[0]
			patt_iter = add_pgiter(page,"patterns [%04x]"%offsets[4],"wld","",buf[offsets[4]:offsets[4]+2+patt_num*154],iter1)
			for i in range(patt_num):
				pattid = buf[offsets[4]+2+i*154:offsets[4]+6+i*154]
				add_pgiter(page,"patt %d [id: %s]"%(i,d2hex(pattid)),"wld","patt",buf[offsets[4]+2+i*154:offsets[4]+156+i*154],patt_iter)
	except:
		print "Something failed in patterns"

	
	try:
		t2_len = struct.unpack("<H",buf[offsets[5]:offsets[5]+2])[0]
		t2_size = 2+9*t2_len
		t2iter = add_pgiter(page,"type2 [%04x]"%offsets[5],"wld","type",buf[offsets[5]:offsets[5]+t2_size],iter1)
		t2diter = add_pgiter(page,"type2","wld","","",diter)
		for i in range(t2_len):
			t = ord(buf[offsets[5]+i*9+2])
			dw1 = struct.unpack("<I",buf[offsets[5]+i*9+3:offsets[5]+i*9+7])[0]
			dw2 = struct.unpack("<I",buf[offsets[5]+i*9+7:offsets[5]+i*9+11])[0]
			add_pgiter(page,"%d [%04x] [%04x/%04x]"%(t,dw1,dw2,dw2-offsets[1]),"wld","t1rec",buf[offsets[5]+i*9+2:offsets[5]+i*9+11],t2iter)
			# chunk "data"
			rlen = struct.unpack("<I",buf[dw2:dw2+4])[0]+4
			add_pgiter(page,"%d [%04x] [%04x/%04x]"%(t,dw1,dw2,dw2-offsets[1]),"wld","t2chn",buf[dw2:dw2+rlen],t2diter)
	except:
		print "Something failed in type2"
	
	add_pgiter(page,"disp [%04x]"%offsets[6],"wld","disp",buf[offsets[6]:offsets[7]],iter1)
	
	try:
		t7_len = struct.unpack("<H",buf[offsets[11]:offsets[11]+2])[0]
		t7_size = 2+9*t7_len
		t7iter = add_pgiter(page,"type7 [%04x]"%offsets[11],"wld","type",buf[offsets[11]:offsets[11]+t7_size],iter1)
		t7diter = add_pgiter(page,"type7","wld","","",diter)
		for i in range(t7_len):
			t = ord(buf[offsets[11]+i*9+2])
			dw1 = struct.unpack("<I",buf[offsets[11]+i*9+3:offsets[11]+i*9+7])[0]
			dw2 = struct.unpack("<I",buf[offsets[11]+i*9+7:offsets[11]+i*9+11])[0]
			print "t7",dw1,"%02x"%dw2
			add_pgiter(page,"%d [%04x] [%04x/%04x]"%(t,dw1,dw2,dw2-offsets[1]),"wld","t1rec",buf[offsets[11]+i*9+2:offsets[11]+i*9+11],t7iter)
			# chunk "data"
			rlen = struct.unpack("<I",buf[dw2:dw2+4])[0]+4
			add_pgiter(page,"%d [%04x] [%04x/%04x]"%(t,dw1,dw2,dw2-offsets[1]),"wld","t7chn",buf[dw2:dw2+rlen],t7diter)

	except:
		print "Something failed in type7"


