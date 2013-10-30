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

def collect_group(data,name,buf,off,grp_id):
	grplen = struct.unpack("<H",buf[off+0x400*(grp_id-1):off+0x400*(grp_id-1)+2])[0]
	data += buf[off+0x400*(grp_id-1)+2:off+0x400*(grp_id+grplen-1)-4]
	nxt = struct.unpack("<i",buf[off+0x400*(grp_id+grplen-1)-4:off+0x400*(grp_id+grplen-1)])[0]
	name += " %02x-%02x"%(grp_id,grp_id+grplen)
	if nxt > 0:
		data,name = collect_block(data,name,buf,off,nxt)
	elif nxt < 0:
		nxt = abs(nxt)
		data,name = collect_group(data,name,buf,off,nxt)
	return data,name


def collect_block(data,name,buf,off,blk_id):
	data += buf[off+0x400*(blk_id-1):off+0x400*blk_id-4]
	name += " %02x"%blk_id
	nxt = struct.unpack("<i",buf[off+0x400*blk_id-4:off+0x400*blk_id])[0]
	if nxt > 0:
		data,name = collect_block(data,name,buf,off,nxt)
	elif nxt < 0:
		nxt = abs(nxt)
		data,name = collect_group(data,name,buf,off,nxt)
	return data,name

def open (page,buf,parent,off=0):
	# 0x3f - 3
	# 0x45 - 8
	
	add_pgiter(page,"Block 0","qxp","block0",buf[off:off+0x400],parent)
	lstlen = struct.unpack("<I",buf[off+0x400+0x1c:off+0x400+0x20])[0]
	lst = []
	for i in range(lstlen/4):
		lst.append(struct.unpack("<I",buf[off+0x400+0x28+i*4:off+0x400+0x2c+i*4])[0])
	for i in lst:
		# collect chain of blocks
		data = buf[off+0x400*(i-1):off+0x400*i-4]
		name = "%02x"%i
		nxt = struct.unpack("<i",buf[off+0x400*i-4:off+0x400*i])[0]
		if nxt > 0:
			# collect next single block
			data,name = collect_block(data,name,buf,off,nxt)
		elif nxt < 0:
			# collect chain of blocks
			data,name = collect_group(data,name,buf,off,abs(nxt))
		add_pgiter(page,name,"qxp","block%02x"%i,data,parent)
