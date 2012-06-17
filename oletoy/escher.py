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

import sys,struct
import gobject
import gtk
import tree
import hexdump
from utils import *


escher_opids = {
0x0000:'left',0x0001:'top',0x0002:'right',0x0003:'bottom',0x0004:'rotation',
0x0005:'gvPage',0x003F:'XFormBoolProps',
0x007F:'ProtectionBoolProps',0x0080:'ITxid',
0x0081:'dxTextLeft',0x0082:'dyTextTop',0x0083:'dxTextRight',0x0084:'dyTextBottom',
0x0085:'WrapText',0x0086:'unused134',0x0087:'anchorText',0x0088:'txflTextFlow',
0x0089:'cdirFont',0x008A:'hspNext',0x008B:'txdir',0x008C:'unused140',
0x008D:'unused141',0x00BF:'txBoolProps',0x00C0:'gtextUNICODE',0x00C2:'gtextAlign',
0x00C3:'gtextSize',0x00C4:'gtextSpacing',0x00C5:'gtextFont',0x00C6:'gtextCSSFont',
0x00FF:'gtextBoolProps',0x0100:'cropFromTop',0x0101:'cropFromBottom',0x0102:'cropFromLeft',
0x0103:'cropFromRight',0x0104:'pib',0x0105:'pibName',0x0106:'pibFlags',
0x0107:'pictureTransparent',0x0108:'pictureContrast',0x0109:'pictureBrightness',
0x010B:'pictureId',0x010C:'pictureDblCrMod',0x010D:'pictureFillCrMod',
0x010E:'pictureLineCrMod',0x010F:'pibPrint',0x0110:'pibPrintName',
0x0111:'pibPrintFlags',0x0112:'movie',0x0115:'pictureTransparentExt',
0x0116:'reserved278',0x0117:'pictureTransparentExtMod',0x0118:'reserved280',
0x0119:'reserved281',0x011A:'pictureRecolor',0x011B:'pictureRecolorExt',
0x011C:'reserved284',0x011D:'pictureRecolorExtMod',0x011E:'reserved286',
0x011F:'reserved287',0x013F:'BlipBoolProps',
0x0140:'geoLeft', 0x0141:'geoTop',0x0142:'geoRight',0x0143:'geoBottom',
0x0144:'shapePath',0x0145:'pVertices',0x0146:'pSegmentInfo',
0x0147:'adjustValue',0x0148:'adjust2Value',0x0149:'adjust3Value',
0x014A:'adjust4Value',0x014B:'adjust5Value',0x014C:'adjust6Value',
0x014D:'adjust7Value',0x014E:'adjust8Value',0x0151:'pConnectionSites',
0x0152:'pConnectionSitesDir',0x0153:'xLimo',0x0154:'yLimo',
0x0155:'pAdjustHandles',0x0156:'pGuides',0x0157:'pInscribe',
0x0158:'cxk',0x017F:'GeomBoolProps',0x0180:'fillType',0x0181:'fillColor',
0x0182:'fillOpacity',0x0183:'fillBackColor',0x0184:'fillBackOpacity',
0x0185:'fillCrMod',0x0186:'fillBlip',0x0187:'fillBlipName',
0x0188:'fillBlipFlags',0x0189:'fillWidth',0x018A:'fillHeight',
0x018B:'fillAngle',0x018C:'fillFocus',0x018D:'fillToLeft',
0x018E:'fillToTop',0x018F:'fillToRight',0x0190:'fillToBottom',
0x0191:'fillRectLeft',0x0192:'fillRectTop',0x0193:'fillRectRight',
0x0194:'fillRectBottom',0x0195:'fillDztype',0x0196:'fillShadePreset',
0x0197:'fillShadeColors',0x0198:'fillOriginX',0x0199:'fillOriginY',
0x019A:'fillShapeOriginX',0x019B:'fillShapeOriginY',0x019C:'fillShadeType',
0x019E:'fillColorExt',0x019F:'reserved415',0x01A0:'fillColorExtMod',
0x01A1:'reserved417',0x01A2:'fillBackColorExt',0x01A3:'reserved419',
0x01A4:'fillBackColorExtMod',0x01A5:'reserved421',0x01A6:'reserved422',
0x01A7:'reserved423',0x01BF:'FillStyleBoolProps',0x01C0:'lineColor',
0x01C1:'lineOpacity',0x01C2:'lineBackColor',0x01C3:'lineCrMod',
0x01C4:'lineType',0x01C5:'lineFillBlip',0x01C6:'lineFillBlipName',
0x01C7:'lineFillBlipFlags',0x01C8:'lineFillWidth',0x01C9:'lineFillHeight',
0x01CA:'lineFillDztype',0x01CB:'lineWidth',0x01CC:'lineMiterLimit',
0x01CD:'lineStyle',0x01CE:'lineDashing',0x01CF:'lineDashStyle',
0x01D0:'lineStartArrowhead',0x01D1:'lineEndArrowhead',0x01D2:'lineStartArrowWidth',
0x01D3:'lineStartArrowLength',0x01D4:'lineEndArrowWidth',0x01D5:'lineEndArrowLength',
0x01D6:'lineJoinStyle',0x01D7:'lineEndCapStyle',0x01D9:'lineColorExt',
0x01DA:'reserved474',0x01DB:'lineColorExtMod',0x01DC:'reserved476',
0x01DD:'lineBackColorExt',0x01DE:'reserved478',0x01DF:'lineBackColorExtMod',
0x01E0:'reserved480',0x01E1:'reserved481',0x01E2:'reserved482',
0x01FF:'LineStyleBoolProps',
0x0200:'shadowType',0x0201:'shadowColor',0x0202:'shadowHighlight',
0x0203:'shadowCrMod',0x0204:'shadowOpacity',0x0205:'shadowOffsetX',
0x0206:'shadowOffsetY',0x0207:'shadowSecondOffsetX',0x0208:'shadowSecondOffsetY',
0x0210:'shadowOriginX',0x0211:'shadowOriginY',0x0212:'shadowColorExt',
0x0213:'reserved531',0x0214:'shadowColorExtMod',0x0215:'reserved533',
0x0216:'shadowHighlightExt',0x0217:'reserved535',0x0218:'shadowHighlightExtMod',
0x0219:'reserved537',0x021A:'reserved538',0x021B:'reserved539',
0x021C:'shadowSoftness',0x023F:'ShadowStyleBoolProps',0x0240:'perspectiveType',
0x0241:'perspectiveOffsetX',0x0242:'perspectiveOffsetY',0x0243:'perspectiveScaleXToX',
0x0244:'perspectiveScaleYToX',0x0245:'perspectiveScaleXToY',0x0246:'perspectiveScaleYToY',
0x0247:'perspectivePerspectiveX',0x0248:'perspectivePerspectiveY',
0x0249:'perspectiveWeight',0x024A:'perspectiveOriginX',
0x024B:'perspectiveOriginY',0x027F:'PerspectiveStyleBoolProps',
0x0280:'c3DSpecularAmt',0x0281:'c3DDiffuseAmt',0x0282:'c3DShininess',
0x0283:'c3DEdgeThickness',0x0284:'c3DExtrudeForward',0x0285:'c3DExtrudeBackward',
0x0286:'reserved646',0x0287:'c3DExtrusionColor',0x0288:'c3DCrMod',
0x0289:'c3DExtrusionColorExt',0x028A:'reserved650',0x028B:'c3DExtrusionColorExtMod',
0x028C:'reserved652',0x028D:'reserved653',0x02BF:'3dObjBoolProps',
0x02C0:'c3DYRotationAngle',0x02C1:'c3DXRotationAngle',0x02C2:'c3DRotationAxisX',
0x02C3:'c3DRotationAxisY',0x02C4:'c3DRotationAxisZ',0x02C5:'c3DRotationAngle',
0x02C6:'c3DRotationCenterX',0x02C7:'c3DRotationCenterY',0x02C8:'c3DRotationCenterZ',
0x02C9:'c3DRenderMode',0x02CA:'c3DTolerance',0x02CB:'c3DXViewpoint',
0x02CC:'c3DYViewpoint',0x02CD:'c3DZViewpoint',0x02CE:'c3DOriginX',
0x02CF:'c3DOriginY',0x02D0:'c3DSkewAngle',0x02D1:'c3DSkewAmount',
0x02D2:'c3DAmbientIntensity',0x02D3:'c3DKeyX',0x02D4:'c3DKeyY',
0x02D5:'c3DKeyZ',0x02D6:'c3DKeyIntensity',0x02D7:'c3DFillX',
0x02D8:'c3DFillY',0x02D9:'c3DFillZ',0x02DA:'c3DFillIntensity',
0x02FF:'3dStyleBoolProps', 0x0301:'hspMaster',0x0303:'cxstyle',
0x0304:'bWMode',0x0305:'bWModePureBW',0x0306:'bWModeBW',
0x0307:'idDiscussAnchor',0x0309:'dgmLayout',0x030A:'dgmNodeKind',
0x030B:'dgmLayoutMRU',0x030C:'equationXML',0x033F:'ShapeBoolProps',
0x0340:'unused832',0x0341:'dxyCalloutGap',0x0342:'spcoa',
0x0343:'spcod',0x0344:'dxyCalloutDropSpecified',0x0345:'dxyCalloutLengthSpecified',
0x037F:'CalloutBoolProps',0x0380:'wzName',0x0381:'wzDescription',
0x0382:'pihlShape',0x0383:'pWrapPolygonVertices',0x0384:'dxWrapDistLeft',
0x0385:'dyWrapDistTop',0x0386:'dxWrapDistRight',0x0387:'dyWrapDistBottom',
0x0388:'lidRegroup',0x038A:'unused906',0x038D:'wzTooltip',
0x038E:'wzScript',0x038F:'posh',0x0390:'posrelh',0x0391:'posv',
0x0392:'posrelv',0x0393:'pctHR',0x0394:'alignHR',0x0395:'dxHeightHR',
0x0396:'dxWidthHR',0x0397:'wzScriptExtAttr',0x0398:'scriptLang',
0x039A:'wzScriptLangAttr',0x039B:'borderTopColor',0x039C:'borderLeftColor',
0x039D:'borderBottomColor',0x039E:'borderRightColor',0x039F:'tableProperties',
0x03A0:'tableRowProperties',0x03A5:'wzWebBot',0x03A9:'metroBlob',
0x03AA:'dhgt',0x03BF:'GroupShapeBoolProps',
0x03C0:'relLeft',0x03C1:'relTop', 0x03C2:'relRight',0x03C3:'relBottom',
0x03C4:'relRotation',0x03C5:'gvRelPage', 0x03FF:'relXFormBoolProps',
0x0402:'wzLineId',0x0403:'wzFillId', 0x0404:'wzPictureId',0x0405:'wzPathId',
0x0406:'wzShadowId',0x0407:'wzPerspectiveId', 0x0408:'wzGtextId',
0x0409:'wzFormulaeId',0x040A:'wzHandlesId',0x040B:'wzCalloutId',
0x040C:'wzLockId',0x040D:'wzTextId',0x040E:'wzThreeDId',0x043F:'wzBoolProps',
0x0500:'dgmt',0x0501:'dgmStyle',0x0504:'pRelationTbl',
0x0505:'dgmScaleX',0x0506:'dgmScaleY',0x0507:'dgmDefaultFontSize',
0x0508:'dgmConstrainBounds',0x0509:'dgmBaseTextScale',0x053F:'dgmBoolProps',
0x0540:'lineLeftColor',0x0541:'lineLeftOpacity',
0x0542:'lineLeftBackColor',0x0543:'lineLeftCrMod',0x0544:'lineLeftType',
0x0545:'lineLeftFillBlip',0x0546:'lineLeftFillBlipName',0x0547:'lineLeftFillBlipFlags',
0x0548:'lineLeftFillWidth',0x0549:'lineLeftFillHeight',0x054A:'lineLeftFillDztype',
0x054B:'lineLeftWidth',0x054C:'lineLeftMiterLimit',0x054D:'lineLeftStyle',
0x054E:'lineLeftDashing',0x054F:'lineLeftDashStyle',0x0550:'lineLeftStartArrowhead',
0x0551:'lineLeftEndArrowhead',0x0552:'lineLeftStartArrowWidth',0x0553:'lineLeftStartArrowLength',
0x0554:'lineLeftEndArrowWidth',0x0555:'lineLeftEndArrowLength',0x0556:'lineLeftJoinStyle',
0x0557:'lineLeftEndCapStyle',0x0559:'lineLeftColorExt',0x055A:'reserved1370',
0x055B:'lineLeftColorExtMod',0x055C:'reserved1372',0x055D:'lineLeftBackColorExt',
0x055E:'reserved1374',0x055F:'lineLeftBackColorExtMod',0x0560:'reserved1376',
0x0561:'reserved1377',0x0562:'reserved1378',0x057F:'LeftLineStyleBoolProps',
0x0580:'lineTopColor',0x0581:'lineTopOpacity',0x0582:'lineTopBackColor',
0x0583:'lineTopCrMod',0x0584:'lineTopType',0x0585:'lineTopFillBlip',
0x0586:'lineTopFillBlipName',0x0587:'lineTopFillBlipFlags',0x0588:'lineTopFillWidth',
0x0589:'lineTopFillHeight',0x058A:'lineTopFillDztype',0x058B:'lineTopWidth',
0x058C:'lineTopMiterLimit',0x058D:'lineTopStyle',0x058E:'lineTopDashing',
0x058F:'lineTopDashStyle',0x0590:'lineTopStartArrowhead',0x0591:'lineTopEndArrowhead',
0x0592:'lineTopStartArrowWidth',0x0593:'lineTopStartArrowLength',
0x0594:'lineTopEndArrowWidth',0x0595:'lineTopEndArrowLength',
0x0596:'lineTopJoinStyle',0x0597:'lineTopEndCapStyle',
0x0598:'lineTopColorExt',0x059A:'reserved1434',
0x059B:'lineTopColorExtMod',0x059C:'reserved1436',
0x059D:'lineTopBackColorExt',0x059E:'reserved1438',
0x059F:'lineTopBackColorExtMod',0x05A0:'reserved1440',
0x05A1:'reserved1441',0x05A2:'reserved1442',0x05BF:'TopLineStyleProps',
0x05C0:'lineRightColor',0x05C1:'lineRighOpacity',0x05C2:'lineRightBackColor',
0x05C3:'lineRightCrMod',0x05C4:'lineRightType',0x05C5:'lineRightFillBlip',
0x05C6:'lineRightFillBlipName',0x05C7:'lineRightFillBlipFlags',
0x05C8:'lineRightFillWidth',0x05C9:'lineRightFillHeight',
0x05CA:'lineRightFillDztype',0x05CB:'lineRightWidth',0x05CC:'lineRightMiterLimit',
0x05CD:'lineRightStyle',0x05CE:'lineRightDashing',0x05CF:'lineRightDashStyle',
0x05D0:'lineRightStartArrowhead',0x05D1:'lineRightEndArrowhead',
0x05D2:'lineRightStartArrowWidth',0x05D3:'lineRightStartArrowLength',
0x05D4:'lineRightEndArrowWidth',0x05D5:'lineRightEndArrowLength',
0x05D6:'lineRightJoinStyle',0x05D7:'lineRightEndCapStyle',
0x05D9:'lineRightColorExt',0x059A:'reserved1498',0x05DB:'lineRightColorExtMod',
0x05DC:'reserved1500',0x05DD:'lineRightBackColorExt',0x05DE:'reserved1502',
0x05DF:'lineRightBackColorExtMod',0x05E0:'reserved1504',0x05E1:'reserved1505',
0x05E2:'reserved1506',0x05FF:'RightLineStyleBoolProps',0x0600:'lineBottomColor',
0x0601:'lineRighOpacity',0x0602:'lineBottomBackColor',0x0603:'lineBottomCrMod',
0x0604:'lineBottomType',0x0605:'lineBottomFillBlip',0x0606:'lineBottomFillBlipName',
0x0607:'lineBottomFillBlipFlags',0x0608:'lineBottomFillWidth',
0x0609:'lineBottomFillHeight',0x060A:'lineBottomFillDztype',
0x060B:'lineBottomWidth',0x060C:'lineBottomMiterLimit',0x060D:'lineBottomStyle',
0x060E:'lineBottomDashing',0x060F:'lineBottomDashStyle',0x0610:'lineBottomStartArrowhead',
0x0611:'lineBottomEndArrowhead',0x0612:'lineBottomStartArrowWidth',
0x0613:'lineBottomStartArrowLength',0x0614:'lineBottomEndArrowWidth',
0x0615:'lineBottomEndArrowLength',0x0616:'lineBottomJoinStyle',
0x0617:'lineBottomEndCapStyle',0x0619:'lineBottomColorExt',
0x061A:'reserved1562',0x061B:'lineBottomColorExtMod',0x061C:'reserved1564',
0x061D:'lineBottomBackColorExt',0x061E:'reserved1566',
0x061F:'lineBottomBackColorExtMod',0x0620:'reserved1568',
0x0621:'reserved1569',0x0622:'reserved1570',0x063F:'BottomLineStyleBoolProps',
0x0680:'webComponentWzHtml',0x0681:'webComponentWzName',0x0682:'webComponentWzUrl',
0x06BF:'webComponentBoolProps',0x0700:'pInkData',0x073F:'pinkBoolProps',
0x0781:'wzSigSetupId',0x0782:'wzSigSetupProvId',0x0783:'wzSigSetupSuggSigner',
0x0784:'wzSigSetupSuggSigner2',0x0785:'wzSigSetupSuggSignerEmail',
0x0786:'wzSigSetupSignInst',0x0787:'wzSigSetupAddlXml',0x0788:'wzSigSetupProvUrl',
0x07BF:'wzSigBoolProps', 0x07C0:'pctHoriz', 0x07C1:'pctVert',
0x07C2:'pctHorizPos',0x07C3:'pctVertPos', 0x07C4:'sizerelh',0x07C5:'sizerelv',
# guesses by frob
0x4104:'PXid',
0x4186:'bgPXid',
0xC0C0:'TextLength',
0xC0C5:'FontNameLength',
0xc105:'NameLength',
0xc187:'bgNameLength',
0xc680:'bookmarkLength',
0xc681:'bookmarkNameLength',
0x06FF:'unk06ff_BoolProps',
0xc383:'wrapPtsLength'
}
#0xc382 -- describes length of some Hyperlink-related structure at the end of the chunk, similar to 0xc105
#			but it's more than just string

msospt = {
0x00:'NotPrimitive',0x01:'Rectangle',0x02:'RoundRectangle',0x03:'Ellipse',
0x04:'Diamond',0x05:'IsocelesTriangle',0x06:'RightTriangle',0x07:'Parallelogram',
0x08:'Trapezoid',0x09:'Hexagon',0x0A:'Octagon',0x0B:'Plus',0x0C:'Star',0x0D:'Arrow',
0x0E:'DontUseThickArrow',0x0F:'HomePlate',0x10:'Cube',0x11:'Balloon',
0x12:'Seal',0x13:'Arc',0x14:'Line',0x15:'Plague',0x16:'Can',0x17:'Donut',
0x18:'TextSimple',0x19:'TextOctagon',0x1A:'TextHexagon',0x1B:'TextCurve',
0x1C:'TextWave',0x1D:'TextRing',0x1E:'TextOnCurve',0x1F:'TextOnRing',
0x20:'StraightConnector1',0x21:'BentConnector2',0x22:'BentConnector3',
0x23:'BentConnector4',0x24:'BentConnector5',0x25:'CurvedConnector2',
0x26:'CurvedConnector3',0x27:'CurvedConnector4',0x28:'CurvedConnector5',
0x29:'Callout1',0x2A:'Callout2',0x2B:'Callout3',0x2C:'AccentCallout1',
0x2D:'AccentCallout2',0x2E:'AccentCallout3',0x2F:'BorderCallout1',
0x30:'BorderCallout2',0x31:'BorderCallout3',0x32:'AccentBorderCallout1',
0x33:'AccentBorderCallout2',0x34:'AccentBorderCallout3',0x35:'Ribbon',
0x36:'Ribbon2',0x37:'Chevron',0x38:'Pentagon',0x39:'NoSmoking',
0x3A:'Seal8',0x3B:'Seal16',0x3C:'Seal32',0x3D:'WedgeRectCallout',
0x3E:'WedgeRRectCallout',0x3F:'WdegeEllipseCallout',0x40:'Wave',
0x41:'FoldedCorner',0x42:'LeftArrow',0x43:'DownArrow',0x44:'UpArrow',
0x45:'LeftRightArrow',0x6:'UpDownArrow',0x47:'IrregularSeal1',
0x48:'IrregularSeal2',0x49:'LightningBolt',0x4A:'Heart',0x4B:'PictureFrame',
0x4C:'QuadArrow',0x4D:'LeftArrowCallout',0x4E:'RightArrowCallout',
0x4F:'UpArrowCallout',0x50:'DownArrowCallout',0x51:'LeftRightArrowCallout',
0x52:'UpDownArrowCallout',0x53:'QuadArrowCallout',0x54:'Bevel',
0x55:'LeftBracket',0x56:'RightBracket',0x57:'LeftBrace',0x58:'RightBrace',
0x59:'LeftUpArrow',0x5A:'BentUpArrow',0x5B:'BentArrow',0x5C:'Seal24',
0x5D:'StripedRightArrow',0x5E:'NotchedRightArrow',0x5F:'BlockArc',
0x60:'SmileyFace',0x61:'VerticalScroll',0x62:'HorizontalScroll',
0x63:'CircularArrow',0x64:'DontUseNotchedCircularArrow',0x65:'UturnArrow',
0x66:'CurvedRightArrow',0x67:'CurvedLeftArrow',0x68:'CurvedUpArrow',
0x69:'CurvedDownArrow',0x6A:'CloudCallout',0x6B:'EllipseRibbon',
0x6C:'EllipseRibbon2',0x6D:'FlowChartProcess',0x6E:'FlowChartDecision',
0x6F:'FlowChartInputOutput',0x70:'FlowChartPredefinedProcess',
0x71:'FlowChartInternalStorage',0x72:'FlowChartDocument',
0x73:'FlowChartMultiDocument',0x74:'FlowChartTerminator',
0x75:'FlowChartPreparation',0x76:'FlowChartManualInput',
0x77:'FlowChartManualOperation',0x78:'FlowChartConnector',
0x79:'FlowChartPunchedCard',0x7A:'FlowChartPunchedTape',
0x7B:'FlowChartSummingJunction',0x7C:'FlowChartOr',
0x7D:'FlowChartCollate',0x7E:'FlowChartSort',
0x7F:'FlowChartExtract',0x80:'FlowChartMerge',0x81:'FlowChartOfflineStorage',
0x82:'FlowChartOnlineStorage',0x83:'FlowChartMagneticTape',
0x84:'FlowChartMagneticDisk',0x85:'FlowChartMagneticDrum',
0x86:'FlowChartDisplay',0x87:'FlowChartDelay',0x88:'TextPlainText',
0x89:'TextStop',0x8A:'TextTriangle',0x8B:'TextTriangleInverted',
0x8C:'TextChevron',0x8D:'TextChevronInverted',0x8E:'TextRingInside',
0x8F:'TextRingOutside',0x90:'TextArchUpCurve',0x91:'TextArchDownCurve',
0x92:'TextCircleCurve',0x93:'TextButtonCurve',0x94:'TextArchUpPour',
0x95:'TextArchDownPour',0x96:'TextCirclePour',0x97:'TextButtomPour',
0x98:'TextCurveUp',0x99:'TextCurveDown',0x9A:'TextCascadeUp',
0x9B:'TextCascadeDown',0x9C:'TextWave1',0x9D:'TextWave2',0x9E:'TextWave3',
0x9F:'TextWave4',0xA0:'TextInflate',0xA1:'TextDeflate',0xA2:'TextInflateBottom',
0xA3:'TextDeflateBottom',0xA4:'TextInflateTop',0xA5:'TextDeflateTop',
0xA6:'TextDeflateInflate',0xA7:'TextDeflateInflateDeflate',
0xA8:'TextFadeRight',0xA9:'TextFadeLeft',0xAA:'TextFadeUp',0xAB:'TextFadeDown',
0xAC:'TextSlantUp',0xAD:'TextSlantDown',0xAE:'TextCanUp',0xAF:'TextCanDown',
0xB0:'FlowChartAlternateProcess',0xB1:'FlowChartOffpageConnector',
0xB2:'Callout90',0xB3:'AccentCallout90',0xB4:'BorderCallout90',
0xB5:'AccentBorderCallout90',0xB6:'LeftRightUpArrow',0xB7:'Sun',0xB8:'Moon',
0xB9:'BracketPair',0xBA:'BracePair',0xBB:'Seal4',0xBC:'DoubleWave',
0xBD:'ActionButtonBlank',0xBE:'ActionButtonHome',0xBF:'ActionButtonHelp',
0xC0:'ActionButtonInformation',0xC1:'ActionButtonForwardNext',
0xC2:'ActionButtonBackPrevious',0xC3:'ActionButtonEnd',0xC4:'ActionButtonBeginning',
0xC5:'ActionButtonReturn',0xC6:'ActionButtonDocument',0xC7:'ActionButtonSound',
0xC8:'ActionButtonMovie',0xC9:'HostControl',0xCA:'TextBox'
}

odraw_id_names = {
	0xF000:'OfficeArtDggContainer', 0xF001:'OfficeArtBStoreContainer',
	0xF002:'OfficeArtDgContainer',0xF003:'OfficeArtSpgrContainer',
	0xF004:'OfficeArtSpContainer',0xF005:'OfficeArtSolverContainer',
	0xF006:'OfficeArtFDGGBlock',0xF007:'OfficeArtFBSE',
	0xF008:'OfficeArtFDG',0xF009:'OfficeArtFSPGR',
	0xF010:'OfficeArtClientAnchor',0xF011: 'OfficeArtClientData',
	0xF00A:'OfficeArtFSP',0xF00B:'OfficeArtFOPT', 0xF00D:'OfficeArtClientTextbox',
	0xF00F:'OfficeArtChildAnchor',0xF012:'OfficeArtFConnectorRule',
	0xF014:'OfficeArtFArcRule',0xF017:'OfficeArtFCalloutRule',
	0xF01A:'OfficeArtBlipEMF',0xF01B:'OfficeArtBlipWMF',
	0xF01C:'OfficeArtBlipPICT',0xF01D:'OfficeArtBlipJPEG',
	0xF01E:'OfficeArtBlipPNG',0xF01F:'OfficeArtBlipDIB',
	0xF020:'OfficeArtBlipTIFF',0xF118:'OfficeArtFRITContainer',
	0xF119:'OfficeArtFDGSL',0xF11A:'OfficeArtColorMRUContainer',
	0xF11D:'OfficeArtFPSPL',0xF11E:'OfficeArtSplitMenuColorContainer',
	0xF121:'OfficeArtSecondaryFOPT',0xF122:'OfficeArtTertiaryFOPT'
}
odraw_bliptypes = {
	0x00:'Error',
	0x01:'Unknown',
	0x02:'EMF',
	0x03:'WMF',
	0x04:'PICT',
	0x05:'JPEG',
	0x06:'PNG',
	0x07:'DIB',
	0x11:'TIFF',
	0x12:'CMYK JPG'
	}

def FDGGBlock (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "spidMax", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	cidcl = struct.unpack("<I",value[12:16])[0]-1
	hd.hdmodel.set (iter1, 0, "cidcl", 1, cidcl ,2,12,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "cspSaved", 1, struct.unpack("<I",value[16:20])[0],2,16,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "cdgSaved", 1, struct.unpack("<I",value[20:24])[0],2,20,3,4,4,"<I")
	off = 24
	for i in range(cidcl):
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "dgid", 1, struct.unpack("<I",value[off:off+4])[0],2,off,3,4,4,"<I")
		iter1 = hd.hdmodel.append(None, None)
		hd.hdmodel.set (iter1, 0, "cspidCur", 1, struct.unpack("<I",value[off+4:off+8])[0],2,off+4,3,4,4,"<I")
		off += 8

def FDG (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "csp", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "spidCur", 1, struct.unpack("<I",value[12:16])[0],2,12,3,4,4,"<I")

def FSPGR (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "xLeft", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "yTop", 1, struct.unpack("<I",value[12:16])[0],2,12,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "xRight", 1, struct.unpack("<I",value[16:20])[0],2,16,3,4,4,"<I")
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "yBottom", 1, struct.unpack("<I",value[20:24])[0],2,20,3,4,4,"<I")

def FSP (hd, size, value):
	iter1 = hd.hdmodel.append(None, None)
	shtype = struct.unpack("<H",value[0:2])[0]>>4
	if msospt.has_key(shtype):
		ntype = "%s (%02x)"%(msospt[shtype],shtype)
	else:
		ntype = "%02x"%shtype
	hd.hdmodel.set (iter1, 0, "Shape", 1, ntype,2,0,3,2,4,"<H")

	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "spid", 1, struct.unpack("<I",value[8:12])[0],2,8,3,4,4,"<I")
	flags = struct.unpack("<I",value[12:16])[0]
	fl = {'group':flags&1,'child':flags&2,'patriarch':flags&4,'Deleted':flags&8,'OleShape':flags&16,
		'HaveMaster':flags&32,'FlipH':flags&64,'FlipV':flags&128,'Connector':flags&256,
		'HaveAnchor':flags&512,'Background':flags&1024,'HaveSpt':flags&2048}
	flagstr = ""
	for i in fl.items():
		if i[1] != 0:
			flagstr += i[0] + " "
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "flags", 1, flagstr,2,12,3,4,4,"<I")



def FBSE (hd, size, value):
	off = 8
	btWin32 = ord(value[off])
	add_iter(hd,"btWin32","%02x (%s)"%(btWin32,key2txt(btWin32, odraw_bliptypes)),off,1,"<B")
	off += 1
	btMac =  ord(value[off])
	add_iter(hd,"btMac","%02x (%s)"%(btMac,key2txt(btMac, odraw_bliptypes)),off,1,"<B")
	off += 1
	rgbUid = d2hex(value[off:off+16])
	add_iter(hd,"rgbUid",rgbUid,off,16,"txt")


fopt_names = {
0xc0c0:'Text',0xc0c5:'Font',0xc105:'Name',0xc187:'bgName',
0xc680:'bookmark',0xc681:'bookmarkName',0xc383:'wrapPoints'
}

def FOPT (hd, size, value):
# ignoring "complex" opids for now
	fnames = []
	off = 8
	while off < size:
		iter1 = hd.hdmodel.append(None, None)
		id = struct.unpack("<H",value[off:off+2])[0]
		if escher_opids.has_key(id):
			opids = escher_opids[id]
		else:
			opids = "undef_0x%02x"%id
		hd.hdmodel.set (iter1, 0, opids, 1, struct.unpack("<i",value[off+2:off+6])[0],2,off+2,3,4,4,"<i")
		if fopt_names.has_key(id):
			nlen = struct.unpack("<i",value[off+2:off+6])[0]
			size -= nlen
			fnames.append([id,nlen])
		off +=6
	for i in range(len(fnames)):
		iter1 = hd.hdmodel.append(None, None)
		name = fopt_names[fnames[i][0]]
		nlen =  fnames[i][1]
		if name == 'wrapPoints':
			hd.hdmodel.set (iter1, 0, name , 1, struct.unpack("<H",value[off:off+2])[0],2,off,3,nlen,4,"<H")
		else:
			hd.hdmodel.set (iter1, 0, name , 1, unicode(value[off:off+nlen],"utf-16"),2,off,3,nlen,4,"txt")
		off += nlen

mspub_opids = {0x2001:'xLeft',0x2002:'yTop',0x2003:'xRight',0x2004:'yBottom'}

clanchor = {1:"Xs",2:"Ys",3:"Xe",4:"Ye"}
def ClientAnchor (hd, size, value):
	off = 12
	while off < size:
		iter1 = hd.hdmodel.append(None, None)
		id = ord(value[off])
		ntype = ord(value[off+1])
		val = struct.unpack("<i",value[off+2:off+6])[0]/12700
		name = clanchor[id]
		hd.hdmodel.set (iter1, 0, name, 1,"%2d pt"%val ,2,off+2,3,4,4,"<i")
		off +=6

def ClientData (hd, size, value):
	off = 14 # assume it only has ShapeID
	iter1 = hd.hdmodel.append(None, None)
	hd.hdmodel.set (iter1, 0, "ShapeID", 1, "%2x"%struct.unpack("<I",value[off:off+4])[0],2,off,3,4,4,"<I")

odraw_ids = {
#	0xF000:'OfficeArtDggContainer', 0xF001:'OfficeArtBStoreContainer',
#	0xF002:'OfficeArtDgContainer',0xF003:'OfficeArtSpgrContainer',
#	0xF004:'OfficeArtSpContainer',0xF005:'OfficeArtSolverContainer',
	0xF006:FDGGBlock,
	0xF007:FBSE,
	0xF008:FDG,
	0xF009:FSPGR,
	0xF00A:FSP,
	0xF00B:FOPT,
# 0xF00D:'OfficeArtClientTextbox',
#	0xF00F:'OfficeArtChildAnchor',
	0xF010:ClientAnchor,
	0xF011:ClientData,
#	0xF012:'OfficeArtFConnectorRule',
#	0xF014:'OfficeArtFArcRule',0xF017:'OfficeArtFCalloutRule',
#	0xF01A:'OfficeArtBlipEMF',0xF01B:'OfficeArtBlipWMF',
#	0xF01C:'OfficeArtBlipPICT',0xF01D:'OfficeArtBlipJPEG',
#	0xF01E:'OfficeArtBlipPNG',0xF01F:'OfficeArtBlipDIB',
#	0xF020:'OfficeArtBlipTIFF',0xF118:'OfficeArtFRITContainer',
#	0xF119:'OfficeArtFDGSL',0xF11A:'OfficeArtColorMRUContainer',
#	0xF11D:'OfficeArtFPSPL',0xF11E:'OfficeArtSplitMenuColorContainer',
	0xF121:FOPT,0xF122:FOPT
}

def parse (model,data,parent,doctype=""):
	try:
		offset = 0
		while offset < len(data) - 8:
			contflag = ord(data[offset])&0xF
			newT = struct.unpack('<H', data[offset+2:offset+4])[0]
			newL = struct.unpack('<I', data[offset+4:offset+8])[0]

			if doctype == "pub":
				if newT == 0xF011:
					shapeid = struct.unpack("<I",data[offset+14:offset+18])[0]
					pname = model.get_value(parent,0)
					model.set_value(parent,0,pname+" (%02x)"%shapeid)

			if newL > 0:
				iter1 = model.append(parent,None)
				if odraw_id_names.has_key(newT):
					name = odraw_id_names[newT]
				else:
					name = "%02x"%newT
				if doctype == "pub":
					if newT == 0xF118 or newT == 0xF11E: #or newT == 0xF11A
						newL += 4
					if newT == 0xF004 or newT == 0xF003:
						newL -= 4
				
				model.set_value(iter1,0,name)
				model.set_value(iter1,1,("escher","odraw",newT))

				if contflag == 0xF:
					if doctype == "pub":
						model.set_value(iter1,2,newL+12)
						model.set_value(iter1,3,data[offset:offset+newL+12])
						parse (model,data[offset+8:offset+12+newL],iter1)
						offset += newL + 12
					else:
						model.set_value(iter1,2,newL+8)
						model.set_value(iter1,3,data[offset:offset+newL+8])
						parse (model,data[offset+8:offset+newL+8],iter1)
						offset += newL + 8
				else:
					model.set_value(iter1,2,newL+8)
					model.set_value(iter1,3,data[offset:offset+newL+8])
					offset += newL + 8
			else:
				offset += 4
	except:
		print "Failed to parse Escher stream",len(data)

