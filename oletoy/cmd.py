# Copyright (C) 2007-2013	Valek Filippov (frob@df.ru)
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
import tree,gtk,gobject,cairo,zlib
import difflib
import ole,escher,rx2,cdr,icc,mf,pict,chdraw,yep,cvx
from utils import *
from os.path import expanduser

try:
	import gtksourceview2
	usegtksv2 = True
except:
	usegtksv2 = False

cdrloda = {0xa:"Outl ID",0x14:"Fild ID",0x1e:"Coords",0xc8:"Stlt ID",
					0x2af8:"Polygon",0x3e8:"Name",0x2efe:"Rotation",0x7d0:"Palette",
					0x1f40:"Lens",0x1f45:"Container"}


class SelectWindow(gtk.Window):
	def __init__(self, mainapp, parent=None):
		gtk.Window.__init__(self)
		self.mainapp = mainapp
		self.set_title("OLE Toy: Select data to compare")
		
		table = gtk.Table(3, 8, False)

		left_lbl = gtk.Label("Left Panel")
		right_lbl = gtk.Label("Right Panel")
		
		tab_lbl = gtk.Label("File:")
		tab_lbl.set_alignment(xalign=0.0, yalign=0.5)
		self.ltab_cb = gtk.ComboBoxEntry()
		self.rtab_cb = gtk.ComboBoxEntry()
		self.ltab_cb.child.set_can_focus(False)
		self.rtab_cb.child.set_can_focus(False)

		self.tab_cbm = gtk.ListStore(gobject.TYPE_STRING)
		for i in self.mainapp.das:
			li = self.tab_cbm.append()
			self.tab_cbm.set_value(li,0,"%s (tab %s)"%(self.mainapp.das[i].pname,i))

		pathcb_lbl = gtk.Label("Record:")
		pathcb_lbl.set_alignment(xalign=0.0, yalign=0.5)
		self.lpath_cb = gtk.ComboBoxEntry()
		self.rpath_cb = gtk.ComboBoxEntry()
		self.lpath_cb.child.set_can_focus(False)
		self.rpath_cb.child.set_can_focus(False)


		path_lbl = gtk.Label("Path:")
		path_lbl.set_alignment(xalign=0.0, yalign=0.5)
		self.lpath_entry = gtk.Entry()
		self.rpath_entry = gtk.Entry()

		soff_lbl = gtk.Label("Start offset:")
		soff_lbl.set_alignment(xalign=0.0, yalign=0.5)
		self.lsoff_spb = gtk.SpinButton()
		self.rsoff_spb = gtk.SpinButton()

		eoff_lbl = gtk.Label("End offset:")
		eoff_lbl.set_alignment(xalign=0.0, yalign=0.5)
		self.leoff_spb = gtk.SpinButton()
		self.reoff_spb = gtk.SpinButton()

		len_lbl = gtk.Label("Length:")
		len_lbl.set_alignment(xalign=0.0, yalign=0.5)
		self.llen_spb = gtk.SpinButton()
		self.rlen_spb = gtk.SpinButton()

		table.attach(left_lbl,
			1, 2, 0, 1, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(right_lbl,
			2, 3, 0, 1, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		table.attach(tab_lbl,
			0, 1, 1, 2, gtk.FILL, 0, 0, 0);
		table.attach(self.ltab_cb,
			1, 2, 1, 2, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(self.rtab_cb,
			2, 3, 1, 2, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		table.attach(pathcb_lbl,
			0, 1, 2, 3, gtk.FILL, 0, 0, 0);
		table.attach(self.lpath_cb,
			1, 2, 2, 3, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(self.rpath_cb,
			2, 3, 2, 3, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		table.attach(path_lbl,
			0, 1, 3, 4, gtk.FILL, 0, 0, 0);
		table.attach(self.lpath_entry,
			1, 2, 3, 4, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(self.rpath_entry,
			2, 3, 3, 4, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		table.attach(soff_lbl,
			0, 1, 4, 5, gtk.FILL, 0, 0, 0);
		table.attach(self.lsoff_spb,
			1, 2, 4, 5, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(self.rsoff_spb,
			2, 3, 4, 5, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		table.attach(eoff_lbl,
			0, 1, 5, 6, gtk.FILL, 0, 0, 0);
		table.attach(self.leoff_spb,
			1, 2, 5, 6, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(self.reoff_spb,
			2, 3, 5, 6, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		table.attach(len_lbl,
			0, 1, 6, 7, gtk.FILL, 0, 0, 0);
		table.attach(self.llen_spb,
			1, 2, 6, 7, gtk.EXPAND | gtk.FILL, 0, 0, 0);
		table.attach(self.rlen_spb,
			2, 3, 6, 7, gtk.EXPAND | gtk.FILL, 0, 0, 0);

		ok_btn = gtk.Button("Ok")
		ok_btn.connect("clicked",self.ok_button_clicked)

		table.attach(ok_btn,
			1, 3, 7, 8, 0, 0, 0, 0);

		self.init_controls()
		# signals here to not react on init_controls
		self.ltab_cb.connect ('changed', self.changed_cb,"ltab")
		self.rtab_cb.connect ('changed', self.changed_cb,"rtab")
		self.lpath_cb.connect ('changed', self.changed_cb,"lpath")
		self.rpath_cb.connect ('changed', self.changed_cb,"rpath")
		self.add(table)
		self.changed = 1

	def changed_cb(self,entry,cb):
		self.changed = 1
		if cb[1:] == "tab":
			pn = entry.get_active()
			doc = self.mainapp.das[pn]
			model = self.mainapp.das[pn].model
			dlen = model.get_value(model.get_iter_first(),2)
			if cb == "ltab":
				self.lpath_cbm = model
				self.lpath_cb.set_model(self.lpath_cbm)
				self.lpath_cb.set_active(0)
				self.lpath_entry.set_text("0")
				self.lsoff_spb.set_value(0)
				self.leoff_spb.set_value(dlen)
				self.llen_spb.set_value(dlen)
			else:
				self.rpath_cbm = model
				self.rpath_cb.set_model(self.rpath_cbm)
				self.rpath_cb.set_active(0)
				self.rpath_entry.set_text("0")
				self.rsoff_spb.set_value(0)
				self.reoff_spb.set_value(dlen)
				self.rlen_spb.set_value(dlen)
		elif cb[1:] == "path":
			model = entry.get_model()
			iter1 = entry.get_active_iter()
			txt = model.get_string_from_iter(iter1)
			dlen = model.get_value(iter1,2)
			if cb == "lpath":
				self.lpath_entry.set_text(txt)
				self.lsoff_spb.set_value(0)
				self.leoff_spb.set_value(dlen)
				self.llen_spb.set_value(dlen)
			else:
				self.rpath_entry.set_text(txt)
				self.rsoff_spb.set_value(0)
				self.reoff_spb.set_value(dlen)
				self.rlen_spb.set_value(dlen)

	def on_dw_destroy(self,widget):
		self.changed = 1

	def ok_button_clicked(self, button):
		if self.changed:
			self.mainapp.dw = DiffWindow(self.mainapp)
			self.mainapp.dw.connect("destroy", self.on_dw_destroy)
			m1 = self.lpath_cb.get_model()
			m2 = self.rpath_cb.get_model()
			iter1 = self.lpath_cb.get_active_iter()
			iter2 = self.rpath_cb.get_active_iter()
			self.mainapp.dw.diffdata1 = m1.get_value(iter1,3)
			self.mainapp.dw.diffdata2 = m2.get_value(iter2,3)
			self.changed = 0
			self.mainapp.dw.diff_test(self.mainapp.dw.diffdata1,self.mainapp.dw.diffdata2)
			self.mainapp.dw.show_all()

	def init_controls(self):
		self.ltab_cb.set_model(self.tab_cbm)
		self.ltab_cb.set_text_column(0)
		self.rtab_cb.set_model(self.tab_cbm)
		self.rtab_cb.set_text_column(0)

		pn1 = self.mainapp.notebook.get_current_page()
		if pn1 != -1:
			pn2 = min(pn1+1,len(self.mainapp.das)-1)
			self.ltab_cb.set_active(pn1)
			self.rtab_cb.set_active(pn2)

			self.lpath_cbm = self.mainapp.das[pn1].model
			self.lpath_cb.set_model(self.lpath_cbm)
			self.lpath_cb.set_text_column(0)
			self.rpath_cbm = self.mainapp.das[pn2].model
			self.rpath_cb.set_model(self.rpath_cbm)
			self.rpath_cb.set_text_column(0)

			doc1 = self.mainapp.das[pn1]
			doc2 = self.mainapp.das[pn2]
			s1 = doc1.view.get_selection()
			m1, iter1 = s1.get_selected()
			if iter1 == None:
				iter1 = doc1.model.get_iter_first()
			s2 = doc2.view.get_selection()
			m2, iter2 = s2.get_selected()
			if iter2 == None:
				iter2 = doc2.model.get_iter_first()
			
			self.lpath_cb.set_active_iter(iter1)
			self.rpath_cb.set_active_iter(iter2)
			self.lpath_entry.set_text(m1.get_string_from_iter(iter1))
			self.rpath_entry.set_text(m2.get_string_from_iter(iter2))
			
			llen = m1.get_value(iter1,2)
			rlen = m2.get_value(iter2,2)
			lsadj = gtk.Adjustment(0, 0, llen-1, 1, 256, 0)
			leadj = gtk.Adjustment(llen-1, 0, llen-1, 1, 256, 0)
			lladj = gtk.Adjustment(llen-1, 0, llen-1, 1, 256, 0)
			rsadj = gtk.Adjustment(0, 0, rlen-1, 1, 256, 0)
			readj = gtk.Adjustment(rlen-1, 0, rlen-1, 1, 256, 0)
			rladj = gtk.Adjustment(rlen-1, 0, rlen-1, 1, 256, 0)

			self.lsoff_spb.set_adjustment(lsadj)
			self.lsoff_spb.set_value(0)
			self.leoff_spb.set_adjustment(leadj)
			self.leoff_spb.set_value(llen-1)
			self.llen_spb.set_adjustment(lladj)
			self.llen_spb.set_value(llen-1)

			self.rsoff_spb.set_adjustment(rsadj)
			self.rsoff_spb.set_value(0)
			self.reoff_spb.set_adjustment(readj)
			self.reoff_spb.set_value(rlen-1)
			self.rlen_spb.set_adjustment(rladj)
			self.rlen_spb.set_value(rlen-1)

			self.lpath_entry.set_sensitive(False)
			self.rpath_entry.set_sensitive(False)
			self.lsoff_spb.set_sensitive(False)
			self.rsoff_spb.set_sensitive(False)
			self.leoff_spb.set_sensitive(False)
			self.reoff_spb.set_sensitive(False)
			self.llen_spb.set_sensitive(False)
			self.rlen_spb.set_sensitive(False)


class DiffWindow(gtk.Window):
	def __init__(self, mainapp, parent=None):
		self.mainapp = mainapp
		# Create the toplevel window
		gtk.Window.__init__(self)
		self.set_title("OLE Toy DIFF")

		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(1165,400)
		da = gtk.DrawingArea()
		da.connect('expose_event', self.draw_diff,s)
		s.add_with_viewport(da)
		self.damm = gtk.DrawingArea()
		self.damm.connect('expose_event', self.draw_diffmm,s)
		self.damm.set_size_request(42,1)
		va = s.get_vadjustment()
		va.connect('value-changed',self.on_diff_va_changed,self.damm,s)

		hbox= gtk.HBox()
		hbox.pack_start(self.damm,0,0,0)
		hbox.pack_start(s,1,1,0)

		tbox = gtk.HBox()
		flr = gtk.HBox()
		flr.set_size_request(42,1)
		vbl = gtk.VBox()
		vbr = gtk.VBox()
		tbox.pack_start(flr,0,0,0)
		tbox.pack_start(vbl,1,1,0)
		tbox.pack_start(vbr,1,1,0)
		# Create statusbar
		self.statusbar = gtk.HBox()
		self.sblabel = gtk.Label()
		self.sblabel.set_use_markup(True)
		exp_btn = gtk.Button("Export")
		exp_btn.set_alignment(1,0.5)
		exp_btn.connect("clicked",self.activate_export)
		self.statusbar.pack_start(self.sblabel, True,True,2)
		self.statusbar.pack_start(exp_btn, 0,0,0)

		vbox = gtk.VBox()
		vbox.pack_start(tbox,0,0,0)
		vbox.pack_start(hbox,1,1,1)
		vbox.pack_start(self.statusbar,0,0,0)
		self.add(vbox)

		self.diffcs = None # cached CairoSurface
		self.wt = None
		self.ht = None
		self.cswidth = None
		self.csheight = None
		self.draft = 1
		self.diffarr = []
		self.diffsize = None
		self.diffdata1 = None
		self.diffdata2 = None

		sw = self.mainapp.sw
		self.f1name = sw.ltab_cb.child.get_text()
		self.f2name = sw.rtab_cb.child.get_text()
		self.r1name = "%s (%s)"%(sw.lpath_cb.child.get_text(),sw.lpath_entry.get_text())
		self.r2name = "%s (%s)"%(sw.rpath_cb.child.get_text(),sw.rpath_entry.get_text())
		filelbll = gtk.Label(self.f1name)
		filelblr = gtk.Label(self.f2name)
		reclbll = gtk.Label(self.r1name)
		reclblr = gtk.Label(self.r2name)
		filelbll.set_alignment(xalign=0.0, yalign=0.5)
		filelblr.set_alignment(xalign=0.0, yalign=0.5)
		reclbll.set_alignment(xalign=0.0, yalign=0.5)
		reclblr.set_alignment(xalign=0.0, yalign=0.5)
		vbl.pack_start(filelbll,0,0,0)
		vbl.pack_start(reclbll,0,0,0)
		vbr.pack_start(filelblr,0,0,0)
		vbr.pack_start(reclblr,0,0,0)


	def activate_export(self, button):
		fname = self.mainapp.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE,"not_implemented_yet.html")
		if fname:
			f = open(fname,'w')
			f.write("<!DOCTYPE html><html><body>")
			f.write("<head>\n<meta charset='utf-8'>\n") 
			f.write("<style type='text/css'>\ntr.top1 td { border-top: 1px solid black; }")
			f.write("tr.title td { border-bottom: 3px solid black; }\n")
			f.write(".mid { border-left: 1px solid black; border-right: 1px solid black;}\n")
			f.write(".mid2 { border-right: 3px solid black; border-right-style: double}\n")
			f.write("</style>\n</head>\n")
			f.write("<table style='font-family:%s;' cellspacing=0 cellpadding=2>\n"%self.mainapp.font)
			f.write("<tr>")
			f.write("<td colspan=3>%s</td><td colspan=3>%s</td>"%(self.f1name,self.f2name))
			f.write("</tr>\n")
			f.write("<tr class='title'>")
			f.write("<td colspan=3>%s</td><td colspan=3>%s</td>"%(self.r1name,self.r2name))
			f.write("</tr>\n")

			addr = 1
			loff = 0
			roff = 0
#			addr1 |Hex1| Asc1 || addr2 |Hex2| Asc2
			for i in self.diffarr:
				ta,tb,tag = i
				if tag == 'delete':
					hexa = d2hex(ta, " ", 16).split("\n")
					asca = d2asc(ta,16).split("\n") 
					clr = "128,192,255"
					clrsp="<span style='background-color: rgba(%s,0.3);'>"%clr
					for j in range(len(hexa)):
						hpad = "&nbsp;"*(47-len(hexa[j]))
						apad = "&nbsp;"*(16-len(asca[j]))
						f.write("<tr>")
						f.write("<td>%06x</td><td class='mid'>%s%s</span></td><td class='mid2'>%s%s</span></td>"%(loff,clrsp,hexa[j]+hpad,clrsp,asca[j]+apad))
						f.write("<td></td><td class='mid'></td><td></td>")
						f.write("</tr>\n")
						addr += 1
						loff += len(asca[j])
				if tag == 'insert':
					hexb = d2hex(tb, " ", 16).split("\n")
					ascb = d2asc(tb,16).split("\n") 
					clr = "128,255,192"
					clrsp="<span style='background-color: rgba(%s,0.3);'>"%clr
					for j in range(len(hexb)):
						hpad = "&nbsp;"*(47-len(hexb[j]))
						apad = "&nbsp;"*(16-len(ascb[j]))
						f.write("<tr>")
						f.write("<td></td><td class='mid'></td><td class='mid2'></td>")
						f.write("<td>%06x</td><td class='mid'>%s%s</span></td><td>%s%s</span></td>"%(roff,clrsp,hexb[j]+hpad,clrsp,ascb[j]+apad))
						f.write("</tr>\n")
						roff += len(ascb[j])
						addr += 1
				if tag == 'equal':
					hexa = d2hex(ta, " ", 16).split("\n")
					asca = d2asc(ta,16).split("\n") 
					for j in range(len(hexa)):
						hpad = "&nbsp;"*(47-len(hexa[j]))
						apad = "&nbsp;"*(16-len(asca[j]))
						f.write("<tr>")
						f.write("<td>%06x</td><td class='mid'>%s</td><td class='mid2'>%s</td>"%(loff,hexa[j]+hpad,asca[j]+apad))
						f.write("<td>%06x</td><td class='mid'>%s</td><td>%s</td>"%(roff,hexa[j]+hpad,asca[j]+apad))
						f.write("</tr>\n")
						loff += len(asca[j])
						roff += len(asca[j])
						addr += 1
				if tag == 'replace':
					hexa = d2hex(ta, " ", 16).split("\n")
					asca = d2asc(ta,16).split("\n") 
					hexb = d2hex(tb, " ", 16).split("\n")
					ascb = d2asc(tb,16).split("\n") 
					clr = "255,192,128"
					clrsp="<span style='background-color: rgba(%s,0.3);'>"%clr
					for j in range(min(len(hexa),len(hexb))):
						hpada = "&nbsp;"*(47-len(hexa[j]))
						apada = "&nbsp;"*(16-len(asca[j]))
						hpadb = "&nbsp;"*(47-len(hexb[j]))
						apadb = "&nbsp;"*(16-len(ascb[j]))
						f.write("<tr>")
						f.write("<td>%06x</td><td class='mid'>%s%s</span></td><td class='mid2'>%s%s</span></td>"%(loff,clrsp,hexa[j]+hpada,clrsp,asca[j]+apada))
						f.write("<td>%06x</td><td class='mid'>%s%s</span></td><td>%s%s</span></td>"%(roff,clrsp,hexb[j]+hpadb,clrsp,ascb[j]+apadb))
						f.write("</tr>\n")
						loff += len(asca[j])
						roff += len(ascb[j])
						addr += 1
					# print leftovers
					if len(hexa) > len(hexb):
						lb = len(hexb)
						for j in range(len(hexa)-lb):
							hpada = "&nbsp;"*(47-len(hexa[j+lb]))
							apada = "&nbsp;"*(16-len(asca[j+lb]))
							f.write("<tr>")
							f.write("<td>%06x</td><td class='mid'>%s%s</span></td><td class='mid2'>%s%s</span></td>"%(loff,clrsp,hexa[j+lb]+hpada,clrsp,asca[j+lb]+apada))
							f.write("<td></td><td class='mid'></td><td></td>")
							f.write("</tr>\n")
							loff += len(asca[j+lb])
							addr += 1
					elif len(hexb)>len(hexa):
						la = len(hexa)
						for j in range(len(hexb)-la):
							hpadb = "&nbsp;"*(47-len(hexb[j+la]))
							apadb = "&nbsp;"*(16-len(ascb[j+la]))
							f.write("<tr>")
							f.write("<td></td><td class='mid'></td><td class='mid2'></td>")
							f.write("<td>%06x</td><td class='mid'>%s%s</span></td><td>%s%s</span></td>"%(roff,clrsp,hexb[j+la]+hpadb,clrsp,ascb[j+la]+apadb))
							f.write("</tr>\n")
							roff += len(ascb[j+la])
							addr += 1

			f.write("<tr class='top1'><td colspan=6></td></tr>\n")
			f.write("</table></body></html>")
			f.close()
		else:
			print "Nothing to export"

	def on_diff_va_changed (self,va,damm,s):
		self.draw_diffmm(damm,None,s)


	def diff_test(self,data1,data2):
		del self.diffarr
		self.diffarr = []
		if data1 != data2:
			sm = difflib.SequenceMatcher(None, data1, data2, False)
			ta = ""
			tb = ""
			clra = 1,1,1
			clrb = 1,1,1
			for tag, i1, i2, j1, j2 in sm.get_opcodes():
				if tag == 'delete':
					ta = data1[i1:i2]
					tb = ""
				if tag == 'insert':
					tb = data2[j1:j2]
					ta = ""
				if tag == 'equal':
					ta = data1[i1:i2]
					tb = ta
				if tag == 'replace':
					ta = data1[i1:i2]
					tb = data2[j1:j2]
				self.diffarr.append((ta,tb,tag))
		# exactly the same records
		else:
			self.diffarr.append((data1,data1,"equal"))



	def draw_diffmm (self, widget, event,scrollbar):
		x,y,width,height = widget.allocation
		mctx = widget.window.cairo_create()
		cs = cairo.ImageSurface (cairo.FORMAT_ARGB32, width, height)
		ctx = cairo.Context (cs)
		if self.diffcs == None:
			return

		# to calculate how many text lines could be on the screen
		ctx.select_font_face(self.mainapp.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(14)
		ctx.set_line_width(1)
		(xt, yt, wt, ht, dx, dy) = ctx.text_extents("o")
		wt = int(dx)
		ht = int(ht+4)

		wscale = 42./self.cswidth
		hscale = height*1./self.csheight
		if height*1./(self.diffsize*ht) > 1:
			hscale = 1
		ctx.scale(wscale,hscale)
		ctx.set_source_surface(self.diffcs,0,0)
		ctx.paint()

		if hscale != 1:
			va = scrollbar.get_vadjustment()
			ctx.set_source_rgb(0,0,0)
			mms = va.get_value()*height/va.get_upper()
			mmh = va.get_page_size()*height/va.get_upper()
			ctx.scale(1./wscale,1./hscale)
			ctx.rectangle(1.5,int(mms)+0.5,39,int(mmh))
			ctx.stroke()
			ctx.scale(wscale,hscale)

		mctx.set_source_surface(cs,0,0)
		mctx.paint()


	def draw_diff (self, widget, event, scrollbar):
		# FIXME!
		# need to move diffsize & diffarr from AppMainWin to DiffWindow
		mctx = widget.window.cairo_create()
		if self.draft == 1:
			x,y,width,height = widget.allocation
			if self.csheight != None:
				width = self.cswidth
				height = self.csheight
				self.draft = 0
			cs = cairo.ImageSurface (cairo.FORMAT_ARGB32, width, height)
			ctx = cairo.Context (cs)
			ctx.select_font_face(self.mainapp.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
			ctx.set_font_size(14)
			ctx.set_line_width(1)
			(xt, yt, wt, ht, dx, dy) = ctx.text_extents("o")
			wt = int(dx)
			ht = int(ht+4)
			
		# clear everything
			ctx.set_source_rgb(0.95,0.95,0.95)
			ctx.rectangle(0,0,width,height)
			ctx.fill()
			addr = 1
			loff = 0
			roff = 0
			for i in self.diffarr:
				ta,tb,tag = i
				if tag == 'delete':
					hexa = d2hex(ta, " ", 16).split("\n")
					asca = d2asc(ta,16).split("\n") 
					r,g,b = 0.5,0.75,1
					for j in range(len(hexa)):
						ctx.set_source_rgb(r,g,b)
						ctx.rectangle(wt*7,ht*(addr-1),wt*64,ht)
						ctx.fill()
						ctx.set_source_rgb(0,0,0)
						ctx.move_to(0,ht*addr)
						ctx.show_text("%06x"%loff)
						ctx.move_to(wt*7,ht*addr)
						ctx.show_text(hexa[j])
						ctx.move_to(wt*55,ht*addr)
						ctx.show_text(asca[j])
						addr += 1
						loff += len(asca[j])
				if tag == 'insert':
					hexb = d2hex(tb, " ", 16).split("\n")
					ascb = d2asc(tb,16).split("\n") 
					r,g,b = 0.5,1,0.75
					for j in range(len(hexb)):
						ctx.set_source_rgb(r,g,b)
						ctx.rectangle(wt*79,ht*(addr-1),wt*64,ht)
						ctx.fill()
						ctx.set_source_rgb(0,0,0)
						ctx.move_to(wt*72,ht*addr)
						ctx.show_text("%06x"%roff)
						ctx.move_to(wt*79,ht*addr)
						ctx.show_text(hexb[j])
						ctx.move_to(wt*127,ht*addr)
						ctx.show_text(ascb[j])
						roff += len(ascb[j])
						addr += 1
				if tag == 'equal':
					hexa = d2hex(ta, " ", 16).split("\n")
					asca = d2asc(ta,16).split("\n") 
					for j in range(len(hexa)):
						ctx.set_source_rgb(0,0,0)
						ctx.move_to(0,ht*addr)
						ctx.show_text("%06x"%loff)
						ctx.move_to(wt*72,ht*addr)
						ctx.show_text("%06x"%roff)
						ctx.move_to(wt*7,ht*addr)
						ctx.show_text(hexa[j])
						ctx.move_to(wt*55,ht*addr)
						ctx.show_text(asca[j])
						ctx.move_to(wt*79,ht*addr)
						ctx.show_text(hexa[j])
						ctx.move_to(wt*127,ht*addr)
						ctx.show_text(asca[j])
						loff += len(asca[j])
						roff += len(asca[j])
						addr += 1
				if tag == 'replace':
					hexa = d2hex(ta, " ", 16).split("\n")
					asca = d2asc(ta,16).split("\n") 
					hexb = d2hex(tb, " ", 16).split("\n")
					ascb = d2asc(tb,16).split("\n") 
					r,g,b = 1,0.75,0.5
					for j in range(min(len(hexa),len(hexb))):
						ctx.set_source_rgb(r,g,b)
						ctx.rectangle(wt*7,ht*(addr-1),wt*64,ht)
						ctx.rectangle(wt*79,ht*(addr-1),wt*64,ht)
						ctx.fill()
						ctx.set_source_rgb(0,0,0)
						ctx.move_to(0,ht*addr)
						ctx.show_text("%06x"%loff)
						ctx.move_to(wt*72,ht*addr)
						ctx.show_text("%06x"%roff)
						ctx.move_to(wt*7,ht*addr)
						ctx.show_text(hexa[j])
						ctx.move_to(wt*55,ht*addr)
						ctx.show_text(asca[j])
						ctx.move_to(wt*79,ht*addr)
						ctx.show_text(hexb[j])
						ctx.move_to(wt*127,ht*addr)
						ctx.show_text(ascb[j])
						loff += len(asca[j])
						roff += len(ascb[j])
						addr += 1
					# print leftovers
					if len(hexa) > len(hexb):
						lb = len(hexb)
						for j in range(len(hexa)-lb):
							ctx.set_source_rgb(r,g,b)
							ctx.rectangle(wt*7,ht*(addr-1),wt*64,ht)
							ctx.fill()
							ctx.set_source_rgb(0,0,0)
							ctx.move_to(0,ht*addr)
							ctx.show_text("%06x"%loff)
							ctx.move_to(wt*7,ht*addr)
							ctx.show_text(hexa[j+lb])
							ctx.move_to(wt*55,ht*addr)
							ctx.show_text(asca[j+lb])
							loff += len(asca[j+lb])
							addr += 1
					elif len(hexb)>len(hexa):
						la = len(hexa)
						for j in range(len(hexb)-la):
							ctx.set_source_rgb(r,g,b)
							ctx.rectangle(wt*79,ht*(addr-1),wt*64,ht)
							ctx.fill()
							ctx.set_source_rgb(0,0,0)
							ctx.move_to(wt*72,ht*addr)
							ctx.show_text("%06x"%roff)
							ctx.move_to(wt*79,ht*addr)
							ctx.show_text(hexb[j+la])
							ctx.move_to(wt*127,ht*addr)
							ctx.show_text(ascb[j+la])
							roff += len(ascb[j+la])
							addr += 1
							
			ctx.set_source_rgb(0,0,0)
			ctx.move_to(int(wt*6.5)+0.5,0)
			ctx.line_to(int(wt*6.5)+0.5,height)
			ctx.move_to(int(wt*54.5)+0.5,0)
			ctx.line_to(int(wt*54.5)+0.5,height)
			ctx.move_to(int(wt*71.5)-0.5,0)
			ctx.line_to(int(wt*71.5)-0.5,height)
			ctx.move_to(int(wt*71.5)+1.5,0)
			ctx.line_to(int(wt*71.5)+1.5,height)
			ctx.move_to(int(wt*78.5)-0.5,0)
			ctx.line_to(int(wt*78.5)-0.5,height)
			ctx.move_to(int(wt*126.5)+0.5,0)
			ctx.line_to(int(wt*126.5)+0.5,height)
			ctx.move_to(int(wt*143.5)+0.5,0)
			ctx.line_to(int(wt*143.5)+0.5,height)
			ctx.stroke()
			self.diffsize = addr-1
			self.diffcs = cs
			self.wt = wt
			self.ht = ht
			self.cswidth = int(wt*143.5)+1
			self.csheight = int(ht*self.diffsize)
			self.draw_diff(widget,event,scrollbar)
			self.draw_diffmm(self.damm,event,scrollbar)
		else:
			cs = self.diffcs
			wt = self.wt
			ht = self.ht
		mctx.set_source_surface(cs,0,0)
		mctx.paint()
		widget.set_size_request(int(wt*143.5)+1,int(ht*self.diffsize))


class CliWindow(gtk.Window):
	def __init__(self, app):
		gtk.Window.__init__(self)
		self.app = app
		self.fname = ""
		open_btn = gtk.Button("Open")
		save_btn = gtk.Button("Save")
		run_btn = gtk.Button("Run")
		if usegtksv2:
			self.tb = gtksourceview2.Buffer()
			tv = gtksourceview2.View(self.tb)
			lm = gtksourceview2.LanguageManager()
			lp = lm.get_language("python")
			self.tb.set_highlight_syntax(True)
			self.tb.set_language(lp)
			self.tb.set_max_undo_levels(16)
			self.tb.set_highlight_matching_brackets(False)
			tv.set_show_line_marks(True)
			tv.set_show_line_numbers(True)
			tv.set_draw_spaces(True)
			tv.set_tab_width(4)
			tv.set_smart_home_end(True)
			tv.set_auto_indent(True)
			tv.set_property("draw-spaces",51) # space, tab, leading, text
		else:
			tv = gtk.TextView()
			self.tb = tv.get_buffer()

		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(660,400)
		s.add(tv)
		s.show_all()
		hbox = gtk.HBox()

		hbox.pack_start(open_btn,0,0,0)
		hbox.pack_start(save_btn,0,0,0)
		hbox.pack_end(run_btn,0,0,0)
		
		vbox = gtk.VBox()
		hbox2 = gtk.HBox()
		hbox2.pack_start(s)
		vbox.pack_start(hbox2)
		vbox.pack_start(hbox,0,0,0)

		runwin = gtk.Window(gtk.WINDOW_TOPLEVEL)
		runwin.set_resizable(True)
		runwin.set_border_width(2)
		runwin.add(vbox)
		runwin.set_title("OleToy CLI")
		runwin.connect ("destroy", self.del_runwin)
		run_btn.connect("button-press-event",self.cli_on_run,self.tb)
		open_btn.connect("button-press-event",self.cli_on_open,self.tb)
		save_btn.connect("button-press-event",self.cli_on_save,self.tb)
		runwin.show_all()
		tv.grab_focus()
		self.app.run_win = runwin

	def del_runwin (self, action):
		self.app.run_win = None

	def cli_on_open (self,wg,event,tb):
		home = expanduser("~")
		self.fname = self.app.file_open('Open',home+"/.oletoy")
		if self.fname:
			manager = gtk.recent_manager_get_default()
			manager.add_item(self.fname)
			offset = 0
			f = open(self.fname,"rb")
			buf = f.read()
			if buf:
				self.tb.set_text(buf)
			f.close()

	def cli_on_save (self,wg,event,tb):
		home = expanduser("~")
		self.fname = self.app.file_open('Save',home+"/.oletoy",self.fname)
		if self.fname:
			txt = self.tb.get_text(tb.get_start_iter(),tb.get_end_iter())
			f = open(self.fname,'wb')
			f.write(txt)
			f.close()
			manager = gtk.recent_manager_get_default()
			manager.add_item(self.fname)

	def cli_on_run (self,wg,event,tb):
		txt = tb.get_text(tb.get_start_iter(),tb.get_end_iter())
		pn = self.app.notebook.get_current_page()
		if pn != -1:
			rapp = self.app
			rpage = self.app.das[pn]
			treeSelection = self.app.das[pn].view.get_selection()
			rmodel, riter = treeSelection.get_selected()
			if riter:
				rbuf = rmodel.get_value(riter,3)
			else:
				rbuf = ""
			exec(txt)


def arg_conv (ctype,carg):
	data = ''
	if ctype.lower() == 'x':
		data = hex2d(carg)
	elif ctype.lower() == 'u':
		data = carg.encode("utf-16")[2:]
	elif ctype.lower() == 'a' or ctype.lower() == 'r':
		data = carg
	return data

def xlsfind (model,path,iter,(page,rowaddr,coladdr)):
	rname = model.get_value(iter,0)
	rdata = model.get_value(iter,3)
	if rname == 'Dimensions':
		rwmin = struct.unpack('<I',rdata[4:8])[0]
		rwmax = struct.unpack('<I',rdata[8:12])[0]
		colmin = struct.unpack('<H',rdata[12:14])[0]
		colmax = struct.unpack('<H',rdata[14:16])[0]
		if rowaddr < rwmin or rowaddr > rwmax or coladdr < colmin or coladdr > colmax:
			return True
	if rname == 'LabelSst' or rname == 'Number' or rname == 'Blank' or rname == 'Formula' or rname == 'RK':
		rw = struct.unpack('<H',rdata[4:6])[0]
		col = struct.unpack('<H',rdata[6:8])[0]
		if rowaddr == rw and coladdr == col:
			s_iter = page.search.append(None,None)
			page.search.set_value(s_iter,0,model.get_string_from_iter(iter))
			page.search.set_value(s_iter,2,"%s (%d)"%(rname,model.get_value(iter,2)))
#			print 'Found',model.get_string_from_iter(iter)
			return True

def recfind (model,path,iter,(page,data)):
	rec = model.get_value(iter,0)
	# for CDR only
	# ?rloda#hexarg
	# means 'search for record "loda" with hexarg equals some arg ID
	# show value for this hexarg
	# without hexarg -- show list of all hexargs in all loda-s
	carg = data.find("#")
	arg = -1
	if page.type[0:3] == "CDR" and carg != -1:
		rdata1 = data[:carg]
		rdata2 = data[carg+1:]

	else:
	# ?rRECORD:uUNITEXT
	# data -> "RECORD:uUNITEXT"
		arg = data.find(":")
		rdata1 = data
		if arg != -1:
			# rdata1 -> "RECORD"
			# rdata2 -> "uUNITEXT" -> converted to "UNITEXT"
			rdata1 = data[:arg]
			ctype = data[arg+1]
			rdata2 = arg_conv(ctype,data[arg+2:])
	pos = rec.find(rdata1)
	if pos != -1:
		# found record, looks for value in normal case
		if arg != -1:
			recdata = model.get_value(iter,3)
			pos2 = recdata.find(rdata2)
			if pos2 == -1:
				return
		if carg == -1:
			s_iter = page.search.append(None,None)
			page.search.set_value(s_iter,0,model.get_string_from_iter(iter))
			page.search.set_value(s_iter,2,"%s (%d)"%(rec,model.get_value(iter,2)))
			page.search.set_value(s_iter,3,page.search.iter_n_children(None))
		# looks for args in CDR record
		else:
			recdata = model.get_value(iter,3)
			n_args = struct.unpack('<i', recdata[4:8])[0]
			s_args = struct.unpack('<i', recdata[8:0xc])[0]
			s_types = struct.unpack('<i', recdata[0xc:0x10])[0]

			for i in range(n_args, 0, -1):
				off1 = struct.unpack('<L',recdata[s_args+i*4-4:s_args+i*4])[0]
				off2 = struct.unpack('<L',recdata[s_args+i*4:s_args+i*4+4])[0]
				argtype = struct.unpack('<L',recdata[s_types + (n_args-i)*4:s_types + (n_args-i)*4+4])[0]
				argtxt = "%04x"%argtype
				argvalue = d2hex(recdata[off1:off2])
				if rdata2 != "":
					if rdata2 == argtxt:
						if cdrloda.has_key(argtype):
							argtxt = cdrloda[argtype]
						s_iter = page.search.append(None,None)
						page.search.set_value(s_iter,0,model.get_string_from_iter(iter))
						page.search.set_value(s_iter,2,"%s [%s %s]"%(rec,argtxt,argvalue))
				else:
					if cdrloda.has_key(argtype):
						argtxt = cdrloda[argtype]
					s_iter = page.search.append(None,None)
					page.search.set_value(s_iter,0,model.get_string_from_iter(iter))
					page.search.set_value(s_iter,2,"%s [%s %s]"%(rec,argtxt,argvalue))
					page.search.set_value(s_iter,3,page.search.iter_n_children(None))

def cmdfind (model,path,iter,(page,data)):
	# in cdr look for leaf chunks only, avoid duplication
	if page.type[0:3] == "CDR" and model.iter_n_children(iter)>0:
		return
	buf = model.get_value(iter,3)
	test = -1
	try:
		while test < len(buf):
			test = buf.find(data,test+1)
			if test != -1:
				s_iter = page.search.append(None,None)
				page.search.set_value(s_iter,0,model.get_string_from_iter(iter))
				page.search.set_value(s_iter,1,test)
				page.search.set_value(s_iter,2,"%04x (%s)"%(test,model.get_value(iter,0)))
				page.search.set_value(s_iter,3,page.search.iter_n_children(None))
			else:
				return
	except:
		pass

def cmp_children (page1, model1, model2, it1, it2, carg):
	for i in range(model1.iter_n_children(it1)):
		iter1 = model1.iter_nth_child(it1,i)
		iter2 = model2.iter_nth_child(it2,i)
		if model1.iter_n_children(iter1) > 0:
			try:
				cmp_children (page1, model1, model2, iter1, iter2, carg)
			except:
				pass
		else:
			data1 = model1.get_value(iter1,3)
			data2 = model2.get_value(iter2,3)
			if len(data1) == len(data2):
				if carg =="*":
					for j in range(len(data1)):
						if ord(data1[j]) != ord(data2[j]):
							s_iter = page1.search.append(None,None)
							page1.search.set_value(s_iter,0,model1.get_string_from_iter(iter1))
							page1.search.set_value(s_iter,1,j)
							page1.search.set_value(s_iter,2,"%04x (%s)"%(j,model1.get_value(iter1,0)))
				else:
					for j in range(len(data1)):
						if ord(data1[j])+carg == ord(data2[j]):
							s_iter = page1.search.append(None,None)
							page1.search.set_value(s_iter,0,model1.get_string_from_iter(iter1))
							page1.search.set_value(s_iter,1,j)
							page1.search.set_value(s_iter,2,"%04x (%s)"%(j,model1.get_value(iter1,0)))
			else:
				s_iter = page1.search.append(None,None)
				page1.search.set_value(s_iter,0,model1.get_string_from_iter(iter1))
				page1.search.set_value(s_iter,1,0)
				page1.search.set_value(s_iter,2,"Size mismatch (%s)"%(model1.get_value(iter1,0)))

def compare (cmd, entry, page1, page2):
	model1 = page1.view.get_model()
	model2 = page2.view.get_model()
	page1.search = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_INT)

	if len(cmd) > 1:
		carg = int(cmd[1:])
	else:
		carg = "*"
		print "Search in progress..."
		treeSelection = page1.view.get_selection()
		tmp, iter1 = treeSelection.get_selected()
		if iter1 != None:
			p = model1.get_path(iter1)
			iter2 = model2.get_iter(p)
			try:
				cmp_children (page1, model1, model2, iter1, iter2, carg)
				page1.show_search("Diff %s"%carg)
			except:
				print "Search failed"
			return

	for i in range(model1.iter_n_children(None)):
		iter1 = model1.iter_nth_child(None,i)
		iter2 = model2.iter_nth_child(None,i)
		if model1.iter_n_children(iter1) > 0:
			try:
				cmp_children (page1, model1, model2, iter1, iter2, carg)
			except:
				pass
		else:
			data1 = model1.get_value(iter1,3)
			data2 = model2.get_value(iter2,3)
			if len(data1) == len(data2):
				if carg =="*":
					for j in range(len(data1)):
						if ord(data1[j]) != ord(data2[j]):
							s_iter = page1.search.append(None,None)
							page1.search.set_value(s_iter,0,model1.get_string_from_iter(iter1))
							page1.search.set_value(s_iter,1,j)
							page1.search.set_value(s_iter,2,"%04x (%s)"%(j,model1.get_value(iter1,0)))
				else:
					for j in range(len(data1)):
						if ord(data1[j])+carg == ord(data2[j]):
							s_iter = page1.search.append(None,None)
							page1.search.set_value(s_iter,0,model1.get_string_from_iter(iter1))
							page1.search.set_value(s_iter,1,j)
							page1.search.set_value(s_iter,2,"%04x (%s)"%(j,model1.get_value(iter1,0)))
			else:
				s_iter = page1.search.append(None,None)
				page1.search.set_value(s_iter,0,model1.get_string_from_iter(iter1))
				page1.search.set_value(s_iter,1,0)
				page1.search.set_value(s_iter,2,"Size mismatch (%s)"%(model1.get_value(iter1,0)))
				
	page1.show_search("Diff %s"%carg)

def parse (cmd, entry, page):
	if cmd[0] == "$":
		pos = cmd.find("@")
		if pos != -1:
			chtype = cmd[1:pos]
			chaddr = cmd[pos+1:]
		else:
			chtype = cmd[1:]
			chaddr = "0"
		print "Command: ",chtype,chaddr
		
		treeSelection = page.view.get_selection()
		model, iter1 = treeSelection.get_selected()
		if iter1 == None:
			page.view.set_cursor_on_cell(0)
			treeSelection = page.view.get_selection()
			model, iter1 = treeSelection.get_selected()
		buf = model.get_value(iter1,3)

		if "ole" == chtype.lower():
			if buf[int(chaddr,16):int(chaddr,16)+8] == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
				ole.ole_open (buf[int(chaddr,16):],page,iter1)
			else:
				print "OLE stream not found at ",chaddr
		elif "b64" == chtype.lower():
			b64decode (page,buf[int(chaddr,16):],iter1)
		elif "cvx" == chtype.lower():
			cvx.parse (page,buf[int(chaddr,16):],iter1)
		elif "esc" == chtype.lower():
			escher.parse (model,buf[int(chaddr,16):],iter1)
		elif "cmx" == chtype.lower():
			cdr.cdr_open (buf[int(chaddr,16):],page,iter1)
		elif "icc" == chtype.lower():
			icc.parse (page,buf[int(chaddr,16):],iter1)
		elif "cdx" == chtype.lower():
			chdraw.open (page,buf[int(chaddr,16):],iter1)
		elif "yep" == chtype.lower():
			yep.parse (page,buf[int(chaddr,16):],iter1)
		elif "yep0" == chtype.lower():
			yep.parse (page,buf[int(chaddr,16):],iter1,0)
			
		elif "emf" == chtype.lower():
			pt = page.type
			page.type = "EMF"
			mf.mf_open (buf[int(chaddr,16):],page,iter1)
			page.type = pt
		elif "pix" == chtype.lower():
#			try:
				off = int(chaddr,16)
				ntype = model.get_value(iter1,1)
				if off:
					iter2 = add_pgiter(page,"Picture","escher","Blip",buf[off:],iter1)
					model.set_value(iter2,1,("escher","odraw","Blip"))
				else:
					model.set_value(iter1,1,("escher","odraw","Blip"))
					page.hd.hv.parent.on_row_activated(page.hd.hv,model.get_path(iter1),None)
#			except:
#				print "Failed to add as a picture"
		elif "dump" == chtype.lower():
			dlg = gtk.FileChooserDialog('Save...', action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons=(gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
			dlg.set_local_only(True)
			resp = dlg.run()
			fname = dlg.get_filename()
			dlg.hide()
			if resp != gtk.RESPONSE_CANCEL:
				nlen = model.get_value(iter1,2)
				if chaddr != 0:
					pos = chaddr.find(":")
					if pos != -1:
						endaddr = chaddr[pos+1:]
						chaddr = chaddr[:pos]
						value = model.get_value(iter1,3)[int(chaddr,16):int(endaddr,16)]
					else:
						value = model.get_value(iter1,3)[int(chaddr,16):]
				else:
					value = model.get_value(iter1,3)[int(chaddr,16):]

				if nlen != None:
					f = open(fname,'wb')
					f.write(value)
					f.close()
				else:
					print "Nothing to save"
		elif "wmf" == chtype.lower() or "apwmf" == chtype.lower():
			pt = page.type
			page.type = chtype.upper()
			mf.mf_open (buf[int(chaddr,16):],page,iter1)
			page.type = pt
		elif "xls" == chtype.lower():
			ch2 = chaddr[1]
			if ch2.isdigit():
				coladdr = ord(chaddr[0].lower()) - 97
				rowaddr = int(chaddr[1:]) - 1
			else:
				coladdr = 26*(ord(chaddr[0].lower()) - 96)+ ord(chaddr[1].lower()) - 97
				rowaddr = int(chaddr[2:]) - 1
			page.search = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_INT)
			model.foreach(xlsfind,(page,rowaddr,coladdr))
			page.show_search("XLS: cell %s"%chaddr)
		elif "rx2" == chtype.lower():
			newL = struct.unpack('>I', buf[int(chaddr,16)+4:int(chaddr,16)+8])[0]
			rx2.parse (model,buf[int(chaddr,16):int(chaddr,16)+newL],0,iter1)
		elif "dib" == chtype.lower():
			iter2 = add_pgiter (page,"[BMP]","",0,dib2bmp(buf[int(chaddr,16):]),iter1)
			model.set_value(iter2,1,("escher","odraw","Blip"))
		elif "pct" == chtype.lower():
			pict.parse (page,buf,iter1)
		elif "zip" == chtype.lower():
			try:
				print int(chaddr,16)
				output = zlib.decompress(buf[int(chaddr,16):])
				add_pgiter (page,"[Decompressed data]","",0,output,iter1)
			except:
				print "Failed to decompress"

	elif cmd[0] == "?":
		ctype = cmd[1]
		carg = cmd[2:]
		# convert line to hex or unicode if required
		data = arg_conv(ctype,carg)
		model = page.view.get_model()
		page.search = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_INT)
		if ctype == 'r' or ctype == 'R':
			model.foreach(recfind,(page,data))
		else:
			model.foreach(cmdfind,(page,data))
		page.show_search(carg)


