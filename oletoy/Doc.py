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
import tree, gtk, gobject
import ole,mf,svm,cdr,clp,rx2,fh,mdb,cpt,cdw

class Page:
	def __init__(self):
		self.type = ''
		self.fname = ''
		self.pname = ''
		self.items = ''
		self.version = 0
		self.hd = None
		self.dict = None
		self.dictmod = None
		self.dictview = None
		self.search = None
		self.wdoc = None  # need to store 'WordDocument' stream
		self.model, self.view, self.scrolled = tree.make_view() #None, None, None

	def fload(self):
		pos = self.fname.rfind('/')
		if pos !=-1:
			self.pname = self.fname[pos+1:]
		else:
			self.pname = self.fname
		offset = 0
		f = open(self.fname)
		buf = f.read()

		if buf[0:8] == "CPT9FILE":
			self.type = cpt.open(buf, self)
			return 0

		if buf[0:8] == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
			self.type = ole.open(buf, self)
			return 0

		if buf[0:2] == "\x50\xc3":
			self.type = "CLP"
			clp.open (buf,self)
			return 0

		if buf[0:6] == "VCLMTF":
			self.type = "SVM"
			svm.open (buf,self)
			return 0

		if buf[0:4] == "RIFF" and buf[8:11] == "CDR":
			self.type = "CDR%x"%(ord(buf[11])-0x30)
			print 'Probably CDR %x'%(ord(buf[11])-0x30)
			cdr.cdr_open(buf,self)
			return 0

		if buf[0:4] == "\xd7\xcd\xc6\x9a":
			self.type = "APWMF"
			mf.mf_open(buf,self)
			print "Aldus Placeable WMF"
			return 0

		if buf[0:6] == "\x01\x00\x09\x00\x00\x03":
			self.type = "WMF"
			print "Probably WMF"
			mf.mf_open(buf,self)
			return 0

		if buf[40:44] == "\x20\x45\x4d\x46":
			self.type = "EMF"
			print "Probably EMF"
			mf.mf_open(buf,self)
			return 0

		if buf[0:2] =="KF" and buf[2] != "\x00":
			self.type = "CDW"
			print "Probably CDW"
			cdw.open(buf,self)
			return 0

		if buf[0:4] == "CAT " and buf[0x8:0xc] == "REX2":
			self.type = "REX2"
			print "Probably REX2"
			rx2.open(buf,self)
			return 0
		
		if buf[4:19] == "Standard Jet DB" or buf[4:19] == "Standard ACE DB":
			self.type = "MDB"
			print "Probably MDB"
			mdb.parse (buf,self)
			return 0
		
		fh_off = buf.find('FreeHand')
		if buf[0:3] == 'AGD':
			agd_off = 0
			agd_ver = ord(buf[agd_off+3])
			self.type = "FH"
			print "Probably Freehand 8"
			try:
				fh.fh_open(buf,self)
				return 0
			except:
				print 'Failed to parse as FH8'
		elif fh_off != -1:
			agd_off = buf.find('AGD')
			if agd_off > fh_off:
				agd_ver = ord(buf[agd_off+3])
				self.type = "FH"
				print "Probably Freehand 9+"
				try:
					fh.fh_open(buf,self)
					return 0
				except:
					print 'Failed to parse as FH9+'

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

	def on_search_row_activated(self, view, path, column):
		treeSelection = view.get_selection()
		model1, iter1 = treeSelection.get_selected()
		goto = model1.get_value(iter1,0)
		addr = model1.get_value(iter1,1)
		self.view.expand_to_path(goto)
		self.view.set_cursor_on_cell(goto)
		intCol = self.view.get_column(0)
		self.view.row_activated(goto,intCol)

		hd = self.hd
		try:
			buffer_hex = hd.txtdump_hex.get_buffer()
			vadj = hd.vscroll2.get_vadjustment()
			newval = addr/16*vadj.get_upper()/buffer_hex.get_line_count()
			vadj.set_value(newval)
		except:
			print "Wrong address"
