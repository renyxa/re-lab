# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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

import sys,struct
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import tree
import hexdump
from utils import *

opcodes = {
	0x0000:"NOP",
	0x0001:"Clip",
	0x0002:"BkPat",
	0x0003:"TxFont",
	0x0004:"TxFace",
	0x0005:"TxMode",
	0x0006:"SpExtra",
	0x0007:"PnSize",
	0x0008:"PnMode",
	0x0009:"PnPat",
	0x000A:"FillPat",
	0x000B:"OvSize",
	0x000C:"Origin",
	0x000D:"TxSize",
	0x000E:"FgColor",
	0x000F:"BkColor",
	0x0010:"TxRatio",
	0x0011:"VersionOp",
	0x0012:"BkPixPat",
	0x0013:"PnPixPat",
	0x0014:"FillPixPat",
	0x0015:"PnLocHFrac",
	0x0016:"ChExtra",
	0x001A:"RGBFgCol",
	0x001B:"RGBBkCol",
	0x001C:"HiliteMode",
	0x001D:"HiliteColor",
	0x001E:"DefHilite",
	0x001F:"OpColor",
	0x0020:"Line",
	0x0021:"LineFrom",
	0x0022:"ShortLine",
	0x0023:"ShortLineFrom",
	0x0028:"LongText",
	0x0029:"DHText",
	0x002A:"DVText",
	0x002B:"DHDVText",
	0x002C:"fontName",
	0x002D:"lineJustify",
	0x002E:"glyphState",
	0x0030:"frameRect",
	0x0031:"paintRect",
	0x0032:"eraseRect",
	0x0033:"invertRect",
	0x0034:"fillRect",
	0x0038:"frameSameRect",
	0x0039:"paintSameRect",
	0x003A:"eraseSameRect",
	0x003B:"invertSameRect",
	0x003C:"fillSameRect",
	0x0040:"frameRRect",
	0x0041:"paintRRect",
	0x0042:"eraseRRect",
	0x0043:"invertRRect",
	0x0044:"fillRRect",
	0x0048:"frameSameRRect",
	0x0049:"paintSameRRect",
	0x004A:"eraseSameRRect",
	0x004B:"invertSameRRect",
	0x004C:"fillSameRRect",
	0x0050:"frameOval",
	0x0051:"paintOval",
	0x0052:"eraseOval",
	0x0053:"invertOval",
	0x0054:"fillOval",
	0x0058:"frameSameOval",
	0x0059:"paintSameOval",
	0x005A:"eraseSameOval",
	0x005B:"invertSameOval",
	0x005C:"fillSameOval",
	0x0060:"frameArc",
	0x0061:"paintArc",
	0x0062:"eraseArc",
	0x0063:"invertArc",
	0x0064:"fillArc",
	0x0068:"frameSameArc",
	0x0069:"paintSameArc",
	0x006A:"eraseSameArc",
	0x006B:"invertSameArc",
	0x006C:"fillSameArc",
	0x0070:"framePoly",
	0x0071:"paintPoly",
	0x0072:"erasePoly",
	0x0073:"invertPoly",
	0x0074:"fillPoly",
	0x0078:"frameSamePoly",
	0x0079:"paintSamePoly",
	0x007A:"eraseSamePoly",
	0x007B:"invertSamePoly",
	0x007C:"fillSamePoly",
	0x0080:"frameRgn",
	0x0081:"paintRgn",
	0x0082:"eraseRgn",
	0x0083:"invertRgn",
	0x0084:"fillRgn",
	0x0088:"frameSameRgn",
	0x0089:"paintSameRgn",
	0x008A:"eraseSameRgn",
	0x008B:"invertSameRgn",
	0x008C:"fillSameRgn",
	0x0090:"BitsRect",
	0x0091:"BitsRgn",
	0x0098:"PackBitsRect",
	0x0099:"PackBitsRgn",
	0x009A:"DirectBitsRect",
	0x009B:"DirectBitsRgn",
	0x00A0:"ShortComment",
	0x00A1:"LongComment",
	0x00FF:"OpEndPic",
	0x02FF:"Version",
	0x0C00:"HeaderOp",
	0x8200:"CompressedQuickTime",
	0x8201:"UncompressedQuickTime"
}

opsizes = {
	0x0000:0,
	0x0002:8,
	0x0003:2,
	0x0004:1,
	0x0005:2,
	0x0006:4,
	0x0007:4,
	0x0008:2,
	0x0009:8,
	0x000A:8,
	0x000B:4,
	0x000C:4,
	0x000D:2,
	0x000E:4,
	0x000F:4,
	0x0010:8,
	0x0011:2,
	0x0015:2,
	0x0016:2,
	0x001A:6,
	0x001B:6,
	0x001C:0,
	0x001D:6,
	0x001E:0,
	0x001F:6,
	0x0020:8,
	0x0021:4,
	0x0022:6,
	0x0023:2,
	0x002D:10,
	0x002E:8,
	0x0030:8,
	0x0031:8,
	0x0032:8,
	0x0033:8,
	0x0034:8,
	0x0035:8,
	0x0036:8,
	0x0037:8,
	0x0038:0,
	0x0039:0,
	0x003A:0,
	0x003B:0,
	0x003C:0,
	0x003D:0,
	0x003E:0,
	0x003F:0,
	0x0040:8,
	0x0041:8,
	0x0042:8,
	0x0043:8,
	0x0044:8,
	0x0045:8,
	0x0046:8,
	0x0047:8,
	0x0048:0,
	0x0049:0,
	0x004A:0,
	0x004B:0,
	0x004C:0,
	0x004D:0,
	0x004E:0,
	0x004F:0,
	0x0050:8,
	0x0051:8,
	0x0052:8,
	0x0053:8,
	0x0054:8,
	0x0055:8,
	0x0056:8,
	0x0057:8,
	0x0058:0,
	0x0059:0,
	0x005A:0,
	0x005B:0,
	0x005C:0,
	0x005D:0,
	0x005E:0,
	0x005F:0,
	0x0060:12,
	0x0061:12,
	0x0062:12,
	0x0063:12,
	0x0064:12,
	0x0065:12,
	0x0066:12,
	0x0067:12,
	0x0068:4,
	0x0069:4,
	0x006A:4,
	0x006B:4,
	0x006C:4,
	0x006D:4,
	0x006E:4,
	0x006F:4,
	0x0078:0,
	0x0079:0,
	0x007A:0,
	0x007B:0,
	0x007C:0,
	0x007D:0,
	0x007E:0,
	0x007F:0,
	0x0088:0,
	0x0089:0,
	0x008A:0,
	0x008B:0,
	0x008C:0,
	0x008D:0,
	0x008E:0,
	0x008F:0,
	0x00A0:2,
	0x00B0:0,
	0x00CF:0,
	0x00FF:2,
	0x02FF:2
}

def clip(data,off):
	return struct.unpack(">H",data[off:off+2])[0] 

def pktbitrect(data,off):
	res = off
	rowbytes = (struct.unpack(">H",data[off:off+2])[0])&0x3fff
	off += 2
	bounds = struct.unpack(">HHHH",data[off:off+8])
	off += 8
	# skip others
	off += 18
	if rowbytes < 8:
		res = rowbytes*(bounds[2]-bounds[0])+28
	else:
		f,t = '>B',1
		if rowbytes > 250:
			f,t = '>H',2
		for i in range(bounds[2]-bounds[0]):
			off += struct.unpack(f,data[off:off+t])[0] + t
		res = off - res
	return res


def dirbitsrect(data,off):
	res = off
	#pixmap
	off += 4 # handle
	rowbytes = (struct.unpack(">H",data[off:off+2])[0])&0x3fff
	off += 2
	bounds = struct.unpack(">HHHH",data[off:off+8])
	off += 8
	# skip version
	off += 2
	packtype = struct.unpack(">H",data[off:off+2])[0]
	off += 2
	# skip others
	off += 32
	#skip src/dst rects
	off += 16
	#skip mode
	off += 2
	# docs p.741
	if rowbytes < 8 or packtype == 1:
		res = rowbytes*(bounds[2]-bounds[0])+68
	elif packtype == 2:
		res = rowbytes*(bounds[2]-bounds[0])*0.75+68
	elif packtype > 2:
		f,t = '>B',1
		if rowbytes > 250:
			f,t = '>H',2
		for i in range(bounds[2]-bounds[0]):
			off += struct.unpack(f,data[off:off+t])[0] + t
		res = off - res
	return res

def longcmnt(data,off):
	return struct.unpack(">H",data[off+2:off+4])[0]+4


op_funcs = {
	0x0001:clip,
	0x0098:pktbitrect,
	0x009a:dirbitsrect,
	0x00a1:longcmnt
}

def opsize(op,data,off):
	if op > 0xff and op != 0x2ff:
		return (op>>8)*2
	else:
		if op in opsizes:
			return opsizes[op]
		elif op in op_funcs:
			return op_funcs[op](data,off)
		else:
			return 254

def parse(page,data,parent):
	off = 0x20a
	while off < len(data):
		opc = struct.unpack(">H",data[off:off+2])[0]
		opn = key2txt(opc,opcodes,"Rsrvd by Apple")
		ops = opsize(opc,data,off+2) # skip opc
		add_pgiter(page,opn,"pict",opc,data[off:off+2+ops],parent)
		off += 2+ops
