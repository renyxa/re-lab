# Copyright (C) 2007,2010,2011	Valek Filippov (frob@df.ru)
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

import gtk
import tree
import hv2
import utils

class hexdump:
	def __init__(self):
		self.vpaned = gtk.VPaned()
		self.model, self.hdview, self.hdscrolled, self.hdrend = tree.make_view2()
		self.hbox0 =gtk.HBox()
		self.da = None
		self.hbox0.pack_start(self.hdscrolled)
		self.vpaned.add1(self.hbox0)
		self.hdscrolled.set_size_request(300, 300)
		self.version = None # to support vsdchunks for different versions
		self.width = 0
		self.height = 0
		self.dispscale = 1.

		self.hv = hv2.HexView()
		self.vpaned.add2(self.hv.table)

	def update():
		pass

	def disp_expose(self,da,event,pixbuf):
		utils.disp_expose(da,event,pixbuf,self.dispscale)

	def disp_on_button_press(self,da,event,pixbuf):
		if event.type  == gtk.gdk.BUTTON_PRESS:
			if event.button == 1:
				self.dispscale *= 1.4
				self.disp_expose(da,event,pixbuf)
			if event.button == 2:
				self.dispscale = 1
				self.da.hide()
				self.da.show()
			if event.button == 3:
				self.dispscale *= .7
				self.da.hide()
				self.da.show()
