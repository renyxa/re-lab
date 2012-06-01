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
import gtk
import tree
import hexdump
import Doc, cmd
import escher,quill
import vsd, vsdchunks,vsdstream4
import xls, vba, ole, doc, mdb, pub
import emfparse,svm,mf,wmfparse,emfplus,rx2,fh,fhparse
import cdr,cmx,wld
from utils import *

version = "0.5.85"

ui_info = \
'''<ui>
	<menubar name='MenuBar'>
	<menu action='FileMenu'>
		<menuitem action='New'/>
		<menuitem action='Open'/>
		<menuitem action='Reload'/>
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

	def activate_manual (self, action):
		w = gtk.Window()
		t = gtk.TextView();
		tb = t.get_buffer()
		iter_txt = tb.get_iter_at_offset(0)
		mytxt = "Main tree:\n\
	Up/Down - walk the tree.\n\
	Right/Left - expand/collapse branch.\n\
	Right click - copy tree path to entry line.\n\
	Delete - remove leaf from the tree\n\
	Type text for quick search (Up/Down for next/prev result).\n\n\
Entry line:\n\
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
	$xls@RC - search XLS file for record related to cell RC\n\
	?aSTRING - search for ASCII string\n\
	?uSTRING - search for Unicode string\n\
	?x0123 - search for hex value\n\
	?rREC{:[aux]STRING} - search for record with REC in the name and STRING in data.\n\
	?rloda#{arg} - search for args in 'loda' records in CDR\n\n\
Hexdump selection:\n\
	Select 2,3,4 or 8 bytes - check tooltip in statusbar.\n\
	For CDR if 4 bytes match with ID from dictionary, tooltip would be yellow.\n\n\
	For CDR select outl/fild ID and press arrow right to scroll to it."
		tb.insert(iter_txt, mytxt)
		w.set_title("OLE Toy Manual")
		w.set_default_size(520, 300)
		w.add(t)
		w.show_all()

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
		if  ftype == "WMF" or ftype  == "APWMF" or ftype  == "EMF" or ftype == "SVM":
			fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
			if fname:
				mf.mf_save(self.das[pn],fname,ftype)
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
		self.label.set_markup("%s"%buffer)

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
				try:
					buffer_hex = hd.txtdump_hex.get_buffer()
					vadj = hd.vscroll2.get_vadjustment()
					newval = addr/16*vadj.get_upper()/buffer_hex.get_line_count()
					vadj.set_value(newval)
				except:
					print "Wrong address"
			elif goto[0] == "$" or goto[0] == "?":
				cmd.parse (goto,self.entry,self.das[pn])
			elif goto[0] == "=":
					cmd.compare (goto,self.entry,self.das[pn],self.das[pn+1])

			else:
				try:
					self.das[pn].view.expand_to_path(goto)
					self.das[pn].view.set_cursor_on_cell(goto)
				except:
					print "No such path"

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
				view.expand_row(intPath,False)
			elif event.keyval == 65361 and model.iter_n_children(iter1)>0:
				view.collapse_row(intPath)
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
		buffer_hex = hd.txtdump_hex.get_buffer()
		try:
			tag = buffer_hex.create_tag("hl",background="yellow")
		except:
			pass
		buffer_hex.remove_tag_by_name("hl",buffer_hex.get_iter_at_offset(0),buffer_hex.get_iter_at_offset(buffer_hex.get_char_count()))
		iter_hex = buffer_hex.get_iter_at_offset(offset*3)
		vadj = hd.vscroll2.get_vadjustment()
		rowh = vadj.get_upper()/buffer_hex.get_line_count()
		newval = rowh*(offset/16)
		lim = vadj.get_upper() - hd.vscroll2.allocation[3]
		if newval + 2*rowh > hd.vscroll2.allocation[3] and newval -2.5*rowh < lim:
			vadj.set_value(newval-rowh*2)
		elif newval < lim:
			vadj.set_value(newval)
		off2 = offset*3+size*3-1
		if off2 < 0:
			off2 = 0
		iter_hex_end = buffer_hex.get_iter_at_offset(off2)
		buffer_hex.apply_tag_by_name("hl",iter_hex,iter_hex_end)
		if size2 > 0:
			iter_hex2 = buffer_hex.get_iter_at_offset(offset2*3)
			off2 = offset2*3+size2*3-1
			if off2 < 0:
				off2 = 0
			iter_hex2_end = buffer_hex.get_iter_at_offset(off2)
			buffer_hex.apply_tag_by_name("hl",iter_hex2,iter_hex2_end)


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
	
			hd.hdmodel.clear()
			if ntype != 0:
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
					if hd.da != None:
						hd.da.destroy()
					if cdr.cdr_ids.has_key(ntype[1]):
						if ntype[1] == 'DISP':
							cdr.cdr_ids[ntype[1]](hd,size,data,self.das[pn])
						else:
							cdr.cdr_ids[ntype[1]](hd,size,data)
				elif ntype[0] == "wld":
					if wld.wld_ids.has_key(ntype[1]):
							wld.wld_ids[ntype[1]](hd,size,data)

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

	def hdscroll_cb(self,view,event):
		pn = self.notebook.get_current_page()
		hd = self.das[pn].hd
		buffer_hex = hd.txtdump_hex.get_buffer()
		line = buffer_hex.get_property ("cursor-position")/47
		vadj = hd.vscroll2.get_vadjustment()
		rowh = vadj.get_upper()/buffer_hex.get_line_count()
		if line == buffer_hex.get_line_count():
			line -= 1
		newval = rowh*line
		nv = round(vadj.get_value()/rowh)
		if newval + rowh > hd.vscroll2.allocation[3]+vadj.get_value():
			if hd.vscroll2.allocation[3]+ (nv+1)*rowh> vadj.get_upper():
				vadj.set_value(vadj.get_upper() - hd.vscroll2.allocation[3]+rowh/5)
			else:
				vadj.set_value((nv+1)*rowh)
		if newval + rowh <= vadj.get_value():
			vadj.set_value((nv-1)*rowh)

	def hdselect_cb(self,event,udata):
		pn = self.notebook.get_current_page()
		model = self.das[pn].view.get_model()
		type = self.das[pn].type
		#print "Type: ",type
		hd = self.das[pn].hd
		try:
			start,end = hd.txtdump_hex.get_buffer().get_selection_bounds()
		except:
			return
		buffer_asc = hd.txtdump_asc.get_buffer()

		slo = start.get_offset()
		elo = end.get_offset()
		if slo%3 == 1:
			slo -= 1
			start.set_offset(slo)
		if slo%3 == 2:
			slo += 1
			start.set_offset(slo)
		if elo%3 == 0:
			elo -= 1
			end.set_offset(elo)
		if elo%3 == 1:
			elo += 1
			end.set_offset(elo)
		hd.txtdump_hex.get_buffer().move_mark_by_name ('selection_bound',start)
		hd.txtdump_hex.get_buffer().move_mark_by_name ('insert',end)

		asl = start.get_line()
		ael = end.get_line()
		aslo = start.get_line_offset()
		aelo = end.get_line_offset()

		try:
			tag = buffer_asc.create_tag("hl",background="yellow")
		except:
			pass
		buffer_asc.remove_tag_by_name("hl",buffer_asc.get_iter_at_offset(0),buffer_asc.get_iter_at_offset(buffer_asc.get_char_count()))
		iter_asc = buffer_asc.get_iter_at_offset(asl*17+aslo/3)
		iter_asc_end = buffer_asc.get_iter_at_offset(ael*17+aelo/3+1)
		buffer_asc.apply_tag_by_name("hl",iter_asc,iter_asc_end)
		dstart = asl*16+aslo/3
		dend = ael*16+aelo/3+1
		buf = hd.data[dstart:dend]
		txt = ""
		if len(buf) == 2:
			txt = "LE: %s\tBE: %s"%(struct.unpack("<h",buf)[0],struct.unpack(">h",buf)[0])
			if type == "FH" and self.das[pn].dict.has_key(struct.unpack(">h",buf)[0]):
				txt = "BE: %s\t"%(struct.unpack(">h",buf)[0])+self.das[pn].dict[struct.unpack(">h",buf)[0]]
			if type == "FH":
				v = struct.unpack(">H",buf)[0]
				txt = "BE: %s\tX: %d\tY: %d"%(struct.unpack(">h",buf)[0],v-1692,v-1584)
			self.update_statusbar(txt)
		if len(buf) == 4:
			txt = "LE: %s\tBE: %s"%(struct.unpack("<i",buf)[0],struct.unpack(">i",buf)[0])
			txt += "\tLEF: %s\tBEF: %s"%(struct.unpack("<f",buf)[0],struct.unpack(">f",buf)[0])
			if type == "pub":
				v = struct.unpack("<i",buf)[0]
				txt = "LE: %s\t(pt/cm/in) %s/%s/%s"%(struct.unpack("<i",buf)[0],v/12700.,v/360000.,v/914400.)
			if type == "FH":
				v1 = struct.unpack(">H",buf[0:2])[0]
				v2 = struct.unpack(">H",buf[2:4])[0]
				txt = "BE: %s\tX: %.4f\tY: %.4f"%(struct.unpack(">i",buf)[0],v1-1692+v2/65536.,v1-1584+v2/65536.)
			if type[0:3] == "CDR":
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

			self.update_statusbar(txt)
		if len(buf) == 8:
			txt = "LE: %s\tBE: %s"%(struct.unpack("<d",buf)[0],struct.unpack(">d",buf)[0])
			self.update_statusbar(txt)
							
		if len(buf) == 3:
			txt = '<span background="#%02x%02x%02x">RGB</span>  '%(ord(buf[0]),ord(buf[1]),ord(buf[2]))
			txt += '<span background="#%02x%02x%02x">BGR</span>'%(ord(buf[2]),ord(buf[1]),ord(buf[0]))
			self.update_statusbar(txt)
		if len(buf)>3 and len(buf)%2 == 0:
			try:
				if type == "FH":
					utxt = unicode(buf,"utf-16be")
				else:
					utxt = unicode(buf,"utf16")
				txt += "\t" +utxt
				self.update_statusbar(txt)
			except:
				pass
		

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
				doc.hd.txtdump_hex.connect('button-release-event',self.hdselect_cb) 
				doc.hd.txtdump_hex.connect('key-release-event',self.hdscroll_cb)
				doc.hd.txtdump_hex.connect('key-press-event',self.hdscroll_cb)
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
