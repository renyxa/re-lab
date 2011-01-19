import gobject
import gtk

def make_view():
   # Create the model. Name/Type/Length/Value/Value2
   model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_PYOBJECT, gobject.TYPE_INT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
   # Create the view itself.
   view = gtk.TreeView(model)
   view.set_reorderable(True)
   view.set_enable_tree_lines(True)
   renderer = gtk.CellRendererText()
   renderer.set_property('family-set',True)
   renderer.set_property('font','monospace')
#   renderer.family="monospace"
   column = gtk.TreeViewColumn('Record', renderer, text=0)
   column2 = gtk.TreeViewColumn('Length', renderer, text=2)
   view.append_column(column)
   view.append_column(column2)
   view.show()
   # Create scrollbars around the view.
   scrolled = gtk.ScrolledWindow()
   scrolled.add(view)
   scrolled.set_size_request(400,400)
   scrolled.show()
   return model,view,scrolled

def make_view2():
   # Create the model.  Name/Value/Offset/Length/Format
   model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_STRING)
   # Create the view itself.
   view = gtk.TreeView(model)
   view.set_enable_tree_lines(True)
   renderer = gtk.CellRendererText()
   renderer2 = gtk.CellRendererText()
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
   scrolled.show()
   return model,view,scrolled,renderer2


def tree_append(model,parent,name,data,dtype,dlen):
    folder = { "name": name, "part": data, "partT": dtype, "partL": dlen}
    iter = model.insert_before(parent, None)
    model.set_value(iter, 0, folder)
    model.set_value(iter, 1, folder["name"])
    model.set_value(iter, 2, folder["partL"])
    return iter

