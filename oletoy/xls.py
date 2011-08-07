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
import gtk,gsf
import tree
import hexdump
import oleparse

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

def add_iter (hd,name,value,offset,length,vtype):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype)

def biff58_font (hd,data):
	fonth = struct.unpack("<H",data[0:2])[0]
	flags = struct.unpack("<H",data[2:4])[0]
	clridx = struct.unpack("<H",data[4:6])[0]
	fontw = struct.unpack("<H",data[6:8])[0]
	esc = struct.unpack("<H",data[8:0xa])[0]
	et = ""
	if escapement.has_key(esc):
		et = escapement[esc]
	und = ord(data[0xa])
	ut = ""
	if underline.has_key(und):
		ut = underline[und]
	fam = ord(data[0xb])
	cset = ord(data[0xc])
	cst = ""
	if charsets.has_key(cset):
		cst = charsets[cset]
	fnlen = ord(data[0xe])
	fname = data[0xf:0xf+fnlen]
	if hd.version == 8:
		fname = unicode(data[0x10:0x10+fnlen*2],"utf-16")
	add_iter (hd,"Font Height",fonth,0,2,"<H")
	add_iter (hd,"Option Flags",flags,2,2,"<H")
	add_iter (hd,"Color Index",clridx,4,2,"<H")
	add_iter (hd,"Font Weight",fontw,6,2,"<H")
	add_iter (hd,"Escapement","%02x (%s)"%(esc,et),8,2,"<H")
	add_iter (hd,"Underline","%02x (%s)"%(und,ut),0xa,1,"<B")
	add_iter (hd,"Font Family",fam,0xb,1,"<B")
	add_iter (hd,"Charset","%02x (%s)"%(cset,cst),0xc,2,"<B")
	add_iter (hd,"Font Name Length",fnlen,0xe,2,"<B")
	add_iter (hd,"Font Name",fname,0xf,fnlen,"txt")


biff5_ids = {0x31:biff58_font}

def parse (page, data, parent):
	offset = 0
	type = "XLS"
	curiter = parent
	idx = 0
	while offset < len(data) - 4:
		rtype = struct.unpack("<H",data[offset:offset+2])[0]
		if rtype == 0:
			break
		iter1 = page.model.append(curiter,None)
		rname = ""
		if rec_ids.has_key(rtype):
			rname = rec_ids[rtype]
		if rtype == 0x809:
			curiter = iter1
			ver = struct.unpack("<H",data[offset+4:offset+6])[0]
			dt = struct.unpack("<H",data[offset+6:offset+8])[0]
			if substream.has_key(dt):
				rname = "BOF (%s)"%substream[dt]
			else:
				rname = "BOF (unknown)" 
			if ver == 0x500:
				type = "XLS5"
				page.version = 5
				print "Version: 5"
			elif ver == 0x600:
				type = "XLS8"
				page.version = 8
				print "Version: 8"
		elif rtype == 10:
			curiter = parent
		elif rtype == 0x208: #row
			rname = "Row %04x"%struct.unpack("<H",data[offset+0x10:offset+0x12])
		elif rtype == 0xe0: #xf
			rname = "XF %02x"%idx
			idx += 1
		offset += 2
		rlen = struct.unpack("<H",data[offset:offset+2])[0]
		offset += 2
		rdata = data[offset:offset+rlen]
		page.model.set_value(iter1,0,rname)
		page.model.set_value(iter1,1,("xls",rtype))
		page.model.set_value(iter1,2,rlen)
		page.model.set_value(iter1,3,rdata)
		page.model.set_value(iter1,7,"0x%02x"%rtype)
		page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
		offset += rlen
