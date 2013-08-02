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

import gobject
import gtk, pango

def drag_data_received_cb(view, context, x, y, selection, info, etime):
      model = view.get_model()
      drop_info = view.get_dest_row_at_pos(x, y)
      if drop_info:
         path, position = drop_info
         iter = model.get_iter(path)
         if (position == gtk.TREE_VIEW_DROP_BEFORE
            or position == gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
             niter = model.insert_before(iter, None)
         else:
            niter = model.insert_after(iter, None)
      else:
          niter = model.append(None)
      if context.action == gtk.gdk.ACTION_MOVE:
          context.finish(True, True, etime)
          model.set(niter,3,selection.data)
      return


def drag_data_get_data(view, context, selection, target_id, etime):
   treeselection = view.get_selection()
   model, iter = treeselection.get_selected()
   data = model.get_value(iter, 3)
   selection.set(selection.target, 8, data)

def make_view():
   # Create the model.
   model = gtk.TreeStore(
    gobject.TYPE_STRING,    # Name
    gobject.TYPE_PYOBJECT,  # Type
    gobject.TYPE_INT,       # Length
    gobject.TYPE_PYOBJECT,  # Value
    gobject.TYPE_PYOBJECT,  # Value2 (peer path for YEP)
    gobject.TYPE_STRING,    # Colour
    gobject.TYPE_STRING,    # Path
    gobject.TYPE_STRING,    # VSD_Stream_Format
    gobject.TYPE_PYOBJECT,  # Command
    gobject.TYPE_STRING     # Tooltip
    )
    
   # Create the view itself.
   view = gtk.TreeView(model)
   view.set_reorderable(True)
#   view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,[("oletoy",gtk.TARGET_SAME_APP,1974)],gtk.gdk.ACTION_DEFAULT|gtk.gdk.ACTION_MOVE)
#   view.enable_model_drag_dest([("oletoy",gtk.TARGET_SAME_APP,1974)],gtk.gdk.ACTION_DEFAULT)
#   view.connect("drag-data-received", drag_data_received_cb)
#   view.connect("drag_data_get", drag_data_get_data)
   view.columns_autosize()
   view.set_enable_tree_lines(True)
   cell = gtk.CellRendererText()
   cell.set_property('family-set',True)
   cell.set_property('font','monospace 10')

   cell1 = gtk.CellRendererText()
   cell1.set_property('family-set',True)
   cell1.set_property('font','monospace 10')
   cell1.set_property('xalign',1)

   cell2 = gtk.CellRendererText()
   cell2.set_property('family-set',True)
   cell2.set_property('font','monospace 8')
  
#   renderer.family="monospace"
   column0 = gtk.TreeViewColumn('Record', cell, text=0,background=5)
   column1 = gtk.TreeViewColumn('Type', cell1, text=7)
   column2 = gtk.TreeViewColumn('Path', cell2, text=6)
   column3 = gtk.TreeViewColumn('Length', cell, text=2)

   view.append_column(column0)
   view.append_column(column1)
   view.append_column(column2)
   view.append_column(column3)
   view.show()
   # Create scrollbars around the view.
   scrolled = gtk.ScrolledWindow()
   scrolled.add(view)
   scrolled.set_size_request(400,400)
   scrolled.show()
   return model,view,scrolled

def make_view2():
   # Create the model.  Name/Value/Offset/Length/Format/(optional) 2nd Offset/2nd Len/Tip
   model = gtk.TreeStore(
    gobject.TYPE_STRING,    # Name
    gobject.TYPE_STRING,    # Value
    gobject.TYPE_INT,       # Offset
    gobject.TYPE_INT,       # Length
    gobject.TYPE_STRING,    # Format
    gobject.TYPE_INT,       # 2nd Offset
    gobject.TYPE_INT,       # 2nd Length
    gobject.TYPE_PYOBJECT,  # Path to fild/outl in CDR
    gobject.TYPE_STRING     # Tooltip
    )
   # Create the view itself.
   view = gtk.TreeView(model)
   view.set_enable_tree_lines(True)
   renderer = gtk.CellRendererText()
   renderer2 = gtk.CellRendererText()
   renderer3 = gtk.CellRendererText()
   renderer2.set_property('editable', True)
   column = gtk.TreeViewColumn('Name', renderer, text=0)
   column2 = gtk.TreeViewColumn('Value', renderer2, text=1)
   view.append_column(column)
   view.append_column(column2)
   view.show()
   view.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
   # Create scrollbars around the view.
   scrolled = gtk.ScrolledWindow()
   scrolled.add(view)
   scrolled.set_size_request(250,300)
   #scrolled.show()
   hpaned = gtk.HPaned()
   hpaned.add1(scrolled)
   hpaned.show()  # was scrolled
   return model,view,hpaned,renderer2


def tree_append(model,parent,name,data,dtype,dlen):
    folder = { "name": name, "part": data, "partT": dtype, "partL": dlen}
    iter = model.insert_before(parent, None)
    model.set_value(iter, 0, folder)
    model.set_value(iter, 1, folder["name"])
    model.set_value(iter, 2, folder["partL"])
    return iter

