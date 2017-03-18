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

import sys,struct,base64
import gtk, cairo

try:
	import gv
	usegraphviz = True
except:
	print 'Graphviz not found. Only used for FreeHand.' # Grid layout will be used.'
	usegraphviz = False


ms_charsets = {0:"Latin", 1:"System default", 2:"Symbol", 77:"Apple Roman",
	128:"Japanese Shift-JIS",129:"Korean (Hangul)",130:"Korean (Johab)",
	134:"Chinese Simplified GBK",136:"Chinese Traditional BIG5",
	161:"Greek",162:"Turkish",163:"Vietnamese",177:"Hebrew",178:"Arabic",
	186:"Baltic",204:"Cyrillic",222:"Thai",238:"Latin II (Central European)",
	255:"OEM Latin I"}

def add_iter (hd,name,value,offset,length,vtype,offset2=0,length2=0,parent=None,tip=None):
	iter = hd.model.append(parent, None)
	hd.model.set (iter, 0, name, 1, value,2,offset,3,length,4,vtype,5,offset2,6,length2,8,tip)
	return iter

def add_tip (hd,iter,text):
	hd.model.set (iter, 8, text)

def pgiter(page, name, ftype, stype, data, iter1,coltype=None, vprmsmp = None):
	page.model.set_value(iter1,0,name)
	page.model.set_value(iter1,1,(ftype,stype))
	if data != None:
		page.model.set_value(iter1,2,len(data))
		page.model.set_value(iter1,3,data)
	if coltype !=None:
		page.model.set_value(iter1,7,coltype)
	if vprmsmp !=None:
		page.model.set_value(iter1,8,vprmsmp)
	
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))

def add_pgiter (page, name, ftype, stype, data, parent = None, coltype = None, vprmsmp = None):
	iter1 = page.model.append (parent,None)
	pgiter(page, name, ftype, stype, data, iter1, coltype, vprmsmp)
	return iter1

def prep_pgiter (page, name, ftype, stype, data, parent = None, coltype=None):
	iter1 = page.model.prepend (parent,None)
	pgiter(page, name, ftype, stype, data, iter1,coltype)
	return iter1

def ins_pgiter (page, name, ftype, stype, data, parent = None, pos = 0):
	# modify to insert into parent at 'pos'
	iter1 = page.model.insert (parent,pos)
	pgiter(page, name, ftype, stype, data, iter1)
	return iter1

def rdata (data,off,fmt):
	fmtlen = struct.calcsize(fmt)
	return struct.unpack(fmt,data[off:off+fmtlen])[0],off+fmtlen

def rcstr(data, off):
	s = ''
	(c, off) = rdata(data, off, '<B')
	while c != 0:
		s += chr(c)
		(c, off) = rdata(data, off, '<B')
	return s, off

def hex2d(data):
	res = ''
	data = data.replace(" ","")
	for i in range(len(data)/2):
		num = int(data[i*2:i*2+2],16)
		res += struct.pack("B",num)
	return res


def cnvrt22(data,end=">"):
	i = struct.unpack("%sh"%end,data[0:2])[0]
	f = struct.unpack("%sH"%end,data[2:4])[0]/65536.
	return i+f


def d2asc(data,ln=0,rch=unicode("\xC2\xB7","utf8")):
	asc = ""
	for i in range(len(data)):
		ch = data[i]
		if ord(ch) < 32 or ord(ch) > 126:
			ch = rch
		asc += ch
		if ln != 0 and i > 0 and (i+1)%ln == 0:
			asc += "\n"
	return asc

def d2hex(data,space="",ln=0):
	s = ""
	for i in range(len(data)):
		s += "%02x%s"%(ord(data[i]),space)
		if ln != 0 and i > 0 and (i+1)%ln == 0:
			s += "\n"
	return s

def d2bin(data):
	return ' '.join(format(ord(x), 'b').zfill(8) for x in data)

def key2txt(key,data,txt="Unknown"):
	if key in data:
		return data[key]
	else:
		return txt

def bflag2txt(flag,data,txt=""):
	if flag != 0:
		for i in [1 << s for s in range(0, 32)]: # flag sets 32 bits wide should be enough
			if flag < i:
				break;
			if flag&i == i:
				txt += key2txt(i,data,"") + "/"
		if len(txt) > 0:
			txt = txt[:len(txt)-1]
	return txt

def dib2bmp(data,strict=0):
	flag = struct.unpack("<I",data[:4])[0]
	if flag != 0x28:
		print "Doesn't look like DIB, sir..."
		if strict:
			return 0
	size = len(data)+14
	bpp = ord(data[14])
	if bpp == 1:
		bsize = size - 0x3e
	else:
		bsize = struct.unpack("<I",data[0x14:0x18])[0]
	return "BM"+struct.pack("<I",size) + "\x00"*4+struct.pack("<I",size-bsize)+data

def b64decode (page,data,parent):
	decdata = base64.b64decode(data)
	add_pgiter (page, "[Base64decoded]", "base64", "", decdata, parent)

def bup2 (string, offlen):
	t = ""
	t2 = ""
	r = []
	string = string.replace(" ","")
	for i in string:
		t += bin(int(i,16))[2:].zfill(4)
		t2 += bin(int(i,16))[2:].zfill(4) + "."
	for i,j in offlen:
		try:
			r.append(int(t[int(i):int(i)+int(j)],2))
		except:
			pass
	return t2[:-1],r


def graph_on_button_press(da,event,data,hd):
	if event.type  == gtk.gdk.BUTTON_PRESS:
		if event.button == 1:
			hd.dispscale *= 1.4
			graph_expose(da,event,data,hd)
		if event.button == 2:
			hd.dispscale = 1
			hd.da.hide()
			hd.da.show()
		if event.button == 3:
			hd.dispscale *= .7
			hd.da.hide()
			hd.da.show()

def graph_expose (da,event,data,hd):
	ctx = da.window.cairo_create()
	ctx.set_source_rgb(0,0,0.5)
	ctx.scale(hd.dispscale,hd.dispscale)
	ctx.set_source_rgb(0,0,0.1)
	y = 0
	for x in range(len(data)):
		y1 = ord(data[x])
#		if y1 - y < 10:
#			ctx.move_to(x*2,256-y1)
		ctx.line_to(x+0.5,256.5-y1)
		y = y1
			
	ctx.stroke()


def graph(hd,data):
	ch = hd.hdscrolled.get_child2()
	if ch:
		ch.connect('expose_event', graph_expose,data,hd)
	else:
		da = gtk.DrawingArea()
		scrolled = gtk.ScrolledWindow()
		scrolled.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
		scrolled.add_with_viewport(da)
		hd.da = scrolled
		hd.hdscrolled.add2(hd.da)
		da.set_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK | gtk.gdk.POINTER_MOTION_MASK)
		da.connect('expose_event', graph_expose,data,hd)
		da.connect("button_press_event",graph_on_button_press,data,hd)

	hd.da.show_all()


def disp_expose (da,event,hd,scale=1):
	x,y,width,height = da.allocation
	ctx = da.window.cairo_create()
	if event and event.area:
		ctx.rectangle(event.area[0],event.area[1],event.area[2],event.area[3])
		ctx.clip()
	ctx.set_source_pixbuf(hd.pixbuf,0,0)
	ctx.paint()
	ctx.stroke()

######## Layout ########

def hr_layout(nodes):
	sq = int(math.sqrt(len(nodes)))+1
	dx = 1
	dy = 1
	devs = {}
	for i in nodes:
		devs["%s"%i] = (dx*70,dy*70)
		dx += 1
		if dx > sq:
			dx = 1
			dy += 1
	return devs

gv_colors = {
	"FHTail":"red",
	"Block":"orange",
	"PropLst":"yellow",
	"Layer":"green",
	"Path":"blue"
	}

def gv_layout(nodes,edges,mode="dot"):
	G = gv.graph("root")
	s = gv.graph(G,"test")
	for i in nodes:
		sg = "%02x %s"%(i,nodes[i][0])
		n = gv.node(s,sg)
		if nodes[i][0] in gv_colors:
			gv.setv(n,"color",gv_colors[nodes[i][0]])
			gv.setv(n,"style","filled")

	for i in edges:
		if i[0] in nodes and i[1] in nodes:
			e = gv.edge(G,"%02x %s"%(i[0],nodes[i[0]][0]),"%02x %s"%(i[1],nodes[i[1]][0]))
			gv.setv(e,"dir","none")
	gv.layout(G, mode)
	gv.render(G)
# for debugging purposes
	gv.render(G,'svg','test.svg')
	devs = {}
	fn = gv.firstnode(G)
	try:
		devs[gv.nameof(fn)] = gv.getv(fn,"pos").split(",")
	except:
		print 'Failed in gv_render'
	for i in range(len(nodes)-1):
		fn = gv.nextnode(G,fn)
		devs[gv.nameof(fn)] = gv.getv(fn,"pos").split(",")

	return devs



def graph_layout (app, doc, algo):
	if usegraphviz and algo in ("fdp","sfdp","neato","circo","osage","dot","twopi"):
		devs = gv_layout(doc.nodes,doc.edges,algo)
	else:
		# hinted random placement
		devs = hr_layout(doc.nodes)
