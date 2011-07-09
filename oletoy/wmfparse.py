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
	hd.hdmodel.set(iter, 0, "y"+i, 1, struct.unpack("<h",value[offset:offset+2])[0],2,offset,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 0, "x"+i, 1, struct.unpack("<h",value[offset+2:offset+4])[0],2,offset+2,3,2,4,"<h")


#30
def SaveDC (hd, size, value):
	return

#258
def SetBKMode (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Mode", 1, struct.unpack("<H",value[6:8])[0],2,6,3,2,4,"<H")

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

#295
def RestoreDC (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "SavedDC", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")

#301
def SelectObject (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Obj ID", 1, struct.unpack("<H",value[6:8])[0],2,6,3,2,4,"<H")

#302
def SetTextAlign (hd, size, value):
	SetBKMode (hd, size, value)

#496
def DeleteObject (hd, size, value):
	SelectObject (hd, size, value)

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

#762
def CreatePenIndirect (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Style", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Width", 1, struct.unpack("<h",value[8:10])[0],2,8,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Height", 1, struct.unpack("<h",value[10:12])[0],2,10,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	clr = "%02X"%ord(value[12])+"%02X"%ord(value[13])+"%02X"%ord(value[14])
	hd.hdmodel.set (iter, 0, "RGB", 1, clr,2,12,3,3,4,"clrgb")

#764
def CreateBrushIndirect (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Style", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	clr = "%02X"%ord(value[8])+"%02X"%ord(value[9])+"%02X"%ord(value[10])
	hd.hdmodel.set (iter, 0, "RGB", 1, clr,2,8,3,3,4,"clrbg")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "Hatch", 1, struct.unpack("<h",value[12:14])[0],2,12,3,2,4,"<h")


#804
def Polygon (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	[count] = struct.unpack("<H",value[6:8])
	hd.hdmodel.set(iter, 0, "Count", 1, count,2,6,3,2,4,"<H")
	for i in range(count):
		PointS (hd, value, i*4+8, str(i))

#805
def Polyline (hd, size, value):
	Polygon (hd, size, value)

#1040
def ScaleViewportExtEx (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "xNum", 1, struct.unpack("<h",value[6:8])[0],2,6,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "xDenom", 1, struct.unpack("<h",value[8:10])[0],2,8,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "yNum", 1, struct.unpack("<h",value[10:12])[0],2,10,3,2,4,"<h")
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, "yDenom", 1, struct.unpack("<h",value[12:14])[0],2,12,3,2,4,"<h")

#1042
def ScaleWindowExtEx (hd, size, value):
	ScaleViewportExtEx (hd, size, value)


#1048
def Ellipse (hd, size, value):
	Rectangle (hd, size, value)

#1051
def Rectangle (hd, size, value):
	PointS(hd,value,6,"S")
	PointS(hd,value,10,"E")

#1336
def PolyPolygon (hd, size, value):
	iter = hd.hdmodel.append(None, None)
	[numpoly] = struct.unpack("<h",value[6:8]) #24/28
	hd.hdmodel.set (iter, 0, "NumOfPoly", 1, numpoly,2,6,3,2,4,"<h")
	counts = {}
	for i in range(numpoly): #32
		iter = hd.hdmodel.append(None, None)
		cnt = struct.unpack("<H",value[i*2+8:i*2+10])[0]
		hd.hdmodel.set (iter, 0, "PolyPnt %d"%i, 1, cnt,2,i*2+8,3,2,4,"<H")
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



wmr_ids = {
#1:'Aldus_Header',2:'CLP_Header16',3:'CLP_Header32',4:'Header',
30:SaveDC,
#53:'RealizePalette', 55:'SetPalEntries', 247:'CreatePalette', 313:'ResizePalette',564:'SelectPalette', 1078:'AnimatePalette', 
#79:'StartPage', 80:'EndPage', 82:'AbortDoc', 94:'EndDoc', 333:'StartDoc', 
#248:'CreateBrush', 322:'DibCreatePatternBrush', 505:'CreatePatternBrush',
258:SetBKMode, 259:SetMapMode, 260:SetROP2, 262:SetPolyfillMode, 263:SetStretchBltMode,
295:RestoreDC, 
#332:'ResetDc', 
301:SelectObject, 
#561:'SetMapperFlags', 
#264:'SetTextCharExtra',
302:SetTextAlign, #513:'SetBKColor', 521:'SetTextColor', 522:'SetTextJustification', 
#298:'InvertRegion', 299:'PaintRegion', 300:'SelectClipRegion',
496:DeleteObject, 531:LineTo, 532:MoveTo,
#544:'OffsetClipRgn', 552:'FillRegion', 
762:CreatePenIndirect,
#763:'CreateFontIndirect',
764:CreateBrushIndirect, #765:'CreateBitmapIndirect', 
804:Polygon, 805:Polyline, 1048:Ellipse, 1051:Rectangle,
#1065:'FrameRegion', 1791:'CreateRegion',
#1045:'ExcludeClipRect', 1046:'IntersectClipRect',
523:SetWindowOrgEx, 524:SetWindowExtEx,525:SetViewportOrgEx, 526:SetViewportExtEx, 527:OffsetWindowOrg, 529:OffsetViewportOrgEx,
1040:ScaleWindowExtEx, 1042:ScaleViewportExtEx,
#1049:'FloodFill', 1352:'ExtFloodFill', 1574:'Escape', 
#1055:'SetPixel',
1336:PolyPolygon, 1564:RoundRect, 2071:Arc, 2074:Pie, 2096:Chord, 
#1313:'TextOut', 1583:'DrawText',2610:'ExtTextOut',
#1790:'CreateBitmap', 1565:'PatBlt', 2338:'BitBlt', 2368:'DibBitblt', 2851:'StretchBlt', 2881:'DibStretchBlt', 3379:'SetDibToDev', 3907:'StretchDIBits'
}
