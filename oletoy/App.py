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

import sys,struct,os
import tree, gtk
import ole,mf,svm,cdr,clp,cpl
import rx2,fh,fh12,mdb,cpt,cdw,pkzip,wld,vsd,yep
import abr,rtf,otxml,chdraw,vfb,fbx,nki
import qxp
import iwa
import lrf
import pdb
import sbimp
import zmf
import zbr
import lit

class Page:
	def __init__(self):
		self.parent = None
		self.type = ''
		self.fname = ''
		self.pname = ''
		self.items = ''
		self.version = 0
		self.hd = None
		self.hpaned = None
		self.dict = None
		self.dictmod = None
		self.dictview = None
		self.dictwin = None
		self.search = None
		self.wdoc = None  # need to store 'WordDocument' stream
		self.wtable = None # need to store 'xTable' stream of ms-doc
		self.wdata = None # need to store 'Data' stream
		self.model, self.view, self.scrolled = tree.make_view() #None, None, None
		self.win = None # for preview
		self.debug = 0
		self.appdoc = None
		self.backpath = None

	def fload(self,buf="",parent=None):
		self.pname = os.path.split(self.fname)[1]
		if buf == "":
			offset = 0
			f = open(self.fname,"rb")
			buf = f.read()

		if buf[2:8] == "IIXPR3":
			self.type = qxp.open(self, buf, parent)
			return 0

		if buf[0:6] == "\x1aWLF10":
			self.type = vfb.open(self, buf, parent)
			return 0

		if buf[0:6] == "<?xml " or buf[0:14] == "\xff\xfe<\0?\0x\0m\0l\0 \0" or buf[0:14] == "\xfe\xff\0<\0?\0x\0m\0l\0 ":
			self.type = otxml.open(buf, self, parent)
			return 0

		if buf[0:8] == "CPT9FILE":
			self.type = cpt.open(buf, self, parent)
			return 0

		if buf[0:8] == "VjCD0100":
			self.type = chdraw.open(self, buf, parent)
			return 0

		if buf[0:4] == "EVHD":
			self.type = yep.parse(self, buf, parent)
			return 0

		if buf[0:5].lower() == "{\\rtf":
			self.type = rtf.open(buf, self, parent)
			return 0

		if buf[0:8] == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
			self.type = ole.ole_open(buf, self, parent)
			return 0

		if buf[0:18] == "Visio (TM) Drawing":
			self.type = vsd.parse(self, buf, parent)
			return 0

		if buf[0:2] == "\x50\xc3":
			self.type = "CLP"
			clp.open (buf,self, parent)
			return 0

		if buf[0:6] == "VCLMTF":
			self.type = "SVM"
			svm.open (buf,self, parent)
			return 0

		if buf[:4] == "\x12\x90\xa8\x7f":
			nki.open(self,buf,parent)
			return 0

		if buf[0:4] == "RIFF" and buf[8:11].lower() == "cdr":
			self.type = "CDR%x"%(ord(buf[11])-0x30)
			print 'Probably CDR',
			cdr.cdr_open(buf,self, parent)
			print self.version
			return 0

		if buf[0:4] == "RIFF" and buf[8:11] == "CMX":
			self.type = "CMX"
			cdr.cdr_open(buf,self, parent,"cmx")
			return 0

		if buf[0:2] == "WL":
			self.type = "CDR2"
			wld.open (buf,self, parent)
			return 0

		if buf[0:2] == "\xcc\xdc":
			self.type = "CPL"
			cpl.open (buf,self, parent)
			return 0

		if buf[0:4] == "8BGR":
			self.type = "BGR"
			abr.abr_open(buf,self, parent,"bgr")
			return 0

		if buf[4:8] == "8BIM":
			self.type = "ABR"
			abr.abr_open(buf,self, parent,"abr")
			return 0

		if buf[0:4] == "\xd7\xcd\xc6\x9a":
			self.type = "APWMF"
			mf.mf_open(buf,self, parent)
			print "Aldus Placeable WMF"
			return 0

		if buf[0:8] == "\x4c\x00\x52\x00\x46\x00\x00\x00":
			self.type = "LRF"
			lrf.open(buf, self, parent)
			print "LRF"
			return 0

		if buf[0:6] == "\x01\x00\x09\x00\x00\x03":
			self.type = "WMF"
			print "Probably WMF"
			mf.mf_open(buf,self, parent)
			return 0

		if buf[40:44] == "\x20\x45\x4d\x46":
			self.type = "EMF"
			print "Probably EMF"
			mf.mf_open(buf,self, parent)
			return 0

		if buf[0:2] =="KF" and buf[2] != "\x00":
			self.type = "CDW"
			print "Probably CDW"
			cdw.open(buf,self, parent)
			return 0

		if buf[0:4] == "CAT " and buf[0x8:0xc] == "REX2":
			self.type = "REX2"
			print "Probably REX2"
			rx2.open(buf,self, parent)
			return 0
		
		if buf[0:20] == "Kaydara FBX Binary  ":
			self.type = "FBX"
			print "Probably FBX"
			fbx.open(buf,self, parent)
			return 0
		
		if buf[4:19] == "Standard Jet DB" or buf[4:19] == "Standard ACE DB":
			self.type = "MDB"
			print "Probably MDB"
			mdb.parse (buf,self, parent)
			return 0
		
		if buf[0:4] == "\x50\x4b\x03\x04":
			self.type = "PKZIP"
			print "Probably PK-ZIP"
			f.close()
			pkzip.open (self.fname,self, parent)
			return 0

		pdbtype = buf[0x3c:0x44]
                if pdbtype in pdb.pdb_types.keys():
			self.type = "PDB"
			print "Probably Palm e-book"
			pdb.open(buf, self, parent, pdbtype)
			return 0

		if buf[2:10] == 'BOOKDOUG':
			self.type = 'IMP'
			print 'Probably SoftBook e-book'
			sbimp.open(buf, self, parent)
			return 0

		if buf[0:8] == 'ITOLITLS':
			self.type = 'LIT'
			print 'Probably LIT'
			lit.open(buf,self,parent)
			return 0

		fh_off = buf.find('FreeHand')
		if buf[0:3] == 'AGD':
			agd_off = 0
			agd_ver = ord(buf[agd_off+3])
			self.type = "FH"
			print "Probably Freehand"
			fh.fh_open(buf,self)
			return 0
		elif fh_off != -1:
			agd_off = buf.find('AGD')
			if agd_off > fh_off:
				agd_ver = ord(buf[agd_off+3])
				self.type = "FH"
				print "Probably Freehand 9+"
				fh.fh_open(buf,self, parent)
				return 0
		else:
			fh_off = buf.find('FHDocHeader')
			if fh_off != -1:
				if buf[0:2] == "FH":
					self.type = "FH"
					print "Probably Freehand <5"
					fh.fh_open(buf, self, parent, 0)
					return 0
		if buf[0:4] == "FHD2" or buf[0:4] == "acf3":
			self.type = "FH12"
			fh12.fh_open(buf, self, parent, 0)
			return 0
		if buf[8:11] == 'xV4':
			self.type = 'ZMF'
			print 'Probably Zoner Draw 4+'
			zmf.zmf4_open(buf, self, parent)
			return 0

		# NOTE: 0x29a is 666 in decimal .-)
		if buf[0:2] == '\x9a\x02' and buf[2:4] in ['\01\0', '\02\0', '\03\0', '\04\0']:
			self.type = 'ZBR'
			print 'Probably Zebra Metafile'
			zbr.open(buf, self, parent)
			return 0

		size = (ord(buf[1]) | (ord(buf[2]) << 8)) + 4
		if buf[0] == '\0' and (size == len(buf) or (size < len(buf) and buf[4:7] == "\x80\x80\x04")):
			self.type = 'IWA'
			print('Probably Apple iWork file')
			iwa.open(buf, self, parent)
			return 0

		if parent == None:
			iter1 = self.model.append(None, None)
			self.model.set_value(iter1, 0, "File")
			self.model.set_value(iter1, 1, 0)
			self.model.set_value(iter1, 2, len(buf))
			self.model.set_value(iter1, 3, buf)
		return 0

	def show_search(self,carg):
		view = gtk.TreeView(self.search)
		view.set_reorderable(True)
		view.set_enable_tree_lines(True)
		cell1 = gtk.CellRendererText()
		cell1.set_property('family-set',True)
		cell1.set_property('font','monospace 10')
		cell2 = gtk.CellRendererText()
		cell2.set_property('family-set',True)
		cell2.set_property('font','monospace 10')
		column1 = gtk.TreeViewColumn('Type', cell1, text=0)
		column2 = gtk.TreeViewColumn('Value', cell2, text=2)
		column3 = gtk.TreeViewColumn('#', cell2, text=3)
		view.append_column(column3)
		view.append_column(column1)
		view.append_column(column2)
		view.show()
		view.connect("row-activated", self.on_search_row_activated)
		scrolled = gtk.ScrolledWindow()
		scrolled.add(view)
		scrolled.set_size_request(400,400)
		scrolled.show()
		searchwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
		searchwin.set_resizable(True)
		searchwin.set_border_width(0)
		scrolled.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		searchwin.add(scrolled)
		searchwin.set_title("Search: %s"%carg)
		searchwin.show_all()

	def on_dict_row_activated(self, view, path, column):
		self.on_search_row_activated(view, path, column, 0)

	def on_search_row_activated(self, view, path, column, dflag = 1):
		treeSelection = view.get_selection()
		model1, iter1 = treeSelection.get_selected()
		goto = model1.get_value(iter1,0)
		self.view.expand_to_path(goto)
		self.view.set_cursor_on_cell(goto)
		intCol = self.view.get_column(0)
		self.view.row_activated(goto,intCol)

		if dflag:
			addr = model1.get_value(iter1,1)
			doc = self.hd.hv
			try:
				off = model1.get_value(iter1,1)
				length = 1
				if off/16 < doc.offnum or off/16 > doc.offnum+doc.numtl:
					doc.offnum = off/16-2
					if doc.offnum < 0:
						doc.offnum = 0
				doc.hl[0] = (off,length,0.8,1,0.8,1)
				doc.expose(None,None)
			except:
				print "Wrong address"
