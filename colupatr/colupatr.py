#!/usr/bin/env python
# Copyright (C) 2011	Valek Filippov (frob@df.ru)
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
import gtk,gobject
import hexview

version = "0.2.1"

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
	<menu action='HelpMenu'>
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

		self.set_title("colupatr")
		self.set_default_size(640, 350)

		self.lebe = 0

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
			( "HelpMenu", None, "_Help" ),			   # name, stock id, label
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
			( "Save", gtk.STOCK_SAVE,                    # name, stock id
				"_Save","<control>S",                      # label, accelerator
				"Save the file",                             # tooltip
				self.activate_save),
			( "Close", gtk.STOCK_CLOSE,                    # name, stock id
				"Close","",                      # label, accelerator
				"Close the file",                             # tooltip
				self.activate_close),
			( "Quit", gtk.STOCK_QUIT,					# name, stock id
				"_Quit", "<control>Q",					 # label, accelerator
				"Quit",									# tooltip
				self.activate_quit ),

			( "About", None,							 # name, stock id
				"About", "",					# label, accelerator
				"About colupatr",								   # tooltip
				self.activate_about ),
		);

		# Create the menubar and toolbar
		action_group = gtk.ActionGroup("AppWindowActions")
		action_group.add_actions(entries)
		return action_group

	def activate_about(self, action):
		dialog = gtk.AboutDialog()
		dialog.set_name("colupatr v"+version)
		dialog.set_copyright("\302\251 Copyright 2011 frob")
		dialog.set_website("http://www.gimp.ru/")
		## Close dialog on user response
		dialog.connect ("response", lambda d, r: d.destroy())
		dialog.show()

	def activate_quit(self, action):
		 gtk.main_quit()
		 return

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

	def activate_save(self, action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			fname = self.file_open("Save",None,None,self.fname)
			if fname:
				f = open(fname,"w")
				doc = self.das[pn]
				f.write(struct.pack("<I",len(doc.lines)))
				for i in doc.lines:
					f.write(struct.pack("<I",i[0]))
					f.write(struct.pack("B",i[1]))
					if i[1] > 1:
						f.write(struct.pack("B",len(i[2])))
						f.write(i[2])
				f.write(doc.data)
				f.close()

	def activate_reload(self, action):
		print "Reload: not implemented yet"

	def activate_open(self,parent=None,buf=None):
		if self.fname !='':
			fname = self.fname
			self.fname = ''
		elif buf == None:
			fname = self.file_open()
		else:
			fname = 'Clipboard'
		print fname
		if fname:
			lines = []
			if buf == None:
				f = open(fname)
				if fname[len(fname)-3:] == "rlp":
					print 'Re-Lab project file'
					rbuf = f.read()
					llen = struct.unpack("<I",rbuf[0:4])[0]
					shift = 0
					for i in range(llen):
						l1 = struct.unpack("<I",rbuf[4+i*5+shift:8+i*5+shift])[0]
						l2 = ord(rbuf[8+i*5+shift])
						if l2 > 1:
							l3len = ord(rbuf[9+i*5+shift])
							l3 = rbuf[10+i*5+shift:10+i*5+shift+l3len]
							shift += l3len+1
							lines.append((l1,l2,l3))
						else:
							lines.append((l1,l2))
					buf = rbuf[4+llen*5+shift+1:]
				else:
					buf = f.read()
				f.close()
			doc = hexview.HexView(buf,lines)
			doc.parent = self
			dnum = len(self.das)
			self.das[dnum] = doc
			pos = fname.rfind('/')
			if pos !=-1:
				pname = fname[pos+1:]
			else:
				pname = fname

			label = gtk.Label(pname)
			self.notebook.append_page(doc.table, label)
			self.notebook.show_tabs = True
			self.notebook.show_all()
			doc.hv.grab_focus()
		return

	def file_open (self,title='Open',parent=None, dirname=None, fname=None):
		if title == 'Save':
			dlg = gtk.FileChooserDialog('Save...',  action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
		else:
			dlg = gtk.FileChooserDialog('Open...', parent, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
		dlg.set_local_only(True)
		resp = dlg.run()
		dlg.hide()
		if resp == gtk.RESPONSE_CANCEL:
				return None
		fname = dlg.get_filename()
		return fname

	def activate_new(self, action):
			return
			doc = hexview.HexView("new")
			doc.parent = self
			dnum = len(self.das)
			self.das[dnum] = doc
			label = gtk.Label('New')
			self.notebook.append_page(doc.table, label)
			self.notebook.show_tabs = True
			self.notebook.show_all()

	def update_statusbar(self, buffer):
		try:
			self.label.set_markup("%s"%buffer)
		except:
			pass

	def calc_status(self,buf,dlen):
		txt = ""
		if self.lebe == 0:
			if dlen == 2:
				if self.lebe == 0:
					txt = "LE: %s"%(struct.unpack("<h",buf)[0])
				else:
					txt = "BE: %s"%(struct.unpack(">h",buf)[0])
			if dlen == 4:
				if self.lebe == 0:
					txt = "LE: %s"%(struct.unpack("<i",buf)[0])
					txt += "\tLEF: %s"%(struct.unpack("<f",buf)[0])
				else:
					txt = "BE: %s"%(struct.unpack(">i",buf)[0])
					txt += "BEF: %s"%(struct.unpack(">f",buf)[0])
			if dlen == 8:
				if self.lebe == 0:
					txt = "LE: %s"%(struct.unpack("<d",buf)[0])
				else:
					txt = "BE: %s"%(struct.unpack(">d",buf)[0])
		if dlen == 3:
			txt = '<span background="#%02x%02x%02x">RGB</span>  '%(ord(buf[0]),ord(buf[1]),ord(buf[2]))
			txt += '<span background="#%02x%02x%02x">BGR</span>'%(ord(buf[2]),ord(buf[1]),ord(buf[0]))
		if dlen > 3:
			try:
#				txt += '\t<span background="#DDFFDD">'+unicode(buf,'cp1251').replace("\n","\\n")[:32]+'</span>'
				txt += '\t<span background="#DDFFDD">'+unicode(buf,'utf16').replace("\n","\\n")[:32]+'</span>'
			except:
				pass
		self.update_statusbar(txt)

	def on_entry_activate (self,action):
		cmdline = self.entry.get_text()
		if len(cmdline) > 0:
			if self.curcmd == -1 or self.cmdhistory[self.curcmd] != cmdline:
				self.cmdhistory.append(cmdline)
				self.curcmd = -1
			pn = self.notebook.get_current_page()
			data = ''
			if pn != -1:
				# try to take current selection
				doc = self.das[pn]
				if doc.sel:
						r1,c1,r2,c2 = doc.sel
						data = doc.data[doc.lines[r1][0]+c1:doc.lines[r2]+c2]
				cmd = cmdline.split()
				doc.bklines = []
				doc.bkhvlines = []
				doc.bklines += doc.lines
				doc.bkhvlines += doc.hvlines

				if  cmd[0].lower() == "fmt":
					cmd = cmd[1:]
					mpos = cmdline.find("*")
					curpos = doc.lines[doc.curr][0]
					if mpos == -1:
						# wrap lines starting from current to provided lengths
						cmdacc = 0
						for k in cmd:
							cmdacc += int(k)
							if cmdacc + curpos > len(doc.data):
								cmd = cmd[:k]
								break
						doc.wrap_helper(doc.curr,cmd,1)

					elif mpos == len(cmdline)-1:
						# repeat wrapping till end
						print "Rpt to end"

					else:
						cmd = cmdline[4:mpos].split()
						rpt = int(cmdline[mpos+1:].strip())
						cmdacc = 0
						for k in cmd:
							cmdacc += int(k)
							if cmdacc + curpos > len(doc.data):
								cmd = cmd[:k]
								rpt = 1
								break
								
						if cmdacc*rpt > doc.lines[len(doc.lines)-1][0]-doc.lines[doc.curr][0]:
							rpt = 1+(doc.lines[len(doc.lines)-1][0]-doc.lines[doc.curr][0])/cmdacc

						#repeat wrapping last arg times
						print "Rpt",rpt,"times",cmd
						for i in range(rpt):
							doc.wrap_helper(doc.curr+i*len(cmd),cmd,0)

					doc.set_maxaddr()
					doc.expose(None,None)
				elif cmd[0].lower() == "goto":
					if len(cmd) > 1:
						try:
							addr = int(cmd[1][:8],16)
							print "Addr: ",addr
						except:
							print "Wrong string for Hex address"
					elif doc.sel:
						if len(data) <4:
							dstr = data + "\x00"*(4-len(data[:4]))
						else:
							dstr = data[:4]
						addr = struct.unpack("<I",dstr)
						print "Addr sel: %04x"%addr
					
					# try to validate/scroll
					llast = len(doc.lines)
					if addr < doc.lines[len(doc.lines)-1][0]:
						lnum = addr/16
						while True:
							if doc.lines[lnum][0] < addr:
								if doc.lines[lnum+1][0] > addr:
									break
								elif doc.lines[lnum+1][0] == addr:
									lnum += 1
								else:
									lnum += (addr - doc.lines[lnum+1][0])/16
							elif  doc.lines[lnum][0] == addr:
								break
							else:
								lnum -= (doc.lines[lnum][0] - addr)/16
							if lnum < 0:
								break
								
						print "Lnum found",lnum,"%x %x"%(doc.lines[lnum][0],doc.lines[lnum+1][0])
						doc.offnum = min(lnum,llast-doc.numtl)
						doc.offset = doc.lines[lnum][0]

					else:
						print "Address after end of file"
						doc.offnum = llast-doc.numtl
						doc.offset = doc.lines[llast-1][0]
					doc.vadj.value = doc.offnum
					doc.expose(doc.hv,action)

	def get_clp_text(self, clipboard, text, data):
		txtlist = text.split()
		data = ""
		try:
			for i in txtlist:
				data += struct.pack("B",int(i,16))
			self.activate_open(None,data)
		except:
			print "Not a copy of hexdump"

	def on_entry_keypressed (self, view, event):
		if event.keyval == 118 and event.state == gtk.gdk.CONTROL_MASK: # ^V
			clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
			clipboard.request_text(self.get_clp_text)
			self.entry.set_text("")
			return True
		elif len(self.cmdhistory) > 0:
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

def main():
	ApplicationMainWindow()
	gtk.main()

if __name__ == '__main__':
  main()
