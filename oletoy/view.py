#!/usr/bin/env python
import sys,struct
import gobject
import gtk
import tree
import hexdump
import Doc
import oleparse

ui_info = \
'''<ui>
	<menubar name='MenuBar'>
	<menu action='FileMenu'>
		<menuitem action='New'/>
		<menuitem action='Open'/>
		<menuitem action='Save'/>
		<menuitem action='Close'/>
		<separator/>
		<menuitem action='Quit'/>
	</menu>
	<menu action='HelpMenu'>
		<menuitem action='About'/>
	</menu>
	</menubar>
</ui>'''

ui_popup = \
'''<ui>
	<popup name="EntryPopup">
		<menuitem name="child" action="child"/>
	</popup>
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
		self.set_default_size(500, 350)

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
		table.attach(self.notebook,
			# X direction #		  # Y direction
			0, 1,					  1, 2,
			gtk.EXPAND | gtk.FILL,	 gtk.EXPAND | gtk.FILL,
			0,						 0);

		# Create statusbar
		self.statusbar = gtk.Statusbar()
		table.attach(self.statusbar,
			# X direction		   Y direction
			0, 1,				   2, 3,
			gtk.EXPAND | gtk.FILL,  0,
			0,					  0)
		self.show_all()
		self.das = {}
		self.fname = ''
		self.selection = None


		if len(sys.argv) > 1:
			for i in range(len(sys.argv)-1):
				self.fname = sys.argv[i+1]
				self.activate_open()

	def __create_action_group(self):
		# GtkActionEntry
		entries = (
			( "FileMenu", None, "_File" ),			   # name, stock id, label
			( "HelpMenu", None, "_Help" ),			   # name, stock id, label
			( "New", gtk.STOCK_NEW,					# name, stock id
				"_New","<control>N",					  # label, accelerator
				"Create file",							 # tooltip
				self.activate_new),
			( "Open", gtk.STOCK_OPEN,					# name, stock id
				"_Open","<control>O",					  # label, accelerator
				"Open a file",							 # tooltip
				self.activate_open),
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
				"_About", "<control>A",					# label, accelerator
				"About",								   # tooltip
				self.activate_about ),
		);

		# Create the menubar and toolbar
		action_group = gtk.ActionGroup("AppWindowActions")
		action_group.add_actions(entries)
		return action_group

	def activate_save (self, action):
		fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
		if fname:
			pn = self.notebook.get_current_page()
			model = self.das[pn].view.get_model()
			f = open(fname,'w')
			model.foreach (self.dump_tree, f)
			f.close()

	def dump_tree (self, model, path, iter, f):
		type = model.get_value(iter,1)
		len = model.get_value(iter,2)
		value = model.get_value(iter,3)
		if len != None:
			f.write(struct.pack("<I",type) + struct.pack("<I",len) + value)
		return False

	def activate_about(self, action):
		dialog = gtk.AboutDialog()
		dialog.set_name("OLE toy")
		dialog.set_copyright("\302\251 Copyright 2010 V.F.")
		dialog.set_website("http://www.gnome.ru/")
		## Close dialog on user response
		dialog.connect ("response", lambda d, r: d.destroy())
		dialog.show()

	def activate_quit(self, action):
		 gtk.main_quit()
		 return
 
	def update_statusbar(self, buffer):
		# clear any previous message, underflow is allowed
		self.statusbar.push(0,'%s' % (buffer))

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

	def update_resize_grip(self, widget, event):
		mask = gtk.gdk.WINDOW_STATE_MAXIMIZED | gtk.gdk.WINDOW_STATE_FULLSCREEN
		if (event.changed_mask & mask):
			self.statusbar.set_has_resize_grip(not (event.new_window_state & mask))

	def on_row_keypressed (self, view, event):
		treeSelection = view.get_selection()
		model, iter = treeSelection.get_selected()
		if iter:
			intPath = model.get_path(iter)
			if event.keyval == 65535:
				model.remove(iter)
				if model.get_iter_first():
					if intPath >= 0:
						view.set_cursor(intPath)
						view.grab_focus()
			else:
				if event.keyval == 99 and event.state == gtk.gdk.CONTROL_MASK:
					self.selection = (model.get_value(iter,0),model.get_value(iter,1),model.get_value(iter,2),model.get_value(iter,3))
				if event.keyval == 118 and event.state == gtk.gdk.CONTROL_MASK and self.selection != None:
					niter = model.insert_after (None, iter)
					model.set_value (niter, 0, self.selection[0])
					model.set_value (niter, 1, self.selection[1])
					model.set_value (niter, 2, self.selection[2])
					model.set_value (niter, 3, self.selection[3])

	def on_row_keyreleased (self, view, event):
		treeSelection = view.get_selection()
		model, iter = treeSelection.get_selected()
		if iter:
			intPath = model.get_path(iter)
			self.on_row_activated(view, intPath, 0)

	def on_hdrow_keyreleased (self, view, event):
		treeSelection = view.get_selection()
		model, iter = treeSelection.get_selected()
		if iter:
			intPath = model.get_path(iter)
			self.on_hdrow_activated(view, intPath, 0)

	def on_hdrow_activated(self, view, path, column):
		pn = self.notebook.get_current_page()
		model = self.das[pn].hd.hdview.get_model()
		hd = self.das[pn].hd
		iter = model.get_iter(path)
		offset = model.get_value(iter,2)
		size = model.get_value(iter,3)
		buffer_hex = hd.txtdump_hex.get_buffer()
		try:
			tag = buffer_hex.create_tag("hl",background="yellow")
		except:
			pass
		buffer_hex.remove_tag_by_name("hl",buffer_hex.get_iter_at_offset(0),buffer_hex.get_iter_at_offset(buffer_hex.get_char_count()))
		iter_hex = buffer_hex.get_iter_at_offset(offset*3)
		off2 = offset*3+size*3-1
		if off2 < 0:
			off2 = 0
		iter_hex_end = buffer_hex.get_iter_at_offset(off2)
		buffer_hex.apply_tag_by_name("hl",iter_hex,iter_hex_end)

	def edited_cb (self, cell, path, new_text):
		pn = self.notebook.get_current_page()
		treeSelection = self.das[pn].view.get_selection()
		model, iter = treeSelection.get_selected()
		hd = self.das[pn].hd
		value = model.get_value(iter,3) 
		hditer = hd.hdmodel.get_iter(path)

		offset = hd.hdmodel.get_value(hditer,2)
		size = hd.hdmodel.get_value(hditer,3)
		fmt = hd.hdmodel.get_value(hditer,4)
#		print 'Format: ', fmt
		if fmt != "clr":
			value = value[0:offset] + struct.pack(fmt,float(new_text))+value[offset+size:]
		else:
			value = value[0:offset] + struct.pack("B",int(new_text[4:6],16))+struct.pack("B",int(new_text[2:4],16))+struct.pack("B",int(new_text[0:2],16))+value[offset+3:]
		model.set_value(iter,3,value)
		self.on_row_activated(self.das[pn].view,model.get_path(iter),0)
		hd.hdview.set_cursor(path)
		hd.hdview.grab_focus()

	def on_row_activated(self, view, path, column):
		pn = self.notebook.get_current_page()
		model = self.das[pn].view.get_model()
		hd = self.das[pn].hd
		iter = model.get_iter(path)
		type = model.get_value(iter,1)
		size = model.get_value(iter,2)
		data = model.get_value(iter,3)
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
			print "Type: %02x"%type
			if oleparse.odraw_ids.has_key(type):
				oleparse.odraw_ids[type](hd, size, data)

	def activate_new (self,parent=None):
		doc = mfdoc.mfPage()
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
		doc.hd.hdview.connect("key-release-event", self.on_hdrow_keyreleased)
		doc.hd.hdview.connect("button-release-event", self.on_hdrow_keyreleased)

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
			err = doc.fload()
			if err == 0:
				dnum = len(self.das)
				self.das[dnum] = doc
				scrolled = doc.scrolled
				doc.hd = hexdump.hexdump()
				vpaned = doc.hd.vpaned
				doc.view.connect("row-activated", self.on_row_activated)
				doc.view.connect("key-press-event", self.on_row_keypressed)
				doc.view.connect("key-release-event", self.on_row_keyreleased)
				doc.view.connect("button-release-event", self.on_row_keyreleased)
				doc.hd.hdview.connect("row-activated", self.on_hdrow_activated)
				doc.hd.hdview.connect("key-release-event", self.on_hdrow_keyreleased)
				doc.hd.hdview.connect("button-release-event", self.on_hdrow_keyreleased)
				doc.hd.hdrend.connect('edited', self.edited_cb)
				hpaned = gtk.HPaned()
				hpaned.add1(scrolled)
				hpaned.add2(vpaned)
				label = gtk.Label(doc.pname)
				self.notebook.append_page(hpaned, label)
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

	def build_context_menu(self,txt,menu):
		pn = self.notebook.get_current_page()
		hd = self.das[pn].hd
		merge = gtk.UIManager()
		merge.insert_action_group(self.__create_action_group_popup(), 0)
		bounds = hd.txtdump_hex.get_buffer().get_selection_bounds()
		try:
			mergeid = merge.add_ui_from_string(ui_popup)
			menu = merge.get_widget("/EntryPopup")
			if not bounds:
				menu.set_sensitive(False)
			menu.popup(None,None,None,0,0)
		except gobject.GError, msg:
			print "building menus failed: %s" % msg

	def __create_action_group_popup(self):
		# GtkActionEntry
		entries = (
		  ( "child", None,					# name, stock id
			"Add child","<control>A",					  # label, accelerator
			"Add EMF command",							 # tooltip
			self.activate_child),
		);
		# Create the menubar and toolbar
		action_group = gtk.ActionGroup("PopupActions")
		action_group.add_actions(entries)
		return action_group

	def activate_child(self, menuitem):
		pn = self.notebook.get_current_page()


def main():
	ApplicationMainWindow()
	gtk.main()

if __name__ == '__main__':
	main()
