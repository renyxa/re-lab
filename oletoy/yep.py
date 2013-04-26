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
psr_dsp_types = {
	1:'HALL1',2:'HALL2',3:'HALL3',4:'HALL4',
	5:'HALL5',6:'HALL M',7:'HALL L',8:'BASIC HALL',
	9:'LARGE HALL',10:'ATMO HALL',11:'ROOM1',12:'ROOM2',
	13:'ROOM3',14:'ROOM4',15:'ROOM5',16:'ROOM6',
	17:'ROOM7',18:'ROOM S',19:'ROOM M',20:'ROOM L',
	21:'ACOSTIC ROOM',22:'DRUMS ROOM',23:'PERC ROOM',24:'STAGE1',
	25:'STAGE2',26:'STAGE3',27:'STAGE4',28:'PLATE1',
	29:'PLATE2',30:'PLATE3',31:'GM PLATE',32:'TUNNEL',
	33:'CANYON',34:'BASEMENT',35:'WHITE ROOM',36:'CHORUS1',
	37:'CHORUS2',38:'CHORUS3',39:'CHORUS4',40:'CHORUS5',
	41:'CHORUS6',42:'CHORUS7',43:'CHORUS8',44:'CHORUS FAST',
	45:'CHORUS LITE',46:'GM CHORUS1',47:'GM CHORUS2',48:'GM CHORUS3',
	49:'GM CHORUS4',50:'FB CHORUS',51:'CELESTE1',52:'CELESTE2',
	53:'SYMPHONIC1',54:'SYMPHONIC2',55:'ENS DETUNE1',56:'ENS DETUNE2',
	57:'KARAOKE1',58:'KARAOKE2',59:'KARAOKE3',60:'ER1',
	61:'ER2',62:'GATE REVERB',63:'REVERS GATE',64:'EQ DISCO',
	65:'EQ TEL',66:'2BAND EQ',67:'3BAND EQ',68:'ST 3BAND EQ',
	69:'HM ENHANCE1',70:'HM ENHANCE2',71:'FLANGER1',72:'FLANGER2',
	73:'FLANGER3',74:'FLANGER4',75:'FLANGER5',76:'GM FLANGER',
	77:'V_FLANGER',78:'TEMPO FLANGER',79:'DELAY LCR1',80:'DELAY LCR2',
	81:'DELAY LR',82:'ECHO',83:'CROSS DELAY',84:'TEMPO DELAY',
	85:'TEMPO ECHO',86:'TEMPO CROSS',87:'V_DST ROCA',88:'V_DST FUSION',
	89:'V_DST CRUNC',90:'V_DST VINTAG',91:'V_DST HARD2',92:'V_DST HEAVY',
	93:'V_DST HARD1',94:'V_DST SOFT',95:'DIST HARD1',96:'DIST HARD2',
	97:'DIST SOFT1',98:'DIST SOFT2',99:'DIST HEAVY',100:'OVERDRIVE1',
	101:'OVERDRIVE2',102:'ST DIST',103:'ST OD',104:'ST DIST HARD',
	105:'ST DIST SOFT',106:'AMP SIM1',107:'AMP SIM2',108:'ST AMP1',
	109:'ST AMP2',110:'ST AMP3',111:'ST AMP4',112:'ST AMP5',
	113:'ST AMP6',114:'DST+DELAY1',115:'DST+DELAY2',116:'OD+DELAY1',
	117:'OD+DELAY2',118:'CMP+DST+DLY1',119:'CMP+DST+DLY2',120:'CMP+OD+DLY1',
	121:'CMP+OD+DLY2',122:'V_DST H+DLY',123:'V_DST S+DLY',124:'DST+TDLY',
	125:'OD+TDLY',126:'COMP+DIST1',127:'COMP+DIST2',128:'CMP+DST+TDLY',
	129:'CMP+OD+TDLY1',130:'CMP+OD+TDLY2',131:'CMP+OD+TDLY3',132:'CMP+OD+TDLY4',
	133:'CMP+OD+TDLY5',134:'CMP+OD+TDLY6',135:'V_DST H+TDL1',136:'V_DST H+TDL2',
	137:'V_DST S+TDL1',138:'V_DST S+TDL2',139:'COMP MED',140:'COMP HEAVY',
	141:'COMP MELODY',142:'COMP BASS',143:'MBAND COMP',144:'COMPRESSOR',
	145:'NOISE GATE',146:'VCE CANCEL',147:'AMBIENCE',148:'TALKING MOD',
	149:'ISOLATOR',150:'PHASER1',151:'PHASER2',152:'PHASER3',
	153:'T_PHASER1',154:'T_PHASER2',155:'EP PHASER1',156:'EP PHASER2',
	157:'EP PHASER3',158:'PITCH CHG1',159:'PITCH CHG2',160:'PITCH CHG3',
	161:'DUAL ROT BRT',162:'D ROT BRT F',163:'DUAL ROT WRM',164:'D ROT WRM F',
	165:'DUAL ROT SP1',166:'DUAL ROT SP2',167:'ROTARY SP1',168:'ROTARY SP2',
	169:'ROT SP2 FAST',170:'ROTARY SP3',171:'ROT SP3 FAST',172:'ROTARY SP4',
	173:'ROT SP4 FAST',174:'ROTARY SP5',175:'ROT SP5 FAST',176:'ROTARY SP6',
	177:'ROTARY SP7',178:'ROT SP7 FAST',179:'ROTARY SP8',180:'ROT SP8 FAST',
	181:'ROTARY SP9',182:'ROT SP9 FAST',183:'2WAY ROT SP',184:'DST+ROT SP',
	185:'DST+2ROT SP',186:'OD+ROT SP',187:'OD+2ROT SP',188:'AMP+ROT SP',
	189:'AMP+2ROT SP',190:'AUTO PAN1',191:'AUTO PAN2',192:'AUTO PAN3',
	193:'EP AUTOPAN',194:'T_AUTO PAN1',195:'T_AUTO PAN2',196:'TREMOLO1',
	197:'TREMOLO2',198:'TREMOLO3',199:'EP TREMOLO',200:'GT TREMOLO1',
	201:'GT TREMOLO2',202:'VIBE VIBRATE',203:'T_TREMOLO',204:'AUTO WAH1',
	205:'AUTO WAH2',206:'AT WAH+DST1',207:'AT WAH+DST2',208:'AT WAH+OD1',
	209:'AT WAH+OD2',210:'TEMPO AT WAH',211:'TOUCH WAH1',212:'TOUCH WAH2',
	213:'TOUCH WAH3',214:'TC WAH+DST1',215:'TC WAH+DST2',216:'TC WAH+OD1',
	217:'TC WAH+OD2',218:'WH+DST+DLY1',219:'WH+DST+DLY2',220:'WH+DST+TDLY',
	221:'WH+OD+DLY1',222:'WH+OD+DLY2',223:'WH+OD+TDLY1',224:'WH+OD+TDLY2',
	225:'CLVI TC WAH1',226:'CLVI TC WAH2',227:'EP TC WAH1',228:'EP TC WAH2',
	229:'PEDAL WAH',230:'PEDAL WH+DST',231:'P.WH+DIST HD',232:'P.WH+DIST HV',
	233:'P.WH+DIST LT',234:'PEDAL WH+OD',235:'P.WH+OD HD',236:'P.WH+OD HV',
	237:'P.WH+OD LT',238:'NO EFFECT',239:'THRU'
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
		add_iter(hd,"DSP Type","%d %s"%(x,key2txt(x,psr_dsp_types)),offset,2,"BB")

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
