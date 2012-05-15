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
from utils import *

cgsf = ctypes.cdll.LoadLibrary('libgsf-1.so')


escapement = {0:"None", 1:"Superscript", 2:"Subscript"}

underline = {0:"None",1:"Single",2:"Double",0x21:"Single accounting",0x22:"Double accounting"}

def fib_base (hd, data):
	off = 0
	add_iter(hd,"wIdent",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter(hd,"nFib",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter(hd,"unused",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter(hd,"lid",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter(hd,"pnNext",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	flags = struct.unpack("<H",data[off:off+2])[0]
	fdict = {0:"fDot",1:"fGlsy",2:"fComplex",3:"fHasPic",
		8:"fEncrypted",9:"fWhichTblStm",10:"fReadOnlyRecommended",11:"fWriteReservation",
		12:"fExtChar",13:"fLoadOverride",14:"fFarEast",15:"fObfuscated"}
	fnames = []
	for i in range(0, 4):
		fnames.append("%s: %d" % (fdict[i], bool(flags&(2**i))))
	fnames.append("cQuickSaves: %d" % (flags >> 4 & (2**4)-1))
	for i in range(8, 16):
		fnames.append("%s: %d" % (fdict[i], bool(flags&(2**i))))
	add_iter(hd,"Flags",", ".join(fnames),off,2,"<H")
	off += 2
	add_iter(hd,"nFibBack",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter(hd,"iKey",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"envr",ord(data[off]),off,1,"B")

def fib_RgW (hd, data):
	off = 0
	add_iter(hd,"csw",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	for i in range(13):
		add_iter(hd,"rsrv%d"%(i+1),struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
		off += 2
	add_iter(hd,"lidFE",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")

def fib_RgLw (hd, data):
	off = 0
	add_iter(hd,"cslw",struct.unpack("<H",data[off:off+2])[0],off,2,"<H")
	off += 2
	add_iter(hd,"cbMac",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"rsrv1",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"rsrv2",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpText",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpFtn",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpHdd",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"rsrv3",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpAtn",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpEdn",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpTxbx",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"ccpHdrTxbx",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	for i in range(11):
		add_iter(hd,"rsrv%d"%(i+4),struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

#Stshf -- StyleSheet
#PlcffndRef -- Footnotes refs
#PlcffndTxt -- Footnotes text
#PlcfandRef -- Dates/Locations of comments
#PlcfandTxt -- Text of comments
#PlcfSed -- PropList location
#PlcPad -- undef, ignore
#PlcfPhe -- ver specific para height info
#SttbfGlsy -- autotext
#PlcfGlsy -- autotext
#PlcfHdd -- header/footer locations
#PlcfBteChpx -- PlcBteChpx
#PlcfBtePapx -- PlcfBtePapx
#PlcfSea -- undef, ignore
#SttbfFfn -- fonts spec
#PlcfFldMom -- field chars location
#PlcfFldHdr -- header field chars location
#PlcfFldFtn -- footer field chars location
#PlcfFldAtn -- comments field chars location
#PlcfFldMcr -- undef, ignore
#SttbfBkmk -- bookmarks name
#PlcfBkf -- standard bookmark
#PlcfBkl -- standard bookmark
#Cmds -- command customizations
#Unused1 -- undef, ignore
#SttbfMcr -- undef, ignore
#PrDrvr -- printer driver info
#PrEnvPort -- print env in portrait mode
#PrEnvLand -- print env in landscape mode
#Wss -- last selection
#Dop -- Dop
#SttbfAssoc -- strings
#Clx -- Clx
#PlcfPgdFtn -- undef, ignore
#AutosaveSource -- undef, ignore
#GrpXstAtnOwners -- comments authors
#SttbfAtnBkmk -- annotation bookmarks
#Unused2 -- undef, ignore
#Unused3 -- undef, ignore
#PlcSpaMom -- shape info
#PlcSpaHdr -- header shape info
#PlcfAtnBkf -- annotation bookmark
#PlcfAtnBkl -- annotation bookmark
#Pms -- print merge
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
		add_iter(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_iter(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
	add_iter(hd,"dwLowDateTime",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	add_iter(hd,"dwHighDateTime",struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
	off += 4
	for i in fclcb97recs2:
		add_iter(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_iter(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

fclcb2krecs = ["PlcfTch","RmdThreading","Mid","SttbRgtplc","MsoEnvelope",
  "PlcfLad","RgDofr","Plcosl","PlcfCookieOld","PgdMotherOld","BkdMotherOld",
  "PgdFtnOld","BkdFtnOld","PgdEdnOld","BkdEdnOld"]

def FcLcb2k (hd,data):
	FcLcb97 (hd,data)
	off = 746
	for i in fclcb2krecs:
		add_iter(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_iter(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
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
		add_iter(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_iter(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
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
		add_iter(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_iter(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

fclcb2k7recs = ["Plcfmthd","SttbfBkmkMoveFrom","PlcfBkfMoveFrom","PlcfBklMoveFrom",
  "SttbfBkmkMoveTo","PlcfBkfMoveTo","PlcfBklMoveTo","Unused1","Unused2",
  "Unused3","SttbfBkmkArto","PlcfBkfArto","PlcfBklArto","ArtoData",
  "Unused4","Unused5","Unused6","OssTheme","ColorSchemeMapping"]

def FcLcb2k7 (hd,data):
	FcLcb2k3 (hd,data)
	off = 1314
	for i in fclcb2k7recs:
		add_iter(hd,"fc%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4
		add_iter(hd,"lcb%s"%i,struct.unpack("<I",data[off:off+4])[0],off,4,"<I")
		off += 4

def fib_RgFcLcbBlob (hd, data):
	off = 0
	cb = struct.unpack("<H",data[off:off+2])[0]
	add_iter(hd,"cbRgFcLcb",cb,off,2,"<H")
	off += 2
	if fclcb2nfib.has_key(cb):
	  fclcb2nfib[cb][1](hd,data)

fclcb2nfib = {0x5d:(0xc1,FcLcb97),0x6c:(0xd9,FcLcb2k),0x88:(0x101,FcLcb2k2),0xa4:(0x10c,FcLcb2k3),0xb7:(0x112,FcLcb2k7)}
recs = {"base":fib_base,"fibRgW":fib_RgW,"fibRgLw":fib_RgLw, "fibRgFcLcbBlob":fib_RgFcLcbBlob}

ptable_unsd = {0:"",7:"",14:"",20:"",25:"",26:"",34:"",35:"",38:"",39:"",45:"",49:"",64:"",65:"",66:"",67:"",68:"",77:"",78:"",79:"",80:"",
  81:"",82:"",86:""}

def parse_data (page, data, dataiter):
	pass

def parse_table (page, data, parent, docdata, docdataiter):
	offset = 0
	fclcb = page.model.get_value(page.wdoc,3)
	for i in range(len(fclcb97recs1)):
		if not ptable_unsd.has_key(i):
		  recoff = struct.unpack("<I",fclcb[2+i*8:6+i*8])[0]
		  reclen = struct.unpack("<I",fclcb[6+i*8:10+i*8])[0]
		  if reclen != 0:
			add_pgiter (page,fclcb97recs1[i],"doc","table",data[recoff:recoff+reclen],parent)


def parse (page, data, parent):
	offset = 0
	page.type = "DOC"
	add_pgiter (page,"Base","doc","base",data[0:0x20],parent)
	offset += 0x20
	csw = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgW","doc","fibRgW",data[offset:offset+2+csw*2],parent)
	offset += 2+csw*2
	cslw = struct.unpack("<H",data[offset:offset+2])[0]
	add_pgiter (page,"fibRgLw","doc","fibRgLw",data[offset:offset+2+cslw*4],parent)
	offset += 2+cslw*4
	cbRgFcLcb = struct.unpack("<H",data[offset:offset+2])[0]
	page.wdoc = add_pgiter (page,"fibRgFcLcbBlob","doc","fibRgFcLcbBlob",data[offset:offset+2+cbRgFcLcb*8],parent)
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

