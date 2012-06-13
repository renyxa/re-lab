# Copyright (C) 2007-2012,	Valek Filippov (frob@df.ru)
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

import sys,struct,zlib,gtk,cdr
from utils import *

def bmp (hd,size,data,page):
	# naive version, not always works as needed
	w = struct.unpack("<I",data[0x38:0x3c])[0]
	h = struct.unpack("<I",data[0x3c:0x40])[0]
	bpp = struct.unpack("<I",data[0x50:0x54])[0]
	size = struct.unpack("<I",data[0x54:0x58])[0]-0x22
	off = 0x150
	img = 'BM'+struct.pack("<I",size)+'\x00\x00\x00\x00\x36\x00\x00\x00\x28\x00\x00\x00'
	img += data[0x38:0x40] + '\x01\x00\x18\x00\x00\x00\x00\x00'
	img += struct.pack("<I",size-0x36)+'\x13\x0b\x00\x00'*2+'\x00'*8
	img += data[off:]
	pixbufloader = gtk.gdk.PixbufLoader()
	pixbufloader.write(img)
	pixbufloader.close()
	pixbuf = pixbufloader.get_pixbuf()
	imgw=pixbuf.get_width()
	imgh=pixbuf.get_height()
	hd.da = gtk.DrawingArea()
	hd.hbox0.pack_start(hd.da)
	hd.da.connect('expose_event', cdr.disp_expose,pixbuf)
	ctx = hd.da.window.cairo_create()
	ctx.set_source_pixbuf(pixbuf,0,0)
	ctx.paint()
	ctx.stroke()
	hd.da.show()


ppp_ids = {
	"SCFFPreview":bmp
}

def parse(page,data,parent,stype):
#	try:
		add_pgiter (page,"Header","ppp","hdr",data[:0x20],parent)
		off = 0x20
		uncmpr = zlib.decompress(data[off:])
		add_pgiter (page,"[Decompressed data]","ppp",stype,uncmpr,parent)
#	except:
#		print 'Failed to decompress the stream',stype

