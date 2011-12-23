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

class HexView():
	def __init__(self,data=None,lines=[],offset=0):
		# UI related onjects
		self.parent = None 						# used to pass info for status bar update (change to signal)
		self.hdr = gtk.DrawingArea()	# header with column address and real offset of the cursor
		self.addr = gtk.DrawingArea()	# leftmost column with line addresses
		self.hv = gtk.DrawingArea()		# middle column with the main hex context
		self.av = gtk.DrawingArea()		# right column with ASCII representation
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
		self.lines = lines			# offsets of lines in dump 
		self.maxaddr = 16				# current length of the longest line
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
		self.bklines = []				# previous state of the lines to support one step undo
		self.bkhvlines = []			# previous state of the hvlines to support one step undo
		self.debug = -1					# -1 -- debug off, 1 -- debug on
		
		# connect signals and call some init functions
		self.hv.set_can_focus(True)
		self.hv.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK)
		self.hv.connect("button_press_event",self.on_button_press)
		self.hv.connect("button_release_event",self.on_button_release)
		self.hv.connect ("key-press-event", self.on_key_press)
		self.hv.connect ("key-release-event", self.on_key_release)
		self.hv.connect("expose_event", self.expose)
		self.hv.connect("motion_notify_event",self.on_motion_notify)
		self.vadj.connect("value_changed", self.on_vadj_changed)

		if lines == []:
			self.init_lines()				# init as a standard "all 0x10 wide" lines
		else:
			self.set_maxaddr()


	def on_vadj_changed (self, vadj):
		if int(vadj.value) != self.offnum:
			self.offnum = int(vadj.value)
			self.vadj.upper = len(self.lines)-self.numtl+1
			self.hv.hide()
			self.hv.show()
		return True

	def set_dxdy(self):
		ctx = self.hv.window.cairo_create()
		ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(14)
		ctx.set_line_width(1)
		(xt, yt, wt, ht, dx, dy) = ctx.text_extents("o")
		x,y,width,height = self.hv.allocation
		self.tdx = int(dx)
		self.tht = int(ht+6)
		self.hbox1.set_size_request(self.tdx*9,0)
		self.hbox3.set_size_request(0,self.tht+4)
		self.vadj.upper = len(self.lines)-self.numtl+1
		self.vadj.value = self.offnum

	def init_lines(self):
		for i in range(len(self.data)/16+1):
			self.lines.append((i*16,))
			self.hvlines.append("")
			self.bkhvlines.append("")
		self.lines.append((len(self.data),))

	def set_maxaddr (self):
		# check and update maxaddr to the value of the longest line
		ma = 16
		for i in range(len(self.lines)-1):
			ta = self.lines[i+1][0]-self.lines[i][0]
			if ta > ma:
				ma = ta
		self.maxaddr = ma

	def on_key_release (self, view, event):
		if event.keyval == 65505 or event.keyval == 65506:
			self.kdrag = 0
			self.mtt = None
			self.expose(view,event)

	def on_key_press (self, view, event):
		flag = 0
		expose = 0
		self.mode = ""
		self.shift = 0
		self.prer = self.curr
		self.prec = self.curc
		if event.state == gtk.gdk.SHIFT_MASK:
			if self.kdrag == 0:
				self.sel = (self.curr,self.curc,self.curr,self.curc)
				self.kdrag = 1
		if event.keyval == 65362: # Up
			flag = 1
			self.mode = "c"
			if self.offnum > 0 and self.curr < self.offnum+1:
				self.offnum -= 1
				self.mode = ""
			self.curr -= 1
			if self.curr < 0:
				self.curr = 0
			if self.curr > self.offnum + self.numtl:
				self.curr = self.offnum
			maxc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
			if self.curc > maxc:
				self.curc = maxc
		elif event.keyval == 100: # "d" for debug
			self.debug *= -1
			pass
		elif event.keyval == 65365: # PgUp
			flag = 1
			self.mode = "c"
			self.curr -= (self.numtl+3)
			if self.curr < 0:
				self.curr = 0
			if self.offnum > 0 and self.curr < self.offnum+1:
				self.offnum -= (self.numtl+3)
				self.mode = ""
			if self.offnum < 0:
				self.offnum = 0
			if self.curr > self.offnum + self.numtl:
				self.curr = self.offnum
			maxc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
			if self.curc > maxc:
				self.curc = maxc
		elif event.keyval == 65364: # Down
			flag = 2
			self.mode = "c"
			if self.offnum < len(self.lines)-self.numtl and self.curr >= self.offnum+self.numtl-3:
				self.offnum += 1
				self.mode = ""
			self.curr += 1
			if self.curr > len(self.lines)-2:
				self.curr = len(self.lines)-2
			if self.curr < self.offnum:
				self.curr = self.offnum
			maxc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
			if self.curc > maxc:
				self.curc = maxc
		elif event.keyval == 65366: # PgDn
			flag = 2
			self.mode = "c"
			self.curr += (self.numtl+3)
			if self.curr > len(self.lines)-2:
				self.curr = len(self.lines)-2
			if self.offnum < len(self.lines)-self.numtl and self.curr >= self.offnum+self.numtl-3:
				self.offnum += (self.numtl+3)
				self.mode = ""
			if self.offnum > len(self.lines)-self.numtl:
				self.offnum = len(self.lines)-self.numtl
			if self.curr < self.offnum:
				self.curr = self.offnum
			maxc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
			if self.curc > maxc:
				self.curc = maxc
		elif event.keyval == 65361: # Left
			if self.debug == 1:
				print self.curc,self.curr
			flag = 1
			self.mode = "c"
			self.curc -= 1
			if self.curc < 0:
				if self.curr > 0:
					self.curr -= 1
					self.curc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
					self.mode = ""
				else:
					self.curc = 0
			self.shift = 1
			
			
		elif event.keyval == 65363: # Right
			flag = 1
			self.mode = "c"
			self.curc += 1
			maxc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
			if self.curc > maxc:
				if self.curr < len(self.lines)-2:
					self.curc = 0
					flag = 2
					if self.offnum < len(self.lines)-self.numtl and self.curr >= self.offnum+self.numtl-3:
						self.offnum += 1
					self.curr += 1
					if self.curr > len(self.lines)-2:
						self.curr = len(self.lines)-2
					if self.curr < self.offnum:
						self.curr = self.offnum
					self.mode = ""
				else:
					self.curc = maxc
			self.shift = -1
		elif event.keyval == 65360: # Home
			flag = 1
			self.mode = "c"
			self.shift -= self.curc
			self.curc = 0
			if event.state == gtk.gdk.CONTROL_MASK:
				self.curr = 0
				self.offnum = 0
				self.mode = ""
		elif event.keyval == 65367: # End
			flag = 2
			self.mode = "c"
			self.shift = self.curc
			if event.state == gtk.gdk.CONTROL_MASK:
				self.curr = len(self.lines)-2
				self.offnum = len(self.lines)-self.numtl
				self.mode = ""
			self.curc = self.lines[self.curr+1][0] - self.lines[self.curr][0] -1
			if self.curc == -1:
				self.curc = 0
		elif event.keyval == 65535: # Del
		# join next row to the current one
			self.bklines = []
			self.bkhvlines = []
			self.bklines += self.lines
			self.bkhvlines += self.hvlines
			if self.curr != len(self.lines)-2: # not in the last row
				self.curr += 1
				self.curc = 0
				self.join_string()
				self.curc = self.lines[self.curr][0] - self.lines[self.curr-1][0]
				self.lines.pop(self.curr)
				self.curr -= 1
				self.set_maxaddr()
				self.tdx = -1 # force to recalculate in expose
		elif event.keyval == 65288: # Backspace
		# at start of the row it joins full row to the previous one
		# any other position -- join left part to the previous row
			self.bklines = []
			self.bkhvlines = []
			self.bklines += self.lines
			self.bkhvlines += self.hvlines
			if self.curr > 0:
				self.join_string()
				if self.curc == 0: #  join full row
					self.curc = self.lines[self.curr][0] - self.lines[self.curr-1][0]
					self.lines.pop(self.curr)
					self.curr -= 1
				else:
					self.lines[self.curr][0] += self.curc
					self.curc = 0
				self.set_maxaddr()
				self.tdx = -1 # force to recalculate in expose
				self.sel = None
		elif event.keyval == 65293: # Enter
			# split row, move everything right to the next (new) one pushing everything down
			self.bklines = []
			self.bkhvlines = []
			self.bklines += self.lines
			self.bkhvlines += self.hvlines
			if self.curr < len(self.lines)-1 and self.curc > 0:
				self.split_string()
				self.lines.insert(self.curr+1,(self.lines[self.curr][0]+self.curc,))
				self.set_maxaddr()
				self.curc -= 1
				self.tdx = -1 # force to recalculate in expose
				self.prec = self.curc - 1
				self.sel = None
		elif event.keyval == 97 and event.state == gtk.gdk.CONTROL_MASK: # ^A
			self.sel = 0,0,self.numtl,self.lines[self.numtl-1][0]
		elif event.keyval == 99 and event.state == gtk.gdk.CONTROL_MASK: # ^C
			#FIXME: this doesn't work
			clp = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
			clp.set_text("test")
#			copy selection to clipboard

		elif event.keyval == 122 and event.state == gtk.gdk.CONTROL_MASK: # ^Z
			self.lines = self.bklines
			self.hvlines = self.bkhvlines
			self.set_maxaddr()
			expose = 1
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

		if self.offnum > len(self.lines)-self.numtl:
			self.offnum = len(self.lines)-self.numtl

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
				expose = 1
				y = (r2-self.offnum+1.5)*self.tht # +1
				x = (self.curc*3+11.5)*self.tdx
				
				s = c2 - c1
				if r1 != r2:
					s = self.lines[r2][0] + c2 - self.lines[r1][0]-c1
				self.mtt = x,y,s
				self.parent.calc_status(self.data[self.lines[r1][0]+c1:self.lines[r2][0]+c2],s)


		self.vadj.upper = len(self.lines)-self.numtl+1
		self.vadj.value = self.offnum
		if self.curr != self.prer or self.curc != self.prec:
			expose = 1
		if expose == 1:
			self.expose(view,event)
			
#		to quickly check what keyval value is for any new key I would like to add
#		print event.keyval,event.state
		return True

	def join_string(self):
		# helper to handle 'backspace'
		if self.curc != 0:
			self.split_string()
		ph,pa = self.hvlines[self.curr]
		nh,na = self.hvlines[self.curr-1]
		self.hvlines[self.curr-1] = nh+ph,na+pa
		self.hvlines.pop(self.curr)

	def split_string(self):
		# helper to handle 'enter' and 'delete'
		prehex,preasc = self.hvlines[self.curr]
		lhex = prehex[:self.curc*3]
		rhex = prehex[self.curc*3:]
		lasc = preasc[:self.curc]
		rasc = preasc[self.curc:]
		self.hvlines[self.curr] = lhex,lasc
		self.hvlines.insert(self.curr+1,(rhex,rasc))

	def on_button_release (self, widget, event):
		self.drag = 0
		self.mtt = None
		self.expose(widget,event)

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
			if rownum > len(self.lines)-2:
				rownum = len(self.lines)
			if event.x > self.tdx*10:
				maxc = self.lines[rownum+1] - self.lines[rownum] -1
				if event.x < self.tdx*(10+maxc*3): # hex
					colnum = int((event.x-self.tdx*8.5)/self.tdx/3)
				elif event.x < self.tdx*(11+maxc*4): #ascii
					colnum = int((event.x-self.tdx*(11+maxc*3))/self.tdx)+1
				else:
					colnum = self.lines[rownum][0]
			else:
				colnum = 0
			c2 = colnum
			c1 = self.curc
			if self.curr > rownum:
				r1 = rownum
				r2 = self.curr
				c1 = colnum
				c2 = self.curc
			else:
				r2 = rownum
				r1 = self.curr
				
			if r1 == r2 and c2 < c1:
				c1 = c2
				c2 = self.curc
			self.sel = r1,c1,r2,c2
			s = c2-c1
			if r1 != r2:
				s = self.lines[r2][0]+ c2 - self.lines[r1][0]-c1
			self.mtt = event.x,event.y,s
			if c1 != c1o or c2 != c2o or r1 != r1o or r2 != r2o:
				self.expose(widget,event)
			self.parent.calc_status(self.data[self.lines[r1][0]+c1:self.lines[r2][0]+c2],s)

	def on_button_press (self, widget, event):
		rownum = int((event.y-self.tht-4)/self.tht)+self.offnum
		if event.x > self.tdx*10:
			if event.x < self.tdx*(10+self.maxaddr*3): # hex
				colnum = int((event.x-self.tdx*8.5)/self.tdx/3)
			elif event.x < self.tdx*(11+self.maxaddr*4): #ascii
				colnum = int((event.x-self.tdx*(11+self.maxaddr*3))/self.tdx)
			else:
				colnum = 16
		else:
			colnum = 0
		self.prer = self.curr
		self.prec = self.curc
		self.curr = rownum
		self.curc = colnum
		self.sel = None
		self.drag = 1
		self.mode = "c"
		self.expose(widget,event)
		self.hv.grab_focus()

	def get_string(self, num):
		hex = ""
		asc = ""
		if self.hvlines[num] == "":
			for j in range(self.lines[num+1][0]-self.lines[num][0]):
				ch = self.data[self.lines[num][0]+j]
				hex += "%02x "%ord(ch)
				if ord(ch) < 32 or ord(ch) > 126:
					ch = "."
				asc += ch
			self.hvlines[num] = (hex,asc)
		return self.hvlines[num]

	def expose (self, widget, event):
		ctx = self.hv.window.cairo_create()
		ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
		ctx.set_font_size(14)
		ctx.set_line_width(1)
		if self.tdx == -1:
			self.set_dxdy()
		x,y,width,height = self.hv.allocation
		self.numtl = int((height - self.tht-4)/self.tht)+1
		self.hbox2.set_size_request(max(width-self.tdx*(10+self.maxaddr*3),0),0)
		if self.numtl >= len(self.lines):
			self.vs.hide()
		else:
			self.vs.show()
		if width >= self.tdx*(9+self.maxaddr*3):
			self.hs.hide()
		else:
			self.hs.show()

		if self.mode == "c":
			# clear prev hdr cursor
			ctx.set_source_rgb(0.9,0.9,0.9)
			ctx.move_to(self.tdx*(10+self.prec*3),self.tht+1.5)
			ctx.line_to(self.tdx*(12+self.prec*3),self.tht+1.5)
			ctx.stroke()
			# clear prev hdr address
			ctx.rectangle(self.tdx*(11+self.maxaddr*3),0,self.tdx*8,self.tht+1.5)
			ctx.fill()
			# draw new hdr cursor
			ctx.set_source_rgb(0,0,0.8)
			ctx.move_to(self.tdx*(10+self.curc*3),self.tht+1.5)
			ctx.line_to(self.tdx*(12+self.curc*3),self.tht+1.5)
			ctx.stroke()
			
			#draw haddr
			haddr = "%02x"%(self.lines[self.curr][0]+self.curc)
			ctx.move_to(self.tdx*(11+self.maxaddr*3),self.tht)
			ctx.show_text(haddr)

			#clear old and new hex and asc
			if self.debug == 1:
				print "mode c",self.prer,self.prec,self.curr,self.curc,self.offnum,self.maxaddr,self.lines[self.prer]
			if self.prer-self.offnum > -1:
				ctx.set_source_rgb(1,1,1)
				if self.sel:
					if self.sel[0] == self.sel[2]:
						if self.prer == self.sel[0] and self.prec >= self.sel[1] and self.prec < self.sel[3]:
							ctx.set_source_rgb(0.7,0.9,0.8)
					else:
						#1st row
						if self.prer == self.sel[0]:
							if self.prec >= self.sel[1] and self.prec <= self.lines[self.prer][0]:
								ctx.set_source_rgb(0.7,0.9,0.8)
						elif self.prer == self.sel[2]:
							if self.prec < self.sel[3]:
								ctx.set_source_rgb(0.7,0.9,0.8)
						elif self.prer > self.sel[0] and self.prer < self.sel[2]:
							ctx.set_source_rgb(0.7,0.9,0.8)
				if self.prec > -1 and self.prec < (self.lines[self.prer+1][0]-self.lines[self.prer][0]):
					# old hex char
					ctx.rectangle(self.tdx*(10+3*self.prec),(self.prer-self.offnum+1)*self.tht+6.5,self.tdx*2+1,self.tht)
					# old asc char
					ctx.rectangle(self.tdx*(11+self.prec+3*self.maxaddr),(self.prer-self.offnum+1)*self.tht+6,self.tdx+1,self.tht+1.5)
					ctx.fill()
				ctx.set_source_rgb(0,0,0)
				if self.prec > -1 and self.prec < (self.lines[self.prer+1][0]-self.lines[self.prer][0]):
					# location of hex
					ctx.move_to(self.tdx*(10+3*self.prec),(self.prer-self.offnum+2)*self.tht+4)
					ctx.show_text("%02x "%ord(self.data[self.lines[self.prer][0]+self.prec]))
				# location of asc
					ctx.move_to(self.tdx*(11+self.prec+3*self.maxaddr),(self.prer-self.offnum+2)*self.tht+4)
					ch = self.data[self.lines[self.prer][0]+self.prec]
					if ord(ch) < 32 or ord(ch) > 126:
						ch = "."
					ctx.show_text(ch)

			if self.curr-self.offnum > -1:
				ctx.rectangle(self.tdx*(10+3*self.curc),(self.curr-self.offnum+1)*self.tht+6.5,self.tdx*2+1,self.tht)
				ctx.set_source_rgb(1,1,1)
				if self.sel:
					if self.sel[0] == self.sel[2]:
						if self.curr == self.sel[0] and self.curc >= self.sel[1] and self.curc < self.sel[3]:
							ctx.set_source_rgb(0.7,0.9,0.8)
					else:
						#1st row
						if self.curr == self.sel[0]:
							if self.curc >= self.sel[1] and self.curc <= self.lines[self.curr][0]:
								ctx.set_source_rgb(0.7,0.9,0.8)
						elif self.curr == self.sel[2]:
							if self.curc < self.sel[3]:
								ctx.set_source_rgb(0.7,0.9,0.8)
						elif self.curr > self.sel[0] and self.curr < self.sel[2]:
							ctx.set_source_rgb(0.7,0.9,0.8)
				ctx.fill()
				ctx.rectangle(self.tdx*(11+self.curc+3*self.maxaddr),(self.curr-self.offnum+1)*self.tht+6,self.tdx,self.tht+1)
				ctx.set_source_rgb(0.75,0.75,1)
				ctx.fill()
				ctx.set_source_rgb(0,0,1)
				ctx.move_to(self.tdx*(10+3*self.curc),(self.curr-self.offnum+2)*self.tht+4)
				ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
				ctx.show_text("%02x "%ord(self.data[self.lines[self.curr][0]+self.curc]))
				ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
				ctx.set_source_rgb(0,0,0)
				ctx.move_to(self.tdx*(11+self.curc+3*self.maxaddr),(self.curr-self.offnum+2)*self.tht+4)
				ch = self.data[self.lines[self.curr][0]+self.curc]
				if ord(ch) < 32 or ord(ch) > 126:
					ch = "."
				ctx.show_text(ch)

			if self.prer != self.curr: # need to clear/draw addr
				if self.prer-self.offnum > -1:
					ctx.rectangle(0,(self.prer-self.offnum+1)*self.tht+4,self.tdx*8,self.tht)
					ctx.set_source_rgb(1,1,1)
					ctx.fill()
					ctx.set_source_rgb(0,0,0)
					ctx.move_to(0,(self.prer-self.offnum+2)*self.tht+4)
					ctx.show_text("%08x"%(self.lines[self.prer][0]))
				if self.curr-self.offnum > -1:
					ctx.rectangle(0,(self.curr-self.offnum+1)*self.tht+4,self.tdx*8,self.tht)
					ctx.set_source_rgb(1,1,1)
					ctx.fill()
					ctx.set_source_rgb(0,0,0.8)
					ctx.move_to(0,(self.curr-self.offnum+2)*self.tht+4)
					ctx.show_text("%08x"%(self.lines[self.curr][0]))
					
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
				ctx.set_source_rgba(0.9,0.95,0.95,0.85)
				ctx.fill()
				ctx.set_source_rgb(0.5,0,0)
				ctx.move_to(self.mtt[0],self.mtt[1]-6) #-6
				ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
				ctx.show_text("%d"%self.mtt[2])
				ctx.select_font_face("Monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

		else:
			# clear top address lane
			ctx.rectangle(0,0,width,self.tht+4)
			ctx.set_source_rgb(0.9,0.9,0.9)
			ctx.fill()
			# clear everything else
			ctx.rectangle(0,self.tht+4,width,height)
			ctx.set_source_rgb(1,1,1)
			ctx.fill()
			# draw lines
			ctx.set_source_rgb(0,0,0)
			ctx.move_to(self.tdx*9+0.5,0)
			ctx.line_to(self.tdx*9+0.5,height)
			ctx.move_to(self.tdx*(10+self.maxaddr*3)+0.5,0)
			ctx.line_to(self.tdx*(10+self.maxaddr*3)+0.5,height)
			ctx.stroke()
			
			if self.sel and (self.sel[0] >= self.offnum and self.sel[0] <= self.offnum + self.numtl):
				if self.sel[0] == self.sel[2]: # one row
					ctx.rectangle(self.tdx*(10+self.sel[1]*3),self.tht*(self.sel[0]+1-self.offnum)+6.5,self.tdx*(self.sel[3]-self.sel[1])*3-self.tdx,self.tht)
					ctx.rectangle(self.tdx*(11+self.sel[1]+self.maxaddr*3),self.tht*(self.sel[0]+1-self.offnum)+6,self.tdx*(self.sel[3]-self.sel[1]),self.tht+1.5)
				else:
					# 1st sel row
					ctx.rectangle(self.tdx*(10+self.sel[1]*3),self.tht*(self.sel[0]+1-self.offnum)+6.5,self.tdx*(self.lines[self.sel[0]+1][0]-self.lines[self.sel[0]][0]-self.sel[1])*3-self.tdx,self.tht)
					ctx.rectangle(self.tdx*(11+self.sel[1]+self.maxaddr*3),self.tht*(self.sel[0]+1-self.offnum)+6,self.tdx*(self.lines[self.sel[0]+1][0]-self.lines[self.sel[0]][0]-self.sel[1]),self.tht+1.5)
					# middle rows
					for i in range(self.sel[2]-self.sel[0]-1):
						ctx.rectangle(self.tdx*10,self.tht*(self.sel[0]+i+2-self.offnum)+6.5,self.tdx*(self.lines[self.sel[0]+i+2][0]-self.lines[self.sel[0]+i+1][0])*3-self.tdx,self.tht)
						ctx.rectangle(self.tdx*(11+self.maxaddr*3),self.tht*(self.sel[0]+i+2-self.offnum)+6,self.tdx*(self.lines[self.sel[0]+i+2][0]-self.lines[self.sel[0]+i+1][0]),self.tht+1.5)
					# last sel row
					ctx.rectangle(self.tdx*10,self.tht*(self.sel[2]+1-self.offnum)+6.5,self.tdx*self.sel[3]*3-self.tdx,self.tht)
					ctx.rectangle(self.tdx*(11+self.maxaddr*3),self.tht*(self.sel[2]+1-self.offnum)+6,self.tdx*self.sel[3],self.tht+1.5)
				ctx.set_source_rgb(0.7,0.9,0.8)
				ctx.fill()
#hdr
			hdr = ""
			ctx.move_to(self.tdx*(10+self.curc*3),self.tht+1.5)
			ctx.line_to(self.tdx*(12+self.curc*3),self.tht+1.5)
			ctx.set_source_rgb(0,0,0.8)
			ctx.stroke()
			ctx.set_source_rgb(0,0,0)

			for i in range(self.maxaddr):
				hdr += "%02x "%i
			ctx.move_to(self.tdx*10,self.tht)
			ctx.show_text(hdr)
			ctx.set_source_rgb(0,0,0.8)
			haddr = "%02x"%(self.lines[self.curr][0]+self.curc)
			ctx.move_to(self.tdx*(11+self.maxaddr*3),self.tht)
			ctx.show_text(haddr)
			ctx.set_source_rgb(0,0,0)
#addr 
			for i in range(min(len(self.lines)-self.offnum-1,self.numtl)):
				ctx.move_to(0,(i+2)*self.tht+4)
				if i == self.curr-self.offnum:
					ctx.set_source_rgb(0,0,0.8)
				ctx.show_text("%08x"%(self.lines[i+self.offnum][0]))
				ctx.set_source_rgb(0,0,0)
# hex/asc  part
			for i in range(min(len(self.lines)-self.offnum-1,self.numtl)):
				ctx.set_source_rgb(0,0,0)
				hex,asc = self.get_string(i+self.offnum)
				if self.debug == 1:
					print "mode 0",i,len(self.lines)-self.offnum-1,self.numtl,asc

				ctx.move_to(self.tdx*10,(i+2)*self.tht+4)
				ctx.show_text(hex)
				ctx.move_to(self.tdx*(10+1+self.maxaddr*3),self.tht*(i+2)+4)
				ctx.show_text(asc)
			self.mode = "c"
			self.expose(widget, event)

		self.mode = ""

		return False
