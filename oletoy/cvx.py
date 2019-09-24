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


import struct
from utils import *

def parse(page,buf,parent):
	tagstack = []
	off = 0
	piter = parent
	pos4 = 0
	while off < len(buf):
		pos1 = buf.find("<BEGIN",off)
		if pos1 != -1:
			pos2 = buf.find("TAG>",pos1)
			tag = buf[pos1+7:pos2-1]
			pos3 = buf.find("<END_%s_TAG>"%tag,off)
			if pos3 < pos4:
				piter = citer
				off = pos3+10+len(tag)
				add_pgiter(page,tag,"cvx",tag,buf[pos1+12+len(tag):pos3],piter)
			else:
				pos4 = pos3
				off = pos2
				pos2 = pos3
				piter = parent
				citer = add_pgiter(page,tag,"cvx",tag,buf[pos1+12+len(tag):pos3],piter)
			print(tag,pos1,pos2,pos3)
		else:
			off = len(buf)
