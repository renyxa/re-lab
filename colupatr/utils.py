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

import struct
import gtk, gobject

def hex2d(data):
	res = ''
	data = data.replace(" ","")
	for i in range(len(data)/2):
		num = int(data[i*2:i*2+2],16)
		res += struct.pack("B",num)
	return res

def d2hex(data,spc=""):
	s = ""
	for i in range(len(data)):
		s += "%02x%s"%(ord(data[i]),spc)
	return s

def arg_conv (ctype,carg):
	data = ''
	if ctype.lower() == 'x':
		data = hex2d(carg)
	elif ctype.lower() == 'u':
		data = carg.encode("utf-16")[2:]
	elif ctype.lower() == 'a' or ctype.lower() == 'r':
		data = carg
	return data

def find_line (doc,addr):
	if addr < doc.lines[len(doc.lines)-1][0]:
		lno = 0
		lnum = addr/16
		while lnum < len(doc.lines) and lno != lnum:
			lno = lnum
			if doc.lines[lnum][0] < addr:
				if doc.lines[lnum+1][0] > addr:
					break
				elif doc.lines[lnum+1][0] == addr:
					lnum += 1
				else:
					lnum += (addr - doc.lines[lnum+1][0])/16
			elif  doc.lines[lnum][0] == addr:
				break
			else:
				lnum -= (doc.lines[lnum][0] - addr)/16
			if lnum < 0:
				break
		return lnum


def cmd_parse(cmd, app,doc):
	if cmd[0] == "?":
		if len(cmd) > 1:
			ctype = cmd[1]
			carg = cmd[2:]
		# convert line to hex or unicode if required
			data = arg_conv(ctype,carg)
		elif doc.sel:
			r1,c1,r2,c2 = doc.sel
			data = doc.data[doc.lines[r1][0]+c1:doc.lines[r2][0]+c2]
			carg = "Selection"
		app.search = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_INT, gobject.TYPE_STRING)
		sflag = 0
		p = doc.data.find(data)
		while p !=-1:
			s_iter = app.search.append(None,None)
			app.search.set_value(s_iter,2,"%02x"%p)
			p = doc.data.find(data,p+1)
			sflag = 1
		if sflag:
			app.show_search(carg)

def html_export(app,doc,sline,doff,dlen):
	fname = app.file_open('Save',None,gtk.FILE_CHOOSER_ACTION_SAVE,doc.fname+".html")
	if fname:
		f = open(fname,'w')
		f.write("<!DOCTYPE html><html><body>")
		f.write("<head>\n<meta charset='utf-8'>\n") 
		f.write("<style type='text/css'>\ntr.top1 td { border-bottom: 1px solid black; }")
		f.write("tr.top2 td { border-bottom: 2px solid purple; }\n")
		f.write("tr.top3 td { border-bottom: 3px solid red; }\n")
		f.write("tr.title td { border-bottom: 3px solid black; }\n")
		f.write(".mid { border-left: 1px solid black; border-right: 1px solid black;}\n")
		f.write("</style>\n</head>\n")
		f.write("<table style='font-family:%s;' cellspacing=0>\n"%doc.font)
		if app.options_htmlhdr:
			addrtxt = ""
			for i in range(doc.maxaddr):
				addrtxt += "%02x "%i
			f.write("<tr class='title'><td>%s</td><td></td><td></td></tr>"%addrtxt[:-1])
		off = 0
		i = 0
		while off < dlen:
			so = doc.lines[sline+i][0]
			eo = doc.lines[sline+i+1][0]
			try:
				txt1 = doc.hvlines[sline+i][0]
			except:
				txt1 = doc.get_string(sline+i)[0]
			txt2 = doc.hvlines[sline+i][1]

			cmntest = doc.chk_comment(so,eo)
			cl = doc.lines[sline+i][1]
			if cl:
				f.write("<tr class='top%s'>"%cl)
			else:
				f.write("<tr>")
			txt3 = ""
			if len(cmntest) > 0:
				tmpoff = 0
				txthex = ""
				txtasc = ""
				txtcmnt = ""
				addr1 = 0
				addr2 = eo - so
				for cmnt in cmntest:
					clr = doc.comments[cmnt].clr
					cmntclr = "%d,%d,%d"%(clr[0]*255,clr[1]*255,clr[2]*255)
					
					if doff + off + tmpoff < doc.comments[cmnt].offset - 1:
						addr1 = doc.comments[cmnt].offset - doff - off - 1
						txthex += txt1[tmpoff*3:addr1*3]
						txtasc += txt2[tmpoff:addr1]
					
					if doc.comments[cmnt].length < eo - so - addr1:
						addr2 = addr1 + doc.comments[cmnt].length
					txthex += "<span style='background-color: rgba(%s,0.3);'>"%cmntclr+txt1[addr1*3:addr2*3-1]+"</span> "
					txtasc += "<span style='background-color: rgba(%s,0.3);'>"%cmntclr+txt2[addr1:addr2]+"</span>"
					tmpoff = addr2
					txtcmnt += "<span style='color: rgb(%s);'>"%cmntclr+doc.comments[cmnt].text+"</span> "+unicode("\xC2\xB7","utf8") + " "
				txthex += " " + txt1[addr2*3:]
				txtasc += txt2[addr2:]
				f.write("<td>%s</td>"%txthex)
				f.write("<td class='mid'>%s</td>"%txtasc)
				f.write("<td>%s</td>"%txtcmnt[:-3])
			else:
				f.write("<td>%s</td><td class='mid'>%s</td><td></td>"%(txt1,txt2))
			f.write("</tr>\n")
			i += 1
			off += eo - so
		f.write("</table></body></html>")
		f.close()
	else:
		print("Nothing to export")

