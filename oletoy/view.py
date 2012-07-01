#!/usr/bin/env python
# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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


import sys,struct
import gobject
import gtk, pango
import tree
import hexdump
import Doc, cmd
import escher,quill
import vsd, vsdchunks,vsdstream4
import xls, vba, ole, doc, mdb, pub
import emfparse,svm,mf,wmfparse,emfplus,rx2,fh,fhparse
import cdr,cmx,wld,ppp
from utils import *

version = "0.7.2"

ui_info = \
'''<ui>
	<menubar name='MenuBar'>
	<menu action='FileMenu'>
		<menuitem action='New'/>
		<menuitem action='Open'/>
		<menuitem action='Reload'/>
		<menuitem action='Options'/>
		<menuitem action='Save'/>
		<menuitem action='Close'/>
		<separator/>
		<menuitem action='Quit'/>
	</menu>
	<menu action='EditMenu'>
		<menuitem action='Insert'/>
		<menuitem action='More'/>
		<menuitem action='Less'/>
		<separator/>
		<menuitem action='Dump'/>
	</menu>
	<menu action='ViewMenu'>
		<menuitem action='Dict'/>
	</menu>
	<menu action='HelpMenu'>
		<menuitem action='Manual'/>
		<menuitem action='About'/>
	</menu>
	</menubar>
</ui>'''

def register_stock_icons():
	''' This function registers our custom toolbar icons, so they  can be themed. '''
	# Add our custom icon factory to the list of defaults
	factory = gtk.IconFactory()
	factory.add_default()

class ApplicationMainWindow(gtk.Window):
	def __init__(self, parent=None):
		register_stock_icons()
		# Create the toplevel window
		gtk.Window.__init__(self)
		try:
			self.set_screen(parent.get_screen())
		except AttributeError:
			self.connect('destroy', lambda *w: gtk.main_quit())

		self.set_title("OLE toy")
		self.set_default_size(400, 350)

		merge = gtk.UIManager()
		self.set_data("ui-manager", merge)
		merge.insert_action_group(self.__create_action_group(), 0)
		self.add_accel_group(merge.get_accel_group())

		try:
			mergeid = merge.add_ui_from_string(ui_info)
		except gobject.GError, msg:
			print "building menus failed: %s" % msg
		bar = merge.get_widget("/MenuBar")
		bar.show()

		table = gtk.Table(1, 3, False)
		self.add(table)

		table.attach(bar,
			# X direction #		  # Y direction
			0, 1,					  0, 1,
			gtk.EXPAND | gtk.FILL,	 0,
			0,						 0);
		
		self.notebook =gtk.Notebook()
		self.notebook.set_tab_pos(gtk.POS_BOTTOM)
		self.notebook.set_scrollable(True)
		table.attach(self.notebook,
			# X direction #		  # Y direction
			0, 1,					  1, 2,
			gtk.EXPAND | gtk.FILL,	 gtk.EXPAND | gtk.FILL,
			0,						 0);

		# Create statusbar
		self.statusbar = gtk.HBox()
		self.entry = gtk.Entry()
		self.statusbar.pack_start(self.entry, False,False,2)
		self.entry.connect ("activate",self.on_entry_activate)
		self.entry.connect ("key-press-event", self.on_entry_keypressed)
		self.label = gtk.Label()
		self.label.set_use_markup(True)
		self.statusbar.pack_start(self.label, True,True,2)
		
		table.attach(self.statusbar,
			# X direction		   Y direction
			0, 1,				   2, 3,
			gtk.EXPAND | gtk.FILL,  0,
			0,					  0)
		self.show_all()
		self.das = {}
		self.fname = ''
		self.selection = None
		self.cmdhistory = []
		self.curcmd = -1

		# configuration options
		self.options_le = 1
		self.options_be = 0
		self.options_txt = 1
		self.options_div = 1
		self.options_enc = "utf-16"
		self.options_win = None
		self.statbuffer = ""


		if len(sys.argv) > 1:
			for i in range(len(sys.argv)-1):
				self.fname = sys.argv[i+1]
				self.activate_open()

	def __create_action_group(self):
		# GtkActionEntry
		entries = (
			( "FileMenu", None, "_File" ),			   # name, stock id, label
			( "EditMenu", None, "_Edit" ),			   # name, stock id, label
			( "ViewMenu", None, "_View" ),			   # name, stock id, label
			( "HelpMenu", None, "_Help" ),			   # name, stock id, label
			( "Insert", gtk.STOCK_ADD,					# name, stock id
				"_Insert Record","<control>I",					# label, accelerator
				"Insert MF Record after the current one",							 # tooltip
				self.activate_add),
			( "More", gtk.STOCK_ADD,					# name, stock id
				"_More bytes","<control>M",					  # label, accelerator
				"Add more bytes at the end of the current record",							 # tooltip
				self.activate_more),
			( "Less", gtk.STOCK_ADD,					# name, stock id
				"_Less bytes","<control>L",					  # label, accelerator
				"Remove some bytes at the end of the current record",							 # tooltip
				self.activate_less),
			( "Dump", gtk.STOCK_SAVE,						# name, stock id
				"D_ump","<control>U",					  # label, accelerator
				"Dump record to file",							 # tooltip
				self.activate_dump),
			( "New", gtk.STOCK_NEW,					# name, stock id
				"_New","<control>N",					  # label, accelerator
				"Create file",							 # tooltip
				self.activate_new),
			( "Open", gtk.STOCK_OPEN,					# name, stock id
				"_Open","<control>O",					  # label, accelerator
				"Open a file",							 # tooltip
				self.activate_open),
			( "Reload", gtk.STOCK_OPEN,					# name, stock id
				"_Reload","<control>R",					  # label, accelerator
				"Reload a file",							 # tooltip
				self.activate_reload),
			( "Dict", gtk.STOCK_INDEX,					# name, stock id
				"_Dictionary","<control>D",					  # label, accelerator
				"Show type dependant dictionary",							 # tooltip
				self.activate_dict),
			( "Options", None,                    # name, stock id
				"Op_tions","<control>T",                      # label, accelerator
				"Configuration options",                             # tooltip
				self.activate_options),
			( "Save", gtk.STOCK_SAVE,                    # name, stock id
				"_Save","<control>S",                      # label, accelerator
				"Save the file",                             # tooltip
				self.activate_save),
			( "Close", gtk.STOCK_CLOSE,                    # name, stock id
				"Close","<control>Z",                      # label, accelerator
				"Close the file",                             # tooltip
				self.activate_close),
			( "Quit", gtk.STOCK_QUIT,					# name, stock id
				"_Quit", "<control>Q",					 # label, accelerator
				"Quit",									# tooltip
				self.activate_quit ),

			( "About", None,							 # name, stock id
				"About", "",					# label, accelerator
				"About OleToy",								   # tooltip
				self.activate_about ),
			( "Manual", gtk.STOCK_HELP,							 # name, stock id
				"Manual", "<control>H",					# label, accelerator
				"Manual for OleToy",								   # tooltip
				self.activate_manual ),
		);

		# Create the menubar and toolbar
		action_group = gtk.ActionGroup("AppWindowActions")
		action_group.add_actions(entries)
		return action_group

	def draw_manual (self, widget, event):
		mytxt = \
"<b>Main tree:</b>\n\
	Up/Down - walk the tree.\n\
	Right/Left - expand/collapse branch.\n\
	Right click - copy tree path to entry line.\n\
	Delete - remove leaf from the tree\n\
	Type text for quick search (Up/Down for next/prev result).\n\n\
<b>Entry line:</b>\n\
	Up/Down - scroll 'command history'\n\
	gtk tree path - scroll/expand tree\n\
	#addr - scroll hexdump to addr\n\
	#addr+shift, #addr-shift - calculate new addr and scroll hexdump\n\
	$deflate{@addr} - try to decompress starting from addr (or 0)\n\
	$dump{@addr} - save record starting from addr (or 0)\n\
	$esc{@addr} - try to parse record as Escher starting from addr (or 0)\n\
	$ole{@addr} - try to parse record as OLE starting from addr (or 0)\n\
	$cmx{@addr} - try to parse record as CMX starting from addr (or 0)\n\
	$icc{@addr} - try to parse record as ICC starting from addr (or 0)\n\
	$pix{@addr} - try to parse record as gdkpixbuf image starting from addr (or 0)\n\
	$xls@RC - search XLS file for record related to cell RC\n\n\
	?aSTRING - search for ASCII string\n\
	?uSTRING - search for Unicode string\n\
	?x0123 - search for hex value\n\
	?rREC{:[aux]STRING} - search for record with REC in the name and STRING in data.\n\
	?rloda#{arg} - search for args in 'loda' records in CDR\n\n\
	={val} - search for differences equal to 'val' between current and next pages\n\
		if value skipped, then compares selected iter on pages for any differences\n\
		if no iter selected, then compares whole pages (be patient)\n\n\
<b>Hexdump selection:</b>\n\
	^E flips edit mode, grey/green/red circle shows status:\n\
		grey - editing switched off,\n\
		green - editing switched on,\n\
		red - data was modified.\n\
	Switch-on edit/modify/switch-off edit will update data in immediate record.\n\
	Changes are not propogate up the tree.\n\n\
	Select 2,3,4 or 8 bytes - check tooltip in the statusbar.\n\
	^T opens \"Options\" dialog to adjust conversion of selected bytes.\n\n\
	For PUB 4 bytes would be additionaly converted to points, cm and inches.\n\
	For CDR if 4 bytes match with ID from dictionary, tooltip would be yellow.\n\
	For CDR select outl/fild ID and press arrow right to scroll to it."

		pl = widget.create_pango_layout("")
		pl.set_markup(mytxt)
		gc = widget.window.new_gc()
		w,h = pl.get_size()
		widget.set_size_request(w/1000, h/1000)
		widget.window.draw_layout(gc, 0, 0, pl)


	def activate_manual(self, action):
		w = gtk.Window()
		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(620,400)
		da = gtk.DrawingArea()
		da.connect('expose_event', self.draw_manual)
		w.set_title("OLE Toy Manual")
		w.set_default_size(520, 300)
		s.add_with_viewport(da)
		w.add(s)
		w.show_all()

	def on_enc_entry_activate (self,entry):
		enc = entry.get_text()
		try:
			unicode("test",enc)
			self.options_enc = enc
			if self.statbuffer != "":
				self.calc_status(self.statbuffer,len(self.statbuffer))
		except:
			entry.set_text(self.options_enc)
		print "Enc set to",self.options_enc

	def on_div_entry_activate (self,entry):
		n = entry.get_text()
		try:
			self.options_div = float(n)
			if self.statbuffer != "":
				self.calc_status(self.statbuffer,len(self.statbuffer))
		except:
			entry.set_text("%.2f"%self.options_div)
		print "Div set to",self.options_div

	def on_option_toggled (self,button):
		lt = button.get_label()
		if lt == "LE":
			self.options_le = abs(self.options_le-1)
		if lt == "BE":
			self.options_be = abs(self.options_be-1)
		if lt == "Txt":
			self.options_txt = abs(self.options_txt-1)
		if self.statbuffer != "":
			self.calc_status(self.statbuffer,len(self.statbuffer))

	def del_optwin (self, action):
		self.options_win = None

	def activate_options (self, action):
		if self.options_win != None:
			self.options_win.show_all()
			self.options_win.present()
		else:
			# le, be, txt, div, enc
			vbox = gtk.VBox()
			le_chkb = gtk.CheckButton("LE")
			be_chkb = gtk.CheckButton("BE")
			txt_chkb = gtk.CheckButton("Txt")
			
			if self.options_le:
				le_chkb.set_active(True)
			if self.options_be:
				be_chkb.set_active(True)
			if self.options_txt:
				txt_chkb.set_active(True)
	
			le_chkb.connect("toggled",self.on_option_toggled)
			be_chkb.connect("toggled",self.on_option_toggled)
			txt_chkb.connect("toggled",self.on_option_toggled)
	
			hbox0 = gtk.HBox()
			hbox0.pack_start(le_chkb)
			hbox0.pack_start(be_chkb)
			hbox0.pack_start(txt_chkb)
			
			hbox1 = gtk.HBox()
			div_lbl = gtk.Label("Div")
			div_entry = gtk.Entry()
			div_entry.connect("activate",self.on_div_entry_activate)
			div_entry.set_text("%.2f"%self.options_div)
			hbox1.pack_start(div_lbl)
			hbox1.pack_start(div_entry)
	
			hbox2 = gtk.HBox()
			enc_lbl = gtk.Label("Enc")
			enc_entry = gtk.Entry()
			enc_entry.connect("activate",self.on_enc_entry_activate)
			hbox2.pack_start(enc_lbl)
			hbox2.pack_start(enc_entry)
			enc_entry.set_text(self.options_enc)

			vbox.pack_start(hbox0)
			vbox.pack_start(hbox1)
			vbox.pack_start(hbox2)

			optwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
			optwin.set_resizable(False)
			optwin.set_border_width(0)
			optwin.add(vbox)
			optwin.set_title("Hexview Options")
			optwin.connect ("destroy", self.del_optwin)
			optwin.show_all()
			self.options_win = optwin


	def del_dictwin (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			self.das[pn].dictwin = None

	def activate_dict (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			if self.das[pn].type[0:3] == "CDR":
				if self.das[pn].dictwin != None:
					self.das[pn].dictwin.show_all()
					self.das[pn].dictwin.present()
				else:
					view = gtk.TreeView(self.das[pn].dictmod)
					view.connect("row-activated", self.das[pn].on_dict_row_activated)
					view.set_reorderable(True)
					view.set_enable_tree_lines(True)
					cell1 = gtk.CellRendererText()
					cell1.set_property('family-set',True)
					cell1.set_property('font','monospace 10')
					cell2 = gtk.CellRendererText()
					cell2.set_property('family-set',True)
					cell2.set_property('font','monospace 10')
					column1 = gtk.TreeViewColumn('Type', cell1, text=1)
					column2 = gtk.TreeViewColumn('Value', cell2, text=2)
					column3 = gtk.TreeViewColumn('Value', cell2, text=3)
					view.append_column(column1)
					view.append_column(column2)
					view.append_column(column3)
					view.show()
					scrolled = gtk.ScrolledWindow()
					scrolled.add(view)
					scrolled.set_size_request(400,400)
					scrolled.show()
					dictwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
					dictwin.set_resizable(True)
					dictwin.set_border_width(0)
					scrolled.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
					dictwin.add(scrolled)
					dictwin.set_title("CDR Dictionary")
					dictwin.connect ("destroy", self.del_dictwin)
					dictwin.show_all()
					self.das[pn].dictwin = dictwin
			elif self.das[pn].type == "FH" and self.das[pn].version < 9:
				view = gtk.TreeView(self.das[pn].dictmod)
				view.set_reorderable(True)
				view.set_enable_tree_lines(True)
				cell0 = gtk.CellRendererText()
				cell0.set_property('family-set',True)
				cell0.set_property('font','monospace 10')
				cell1 = gtk.CellRendererText()
				cell1.set_property('family-set',True)
				cell1.set_property('font','monospace 10')
				cell2 = gtk.CellRendererText()
				cell2.set_property('family-set',True)
				cell2.set_property('font','monospace 10')
				column0 = gtk.TreeViewColumn('Key', cell1, text=0)
				column1 = gtk.TreeViewColumn('Value', cell1, text=1)
				column2 = gtk.TreeViewColumn('???', cell2, text=2)
				view.append_column(column0)
				view.append_column(column1)
				view.append_column(column2)
				view.show()
				scrolled = gtk.ScrolledWindow()
				scrolled.add(view)
				scrolled.set_size_request(400,400)
				scrolled.show()
				dictwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
				dictwin.set_resizable(True)
				dictwin.set_border_width(0)
				scrolled.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
				dictwin.add(scrolled)
				dictwin.set_title("FH Dictionary")
				dictwin.show_all()

	def activate_add (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			if self.das[pn].type == "EMF":
				dictmod, dictview = mf.emf_gentree()
			elif self.das[pn].type == "APWMF" or self.das[pn].type == "WMF":
				dictmod, dictview = mf.wmf_gentree()
			elif self.das[pn].type[:3] == "XLS":
				dictmod, dictview = xls.gentree()
			else:
				return
			dictview.connect("row-activated", self.on_dict_row_activated)
			dictwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
			dictwin.set_resizable(True)
			dictwin.set_default_size(650, 700)
			dictwin.set_border_width(0)
			dwviewscroll = gtk.ScrolledWindow()
			dwviewscroll.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
			dwviewscroll.add(dictview)
			dictwin.add(dwviewscroll)
			dictwin.set_title("Insert record: "+self.das[pn].pname)
			dictwin.show_all()
		return

	def activate_more (self, action):
		pn = self.notebook.get_current_page()
		treeSelection = self.das[pn].view.get_selection()
		model, iter1 = treeSelection.get_selected()
		type = model.get_value(iter1,1)[0]
		print 'Type',type
		value = model.get_value(iter1,3)
		if type == "emf":
			size = model.get_value(iter1,2)+4
			model.set_value(iter1,3,value[0:4]+struct.pack("<I",size)+value[8:]+'\x00'*4)
		elif type == "wmf":
			size = model.get_value(iter1,2)+2
			model.set_value(iter1,3,struct.pack("<I",len(value)/2+1)+value[4:]+'\x00'*2)
		elif type == "xls":
			size = model.get_value(iter1,2)+1
			model.set_value(iter1,3,value[:2]+struct.pack("<H",size)+value[4:3+size]+'\x00')
		else:
			return
		model.set_value(iter1,2,size)

	def activate_less (self, action):
		pn = self.notebook.get_current_page()
		treeSelection = self.das[pn].view.get_selection()
		model, iter1 = treeSelection.get_selected()
		type = model.get_value(iter1,1)[0]
		size = model.get_value(iter1,2)
		value = model.get_value(iter1,3)
		if type == "emf" and size > 11:
			model.set_value(iter1,2,size-4)
			model.set_value(iter1,3,value[0:4]+struct.pack("<I",size-4)+value[8:size-4])
		elif type == "wmf" and size > 7:
			model.set_value(iter1,2,size-2)
			model.set_value(iter1,3,struct.pack("<I",len(value)/2-1)+value[4:size-2])
		elif type == "xls" and size > 0:
			model.set_value(iter1,2,size-1)
			model.set_value(iter1,3,value[:2]+struct.pack("<H",size-1)+value[4:3+size])

	def activate_dump (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			treeSelection = self.das[pn].view.get_selection()
			model, iter1 = treeSelection.get_selected()
			data = model.get_value(iter1,3)
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				nlen = model.get_value(iter1,2)
				value = model.get_value(iter1,3)
				if nlen != None:
					f = open(fname,'w')
					f.write(value)
					f.close()
				else:
					print "Nothing to save"


	def on_dict_row_activated(self, view, path, column):
		pn = self.notebook.get_current_page()
		model = self.das[pn].view.get_model()
		dictmodel = view.get_model()
		treeSelection = self.das[pn].view.get_selection()
		model2, iter2 = treeSelection.get_selected()
		iter = dictmodel.get_iter(path)
		type = dictmodel.get_value(iter,1)
		if self.das[pn].type[:3] == "XLS":
			iter1 = model.insert_after(None,iter2)
			model.set_value(iter1,0,dictmodel.get_value(iter,0))
			model.set_value(iter1,1,("xls",type))
			model.set_value(iter1,2,0)
			model.set_value(iter1,3,struct.pack("<H",type)+"\x00"*2)
			model.set_value(iter1,6,model.get_string_from_iter(iter1))
			model.set_value(iter1,7,"0x%02x"%type)
			self.das[pn].view.set_cursor_on_cell(model.get_string_from_iter(iter1))

		elif self.das[pn].type == "EMF":
			if type != -1:
				size = int(dictmodel.get_value(iter,2))
				if iter2:
					if model.get_value(iter2,1)[1] == 0x46:
						if type > 0x4000:
							cursize = model2.get_value(iter2,2)
							curval = model2.get_value(iter2,3)
							addval = dictmodel.get_value(iter,3)
							model2.set_value(iter2,2,size+len(addval))
							model2.set_value(iter2,3,curval+addval)
							#clear and parse GDIComment again
							mf.parse_gdiplus(addval,-16,model2,iter2)
					else:
						iter1 = model.insert_after(None,iter2)
				else:
					iter1 = model.append(None,None)
				if model.get_value(iter2,1)[1] != 0x46:
					rname = mf.emr_ids[type]
					model.set_value(iter1,0,rname)
					model.set_value(iter1,1,("emf",type))
					model.set_value(iter1,2,size)
				# check dict rec type, if EMF+ -- wrap it into GDI comment
					model.set_value(iter1,3,struct.pack("<I",type)+struct.pack("<I",size)+"\x00"*(size-8))
					model.set_value(iter1,6,model.get_string_from_iter(iter1))
					self.das[pn].view.set_cursor_on_cell(model.get_string_from_iter(iter1))
					print "Insert:",rname,size

		elif self.das[pn].type == "APWMF" or self.das[pn].type == "WMF":
			if type != -1:
				size = int(dictmodel.get_value(iter,2))
				if iter2:
					iter1 = model.insert_after(None,iter2)
				else:
					iter1 = model.append(None,None)

				rname = mf.wmr_ids[type]
				model.set_value(iter1,0,rname)
				model.set_value(iter1,1,("wmf",type))
				model.set_value(iter1,2,size)
				val = dictmodel.get_value(iter,3)
				if val != "":
					model.set_value(iter1,3,val)
				else:
					model.set_value(iter1,3,struct.pack("<I",size/2)+struct.pack("<H",type)+"\x00"*(size-6))
				model.set_value(iter1,6,model.get_string_from_iter(iter1))
				self.das[pn].view.set_cursor_on_cell(model.get_string_from_iter(iter1))
				print "Insert:",rname,size

	def activate_save (self, action):
		pn = self.notebook.get_current_page()
		ftype = self.das[pn].type
		print ftype
		if  ftype == "WMF" or ftype  == "APWMF" or ftype  == "EMF" or ftype == "SVM":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				mf.mf_save(self.das[pn],fname,ftype)
		elif ftype == "cfb":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				ole.save(self.das[pn],fname)
		elif ftype == "vsd":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				vsd.save(self.das[pn],fname)
		elif ftype == "pub":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				pub.save(self.das[pn],fname)
		elif ftype[0:3] == "XLS":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				xls.save(self.das[pn],fname)
		elif ftype == "doc":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				doc.save(self.das[pn],fname)
		elif ftype == "FH":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				fh.fh_save(self.das[pn],fname)
		elif ftype[0:3] == "CDR":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				cdr.save(self.das[pn],fname)
		else:
			self.active_dump(self,action)

	def activate_about(self, action):
		dialog = gtk.AboutDialog()
		dialog.set_name("OLE toy v"+version)
		dialog.set_copyright("\302\251 Copyright 2010-2012 V.F.")
		dialog.set_website("http://www.gnome.ru/")
		## Close dialog on user response
		dialog.connect ("response", lambda d, r: d.destroy())
		dialog.show()

	def activate_quit(self, action):
		 gtk.main_quit()
		 return
 
	def update_statusbar(self, buffer):
		try:
			self.label.set_markup("%s"%buffer)
		except:
			pass

	def on_entry_activate (self,action):
		goto = self.entry.get_text()
		if len(goto) > 0:
			if self.curcmd == -1 or self.cmdhistory[self.curcmd] != goto:
				self.cmdhistory.append(goto)
				self.curcmd = -1
			pn = self.notebook.get_current_page()
			col = self.das[pn].view.get_column(0)
			if goto[0] == "#":
				pos = goto.find("+")
				try:
					if pos != -1:
						addr1 = int(goto[1:pos],16)
						addr2 = int(goto[pos+1:],16)
						addr = addr1+addr2
					else:
						pos = goto.find("-")
						if pos != -1:
							addr1 = int(goto[1:pos],16)
							addr2 = int(goto[pos+1:],16)
							addr = addr1-addr2
						else:
							addr = int(goto[1:], 16)
					self.entry.set_text("#%02x"%addr)
					hd = self.das[pn].hd
					buffer_hex = hd.txtdump_hex.get_buffer()
					vadj = hd.vscroll2.get_vadjustment()
					newval = addr/16*vadj.get_upper()/buffer_hex.get_line_count()
					vadj.set_value(newval)
				except:
					self.update_statusbar("<span foreground='#ff0000'>Wrong address</span>")
			elif goto[0] == "$" or goto[0] == "?":
				cmd.parse (goto,self.entry,self.das[pn])
			elif goto[0] == "=":
					cmd.compare (goto,self.entry,self.das[pn],self.das[pn+1])

			else:
				try:
					self.das[pn].view.expand_to_path(goto)
					self.das[pn].view.set_cursor_on_cell(goto)
				except:
					self.update_statusbar("No such path")

	def on_entry_keypressed (self, view, event):
		if len(self.cmdhistory) > 0:
			if event.keyval == 65362:
				if self.curcmd == -1:
					if len(self.cmdhistory) > 1:
						self.curcmd = len(self.cmdhistory) - 2
					else:
						self.curcmd = 0
				elif self.curcmd > 0:
					self.curcmd -= 1
				self.entry.set_text(self.cmdhistory[self.curcmd])
				return True
			elif event.keyval == 65364:
				if self.curcmd == -1:
					self.curcmd = len(self.cmdhistory) - 1
				elif self.curcmd < len(self.cmdhistory) - 1:
					self.curcmd += 1
				self.entry.set_text(self.cmdhistory[self.curcmd])
				return True

	def activate_close(self, action):
		pn = self.notebook.get_current_page()
		if pn == -1:
			gtk.main_quit()
		else:
			del self.das[pn]
			self.notebook.remove_page(pn)
			if pn < len(self.das):  ## not the last page
				for i in range(pn,len(self.das)):
					self.das[i] = self.das[i+1]
				del self.das[len(self.das)-1]
		return

	def on_row_keypressed (self, view, event):
		treeSelection = view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1:
			intPath = model.get_path(iter1)
			if event.keyval == 65535:
				model.remove(iter1)
				if model.get_iter_first():
					if intPath >= 0:
						view.set_cursor(intPath)
						view.grab_focus()
			elif event.keyval == 65363 and model.iter_n_children(iter1)>0:
				if not view.row_expanded(intPath):
					view.expand_row(intPath,False)
					view.columns_autosize()
					return 1
				view.columns_autosize()
			elif event.keyval == 65361 and model.iter_n_children(iter1)>0:
				view.collapse_row(intPath)
				view.columns_autosize()
			else:
				if event.keyval == 99 and event.state == gtk.gdk.CONTROL_MASK:
					self.selection = (model.get_value(iter1,0),model.get_value(iter1,1),model.get_value(iter1,2),model.get_value(iter1,3))
				if event.keyval == 118 and event.state == gtk.gdk.CONTROL_MASK and self.selection != None:
					niter = model.insert_after (None, iter1)
					model.set_value (niter, 0, self.selection[0])
					model.set_value (niter, 1, self.selection[1])
					model.set_value (niter, 2, self.selection[2])
					model.set_value (niter, 3, self.selection[3])

	def on_row_keyreleased (self, view, event):
		treeSelection = view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1:
			intPath = model.get_path(iter1)
			val = model.get_value(iter1,8)
			self.on_row_activated(view, intPath, 0)
			if event.type  == gtk.gdk.BUTTON_RELEASE and event.button == 3:
				self.entry.set_text(model.get_string_from_iter(iter1))
			elif event.type  == gtk.gdk.BUTTON_RELEASE and event.button == 2:
				if val[0] == "path" and val[1] != None:
					pn = self.notebook.get_current_page()
					dm = self.das[pn].dictmod
					print "Go to iter:",val[1]
					try:
						self.das[pn].view.expand_to_path(val[1])
						self.das[pn].view.set_cursor_on_cell(val[1])
					except:
						print "No such path"
			elif event.type  == gtk.gdk.KEY_RELEASE and event.keyval == 65363:
				pn = self.notebook.get_current_page()
				ha = self.das[pn].scrolled.get_hadjustment()
				ha.set_value(0)

	def on_hdrow_keyreleased (self, view, event):
		treeSelection = view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1:
			if event.type == gtk.gdk.KEY_RELEASE and event.keyval == 65363:
				val = model.get_value(iter1,7)
				if val != None:
					if val[0] == "cdr goto":
						pn = self.notebook.get_current_page()
						dm = self.das[pn].dictmod
						print "Go to:",val[1]
						for i in range(dm.iter_n_children(None)):
							ci = dm.iter_nth_child(None,i)
							v2 = dm.get_value(ci,2)
							if v2 == val[1]:
								goto = dm.get_value(ci,0)
								try:
									self.das[pn].view.expand_to_path(goto)
									self.das[pn].view.set_cursor_on_cell(goto)
								except:
									print "No such path"
				elif model.iter_n_children(iter1)>0:
					intPath = model.get_path(iter1)
					view.expand_row(intPath,False)
			elif event.type == gtk.gdk.KEY_RELEASE and event.keyval == 65361 and model.iter_n_children(iter1)>0:
				intPath = model.get_path(iter1)
				view.collapse_row(intPath)
			else:
				intPath = model.get_path(iter1)
				self.on_hdrow_activated(view, intPath, 0)
				if event.type  == gtk.gdk.BUTTON_RELEASE and event.button == 3:
					val = model.get_value(iter1,1)
					self.entry.set_text("#%s"%val)

	def on_hdrow_activated(self, view, path, column):
		pn = self.notebook.get_current_page()
		model = self.das[pn].hd.hdview.get_model()
		hd = self.das[pn].hd
		iter1 = model.get_iter(path)
		offset = model.get_value(iter1,2)
		size = model.get_value(iter1,3)
		offset2 = model.get_value(iter1,5)
		size2 = model.get_value(iter1,6)
		hd.hv.hl[0] = offset,size,1,1,0,0.9
		if size2 > 0:
			hd.hv.hl[1] = offset2,size2,1,0,1,0.9
		elif hd.hv.hl.has_key(1):
			del hd.hv.hl[1]

		hd.hv.offset = offset

		lnum = offset/16
		hd.hv.curr = lnum
		hd.hv.curc = offset - lnum*16

		if hd.hv.offnum > lnum or lnum > hd.hv.offnum + hd.hv.numtl:
			hd.hv.offnum = lnum-2
			if hd.hv.offnum < 0:
				hd.hv.offnum = 0

		hd.hv.expose(None,None)


	def calc_status(self,buf,dlen):
		pn = self.notebook.get_current_page()
		ftype = self.das[pn].type
		self.statbuffer = buf
		txt = ""
		txt2 = ""
		if dlen == 2:
			if self.options_le == 1:
				txt = "LE: %s\t"%((struct.unpack("<h",buf)[0])/self.options_div)
			if self.options_be == 1:
				txt += "BE: %s"%((struct.unpack(">h",buf)[0])/self.options_div)
		if dlen == 4:
			if ftype == "pub":
				v = struct.unpack("<i",buf)[0]
				txt = "LE: %s\t(pt/cm/in) %s/%s/%s"%(struct.unpack("<i",buf)[0],round(v/12700.,2),round(v/360000.,3),round(v/914400.,4))
			elif ftype == "FH":
				v1 = struct.unpack(">H",buf[0:2])[0]
				v2 = struct.unpack(">H",buf[2:4])[0]
				txt = "BE: %s\tX: %.4f\tY: %.4f"%(struct.unpack(">i",buf)[0],v1-1692+v2/65536.,v1-1584+v2/65536.)
			else:
				if self.options_le == 1:
					txt = "LE: %s"%((struct.unpack("<i",buf)[0])/self.options_div)
					txt += "\tLEF: %s\t"%((struct.unpack("<f",buf)[0])/self.options_div)
				if self.options_be == 1:
					txt += "BE: %s\t"%((struct.unpack(">i",buf)[0])/self.options_div)
					txt += "BEF: %s"%((struct.unpack(">f",buf)[0])/self.options_div)

				if ftype[0:3] == "CDR":
					c2 = ord(buf[0])/255.
					m2 = ord(buf[1])/255.
					y2 = ord(buf[2])/255.
					k2 = ord(buf[3])/255.
					c22 = (c2 * (1 - k2) + k2)
					m22 = (m2 * (1 - k2) + k2)
					y22 = (y2 * (1 - k2) + k2)
					c1 = ord(buf[0])/100.
					m1 = ord(buf[1])/100.
					y1 = ord(buf[2])/100.
					k1 = ord(buf[3])/100.
					if c1 <= 1 and m1 <= 1 and y1 <= 1 and k1 <= 1:
						c = (c1 * (1 - k1) + k1)
						m = (m1 * (1 - k1) + k1)
						y = (y1 * (1 - k1) + k1)
						r1 = 255*(1 - c)
						g1 = 255*(1 - m)
						b1 = 255*(1 - y)
						txt += '<span background="#%02x%02x%02x">CMYK100</span> '%(r1,g1,b1)
						#print r1,g1,b1
					r2 = 255*(1 - c22)
					g2 = 255*(1 - m22)
					b2 = 255*(1 - y22)
					#print r2,g2,b2
					txt += '<span background="#%02x%02x%02x">CMYK</span>'%(r2,g2,b2)
					dictm = self.das[pn].dictmod
					bstr = d2hex(buf)
					for i in range(dictm.iter_n_children(None)):
						if bstr == dictm.get_value(dictm.iter_nth_child(None,i),2):
							txt = '<span background="#FFFF00">'+txt+'</span>  '
							break

		if dlen == 8:
			if self.options_le == 1:
				txt = "LE: %s\t"%((struct.unpack("<d",buf)[0])/self.options_div)
			if self.options_be == 1:
				txt += "BE: %s"%((struct.unpack(">d",buf)[0])/self.options_div)
		if dlen == 3:
			txt = '<span background="#%02x%02x%02x">RGB</span>  '%(ord(buf[0]),ord(buf[1]),ord(buf[2]))
			txt += '<span background="#%02x%02x%02x">BGR</span>'%(ord(buf[2]),ord(buf[1]),ord(buf[0]))
		if dlen > 3 and dlen != 4 and dlen != 8 and self.options_txt == 1:
			try:
				txt += '\t<span background="#DDFFDD">'+unicode(buf,self.options_enc).replace("\n","\\n")[:32]+'</span>'
			except:
				pass
				
		self.update_statusbar(txt)

	def update_data(self):
		pn = self.notebook.get_current_page()
		treeSelection = self.das[pn].view.get_selection()
		model, iter1 = treeSelection.get_selected()
		hd = self.das[pn].hd
		model.set_value(iter1,3,hd.hv.data)
		hd.hv.modified = 0
		hd.hv.expose(None,None)

	def edited_cb (self, cell, path, new_text):
		pn = self.notebook.get_current_page()
		treeSelection = self.das[pn].view.get_selection()
		model, iter1 = treeSelection.get_selected()
		hd = self.das[pn].hd
		value = model.get_value(iter1,3) 
		hditer = hd.hdmodel.get_iter(path)

		offset = hd.hdmodel.get_value(hditer,2)
		size = hd.hdmodel.get_value(hditer,3)
		fmt = hd.hdmodel.get_value(hditer,4)
		#print 'Format: ', fmt

		if fmt == "clr":
			value = value[0:offset] + struct.pack("B",int(new_text[4:6],16))+struct.pack("B",int(new_text[2:4],16))+struct.pack("B",int(new_text[0:2],16))+value[offset+3:]
		elif fmt == "clrgb":
			value = value[0:offset] + struct.pack("B",int(new_text[0:2],16))+struct.pack("B",int(new_text[2:4],16))+struct.pack("B",int(new_text[4:6],16))+value[offset+3:]
		elif fmt == "txt":
			value = value[0:offset]+new_text+value[offset+size:]
		elif fmt == "utxt":
			value = value[0:offset]+new_text.encode("utf-16-le")+value[offset+size:]
		else:
			value = value[0:offset] + struct.pack(fmt,float(new_text))+value[offset+size:]

		model.set_value(iter1,3,value)
		if self.das[pn].type == "vsd":
			(ifmt,itype,t) = model.get_value(iter1,1)
		else:
			(ifmt,itype) = model.get_value(iter1,1)
		if ifmt == "emf" and itype > 0x4000:
			piter = model.iter_parent(iter1)
			nvalue = model.get_value(piter,3)[:16]
			for i in range(model.iter_n_children(piter)):
				nvalue += model.get_value(model.iter_nth_child(piter,i),3)
			model.set_value(piter,3,nvalue)
			
		self.on_row_activated(self.das[pn].view,model.get_path(iter1),0)
		hd.hdview.set_cursor(path)
		hd.hdview.grab_focus()

	def on_row_activated(self, view, path, column):
		pn = self.notebook.get_current_page()
		model = self.das[pn].view.get_model()
		hd = self.das[pn].hd
		hd.version = self.das[pn].version
		iter1 = model.get_iter(path)
		ntype = model.get_value(iter1,1)
		size = model.get_value(iter1,2)
		data = model.get_value(iter1,3)
		if hd.hv.modified:
			dialog = gtk.MessageDialog(parent = None, buttons = gtk.BUTTONS_YES_NO, 
			flags =gtk.DIALOG_DESTROY_WITH_PARENT,type = gtk.MESSAGE_WARNING, 
			message_format = "Do you want to save your changes?")
			
			dialog.set_title("Unsaved changes in data")
			result = dialog.run()
			dialog.destroy()
			if result == gtk.RESPONSE_YES:
				model.set_value(hd.hv.iter,3,hd.hv.data)
			elif result == gtk.RESPONSE_NO:
				print "Changes discarded"

		if data != None:
			hd.hv.modified = 0
			hd.hv.editmode = 0
			hd.hv.offnum = 0
			hd.hv.iter = iter1
			hd.hv.data = data
			hd.hv.parent = self
			hd.hv.hvlines = []
			hd.hv.hl = {}
			hd.hv.sel = None
			hd.hv.curr = 0
			hd.hv.curc = 0
			hd.hv.prer = 0
			hd.hv.prec = 0
			hd.hv.init_lines()
			hd.hv.expose(None,None)

			hd.hdmodel.clear()

			if hd.da != None:
				hd.da.destroy()

			if ntype != 0:
				ut = ""
				for i in range(len(ntype)):
					ut += "%s "%ntype[i]
				self.update_statusbar("[ %s]"%ut)
				if ntype[0] == "escher":
					if ntype[1] == "odraw":
						if escher.odraw_ids.has_key(ntype[2]):
							escher.odraw_ids[ntype[2]](hd, size, data)
				elif ntype[0] == "quill":
					if quill.sub_ids.has_key(ntype[1]):
						quill.sub_ids[ntype[1]](hd, size, data)
				elif ntype[0] == "vsd":
					if ntype[1] == "chnk":
						if vsdchunks.chnk_func.has_key(ntype[2]):
							vsdchunks.chnk_func[ntype[2]](hd, size, data)
					elif ntype[1] == "str4":
						if vsdstream4.stream_func.has_key(ntype[2]):
							vsdstream4.stream_func[ntype[2]](hd, size, data)
					elif ntype[1] == "hdr":
						vsd.hdr(hd,data)
				elif ntype[0] == "vba" and ntype[1] == "dir":
					vba.vba_dir(hd,data)
				elif ntype[0] == "vba" and ntype[1] == "src":
					vba.vba_src(hd,data)
				elif ntype[0] == "ppp":
					if ppp.ppp_ids.has_key(ntype[1]):
						ppp.ppp_ids[ntype[1]](hd,size,data,self.das[pn])
				elif ntype[0] == "emf":
					if emfparse.emr_ids.has_key(ntype[1]):
						emfparse.emr_ids[ntype[1]](hd,size,data)
				elif ntype[0] == "wmf":
					if wmfparse.wmr_ids.has_key(ntype[1]):
						wmfparse.wmr_ids[ntype[1]](hd,size,data)
				elif ntype[0] == "svm":
					if svm.svm_ids.has_key(ntype[1]):
						svm.svm_ids[ntype[1]](hd,size,data)
				elif ntype[0] == "cmx":
					if cmx.cmx_ids.has_key(ntype[1]):
						cmx.cmx_ids[ntype[1]](hd,size,data)
				elif ntype[0] == "cdr":
					if cdr.cdr_ids.has_key(ntype[1]):
						if ntype[1] == 'DISP':
							cdr.cdr_ids[ntype[1]](hd,size,data,self.das[pn])
						else:
							cdr.cdr_ids[ntype[1]](hd,size,data)
				elif ntype[0] == "wld":
					if wld.wld_ids.has_key(ntype[1]):
							wld.wld_ids[ntype[1]](hd,size,data)
				elif ntype[0][0:3] == "pub":
					if pub.pub98_ids.has_key(ntype[1]):
							pub.pub98_ids[ntype[1]](hd,size,data)
				elif	ntype[0] == "emf+":
					if emfplus.emfplus_ids.has_key(ntype[1]):
						emfplus.emfplus_ids[ntype[1]](hd,data)
				elif ntype[0] == "xls":
					if xls.biff5_ids.has_key(ntype[1]):
						xls.biff5_ids[ntype[1]](hd,data)
				elif ntype[0] == "doc":
					if doc.recs.has_key(ntype[1]):
						doc.recs[ntype[1]](hd,data)
				elif ntype[0] == "mdb":
					if mdb.rec_ids.has_key(ntype[1]):
						mdb.rec_ids[ntype[1]](hd,data)
				elif	ntype[0] == "cfb":
					if ole.ole_ids.has_key(ntype[1]):
						ole.ole_ids[ntype[1]](hd,data)
				elif ntype[0] == "rx2":
					if rx2.rx2_ids.has_key(ntype[1]):
						rx2.rx2_ids[ntype[1]](hd,data)
				elif ntype[0] == "fh":
					if fhparse.hdp.has_key(ntype[1]):
						fhparse.hdp[ntype[1]](hd,data,self.das[pn])
				elif ntype[0] == "ole":
					if ole.ole_ids.has_key(ntype[1]):
						ole.ole_ids[ntype[1]](hd,data)


	def activate_new (self,parent=None):
		doc = Doc.Page()
		dnum = len(self.das)
		self.das[dnum] = doc
		scrolled = doc.scrolled
		doc.hd = hexdump.hexdump()
		doc.hd.txtdump_hex.connect('populate_popup',self.build_context_menu)
		vpaned = doc.hd.vpaned
		hpaned = gtk.HPaned()
		hpaned.add1(scrolled)
		hpaned.add2(vpaned)
		label = gtk.Label("Unnamed")
		self.notebook.append_page(hpaned, label)
		self.notebook.show_tabs = True
		self.notebook.show_all()
		doc.view.connect("row-activated", self.on_row_activated)
		doc.view.connect("key-press-event", self.on_row_keypressed)
		doc.view.connect("key-release-event", self.on_row_keyreleased)
		doc.view.connect("button-release-event", self.on_row_keyreleased)
		doc.hd.hdview.connect("row-activated", self.on_hdrow_activated)
		doc.hd.hdview.connect("key-press-event", self.on_hdrow_keypressed)
		doc.hd.hdview.connect("key-release-event", self.on_hdrow_keyreleased)
		doc.hd.hdview.connect("button-release-event", self.on_hdrow_keyreleased)

	def activate_reload (self,parent=None):
		pn = self.notebook.get_current_page()
		treeSelection = self.das[pn].view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1:
			intPath = model.get_path(iter1)
		fname = self.das[pn].fname
		self.activate_close(self)
		print "Reloading ",fname
		self.fname = fname
		self.activate_open(self)
		self.notebook.set_current_page(pn)
		if iter1:
			self.das[pn].view.expand_to_path(intPath)
			self.das[pn].view.set_cursor_on_cell(intPath)

	def activate_open(self,parent=None):
		if self.fname !='':
			fname = self.fname
			self.fname = ''
		else:
			fname = self.file_open()
		print fname
		if fname:
			doc = Doc.Page()
			doc.fname = fname
			doc.parent = self
			doc.hd = hexdump.hexdump()
			err = doc.fload()
			if err == 0:
				dnum = len(self.das)
				self.das[dnum] = doc
				scrolled = doc.scrolled
				vpaned = doc.hd.vpaned
				doc.view.connect("row-activated", self.on_row_activated)
				doc.view.connect("key-press-event", self.on_row_keypressed)
				doc.view.connect("key-release-event", self.on_row_keyreleased)
				doc.view.connect("button-release-event", self.on_row_keyreleased)
				doc.hd.hdview.connect("row-activated", self.on_hdrow_activated)
				doc.hd.hdview.connect("key-release-event", self.on_hdrow_keyreleased)
				doc.hd.hdview.connect("button-release-event", self.on_hdrow_keyreleased)
				doc.hd.hdrend.connect('edited', self.edited_cb)
				doc.hd.hdview.set_tooltip_column(8)
				
				hpaned = gtk.HPaned()
				hpaned.add1(scrolled)
				hpaned.add2(vpaned)
				label = gtk.Label(doc.pname)
				eventbox = gtk.EventBox()
				eventbox.add(label)
				eventbox.show_all()
				self.notebook.append_page(hpaned, eventbox)
				self.notebook.set_tab_reorderable(hpaned, True)
				self.notebook.show_tabs = True
				self.notebook.show_all()
			else:
				print err
		return

	def file_open (self,title='Open',parent=None, dirname=None, fname=None):
		if title == 'Save':
			dlg = gtk.FileChooserDialog('Save...', action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
		else:
			dlg = gtk.FileChooserDialog('Open...', parent, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
		dlg.set_local_only(True)
		resp = dlg.run()
		fname = dlg.get_filename()
		dlg.hide()
		if resp == gtk.RESPONSE_CANCEL:
			return None
		return fname

def main():
	ApplicationMainWindow()
	gtk.main()

if __name__ == '__main__':
	main()
