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

import struct

win_types = {0x15:'Drawing',0x1d:'Stencil'}

def EventItem (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ID", 1, "%d"%struct.unpack("<I",value[4:8]),2,4,3,4,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "EventCode", 1, "%d"%struct.unpack("<h",value[8:10]),2,4,3,4,4,"<d")
# + 2 bytes of 'Action' and/or 'Enabled'
# + 2 \0\0 terminated strings -- 1st is for 'Target', 2nd -- 'TargetArgs'


def StencilPage (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "UniqueID", 1, "",2,16,3,8,4,"txt")
	iter1 = hd.hdmodel.append(None, None)
	base_id = "%02X%02X%02X%02X-"%(ord(value[0x3f]),ord(value[0x3e]),ord(value[0x3d]),ord(value[0x3c]))
	base_id += "%02X%02X-%02X%02X-"%(ord(value[0x39]),ord(value[0x38]),ord(value[0x3b]),ord(value[0x3a]))
	base_id += "%02X%02X-%02X%02X%"%(ord(value[0x24]),ord(value[0x25]),ord(value[0x26]),ord(value[0x27]))
	base_id += "02X%02X%02X%02X"%(ord(value[0x28]),ord(value[0x29]),ord(value[0x2a]),ord(value[0x2b]))
	hd.hdmodel.set (iter1, 0, "BaseID", 1, base_id,2,24,3,28,4,"txt")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "UniqueID", 1, "",2,16,3,8,4,"txt")


def Window (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	[type] = struct.unpack("<I",value[6:10])
	if win_types.has_key(type):
		type = win_types[type]
	else:
		type = "%02x"%type
	hd.hdmodel.set (iter1, 0, "WinType", 1, type,2,6,3,4,4,"txt")

	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "WinLeft", 1, "%d"%struct.unpack("<h",value[0x12:0x14]),2,0x12,3,2,4,"<h")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "WinTop", 1, "%d"%struct.unpack("<h",value[0x14:0x16]),2,0x14,3,2,4,"<h")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "WinWidth", 1, "%d"%struct.unpack("<h",value[0x16:0x18]),2,0x16,3,2,4,"<h")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "WinHeight", 1, "%d"%struct.unpack("<h",value[0x18:0x1a]),2,0x18,3,2,4,"<h")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ViewCenterX", 1, "%.2f"%struct.unpack("<d",value[0x2a:0x32]),2,0x2a,3,8,4,"<d")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ViewCenterY", 1, "%.2f"%struct.unpack("<d",value[0x32:0x3a]),2,0x32,3,8,4,"<d")



stream_func = {0x1e:StencilPage,0x2a:Window,0x2f:EventItem}
