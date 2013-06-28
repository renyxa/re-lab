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
import tree,gtk,gobject,zlib
import ole,escher,rx2,cdr,icc,mf,pict,chdraw,yep,cvx
from utils import *
from os.path import expanduser

try:
	import gtksourceview2
except:
	print "gtksourceview2 was not found. Don't try to use 'run' command."

cdrloda = {0xa:"Outl ID",0x14:"Fild ID",0x1e:"Coords",0xc8:"Stlt ID",
					0x2af8:"Polygon",0x3e8:"Name",0x2efe:"Rotation",0x7d0:"Palette",
					0x1f40:"Lens",0x1f45:"Container"}

class CliWindow(gtk.Window):
	def __init__(self, app):
		gtk.Window.__init__(self)
		self.app = app
		self.fname = ""
		open_btn = gtk.Button("Open")
		save_btn = gtk.Button("Save")
		run_btn = gtk.Button("Run")
		self.tb = gtksourceview2.Buffer()
		tv = gtksourceview2.View(self.tb)
		lm = gtksourceview2.LanguageManager()
		lp = lm.get_language("python")
		self.tb.set_highlight_syntax(True)
		self.tb.set_language(lp)
		tv.set_show_line_marks(True)
		tv.set_show_line_numbers(True)
		tv.set_draw_spaces(True)
		tv.set_insert_spaces_instead_of_tabs(True)
		tv.set_tab_width(4)
		s = gtk.ScrolledWindow()
		s.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		s.set_size_request(660,400)
		s.add_with_viewport(tv)
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


