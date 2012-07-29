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

import struct
from utils import *

def next (hv):
	if hv.offnum < len(hv.lines)-hv.numtl and hv.curr >= hv.offnum+hv.numtl-3:
		hv.offnum += 1
		hv.mode = ""
	hv.curr += 1
	if hv.curr > len(hv.lines)-2:
		hv.curr = len(hv.lines)-2
	if hv.curr < hv.offnum:
		hv.curr = hv.offnum
	maxc = hv.lines[hv.curr+1][0] - hv.lines[hv.curr][0] -1
	if hv.curc > maxc:
		hv.curc = maxc

def read (hv, fmt, off=-1):
	if off == -1:
		off = tell(hv)
	res = struct.unpack(fmt,hv.data[off:off + struct.calcsize(fmt)])[0]
	return res

def seek (hv, off):
	llast = len(hv.lines)
	if off < hv.lines[len(hv.lines)-1][0]:
		lnum = find_line(hv,off)
		hv.curr = lnum
		hv.curc = off - hv.lines[lnum][0]
		hv.offnum = min(lnum,llast-hv.numtl)
		hv.offset = hv.lines[lnum][0]

def tell (hv):
	return hv.lines[hv.curr][0]+hv.curc

def wrap (hv,col):
	hv.fmt(hv.curr,(col,))
