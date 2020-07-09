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

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk,Pango, GObject, Gdk

def treeview_copy_row(treeview, srcmodel, source, dstmodel, target, drop_position):
	source_row = srcmodel[source]
	if drop_position == Gtk.TreeViewDropPosition.INTO_OR_BEFORE:
		new = dstmodel.prepend(parent=target, row=source_row)
	elif drop_position == Gtk.TreeViewDropPosition.INTO_OR_AFTER:
		new = dstmodel.append(parent=target, row=source_row)
	elif drop_position == Gtk.TreeViewDropPosition.BEFORE:
		new = dstmodel.insert_before(parent=None, sibling=target, row=source_row)
	elif drop_position == Gtk.TreeViewDropPosition.AFTER:
		new = dstmodel.insert_after(parent=None, sibling=target, row=source_row)

	# Copy any children of the source row
	for n in range(srcmodel.iter_n_children(source)):
		child = srcmodel.iter_nth_child(source, n)
		treeview_copy_row(treeview, srcmodel, child, dstmodel, new, Gtk.TreeViewDropPosition.INTO_OR_BEFORE)


def on_drag_data_received(treeview, drag_context, x, y, selection_data, info, eventtime):
	srcmodel,src = drag_context.get_source_widget().get_selection().get_selected()
	dstmodel = treeview.get_model()
	target_path, drop_position = treeview.get_dest_row_at_pos(x, y)
	dst = dstmodel.get_iter(target_path)

	if dstmodel != srcmodel or not srcmodel.is_ancestor(src, dst):
		treeview_copy_row(treeview, srcmodel, src, dstmodel, dst, drop_position)
		if (drop_position == Gtk.TreeViewDropPosition.INTO_OR_BEFORE
			or drop_position == Gtk.TreeViewDropPosition.INTO_OR_AFTER):
			treeview.expand_row(target_path, open_all=False)
		# Finish the drag and have Gtk+ delete the drag source rows if needed
		if dstmodel == srcmodel:
			# move inside the tree
			drag_context.finish(success=True, del_=True, time=eventtime)
		else:
			# copy between trees
			drag_context.finish(success=True, del_=False, time=eventtime)
	else:
		drag_context.finish(success=False, del_=False, time=eventtime)

def make_view():
	# Create the model.
	model = Gtk.TreeStore(
	GObject.TYPE_STRING,    # Name
	GObject.TYPE_PYOBJECT,  # Type
	GObject.TYPE_INT,       # Length
	GObject.TYPE_PYOBJECT,  # Value
	GObject.TYPE_PYOBJECT,  # Value2 (peer path for YEP)
	GObject.TYPE_STRING,    # Colour
	GObject.TYPE_STRING,    # Path
	GObject.TYPE_STRING,    # VSD_Stream_Format
	GObject.TYPE_PYOBJECT,  # Command
	GObject.TYPE_STRING     # Tooltip
	)
    
	# Create the view itself.
	view = Gtk.TreeView(model)
	view.set_reorderable(True)
	target_entries = [('oletoy', Gtk.TargetFlags.SAME_APP, 0)]
	view.enable_model_drag_source(
		Gdk.ModifierType.BUTTON1_MASK, target_entries, Gdk.DragAction.DEFAULT|Gdk.DragAction.MOVE)
	view.enable_model_drag_dest(target_entries,Gdk.DragAction.DEFAULT)
	view.connect('drag-data-received', on_drag_data_received)

	view.columns_autosize()
	view.set_enable_tree_lines(True)
	cell = Gtk.CellRendererText()
	cell.set_property('family-set',True)
	cell.set_property('font','monospace 10')

	cell1 = Gtk.CellRendererText()
	cell1.set_property('family-set',True)
	cell1.set_property('font','monospace 10')
	cell1.set_property('xalign',1)

	cell2 = Gtk.CellRendererText()
	cell2.set_property('family-set',True)
	cell2.set_property('font','monospace 8')

#	renderer.family="monospace"
	column0 = Gtk.TreeViewColumn('Record', cell, text=0,background=5)
	column1 = Gtk.TreeViewColumn('Type', cell1, text=7)
	column2 = Gtk.TreeViewColumn('Path', cell2, text=6)
	column3 = Gtk.TreeViewColumn('Length', cell, text=2)

	view.append_column(column0)
	view.append_column(column1)
	view.append_column(column2)
	view.append_column(column3)
	view.show()
	# Create scrollbars around the view.
	scrolled = Gtk.ScrolledWindow()
	scrolled.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
	scrolled.add(view)
	scrolled.set_size_request(400,400)
	scrolled.show()
	return model,view,scrolled

def make_view2():
	# Create the model.  Name/Value/Offset/Length/Format/(optional) 2nd Offset/2nd Len/Tip
	model = Gtk.TreeStore(
	GObject.TYPE_STRING,    # Name
	GObject.TYPE_STRING,    # Value
	GObject.TYPE_INT,       # Offset
	GObject.TYPE_INT,       # Length
	GObject.TYPE_STRING,    # Format
	GObject.TYPE_INT,       # 2nd Offset
	GObject.TYPE_INT,       # 2nd Length
	GObject.TYPE_PYOBJECT,  # Path to fild/outl in CDR
	GObject.TYPE_STRING     # Tooltip
	)
	# Create the view itself.
	view = Gtk.TreeView(model)
	view.set_enable_tree_lines(True)
	renderer = Gtk.CellRendererText()
	renderer2 = Gtk.CellRendererText()
	renderer3 = Gtk.CellRendererText()
	renderer2.set_property('editable', True)
	column = Gtk.TreeViewColumn('Name', renderer, text=0)
	column2 = Gtk.TreeViewColumn('Value', renderer2, text=1)
	view.append_column(column)
	view.append_column(column2)
	view.show()
	view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
	# Create scrollbars around the view.
	scrolled = Gtk.ScrolledWindow()
	scrolled.set_policy(Gtk.PolicyType.AUTOMATIC,Gtk.PolicyType.AUTOMATIC)
	scrolled.add(view)
	scrolled.set_size_request(250,300)
	#scrolled.show()
	hpaned = Gtk.HPaned()
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

