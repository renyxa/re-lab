# Copyright (C) 2007,2010-2013	Valek Filippov (frob@df.ru)
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

import sys,struct,math
from utils import *
from midi import *

# PSR DSP Types p. 25 
# http://www2.yamaha.co.jp/manual/pdf/emi/english/port/psrs650_en_dl_a0.pdf
# DSP type no.	DSP type name	(MSB)	(LSB)
psr_dsp_types = {
	0x0000:'NO EFFECT',
	0x0100:'HALL1',
	0x0101:'HALL5',
	0x0106:'HALL M',
	0x0107:'HALL L',
	0x0110:'HALL2',
	0x0111:'HALL3',
	0x0112:'HALL4',
	0x0117:'ATMO HALL',
	0x011E:'BASIC HALL',
	0x011F:'LARGE HALL',
	0x0200:'ROOM5',
	0x0201:'ROOM6',
	0x0202:'ROOM7',
	0x0205:'ROOM S',
	0x0206:'ROOM M',
	0x0207:'ROOM L',
	0x0210:'ROOM1',
	0x0211:'ROOM2',
	0x0212:'ROOM3',
	0x0213:'ROOM4',
	0x0214:'ACOSTIC ROOM',
	0x0215:'DRUMS ROOM',
	0x0216:'PERC ROOM',
	0x0300:'STAGE3',
	0x0301:'STAGE4',
	0x0310:'STAGE1',
	0x0311:'STAGE2',
	0x0400:'PLATE3',
	0x0407:'GM PLATE',
	0x0410:'PLATE1',
	0x0411:'PLATE2',
	0x0500:'DELAY LCR2',
	0x0510:'DELAY LCR1',
	0x0600:'DELAY LR',
	0x0700:'ECHO',
	0x0800:'CROSS DELAY',
	0x0900:'ER1',
	0x0901:'ER2',
	0x0A00:'GATE REVERB',
	0x0B00:'REVERS GATE',
	0x1000:'WHITE ROOM',
	0x1100:'TUNNEL',
	0x1200:'CANYON',
	0x1300:'BASEMENT',
	0x1400:'KARAOKE1',
	0x1401:'KARAOKE2',
	0x1402:'KARAOKE3',
	0x1500:'TEMPO DELAY',
	0x1508:'TEMPO ECHO',
	0x1600:'TEMPO CROSS',
	0x4000:'THRU',
	0x4100:'CHORUS6',
	0x4101:'CHORUS7',
	0x4102:'CHORUS5',
	0x4103:'GM CHORUS1',
	0x4104:'GM CHORUS2',
	0x4105:'GM CHORUS3',
	0x4106:'GM CHORUS4',
	0x4107:'FB CHORUS',
	0x4108:'CHORUS8',
	0x4110:'CHORUS FAST',
	0x4111:'CHORUS LITE',
	0x4200:'CELESTE1',
	0x4201:'CHORUS4',
	0x4202:'CELESTE2',
	0x4208:'CHORUS2',
	0x4210:'CHORUS3',
	0x4211:'CHORUS1',
	0x4212:'ROTARY SP5',
	0x4213:'ROT SP5 FAST',
	0x4300:'FLANGER5',
	0x4301:'FLANGER4',
	0x4307:'GM FLANGER',
	0x4308:'FLANGER1',
	0x4310:'FLANGER2',
	0x4311:'FLANGER3',
	0x4400:'SYMPHONIC2',
	0x4410:'SYMPHONIC1',
	0x4500:'ROTARY SP6',
	0x4501:'DST+ROT SP',
	0x4502:'OD+ROT SP',
	0x4503:'AMP+ROT SP',
	0x4510:'ROTARY SP1',
	0x4511:'ROTARY SP8',
	0x4512:'ROT SP8 FAST',
	0x4513:'ROTARY SP9',
	0x4514:'ROT SP9 FAST',
	0x4600:'TREMOLO3',
	0x4610:'TREMOLO1',
	0x4611:'ROTARY SP4',
	0x4612:'EP TREMOLO',
	0x4613:'GT TREMOLO2',
	0x4614:'ROT SP4 FAST',
	0x4700:'AUTO PAN2',
	0x4701:'AUTO PAN3',
	0x4710:'AUTO PAN1',
	0x4711:'ROTARY SP2',
	0x4712:'ROTARY SP3',
	0x4713:'TREMOLO2',
	0x4714:'GT TREMOLO1',
	0x4715:'EP AUTOPAN',
	0x4716:'ROTARY SP7',
	0x4717:'ROT SP2 FAST',
	0x4718:'ROT SP3 FAST',
	0x4719:'ROT SP7 FAST',
	0x4800:'PHASER1',
	0x4808:'PHASER2',
	0x4810:'EP PHASER3',
	0x4811:'EP PHASER1',
	0x4812:'EP PHASER2',
	0x4813:'PHASER3',
	0x4900:'DIST HEAVY',
	0x4901:'COMP+DIST2',
	0x4908:'ST DIST',
	0x4910:'COMP+DIST1',
	0x4A00:'OVERDRIVE1',
	0x4A08:'ST OD',
	0x4A09:'OVERDRIVE2',
	0x4B00:'AMP SIM1',
	0x4B01:'AMP SIM2',
	0x4B08:'ST AMP3',
	0x4B10:'DIST HARD1',
	0x4B11:'DIST SOFT1',
	0x4B12:'ST DIST HARD',
	0x4B13:'ST DIST SOFT',
	0x4B14:'ST AMP1',
	0x4B15:'ST AMP2',
	0x4B16:'DIST HARD2',
	0x4B17:'DIST SOFT2',
	0x4B18:'ST AMP4',
	0x4B19:'ST AMP5',
	0x4B1A:'ST AMP6',
	0x4C00:'3BAND EQ',
	0x4C10:'EQ DISCO',
	0x4C11:'EQ TEL',
	0x4C12:'ST 3BAND EQ',
	0x4D00:'2BAND EQ',
	0x4E00:'AUTO WAH2',
	0x4E01:'AT WAH+DST2',
	0x4E02:'AT WAH+OD2',
	0x4E10:'AUTO WAH1',
	0x4E11:'AT WAH+DST1',
	0x4E12:'AT WAH+OD1',
	0x4F00:'TEMPO AT WAH',
	0x5000:'PITCH CHG2',
	0x5001:'PITCH CHG3',
	0x5010:'PITCH CHG1',
	0x5100:'HM ENHANCE2',
	0x5110:'HM ENHANCE1',
	0x5200:'TOUCH WAH1',
	0x5201:'TC WAH+DST2',
	0x5202:'TC WAH+OD2',
	0x5208:'TOUCH WAH2',
	0x5210:'TC WAH+DST1',
	0x5211:'TC WAH+OD1',
	0x5212:'CLVI TC WAH1',
	0x5213:'EP TC WAH1',
	0x5214:'TOUCH WAH3',
	0x521C:'CLVI TC WAH2',
	0x521D:'EP TC WAH2',
	0x5300:'COMPRESSOR',
	0x5310:'COMP MED',
	0x5311:'COMP HEAVY',
	0x5400:'NOISE GATE',
	0x5500:'VCE CANCEL',
	0x5600:'2WAY ROT SP',
	0x5601:'DST+2ROT SP',
	0x5602:'OD+2ROT SP',
	0x5603:'AMP+2ROT SP',
	0x5700:'ENS DETUNE1',
	0x5710:'ENS DETUNE2',
	0x5800:'AMBIENCE',
	0x5D00:'TALKING MOD',
	0x5F00:'DST+DELAY2',
	0x5F01:'OD+DELAY2',
	0x5F10:'DST+DELAY1',
	0x5F11:'OD+DELAY1',
	0x6000:'CMP+DST+DLY2',
	0x6001:'CMP+OD+DLY2',
	0x6010:'CMP+DST+DLY1',
	0x6011:'CMP+OD+DLY1',
	0x6100:'WH+DST+DLY2',
	0x6101:'WH+OD+DLY2',
	0x6110:'WH+DST+DLY1',
	0x6111:'WH+OD+DLY1',
	0x6200:'V_DIST HARD1',
	0x6201:'V_DST H+DLY',
	0x6202:'V_DIST SOFT',
	0x6203:'V_DST S+DLY',
	0x621C:'V_DIST CRUNC',
	0x621D:'V_DIST VINTAG',
	0x621E:'V_DIST HARD2',
	0x621F:'V_DIST HEAVY',
	0x6300:'DUAL ROT SP1',
	0x6301:'DUAL ROT SP2',
	0x6310:'DUAL ROT BRT',
	0x6311:'DUAL ROT WRM',
	0x631E:'D ROT BRT F',
	0x631F:'D ROT WRM F',
	0x6400:'DST+TDLY',
	0x6401:'OD+TDLY',
	0x6500:'CMP+DST+TDLY',
	0x6501:'CMP+OD+TDLY1',
	0x6510:'CMP+OD+TDLY2',
	0x6511:'CMP+OD+TDLY3',
	0x6512:'CMP+OD+TDLY4',
	0x6513:'CMP+OD+TDLY5',
	0x6514:'CMP+OD+TDLY6',
	0x6600:'WH+DST+TDLY',
	0x6601:'WH+OD+TDLY1',
	0x6610:'WH+OD+TDLY2',
	0x6700:'V_DST H+TDL1',
	0x6701:'V_DST S+TDL1',
	0x6710:'V_DST S+TDL2',
	0x6711:'V_DST H+TDL2',
	0x6712:'V_DIST ROCA',
	0x6713:'V_DIST FUSION',
	0x6800:'V_FLANGER',
	0x6900:'MBAND COMP',
	0x6910:'COMP MELODY',
	0x6911:'COMP BASS',
	0x6B00:'TEMPO FLANGER',
	0x6C00:'T_PHASER1',
	0x6C10:'T_PHASER2',
	0x7300:'ISOLATOR',
	0x7700:'VIBE VIBRATE',
	0x7800:'T_TREMOLO',
	0x7900:'T_AUTO PAN1',
	0x7901:'T_AUTO PAN2',
	0x7A00:'PEDAL WAH',
	0x7A01:'PEDAL WH+DST',
	0x7A02:'PEDAL WH+OD',
	0x7A15:'P.WH+DIST HD',
	0x7A16:'P.WH+OD HD',
	0x7A17:'P.WH+DIST HV',
	0x7A18:'P.WH+OD HV',
	0x7A19:'P.WH+DIST LT',
	0x7A1A:'P.WH+OD LT'
}

psr_dsp_ids = {
	0:237,256:0,257:4,262:5,263:6,272:1,273:2,274:3,
	279:9,286:7,287:8,512:14,513:15,514:16,517:17,518:18,
	519:19,528:10,529:11,530:12,531:13,532:20,533:21,534:22,
	768:25,769:26,784:23,785:24,1024:29,1031:30,1040:27,1041:28,
	1280:79,1296:78,1536:80,1792:81,2048:82,2304:59,
	2305:60,2560:61,2816:62,4096:34,4352:31,4608:32,
	4864:33,5120:56,5121:57,5122:58,5376:83,5384:84,
	5632:85,16384:238,16640:40,16641:41,16642:39,16643:45,
	16644:46,16645:47,16646:48,16647:49,16648:42,16656:43,
	16657:44,16896:50,16897:38,16898:51,16904:36,16912:37,
	16913:35,16914:173,16915:174,17152:74,17153:73,17159:75,
	17160:70,17168:71,17169:72,17408:53,17424:52,17664:175,
	17665:183,17666:185,17667:187,17680:166,17681:178,17682:179,
	17683:180,17684:181,17920:197,17936:195,17937:171,17938:198,
	17939:200,17940:172,18176:190,18177:191,18192:189,18193:167,
	18194:169,18195:196,18196:199,18197:192,18198:176,18199:168,
	18200:170,18201:177,18432:149,18440:150,18448:156,18449:154,
	18450:155,18451:151,18688:98,18689:126,18696:101,18704:125,
	18944:99,18952:102,18953:100,19200:105,19201:106,19208:109,
	19216:94,19217:96,19218:103,19219:104,19220:107,19221:108,
	19222:95,19223:97,19224:110,19225:111,19226:112,19456:66,
	19472:63,19473:64,19474:67,19712:65,19968:204,19969:206,
	19970:208,19984:203,19985:205,19986:207,20224:209,20480:158,
	20481:159,20496:157,20736:69,20752:68,20992:210,20993:214,
	20994:216,21000:211,21008:213,21009:215,21010:224,21011:226,
	21012:212,21020:225,21021:227,21248:143,21264:138,21265:139,
	21504:144,21760:145,22016:182,22017:184,22018:186,22019:188,
	22272:54,22288:55,22528:146,23808:147,24320:114,24321:116,
	24336:113,24337:115,24576:118,24577:120,24592:117,24593:119,
	24832:218,24833:221,24848:217,24849:220,25088:92,25089:121,
	25090:93,25091:122,25116:88,25117:89,25118:90,25119:91,
	25344:164,25345:165,25360:160,25361:162,25374:161,25375:163,
	25600:123,25601:124,25856:127,25857:128,25872:129,25873:130,
	25874:131,25875:132,25876:133,26112:219,26113:222,26128:223,
	26368:134,26369:136,26384:137,26385:135,26386:86,26387:87,
	26624:76,26880:142,26896:140,26897:141,27392:77,27648:152,
	27664:153,29440:148,30464:201,30720:202,30976:193,30977:194,
	31232:228,31233:229,31234:233,31253:230,31254:234,31255:231,
	31256:235,31257:232,31258:236
}

# returns size of the RIFF-based tree starting from 'parent'
def get_parent_size (page, parent):
	size = 8 # fourcc + chunk size
	for i in range(page.model.iter_n_children(parent)):
		citer = page.model.iter_nth_child(parent, i)
		size += len(page.model.get_value(citer,3)) + 8 # data size plus child fourcc and chunk size dwords
	return size

# collects tree under 'parent' inserting fourcc-s and chunk sizes
def collect_tree (page, parent):
	ctdata = ""
	# FIXME! 'VWDT' is not recollected from samples at the moment.
	if page.model.iter_n_children(parent) > 0 and page.model.get_value(parent,1)[1] != "VWDT":
		for i in range(page.model.iter_n_children(parent)):
			citer = page.model.iter_nth_child(parent, i)
			cdata = page.model.get_value(citer,3)
			clen = len(cdata)
			name = page.model.get_value(citer,1)[1]
			if name[:5] == "IPIT/":
				name = name[5:]
				pos = cdata.find("\x00")
				if pos != -1:
					clen = pos
			elif name == "SSTY":
				clen = page.model.get_value(citer,2)
			ctdata += name + struct.pack(">I",clen)+cdata
		if page.model.get_value(parent,1)[1] == "dontsave":
			return ctdata
		else:
			return page.model.get_value(parent,1)[1]+struct.pack(">I",len(ctdata))+ctdata
	else:
		ctdata = page.model.get_value(parent,3)
		name = page.model.get_value(parent,1)[1]
		clen = len(ctdata)
		return name+struct.pack(">I",clen)+ctdata


# collects tree in VPRM, skips "vdblock" and "prtshdr"
def collect_vprm (page, parent):
	data = ""
	for i in range(page.model.iter_n_children(parent)):
		citer = page.model.iter_nth_child(parent, i)
		itype = page.model.get_value(citer,1)[1]
		if itype != "vdblock" and itype != "prtshdr":
			data += page.model.get_value(citer,3)
		if page.model.iter_n_children(citer) > 0:
			data += collect_vprm (page, citer)
	return data

# saves YEP file
def save (page, fname):
	data = ""
	iter1 = page.model.get_iter_first()
	while None != iter1:
		if page.model.get_value(iter1,1)[1] != "VPRM":
			data += collect_tree (page, iter1)
		else:
			tdata = collect_vprm (page, iter1)
			data += page.model.get_value(iter1,1)[1] + struct.pack(">I",len(tdata))+tdata
		iter1 = page.model.iter_next(iter1)
	f = open(fname,"wb")
	f.write(data)
	f.close()


def vbhdr (hd, data, off):
	offset = 0
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to Elements Header","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to Elements Header","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 4
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to Elements offsets","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to Elements offsets","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 8
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to Drumkit blocks","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to Drumkit blocks","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 12
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to ???","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to ???","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 16
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to Graph","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to Graph","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 20
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to end of the Graph","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to end of the Graph","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 24
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to ???","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to ???","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")

	offset = 28
	x = struct.unpack(">I",data[offset:offset+4])[0]
	if x == 0:
		add_iter(hd,"Offset to ???","no block",offset,4,">I")
	else:
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to ???","%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")


	offset = 33
	x = ord(data[offset])
	add_iter(hd,"Bank MSB",x,offset,1,"B")

	offset = 34
	x = ord(data[offset])
	add_iter(hd,"Bank LSB",x,offset,1,"B")
	
	offset = 35
	x = ord(data[offset])
	add_iter(hd,"Program Change No.",x,offset,1,"B")


def p1s0 (hd, data, off):
	offset = 1
	x = ord(data[offset])
	if x == 0:
		add_iter(hd,"Voice Type","Normal",offset,1,"B")
	else:
		add_iter(hd,"Voice Type","Drum Kit",offset,1,"B")

	offset = 3
	x = 255-ord(data[offset])
	add_iter(hd,"Voice - Master Volume",x,offset,1,"B")

def p1s1 (hd, data, off):
	offset = 0
	x = 255-ord(data[offset])
	add_iter(hd,"Element Volume",x,offset,1,"B")

	offset = 6
	x = ord(data[offset])
	add_iter(hd,"Key Range - High note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

	offset = 7
	x = ord(data[offset])
	add_iter(hd,"Key Range - Low note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

def elemhdr (hd, data, off):
	offset = 0
	x = struct.unpack(">H",data[offset:offset+2])[0]
	if x >=32768:
               x = x-32768
	add_iter(hd,"Assigned Sample",x,offset,2,"<h")
	
	offset = 4
	x = ord(data[offset])
	add_iter(hd,"Num of Key Banks",x,offset,1,"B")

def bank (hd, data, off):
	offset = 1
	x = ord(data[offset])-64
	add_iter(hd,"Panorama",x,offset,1,"B")
        
	offset = 2
	x = ord(data[offset])
	add_iter(hd,"Key Range - High note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

	offset = 3
	x = ord(data[offset])
	add_iter(hd,"Key Range - Low note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

	offset = 4
	x = ord(data[offset])
	add_iter(hd,"Velocity Range - Hight",x,offset,1,"B")

	offset = 5
	x = ord(data[offset])
	add_iter(hd,"Velocity Range - Low",x,offset,1,"B")

	offset = 61
	x = 128-ord(data[offset])
	add_iter(hd,"Envelope - Attack",x,offset,1,"B")

	offset = 62
	x = 127-ord(data[offset])
	add_iter(hd,"Envelope - Decay",x,offset,1,"B")

	offset = 63
	x = 127-ord(data[offset])
	add_iter(hd,"Envelope - Sustain",x,offset,1,"B")

	offset = 65
	x = 127-ord(data[offset])
	add_iter(hd,"Envelope - Release",x,offset,1,"B")

	offset = 69
	x = 255-ord(data[offset])
	add_iter(hd,"Envelope - Decay Level",x,offset,1,"B")

	offset = 70
	x = 255-ord(data[offset])
	add_iter(hd,"Envelope - Sus Level",x,offset,1,"B")

	offset = 91
	x = ord(data[offset])/16
	add_iter(hd,"Velocity Sens - Level",x,offset,1,"B")

	offset = 141
	x = ord(data[offset])
	add_iter(hd,"Filter - Resonance",x,offset,1,"B")

def dkblock(hd, data, off):
	offset = 3
	x = ord(data[offset])
	if x == 0:
                add_iter(hd,"Alternate group","N",offset,1,"B")
	else:
                add_iter(hd,"Alternate group",chr(x+64),offset,1,"B")

	offset = 9
	x = ord(data[offset])
	if x == 0:
                add_iter(hd,"Key Off","Disable",offset,1,"B")
	else:
                add_iter(hd,"Key Off","Enable",offset,1,"B")

def hdralst(hd, data, off):
	ind = 0
	off = 0
	while off < len(data):
		item_s = struct.unpack(">h",data[off:off+2])[0]
		item_e = struct.unpack(">h",data[off+2:off+4])[0]
		add_iter(hd,"Sample group %d"%ind,"Samples from %02x to %02x"%(item_s,item_e),off,4,">hh")
		off += 4
		ind += 1

def hdra(hd, data, off):
	offset = 0
	var0 = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter(hd,"Offset to List of Sample groups","%02x + %02x = %02x"%(off,var0,off+var0),offset,4,">I")

	offset += 4
	size = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter(hd,"Offset to Samples Offsets","%02x + %02x = %02x"%(off,size,off+size),offset,4,">I")


def hdrbch (hd, data, off):
	offset = 8
	x = ord(data[offset])
	add_iter(hd,"Key Range - High note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

	offset = 9
	x = ord(data[offset])
	add_iter(hd,"Key Range - Low note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")
        
	offset = 12
	x = 255-ord(data[offset])
	add_iter(hd,"Volume",x,offset,1,"B")
	
	offset = 13
	x = ord(data[offset])-64
	add_iter(hd,"Panorama",x,offset,1,"B")

	offset = 16
	x = ord(data[offset])
	add_iter(hd,"Tuning Center Key-Note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

	offset = 17
	x = ord(data[offset])        
	if x >=32:
                x = ord(data[offset])-128
	add_iter(hd,"Tuning Coarse",x,offset,1,"B")

	offset = 18
	x = ord(data[offset])        
	if x >=64:
                x = ord(data[offset])-256
	add_iter(hd,"Tuning Fine",x,offset,1,"B")

	offset = 19
	x = ord(data[offset])        
	add_iter(hd,"Number of channels",x,offset,1,"B")

	offset = 0x20
	for i in range(3):
		x = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Length %d"%i,"%02x"%x,offset,4,">I")
		offset += 4

	offset = 0x2c
	add_iter(hd,"VWDT format?",d2hex(data[offset:offset+4]," "),offset,4,"txt")

	offset = 0x3c
	x = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter(hd,"Offset 0","%02x"%x,offset,4,">I")
	offset = 0x44
	x = struct.unpack(">I",data[offset:offset+4])[0]
	add_iter(hd,"Offset 1","%02x"%x,offset,4,">I")


def vvst(hd, data, off):
	offset = 0
	x = data[offset:offset+16]
	add_iter(hd,"Voice name",x,offset,16,"B")

	offset = 24
	x = ord(data[offset])
	add_iter(hd,"Bank MSB",x,offset,1,"B")

	offset = 25
	x = ord(data[offset])
	add_iter(hd,"Bank LSB",x,offset,1,"B")

	offset = 26
	x = ord(data[offset])
	add_iter(hd,"Program Change No.",x,offset,1,"B")

	offset = 36
	x = ord(data[offset])-64
	add_iter(hd,"Vibrato Speed",x,offset,1,"B")

	offset = 37
	x = ord(data[offset])-64
	add_iter(hd,"Vibrato Depth",x,offset,1,"B")

	offset = 38
	x = ord(data[offset])-64
	add_iter(hd,"Vibrato Delay",x,offset,1,"B")

	offset = 39
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Up) - Low Pass Filter",x,offset,1,"B")

	offset = 40
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Up) - Amplitude",x,offset,1,"B")

	offset = 41
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Up) - LFO PMOD Depth",x,offset,1,"B")

	offset = 42
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Up) - LFO FMOD Depth",x,offset,1,"B")

	offset = 43
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Up) - LFO AMOD Depth",x,offset,1,"B")

	offset = 49
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Down) - Low Pass Filter",x,offset,1,"B")

	offset = 50
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Down) - Amplitude",x,offset,1,"B")

	offset = 51
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Down) - LFO PMOD Depth",x,offset,1,"B")

	offset = 52
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Down) - LFO FMOD Depth",x,offset,1,"B")

	offset = 53
	x = ord(data[offset])
	add_iter(hd,"Joy Stick Assign (Down) - LFO AMOD Depth",x,offset,1,"B")

	offset = 56
	x = ord(data[offset])
	if x == 0:
                add_iter(hd,"Mono / Poly","Mono",offset,1,"B")
	else:
                add_iter(hd,"Mono / Poly","Poly",offset,1,"B")

	offset = 57
	x = ord(data[offset])
	add_iter(hd,"Main Volume",x,offset,1,"B")

	offset = 62
	x = ord(data[offset])-64
	add_iter(hd,"Octave",x,offset,1,"B")

#	offset = 63
#	x = ord(data[offset])-64
#	add_iter(hd,"Octave",x,offset,1,"B")

	offset = 74
	x = ord(data[offset])
	add_iter(hd,"Reverb Depth",x,offset,1,"B")

	offset = 75
	x = ord(data[offset])
	add_iter(hd,"Chorus Depth",x,offset,1,"B")

	offset = 76
	x = ord(data[offset])
        if x == 0:
                add_iter(hd,"DSP SW","Off",offset,1,"B")
	else:
                add_iter(hd,"DSP SW","On",offset,1,"B")

	offset = 88
	x = struct.unpack(">H",data[offset:offset+2])[0]
	add_iter(hd,"DSP Type","%d - %s"%(key2txt(x,psr_dsp_ids),key2txt(x,psr_dsp_types)),offset,2,">H")

	offset = 90
	x = ord(data[offset])
	add_iter(hd,"DSP Depth",x,offset,1,"B")

def samples(hd, data, off):
	ind = 0
	offset = 0
	while offset < len(data):
		v = struct.unpack(">I",data[offset:offset+4])[0]
		add_iter(hd,"Offset to Sample %d"%ind,"%02x + %02x = %02x"%(off,v,off+v),offset,4,">I")
		offset += 4
		ind += 1

vprmfunc = {"bank":bank, "dkblock":dkblock, "elemhdr":elemhdr,
	"hdra":hdra, "hdralst":hdralst, "hdrbch":hdrbch, "p1s0":p1s0, "p1s1":p1s1, 
	"vbhdr":vbhdr, "VVST":vvst, "samples":samples}

def hdr1item (page,data,parent,offset=0):
	off = 0
	# size of the "main header for level2 block
	# i.e. 'offset to the "elements header"'
	h1off0 = struct.unpack(">I",data[off:off+4])[0]
	if h1off0 != 0x24:
		print "ATTENTION! YEP: size of VPRM header2 is not 0x24, it's %02x"%h1off0
	off += 4
	vdtxt = "Drumkit"
	if ord(data[0x25]) == 0x00:
		vdtxt = "Voice"
	vdidxa = ord(data[0x21])
	vdidxb = ord(data[0x22])
	vdidxc = ord(data[0x23])	
	h1citer = add_pgiter(page,"%s Block [%d-%d-%d]"%(vdtxt,vdidxa,vdidxb,vdidxc),"vprm","vdblock",data,parent,"%02x  "%offset)
	add_pgiter(page,"V/Dk Header","vprm","vbhdr",data[:h1off0],h1citer,"%02x  "%offset)
	# offset to the list of offsets of elements
	h1off1 = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	# this offset is used in Drumkits only
	h1off2 = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	# seems to be 0s allways in files we have
	h1off3 = struct.unpack(">I",data[off:off+4])[0]
	off += 4
	# offset to the graph
	h1off4 = struct.unpack(">I",data[off:off+4])[0]
	off += 4

	# parse 'elements header'
	p1iter = add_pgiter(page,"Elements Header","vprm","prtshdr",data[h1off0:h1off1],h1citer,"%02x  "%(offset+h1off0))
	# first dozen in 'Elements header'
	add_pgiter(page,"Common settings","vprm","p1s0",data[h1off0:h1off0+12],p1iter,"%02x  "%(offset+h1off0))
	off = h1off0+12
	# number of elements for voice/drumkit
	p1num = struct.unpack(">I",data[off:off+4])[0]
	add_pgiter(page,"Num of sequences","vprm","p1num",data[off:off+4],p1iter,"%02x  "%(offset+off))
	off += 4
	# FIXME! Guessing that number of dozens would match with number of elements
	elements = {}
	for i in range(p1num):
		# type for all 'PH seq' after 0 is "p1s1" now
		add_pgiter(page,"PH seq%d"%(i+1),"vprm","p1s1",data[off:off+12],p1iter,"%02x  "%(offset+off))
		pid = ord(data[off+12])
		elements[pid] = 1
		off += 12
		if off > h1off1:
			print "ATTENTION! YEP: not enough bytes for 'dozens'..."
	
	# parse list of offsets to elements
	poffs = []
	# FIXME! assumption that number of offsets would match number of unique IDs in "dozens"
	#	for i in range(len(elements)):
	# that was wrong, try with number of elements
	# that was also wrong need to compare current offset with first element offset
	eloff1 = struct.unpack(">I",data[h1off1:h1off1+4])[0]
	enum = (eloff1 - h1off1)/4
	for i in range(enum):
		poffs.append(struct.unpack(">I",data[h1off1+i*4:h1off1+i*4+4])[0])
	p2iter = add_pgiter(page,"Elements offsets","vprm","poffs",data[h1off1:h1off1+enum*4],h1citer,"%02x  "%(offset+h1off1))

	# parse elements
	ind = 0
	try:
		for i in poffs:
			off = i
			# number of Key Banks
			elnum = ord(data[off+4])
			piter = add_pgiter(page,"Element %d"%ind,"vprm","elemhdr",data[off:off+176],h1citer,"%02x  "%(offset+off))
			off += 176
			ind += 1
			# collect Key Banks
			# FIXME! we do not check for data bonds in the loop here
			for j in range(elnum):
				add_pgiter(page,"Key Bank %d"%j,"vprm","bank",data[off:off+180],piter,"%02x  "%(offset+off))
				off += 180
	except:
		print "Failed in parsing elements","%02x %02x %02x"%(i,j,off), page.model.get_string_from_iter(piter) #sys.exc_info()

	# add drumkit's "h1off2" block
	# FIXME!  Bold assumption that "h1off3 is 'reserved'
	if h1off2 > 0:
#		if vdtxt == "Drumkit":
			dbiter = add_pgiter(page,"Drumkit block","vprm","dontsave","",h1citer,"%02x  "%(offset+h1off2))
			dboff = struct.unpack(">I",data[h1off2:h1off2+4])[0]
			add_pgiter(page,"Drumkit blocks offset","vprm","dkboff",data[h1off2:h1off2+4],dbiter,"%02x  "%(offset+h1off2))
			
			if dboff > h1off2+4:
				add_pgiter(page,"Drumkit blocks filler","vprm","dkbfiller",data[h1off2+4:dboff],dbiter,"%02x  "%(offset+h1off2+4))
			tmpoff = dboff
			ind = 0
			while tmpoff < h1off4:
				add_pgiter(page,"Drumkit block %d"%ind,"vprm","dkblock",data[tmpoff:tmpoff+24],dbiter,"%02x  "%(offset+tmpoff))
				ind += 1
				tmpoff += 24

	# add graph
	diter = add_pgiter(page,"Graph","vprm","graph",data[h1off4:],h1citer,"%02x  "%(offset+h1off4))

# page, data of the 'block', sample id, block id, iter for VWDT 
def vwdt(page,data,sampleid,blockid,vwdtiter,off):
	# frequency is at offset 0x18
	freq = struct.unpack(">I",data[0x18:0x1c])[0]

	offset = 0x20
	len0 = struct.unpack(">I",data[offset:offset+4])[0]
	offset += 4
	len1 = struct.unpack(">I",data[offset:offset+4])[0]
	offset += 4
	len2 = struct.unpack(">I",data[offset:offset+4])[0]

	offset = 0x3c
	off0 = struct.unpack(">I",data[offset:offset+4])[0]
	offset = 0x44
	off1 = struct.unpack(">I",data[offset:offset+4])[0]

	# 0x0a seems to be "uncompressed raw, signed, BE"
	# 0x06 have to be somehow compressed
	# FIXME! need to find number of channels and bits per sample
	fmt = ord(data[0x2c])
	# FIXME! need to find how to interpret "lenghts/offsets" in fmt 6
	vdata = page.model.get_value(vwdtiter,3)
	iname = "Sample %02x, Block %02x [FQ: %d]"%(sampleid,blockid,freq)
	if fmt&0x4:
		len1 *= 16
	if off1 > 0:
		ri = add_pgiter(page,"%s (Left)"%iname,"vwdt","dontsave",vdata[off0*2:off0*2+len1*2+0x20],vwdtiter,"%02x  "%(off0*2+off))
		add_pgiter(page,"%s (Right)"%iname,"vwdt","dontsave",vdata[off1*2:off1*2+len1*2+0x20],vwdtiter,"%02x  "%(off1*2+off))
	else:
		ri = add_pgiter(page,"%s (Mono)"%iname,"vwdt","dontsave",vdata[off0*2:off0*2+len1*2+0x20],vwdtiter,"%02x  "%(off0*2+off))
	return ri

def vprm (page, data, parent, offset=0, vwdtiter=None, vwdtoff=0):
	sig = data[:16]
	add_pgiter(page,"Signature","vprm","sign",data[:16],parent,"%02x  "%offset)
	off = 16
	ptr = struct.unpack(">I",data[off:off+4])[0]
	add_pgiter(page,"Offset to samples","vprm","offsmpl",data[off:off+4],parent,"%02x  "%(offset+off))
	off += 4

	hdr1end = struct.unpack(">I",data[off:off+4])[0]
	h1iter = add_pgiter(page,"Voices","vprm","voices",data[20:hdr1end],parent,"%02x  "%(offset+off))
	off += 4
	hdr1 = []
	while off < hdr1end:
		v = struct.unpack(">I",data[off:off+4])[0]
		if v != 0:
			hdr1.append(v)
		off += 4
	for i in hdr1:
		hdr1item (page,data[off:i],h1iter,(offset+off))
		off = i
	hdr1item (page,data[off:ptr],h1iter,(offset+off))

	off = ptr
	off2 = ptr
	v1 = struct.unpack(">I",data[off:off+4])[0] # ??? "allways" 8
	hdraend = struct.unpack(">I",data[off2+4:off2+8])[0]
	smplsiter = add_pgiter(page,"Samples","vprm","dontsave","",parent,"%02x  "%(offset+off))
	haiter = add_pgiter(page,"Sample groups header","vprm","hdra",data[off:off+8],smplsiter,"%02x  "%(offset+off))
	haiterlst = add_pgiter(page,"List of Sample groups","vprm","hdralst",data[off+8:off+hdraend],smplsiter,"%02x  "%(offset+off+8))
	slist = []
	shdrsize = struct.unpack(">I",data[off:off+4])[0]
	shdrlen = struct.unpack(">I",data[off+4:off+8])[0]
	tmpoff = off + shdrsize
	while tmpoff < off+shdrlen:
		ss = struct.unpack(">h",data[tmpoff:tmpoff+2])[0]
		se = struct.unpack(">h",data[tmpoff+2:tmpoff+4])[0]
		slist.append((ss,se))
		tmpoff += 4
	off2 += hdraend
	hdrbend = off+struct.unpack(">I",data[off2:off2+4])[0]
	hbiter = add_pgiter(page,"Samples Offsets","vprm","samples",data[off+hdraend:hdrbend],smplsiter,"%02x  "%(offset+off+hdraend),offset+off)
	hdrb = []
	off2 += 4
	while off2 < hdrbend:
		v = struct.unpack(">I",data[off2:off2+4])[0]
		if v != 0:
			hdrb.append(v+off)
		off2 += 4
	hdrb.append(len(data))
	ind = 0
	for i in slist:
		siter = add_pgiter(page,"Sample group %d"%ind,"vprm","sample","",smplsiter,"%02x  "%(offset+off2))
		try:  # to workaround current problem with Europack
			for j in range(i[0],i[1]+1):
				if not j < 0:
					bend = hdrb[j]
					v3 = ord(data[off2+9])
					v4 = ord(data[off2+8])
					ti = add_pgiter(page,"Block %04d %02x-%02x [%s - %s]"%(j,v3,v4,pitches[v3],pitches[v4]),"vprm","hdrbch",data[off2:bend],siter,"%02x  "%(offset+off2))
					ri = vwdt(page,data[off2:bend],ind,j,vwdtiter,vwdtoff)
					page.model.set_value(ti,4,page.model.get_string_from_iter(ri))

					off2 = bend
		except:
			print 'Failed in the loop at lines 737..747'
		ind += 1

def parse (page, data, parent,align=4.,prefix="",offset=0):
	off = 0
	vvstgrpiter = None
	sstygrpiter = None
	vwdtiter = None
	while off < len(data):
		piter = parent
		fourcc = data[off:off+4]
		off += 4
		l = struct.unpack(">I",data[off:off+4])[0]
		if align:
			length = int(math.ceil(l/align)*align)
		else:
			length = l
		off += 4
		if fourcc == "SSTY":
			stname = data[off:off+16]
			p = stname.find("\x00")
			if p != -1:
				stname = stname[:p]
			iname = fourcc+" %s"%stname
			if sstygrpiter == None:
				sstygrpiter = add_pgiter(page,"SSTYs","ssty","dontsave","",parent,"%02x  "%(offset+off))
			piter = sstygrpiter
		elif fourcc == "VVST":
                        na = ord(data[off+0x18])
                	nb = ord(data[off+0x19])
                	nc = ord(data[off+0x1a])	
			if ord(data[off+0x14]) == 0x3f or ord(data[off+0x14]) == 0x00:
				f = "[Voice %d-%d-%d]"%(na,nb,nc)
			else:
				f = "[DrumKit %d-%d-%d]"%(na,nb,nc)
			iname = fourcc+f+" %s"%(data[off:off+16])
			if vvstgrpiter == None:
				vvstgrpiter = add_pgiter(page,"VVSTs","vvst","dontsave","",parent,"%02x  "%(offset+off))
			piter = vvstgrpiter
		else:
			iname = "%s"%fourcc

		citer = add_pgiter(page,"%s [%04x]"%(iname,l),"yep","%s%s"%(prefix,fourcc),data[off:off+length],piter,"%02x  "%(offset+off))
		if fourcc == "VWDT":
			vwdtiter = citer
			vwdtoff = off
		if fourcc == "SSTY":
			page.model.set_value(citer,2,l)
		if fourcc == "VPRM":
			# change 'off' to '0' to show offsets from start of VPRM
			# currently from the start of the file
			vprm (page, data[off:off+length], citer, off, vwdtiter,vwdtoff)
		if fourcc == "IPIT":
			parse (page, data[off:off+length], citer, 4., "IPIT/",off)
		off += length
	page.view.get_column(1).set_title("Offset")
	return "YEP"
