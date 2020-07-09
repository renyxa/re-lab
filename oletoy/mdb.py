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
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from utils import *


def hd_data_hdr(hd,buf):
	offset = 0
	free_space = struct.unpack("<H",buf[offset+2:offset+4])[0]
	tdef = struct.unpack("<I",buf[offset+4:offset+8])[0]
	unkn = struct.unpack("<I",buf[offset+8:offset+12])[0]
	nrows = struct.unpack("<H",buf[offset+12:offset+14])[0]
	add_iter(hd,"Free space",free_space,2,2,"<H")
	add_iter(hd,"Table def",tdef,4,4,"<I")
	add_iter(hd,"Unknown",unkn,8,4,"<I")
	add_iter(hd,"Num rows",nrows,12,2,"<H")

# 0 means not listed in mdbtools
coltypes = {1:("BOOL",1),2:("BYTE",1),3:("INT",2),4:("LONG",4),
	5:("CURRENCY",8),6:("FLOAT",4),7:("DOUBLE",8),8:("SDATETIME",8),
	9:("BINARRAY",255),0xa:("TEXT",255),0xb:("OLE",0),0xc:("MEMO",0),
	0xf:("GUID",0)}

def hd_table(hd,buf):
	offset = 0
	tdef_id = struct.unpack("<H",buf[offset+2:offset+4])[0]
	next_pg = struct.unpack("<I",buf[offset+4:offset+8])[0]
	tdef_len = struct.unpack("<I",buf[offset+8:offset+12])[0]
	unkn1 = struct.unpack("<I",buf[offset+12:offset+16])[0]
	nrows = struct.unpack("<I",buf[offset+16:offset+20])[0]
	autonum = struct.unpack("<I",buf[offset+20:offset+24])[0]
	unkn2 = buf[offset+24:offset+40]
	table_type = ord(buf[offset+40])
	maxcols = struct.unpack("<H",buf[offset+41:offset+43])[0]
	nvarcols = struct.unpack("<H",buf[offset+43:offset+45])[0]
	ncols = struct.unpack("<H",buf[offset+45:offset+47])[0]
	nidx = struct.unpack("<I",buf[offset+47:offset+51])[0]
	nridx = struct.unpack("<I",buf[offset+51:offset+55])[0]
	used_pg = struct.unpack("<I",buf[offset+55:offset+59])[0]
	free_pg = struct.unpack("<I",buf[offset+59:offset+63])[0]
	add_iter(hd,"tdef ID",tdef_id,2,2,"<H")
	add_iter(hd,"Next Page",next_pg,4,4,"<I")
	add_iter(hd,"tdef len",tdef_len,8,4,"<I")
	add_iter(hd,"unkn1",unkn1,12,4,"<I")
	add_iter(hd,"nrows",nrows,16,4,"<I")
	add_iter(hd,"autonum",autonum,20,4,"<I")
	add_iter(hd,"unkn2",unkn2,24,16,"txt")
	add_iter(hd,"Table type",table_type,40,1,"B")
	add_iter(hd,"Max Columns",maxcols,41,2,"<H")
	add_iter(hd,"Num Var Columns",nvarcols,43,2,"<H")
	add_iter(hd,"Num Columns",ncols,45,2,"<H")
	add_iter(hd,"Num IDXs",nidx,47,4,"<I")
	add_iter(hd,"Num real IDXs",nridx,51,4,"<I")
	add_iter(hd,"Used Pages",used_pg,55,4,"<I")
	add_iter(hd,"Free Pages",free_pg,59,4,"<I")
	for i in range(nridx):
		nri_unkn1 = struct.unpack("<I",buf[offset+63+i*12:offset+67+i*12])[0]
		nidxr = struct.unpack("<I",buf[offset+67+i*12:offset+71+i*12])[0]
		nri_unkn2 = struct.unpack("<I",buf[offset+71+i*12:offset+75+i*12])[0]
		add_iter(hd,"Num  IDX Rows??",nidxr,67+i*12,4,"<I")
	offset += i*12

	for i in range(ncols):
		add_iter(hd,"Column %02x"%i,"",offset+75+i*25,0,"txt")
		coltype = ord(buf[offset+75+i*25])
		if coltype in coltypes:
			ctxt = coltypes[coltype][0]
		else:
			ctxt = "%02x"%coltype
		add_iter(hd,"  Column type",ctxt,offset+75+i*25,1,"<B")
		unkn = struct.unpack("<I",buf[offset+76+i*25:offset+80+i*25])[0]
		add_iter(hd,"  Unkn1",unkn,offset+76+i*25,4,"<I")
		colnum = struct.unpack("<H",buf[offset+80+i*25:offset+82+i*25])[0]
		add_iter(hd,"  Column number",colnum,offset+80+i*25,2,"<H")
		offv = struct.unpack("<H",buf[offset+82+i*25:offset+84+i*25])[0]
		add_iter(hd,"  Offset for Varlen Columns",offv,offset+82+i*25,2,"<H")
		colnumwd = struct.unpack("<H",buf[offset+84+i*25:offset+86+i*25])[0]
		add_iter(hd,"  Colnum (with deleted)",colnumwd,offset+84+i*25,2,"<H")
		scale = struct.unpack("<I",buf[offset+86+i*25:offset+90+i*25])[0]
		add_iter(hd,"  LangID??",scale,offset+86+i*25,4,"<I")
		add_iter(hd,"  Bitmask",ord(buf[offset+90+i*25]),offset+90+i*25,1,"B")
		add_iter(hd,"  Unkn2",ord(buf[offset+91+i*25]),offset+91+i*25,1,"B")
		add_iter(hd,"  Unkn3","%02x"%struct.unpack("<I",buf[offset+92+i*25:offset+96+i*25]),offset+92+i*25,4,"<I")
		offf = struct.unpack("<H",buf[offset+96+i*25:offset+98+i*25])[0]
		add_iter(hd,"  Offset for Fixed Columns",offf,offset+96+i*25,2,"<H")
		collen = struct.unpack("<H",buf[offset+98+i*25:offset+100+i*25])[0]
		add_iter(hd,"  Column Length",offf,offset+98+i*25,2,"<H")
	offset += i*25

	for i in range(ncols):
		cnlen = struct.unpack("<H",buf[offset+100:offset+102])[0]
		cname = buf[offset+102:offset+102+cnlen]
		add_iter(hd,"Column NameLen",cnlen,offset+100,2,"<H")
		add_iter(hd,"  Column Name",unicode(cname,"utf16"),offset+102,cnlen,"utxt")
		offset += 2+ cnlen

	for i in range(nridx):
		add_iter(hd,"---- %02x"%i,"",offset+100,0,"txt")
		nri_unkn2 = struct.unpack("<I",buf[offset+100:offset+104])[0]
		add_iter(hd,"nri_unkn2",nri_unkn2,offset+100,4,"<I")
		for j in range(10):
			cnum = struct.unpack("<H",buf[offset+104+j*3:offset+106+j*3])[0]
			corder = ord(buf[offset+106+j*3])
			add_iter(hd," Column Num",cnum,offset+104+j*3,2,"<H")
			add_iter(hd,"  Column Order",corder,offset+106+j*3,1,"B")
		offset += 28
		nri_unkn3 = struct.unpack("<I",buf[offset+106:offset+110])[0]
		add_iter(hd,"nri_unkn3",nri_unkn3,offset+106,4,"<I")
		first_dp = struct.unpack("<I",buf[offset+110:offset+114])[0]
		add_iter(hd,"Data Ptr IDX page",first_dp,offset+110,4,"<I")
		add_iter(hd,"Flags",ord(buf[offset+114]),offset+114,1,"B")
		add_iter(hd,"nri_unkn4","",offset+115,9,"txt")
		offset += 24

	for i in range(nridx):
		add_iter(hd,"---- %02x"%i,"",offset+100,0,"txt")
		nri_unkn5 = struct.unpack("<I",buf[offset+100:offset+104])[0]
		idx_num = struct.unpack("<I",buf[offset+104:offset+108])[0]
		idx_num2 = struct.unpack("<I",buf[offset+108:offset+112])[0]
		nri_unknfrob = ord(buf[offset+112])
		nri_unkn6 = struct.unpack("<I",buf[offset+113:offset+117])[0]
		nri_unkn7 = struct.unpack("<I",buf[offset+117:offset+121])[0]
		nri_unkn8 = struct.unpack("<H",buf[offset+121:offset+123])[0]
		prikey = ord(buf[offset+123])
		nri_unkn9 = struct.unpack("<I",buf[offset+124:offset+128])[0]
		add_iter(hd,"nri_unkn5",nri_unkn5,offset+100,4,"<I")
		add_iter(hd,"Num of Index",idx_num,offset+104,4,"<I")
		add_iter(hd,"Num of Index2",idx_num2,offset+108,4,"<I")
		add_iter(hd,"nri_unknfrob",nri_unknfrob,offset+112,1,"B")
		add_iter(hd,"nri_unkn6",nri_unkn6,offset+113,4,"<I")
		add_iter(hd,"nri_unkn7",nri_unkn7,offset+117,4,"<I")
		add_iter(hd,"nri_unkn8",nri_unkn8,offset+121,2,"<H")
		add_iter(hd,"Primary Key",prikey,offset+123,1,"B")
		add_iter(hd,"nri_unkn9",nri_unkn9,offset+124,4,"<I")
		offset+=28

	for i in range(nridx):
		cnlen = struct.unpack("<H",buf[offset+100:offset+102])[0]
		cname = buf[offset+102:offset+102+cnlen]
		add_iter(hd,"Index NameLen",cnlen,offset+100,2,"<H")
		add_iter(hd,"  Index Name",unicode(cname,"utf16"),offset+102,cnlen,"utxt")
		offset += 2+ cnlen

rec_ids = {"data_hdr":hd_data_hdr, "Table":hd_table}

def db (buf,page,offset,parent):
	iter1 = page.model.append(parent,None)
	page.model.set_value(iter1,0,"Version %d"%(ord(buf[offset+0x14])+3))
	page.model.set_value(iter1,1,("mdb",0x100))
	page.model.set_value(iter1,2,0)
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))

def data (buf,page,offset,parent):
	nrows = struct.unpack("<H",buf[offset+12:offset+14])[0]
	add_pgiter(page,"Header",buf[offset:offset+14+nrows*2],"data_hdr",parent)
	
	firstrow = struct.unpack("<H",buf[offset+12+nrows*2:offset+14+nrows*2])[0]
	if firstrow < 0x1000 and 16+nrows*2 < firstrow:
		add_pgiter(page,"Neck",buf[offset+16+nrows*2:offset+firstrow],"data_neck",parent)
	recend = 0x1000
	for i in range(nrows):
		recoff = struct.unpack("<H",buf[offset+14+i*2:offset+16+i*2])[0]
		if recoff < 0x1000:
			add_pgiter(page,"Record %02x"%i,buf[offset+recoff:offset+recend],"data_rec",parent)
		else:
			add_pgiter(page,"Record %02x"%i,"","data_rec",parent)
		recend = recoff # could be a problem with >0x1000 recoff

def table (buf,page,offset,parent):
	pass

def int_idx (buf,page,offset,parent):
	pass

def leaf_idx (buf,page,offset,parent):
	pass

def usage_bmp (buf,page,offset,parent):
	pass


block_types = {0x100:('DB',db),0x101:('Data',data),0x102:('Table',table),0x103:('IntMed IDX',int_idx),
	0x104:('Leaf IDX',leaf_idx),0x105:('Pg Usage Bitmaps',usage_bmp)}

def parse (buf,page,parent):
	offset = 0
	i = 0
	while offset < len(buf):
		iter1 = page.model.append(parent,None)
		page.model.set_value(iter1,0,"Block %02x"%i)
		page.model.set_value(iter1,1,("mdb",0))
		page.model.set_value(iter1,2,0x1000)
		page.model.set_value(iter1,3,buf[offset:offset+0x1000])
		bt = struct.unpack("<H",buf[offset:offset+2])[0]
		if bt in block_types:
			bts = block_types[bt][0]
			page.model.set_value(iter1,1,("mdb",bts))
			block_types[bt][1](buf,page,offset,iter1)
		else:
			bts = "  %02x"%bt
		page.model.set_value(iter1,7,bts)
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += 0x1000
		i += 1
