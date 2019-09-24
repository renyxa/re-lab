# Copyright (C) 2007,2010-2013	Valek Filippov (frob@df.ru)
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

import struct
from utils import *
import gobject, gtk
import os, pango
from os.path import expanduser


try:
	import gtksourceview2
	usegtksv2 = True
except:
	usegtksv2 = False



def make_cli_view(cli):
	model = gtk.TreeStore(
	gobject.TYPE_STRING,	# 0 Snippet Name
	gobject.TYPE_STRING, 	# 1 Snippet text
	)
	view = gtk.TreeView(model)
	view.set_reorderable(True)
	view.columns_autosize()
	view.set_enable_tree_lines(True)
	cell = gtk.CellRendererText()
	cell.set_property('family-set',True)
	cell.set_property('font','monospace 10')
	column0 = gtk.TreeViewColumn('SnipName', cell, text=0)
	view.append_column(column0)
	view.set_headers_visible(False)
	view.set_tooltip_column(1)
	treescr = gtk.ScrolledWindow()
	treescr.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
	treescr.add(view)
	treescr.set_size_request(150,-1)
	
	target_entries = [('text/plain', 0, 0)]

	view.enable_model_drag_source(
		gtk.gdk.BUTTON1_MASK, target_entries, gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY)
	view.enable_model_drag_dest(target_entries,gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_COPY)
	view.connect('drag-data-received', cli.on_drag_data_received)
	view.connect("key-press-event", on_row_keypressed)

	return view, model, treescr

def on_row_keypressed (view, event):
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


def create_tbtv(lang="python"):
	# rely on gtksourceview2
	if usegtksv2:
		tb = gtksourceview2.Buffer()
		tv = gtksourceview2.View(tb)
		if lang == "python":
			lm = gtksourceview2.LanguageManager()
			lp = lm.get_language(lang)
			tb.set_language(lp)
		tb.set_highlight_syntax(True)
		tb.set_max_undo_levels(16)
		tb.set_highlight_matching_brackets(False)
		tv.set_show_line_marks(True)
		tv.set_show_line_numbers(True)
		tv.set_draw_spaces(True)
		tv.set_tab_width(4)
		tv.set_smart_home_end(True)
		tv.set_auto_indent(True)
		tv.set_property("draw-spaces",51) # space, tab, leading, text
	else:
		tv = gtk.TextView()
		tb = tv.get_buffer()
	fontdesc = pango.FontDescription("Monospace")
	tv.modify_font(fontdesc)
	return tb,tv


class BTW():
	def __init__(self, app):
		self.app = app
		self.model = gtk.TreeStore(
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			gobject.TYPE_STRING,
			)
		self.view = gtk.TreeView(self.model)
		self.view.set_reorderable(True)
		self.view.columns_autosize()
		self.view.set_enable_tree_lines(True)
		cell0 = gtk.CellRendererText()
		cell0.set_property('family-set',True)
		cell0.set_property('font','monospace 10')
		cell = gtk.CellRendererText()
		cell.set_property('family-set',True)
		cell.set_property('font','monospace 9')
		c0 = gtk.TreeViewColumn('', cell0, text=0)
		c8 = gtk.TreeViewColumn('8', cell, text=8)
		c7 = gtk.TreeViewColumn('7', cell, text=7)
		c6 = gtk.TreeViewColumn('6', cell, text=6)
		c5 = gtk.TreeViewColumn('5', cell, text=5)
		c4 = gtk.TreeViewColumn('4', cell, text=4)
		c3 = gtk.TreeViewColumn('3', cell, text=3)
		c2 = gtk.TreeViewColumn('2', cell, text=2)
		c1 = gtk.TreeViewColumn('1', cell, text=1)
		ct = gtk.TreeViewColumn('', cell0, text=9)
		c8.set_clickable(True)
		c7.set_clickable(True)
		c6.set_clickable(True)
		c5.set_clickable(True)
		c4.set_clickable(True)
		c3.set_clickable(True)
		c2.set_clickable(True)
		c1.set_clickable(True)
		self.view.append_column(c0)
		self.view.append_column(c8)
		self.view.append_column(c7)
		self.view.append_column(c6)
		self.view.append_column(c5)
		self.view.append_column(c4)
		self.view.append_column(c3)
		self.view.append_column(c2)
		self.view.append_column(c1)
		self.view.append_column(ct)
		self.view.set_headers_visible(False)

		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(660,400)
		s.add(self.view)
		s.show_all()
		w = gtk.Window(gtk.WINDOW_TOPLEVEL)
		w.add(s)
		w.show_all()


class CliWindow():
	def __init__(self, app):
		self.app = app
		self.scripts = {}
		self.snipsdir = app.snipsdir
		self.OSD = None
		self.OSD_txt = ""

		tb,tv = create_tbtv()
		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(660,400)
		s.add(tv)
		s.show_all()
		
		self.clinb = gtk.Notebook()

		frame = gtk.Frame("Snippets")
		self.snview,self.snmodel,self.scroll = make_cli_view(self)
		self.snview.connect("row-activated", self.on_row_activated)

		frame.add(self.scroll)
		self.restore_state()
		if len(self.scripts) == 0:
			tab_lbl = TabLabel("New 1")
			tab_lbl.connect("close-clicked", tab_lbl.on_tab_close_clicked, self.clinb, s, self.scripts, "script")
			self.clinb.append_page(s, tab_lbl)
			self.clinb.set_tab_reorderable(s, True)
			self.clinb.show_all()
			self.scripts[len(self.scripts)] = [tb,"New 1",tab_lbl]

		mainhb = gtk.HBox()
		mainhb.pack_start(self.clinb,1,1,0)
		mainhb.pack_start(frame,0,0,0)

		new_btn = gtk.Button("New")
		open_btn = gtk.Button("Open")
		save_btn = gtk.Button("Save")
		run_btn = gtk.Button("Run")

		hbox = gtk.HBox()
		hbox.pack_start(new_btn,0,0,0)
		hbox.pack_start(open_btn,0,0,0)
		hbox.pack_start(save_btn,0,0,0)
		hbox.pack_end(run_btn,0,0,0)

		vbox = gtk.VBox()
		vbox.pack_start(mainhb)
		vbox.pack_start(hbox,0,0,0)

		runwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
#		runwin.set_icon_from_file(os.path.join(self.app.execpath,"pixmaps/icon.png"))

		accgrp = gtk.AccelGroup()
		accgrp.connect_group(110, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.on_key_press) #N
		accgrp.connect_group(111, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.on_key_press) #O
		accgrp.connect_group(114, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.on_key_press) #R
		accgrp.connect_group(115, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.on_key_press) #S
		accgrp.connect_group(105, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.on_key_press) #I
		accgrp.connect_group(117, gtk.gdk.CONTROL_MASK, gtk.ACCEL_VISIBLE, self.on_key_press) #U

		runwin.add_accel_group(accgrp)
		runwin.set_resizable(True)
		runwin.set_border_width(2)
		runwin.add(vbox)
		runwin.set_title("colupatr CLI")
		runwin.connect ("destroy", self.del_runwin)
		run_btn.connect("button-press-event",self.cli_on_run)
		new_btn.connect("button-press-event",self.cli_on_new)
		open_btn.connect("button-press-event",self.cli_on_open)
		save_btn.connect("button-press-event",self.cli_on_save)
		runwin.show_all()
		tv.grab_focus()
		self.app.run_win = runwin


	def add_snippet(self,name,text):
		iter = self.snmodel.append(None,None)
		self.snmodel.set(iter,0,name,1,text)
		self.save_state("snippets")

	def save_state(self,mode="all"):
		# save the state, ignore 'New' files
		if mode in ("files","all"):
			try:
				fs = open(os.path.join(self.snipsdir,"cli_state"),"wb")
				for s in self.scripts.values():
					d = s[1]
					fn = s[2].get_label_text()
					if d != fn:
						fs.write(os.path.join(d,fn))
						fs.write("\n")
				fs.close()
			except:
				print('Failed to save state')

		if mode in ("snippets","all"):
			try:
				fs = open(os.path.join(self.snipsdir,"cli_snippets"),"wb")
				fs.write("# Re-Lab snippets file #\n")
				for i in  range(self.snmodel.iter_n_children(None)):
					ch = self.snmodel.iter_nth_child(None,i)
					n,t = self.snmodel.get_value(ch,0),self.snmodel.get_value(ch,1)
					fs.write("%s %d\n"%(n,len(t)))
					fs.write(t)
					fs.write("\n")
				fs.close()
			except:
				print('Failed to save snippets')

	def restore_state(self):
		# open recent files
		try:
			fs = open(os.path.join(self.snipsdir,"cli_state"),"rb")
			for l in fs:
				try:
					self.cli_on_open(None,None,[l[:-1]])
				except:
					pass # file not loaded
		except:
			print('No saved CLI state was found')

		# load snippets
		try:
			fs = open(os.path.join(self.snipsdir,"cli_snippets"),"rb")
			l = fs.readline() # skip 'header'
			flag = 1
			for l in fs:
				if flag == 1 and len(l)>0:
					name,tlen = l.split()
					txt = ""
					flag = 0
				else:
					txt += l
					if len(txt) > int(tlen):
						flag = 1
						self.add_snippet(name,txt[:-1])
			fs.close()
		except:
			print('Failed to load snippets')


	def del_runwin (self, action):
		self.app.run_win = None

	def on_key_press(self,a1,a2,a3,a4):
		if a3 == 110:
			self.cli_on_new (None,None)
		elif a3 == 111:
			self.cli_on_open (None,None)
		elif a3 == 114:
			self.cli_on_run (None,None)
		elif a3 == 115:
			self.cli_on_save (None,None)
		elif a3 == 105:
			self.cli_on_ident_more (None,None)
		elif a3 == 117:
			self.cli_on_ident_less (None,None)
			
		return True


	def cli_on_ident_more (self,a,b):
		pnb = self.clinb.get_current_page()
		if pnb != -1:
			tb = self.scripts[pnb][0]
			sbnds = tb.get_selection_bounds()
			if sbnds:
				for i in range(sbnds[0].get_line(),sbnds[1].get_line()):
					tb.insert(tb.get_iter_at_line(i),"\t")


	def cli_on_ident_less (self,a,b):
		pnb = self.clinb.get_current_page()
		if pnb != -1:
			tb = self.scripts[pnb][0]
			sbnds = tb.get_selection_bounds()
			if sbnds:
				for i in range(sbnds[0].get_line(),sbnds[1].get_line()):
					start = tb.get_iter_at_line(i)
					end = tb.get_iter_at_line_offset(i,1)
					t = tb.get_text(start,end)
					if t in (" ","\t"):
						tb.delete(start,end)


	def on_row_activated(self,view,path,column):
		iter1 = self.snmodel.get_iter(path)
		txt = self.snmodel.get_value(iter1,1)
		pn = self.clinb.get_current_page()
		if pn != -1:
			tb = self.scripts[pn][0]
			tb.insert_at_cursor(txt)


	def cli_on_open (self,wg,event,fname=None):
		home = expanduser("~")
		if fname is None:
			fname = self.app.file_open('Open',None,os.path.join(home,".oletoy"))
			if fname:
				manager = gtk.recent_manager_get_default()
				for n in fname:
					manager.add_item(n)
		if fname:
			for n in fname:
				f = open(n,"rb")
				buf = f.read()
				if buf:
					self.cli_on_new(wg,event,buf,n)
				f.close()


	def curpage_is_empty(self):
		pn = self.clinb.get_current_page()
		if pn != -1:
			script = self.scripts[pn]
			if not len(script[0].get_text(script[0].get_start_iter(),script[0].get_end_iter())):
				return True
		return False


	def cli_on_save (self,wg,event):
		pn = self.clinb.get_current_page()
		if pn != -1:
			script = self.scripts[pn]
			fname = script[2].get_label_text()
			home = expanduser("~")
			fname = self.app.file_open('Save',None,script[1],fname)
			if fname:
				txt = script[0].get_text(script[0].get_start_iter(),script[0].get_end_iter())
				f = open(fname,'wb')
				f.write(txt)
				f.close()
				manager = gtk.recent_manager_get_default()
				manager.add_item(fname)
				# need to change tab label and store fname
				dname,pname = os.path.split(fname)
				script[1] = dname
				script[2].change_text(pname)
		self.save_state()


	def cli_on_new (self,wg,event,txt="",fname=""):
		if fname == "":
			fname = "New %s"%(len(self.scripts)+1)
		dname,pname = os.path.split(fname)
		if self.curpage_is_empty():
			pn = self.clinb.get_current_page()
			if pn != -1:
				script = self.scripts[pn]
				script[0].set_text(txt)
				script[1] = dname
				script[2].change_text(pname)
		else:
			tb,tv = create_tbtv()
			s = gtk.ScrolledWindow()
			s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
			s.set_size_request(660,400)
			s.add(tv)
			s.show_all()
	
			tab_lbl = TabLabel(pname)
			tab_lbl.connect("close-clicked", tab_lbl.on_tab_close_clicked, self.clinb, s, self.scripts, "script")
			self.clinb.append_page(s, tab_lbl)
			self.clinb.set_current_page(-1)
			if txt != "":
				tb.set_text(txt)
			self.scripts[len(self.scripts)] = [tb,dname,tab_lbl]
			tv.grab_focus()


	def cli_on_run (self,wg,event):
		pn = self.app.notebook.get_current_page()
		if pn != -1:
			rapp = self.app
			rdoc = self.app.das[pn]
			pnb = self.clinb.get_current_page()
			if pnb != -1:
				script = self.scripts[pnb]
				txt = script[0].get_text(script[0].get_start_iter(),script[0].get_end_iter())
				exec(txt)


	def on_drag_data_received(self, view, drag_context, x, y, selection_data, info, eventtime):
		self.OSD_txt = selection_data.get_text()
		if self.OSD is None:
			self.OSD = OSD_Entry(self,None,"snippet")
		xv,yv,w,h = self.scroll.allocation
		xw,yw = self.scroll.get_parent_window().get_position()
		self.OSD.hide()
		self.OSD.show_all()
		self.OSD.move(x+xw+xv,y+yw+yv)
		self.OSD.set_keep_above(True)
		drag_context.finish(success=True, del_=False, time=eventtime)



class OSD_Entry(gtk.Window):
	def __init__(self, parent, oid, mode="snippet"):
		gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)
		self.Doc = parent
		self.oid = oid
		self.mode = mode
		self.set_resizable(True)
		self.set_modal(True)
		self.set_decorated(False)
		self.set_border_width(0)
		self.xs,self.ys = 0,0
		self.entry = gtk.Entry()
		self.entry.connect("key-press-event",self.entry_key_pressed)
		self.add(self.entry)

	def entry_key_pressed(self, entry, event):
		# Changing Label
		if event.keyval == 65307: # Esc
			self.hide()
			entry.set_text("")
			if self.mode == "snippet" and self.Doc.OSD_txt:
				self.Doc.add_snippet("noname",self.Doc.OSD_txt)
				self.Doc.OSD_txt = ""
		elif event.keyval == 65293: # Enter
			self.hide()
			txt = entry.get_text()
			if self.mode == "snippet" and self.Doc.OSD_txt:
				if txt == "":
					txt = "noname"
				self.Doc.add_snippet(txt,self.Doc.OSD_txt)
				self.Doc.OSD_txt = ""



class TabLabel(gtk.HBox):
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
		self.eb = gtk.EventBox()
		self.eb.add(label)
		self.pack_start(self.eb,1,1,0)
		self.pack_start(btn,0,0,0)
		self.show_all()

	def change_text(self,text):
		self.eb.get_children()[0].set_text(text)

	def get_label_text (self):
		return self.eb.get_children()[0].get_text()

	def tab_button_clicked(self, button):
		self.emit("close-clicked")

 	def on_tab_close_clicked(self, tab_label, notebook, tab_widget, arr, tabtype):
		# FROB: need to ask for confirmation of file/page removal
		pn = notebook.page_num(tab_widget)
		if pn != -1:
			del arr[pn]
			notebook.remove_page(pn)
		else: #if len(arr) == 0:
			if tabtype == "doc":
				gtk.main_quit()
			elif tabtype == "page":
				print("FROB: delete the last page -> close file?")
		if pn < len(arr):  ## not the last page
			for i in range(pn,len(arr)):
				arr[i] = arr[i+1]
			del arr[len(arr)-1]




def next (hv):
	if hv.offnum < len(hv.lines)-hv.numtl and hv.curr >= hv.offnum+hv.numtl-3:
		hv.offnum += 1
		hv.mode = ""
	hv.curr += 1
	if hv.curr > len(hv.lines)-2:
		hv.curr = len(hv.lines)-2
	if hv.curr < hv.offnum:
		hv.curr = hv.offnum
	maxc = hv.lines[hv.curr+1][0] - hv.lines[hv.curr][0] -1
	if hv.curc > maxc:
		hv.curc = maxc

def prev (hv):
	if hv.offnum > 0 and hv.curr < hv.offnum+1:
		hv.offnum -= 1
		hv.mode = ""
	hv.curr -= 1
	if hv.curr < 0:
		hv.curr = 0
	if hv.curr > hv.offnum + hv.numtl:
		hv.curr = hv.offnum
	maxc = hv.lines[hv.curr+1][0] - hv.lines[hv.curr][0] -1
	if hv.curc > maxc:
		hv.curc = maxc

def read (hv, fmt, off=-1):
	if off == -1:
		off = tell(hv)
	res = struct.unpack(fmt,hv.data[off:off + struct.calcsize(fmt)])[0]
	return res

def rwrap (hv, col):
	# wrap line from the end
	# push down if longer than col
	# borrow from previous line if shorter than col
	ls = hv.line_size(hv.curr)
	if ls == col:
		# return 1 to be able to check if line wasn't changed
		return 1
	if ls > col:
		wrap (hv,ls-col)
		hv.curc = 0
	else:
		if hv.curr > 0:
			pls = hv.line_size(hv.curr-1)
			prev(hv)
			wrap(hv,ls+pls)
			rwrap(hv,col)

def seek (hv, off):
	llast = len(hv.lines)
	if off < hv.lines[len(hv.lines)-1][0]:
		lnum = find_line(hv,off)
		hv.curr = lnum
		hv.curc = off - hv.lines[lnum][0]
		hv.offnum = min(lnum,llast-hv.numtl)
		hv.offset = hv.lines[lnum][0]

def size (hv, row = -1):
	if row == -1:
		row = hv.curr
	return hv.line_size(row)

def tell (hv):
	return hv.lines[hv.curr][0]+hv.curc

def wrap (hv,col):
	if col > 0:
		hv.fmt(hv.curr,(col,))
