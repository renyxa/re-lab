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

import zipfile
from utils import *

class PkzipPackage:
	def __init__(self, names):
		self.listNames = []
		for n in names:
			self.listNames.append(n.filename)

	def namelist(self):
		return self.listNames

def open(fname,page,parent=None):
	try:
		dirstruct = {}
		iters = []
		root_itr = None
		z = zipfile.ZipFile(fname,"r")
		page.fdata = {}
		package = PkzipPackage(z.filelist)
		for i in z.filelist:
			fn = i.filename
			data = z.read(fn)
			print(fn)
			pos = fn.rfind("/")
			if pos == -1:
				name = fn
			else:
				name = "[%s]%s"%(fn[:pos],fn[pos:])
			itr = add_pgiter(page,name,"pkzip",0,data)
			if len(data) > 0:
				if "root.dat" in name:
					root_itr = (data, itr)
				else:
					iters.append((data, itr))
		if root_itr:
			iters.append(root_itr)
		for (data, itr) in iters:
			page.fload(data, itr, package)

	except zipfile.BadZipfile:
		print("Open as PKZIP failed")
	except zipfile.LargeZipFile:
		print("Open as PKZIP failed")
