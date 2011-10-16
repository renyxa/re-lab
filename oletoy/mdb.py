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

import sys,struct,gtk,gobject

def parse (buf,page):
	offset = 0
	i = 0
	while offset < len(buf):
		iter1 = page.model.append(None,None)
		page.model.set_value(iter1,0,"Block %02x"%i)
		page.model.set_value(iter1,1,("mdb",0))
		page.model.set_value(iter1,2,0x1000)
		page.model.set_value(iter1,3,buf[offset:offset+0x1000])
		page.model.set_value(iter1,7,"  %02x"%struct.unpack("<H",buf[offset:offset+2]))
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += 0x1000
		i += 1
