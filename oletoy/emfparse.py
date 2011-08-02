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
import gobject
import gtk
import tree
import hexdump


ColorSpace = {1:"ENABLE",2:"DISABLE",3:"DELETE_TRANSFORM"}

ColorMatchToTarget = {0:"NOTEMBEDDED",1:"EMBEDDED"}

def PointS (hd, value, offset, i=""):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "x"+i, 1, struct.unpack("<h",value[offset:offset+2])[0],2,offset,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "y"+i, 1, struct.unpack("<h",value[offset+2:offset+4])[0],2,offset+2,3,2,4,"<h")

def PointL (hd, value, offset, i=""):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "x"+i, 1, struct.unpack("<i",value[offset:offset+4])[0],2,offset,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "y"+i, 1, struct.unpack("<i",value[offset+4:offset+8])[0],2,offset+4,3,4,4,"<i")

def GC_BeginGroup (hd, value):
	PointL(hd,value,0x14,"S")
	PointL(hd,value,0x1c,"E")
	nlen = struct.unpack("<I",value[0x24:0x28])[0]
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "DescLength", 1, nlen,2,0x24,3,4,4,"<I")
	txt = unicode(value[0x28:0x28+nlen*2],"utf-16")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Description", 1, txt,2,0x28,3,nlen*2,4,"txt")

def GC_EndGroup (hd, value):
	pass

#1
def Header (hd, size, value):
	PointL (hd, value, 8, "S")
	PointL (hd, value, 16, "E")
	PointL (hd, value, 24, "S (mm)")
	PointL (hd, value, 32, "E (mm)")
	iter = hd.hdmodel.append(None, None)
	[sig] = struct.unpack("<i",value[40:44])
	hd.hdmodel.set(iter, 0, "Signature", 1, "0x%08X"%sig,2,40,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Version", 1, "0x%08X"%struct.unpack("<i",value[44:48]),2,44,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Size", 1, struct.unpack("<I",value[48:52])[0],2,48,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Records", 1, struct.unpack("<I",value[52:56])[0],2,52,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Objects", 1, struct.unpack("<H",value[56:58])[0],2,56,3,2,4,"<H")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Reservd", 1, struct.unpack("<H",value[58:60])[0],2,58,3,2,4,"<H")
	iter = hd.hdmodel.append(None, None)
	[descsize] = struct.unpack("<I",value[60:64])
	hd.hdmodel.set(iter, 0, "DescSize", 1, descsize,2,60,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	[descoff] = struct.unpack("<I",value[64:68])
	hd.hdmodel.set(iter, 0, "DescOffset", 1, "0x%02x"%descoff,2,64,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	[palnum] = struct.unpack("<I",value[68:72])
	hd.hdmodel.set(iter, 0, "PalEntries", 1, palnum,2,68,3,4,4,"<I")
	PointL (hd, value, 72, "Dev")
	PointL (hd, value, 80, "Dev (mm)")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "cbPxlFmt", 1, struct.unpack("<I",value[88:92])[0],2,88,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "offPxlFmt", 1, struct.unpack("<I",value[92:96])[0],2,92,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "bOpenGL", 1, struct.unpack("<I",value[96:100])[0],2,96,3,4,4,"<I")
	PointL (hd, value, 100, " (micrometers)")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "Description", 1, unicode(value[descoff:descoff+descsize*2],"utf-16"),2,descoff,3,descsize*2,4,"txt")

#2
def Polybezier (hd, size, value):
	Rectangle (hd, size, value)
	iter = hd.hdmodel.append(None, None)
	[count] = struct.unpack("<i",value[24:28])
	hd.hdmodel.set(iter, 0, "Count", 1, count,2,24,3,4,4,"<i")
	for i in range(count):
		PointL (hd, value, i*8+28, str(i))

#3
def Polygon (hd, size, value):
	Polybezier (hd, size, value)

#4
def Polyline (hd, size, value):
	Polybezier (hd, size, value)

#5
def PolybezierTo (hd, size, value):
	Polybezier (hd, size, value)

#6
def PolylineTo (hd, size, value):
	Polybezier (hd, size, value)

#7
def PolyPolyline (hd, size, value):
	Rectangle (hd, size, value)
	iter = hd.hdmodel.append(None, None)
	[numpoly] = struct.unpack("<i",value[24:28])
	hd.hdmodel.set (iter, 0, "NumOfPoly", 1, numpoly,2,24,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	[count] = struct.unpack("<i",value[28:32])
	hd.hdmodel.set (iter, 0, "Count", 1, count,2,28,3,4,4,"<i")
	for i in range(numpoly):
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "PolyPnt %d"%i, 1, struct.unpack("<I",value)[32+i*4:36+i*4][0],2,32+i*4,3,4,4,"<I")
	for i in range(count):
		PointL (hd, value, i*8+32+numpoly*4, str(i))

#8
def PolyPolygon (hd, size, value):
	PolyPolyline (hd, size, value)

#9
def SetWindowExtEx (hd, size, value):
	PointL (hd,value,8)

#10
def SetWindowOrgEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#11
def SetViewportExtEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#12
def SetViewportOrgEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#13
def SetBrushOrgEx (hd, size, value):
	PointL (hd, value, 8, "Org")

#16
def SetMapperFlags (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Mode", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#17
def SetMapMode (hd, size, value):
	SetBKMode (hd, size, value)

#18
def SetBKMode (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Mode", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#19
def SetPolyfillMode (hd, size, value):
	SetBKMode (hd, size, value)

#20
def SetRop2 (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Mode", 1, "0x%0x"%struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#21
def SetStretchBltMode (hd, size, value):
	SetBKMode (hd, size, value)

#22
def SetTextAlign (hd, size, value):
	SetBKMode (hd, size, value)

#23
def SetColorAdjustment (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Size", 1, struct.unpack("<i",value[8:10])[0],2,8,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Values", 1, struct.unpack("<i",value[10:12])[0],2,10,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "IllumIdx", 1, struct.unpack("<i",value[12:14])[0],2,12,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "RedGamma", 1, struct.unpack("<i",value[14:16])[0],2,14,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "GreenGamma", 1, struct.unpack("<i",value[16:18])[0],2,16,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "BlueGamma", 1, struct.unpack("<i",value[18:20])[0],2,18,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "RefBlack", 1, struct.unpack("<i",value[20:22])[0],2,20,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "RefWhite", 1, struct.unpack("<i",value[22:24])[0],2,22,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Contrast", 1, struct.unpack("<i",value[24:26])[0],2,24,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Brightness", 1, struct.unpack("<i",value[26:28])[0],2,26,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Colorfull", 1, struct.unpack("<i",value[28:30])[0],2,28,3,2,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "RedGreenTint", 1, struct.unpack("<i",value[30:32])[0],2,30,3,2,4,"<i")

#24
def SetTextColor (hd, size, value):
	SetBKColor (hd, size, value)

#25
def SetBKColor (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	clr = "%02X"%ord(value[10])+"%02X"%ord(value[9])+"%02X"%ord(value[8])
	hd.hdmodel.set (iter, 0, "RGB", 1, clr,2,8,3,3,4,"clr")

#26
def OffsetClipRgn (hd, size, value):
	SetWindowExtEx (hd, size, value)
	
#27
def MoveToEx (hd, size, value):
	SetWindowExtEx (hd, size, value)

#29
def ExcludeClipRect (hd, size, value):
	Rectangle (hd, size, value)

#30
def IntersectClipRect (hd, size, value):
	Rectangle (hd, size, value)

#31
def ScaleViewportExtEx (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "xNum", 1, struct.unpack("<i",value[8:12])[0],2,8,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "xDenom", 1, struct.unpack("<i",value[12:16])[0],2,12,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "yNum", 1, struct.unpack("<i",value[16:20])[0],2,16,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "yDenom", 1, struct.unpack("<i",value[20:24])[0],2,20,3,4,4,"<i")

#32
def ScaleWindowExtEx (hd, size, value):
	ScaleViewportExtEx (hd, size, value)
	
#33
def SaveDC (hd, size, value):
	return

#34
def RestoreDC (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "SavedDC", 1, struct.unpack("<i",value[8:12])[0],2,8,3,4,4,"<i")

#35
def SetWorldTransform  (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "m11", 1, struct.unpack("<f",value[8:12])[0],2,8,3,4,4,"<f")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "m12", 1, struct.unpack("<f",value[12:16])[0],2,12,3,4,4,"<f")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "m21", 1, struct.unpack("<f",value[16:20])[0],2,16,3,4,4,"<f")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "m22", 1, struct.unpack("<f",value[20:24])[0],2,24,3,4,4,"<f")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Dx", 1, struct.unpack("<f",value[24:28])[0],2,24,3,4,4,"<f")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Dy", 1, struct.unpack("<f",value[28:32])[0],2,28,3,4,4,"<f")

#36
def ModifyWorldTransform (hd, size, value):
	SetWorldTransform  (hd, size, value)
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Mode", 1, struct.unpack("<I",value[32:36])[0],2,32,3,4,4,"<I")

#37
def SelectObject (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "ObjID", 1, "0x%0x"%struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#38
def CreatePen (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "ObjID", 1, "0x%0x"%struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "PenStyle", 1, struct.unpack("<i",value[12:16])[0],2,12,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Width", 1, struct.unpack("<i",value[16:20])[0],2,16,3,4,4,"<i")
	# skip 4 bytes
	iter = hd.hdmodel.append(None, None)
	clr = "%02X"%ord(value[26])+"%02X"%ord(value[25])+"%02X"%ord(value[24])
	hd.hdmodel.set (iter, 0, "RGB", 1, clr,2,24,3,3,4,"clr")

#39
def CreateBrushIndirect (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "ObjID", 1, "0x%0x"%struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "BrushStyle", 1, struct.unpack("<i",value[12:16])[0],2,12,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	clr = "%02X"%ord(value[18])+"%02X"%ord(value[17])+"%02X"%ord(value[16])
	hd.hdmodel.set (iter, 0, "RGB", 1, clr,2,16,3,3,4,"clr")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Hatch", 1, struct.unpack("<i",value[20:24])[0],2,20,3,4,4,"<i")

#40
def DeleteObject (hd, size, value):
	SelectObject (hd, size, value)

#41
def AngleArc (hd, size, value):
	PointL (hd, value, 8, "C")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Radius", 1, struct.unpack("<I",value[16:20])[0],2,16,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "StartAng", 1, struct.unpack("<f",value[20:24])[0],2,20,3,4,4,"<f")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "SweepAng", 1, struct.unpack("<f",value[24:28])[0],2,24,3,4,4,"<f")

#42
def Ellipse (hd, size, value):
	Rectangle (hd, size, value)

#43
def Rectangle (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "xS", 1, struct.unpack("<i",value[8:12])[0],2,8,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "yS", 1, struct.unpack("<i",value[12:16])[0],2,12,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "xE", 1, struct.unpack("<i",value[16:20])[0],2,16,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "yE", 1, struct.unpack("<i",value[20:24])[0],2,20,3,4,4,"<i")

#44
def RoundRect (hd, size, value):
	Rectangle (hd, size, value)
	PointL (hd, value, 24, "R")

#45
def Arc (hd, size, value):
	Rectangle (hd, size, value)
	PointL (hd, value, 24, "S")
	PointL (hd, value, 32, "E")

#46
def Chord (hd, size, value):
	Arc (hd, size, value)

#47
def Pie (hd, size, value):
	Arc (hd, size, value)

#48
def SelectPalette (hd, size, value):
	SelectObject (hd, size, value)

#54
def LineTo (hd, size, value):
	SetWindowExtEx (hd, size, value)

#55
def ArcTo (hd, size, value):
	Arc (hd, size, value)

#56
def Polydraw (hd, size, value):
	Polybezier (hd, size, value)
	[count] = struct.unpack("<i",value[24:28])
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Count", 1, count,2,24,3,4)
	for i in range(count):
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "abType %d"%i, 1, str(value[count*4+28+i]),2,count*4+28+i,3,1,4,"b")

#57
def SetArcDirection (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "ArcDirection", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#58
def SetMiterLimit (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "MitterLimit", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#59
def BeginPath (hd, size, value):
	return

#60
def EndPath (hd, size, value):
	return

#61
def CloseFigure (hd, size, value):
	return

#62
def FillPath (hd, size, value):
	Rectangle (hd, size, value)

#63
def StrokeAndFillPath (hd, size, value):
	Rectangle (hd, size, value)

#64
def StrokePath (hd, size, value):
	Rectangle (hd, size, value)

#65
def FlattenPath (hd, size, value):
	return

#66
def WidenPath (hd, size, value):
	return

#67
def SelectClipPath (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "RegionMode", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#68
def AbortPath (hd, size, value):
	return

#0x46
def GDIComment (hd, size, value):
	type = value[0xC:0x10]
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Type", 1, type,2,0xc,3,4,4,"txt")
	if type == '\x47\x44\x49\x43':
		ctype = struct.unpack("<I",value[0x10:0x14])[0]
		ct = "unknown"
		if gc_ids.has_key(ctype):
			ct = gc_ids[ctype]
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "PubComment ID", 1, "%d (%s)"%(ctype,ct),2,0x10,3,4,4,"<I")
		if gcfunc_ids.has_key(ctype):
			gcfunc_ids[ctype](hd,value)

#0x49
def InvertRgn (hd, size, value):
	Rectangle (hd,size,value)
	iter = hd.hdmodel.append(None, None)
	rds = struct.unpack("<I",value[0x18:0x1c])[0]
	hd.hdmodel.set (iter, 0, "RgnDataSize", 1, rds,2,0x18,3,4,4,"<I")
	#FIXME! Add RegionData->RegionDataHeader

#0x55
def Polybezier16 (hd, size, value):
	Rectangle (hd, size, value)
	iter = hd.hdmodel.append(None, None)
	[count] = struct.unpack("<i",value[24:28])
	hd.hdmodel.set (iter, 0, "Count", 1, count,2,24,3,4,4,"<i")
	for i in range(count):
		PointS (hd, value, i*4+28, str(i))

#0x56
def Polygon16 (hd, size, value):
	Polybezier16 (hd, size, value)

#0x57
def Polyline16 (hd, size, value):
	Polybezier16 (hd, size, value)

#0x58
def PolybezierTo16 (hd, size, value):
	Polybezier16 (hd, size, value)

#0x59
def PolylineTo16 (hd, size, value):
	Polybezier16 (hd, size, value)

#0x5a
def PolyPolyline16 (hd, size, value):
	Rectangle (hd, size, value)
	iter = hd.hdmodel.append(None, None)
	[numpoly] = struct.unpack("<i",value[24:28])
	hd.hdmodel.set (iter, 0, "NumOfPoly", 1, numpoly,2,24,3,4,4,"<i")
	iter = hd.hdmodel.append(None, None)
	[count] = struct.unpack("<i",value[28:32])
	hd.hdmodel.set (iter, 0, "Count", 1, count,2,28,3,4,4,"<i")
	for i in range(numpoly):
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "PolyPnt %d"%i, 1, struct.unpack("<I",value[i*4+32:i*4+36])[0],2,i*4+32,3,4,4,"<I")
	for i in range(count):
		PointS (hd, value, i*4+32+numpoly*4, str(i))

#0x5b
def PolyPolygon16 (hd, size, value):
	PolyPolyline16 (hd, size, value)

#0x5c
def Polydraw16 (hd, size, value):
	Polybezier16 (hd, size, value)
	[count] = struct.unpack("<i",value[24:28])
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Count", 1, count,2,28,3,4,4,"<i")
	for i in range(count):
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "abType %d"%i, 1, str(value[count*4+28+i]),2,count*4+28+i,3,1,4,"b")

#95
def ExtCreatePen (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "ObjID", 1, "0x%0x"%struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "offBmi", 1, struct.unpack("<I",value[12:16])[0],2,12,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "cbBmi", 1, struct.unpack("<I",value[16:20])[0],2,16,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "offBits", 1, struct.unpack("<I",value[20:24])[0],2,20,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "cbBits", 1, struct.unpack("<I",value[24:28])[0],2,24,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "PenStyle", 1, struct.unpack("<I",value[24:28])[0],2,28,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Width", 1, struct.unpack("<I",value[32:36])[0],2,32,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "BrushStyle", 1, struct.unpack("<I",value[36:40])[0],2,36,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	clr = "%02X"%ord(value[42])+"%02X"%ord(value[41])+"%02X"%ord(value[40])
	hd.hdmodel.set (iter, 0, "RGB", 1, clr,2,40,3,3,4,"clr")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "BrushHatch", 1, struct.unpack("<I",value[44:48])[0],2,44,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	[numstyle] = struct.unpack("<I",value[48:52])
	hd.hdmodel.set (iter, 0, "NumEntryStyle", 1, numstyle,2,48,3,4,4,"<I")
	for i in range(numstyle):
		iter = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter, 0, "Dash/Gap %d"%i, 1, struct.unpack("<I",value[52+i*4:56+i*4])[0],2,52+i*4,3,4,4,"<I")
	# Optional BitmapBuffer
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "BitmapBuffer", 1, "(Optional)",2,52+numstyle*4,3,0)

#98
def SetICMMode (hd, size, value):
	SetBKMode (hd, size, value)

#0x64
def SetColorSpace (hd, size, value):
	SelectObject (hd, size, value)

#0x65
def DeleteColorSpace (hd, size, value):
	SelectObject (hd, size, value)

#0x6d
def ForceUFIMapping (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "ChkSum", 1, struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Idx", 1, struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")

#0x73
def SetLayout (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "LayoutMode", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

#0x79
def ClrMatchToTargetW (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	dwAction = struct.unpack("<I",value[0x8:0xc])[0]
	dt = "unknown"
	if ColorSpace.has_key(dwAction):
		dt = ColorSpace[dwAction]
	hd.hdmodel.set (iter, 0, "dwAction", 1, "%d (%s)"%(dwAction,dt),2,8,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	dwFlags = struct.unpack("<I",value[0xc:0x10])[0]
	dt = "unknown"
	if ColorMatchToTarget.has_key(dwFlags):
		dt = ColorMatchToTarget[dwFlags]
	hd.hdmodel.set (iter, 0, "dwFlags", 1, "%d (%s)"%(dwFlags,dt),2,0xc,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	cbName = struct.unpack("<I",value[0x10:0x14])[0]
	hd.hdmodel.set (iter, 0, "cbName", 1, "%d"%cbName,2,0x10,3,4,4,"<I")
	iter = hd.hdmodel.append(None, None)
	cbData = struct.unpack("<I",value[0x14:0x18])[0]
	hd.hdmodel.set (iter, 0, "cbData", 1, "%d"%cbData,2,0x14,3,4,4,"<I")
	txt = unicode(value[0x18:0x18+cbName*2],"utf-16")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Name", 1, txt,2,0x18,3,cbName*2,4,"utxt")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Data",2,0x18+cbName*2,3,cbData,4,"txt")

gc_ids = {0x80000001:"WindowsMetafile",2:"BeginGroup", 3:"EndGroup",
	0x40000004:"MultiFormats",
	0x00000040:"UNICODE_STRING",0x00000080:"UNICODE_END"} #last two must not be used

gcfunc_ids = {
	#0x80000001:"WindowsMetafile",
	2:GC_BeginGroup,
	3:GC_EndGroup,
	#0x40000004:"MultiFormats"
	}

emr_ids = {1:Header,2:Polybezier,3:Polygon,4:Polyline,5:PolybezierTo,\
	6:PolylineTo,7:PolyPolyline,8:PolyPolygon,9:SetWindowExtEx,0xa:SetWindowOrgEx,\
	0xb:SetViewportExtEx,0xc:SetViewportOrgEx,0xd:SetBrushOrgEx,\
	#0xe:'EOF',0xf:'SetPixelV',\
	0x10:SetMapperFlags,0x11:SetMapMode,0x12:SetBKMode,0x13:SetPolyfillMode,0x14:SetRop2,\
	0x15:SetStretchBltMode,0x16:SetTextAlign,0x17:SetColorAdjustment,0x18:SetTextColor,\
	0x19:SetBKColor,0x1a:OffsetClipRgn,0x1b:MoveToEx,\
	#0x1c:'SetMetaRgn',
	0x1d:ExcludeClipRect,\
	0x1e:IntersectClipRect,0x1f:ScaleViewportExtEx,0x20:ScaleWindowExtEx,0x21:SaveDC,\
	0x22:RestoreDC,0x23:SetWorldTransform,0x24:ModifyWorldTransform,0x25:SelectObject,\
	0x26:CreatePen,0x27:CreateBrushIndirect,0x28:DeleteObject,\
	0x29:AngleArc,
	0x2a:Ellipse, 0x2b:Rectangle,0x2c:RoundRect,0x2d:Arc,0x2e:Chord,0x2f:Pie,0x30:SelectPalette,\
	#0x31:'CreatePalette',0x32:'SetPaletteEntries',0x33:'ResizePalette',0x34:'RealizePalette',\
	#0x35:'ExtFloodFill',
	0x36:LineTo,0x37:ArcTo,0x38:Polydraw,0x39:SetArcDirection,0x3a:SetMiterLimit,\
	0x3b:BeginPath,0x3c:EndPath,0x3d:CloseFigure,0x3e:FillPath,0x3f:StrokeAndFillPath,\
	0x40:StrokePath,0x41:FlattenPath,0x42:WidenPath,0x43:SelectClipPath,0x44:AbortPath,\
	0x46:GDIComment,
	#0x47:'FillRgn',0x48:'FrameRgn',
	0x49:InvertRgn,
	#0x4a:'PaintRgn',0x4b:'ExtSelectClipRgn',\
	#0x4c:'BitBlt',0x4d:'StretchBlt',0x4e:'MaskBlt',0x4f:'PlgBlt',0x50:'SetDIBitsToDevice',0x51:'StretchDIBits',\
	#0x52:'ExtCreateFontIndirectW',0x53:'ExtTextOutA',0x54:'ExtTextOutW',
	0x55:Polybezier16,0x56:Polygon16,0x57:Polyline16,0x58:PolybezierTo16,0x59:PolylineTo16,0x5a:PolyPolyline16,0x5b:PolyPolygon16,\
	0x5c:Polydraw16,
	#0x5d:'CreateMonoBrush',0x5e:'CreateDIBPatternBrushPT',
	0x5f:ExtCreatePen,\
	#0x60:'PolyTextOutA',0x61:'PolyTextOutW',
	0x62:SetICMMode,
	#0x63:'CreateColorSpace',
	0x64:SetColorSpace,0x65:DeleteColorSpace,
	#0x66:'GLSRecord',0x67:'GLSBoundedRecord',0x68:'PixelFormat',0x69:'DrawEscape',\
	#0x6a:'ExtEscape',0x6b:'StartDoc',0x6c:'SmallTextOut',
	0x6d:ForceUFIMapping,
	#0x6e:'NamedEscape',\
	#0x6f:'ColorCorrectPalette',0x70:'SetICMProfileA',0x71:'SetICMProfileW',0x72:'AlphaBlend',\
	0x73:SetLayout,\
	#0x74:'TransparentBlt',0x76:'GradientFill',0x77:'SetLinkedUFI',\
	#0x78:'SetTextJustification',
	0x79:ClrMatchToTargetW,
	#0x7a:'CreateColorSpaceW'
	}
