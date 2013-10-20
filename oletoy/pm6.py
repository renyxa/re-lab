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

recs = {
	0xd:"TextBlock",
	0xe:"TIFF ?",
	0xf:"WMF ?",
	# 0x10 --- embedded images?
	0x13:"Fonts",
	0x14:"Styles",
	0x15:"Colors",
	0x2f:"Templates",
}

def parse_trailer(page,data,tr_off,tr_len,parent,eflag,tr):
	for i in range(tr_len):
		rid1 = ord(data[tr_off+1])
		size = struct.unpack("%sH"%eflag,data[tr_off+2:tr_off+4])[0]
		off = struct.unpack("%sI"%eflag,data[tr_off+4:tr_off+8])[0]
		tr_off += 10
		if rid1 > 0 or size == 0:
			flag2 = ord(data[tr_off])
			rid2 = ord(data[tr_off + 1])
			tr_off += 6
			add_pgiter(page,"%02x %04x %08x %02x %02x"%(rid1,size,off,flag2,rid2),"pm","tr_rec",data[tr_off-16:tr_off],parent)
		else:
			triter = add_pgiter(page,"%02x %04x %08x"%(rid1,size,off),"pm","tr_rec",data[tr_off-10:tr_off],parent)
			parse_trailer(page,data,off,size,triter,eflag,tr)
		tr[off] = (rid1,size)
	return tr

def open (page,buf,parent,off=0):
	add_pgiter(page,"PM Header","pm","header",buf[0:0x36],parent)
	eflag = "<"
	if buf[6:8] == "\x99\xff":
		eflag = ">"
	tr_len = struct.unpack("%sH"%eflag,buf[0x2e:0x30])[0]
	tr_off = struct.unpack("%sI"%eflag,buf[0x30:0x34])[0]
	off += 0x36
	triter = add_pgiter(page,"Trailer","pm","trailer",buf[tr_off:tr_off+tr_len*16],parent)
	tr = {}
	parse_trailer(page,buf,tr_off,tr_len,triter,eflag,tr)
	tr[tr_off] = (0,0)
	trsort = sorted(tr.keys())[1:]
	start = 0x36
	rec = 0
	flag = 0
	for i in trsort:
		add_pgiter(page,"%s %04x [%08x-%08x]"%(key2txt(rec,recs,"%02x"%rec),flag,start,i),"pm","rec",buf[start:i],parent)
		start = i
		rec,flag = tr[i][0],tr[i][1]
	if rec != 0 and flag != 0:
		add_pgiter(page,"%s %04x [%08x-%08x]"%(key2txt(rec,recs,"%02x"%rec),flag,start,len(buf)),"pm","rec",buf[start:],parent)
		
