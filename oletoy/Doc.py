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
import ole,mf,svm,cdr,clp,rx2,fh

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
			
		if buf[0:4] == "CAT " and buf[0x8:0xc] == "REX2":
			self.type = "REX2"
			print "Probably REX2"
			rx2.open(buf,self)
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
		hd = self.hd
# FIXME! copy-pasted from view.py
# check why need double activation to scroll to addr
		hd.version = self.version
		treeSelection = self.view.get_selection()
		model, siter = treeSelection.get_selected()
		ntype = model.get_value(siter,1)
		size = model.get_value(siter,2)
		data = model.get_value(siter,3)
		hd.data = data
		str_addr = ''
		str_hex = ''
		str_asc = ''
		if data != None:
			for line in range(0, len(data), 16):
				str_addr+="%07x: "%line
				end = min(16, len(data) - line)
				for byte in range(0, 15):
					if byte < end:
						str_hex+="%02x " % ord(data[line + byte])
						if ord(data[line + byte]) < 32 or 126<ord(data[line + byte]):
							str_asc +='.'
						else:
							str_asc += data[line + byte]
				if end > 15:			
					str_hex+="%02x" % ord(data[line + 15])
					if ord(data[line + 15]) < 32 or 126<ord(data[line + 15]):
						str_asc += '.'
					else:
						str_asc += data[line + 15]
					str_hex+='\n'
					str_asc+='\n'
					str_addr+='\n'
			if len(str_hex) < 47:
				str_hex += " "*(47-len(str_hex))
	
			buffer_addr = hd.txtdump_addr.get_buffer()
			iter_addr = buffer_addr.get_iter_at_offset(0)
			iter_addr_end = buffer_addr.get_iter_at_offset(buffer_addr.get_char_count())
			buffer_addr.delete(iter_addr, iter_addr_end)
			buffer_addr.insert_with_tags_by_name(iter_addr, str_addr,"monospace")
			buffer_asc = hd.txtdump_asc.get_buffer()
			iter_asc = buffer_asc.get_iter_at_offset(0)
			iter_asc_end = buffer_asc.get_iter_at_offset(buffer_asc.get_char_count())
			buffer_hex = hd.txtdump_hex.get_buffer()
			iter_hex = buffer_hex.get_iter_at_offset(0)
			iter_hex_end = buffer_hex.get_iter_at_offset(buffer_hex.get_char_count())
			buffer_hex.delete(iter_hex, iter_hex_end)
			buffer_hex.insert_with_tags_by_name(iter_hex, str_hex,"monospace")
			buffer_asc.delete(iter_asc, iter_asc_end)
			buffer_asc.insert_with_tags_by_name(iter_asc, str_asc,"monospace")
		try:
			buffer_hex = hd.txtdump_hex.get_buffer()
			vadj = hd.vscroll2.get_vadjustment()
			newval = addr/16*vadj.get_upper()/buffer_hex.get_line_count()
			vadj.set_value(newval)
		except:
			print "Wrong address"
