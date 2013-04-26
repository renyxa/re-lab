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
	0:('HALL1',1,0),
	1:('HALL2',1,16),
	2:('HALL3',1,17),
	3:('HALL4',1,18),
	4:('HALL5',1,1),
	5:('HALL M',1,6),
	6:('HALL L',1,7),
	7:('BASIC HALL',1,30),
	8:('LARGE HALL',1,31),
	9:('ATMO HALL',1,23),
	10:('ROOM1',2,16),
	11:('ROOM2',2,17),
	12:('ROOM3',2,18),
	13:('ROOM4',2,19),
	14:('ROOM5',2,0),
	15:('ROOM6',2,1),
	16:('ROOM7',2,2),
	17:('ROOM S',2,5),
	18:('ROOM M',2,6),
	19:('ROOM L',2,7),
	20:('ACOSTIC ROOM',2,20),
	21:('DRUMS ROOM',2,21),
	22:('PERC ROOM',2,22),
	23:('STAGE1',3,16),
	24:('STAGE2',3,17),
	25:('STAGE3',3,0),
	26:('STAGE4',3,1),
	27:('PLATE1',4,16),
	28:('PLATE2',4,17),
	29:('PLATE3',4,0),
	30:('GM PLATE',4,7),
	31:('TUNNEL',17,0),
	32:('CANYON',18,0),
	33:('BASEMENT',19,0),
	34:('WHITE ROOM',16,0),
	35:('CHORUS1',66,17),
	36:('CHORUS2',66,8),
	37:('CHORUS3',66,16),
	38:('CHORUS4',66,1),
	39:('CHORUS5',65,2),
	40:('CHORUS6',65,0),
	41:('CHORUS7',65,1),
	42:('CHORUS8',65,8),
	43:('CHORUS FAST',65,16),
	44:('CHORUS LITE',65,17),
	45:('GM CHORUS1',65,3),
	46:('GM CHORUS2',65,4),
	47:('GM CHORUS3',65,5),
	48:('GM CHORUS4',65,6),
	49:('FB CHORUS',65,7),
	50:('CELESTE1',66,0),
	51:('CELESTE2',66,2),
	52:('SYMPHONIC1',68,16),
	53:('SYMPHONIC2',68,0),
	54:('ENS DETUNE1',87,0),
	55:('ENS DETUNE2',87,16),
	56:('KARAOKE1',20,0),
	57:('KARAOKE2',20,1),
	58:('KARAOKE3',20,2),
	59:('ER1',9,0),
	60:('ER2',9,1),
	61:('GATE REVERB',10,0),
	62:('REVERS GATE',11,0),
	63:('EQ DISCO',76,16),
	64:('EQ TEL',76,17),
	65:('2BAND EQ',77,0),
	66:('3BAND EQ',76,0),
	67:('ST 3BAND EQ',76,18),
	68:('HM ENHANCE1',81,16),
	69:('HM ENHANCE2',81,0),
	70:('FLANGER1',67,8),
	71:('FLANGER2',67,16),
	72:('FLANGER3',67,17),
	73:('FLANGER4',67,1),
	74:('FLANGER5',67,0),
	75:('GM FLANGER',67,7),
	76:('V_FLANGER',104,0),
	77:('TEMPO FLANGER',107,0),
	78:('DELAY LCR1',5,16),
	79:('DELAY LCR2',5,0),
	80:('DELAY LR',6,0),
	81:('ECHO',7,0),
	82:('CROSS DELAY',8,0),
	83:('TEMPO DELAY',21,0),
	84:('TEMPO ECHO',21,8),
	85:('TEMPO CROSS',22,0),
	86:('V_DIST ROCA',103,18),
	87:('V_DIST FUSION',103,19),
	88:('V_DIST CRUNC',98,28),
	89:('V_DIST VINTAG',98,29),
	90:('V_DIST HARD2',98,30),
	91:('V_DIST HEAVY',98,31),
	92:('V_DIST HARD1',98,0),
	93:('V_DIST SOFT',98,2),
	94:('DIST HARD1',75,16),
	95:('DIST HARD2',75,22),
	96:('DIST SOFT1',75,17),
	97:('DIST SOFT2',75,23),
	98:('DIST HEAVY',73,0),
	99:('OVERDRIVE1',74,0),
	100:('OVERDRIVE2',74,9),
	101:('ST DIST',73,8),
	102:('ST OD',74,8),
	103:('ST DIST HARD',75,18),
	104:('ST DIST SOFT',75,19),
	105:('AMP SIM1',75,0),
	106:('AMP SIM2',75,1),
	107:('ST AMP1',75,20),
	108:('ST AMP2',75,21),
	109:('ST AMP3',75,8),
	110:('ST AMP4',75,24),
	111:('ST AMP5',75,25),
	112:('ST AMP6',75,26),
	113:('DST+DELAY1',95,16),
	114:('DST+DELAY2',95,0),
	115:('OD+DELAY1',95,17),
	116:('OD+DELAY2',95,1),
	117:('CMP+DST+DLY1',96,16),
	118:('CMP+DST+DLY2',96,0),
	119:('CMP+OD+DLY1',96,17),
	120:('CMP+OD+DLY2',96,1),
	121:('V_DST H+DLY',98,1),
	122:('V_DST S+DLY',98,3),
	123:('DST+TDLY',100,0),
	124:('OD+TDLY',100,1),
	125:('COMP+DIST1',73,16),
	126:('COMP+DIST2',73,1),
	127:('CMP+DST+TDLY',101,0),
	128:('CMP+OD+TDLY1',101,1),
	129:('CMP+OD+TDLY2',101,16),
	130:('CMP+OD+TDLY3',101,17),
	131:('CMP+OD+TDLY4',101,18),
	132:('CMP+OD+TDLY5',101,19),
	133:('CMP+OD+TDLY6',101,20),
	134:('V_DST H+TDL1',103,0),
	135:('V_DST H+TDL2',103,17),
	136:('V_DST S+TDL1',103,1),
	137:('V_DST S+TDL2',103,16),
	138:('COMP MED',83,16),
	139:('COMP HEAVY',83,17),
	140:('COMP MELODY',105,16),
	141:('COMP BASS',105,17),
	142:('MBAND COMP',105,0),
	143:('COMPRESSOR',83,0),
	144:('NOISE GATE',84,0),
	145:('VCE CANCEL',85,0),
	146:('AMBIENCE',88,0),
	147:('TALKING MOD',93,0),
	148:('ISOLATOR',115,0),
	149:('PHASER1',72,0),
	150:('PHASER2',72,8),
	151:('PHASER3',72,19),
	152:('T_PHASER1',108,0),
	153:('T_PHASER2',108,16),
	154:('EP PHASER1',72,17),
	155:('EP PHASER2',72,18),
	156:('EP PHASER3',72,16),
	157:('PITCH CHG1',80,16),
	158:('PITCH CHG2',80,0),
	159:('PITCH CHG3',80,1),
	160:('DUAL ROT BRT',99,16),
	161:('D ROT BRT F',99,30),
	162:('DUAL ROT WRM',99,17),
	163:('D ROT WRM F',99,31),
	164:('DUAL ROT SP1',99,0),
	165:('DUAL ROT SP2',99,1),
	166:('ROTARY SP1',69,16),
	167:('ROTARY SP2',71,17),
	168:('ROT SP2 FAST',71,23),
	169:('ROTARY SP3',71,18),
	170:('ROT SP3 FAST',71,24),
	171:('ROTARY SP4',70,17),
	172:('ROT SP4 FAST',70,20),
	173:('ROTARY SP5',66,18),
	174:('ROT SP5 FAST',66,19),
	175:('ROTARY SP6',69,0),
	176:('ROTARY SP7',71,22),
	177:('ROT SP7 FAST',71,25),
	178:('ROTARY SP8',69,17),
	179:('ROT SP8 FAST',69,18),
	180:('ROTARY SP9',69,19),
	181:('ROT SP9 FAST',69,20),
	182:('2WAY ROT SP',86,0),
	183:('DST+ROT SP',69,1),
	184:('DST+2ROT SP',86,1),
	185:('OD+ROT SP',69,2),
	186:('OD+2ROT SP',86,2),
	187:('AMP+ROT SP',69,3),
	188:('AMP+2ROT SP',86,3),
	189:('AUTO PAN1',71,16),
	190:('AUTO PAN2',71,0),
	191:('AUTO PAN3',71,1),
	192:('EP AUTOPAN',71,21),
	193:('T_AUTO PAN1',121,0),
	194:('T_AUTO PAN2',121,1),
	195:('TREMOLO1',70,16),
	196:('TREMOLO2',71,19),
	197:('TREMOLO3',70,0),
	198:('EP TREMOLO',70,18),
	199:('GT TREMOLO1',71,20),
	200:('GT TREMOLO2',70,19),
	201:('VIBE VIBRATE',119,0),
	202:('T_TREMOLO',120,0),
	203:('AUTO WAH1',78,16),
	204:('AUTO WAH2',78,0),
	205:('AT WAH+DST1',78,17),
	206:('AT WAH+DST2',78,1),
	207:('AT WAH+OD1',78,18),
	208:('AT WAH+OD2',78,2),
	209:('TEMPO AT WAH',79,0),
	210:('TOUCH WAH1',82,0),
	211:('TOUCH WAH2',82,8),
	212:('TOUCH WAH3',82,20),
	213:('TC WAH+DST1',82,16),
	214:('TC WAH+DST2',82,1),
	215:('TC WAH+OD1',82,17),
	216:('TC WAH+OD2',82,2),
	217:('WH+DST+DLY1',97,16),
	218:('WH+DST+DLY2',97,0),
	219:('WH+DST+TDLY',102,0),
	220:('WH+OD+DLY1',97,17),
	221:('WH+OD+DLY2',97,1),
	222:('WH+OD+TDLY1',102,1),
	223:('WH+OD+TDLY2',102,16),
	224:('CLVI TC WAH1',82,18),
	225:('CLVI TC WAH2',82,28),
	226:('EP TC WAH1',82,19),
	227:('EP TC WAH2',82,29),
	228:('PEDAL WAH',122,0),
	229:('PEDAL WH+DST',122,1),
	230:('P.WH+DIST HD',122,21),
	231:('P.WH+DIST HV',122,23),
	232:('P.WH+DIST LT',122,25),
	233:('PEDAL WH+OD',122,2),
	234:('P.WH+OD HD',122,22),
	235:('P.WH+OD HV',122,24),
	236:('P.WH+OD LT',122,26),
	237:('NO EFFECT',0,0),
	238:('THRU',64,0)
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
	if page.model.iter_n_children(parent) > 0:
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

def p1s0 (hd, data):
	offset = 3
	x = 255-ord(data[offset])
	add_iter(hd,"Voice - Master Volume",x,offset,1,"B")

def p1s1 (hd, data):
	offset = 0
	x = 255-ord(data[offset])
	add_iter(hd,"Element Volume",x,offset,1,"B")

	offset = 6
	x = ord(data[offset])
	add_iter(hd,"Key Range - High note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

	offset = 7
	x = ord(data[offset])
	add_iter(hd,"Key Range - Low note","%d (%s)"%(x,key2txt(x,pitches)),offset,1,"B")

def elemhdr (hd, data):
	offset = 4
	x = ord(data[offset])
	add_iter(hd,"Num of Key Banks",x,offset,1,"B")

def bank (hd, data):
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

def dkblock(hd,data):
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
                
def hdra(hd,data):
	off = 0
	var0 = struct.unpack(">I",data[off:off+4])[0]
	add_iter(hd,"Offset A",var0,off,4,">I")
	off += 4
	size = struct.unpack(">I",data[off:off+4])[0]
	add_iter(hd,"Offset B",size,off,4,">I")
	off += 4
	ind = 0
	while off < size:
		item_s = struct.unpack(">h",data[off:off+2])[0]
		item_e = struct.unpack(">h",data[off+2:off+4])[0]
		add_iter(hd,"Sample group %02x"%ind,"%02x %02x"%(item_s,item_e),off,2,">h")
		off += 4
		ind += 1

def hdrbch (hd, data):
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

def vvst(hd,data):
	offset = 57
	x = ord(data[offset])
	add_iter(hd,"Main Volume",x,offset,1,"B")

	offset = 62
	x = ord(data[offset])-64
	add_iter(hd,"Octave",x,offset,1,"B")

	offset = 63
	x = ord(data[offset])-64
	add_iter(hd,"Octave",x,offset,1,"B")

	offset = 74
	x = ord(data[offset])
	add_iter(hd,"Reverb Depth",x,offset,1,"B")

	offset = 75
	x = ord(data[offset])
	add_iter(hd,"Chorus Depth",x,offset,1,"B")

	offset = 88
	if ord(data[offset]) == 1:
		x = ord(data[offset+1])
		if x in psr_dsp_types:
			xt = psr_dsp_types[x][0]
		else:
			xt = "(Unknown)"
		add_iter(hd,"DSP Type","%d %s"%(x,xt),offset,2,"BB")

	offset = 90
	x = ord(data[offset])
	add_iter(hd,"DSP Depth",x,offset,1,"B")

vprmfunc = {"p1s0":p1s0, "p1s1":p1s1, "elemhdr":elemhdr, "bank":bank, "dkblock":dkblock, "hdra":hdra, "hdrbch":hdrbch, "VVST":vvst}

def hdr1item (page,data,parent,offset=0):
	off = 0
	# size of the "main header for level2 block
	# i.e. 'offset to the "elements header"'
	h1off0 = struct.unpack(">I",data[off:off+4])[0]
	if h1off0 != 0x24:
		print "ATTENTION! YEP: size of VPRM header2 is not 0x24, it's %02x"%h1off0
	off += 4
	vdtxt = "Drumkit"
	if ord(data[0x21]) == 0x3f:
		vdtxt = "Voice"
	vdidx = ord(data[0x23])
	h1citer = add_pgiter(page,"%s Block %d"%(vdtxt,vdidx),"vprm","vdblock",data,parent,"%02x  "%offset)
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
	# FIXME!  No validation that we do not cross the 1st offset to elements
	# FIXME! assumption that number of offsets would match number of unique IDs in "dozens"
	#	for i in range(len(elements)):
	# that was wrong, try with number of elements
	for i in range(p1num):
		poffs.append(struct.unpack(">I",data[h1off1+i*4:h1off1+i*4+4])[0])
	p2iter = add_pgiter(page,"Elements offsets","vprm","poffs",data[h1off1:h1off1+p1num*4],h1citer,"%02x  "%(offset+h1off1))

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
		print "Failed in parsing elements","%02x"%i,sys.exc_info()

	# add drumkit's "h1off2" block
	# FIXME!  Bold assumption that "h1off3 is 'reserved'
	if vdtxt == "Drumkit":
		dbiter = add_pgiter(page,"Drumkit block","vprm","dontsave","",h1citer,"%02x  "%(offset+h1off2))
		dboff = struct.unpack(">I",data[h1off2:h1off2+4])[0]
		add_pgiter(page,"Drumkit blocks offset","vprm","dkboff",data[h1off2:h1off2+4],dbiter,"%02x  "%(offset+h1off2))
		
		if dboff > h1off2+4:
			add_pgiter(page,"Drumkit blocks filler","vprm","dkbfiller",data[h1off2+4:dboff],dbiter,"%02x  "%(offset+h1off2+4))
		tmpoff = dboff
		ind = 0
		while tmpoff < h1off4:
			add_pgiter(page,"Drumkit block %d"%ind,"vprm","dkblock",data[tmpoff:tmpoff+24],dbiter,"%02x  "%tmpoff)
			ind += 1
			tmpoff += 24

	# add graph
	diter = add_pgiter(page,"Graph","vprm","graph",data[h1off4:],h1citer,"%02x  "%(offset+h1off4))
	
def vprm (page, data, parent, offset=0):
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
	haiter = add_pgiter(page,"List of Sample groups","vprm","hdra",data[off:off+hdraend],smplsiter,"%02x  "%(offset+off))
	slist = []
	shdrsize = struct.unpack(">I",data[off:off+4])[0]
	shdrlen = struct.unpack(">I",data[off+4:off+8])[0]
	tmpoff = off + shdrsize
	while tmpoff < off+shdrlen:
		ss = struct.unpack(">H",data[tmpoff:tmpoff+2])[0]
		se = struct.unpack(">H",data[tmpoff+2:tmpoff+4])[0]
		slist.append((ss,se))
		tmpoff += 4
	off2 += hdraend
	hdrbend = off+struct.unpack(">I",data[off2:off2+4])[0]
	hbiter = add_pgiter(page,"Samples Offsets","vprm","samples",data[off+hdraend:hdrbend],smplsiter,"%02x  "%(offset+off+hdraend))
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
		siter = add_pgiter(page,"Sample %d"%ind,"vprm","sample","",smplsiter,"%02x  "%(offset+off2))
		try:  # to workaround current problem with Europack
			for j in range(i[0],i[1]+1):
					bend = hdrb[j]
					v3 = ord(data[off2+9])
					v4 = ord(data[off2+8])
					add_pgiter(page,"Block %04x %02x-%02x [%s - %s]"%(j,v3,v4,pitches[v3],pitches[v4]),"vprm","hdrbch",data[off2:bend],siter,"%02x  "%(offset+off2))
					off2 = bend
		except:
			print 'Failed in the loop at lines 356..361'
		ind += 1

def parse (page, data, parent,align=4.,prefix=""):
	off = 0
	vvstgrpiter = None
	sstygrpiter = None
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
				sstygrpiter = add_pgiter(page,"SSTYs","ssty","dontsave","",parent,"%02x  "%(off+off))
			piter = sstygrpiter
		elif fourcc == "VVST":
			n = struct.unpack(">H",data[off+0x19:off+0x1b])[0]
			if ord(data[off+0x18]) == 0x3f:
				f = "[Voice %s]"%n
			else:
				f = "[DrumKit %s]"%n
			iname = fourcc+f+" %s"%(data[off:off+16])
			if vvstgrpiter == None:
				vvstgrpiter = add_pgiter(page,"VVSTs","vvst","dontsave","",parent,"%02x  "%(off+off))
			piter = vvstgrpiter
		else:
			iname = "%s"%fourcc
		
		citer = add_pgiter(page,"%s [%04x]"%(iname,l),"yep","%s%s"%(prefix,fourcc),data[off:off+length],piter)
		if fourcc == "SSTY":
			page.model.set_value(citer,2,l)
		if fourcc == "VPRM":
			vprm (page, data[off:off+length], citer)
		if fourcc == "IPIT":
			parse (page, data[off:off+length], citer, 4., "IPIT/")
		off += length
	page.view.get_column(1).set_title("Offset")
	return "YEP"
