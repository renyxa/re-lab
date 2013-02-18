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

def inflate_vba_stream (data):
  i = 0
  pos = 0
  buf = ""
  res = ""
  while i < len(data):
    flag = ord(data[i])
    i += 1
    for mask in (1,2,4,8,16,32,64,128):
     try:
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
          srcpos = (pos - distance - 1) % 4096
          c = buf[srcpos]
          buf = buf[:pos % 4096] + c + buf[pos % 4096 + 1:]
          pos +=1
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
     except:
			 # FIXME!  Better handling of LZ stream ends?
       print "Not enough bytes to decompress. Flag/Mask were %02x/%02x"%(flag,mask)
       i += 1
       break
  if pos % 4096:
    res += buf
  return res

def inflate_vba_oletoy (data,ptype):
  if ord(data[0]) != 1:
    print "Attempt to inflate wrong stream"
    return ""

  off = 1
  res = ""
  while off < len(data):
    flags = struct.unpack("<H",data[off:off+2])[0]
    cf = (flags&0xf000)/0x1000
    clen = flags&0xfff
   
# to workaround MSOffice compression bugs.
# XLS is slightly different than PPT and DOC

    if cf == 0xb and clen > 0 and ((ptype[:3] != "XLS" and len(data)-off < 4096) or ptype[:3] == "XLS"):
      res += inflate_vba_stream(data[off+2:off+2+clen+1])
      off += clen+3
    else:
      res += inflate_vba_stream(data[off+2:off+4096])
      off += 4096
  return res

def inflate_vba_gsf (data,ptype):
  import ctypes as C
  cgsf = C.cdll.LoadLibrary('libgsf-1.so')
  cgsf.gsf_init()
  cgsf.gsf_input_memory_new.restype = C.c_void_p
  src = cgsf.gsf_input_memory_new (data,len(data),False)
  size = C.create_string_buffer(4)
  cgsf.gsf_vba_inflate.argtypes = [C.c_void_p,C.c_double,C.c_void_p,C.c_int]
  res = C.string_at(cgsf.gsf_vba_inflate(src,C.c_double(0),size,C.c_int(0)),struct.unpack("<I",size)[0])
  cgsf.gsf_shutdown()
  return res
  
def inflate_vba (data,ptype):
  return inflate_vba_gsf (data,ptype)
#    return inflate_vba_oletoy (data,ptype)

# vsd inflate
def inflate(ptr,vsd):
#    print "Inf %02x %02x %02x %02x %02x"%(ptr.type,ptr.address,ptr.offset,ptr.length,ptr.format),len(vsd)
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
                    dlen = (addr2&15) + 3
                    point = (addr2&240)*16+addr1
                    i = i + 2
                    if point > 4078:
                        point = point - 4078
                    else:
                        point = point + 18
                    for j in range (dlen):
                        buff[(pos+j)&4095]=buff[(point+j)&4095]
                        res = res + buff[(point+j)&4095]
                    pos = pos + dlen
        except:
            print 'Inflate failed',i,ptr.length
            return res
    return res

# vsd deflate
def deflate_piastre (buf, flavour=0):
  # 'compression' function which increase size of the result by 12.5%
  if flavour == 0:
    token = '\xFF'
  else:
    token = '\x00'
  i = 0
  res = ''
  while i< len(buf):
    res += token+buf[i:i+8]
    i +=8
  n = len(buf)-(len(buf)/8)*8
  res += '\x00'*n
  return res

def deflate (buf, flavour):
  # wrapper to avoid later renaming if I implement something better then 'piastre' ;-)
  return deflate_piastre (buf, flavour)
