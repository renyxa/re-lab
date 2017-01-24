# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
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

import struct


def sl_8bytes(hd, data, shift, offset, blk_off):
	value = struct.unpack("<d",data[offset+blk_off:offset+blk_off+8])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tieee754", 1, value,2,shift+offset+blk_off,3,8,4,"<d")
	return blk_off+8

def sl_2bytes(hd, data, shift, offset, blk_off):
	value = struct.unpack("<h",data[offset+blk_off:offset+blk_off+2])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tword", 1, value,2,shift+offset+blk_off,3,2,4,"<h")
	return blk_off+2

def sl_1byte(hd, data, shift, offset, blk_off):
	value = ord(data[offset+blk_off])
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tbyte", 1, value,2,shift+offset+blk_off,3,1,4,"<b")
	return blk_off+1

names75 = {0x00:"PinX",0x01:"PinY",0x02:"Width",0x03:"Height",
0x04:"LocPinX",0x05:"LocPinY",0x06:"Angle",0x07:"FlipX",0x08:"FlipY",
0x09:"ResizeMode",0x0A:"BeginX",0x0B:"BeginY",0x0C:"EndX",0x0D:"EndY",
0x0E:"LineWeight",0x0F:"LineColor",0x10:"LinePattern",0x11:"FillForegnd",
0x12:"FillBkgnd",0x13:"FillPattern",0x14:"TextDirection",0x15:"TextContainer",
0x16:"TextGeometry",
0x17:'unkn_0x17',0x18:'unkn_0x18',0x19:'unkn_0x19',0x1A:'unkn_0x1A',
0x1B:'unkn_0x1B',0x1C:'unkn_0x1C',
0x1D:"TxtPinX",0x1E:"TxtPinY",0x1F:"TxtWidth",0x20:"TxtHeight",
0x21:"TxtLocPinX",0x22:"TxtLocPinY",0x23:"TxtAngle",0x24:"TxtFlipX",
0x25:"TxtFlipY",0x26:"ImageOffsetX",0x27:"ImageOffsetY",0x28:"ImageWidth",
0x29:"ImageHeight",
0x2A:'unkn_0x2A',0x2B:'unkn_0x2B',0x2C:'unkn_0x2C',
0x2D:"BeginArrow",0x2E:"EndArrow",0x2F:"EndArrowSize",0x30:"Rounding",
0x31:"VerticalAlign",0x32:"ShdwBkgnd",0x33:"BottomMargin",0x34:"LeftMargin",
0x35:"RightMargin",0x36:"TextMaxDepth",0x37:"LockWidth",0x38:"LockHeight",
0x39:"LockMoveX",0x3A:"LockMoveY",0x3B:"LockAspect",0x3C:"LockDelete",
0x3D:"LockBegin",0x3E:"LockEnd",0x3F:"LockRotate",0x40:"LockCrop",
0x41:"LockVtxEdit",0x42:"LockTextEdit",0x43:"LockFormat",0x44:"LockGroup",
0x45:"LockCalcWH",0x46:"LockSelect",
0x47:'unkn_0x47',0x48:'unkn_0x48',0x49:'unkn_0x49',0x4A:'unkn_0x4A',
0x4B:"ShdwPattern",0x4C:"Sharpen",0x4D:"EventDblClick",0x4E:"EventXFMod",
0x4F:"EventDrop",
0x50:'unkn_0x50',
0x51:"DrawingScale",0x52:"PageScale",0x53:"PageWidth",0x54:"PageHeight",
0x55:"ShdwOffsetX",0x56:"ShdwOffsetY",0x57:"NoObjHandles",
0x58:"NonPrinting",0x59:"NoCtlHandles",0x5A:"NoAlignBox",
0x5B:"UpdateAlignBox",0x5C:"HideText",0x5D:"DrawingSizeType",
0x5E:"DrawingScaleType",
0x5F:'unkn_0x5F',0x60:'unkn_0x60',0x61:'unkn_0x61',
0x62:"LineCap",0x63:"DynFeedback",0x64:"GlueType",0x65:"WalkPreference",
0x66:"BegTrigger",0x67:"EndTrigger",0x68:"XRulerDensity",
0x69:"YRulerDensity",0x6A:"XRulerSpacing",0x6B:"YRulerSpacing",
0x6C:"XRulerOrigin",0x6D:"YRulerOrigin",0x6E:"XGridDensity",
0x6F:"YGridDensity",0x70:"XGridSpacing",0x71:"YGridSpacing",
0x72:"XGridOrigin",0x73:"YGridOrigin",0x74:"HelpTopic",
0x75:"Copyright",0x76:"LayerMember",0x77:"ObjType",
0x78:'unkn_0x78',0x79:'unkn_0x79',0x7A:'unkn_0x7A',0x7B:'unkn_0x7B',
0x7C:'unkn_0x7C',0x7D:'unkn_0x7D',0x7E:'unkn_0x7E',0x7F:'unkn_0x7F',
0x80:'unkn_0x80',0x81:'unkn_0x81',0x82:'unkn_0x82',0x83:'unkn_0x83',
0x84:"InhibitSnap",0x85:"NoLiveDynamics",0x86:"OutputFormat",
0x87:"PreviewQuality",0x88:"Gamma",0x89:"Contrast",0x8A:"Brightness",
0x8B:"TextBkgnd",0x8C:"Blur",0x8D:"Denoise",0x8E:"Transparency",
0x8F:"CompressionLevel",0x90:"ConFixedCode",0x91:"SelectMode",
0x92:"DisplayMode",0x93:"IsDropTarget",0x94:"IsSnapTarget",
0x95:"IsTextEditTarget",0x96:"EventTextOverflow",0x97:"ShapeTabStop",
0x98:"Comment",0x99:"BeginArrowSize",0x9A:"DefaultTabStop",
0x9B:"ShdwForegnd",0x9C:"TopMargin",0x9D:"TheData",
0x9E:"TheText",0x9F:"ShapePermeableX",0xA0:"ShapePermeableY",
0xA1:"ShapePermeablePlace",0xA2:"ShapeFixedCode",0xA3:"ShapePlowCode",
0xA4:"ShapeRouteStyle",0xA5:"ShapePlaceStyle",0xA6:"CompressionType",
0xA7:"ConLineJumpCode",0xA8:"ConLineJumpStyle",0xA9:"ShapePlaceDepth",
0xAA:"ResizePage",0xAB:"EnableGrid",0xAC:"DynamicsOff",
0xAD:"CtrlAsInput",0xAE:"PlaceStyle",0xAF:"RouteStyle",
0xB0:"PlaceDepth",0xB1:"PlowCode",0xB2:"LineJumpCode",
0xB3:"LineJumpStyle",0xB4:"LineToNodeX",0xB5:"LineToNodeY",
0xB6:"BlockSizeX",0xB7:"BlockSizeY",0xB8:"AvenueSizeX",
0xB9:"AvenueSizeY",0xBA:"LineToLineX",0xBB:"LineToLineY",
0xBC:"LineJumpFactorX",0xBD:"LineJumpFactorY",0xBE:"Metric",
0xBF:"HideForApply",0xC0:"IsDropSource",0xC1:"PreviewScope",
0xC2:"PageLineJumpDirX",0xC3:"PageLineJumpDirY",0xC4:"ConLineJumpDirX",
0xC5:"ConLineJumpDirY",0xC6:"LockPreview",0xC7:"DontMoveChildren",
0xC8:"LineAdjustFrom",0xC9:"LineAdjustTo",0xCA:"EnableLineProps",
0xCB:"EnableFillProps",0xCC:"EnableTextProps",
0xCD:'unkn_0xCD',0xCE:'unkn_0xCE',0xCF:'unkn_0xCF',0xD0:'unkn_0xD0',
0xD1:'unkn_0xD1',0xD2:'unkn_0xD2',0xD3:'unkn_0xD3',0xD4:'unkn_0xD4',
0xD5:'unkn_0xD5',0xD6:'unkn_0xD6',0xD7:'unkn_0xD7',0xD8:'unkn_0xD8',
0xD9:'unkn_0xD9',0xDA:'unkn_0xDA',0xDB:'unkn_0xDB',0xDC:'unkn_0xDC',
0xDD:'unkn_0xDD',0xDE:'unkn_0xDE',0xDF:'unkn_0xDF',0xE0:'unkn_0xE0',
0xE1:'unkn_0xE1',0xE2:'unkn_0xE2',0xE3:'unkn_0xE3',0xE4:'unkn_0xE4',
0xE5:'unkn_0xE5',0xE6:'unkn_0xE6',0xE7:'unkn_0xE7',0xE8:'unkn_0xE8',
0xE9:'unkn_0xE9',0xEA:'unkn_0xEA',0xEB:'unkn_0xEB',0xEC:'unkn_0xEC',
0xED:'unkn_0xED',0xEE:'unkn_0xEE',0xEF:'unkn_0xEF',0xF0:'unkn_0xF0',
0xF1:'unkn_0xF1',0xF2:'unkn_0xF2',0xF3:'unkn_0xF3',0xF4:'unkn_0xF4',
0xF5:'unkn_0xF5',0xF6:'unkn_0xF6',0xF7:'unkn_0xF7',0xF8:'unkn_0xF8',
0xF9:'unkn_0xF9',0xFA:'unkn_0xFA',0xFB:'unkn_0xFB',0xFC:'unkn_0xFC',
0xFD:'unkn_0xFD',0xFE:'unkn_0xFE',0xFF:'unkn_0xFF'}

fnames7ab = {
0x00:'_NYI',													0x01:'_ADD(num1;num2)',
0x02:'_SUB(num1;num2)',								0x03:'UNKNOWN_3',
0x04:'_DIV(num1;num2)',								0x05:'_UPLUS(num1)',
0x06:'_UMINUS(num1)',									0x07:'_PCT(num1)',
0x08:'SUM(num1;num2;...)',						0x09:'MAX(num1;num2;...)',
0x0a:'MIN(num1; num2;...)',						0x0b:'PNT(x_num; y_num)',
0x0c:'PNTX(num)',											0x0d:'PNTY(num)',
0x0e:'LOC(num)',											0x0f:'ABS(num)',
0x10:'POW(num; exp)',									0x11:'SQRT(num)',
0x12:'ATAN2(num1;num2)',							0x13:'PI()',
0x14:'RAD(ang)',											0x15:'DEG(num)',
0x16:'UNKNOWN_22',										0x17:'_FLT(num1;num2)',
0x18:'_FLE(num1;num2)',								0x19:'_FEQ(num1;num2)',
0x1a:'_FGE(num1;num2)',								0x1b:'_FGT(num1;num2)',
0x1c:'_FNE(num1;num2)',								0x1d:'AND()',
0x1e:'OR()',													0x1f:'NOT(num)',
0x20:'BITAND(num1;num2)',							0x21:'BITOR(num1;num2)',
0x22:'BITOXR(num1;num2)',							0x23:'BITNOT(num)',
0x24:'COS(num)',											0x25:'COSH(num)',
0x26:'SIN(num)',											0x27:'SINH(num)',
0x28:'TAN(angle)',										0x29:'TANH(angle)',
0x2a:'LN(num)',												0x2b:'LOG10(num)',
0x2c:'RAND()',												0x2d:'TEXTWIDTH(text;num)',
0x2e:'TEXTHEIGHT(text;num)',					0x2f:'_GLUELOC(num1;num2;num3;num4)',
0x30:'_GLUEPAR(num1;num2;num3;num4)',	0x31:'REF()',
0x32:'_MARKER(num)',									0x33:'PAR(point)',
0x34:'_ELLIPSE_THETA(n1;n2;n3;n4;w;h)',0x35:'_ELLIPSE_ECC(n1;n2;n3;n4;w;h;_ellipse_theta)',
0x36:'_UMARKER(num1;num2)',						0x37:'EVALTEXT(text)',
0x38:'_GLUELOCPCT(num1;num2;num3)',		0x39:'_GLUEPARPCT(num1;num2;num3)',
0x3a:'DATE(year;month;day)',					0x3b:'TIME(hour;minute;second)',
0x3c:'NOW()',													0x3d:'INT(num)',
0x3e:'_MOD(num1;num2)',								0x3f:'ROUND(num;numdigits)',
0x40:'TRUNC(num;numdigits)',					0x41:'GUARD(num)',
0x42:'MAGNITUDE(constA;A;constB;B)',	0x43:'_ELT(num1;num2)',
0x44:'_ELE(num1;num2)',								0x45:'_EEQ(num1;num2)',
0x46:'_EGE(num1;num2)',								0x47:'_EGT(num1;num2)',
0x48:'_ENE(num1;num2)',								0x49:'_CAT(num1;num2)',
0x4a:'NA()',													0x4b:'DEFAULTEVENT()',
0x4c:'OPENTEXTWIN()',									0x4d:'OPENGROUPWIN()',
0x4e:'OPENSHEETWIN()',								0x4f:'DOOLEVERB(num)',
0x50:'GOTOPAGE(page)',								0x51:'RUNADDON(name)',
0x52:'HELP(topic)',										0x53:'ISERROR(cellref)',
0x54:'ISERR(cellref)',								0x55:'ISERRNA(cellref)',
0x56:'ISERRVALUE(cellref)',						0x57:'OPENPAGE(page)',
0x58:'ACOS(num)',											0x59:'ASIN(num)',
0x5a:'ATAN(num)',											0x5b:'SIGN(num; fuzz)',
0x5c:'INTUP(num)',										0x5d:'ANG360(num)',
0x5e:'FLOOR(num1;num2)',							0x5f:'CEILING(num1;num2)',
0x60:'GRAVITY(num1;num2;num3)',				0x61:'RECTSECT(w;h;x;y;option)',
0x62:'MODULUS(number; divisor)',			0x63:'LOTUSNOTES(lotusname)',
0x64:'USERUI(state;dflt_exp;user_exp)',0x65:'_UCON_C1(num1;num2;num3;num4;num5)',
0x66:'_UCON_C2(num1;num2)',						0x67:'_UCON_D1(num1;num2;num3;num4;num5)',
0x68:'_UCON_D2(num1;num2)',						0x69:'_UCON_X1(num1;num2;num3;num4;num5;num6;num7;num8;num9;num10)',
0x6a:'_UCON_X2(num1;num2;num3;num4;num5;num6;num7;num8)',
0x6b:'_UCON_Y1(num1;num2;num3;num4;num5;num6;num7;num8;num9;num10)',
0x6c:'_UCON_Y2(num1;num2;num3;num4;num5;num6;num7;num8)',
0x6d:'_UCON_SIMPLE(num1;num2;num3;num4;num5;num6;num7;num8)',
0x6e:'_UCON_BEGTYP(num1;num2;num3;num4;num5)',
0x6f:'_UCON_ENDTYP(num1;num2;num3;num4;num5)',
0x70:'_WALKGLUE(num1,num2,num3)',			0x71:'_SHAPEMIN(num1)',
0x72:'_SHAPEMAX(num1)',								0x73:'_XFTRIGGER(cell)',
0x74:'_UCON_C3(num1;num2)',						0x75:'_UCON_D3(num1;num2)',
0x76:'_UCON_X3(num1;num2;num3;num4;num5;num6;num7;num8;num9)',
0x77:'_UCON_Y3(num1;num2;num3;num4;num5;num6;num7;num8;num9)',
0x78:'_UCON_GEOTYP(num1;num2)',				0x79:'RUNADDONWARGS(name;args)',
0x7a:'DEPENDSON(num1;num2)',					0x7b:'OPENFILE()',
0x7c:'FORMAT(num1;num2)',							0x7d:'CHAR(num)',
0x7e:'SETF(cell;formula)',						0x7f:'LOOKUP(key;list;delim_opt)',
0x80:'INDEX(idx;list;delim_opt;error_opt)',
0x81:'PLAYSOUND(filename;is_alias;beep_on_fail;sync)',
0x82:'DOCMD(cmd)',										0x83:'RGB(red;green;blue)',
0x84:'HSL(hue;sat;lum)',							0x85:'RED(num)',
0x86:'GREEN(num)',										0x87:'BLUE(num)',
0x88:'HUE(num)',											0x89:'SAT(num)',
0x8a:'LUM(num)',											0x8b:'USE(mastername;opt1;opt2;opt3)',
0x8c:'DATEVALUE(num;locale)',					0x8d:'TIMEVALUE(time;locale_opt)',
0x8e:'DATETIME(num;locale)',					0x8f:'HOUR(num;locale)',
0x90:'MINUTE(datetime;locale_opt)',		0x91:'SECOND(num;locale)',
0x92:'YEAR(datetime;locale_opt)',			0x93:'MONTH(datetime;locale_opt)',
0x94:'DAY(num;locale)',								0x95:'WEEKDAY(datetime;locale_opt)',
0x96:'DAYOFYEAR(num;locale)',					0x97:'CY(num1;country_code)',
0x98:'UPPER(string)',									0x99:'LOWER(string)',
0x9a:'FORMATEX(num1;num2;num3;num4)',	0x9b:'CALLTHIS(...)',
0x9c:'HYPERLINK(link;sublink;info;new_win;frame)',
0x9d:'INTERSECTX(x1;y1;ang1;x2;y2;ang2)',
0x9e:'INTERSECTY(x1;y1;ang1;x2;y2;ang2)',
0x9f:'POLYLINE(xType;yType;x1; y1;...)',
0xa0:'_POLYARC',											0xa1:'NURBS(knotLast;degree;xType;yType;x1;y1;knot1;weight1;...)',
0xa2:'LOCTOLOC(srcPoint;srcRef;dstRef)',0xa3:'LOCTOPAR(srcPoint;srcRef;dstRef)',
0xa4:'ANGLETOLOC(srcAng;srcRef;dstRef)',0xa5:'ANGLETOPAR(srcAng,srcRef,dstRef)',
0xa6:'DocCreation()',									0xa7:'DocLastPrint()',
0xa8:'DocLastEdit()',									0xa9:'DocLastSave()',
0xaa:'PageCount()',										0xab:'Creator()',
0xac:'Description()',									0xad:'Directory()',
0xae:'Filename()',										0xaf:'Keywords()',
0xb0:'Subject()',											0xb1:'Title()',
0xb2:'Manager()',											0xb3:'Company()',
0xb4:'Category()',										0xb5:'HyperlinkBase()',
0xb6:'BkgPageName(name)',							0xb7:'PageName(lcid)',
0xb8:'PageNumber()',									0xb9:'Data1()',
0xba:'Data2()',												0xbb:'Data3()',
0xbc:'ListSep()',											0xbd:'ID()',
0xbe:'Type()',												0xbf:'TypeDesc()',
0xc0:'Name(lcid_opt)',								0xc1:'MasterName(lcid_opt)',
0xc2:'FieldPicture(num)',							0xc3:'StrSame(str1;str2;ignore_case)',
0xc4:'StrSameEx(str1;str2;localeID;flags)',
0xc5:'ShapeText(text;flags_opt)',			0xc6:'DecimalSep()',
0xC7:'RUNMACRO(...)',									0xC8:'FORMULAEXISTS(cel_ref)',
0xC9:'LOCALFORMULAEXISTS(cel_ref)',		0xCA:'FIND(str,str,pos,flag)',
0xCB:'LEFT(text,pos)',								0xCC:'LEN(text)',
0xCD:'MID(...)',											0xCE:'REPLACE(...)',
0xCF:'REPT(...)',											0xD0:'RIGHT(...)',
0xD1:'TRIM(...)',											0xD2:'QUEUEMARKEREVENT(...)',
0xD3:'BOUND',													0xD4:'SUBSTITUTE(...)',
0xD5:'BLOB(...)',											0xD6:'UNICHAR(...)',
0xD7:'REWIDEN(...)',									0xD8:'SETATREF(...)',
0xD9:'SETATREFEXPR(...)',							0xDA:'SETATREFVAL(...)',
0xDB:'THEME',													0xDC:'TINT(...)',
0xDD:'SHADE',													0xDE:'TONE(...)',
0xDF:'LUMDIFF',												0xE0:'SATDIFF(...)',
0xE1:'HUEDIFF(clr1,clr2)',						0xE2:'BLEND(clr1,clr2,mix)',
0xE3:'THEMEGUARD()',									0xE4:'CELLISTHEMED(...)',
0xE5:'THEMERESTORE',									0xE6:'EVALLCELL(...)',
0xE7:'ARG(...)',											0xE8:'FONTTOID(font)',
0xE9:'SHEETREF(...)',									0xEA:'BOUNDINGBOXRECT(...)',
0xEB:'BOUNDINGBOXDIST(...)',					0xEC:'MSOTINT(...)',
0xED:'MSOSHADE(...)',									0xEE:'PATHLENGTH(...)',
0xEF:'POINTALONGPATH(...)',						0xF0:'ANGELALONGPATH(...)',
0xF1:'NEARESTPOINTONPATH(...)',									0xF2:'DISTTOPATH(ref,num1,num2)',
0xF3:'UNKNOWN_0xf3',									0xF4:'LISTMEMBERCOUNT()',
0xF5:'LISTORDER(...)',								0xF6:'CONTAINERCOUNT()',
0xF7:'CONTAINERMEMBERCOUNT()',				0xF8:'UNKNOWN_0xf8',
0xF9:'CALLOUTCOUNT(...)',							0xFA:'UNKNOWN_0xfa',
0xFB:'HASCATEGORY(text)',							0xFC:'UNKNOWN_0xfc',
0xFD:'IS1D()',												0xFE:'UNKNOWN_0xfe',
0xFF:'UNKNOWN_0xff',									0x10A:'SEGMENTCOUNT(...)',
0x10B:'PATHSEGMENT(...)',							0x10C:'VERSION()',}

def sl_funcs7b(hd, data, shift, offset, blk_off):
	nargs = struct.unpack("<I",data[offset+blk_off:offset+blk_off+4])[0]
	fid = struct.unpack("<h",data[offset+blk_off+4:offset+blk_off+6])[0]
	nm_str = "# of args: %i "%nargs
	if fnames7ab.has_key(fid):
		nm_str += "("+fnames7ab[fid]+")" 
	else:
		nm_str += "%02x"%fid
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tfunc7b", 1, nm_str,2,shift+offset+blk_off,3,8,4,"<d")
	return blk_off+8

def sl_funcs7a(hd, data, shift, offset, blk_off):
	if hd.version > 5:
		fid = struct.unpack("<h",data[offset+blk_off:offset+blk_off+2])[0]
	else:
		fid = ord(data[offset+blk_off])
	if fnames7ab.has_key(fid):
		nm_str = fnames7ab[fid]
	else:
		nm_str = "%02x"%fid
	iter1 = hd.model.append(None, None)
	if hd.version > 5:
		hd.model.set (iter1, 0, "\tfunc7a", 1, nm_str,2,shift+offset+blk_off,3,4,4,"<I")
		return blk_off+4
	else:
		hd.model.set (iter1, 0, "\tfunc7a", 1, nm_str,2,shift+offset+blk_off,3,2,4,"<H")
		return blk_off+2

def sl_str(hd, data, shift, offset, blk_off):
	slen = ord(data[offset+blk_off])
	if hd.version == 11:
		txt = unicode(data[offset+blk_off+1:offset+blk_off+3+slen*2],"utf-16")
		tlen = slen*2+3
	else:
		txt = data[offset+blk_off+1:offset+blk_off+2+slen]
		tlen = slen+2
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tstring", 1, txt,2,shift+offset+blk_off,3,tlen,4,"txt")
	return blk_off+tlen

sl_opnames = {0x3:'+', 0x4:'-', 0x5:'*', 0x6:'/', 0x7:'^', 0x8:'&', 0x9:'<',
				0xa:'<=', 0xb:'=', 0xc:'>=', 0xd:'>', 0xe:'!=',
				0x13:'neg.sign', 0x14:'%', 0xe4:'()'}

def sl_ops(hd, data, shift, offset, blk_off):
	op = ord(data[offset+blk_off])
	if sl_opnames.has_key(op):
		op_txt = sl_opnames[op]
	else:
		op_txt = "%02x"%op
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tops", 1, op_txt,2,shift+offset+blk_off,3,1,4,"<b")
	return blk_off+1

def sl_names70 (hd, data, shift, offset, blk_off):
	# FIXME, just skipping at the moment
	iter1 = hd.model.append(None, None)
	length = 11
	v1,v2,v3,v4 = "","","",""
	if hd.version < 6:
		length = 7
		v1 = struct.unpack("<H",data[offset+blk_off:offset+blk_off+2])[0]
		v2 = struct.unpack("<H",data[offset+blk_off+2:offset+blk_off+4])[0]
		try:
			v3 = sl_objs72[ord(data[offset+blk_off+4])]
		except:
			v3 = "unkn_0x%d"%ord(data[offset+blk_off+4])
		try:
			v4 = sl_vars72[struct.unpack("<H",data[offset+blk_off+5:offset+blk_off+7])[0]]
		except:
			v4 = "unkn_0x%d"%(struct.unpack("<H",data[offset+blk_off+5:offset+blk_off+7])[0])
	hd.model.set (iter1, 0, "\tnames70 [%d %d : %s: %s]"%(v1,v2,v3,v4), 1, "",2,shift+offset+blk_off,3,7,4,"txt")

	return blk_off+length


sl_vars72 = {0:"X",1:"Y"}
sl_objs72 = {1:"Sheet",2:"Member",3:"Char",4:"Para",5:"Tabs",6:"Scratch",7:"Connections",8:"TextFields",9:"Controls",
						0xF0:"Actions",0xF1:"Layer",0xF2:"User",0xF3:"Prop",0xF4:"Hyperlink"}

def sl_names72 (hd, data, shift, offset, blk_off):
	idx = struct.unpack("<I",data[offset+blk_off:offset+blk_off+4])[0]
	obj = ord(data[offset+blk_off+4])
	var = ord(data[offset+blk_off+5])
	if obj > 9 and obj < 0xf0:
		obj_name = "Geometry%d"%(obj-9)
	elif sl_objs72.has_key(obj):
		obj_name = sl_objs72[obj]
	else:
		obj_name = "Obj%02x"%obj
	if sl_vars72.has_key(var):
		var_name = sl_vars72[var]
	else:
		var_name = "Var%02x_"%var
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tnames72", 1, obj_name+"."+var_name+"%d"%idx,2,shift+offset+blk_off,3,7,4,"txt")
	return blk_off+7

def sl_names74 (hd, data, shift, offset, blk_off):
	var = struct.unpack("<h",data[offset+blk_off:offset+blk_off+2])[0]
	idx = struct.unpack("<I",data[offset+blk_off+4:offset+blk_off+8])[0]
	if names75.has_key(var):
		var_name = names75[var]
	else:
		var_name = "Var%02x"%var
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tnames74", 1, "Sheet.%d!"%idx+var_name,2,shift+offset+blk_off,3,8,4,"txt")
	return blk_off+8

def sl_names75(hd, data, shift, offset, blk_off):
	value = ord(data[offset+blk_off])
	nm_str = "%02x"%value
	if names75.has_key(value):
		nm_str = names75[value]
	iter1 = hd.model.append(None, None)
	l,t = 4,"<I"
	if hd.version < 6:
		l,t = 2, "<H"
	hd.model.set (iter1, 0, "\tname75", 1, nm_str,2,shift+offset+blk_off,3,l,4,t)
	return blk_off+l

def sl_names76 (hd, data, shift, offset, blk_off):
	# FIXME, just skipping at the moment
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tnames76", 1, "",2,shift+offset+blk_off,3,17,4,"txt")
	return blk_off+17

sl_logops = {0xa0:'AND()',0xa1:'OR()',0xa2:'IF()'}

def sl_logfunc (hd, data, shift, offset, blk_off):
	# FIXME, just skipping at the moment
	op = ord(data[offset+blk_off])
	if sl_logops.has_key(op):
		op_txt = sl_logops[op]
	else:
		op_txt = "%02x"%op
	len = struct.unpack("<I",data[offset+blk_off+1:offset+blk_off+5])[0]
	iter1 = hd.model.append(None, None)
	hd.model.set (iter1, 0, "\tlog.func", 1, op_txt,2,shift+offset+blk_off+1,3,len-1,4,"txt")
	return blk_off+len

def sl_nurbs (hd, data, shift, offset, blk_off):
	# the same as "NURBS Data (type 0x82)"
		iter1 = hd.model.append(None, None)
		hd.model.set (iter1, 0, "\tknotLast", 1, "%.2f"%struct.unpack("<d",data[offset+blk_off:offset+blk_off+8]),2,shift+offset+blk_off,3,8,4,"<d")
		iter1 = hd.model.append(None, None)
		hd.model.set (iter1, 0, "\tdegree", 1, "%.2f"%struct.unpack("<h",data[offset+blk_off+8:offset+blk_off+10]),2,shift+offset+blk_off+8,3,2,4,"<h")
		xType = ord(data[offset+blk_off+10])
		yType = ord(data[offset+blk_off+11])
		iter1 = hd.model.append(None, None)
		hd.model.set (iter1, 0, "\txType", 1, xType,2,shift+offset+blk_off+10,3,1,4,"<b")
		iter1 = hd.model.append(None, None)
		hd.model.set (iter1, 0, "\tyType", 1, yType,2,shift+offset+blk_off+11,3,1,4,"<b")
		[num_pts] = struct.unpack("<I",data[offset+blk_off+12:offset+blk_off+16])
		iter1 = hd.model.append(None, None)
		hd.model.set (iter1, 0, "\t# of pts", 1, num_pts,2,shift+offset+blk_off+12,3,4,4,"<I")
		for i in range(num_pts):
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "--- x%d"%(i+1), 1, "%.2f"%struct.unpack("<d",data[offset+blk_off+16+i*32:offset+blk_off+24+i*32]),2,shift+offset+blk_off+16+i*32,3,8,4,"<d")
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\t y%d"%(i+1), 1, "%.2f"%struct.unpack("<d",data[offset+blk_off+24+i*32:offset+blk_off+32+i*32]),2,shift+offset+blk_off+24+i*32,3,8,4,"<d")
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\t knot%d"%(i+1), 1, "%.2f"%struct.unpack("<d",data[offset+blk_off+32+i*32:offset+blk_off+40+i*32]),2,shift+offset+blk_off+32+i*32,3,8,4,"<d")
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\t weight%d"%(i+1), 1, "%.2f"%struct.unpack("<d",data[offset+blk_off+40+i*32:offset+blk_off+48+i*32]),2,shift+offset+blk_off+40+i*32,3,8,4,"<d")
		return blk_off + 40 + num_pts*32



def get_slice (hd, data, shift, offset, blk_off):
	blk_func = ord(data[offset+blk_off])
	if blk_func < 0x20 or blk_func == 0xe4:
		blk_off = sl_ops (hd,data,shift,offset,blk_off)
	elif blk_func > 0x19 and blk_func < 0x60:
		blk_off = sl_8bytes(hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x60:
		blk_off = sl_str (hd,data,shift,offset,blk_off+1)  #may require 'version' to check for 6 vs 11
	elif blk_func == 0x61:
		blk_off = sl_1byte(hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x62:
		blk_off = sl_2bytes(hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x70:
		blk_off = sl_names70 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x72:
		blk_off = sl_names72 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x74:
		blk_off = sl_names74 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x75:
		blk_off = sl_names75 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x76:
		blk_off = sl_names76 (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x7a or blk_func == 0x80:
		blk_off = sl_funcs7a (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x7b or blk_func == 0x81:
		blk_off = sl_funcs7b (hd,data,shift,offset,blk_off+1)
	elif blk_func == 0x8a:
		blk_off = sl_nurbs (hd,data,shift,offset,blk_off+1)
	elif blk_func > 0x9f and blk_func < 0xa4:
		blk_off = sl_logfunc (hd,data,shift,offset,blk_off)
	else:
		blk_off += 1 # bad idea, but just to skip unknowns
	return blk_off

def parse (hd, size, value,shift):
	# offset -- where we are in the buffer
	# shift -- what to add to hd iter
	# blk_off -- offset inside the block
	offset = 0
	blk_id = 0
	data = value[shift:]
	
	while offset < len(data):
		blk_len = struct.unpack("<I",data[offset:offset+4])[0]
		if blk_len == 0:
			blk_len = 4  # 4 bytes "trailer" at the end of chunk
		else:
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "Blk #%d Length"%blk_id, 1, blk_len,2,shift+offset,3,4,4,"<d")
			blk_id += 1
			blk_off = 4
			blk_type = ord(data[offset+blk_off])
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\tBlk Type", 1, blk_type,2,shift+offset+blk_off,3,1,4,"<b")
			blk_off = 5
			blk_idx = ord(data[offset+blk_off]) # which cell in the shapesheet this formula is for
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\tBlk IDX", 1, blk_idx,2,shift+offset+blk_off,3,1,4,"<b")
			blk_off = 6
			if blk_type == 2:
				while blk_off < blk_len:
					blk_off = get_slice(hd, data, shift, offset, blk_off)

		offset += blk_len

def parse5 (hd, size, value, shift):
	offset = 0
	blk_id = 0
	data = value[shift:]
	
	while offset < len(data)-2:
		blk_len = struct.unpack("<H",data[offset:offset+2])[0]
		if blk_len == 0:
			blk_len = 2  # 4 bytes "trailer" at the end of chunk
		else:
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "Blk #%d Length"%blk_id, 1, blk_len,2,shift+offset,3,2,4,"<H")
			blk_id += 1
			blk_off = 2
			blk_type = ord(data[offset+blk_off])
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\tBlk Type", 1, blk_type,2,shift+offset+blk_off,3,1,4,"<b")
			blk_off = 3
			blk_idx = ord(data[offset+blk_off]) # which cell in the shapesheet this formula is for
			iter1 = hd.model.append(None, None)
			hd.model.set (iter1, 0, "\tBlk IDX", 1, blk_idx,2,shift+offset+blk_off,3,1,4,"<b")
			blk_off = 4
			if blk_type == 2:
				while blk_off < blk_len:
					blk_off = get_slice(hd, data, shift, offset, blk_off)

		offset += blk_len

