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

def little_endian(fmt):
	return '<' + fmt

def big_endian(fmt):
	return '>' + fmt

def collect_group(data,name,buf,fmt,off,grp_id):
	grplen = struct.unpack(fmt('H'),buf[off+0x400*(grp_id-1):off+0x400*(grp_id-1)+2])[0]
	data += buf[off+0x400*(grp_id-1)+2:off+0x400*(grp_id+grplen-1)-4]
	nxt = struct.unpack(fmt('i'),buf[off+0x400*(grp_id+grplen-1)-4:off+0x400*(grp_id+grplen-1)])[0]
	name += " %02x-%02x"%(grp_id,grp_id+grplen-1)
	if nxt > 0:
		data,name = collect_block(data,name,buf,fmt,off,nxt)
	elif nxt < 0:
		nxt = abs(nxt)
		data,name = collect_group(data,name,buf,fmt,off,nxt)
	return data,name


def collect_block(data,name,buf,fmt,off,blk_id):
	data += buf[off+0x400*(blk_id-1):off+0x400*blk_id-4]
	name += " %02x"%blk_id
	nxt = struct.unpack(fmt('i'),buf[off+0x400*blk_id-4:off+0x400*blk_id])[0]
	if nxt > 0:
		data,name = collect_block(data,name,buf,fmt,off,nxt)
	elif nxt < 0:
		nxt = abs(nxt)
		data,name = collect_group(data,name,buf,fmt,off,nxt)
	return data,name

def open_v5 (page,buf,parent,fmt,off=0,bs=1):
	rlen = 0x100
	i = bs
	flag = 0
	try:
		while off < len(buf):
			if flag == 0:
				start = off
				off += rlen - 4
				(nxt, off) = rdata(buf, off, fmt('i'))
				if nxt < 0:
					nxt = abs(nxt)
					(flag, _) = rdata(buf, off, fmt('H'))
				n = "%02x [%02x]"%(i,nxt)
				add_pgiter(page,n,"qxp","block%02x"%i,buf[start:start+rlen],parent)
				i += 1
			else:
				start = off
				off += rlen * flag - 4
				(nxt, off) = rdata(buf, off, fmt('i'))
				flag2 = 0
				if nxt < 0:
					nxt = abs(nxt)
					(flag2, _) = rdata(buf, off, fmt('H'))
				n = "%02x-%02x [%02x]"%(i,i+flag-1,nxt)
				add_pgiter(page,n,"qxp","block%02x"%i,buf[start:start+rlen*flag],parent)
				i += flag
				flag = flag2
			if nxt > i:
				# need to jump
				piter = add_pgiter(page,"jump %02x-%02x"%(i,nxt-1),"qxp","block%02x"%i,buf[off:off+rlen*(nxt-i)],parent)
				open_v5(page,buf[off:off+rlen*(nxt-i)],piter,fmt,0,i)
				off += rlen*(nxt-i)
				# overwrite flag
				if flag:
					(flag, _) = rdata(buf, off, fmt('H'))
				i = nxt
	except:
		print "failed in qxd loop"
	return "QXP5"


def open (page,buf,parent):
	if buf[2:4] == 'II':
		fmt = little_endian
	elif buf[2:4] == 'MM':
		fmt = big_endian
	else:
		print "unknown format '%s', assuming big endian" % buf[2:4]
		fmt = big_endian

	# 0x3f - 3
	# 0x41 - 4
	# 0x42 - 5
	# 0x43 - 6
	# 0x44? -7
	# 0x45 - 8
	if ord(buf[8]) < 0x43:
		open_v5 (page,buf,parent,fmt,0)
	else:
		rlen = 0x400
		off = 0
		parent = add_pgiter(page,"File","qxp","file",buf,parent)
	
		add_pgiter(page,"01","qxp","block01",buf[off:off+rlen],parent)
		
		lstlen1 = struct.unpack(fmt('I'),buf[off+rlen+0x14:off+rlen+0x18])[0]
		lstlen2 = struct.unpack(fmt('I'),buf[off+rlen+0x18:off+rlen+0x1c])[0]
		lstlen3 = struct.unpack(fmt('I'),buf[off+rlen+0x1c:off+rlen+0x20])[0]
		lstlen4 = struct.unpack(fmt('I'),buf[off+rlen+0x20:off+rlen+0x24])[0]
		txtlstlen = struct.unpack(fmt('I'),buf[off+rlen+0x24:off+rlen+0x28])[0]
		lst = []
		txtlstoff = 0x28+lstlen1++lstlen2+lstlen3+lstlen4
		for i in range(lstlen1/4):
			lst.append(struct.unpack(fmt('I'),buf[off+rlen+0x28+i*4:off+rlen+0x2c+i*4])[0])
		for i in lst:
			# collect chain of blocks
			data = buf[off+rlen*(i-1):off+rlen*i-4]
			name = "%02x"%i
			nxt = struct.unpack(fmt('i'),buf[off+rlen*i-4:off+rlen*i])[0]
			if nxt > 0:
				# collect next single block
				data,name = collect_block(data,name,buf,fmt,off,nxt)
			elif nxt < 0:
				# collect chain of blocks
				data,name = collect_group(data,name,buf,fmt,off,abs(nxt))
			add_pgiter(page,name,"qxp","block%02x"%i,data,parent)

		
		for j in range(txtlstlen/4):
			i = struct.unpack(fmt('I'),buf[off+rlen+txtlstoff+j*4:off+rlen+txtlstoff+j*4+4])[0]
			data = buf[off+rlen*(i-1):off+rlen*i]
			name = "TXT %02x"%i
			add_pgiter(page,name,"qxp","txtblock%02x"%i,data,parent)
		return "QXP6"
	
# vim: set ft=python sts=4 sw=4 noet:
