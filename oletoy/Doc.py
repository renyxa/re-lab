import sys,struct
import tree, gtk, gobject
import oleparse

class Page:
	def __init__(self):
		self.type = 0
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
		oleparse.open(self.fname,self.model)
		return 0
