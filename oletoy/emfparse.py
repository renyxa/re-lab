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

#70
def GDIComment (hd, size, value):
	type = value[0xC:0x10]
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Type", 1, type,2,0xc,3,4,4,"<I")

#85
def Polybezier16 (hd, size, value):
	Rectangle (hd, size, value)
	iter = hd.hdmodel.append(None, None)
	[count] = struct.unpack("<i",value[24:28])
	hd.hdmodel.set (iter, 0, "Count", 1, count,2,24,3,4,4,"<i")
	for i in range(count):
		PointS (hd, value, i*4+28, str(i))

#86
def Polygon16 (hd, size, value):
	Polybezier16 (hd, size, value)

#87
def Polyline16 (hd, size, value):
	Polybezier16 (hd, size, value)

#88
def PolybezierTo16 (hd, size, value):
	Polybezier16 (hd, size, value)

#89
def PolylineTo16 (hd, size, value):
	Polybezier16 (hd, size, value)

#90
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

#91
def PolyPolygon16 (hd, size, value):
	PolyPolyline16 (hd, size, value)

#92
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

#100
def SetColorSpace (hd, size, value):
	SelectObject (hd, size, value)

#101
def DeleteColorSpace (hd, size, value):
	SelectObject (hd, size, value)

#115
def SetLayout (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "LayoutMode", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")

emr_ids = {1:Header,2:Polybezier,3:Polygon,4:Polyline,5:PolybezierTo,\
	6:PolylineTo,7:PolyPolyline,8:PolyPolygon,9:SetWindowExtEx,10:SetWindowOrgEx,\
	11:SetViewportExtEx,12:SetViewportOrgEx,13:SetBrushOrgEx,\
	#14:'EOF',15:'SetPixelV',\
	16:SetMapperFlags,17:SetMapMode,18:SetBKMode,19:SetPolyfillMode,20:SetRop2,\
	21:SetStretchBltMode,22:SetTextAlign, 23:SetColorAdjustment,24:SetTextColor,\
	25:SetBKColor,26:OffsetClipRgn,27:MoveToEx,\
	#28:'SetMetaRgn',
	29:ExcludeClipRect,\
	30:IntersectClipRect,31:ScaleViewportExtEx,32:ScaleWindowExtEx,33:SaveDC,\
	34:RestoreDC,35:SetWorldTransform,36:ModifyWorldTransform,37:SelectObject,\
	38:CreatePen,39:CreateBrushIndirect,40:DeleteObject,\
	41:AngleArc,
	42:Ellipse, 43:Rectangle,44:RoundRect,45:Arc,46:Chord,47:Pie,48:SelectPalette,\
	#49:'CreatePalette',50:'SetPaletteEntries',51:'ResizePalette',52:'RealizePalette',\
	#53:'ExtFloodFill',
	54:LineTo,55:ArcTo,56:Polydraw,57:SetArcDirection,58:SetMiterLimit,\
	59:BeginPath,60:EndPath,61:CloseFigure,62:FillPath,63:StrokeAndFillPath,\
	64:StrokePath,65:FlattenPath,66:WidenPath,67:SelectClipPath,68:AbortPath,\
	70:GDIComment,
	#71:'FillRgn',72:'FrameRgn',73:'InvertRgn',74:'PaintRgn',75:'ExtSelectClipRgn',\
	#76:'BitBlt',77:'StretchBlt',78:'MaskBlt',79:'PlgBlt',80:'SetDIBitsToDevice',81:'StretchDIBits',\
	#82:'ExtCreateFontIndirectW',83:'ExtTextOutA',84:'ExtTextOutW',
	85:Polybezier16,86:Polygon16,87:Polyline16,88:PolybezierTo16,89:PolylineTo16,90:PolyPolyline16,91:PolyPolygon16,\
	92:Polydraw16,
	#93:'CreateMonoBrush',94:'CreateDIBPatternBrushPT',
	95:ExtCreatePen,\
	#96:'PolyTextOutA',97:'PolyTextOutW',
	98:SetICMMode,
	#99:'CreateColorSpace',
	100:SetColorSpace,101:DeleteColorSpace,
	#102:'GLSRecord',103:'GLSBoundedRecord',104:'PixelFormat',105:'DrawEscape',\
	#106:'ExtEscape',107:'StartDoc',108:'SmallTextOut',109:'ForceUFIMapping',110:'NamedEscape',\
	#111:'ColorCorrectPalette',112:'SetICMProfileA',113:'SetICMProfileW',114:'AlphaBlend',\
	115:SetLayout,\
	#116:'TransparentBlt',118:'GradientFill',119:'SetLinkedUFI',\
	#120:'SetTextJustification',121:'ColorMatchToTargetW',122:'CreateColorSpaceW'
	}
