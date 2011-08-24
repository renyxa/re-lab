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

def parse (model,buf,offset = 0,parent=None):
		newT = buf[offset:offset+4]
		offset += 4
		newL = struct.unpack('>I', buf[offset:offset+4])[0]
		offset += 4
		if newL%2 == 1:
			newL += 1

		if newT == "CAT ":
			desc = buf[offset:offset+4]
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"CAT ")
			model.set_value(iter1,1,("rx2","cat"))
			model.set_value(iter1,2,newL)
			model.set_value(iter1,3,buf[offset:offset+newL])
			model.set_value(iter1,6,model.get_string_from_iter(iter1))

			offset += 4
			i = 0
			while i < newL:
				try:
					offset,nlen = parse (model,buf,offset,iter1)
					i += nlen
				except:
					break
		else:
			newV = buf[offset:offset+newL]
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,newT)
			model.set_value(iter1,1,("rx2",newT))
			model.set_value(iter1,2,newL)
			model.set_value(iter1,3,buf[offset:offset+newL])
			model.set_value(iter1,6,model.get_string_from_iter(iter1))

			offset = offset + newL
			if newT == "SLCE":
				[sloffset] = struct.unpack('>I', newV[0:4])
				[sllen] = struct.unpack('>I', newV[4:8])
				[slunkn] =	struct.unpack('>I', newV[8:12])

				iter1 = model.append(parent,None)
				model.set_value(iter1,0,newT)
				model.set_value(iter1,1,("rx2",newT))
				model.set_value(iter1,2,newL)
				model.set_value(iter1,3,buf[offset:offset+newL])
				model.set_value(iter1,6,model.get_string_from_iter(iter1))
		return offset,newL+8


def open (buf,page):
	parse (page.model,buf,0)
