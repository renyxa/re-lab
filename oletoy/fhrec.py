#!/usr/bin/env python

import sys,struct,zlib
import fh

ver = {0x31:5,0x32:7,0x33:8,0x34:9,0x35:10,0x36:11,'mcl':-1}

def d2hex(data,space="",ln=0):
	s = ""
	for i in range(len(data)):
		s += "%02x%s"%(ord(data[i]),space)
		if ln != 0 and (i % ln) == 0:
			s += "\n"
			
	return s


def parse_agd (FHDoc,rname,dumpsize):
	offset = 0
	j = 0
	for i in FHDoc.reclist:
		j += 1
		if FHDoc.dictitems[i] in FHDoc.chunks:
			try:
				res = FHDoc.chunks[FHDoc.dictitems[i]](offset,j)
				if -1 < res <= len(FHDoc.data)-offset:
					if rname == "*" or FHDoc.dictitems[i] == rname:
						print "%-16s [%4x] "%(FHDoc.dictitems[i],res),"%02x\t"%j,d2hex(FHDoc.data[offset:offset+dumpsize]," ")
					offset += res
				else:
					print "Failed on record %d (%s)"%(j,FHDoc.dictitems[i]),res
					print "Next is",FHDoc.dictitems[FHDoc.reclist[j+1]]
					return
			except:
				print "Failed on record %d (%s)"%(j,FHDoc.dictitems[i])
				print "Next is",FHDoc.dictitems[FHDoc.reclist[j+1]]
				return
				
		else:
				print "Unknown record type: %s (%02x)"%(FHDoc.dictitems[i],j)
				return
	print "FH Tail!"

def parse_dict (FHDoc,data,offset):
	if FHDoc.version > 8:
		dictsize = struct.unpack('>h', data[offset:offset+2])[0]
		print 'Dict size:\t%u'%dictsize
		offset+=4
		for i in range(dictsize):
			key = struct.unpack('>h', data[offset:offset+2])[0]
			k = 0
			while ord(data[offset+k+2]) != 0:
				k+=1
			value = data[offset+2:offset+k+2]
			offset = offset+k+3
			FHDoc.dictitems[key] = value
	return offset

def parse(buf,rname,dumpsize=8):
	offset = buf.find('AGD')
	version = ver[ord(buf[offset+3])]
	size = struct.unpack('>L', buf[offset+8:offset+12])[0]
	if version > 8:
		output = zlib.decompress(buf[offset+14:offset+14+size],-15)
	else:
		output = buf[offset+12:offset+size]
	doc = fh.FHDoc(output,None,None)
	doc.version = version
	offset = offset + size
	offset = parse_dict(doc,buf,offset)
	doc.parse_list(buf,offset)
	parse_agd(doc,rname,dumpsize)


def main():
	if len(sys.argv) >= 3:
		filename = sys.argv[2]
		rname =  sys.argv[1]
		print filename
		try:
			input = open(filename)
			buf = input.read()
			if parse(buf,rname):
				print filename
		except:
			print "No file"
			return 0
	else:
		print "Use filename as an option"
		return

if __name__ == '__main__':
	main()
