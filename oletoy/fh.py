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
#

import sys,struct,tree,zlib,fhparse

chunks = { "BrushTip":fhparse.BrushTip, "Brush":fhparse.Brush, "VDict":fhparse.VDict, "UString":fhparse.UString, "SymbolClass":fhparse.SymbolClass,\
				"PerspectiveGrid":fhparse.PerspectiveGrid,"MpObject":fhparse.MpObject,"MString":fhparse.MString,"MList":fhparse.MList,"MDict":fhparse.MDict,\
				"DateTime":fhparse.DateTime,"FHDocHeader":fhparse.FHDocHeader,"Block":fhparse.Block,"Element":fhparse.Element,"BrushList":fhparse.BrushList,\
				"VMpObj":fhparse.VMpObj,"AGDFont":fhparse.AGDFont,"FileDescriptor":fhparse.FileDescriptor,"TabTable":fhparse.TabTable,\
				"SymbolLibrary":fhparse.SymbolLibrary,"PropLst":fhparse.PropLst,"Procedure":fhparse.Procedure,"Color6":fhparse.Color6,"Data":fhparse.Data,\
				"MName":fhparse.MName,"List":fhparse.List,"LinePat":fhparse.LinePat,"ElemList":fhparse.ElemList,"ElemPropLst":fhparse.ElemPropLst,"Figure":fhparse.Figure,\
				"StylePropLst":fhparse.StylePropLst,"SpotColor6":fhparse.SpotColor6,"BasicLine":fhparse.BasicLine,"BasicFill":fhparse.BasicFill,\
				"Guides":fhparse.Guides,"Path":fhparse.Path,"Collector":fhparse.Collector,"Rectangle":fhparse.Rectangle,"Layer":fhparse.Layer,\
				"ArrowPath":fhparse.ArrowPath,"Group":fhparse.Group,"Xform":fhparse.Xform,"Oval":fhparse.Oval,"MultiColorList":fhparse.MultiColorList,\
				"ContourFill":fhparse.ContourFill,"ClipGroup":fhparse.ClipGroup,"NewBlend":fhparse.NewBlend,"BrushStroke":fhparse.BrushStroke,\
				"GraphicStyle":fhparse.GraphicStyle,"ContentFill":fhparse.ContentFill,"AttributeHolder":fhparse.AttributeHolder,\
				"FWShadowFilter":fhparse.FWShadowFilter,"FilterAttributeHolder":fhparse.FilterAttributeHolder,\
				"FWBevelFilter":fhparse.FWBevelFilter,"Extrusion":fhparse.Extrusion,"LinearFill":fhparse.LinearFill,\
				"CompositePath":fhparse.CompositePath,"GradientMaskFilter":fhparse.GradientMaskFilter,"DataList":fhparse.DataList,\
				"ImageImport":fhparse.ImageImport,"TextBlok":fhparse.TextBlok,"Paragraph":fhparse.Paragraph,"TString":fhparse.TString,\
				"LineTable":fhparse.LineTable,"TextColumn":fhparse.TextColumn,"RadialFillX":fhparse.RadialFillX,"TaperedFillX":fhparse.TaperedFillX,\
				"TintColor6":fhparse.TintColor6,"TaperedFill":fhparse.TaperedFill,"LensFill":fhparse.LensFill,"SymbolInstance":fhparse.SymbolInstance,\
				"BendFilter":fhparse.BendFilter, "TransformFilter":fhparse.TransformFilter,"NewContourFill":fhparse.NewContourFill,\
				"RaggedFilter":fhparse.RaggedFilter,"NewRadialFill":fhparse.NewRadialFill,"SketchFilter":fhparse.SketchFilter,\
				"ExpandFilter":fhparse.ExpandFilter,"ConeFill":fhparse.ConeFill, "DuetFilter":fhparse.DuetFilter, "TileFill":fhparse.TileFill,\
				"OpacityFilter":fhparse.OpacityFilter,"FWBlurFilter":fhparse.FWBlurFilter,"FWGlowFilter":fhparse.FWGlowFilter,"TFOnPath":fhparse.TFOnPath,\
				"CharacterFill":fhparse.CharacterFill,"FWFeatherFilter":fhparse.FWFeatherFilter, "PolygonFigure":fhparse.PolygonFigure,\
				"CalligraphicStroke":fhparse.CalligraphicStroke, "Envelope":fhparse.Envelope, "PathTextLineInfo":fhparse.PathTextLineInfo,\
				"PatternFill":fhparse.PatternFill,"FWSharpenFilter":fhparse.FWSharpenFilter,"RadialFill":fhparse.RadialFill,"SwfImport":fhparse.SwfImport,\
				"PerspectiveEnvelope":fhparse.PerspectiveEnvelope,"MultiBlend":fhparse.MultiBlend, "MasterPageElement":fhparse.MasterPageElement,\
				"MasterPageDocMan":fhparse.MasterPageDocMan,"MasterPageSymbolClass":fhparse.MasterPageSymbolClass, "MasterPageLayerElement":fhparse.MasterPageLayerElement,\
				"MQuickDict":fhparse.MQuickDict,"TEffect":fhparse.TEffect, "MasterPageSymbolInstance":fhparse.MasterPageSymbolInstance,\
				"MasterPageLayerInstance":fhparse.MasterPageLayerInstance, "TextInPath":fhparse.TextInPath, "ImageFill":fhparse.ImageFill}

ver = {0x31:5,0x32:7,0x33:8,0x34:9,0x35:10,0x36:11,'mcl':-1}


def open (buf,page):
	iter1 = page.model.append(None,None)
	page.model.set_value(iter1,0,"FH file")
	page.model.set_value(iter1,1,("fh","file"))
	page.model.set_value(iter1,2,len(buf))
	page.model.set_value(iter1,3,buf)
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))

	offset = buf.find('AGD')
	page.version = ver[ord(buf[offset+3])]
	print 'Version:\t',page.version
	print 'Offset: \t%x'%offset
	[size] = struct.unpack('>L', buf[offset+8:offset+12])
	print 'Size:\t\t%x'%size
	iter1 = page.model.append(None,None)
	page.model.set_value(iter1,0,"FH Header")
	page.model.set_value(iter1,1,("fh","header"))
	page.model.set_value(iter1,2,12)
	page.model.set_value(iter1,3,buf[offset:offset+12])
	page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
	output = zlib.decompress(buf[offset+14:offset+14+size],-15)
	offset = offset + size
	dditer = page.model.append(None,None)
	page.model.set_value(dditer,0,"FH Decompressed Data")
	page.model.set_value(dditer,1,("fh","data"))
	page.model.set_value(dditer,2,size)
	page.model.set_value(dditer,3,output)
	page.model.set_value(dditer,6,page.model.get_string_from_iter(dditer))
	
	dictsize = struct.unpack('>h', buf[offset:offset+2])[0]
	print 'Dict size:\t%u'%dictsize
	dictiter = page.model.append(None,None)
	page.model.set_value(dictiter,0,"FH Dictionary")
	page.model.set_value(dictiter,1,("fh","dict"))
	page.model.set_value(dictiter,2,dictsize+4)
	page.model.set_value(dictiter,3,buf[offset:offset+dictsize+4])
	page.model.set_value(dictiter,6,page.model.get_string_from_iter(dictiter))
	offset+=4
	items = {}
	for i in range(dictsize):
		[key] = struct.unpack('>h', buf[offset:offset+2])
		k = 0
		while ord(buf[offset+k+2]) != 0:
			k+=1
		value = buf[offset+2:offset+k+2]
		niter = page.model.append(dictiter,None)
		page.model.set_value(niter,0,"%04x %s"%(key,value))
		page.model.set_value(niter,1,("fh","dval"))
		page.model.set_value(niter,2,k+3)
		page.model.set_value(niter,3,buf[offset:offset+k+3])
		page.model.set_value(niter,6,page.model.get_string_from_iter(niter))
		offset = offset+k+3
		items[key] = value
	[size] = struct.unpack('>L', buf[offset:offset+4])
	print '# of items:\t%u'%size
	page.dict = items
	offset+= 4

	parser = fhparse.parser()
	parser.data = output
	parser.version = page.version
	parser.iter = dditer
	unkn_flag = 0
	agdoffset = 0
	length = 0

	for i in range(size):
		[key] = struct.unpack('>h', buf[offset:offset+2])
		offset+= 2
		if chunks.has_key(items[key]):
			if unkn_flag == 0:
				try:
					length = chunks[items[key]](parser,agdoffset, key)
				except:
					print "Failed to parse. Chunk: %02x 2:%s"%(i,i-1)
					return
			else:
				length = 128
				if agdoffset + length > len(output):
					length = len(output) - agdoffset
				# later will implement search for easy detectable chunks
			iname = items[key]
			iter1 = page.model.append(dditer,None)
			page.model.set_value(iter1,0,"%s [%02x]"%(iname,i+1))
			page.model.set_value(iter1,1,("fh",iname))
			page.model.set_value(iter1,2,length)
			page.model.set_value(iter1,3,output[agdoffset:agdoffset+length])
			page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
			agdoffset = agdoffset + length
			
		else:
			print 'WARNING! Unknown key: ',items[key],"%02x %02x"%(i+1,agdoffset)
			unkn_flag = 1
			length = 128
			if agdoffset + length > len(output):
				length = len(output) - agdoffset
			iname = items[key]
			name = "%02x: "%(i+1)+" !!! " + iname+"\t0x%02x"%length+"\t0x%02x"%agdoffset+" <-------"
			iter1 = page.model.append(dditer,None)
			page.model.set_value(iter1,0,name)
			page.model.set_value(iter1,1,("fh","unknown"))
			page.model.set_value(iter1,2,length)
			page.model.set_value(iter1,3,output[agdoffset:agdoffset+length])
			page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
