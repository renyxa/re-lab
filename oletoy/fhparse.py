#!/usr/bin/env python
import sys,struct,zlib
from utils import *

vmp_rec = {
	0x0321:"Name?",
	0x065b:"?",
	0x15e3:"Txt Align", # 0 left, 1 right, 2 center, 3 justify, 
	0x15ea:"?",
	0x15f2:"?",
	0x15f9:"?",
	0x1604:"?",
	0x160b:"?",
	0x1614:"?",
	0x161c:"Spc % Letter Max",
	0x1624:"Spc % Word Max",
	0x162b:"?",
	0x1634:"Spc % Letter Min",
	0x163c:"Spc % Word Min",
	0x1644:"?",
	0x164c:"Spc % Letter Opt",
	0x1654:"Spc % Word Opt",
	0x165c:"?",
	0x1664:"?",
	0x166b:"?",
	0x1674:"?",
	0x167c:"?",
	0x1684:"ParaSpc Below",
	0x168c:"ParaSpc Above",
	0x1691:"TabTable ID",
	0x169c:"BaseLn Shift" ,
	0x16a2:"?",
	0x16aa:"?",
	0x16b1:"?",
	0x16b9:"Txt Color ID",
	0x16c1:"Font ID",
	0x16c9:"?",
	0x16d4:"Hor Scale %",
	0x16dc:"Leading",
	0x16e3:"Leading Type", # 0 +, 1 =, 2 % 
	0x16ec:"Rng Kern %",
	0x16f1:"?",
	0x16fb:"?",
	0x1729:"?",
	0x1734:"?",
	0x1739:"?",
	0x1743:"?",
	0x1749:"Next style?",
	0x1c24:"?",
	0x1c2c:"?",
	0x1c34:"?",
	0x1c3c:"?",
	0x1c43:"?",
	0x1c4c:"?",
	0x1c51:"?",
	0x1c71:"?",
	0x1c7c:"?",
	0x1c84:"?",
	0x1c89:"?",
	}

teff_rec = {
	0x1a91:"Effect Name",
#	0x1ab9:"",
#	0x1ac1:"", 
#	0x1acc:"BG Width", #2.2
#	0x1ad4:"Stroke Width", #2.2
#	0x1adb:"Count",
	}

def hdVMpObj(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if vmp_rec.has_key(rec):
			rname = vmp_rec[rec]
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,d2hex(data[shift+4:shift+6]),shift,6,"txt")
			shift+=6
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8

def hdTEffect(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	shift = 8
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if teff_rec.has_key(rec):
			rname = teff_rec[rec]
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,d2hex(data[shift+4:shift+6]),shift,6,"txt")
			shift+=6
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8

def hdTFOnPath(hd,data,page):
	offset = 0
	[num] = struct.unpack('>h', data[offset+4:offset+6])
	shift = 26
	for i in range(num):
		key = struct.unpack('>h', data[offset+shift:offset+shift+2])[0]
		rec = struct.unpack('>h', data[offset+shift+2:offset+shift+4])[0]
		if teff_rec.has_key(rec):
			rname = teff_rec[rec]
		else:
			rname = '\t\t%04x'%rec
		if rname == "?":
			rname = '\t\t%04x'%rec
		if key == 2:
			add_iter (hd,rname,d2hex(data[shift+4:shift+6]),shift,6,"txt")
			shift+=6
		else:
			add_iter (hd,rname,d2hex(data[shift+4:shift+8]),shift,8,"txt")
			shift+=8

def hdHaftone(hd,data,page):
	offset = 0
	# 0-2 -- link to MName with "Screen" string
	# 2-4.4-6 -- angle
	# 6-8 -- Frequency

pts_types = {0:"corner",1:"connector",2:"curve"}
def hdPath(hd,data,page):
	offset = 0
	# 15 -- flatness
	# 19 -- 0 no Even/Odd no Closed, 1 closed, 2 Even/Odd, 3 Even/Odd + Closed
	# ptype+1 -- 0x1b -- automatic, 0x9 -- no authomatic
	
	shift = offset + 22
	numpts = struct.unpack('>h', data[offset+20:offset+22])[0]
	for i in range(numpts):
		ptype = ord(data[shift+1+i*27])
		add_iter (hd,'Type %d'%i,"%d (%s)"%(ptype,pts_types[ptype]),shift+i*27+1,1,"B")
		x1 = struct.unpack('>H', data[shift+i*27+3:shift+i*27+5])[0] - 1692
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>H', data[shift+i*27+7:shift+i*27+9])[0] - 1584
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'X %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'Y %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift +=8
		x1 = struct.unpack('>H', data[shift+i*27+3:shift+i*27+5])[0] - 1692
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>H', data[shift+i*27+7:shift+i*27+9])[0] - 1584
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'\tXh1 %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'\tYh1 %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift +=8
		x1 = struct.unpack('>H', data[shift+i*27+3:shift+i*27+5])[0] - 1692
		x1f = struct.unpack('>H', data[shift+i*27+5:shift+i*27+7])[0]
		y1 = struct.unpack('>H', data[shift+i*27+7:shift+i*27+9])[0] - 1584
		y1f = struct.unpack('>H', data[shift+i*27+9:shift+i*27+11])[0]
		add_iter (hd,'\tXh2 %d'%i,"%.4f"%(x1+x1f/65536.),shift+i*27+3,4,"txt")
		add_iter (hd,'\tYh2 %d'%i,"%.4f"%(y1+y1f/65536.),shift+i*27+7,4,"txt")
		shift -=16

def hdAGDFont(hd,data,page):
	offset = 0
	fsize = struct.unpack('>H', data[offset+26:offset+28])[0]
	fstyle = ord(data[offset+21])
	fstxt = 'Plain'
	if fstyle == 1:
		fstxt = 'Bold'
	if fstyle == 2:
		fstxt = 'Italic'
	if fstyle == 3:
		fstxt = 'BoldItalic'
	add_iter (hd,'Font Style',fstxt,21,1,"B")
	add_iter (hd,'Font Size',fsize,26,2,">h")

def hdLinearFill(hd,data,page):
	offset = 0
	# 2-4 -- angle1
	# 11 -- overprint
	# 16-20 -- X
	# 20-24 -- Y
	# 24-28 -- <->1
	# 28-30 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 30-32 -- repeat
	pass

def hdNewRadialFill(hd,data,page):
	offset = 0
	# 2-6 -- X
	# 6-10 -- Y
	# 15 -- overprint
	# 22-24 -- angle1
	# 26-30 -- <-> Hndl1
	# 30-32 -- angle2
	# 34-38 -- <-> Hndl2
	# 38-40 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 40-42 -- repeat
	pass

def hdNewContourFill(hd,data,page):
	offset = 0
	# 2-6 -- X
	# 6-10 -- Y
	# 10-12 -- Taper
	# 15 -- overprint
	# 18-20 -- link to ColorList
	# 20-22 -- link to GraphicStyle
	# 22-24 -- angle1
	# 26-30 -- <-> Hndl1
	# 31 -- 1 normal, 0 repeat, 2 reflect, 3 autosize
	# 32-34 -- repeat
	pass 

def hdLensFill(hd,data,page):
	offset = 0
	# 39: 0 -- Transparency, 1 -- Magnify, 2 -- Lighten, 3 -- Darken, 4 -- Invert, 5 -- Monochrome
	# Transparency
	# 8-10.10-12 -- Opacity
	# 26-30 -- X
	# 30-34 -- Y
	# 37: 1 -- CenterPoint, 2 -- ObjOnly, 4 -- Snapshot (flags)
	# Magnify
	# 8-10.10-12 -- mag.coeff
	pass

def hdBendFilter(hd,data,page):
	offset = 0
	# 0-2  -- Size
	# 2-4.4-6 -- X
	# 6-8.8-10 -- Y
	pass

def hdLayer(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	mode = ord(data[offset+9])
	lmtxt = 'Normal'
	if mode&0x10 == 0x10:
		lmtxt = 'Wire'
	if mode&0x1 == 1:
		lmtxt += ' Locked'
	visib = ord(data[offset+17])
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'View mode',lmtxt,offset+9,1,"txt")
	add_iter (hd,'Visible',visib,offset+17,1,"B")

def hdRectangle(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	xform = struct.unpack('>H', data[offset+16:offset+18])[0]
	x1 = struct.unpack('>H', data[offset+18:offset+20])[0] - 1692
	x1f = struct.unpack('>H', data[offset+20:offset+22])[0]
	y1 = struct.unpack('>H', data[offset+22:offset+24])[0] - 1584
	y1f = struct.unpack('>H', data[offset+24:offset+26])[0]
	x2 = struct.unpack('>H', data[offset+26:offset+28])[0] - 1692
	x2f = struct.unpack('>H', data[offset+28:offset+30])[0]
	y2 = struct.unpack('>H', data[offset+30:offset+32])[0] - 1584
	y2f = struct.unpack('>H', data[offset+32:offset+34])[0]
	rtlt = struct.unpack('>H', data[offset+34:offset+36])[0]
	rtltf = struct.unpack('>H', data[offset+36:offset+38])[0]
	rtll = struct.unpack('>H', data[offset+38:offset+40])[0]
	rtllf = struct.unpack('>H', data[offset+40:offset+42])[0]
	if page.version > 10:
		rtrt = struct.unpack('>H', data[offset+42:offset+44])[0]
		rtrtf = struct.unpack('>H', data[offset+44:offset+46])[0]
		rtrr = struct.unpack('>H', data[offset+46:offset+48])[0]
		rtrrf = struct.unpack('>H', data[offset+48:offset+50])[0]
		rbrb = struct.unpack('>H', data[offset+50:offset+52])[0]
		rbrbf = struct.unpack('>H', data[offset+52:offset+54])[0]
		rbrr = struct.unpack('>H', data[offset+54:offset+56])[0]
		rbrrf = struct.unpack('>H', data[offset+56:offset+58])[0]
		rblb = struct.unpack('>H', data[offset+58:offset+60])[0]
		rblbf = struct.unpack('>H', data[offset+60:offset+62])[0]
		rbll = struct.unpack('>H', data[offset+62:offset+64])[0]
		rbllf = struct.unpack('>H', data[offset+64:offset+66])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	add_iter (hd,'XForm',"%02x"%xform,16,2,">h")
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),18,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),22,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),26,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),30,4,"txt")
	if page.version > 10:
		add_iter (hd,'Rad TopLeft (Top)',"%.4f"%(rtlt+rtltf/65536.),34,4,"txt")
		add_iter (hd,'Rad TopLeft (Left)',"%.4f"%(rtll+rtllf/65536.),38,4,"txt")
		add_iter (hd,'Rad TopRight (Top)',"%.4f"%(rtrt+rtrtf/65536.),42,4,"txt")
		add_iter (hd,'Rad TopRight (Right)',"%.4f"%(rtrr+rtrrf/65536.),46,4,"txt")
		add_iter (hd,'Rad BtmRight (Btm)',"%.4f"%(rbrb+rbrbf/65536.),50,4,"txt")
		add_iter (hd,'Rad BtmRight (Right)',"%.4f"%(rbrr+rbrrf/65536.),54,4,"txt")
		add_iter (hd,'Rad BtmLeft (Btm)',"%.4f"%(rblb+rblbf/65536.),58,4,"txt")
		add_iter (hd,'Rad BtmLeft (Left)',"%.4f"%(rbll+rbllf/65536.),62,4,"txt")
	else:
		add_iter (hd,'Rad X',"%d"%rtlt,34,2,">h")
		add_iter (hd,'Rad Y',"%d"%rtll,38,2,">h")
		

def hdOval(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	xform = struct.unpack('>H', data[offset+16:offset+18])[0]
	x1 = struct.unpack('>H', data[offset+18:offset+20])[0] - 1692
	x1f = struct.unpack('>H', data[offset+20:offset+22])[0]
	y1 = struct.unpack('>H', data[offset+22:offset+24])[0] - 1584
	y1f = struct.unpack('>H', data[offset+24:offset+26])[0]
	x2 = struct.unpack('>H', data[offset+26:offset+28])[0] - 1692
	x2f = struct.unpack('>H', data[offset+28:offset+30])[0]
	y2 = struct.unpack('>H', data[offset+30:offset+32])[0] - 1584
	y2f = struct.unpack('>H', data[offset+32:offset+34])[0]
	arc1 = struct.unpack('>H', data[offset+34:offset+36])[0]
	arc1f = struct.unpack('>H', data[offset+36:offset+38])[0]
	arc2 = struct.unpack('>H', data[offset+38:offset+40])[0]
	arc2f = struct.unpack('>H', data[offset+40:offset+42])[0]
	clsd = ord(data[offset+42])
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	add_iter (hd,'XForm',"%02x"%xform,16,2,">h")
	add_iter (hd,'X1',"%.4f"%(x1+x1f/65536.),18,4,"txt")
	add_iter (hd,'Y1',"%.4f"%(y1+y1f/65536.),22,4,"txt")
	add_iter (hd,'X2',"%.4f"%(x2+x2f/65536.),26,4,"txt")
	add_iter (hd,'Y2',"%.4f"%(y2+y2f/65536.),30,4,"txt")
	add_iter (hd,'Arc <>',"%.4f"%(arc1+arc1f/65536.),34,4,"txt")
	add_iter (hd,'Arc ()',"%.4f"%(arc2+arc2f/65536.),38,4,"txt")
	add_iter (hd,'Closed',clsd,42,1,"B")

def hdGroup(hd,data,page):
	offset = 0
	gr_style = struct.unpack('>H', data[offset:offset+2])[0]
	layer = struct.unpack('>H', data[offset+2:offset+4])[0]
	add_iter (hd,'Graphic Style',"%02x"%gr_style,0,2,">H")
	add_iter (hd,'Parent',"%02x"%layer,2,2,">h")
	if data[offset+2:offset+4] == '\xFF\xFF':
		xform = struct.unpack('>H', data[offset+16:offset+18])[0]
		add_iter (hd,'XForm',"%02x"%xform,16,2,">h")

def hdBasicLine(hd,data,page):
	offset = 0
	clr = struct.unpack('>H', data[offset:offset+2])[0] # link to color chunk????
	dash = struct.unpack('>H', data[offset+2:offset+4])[0] # link to linepat chunk
	larr = struct.unpack('>H', data[offset+4:offset+6])[0] # link to arrowpat chunk
	rarr = struct.unpack('>H', data[offset+6:offset+8])[0] # link to arrowpat chunk

	mit = struct.unpack('>H', data[offset+8:offset+10])[0]
	mitf = struct.unpack('>H', data[offset+10:offset+12])[0]
	w = struct.unpack('>H', data[offset+12:offset+14])[0]
	overprint = ord(data[offset+17])
	join = ord(data[offset+18]) # 0 - angle, 1 - round, 2 - square
	cap = ord(data[offset+19]) # 0 - none, 1 - round, 2 - square
	add_iter (hd,'Miter',"%.4f"%(mit+mitf/65536.),8,4,"txt")
	add_iter (hd,'Width',w,12,2,">H")

def hdList(hd,data,page):
	offset = 0
	ltype = struct.unpack('>H', data[offset+10:offset+12])[0]
	ltxt = "%02x"%ltype
	if page.dict.has_key(ltype):
		ltxt += " (%s)"%page.dict[ltype]
		add_iter (hd,'List Type',ltxt,10,2,">H")

def hdColor6(hd,data,page):
	offset = 0
	ustr1 = struct.unpack('>H', data[offset+2:offset+4])[0]
	ustr2 = struct.unpack('>H', data[offset+14:offset+16])[0]
	add_iter (hd,'Name1?',"%02x"%ustr1,2,2,">h")
	add_iter (hd,'Name2?',"%02x"%ustr2,14,2,">h")

hdp = {
	"Rectangle":hdRectangle,
	"BasicLine":hdBasicLine,
	"Oval":hdOval,
	"Group":hdGroup,
	"AGDFont":hdAGDFont,
	"Layer":hdLayer,
	"List":hdList,
	"MList":hdList,
	"BrushList":hdList,
	"Color6":hdColor6,
	"SpotColor6":hdColor6,
	"TintColor6":hdColor6,
	"VMpObj":hdVMpObj,
	"Path":hdPath,
	"TFOnPath":hdTFOnPath,
	"TextColumn":hdTFOnPath,
	"TextInPath":hdTFOnPath,
	"TEffect":hdTEffect,
	"VDict":hdTEffect
	}


class FHDoc():
	def __init__(self,data,page,parent):
		self.version = page.version
		self.data = data
		self.iter = parent
		self.page = page
		self.dictitems = {}
		self.diter = add_pgiter(page,"FH Data","fh","data",self.data,self.iter)
		self.reclist = []

		self.chunks = {
		"AGDFont":self.VMpObj,
		"AGDSelection":self.AGDSelection,
		"ArrowPath":self.ArrowPath,
		"AttributeHolder":self.AttributeHolder,
		"BasicFill":self.BasicFill,
		"BasicLine":self.BasicLine,
		"BendFilter":self.BendFilter,
		"Block":self.Block,
		"BrushList":self.BrushList,
		"Brush":self.Brush,
		"BrushStroke":self.BrushStroke,
		"BrushTip":self.BrushTip,
		"CalligraphicStroke":self.CalligraphicStroke,
		"CharacterFill":self.CharacterFill,
		"ClipGroup":self.ClipGroup,
		"Collector":self.Collector,
		"Color6":self.Color6,
		"CompositePath":self.CompositePath,
		"ConeFill":self.ConeFill,
		"ConnectorLine":self.ConnectorLine,
		"ContentFill":self.ContentFill,
		"ContourFill":self.ContourFill,
		"CustomProc":self.CustomProc,
		"DataList":self.DataList,
		"Data":self.Data,
		"DateTime":self.DateTime,
		"DuetFilter":self.DuetFilter,
		"Element":self.Element,
		"ElemList":self.ElemList,
		"ElemPropLst":self.ElemPropLst,
		"Envelope":self.Envelope,
		"ExpandFilter":self.ExpandFilter,
		"Extrusion":self.Extrusion,
		"FHDocHeader":self.FHDocHeader,
		"Figure":self.Figure,
		"FileDescriptor":self.FileDescriptor,
		"FilterAttributeHolder":self.FilterAttributeHolder,
		"FWBevelFilter":self.FWBevelFilter,
		"FWBlurFilter":self.FWBlurFilter,
		"FWFeatherFilter":self.FWFeatherFilter,
		"FWGlowFilter":self.FWGlowFilter,
		"FWShadowFilter":self.FWShadowFilter,
		"FWSharpenFilter":self.FWSharpenFilter,
		"GradientMaskFilter":self.GradientMaskFilter,
		"GraphicStyle":self.GraphicStyle,
		"Group":self.Group,
		"Guides":self.Guides,
		"Halftone":self.Halftone,
		"ImageFill":self.ImageFill,
		"ImageImport":self.ImageImport,
		"Layer":self.Layer,
		"LensFill":self.LensFill,
		"LinearFill":self.LinearFill,
		"LinePat":self.LinePat,
		"LineTable":self.LineTable,
		"List":self.List,
		"MasterPageDocMan":self.MasterPageDocMan,
		"MasterPageElement":self.MasterPageElement,
		"MasterPageLayerElement":self.MasterPageLayerElement,
		"MasterPageLayerInstance":self.MasterPageLayerInstance,
		"MasterPageSymbolClass":self.MasterPageSymbolClass,
		"MasterPageSymbolInstance":self.MasterPageSymbolInstance,
		"MDict":self.MDict,
		"MList":self.MList,
		"MName":self.MName,
		"MpObject":self.MpObject,
		"MQuickDict":self.MQuickDict,
		"MString":self.MString,
		"MultiBlend":self.MultiBlend,
		"MultiColorList":self.MultiColorList,
		"NewBlend":self.NewBlend,
		"NewContourFill":self.NewContourFill,
		"NewRadialFill":self.NewRadialFill,
		"OpacityFilter":self.OpacityFilter,
		"Oval":self.Oval,
		"Paragraph":self.Paragraph,
		"Path":self.Path,
		"PathTextLineInfo":self.PathTextLineInfo,
		"PatternFill":self.PatternFill,
		"PatternLine":self.PatternLine,
		"PerspectiveEnvelope":self.PerspectiveEnvelope,
		"PerspectiveGrid":self.PerspectiveGrid,
		"PolygonFigure":self.PolygonFigure,
		"Procedure":self.Procedure,
		"PropLst":self.PropLst,
		"PSLine":self.PSLine,
		"RadialFill":self.RadialFill,
		"RadialFillX":self.RadialFillX,
		"RaggedFilter":self.RaggedFilter,
		"Rectangle":self.Rectangle,
		"SketchFilter":self.SketchFilter,
		"SpotColor6":self.SpotColor6,
		"StylePropLst":self.StylePropLst,
		"SwfImport":self.SwfImport,
		"SymbolClass":self.SymbolClass,
		"SymbolInstance":self.SymbolInstance,
		"SymbolLibrary":self.SymbolLibrary,
		"TabTable":self.TabTable,
		"TaperedFill":self.TaperedFill,
		"TaperedFillX":self.TaperedFillX,
		"TEffect":self.TEffect,
		"TextBlok":self.TextBlok,
		"TextColumn":self.TextColumn,
		"TextInPath":self.TextInPath,
		"TFOnPath":self.TFOnPath,
		"TileFill":self.TileFill,
		"TintColor6":self.TintColor6,
		"TransformFilter":self.TransformFilter,
		"TString":self.TString,
		"UString":self.UString,
		"VDict":self.VDict,
		"VMpObj":self.VMpObj,
		"Xform":self.Xform
	}

	def read_recid(self,off):
		if self.data[off:off+2] == '\xFF\xFF':
			rid = struct.unpack('>i', self.data[off:off+4])[0]
			l = 4
		else:
			rid = struct.unpack('>h', self.data[off:off+2])[0]
			l = 2
		return l,rid

	def AGDSelection(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length=4*size+6
		res,rid = self.read_recid(off+12)
		return length+res

	def ArrowPath(self,off,mode=0):
		size =  ord(self.data[off+21])
		res=size*27+30
		return res

	def AttributeHolder(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		return res+L

	def BasicFill(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+4

	def BasicLine(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+18
	
	def BendFilter(self,off,mode=0):
		return 10

	def Block(self,off,mode=0):
		if self.version == 10:
			flags =  struct.unpack('>h', self.data[off:off+2])[0]
			res = 2
			for i in range(21):
				L,rid1 = self.read_recid(off+res)
				res += L
			res += 1
			for i in range(2):
				L,rid1 = self.read_recid(off+res)
				res += L
		else:
			# FIXME! ver11 starts with size==7
			res = 0
			for i in range(12):
				L,rid1 = self.read_recid(off+res)
				res += L
			res += 14
			for i in range(3):
				L,rid1 = self.read_recid(off+res)
				res += L
			res +=1
			for i in range(4):
				L,rid1 = self.read_recid(off+res)
				res += L
		return res

	def Brush(self,off,mode=0):
		res,rid1 = self.read_recid(off)
		L,rid1 = self.read_recid(off+res)
		res += L
		return res

	def BrushList(self,off,mode=0):
		size =  struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 12
		for i in range(size):
			L,rid1 = self.read_recid(off+res)
			res += L
		return res

	def BrushStroke(self,off,mode=0):
		res,rid1 = self.read_recid(off)
		L,rid1 = self.read_recid(off+res)
		res += L
		L,rid1 = self.read_recid(off+res)
		res += L
		return res

	def BrushTip(self,off,mode=0):
		type = struct.unpack('>h', self.data[off:off+2])[0]
		length= 60
		if self.version == 11:
			length=64
		res,rid1 = self.read_recid(off)
		return length+res

	def CalligraphicStroke(self,off,mode=0):
		# FXIME! recid?
		return 16

	def CharacterFill(self,off,mode=0):
		# Warning! Flag?
		return 0

	def ClipGroup(self,off,mode=0):
		res,rid1 = self.read_recid(off)
		L,rid1 = self.read_recid(off+res)
		res += L
		L,rid1 = self.read_recid(off+8+res)
		res += L
		return res+10

	def Collector(self,off,mode=0):
		# FIXME! don't have test files for this one
		return 4


	def Color6(self,off,mode=0):
		length=24
		var = ord(self.data[off+1])
		if var == 4:
			length=28
		if var == 7:
			length=40
		if self.version < 10:
			length-=2
		res,rid1 = self.read_recid(off+2)
		L,rid = self.read_recid(off+12+res)
		return res+length+L

	def CompositePath(self,off,mode=0):
		res,rid1 = self.read_recid(off)
		L,rid1 = self.read_recid(off+res)
		res += L
		L,rid1 = self.read_recid(off+8+res)
		res += L
		return res+8

	def ConeFill(self,off,mode=0):
		res,rid1 = self.read_recid(off)
		L,rid1 = self.read_recid(off+res)
		res += L
		L,rid1 = self.read_recid(off+16+res)
		res += L
		return res+30

	def ConnectorLine(self,off,mode=0):
		num = struct.unpack('>h', self.data[off+20:off+22])[0]
		length= 58+num*27
		return length

	def ContentFill(self,off,mode=0):
		# FIXME! Flag?
		return 0

	def ContourFill(self,off,mode=0):
		if self.version == 10:
			length = 24
		else:
			num = struct.unpack('>h', self.data[off+0:off+2])[0]
			size= struct.unpack('>h', self.data[off+2:off+4])[0]
			length = 0
			while num !=0:
				length = length +10+size*2
				num = struct.unpack('>h', self.data[off+0+length:off+2+length])[0]
				size= struct.unpack('>h', self.data[off+2+length:off+4+length])[0]
			length = length +10+size*2
		return length

	def CustomProc(self,off,mode=0):
		# FIXME! recid?
		return 48

	def Data(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		length= 6+size*4
		return length

	def DataList(self,off,mode=0):
		size= struct.unpack('>h', self.data[off:off+2])[0]
		res = 10
		for i in range(size):
			L,rid = self.read_recid(off+res)
			res += L
		return res

	def DateTime(self,off,mode=0):
		return 14

	def DuetFilter(self,off,mode=0):
		return 14

	def Element(self,off,mode=0):
		return 4

	def ElemList(self,off,mode=0):
		return 4

	def ElemPropLst(self,off,mode=0):
		# FIXME! one more read_recid @6 ?
		size = struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 10
		if size != 0:
			for i in range(size*2):
				l,rid = self.read_recid(off+res)
				res += l
		return res

	def Envelope (self,off,mode=0):
		num = struct.unpack('>h', self.data[off+20:off+22])[0]
		num2 = struct.unpack('>h', self.data[off+43:off+45])[0]
		length = 45+num2*4+num*27
		return length

	def ExpandFilter(self,off,mode=0):
		return 14

	def Extrusion(self,off,mode=0):
		var1 = ord(self.data[off+0x60])
		var2 = ord(self.data[off+0x61])
		length= 96 + self.xform_calc(var1,var2)+2
		return length

	def Figure (self,off,mode=0):
		return 4

	def FHDocHeader(self,off,mode=0):
		# FIXME!
		return 4

	def FilterAttributeHolder(self,off,mode=0):
		res,rid = self.read_recid(off+2)
		L,rid = self.read_recid(off+2)
		res += L
		return res+2

	def FWSharpenFilter(self,off,mode=0):
		return 16

	def FileDescriptor(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off)
		res += L
		size = struct.unpack('>h', self.data[off+5+res:off+7+res])[0]
		res += 7+size
		return res

	def FWBevelFilter(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+28

	def FWBlurFilter(self,off,mode=0):
		return 12

	def FWFeatherFilter(self,off,mode=0):
		return 8

	def FWGlowFilter(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+20

	def FWShadowFilter(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+20

	def GradientMaskFilter(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res

	def GraphicStyle(self,off,mode=0):
		size = 2*struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 6
		for i in range(2+size):
				L,rid = self.read_recid(off+res)
				res += L
		return res

	def Group(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+res+8)
		res += L
		L,rid = self.read_recid(off+res+8)
		res += L
		return res+8

	def Guides(self,off,mode=0):
		size =  struct.unpack('>h', self.data[off:off+2])[0]
		res,rid = self.read_recid(off+2)
		L,rid = self.read_recid(off+2+res)
		res += L
		res += 18 + size*8
		return res

	def Halftone(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+8

	def ImageFill(self,off,mode=0):
		#FIXME! recid
		return 6

	def ImageImport(self,off,mode=0):
		shift = 34
		res,rid = self.read_recid(off)
		res += 10
		for i in range(4):
			L,rid = self.read_recid(off+res)
			res += L
		while ord(self.data[off+shift+res]) != 0:
			shift += 1
		shift += 1
		if self.version == 11:
			shift += 2
		return shift+res

	def Layer(self,off,mode=0):
		length=14
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+10+res)
		res += L
		L,rid = self.read_recid(off+10+res)
		res += L
		return length+res

	def LensFill(self,off,mode=0):
		res,rid = self.read_recid(off)
		return res+38

	def LinearFill(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+12+res)
		res += L
		return res+28

	def LinePat(self,off,mode=0):
		numstrokes = struct.unpack('>h', self.data[off:off+2])[0]
		res = 10+numstrokes*4
		if numstrokes == 0 and self.version == 8:
			res = 28 # for Ver8, to skip 1st 14 bytes of 0s
		return res

	def LineTable(self,off,mode=0):
		size= struct.unpack('>h', self.data[off+2:off+4])[0]
		#FIXME! probably more read_recids required
		res,rid = self.read_recid(off+52)
		return res+2+size*50

	def List(self,off,mode=0):
		size = struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 12
		for i in range(size):
			l,rid = self.read_recid(off+res)
			res += l
		return res

	def MasterPageElement(self,off,mode=0):
		return 14
	
	def MasterPageDocMan(self,off,mode=0):
		return 4

	def MasterPageLayerElement(self,off,mode=0):
		return 14

	def MasterPageLayerInstance(self,off,mode=0):
		var1 = ord(self.data[off+0xe])
		var2 = ord(self.data[off+0xf])
		length=14 + self.xform_calc(var1,var2)+2 +2
		return length

	def MasterPageSymbolClass(self,off,mode=0):
		return 12

	def MasterPageSymbolInstance(self,off,mode=0):
		var1 = ord(self.data[off+0xe])
		var2 = ord(self.data[off+0xf])
		length=14 + self.xform_calc(var1,var2)+2 +2
		return length

	def MList(self,off,mode=0):
		return self.List(off,mode)

	def MName(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		return 4*(size+1)

	def MQuickDict(self,off,mode=0):
		size =  struct.unpack('>h', self.data[off+0:off+2])[0]
		return 7 + size*4
	
	def MString(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		return 4*(size+1)

	def MDict(self,off,mode=0):
		size =  struct.unpack('>h', self.data[off+2:off+4])[0]
		length = 6 + size*4
		return length

	def MpObject (self,off,mode=0):
		return 4

	def MultiBlend(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		return 52 + size*6

	def MultiColorList(self,off,mode=0):
		num= struct.unpack('>h', self.data[off:off+2])[0]
		res = 0
		for i in range(num):
				L,rid = self.read_recid(off+4+i*8+res)
				res += L
		return num*8+res+4

	def NewBlend(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+8+res)
		res += L
		L,rid = self.read_recid(off+8+res)
		res += L
		L,rid = self.read_recid(off+8+res)
		res += L
		return res+34

	def NewContourFill(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+14+res)
		res += L
		L,rid = self.read_recid(off+14+res)
		res += L
		return res+28

	def NewRadialFill(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+16+res)
		res += L
		return res+39

	def OpacityFilter(self,off,mode=0):
		return 4

	def Oval(self,off,mode=0):
		if self.version > 10:
			length=38
		else:
			length=28
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+12+res)
		res += L
		return length+res

	def Paragraph(self,off,mode=0):
		size= struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 6
		for i in range(4):
			L,rid = self.read_recid(off+res)
			res += L
		if size == 1:
			pass
		elif size == 2:
			res += 24
		elif size == 3:
			res += 48
		elif size == 4:
			res += 72
		elif size == 5:
			res += 96
		elif size == 7:
			res += 144
		else:
			print "Paragraph with unknown size!!!",size
			res += 200
		return res+20

	def PathTextLineInfo(self,off,mode=0):
		# FIXME!
		# SHOULD BE VARIABLE, just have no idea about base and multiplier
		length= 46
		return length

	def PatternFill(self,off,mode=0):
		return 10

	def Path(self,off,mode=0):
		size =  struct.unpack('>h', self.data[off:off+2])[0]
		length=128
		var=struct.unpack('>h', self.data[off+20:off+22])[0]
		length = 22 + 27*var
		if size==0:
			var=ord(self.data[off+15])
			length = 16 + 27*var
		if self.data[off+4:off+6] == '\xFF\xFF':
			var=struct.unpack('>h', self.data[off+22:off+24])[0]
			length = 24 + 27*var
		if self.data[off+16:off+18] == '\xFF\xFF':
			var=struct.unpack('>h', self.data[off+24:off+26])[0]
			length = 26 + 27*var
		return length

	def PatternLine(self,off,mode=0):
		# 0-2 -- link to Color
		# 2-10 -- bitmap of the pattern
		# 10-14 -- mitter?
		# 14-16 -- width?
		length= 22
		return length
	
	def PSLine(self,off,mode=0):
		# 0-2 -- link to Color
		# 2-4 -- link to UString with PS commands
		# 4-6 width
		length= 8
		return length
	
	def PerspectiveEnvelope(self,off,mode=0):
		return 177

	def PerspectiveGrid(self,off,mode=0):
		i = 0
		while ord(self.data[off+i]) != 0:
			i += 1
		length=59+i
		return length

	def PolygonFigure(self,off,mode=0):
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+12+res)
		res += L
		return res+47

	def Procedure (self,off,mode=0):
		return 4

	def PropLst(self,off,mode=0):
		size = struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 8
		for i in range(2*size):
			L,rid = self.read_recid(off+res)
			res += L
		return res

	def RadialFill(self,off,mode=0):
		return 16

	def RadialFillX(self,off,mode=0):
		#FIXME! verify for v11 and more v10 files
		length=22 #v11
		if self.version == 10:
			length = 22
		return length

	def RaggedFilter(self,off,mode=0):
		return 16

	def Rectangle(self,off,mode=0):
		length=69 #?ver11?
		if self.version < 11:
			length = 36
		res,rid = self.read_recid(off)
		L,rid = self.read_recid(off+res)
		res += L
		L,rid = self.read_recid(off+12+res)
		res += L
		return length+res

	def SketchFilter(self,off,mode=0):
		return 11

	def SpotColor6(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		shift,recid = self.read_recid(off+2)
		res = 26 + size*4 + shift
#		FIXME! verify it
#		if parser.version < 10:
#			length = 38
		return res

	def SwfImport(self,off,mode=0):
		#FIXME! recid
		return 43

	def StylePropLst(self,off,mode=0):
		size = struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 8
		L,rif = self.read_recid(off+res)
		res += L
		for i in range(size*2):
			L,rif = self.read_recid(off+res)
			res += L
		return res

	def SymbolClass(self,off,mode=0):
		res = 0
		for i in range(5):
			L,rif = self.read_recid(off+res)
			res += L
		return res

	def SymbolInstance(self,off,mode=0):
		shift = 0
		res,rif = self.read_recid(off)
		L,rif = self.read_recid(off+res)
		res += L
		L,rif = self.read_recid(off+res+8)
		res += L
		var1 = ord(self.data[off+res+8])
		var2 = ord(self.data[off+res+9])
		return 10 + res + self.xform_calc(var1,var2)

	def SymbolLibrary(self,off,mode=0):
		size =  struct.unpack('>h', self.data[off+2:off+4])[0]
		res = 12
		for i in range(size+3):
			L,rif = self.read_recid(off+res)
			res += L
		return res

	def TabTable(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		return 4+size*6

	def TaperedFill(self,off,mode=0):
		return 12

	def TaperedFillX(self,off,mode=0):
		# FIXME! Check for ver11 and more ver10 files
		length=18  # v11
		if self.version == 10:
			length = 18
		return length

	def TEffect(self,off,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 8
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			rec = struct.unpack('>h', self.data[off+shift+2:off+shift+4])[0]
			if not rec in teff_rec:
				print 'Unknown TEffect record: %04x'%rec
			if key == 2:
				shift+=6
			else:
				shift+=8
		return shift

	def TextBlok(self,off,mode=0):
		size = struct.unpack('>h', self.data[off:off+2])[0]
		return 4+size*4

	def TextColumn(self,off,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		res = 8
		for i in range(2):
			L,rif = self.read_recid(off+res)
			res += L
		res += 8  # FIXME! check if those are recIDs
		for i in range(3):
			L,rif = self.read_recid(off+res)
			res += L
			
		for i in range(num):
			key = struct.unpack('>h', self.data[off+res:off+res+2])[0]
			if key == 0 or self.data[off+res+4:off+res+6] == '\xFF\xFF':
				res+=8
			else:
				res+=6
		return res

	def TFOnPath(self,off,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 26
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			if key == 2:
				shift+=6
			else:
				shift+=8
		return shift

	def TextInPath(self,off,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 20
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			if self.data[off+shift+4:off+shift+6] == '\xFF\xFF':
				shift += 2
			if key == 0:
				shift+=8
			else:
				shift+=6
		return shift+8

	def TileFill(self,off,mode=0):
		res,rif = self.read_recid(off)
		L,rif = self.read_recid(off+res)
		res += L
		return res+28

	def TintColor6(self,off,mode=0):
		res,rif = self.read_recid(off+16)
		return res+36

	def TransformFilter(self,off,mode=0):
		return 39

	def TString(self,off,mode=0):
		size= struct.unpack('>h', self.data[off+2:off+4])[0]
		res=20
		for i in range(size):
			L,rif = self.read_recid(off+res)
			res += L
		return res

	def UString(self,off,mode=0):
		size = struct.unpack('>H', self.data[off:off+2])[0]
		length = struct.unpack('>H', self.data[off+2:off+4])[0]
		res=4*(size+1)
		if mode == 0:
			return res
		elif mode == 1:
			add_iter(self.page.hd,"RecSize",size,0,2,">H")
			add_iter(self.page.hd,"Len",size,0,2,">H")
			add_iter(self.page.hd,"String",off+4,size-4,"ustr")

	def VDict(self,off,mode=0):
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 8
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			if key == 2:
				shift+=6
			else:
				shift+=8
		return shift

	def VMpObj(self,off,mode=0):
		# FIXME! check for \xFF\xFF
		num = struct.unpack('>h', self.data[off+4:off+6])[0]
		shift = 8
		for i in range(num):
			key = struct.unpack('>h', self.data[off+shift:off+shift+2])[0]
			rec = struct.unpack('>h', self.data[off+shift+2:off+shift+4])[0]
# Activate for debug
#			if not rec in vmp_rec:
#				print 'Unknown VMpObj record: %04x'%rec
			
			if key == 0 or self.data[off+shift+4:off+shift+6] == '\xFF\xFF':
				shift+=8
			else:
				shift+=6
		
		return shift


	def xform_calc(self,var1,var2):
		a5 = not (var1&0x20)/0x20
		a4 = not (var1&0x10)/0x10
		a2 = (var1&0x4)/0x4
		a1 = (var1&0x2)/0x2
		a0 = (var1&0x1)/0x1
		b6 = (var2&0x40)/0x40
		b5 = (var2&0x20)/0x20
		if a2:
			return 0
		xlen = (a5+a4+a1+a0+b6+b5)*4
		return xlen
	
	def Xform(self,off,mode=0):
		var1 = ord(self.data[off])
		var2 = ord(self.data[off+1])
		len1 = self.xform_calc(var1,var2)
		var1 = ord(self.data[off+len1+2])
		var2 = ord(self.data[off+len1+3])
		len2 = self.xform_calc(var1,var2)
		length = len1+len2+4
		return length

	def parse_agd (self):
		offset = 0
		j = 0
		for i in self.reclist:
			j += 1
			if self.dictitems[i] in self.chunks:
				try:
					res = self.chunks[self.dictitems[i]](offset)
					if -1 < res <= len(self.data)-offset:
						add_pgiter(self.page,"[%02x] %s"%(j,self.dictitems[i]),"fh",self.dictitems[i],self.data[offset:offset+res],self.diter)
						offset += res
					else:
						add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
						print "Failed on record %d (%s)"%(j,self.dictitems[i]),res
						print "Next is",self.dictitems[self.reclist[j+1]]
						return
				except:
					add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
					print "Failed on record %d (%s)"%(j,self.dictitems[i])
					print "Next is",self.dictitems[self.reclist[j+1]]
					return
					
			else:
					print "Unknown record type: %s (%02x)"%(self.dictitems[i],j)
					add_pgiter(self.page,"!!! %s"%self.dictitems[i],"fh","unknown",self.data[offset:offset+256],self.diter)
					if j < len(self.reclist):
						add_pgiter(self.page,"!!! %s"%self.dictitems[self.reclist[j]],"fh","unknown","",self.diter)
					return
		add_pgiter(self.page,"FH Tail","fh","tail",self.data[offset:],self.diter)
		print "FH Tail!"

	def parse_list(self,data,offset):
		size = struct.unpack('>L', data[offset:offset+4])[0]
		print '# of items:\t%u'%size
		offset+= 4
		for i in range(size):
			key = struct.unpack('>h', data[offset:offset+2])[0]
			offset+= 2
			self.reclist.append(key)

	def parse_dict (self,data,offset):
		if self.version > 8:
			dictsize = struct.unpack('>h', data[offset:offset+2])[0]
			print 'Dict size:\t%u'%dictsize
			dictiter = add_pgiter(self.page,"FH Dictionary","fh","dict","",self.iter)
			offset+=4
			for i in range(dictsize):
				key = struct.unpack('>h', data[offset:offset+2])[0]
				k = 0
				while ord(data[offset+k+2]) != 0:
					k+=1
				value = data[offset+2:offset+k+2]
				add_pgiter(self.page,"%04x %s"%(key,value),"fh","dval",data[offset:offset+k+3],dictiter)
				offset = offset+k+3
				self.dictitems[key] = value
#		else:
#			#FIXME! need to migrate it
#			offset,items = v8dict(buf,offset,dictiter,page)

		self.page.dict = self.dictitems
		return offset

