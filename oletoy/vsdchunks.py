# Copyright (C) 2007-2010,	Valek Filippov (frob@df.ru)
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

import vsdoc
import struct
import vsd

chunknoshift = {
            0x15:'Page',\
            0x18:'FontFaces',\
            0x1a:'Styles',\
            0x46:'PageSheet',\
            0x47:'ShapeType="Group"',\
            0x48:'ShapeType="Shape"',\
            0x4a:'StyleSheet',\
            0x4d:'ShapeType="Guide"',\
            0x4e:'ShapeType="Foreign"',\
            0x4f:'DocSheet'}
            
chunklist = {
            0x2c:'NameList',\
            0x64:'ScratchList',\
            0x65:'ShapeList',\
            0x67:'UserDefList',\
            0x68:'PropList',\
            0x69:'CharList',\
            0x6a:'ParaList',\
            0x6b:'TabsDataList',\
            0x6c:'GeomList',\
            0x6d:'CustPropsList',\
            0x6e:'ActIdList',\
            0x6f:'LayerList',\
            0x70:'CtrlList',\
            0x71:'CPntsList',
            0x76:'SmartTagList'}

chunktype = {
		0x0c:'FrgnData ',\
		0x0d:'OLE_List ',\
		0x0e:'Text IX  ',\
		0x10:'Data1    ',\
		0x11:'Data2    ',\
		0x12:'Data3    ',\
		0x15:'Page     ',\
		0x18:'FontFaces',\
		0x19:'FontFace ',\
		0x1a:'Styles   ',\
		0x1f:'OLE_Data ',\
		0x23:'Icon     ',\
		0x28:'Shape Stencil',\
		0x2c:'NameList ',\
		0x2d:'Name     ',\
		0x31:'Document ',\
		0x46:'PageSheet',\
		0x47:'ShapeType="Group"',\
		0x48:'ShapeType="Shape"',\
		0x4a:'StyleSheet',\
		0x4d:'ShapeType="Guide"',\
		0x4e:'ShapeType="Foreign"',\
		0x4f:'DocSheet ',\
		0x64:'ScratchList',\
		0x65:'ShapeList',\
		0x67:'UserDefList',\
		0x68:'PropList ',\
		0x69:'CharList ',\
		0x6a:'ParaList ',\
		0x6b:'TabsDataList',\
		0x6c:'GeomList ',\
		0x6d:'CustPropsList',\
		0x6e:'ActIdList',\
		0x6f:'LayerList',\
		0x70:'CtrlList ',\
		0x71:'CPntsList',\
		0x76:'SmartTagLst',\
		0x83:'ShapeID  ',\
		0x84:'Event    ',\
		0x85:'Line     ',
		0x86:'Fill     ',\
		0x87:'TextBlock',\
		0x88:'Tabs Data',\
		0x89:'Geometry ',\
		0x8a:'MoveTo   ',\
		0x8b:'LineTo   ',\
		0x8c:'ArcTo    ',\
		0x8d:'InfinLine',\
		0x8f:'Ellipse  ',\
		0x90:'EllpArcTo',\
		0x92:'PageProps',\
		0x93:'StyleProps',\
		0x94:'Char IX ',\
		0x95:'ParaIX  ',\
		0x96:'Tabs Data',\
		0x97:'Tabs Data',\
		0x98:'FrgnType',\
		0x99:'ConnectPts',\
		0x9b:'XForm   ',\
		0x9c:'TxtXForm',\
		0x9d:'XForm1D ',\
		0x9e:'Scratch ',\
		0xa0:'Protection',\
		0xa1:'TextFields',\
		0xa2:'Control ',\
		0xa3:'Help    ',\
		0xa4:'Misc    ',\
		0xa5:'SplineStart',\
		0xa6:'SplineKnot',\
		0xa7:'LayerMem',\
		0xa8:'LayerIX ',\
		0xa9:'Act ID  ',\
		0xaa:'Control ',\
		0xb4:'User-defined',\
		0xb5:'Tabs Data',\
		0xb6:'CustomProps',\
		0xb7:'RulerGrid',\
		0xb9:'ConnectionPoints',\
		0xba:'ConnectionPoints',\
		0xbb:'ConnectionPoints',\
		0xbc:'DocProps',\
		0xbd:'Image   ',\
		0xbe:'Group   ',\
		0xbf:'Layout  ',\
		0xc0:'PageLayout',\
		0xc1:'PolylineTo',\
		0xc3:'NURBSTo ',\
		0xc4:'Hyperlink',\
		0xc5:'Reviewer',\
		0xc6:'Annotation',\
		0xc7:'SmartTagDef',\
		0xc8:'PrintProps',\
		0xc9:'NameIDX ',\
		0xd1:'NRBSTo Data'}

def parse(model, version, parent, pntr):
	offset = 0
	tmppntr = vsd.pointer()
	tmppntr2 = vsd.pointer()
	path = parent
	path0 =  parent
	path1 =  parent
	path2 =  parent
#	path_pointer = 0
	level = 0
	while offset < len(pntr.data):
		try:
			chnk = vsdoc.chunk()
			if version<6:
				ch_hdr_len = 12
				trailer = 0
				[chnk.type] = struct.unpack('<h', pntr.data[offset:offset+2])
				if chnk.type == 0:
					 offset+=12
				else:
					[chnk.IX] = struct.unpack('<h', pntr.data[offset+2:offset+4])
					if chnk.IX == 0xffff:
						chnk.IX = -1
					chnk.level = ord(pntr.data[offset+4])
					chnk.unkn3 = ord(pntr.data[offset+5])
					[chnk.list] = struct.unpack('<h', pntr.data[offset+6:offset+8])
					[chnk.length] = struct.unpack('<L', pntr.data[offset+8:offset+12])
##				print 'T/IX/Lvl/Unk3/Lst/Len: %x %x %x %x %x %x'%(chnk.type,chnk.IX,chnk.level,chnk.unkn3,chnk.list,chnk.length),'DL/O: %x %x'%(len(pntr.data),offset)
			else:
				ch_hdr_len = 19
				[chnk.type] = struct.unpack('<L', pntr.data[offset:offset+4])
				if chnk.type == 0:
					offset+=4
				else:
					[chnk.IX] = struct.unpack('<L', pntr.data[offset+4:offset+8])
					if chnk.IX == 0xffffffff:
						chnk.IX = -1
					[chnk.list] = struct.unpack('<L', pntr.data[offset+8:offset+12])
					[chnk.length] = struct.unpack('<L', pntr.data[offset+12:offset+16])
					[chnk.level] = struct.unpack('<h', pntr.data[offset+16:offset+18])
					chnk.unkn3 = ord(pntr.data[offset+18])
					trailer = 0
					if (chnk.list != 0) or (chnk.type == 0x71) or (chnk.type==0x70):
						trailer = 8
					if (0x6b == chnk.type or 0x6a == chnk.type or 0x69 == chnk.type or 0x66 == chnk.type or 0x65 == chnk.type or 0x2c == chnk.type):
						trailer = 8
					
					if(11 == version): #/* separators were found only in Visio2k3 atm.  trailer means that there is a separator too. */
						if 0 != chnk.list or\
							(2 == chnk.level and 0x55 == chnk.unkn3) or\
							(2 == chnk.level and 0x54 == chnk.unkn3 and 0xaa == chnk.type) or\
							(3 == chnk.level and 0x50 != chnk.unkn3) or\
							(0x69 == chnk.type or 0x6a == chnk.type or 0x6b == chnk.type or 0x71 == chnk.type) or\
							(0xb4 == chnk.type or 0xb6 == chnk.type or 0xb9 == chnk.type or 0xa9 == chnk.type):
							trailer = trailer + 4
					if(11 == version and (0x1f == chnk.type or 0xc9 == chnk.type)):
						trailer = 0
						
			if level==0:
				level=chnk.level
			ptr = vsd.pointer()
			ptr.data = pntr.data[offset:offset+ch_hdr_len+chnk.length+trailer]
			offset = offset + ch_hdr_len+ chnk.length+trailer

			if chunktype.has_key(chnk.type):
				itername = '%-24s'%chunktype[chnk.type]+'(IX: %02x  Len: %02x Lvl: %u)'%(chnk.IX, chnk.length,chnk.level)
			else:
				itername = 'Type: %02x \t\tI/L List/Level/u3: %02x/%02x  %02x %02x %02x'%(chnk.type,chnk.IX,chnk.length,chnk.list,chnk.level,chnk.unkn3)
				
			if chnk.level ==0:
				path = path0
			if chnk.level ==1:
				path = path0
			if chnk.level == 2:
				path = path1
			if chnk.level == 3:
				path = path2
				
#			ptr.path = path			
			iter1 = model.append(path, None)
			model.set_value(iter1,0,itername)
			model.set_value(iter1,1,("vsd","chnk",chnk.type))
			model.set_value(iter1,2,len(ptr.data))
			model.set_value(iter1,3,ptr.data)
			model.set_value(iter1,4,ptr)

			if chnk.level ==0:
				path0 = iter1
			if chnk.level ==1:
				path1 = iter1
			if chnk.level == 2:
				path2 = iter1

		except:
			name = model.get_value(parent,0)
			print 'Something wrong with chunks',name,'%x'%offset
			offset = offset + ch_hdr_len
	return
