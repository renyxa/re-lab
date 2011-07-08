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

import gsf

def inflate(ptr,vsd):
    res = ''
    buff = ['\x00']*4096
    pos = 0
    i = 0
    offset = ptr.offset
    while i < ptr.length:
        try:
            flag = ord(vsd[offset])
            offset=offset+1
            i = i + 1
            for mask in (1,2,4,8,16,32,64,128):
                if flag&mask: # this bit in flag is ON
                    pst = pos&4095
                    buff[pst] =  vsd[offset]
                    offset=offset+1
                    res = res + buff[pst]
                    pos=pos+1
                    i = i + 1
                else:
                    if offset-ptr.offset > ptr.length - 2:
                        break
                    addr1 = ord(vsd[offset])
                    offset=offset+1
                    addr2 = ord(vsd[offset])
                    offset=offset+1
                    len = (addr2&15) + 3
                    point = (addr2&240)*16+addr1
                    i = i + 2
                    if point > 4078:
                        point = point - 4078
                    else:
                        point = point + 18
                    for j in range (len):
                        buff[(pos+j)&4095]=buff[(point+j)&4095]
                        res = res + buff[(point+j)&4095]
                    pos = pos + len
        except:
            print 'Inflate failed',i,ptr.length
            i+=1
    return res

def deflate_piastre (buf):
  # 'compression' function which increase size of the result by 12.5%
  i = 0
  res = ''
  while i< len(buf):
    res += '\xFF'+buf[i:i+8]
    i +=8
  n = len(buf)-(len(buf)/8)*8
  res += '\x00'*n
  return res

def deflate (buf):
  # wrapper to avoid later renaming if I implement something better then 'piastre' ;-)
  return deflate_piastre (buf)
