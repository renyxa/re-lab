#!/usr/bin/env python
# Copyright (C) 2007-2013,	Valek Filippov (frob@df.ru)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 or later of the GNU General Public
# License as published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
# USA


import sys,struct,ctypes,os
import gobject
import gtk, pango, cairo
import tree
import hexdump
import App, cmd
import escher,quill
import vsd,vsd2,vsdchunks,vsdchunks5,vsdstream4
import xls, vba, ole, doc, mdb, pub, ppt, rtf, pm6
import emfparse,svm,mf,wmfparse,emfplus
import rx2,fh
import cdr,cmx,wld,cpt,ppp,pict,chdraw,yep,midi
import vfb
import lrf
import wt602
import pdb
import sbimp
import zmf
import zbr
import hv2, utils
from utils import *
from hv2 import HexView

try:
	import indd
except:
	pass

version = "0.7.40"

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
		<separator/>
		<menuitem action='Config'/>
	</menu>
	<menu action='ViewMenu'>
		<menuitem action='Dict'/>
		<menuitem action='Graph'/>
		<menuitem action='Sync Panels'/>
		<menuitem action='Diff'/>
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


class OldTabLabel(gtk.HBox):
	__gsignals__ = {"close-clicked": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),}

	def __init__(self, label_text):
		gtk.HBox.__init__(self)
		label = gtk.Label(label_text)
		image = gtk.Image()
		image.set_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
		btn = gtk.Button()
		btn.set_image(image)
		btn.set_relief(gtk.RELIEF_NONE)
		btn.set_focus_on_click(False)
		btn.connect("clicked",self.tab_button_clicked)
		self.pack_start(label,1,1,0)
		self.pack_start(btn,0,0,0)
		self.show_all()

	def tab_button_clicked(self, button):
		self.emit("close-clicked")


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
		self.set_default_size(1100, 550)

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
		self.notebook.connect("page-reordered",self.on_page_reordered)
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

		self.cbm = None
		self.sw = None

		# configuration options
		self.options_le = 1
		self.options_be = 0
		self.options_txt = 0
		self.options_div = 1
		self.options_enc = "utf-16"
		self.options_bup = 0

		self.init_config()

		self.options_win = None
		self.bup_win = None
		self.offlen = None
		self.statbuffer = ""
		self.run_win = None

		try:
			self.cgsf = ctypes.cdll.LoadLibrary(self.gsfname)
		except:
			print "Libgsf-1 was not found, do not try to open OLE-based files."


		if len(sys.argv) > 1:
			for i in range(len(sys.argv)-1):
				self.fname = sys.argv[i+1]
				self.activate_open()

	def on_win_destroy(self,widget):
		del self.sw
		self.sw = None

	def init_config(self): # redefine UI/behaviour options from file
		self.font = "Monospace"
		self.fontsize = 14
		self.gsfname = 'libgsf-1.so'
		self.snipsdir = os.path.join(os.path.expanduser("~"),".oletoy")

		try:
			execfile("oletoy.cfg")
			print 'Config loaded...'
		except:
			pass

	def save_config(self):
		cfg = open("oletoy.cfg","w")
		cfg.write("# Monospace font for HexView\nself.font='%s'\n\n"%self.font)
		cfg.write("# Font size for HexView\nself.fontsize=%s\n\n"%self.fontsize)
		cfg.write("# Name of the libgsf\nself.gsfname='%s'\n\n"%self.gsfname)

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
			( "Config", gtk.STOCK_SAVE,						# name, stock id
				"Con_fig","<control>F",					  # label, accelerator
				"Configure OLE Toy",							 # tooltip
				self.activate_config),
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
			( "Graph", gtk.STOCK_INDEX,					# name, stock id
				"_Graph","<control>G",					  # label, accelerator
				"Show graph",							 # tooltip
				self.activate_graph),
			( "Sync Panels", gtk.STOCK_INDEX,					# name, stock id
				"S_ync","<control>Y",					  # label, accelerator
				"Sync Panels",							 # tooltip
				self.activate_syncpanels),
			( "Diff", gtk.STOCK_INDEX,					# name, stock id
				"Diff","<control>X",					  # label, accelerator
				"Diff for two records",							 # tooltip
				self.activate_diff),

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
	Left (on collapsed leaf) - jump to parent leaf.\n\
	^Up/Down - Previous/Next branch of the same level.\n\
	Right click - copy tree path to entry line.\n\
	Delete - remove leaf from the tree\n\
	Type text for quick search (Up/Down for next/prev result).\n\n\
<b>Entry line:</b>\n\
	Up/Down - scroll 'command history'\n\
	gtk tree path - scroll/expand tree\n\
	<tt>#addr</tt> - scroll hexdump to addr\n\
	<tt>#addr+shift, #addr-shift</tt> - calculate new addr and scroll hexdump\n\
	<tt>$b64{@addr}</tt> - try to decode record as base64 encoded string starting from addr (or 0)\n\
	<tt>$cdx{@addr}</tt> - try to parse record as CDX starting from addr (or 0)\n\
	<tt>$cmx{@addr}</tt> - try to parse record as CMX starting from addr (or 0)\n\
	<tt>$dib{@addr}</tt> - try to parse record as DIB starting from addr (or 0)\n\
	<tt>$dump{@addr1{:addr2}}</tt> - save record starting from addr1 (or 0) to addr2 (or end)\n\
	<tt>$emf{@addr}</tt> - try to parse record as EMF starting from addr (or 0)\n\
	<tt>$esc{@addr}</tt> - try to parse record as Escher starting from addr (or 0)\n\
	<tt>$icc{@addr}</tt> - try to parse record as ICC starting from addr (or 0)\n\
	<tt>$ole{@addr}</tt> - try to parse record as OLE starting from addr (or 0)\n\
	<tt>$pix{@addr}</tt> - try to parse record as gdkpixbuf image starting from addr (or 0)\n\
	<tt>$wmf{@addr}</tt> - try to parse record as WMF starting from addr (or 0)\n\
	<tt>$xls@RC</tt> - search XLS file for record related to cell RC\n\
	<tt>$yep{0}{@addr}</tt> - try to parse as BE fourcc RIFF with dword alignment ({0} -- w/o alignment)\n\
	<tt>$zip{@addr}</tt> - try to decompress starting from addr (or 0)\n\n\
	<tt>run</tt> - open CLI window. Use rapp,rpage,rmodel,riter and rbuf\n\
	<tt>reload(module)</tt> - rerun part of the OLE Toy and reload a file\n\
	<tt>rename</tt> - rename current record\n\
	<tt>split@addr</tt> - split current record by addr\n\
	<tt>join {args}</tt> - combine few records starting from selected one.\n\
	               {args} could be number of recs to combine\n\
	               (@offset to skip first offset bytes in each record)\n\
	               or a list of offsets in recs to be combined (comma separated)\n\n\
	<tt>?aSTRING</tt> - search for ASCII string\n\
	<tt>?uSTRING</tt> - search for Unicode (utf16) string\n\
	<tt>?x0123</tt> - search for hex value\n\
	<tt>?rREC{:[aux]STRING}</tt> - search for record with REC in the name and STRING in data.\n\
	<tt>?rloda#{arg}</tt> - search for args in 'loda' records in CDR\n\n\
	<tt>={val}</tt> - search for differences equal to 'val' between current and next pages\n\
		if value skipped, then compares selected iter on pages for any differences\n\
		if no iter selected, then compares whole pages (be patient)\n\n\
<b>Hexdump selection:</b>\n\
	<tt>^E</tt> flips edcurrentlyit mode, grey/green/red circle shows status:\n\
		grey - editing switched off,\n\
		green - editing switched on,\n\
		red - data was modified.\n\
	Switch-on edit/modify/switch-off edit will update data in immediate record.\n\
	Changes do not propogate up the tree.\n\n\
	Select 2,3,4 or 8 bytes - check tooltip in the statusbar.\n\n\
	<tt>^T</tt> opens \"Options\" dialog to adjust conversion of selected bytes.\n\n\
	For PUB 4 bytes would be additionaly converted to points, cm and inches.\n\
	For CDR if 4 bytes match with ID from dictionary, tooltip would be yellow.\n\
	For CDR select outl/fild ID and press arrow right to scroll to it.\n\
	For YEP press arrow right on VPRM block to jump to VWDT sample.\n\
	Press Backspace to come back.\n\n\
<b>Diff:</b>\n\
	^X opens a window that allows to select two records to compare them.\n\
	For the left side it pre-selects currently activated tab for file and\n\
	its current tree selection for record. If no leaf selected in the tree,\n\
	then the first record in the file pre-selected for the record field.\n\
	For the right side it chooses the next tab for the file and its selection\n\
	for the record. If currently activated tab is the last or the only in the list,\n\
	that file will be pre-selected for the right side.\n\
	Paths, offsets and lengths are display only at the moment.\n\n\
	Once selection of the records are completed, press 'Run' button.\n\
	OLEToy uses python's difflib to calculate the difference between those records.\n\
	(Note: it can 'freeze' the program during this calculation)\n\n\
	Diff window highlights the differences:\n\
	  <span bgcolor='#80C0FF'>blue</span> for bytes to add on the right side to match with left side\n\
	  <span bgcolor='#80FFC0'>green</span> for bytes to add on the left side to match with the right side\n\
	  <span bgcolor='#FFC080'>orange</span> for bytes that need to be interchanged between two\n\n\
	There are 'minimap' on the left edge and hex offsets of the first byte of each line\n\
	for both left and right panels." 

		pl = widget.create_pango_layout("")
		pl.set_markup(mytxt)
		gc = widget.window.new_gc()
		w,h = pl.get_size()
		widget.set_size_request(w/1000, h/1000)
		widget.window.draw_layout(gc, 0, 0, pl)


	def activate_syncpanels(self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			hp_pos = self.das[pn].hpaned.get_position()
			vp_pos = self.das[pn].hd.vpaned.get_position()
			for i in self.das:
				self.das[i].hpaned.set_position(hp_pos)
				self.das[i].hd.vpaned.set_position(vp_pos)


	def activate_diff(self, action,data1=None,data2=None):
		if self.sw == None:
			self.sw = cmd.SelectWindow(self)
			self.sw.connect("destroy", self.on_win_destroy)
			self.dw = None
			self.sw.show_all()


	def activate_manual(self, action):
		w = gtk.Window()
		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(860,500)
		da = gtk.DrawingArea()
		da.connect('expose_event', self.draw_manual)
		w.set_title("OLE Toy Manual")
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
		if lt == "BUP":
			self.options_bup = abs(self.options_bup-1)
			if self.options_bup == 1:
				self.activate_bup("")
			
		if self.statbuffer != "":
			self.calc_status(self.statbuffer,len(self.statbuffer))


	def del_win(self,action,win):
		if win == "bup":
			self.bup_win = None
		if win == "options":
			self.options_win = None
		if win == "dict":
			pn = self.notebook.get_current_page()
			if pn != -1:
				self.das[pn].dictwin = None


	def open_cli(self):
		if self.run_win != None:
			self.run_win.show_all()
			self.run_win.present()
		else:
			self.run_win = cmd.CliWindow(self)


	def on_off_entry_activate(self,entry):
		o = self.off_entry.get_text().split()
		l = self.len_entry.get_text().split()
		self.offlen = zip(o,l)


	def activate_graph (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			treeSelection = self.das[pn].view.get_selection()
			model, iter1 = treeSelection.get_selected()
			if iter1:
				graph(self.das[pn].hd,model.get_value(iter1,3))


	def activate_bup (self, action):
		if self.bup_win != None:
			self.bup_win.show_all()
			self.bup_win.present()
		else:
			vbox = gtk.VBox()
			self.off_entry = gtk.Entry()
			self.off_entry.connect("activate",self.on_off_entry_activate)
			self.len_entry = gtk.Entry()
			self.len_entry.connect("activate",self.on_off_entry_activate)
			vbox.pack_start(self.off_entry)
			vbox.pack_start(self.len_entry)
			bupwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
			bupwin.set_border_width(0)
			bupwin.add(vbox)
			bupwin.set_title("Bits unpacker")
			bupwin.connect ("destroy", self.del_win,"bup")
			bupwin.show_all()
			self.bup_win = bupwin


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
			bup_chkb = gtk.CheckButton("BUP")
			
			if self.options_le:
				le_chkb.set_active(True)
			if self.options_be:
				be_chkb.set_active(True)
			if self.options_txt:
				txt_chkb.set_active(True)
			if self.options_bup:
				bup_chkb.set_active(True)

			le_chkb.connect("toggled",self.on_option_toggled)
			be_chkb.connect("toggled",self.on_option_toggled)
			txt_chkb.connect("toggled",self.on_option_toggled)
			bup_chkb.connect("toggled",self.on_option_toggled)

			hbox0 = gtk.HBox()
			hbox0.pack_start(le_chkb)
			hbox0.pack_start(be_chkb)
			hbox0.pack_start(txt_chkb)
			hbox0.pack_start(bup_chkb)
			
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
			optwin.connect ("destroy", self.del_win, "options")
			optwin.show_all()
			self.options_win = optwin


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
					cell1.set_property('font',"%s %s"%(self.font,'10'))
					cell2 = gtk.CellRendererText()
					cell2.set_property('family-set',True)
					cell2.set_property('font',"%s %s"%(self.font,'10'))
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
					dictwin.connect ("destroy", self.del_win,"dict")
					dictwin.show_all()
					self.das[pn].dictwin = dictwin
			elif self.das[pn].type == "FH": # and self.das[pn].version < 9:
				view = gtk.TreeView(self.das[pn].dictmod)
				view.set_reorderable(True)
				view.set_enable_tree_lines(True)
				cell0 = gtk.CellRendererText()
				cell0.set_property('family-set',True)
				cell0.set_property('font',"%s %s"%(self.font,'10'))
				cell1 = gtk.CellRendererText()
				cell1.set_property('family-set',True)
				cell1.set_property('font',"%s %s"%(self.font,'10'))
				cell2 = gtk.CellRendererText()
				cell2.set_property('family-set',True)
				cell2.set_property('font',"%s %s"%(self.font,'10'))
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
		value = model.get_value(iter1,3)
		if type == "emf":
			size = model.get_value(iter1,2)+4
			model.set_value(iter1,3,value[0:4]+struct.pack("<I",size)+value[8:]+'\x00'*4)
		elif type == "wmf":
			size = model.get_value(iter1,2)+2
			model.set_value(iter1,3,struct.pack("<I",len(value)/2+1)+value[4:]+'\x00'*2)
		elif type == "vprm":
			size = model.get_value(iter1,2)+1
			model.set_value(iter1,3,value+'\x00')
		elif type == "xls":
			size = model.get_value(iter1,2)+1
			model.set_value(iter1,3,value[:2]+struct.pack("<H",size)+value[4:3+size]+'\x00')
		else:
			print 'Type',type
			return
		model.set_value(iter1,2,size)

	def activate_less (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
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
			elif type == "vprm":
				size = model.get_value(iter1,2)-1
				model.set_value(iter1,3,value[:-1])
			elif type == "xls" and size > 0:
				model.set_value(iter1,2,size-1)
				model.set_value(iter1,3,value[:2]+struct.pack("<H",size-1)+value[4:3+size])

	def activate_dump (self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			treeSelection = self.das[pn].view.get_selection()
			model, iter1 = treeSelection.get_selected()
			data = model.get_value(iter1,3)
			fname = self.file_open('Save')
			if fname:
				nlen = model.get_value(iter1,2)
				value = model.get_value(iter1,3)
				if nlen != None:
					f = open(fname,'wb')
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
		fname = self.das[pn].fname
		print ftype
		if  ftype == "WMF" or ftype  == "APWMF" or ftype  == "EMF" or ftype == "SVM":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				mf.mf_save(self.das[pn],fname,ftype)
		elif ftype == "cfb":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				ole.save(self.das[pn],fname)
		elif ftype == "vsd":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				vsd.save(self.das[pn],fname)
		elif ftype == "pub":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				pub.save(self.das[pn],fname)
		elif ftype == "YEP":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				yep.save(self.das[pn],fname)
		elif ftype[0:3] == "XLS":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				xls.save(self.das[pn],fname)
		elif ftype == "doc":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				doc.save(self.das[pn],fname)
		elif ftype == "FH":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				fh.fh_save(self.das[pn],fname)
		elif ftype[0:3] == "CDR":
			fname = self.file_open('Save',None,None,fname)
			if fname:
				cdr.save(self.das[pn],fname)
		else:
			self.activate_dump(action)

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

	def activate_config(self, action):
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
			elif 'reload' in goto.lower():
				#try:
				if 1:
					exec("reload(%s)"%goto[7:-1])
					self.activate_reload(None)
				#except:
				#	print "Cannot reload",goto[7:-1]
				#	print sys.exc_info()[1]

			elif goto.lower() == "run":
				self.open_cli()
			elif 'split@' in goto.lower():
				pos = goto.find("@")
				off = int(goto[pos+1:],16)
				treeSelection = self.das[pn].view.get_selection()
				model, niter = treeSelection.get_selected()
				if niter != None:
					v = model.get_value(niter,3)
					add_pgiter(self.das[pn],"Part1","dontsave","",v[:off],niter)
					add_pgiter(self.das[pn],"Part2","dontsave","",v[off:],niter)
			elif 'rename' in goto.lower():
				treeSelection = self.das[pn].view.get_selection()
				model, niter = treeSelection.get_selected()
				if niter != None:
					model.set_value(niter,0,goto[7:])
			elif 'join' in goto.lower():
				if "," in goto:
					j = goto[5:].split(",")
					treeSelection = self.das[pn].view.get_selection()
					model, niter = treeSelection.get_selected()
					iter1 = niter
					if niter != None:
						v = ""
						for i in j:
							v += model.get_value(niter,3)[int(i,16):]
							niter = model.iter_next(niter)
				else:
					if '@' in goto:
						pos = goto.find("@")
						num = int(goto[5:pos],16)
						off = int(goto[pos+1:],16)
					else:
						num = int(goto[5:],16)
						off = 0
					treeSelection = self.das[pn].view.get_selection()
					model, niter = treeSelection.get_selected()
					iter1 = niter
					if niter != None:
						v = model.get_value(niter,3)[off:]
						for i in range(num-1):
							niter = model.iter_next(niter)
							v += model.get_value(niter,3)[off:]
				if iter1 != None:
					add_pgiter(self.das[pn],"[Joined data]","dontsave","",v,iter1)

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

			if self.cbm != None:
				li = self.cbm.get_iter_from_string("%s"%pn)
				self.cbm.remove(li)
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
			elif event.keyval == 65361:
				if view.row_expanded(intPath):
					view.collapse_row(intPath)
				else:
					parent = model.iter_parent(iter1)
					if parent:
						intPath2 = model.get_path(parent)
						view.set_cursor(intPath2)
						view.grab_focus()
				view.columns_autosize()
			elif event.state == gtk.gdk.CONTROL_MASK and event.keyval == 65364:
				iter2 = model.iter_next(iter1)
				if iter2:
					intPath2 = model.get_path(iter2)
					view.set_cursor(intPath2)
					view.grab_focus()
				return 1
			elif event.state == gtk.gdk.CONTROL_MASK and event.keyval == 65362:
				position = intPath[-1]
				if position != 0:
					Path2 = list(intPath)[:-1]
					Path2.append(position - 1)
					prev = model.get_iter(tuple(Path2))
					intPath2 = model.get_path(prev)
					view.set_cursor(intPath2)
					view.grab_focus()
				return 1
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
				ntype = model.get_value(iter1,1)
				if ntype[0] == 'vprm' and ntype[1] == 'hdrbch':
					self.das[pn].backpath = model.get_string_from_iter(iter1)
					goto = model.get_value(iter1,4)
					try:
						self.das[pn].view.expand_to_path(goto)
						self.das[pn].view.set_cursor_on_cell(goto)
					except:
						print "No such path"
			elif event.type  == gtk.gdk.KEY_RELEASE and event.keyval == 65288:
				pn = self.notebook.get_current_page()
				goto = self.das[pn].backpath
				if goto != None:
					print goto
					try:
						self.das[pn].view.expand_to_path(goto)
						self.das[pn].view.set_cursor_on_cell(goto)
					except:
						print "No such path for back path"



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
						ts = self.das[pn].view.get_selection()
						m,i = ts.get_selected()
						self.das[pn].backpath = m.get_string_from_iter(i)
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
		if ftype == "YEP":
			if dlen == 1:
				txt += key2txt(ord(buf),midi.pitches,"")
		
		if self.offlen and self.options_bup == 1:
			bup = bup2(d2hex(buf),self.offlen)
			txt = "%s %s"%(bup[0],bup[1])
			
		if dlen == 2:
			if self.options_le == 1:
				txt += "LE: %s\t"%((struct.unpack("<h",buf)[0])/self.options_div)
			if self.options_be == 1:
				txt += "BE: %s"%((struct.unpack(">h",buf)[0])/self.options_div)
		if dlen == 4:
			if ftype == "pub":
				v = struct.unpack("<i",buf)[0]
				txt += "LE: %s\t(pt/cm/in) %s/%s/%s"%(struct.unpack("<i",buf)[0],round(v/12700.,2),round(v/360000.,3),round(v/914400.,4))
			elif ftype == "FH":
				v1 = struct.unpack(">h",buf[0:2])[0]
				v2 = struct.unpack(">h",buf[2:4])[0]
				txt += "BE: %s\tX: %.4f\tY: %.4f\tF: %.4f\tRG: %.2f"%(struct.unpack(">i",buf)[0],v1-1692+v2/65536.,v1-1584+v2/65536.,v1+v2/65536.,(v1+v2/65536.)*180/3.1415926)
			else:
				if self.options_le == 1:
					txt += "LE: %s"%((struct.unpack("<i",buf)[0])/self.options_div)
					txt += "\tLEF: %s\t"%((struct.unpack("<f",buf)[0])/self.options_div)
				if self.options_be == 1:
					txt += "BE: %s\t"%((struct.unpack(">i",buf)[0])/self.options_div)
					txt += "BEF: %s"%((struct.unpack(">f",buf)[0])/self.options_div)

				if ftype[0:3] == "CDR" or ftype[0:3] == "CMX":
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
							txt += '<span background="#FFFF00">'+txt+'</span>  '
							break

		if dlen == 8:
			if self.options_le == 1:
				txt += "LE: %s\t"%((struct.unpack("<d",buf)[0])/self.options_div)
			if self.options_be == 1:
				txt += "BE: %s"%((struct.unpack(">d",buf)[0])/self.options_div)
		if dlen == 3:
			txt += '<span background="#%02x%02x%02x">RGB</span>  '%(ord(buf[0]),ord(buf[1]),ord(buf[2]))
			txt += '<span background="#%02x%02x%02x">BGR</span>'%(ord(buf[2]),ord(buf[1]),ord(buf[0]))
		if dlen > 3 and self.options_txt == 1 and ftype != "RTF":
			try:
				txt += '\t<span background="#DDFFDD">'+unicode(buf,self.options_enc).replace("\n","\\n")[:32]+'</span>'
			except:
				print sys.exc_info()

		if ftype == "RTF":
			txt = '<span background="#DDFFDD">'+rtf.recode(buf,self.options_enc)+'</span>'
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
		hditer = hd.model.get_iter(path)

		offset = hd.model.get_value(hditer,2)
		size = hd.model.get_value(hditer,3)
		fmt = hd.model.get_value(hditer,4)
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

	def on_page_reordered(self,nb,widget,num):
		# to detect from where tab was dragged
		# not aware about straight way to find it
		# hence use reverse way
		for i in range(len(self.das)):
			if i != num:
				if widget == self.das[i].hpaned:
					numold = i
		if numold > num: # moved from right to left
			# skip to num and after numold
			for i in range(len(self.das)):
				if i == num:
					tmp = self.das[i]
					self.das[i] = self.das[numold]
				elif i > num and i <= numold:
					tmp2 = self.das[i]
					self.das[i] = tmp
					tmp = tmp2
				if i > numold:
					break
		else: # moved from left to right
			# skip to num and after numold
			for i in range(len(self.das)):
				if i >= numold and i < num:
					if i == numold:
						tmp = self.das[i]
					self.das[i] = self.das[i+1]
				elif i == num:
					self.das[i] = tmp
					break

	def on_row_activated(self, view, path, column):
		pn = self.notebook.get_current_page()
		model = self.das[pn].view.get_model()
		hd = self.das[pn].hd
		hd.version = self.das[pn].version
		iter1 = model.get_iter(path)
		ntype = model.get_value(iter1,1)
		size = model.get_value(iter1,2)
		data = model.get_value(iter1,3)
		if self.das[pn].type == "YEP":
			gloff = model.get_value(iter1,7)
		else:
			gloff = None
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
			hd.hv.parent = self
			hd.hv.iter = iter1
			hd.hv.vadj.upper = len(data)/16+2
			hd.hv.vadj.value = 0
			hd.hv.data = data
			hd.hv.hvlines = []
			hd.hv.hl = {}
			hd.hv.sel = None
			hd.hv.curr = 0
			hd.hv.curc = 0
			hd.hv.prer = 0
			hd.hv.prec = 0
			hd.hv.init_lines()
			if gloff != None:
				hd.hv.global_off = int(gloff,16)
			hd.hv.expose(None,None)

			hd.model.clear()

			if hd.da != None:
				hd.da.destroy()

			if ntype != 0:
				ut = ""
				for i in range(len(ntype)):
					ut += "%s "%ntype[i]
				self.update_statusbar("[ %s]"%ut)
				# YEP
				if ntype[0] == "vprm" or ntype[0] == "yep":
					if ntype[1] in yep.vprmfunc:
						off = 0
						offsmp = model.get_value(iter1,8)
						if offsmp == None:
							offstr = model.get_value(iter1,7)
							if offstr:
								off = int(offstr,16)
						else:
							off = offsmp
						yep.vprmfunc[ntype[1]](hd,data,off)
				if ntype[0] == "escher":
					if ntype[1] == "odraw":
						if escher.odraw_ids.has_key(ntype[2]):
							escher.odraw_ids[ntype[2]](hd, size, data)
				elif ntype[0] == "quill":
					if quill.sub_ids.has_key(ntype[1]):
						quill.sub_ids[ntype[1]](hd, size, data)
				elif ntype[0][:4] == "vsd2":
					off = 19
					if ntype[0] == "vsd24":
						off = 4
					if ntype[1] in vsdchunks.chnk_func:
						vsdchunks.chnk_func[ntype[1]](hd, size, data,off)
				elif ntype[0] == "vsd":
					if ntype[1] == "chnk":
						if vsdchunks.chnk_func.has_key(ntype[2]):
							vsdchunks.chnk_func[ntype[2]](hd, size, data)
					elif ntype[1] == "str4":
						if vsdstream4.stream_func.has_key(ntype[2]):
							vsdstream4.stream_func[ntype[2]](hd, size, data)
					elif ntype[1] == "hdr":
						vsd.hdr(hd,data)
				elif ntype[0][:4] == "vsdv" and ntype[1][:4] == "chnk":
						if vsdchunks5.chnk_func.has_key(int(ntype[1][5:])):
							vsdchunks5.chnk_func[int(ntype[1][5:])](hd, size, data)
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
				elif ntype[0] == "lrf":
					if lrf.lrf_ids.has_key(ntype[1]):
						lrf.lrf_ids[ntype[1]](hd, size, data)
				elif ntype[0] == "wt602":
					if wt602.wt602_ids.has_key(ntype[1]):
						wt602.wt602_ids[ntype[1]](hd, size, data)
				elif ntype[0] == 'imp':
					if sbimp.imp_ids.has_key(ntype[1]):
						sbimp.imp_ids[ntype[1]](hd, size, data)
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
					if ole.cfb_ids.has_key(ntype[1]):
						ole.cfb_ids[ntype[1]](hd,data)
				elif ntype[0] == "rx2":
					if rx2.rx2_ids.has_key(ntype[1]):
						rx2.rx2_ids[ntype[1]](hd,data)
				elif ntype[0] == "pdb":
					if pdb.pdb_ids.has_key(ntype[1]):
						pdb.pdb_ids[ntype[1]](hd, size, data)
				elif ntype[0] == "fh":
					if fh.hdp.has_key(ntype[1]):
						fh.hdp[ntype[1]](hd,data,self.das[pn])
				elif ntype[0] == "zmf":
					if zmf.zmf_ids.has_key(ntype[1]):
						zmf.zmf_ids[ntype[1]](hd, size, data)
				elif ntype[0] == "zbr":
					if zbr.zbr_ids.has_key(ntype[1]):
						zbr.zbr_ids[ntype[1]](hd, size, data)
				elif ntype[0] == "xml":
					add_iter (hd,"",data,0,len(data),"txt")

	def tab_button_clicked(self, button):
		print 'Close tab clicked',button.get_parent().get_parent()

	def activate_new (self,parent=None):
		doc = App.Page()
		dnum = len(self.das)
		self.das[dnum] = doc
		scrolled = doc.scrolled
		doc.hd = hexdump.hexdump()
		vpaned = doc.hd.vpaned
		hpaned = gtk.HPaned()
		hpaned.add1(scrolled)
		hpaned.add2(vpaned)
		label = cmd.TabLabel("Unnamed")
		label.connect("close-clicked", self.on_tab_close_clicked, self.notebook, doc.hpaned)
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
		page = self.das[pn]
		treeSelection = page.view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1:
			intPath = model.get_path(iter1)
		if iter1 and self.das[pn].type == "FH":
			par = model.iter_parent(iter1)
			start,off = model.get_value(iter1,4)
			print "Reloading FH from %02x ..."%off
			r = model.remove(iter1)
			while r:
				r = model.remove(iter1)
			print "Iters removed"

			fho = page.appdoc
			fhn = fh.FHDoc(fho.data,fho.page,fho.iter)
			fhn.dictitems = fho.dictitems
			fhn.version = fho.version
			fhn.diter = fho.diter
			fhn.reclist = fho.reclist
			fhn.recs = fho.recs
			page.appdoc = fhn
			fhn.parse_agd(off,start)
			del(fho)
		else:
			fname = self.das[pn].fname
			print "Reloading ",fname
			model.clear()
			self.das[pn].fload()
		if iter1:
			self.das[pn].view.expand_to_path(intPath)
			self.das[pn].view.set_cursor_on_cell(intPath)

	def on_tab_close_clicked(self, tab_label, notebook, tab_widget):
		""" Callback for the "close-clicked" emitted by custom TabLabel widget. """
		pn = notebook.page_num(tab_widget)
		del self.das[pn]
		self.notebook.remove_page(pn)
		if pn < len(self.das):  ## not the last page
			for i in range(pn,len(self.das)):
				self.das[i] = self.das[i+1]
			del self.das[len(self.das)-1]
		if self.cbm != None:
			li = self.cbm.get_iter_from_string("%s"%pn)
			self.cbm.remove(li)

	def activate_open(self,parent=None):
		if self.fname !='':
			fname = self.fname
			self.fname = ''
		else:
			fname = self.file_open()
		if fname:
			print fname
			manager = gtk.recent_manager_get_default()
			manager.add_item(fname)
			doc = App.Page()
			doc.fname = fname
			doc.parent = self
			doc.hd = hexdump.hexdump()
			doc.hd.hv.font = self.font
			doc.hd.hv.fontsize = self.fontsize
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
				
				doc.hpaned = gtk.HPaned()
				doc.hpaned.add1(scrolled)
				doc.hpaned.add2(vpaned)
				label = cmd.TabLabel(doc.pname)
				label.connect("close-clicked", self.on_tab_close_clicked, self.notebook, doc.hpaned)
				self.notebook.append_page(doc.hpaned, label)
				self.notebook.set_tab_reorderable(doc.hpaned, True)
				self.notebook.show_tabs = True
				self.notebook.show_all()
				self.notebook.set_current_page(-1)
				if self.cbm != None:
					li = self.cbm.append()
					self.cbm.set_value(li,0,"%s (tab %s)"%(doc.pname,dnum))
			else:
				print err
		return

	def file_open (self, title='Open', parent=None, dirname=None, fname=""):
		if title == 'Save':
			dlg = gtk.FileChooserDialog('Save...', action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
			dlg.set_current_name(fname)
		else:
			dlg = gtk.FileChooserDialog('Open...', None, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
#		dlg.set_current_folder(dirname)
		dlg.set_local_only(True)
		if dirname and fname != "":
			dlg.select_filename(os.path.join(dirname,fname))

		resp = dlg.run()
		dlg.hide()
		if resp == gtk.RESPONSE_CANCEL:
			return None
		fname = dlg.get_filename()
		return fname


def main():
	ApplicationMainWindow()
	gtk.main()

if __name__ == '__main__':
	main()
