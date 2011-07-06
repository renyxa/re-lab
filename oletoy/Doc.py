import sys,struct
import tree, gtk, gobject
import gsf
import oleparse,mf,svm

class Page:
	def __init__(self):
		self.type = ''
		self.fname = ''
		self.pname = ''
		self.items = ''
		self.hd = None
		self.model, self.view, self.scrolled = tree.make_view() #None, None, None

	def fload(self):
		pos = self.fname.rfind('/')
		if pos !=-1:
			self.pname = self.fname[pos+1:]
		else:
			self.pname = self.fname
		offset = 0
		src = gsf.InputStdio(self.fname)
		buf = src.read(8)
		if buf == "\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
			self.type = oleparse.open(src, self)
			return 0

		if buf[0:6] == "VCLMTF":
			self.type = "SVM"
			src.seek(0,1)
			buf = src.read(src.size())
			svm.open (buf,self)
			return 0
			
		if buf[0:4] == "\xd7\xcd\xc6\x9a":
			self.type = "APWMF"
			src.seek(0,1)
			buf = src.read(src.size())
			mf.open(buf,self)
			print "Aldus Placeable WMF"

		if buf[0:6] == "\x01\x00\x09\x00\x00\x03":
			self.type = "WMF"
			src.seek(0,1)
			buf = src.read(src.size())
			print "Probably WMF"
			mf.open(buf,self)
			return 0

		src.seek(32,0)
		buf = src.read(4)
		if buf == "\x20\x45\x4d\x46":
			self.type = "EMF"
			print "Probably EMF"
			src.seek(0,1)
			buf = src.read(src.size())
			mf.open(buf,self)
			return 0
		src.seek(0,1)
		buf = src.read(src.size())
		iter1 = self.model.append(None, None)
		self.model.set_value(iter1, 0, "File")
		self.model.set_value(iter1, 1, 0)
		self.model.set_value(iter1, 2, src.size())
		self.model.set_value(iter1, 3, buf)
		return 0

