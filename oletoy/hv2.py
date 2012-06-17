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

import gtk
import cairo
import struct
import os


class HexView():
	def __init__(self,data="",offset=0):
		# UI related objects
		self.parent = None 						# used to pass info for status bar update (change to signal)
		self.iter = None 							# to store iter for saving modifications
		self.hv = gtk.DrawingArea()		# middle column with the main hex context
		self.vadj = gtk.Adjustment(0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
		self.hadj = gtk.Adjustment(0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
		self.vs = gtk.VScrollbar(self.vadj)
		self.hs = gtk.HScrollbar(self.hadj)
		self.hbox1 = gtk.HBox()
		self.hbox2 = gtk.HBox()
		self.hbox3 = gtk.HBox()
		self.table = gtk.Table(3,4,False)
		self.table.attach(self.hv,0,3,0,2)
		self.table.attach(self.hbox1,0,1,2,3,0,0)
		self.table.attach(self.hs,1,2,2,3,gtk.EXPAND|gtk.FILL,0)
		self.table.attach(self.hbox2,2,3,2,3,0,0)
		self.table.attach(self.hbox3,3,4,0,1,0,0)
		self.table.attach(self.vs,3,4,1,2,0)

		# variables to store things
		self.data = data				# data presented in the widget
		self.offset = offset		# current cursor offset
		self.offnum = 0					# offset in lines
		self.tdx = -1						# width of one glyph
		self.tht = 0						# height of one glyph
		self.numtl = 0					# number of lines
		self.hvlines = []				# cached text of lines
		self.selr = None
		self.selc = None
		self.drag = 0						# flag to track if we drag something
		self.kdrag = 0					# flag to reinit selection if shift was released/pressed
		self.curr = 0						# current row
		self.curc = 0						# current column
		self.mode = ""					# flag to jump to the current scrollbar offset or scroll back to hv cursor
		self.prer = 0						# previous row
		self.prec = 0						# previous column
		self.shift = 0
		self.sel = None					# to keep current selection (rs,cs,re,ce)
		self.mtt = None					# mx, my, num -- to show how many bytes selected
		self.exposed = 0
		self.editmode = 0
		self.edpos = 0
		self.modified = 0
		self.ch = unicode("\xC2\xB7","utf8") # symbol for non-ascii
		self.hl = {} # highligths (offset,len,colour=clr1)
		self.numtl = 0 # number of the lines on the screen

		# connect signals and call some init functions
		self.hv.set_can_focus(True)
		self.hv.set_app_paintable(True)
		self.hv.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK)
		self.hv.connect("button_press_event",self.on_button_press)
		self.hv.connect("button_release_event",self.on_button_release)
		self.hv.connect ("key-press-event", self.on_key_press)
		self.hv.connect ("key-release-event", self.on_key_release)
		self.hv.connect("expose_event", self.expose)
		self.hv.connect("motion_notify_event",self.on_motion_notify)
		self.vadj.connect("value_changed", self.on_vadj_changed)

		# functions to handle kbd input

		self.okp = {
			65362:self.okp_up,
			65365:self.okp_pgup,
			65364:self.okp_down,
			65366:self.okp_pgdn,
			65361:self.okp_left,
			65363:self.okp_right,
			65360:self.okp_home,
			65367:self.okp_end,
			97:self.okp_selall, # ^A for 'select all'
			99:self.okp_copy, # ^C for 'copy'
			101:self.okp_fledit # ^E to flip edit
			}

		self.edmap = {48:0,49:1,50:2,51:3,52:4,53:5,54:6,55:7,56:8,57:9,
			97:10,98:11,99:12,100:13,101:14,102:15}

		self.init_config()
		self.init_lines()


	def init_lines(self):
		self.lines = 1+len(self.data)/16 # number of lines in file
		if len(self.data)%16 != 0:
			self.lines += 1
		
		for i in range(self.lines):
			self.hvlines.append("")



	def init_config(self): # redefine UI/behaviour options from file
		try:
			execfile(os.path.expanduser("~/.oletoy/oletoy.cfg"))
		except:
			self.font = "Monospace"
			self.fontsize = 14
			self.hlclr = 1,1,0.5
			self.hdrclr = 0.9,0.9,0.9
			self.lineclr = 0,0,0
			self.curclr = 0,0,0.8
			self.selclr = 0.7,0.9,0.8,1
			self.aschlclr = 0.75,0.75,1
			self.txtcurclr = 0,0,1
			self.mttclr = 0.9,0.95,0.95,0.85
			self.mttxtclr = 0.5,0,0

	def set_dxdy(self):
		# calculate character extents
		ctx = self.hv.window.cairo_create()
		ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(self.fontsize)
		ctx.set_line_width(1)
		(xt, yt, wt, ht, dx, dy) = ctx.text_extents("o")
		x,y,width,height = self.hv.allocation
		self.tdx = int(dx)
		self.tht = int(ht+6)
		self.hbox1.set_size_request(self.tdx*9,0)
		self.hbox3.set_size_request(0,self.tht+4)
		self.vadj.upper = self.lines-self.numtl+1
		self.vadj.value = self.offnum

	def get_string(self, num):
		hex = ""
		asc = ""
		slen = 16
		if num == self.lines -2 and len(self.data)%16 !=0:
			slen = len(self.data)%16
		if self.hvlines[num] == "":
			for j in range(slen):
				ch = self.data[num*16+j]
				hex += "%02x "%ord(ch)
				if ord(ch) < 32 or ord(ch) > 126:
					ch = self.ch
				asc += ch
			self.hvlines[num] = (hex,asc)
		return self.hvlines[num]

	def line_size(self,row):
		# returns size of line or -1 if 'row' is behind
		# acceptable range
		if row < self.lines-2:
			return 16
		elif row == self.lines-2:
			return len(self.data)%16
		else:
			return -1

	def okp_fledit(self,event):
		if event.state == gtk.gdk.CONTROL_MASK:
			if self.editmode:
				self.editmode = 0
				self.parent.update_data()
			else:
				self.editmode = 1
			self.expose(None,event)

	def okp_selall(self,event):
		if event.state == gtk.gdk.CONTROL_MASK:
			self.sel = 0,0,self.lines-2,len(self.data)%16
			self.expose(None,event)

	def okp_copy(self,event):
			#	copy selection to clipboard
			if event.state == gtk.gdk.CONTROL_MASK and self.sel:
				clp = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
				r1,c1,r2,c2 = self.sel
				if r1 == r2:
					text = self.hvlines[r1][0][c1*3:c2*3]
				else:
					text = self.hvlines[r1][0][c1*3:] + "\n"
					for i in range(min(r2-r1-1,self.lines-2)):
						text += self.hvlines[r1+i+1][0] + "\n"
					text += self.hvlines[r2][0][:c2*3]
				clp.set_text(text)
				clp.store()

	def okp_edit(self,event):
		if self.editmode:
			pos = self.curr*16+self.curc
			v = ord(self.data[pos])
			self.modified = 1
			if self.edpos == 0:
				v1 = self.edmap[event.keyval]*16+(v&0xF)
				self.edpos = 1
				self.data = self.data[:pos]+chr(v1)+self.data[pos+1:]
				self.hvlines[self.curr] = ""
				self.get_string(self.curr)
				self.exposed = 1
			else:
				v1 = (v&0xF0)+self.edmap[event.keyval]
				self.edpos = 0
				self.data = self.data[:pos]+chr(v1)+self.data[pos+1:]
				self.hvlines[self.curr] = ""
				self.get_string(self.curr)
				if pos != len(self.data)-1:
					self.okp_right(event)
				else:
					self.hv.hide()
					self.hv.show()



	def okp_left(self,event):
		self.mode = "c"
		self.curc -= 1
		if self.curc < 0:
			if self.curr > 0:
				self.curr -= 1
				self.curc = 15
				self.mode = ""
			else:
				self.curc = 0
		self.shift = 1
		return 1

	def okp_right(self,event):
		self.mode = "c"
		self.curc += 1
		if self.curr == self.lines -2:
			maxc = len(self.data)%16 - 1
			if maxc != 0 and self.curc > maxc:
				self.curc = maxc
		elif self.curc > 15:
			if self.curr < self.lines-2:
				self.curc = 0
				flag = 2
				if self.offnum < self.lines-self.numtl and self.curr >= self.offnum+self.numtl-3:
					self.offnum += 1
				self.curr += 1
				if self.curr > self.lines-2:
					self.curr = self.lines-2
				if self.curr < self.offnum:
					self.curr = self.offnum
				self.mode = ""
			else:
				self.curc = 15
		self.shift = -1
		return 1

#-----------------------

	def okp_up(self,event):
		self.mode = "c"
		if self.offnum > 0 and self.curr < self.offnum+1:
			self.offnum -= 1
			self.mode = ""
		self.curr -= 1
		if self.curr < 0:
			self.curr = 0
		if self.curr > self.offnum + self.numtl:
			self.curr = self.offnum
		maxc = 15
		if self.curc > maxc:
			self.curc = maxc
		return 1

	def okp_pgup(self,event):
		self.mode = "c"
		self.curr -= (self.numtl-2)
		if self.curr < 0:
			self.curr = 0
		if self.offnum > 0 and self.curr < self.offnum+1:
			self.offnum -= (self.numtl-2)
			self.mode = ""
		if self.offnum < 0:
			self.offnum = 0
		if self.curr > self.offnum + self.numtl:
			self.curr = self.offnum
		maxc = 15
		if self.curc > maxc:
			self.curc = maxc
		return 1

	def okp_down(self,event):
		self.mode = "c"
		if self.offnum < self.lines-self.numtl and self.curr >= self.offnum+self.numtl-3:
			self.offnum += 1
			self.mode = ""
		self.curr += 1
		if self.curr > self.lines-2:
			self.curr = self.lines-2
		if self.curr < self.offnum:
			self.curr = self.offnum
		maxc = 15
		if self.curr == self.lines -2 and len(self.data)%16 != 0:
			maxc = len(self.data)%16 -1
		if self.curc > maxc:
			self.curc = maxc
		return 2

	def okp_pgdn(self,event):
		self.mode = "c"
		self.curr += (self.numtl-2)
		if self.curr > self.lines-2:
			self.curr = self.lines-2
		if self.offnum < self.lines-self.numtl and self.curr >= self.offnum+self.numtl-3:
			self.offnum += (self.numtl-2)
			self.mode = ""
		if self.offnum > self.lines-self.numtl:
			self.offnum = self.lines-self.numtl
		if self.curr < self.offnum:
			self.curr = self.offnum
		maxc = 15
		if self.curr == self.lines-2 and len(self.data)%16 != 0:
			maxc = len(self.data)%16 -1
		if self.curc > maxc:
			self.curc = maxc
		return 2

	def okp_home(self,event):
		self.mode = "c"
		self.shift -= self.curc
		self.curc = 0
		if event.state == gtk.gdk.CONTROL_MASK:
			self.curr = 0
			self.offnum = 0
			self.mode = ""
		return 1

	def okp_end(self,event):
		self.mode = "c"
		self.shift = self.curc
		if event.state == gtk.gdk.CONTROL_MASK:
			self.curr = self.lines-2
			self.offnum = self.lines-self.numtl
			self.mode = ""
		self.curc = 15
		if self.curr == self.lines -2 and len(self.data)%16 != 0:
			self.curc = len(self.data)%16 - 1
		return 2


#-----------------------

	def on_motion_notify (self, widget, event):
		if self.drag:
			flag = 0
			if self.sel:
				r1o = self.sel[0]
				c1o = self.sel[1]
				r2o = self.sel[2]
				c2o = self.sel[3]
			else:
				r1o,c1o,r2o,c2o = 0,0,0,0
			rownum = int((event.y-self.tht-4)/self.tht)+self.offnum
			if event.y - self.tht - 4 < 0:
				rownum = self.curr
			if rownum > self.lines-2:
				rownum = self.lines-2
			if event.x > self.tdx*10:
				if event.x < self.tdx*(10+16*3): # hex
					colnum = int(((event.x-self.tdx*9.5)/self.tdx+1.5)/3)
				elif event.x < self.tdx*(11+16*4): #ascii
					colnum = int((event.x-self.tdx*(11+16*3))/self.tdx)+1
				else:
					colnum = self.line_size(rownum)
			else:
				colnum = self.curc
			if colnum > self.line_size(rownum):
				colnum = self.line_size(rownum)
			if colnum < 0:
				colnum = 0
			c2 = colnum
			c1 = self.curc
			if self.curr > rownum:
				r1 = rownum
				r2 = self.curr
				c1 = colnum
				c2 = self.curc+1
			else:
				r2 = rownum
				r1 = self.curr
			if r1 == r2 and c2 <= c1:
				c = c1
				c1 = c2
				c2 = c+1
			self.sel = r1,c1,r2,c2

			s = c2-c1
			if r1 != r2:
				s = (r2-r1)*16 + c2 - c1
			if r2 == self.lines:
				s += len(data)%16
			if s > 0:
				self.mtt = event.x,event.y,s
			else:
				self.mtt = None
			if c1 != c1o or c2 != c2o or r1 != r1o or r2 != r2o:
				self.expose(widget,event)
			self.parent.calc_status(self.data[self.line_size(r1)+c1:self.line_size(r2)+c2],s)


	def on_key_press (self, view, event):
		# handle keyboard input
		flag = 0
		self.exposed = 0
		self.mode = ""
		self.shift = 0
		self.prer = self.curr
		self.prec = self.curc
		if event.state == gtk.gdk.SHIFT_MASK:
			if self.kdrag == 0:
				self.sel = (self.curr,self.curc,self.curr,self.curc)
				self.kdrag = 1
		if (event.keyval>47 and event.keyval<58) or (event.keyval>96 and event.keyval<103 and event.state != gtk.gdk.CONTROL_MASK):
			self.okp_edit(event)
		else:
			self.edpos = 0

		if self.okp.has_key(event.keyval):
			tmp = self.okp[event.keyval](event)
			if tmp:
				flag = tmp

		if self.curr < self.offnum:
			# Left/Right/BS/Enter 												 -- scroll back to cursor   (flag 0)
			# cursor upper than position and Up/PgUp/Home  -- scroll back to cursor   (flag 1)
			# cursor upper than position and Down/PgDn/End -- move cursor to position (flag 2)
			if flag < 2:
				self.offnum = self.curr
			else:
				self.curr = self.offnum
		elif self.curr > self.offnum+self.numtl:
			# Left/Right/BS/Enter 												 -- scroll back to cursor   (flag 0)
			# cursor lower than position and Down/PgDn/End -- scroll back to cursor   (flag 2)
			# cursor lower than position and Up/PgUp/Home  -- move cursor to position (flag 1)
			if flag != 1:
				self.offnum = self.curr
			else:
				self.curr = self.offnum

		if self.offnum > max(self.lines-self.numtl,0):
			self.offnum = self.lines-self.numtl

		if event.state == gtk.gdk.SHIFT_MASK:
			if self.sel != None:
				r1 = self.sel[0]
				r2 = self.sel[2]
				c1 = self.sel[1]
				c2 = self.sel[3]
				if self.curr == self.prer: # in the same line
					if r1 == r2:
						if self.curc > self.prec: # move right
							if c2 <= self.curc:
								c2 = self.curc+1
							else:
								c1 = self.curc
						else: # move left
							if c1 == self.prec:
								c1 = self.curc
							else:
								c2 = self.curc+1
					else:
						if self.curc > self.prec: # move right
							if self.curr == r2: # increase c2
								c2 = self.curc+1
							else:								# increase c1
								c1 = self.curc
						else:
							if self.curr == r2: # decrease c1
								c2 = self.curc+1
							else:								# decrease c2
								c1 = self.curc
				elif self.curr > self.prer: # move down
					if r2 == self.prer:
						r2 = self.curr
						c2 = self.curc+1
					else:
						r1 = self.curr
						c1 = self.curc
				else: # move up
					if r2 == self.prer and r1 != r2:
						r2 = self.curr
						c2 = self.curc+1
					else:
						if r2 <= self.curr:
							c = c2
							c = self.curc
							c1 = c
							r1 = self.curr
						else:
							r1 = self.curr
							c1 = self.curc

				self.sel = r1,c1,r2,c2
				self.mode = ""
				self.exposed = 1
				y = (r2-self.offnum+1.5)*self.tht # +1
				x = (self.curc*3+11.5)*self.tdx
				
				s = c2 - c1
				if r1 != r2:
					s = (r2-r1)*16 + c2 - c1
				if r2 == self.lines:
					s += len(data)%16
				self.mtt = x,y,s
				self.parent.calc_status(self.data[r1*16+c1:r2*16+c2],s)


		self.vadj.upper = self.lines-self.numtl+1
		self.vadj.value = self.offnum
		if self.curr != self.prer or self.curc != self.prec or self.exposed == 1:
			self.expose(view,event)

#		to quickly check what keyval value is for any new key I would like to add
#		print event.keyval,event.state
		return True



	def on_key_release (self, view, event):
		# part of the data selection from keyboard
		if event.keyval == 65505 or event.keyval == 65506:
			self.kdrag = 0
			self.mtt = None
			self.expose(view,event)

	def on_vadj_changed (self, vadj):
		# vertical scroll line
		if int(vadj.value) != self.offnum:
			self.offnum = int(vadj.value)
			self.vadj.upper = self.lines-self.numtl+1
			self.hv.hide()
			self.hv.show()
		return True


	def on_button_release (self, widget, event):
		self.drag = 0
		self.mtt = None
		self.expose(widget,event)


	def on_button_press (self, widget, event):
		rownum = int((event.y-self.tht-4)/self.tht)+self.offnum
		if event.y - self.tht - 4 < 0:
			rownum = self.curr
		if rownum > self.lines-2:
			rownum = self.lines-2
		if event.x > self.tdx*10:
			if event.x < self.tdx*(10+16*3): # hex
				colnum = int((event.x-self.tdx*9.5)/self.tdx/3)
			elif event.x < self.tdx*(11+16*4): #ascii
				colnum = int((event.x-self.tdx*(12+16*3))/self.tdx)
			else:
				colnum = self.line_size(rownum)-1
		else:
			colnum = self.curc
		if colnum > self.line_size(rownum)-1:
			colnum = self.line_size(rownum)-1
		if colnum < 0:
			colnum = self.curc
		self.prer = self.curr
		self.prec = self.curc
		self.curr = rownum
		self.curc = colnum
		self.sel = None
		self.drag = 1
		self.mode = "c"
		self.expose(widget,event)
		self.hv.grab_focus()

	def ol2quad(self,o,l):
		if o > len(self.data) - 1:
			return -1,0,0,0
		r0 = o/16
		c0 = o%16
		if o+l > len(self.data) -1:
			r1 = self.lines-2
			c1 = len(self.data)%16
			if c1 == 0:
				c1 = 16
		else:
			r1 = (o+l)/16
			c1 = (o+l)%16
			if c1 == 0:
				c1 = 16
				r1 -= 1
		return r0,c0,r1,c1

	def inhl(self,ctx,r,c):
		for i in self.hl:
			hl = self.hl[i]
			r0,c0,r1,c1 = self.ol2quad(hl[0],hl[1])
			if r0 != -1:
				if r0 == r1:
					if r == r0 and c >= c0 and c < c1:
						ctx.set_source_rgba(hl[2],hl[3],hl[4],hl[5])
				else:
					if r == r0:
						if c >= c0 and c <= 15:
							ctx.set_source_rgba(hl[2],hl[3],hl[4],hl[5])
					elif r == r1:
						if c < c1:
							ctx.set_source_rgba(hl[2],hl[3],hl[4],hl[5])
					elif r > r0 and r < r1:
						ctx.set_source_rgba(hl[2],hl[3],hl[4],hl[5])


	def draw_selection(self,ctx,r0,c0,r1,c1,clr=(0.5,0.5,0.5,0.5)):
		if r0 == r1: # one row
			ctx.rectangle(self.tdx*(10+c0*3),self.tht*(r0+1-self.offnum)+6.5,self.tdx*(c1-c0)*3-self.tdx,self.tht)
			ctx.rectangle(self.tdx*(11+c0+16*3),self.tht*(r0+1-self.offnum)+6,self.tdx*(c1-c0),self.tht+1.5)
		else:
			# 1st sel row
			ctx.rectangle(self.tdx*(10+c0*3),self.tht*(r0+1-self.offnum)+6.5,self.tdx*(16-c0)*3-self.tdx,self.tht)
			ctx.rectangle(self.tdx*(11+c0+16*3),self.tht*(r0+1-self.offnum)+6,self.tdx*(16-c0),self.tht+1.5)
			# middle rows
			for i in range(r1-r0-1):
				ctx.rectangle(self.tdx*10,self.tht*(r0+i+2-self.offnum)+6.5,self.tdx*47,self.tht)
				ctx.rectangle(self.tdx*(11+16*3),self.tht*(r0+i+2-self.offnum)+6,self.tdx*16,self.tht+1.5)
			# last sel row
			ctx.rectangle(self.tdx*10,self.tht*(r1+1-self.offnum)+6.5,self.tdx*c1*3-self.tdx,self.tht)
			ctx.rectangle(self.tdx*(11+16*3),self.tht*(r1+1-self.offnum)+6,self.tdx*c1,self.tht+1.5)
		ctx.set_source_rgba(clr[0],clr[1],clr[2],clr[3])
		ctx.fill()

	def draw_edit(self,ctx):
		ctx.move_to(self.tdx*2-2,self.tdx)
		ctx.arc(self.tdx+2,self.tdx,self.tdx/2.,0,6.29)
		ctx.set_source_rgb(0.6,0.6,0.6)
		if self.editmode:
			if self.modified:
				ctx.set_source_rgb(1,0.4,0.4)
			else:
				ctx.set_source_rgb(0.4,1,0.4)
		ctx.fill_preserve()
		ctx.set_source_rgb(0,0,0)
		ctx.stroke()

	def expose(self,widget,event):
		if len(self.data) < 1:
			return
		ctx = self.hv.window.cairo_create()
		ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(self.fontsize)
		ctx.set_line_width(1)
		cmnt_off = (-1,-1)
		if self.tdx == -1:
			self.set_dxdy()
		x,y,width,height = self.hv.allocation
		self.numtl = min(int((height - self.tht-4)/self.tht)+1,self.lines)
		self.hbox2.set_size_request(max(width-self.tdx*(10+16*3),0),0)
		if self.numtl >= self.lines:
			self.vs.hide()
		else:
			self.vs.show()
		if width >= self.tdx*(9+16*3):
			self.hs.hide()
		else:
			self.hs.show()

		if self.mode == "":
			# clear top address lane
			ctx.rectangle(0,0,width,self.tht+4)
			ctx.set_source_rgb(self.hdrclr[0],self.hdrclr[1],self.hdrclr[2])
			ctx.fill()
			# clear everything else
			ctx.rectangle(0,self.tht+4,width,height)
			ctx.set_source_rgb(1,1,1)
			ctx.fill()
			# draw lines
			ctx.set_source_rgb(self.lineclr[0],self.lineclr[1],self.lineclr[2])
			ctx.move_to(self.tdx*9+0.5,0)
			ctx.line_to(self.tdx*9+0.5,height)
			ctx.move_to(self.tdx*(10+16*3)+0.5,0)
			ctx.line_to(self.tdx*(10+16*3)+0.5,height)
			ctx.move_to(self.tdx*(12+16*4)+0.5,0)
			ctx.line_to(self.tdx*(12+16*4)+0.5,height)
			ctx.stroke()

# FIXME! Overpage selection, adopt to all lines the same except last one in some cases
			if self.sel and (self.sel[0] >= self.offnum and self.sel[0] <= self.offnum + self.numtl):
				self.draw_selection(ctx,self.sel[0],self.sel[1],self.sel[2],self.sel[3],self.selclr)
				
			for i in self.hl:
				r0,c0,r1,c1 = self.ol2quad(self.hl[i][0],self.hl[i][1])
				if r0 != -1 and (r0 >= self.offnum and r0 <= self.offnum + self.numtl):
					self.draw_selection(ctx,r0,c0,r1,c1,(self.hl[i][2],self.hl[i][3],self.hl[i][4],self.hl[i][5]))

#hdr
			hdr = ""
			ctx.move_to(self.tdx*(10+self.curc*3),self.tht+1.5)
			ctx.line_to(self.tdx*(12+self.curc*3),self.tht+1.5)
			ctx.set_source_rgb(self.curclr[0],self.curclr[1],self.curclr[2])
			ctx.stroke()
			ctx.set_source_rgb(self.lineclr[0],self.lineclr[1],self.lineclr[2])
			for i in range(16):
				hdr += "%02x "%i
			ctx.move_to(self.tdx*10,self.tht)
			ctx.show_text(hdr)
			ctx.set_source_rgb(self.curclr[0],self.curclr[1],self.curclr[2])
			haddr = "%02x"%(self.curr*16+self.curc)
			ctx.move_to(self.tdx*(11+16*3),self.tht)
			ctx.show_text(haddr)
			ctx.set_source_rgb(self.lineclr[0],self.lineclr[1],self.lineclr[2])
			
#addr 
			for i in range(min(self.lines-self.offnum-1,self.numtl)):
				ctx.move_to(0,(i+2)*self.tht+4)
				if i == self.curr-self.offnum:
					ctx.set_source_rgb(self.curclr[0],self.curclr[1],self.curclr[2])
				ctx.show_text("%08x"%((i+self.offnum)*16))
				ctx.set_source_rgb(self.lineclr[0],self.lineclr[1],self.lineclr[2])
# hex/asc  part
			for i in range(min(self.lines-self.offnum-1,self.numtl)):
				ctx.set_source_rgb(0,0,0)
				hex,asc = self.get_string(i+self.offnum)
				ctx.move_to(self.tdx*10,(i+2)*self.tht+4)
				ctx.show_text(hex)
				ctx.move_to(self.tdx*(10+1+16*3),self.tht*(i+2)+4)
				ctx.show_text(asc)

			self.draw_edit(ctx)

		# clear prev hdr cursor
		ctx.set_source_rgb(self.hdrclr[0],self.hdrclr[1],self.hdrclr[2])
		ctx.move_to(self.tdx*(10+self.prec*3),self.tht+1.5)
		ctx.line_to(self.tdx*(12+self.prec*3),self.tht+1.5)
		ctx.stroke()
		# clear prev hdr address
		ctx.rectangle(self.tdx*(11+16*3),0,self.tdx*8,self.tht+1.5)
		ctx.fill()
		# draw new hdr cursor
		ctx.set_source_rgb(self.curclr[0],self.curclr[1],self.curclr[2])
		ctx.move_to(self.tdx*(10+self.curc*3),self.tht+1.5)
		ctx.line_to(self.tdx*(12+self.curc*3),self.tht+1.5)
		ctx.stroke()
		
		#draw haddr
		haddr = "%02x"%(self.curr*16+self.curc)
		ctx.move_to(self.tdx*(11+16*3),self.tht)
		ctx.show_text(haddr)

		#clear old and new hex and asc
		if self.prer-self.offnum > -1:
			ctx.set_source_rgb(1,1,1)
			
			if self.sel:
				if self.sel[0] == self.sel[2]:
					if self.prer == self.sel[0] and self.prec >= self.sel[1] and self.prec < self.sel[3]:
						ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
				else:
					#1st row
					if self.prer == self.sel[0]:
						if self.prec >= self.sel[1] and self.prec <= 15:
							ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
					elif self.prer == self.sel[2]:
						if self.prec < self.sel[3]:
							ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
					elif self.prer > self.sel[0] and self.prer < self.sel[2]:
						ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])

			if len(self.hl)> 0:
				self.inhl(ctx,self.prer,self.prec)

			if self.prec > -1 and self.prec < 16:
				# old hex char
				ctx.rectangle(self.tdx*(10+3*self.prec),(self.prer-self.offnum+1)*self.tht+6.5,self.tdx*2+1,self.tht)
				# old asc char
				ctx.rectangle(self.tdx*(11+self.prec+3*16),(self.prer-self.offnum+1)*self.tht+6,self.tdx+1,self.tht+1.5)
				ctx.fill()
			ctx.set_source_rgb(0,0,0)
			if self.prec > -1 and self.prec < 16:
				# location of hex
				ctx.move_to(self.tdx*(10+3*self.prec),(self.prer-self.offnum+2)*self.tht+4)
				ctx.show_text("%02x "%ord(self.data[self.prer*16+self.prec]))
				# location of asc
				ctx.move_to(self.tdx*(11+self.prec+3*16),(self.prer-self.offnum+2)*self.tht+4)
				ch = self.data[self.prer*16+self.prec]
				if ord(ch) < 32 or ord(ch) > 126:
					ch = self.ch
				ctx.show_text(ch)

		if self.curr-self.offnum > -1:
			ctx.rectangle(self.tdx*(10+3*self.curc),(self.curr-self.offnum+1)*self.tht+6.5,self.tdx*2+1,self.tht)
			ctx.set_source_rgb(1,1,1)
			if self.sel:
				if self.sel[0] == self.sel[2]:
					if self.curr == self.sel[0] and self.curc >= self.sel[1] and self.curc < self.sel[3]:
						ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
				else:
					#1st row
					if self.curr == self.sel[0]:
						if self.curc >= self.sel[1] and self.curc <= self.line_size(self.curr):
							ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
					elif self.curr == self.sel[2]:
						if self.curc < self.sel[3]:
							ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
					elif self.curr > self.sel[0] and self.curr < self.sel[2]:
						ctx.set_source_rgb(self.selclr[0],self.selclr[1],self.selclr[2])
			if len(self.hl)> 0:
				self.inhl(ctx,self.curr,self.curc)

			ctx.fill()
			ctx.rectangle(self.tdx*(11+self.curc+3*16),(self.curr-self.offnum+1)*self.tht+6,self.tdx,self.tht+1)
			ctx.set_source_rgb(self.aschlclr[0],self.aschlclr[1],self.aschlclr[2])
			ctx.fill()
			ctx.set_source_rgb(self.txtcurclr[0],self.txtcurclr[1],self.txtcurclr[2])
			ctx.move_to(self.tdx*(10+3*self.curc),(self.curr-self.offnum+2)*self.tht+4)
			ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
			ctx.show_text("%02x "%ord(self.data[self.curr*16+self.curc]))
			ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
			ctx.set_source_rgb(0,0,0)
			ctx.move_to(self.tdx*(11+self.curc+3*16),(self.curr-self.offnum+2)*self.tht+4)
			ch = self.data[self.curr*16+self.curc]
			if ord(ch) < 32 or ord(ch) > 126:
				ch = self.ch
			ctx.show_text(ch)

		if self.prer != self.curr: # need to clear/draw addr
			if self.prer-self.offnum > -1:
				ctx.rectangle(0,(self.prer-self.offnum+1)*self.tht+4,self.tdx*8,self.tht)
				ctx.set_source_rgb(1,1,1)
				ctx.fill()
				ctx.set_source_rgb(0,0,0)
				ctx.move_to(0,(self.prer-self.offnum+2)*self.tht+4)
				ctx.show_text("%08x"%(self.prer*16))
			if self.curr-self.offnum > -1:
				ctx.rectangle(0,(self.curr-self.offnum+1)*self.tht+4,self.tdx*8,self.tht)
				ctx.set_source_rgb(1,1,1)
				ctx.fill()
				ctx.set_source_rgb(self.curclr[0],self.curclr[1],self.curclr[2])
				ctx.move_to(0,(self.curr-self.offnum+2)*self.tht+4)
				ctx.show_text("%08x"%(self.curr*16))

# math.floor(math.log10(self.mtt[2])
		if self.mtt:
			sh = 0
			if self.mtt[2] > 9999:
				sh = 4
			elif self.mtt[2] > 999:
				sh = 3
			elif self.mtt[2] > 99:
				sh = 2
			elif self.mtt[2] > 9:
				sh = 1

			ctx.rectangle(self.mtt[0]-self.tdx*0.5,self.mtt[1]-self.tht-6,self.tdx*(2+sh),self.tht+4) #-6
			ctx.set_source_rgba(self.mttclr[0],self.mttclr[1],self.mttclr[2],self.mttclr[3])
			ctx.fill()
			ctx.set_source_rgb(self.mttxtclr[0],self.mttxtclr[1],self.mttxtclr[2])
			ctx.move_to(self.mtt[0],self.mtt[1]-6) #-6
			ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
			ctx.show_text("%d"%self.mtt[2])
			ctx.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

		self.mode = ""

		return True
