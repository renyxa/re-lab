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

import sys,struct,os
from datetime import datetime
import gtk,gobject
try:
    import gtksourceview2
except:
    print "gtksourceview2 was not found. Don't use 'run'..."
import hexview
import utils
import cli

version = "0.5.1"

ui_info = \
'''<ui>
	<menubar name='MenuBar'>
	<menu action='FileMenu'>
		<menuitem action='New'/>
		<menuitem action='Open'/>
		<menuitem action='Reload'/>
		<menuitem action='Save'/>
		<menuitem action='Options'/>
		<menuitem action='Close'/>
		<separator/>
		<menuitem action='Quit'/>
	</menu>
	<menu action='HelpMenu'>
		<menuitem action='About'/>
		<menuitem action='Manual'/>
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
		self.entry.set_size_request(300,24)
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
		self.search = None
		# configuration options
		self.options_le = 1
		self.options_be = 0
		self.options_txt = 1
		self.options_ipaddr = 0
		self.options_div = 1
		self.options_enc = "utf-16"
		self.options_win = None
		self.statbuffer = ""

		self.run_win = None

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
			( "Options", None,                    # name, stock id
				"Op_tions","<control>T",                      # label, accelerator
				"Configuration options",                             # tooltip
				self.activate_options),

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
				"About colupatr",								   # tooltip
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

	def activate_about(self, action):
		dialog = gtk.AboutDialog()
		dialog.set_name("colupatr v"+version)
		dialog.set_copyright("\302\251 Copyright 2011 frob")
		dialog.set_website("http://www.gimp.ru/")
		## Close dialog on user response
		dialog.connect ("response", lambda d, r: d.destroy())
		dialog.show()

	def draw_manual (self, widget, event):
		mytxt = \
"<b>Keys:</b>\n\
	<tt>[Del]</tt>	attach next row to the current one\n\
	<tt>[BS] </tt>	at the start of the row: attach row to the previous one\n\
			at the middle of row: attach left part to the previous row\n\
	<tt>[Tab]</tt>	 wrap or expand current row to the size of previous one,\n\
			move to next line\n\
\n\
<b>Commands:</b>\n\
	<tt>?</tt>		search\n\
	<tt>!</tt>		comment\n\
	<tt>/</tt>		separate at address\n\
	<tt>goto</tt>		scroll to address\n\
	<tt>fmt</tt>		wrap lines\n\
	<tt>reload</tt>	reload hexview\n\
	<tt>name</tt>		rename the tab\n\
\n\
<b>Runs:</b>\n\
	<tt>run cli.wrap(hv,cli.read(hv,\">h\")+2); cli.next(hv)</tt>\n\
	<tt>run if cli.rwrap(hv,hv.line_size(hv.curr+1)): cli.prev(hv)</tt>\n\
		"

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
		s.set_size_request(660,400)
		da = gtk.DrawingArea()
		da.connect('expose_event', self.draw_manual)
		w.set_title("colupatr Manual")
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
		if lt == "IP Addr":
			self.options_ipaddr = abs(self.options_ipaddr-1)

		if self.statbuffer != "":
			self.calc_status(self.statbuffer,len(self.statbuffer))

	def del_optwin (self, action):
		self.options_win = None

	def del_runwin (self, action):
		self.run_win = None

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
			ipaddr_chkb = gtk.CheckButton("IP Addr")
			
			if self.options_le:
				le_chkb.set_active(True)
			if self.options_be:
				be_chkb.set_active(True)
			if self.options_txt:
				txt_chkb.set_active(True)
			if self.options_ipaddr:
				ipaddr_chkb.set_active(True)
	
			le_chkb.connect("toggled",self.on_option_toggled)
			be_chkb.connect("toggled",self.on_option_toggled)
			txt_chkb.connect("toggled",self.on_option_toggled)
			ipaddr_chkb.connect("toggled",self.on_option_toggled)
	
			hbox0 = gtk.HBox()
			hbox0.pack_start(le_chkb)
			hbox0.pack_start(be_chkb)
			hbox0.pack_start(txt_chkb)
			hbox0.pack_start(ipaddr_chkb)
			
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
	#		ok_btn = gtk.Button("OK")
	
			vbox.pack_start(hbox0)
			vbox.pack_start(hbox1)
			vbox.pack_start(hbox2)
	#		vbox.pack_start(ok_btn)
			
			optwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
			optwin.set_resizable(False)
			optwin.set_border_width(0)
			optwin.add(vbox)
			optwin.set_title("Colupatr Options")
			optwin.connect ("destroy", self.del_optwin)
			optwin.show_all()
			self.options_win = optwin
			

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


	def rlp_pack(self,dscr,fmt,value,f):
		dl = len(dscr)
		f.write(struct.pack("B",dl))
		f.write(dscr)
		f.write(fmt)
		if fmt == " s":
			vl = len(value)
			f.write(struct.pack("<I",vl))
			v = value
		else:
			v = struct.pack(fmt,value)
		f.write(v)

	def activate_save(self,action):
		pn = self.notebook.get_current_page()
		if pn != -1:
			doc = self.das[pn]
			fname = self.file_open("Save",None,None,doc.fname)
			if fname:
				doc.fname = fname
				pos = fname.rfind('/')
				if pos !=-1:
					pname = fname[pos+1:]
				else:
					pname = fname
				ebox = self.notebook.get_tab_label(doc.table)
				ebox.get_children()[0].set_text(pname)
				f = open(fname,"wb")
				f.write("RE-LABv05 [DL(B)|D|VF(2c)|VL(<I)|V]")
				self.rlp_pack("Colupatr Version"," s",version,f)
				self.rlp_pack("Change UID"," s",os.environ.get("USERNAME"),f)
				self.rlp_pack("Change time"," s",str(datetime.now()),f)
				self.rlp_pack("Num of lines","<I",len(doc.lines),f)
				for i in range(len(doc.lines)):
					l = doc.lines[i][0]
					s = doc.lines[i][1]
					f.write(struct.pack("<I",l))
					f.write(struct.pack("B",s))
				self.rlp_pack("Num of comments","<I",len(doc.comments),f)
				for i in doc.comments:
					cmnt = doc.comments[i]
					t = cmnt.text
					o = cmnt.offset
					l = cmnt.length
					c = cmnt.clr
					ct = cmnt.ctype
					f.write(struct.pack("B",len(t)))
					f.write(t)
					f.write(struct.pack("<I",o))
					f.write(struct.pack("<I",l))
					f.write(struct.pack("B",int(c[0]*255)))
					f.write(struct.pack("B",int(c[1]*255)))
					f.write(struct.pack("B",int(c[2]*255)))
					f.write(struct.pack("B",ct))
				self.rlp_pack("Data BLOB","<B",0,f)
				f.write(doc.data)
				f.close()


	def activate_reload(self, action):
		print "Reload: not implemented yet"

	def on_lbl_press (self, view, event,label):
		if event.type == gtk.gdk._2BUTTON_PRESS:
			print "will edit the label"
		else:
			print label.get_selection_bounds()


	def rlp_unpack(self,buf,off):
		dl = ord(buf[off])
		off += 1
		k = buf[off:off+dl]
		off += dl
		fmt = buf[off:off+2]
		off += 2
		if fmt == " s":
			vl = struct.unpack("<I",buf[off:off+4])[0]
			off += 4
			v = buf[off:off+vl]
			off += vl
		else:
			v = struct.unpack(fmt,buf[off:off+struct.calcsize(fmt)])[0]
			off += struct.calcsize(fmt)
		return off,k,v


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
			comments = {}
			if buf == None:
				f = open(fname,"rb")
				rbuf = f.read()
				if rbuf[:9] == "RE-LABv05":
					print 'Re-Lab project file'
					# skip "signature"
					off = 35
					k = ""
					while k != "Num of lines":
						off,k,v = self.rlp_unpack(rbuf,off)
						print k,v
					for i in range(v):
						l = struct.unpack("<I",rbuf[off:off+4])[0]
						off += 4
						s = ord(rbuf[off])
						lines.append((l,s))
						off += 1
					
					while k != "Num of comments":
						off,k,v = self.rlp_unpack(rbuf,off)
						print k,v
					for i in range(v):
						tl = ord(rbuf[off])
						off += 1
						txt = rbuf[off:off+tl]
						off += tl
						coff = struct.unpack("<I",rbuf[off:off+4])[0]
						off += 4
						clen = struct.unpack("<I",rbuf[off:off+4])[0]
						off += 4
						clr0 = ord(rbuf[off])/255
						clr1 = ord(rbuf[off+1])/255
						clr2 = ord(rbuf[off+2])/255
						ct = ord(rbuf[off+3])
						off += 4
						comments[coff] = hexview.Comment(txt,coff,clen,(clr0,clr1,clr2),ct)
					while k != "Data BLOB":
						off,k,v = self.rlp_unpack(rbuf,off)
						print k,v
					buf = rbuf[off:]
				elif fname[len(fname)-3:] == "rlp":
					print 'Probably old Re-Lab project file'
					llen = struct.unpack("<I",rbuf[0:4])[0]
					clen = struct.unpack("<I",rbuf[4:8])[0]
					off = 8
					for i in range(llen):
						l1 = struct.unpack("<I",rbuf[off:off+4])[0]
						off += 4
						l2 = ord(rbuf[off])
						off += 1
						if l2 > 1:
							off += 4
							l2 = 1
						lines.append((l1,l2))
					for i in range(clen):
						c1 = struct.unpack("<I",rbuf[off:off+4])[0]
						off += 4
						c2 = ord(rbuf[off])
						off += 1
						c3 = ord(rbuf[off])
						off += 1
						c4 = rbuf[off:off+c3]
						comments[c1+1] = hexview.Comment(c4,c1+1,c2,(1,0,0),0)
						off += c3
					buf = rbuf[off:]
				else:
					buf = rbuf
				f.close()
			doc = hexview.HexView(buf,lines,comments)
			doc.parent = self
			doc.fname = fname
			dnum = len(self.das)
			self.das[dnum] = doc
			pos = fname.rfind('/')
			if pos !=-1:
				pname = fname[pos+1:]
			else:
				pname = fname

			label = gtk.Label(pname)
			ebox = gtk.EventBox()
			ebox.add(label)
			ebox.show_all()
			self.notebook.append_page(doc.table, ebox)
			self.notebook.set_tab_reorderable(doc.table, True)
			self.notebook.show_tabs = True
			self.notebook.show_all()
			doc.hv.grab_focus()
		return

	def file_open (self,title='Open',parent=None, dirname=None, fname=None):
		if title == 'Save':
			dlg = gtk.FileChooserDialog('Save...', action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
			dlg.set_current_name(fname)
		else:
			dlg = gtk.FileChooserDialog('Open...', parent, buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK,gtk.RESPONSE_OK))
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

	def d2hex(self,data):
		s = ""
		for i in range(len(data)):
			s += "%02x"%ord(data[i])
		return s

	def calc_status(self,buf,dlen):
		self.statbuffer = buf
		txt = ""
		txt2 = ""
		if dlen == 2:
			if self.options_le == 1:
				txt = "LE: %s\t"%((struct.unpack("<h",buf)[0])/self.options_div)
			if self.options_be == 1:
				txt += "BE: %s"%((struct.unpack(">h",buf)[0])/self.options_div)
		if dlen == 4:
			if self.options_le == 1:
				txt = "LE: %s"%((struct.unpack("<i",buf)[0])/self.options_div)
				txt += "\tLEF: %s\t"%((struct.unpack("<f",buf)[0])/self.options_div)
			if self.options_be == 1:
				txt += "BE: %s\t"%((struct.unpack(">i",buf)[0])/self.options_div)
				txt += "BEF: %s"%((struct.unpack(">f",buf)[0])/self.options_div)
			if self.options_ipaddr == 1:
				txt += "%d.%d.%d.%d"%(ord(buf[0]),ord(buf[1]),ord(buf[2]),ord(buf[3]))
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

	def html_export(self,doc,sline,coff,clen):
		fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE,doc.fname+".html")
		if fname:
			f = open(fname,'w')
			f.write("<!DOCTYPE html><html><body><table style='font-family:%s;' cellspacing=0>\n"%doc.font)
			f.write("<head>\n<meta charset='utf-8'>\n") 
			f.write("<style type='text/css'>\ntr.top1 td { border-top: 1px solid black; }")
			f.write("tr.top2 td { border-top: 2px solid purple; }\n")
			f.write("tr.top3 td { border-top: 3px solid red; }\n")
			f.write(".mid { border-left: 1px solid black; border-right: 1px solid black;}\n")
			f.write("</style>\n</head>\n")
			off = 0
			i = 0
			while off < clen:
				so = doc.lines[sline+i][0]
				eo = doc.lines[sline+i+1][0]
				try:
					txt1 = doc.hvlines[sline+i][0]
				except:
					txt1 = doc.get_string(sline+i)[0]
				txt2 = doc.hvlines[sline+i][1]
				off += eo - so
				cmnt = doc.chk_comment(so,eo)
				cl = doc.lines[sline+i][1]
				if cl:
					f.write("<tr class='top%s'>"%cl)
				else:
					f.write("<tr>")
				txt3 = ""
				if cmnt != -1:
					txt3 += doc.comments[cmnt].text
					clr = doc.comments[cmnt].clr
					cmntclr = "%d,%d,%d"%(clr[0]*255,clr[1]*255,clr[2]*255)
					
					f.write("<td style='background-color: rgba(%s,0.3);'>%s</td><td class='mid'>%s</td><td style='color: rgba(%s,1);'>%s</td>"%(cmntclr,txt1,txt2,cmntclr,txt3))
				else:
					f.write("<td>%s</td><td class='mid'>%s</td><td></td>"%(txt1,txt2))
				f.write("</tr>\n")
				i += 1
			f.write("</table></body></html>")
			f.close()
		else:
			print "Nothing to export"

	def on_entry_activate (self,action,cmdline=""):
		if cmdline == "":
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
						data = doc.data[doc.lines[r1][0]+c1:doc.lines[r2][0]+c2]
				cmd = cmdline.split()
				doc.bklines = []
				doc.bkhvlines = []
				doc.bklines += doc.lines
				doc.bkhvlines += doc.hvlines

				if cmd[0].lower() == "name" and len(cmd) > 1:
					ebox = self.notebook.get_tab_label(doc.table)
					ebox.get_children()[0].set_text(cmd[1])
				elif cmd[0].lower() == "bck":
					pass
				elif cmd[0].lower() == "reload":
					exec("reload(hexview)")
				elif cmdline[:3].lower() == "run":
					hv = doc
					if len(cmdline) < 5:
						self.open_cli()
						cmdline = ""
					else:
						cmdline = cmdline[4:]
						exec(cmdline)
						hv.expose(None,None)
				elif cmd[0].lower() == "fmt":
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
						doc.fmt_row(doc.curr,cmd)
						lrow = doc.curr+len(cmd)

					elif mpos == len(cmdline)-1:
						# repeat wrapping till end
						print "Rpt to end"
						cmd = cmdline[4:mpos].split()
						cmdacc = 0
						rpt = 0
						for k in cmd:
							cmdacc += int(k)
							if cmdacc + curpos > len(doc.data):
								cmd = cmd[:k]
								rpt = 1
								break
						if rpt == 0:
							rpt = 1+(doc.lines[len(doc.lines)-1][0]-doc.lines[doc.curr][0])/cmdacc
						for i in range(rpt):
							doc.fmt_row(doc.curr+i*len(cmd),cmd)

						lrow = doc.curr+i*len(cmd)
						
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
							doc.fmt_row(doc.curr+i*len(cmd),cmd)

						lrow = doc.curr+i*len(cmd)+1

					doc.hvlines[lrow] = ""
					doc.set_maxaddr()
					doc.expose(None,None)

				elif cmd[0].lower() == "goto":
					addr = 0
					addrflag = 0
					if len(cmd) > 1:
						try:
							goto = cmdline[4:]
							pos = goto.find("+")
							if pos != -1:
								if pos == 1:
									addr = doc.lines[doc.curr][0]+doc.curc+int(goto[pos+1:],16)
									addrflag = 1
								else:
									addr = int(goto[1:pos],16)+int(goto[pos+1:],16)
							else:
								pos = goto.find("-")
								if pos != -1:
									if pos == 1:
										addr = doc.lines[doc.curr][0]+doc.curc-int(goto[pos+1:],16)
										addrflag = 1
									else:
										addr = int(goto[1:pos],16)-int(goto[pos+1:],16)
								else:
									addr = int(goto[1:], 16)
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
						lnum = utils.find_line(doc,addr)
						print "Lnum found",lnum,"%x %x"%(doc.lines[lnum][0],doc.lines[lnum+1][0])
						if addrflag == 0:
							self.entry.set_text("goto %x"%addr)
						doc.curr = lnum
						doc.curc = addr - doc.lines[lnum][0]
						doc.offnum = min(lnum,llast-doc.numtl)
						doc.offset = doc.lines[lnum][0]

					else:
						print "Address after end of file"
						doc.offnum = llast-doc.numtl
						doc.offset = doc.lines[llast-1][0]
					doc.vadj.value = doc.offnum
					doc.expose(doc.hv,action)
				elif cmdline[0] == "?":
					utils.cmd_parse(cmdline,self,doc)
				elif cmdline[0] == "!":
					# off;len;text
					cmd = cmdline[1:].split(";")
					if len(cmd) < 3:
						# add comment to selection or cursor
						if doc.cursor_in_sel():
							rs,cs,re,ce = doc.sel
							clen = doc.get_sel_len()
						else:
							rs = doc.curr
							cs = doc.curc
							clen = 1
						text = cmdline[1:]
						off = doc.lines[rs][0]+cs+1
					else:
						text = ";".join(cmd[2:])
						off = int(cmd[0],16)+1
						clen = int(cmd[1],16)
					try:
						doc.insert_comment2(text,off,clen)
						doc.expose(doc.hv,action)
					except:
						print "Wrong args",sys.exc_info()
				elif cmdline.lower() == "dump":
					fname = self.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE)
					if fname:
						f = open(fname,'wb')
						f.write(doc.data)
						f.close()
					else:
						print "Nothing to save"
				elif cmd[0].lower() == "html":
					off = -1
					try:
						off = int(cmd[1],16)
						clen = int(cmd[2],16)
						lnum = 0
						if off < len(doc.data):
							lnum = utils.find_line(doc,off)
							addr = doc.lines[lnum]
							if addr < off:
								clen += off - addr
					except:
						print "Something wrong with arguments",sys.exc_info()
					if off == -1:
						lnum = 0
						clen = len(doc.data)
					self.html_export(doc,lnum,off,clen)
				elif cmdline[0] == "/":
					if len(cmdline) > 1:
						pos1 = cmdline.find("+")
						pos2 = cmdline.find("-")
						if pos1 != -1 or pos2 != -1:
							pos = max(pos1,pos2)
							try:
								arg1 = int(cmdline[1:pos],16)
								arg2 = int(cmdline[pos+1:],16)
								if pos1 != -1:
									addr = arg1+arg2
									self.entry.set_text("/%x+%x"%(addr,arg2))
								else:
									addr = arg1-arg2
									self.entry.set_text("/%x-%x"%(addr,arg2))
								lnum = utils.find_line (doc,addr)
								cnum = addr - doc.lines[lnum][0]
							except:
								print "Invalid offset"
						else:
							arg = cmdline[1:]
							try:
								addr = int(arg,16)
								lnum = utils.find_line (doc,addr)
								cnum = addr - doc.lines[lnum][0]
							except:
								print "Invalid offset"
					else:
						lnum = doc.curr
						cnum = doc.curc
					if lnum > 0:
						if cnum > 0:
							doc.fmt(lnum,[cnum])
							lnum += 1
							doc.curr = lnum
							doc.curc = 0
						s = (doc.lines[lnum-1][1]+1)%4
						doc.lines[lnum-1] = (doc.lines[lnum-1][0],s)
						# scroll down if went below screen
						if lnum > doc.offnum+doc.numtl-3:
							doc.offnum += doc.numtl/2
						# scroll up if went above screen
						if lnum < doc.offnum:
							doc.offnum = lnum
						doc.expose(None,None)


	def on_search_row_activated(self, view, path, column):
		treeSelection = view.get_selection()
		model1, iter1 = treeSelection.get_selected()
		goto = model1.get_value(iter1,2)
#		addr = model1.get_value(iter1,1)
		self.on_entry_activate (None,"goto %s"%goto)


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


	def get_clp_text(self, clipboard, text, data):
		txtlist = text.split()
		data = ""
		try:
			for i in txtlist:
				data += struct.pack("B",int(i,16))
			self.activate_open(None,data)
		except:
			print "Not a copy of hexdump"

	def open_cli_old(self):
		dialog = gtk.Dialog("colupatr CLI",	None,
			gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
			(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
			gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		tb = gtk.TextBuffer()
		tv = gtk.TextView(tb)
		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(660,400)
		s.add_with_viewport(tv)
		dialog.vbox.pack_start(s)
		s.show_all()
		resp = dialog.run()
		dialog.destroy()
		txt = ""
		if resp == gtk.RESPONSE_ACCEPT:
			txt = tb.get_text(tb.get_start_iter(),tb.get_end_iter())
			print txt
		return txt

	def cli_on_run (self,wg,event,tb):
		txt = tb.get_text(tb.get_start_iter(),tb.get_end_iter())
		pn = self.notebook.get_current_page()
		if pn != -1:
			hv = self.das[pn]
			exec(txt)
			hv.expose(None,None)

	def cli_on_open (self,wg,event,tb):
		print "Not implemented yet"

	def cli_on_save (self,wg,event,tb):
		print "Not implemented yet"

	def open_cli(self):
		if self.run_win != None:
			self.run_win.show_all()
			self.run_win.present()
		else:
			open_btn = gtk.Button("Open")
			save_btn = gtk.Button("Save")
			run_btn = gtk.Button("Run")
			tb = gtksourceview2.Buffer()
			tv = gtksourceview2.View(tb)
			lm = gtksourceview2.LanguageManager()
			lp = lm.get_language("python")
			tb.set_highlight_syntax(True)
			tb.set_language(lp)
			s = gtk.ScrolledWindow()
			s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
			s.set_size_request(660,400)
			s.add_with_viewport(tv)
			s.show_all()
			hbox = gtk.HBox()
			hbox.pack_start(open_btn)
			hbox.pack_start(save_btn)
			hbox.pack_start(run_btn)
			vbox = gtk.VBox()
			vbox.pack_start(s)
			vbox.pack_start(hbox)
			
			runwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
			runwin.set_resizable(True)
			runwin.set_border_width(2)
			runwin.add(vbox)
			runwin.set_title("Colupatr CLI")
			runwin.connect ("destroy", self.del_runwin)
			run_btn.connect("button-press-event",self.cli_on_run,tb)
			open_btn.connect("button-press-event",self.cli_on_open,tb)
			save_btn.connect("button-press-event",self.cli_on_save,tb)
			runwin.show_all()
			self.run_win = runwin


	def on_entry_keypressed (self, view, event):
		if event.state == gtk.gdk.CONTROL_MASK and event.keyval == 118 : # ^V
				clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
				clipboard.request_text(self.get_clp_text)
				self.entry.set_text("")
				return True
		elif event.state == gtk.gdk.CONTROL_MASK and event.keyval == 32 : # ^Space
			pn = self.notebook.get_current_page()
			if pn != -1:
				doc = self.das[pn]
				doc.hv.grab_focus()
			return True
		elif event.state&gtk.gdk.MOD1_MASK == gtk.gdk.MOD1_MASK:
				event.state = event.state&0x3ff7 # exclude Alt
				pn = self.notebook.get_current_page()
				if pn != -1:
					doc = self.das[pn]
					if doc.okp.has_key(event.keyval):
						doc.on_key_press(None,event)
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
