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

import sys,struct
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import tree
import hexdump
from utils import *

def PointS (hd, value, offset, i=""):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "y"+i, 1, struct.unpack("<h",value[offset:offset+2])[0],2,offset,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "x"+i, 1, struct.unpack("<h",value[offset+2:offset+4])[0],2,offset+2,3,2,4,"<h")

def PointL (hd, value, offset, i=""):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "x"+i, 1, struct.unpack("<i",value[offset:offset+4])[0],2,offset,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "y"+i, 1, struct.unpack("<i",value[offset+4:offset+8])[0],2,offset+4,3,4,4,"<i")

#1
def Aldus_Header (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Signature", 1, struct.unpack("<i",value[0:4])[0],2,0,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Handle", 1, struct.unpack("<h",value[4:6])[0],2,4,3,2,4,"<h")
	PointS (hd, value,6,'S')
	PointS (hd, value,10,'E')
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Inch", 1, struct.unpack("<h",value[14:16])[0],2,14,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Reserved", 1, struct.unpack("<i",value[16:20])[0],2,16,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Checksum", 1, struct.unpack("<h",value[20:22])[0],2,20,3,2,4,"<h")

#4
def Header (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Type", 1, struct.unpack("<h",value[0:2])[0],2,0,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "HdrSize", 1, struct.unpack("<h",value[2:4])[0],2,2,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Version", 1, struct.unpack("<h",value[4:6])[0],2,4,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Size", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "#Objects", 1, struct.unpack("<h",value[10:12])[0],2,10,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "MaxRecord", 1, struct.unpack("<i",value[12:16])[0],2,12,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "#Parameters", 1, struct.unpack("<h",value[16:18])[0],2,16,3,2,4,"<h")

#30
def SaveDC (hd, size, value):
	return

#258
def SetBKMode (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Mode", 1, struct.unpack("<H",value[6:8])[0],2,6,3,2,4,"<H")

#259
def SetMapMode (hd, size, value):
	SetBKMode (hd, size, value)

#260
def SetROP2 (hd, size, value):
	SetBKMode (hd, size, value)

#262
def SetPolyfillMode (hd, size, value):
	SetBKMode (hd, size, value)

#263
def SetStretchBltMode (hd, size, value):
	SetBKMode (hd, size, value)

#264
def SetTextCharExtra (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Extra", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")

#295
def RestoreDC (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "SavedDC", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")

#298
def InvertRegion (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Region ID", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")

#299
def PaintRegion (hd, size, value):
	InvertRegion (hd, size, value)

#300
def SelectClipRegion (hd, size, value):
	InvertRegion (hd, size, value)

#301
def SelectObject (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Obj ID", 1, struct.unpack("<H",value[6:8])[0],2,6,3,2,4,"<H")

#302
def SetTextAlign (hd, size, value):
	SetBKMode (hd, size, value)

#496
def DeleteObject (hd, size, value):
	SelectObject (hd, size, value)

#513
def SetBKColor (hd, size, value):
	iter = hd.model.append(None, None)
	clr = "%02X"%ord(value[6])+"%02X"%ord(value[7])+"%02X"%ord(value[8])
	hd.model.set (iter, 0, "RGB", 1, clr,2,6,3,3,4,"clrbg")

#521
def SetTextColor (hd, size, value):
	SetBKColor (hd, size, value)

#522
def SetTextJustification (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Extra", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Count", 1, struct.unpack("<i",value[10:14])[0],2,10,3,4,4,"<i")

#523
def SetWindowExtEx (hd, size, value):
	PointS (hd,value,6)

#524
def SetWindowOrgEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#525
def SetViewportExtEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#526
def SetViewportOrgEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#527
def OffsetWindowOrg (hd, size, value):
	SetWindowExtEx (hd, size, value)

#529
def OffsetViewportOrgEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#531
def LineTo (hd, size, value):
	SetWindowExtEx (hd, size, value)

#532
def MoveTo (hd, size, value):
	SetWindowExtEx (hd, size, value)

#544
def OffsetClipRgn (hd, size, value):
	PointS (hd,value,size,'off')

#552
def FillRegion (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Region", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Brush", 1, struct.unpack("<i",value[10:14])[0],2,10,3,4,4,"<i")

#561
def SetMapperFlags (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Flag", 1, struct.unpack("<i",value[6:10])[0],2,6,3,4,4,"<i")

#762
def CreatePenIndirect (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Style", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Width", 1, struct.unpack("<h",value[8:10])[0],2,8,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Height", 1, struct.unpack("<h",value[10:12])[0],2,10,3,2,4,"<h")
	iter = hd.model.append(None, None)
	clr = "%02X"%ord(value[12])+"%02X"%ord(value[13])+"%02X"%ord(value[14])
	hd.model.set (iter, 0, "RGB", 1, clr,2,12,3,3,4,"clrgb")

#763
def CreateFontIndirect (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Height", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Width", 1, struct.unpack("<h",value[8:10])[0],2,8,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Escapement", 1, struct.unpack("<h",value[10:12])[0],2,10,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Orientation", 1, struct.unpack("<h",value[12:14])[0],2,12,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Weight", 1, struct.unpack("<h",value[14:16])[0],2,14,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Italic", 1, ord(value[16]),2,16,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Underline", 1, ord(value[17]),2,17,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "StrikeOut", 1, ord(value[18]),2,18,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Charset", 1, ord(value[19]),2,19,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "OutPrecision", 1, ord(value[20]),2,20,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "ClipPrecision", 1, ord(value[21]),2,21,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Quality", 1, ord(value[22]),2,22,3,1,4,"<B")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Pitch&Family", 1, ord(value[23]),2,23,3,1,4,"<B")

#764
def CreateBrushIndirect (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Style", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.model.append(None, None)
	clr = "%02X"%ord(value[8])+"%02X"%ord(value[9])+"%02X"%ord(value[10])
	hd.model.set (iter, 0, "RGB", 1, clr,2,8,3,3,4,"clrbg")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Hatch", 1, struct.unpack("<h",value[12:14])[0],2,12,3,2,4,"<h")

#804
def Polygon (hd, size, value):
	iter = hd.model.append(None, None)
	[count] = struct.unpack("<H",value[6:8])
	hd.model.set(iter, 0, "Count", 1, count,2,6,3,2,4,"<H")
	for i in range(count):
		PointS (hd, value, i*4+8, str(i))

#805
def Polyline (hd, size, value):
	Polygon (hd, size, value)

#1040
def ScaleViewportExtEx (hd, size, value):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "xNum", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "xDenom", 1, struct.unpack("<h",value[8:10])[0],2,8,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "yNum", 1, struct.unpack("<h",value[10:12])[0],2,10,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "yDenom", 1, struct.unpack("<h",value[12:14])[0],2,12,3,2,4,"<h")

#1042
def ScaleWindowExtEx (hd, size, value):
	ScaleViewportExtEx (hd, size, value)

#1045
def ExcludeClipRect (hd, size, value):
	Rectangle (hd, size, value)

#1046
def IntersectClipRect (hd, size, value):
	Rectangle (hd, size, value)

#1048
def Ellipse (hd, size, value):
	Rectangle (hd, size, value)

#1051
def Rectangle (hd, size, value):
	PointS(hd,value,6,"S")
	PointS(hd,value,10,"E")

#1336
def PolyPolygon (hd, size, value):
	iter = hd.model.append(None, None)
	[numpoly] = struct.unpack("<h",value[6:8]) #24/28
	hd.model.set (iter, 0, "NumOfPoly", 1, numpoly,2,6,3,2,4,"<h")
	counts = {}
	for i in range(numpoly): #32
		iter = hd.model.append(None, None)
		cnt = struct.unpack("<H",value[i*2+8:i*2+10])[0]
		hd.model.set (iter, 0, "PolyPnt %d"%i, 1, cnt,2,i*2+8,3,2,4,"<H")
		counts[i]=cnt
	offset = 8+numpoly*2
	for i in counts:
		for j in range(counts[i]):
			PointS (hd, value, offset, str(j)+" (pg%d)"%i)
			offset += 4

#1564
def RoundRect (hd, size, value):
	Rectangle (hd, size, value)
	PointS (hd, value, 14, "Diam")

#1791
def CreateRegion (hd, size, value):
	PointL (hd, value, 6, "S")
	PointL (hd, value, 14, "E")

#2071
def Arc (hd, size, value):
	PointS(hd,value,6,"Rs")
	PointS(hd,value,10,"Re")
	PointS (hd, value, 14, "S")
	PointS (hd, value, 18, "E")

#2074
def Pie (hd, size, value):
	Arc (hd, size, value)

#2096
def Chord (hd, size, value):
	Arc (hd, size, value)

#2610
def ExtTextOut (hd, size, value):
	PointS (hd, value, 6)
	iter = hd.model.append(None, None)
	count = struct.unpack("<h",value[10:12])[0]
	hd.model.set (iter, 0, "Count", 1, count, 2,10,3,2,4,"<h")
	iter = hd.model.append(None, None)
	flags = struct.unpack("<h",value[12:14])[0]
	hd.model.set (iter, 0, "Flags", 1, flags, 2,12,3,2,4,"<h")
	off = 0xe
	if (flags&4):
		PointS(hd,value,off,"S")
		PointS(hd,value,off+4,"S")
		off += 8
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Text", 1, value[off:off+count],2,off,3,count,4,"txt")
	off += count
	if flags&0x10 == 0:
		if flags&0x2000:
			for i in range(count):
				iter = hd.model.append(None, None)
				hd.model.set (iter, 0, "Dx%d"%i, 1, struct.unpack("<H",value[off+i*4:off+2+i*4])[0],2,off+i*4,3,2,4,"<H")
				iter = hd.model.append(None, None)
				hd.model.set (iter, 0, "Dy%d"%i, 1, struct.unpack("<H",value[off+2+i*4:off+4+i*4])[0],2,off+2+i*4,3,2,4,"<H")
		else:
			for i in range(count):
				iter = hd.model.append(None, None)
				hd.model.set (iter, 0, "Dx%d"%i, 1, struct.unpack("<h",value[off+i*2:off+2+i*2])[0],2,off+i*2,3,2,4,"<H")
			
	# Fixme! DX/DY depends on flags

wmr_ids = {
1:Aldus_Header,
#2:'CLP_Header16',3:'CLP_Header32',
4:Header, 30:SaveDC,
#53:'RealizePalette', 55:'SetPalEntries', 247:'CreatePalette', 313:'ResizePalette',564:'SelectPalette', 1078:'AnimatePalette', 
#79:'StartPage', 80:'EndPage', 82:'AbortDoc', 94:'EndDoc', 333:'StartDoc', 
#248:'CreateBrush', 322:'DibCreatePatternBrush', 505:'CreatePatternBrush',
258:SetBKMode, 259:SetMapMode, 260:SetROP2, 262:SetPolyfillMode, 263:SetStretchBltMode,
264:SetTextCharExtra, 295:RestoreDC,  298:InvertRegion, 299:PaintRegion,
300:SelectClipRegion, 301:SelectObject, 302:SetTextAlign,
#332:'ResetDc', 

496:DeleteObject, 513:SetBKColor, 521:SetTextColor, 522:SetTextJustification,
523:SetWindowOrgEx, 524:SetWindowExtEx,525:SetViewportOrgEx,
526:SetViewportExtEx, 527:OffsetWindowOrg, 529:OffsetViewportOrgEx,
531:LineTo, 532:MoveTo, 544:OffsetClipRgn, 552:FillRegion, 561:SetMapperFlags,  
762:CreatePenIndirect, 763:CreateFontIndirect, 764:CreateBrushIndirect,
#765:'CreateBitmapIndirect', 
804:Polygon, 805:Polyline, 1040:ScaleWindowExtEx, 1042:ScaleViewportExtEx,
1045:ExcludeClipRect, 1046:IntersectClipRect, 1048:Ellipse, 1051:Rectangle,

#1065:'FrameRegion',
#1049:'FloodFill', 1352:'ExtFloodFill', 1574:'Escape', 
#1055:'SetPixel',
1336:PolyPolygon, 1564:RoundRect, 1791:CreateRegion, 2071:Arc, 2074:Pie, 2096:Chord, 
#1313:'TextOut', 1583:'DrawText',
2610:ExtTextOut,
#1790:'CreateBitmap', 1565:'PatBlt', 2338:'BitBlt', 2368:'DibBitblt', 2851:'StretchBlt', 2881:'DibStretchBlt', 3379:'SetDibToDev', 3907:'StretchDIBits'
}
