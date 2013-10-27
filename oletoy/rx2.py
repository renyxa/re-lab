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

import sys,struct,gtk

def parse (model,buf,offset = 0,parent=None):
		newT = buf[offset:offset+4]
		offset += 4
		newL = struct.unpack('>I', buf[offset:offset+4])[0]
		offset += 4
		if newL%2 == 1:
			newL += 1

		if newT == "CAT ":
			desc = buf[offset:offset+4]
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,"CAT %s"%desc)
			model.set_value(iter1,1,("rx2","cat"))
			model.set_value(iter1,2,newL)
			model.set_value(iter1,3,buf[offset-8:offset+newL])
			model.set_value(iter1,6,model.get_string_from_iter(iter1))

			offset += 4
			i = 0
			while i < newL:
				try:
					offset,nlen = parse (model,buf,offset,iter1)
					i += nlen
				except:
					break
		else:
			newV = buf[offset:offset+newL]
			iter1 = model.append(parent,None)
			model.set_value(iter1,0,newT)
			model.set_value(iter1,1,("rx2",newT))
			model.set_value(iter1,2,newL)
			model.set_value(iter1,3,buf[offset-8:offset+newL])
			model.set_value(iter1,6,model.get_string_from_iter(iter1))
			if newT == "SLCE":
				sloffset = struct.unpack('>I', newV[0:4])[0]
				sllen = struct.unpack('>I', newV[4:8])[0]
				slunkn =	struct.unpack('>I', newV[8:12])[0]
				model.set_value(iter1,0,"%s %04x %04x"%(newT,sloffset,sllen))
			if newT == "SDAT":
				iter2 = model.append(iter1,None)
				model.set_value(iter2,0,"Data")
				model.set_value(iter2,1,("rx2","data"))
				model.set_value(iter2,2,newL-8)
				model.set_value(iter2,3,buf[offset:offset+newL])
				model.set_value(iter2,6,model.get_string_from_iter(iter2))
				
			offset += newL
		return offset,newL+8
	
def rx2_head (hd, data):
	off = 13
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Bytes per sample?",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")

def rx2_eq (hd,data):
	off = 8
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Enabled",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off +=1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Lo Cut",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Lo",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "G",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Q",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Hi",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "G",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Q",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Hi Cut",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")

def rx2_trsh (hd,data):
	off = 8
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Enabled",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off +=1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Attack",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Decay",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Stretch",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")

def rx2_comp (hd,data):
	off = 8
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Enabled",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off +=1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Thrsh",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Amount",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Attack",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Release",1, struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")

def rx2_slce (hd,data):
	#FF: i'm pretty confident that this relates to the offset as I created a slice very close to the start
	# and it had a value of 3, and a file with 3 slices in had values here that looked proportional to the
	# slice start 
	off = 8
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Offset?",1, "%02x"%struct.unpack(">I",data[off:off+4])[0],2,off,3,4,4,">I")
	off +=4
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Length?",1, "%02x"%struct.unpack(">I",data[off:off+4])[0],2,off,3,4,4,">I")
	off +=4
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Unkn1",1, "%02x"%struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	off +=2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Unkn2",1, "%02x"%struct.unpack(">H",data[off:off+2])[0],2,off,3,2,4,">H")
	
def rx2_sinf (hd, data):
	off = 14;
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Sound/slice length 1",1, struct.unpack(">I",data[off:off+4])[0],2,off,3,4,4,">I")
	
	off = 21;
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Move left locator to first slice point",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	
	off +=1;
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Sound/slice length 2",1, struct.unpack(">I",data[off:off+4])[0],2,off,3,4,4,">I")

def rx2_glob(hd,data):
	off = 12 
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Length (Bars)",1, struct.unpack(">H", data[off:off+2])[0],2,off,3,2,4,">H")
	off += 2
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Length (Beats)",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Time Signature (upper numeral)",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Time Signature (lower numeral)",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Sens",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	
	#gate sensitivity has 1 decimal place but is stored as an integer so needs to be divided by 10
	off = 18
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Gate Sens",1, struct.unpack(">H", data[off:off+2])[0] / 10.0,2,off,3,2,4,">H")
	off += 2
	
	#gain ranges from -inf then -60db to +18db
	# -inf is stored as 00 00
	# -60db is stored as 00 01
	# -54db is stored as 00 02
	# -50.5db is stored as 00 03
	# -48db is stored as 00 04
	# -46db is stored as 00 05
	# -44.4db is stored as 00 06
	# -38.4db is stored as 00 0C
	# -25.8db is stored as 00 33
	# -20.8db is stored as 00 5B
	# -19.5db is stored as 00 6A
	# -17.6db is stored as 00 84
	# -12.6db is stored as 00 EA
	# -9.3db is stored as 01 57
	# -3.9db is stored as 02 7D
	# 0db is stored as 03 E8 (1000)
	# 18db is stored as 1F 07 (7943)
	# It looks like it starts out as an enumeration but at some point switches over to values. log scale?
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Gain (not sure about scale)",1, struct.unpack(">H", data[off:off+2])[0],2,off,3,2,4,">H")	
	off += 2
	#pitch has 2 decimal places but is stored as an integer
	#if the number displayed is 5.75, it will be stored as an integer 575
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Pitch",1, struct.unpack(">H", data[off:off+2])[0] / 100.0 ,2,off,3,2,4,">H")
	
	#FF: am assuming 32-bit int - can't be certain that it uses all 4 bytes, have only seen the last 3 bytes used (offset 25-27) 
	#there are 3 decimal places in the tempo, so it is multiplied by 1000 and stored as an integer  
	off = 24
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Tempo (BPM)",1, struct.unpack(">L", data[off:off+4])[0] / 1000.0 ,2,off,3,4,4,">L")	
	off += 4
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Toggle: Export as multiple samples",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Toggle: Silence Selected",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")


def rx2_recy(hd, data):
	off = 9
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Bytes per sample?",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	
	off = 13
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Toggle: Preview",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")

    #this changed when the number of visible slices changed
	off = 16	
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "something to do with visible slices?",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1;
	
	#this changes when you move the pitch control, at the same time as the pitch setting at offset 22 in the GLOB section.
	#this also changes if you enable/disable the Envelope effect (but not either of the other two)
	#I am not sure what this value means. Might need access to a copy of recycle 1 to work this out?
	
	#I also observed that it is related to the length of the file. Without changing the pitch from the default:
	#file length(samples)        value (dec)
	#5							14
	#10							28
	#25							70
	#125						352
	#375						1056
	

	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Pitch/TRSH/num samples ?",1, struct.unpack(">H", data[off:off+2])[0],2,off,3,2,4,">H")
	
	off = 22
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Visible Slices",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	
	
	
def rx2_rcyx(hd, data):
	off = 16
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Selected Tool (0=Arrow,1=Mute,2=Lock,3=Pen)",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1	
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Toggle: Envelope Toolbar",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Toggle: Equaliser Toolbar",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")
	off += 1
	iter = hd.model.append(None, None)
	hd.model.set(iter, 0, "Toggle: Transient Shaper Toolbar",1, struct.unpack(">B", data[off:off+1])[0],2,off,3,1,4,">B")	

rx2_ids = {"EQ  ":rx2_eq, "TRSH":rx2_trsh,  "COMP":rx2_comp, "SLCE":rx2_slce, 
		"SINF":rx2_sinf, "GLOB":rx2_glob, "RCYX":rx2_rcyx, "RECY":rx2_recy,
		"HEAD": rx2_head}

def open (buf,page,parent):
	parse (page.model,buf,0,parent)
