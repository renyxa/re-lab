# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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

class vsdoc:
    def __init__(self):
        self.colors = [] #color()
        self.fonts = {} #font dict
        self.pages = [] #page()
        self.model = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
        self.version = 0
        self.zoom = 1 # initial zoom, I'm giong to implement something that will use it
        self.fname = ''
        self.stencils = []
        self.stmap = {} #dict of stencil signatures <-> numbers
        self.names = {} #dict of names used for page and stencil page items
        self.styles = [] # style() 0x1a
        self.preview = None
     
    def usage():
        class_pages = page()
        class_vsdoc.pages.append(class_pages)
        class_stencils = stencil()
        class_vsdoc.stensils.append(class_stencils)

class stencil:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.shapes = {} #shape()
        self.name = ''
        self.nameidx = 0
        self.icon = ()
        self.curshape = -1
    def usage():
        class_shapes = shape()
        class_vsdoc.shapes.append(class_shapes)

class page:
    def __init__(self):
        self.width = 0
        self.height = 0
        self.zoom = 1
        self.shapes = {} #shape()
        self.name = ''
        self.nameidx = 0
        self.curshape = -1
    def usage():
        class_shapes = shape()
        class_vsdoc.shapes.append(class_shapes)

class shape:
    def __init__(self):
        self.shapes = {} #shape()
        self.type = 0 # Shape, Group or Foreign at the moment
        self.xform = XForm()
        self.xform1d = None
        self.geom = Geom()
        self.fill = Fill()
        self.line = Line()
        self.char = Char()
        self.text = Text()
        self.ShapeList = []
        self.Foreign = Foreign()
        self.grpflag = 0
        self.IX = None
        
    def usage():
        class_shapes = shape()
        class_vsdoc.shapes.append(class_shapes)

class Foreign:
    Data = ()
    Type = 0
    Subtype = 8
    Format = 0
    Stencil = 0
    stflag = 0
    sig = ''
    List = []

class color:
    r = 0
    g = 0
    b = 0
    a = 0

class Fill:
    set = 0
    fgcolor = color()
    fgcolor.r = 255.0
    fgcolor.g = 255.0
    fgcolor.b = 255.0
    fgcolor.a = 0
    bgcolor = color()
    fgpattern = 0
    shfgclr = color()
    shbgclr = color()
    shpattern = 0
    shoffX = 0
    shoffY = 0

class TxtBlock:
    LMarg = 1.4111
    RMarg = 1.4111
    TMarg = 1.4111
    BMarg = 1.4111
    VAlign = 1
    TxtBG = color()
    DfltTab = 15
    TxtDir = 0 # L2R?

class Para:
    ind1st = 0
    indLeft = 0
    indRight = 0
    spLine = -1.2
    spBefore = 0
    spAfter = 0
    HAlign = 1
    Bullet = 0
    BulletStr = ''

class XForm1D:
    bx = 0
    by = 0
    ex = 0
    ey = 0
    
class XForm:
    x = 0
    y = 0
    w = 0
    h = 0
    locx = 0
    locy = 0
    flipx = 0
    flipy = 0
    ang = 0

class TxtXForm:
    x = 0
    y = 0
    w = 0
    h = 0
    locx = 0
    locy = 0
    ang = 0

class Text:
    txt = ''
    txtblock = TxtBlock()
    para = Para()
    txtxform = TxtXForm()

class cmd:
    type = ''
    args = ()

class Geom:
    def __init__(self):
        self.cmds = []
        self.nofill = 0
        self.noline = 0
        self.noshow = 0
        self.nosnap = 0
        self.list = []
        
    def usage():
        class_cmds = cmd()
        class_vsdoc.cmds.append(class_cmds)
    
class Line:
    flags = 0
    lineclr = color()
    lineclr.r = 0.
    lineclr.g = 0.
    lineclr.b = 0.
    width = 0.254
    pattern = 1

class Char:
    fntsize = 4.2333
    charclr = color()
    charclr .r = 0.
    charclr .g = 0.
    charclr .b = 0.
    fntnum = 0
    fbold = 0
    fslant = 0
    funder = 0
    style = ''

class font:
    id = 0
    name = 'Arial'

class chunk:
    type = 0    #dword
    IX = 0        #dword
    unkn1 = 0   #dword
    length = 0  #dword
    unkn2 = 0   #word
    unkn3 = 0   #byte
    data = ''

class pointer:
    type = 0
    address = 0
    offset = 0
    length = 0
    format = 0
    path = '' # here I'm going to store path to TreeStore row with this pointer
    data = '' # here I'm going to store content of suitable part of vsd file

