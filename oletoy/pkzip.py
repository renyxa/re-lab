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

#add_pgiter (page, name, ftype, stype, data, parent = None):

def open(fname,page,parent=None):
	try:
		dirstruct = {}
		z = zipfile.ZipFile(fname,"r")
		for i in z.filelist:
			fn = i.filename
			data = z.read(fn)
			print fn
			pos = fn.rfind("/")
			if pos == -1:
				iter = add_pgiter(page,fn,"pkzip",0,data)
			else:
				iter = add_pgiter(page,"[%s]%s"%(fn[:pos],fn[pos:]),"pkzip",0,data)
			if len(data) > 0:
				page.fload(data,iter)
			
	except:
		print "Open as PKZIP failed"
