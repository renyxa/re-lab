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

import sys,struct,gtk
from utils import *

def open (buf,page,parent):
	offset = 2
	cnt = struct.unpack('<H', buf[offset:offset+2])[0]
	iter1 = page.model.append(parent,None)
	page.model.set_value(iter1,0,"CLP_Header")
	page.model.set_value(iter1,1,("clp",0))
	page.model.set_value(iter1,2,4)
	page.model.set_value(iter1,3,buf[0:4])
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	offset += 2
	
	for i in range(cnt):
		iter1 = page.model.append(parent,None)
		page.model.set_value(iter1,0,"FormatRecord %d"%i)
		page.model.set_value(iter1,1,("clp",1))
		page.model.set_value(iter1,2,0x59)
		page.model.set_value(iter1,3,buf[offset:offset+0x59])
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		fmtid = struct.unpack('<H', buf[offset:offset+2])[0]
		datalen = struct.unpack('<I', buf[offset+2:offset+6])[0]
		dataoff = struct.unpack('<I', buf[offset+6:offset+0xa])[0]
		iter2 = page.model.append(iter1,None)
		page.model.set_value(iter2,0,"Data (Fmt, Off, Len) %02x %02x %02x"%(fmtid,dataoff,datalen))
		page.model.set_value(iter2,1,("clp",2))
		page.model.set_value(iter2,2,datalen)
		page.model.set_value(iter2,3,buf[dataoff:dataoff+datalen])
		page.model.set_value(iter2,6,page.model.get_string_from_iter(iter2))
		offset += 0x59
