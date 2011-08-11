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

import gsf, struct

def inflate_vba_stream (data):
  i = 0
  pos = 0
  buf = ""
  res = ""
  while i < len(data):
    flag = ord(data[i])
    i += 1
    for mask in (1,2,4,8,16,32,64,128):
      if flag&mask:
        addr = struct.unpack("<H",data[i:i+2])[0]
        i += 2
        win_pos = pos % 4096
        if win_pos <= 0x80:
          if win_pos <= 0x20:
            if win_pos <= 0x10:
              shift = 12
            else:
              shift = 11
          else:
            if win_pos <= 0x40:
              shift = 10
            else:
              shift = 9
        else:
          if win_pos <= 0x200:
            if win_pos <= 0x100:
              shift = 8
            else:
              shift = 7
          elif win_pos <= 0x800:
            if win_pos <= 0x400:
              shift = 6
            else:
              shift = 5
          else:
            shift = 4
        blen = (addr & ((1 << shift) - 1)) + 3
        distance = addr >> shift
        clean = True
        for j in range(blen):
#          print "Addr ",len(buf),j,addr,i
          srcpos = (pos - distance - 1) % 4096
          c = buf[srcpos]
          buf = buf[:pos % 4096] + c + buf[pos % 4096 + 1:]
          pos +=1
#        print "---------------"
      else:  
        if pos != 0 and pos % 4096 == 0 and clean:
          i += 2  # why? (check gsf_msole_inflate)
          clean = False
          res += buf
          break
        if i < len(data):
          c = data[i]
          buf = buf[:pos % 4096] + c + buf[pos % 4096 + 1:]
          pos += 1
          i += 1
        clean = True
  if pos % 4096:
    res += buf
  return res

def inflate_vba (data):
  if ord(data[0]) != 1:
    print "Attempt to inflate wrong stream"
    return ""

  off = 1
  res = ""
  while off < len(data):
    flags = struct.unpack("<H",data[off:off+2])[0]
    cf = (flags&0xf000)/0x1000
    if cf == 0xb: #compressed
      clen = flags&0xfff
      res += inflate_vba_stream(data[off+2:off+2+clen+3])
      off += clen+5
    else:
      res += data[off+2:off+2+4095]
      off += 4095
  return res

# vsd inflate
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

# vsd deflate
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
