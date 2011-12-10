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

import sys,struct
import gobject
import gtk
import tree
import hexdump
import escher
import ctypes
from utils import *

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')


charsets = {0:"Latin", 1:"System default", 2:"Symbol", 77:"Apple Roman",
	128:"Japanese Shift-JIS",129:"Korean (Hangul)",130:"Korean (Johab)",
	134:"Chinese Simplified GBK",136:"Chinese Traditional BIG5",
	161:"Greek",162:"Turkish",163:"Vietnamese",177:"Hebrew",178:"Arabic",
	186:"Baltic",204:"Cyrillic",222:"Thai",238:"Latin II (Central European)",
	255:"OEM Latin I"}

escapement = {0:"None", 1:"Superscript", 2:"Subscript"}

underline = {0:"None",1:"Single",2:"Double",0x21:"Single accounting",0x22:"Double accounting"}

substream = {5:"Book", 16:"Sheet", 32:"Chart", 64:"Macro"}

rec_ids = {
	6:"Formula", 10:"EOF", 12:"CalcCount", 13:"CalcMode", 14:"CalcPrecision",
	15:"CalcRefMode", 16:"CalcDelta", 17:"CalcIter", 18:"Protect", 19:"Password",
	20:"Header", 21:"Footer", 23:"ExternSheet", 24:"Lbl", 25:"WinProtect",
	26:"VerticalPageBreaks", 27:"HorizontalPageBreaks", 28:"Note", 29:"Selection",
	34:"Date1904", 35:"ExternName", 38:"LeftMargin", 39:"RightMargin", 40:"TopMargin",
	41:"BottomMargin", 42:"PrintRowCol", 43:"PrintGrid", 47:"FilePass", 49:"Font",
	51:"PrintSize", 60:"Continue", 61:"Window1", 64:"Backup", 65:"Pane", 66:"CodePage",
	77:"Pls", 80:"DCon", 81:"DConRef", 82:"DConName", 85:"DefColWidth", 89:"XCT",
	90:"CRN", 91:"FileSharing", 92:"WriteAccess", 93:"Obj", 94:"Uncalced",
	95:"CalcSaveRecalc", 96:"Template", 97:"Intl", 99:"ObjProtect", 125:"ColInfo",
	128:"Guts", 129:"WsBool", 130:"GridSet", 131:"HCenter", 132:"VCenter",
	133:"BoundSheet8", 134:"WriteProtect", 140:"Country", 141:"HideObj",
	144:"Sort", 146:"Palette", 151:"Sync", 152:"LPr", 153:"DxGCol", 154:"FnGroupName",
	155:"FilterMode", 156:"BuiltInFnGroupCount", 157:"AutoFilterInfo",
	158:"AutoFilter", 160:"Scl", 161:"Setup", 174:"ScenMan", 175:"SCENARIO",
	176:"SxView", 177:"Sxvd", 178:"SXVI", 180:"SxIvd", 181:"SXLI", 182:"SXPI",
	184:"DocRoute", 185:"RecipName", 189:"MulRk", 190:"MulBlank", 193:"Mms",
	197:"SXDI", 198:"SXDB", 199:"SXFDB", 200:"SXDBB", 201:"SXNum", 202:"SxBool",
	203:"SxErr", 204:"SXInt", 205:"SXString", 206:"SXDtr", 207:"SxNil", 208:"SXTbl",
	209:"SXTBRGIITM", 210:"SxTbpg", 211:"ObProj", 213:"SXStreamID", 215:"DBCell",
	216:"SXRng", 217:"SxIsxoper", 218:"BookBool", 220:"DbOrParamQry",
	221:"ScenarioProtect", 222:"OleObjectSize", 224:"XF", 225:"InterfaceHdr",
	226:"InterfaceEnd", 227:"SXVS", 229:"MergeCells", 233:"BkHim",
	235:"MsoDrawingGroup", 236:"MsoDrawing", 237:"MsoDrawingSelection",
	239:"PhoneticInfo", 240:"SxRule", 241:"SXEx", 242:"SxFilt", 244:"SxDXF", 
	245:"SxItm", 246:"SxName", 247:"SxSelect", 248:"SXPair", 249:"SxFmla",
	251:"SxFormat", 252:"SST", 253:"LabelSst", 255:"ExtSST", 256:"SXVDEx",
	259:"SXFormula", 290:"SXDBEx", 311:"RRDInsDel", 312:"RRDHead",
	315:"RRDChgCell", 317:"RRTabId", 318:"RRDRenSheet", 319:"RRSort", 320:"RRDMove",
	330:"RRFormat", 331:"RRAutoFmt", 333:"RRInsertSh", 334:"RRDMoveBegin",
	335:"RRDMoveEnd", 336:"RRDInsDelBegin", 337:"RRDInsDelEnd", 338:"RRDConflict",
	339:"RRDDefName", 340:"RRDRstEtxp", 351:"LRng", 352:"UsesELFs", 353:"DSF",
	401:"CUsr", 402:"CbUsr", 403:"UsrInfo", 404:"UsrExcl", 405:"FileLock",
	406:"RRDInfo", 407:"BCUsrs", 408:"UsrChk", 425:"UserBView", 426:"UserSViewBegin",
	426:"UserSViewBegin_Chart", 427:"UserSViewEnd", 428:"RRDUserView", 429:"Qsi",
	430:"SupBook", 431:"Prot4Rev", 432:"CondFmt", 433:"CF", 434:"DVal",
	437:"DConBin", 438:"TxO", 439:"RefreshAll", 440:"HLink", 441:"Lel",
	442:"CodeName", 443:"SXFDBType", 444:"Prot4RevPass", 445:"ObNoMacros",
	446:"Dv", 448:"Excel9File", 449:"RecalcId", 450:"EntExU2", 512:"Dimensions",
	513:"Blank", 515:"Number", 516:"Label", 517:"BoolErr", 519:"String",
	520:"Row", 523:"Index", 545:"Array", 549:"DefaultRowHeight", 566:"Table",
	574:"Window2", 638:"RK", 659:"Style", 1048:"BigName", 1054:"Format",
	1084:"ContinueBigName", 1212:"ShrFmla", 2048:"HLinkTooltip", 2049:"WebPub",
	2050:"QsiSXTag", 2051:"DBQueryExt", 2052:"ExtString", 2053:"TxtQry",
	2054:"Qsir", 2055:"Qsif", 2056:"RRDTQSIF", 2057:"BOF", 2058:"OleDbConn",
	2059:"WOpt", 2060:"SXViewEx", 2061:"SXTH", 2062:"SXPIEx", 2063:"SXVDTEx",
	2064:"SXViewEx9", 2066:"ContinueFrt", 2067:"RealTimeData", 2128:"ChartFrtInfo",
	2129:"FrtWrapper", 2130:"StartBlock", 2131:"EndBlock", 2132:"StartObject",
	2133:"EndObject", 2134:"CatLab", 2135:"YMult", 2136:"SXViewLink",
	2137:"PivotChartBits", 2138:"FrtFontList", 2146:"SheetExt", 2147:"BookExt",
	2148:"SXAddl", 2149:"CrErr", 2150:"HFPicture", 2151:"FeatHdr", 2152:"Feat",
	2154:"DataLabExt", 2155:"DataLabExtContents", 2156:"CellWatch",
	2161:"FeatHdr11", 2162:"Feature11", 2164:"DropDownObjIds",
	2165:"ContinueFrt11", 2166:"DConn", 2167:"List12", 2168:"Feature12",
	2169:"CondFmt12", 2170:"CF12", 2171:"CFEx", 2172:"XFCRC", 2173:"XFExt",
	2174:"AutoFilter12", 2175:"ContinueFrt12", 2180:"MDTInfo", 2181:"MDXStr",
	2182:"MDXTuple", 2183:"MDXSet", 2184:"MDXProp", 2185:"MDXKPI", 2186:"MDB",
	2187:"PLV", 2188:"Compat12", 2189:"DXF", 2190:"TableStyles", 2191:"TableStyle",
	2192:"TableStyleElement", 2194:"StyleExt", 2195:"NamePublish", 2196:"NameCmt",
	2197:"SortData", 2198:"Theme", 2199:"GUIDTypeLib", 2200:"FnGrp12",
	2201:"NameFnGrp12", 2202:"MTRSettings", 2203:"CompressPictures",
	2204:"HeaderFooter", 2205:"CrtLayout12", 2206:"CrtMlFrt", 2207:"CrtMlFrtContinue",
	2211:"ForceFullCalculation", 2212:"ShapePropsStream", 2213:"TextPropsStream",
	2214:"RichTextStream", 2215:"CrtLayout12A", 4097:"Units", 4098:"Chart",
	4099:"Series", 4102:"DataFormat", 4103:"LineFormat", 4105:"MarkerFormat",
	4106:"AreaFormat", 4107:"PieFormat", 4108:"AttachedLabel", 4109:"SeriesText",
	4116:"ChartFormat", 4117:"Legend", 4118:"SeriesList", 4119:"Bar", 4120:"Line",
	4121:"Pie", 4122:"Area", 4123:"Scatter", 4124:"CrtLine", 4125:"Axis",
	4126:"Tick", 4127:"ValueRange", 4128:"CatSerRange", 4129:"AxisLine",
	4130:"CrtLink", 4132:"DefaultText", 4133:"Text", 4134:"FontX",
	4135:"ObjectLink", 4146:"Frame", 4147:"Begin", 4148:"End", 4149:"PlotArea",
	4154:"Chart3d", 4156:"PicF", 4157:"DropBar", 4158:"Radar", 4159:"Surf",
	4160:"RadarArea", 4161:"AxisParent", 4163:"LegendException", 4164:"ShtProps",
	4165:"SerToCrt", 4166:"AxesUsed", 4168:"SBaseRef", 4170:"SerParent",
	4171:"SerAuxTrend", 4174:"IFmtRecord", 4175:"Pos", 4176:"AlRuns",
	4177:"BRAI", 4187:"SerAuxErrBar", 4188:"ClrtClient", 4189:"SerFmt",
	4191:"Chart3DBarShape", 4192:"Fbi", 4193:"BopPop", 4194:"AxcExt",
	4195:"Dat", 4196:"PlotGrowth", 4197:"SIIndex", 4198:"GelFrame",
	4199:"BopPopCustom", 4200:"Fbi2"
	}

def RgceArea (hd,data,off):
	rf = struct.unpack("<H",data[off:off+2])[0]
	rl = struct.unpack("<H",data[off+2:off+4])[0]
	cf = struct.unpack("<H",data[off+4:off+6])[0]
	cl = struct.unpack("<H",data[off+6:off+8])[0]
	add_iter(hd,"\trowFirst",rf,off,2,"<H")
	add_iter(hd,"\trowLast",rl,off+2,2,"<H")
	add_iter(hd,"\tcolFirst",cf,off+4,2,"<H")
	add_iter(hd,"\tcolLast",cl,off+6,2,"<H")

def PtgAdd (hd,data,off):
	add_iter(hd,"Add","",off,1,"B")

def PtgConcat (hd,data,off):
	add_iter(hd,"Concat","",off,1,"B")

def PtgDiv (hd,data,off):
	add_iter(hd,"Div","",off,1,"B")

def PtgEq (hd,data,off):
	add_iter(hd,"Equal","",off,1,"B")

def PtgGe (hd,data,off):
	add_iter(hd,"Greater or Equal","",off,1,"B")

def PtgGt (hd,data,off):
	add_iter(hd,"Greater","",off,1,"B")

def PtgLe (hd,data,off):
	add_iter(hd,"Less or Equal","",off,1,"B")

def PtgLt (hd,data,off):
	add_iter(hd,"Less","",off,1,"B")

def PtgMul (hd,data,off):
	add_iter(hd,"Mul","",off,1,"B")

def PtgNe (hd,data,off):
	add_iter(hd,"Not Equal","",off,1,"B")

def PtgPower (hd,data,off):
	add_iter(hd,"Power","",off,1,"B")

def PtgSub (hd,data,off):
	add_iter(hd,"Sub","",off,1,"B")

def PtgArea (hd,data,off):
	add_iter(hd,"Area","",off,1,"B")
	RgceArea(hd,data,off+1)

def PtgNotImpl (hd,data,off):
	pass

ptg = {0x01:("PtgExp",PtgNotImpl),0x02:("PtgTbl",PtgNotImpl),0x03:("PtgAdd",PtgAdd),0x04:("PtgSub",PtgSub),
	0x05:("PtgMul",PtgMul),0x06:("PtgDiv",PtgDiv),0x07:("PtgPower",PtgPower),0x08:("PtgConcat",PtgConcat),
	0x09:("PtgLt",PtgLt),0x0A:("PtgLe",PtgLe),0x0B:("PtgEq",PtgEq),0x0C:("PtgGe",PtgGe),
	0x0D:("PtgGt",PtgGt),0x0E:("PtgNe",PtgNe),0x0F:("PtgIsect",PtgNotImpl),0x10:("PtgUnion",PtgNotImpl),
	0x11:("PtgRange",PtgNotImpl),0x12:("PtgUplus",PtgNotImpl),0x13:("PtgUminus",PtgNotImpl),0x14:("PtgPercent",PtgNotImpl),
	0x15:("PtgParen",PtgNotImpl),0x16:("PtgMissArg",PtgNotImpl),0x17:("PtgStr",PtgNotImpl),0x1C:("PtgErr",PtgNotImpl),
	0x1D:("PtgBool",PtgNotImpl),0x1E:("PtgInt",PtgNotImpl),0x1F:("PtgNum",PtgNotImpl),0x20:("PtgArray",PtgNotImpl),
	0x21:("PtgFunc",PtgNotImpl),0x22:("PtgFuncVar",PtgNotImpl),0x23:("PtgName",PtgNotImpl),0x24:("PtgRef",PtgNotImpl),
	0x25:("PtgArea",PtgArea),0x26:("PtgMemArea",PtgNotImpl),0x27:("PtgMemErr",PtgNotImpl),0x28:("PtgMemNoMem",PtgNotImpl),
	0x29:("PtgMemFunc",PtgNotImpl),0x2A:("PtgRefErr",PtgNotImpl),0x2B:("PtgAreaErr",PtgNotImpl),0x2C:("PtgRefN",PtgNotImpl),
	0x2D:("PtgAreaN",PtgNotImpl),0x39:("PtgNameX",PtgNotImpl),0x3A:("PtgRef3d",PtgNotImpl),0x3B:("PtgArea3d",PtgNotImpl),
	0x3C:("PtgRefErr3d",PtgNotImpl),0x3D:("PtgAreaErr3d",PtgNotImpl),0x40:("PtgArray",PtgNotImpl),0x41:("PtgFunc",PtgNotImpl),
	0x42:("PtgFuncVar",PtgNotImpl),0x43:("PtgName",PtgNotImpl),0x44:("PtgRef",PtgNotImpl),0x45:("PtgArea",PtgNotImpl),
	0x46:("PtgMemArea",PtgNotImpl),0x47:("PtgMemErr",PtgNotImpl),0x48:("PtgMemNoMem",PtgNotImpl),0x49:("PtgMemFunc",PtgNotImpl),
	0x4A:("PtgRefErr",PtgNotImpl),0x4B:("PtgAreaErr",PtgNotImpl),0x4C:("PtgRefN",PtgNotImpl),0x4D:("PtgAreaN",PtgNotImpl),
	0x59:("PtgNameX",PtgNotImpl),0x5A:("PtgRef3d",PtgNotImpl),0x5B:("PtgArea3d",PtgNotImpl),0x5C:("PtgRefErr3d",PtgNotImpl),
	0x5D:("PtgAreaErr3d",PtgNotImpl),0x60:("PtgArray",PtgNotImpl),0x61:("PtgFunc",PtgNotImpl),0x62:("PtgFuncVar",PtgNotImpl),
	0x63:("PtgName",PtgNotImpl),0x64:("PtgRef",PtgNotImpl),0x65:("PtgArea",PtgNotImpl),0x66:("PtgMemArea",PtgNotImpl),
	0x67:("PtgMemErr",PtgNotImpl),0x68:("PtgMemNoMem",PtgNotImpl),0x69:("PtgMemFunc",PtgNotImpl),0x6A:("PtgRefErr",PtgNotImpl),
	0x6B:("PtgAreaErr",PtgNotImpl),0x6C:("PtgRefN",PtgNotImpl),0x6D:("PtgAreaN",PtgNotImpl),0x79:("PtgNameX",PtgNotImpl),
	0x7A:("PtgRef3d",PtgNotImpl),0x7B:("PtgArea3d",PtgNotImpl),0x7C:("PtgRefErr3d",PtgNotImpl),0x7D:("PtgAreaErr3d",PtgNotImpl)}

ptg18 = {0x01:"PtgElfLel",0x02:"PtgElfRw",0x03:"PtgElfCol",0x06:"PtgElfRwV",
	0x07:"PtgElfColV",0x0A:"PtgElfRadical",0x0B:"PtgElfRadicalS",0x0D:"PtgElfColS",
	0x0F:"PtgElfColSV",0x10:"PtgElfRadicalLel",0x1D:"PtgSxName"}

ptg19 = {0x01:"PtgAttrSemi",0x02:"PtgAttrIf",0x04:"PtgAttrChoose",0x08:"PtgAttrGoto",
	0x10:"PtgAttrSum",0x20:"PtgAttrBaxcel",0x21:"PtgAttrBaxcel",0x40:"PtgAttrSpace",0x41:"PtgAttrSpaceSemi"}

def gentree():
	model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)
	view = gtk.TreeView(model)
	renderer = gtk.CellRendererText()
	column = gtk.TreeViewColumn('Group/Record', renderer, text=0)
	column2 = gtk.TreeViewColumn('Length', renderer, text=2)
	view.append_column(column)
	view.append_column(column2)
	iter = model.append(None, None)
	model.set(iter, 0, "XLS Records", 1, -1, 2, "")
	for i in rec_ids.items():
		niter = model.append (iter, None)
		model.set(niter, 0, i[1], 1, i[0], 2, "0")
	return model,view

def XLUnicodeRichExtendedString (hd,data,offset):
	cch = struct.unpack("<H",data[0+offset:2+offset])[0]
	flags = ord(data[offset+2])
	fHighByte = flags&1
	fExtSt = (flags&4)/4
	fRichSt = (flags&8)/8
	add_iter (hd,"  cch",cch,offset,2,"<H")
	add_iter (hd,"  fHighByte",fHighByte,offset+2,1,"<B")
	add_iter (hd,"  fExtSt",fExtSt,offset+2,1,"<B")
	add_iter (hd,"  fRichSt",fRichSt,offset+2,1,"<B")
	offset += 2
	if fRichSt:
		cRun = struct.unpack("<H",data[1+offset:3+offset])[0]
		add_iter (hd,"  cRun",cRun,offset+1,2,"<H")
		offset += 2
	if fExtSt:
		cbExtRst = struct.unpack("<I",data[1+offset:5+offset])[0]
		add_iter (hd,"  cbExtRst",cbExtRst,offset+1,4,"<H")
		offset += 4
	if fHighByte:
		text = unicode(data[offset+1:offset+1+cch*2],"utf16")
		add_iter (hd,"  text",text,offset+1,cch*2,"txt")
		offset += cch*2 + 1
	else:
		text = data[offset+1:offset+1+cch]
		add_iter (hd,"  text",text,offset+1,cch,"txt")
		offset += cch + 1
	if fRichSt:
		for i in range(cRun):
			ich = struct.unpack("<H",data[0+offset+i*4:2+offset+i*4])[0]
			ifnt = struct.unpack("<H",data[2+offset+i*4:4+offset+i*4])[0]
			add_iter (hd,"  ich %d"%i,ich,offset+i*4,2,"<H")
			add_iter (hd,"  ifnt %d"%i,ifnt,2+offset+i*4,2,"<H")
		offset += cRun*4
	if fExtSt:
		add_iter (hd,"  ExtRst",None,offset,cbExtRst,"txt")
		offset += cbExtRst
	return offset


lbl_flags = {1:"Hidden ",2:"Func ",3:"OB ",4:"Proc ",5:"CalcExp ",6:"Builtin "}
lbl_grp = ["All", "Financial", "Date Time", "Math Trigonometry", "Statistical",
	"Lookup", "Database", "Text", "Logical", "Info", "Commands", "Customize",
	"Macro Control", "DDE External", "User Defined", "Engineering", "Cube"]
lbl_names = ["Consolidate_Area", "Auto_Open", "Auto_Close", "Extract", "Database", "Criteria", "Print_Area", "Print_Titles", "Recorder", "Data_Form", "Auto_Activate", "Auto_Deactivate", "Sheet_Title", "_FilterDatabase"]
#0x18
def biff_lbl (hd,data):
	off = 4
	flags = struct.unpack("<H",data[0+off:2+off])[0]
	fname = ""
	fbltin = 0
	for i in range(6):
		if flags&(2**i):
			fname += lbl_flags[i+1]
			if i == 5:
				fbltin = 1

	if flags&(2**13):
		fname += "Published "
	if flags&(2**14):
		fname += "WrkBookParam"
	add_iter (hd,"Flags",fname,0+off,2,"<H")
	grp = (flags/64)&0x3F
	grpname = lbl_grp[grp]
	add_iter (hd,"Grp",grpname,0+off,2,"<H")
	chKey = ord(data[3+off])
	add_iter (hd,"chKey",chKey,3+off,1,"B")
	cch = ord(data[4+off])
	add_iter (hd,"cch",cch,4+off,1,"B")
	cce = struct.unpack("<H",data[5+off:7+off])[0]
	add_iter (hd,"cce",cce,5+off,2,"<H")
	rsrv3 = struct.unpack("<H",data[7+off:9+off])[0]
	itab = struct.unpack("<H",data[9+off:11+off])[0]
	add_iter (hd,"itab",itab,9+off,2,"<H")
	#rsrv4 1 byte
	#rsrv5 1 byte
	#rsrv6 1 byte
	#rsrv7 1 byte ??? seems to be fHightByte
	fhb = ord(data[14+off])
	add_iter (hd,"fHighByte",fhb,41+off,1,"B")
	if fbltin:
		lname = lbl_names[ord(data[15+off])]
	else:
		if fhb == 0:
			lname = data[15+off:15+chKey+off]
		else:
			lname = unicode(data[15+off:15+chKey+off],"utf16")
	add_iter (hd,"Name",lname,15+off,chKey,"txt")
	# FIXME: parse the whole expression
	pkey = ord(data[15+chKey+off])
	if ptg.has_key(pkey):
		ptg[pkey][1](hd,data,off+chKey+15)

#0x31
def biff58_font (hd,data):
	off = 4
	fonth = struct.unpack("<H",data[0+off:2+off])[0]
	flags = struct.unpack("<H",data[2+off:4+off])[0]
	clridx = struct.unpack("<H",data[4+off:6+off])[0]
	fontw = struct.unpack("<H",data[6+off:8+off])[0]
	esc = struct.unpack("<H",data[8+off:0xa+off])[0]
	et = ""
	if escapement.has_key(esc):
		et = escapement[esc]
	und = ord(data[0xa+off])
	ut = ""
	if underline.has_key(und):
		ut = underline[und]
	fam = ord(data[0xb+off])
	cset = ord(data[0xc+off])
	cst = ""
	if charsets.has_key(cset):
		cst = charsets[cset]
	fnlen = ord(data[0xe+off])
	fname = data[0xf+off:0xf+fnlen+off]
	if hd.version == 8:
		if ord(data[0xf+off]) == 1:
			fname = unicode(data[0x10+off:0x10+fnlen*2+off],"utf-16")
		else:
			fname = data[0x10+off:0x10+fnlen*2+off]

	add_iter (hd,"Font Height",fonth,0+off,2,"<H")
	add_iter (hd,"Option Flags",flags,2+off,2,"<H")
	add_iter (hd,"Color Index",clridx,4+off,2,"<H")
	add_iter (hd,"Font Weight",fontw,6+off,2,"<H")
	add_iter (hd,"Escapement","%02x (%s)"%(esc,et),8+off,2,"<H")
	add_iter (hd,"Underline","%02x (%s)"%(und,ut),0xa+off,1,"<B")
	add_iter (hd,"Font Family",fam,0xb+off,1,"<B")
	add_iter (hd,"Charset","%02x (%s)"%(cset,cst),0xc+off,2,"<B")
	add_iter (hd,"Font Name Length",fnlen,0xe+off,2,"<B")
	add_iter (hd,"Font Name",fname,0x10+off,fnlen,"txt")


xf_flags = {1:"Locked ",2:"Hidden ",3:"Style ",4:"123Prefix "}

#0x55
def biff_defcolw (hd,data):
	off = 4
	cw = struct.unpack("<H",data[0+off:2+off])[0]
	add_iter (hd,"cchdefColWidth",cw,off,2,"<H")

#0x7d
def biff_colinfo (hd,data):
	off = 4
	colFirst = struct.unpack("<H",data[0+off:2+off])[0]
	colLast = struct.unpack("<H",data[2+off:4+off])[0]
	coldx = struct.unpack("<H",data[4+off:6+off])[0]
	ixfe = struct.unpack("<H",data[6+off:8+off])[0]
	flags1 = ord(data[8+off])
	flags2 = ord(data[9+off])
	unused = struct.unpack("<H",data[10+off:12+off])[0]
	fHidden = flags1&1
	fUserSet = (flags1&2)/2
	fBestFit = (flags1&4)/4
	fPhonetic = (flags1&8)/8
	iOutLevel = flags2&7
	fCollapsed = (flags2&16)/16
	add_iter (hd,"colFirst",colFirst,off,2,"<H")
	add_iter (hd,"colLast",colLast,off+2,2,"<H")
	add_iter (hd,"coldx",coldx,off+4,2,"<H")
	add_iter (hd,"ixfe",ixfe,off+6,2,"<H")
	add_iter (hd,"fHidden",fHidden,off+8,1,"<B")
	add_iter (hd,"fUserSet",fUserSet,off+8,1,"<B")
	add_iter (hd,"fBestFit",fBestFit,off+8,1,"<B")
	add_iter (hd,"fPhonetic",fPhonetic,off+8,1,"<B")
	add_iter (hd,"iOutLevel",iOutLevel,off+9,1,"<B")
	add_iter (hd,"fCollapsed",fCollapsed,off+9,1,"<B")

#0xe0
def biff_xf (hd,data):
	off = 4
	fontidx = struct.unpack("<H",data[0+off:2+off])[0]
	numfmt = struct.unpack("<H",data[2+off:4+off])[0]
	flags = struct.unpack("<H",data[4+off:6+off])[0]
	fstyle = (flags&4)/4
	xfparent = flags/16
	fname = ""
	for i in range(4):
		if flags&(2**i):
			fname += xf_flags[i+1]
	add_iter (hd,"Font IDX",fontidx,0+off,2,"<H")
	add_iter (hd,"Num format",numfmt,2+off,2,"<H")
	add_iter (hd,"Flags/Parent","%s  %02x"%(fname,xfparent),4+off,2,"<H")
	off = 10
	alc = ord(data[off])&7
	fWrap = (ord(data[off])&8)/8
	alcV = (ord(data[off])&70)/0x10
	fJustLast = (ord(data[off])&80)/0x80
	trot = ord(data[off+1])
	cIndent = ord(data[off+2])&0xF
	fShrinkToFit = (ord(data[off+2])&0x10)/0x10
	rsvd1 = (ord(data[off+2])&0x20)/0x20
	iReadOrder = (ord(data[off+2])&0xc0)/0x40
	unused = ord(data[off+3])
	dgLeft = ord(data[off+4])&0xF
	dgRight = (ord(data[off+4])&0xF0)/0x10
	dgTop = ord(data[off+5])&0xF
	dgBottom = (ord(data[off+5])&0xF0)/0x10
	lrg = struct.unpack("<H",data[6+off:8+off])[0]
	icvLeft = lrg&0x7f
	icvRight = (lrg&0x3f80)/0x80
	grbitDiag = (lrg&0xc000)/0x4000
	tbd = struct.unpack("<I",data[8+off:12+off])[0]
	icvTop = tbd&0x7f
	icvBottom = (tbd&0x3f80)/0x80
	icvDiag = (tbd&0x1fc000)/0x4000
	dgDiag = (tbd&0x1e00000)/0x200000
	rsvd2 = (tbd&0x2000000)/0x2000000
	fls = (tbd&0xfc000000)/0x4000000
	pfb = struct.unpack("<H",data[12+off:14+off])[0]
	icvFore = pfb&0x7f
	icvBack = (pfb&0x3f80)/0x80
	rsvd3 = (pfb&0xc000)/0x4000
	add_iter (hd,"alc",alc,off,1,"<B")
	add_iter (hd,"fWrap",fWrap,off,1,"<B")
	add_iter (hd,"alcV",alcV,off,1,"<B")
	add_iter (hd,"fJustLast",fJustLast,off,1,"<B")
	add_iter (hd,"trot",trot,off+1,1,"<B")
	add_iter (hd,"cIndent",cIndent,off+2,1,"<B")
	add_iter (hd,"fShrinkToFit",fShrinkToFit,off+2,1,"<B")
	add_iter (hd,"rsvd1",rsvd1,off+2,1,"<B")
	add_iter (hd,"iReadOrder",iReadOrder,off+2,1,"<B")
	add_iter (hd,"unused",unused,off+3,1,"<B")
	add_iter (hd,"dgLeft",dgLeft,off+4,1,"<B")
	add_iter (hd,"dgRight",dgRight,off+4,1,"<B")
	add_iter (hd,"dgTop",dgTop,off+5,1,"<B")
	add_iter (hd,"dgBottom",dgBottom,off+5,1,"B")
	add_iter (hd,"icvLeft",icvLeft,off+6,1,"<B")
	add_iter (hd,"icvRight",icvRight,off+6,1,"<B")
	add_iter (hd,"grbitDiag",grbitDiag,off+7,1,"<B")
	add_iter (hd,"icvTop",icvTop,off+8,1,"<B")
	add_iter (hd,"icvBottom",icvBottom,off+9,1,"<B")
	add_iter (hd,"dgDiag",dgDiag,off+10,1,"<B")
	add_iter (hd,"rsvd2",rsvd2,off+11,1,"<B")
	add_iter (hd,"fls",fls,off+11,1,"<B")
	add_iter (hd,"icvFore",icvFore,off+12,1,"<B")
	add_iter (hd,"icvBack",icvBack,off+13,1,"<B")
	add_iter (hd,"rsvd3",rsvd3,off+13,1,"<B")

#0xe5
def biff_mergecells (hd,data):
	off = 4
	cmcs = struct.unpack("<H",data[0+off:2+off])[0]
	add_iter (hd,"cmcs",cmcs,off,2,"<H")
	for i in range(cmcs):
		rwFirst = struct.unpack("<H",data[2+off+i*8:4+off+i*8])[0]
		rwLast = struct.unpack("<H",data[4+off+i*8:6+off+i*8])[0]
		colFirst = struct.unpack("<H",data[6+off+i*8:8+off+i*8])[0]
		colLast = struct.unpack("<H",data[8+off+i*8:10+off+i*8])[0]
		add_iter (hd,"rwFirst %d"%i,rwFirst,off+2+i*8,2,"<H")
		add_iter (hd,"  rwLast %d"%i,rwLast,off+4+i*8,2,"<H")
		add_iter (hd,"  colFirst %d"%i,colFirst,off+6+i*8,2,"<H")
		add_iter (hd,"  colLast %d"%i,colLast,off+8+i*8,2,"<H")

#0xfc
def biff_sst (hd,data):
	off = 4
	cstTotal = struct.unpack("<I",data[0+off:4+off])[0]
	cstUnique = struct.unpack("<I",data[4+off:8+off])[0]
	add_iter (hd,"cstTotal",cstTotal,off,4,"<I")
	add_iter (hd,"cstUnique",cstUnique,off+4,4,"<I")
	offset = 12
	for i in range(cstUnique):
		add_iter (hd,"rgb %d"%i,None,0,0,"txt")
		offset = XLUnicodeRichExtendedString (hd,data,offset)

#0xfd
def biff_labelsst (hd,data):
	off = 4
	biff_blank(hd,data)
	isst = struct.unpack("<I",data[6+off:10+off])[0]
	add_iter (hd,"isst",isst,6+off,4,"<I")

#0x1ae
def biff_supbook (hd,data):
	off = 4
	ctab = struct.unpack("<H",data[0+off:2+off])[0]
	cch = struct.unpack("<H",data[2+off:4+off])[0]
	add_iter (hd,"ctab",ctab,0+off,2,"<H")
	add_iter (hd,"cch",cch,2+off,2,"<H")

#0x200
def biff_dimensions (hd,data):
	off = 4
	rwMic = struct.unpack("<I",data[0+off:4+off])[0]
	rwMac = struct.unpack("<I",data[4+off:8+off])[0]
	colMic = struct.unpack("<H",data[8+off:10+off])[0]
	colMac = struct.unpack("<H",data[10+off:12+off])[0]
	add_iter (hd,"rwMic",rwMic,off,4,"<I")
	add_iter (hd,"rwMac",rwMac,off+4,4,"<I")
	add_iter (hd,"colMic",colMic,off+8,2,"<H")
	add_iter (hd,"colMac",colMac,off+10,2,"<H")

#0x201
def biff_blank(hd,data):
	off = 4
	rw = struct.unpack("<H",data[0+off:2+off])[0]
	col = struct.unpack("<H",data[2+off:4+off])[0]
	ixfe = struct.unpack("<H",data[4+off:6+off])[0]
	add_iter (hd,"rw",rw,off,2,"<H")
	add_iter (hd,"col",col,off+2,2,"<H")
	add_iter (hd,"ixfe",ixfe,off+4,2,"<H")

#0x203
def biff_number (hd,data):
	off = 4
	biff_blank(hd,data)
	num = struct.unpack("<d",data[6+off:14+off])[0]
	add_iter (hd,"num",num,6+off,8,"<d")

#0x208
def biff_row (hd,data):
	off = 4
	rw = struct.unpack("<H",data[0+off:2+off])[0]
	colMic = struct.unpack("<H",data[2+off:4+off])[0]
	colMac = struct.unpack("<H",data[4+off:6+off])[0]
	miyRw = struct.unpack("<H",data[6+off:8+off])[0]
	rsrv1 = struct.unpack("<H",data[8+off:10+off])[0]
	unused1 = struct.unpack("<H",data[10+off:12+off])[0]
	flags1 = ord(data[12+off])
	iOutLevel = flags1&7
	fCollapsed = (flags1&16)/16
	fDyZero = (flags1&32)/32
	fUnsync= (flags1&64)/64
	fGhostDirty = (flags1&128)/128
	flags2 = struct.unpack("<H",data[14+off:16+off])[0]
	ixfe_val = flags2&0xFFF
	flags2 /= 4096
	fExAsc = flags2&1
	fExDes = (flags2&2)/2
	fPhonetic = (flags2&4)/4
	add_iter (hd,"rw",rw,off,2,"<H")
	add_iter (hd,"colMic",colMic,off+2,2,"<H")
	add_iter (hd,"colMac",colMac,off+4,2,"<H")
	add_iter (hd,"miyRw",miyRw,off+6,2,"<H")
	add_iter (hd,"iOutLevel",iOutLevel,12+off,1,"<B")
	add_iter (hd,"fCollapsed",fCollapsed,12+off,1,"<B")
	add_iter (hd,"fDyZero",fDyZero,12+off,1,"<B")
	add_iter (hd,"fUnsync",fUnsync,12+off,1,"<B")
	add_iter (hd,"fGhostDirty",fGhostDirty,12+off,1,"<B")
	add_iter (hd,"ixfe_val",ixfe_val,14+off,2,"<H")
	add_iter (hd,"fExAsc",fExAsc,15+off,1,"<B")
	add_iter (hd,"fExDes",fExDes,15+off,1,"<B")
	add_iter (hd,"fPhonetic",fPhonetic,15+off,1,"<B")

#0x225
def biff_defrowh (hd,data):
	off = 4
	flags = struct.unpack("<H",data[0+off:2+off])[0]
	fUnsync = flags&1
	fDyZero = (flags&2)/2
	fExAsc = (flags&4)/4
	fExDes = (flags&8)/8
	add_iter (hd,"fUnsync",fUnsync,off,1,"<B")
	add_iter (hd,"fDyZero",fDyZero,off,1,"<B")
	add_iter (hd,"fExAsc",fExAsc,off,1,"<B")
	add_iter (hd,"fExDes",fExDes,off,1,"<B")
	if fDyZero == 0:
		miyRw = struct.unpack("<H",data[2+off:4+off])[0]
		add_iter (hd,"miyRw",miyRw,off+2,2,"<H")
	else:
		miyRwHidden = struct.unpack("<H",data[4+off:6+off])[0]
		add_iter (hd,"miyRwHidden",miyRwHidden,off+4,2,"<H")

#0x27e
def biff_rk (hd,data):
	off = 4
	biff_blank(hd,data)
	value = struct.unpack("<I",data[6+off:10+off])[0]
	fx100 = value&1
	fint = (value&2)/2
	num = value/4
	add_iter (hd,"fx100",fx100,6+off,1,"B")
	add_iter (hd,"fint",fint,6+off,1,"B")
	if fint:
		numv = num
	else:
		n = struct.pack("\x00\x00\x00\x00"+num*4)
		numv = struct.unpack("<d",n)
	if fx100:
		numv *= 100
	
	add_iter (hd,"num (%d)"%numv,num,6+off,4,"<I")

biff5_ids = {0x18:biff_lbl, 0x31:biff58_font,0x55:biff_defcolw,0x7d:biff_colinfo,0xe0:biff_xf,
	0xe5:biff_mergecells,0xfc:biff_sst,0xfd:biff_labelsst,
	0x1ae:biff_supbook,0x200:biff_dimensions,0x201:biff_blank,0x203:biff_number,0x208:biff_row,0x225:biff_defrowh,
	0x27e:biff_rk}

def parse (page, data, parent):
	offset = 0
	ftype = "XLS"
	idx = 0
	lblidx = 1
	iters = []
	iters.append(parent)
	print "Length of iters ",len(iters)
	curiter = iters[len(iters)-1]
	try:
		while offset < len(data) - 4:
			rtype = struct.unpack("<H",data[offset:offset+2])[0]
			if rtype == 0:
				break
			iter1 = page.model.append(curiter,None)
			rname = ""
			if rec_ids.has_key(rtype):
				rname = rec_ids[rtype]
			if rtype == 0x809:
				iters.append(iter1)
				curiter = iter1
				ver = struct.unpack("<H",data[offset+4:offset+6])[0]
				dt = struct.unpack("<H",data[offset+6:offset+8])[0]
				if substream.has_key(dt):
					rname = "BOF (%s)"%substream[dt]
				else:
					rname = "BOF (unknown)" 
				if ver == 0x500:
					ftype = "XLS5"
					page.version = 5
					print "Version: 5"
				elif ver == 0x600:
					ftype = "XLS8"
					page.version = 8
					print "Version: 8"
			elif rtype == 10 or rtype == 0x1034:
				iters.pop()
				curiter = iters[len(iters)-1]
			elif rtype == 0x1033:
				iters.append(iter1)
				curiter = iter1
#			elif rtype == 0x208: #row
#				rname = "Row %04x"%struct.unpack("<H",data[offset+0x10:offset+0x12])
			elif rtype == 0xe0: #xf
				rname = "XF %02x"%idx
				idx += 1
			elif rtype == 0x18: #Lbl
				rname = "Lbl %02x"%lblidx
				lblidx += 1
			offset += 2
			rlen = struct.unpack("<H",data[offset:offset+2])[0]
			offset += 2
			rdata = data[offset-4:offset+rlen]
			page.model.set_value(iter1,0,rname)
			page.model.set_value(iter1,1,("xls",rtype))
			page.model.set_value(iter1,2,rlen)
			page.model.set_value(iter1,3,rdata)
			page.model.set_value(iter1,7,"0x%02x"%rtype)
			page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
			if rtype == 0xec: #MsoDrawing
				escher.parse (page.model,rdata[4:],iter1)
			offset += rlen
	except:
		print "Something was wrong in XLS parse"

	return ftype

def collect_tree (model, parent, value=""):
	for i in range(model.iter_n_children(parent)):
		citer = model.iter_nth_child(parent, i)
		print 'mname',model.get_value(citer,0)

		value += model.get_value(citer,3)
		if model.iter_n_children(citer):
#			print 'We call collect',len(value)
			value = collect_tree(model, citer, value)
	return value

def dump_iter (model, parent, outfile):
	ntype = model.get_value(parent,1)
	name = model.get_value(parent,0)
	value = ""
	if name == 'Workbook' or name == 'Book':
		value = collect_tree(model, parent)
	else:
		value = model.get_value(parent,3)
	child = cgsf.gsf_outfile_new_child(outfile,name,0)
	cgsf.gsf_output_write (child,len(value),value)
	cgsf.gsf_output_close (child)


def save (page, fname):
	model = page.view.get_model()
	cgsf.gsf_init()
	output = cgsf.gsf_output_stdio_new (fname)
	outfile = cgsf.gsf_outfile_msole_new (output);
	iter1 = model.get_iter_first()
	while None != iter1:
	  dump_iter (model, iter1, outfile)
	  iter1 = model.iter_next(iter1)
	cgsf.gsf_output_close(outfile)
	cgsf.gsf_shutdown()
