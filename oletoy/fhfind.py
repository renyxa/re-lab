#!/usr/bin/env python

import sys,struct,zlib

# find /home/frob/RTP/revenge/freehand/ -name "*.fh11" | xargs -i ./fhfind.py ConnectorLine {}



def parse(buf,rname):
	offset = buf.find('AGD')
	size = struct.unpack('>L', buf[offset+8:offset+12])[0]
	offset = offset + size
	dictoffset = offset

	dictsize = struct.unpack('>h', buf[offset:offset+2])[0]
	offset+=4
	rkey = -1
	for i in range(dictsize):
		key = struct.unpack('>h', buf[offset:offset+2])[0]
		k = 0
		while ord(buf[offset+k+2]) != 0:
			k+=1
		value = buf[offset+2:offset+k+2]
		if value == rname:
			rkey = key
		offset = offset+k+3

	size = struct.unpack('>L', buf[offset:offset+4])[0]
	offset+= 4
	agdoffset = 0
	length = 0

	for i in range(size):
		key = struct.unpack('>h', buf[offset:offset+2])[0]
		offset+= 2
		if key == rkey:
			return 1
	return 0

def main():
	if len(sys.argv) >= 3:
		filename = sys.argv[2]
		rname =  sys.argv[1]

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
