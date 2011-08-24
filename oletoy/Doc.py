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

import sys,struct
import tree, gtk, gobject
import ole,mf,svm,cdr,clp,rx2

class Page:
	def __init__(self):
		self.type = ''
		self.fname = ''
		self.pname = ''
		self.items = ''
		self.version = 0
		self.hd = None
		self.model, self.view, self.scrolled = tree.make_view() #None, None, None

	def fload(self):
		pos = self.fname.rfind('/')
		if pos !=-1:
			self.pname = self.fname[pos+1:]
		else:
			self.pname = self.fname
		offset = 0
		f = open(self.fname)
		buf = f.read()

		if buf[0:8] == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
			self.type = ole.open(buf, self)
			return 0

		if buf[0:2] == "\x50\xc3":
			self.type = "CLP"
			clp.open (buf,self)
			return 0

		if buf[0:6] == "VCLMTF":
			self.type = "SVM"
			svm.open (buf,self)
			return 0

		if buf[0:4] == "RIFF" and buf[8:11] == "CDR":
			self.type = "CDR%x"%(ord(buf[11])-0x30)
			print 'Probably CDR %x'%(ord(buf[11])-0x30)
			cdr.cdr_open(buf,self)
			return 0

		if buf[0:4] == "\xd7\xcd\xc6\x9a":
			self.type = "APWMF"
			mf.mf_open(buf,self)
			print "Aldus Placeable WMF"
			return 0

		if buf[0:6] == "\x01\x00\x09\x00\x00\x03":
			self.type = "WMF"
			print "Probably WMF"
			mf.mf_open(buf,self)
			return 0

		if buf[40:44] == "\x20\x45\x4d\x46":
			self.type = "EMF"
			print "Probably EMF"
			mf.mf_open(buf,self)
			return 0
			
		if buf[0:4] == "CAT " and buf[0x8:0xc] == "REX2":
			self.type = "REX2"
			print "Probably REX2"
			rx2.open(buf,self)
			return 0
			
		iter1 = self.model.append(None, None)
		self.model.set_value(iter1, 0, "File")
		self.model.set_value(iter1, 1, 0)
		self.model.set_value(iter1, 2, len(buf))
		self.model.set_value(iter1, 3, buf)
		return 0

