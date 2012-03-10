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
from utils import *

def parse (page, data, parent):
	off = 0
	while off < len(data) - 2:
		type = struct.unpack('<H', data[off:off+2])[0]
		off += 2
		length = struct.unpack('<H', data[off:off+2])[0]
		off += 2
		value = data[off:off+length]
		add_pgiter (page,"Type %02x Len %02x"%(type,length),"qpw","rec",value,parent)
		off += length
