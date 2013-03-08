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

UnitType = {0:"World",1:"Display",2:"Pixel",3:"Point",
  4:"Inch",5:"Document",6:"Millimeter"}

TextRenderingHint = {0:"SystemDefault",1:"SingleBitPerPixelGridFit",
	2:"SingleBitPerPixel",3:"AntialiasGridFit",4:"Antialias",
	5:"ClearTypeGridFit"}

SmoothingMode = {0:"Default",1:"HighSpeed",2:"SmoothingModeHighQuality",
	3:"None", 4:"AntiAlias8x4",5:"AntiAlias8x8"}

ObjectType = {0:"Invalid",1:"Brush",2:"Pen",3:"Path",4:"Region",5:"Image",
	6:"Font",7:"StringFormat",8:"ImageAttributes",9:"CustomLineCap"}

PenDataFlags = {0:"Transform", 1:"StartCap", 2:"EndCap", 3:"Join",
	4:"MiterLimit", 5:"LineStyle", 6:"DashedLineCap", 7:"DashedLineOffset",
	8:"DashedLine", 9:"NonCenter", 10:"CompoundLine", 11:"CustomStartCap",
	12:"CustomEndCap"}

BrushDataFlags = {0:"Path",1:"Transform",2:"PresetColors",3:"BlendFactorsH",
	4:"BlendFactorsV",5:"FocusScales",6:"IsGammaCorrected",7:"DoNotTransform"}

BrushType = {0:"SolidColor", 1:"HatchFill", 2:"TextureFill",
	3:"PathGradient", 4:"LinearGradient"}

HatchStyle = {0:"Horizontal", 1:"Vertical", 2:"ForwardDiagonal",
	3:"BackwardDiagonal",4:"LargeGrid",5:"DiagonalCross", 6:"05Percent",
	7:"10Percent", 8:"20Percent", 9:"25Percent", 10:"30Percent", 11:"40Percent",
	12:"50Percent", 13:"60Percent", 14:"70Percent", 15:"75Percent", 16:"80Percent",
	17:"90Percent", 18:"LightDownwardDiagonal", 19:"LightUpwardDiagonal",
	20:"DarkDownwardDiagonal", 21:"DarkUpwardDiagonal", 22:"WideDownwardDiagonal",
	23:"WideUpwardDiagonal", 24:"LightVertical", 25:"LightHorizontal",
	26:"NarrowVertical", 27:"NarrowHorizontal", 28:"DarkVertical",
	29:"DarkHorizontal", 30:"DashedDownwardDiagonal", 31:"DashedUpwardDiagonal",
	32:"DashedHorizontal", 33:"DashedVertical", 34:"SmallConfetti", 35:"LargeConfetti",
	36:"ZigZag", 37:"Wave", 38:"DiagonalBrick", 39:"HorizontalBrick",
	40:"Weave", 41:"Plaid", 42:"Divot", 43:"DottedGrid", 44:"DottedDiamond",
	45:"Shingle", 46:"Trellis", 47:"Sphere", 48:"SmallGrid", 49:"SmallCheckerBoard",
	50:"LargeCheckerBoard", 51:"OutlinedDiamond", 52:"SolidDiamond"}

WrapMode = {0:"Tile",1:"TileFlipX",2:"TileFlipY",3:"TileFlipXY",4:"Clamp"}

PathPointType = {0:"Start", 1:"Line", 3:"Bezier"}

PathPointTypeFlags = {0:"DashMode",1:"PathMarker",2:"RLE",3:"CloseSubpath"} # Added RLE and translated to power for high 4 bits

RegionNodeDataType = {1:"And",2:"Or",3:"Xor",4:"Exclude",5:"Complement",
	0x10000000:"Rect",0x10000001:"Path",0x10000002:"Empty",0x10000003:"Infinite"}

ImageType = {0:"Unknown",1:"Bitmap",2:"Metafile"}

MetafileType = {0:"Wmf",1:"WmfPlaceable",2:"Emf",3:"EmfPlusOnly",4:"EmfPlusDual"}

FontStyleFlags = {0:"Bold", 1:"Italic", 2:"Underline", 3:"Strikeout"}

StrFmtFlagNames = {0:"DirectionRightToLeft",1:"DirectionVertical",
	2:"NoFitBlackBox",3:"DisplayFormatControl",4:"NoFontFallback",
	5:"MeasureTrailingSpaces",6:"NoWrap",7:"LineLimit",8:"NoClip",9:"BypassGDI"}

StrFmtFlagValues = {0:0x1, 1:0x2, 2:0x4, 3:0x20, 4:0x400,5:0x800,
	6:0x1000, 7:0x2000, 8:0x4000, 9:0x80000000}

LangIDnames = {0x0000:"LANG_NEUTRAL", 0x0004:"zh-CHS", 0x007F:"LANG_INVARIANT",
	0x0400:"LANG_NEUTRAL_USER_DEFAULT", 0x0401:"ar-SA", 0x0402:"bg-BG", 0x0403:"ca-ES",
	0x0404:"zh-CHT", 0x0405:"cs-CZ", 0x0406:"da-DK", 0x0407:"de-DE", 0x0408:"el-GR",
	0x0409:"en-US", 0x040A:"es-Tradnl-ES", 0x040B:"fi-FI", 0x040C:"fr-FR", 0x040D:"he-IL",
	0x040E:"hu-HU", 0x040F:"is-IS", 0x0410:"it-IT", 0x0411:"ja-JA", 0x0412:"ko-KR",
	0x0413:"nl-NL", 0x0414:"nb-NO", 0x0415:"pl-PL", 0x0416:"pt-BR", 0x0417:"rm-CH",
	0x0418:"ro-RO", 0x0419:"ru-RU", 0x041A:"hr-HR", 0x041B:"sk-SK", 0x041C:"sq-AL",
	0x041D:"sv-SE", 0x041E:"th-TH", 0x041F:"tr-TR", 0x0420:"ur-PK", 0x0421:"id-ID",
	0x0422:"uk-UA", 0x0423:"be-BY", 0x0424:"sl-SI", 0x0425:"et-EE", 0x0426:"lv-LV",
	0x0427:"lt-LT", 0x0428:"tg-TJ", 0x0429:"fa-IR", 0x042A:"vi-VN", 0x042B:"hy-AM",
	0x042C:"az-Latn-AZ", 0x042D:"eu-ES", 0x042E:"wen-DE", 0x042F:"mk-MK", 0x0430:"st-ZA",
	0x0432:"tn-ZA", 0x0434:"xh-ZA", 0x0435:"zu-ZA", 0x0436:"af-ZA", 0x0437:"ka-GE",
	0x0438:"fa-FA", 0x0439:"hi-IN", 0x043A:"mt-MT", 0x043B:"se-NO", 0x043C:"ga-GB",
	0x043E:"ms-MY", 0x043F:"kk-KZ", 0x0440:"ky-KG", 0x0441:"sw-KE", 0x0442:"tk-TM",
	0x0443:"uz-Latn-UZ", 0x0444:"tt-Ru", 0x0445:"bn-IN", 0x0446:"pa-IN", 0x0447:"gu-IN",
	0x0448:"or-IN", 0x0449:"ta-IN", 0x044A:"te-IN", 0x044B:"kn-IN", 0x044C:"ml-IN",
	0x044D:"as-IN", 0x044E:"mr-IN", 0x044F:"sa-IN", 0x0450:"mn-MN", 0x0451:"bo-CN",
	0x0452:"cy-GB", 0x0453:"km-KH", 0x0454:"lo-LA", 0x0456:"gl-ES", 0x0457:"kok-IN",
	0x0459:"sd-IN", 0x045A:"syr-SY", 0x045B:"si-LK", 0x045D:"iu-Cans-CA", 0x045E:"am-ET",
	0x0461:"ne-NP",0x0462:"fy-NL",  0x0463:"ps-AF",0x0464:"fil-PH",  0x0465:"div-MV",
	0x0468:"ha-Latn-NG", 0x046A:"yo-NG",0x046B:"quz-BO", 0x046C:"nzo-ZA",  0x046D:"ba-RU",
	0x046E:"lb-LU", 0x046F:"kl-GL", 0x0470:"ig-NG", 0x0477:"so-SO", 0x0478:"ii-CN",
	0x047A:"arn-CL",0x047C:"moh-CA",  0x047E:"br-FR", 0x0480:"ug-CN",0x0481:"mi-NZ", 
	0x0482:"oc-FR", 0x0483:"co-FR",0x0484:"gsw-FR", 0x0485:"sah-RU", 0x0486:"qut-GT", 
	0x0487:"rw-RW", 0x0488:"wo-SN", 0x048C:"gbz-AF", 0x0800:"LANG_NEUTRAL_SYS_DEFAULT",
	0x0801:"ar-IQ",0x0804:"zh-CN",  0x0807:"de-CH", 0x0809:"en-GB",0x080A:"es-MX", 
	0x080C:"fr-BE",0x0810:"it-CH",  0x0812:"ko-Johab-KR",0x0813:"nl-BE",  0x0814:"nn-NO",
	0x0816:"pt-PT",  0x081A:"sr-Latn-SP", 0x081D:"sv-FI", 0x0820:"ur-IN", 0x0827:"lt-C-LT",
	0x082C:"az-Cyrl-AZ", 0x082E:"wee-DE", 0x083B:"se-SE", 0x083C:"ga-IE", 0x083E:"ms-BN",
	0x0843:"uz-Cyrl-UZ", 0x0845:"bn-BD", 0x0850:"mn-Mong-CN", 0x0859:"sd-PK", 0x085D:"iu-Latn-CA",
	0x085F:"tzm-Latn-DZ", 0x086B:"quz-EC", 0x0C00:"LANG_NEUTRAL_CUSTOM_DEFAULT", 
	0x0C01:"ar-EG", 0x0C04:"zh-HK", 0x0C07:"de-AT", 0x0C09:"en-AU", 0x0C0A:"es-ES",
	0x0C0C:"fr-CA", 0x0C1A:"sr-Cyrl-CS", 0x0C3B:"se-FI",0x0C6B:"quz-PE",
	0x1000:"LANG_NEUTRAL_CUSTOM",  0x1001:"ar-LY", 0x1004:"zh-SG", 0x1007:"de-LU",
	0x1009:"en-CA", 0x100A:"es-GT", 0x100C:"fr-CH", 0x101A:"hr-BA", 0x103B:"smj-NO",
	0x1400:"LANG_NEUTRAL_CUSTOM_DEFAULT_MUI", 0x1401:"ar-DZ", 0x1404:"zh-MO", 0x1407:"de-LI",
	0x1409:"en-NZ", 0x140A:"es-CR", 0x140C:"fr-LU", 0x141A:"bs-Latn-BA", 0x143B:"smj-SE",
	0x1801:"ar-MA", 0x1809:"en-IE", 0x180A:"es-PA", 0x180C:"ar-MC", 0x181A:"sr-Latn-BA",
	0x183B:"sma-NO", 0x1C01:"ar-TN", 0x1C09:"en-ZA", 0x1C0A:"es-DO", 0x1C1A:"sr-Cyrl-BA",
	0x1C3B:"sma-SE", 0x2001:"ar-OM", 0x2008:"el-2-GR", 0x2009:"en-JM", 0x200A:"es-VE",
	0x201A:"bs-Cyrl-BA", 0x203B:"sms-FI", 0x2401:"ar-YE", 0x2409:"ar-029", 0x240A:"es-CO",
	0x243B:"smn-FI", 0x2801:"ar-SY", 0x2809:"en-BZ", 0x280A:"es-PE", 0x2C01:"ar-JO",
	0x2C09:"en-TT", 0x2C0A:"es-AR", 0x3001:"ar-LB", 0x3009:"en-ZW", 0x300A:"es-EC",
	0x3401:"ar-KW", 0x3409:"en-PH", 0x340A:"es-CL", 0x3801:"ar-AE", 0x380A:"es-UY",
	0x3C01:"ar-BH", 0x3C0A:"es-PY", 0x4001:"ar-QA", 0x4009:"en-IN", 0x400A:"es-BO",
	0x4409:"en-MY", 0x440A:"es-SV", 0x4809:"en-SG", 0x480A:"es-HN", 0x4C0A:"es-NI",
	0x500A:"es-PR", 0x540A:"es-US", 0x7C04:"zh-Hant"} 

StrAlign = {0:"Near",1:"Center",2:"Far"}

StrDgtSubs = {0:"User",1:"None",2:"National",3:"Traditional"}

HotPfx = {0:"None", 1:"Show", 2:"Hide"}

StrTrim = {0:"None", 1:"Character", 2:"Word", 3:"EllipsisCharacter", 4:"EllipsisWord", 5:"EllipsisPath"}

ClampMode = {0:"Rect",1:"Bitmap"}

CustLCapDataType ={0:"Default",1:"AdjustableArrow"}

DrvStrOptFlags = {0:"CmapLookup", 1:"Vertical", 2:"RealizedAdvance", 3:"LimitSubpixel"}

CombineMode = {0:"Replace", 1:"Intersect", 2:"Union", 3:"XOR", 4:"Exclude", 5:"Complement"}

InterpolationMode = {0:"Default",1:"LowQuality",2:"HighQuality",3:"Bilinear",
	4:"Bicubic",5:"NearestNeighbor",6:"HighQualityBilinear",7:"HighQualityBicubic"}

PixelOffsetMode = {0:"Default",1:"HighSpeed",2:"HighQuality",3:"None",4:"Half"}

CompositingQuality = {0:"Default",1:"HighSpeed",2:"HighQuality",3:"GammaCorrected",4:"AssumeLinear"}

CompositingMode = {0:"Over",1:"Copy"}

def PointL (hd, value, offset, i=""):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "x"+i, 1, struct.unpack("<i",value[offset:offset+4])[0],2,offset,3,4,4,"<i")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "y"+i, 1, struct.unpack("<i",value[offset+4:offset+8])[0],2,offset+4,3,4,4,"<i")

def PointF (hd, value, offset, i=""):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sX"%i, 1, struct.unpack("<f",value[offset:offset+4])[0],2,offset,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sY"%i, 1, struct.unpack("<f",value[offset+4:offset+8])[0],2,offset+4,3,4,4,"<f")

def PointS (hd, value, offset, i=""):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sX"%i, 1, struct.unpack("<h",value[offset:offset+2])[0],2,offset,3,2,4,"<h")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sY"%i, 1, struct.unpack("<h",value[offset+2:offset+4])[0],2,offset+2,3,2,4,"<h")

def PointR (hd, value, offset, i=""):
	hb = ord(value[offset])
	iter = hd.model.append(None, None)
	off = 0
	if hb < 0x80: # 1 byte coord
		hd.model.set(iter, 0, "%sX"%i, 1, hb,2,offset,3,1,4,"<h")
		off = 1
	else:
		tv = struct.unpack("<H",value[offset:offset+2])[0]&0x3FFF
		tvs = (hb&0x40)/0x40
		if tvs:
			tv = -tv-1
		hd.model.set(iter, 0, "%sY"%i, 1, tv,2,offset,3,1,4,"<h")
		off = 2
	hb = ord(value[offset+off])
	iter = hd.model.append(None, None)
	off = 0
	if hb < 0x80: # 1 byte coord
		hd.model.set(iter, 0, "%sX"%i, 1, hb,2,offset+off,3,1,4,"<h")
		off += 1
	else:
		tv = struct.unpack("<H",value[offset+off:offset+off+2])[0]&0x3FFF
		tvs = (hb&0x40)/0x40
		if tvs:
			tv = -tv-1
		hd.model.set(iter, 0, "%sY"%i, 1, tv,2,offset,3,1,4,"<h")
		off += 2
	return off

def PointType(value,offset):
	ptype = ord(value[offset])
	ptft = ""
	ptf = (ptype&0xF0)/16
	for j in range(4):
		if ptf&1:
			ptft = PathPointTypeFlags[j]
		ptf /= 2
	ptt = ptype&0xF
	pttt = "unknown"
	if PathPointType.has_key(ptt):
		pttt = PathPointType[ptt]
	return ptft,pttt

def RectF (hd, value, offset, i=""):
	PointF (hd,value,offset,i)
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sWidth"%i, 1, struct.unpack("<f",value[offset+8:offset+12])[0],2,offset+8,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sHeight"%i, 1, struct.unpack("<f",value[offset+12:offset+16])[0],2,offset+12,3,4,4,"<f")

def RectS (hd, value, offset, i=""):
	PointS (he,value,offset,i)
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sWidth"%i, 1, struct.unpack("<f",value[offset+4:offset+6])[0],2,offset+4,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sHeight"%i, 1, struct.unpack("<f",value[offset+6:offset+8])[0],2,offset+6,3,4,4,"<f")

def RGBA (hd, value, offset,i=""):
	clr = "%02X"%ord(value[offset+2])+"%02X"%ord(value[offset+1])+"%02X"%ord(value[offset])+"%02X"%ord(value[offset+3])
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "%s RGBA"%i, 1, clr,2,offset,3,4,4,"clr")

def XFormMtrx (hd, value, offset):
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "m11", 1, struct.unpack("<f",value[offset:offset+4])[0],2,offset,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "m12", 1, struct.unpack("<f",value[offset+4:offset+8])[0],2,offset+4,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "m21", 1, struct.unpack("<f",value[offset+8:offset+12])[0],2,offset+8,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "m22", 1, struct.unpack("<f",value[offset+12:offset+16])[0],2,offset+12,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Dx", 1, struct.unpack("<f",value[offset+16:offset+20])[0],2,offset+16,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set (iter, 0, "Dy", 1, struct.unpack("<f",value[offset+20:offset+24])[0],2,offset+20,3,4,4,"<f")

def PDF_Xform (hd, value, offset):
	XFormMtrx(hd,value,offset)
	return 24

def PDF_StartCap (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  StartCap", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_EndCap (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  EndCap", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_Join (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Join", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_MiterLimit (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Mitter", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_LineStyle (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  LineStyle", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_DashedLineCap (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  DashLineCap", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_DashedLineOffset (hd, value, offset):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  DashLineOffset", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_DashedLine (hd, value, offset):
	iter = hd.model.append(None, None)
	dlsize = struct.unpack("<I",value[0:4])[0]
	hd.model.set(iter, 0, "  DashLineNumElems", 1,"%d"%dlsize,2,offset,3,4,4,"<I")
	for i in range(dlsize):
		iter = hd.model.append(None, None)
		ds = struct.unpack("<I",value[4+i*4:8+i*4])[0]
		hd.model.set(iter, 0, "    DashElem %d"%i, 1, "%d"%ds,2,offset+4+i*4,3,4,4,"<I")
	return (dlsize+1)*4

def PDF_NonCenter (hd, value, offset):
# FIXME! Add Enum
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  PenAlignment", 1,"%d"%struct.unpack("<I",value[0:4])[0],2,offset,3,4,4,"<I")
	return 4

def PDF_CompoundLine (hd, value, offset):
	iter = hd.model.append(None, None)
	dlsize = struct.unpack("<I",value[0:4])[0]
	hd.model.set(iter, 0, "  CompLineNumElems", 1,"%d"%dlsize,2,offset,3,4,4,"<I")
	for i in range(dlsize):
		iter = hd.model.append(None, None)
		ds = struct.unpack("<I",value[4+i*4:8+i*4])[0]
		hd.model.set(iter, 0, "    CompLineElem %d"%i, 1, "%d"%ds,2,offset+4+i*4,3,4,4,"<I")
	return (dlsize+1)*4

def PDF_CustomStartCap (hd, value, offset):
# FIXME! Add parsing of CapData
	iter = hd.model.append(None, None)
	dlsize = struct.unpack("<I",value[0:4])[0]
	hd.model.set(iter, 0, "  CustStartCap", 1,"%d"%dlsize,2,offset,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  CustStartCapData", 1,"",2,offset+4,3,dlsize,4,"<I")
	return dlsize+4

def PDF_CustomEndCap (hd, value, offset):
# FIXME! Add parsing of CapData
	iter = hd.model.append(None, None)
	dlsize = struct.unpack("<I",value[0:4])[0]
	hd.model.set(iter, 0, "  CustEndCap", 1,"%d"%dlsize,2,offset,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  CustEndCapData", 1,"",2,offset+4,3,dlsize,4,"<I")
	return dlsize+4

def BDF_PresetColors (hd, value, offset):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "PresetColor")
	iter = hd.model.append(None, None)
	pcnt = struct.unpack("<I",value[offset:offset+4])[0]
	hd.model.set(iter, 0, "  PosCount", 1, "%d"%pcnt,2,offset,3,4,4,"<I")
	for i in range(pcnt):
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "  BlendPos%d"%i, 1, "%.2f"%struct.unpack("<f",value[offset+4+i*4:offset+8+i*4]),2,offset+4+i*4,3,4,4,"<I")
	for i in range(pcnt):
		RGBA(hd,value,offset+pcnt*4+4+i*4,"  Blend%d Clr"%i)
	return 4+pcnt*8

def BT_SolidColor (hd, value, offset):
	RGBA(hd,value,offset)

def BT_HatchFill (hd, value, offset):
	iter = hd.model.append(None, None)
	hstyle = struct.unpack("<I",value[offset+0:offset+4])[0]
	hst = "unknown"
	if HatchStyle.has_key(hstyle):
		hst = HatchStyle(hstyle)
	hd.model.set(iter, 0, "  HatchStyle", 1, "0x%02X (%s)"%(hstyle,hst),2,offset,3,4,4,"<I")
	RGBA(hd,value,offset+4,"ForeClr ")
	RGBA(hd,value,offset+8,"BackClr ")

def BT_TextureFill (hd, value, offset):
	iter = hd.model.append(None, None)
	bdflags = struct.unpack("<I",value[offset+0:offset+4])[0]
	bdf = []
	bdft = ""
	flags = bdflags
	for i in range(8):
		bdf.append(flags&1)
		flags /= 2
	for i in range(8):
		if bdf[i] == 1:
			bdft += BrushDataFlags[i] + ", "
	bdft = bdft[0:len(bdft)-2]
	hd.model.set(iter, 0, "  BrushDataFlags", 1, "0x%02X (%s)"%(bdflags,bdft),2,offset,3,4,4,"<I")
	iter = hd.model.append(None, None)
	wmode = struct.unpack("<I",value[offset+4:offset+8])[0]
	wmt = ""
	if WrapMode.has_key(wmode):
		wmt = WrapMode[wmode]
	hd.model.set(iter, 0, "  WrapMode", 1, "0x%02X (%s)"%(wmode,wmt),2,offset+4,3,4,4,"<I")
	offset += 8
	for i in range(8):
		if bdf[i] == 1:
			if bdf_ids.has_key(i):
				offset += bdf_ids[i](hd,value,offset)

def BT_PathGradient (hd, value, offset):
	iter = hd.model.append(None, None)
	bdflags = struct.unpack("<I",value[offset+0:offset+4])[0]
	bdf = []
	bdft = ""
	flags = bdflags
	for i in range(8):
		bdf.append(flags&1)
		flags /= 2
	for i in range(8):
		if bdf[i] == 1:
			bdft += BrushDataFlags[i] + ", "
	bdft = bdft[0:len(bdft)-2]
	hd.model.set(iter, 0, "  BrushDataFlags", 1, "0x%02X (%s)"%(bdflags,bdft),2,offset,3,4,4,"<I")
	iter = hd.model.append(None, None)
	wmode = struct.unpack("<I",value[offset+4:offset+8])[0]
	wmt = ""
	if WrapMode.has_key(wmode):
		wmt = WrapMode[wmode]
	hd.model.set(iter, 0, "  WrapMode", 1, "0x%02X (%s)"%(wmode,wmt),2,offset+4,3,4,4,"<I")
	RGBA(hd,value,offset+8,"CenterClr")
	PointF(hd,value,offset+12,"CenterPoint")
	surclrcnt = struct.unpack("<I",value[offset+20:offset+24])[0]
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  SurClrCount", 1, "0x%02X"%surclrcnt,2,offset+20,3,4,4,"<I")
	for i in range(surclrcnt):
		RGBA(hd,value,offset+24+i*4,"SurClr#%s"%i)
	if bdf[0]:
		#Boundary path object
		iter = hd.model.append(None, None)
		psize = struct.unpack("<I",value[offset+24+surclrcnt*4:offset+28+surclrcnt*4])[0]
		hd.model.set(iter, 0, "Path Size", 1, "0x%02X"%psize,2,offset+24+surclrcnt*4,3,4,4,"<I")
		ObjPath(hd,value,offset+16+surclrcnt*4)
		offset += psize+28+surclrcnt*4
	else:
		#Boundary point object
		numofpts = struct.unpack("<I",value[offset+28+surclrcnt*4:offset+32+surclrcnt*4])[0]
		for i in range(numofpts):
			PointF(hd,value,offset+32+surclrcnt*4+i*8,"BndrPnt#%s"%i)
		offset += 32+surclrcnt*4+numofpts*8
	for i in range(7): # have to skip first flag
		if bdf[i+1] == 1:
			if bdf_ids.has_key(i+1):
				offset += bdf_ids[i+1](hd,value,offset)

def BT_LinearGradient (hd, value, offset):
	iter = hd.model.append(None, None)
	bdflags = struct.unpack("<I",value[offset:offset+4])[0]
	bdf = []
	bdft = ""
	flags = bdflags
	for i in range(8):
		bdf.append(flags&1)
		flags /= 2
	for i in range(8):
		if bdf[i] == 1:
			bdft += BrushDataFlags[i] + ", "
	bdft = bdft[0:len(bdft)-2]
	hd.model.set(iter, 0, "  BrushDataFlags", 1, "0x%02X (%s)"%(bdflags,bdft),2,offset,3,4,4,"<I")
	iter = hd.model.append(None, None)
	wmode = struct.unpack("<I",value[offset+4:offset+8])[0]
	wmt = ""
	if WrapMode.has_key(wmode):
		wmt = WrapMode[wmode]
	hd.model.set(iter, 0, "  WrapMode", 1, "0x%02X (%s)"%(wmode,wmt),2,offset+4,3,4,4,"<I")
	PointL(hd,value,offset+8,"s")
	PointL(hd,value,offset+16,"e")
	RGBA(hd,value,offset+24,"StartClr")
	RGBA(hd,value,offset+28,"EndClr")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Rsrv1", 1, "0x%02X"%struct.unpack("<I",value[offset+32:offset+36])[0],2,offset+32,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Rsrv2", 1, "0x%02X"%struct.unpack("<I",value[offset+36:offset+40])[0],2,offset+36,3,4,4,"<I")
	offset += 40
	for i in range(8):
		if bdf[i] == 1:
			if bdf_ids.has_key(i):
				offset += bdf_ids[i](hd,value,offset)

def RegionNode (hd,value,offset,txt=""):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "%sRegionNode"%txt)
	rtype = struct.unpack("<I",value[offset:offset+4])[0]
	rt = "unknown"
	if RegionNodeDataType.has_key(rtype):
		rt = RegionNodeDataType[rtype]
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "  RegionNodeType", 1, rt,2,offset,3,4,4,"<I")
	if rnd_ids.has_key(rtype):
		offset = rnd_ids[rtype](hd,value,offset,i)
	return offset

def RND_Child (hd,value,offset,i):
	offset = RegionNode(hd,value,offset,"Left ")
	offset = RegionNode(hd,value,offset,"Right ")
	return offset

def RND_Rect (hd,value,offset,i):
	RectF (hd,value,offset,"  ")
	offset += 16
	return offset

def RND_Path (hd,value,offset,i):
	iter = hd.model.append(None, None)
	psize = struct.unpack("<I",value[offset:offset+4])[0]
	hd.model.set(iter, 0, "Path Size", 1, "0x%02X"%psize,2,offset,3,4,4,"<I")
	ObjPath(hd,value,offset-8)
	return offset+psize

def RND_Empty (hd,value,offset,i):
	return offset

def ObjBrush (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Brush")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	btype = struct.unpack("<I",value[offset+0x10:offset+0x14])[0]
	bt = "unknown"
	if BrushType.has_key(btype):
		bt = BrushType[btype]
	hd.model.set(iter, 0, "  Type", 1, "0x%02X (%s)"%(btype,bt),2,offset+0x10,3,4,4,"<I")
	if bt_ids.has_key(btype):
		bt_ids[btype](hd,value,offset+0x14)

def ObjPen (hd, value):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Pen")
	ver = struct.unpack("<I",value[0xc:0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Type", 1, "0x%02X"%struct.unpack("<I",value[0x10:0x14])[0],2,0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	pdflags = struct.unpack("<I",value[0x14:0x18])[0]
	pdf = []
	pdft = ""
	flags = pdflags
	for i in range(13):
		pdf.append(flags&1)
		flags /= 2
	for i in range(13):
		if pdf[i] == 1:
			pdft += PenDataFlags[i] + ", "
	pdft = pdft[0:len(pdft)-2]
	hd.model.set(iter, 0, "  PenDataFlags", 1, "0x%02X (%s)"%(pdflags,pdft),2,0x14,3,4,4,"<I")
	iter = hd.model.append(None, None)
	utype = struct.unpack("<I",value[0x18:0x1c])[0]
	ut ="unknown"
	if UnitType.has_key(utype):
		ut = UnitType[utype]
	hd.model.set(iter, 0, "  PenUnits", 1, "0x%02X (%s)"%(utype,ut),2,0x18,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  PenWidth", 1, "%.2f"%struct.unpack("<f",value[0x1c:0x20])[0],2,0x1c,3,4,4,"<f")
	offset = 0x20
	for i in range(12):
		if pdf[i] == 1:
			if pdf_ids.has_key(i):
				offset += pdf_ids[i](hd,value[offset:],offset)
	ObjBrush (hd,value,offset-12) # to adjust ObjBrush header

def ObjPath (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Path")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	ppcnt = struct.unpack("<I",value[offset+0x10:offset+0x14])[0]
	hd.model.set(iter, 0, "  PathPointCount", 1, "%d"%ppcnt,2,offset+0x10,3,4,4,"<I")

	iter = hd.model.append(None, None)
	ppflags = struct.unpack("<H",value[offset+0x14:offset+0x16])[0]
	fc = (ppflags&0x4000)/0x4000
	fr = (ppflags&0x1000)/0x1000
	fp = (ppflags&0x800)/0x800
	hd.model.set(iter, 0, "  PathPointFlags (c,r,p)", 1, "0x%02X (%d %d %d)"%(ppflags,fc,fr,fp),2,offset+0x14,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Reserved",2,offset+0x16,3,2,4,"<H")
	if fp == 0:
		if fc == 0:
			for i in range(ppcnt):
				PointF(hd,value,offset+0x18+i*8,"    Abs Pnt%s "%i)
			offset += 0x18+i*8+8
		else:
			for i in range(ppcnt):
				PointS(hd,value,offset+0x18+i*4,"    Abs Pnt%s "%i)
			offset += 0x18+i*4+4
	else:
		offset += 0x18
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)
	if fr == 0:
		for i in range(ppcnt):
			iter = hd.model.append(None, None)
			ptft,pttt = PointType(value,offset+i)
			hd.model.set(iter, 0, "    Pnt%d Type"%i,1,"%s %s"%(ptft,pttt),2,offset+i,3,1,4,"<B")
	else:
		i = 0
		while i < ppcnt:
			hb = ord(value[offset+i])
			if (hb&0x40):
				ptft1 = ""
				if hb&0x80:
					ptft1 = "Bezier"
				run = hb&0x3f
				ptft,pttt = PointType(value,offset+i+1)
				ptft1 += ptft
				iter = hd.model.append(None, None)
				ptft,pttt = PointType(value,offset+i)
				hd.model.set(iter, 0, "    Pnts %d to %d Type"%(i,i+run),1,"%s %s"%(ptft1,pttt),2,offset+i,3,1,4,"<B")
				i += 2 
			else:
				iter = hd.model.append(None, None)
				ptft,pttt = PointType(value,offset+i)
				hd.model.set(iter, 0, "    Pnt%d Type"%i,1,"%s %s"%(ptft,pttt),2,offset+i,3,1,4,"<B")
				i += 1 

def ObjRegion (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Region")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	rncnt = struct.unpack("<I",value[offset+0x10:offset+0x14])[0]
	hd.model.set(iter, 0, "  RegionNodeCount", 1, "%d"%rncnt,2,offset+0x10,3,4,4,"<I")
	offset += 0x14
	for i in range(rncnt+1):
		offset = RegionNode(hd,value,offset)

def ObjImage (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Image")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	itype = struct.unpack("<I",value[offset+0x10:offset+0x14])[0]
	it = "unknown"
	if ImageType.has_key(itype):
		it = ImageType[itype]
	hd.model.set(iter, 0, "  Type", 1, "0x%02X (%s)"%(itype,it),2,offset+0x10,3,4,4,"<I")
	if itype == 2:  # Metafile
		mtype = struct.unpack("<I",value[offset+0x14:offset+0x18])[0]
		msize = struct.unpack("<I",value[offset+0x18:offset+0x1c])[0]
		iter = hd.model.append(None, None)
		mt = "unknown"
		if MetaFileType.has_key(mtype):
			mt = MetaFileType[mtype]
		hd.model.set(iter, 0, "  MetaFileType", 1, "0x%02X (%s)"%(mtype,mt),2,offset+0x14,3,4,4,"<I")
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "  MetaFileSize", 1, "0x%02X"%msize,2,offset+0x18,3,4,4,"<I")
		#FIXME! send Metafile values to parser

def ObjStringFormat (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "StringFormat")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	sfflags = struct.unpack("<I",value[offset+0x10:offset+0x14])[0]
	sft = ""
	for i in range(10):
		if sfflags&StrFmtFlagValues[i]:
			sft += StrFmtFlagNames[i]
	hd.model.set(iter, 0, "  StringFmt Flags", 1, "0x%04X (%s)"%(sfflags,sft),2,offset+0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	langid = struct.unpack("<I",value[offset+0x14:offset+0x18])[0]
	lt = "unknown"
	if LangIDnames.has_key(lanid):
		lt = LangIDnames[langid]
	hd.model.set(iter, 0, "  LangID", 1, "0x%04X (%s)"%(langid,lt),2,offset+0x14,3,4,4,"<I")
	iter = hd.model.append(None, None)
	stral = struct.unpack("<I",value[offset+0x18:offset+0x1c])[0]
	sat = "unknown"
	if StrAlign.has_key(stral):
		sat = StrAlign[stral]
	hd.model.set(iter, 0, "  StringAlign", 1, "0x%04X (%s)"%(stral,sat),2,offset+0x18,3,4,4,"<I")
	iter = hd.model.append(None, None)
	lineal = struct.unpack("<I",value[offset+0x1c:offset+0x20])[0]
	lat = "unknown"
	if StrAlign.has_key(lineal):
		lat = StrAlign[lineal]
	hd.model.set(iter, 0, "  LineAlign", 1, "0x%04X (%s)"%(lineal,lat),2,offset+0x1c,3,4,4,"<I")
	iter = hd.model.append(None, None)
	sds = struct.unpack("<I",value[offset+0x20:offset+0x24])[0]
	sdst = "unknown"
	if StrDgtSubs.has_key(sds):
		sdst = StrDgtSubs[sds]
	hd.model.set(iter, 0, "  StrDigitSubst", 1, "0x%04X (%s)"%(sbs,sbst),2,offset+0x20,3,4,4,"<I")
	iter = hd.model.append(None, None)
	langid = struct.unpack("<I",value[offset+0x24:offset+0x28])[0]
	lt = "unknown"
	if LangIDnames.has_key(lanid):
		lt = LangIDnames[langid]
	hd.model.set(iter, 0, "  DigitLang", 1, "0x%04X (%s)"%(langid,lt),2,offset+0x24,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  FirstTabOffset", 1, "%.2f"%struct.unpack("<f",value[offset+0x28:offset+0x2c])[0],2,offset+0x28,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hkp = struct.unpack("<I",value[offset+0x2c:offset+0x30])[0]
	hkpt = "unknown"
	if HotPfx.has_key(hkp):
		hkpt = HotPfx[hkp]
	hd.model.set(iter, 0, "  HotKeyPrefix", 1, "0x%04X (%s)"%(hkp,hkpt),2,offset+0x2c,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  LeadMargin", 1, "%.2f"%struct.unpack("<f",value[offset+0x30:offset+0x34])[0],2,offset+0x30,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  TrailMargin", 1, "%.2f"%struct.unpack("<f",value[offset+0x34:offset+0x38])[0],2,offset+0x34,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Tracking", 1, "%.2f"%struct.unpack("<f",value[offset+0x38:offset+0x3c])[0],2,offset+0x38,3,4,4,"<f")
	iter = hd.model.append(None, None)
	strim = struct.unpack("<I",value[offset+0x3c:offset+0x40])[0]
	st = "unknown"
	if StrTrim.has_key(strim):
		st = StrTrim[strim]
	hd.model.set(iter, 0, "  StrTrimming", 1, "0x%04X (%s)"%(strim,st),2,offset+0x3c,3,4,4,"<I")
	iter = hd.model.append(None, None)
	tscnt = struct.unpack("<I",value[offset+0x40:offset+0x44])[0]
	hd.model.set(iter, 0, "  TabStopCount", 1, "0x%04X"%tscnt,2,offset+0x40,3,4,4,"<I")
	iter = hd.model.append(None, None)
	rgcnt = struct.unpack("<I",value[offset+0x44:offset+0x48])[0]
	hd.model.set(iter, 0, "  RangeCount", 1, "0x%04X"%tscnt,2,offset+0x44,3,4,4,"<I")
	for i in range(tscnt):
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "  TabStop%d"%i, 1, "%.2f"%struct.unpack("<f",value[offset+0x48+i*4:offset+0x4c+i*4])[0],2,offset+0x48+i*4,3,4,4,"<f")
	offset += 0x4c + tscnt*4
	for i in range(rgcnt):
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "  Range%d First"%i, 1, "%d"%struct.unpack("<i",value[offset+i*4:offset+4+i*4])[0],2,offset+i*4,3,4,4,"<i")
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "  Range%d Length"%i, 1, "%d"%struct.unpack("<i",value[offset+4+i*4:offset+8+i*4])[0],2,offset+4+i*4,3,4,4,"<i")

def ObjFont (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Font")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	emsize = struct.unpack("<f",value[offset+0x10:offset+0x14])[0]
	hd.model.set(iter, 0, "  EmSize", 1, "%.2f"%emsize,2,offset+0x10,3,4,4,"<f")
	iter = hd.model.append(None, None)
	utype = struct.unpack("<I",value[offset+0x14:offset+0x18])[0]
	ut ="unknown"
	if UnitType.has_key(utype):
		ut = UnitType[utype]
	hd.model.set(iter, 0, "EmSize Units", 1, "0x%02X (%s)"%(utype,ut),2,offset+0x14,3,4,4,"<I")
	iter = hd.model.append(None, None)
	fflags = struct.unpack("<I",value[offset+0x18:offset+0x1c])[0]
	fdft = ""
	flags = fflags
	for i in range(4):
		if flags&1:
			fdft += FontStyleFlags[i]
		flags /= 2
	hd.model.set(iter, 0, "  Style", 1, "0x%02X (%s)"%(fflags,fdft),2,offset+0x18,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Reserved",2,offset+0x1c,3,4,4,"<I")
	iter = hd.model.append(None, None)
	nlen = struct.unpack("<I",value[offset+0x20:offset+0x24])[0]
	hd.model.set(iter, 0, "  FontName Len", 1, "%d"%nlen,2,offset+0x20,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  FontName", 1, unicode(value[offset+0x24:],"utf-16"),2,offset+0x24,3,nlen*2,4,"<I")

def ObjImgAttr (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "ImgAttributes")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Reserved1",2,offset+0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	wmode = struct.unpack("<I",value[0x14:0x18])[0]
	wmt = ""
	if WrapMode.has_key(wmode):
		wmt = WrapMode[wmode]
	hd.model.set(iter, 0, "  WrapMode", 1, "0x%02X (%s)"%(wmode,wmt),2,offset+0x14,3,4,4,"<I")
	RGBA(hd,value[0x18:],0x18,"ClampClr ")
	iter = hd.model.append(None, None)
	cmode = struct.unpack("<I",value[0x1c:0x20])[0]
	cmt = ""
	if ClampMode.has_key(cmode):
		cmt = ClampMode[cmode]
	hd.model.set(iter, 0, "  ClampMode", 1, "0x%02X (%s)"%(cmode,cmt),2,offset+0x1c,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Reserved2",2,offset+0x20,3,4,4,"<I")

def ObjCustLineCap (hd, value, offset = 0):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "CustLineCap")
	ver = struct.unpack("<I",value[offset+0xc:offset+0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Sig", 1, "0x%03X"%(sig/4096),2,offset+0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "  Ver Graphics", 1, "0x%02X"%graph,2,offset+0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	citype = struct.unpack("<I",value[offset+0x10:offset+0x14])[0]
	ct = "unknown"
	if CustLCapDataType.has_key(ctype):
		ct = CustLCapDataType[ctype]
	hd.model.set(iter, 0, "  CustLineCapDataType", 1, "0x%02X (%s)"%(ctype,ct),2,offset+0x10,3,4,4,"<I")
	#FIXME! Parse CustLineCapData

#0x4001
def Header (hd, value):
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%struct.unpack("<H",value[2:4])[0],2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	ver = struct.unpack("<I",value[0xc:0x10])[0]
	sig = ver&0xFFFFF000
	graph = ver&0xFFF
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Ver Sig", 1, "0x%03X"%(sig/4096),2,0xd,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Ver Graphics", 1, "0x%02X"%graph,2,0xc,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "EMF+ Flags", 1, "0x%08X"%struct.unpack("<I",value[0x10:0x14])[0],2,0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "LogDpiX (lpi)", 1, "%d"%struct.unpack("<I",value[0x14:0x18])[0],2,0x14,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "LogDpiY (lpi)", 1, "%d"%struct.unpack("<I",value[0x18:0x1c])[0],2,0x18,3,4,4,"<I")

#0x4002
def EOF (hd, value):
	pass

#0x4004
def GetDC (hd, value):
	pass

#0x4008
def Object (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	c = (ord(value[3])&0x80)/0x80
	otf = (flags&0xEF00)/256
	ot = "unknown"
	oid = (flags&0xFF)
	if ObjectType.has_key(otf):
		ot = ObjectType[otf]
	hd.model.set(iter, 0, "Flags (c, type, id)", 1, "0x%04X (%d, %s, %02x)"%(flags,c,ot,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if obj_ids.has_key(otf):
		obj_ids[otf](hd,value)

#0x4009
def Clear (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	RGBA(hd,value,0xc,"Color ")

#0x4010
def FillPie (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	fc = (flags&0x4000)/0x4000
	hd.model.set(iter, 0, "Flags (s, c)", 1, "0x%04X (%d, %d)"%(flags,fs,fc),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "StartAngle", 1, struct.unpack("<f",value[0x10:0x14])[0],2,0x10,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "SweepAngle", 1, struct.unpack("<f",value[0x14:0x18])[0],2,0x14,3,4,4,"<f")
	if fc == 1:  # 2bytes rect
		RectS(hd,value,0x18+i*8,"Rect ")
	else: # 4bytes rect
		RectF(hd,value,0x18+i*16,"Rect ")

#0x400A
def FillRects (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	fc = (flags&0x4000)/0x4000
	hd.model.set(iter, 0, "Flags (s, c)", 1, "0x%04X (%d, %d)"%(flags,fs,fc),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0x10:0x14])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0x10,3,4,4,"<I")
	if fc == 1:  # 2bytes rect
		for i in range(cnt):
			RectS(hd,value,0x14+i*8,"Rect%d "%i)
	else: # 4bytes rect
		for i in range(cnt):
			RectF(hd,value,0x14+i*16,"Rect%d "%i)

#0x400B
def DrawRects (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, PenID)", 1, "0x%04X (%d, %02x)"%(flags,fc,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0xc:0x10])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0xc,3,4,4,"<I")
	if fc == 1:  # 2bytes rect
		for i in range(cnt):
			RectS(hd,value,0x10+i*8,"Rect%d "%i)
	else: # 4bytes rect
		for i in range(cnt):
			RectF(hd,value,0x10+i*16,"Rect%d "%i)

#0x400C
def FillPolygon (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	fc = (flags&0x4000)/0x4000
	fp = (flags&0x800)/0x800
	hd.model.set(iter, 0, "Flags (s, c, p)", 1, "0x%04X (%d, %d, %d)"%(flags,fs,fc,fp),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0x10:0x14])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0x10,3,4,4,"<I")
	if fp == 0:
		if fc == 0:
			for i in range(cnt):
				PointF(hd,value,0x14+i*8,"    Abs Pnt%s "%i)
		else:
			for i in range(ppcnt):
				PointS(hd,value,0x14+i*4,"    Abs Pnt%s "%i)
	else:
		offset = 0x14
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)

#0x400D
def DrawLines (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	fl = (flags&0x2000)/0x2000
	fp = (flags&0x800)/0x800
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, l, p, PenID)", 1, "0x%04X (%d, %d, %d, %02x)"%(flags,fc,fl,fp, oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0xc:0x10])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0xc,3,4,4,"<I")
	if fp == 0:
		if fc == 0:
			for i in range(cnt):
				PointF(hd,value,0x10+i*8,"    Abs Pnt%s "%i)
		else:
			for i in range(ppcnt):
				PointS(hd,value,0x10+i*4,"    Abs Pnt%s "%i)
	else:
		offset = 0x10
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)

#0x400E
def FillEllipse (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	fc = (flags&0x4000)/0x4000
	hd.model.set(iter, 0, "Flags (s, c)", 1, "0x%04X (%d, %d)"%(flags,fs,fc),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	if fc == 1:  # 2bytes rect
		RectS(hd,value,0x10+i*8,"Rect ")
	else: # 4bytes rect
		RectF(hd,value,0x10+i*16,"Rect ")

#0x400F
def DrawEllipse (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, PenID)", 1, "0x%04X (%d, %02x)"%(flags,fc,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fc == 1:  # 2bytes rect
		RectS(hd,value,0xc+i*8,"Rect ")
	else: # 4bytes rect
		RectF(hd,value,0xc+i*16,"Rect ")

#0x4011
def DrawPie (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, PenID)", 1, "0x%04X (%d, %02x)"%(flags,fc,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "StartAngle", 1, struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "SweepAngle", 1, struct.unpack("<f",value[0x10:0x14])[0],2,0x10,3,4,4,"<f")
	if fc == 1:  # 2bytes rect
		RectS(hd,value,0x14+i*8,"Rect ")
	else: # 4bytes rect
		RectF(hd,value,0x14+i*16,"Rect ")

#0x4012
def DrawArc (hd, value):
	DrawPie (hd, value)

#0x4013
def FillRegion (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (s, RegionID)", 1, "0x%04X (%d, %02x)"%(flags,fs,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")

#0x4014
def FillPath (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (s, PathID)", 1, "0x%04X (%d, %02x)"%(flags,fs,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value,0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")

#0x4015
def DrawPath (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (PathID)", 1, "0x%04X (%02x)"%(flags,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Pen ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")

#0x4016
def FillClosedCurve (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	fc = (flags&0x4000)/0x4000
	fw = (flags&0x2000)/0x2000
	fp = (flags&0x800)/0x800
	hd.model.set(iter, 0, "Flags (s, c, w, p)", 1, "0x%04X (%d, %d, %d, %d)"%(flags,fs,fc,fw,fp),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value,0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Tension", 1, struct.unpack("<f",value[0x10:0x14])[0],2,0x10,3,4,4,"<f")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0x14:0x18])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0x14,3,4,4,"<I")
	if fp == 0:
		if fc == 0:
			for i in range(cnt):
				PointF(hd,value,0x18+i*8,"    Abs Pnt%s "%i)
		else:
			for i in range(ppcnt):
				PointS(hd,value,0x18+i*4,"    Abs Pnt%s "%i)
	else:
		offset = 0x18
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)

#0x4017
def DrawClosedCurve (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	fp = (flags&0x800)/0x800
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, p, PenID)", 1, "0x%04X (%d, %d, %02x)"%(flags,fc,fp,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Tension", 1, struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0x10:0x14])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0x10,3,4,4,"<I")
	if fp == 0:
		if fc == 0:
			for i in range(cnt):
				PointF(hd,value,0x14+i*8,"    Abs Pnt%s "%i)
		else:
			for i in range(ppcnt):
				PointS(hd,value,0x14+i*4,"    Abs Pnt%s "%i)
	else:
		offset = 0x14
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)

#0x4018
def DrawCurve (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, PenID)", 1, "0x%04X (%d, %02x)"%(flags,fc,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Tension", 1, struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Offset", 1, struct.unpack("<I",value[0x10:0x14])[0],2,0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "NumSegments", 1, struct.unpack("<I",value[0x14:0x18])[0],2,0x14,3,4,4,"<I")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0x18:0x1c])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0x18,3,4,4,"<I")
	if fc == 1:  # 2bytes rect
		for i in range(cnt):
			PointS(hd,value,0x1c+i*8,"Point%d "%i)
	else: # 4bytes rect
		for i in range(cnt):
			PointF(hd,value,0x1c+i*16,"Point%d "%i)

#0x4019
def DrawBeziers (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	fp = (flags&0x800)/0x800
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, p, PenID)", 1, "0x%04X (%d, %d, %02x)"%(flags,fc,fp,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	cnt = struct.unpack("<I",value[0xc:0x10])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%cnt,2,0xc,3,4,4,"<I")
	if fp == 0:
		if fc == 0:
			for i in range(cnt):
				PointF(hd,value,0x10+i*8,"    Abs Pnt%s "%i)
		else:
			for i in range(ppcnt):
				PointS(hd,value,0x10+i*4,"    Abs Pnt%s "%i)
	else:
		offset = 0x10
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)

#0x401A
def DrawImage (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, ImageID)", 1, "0x%04X (%d, %02x)"%(flags,fc,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "ImgAttrID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	utype = struct.unpack("<I",value[0x10:0x14])[0]
	ut = "unknown"
	if UnitType.has_key(utype):
		ut = UnitType[utype]
	hd.model.set(iter, 0, "SrcUnit", 1, "0x%02X (%s)"%(utype,ut),2,0x10,3,4,4,"<I")
	RectF(hd,value,0x14,"SrcRect ")
	if fc == 1:  # 2bytes rect
		RectS(hd,value,0x24+i*8,"Rect ")
	else: # 4bytes rect
		RectF(hd,value,0x24+i*16,"Rect ")

#0x401B
def DrawImagePoints (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fc = (flags&0x4000)/0x4000
	fe = (flags&0x2000)/0x2000
	fp = (flags&0x800)/0x800
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (c, e, p, ImageID)", 1, "0x%04X (%d, %d, %d, %02x)"%(flags,fc,fe,fp,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "ImgAttrID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	utype = struct.unpack("<I",value[0x10:0x14])[0]
	ut = "unknown"
	if UnitType.has_key(utype):
		ut = UnitType[utype]
	hd.model.set(iter, 0, "SrcUnit", 1, "0x%02X (%s)"%(utype,ut),2,0x10,3,4,4,"<I")
	RectF(hd,value,0x14,"SrcRect ")
	iter = hd.model.append(None, None)
	ppcnt = struct.unpack("<I",value[0x24:0x28])[0]
	hd.model.set(iter, 0, "Count", 1, "0x%02X"%ppcnt,2,0x24,3,4,4,"<I")
	if fp == 0:
		if fc == 0:
			for i in range(ppcnt):
				PointF(hd,value,0x28+i*8,"    Abs Pnt%s "%i)
		else:
			for i in range(ppcnt):
				PointS(hd,value,0x28+i*4,"    Abs Pnt%s "%i)
	else:
		offset = 0x28
		for i in range(ppcnt):
			offset += PointR(hd,value,offset,"    Rel Pnt%s "%i)

#0x401C
def DrawString (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (s, FontID)", 1, "0x%04X (%d, %02x)"%(flags,fs,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Format ID", 1, "0x%02X"%struct.unpack("<I",value[0x10:0x14])[0],2,0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	glcnt = struct.unpack("<I",value[0x14:0x18])[0]
	hd.model.set(iter, 0, "  Length", 1, "%d"%glcnt,2,0x14,3,4,4,"<I")
	RectF(hd,value,0x18,"LayoutRect ")
	iter = hd.model.append(None, None)
	txt = unicode(value[0x28:0x28+glcnt*2],"utf-16")
	hd.model.set(iter, 0, "  String", 1, txt,2,0x28,3,glcnt*2,4,"utxt")

#0x401D
def SetRenderingOrigin (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "x", 1, "%d"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "y", 1, "%d"%struct.unpack("<I",value[0x10:0x14])[0],2,0x10,3,4,4,"<I")

#0x401E
def SetAntiAliasMode (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	smf = (flags&0xfe)/2
	sm = "unknown"
	a = flags&1
	if SmoothingMode.has_key(smf):
		sm = SmoothingMode[smf]
	hd.model.set(iter, 0, "Flags (mode, a)", 1, "0x%04X (%s, %d)"%(flags,sm,a),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x401F
def SetTextRenderingHint (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	trh = "unknown"
	if TextRenderingHint.has_key(flags):
		trh = TextRenderingHint[flags]
	hd.model.set(iter, 0, "Flags (Txt Rendr hint)", 1, "0x%04X (%s)"%(flags,trh),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4020
def SetTextContrast (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	gamma = (flags&0xFFF)/1000
	hd.model.set(iter, 0, "Flags (gamma)", 1, "0x%04X (%d)"%(flags,gamma),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4021
def SetInterpolationMode (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	imode = ord(value[2])
	imt = "unknown"
	if InterpolationMode.has_key(imode):
		imt = InterpolationMode[imode]
	hd.model.set(iter, 0, "Flags (IntrpMode)", 1, "0x%04X (%s)"%(flags,imt),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4022
def SetPixelOffsetMode (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	imode = ord(value[2])
	imt = "unknown"
	if InterpolationMode.has_key(imode):
		imt = InterpolationMode[imode]
	hd.model.set(iter, 0, "Flags (PxlOffsetMode)", 1, "0x%04X (%s)"%(flags,imt),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4023
def SetCompositingMode (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	imode = ord(value[2])
	imt = "unknown"
	if CompositingMode.has_key(imode):
		imt = CompositingMode[imode]
	hd.model.set(iter, 0, "Flags (ComposMode)", 1, "0x%04X (%s)"%(flags,imt),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4024
def SetCompositingQuality (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	imode = ord(value[2])
	imt = "unknown"
	if CompositingQuality.has_key(imode):
		imt = CompositingQuality[imode]
	hd.model.set(iter, 0, "Flags (ComposQly)", 1, "0x%04X (%s)"%(flags,imt),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4025
def Save (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "StackIdx", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")

#0x4026
def Restore (hd, value):
	Save(hd, value)

#0x4027
def BeginContainer (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	utype = ord(value[3])
	ut = "unknown"
	if UnitType.has_key(utype):
		ut = UnitType[utype]
	hd.model.set(iter, 0, "Flags (PgUnit)", 1, "0x%04X (%s)"%(flags,ut),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	RectF(hd,value,0xc,"DestRect ")
	RectF(hd,value,0x1c,"SrcRect ")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "StackIdx", 1, "0x%02X"%struct.unpack("<I",value[0x2c:0x30])[0],2,0x2c,3,4,4,"<I")

#0x4028
def BeginContainerNoParams (hd, value):
	Save(hd, value)

#0x4029
def EndContainer (hd, value):
	Save(hd, value)

#0x402A
def SetWorldXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	XFormMtrx(hd,value,0xc)

#0x402B
def RstWorldXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x402C
def MultiplyWorldXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fa = (flags&0x2000)/0x2000
	hd.model.set(iter, 0, "Flags (a)", 1, "0x%04X (%d)"%(flags,fa),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	XFormMtrx(hd,value,0xc)

#0x402D
def XlateWorldXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fa = (flags&0x2000)/0x2000
	hd.model.set(iter, 0, "Flags (a)", 1, "0x%04X (%d)"%(flags,fa),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Dx", 1, "%f"%struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Dy", 1, "%f"%struct.unpack("<f",value[0x10:0x14])[0],2,0x10,3,4,4,"<f")

#0x402E
def ScaleWorldXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fa = (flags&0x2000)/0x2000
	hd.model.set(iter, 0, "Flags (a)", 1, "0x%04X (%d)"%(flags,fa),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Sx", 1, "%f"%struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Sy", 1, "%f"%struct.unpack("<f",value[0x10:0x14])[0],2,0x10,3,4,4,"<f")

#0x402F
def RotateWorldXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fa = (flags&0x2000)/0x2000
	hd.model.set(iter, 0, "Flags (a)", 1, "0x%04X (%d)"%(flags,fa),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Angle", 1, "%f"%struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")

#0x4030
def SetPageXform (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	ut ="unknown"
	if UnitType.has_key(flags):
		ut = UnitType[flags]
	hd.model.set(iter, 0, "Flags (UnitType)", 1, "0x%04X (%s)"%(flags,ut),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Page Scale", 1, "%.f"%struct.unpack("<f",value[0xc:0x10])[0],2,0xc,3,4,4,"<f")

#0x4031
def RstClip (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4032
def SetClipRect (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	combmode = (flags&0xF00)/256
	cmt = "unknown"
	if CombineMode.has_key(combmode):
		cmt = CombineMode[combmode]
	hd.model.set(iter, 0, "Flags (CM)", 1, "0x%04X (%02x (%s))"%(flags,combmode,cmt),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	RectF(hd,value,0xc,"ClipRect ")

#0x4033
def SetClipPath (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	combmode = (flags&0xF00)/256
	oid = ord(value[2])
	cmt = "unknown"
	if CombineMode.has_key(combmode):
		cmt = CombineMode[combmode]
	hd.model.set(iter, 0, "Flags (CM, PathID)", 1, "0x%04X (%02x (%s), %02x)"%(flags,combmode,cmt,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4034
def SetClipRgn (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	combmode = (flags&0xF00)/256
	oid = ord(value[2])
	cmt = "unknown"
	if CombineMode.has_key(combmode):
		cmt = CombineMode[combmode]
	hd.model.set(iter, 0, "Flags (CM, RgnID)", 1, "0x%04X (%02x (%s), %02x)"%(flags,combmode,cmt,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")

#0x4035
def OffsetClip (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	hd.model.set(iter, 0, "Flags", 1, "0x%04X"%flags,2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	PointF(hd,value,0xc,"D")

#0x4036
def DrawDriverString (hd, value):
	iter = hd.model.append(None, None)
	flags = struct.unpack("<H",value[2:4])[0]
	fs = (flags&0x8000)/0x8000
	oid = ord(value[2])
	hd.model.set(iter, 0, "Flags (s, FontID)", 1, "0x%04X (%d, %02x)"%(flags,fs,oid),2,2,3,2,4,"<H")
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Data Size", 1, "0x%02X"%struct.unpack("<I",value[8:0xc])[0],2,8,3,4,4,"<I")
	if fs == 1:
		RGBA(hd,value[0xc:],0xc,"Brush Clr")
	else:
		iter = hd.model.append(None, None)
		hd.model.set(iter, 0, "Brush ID", 1, "0x%02X"%struct.unpack("<I",value[0xc:0x10])[0],2,0xc,3,4,4,"<I")
	iter = hd.model.append(None, None)
	dsof = struct.unpack("<I",value[0x10:0x14])[0]
	dsot = ""
	flags = dsof
	fcm = dsof&1
	for i in range(5):
		if flags&1:
			dsot += DrvStrOptFlags[i]
		flags /= 2
	hd.model.set(iter, 0, "  DrvStringOpt Flags", 1, "0x%02X (%s)"%(dsof,dsot),2,0x10,3,4,4,"<I")
	iter = hd.model.append(None, None)
	mp = struct.unpack("<I",value[0x14:0x18])[0]
	hd.model.set(iter, 0, "  Matrix Present", 1, "%d"%mp,2,0x14,3,4,4,"<I")
	iter = hd.model.append(None, None)
	glcnt = struct.unpack("<I",value[0x18:0x1c])[0]
	hd.model.set(iter, 0, "  Glyph Count", 1, "%d"%glcnt,2,0x18,3,4,4,"<I")
	iter = hd.model.append(None, None)
	glyphs = value[0x1c:0x1c+glcnt*2]
#	fcm == 1 -- unicode, fcm == 0 -- indexes to glyphs in the font referred by FontID above
	txt = unicode(glyphs,"utf-16")
	hd.model.set(iter, 0, "  Glyphs", 1, txt,2,0x1c,3,glcnt*2,4,"utxt")
	for i in range(glcnt):
		PointF(hd,value,0x1c+glcnt*2+i*8,"Glyph%d Pos "%i)
	if mp:
		XFormMtrx(hd,value,0x1c+glcnt*10)

bdf_ids = {
	0:RND_Path, # will never be used
	#1:BDF_Transform,
	2:BDF_PresetColors,
	#3:BDF_BlendFactorsH,
	#4:BDF_BlendFactorsV,
	#5:BDF_FocusScales,
	#6:BDF_IsGammaCorrected,
	#7:BDF_DoNotTransform
	}

pdf_ids = {0:PDF_Xform, 1:PDF_StartCap, 2:PDF_EndCap, 3:PDF_Join,
	4:PDF_MiterLimit, 5:PDF_LineStyle, 6:PDF_DashedLineCap,
	7:PDF_DashedLineOffset, 8:PDF_DashedLine, 9:PDF_NonCenter,
	10:PDF_CompoundLine, 11:PDF_CustomStartCap, 12:PDF_CustomEndCap}

bt_ids = {0:BT_SolidColor, 1:BT_HatchFill, 2:BT_TextureFill,
	3:BT_PathGradient, 4:BT_LinearGradient}

rnd_ids = {0:RND_Child,1:RND_Child,2:RND_Child,3:RND_Child,4:RND_Child,
	5:RND_Rect,6:RND_Path,7:RND_Empty,8:RND_Empty}

obj_ids = {1:ObjBrush, 2:ObjPen,3:ObjPath,4:ObjRegion,5:ObjImage,6:ObjFont,
	7:ObjStringFormat, 8:ObjImgAttr,9:ObjCustLineCap}

emfplus_ids = {
0x4001:Header, 0x4002:EOF, # 0x4003:"Comment",
0x4004:GetDC,

# 0x4005:"MultiFormatStart", 0x4006:"MultiFormatSection",0x4007:"MultiFormatEnd", -- MUST NOT BE USED

0x4008:Object, 0x4009:Clear, 0x400A:FillRects, 0x400B:DrawRects,
0x400C:FillPolygon, 0x400D:DrawLines, 0x400E:FillEllipse,
0x400F:DrawEllipse, 0x4010:FillPie,0x4011:DrawPie, 0x4012:DrawArc,
0x4013:FillRegion, 0x4014:FillPath, 0x4015:DrawPath,
0x4016:FillClosedCurve, 0x4017:DrawClosedCurve, 0x4018:DrawCurve,
0x4019:DrawBeziers, 0x401A:DrawImage, 0x401B:DrawImagePoints,
0x401C:DrawString,

0x401D:SetRenderingOrigin,0x401E:SetAntiAliasMode,0x401F:SetTextRenderingHint,
0x4020:SetTextContrast, 0x4021:SetInterpolationMode, 0x4022:SetPixelOffsetMode,
0x4023:SetCompositingMode, 0x4024:SetCompositingQuality,

0x4025:Save, 0x4026:Restore,0x4027:BeginContainer, 0x4028:BeginContainerNoParams,
0x4029:EndContainer,

0x402A:SetWorldXform, 0x402B:RstWorldXform,0x402C:MultiplyWorldXform,0x402D:XlateWorldXform,
0x402E:ScaleWorldXform,0x402F:RotateWorldXform, 0x4030:SetPageXform,

0x4031:RstClip, 0x4032:SetClipRect,0x4033:SetClipPath,0x4034:SetClipRgn,0x4035:OffsetClip,
0x4036:DrawDriverString,

#0x4037:"StrokeFillPath",
#0x4038:"SerializableObject", 0x4039:"SetTSGraphics", 0x403A:"SetTSClip"
}
