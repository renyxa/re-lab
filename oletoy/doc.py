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
import inflate
import ctypes

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')


charsets = {0:"Latin", 1:"System default", 2:"Symbol", 77:"Apple Roman",
	128:"Japanese Shift-JIS",129:"Korean (Hangul)",130:"Korean (Johab)",
	134:"Chinese Simplified GBK",136:"Chinese Traditional BIG5",
	161:"Greek",162:"Turkish",163:"Vietnamese",177:"Hebrew",178:"Arabic",
	186:"Baltic",204:"Cyrillic",222:"Thai",238:"Latin II (Central European)",
	255:"OEM Latin I"}

escapement = {0:"None", 1:"Superscript", 2:"Subscript"}

underline = {0:"None",1:"Single",2:"Double",0x21:"Single accounting",0x22:"Double accounting"}

def add_hditer (hd,name,value,offset,length,vtype):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype)

def add_pgiter (page, name, ftype, stype, data, parent = None):
	iter1 = page.model.append (parent,None)
	page.model.set_value(iter1,0,name)
	page.model.set_value(iter1,1,(ftype,stype))
	page.model.set_value(iter1,2,len(data))
	page.model.set_value(iter1,3,data)
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	return iter1


def fib_base (hd, data):
	off = 0
	add_hditer(hd,"wIdent",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"nFib",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"unused",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"lid",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"pnNext",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	# FIXME
	add_hditer(hd,"FixMe (flags)",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"nFibBack",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"iKey",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"envr",ord(data[off]),off,1,"B")

def fib_RgW (hd, data):
	off = 0
	add_hditer(hd,"csw",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	for i in range(13):
		add_hditer(hd,"rsrv%d"%(i+1),struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
		off += 2
	add_hditer(hd,"lidFE",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")

def fib_RgLw (hd, data):
	off = 0
	add_hditer(hd,"cslw",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_hditer(hd,"cbMac",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"rsrv1",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"rsrv2",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpText",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpFtn",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpHdd",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"rsrv3",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpAtn",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpEdn",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpTxbx",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"ccpHdrTxbx",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	for i in range(11):
		add_hditer(hd,"rsrv%d"%(i+4),struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

#fcStshf -- StyleSheet offset in Table
#fcPlcffndRef -- Footnotes refs offset
#fcPlcffndTxt -- Footnotes text offset
#fcPlcfandRef -- Dates/Locations of comments offset
#fcPlcfandTxt -- Text of comments offset
#fcPlcfSed -- PropList location offset
#fcPlcPad -- undef, ignore
#fcPlcfPhe -- ver specific para height info offset
#fcSttbfGlsy -- autotext offset
#fcPlcfGlsy -- autotext offset
#fcPlcfHdd -- header/footer locations offset
#fcPlcfBteChpx -- PlcBteChpx offset
#fcPlcfBtePapx -- PlcfBtePapx offset
#fcPlcfSea -- undef, ignore
#fcSttbfFfn -- fonts spec offset
#fcPlcfFldMom -- field chars location offset
#fcPlcfFldHdr -- header field chars location offset
#fcPlcfFldFtn -- footer field chars location offset
#fcPlcfFldAtn -- comments field chars location offset
#fcPlcfFldMcr -- undef, ignore
#fcSttbfBkmk -- bookmarks name offset
#fcPlcfBkf -- standard bookmark offset
#fcPlcfBkl -- standard bookmark offset
#fcCmds -- command customizations offset
#fcUnused1 -- undef, ignore
#fcSttbfMcr -- undef, ignore
#fcPrDrvr -- printer driver info offset
#fcPrEnvPort -- print env in portrait mode offset
#fcPrEnvLand -- print env in landscape mode offset
#fcWss -- last selection offset
#fcDop -- Dop offset
#fcSttbfAssoc -- strings offset
#fcClx -- Clx offset
#fcPlcfPgdFtn -- undef, ignore
#fcAutosaveSource -- undef, ignore
#fcGrpXstAtnOwners -- comments authors offset
#fcSttbfAtnBkmk -- annotation bookmarks offset
#fcUnused2 -- undef, ignore
#fcUnused3 -- undef, ignore
#fcPlcSpaMom -- shape info offset
#fcPlcSpaHdr -- header shape info offset
#fcPlcfAtnBkf -- annotation bookmark offset
#fcPlcfAtnBkl -- annotation bookmark offset
#fcPms -- print merge offset
#FormFldSttbs
#PlcfendRef 
#PlcfFldEdn
#Unused4
#DggInfo
#SttbfRMark
#SttbfCaption
#SttbfAutoCaption
#PlcfWkb
#PlcfSpl
#PlcftxbxTxt
#PlcfFldTxbx
#PlcfHdrtxbxTxt
#PlcffldHdrTxbx
#StwUser
#SttbTtmbd
#CookieData
#PgdMotherOldOld
#BkdMotherOldOld
#PgdFtnOldOld
#BkdFtnOldOld
#PgdEdnOldOld
#BkdEdnOldOld
#SttbfIntlFld
#RouteSlip
#SttbSavedBy
#SttbFnm
#PlfLst
#PlfLfo
#PlcfTxbxBkd
#PlcfTxbxHdrBkd
#DocUndoWord9
#RgbUse
#Usp
#Uskf
#PlcupcRgbUse
#PlcupcUsp
#SttbGlsyStyle
#Plcosl
#Plcocx
#PlcfBteLvc


fclcb97recs1 = ["StshfOrig","Stshf","PlcffndRef","PlcffndTxt","PlcfandRef",
  "PlcfandTxt","PlcfSed","PlcPad","PlcfPhe","SttbfGlsy","PlcfGlsy",
  "PlcfHdd","PlcfBteChpx","PlcfBtePapx","PlcfSea","SttbfFfn","PlcfFldMom",
  "PlcfFldHdr","PlcfFldFtn","PlcfFldAtn","PlcfFldMcr","SttbfBkmk",
  "PlcfBkf","PlcfBkl","Cmds","Unused1","SttbfMcr","PrDrvr","PrEnvPort",
  "PrEnvLand","Wss","Dop","SttbfAssoc","Clx","PlcfPgdFtn","AutosaveSource",
  "GrpXstAtnOwners","SttbfAtnBkmk","Unused2","Unused3","PlcSpaMom",
  "PlcSpaHdr","PlcfAtnBkf","PlcfAtnBkl","Pms","FormFldSttbs","PlcfendRef",
  "PlcfendTxt","PlcfFldEdn","Unused4","DggInfo","SttbfRMark","SttbfCaption",
  "SttbfAutoCaption","PlcfWkb","PlcfSpl","PlcftxbxTxt","PlcfFldTxbx",
  "PlcfHdrtxbxTxt","PlcffldHdrTxbx","StwUser","SttbTtmbd","CookieData",
  "PgdMotherOldOld","BkdMotherOldOld","PgdFtnOldOld","BkdFtnOldOld",
  "PgdEdnOldOld","BkdEdnOldOld","SttbfIntlFld","RouteSlip","SttbSavedBy",
  "SttbFnm","PlfLst","PlfLfo","PlcfTxbxBkd","PlcfTxbxHdrBkd",
  "DocUndoWord9","RgbUse","Usp","Uskf","PlcupcRgbUse","PlcupcUsp",
  "SttbGlsyStyle","Plgosl","Plcocx","PlcfBteLvc"]

#dwLowDateTime
#dwHighDateTime

#PlcfLvcPre10

fclcb97recs2 = ["PlcfLvcPre10","PlcfAsumy","PlcfGram","SttbListNames","SttbfUssr"]

def FcLcb97 (hd,data):
	off = 2
	for i in fclcb97recs1:
		add_hditer(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_hditer(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
	add_hditer(hd,"dwLowDateTime",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_hditer(hd,"dwHighDateTime",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	for i in fclcb97recs2:
		add_hditer(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_hditer(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

fclcb2krecs = ["PlcfTch","RmdThreading","Mid","SttbRgtplc","MsoEnvelope",
  "PlcfLad","RgDofr","Plcosl","PlcfCookieOld","PgdMotherOld","BkdMotherOld",
  "PgdFtnOld","BkdFtnOld","PgdEdnOld","BkdEdnOld"]

def FcLcb2k (hd,data):
	FcLcb97 (hd,data)
	off = 746
	for i in fclcb2krecs:
		add_hditer(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_hditer(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

fclcb2k2recs = ["Unused1","PlcfPgp","Plcfuim","PlfguidUim","AtrdExtra",
  "Plrsid","SttbfBkmkFactoid","PlcfBkfFactoid","Plcfcookie","PlcfBklFactoid",
  "FactoidData","DocUndo","SttbfBkmkFcc","PlcfBkfFcc","PlcfBklFcc",
  "SttbfbkmkBPRepairs","PlcfbkfBPRepairs","PlcfbklBPRepairs","PmsNew",
  "ODSO","PlcfpmiOldXP","PlcfpmiNewXP","PlcfpmiMixedXP","Unused2","Plcffactoid",
  "PlcflvcOldXP","PlcflvcNewXP","PlcflvcMixedXP"]

def FcLcb2k2 (hd,data):
	FcLcb2k (hd,data)
	off = 866
	for i in fclcb2k2recs:
		add_hditer(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_hditer(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

fclcb2k3recs = ["Hplxsdr","SttbfBkmkSdt","PlcfBkfSdt","PlcfBklSdt","CustomXForm",
  "SttbfBkmkProt","PlcfBkfProt","PlcfBklProt","SttbProtUser","Unused","PlcfpmiOld",
  "PlcfpmiOldInline","PlcfpmiNew","PlcfpmiNewInline","PlcflvcOld","PlcflvcOldInline",
  "PlcflvcNew","PlcflvcNewInline","PgdMother","BkdMother","AfdMother","PgdFtn",
  "BkdFtn","AfdFtn","PgdEdn","BkdEdn","AfdEdn","Afd"]

def FcLcb2k3 (hd,data):
	FcLcb2k2 (hd,data)
	off = 1090
	for i in fclcb2k3recs:
		add_hditer(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_hditer(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

fclcb2k7recs = ["Plcfmthd","SttbfBkmkMoveFrom","PlcfBkfMoveFrom","PlcfBklMoveFrom",
  "SttbfBkmkMoveTo","PlcfBkfMoveTo","PlcfBklMoveTo","Unused1","Unused2",
  "Unused3","SttbfBkmkArto","PlcfBkfArto","PlcfBklArto","ArtoData",
  "Unused4","Unused5","Unused6","OssTheme","ColorSchemeMapping"]

def FcLcb2k7 (hd,data):
	FcLcb2k3 (hd,data)
	off = 1314
	for i in fclcb2k7recs:
		add_hditer(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_hditer(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

def fib_RgFcLcbBlob (hd, data):
	off = 0
	cb = struct.unpack("<H",data[off:off+2])[0]
	add_hditer(hd,"cbRgFcLcb",cb,off,2,"<H")
	off += 2
	if fclcb2nfib.has_key(cb):
	  fclcb2nfib[cb][1](hd,data)

fclcb2nfib = {0x5d:(0xc1,FcLcb97),0x6c:(0xd9,FcLcb2k),0x88:(0x101,FcLcb2k2),0xa4:(0x10c,FcLcb2k3),0xb7:(0x112,FcLcb2k7)}
recs = {"base":fib_base,"fibRgW":fib_RgW,"fibRgLw":fib_RgLw, "fibRgFcLcbBlob":fib_RgFcLcbBlob}

def parse (page, data, parent):
	offset = 0
	type = "DOC"
	add_pgiter (page,"Base","doc","base",data[0:0x20],parent)
	offset += 0x20
	csw = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgW","doc","fibRgW",data[offset:offset+2+csw*2],parent)
	offset += 2+csw*2
	cslw = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgLw","doc","fibRgLw",data[offset:offset+2+cslw*4],parent)
	offset += 2+cslw*4
	cbRgFcLcb = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgFcLcbBlob","doc","fibRgFcLcbBlob",data[offset:offset+2+cbRgFcLcb*8],parent)
	offset += 2+cbRgFcLcb*8
	cswNew = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgCswNew","doc","fibRgCswNew",data[offset:offset+2+cswNew*2],parent)


def dump_tree (model, parent, outfile):
	ntype = model.get_value(parent,1)
	name = model.get_value(parent,0)
	if ntype[1] == 0:
	  child = cgsf.gsf_outfile_new_child(outfile,name,0)
	  value = model.get_value(parent,3)
	  if name[:6] == "Module":
		piter = model.iter_nth_child(parent,0)
		data = model.get_value(piter,3)
		srcoff = model.get_value(piter,1)[2]
		off = 0
		value = value[:srcoff]
		while  off + 4094 < len(data):
		  value += "\x30\x00"+data[off:off+4094]
		  off += 4094
		if off < len(data):
		  res = inflate.deflate(data[off:],1)
		  flag = 0xb000+len(res)
		  value += struct.pack("<H",flag)+res
	  cgsf.gsf_output_write (child,len(value),value)

	else: # Directory
	  child = cgsf.gsf_outfile_new_child(outfile,name,1)

	  for i in range(model.iter_n_children(parent)):
		piter = model.iter_nth_child(parent,i)
		dump_tree (model, piter, child)

	cgsf.gsf_output_close (child)


def save (page, fname):
	model = page.view.get_model()
	cgsf.gsf_init()
	output = cgsf.gsf_output_stdio_new (fname)
	outfile = cgsf.gsf_outfile_msole_new (output);
	iter1 = model.get_iter_first()
	while None != iter1:
	  dump_tree(model, iter1, outfile)
	  iter1 = model.iter_next(iter1)
	cgsf.gsf_output_close(outfile)
	cgsf.gsf_shutdown()

