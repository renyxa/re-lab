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

import sys,struct
import gtk
import tree
import hexdump
import ole
import zlib


rec_ids = {0x03E8:"RT_Document",
	0x03E9:"RT_DocumentAtom",
	0x03EA:"RT_EndDocumentAtom",
	0x03EE:"RT_Slide",
	0x03EF:"RT_SlideAtom",
	0x03F0:"RT_Notes",
	0x03F1:"RT_NotesAtom",
	0x03F2:"RT_Environment",
	0x03F3:"RT_SlidePersistAtom",
	0x03F8:"RT_MainMaster",
	0x03F9:"RT_SlideShowSlideInfoAtom",
	0x03FA:"RT_SlideViewInfo",
	0x03FB:"RT_GuideAtom",
	0x03FD:"RT_ViewInfoAtom",
	0x03FE:"RT_SlideViewInfoAtom",
	0x03FF:"RT_VbaInfo",
	0x0400:"RT_VbaInfoAtom",
	0x0401:"RT_SlideShowDocInfoAtom",
	0x0402:"RT_Summary",
	0x0406:"RT_DocRoutingSlipAtom",
	0x0407:"RT_OutlineViewInfo",
	0x0408:"RT_SorterViewInfo",
	0x0409:"RT_ExternalObjectList",
	0x040A:"RT_ExternalObjectListAtom",
	0x040B:"RT_DrawingGroup",
	0x040C:"RT_Drawing",
	0x040D:"RT_GridSpacing10Atom",
	0x040E:"RT_RoundTripTheme12Atom",
	0x040F:"RT_RoundTripColorMapping12Atom",
	0x0410:"RT_NamedShows",
	0x0411:"RT_NamedShow",
	0x0412:"RT_NamedShowSlidesAtom",
	0x0413:"RT_NotesTextViewInfo9",
	0x0414:"RT_NormalViewSetInfo9",
	0x0415:"RT_NormalViewSetInfo9Atom",
	0x041C:"RT_RoundTripOriginalMainMasterId12Atom",
	0x041D:"RT_RoundTripCompositeMasterId12Atom",
	0x041E:"RT_RoundTripContentMasterInfo12Atom",
	0x041F:"RT_RoundTripShapeId12Atom",
	0x0420:"RT_RoundTripHFPlaceholder12Atom",
	0x0422:"RT_RoundTripContentMasterId12Atom",
	0x0423:"RT_RoundTripOArtTextStyles12Atom",
	0x0424:"RT_RoundTripHeaderFooterDefaults12Atom",
	0x0425:"RT_RoundTripDocFlags12Atom",
	0x0426:"RT_RoundTripShapeCheckSumForCL12Atom",
	0x0427:"RT_RoundTripNotesMasterTextStyles12Atom",
	0x0428:"RT_RoundTripCustomTableStyles12Atom",
	0x07D0:"RT_List",
	0x07D5:"RT_FontCollection",
	0x07D6:"RT_FontCollection10",
	0x07E3:"RT_BookmarkCollection",
	0x07E4:"RT_SoundCollection",
	0x07E5:"RT_SoundCollectionAtom",
	0x07E6:"RT_Sound",
	0x07E7:"RT_SoundDataBlob",
	0x07E9:"RT_BookmarkSeedAtom",
	0x07F0:"RT_ColorSchemeAtom",
	0x07F8:"RT_BlipCollection9",
	0x07F9:"RT_BlipEntity9Atom",
	0x0BC1:"RT_ExternalObjectRefAtom",
	0x0BC3:"RT_PlaceholderAtom",
	0x0BDB:"RT_ShapeAtom",
	0x0BDC:"RT_ShapeFlags10Atom",
	0x0BDD:"RT_RoundTripNewPlaceholderId12Atom",
	0x0F9E:"RT_OutlineTextRefAtom",
	0x0F9F:"RT_TextHeaderAtom",
	0x0FA0:"RT_TextCharsAtom",
	0x0FA1:"RT_StyleTextPropAtom",
	0x0FA2:"RT_MasterTextPropAtom",
	0x0FA3:"RT_TextMasterStyleAtom",
	0x0FA4:"RT_TextCharFormatExceptionAtom",
	0x0FA5:"RT_TextParagraphFormatExceptionAtom",
	0x0FA6:"RT_TextRulerAtom",
	0x0FA7:"RT_TextBookmarkAtom",
	0x0FA8:"RT_TextBytesAtom",
	0x0FA9:"RT_TextSpecialInfoDefaultAtom",
	0x0FAA:"RT_TextSpecialInfoAtom",
	0x0FAB:"RT_DefaultRulerAtom",
	0x0FAC:"RT_StyleTextProp9Atom",
	0x0FAD:"RT_TextMasterStyle9Atom",
	0x0FAE:"RT_OutlineTextProps9",
	0x0FAF:"RT_OutlineTextPropsHeader9Atom",
	0x0FB0:"RT_TextDefaults9Atom",
	0x0FB1:"RT_StyleTextProp10Atom",
	0x0FB2:"RT_TextMasterStyle10Atom",
	0x0FB3:"RT_OutlineTextProps10",
	0x0FB4:"RT_TextDefaults10Atom",
	0x0FB5:"RT_OutlineTextProps11",
	0x0FB6:"RT_StyleTextProp11Atom",
	0x0FB7:"RT_FontEntityAtom",
	0x0FB8:"RT_FontEmbedDataBlob",
	0x0FBA:"RT_CString",
	0x0FC1:"RT_MetaFile",
	0x0FC3:"RT_ExternalOleObjectAtom",
	0x0FC8:"RT_Kinsoku",
	0x0FC9:"RT_Handout",
	0x0FCC:"RT_ExternalOleEmbed",
	0x0FCD:"RT_ExternalOleEmbedAtom",
	0x0FCE:"RT_ExternalOleLink",
	0x0FD0:"RT_BookmarkEntityAtom",
	0x0FD1:"RT_ExternalOleLinkAtom",
	0x0FD2:"RT_KinsokuAtom",
	0x0FD3:"RT_ExternalHyperlinkAtom",
	0x0FD7:"RT_ExternalHyperlink",
	0x0FD8:"RT_SlideNumberMetaCharAtom",
	0x0FD9:"RT_HeadersFooters",
	0x0FDA:"RT_HeadersFootersAtom",
	0x0FDF:"RT_TextInteractiveInfoAtom",
	0x0FE4:"RT_ExternalHyperlink9",
	0x0FE7:"RT_RecolorInfoAtom",
	0x0FEE:"RT_ExternalOleControl",
	0x0FF0:"RT_SlideListWithText",
	0x0FF1:"RT_AnimationInfoAtom",
	0x0FF2:"RT_InteractiveInfo",
	0x0FF3:"RT_InteractiveInfoAtom",
	0x0FF5:"RT_UserEditAtom",
	0x0FF6:"RT_CurrentUserAtom",
	0x0FF7:"RT_DateTimeMetaCharAtom",
	0x0FF8:"RT_GenericDateMetaCharAtom",
	0x0FF9:"RT_HeaderMetaCharAtom",
	0x0FFA:"RT_FooterMetaCharAtom",
	0x0FFB:"RT_ExternalOleControlAtom",
	0x1004:"RT_ExternalMediaAtom",
	0x1005:"RT_ExternalVideo",
	0x1006:"RT_ExternalAviMovie",
	0x1007:"RT_ExternalMciMovie",
	0x100D:"RT_ExternalMidiAudio",
	0x100E:"RT_ExternalCdAudio",
	0x100F:"RT_ExternalWavAudioEmbedded",
	0x1010:"RT_ExternalWavAudioLink",
	0x1011:"RT_ExternalOleObjectStg",
	0x1012:"RT_ExternalCdAudioAtom",
	0x1013:"RT_ExternalWavAudioEmbeddedAtom",
	0x1014:"RT_AnimationInfo",
	0x1015:"RT_RtfDateTimeMetaCharAtom",
	0x1018:"RT_ExternalHyperlinkFlagsAtom",
	0x1388:"RT_ProgTags",
	0x1389:"RT_ProgStringTag",
	0x138A:"RT_ProgBinaryTag",
	0x138B:"RT_BinaryTagDataBlob",
	0x1770:"RT_PrintOptionsAtom",
	0x1772:"RT_PersistDirectoryAtom",
	0x177A:"RT_PresentationAdvisorFlags9Atom",
	0x177B:"RT_HtmlDocInfo9Atom",
	0x177C:"RT_HtmlPublishInfoAtom",
	0x177D:"RT_HtmlPublishInfo9",
	0x177E:"RT_BroadcastDocInfo9",
	0x177F:"RT_BroadcastDocInfo9Atom",
	0x1784:"RT_EnvelopeFlags9Atom",
	0x1785:"RT_EnvelopeData9Atom",
	0x2AFB:"RT_VisualShapeAtom",
	0x2B00:"RT_HashCodeAtom",
	0x2B01:"RT_VisualPageAtom",
	0x2B02:"RT_BuildList",
	0x2B03:"RT_BuildAtom",
	0x2B04:"RT_ChartBuild",
	0x2B05:"RT_ChartBuildAtom",
	0x2B06:"RT_DiagramBuild",
	0x2B07:"RT_DiagramBuildAtom",
	0x2B08:"RT_ParaBuild",
	0x2B09:"RT_ParaBuildAtom",
	0x2B0A:"RT_LevelInfoAtom",
	0x2B0B:"RT_RoundTripAnimationAtom12Atom",
	0x2B0D:"RT_RoundTripAnimationHashAtom12Atom",
	0x2EE0:"RT_Comment10",
	0x2EE1:"RT_Comment10Atom",
	0x2EE4:"RT_CommentIndex10",
	0x2EE5:"RT_CommentIndex10Atom",
	0x2EE6:"RT_LinkedShape10Atom",
	0x2EE7:"RT_LinkedSlide10Atom",
	0x2EEA:"RT_SlideFlags10Atom",
	0x2EEB:"RT_SlideTime10Atom",
	0x2EEC:"RT_DiffTree10",
	0x2EED:"RT_Diff10",
	0x2EEE:"RT_Diff10Atom",
	0x2EEF:"RT_SlideListTableSize10Atom",
	0x2EF0:"RT_SlideListEntry10Atom",
	0x2EF1:"RT_SlideListTable10",
	0x2F14:"RT_CryptSession10Container",
	0x32C8:"RT_FontEmbedFlags10Atom",
	0x36B0:"RT_FilterPrivacyFlags10Atom",
	0x36B1:"RT_DocToolbarStates10Atom",
	0x36B2:"RT_PhotoAlbumInfo10Atom",
	0x36B3:"RT_SmartTagStore11Container",
	0x3714:"RT_RoundTripSlideSyncInfo12",
	0x3715:"RT_RoundTripSlideSyncInfoAtom12",
	
	0xF01A:"OfficeArtBlipEMF",
	0xF01B:"OfficeArtBlipWMF",
	0xF01C:"OfficeArtBlipPICT",
	0xF01D:"OfficeArtBlipJPEG",
	0xF01E:"OfficeArtBlipPNG",
	0xF01F:"OfficeArtBlipDIB",
	0xF029:"OfficeArtBlipTIFF",
	0xF02A:"OfficeArtBlipJPEG",
	
	0xF125:"RT_TimeConditionContainer",
	0xF127:"RT_TimeNode",
	0xF128:"RT_TimeCondition",
	0xF129:"RT_TimeModifier",
	0xF12A:"RT_TimeBehaviorContainer",
	0xF12B:"RT_TimeAnimateBehaviorContainer",
	0xF12C:"RT_TimeColorBehaviorContainer",
	0xF12D:"RT_TimeEffectBehaviorContainer",
	0xF12E:"RT_TimeMotionBehaviorContainer",
	0xF12F:"RT_TimeRotationBehaviorContainer",
	0xF130:"RT_TimeScaleBehaviorContainer",
	0xF131:"RT_TimeSetBehaviorContainer",
	0xF132:"RT_TimeCommandBehaviorContainer",
	0xF133:"RT_TimeBehavior",
	0xF134:"RT_TimeAnimateBehavior",
	0xF135:"RT_TimeColorBehavior",
	0xF136:"RT_TimeEffectBehavior",
	0xF137:"RT_TimeMotionBehavior",
	0xF138:"RT_TimeRotationBehavior",
	0xF139:"RT_TimeScaleBehavior",
	0xF13A:"RT_TimeSetBehavior",
	0xF13B:"RT_TimeCommandBehavior",
	0xF13C:"RT_TimeClientVisualElement",
	0xF13D:"RT_TimePropertyList",
	0xF13E:"RT_TimeVariantList",
	0xF13F:"RT_TimeAnimationValueList",
	0xF140:"RT_TimeIterateData",
	0xF141:"RT_TimeSequenceData",
	0xF142:"RT_TimeVariant",
	0xF143:"RT_TimeAnimationValue",
	0xF144:"RT_TimeExtTimeNodeContainer",
	0xF145:"RT_TimeSlaveContainer",
	}

def parse (page, data, parent):
	offset = 0
	try:
		while offset < len(data) - 4:
			verinst = struct.unpack("<H",data[offset:offset+2])[0]
			offset += 2
			rtype = struct.unpack("<H",data[offset:offset+2])[0]
			offset += 2
			rlen = struct.unpack("<I",data[offset:offset+4])[0]
			offset += 4
			rdata = data[offset-8:offset+rlen]
			iter1 = page.model.append(parent,None)
			rname = "%02x  ver %02x inst %02x"%(rtype,verinst&0xf,(verinst&0xFFF0)/0x10)
			if rec_ids.has_key(rtype):
				rname = rec_ids[rtype] + " ver %02x inst %02x"%(verinst&0xf,(verinst&0xFFF0)/0x10)
			page.model.set_value(iter1,0,rname)
			page.model.set_value(iter1,1,("ppt",rtype))
			page.model.set_value(iter1,2,rlen)
			page.model.set_value(iter1,3,rdata)
			page.model.set_value(iter1,7,"%02x"%rtype)
			page.model.set_value(iter1,6,page.model.get_string_from_iter(iter1))
			if rtype == 0x1011:
				if (verinst&0xFFF0)/0x10 == 1:
					decomp = zlib.decompressobj()
					uncompdata = decomp.decompress(data[offset+4:offset+rlen])
				else:
					uncompdata = data[offset+4:offset+rlen]
				ole.open(uncompdata,page,iter1)
			offset += rlen
	except:
		print "Failed in ppt parse"
