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

def open (page,buf,parent,off=0,bs=1):
	# 0x3f - 3
	# 0x41 - 4
	# 0x42 - 5
	# 0x43 - 6
	# 0x44? -7
	# 0x45 - 8
	if bs!=1 or ord(buf[8]) < 0x42:
		rlen = 0x100
		i = bs
		flag = 0
		try:
			while off < len(buf):
				if flag == 0:
					nxt = struct.unpack("<i",buf[off+rlen-4:off+rlen])[0]
					n = "%02x [%02x]"%(i,nxt)
					if nxt < 0:
						nxt = abs(nxt)
						flag = struct.unpack("<H",buf[off+rlen:off+rlen+2])[0]
						n = "%02x [%02x]"%(i,nxt)
					add_pgiter(page,n,"qxp","block%02x"%i,buf[off:off+rlen],parent)
					off += rlen
					i += 1
				else:
					nxt = struct.unpack("<i",buf[off+rlen*flag-4:off+rlen*flag])[0]
					n = "%02x-%02x [%02x]"%(i,i+flag-1,nxt)
					flag2 = 0
					if nxt < 0:
						nxt = abs(nxt)
						flag2 = struct.unpack("<H",buf[off+rlen*flag:off+rlen*flag+2])[0]
						n = "%02x-%02x [%02x]"%(i,i+flag-1,nxt)
					add_pgiter(page,n,"qxp","block%02x"%i,buf[off:off+rlen*flag],parent)
					off += rlen*flag
					i += flag
					flag = flag2
				if nxt > i:
					# need to jump
					piter = add_pgiter(page,"jump %02x-%02x"%(i,nxt-1),"qxp","block%02x"%i,buf[off:off+rlen*(nxt-i)],parent)
					open(page,buf[off:off+rlen*(nxt-i)],piter,0,i)
					off += rlen*(nxt-i)
					# overwrite flag
					if flag:
						flag = struct.unpack("<H",buf[off:off+2])[0]
					i = nxt
		except:
			print "failed in qxd loop"
		return "QXP5"
		
	rlen = 0x400
	parent = add_pgiter(page,"File","qxp","file",buf,parent)

	add_pgiter(page,"Block 0","qxp","block0",buf[off:off+rlen],parent)
	lstlen = struct.unpack("<I",buf[off+rlen+0x1c:off+rlen+0x20])[0]
	lst = []
	for i in range(lstlen/4):
		lst.append(struct.unpack("<I",buf[off+rlen+0x28+i*4:off+rlen+0x2c+i*4])[0])
	for i in lst:
		# collect chain of blocks
		data = buf[off+rlen*(i-1):off+rlen*i-4]
		name = "%02x"%i
		nxt = struct.unpack("<i",buf[off+rlen*i-4:off+rlen*i])[0]
		if nxt > 0:
			# collect next single block
			data,name = collect_block(data,name,buf,off,nxt)
		elif nxt < 0:
			# collect chain of blocks
			data,name = collect_group(data,name,buf,off,abs(nxt))
		add_pgiter(page,name,"qxp","block%02x"%i,data,parent)
	return "QXP6"
