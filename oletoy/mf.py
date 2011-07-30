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

import sys,struct,gtk,gobject

emrplus_ids = {
  0x4001:"E+Header", 0x4002:"E+EOF", 0x4003:"E+Comment", 0x4004:"E+GetDC",
  0x4005:"E+MultiFormatStart", 0x4006:"E+MultiFormatSection",
  0x4007:"E+MultiFormatEnd", 0x4008:"E+Object", 0x4009:"E+Clear",
  0x400A:"E+FillRects", 0x400B:"E+DrawRects", 0x400C:"E+FillPolygon",
  0x400D:"E+DrawLines", 0x400E:"E+FillEllipse", 0x400F:"E+DrawEllipse",
  0x4010:"E+FillPie", 0x4011:"E+DrawPie", 0x4012:"E+DrawArc",
  0x4013:"E+FillRgn", 0x4014:"E+FillPath", 0x4015:"E+DrawPath",
  0x4016:"E+FillClosedCurve", 0x4017:"E+DrawClosedCurve", 0x4018:"E+DrawCurve",
  0x4019:"E+DrawBeziers", 0x401A:"E+DrawImage", 0x401B:"E+DrawImagePoints",
  0x401C:"E+DrawString", 0x401D:"E+SetRenderingOrigin", 0x401E:"E+SetAntiAliasMode",
  0x401F:"E+SetTextRenderingHint", 0x4020:"E+SetTextContrast", 0x4021:"E+SetInterpolationMode",
  0x4022:"E+SetPixelOffsetMode", 0x4023:"E+SetCompositingMode",
  0x4024:"E+SetCompositingQuality", 0x4025:"E+Save", 0x4026:"E+Restore",
  0x4027:"E+BeginContainer", 0x4028:"E+BeginContainerNoParams",
  0x4029:"E+EndContainer", 0x402A:"E+SetWorldTransform",
  0x402B:"E+ResetWorldTransform", 0x402C:"E+MultiplyWorldTransform",
  0x402D:"E+TranslateWorldTransform", 0x402E:"E+ScaleWorldTransform",
  0x402F:"E+RotateWorldTransform", 0x4030:"E+SetPageTransform",
  0x4031:"E+ResetClip", 0x4032:"E+SetClipRect", 0x4033:"E+SetClipPath",
  0x4034:"E+SetClipRgn", 0x4035:"E+OffsetClip", 0x4036:"E+DrawDriverstring",
  0x4037:"E+StrokeFillPath", 0x4038:"E+SerializableObject", 0x4039:"E+SetTSGraphics",
  0x403A:"E+SetTSClip"}

emr_ids = {0:'Unknown', 1:'Header',2:'Polybezier',3:'Polygon',4:'Polyline',5:'PolybezierTo',\
                 6:'PolylineTo',7:'PolyPolyline',8:'PolyPolygon',9:'SetWindowExtEx',10:'SetWindowOrgEx',\
                 11:'SetViewportExtEx',12:'SetViewportOrgEx',13:'SetBrushOrgEx',14:'EOF',15:'SetPixelV',\
                 16:'SetMapperFlags',17:'SetMapMode',18:'SetBKMode',19:'SetPolyfillMode',20:'SetRop2',\
                 21:'SetStretchBltMode',22:'SetTextAlign', 23:'SetColorAdjustment',24:'SetTextColor',\
                 25:'SetBKColor',26:'OffsetClipRgn',27:'MoveToEx',28:'SetMetaRgn',29:'ExcludeClipRect',\
                 30:'IntersectClipRect',31:'ScaleViewportExtEx',32:'ScaleWindowExtEx',33:'SaveDC',\
                 34:'RestoreDC',35:'SetWorldTransform',36:'ModifyWorldTransform',37:'SelectObject',\
                 38:'CreatePen',39:'CreateBrushIndirect',40:'DeleteObject',41:'AngleArc',42:'Ellipse',\
                 43:'Rectangle',44:'RoundRect',45:'Arc',46:'Chord',47:'Pie',48:'SelectPalette',\
                 49:'CreatePalette',50:'SetPaletteEntries',51:'ResizePalette',52:'RealizePalette',\
                 53:'ExtFloodFill',54:'LineTo',55:'ArcTo',56:'Polydraw',57:'SetArcDirection',58:'SetMiterLimit',\
                 59:'BeginPath',60:'EndPath',61:'CloseFigure',62:'FillPath',63:'StrokeAndFillPath',\
                 64:'StrokePath',65:'FlattenPath',66:'WidenPath',67:'SelectClipPath',68:'AbortPath', ##69 is missed
                 70:'GDIComment',71:'FillRgn',72:'FrameRgn',73:'InvertRgn',74:'PaintRgn',75:'ExtSelectClipRgn',\
                 76:'BitBlt',77:'StretchBlt',78:'MaskBlt',79:'PlgBlt',80:'SetDIBitsToDevice',81:'StretchDIBits',\
                 82:'ExtCreateFontIndirectW',83:'ExtTextOutA',84:'ExtTextOutW',85:'Polybezier16',86:'Polygon16',\
                 87:'Polyline16',88:'PolybezierTo16',89:'PolylineTo16',90:'PolyPolyline16',91:'PolyPolygon16',\
                 92:'Polydraw16',93:'CreateMonoBrush',94:'CreateDIBPatternBrushPT',95:'ExtCreatePen',\
                 96:'PolyTextOutA',97:'PolyTextOutW',98:'SetICMMode',99:'CreateColorSpace',100:'SetColorSpace',\
                 101:'DeleteColorSpace',102:'GLSRecord',103:'GLSBoundedRecord',104:'PixelFormat',105:'DrawEscape',\
                 106:'ExtEscape',107:'StartDoc',108:'SmallTextOut',109:'ForceUFIMapping',110:'NamedEscape',\
                 111:'ColorCorrectPalette',112:'SetICMProfileA',113:'SetICMProfileW',114:'AlphaBlend',\
                 115:'SetLayout',116:'TransparentBlt',117:'Reserved_117',118:'GradientFill',119:'SetLinkedUFI',
                 120:'SetTextJustification',121:'ColorMatchToTargetW',122:'CreateColorSpaceW'}

wmr_ids = {0:'Unknown',1:'Aldus_Header',2:'CLP_Header16',3:'CLP_Header32',4:'Header',
            30:'SaveDC', 295:'RestoreDC', 332:'ResetDc', 
            
            53:'RealizePalette', 55:'SetPalEntries', 247:'CreatePalette', 313:'ResizePalette',564:'SelectPalette', 1078:'AnimatePalette', 
            79:'StartPage', 80:'EndPage', 82:'AbortDoc', 94:'EndDoc', 333:'StartDoc', 
            
            248:'CreateBrush', 322:'DibCreatePatternBrush', 505:'CreatePatternBrush',
            762:'CreatePenIndirect',763:'CreateFontIndirect', 764:'CreateBrushIndirect', 765:'CreateBitmapIndirect', 
            496:'DeleteObject', 301:'SelectObject', 
            
            258:'SetBKMode', 259:'SetMapMode', 260:'SetROP2', 261:'SetRelabs', 262:'SetPolyfillMode', 263:'SetStretchBltMode',
            561:'SetMapperFlags', 
            264:'SetTextCharExtra', 302:'SetTextAlign', 513:'SetBKColor', 521:'SetTextColor', 522:'SetTextJustification', 
            
            298:'InvertRegion', 299:'PaintRegion', 300:'SelectClipRegion',544:'OffsetClipRgn', 552:'FillRegion', 1065:'FrameRegion', 1791:'CreateRegion',
            1045:'ExcludeClipRect', 1046:'IntersectClipRect',
            523:'SetWindowOrgEx', 524:'SetWindowExtEx',525:'SetViewportOrgEx', 526:'SetViewportExtEx', 527:'OffsetWindowOrg', 529:'OffsetViewportOrgEx',
            1040:'ScaleWindowExtEx', 1042:'ScaleViewportExtEx',
            
            1049:'FloodFill', 1352:'ExtFloodFill', 1574:'Escape', 
            
            531:'LineTo', 532:'MoveTo', 804:'Polygon', 805:'Polyline', 1048:'Ellipse', 1051:'Rectangle', 1055:'SetPixel', 
            1336:'PolyPolygon', 1564:'RoundRect', 2071:'Arc', 2074:'Pie', 2096:'Chord', 
            1313:'TextOut', 1583:'DrawText',2610:'ExtTextOut',
            1790:'CreateBitmap', 1565:'PatBlt', 2338:'BitBlt', 2368:'DibBitblt', 2851:'StretchBlt', 2881:'DibStretchBlt', 3379:'SetDibToDev', 3907:'StretchDIBits'}

def emf_gentree ():
	#							Record/Group Name		Rec. Type		Min. Length
	model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING)
	view = gtk.TreeView(model)
	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn('Group/Record', renderer, text=0)
	column2 = gtk.TreeViewColumn('Length', renderer, text=2)
	view.append_column(column)
	view.append_column(column2)

	# Bitmap Record Types
	bmprec = (0x72, 0x4c, 0x4e, 0x4f, 0x50, 0x4d, 0x51,0x74)
	# CLipping Record Types
	cliprec = (0x1a, 0x1c, 0x1d, 0x1e, 0x43, 0x4b)

	# Comment Record Type and Control Record Types
	ctrlrec = (0x46, 0x1, 0xE)

	# Drawing Record Types
	drawrec= ((0x2,28), (0x3,28), (0x4,28), (0x5,28), (0x6,28), (0x7,32), (0x8,28), (0xF,20), (0x29, 28), (0x2a, 24), (0x2b,24), (0x2c,32), (0x2d, 40), (0x2e, 40), (0x2f,40),\
			  (0x35,24), (0x36,16), (0x37, 40), (0x38,28), (0x3e,24), (0x3f,24), (0x40,24), (0x47,32), (0x48,40), (0x4a,28), (0x53, 36), (0x54,36), (0x55,28),\
			  (0x56,28),(0x57,28), (0x58,28), (0x59,28), (0x5a,32), (0x5b,32), (0x5c,28), (0x60,36), (0x61,36), (0x6c,52), (0x76,36))

	# Escape Record Types
	escrec = (0x69, 0x6a, 0x6e)
	
	# Object Creation Record Types
	objcrec = ((0x5d,32),  (0x5e,32), (0x5f,32), (0x7a,20), (0x26,28), (0x27,24), (0x31,12), (0x52,16), (0x63,12))
	
	# Object Manipulation Record Types
	objmrec = (0x25, 0x28, 0x30, 0x32, 0x33, 0x64, 0x65, 0x6f)
	
	# OpenGL Record Types
	## 0x66, 0x67
	
	# Path Bracket Record Types
	pathrec = (0x3b, 0x3c, 0x3d, 0x41, 0x42, 0x44)
	
	# State Record Types
	staterec = (0xa, 0xb, 0xc, 0xd, 0x17, 0x1b, 0x1f, 0x9, 0x10, 0x11, 0x12, 0x13, 0x14, 0x15,\
				0x16, 0x18, 0x19, 0x20, 0x21, 0x22, 0x34, 0x39, 0x3a, 0x49, 0x62, 0x68, 0x6d,\
				0x70, 0x71, 0x73, 0x77, 0x78, 0x79)

	# Transform Record Types
	## 0x23, 0x24

	iter = model.append(None, None)
	model.set(iter, 0, "Bitmap Records", 1, -1, 2, "")
	for i in range (len(bmprec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[bmprec[i]], 1, bmprec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "Clipping Records", 1, -1, 2, "")
	for i in range (len(cliprec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[cliprec[i]], 1, cliprec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "Comment & Control Records", 1, -1, 2, "")
	for i in range (len(ctrlrec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[ctrlrec[i]], 1, ctrlrec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "Drawing Records", 1, -1, 2, "")
	for i in range (len(drawrec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[drawrec[i][0]], 1, drawrec[i][0], 2, drawrec[i][1])

	iter = model.append(None, None)
	model.set(iter, 0, "Escape Records", 1, -1, 2, "")
	for i in range (len(escrec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[escrec[i]], 1, escrec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "Object Creation Records", 1, -1, 2, "")
	for i in range (len(objcrec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[objcrec[i][0]], 1, objcrec[i][0], 2, objcrec[i][1])

	iter = model.append(None, None)
	model.set(iter, 0, "Object Modification Records", 1, -1, 2, "")
	for i in range (len(objmrec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[objmrec[i]], 1, objmrec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "OpenGL Records", 1, -1, 2, "")
	niter = model.append (iter, None)
	model.set(niter, 0, emr_ids[0x66], 1, 0x66, 2, 8)
	niter = model.append (iter, None)
	model.set(niter, 0, emr_ids[0x67], 1, 0x67, 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "Path Bracket Records", 1, -1, 2, "")
	for i in range (len(pathrec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[pathrec[i]], 1, pathrec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "State Records", 1, -1, 2, "")
	for i in range (len(staterec)):
		niter = model.append (iter, None)
		model.set(niter, 0, emr_ids[staterec[i]], 1, staterec[i], 2, 8)

	iter = model.append(None, None)
	model.set(iter, 0, "Transform Records", 1, -1, 2, "")
	niter = model.append (iter, None)
	model.set(niter, 0, emr_ids[0x23], 1, 0x23, 2, 8)
	niter = model.append (iter, None)
	model.set(niter, 0, emr_ids[0x24], 1, 0x24, 2, 8)

	return model,view


def mf_open (buf,page):
	offset = 0
	if page.type == 'EMF':
	  while offset < len(buf) - 8:
		newT = struct.unpack('<I', buf[offset:offset+4])[0]
		newL = struct.unpack('<I', buf[offset+4:offset+8])[0]
		newV = buf[offset:offset+newL]
		rname = emr_ids[newT]
		iter1 = page.model.append(None,None)
		page.model.set_value(iter1,0,rname)
		page.model.set_value(iter1,1,("emf",newT))
		page.model.set_value(iter1,2,newL)
		page.model.set_value(iter1,3,newV)
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		#print offset, newT, rname, newL
		if newT == 0x46: # GDIComment
			eplen = struct.unpack("<I",buf[offset+0x8:offset+0xc])[0]
			eptype = buf[offset+0xc:offset+0x10]
			if eptype == '\x45\x4d\x46\x2b':
			  i = 0
			  while i < eplen - 4:
				try:
				  eprid = struct.unpack('<H',buf[offset+i+0x10:offset+i+0x12])[0]
				  eprlen = struct.unpack('<I',buf[offset+i+0x14:offset+i+0x18])[0]
				  eprname = "%02x"%eprid
				  if emrplus_ids.has_key(eprid):
					eprname = emrplus_ids[eprid]
				  iter2 = page.model.append(iter1, None)
				  page.model.set(iter2, 0, eprname, 1, ("emf+",eprid))
				  page.model.set(iter2, 2, eprlen)
				  page.model.set(iter2, 3, buf[offset+0x10+i:offset+0x10+i+eprlen], 6, page.model.get_string_from_iter(iter2))
				  i += eprlen
				except:
				  print "Oops"
				  i += eplen
		offset = offset + newL

	elif page.type == 'APWMF' or page.type == 'WMF':
		if page.type == 'APWMF':
		  iter1 = page.model.append(None,None)
		  page.model.set_value(iter1,0,'AP Header')
		  page.model.set_value(iter1,1,("wmf",1))
		  page.model.set_value(iter1,2,22)
		  page.model.set_value(iter1,3,buf[0:22])
		  page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		  offset = 22
		iter1 = page.model.append(None,None)
		page.model.set_value(iter1,0,'WMF Header')
		page.model.set_value(iter1,1,("wmf",4))
		page.model.set_value(iter1,2,18)
		page.model.set_value(iter1,3,buf[offset:offset+18])
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += 18

		while offset < len(buf) - 6:
			[newL] = struct.unpack('<I', buf[offset:offset+4])
			[newT] = struct.unpack('<H', buf[offset+4:offset+6])
			newV = buf[offset:offset+newL*2]
			rname = wmr_ids[newT]
			iter1 = page.model.append(None,None)
			page.model.set_value(iter1,0,rname)
			page.model.set_value(iter1,1,("wmf",newT))
			page.model.set_value(iter1,2,newL*2)
			page.model.set_value(iter1,3,newV)
			page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
			offset = offset + newL*2
			if rname == 'Unknown':
				iter1 = page.model.append(None,None)
				page.model.set_value(iter1,0,'Leftover')
				page.model.set_value(iter1,1,("wmf",'-1'))
				nlen = len(buf)-offset
				nval = buf[offset:]
				page.model.set_value(iter1,2,nlen)
				page.model.set_value(iter1,3,nval)
				page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
				offset += nlen

def mf_save (page, fname, ftype):
	model = page.view.get_model()
	f = open(fname,'w')
	model.foreach (dump_mf_tree, f)
	f.close()

def dump_mf_tree (model, path, parent, f):
	nlen = model.get_value(parent,2)
	value = model.get_value(parent,3)
	if nlen != None:
		f.write(value)
	return False
