# Copyright (C) 2007-2011,	Valek Filippov (frob@df.ru)
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

import sys,struct
import gobject
import gtk
import tree
import hexdump
import inflate
from utils import *


def rt_0 (data):
	return ""

def rt_2 (data):
	return "%02x"%struct.unpack("<H",data)[0]

def rt_4 (data):
	return "%02x"%struct.unpack("<I",data)[0]

def rt_TL (data):
	return data[4:]

def rt_U (data):
	return unicode(data,"utf-16")

def rt_UL (data):
	return rt_U(data[4:])

rec_types = {1:rt_4,2:rt_4,3:rt_2,0x14:rt_4,9:rt_0,0xd:rt_TL,0xf:rt_2,
	0x13:rt_2, 0x2c:rt_2,0x31:rt_4,0x32:rt_U,0x3e:rt_U,0x47:rt_U}

rec_ids = {1:"SysKind",2:"Lcid",3:"CodePage",4:"Name",5:"DocString",
	6:"HelpFile1",7:"HelpContext",8:"LibFlags",9:"Version",
	0xc:"Constants", 0xd:"RefRegistred", 0xe:"RefProject",
	0xf:"ProjModules", 0x10:"Terminator", 0x13:"ProjCookie",
	0x14:"LcidInvoke",0x16:"RefName",
	0x19:"ModuleName", 0x1a:"ModuleStreamName",
	0x1c:"ModuleDocString", 0x1e:"ModuleHelpContext",
	0x21:"ModuleType",0x22:"ModuleType (Doc,Class,Designer)",
	0x25:"ModuleReadOnly", 0x28:"ModulePrivate",
	0x2b:"ModuleTerminator", 0x2c:"ModuleCookie", 0x31:"ModuleOffset",
	0x32:"ModuleStreamNameUnicode",
	0x2f:"RefControl", 0x33:"RefOrig",0x3c:"ConstantsUnicode",
	0x3d:"HelpFile2", 0x3e:"RefNameUnicode", 0x40:"DocStringUnicode",
	0x47:"ModuleNameUnicode",
	0x48:"ModuleDocStringUnicode",
	0x49:"HelpFile2" #typo?
	}

def vba_src (hd,data):
	iter = hd.hdmodel.append(None, None)
	hd.hdmodel.set(iter, 1, data,2,0,3,len(data),4,"txt")

def vba_dir (hd,data):
	off = 0
	miter = None
	while off < len(data):
		recid = struct.unpack("<H",data[off:off+2])[0]
		reclen = struct.unpack("<I",data[off+2:off+6])[0]
		if recid == 9:
			reclen = 6
		recname = "%02x"%recid
		if rec_ids.has_key(recid):
			recname = rec_ids[recid]
		iter = hd.hdmodel.append(miter, None)
		if rec_types.has_key(recid):
			value = rec_types[recid](data[off+6:off+6+reclen])
		else:
			value = data[off+6:off+6+reclen]
		hd.hdmodel.set(iter, 0, recname,1, value,2,off,3,reclen+6,4,"txt")
		off += reclen + 6
		if recid == 0x19:
			miter = iter
		if recid == 0x2b:
			miter = None

def parse (page, data, parent):
	model = page.model
	if ord(data[0]) == 1:
		# compressed stream
		try:
			if model:
				value = inflate.inflate_vba(data,page.type)
				iter1 = model.append(parent,None)
				model.set_value(iter1,0,"[Decompressed stream]")
				model.set_value(iter1,1,("vba","dir"))
				model.set_value(iter1,2,len(value))
				model.set_value(iter1,3,value)
				model.set_value(iter1,6,model.get_string_from_iter(iter1))
		except:
			print 'VBA Inflate failed'
	off = 0
	mods = {}
	while off < len(value):
		try:
			recid = struct.unpack("<H",value[off:off+2])[0]
			reclen = struct.unpack("<I",value[off+2:off+6])[0]
			if recid == 9:
				reclen = 6
			if recid == 0x19: # ModuleName
				mname1 = value[off+6:off+6+reclen]
			if recid == 0x31: # ModuleOffset
				moff1 = struct.unpack("<I",value[off+6:off+10])[0]
				mods[mname1] = moff1
			off += reclen + 6
		except:
			print "Failed at VBA parsing"
			off += 2

#	print "Found %d modules"%len(mods)

	vbaiter = model.iter_parent(parent)
	for k in range(model.iter_n_children(vbaiter)):
		citer = model.iter_nth_child(vbaiter,k)
		cname = model.get_value(citer,0)
		if mods.has_key(cname):
			cdata = model.get_value(citer,3)
			if ord(cdata[mods[cname]]) == 1:
				try:
					cvalue = inflate.inflate_vba(cdata[mods[cname]:],page.type)
					iter1 = model.append(citer,None)
					model.set_value(iter1,0,"VBA SourceCode")
					model.set_value(iter1,1,("vba","src",mods[cname]))
					model.set_value(iter1,2,len(cvalue))
					model.set_value(iter1,3,cvalue)
					model.set_value(iter1,6,model.get_string_from_iter(iter1))
				except:
					print 'VBA Src Inflate failed ',cname
