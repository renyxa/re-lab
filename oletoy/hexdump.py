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
import gobject
import tree

class hexdump:
	def __init__(self):
		self.vpaned = gtk.VPaned()
		self.data = None
		self.hdmodel, self.hdview, self.hdscrolled, self.hdrend = tree.make_view2()
		self.hbox0 =gtk.HBox()
		self.da = None
		self.hbox0.pack_start(self.hdscrolled)
		self.vpaned.add1(self.hbox0)
		self.hdscrolled.set_size_request(300, 300)
		self.version = None # to support vsdchunks for different versions
		self.width = 0
		self.height = 0
		
		vbox =gtk.VBox()
		hbox1 =gtk.HBox()

		addrlabel = gtk.TextView();
		buffer = addrlabel.get_buffer()
		buffer.create_tag("monospace", font="monospace 10")
		iter_label = buffer.get_iter_at_offset(0)
		buffer.insert_with_tags_by_name(iter_label, "         ","monospace")
		
		hexlabel = gtk.TextView();
		buffer = hexlabel.get_buffer()
		buffer.create_tag("monospace", font="monospace 10")
		iter_label = buffer.get_iter_at_offset(0)
		buffer.insert_with_tags_by_name(iter_label, "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f","monospace")
		
		hbox1.pack_start(addrlabel,False,True,2)
		hbox1.pack_start(hexlabel,False,True,2)
		vbox.pack_start(hbox1,False,True,2)
		
		self.vscroll2 = gtk.ScrolledWindow()
		hbox2 =gtk.HBox()
		self.txtdump_addr = gtk.TextView();
		self.txtdump_hex = gtk.TextView();
		self.txtdump_asc = gtk.TextView();
		self.txtdump_addr.set_editable(False)
#		self.txtdump_hex.set_editable(False)
#		self.txtdump_asc.set_editable(False)
		buffer = self.txtdump_addr.get_buffer()
		buffer.create_tag("monospace", font="monospace 10")
		buffer = self.txtdump_asc.get_buffer()
		buffer.create_tag("monospace", font="monospace 10")
		buffer = self.txtdump_hex.get_buffer()
		buffer.create_tag("monospace", font="monospace 10")
		hbox2.pack_start(self.txtdump_addr, False,True,2)
		hbox2.pack_start(self.txtdump_hex, False,True,2)
		hbox2.pack_start(self.txtdump_asc, True,True,2)
		self.vscroll2.add_with_viewport(hbox2)
		vbox.pack_start(self.vscroll2,True,True,2)
		self.vpaned.add2(vbox)

	def update():
		pass

