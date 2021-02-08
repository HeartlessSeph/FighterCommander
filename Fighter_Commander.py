#!python3

# -*- coding: utf-8 -*-
import binascii
import sys
import os
import json
import copy
import re
import glob
import argparse
from collections import OrderedDict
from collections import defaultdict


print ('''
   +------------------------+
   |   FIGHTER  COMMANDER   |
   +------------------------+\n
   TEST VERSION - EXPECT ERRORS\n''')

if (len(sys.argv) <= 1):
	print ("Usage: Drag and drop fighter_command.cfc onto Fighter Commander to extract to json")
	print ("Drag and drop folder containing jsons onto Fighter Commander to rebuild fighter_command.cfc")
	input("Press ENTER to exit... ")
	sys.exit()

def bitfield(num):
	bitfieldlist = [1 if num & (1 << (7-n)) else 0 for n in range(8)]
	if len(bitfieldlist) < 8:
		append = 8 - len(bitfieldlist)
		x = 0
		while x < append:
			bitfieldlist.append(0)
			x = x + 1
	return bitfieldlist
	
def bitfieldListMask(bitfield, List):
	curstring = ""
	x = 0
	while x < len(List):
		if bitfield[x] == 1:
			if curstring == "":
				curstring = List[x]
			else:
				curstring = curstring + ", " + List[x]
		x = x + 1
	return curstring
	
def bitlistToInteger(Bitlist):
	return int("".join(str(x) for x in Bitlist), 2)
	
def iterateStringstoBits(Bitlist, Bitstringlist):
	StringList = Bitstringlist.split(",")
	Newbitlist = []
	x = 0
	while x < len(Bitlist):
		bitvalue = 0
		y = 0
		while y < len(StringList):
			if StringList[y].lower() == Bitlist[x].lower(): bitvalue = 1
			y = y + 1
		Newbitlist.append(bitvalue)
		x = x + 1
	return Newbitlist

def int_to_bytes(n, minlen=0, endiantype = "little"):
	""" Convert integer to bytearray with optional minimum length. 
	"""
	if isinstance(n, float) == True:
		n = int(n)
	if n > 0:
		if n > 16777215:
			b = 0
			b = int.to_bytes(n, 4, endiantype)
		elif n > 65535:
			b = 0
			b = int.to_bytes(n, 3, endiantype)
		elif n > 255:
			b = 0
			b = int.to_bytes(n, 2, endiantype)
		else:
			b = 0
			b = int.to_bytes(n, 1, endiantype)
	elif n == 0:
		b = bytearray(b'\x00')
	elif n < 0:
		if n < -16777215:
			n = 4294967296 + n
			b = 0
			b = int.to_bytes(n, 4, endiantype)
		elif n < -65535:
			n = 16777216 + n
			b = 0
			b = int.to_bytes(n, 3, endiantype)
		elif n < -255:
			n = 65536 + n
			b = 0
			b = int.to_bytes(n, 2, endiantype)
		else:
			n = 256 + n
			b = 0
			b = int.to_bytes(n, 1, endiantype)

	if minlen > 0 and len(b) < minlen and endiantype == "little": # zero padding needed?
		padding = bytearray((minlen-len(b)))
		b = bytearray(b)
		b.extend((padding))
	if minlen > 0 and len(b) < minlen and endiantype == "big": # zero padding needed?
		padding = bytearray((minlen-len(b)))
		padding.extend((b))
		b = padding
	return b
	
def aligntext(myfile):
	currentpos = myfile.tell()
	numfiller = 8 - (currentpos % 8)
	if numfiller == 0:
		numfiller = 8
	x = 0
	while x < numfiller:
		myfile.write(b'\xCC')
		x = x + 1

def tree():
    def the_tree():
        return defaultdict(the_tree)
    return the_tree()
#
def GetStringFromPointer(myfile, pointerval = 0, endiantype = "little"):
	chars = []
	h = myfile.tell()
	if pointerval != 0:
		pointercheck = pointerval
	else:
		pointercheck = int.from_bytes(myfile.read(4),endiantype)
	myfile.seek(pointercheck)
	b = 0
	while True:
		c = myfile.read(1)
		if c == b'\x00':
			if b == 0:
				myfile.seek(h)
				stringver = "Null"
				return stringver
			else:
				myfile.seek(h)
				stringver = b''.join(chars)
				stringver = stringver.decode("utf-8") 
				return stringver
		else:
			chars.append(c)
			b = b + 1
#
def GetCommandSetName(myfile, endiantype = "little"):
	chars = []
	h = myfile.tell()
	pointercheck1 = int.from_bytes(myfile.read(4),endiantype)
	myfile.seek(pointercheck1)
	pointercheck2 = int.from_bytes(myfile.read(4),endiantype)
	myfile.seek(pointercheck2)
	while True:
		c = myfile.read(1)
		if c == b'\x00':
			myfile.seek(h)
			stringver = b''.join(chars)
			stringver = stringver.decode("utf-8")
			return stringver
		else:
			chars.append(c)
#			
def GoToPointer(myfile, pointerval = 0, endiantype = "little"):
	if pointerval != 0:
		myfile.seek(pointerval)
	else:
		pointer = int.from_bytes(myfile.read(4),endiantype)
		myfile.seek(pointer)
#	
def GetMovefromIDx(Idx, FollowUpMoveIdx):
	y = 0
	while y < len(FollowUpMoveIdx):
		if Idx == FollowUpMoveIdx[y][0]:
			return FollowUpMoveIdx[y][1]
		else:
			y = y + 1
			
def downgradeDictToOE(mydict):
	newdict = OrderedDict()
	for k, v in mydict.items():
		newkey = k - 1
		if newkey >= 0:	newdict[newkey] = mydict[k]
	return newdict
	
	
CommandSetDictionary = tree() #Stores Data for Command Sets
CommandSetIDDictionary = OrderedDict() #Stores a list of Command Sets and their ID's for reference.
CommandSetOrderIDxDictionary = OrderedDict()
VersionDictionary = OrderedDict() #Stores a list of Version Numbers and their Associated Engine
VersionDictionary[7] = "Old Engine"
VersionDictionary[16] = "Dragon Engine"
VersionDictionary[17] = "Dragon Engine"
OEGameDictionary = OrderedDict()
OEGameDictionary["Yakuza 0 / Kiwami 1"] = 0
OEGameDictionary["Yakuza 5"] = 1
jsonfile = OrderedDict() #Stores the dumped json from file.
FollowUpMoveIdx = [] #Stores Id's of Moves for follow ups
ButtonPressListDE = ["R1", "L2", "L1", "Cross", "Circle", "Triangle", "Square", "Unknown"]
ButtonPressListOE = ["Unknown","R1", "L2", "L1", "Cross", "Circle", "Triangle", "Square"]
DirectionalPadListDE = ["Unknown1","Unknown7","Unknown6","Unknown5","D-Pad Right","D-Pad Left","D-Pad Down","D-Pad Up"]
DirectionalPadListOE = DirectionalPadListDE
StateModifiersDictK2 = {0: "Unk0", 1: "Unk1", 2: "Unk2", 3: "Run Startup to Full Run", 4: "Enemy Down, Including getting up Animation", 5: "Enemy Standing", 6: "Unk6", 7: "Enemy Down from the Front", 8: "Enemy Down from Behind", 9: "Unk9", 10: "Unk10", 11: "Unk11", 12: "Unk12", 13: "Unk13", 14: "Unk14", 15: "Unk15", 16: "Unk16", 17: "Unk17", 18: "Unk18", 19: "Unk19", 20: "Unk21", 22: "Unk22", 23: "Unk24", 25: "Unk25", 26: "Unk26", 27: "Unk27", 28: "Unk28", 29: "Unk29", 30: "Unk30", 31: "Unk31", 32: "Unk32", 33: "Unk33", 34: "Unk34", 35: "Unk35", 36: "Unk36", 37: "Unk37", 38: "Unk38", 39: "Unk39", 40: "Unk40"}
StateModifiersDictOE = downgradeDictToOE(StateModifiersDictK2)
QuickstepDictDE = {0: "Front Quickstep", 1: "Left Quickstep", 2: "Back Quickstep", 3: "Right Quickstep"}
QuickstepDictOE = QuickstepDictDE
PropertyTypeDictDE = {1: "Button Press", 2: "Button Hold", 3: "Follow Up Start Lock", 4: "Follow Up Lifetime Lock", 5: "State Modifier", 6: "Button Press (Buffered Input)", 7: "Follow Up On Hit", 9: "Analog Deadzone",11: "Heat Action", 12: "Enemy Distance", 19: "Analog Direction", 22: "Quickstep", 23: "Upgrade Unlock", 26: "Timing"}
PropertyTypeDictOE = downgradeDictToOE(PropertyTypeDictDE)
ButtonPressConditionalsDE = ["Input must be Held", "Execute action on Button Release","Unknown3","Unknown4","Unknown5","Unknown6","Unknown7","Unknown8"]
ButtonPressConditionalsOE = ["Unknown8","Input must be Held", "Execute action on Button Release","Unknown3","Unknown4","Unknown5","Unknown6","Unknown7"]

CommandSetOrderIDx = 0

parser = argparse.ArgumentParser(description="Fighter_cfc extraction tool")
parser.add_argument("file", help=".cfc file")
parser.add_argument("-sn", "--simplenames", help="Shorten property names to not include the type of property", action="store_true")
args = parser.parse_args()
kfile = args.file
filecheck = os.path.isfile(kfile)


#File Extract
if filecheck == True:
	f = open(kfile, 'rb')

	patchedFile = "" #Init patched file

	curdir =  os.getcwd()
	mypath = curdir + "\\Fighter Command"
	if not os.path.isdir(mypath):
	   os.makedirs(mypath)
		
		
	f.seek(8, 1)#skips filetype and endianess
	fileversion = int.from_bytes(f.read(1),"little")
	if fileversion == 0:
		f.seek(2, 1)
		fileversion = fileversion = int.from_bytes(f.read(1),"big")
	else:
		f.seek(3, 1)
	
	#Start of Old Engine Extraction
	if VersionDictionary[fileversion] == "Old Engine":
		print("Please choose which Old Engine Game you are extracting from:")
		print("0 = Yakuza 0/Kiwami 1")
		print("1 = Yakuza 5")
		OEGameText = input("Enter a Number: ")
		OEGame = int(OEGameText)
		if OEGame > 1:
			print("An incorrect option was entered. Please restart the program and try again.")
			input("Press ENTER to exit... ")
			sys.exit()
		filesize = int.from_bytes(f.read(4),"big")
		f.seek(filesize)
		f.seek(-8, 1)
		NumCommandSets = int.from_bytes(f.read(4),"big")
		CommandSetTable = int.from_bytes(f.read(4),"big")
		f.seek(CommandSetTable)
	
		a = 0
		while a < NumCommandSets:
			CommandSetDictionary["File Version"] = fileversion
			if OEGame == 0:
				CommandSetDictionary["Old Engine Game"] = "Yakuza 0 / Kiwami 1"
			elif OEGame == 1:
				CommandSetDictionary["Old Engine Game"] = "Yakuza 5"
			setname = GetCommandSetName(f, "big")
			FollowUpMoveIdx = []
			nextset = f.tell() + 4
			GoToPointer(f, 0, "big")
			f.seek(4, 1)
			battlesetname = GetStringFromPointer(f, 0, "big")
			f.seek(4, 1)
			CommandSetDictionary[(setname)]["Command Set Name"] = battlesetname
			NumMoves = int.from_bytes(f.read(4),"big")
			MoveTablePointer = int.from_bytes(f.read(4),"big")
			NumWepSets = int.from_bytes(f.read(4),"big")
			WeaponListPointer = int.from_bytes(f.read(4),"big")
			GoToPointer(f, MoveTablePointer, "big")

			b = 0
			firstmove = f.tell()
			while b < NumMoves:
				nextmove = f.tell() + 4
				GoToPointer(f, 0, "big")
				movename = GetStringFromPointer(f, 0, "big")
				f.seek(4, 1)
				FollowUpMoveIdx.append([b, movename])
				NumFollowUps = int.from_bytes(f.read(1),"big")
				if OEGame == 0:
					NumAdditionalProps = int.from_bytes(f.read(1),"big")
					AnimTableBool = int.from_bytes(f.read(1),"big")
				elif OEGame == 1:
					AnimTableBool = int.from_bytes(f.read(1),"big")
					NumAdditionalProps = int.from_bytes(f.read(1),"big")
				movetype = int.from_bytes(f.read(1),"big")
				AnimPointer = int.from_bytes(f.read(4),"big")
				f.seek(-4, 1)
				animshort1 = int.from_bytes(f.read(2),"big")
				animshort2 = int.from_bytes(f.read(2),"big")
				FollowUpsPointer = int.from_bytes(f.read(4),"big")
				if OEGame == 0:
					AdditionalPropsPointer = int.from_bytes(f.read(4),"big")
				elif OEGame == 1:
					AdditionalPropsPointer = AnimPointer
				
				#f.seek(12, 1) why was this here again?
				CommandSetDictionary[(setname)]["Move Table"][movename]["Move Type"] = movetype #+ 1
				CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table Bool"] = AnimTableBool
				
		#Anim Tables-----------------------------------------------------------------------------------------
				if AnimTableBool == 1:
					currentpos = f.tell()
					f.seek(AnimPointer)
					if OEGame == 0:
						NumAnims = int.from_bytes(f.read(2),"big")
					elif OEGame == 1:
						unkval = NumAnims = int.from_bytes(f.read(1),"big")
						NumAnims = int.from_bytes(f.read(1),"big")
					f.seek(2, 1)
					AnimTablePointer = int.from_bytes(f.read(4),"big")
					f.seek(AnimTablePointer)
					c = 1
					while c < NumAnims + 1:
						currentanimpos = f.tell()
						GoToPointer(f, 0, "big")
						AnimName = GetStringFromPointer(f, 0 , "big")
						f.seek(4, 1)
						unkbyte1 = int.from_bytes(f.read(1),"little")
						unkbyte2 = int.from_bytes(f.read(1),"little")
						unkbyte3 = int.from_bytes(f.read(1),"little")
						unkbyte4 = int.from_bytes(f.read(1),"little")
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Animation Used"] = AnimName
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 1"] = unkbyte1
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 2"] = unkbyte2
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 3"] = unkbyte3
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 4"] = unkbyte4
						f.seek(currentanimpos+4)
						c = c + 1
					f.seek(currentpos)
				elif movetype == 3:
					CommandSetDictionary[(setname)]["Move Table"][movename]["Moveset IDx for Sync"] = animshort1
					CommandSetDictionary[(setname)]["Move Table"][movename]["Unknown Short"] = animshort2
				elif movetype == 2:
					CommandSetDictionary[(setname)]["Move Table"][movename]["Moveset IDx"] = animshort1 
					CommandSetDictionary[(setname)]["Move Table"][movename]["Unknown Short"] = animshort2
				else:
					AnimName = GetStringFromPointer(f, AnimPointer, "big")
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Used"] = AnimName
		#Anim Tables-----------------------------------------------------------------------------------------


		#Follow Up Tables-----------------------------------------------------------------------------------------
				f.seek(FollowUpsPointer)
				c = 1
				while c < NumFollowUps + 1:
					nextfollowup = f.tell() + 4
					GoToPointer(f, 0, "big")
					numfollowupprops = int.from_bytes(f.read(2),"big")
					idoffollowup = int.from_bytes(f.read(2),"big")
					CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up to"] = idoffollowup
					GoToPointer(f, 0, "big")
					d = 1
					while d < numfollowupprops + 1:
						nextproperty = f.tell() + 4
						GoToPointer(f, 0, "big")
						propint1 = int.from_bytes(f.read(4),"big")
						f.seek(-4, 1)
						propbyte1 = int.from_bytes(f.read(1),"big")
						propbyte2 = int.from_bytes(f.read(1),"big")
						propbyte3 = int.from_bytes(f.read(1),"big")
						propbyte4 = int.from_bytes(f.read(1),"big")
						propint2 = int.from_bytes(f.read(4),"big")
						f.seek(-4, 1)
						propbyte5 = int.from_bytes(f.read(1),"big")
						propbyte6 = int.from_bytes(f.read(1),"big")
						propbyte7 = int.from_bytes(f.read(1),"big")
						propbyte8 = int.from_bytes(f.read(1),"big")
						f.seek(-4,1)
						propshort1 = int.from_bytes(f.read(2),"big")
						propshort2 = int.from_bytes(f.read(2),"big")
						if args.simplenames: typedes = ""
						else: 
							if propint1 in PropertyTypeDictOE:
								typedes = "| Type " + str(propint1) + " = " + PropertyTypeDictOE[propint1]
							else: typedes = ""
						
						
						if propint1 == 10:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1 #+ 1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Hact Name"] = GetStringFromPointer(f, propint2, "big")							
						elif propint1 == 22:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1 #+ 1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Skill Name"] = GetStringFromPointer(f, propint2, "big")
						elif propint1 == 0:
							ButtonPressBitmask = bitfield(propbyte8)
							DPadBitmask = bitfield(propbyte7)
							ConditionalsBitmask = bitfield(propbyte5)
							buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressListOE)
							dpad = bitfieldListMask(DPadBitmask, DirectionalPadListOE)
							conditional = bitfieldListMask(ConditionalsBitmask, ButtonPressConditionalsOE)
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Button Press"] = buttonpress
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Directional Pad"] = dpad
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditionals"] = conditional
						elif propint1 == 1:						
							ButtonPressBitmask = bitfield(propbyte8)
							DPadBitmask = bitfield(propbyte7)
							ConditionalsBitmask = bitfield(propbyte5)
							buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressListOE)
							dpad = bitfieldListMask(DPadBitmask, DirectionalPadListOE)
							conditional = bitfieldListMask(ConditionalsBitmask, ButtonPressConditionalsOE)
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Button Press"] = buttonpress
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Directional Pad"] = dpad
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditionals"] = conditional
						elif propint1 == 2:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte8
						elif propint1 == 3:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte8
						elif propint1 == 4:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["State Type"] = StateModifiersDictOE[propbyte8]
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 4"] = propbyte5
						elif propint1 == 5:						
							ButtonPressBitmask = bitfield(propbyte8)
							DPadBitmask = bitfield(propbyte7)
							ConditionalsBitmask = bitfield(propbyte5)
							buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressListOE)
							dpad = bitfieldListMask(DPadBitmask, DirectionalPadListOE)
							conditional = bitfieldListMask(ConditionalsBitmask, ButtonPressConditionalsOE)
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Button Press"] = buttonpress
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Directional Pad"] = dpad
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditionals"] = conditional
						elif propint1 == 6:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte8
						elif propint1 == 8:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte5
						elif propint1 == 11:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Enemy Distance"] = propshort2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 4"] = propbyte5
						elif propint1 == 18:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte"] = propbyte8
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Analog Direction"] = propbyte7
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditions"] = propbyte5
						elif propint1 == 21:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Quickstep Direction"] = QuickstepDictOE[propbyte8]
						elif propint1 == 25:						
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Timing"] = propint2
						else:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Property Type"] = propint1 #+ 1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 1"] = propbyte8
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 2"] = propbyte7
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 3"] = propbyte6
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 4"] = propbyte5							
						f.seek(nextproperty)
						d = d + 1
					c = c + 1
					f.seek(nextfollowup)
		#Follow Up Tables-----------------------------------------------------------------------------------------
		
		
		#Additional Move Properties-------------------------------------------------------------------------------
				f.seek(AdditionalPropsPointer)
				c = 1
				while c < NumAdditionalProps + 1:
					nextadditionalprop = f.tell() + 4
					GoToPointer(f, 0, "big")
					movepropshort1 = int.from_bytes(f.read(2),"big")
					movepropshort2 = int.from_bytes(f.read(2),"big")
					CommandSetDictionary[(setname)]["Move Table"][movename]["Additional Properties Table"]["Additional Property " + str(c)]["Unk Short 1"] = movepropshort1
					CommandSetDictionary[(setname)]["Move Table"][movename]["Additional Properties Table"]["Additional Property " + str(c)]["Unk Short 2"] = movepropshort2
					c = c + 1
					f.seek(nextadditionalprop)		
		#Additional Move Properties-------------------------------------------------------------------------------
				f.seek(nextmove)
				b = b + 1
				
				
		#Re-Iterates through the moves to replace IDx of follow up with String		
			f.seek(firstmove)
			b = 0	
			while b < NumMoves:
				nextmove = f.tell() + 4
				GoToPointer(f, 0, "big")
				movename = GetStringFromPointer(f, 0, "big")
				f.seek(4, 1)
				NumFollowUps = int.from_bytes(f.read(1),"big")
				f.seek(7, 1)
				FollowUpsPointer = int.from_bytes(f.read(4),"big")
				f.seek(FollowUpsPointer)
				c = 1
				while c < NumFollowUps + 1:
					nextfollowup = f.tell() + 4
					GoToPointer(f,0,"big")
					numfollowupprops = int.from_bytes(f.read(2),"big")
					idoffollowup = int.from_bytes(f.read(2),"big")
					followupstring = GetMovefromIDx(idoffollowup, FollowUpMoveIdx)
					f.seek(4, 1)
					CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up to"] = followupstring
					GoToPointer(f,0,"big")
					c = c + 1
					f.seek(nextfollowup)
				f.seek(nextmove)
				b = b + 1
		#End of Re-Iteration

			f.seek(WeaponListPointer)
			b = 1
			while b < NumWepSets + 1:
				nextwepset = f.tell() + 4
				GoToPointer(f,0,"big")
				f.seek(4,1)
				wepcommandset = int.from_bytes(f.read(4),"big")
				f.seek(-4,1)
				if wepcommandset == 0:
					wepcommandset = "Zero"
				else:
					wepcommandset = GetStringFromPointer(f,0,"big")
				f.seek(-4,1)
				GoToPointer(f,0,"big")
				numwepproperties = int.from_bytes(f.read(2),"big")
				f.seek(2, 1)
				WepPropertiesPointer = int.from_bytes(f.read(4),"big")
				f.seek(WepPropertiesPointer)
				CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Command Set Name for Weapon Moveset"] = wepcommandset
				c = 1
				while c < numwepproperties + 1:
					nextweppos = f.tell() + 4
					GoToPointer(f,0,"big")
					wepshort1 = int.from_bytes(f.read(2),"big")
					wepshort2 = int.from_bytes(f.read(2),"big")
					wepshort3 = int.from_bytes(f.read(2),"big")
					wepshort4 = int.from_bytes(f.read(2),"big")
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Weapon Category ID"] = wepshort4
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 2"] = wepshort3
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 3"] = wepshort2
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 4"] = wepshort1
					c = c + 1
					f.seek(nextweppos)
				f.seek(nextwepset)
				b = b + 1
			f.seek(nextset)
			CommandSetOrderIDxDictionary[CommandSetOrderIDx] = setname
			CommandSetOrderIDx = CommandSetOrderIDx + 1
			
			with open(mypath + "\\" + str(setname) + ".json", 'w') as outfile:
				json.dump(CommandSetDictionary, outfile, indent=2, ensure_ascii=False)
			CommandSetDictionary.clear()
			a = a + 1
			
		with open("Command Set Order List.json", 'w') as outfile:
			json.dump(CommandSetOrderIDxDictionary, outfile, indent=1, ensure_ascii=False)
	
	
	
	
	
	

	
	#Start of Dragon Engine Extraction
	if VersionDictionary[fileversion] == "Dragon Engine":
		filesize = int.from_bytes(f.read(4),"little")
		f.seek(filesize)
		f.seek(-8, 1)
		NumCommandSets = int.from_bytes(f.read(4),"little")
		f.seek(-12, 1)
		CommandSetTable = int.from_bytes(f.read(4),"little")
		f.seek(CommandSetTable)

		a = 0
		while a < NumCommandSets:
			CommandSetDictionary["File Version"] = fileversion
			setname = GetCommandSetName(f)
			FollowUpMoveIdx = []
			nextset = f.tell() + 8
			GoToPointer(f)
			f.seek(8, 1)
			CommandSetID = int.from_bytes(f.read(4),"little")
			CommandSetIDDictionary[(setname)]= CommandSetID#
			CommandSetDictionary[(setname)]["Command Set ID"] = CommandSetID
			f.seek(4, 1)
			MoveTablePointer = int.from_bytes(f.read(4),"little")
			f.seek(4, 1)
			WeaponListPointer = int.from_bytes(f.read(4),"little")
			f.seek(4, 1)
			NumMoves = int.from_bytes(f.read(2),"little")
			NumWepSets = int.from_bytes(f.read(2),"little")
			GoToPointer(f, MoveTablePointer)

			b = 0
			firstmove = f.tell()
			while b < NumMoves:
				nextmove = f.tell() + 8
				GoToPointer(f)
				movename = GetStringFromPointer(f)
				FollowUpMoveIdx.append([b, movename])
				f.seek(8, 1)
				AnimPointer = int.from_bytes(f.read(4),"little")
				f.seek(-4, 1)
				animbyte1 = int.from_bytes(f.read(1),"little")
				animbyte2 = int.from_bytes(f.read(1),"little")
				animbyte3 = int.from_bytes(f.read(1),"little")
				animbyte4 = int.from_bytes(f.read(1),"little")
				f.seek(-4, 1)
				animshort1 = int.from_bytes(f.read(2),"little")
				animshort2 = int.from_bytes(f.read(2),"little")
				animbyte5 = int.from_bytes(f.read(1),"little")
				animbyte6 = int.from_bytes(f.read(1),"little")
				animbyte7 = int.from_bytes(f.read(1),"little")
				animbyte8 = int.from_bytes(f.read(1),"little")
				FollowUpsPointer = int.from_bytes(f.read(4),"little")
				f.seek(12, 1)
				NumFollowUps = int.from_bytes(f.read(2),"little")
				AnimTableBool = int.from_bytes(f.read(1),"little")
				movetype = int.from_bytes(f.read(1),"little")
				CommandSetDictionary[(setname)]["Move Table"][movename]["Move Type"] = movetype
				CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table Bool"] = AnimTableBool
				
		#Anim Tables-----------------------------------------------------------------------------------------
				if AnimTableBool == 1:
					currentpos = f.tell()
					f.seek(AnimPointer)
					AnimTablePointer = int.from_bytes(f.read(4),"little")
					f.seek(5, 1)
					NumAnims = int.from_bytes(f.read(1),"little")
					f.seek(AnimTablePointer)
					c = 1
					while c < NumAnims + 1:
						currentanimpos = f.tell()
						GoToPointer(f)
						AnimName = GetStringFromPointer(f)
						f.seek(4, 1)
						unkuint32 = int.from_bytes(f.read(4),"little")
						unkbyte1 = int.from_bytes(f.read(1),"little")
						unkbyte2 = int.from_bytes(f.read(1),"little")
						unkbyte3 = int.from_bytes(f.read(1),"little")
						unkbyte4 = int.from_bytes(f.read(1),"little")
						unkbyte5 = int.from_bytes(f.read(1),"little")
						unkbyte6 = int.from_bytes(f.read(1),"little")
						unkbyte7 = int.from_bytes(f.read(1),"little")
						unkbyte8 = int.from_bytes(f.read(1),"little")
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Animation Used"] = AnimName
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown uint32"] = unkuint32
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 1"] = unkbyte1
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 2"] = unkbyte2
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 3"] = unkbyte3
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 4"] = unkbyte4
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 5"] = unkbyte5
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 6"] = unkbyte6
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 7"] = unkbyte7
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Table"]["Animation " + str(c)]["Unknown byte 8"] = unkbyte8
						f.seek(currentanimpos+8)
						c = c + 1
					f.seek(currentpos)
				elif movetype == 4:
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 1"] = animbyte1
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 2"] = animbyte2
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 3"] = animbyte3
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 4"] = animbyte4
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 5"] = animbyte5
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 6"] = animbyte6
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 7"] = animbyte7
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 8"] = animbyte8
				elif movetype == 3:
					CommandSetDictionary[(setname)]["Move Table"][movename]["Moveset IDx"] = animshort1
					CommandSetDictionary[(setname)]["Move Table"][movename]["Unknown Short"] = animshort2
				elif movetype == 17:
					useless = "useless"
				else:
					AnimName = GetStringFromPointer(f, AnimPointer)
					CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Used"] = AnimName
		#Anim Tables-----------------------------------------------------------------------------------------


		#Follow Up Tables-----------------------------------------------------------------------------------------
				f.seek(FollowUpsPointer)
				c = 1
				while c < NumFollowUps + 1:
					nextfollowup = f.tell() + 8
					GoToPointer(f)
					numfollowupprops = int.from_bytes(f.read(2),"little")
					idoffollowup = int.from_bytes(f.read(2),"little")
					f.seek(4, 1)
					CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up to"] = idoffollowup
					GoToPointer(f)
					d = 1
					while d < numfollowupprops + 1:
						nextproperty = f.tell() + 8
						GoToPointer(f)
						propint1 = int.from_bytes(f.read(4),"little")
						f.seek(-4, 1)
						propint1ver17 = int.from_bytes(f.read(3),"little")
						f.seek(-3, 1)
						propbyte1 = int.from_bytes(f.read(1),"little")
						propbyte2 = int.from_bytes(f.read(1),"little")
						f.seek(-2,1)
						propshort1 = int.from_bytes(f.read(2),"little")
						propbyte3 = int.from_bytes(f.read(1),"little")
						propbyte4 = int.from_bytes(f.read(1),"little")
						f.seek(-2,1)
						propshort2 = int.from_bytes(f.read(2),"little")
						f.seek(4, 1)
						propint2 = int.from_bytes(f.read(4),"little")
						f.seek(-4, 1)
						propbyte5 = int.from_bytes(f.read(1),"little")
						propbyte6 = int.from_bytes(f.read(1),"little")
						propbyte7 = int.from_bytes(f.read(1),"little")
						propbyte8 = int.from_bytes(f.read(1),"little")
						if args.simplenames: typedes = ""
						else: 
							if propint2 in PropertyTypeDictDE:
								typedes = "| Type " + str(propint2) + " = " + PropertyTypeDictDE[propint2]
							else: typedes = ""						
						
						if propint2 == 11:
							if fileversion == 17:
								CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
								CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Heat Action IDx"] = propint1ver17
								CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unknown Property Byte"] = propbyte4					
							if fileversion == 16:
								CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
								CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Hact Name"] = GetStringFromPointer(f, propint1)
						elif propint2 == 1:
							ButtonPressBitmask = bitfield(propbyte1)
							DPadBitmask = bitfield(propbyte2)
							ConditionalsBitmask = bitfield(propbyte4)
							buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressListDE)
							dpad = bitfieldListMask(DPadBitmask, DirectionalPadListDE)
							conditional = bitfieldListMask(ConditionalsBitmask, ButtonPressConditionalsDE)
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Button Press"] = buttonpress
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Directional Pad"] = dpad
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditionals"] = conditional
						elif propint2 == 2:
							ButtonPressBitmask = bitfield(propbyte1)
							DPadBitmask = bitfield(propbyte2)
							ConditionalsBitmask = bitfield(propbyte4)
							buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressListDE)
							dpad = bitfieldListMask(DPadBitmask, DirectionalPadListDE)
							conditional = bitfieldListMask(ConditionalsBitmask, ButtonPressConditionalsDE)
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Button Press"] = buttonpress
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Directional Pad"] = dpad
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditionals"] = conditional
						elif propint2 == 3:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte1
						elif propint2 == 4:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte1
						elif propint2 == 5:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["State Type"] = StateModifiersDictK2[propbyte1]
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 4"] = propbyte4						
						elif propint2 == 6:
							ButtonPressBitmask = bitfield(propbyte1)
							DPadBitmask = bitfield(propbyte2)
							ConditionalsBitmask = bitfield(propbyte4)
							buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressListDE)
							dpad = bitfieldListMask(DPadBitmask, DirectionalPadListDE)
							conditional = bitfieldListMask(ConditionalsBitmask, ButtonPressConditionalsDE)
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Button Press"] = buttonpress
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Directional Pad"] = dpad
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditionals"] = conditional
						elif propint2 == 7:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte1
						elif propint2 == 9:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 1"] = propbyte4
						elif propint2 == 12:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Enemy Distance"] = propshort1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte 4"] = propbyte4
						elif propint2 == 19:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Unk Byte"] = propbyte1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Analog Direction"] = propbyte2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Conditions"] = propbyte4
						elif propint2 == 22:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Quickstep Direction"] = QuickstepDictDE[propbyte1]
						elif propint2 == 23:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Skill ID"] = propint1
						elif propint2 == 26:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d) + typedes]["Timing"] = propint1
						else:
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Property Type"] = propint2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 1"] = propbyte1
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 2"] = propbyte2
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 3"] = propbyte3
							CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 4"] = propbyte4
						f.seek(nextproperty)
						d = d + 1
					c = c + 1
					f.seek(nextfollowup)
				f.seek(nextmove)
		#Follow Up Tables-----------------------------------------------------------------------------------------
				b = b + 1
				
				
		#Re-Iterates through the moves to replace IDx of follow up with String		
			f.seek(firstmove)
			b = 0	
			while b < NumMoves:
				nextmove = f.tell() + 8
				GoToPointer(f)
				movename = GetStringFromPointer(f)
				f.seek(16, 1)
				FollowUpsPointer = int.from_bytes(f.read(4),"little")
				f.seek(12, 1)
				NumFollowUps = int.from_bytes(f.read(2),"little")
				f.seek(FollowUpsPointer)
				c = 1
				while c < NumFollowUps + 1:
					nextfollowup = f.tell() + 8
					GoToPointer(f)
					numfollowupprops = int.from_bytes(f.read(2),"little")
					idoffollowup = int.from_bytes(f.read(2),"little")
					followupstring = GetMovefromIDx(idoffollowup, FollowUpMoveIdx)
					f.seek(4, 1)
					CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up to"] = followupstring
					GoToPointer(f)
					c = c + 1
					f.seek(nextfollowup)
				f.seek(nextmove)
				b = b + 1
		#End of Re-Iteration

			f.seek(WeaponListPointer)
			b = 1
			while b < NumWepSets + 1:
				nextwepset = f.tell() + 8
				GoToPointer(f)
				GoToPointer(f)
				numwepproperties = int.from_bytes(f.read(2),"little")
				wepcommandset = int.from_bytes(f.read(2),"little")
				f.seek(4, 1)
				WepPropertiesPointer = int.from_bytes(f.read(4),"little")
				f.seek(WepPropertiesPointer)
				CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Command Set ID for Weapon Moveset"] = wepcommandset
				c = 1
				while c < numwepproperties + 1:
					nextweppos = f.tell() + 8
					GoToPointer(f)
					wepshort1 = int.from_bytes(f.read(2),"little")
					wepshort2 = int.from_bytes(f.read(2),"little")
					f.seek(4, 1)
					wepshort3 = int.from_bytes(f.read(2),"little")
					wepshort4 = int.from_bytes(f.read(2),"little")
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Weapon Category ID"] = wepshort1
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 2"] = wepshort2
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 3"] = wepshort3
					CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 4"] = wepshort4
					c = c + 1
					f.seek(nextweppos)
				f.seek(nextwepset)
				b = b + 1
			f.seek(nextset)
			
			with open(mypath + "\\" + str(setname) + ".json", 'w') as outfile:
				json.dump(CommandSetDictionary, outfile, indent=2, ensure_ascii=False)
			CommandSetDictionary.clear()
			a = a + 1
			
			CommandSetOrderIDxDictionary[CommandSetOrderIDx] = setname
			CommandSetOrderIDx = CommandSetOrderIDx + 1
			
		with open("Command Set List (Reference Only).json", 'w') as outfile:
			json.dump(CommandSetIDDictionary, outfile, indent=1, ensure_ascii=False)
			
		with open("Command Set Order List.json", 'w') as outfile:
			json.dump(CommandSetOrderIDxDictionary, outfile, indent=1, ensure_ascii=False)
		f.close
#End of File extract

#File Rebuild
else:
	stringlist = []
	stringpointerdict = OrderedDict()#Stores location of Strings written to file
	curdir =  os.getcwd()
	workdir = sys.argv[1]
	newfile = open("fighter_command new.cfc", 'w+b')
	for f in os.listdir(kfile):#Gets file version
		curfile = workdir + "\\" + f
		with open(curfile, 'r', encoding='utf8') as file:
			jsonfile = json.load(file)
			fileversion = jsonfile["File Version"]
			if "Old Engine Game" in jsonfile:
				enginegame = jsonfile["Old Engine Game"]
			else:
				enginegame = 0
	

		
	if VersionDictionary[fileversion] == "Dragon Engine":
		newfile.write(b'\x43\x46\x43\x49\x21\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')#Writes header with filesize filler
		for f in os.listdir(kfile):#Loops through all Json files and collects string data
			curfile = workdir + "\\" + f
			with open(curfile, 'r', encoding='utf8') as file:
				jsonfile = json.load(file)
				fileversion = jsonfile["File Version"]
				commandsetname = list(jsonfile.keys())[1]
				stringlist.append(commandsetname)
				commandsetID = jsonfile[commandsetname]["Command Set ID"]
				for move in list(jsonfile[commandsetname]["Move Table"].keys()):
					movename = move
					stringlist.append(movename)
					if "Animation Used" in jsonfile[commandsetname]["Move Table"][movename]:
						animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Used"]
						if animvalue == "Null":
							animvalue = b'\x00'
						stringlist.append(animvalue)
					if "Animation Table" in jsonfile[commandsetname]["Move Table"][movename]:
						for animtables in list(jsonfile[commandsetname]["Move Table"][movename]["Animation Table"].keys()):
							animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtables]["Animation Used"]
							if animvalue == "Null":
								animvalue = b'\x00'
							stringlist.append(animvalue)
					if "Follow Up Table" in jsonfile[commandsetname]["Move Table"][movename]:
						for followuptable in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"].keys()):
							if "Follows Up Properties" in jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]:
								for followupprop in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"].keys()):
									propertytype = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Property Type"]
									if propertytype == 11:
										heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Hact Name"]
										stringlist.append(heataction)
		stringlist = list( dict.fromkeys(stringlist) )
		x = 0
		
		#Writes string list to file collecting the string location and string in a dictionary.
		while x < len(stringlist):
			currentpos = newfile.tell()
			currentstring = stringlist[x]
			if currentstring == b'\x00':#Checks if null
				newfile.write(b'\x00')
			else:
				newfile.write(currentstring.encode('utf-8'))
				newfile.write(b'\x00')
			stringpointerdict[currentstring] = currentpos
			x = x + 1
		aligntext(newfile)#Adds the CC Byte enders to the end of the string table.
		
		#Parsing data from the jsons into Fighter_Command begins here.
		CommandSetPointerList = []
		numcommandsets = len(os.listdir(kfile))
		orderfile = open("Command Set Order List.json", 'rb')
		CommandSetOrderDictionary = json.load(orderfile)
		CommandSetOrderIDx = 0
		while CommandSetOrderIDx < numcommandsets:
			curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
			with open(curfile, 'r', encoding='utf8') as file:
				jsonfile = json.load(file)
				MovePointers = []
				FollowUpIdx = OrderedDict()
				fileversion = jsonfile["File Version"]
				commandsetname = list(jsonfile.keys())[1]
				commandsetID = jsonfile[commandsetname]["Command Set ID"]

				#Shitty copy paste to get Move Idx's for later use
				x = 0
				for move in list(jsonfile[commandsetname]["Move Table"].keys()):
					movename = move
					FollowUpIdx[movename] = x
					x = x + 1
					
				x = 0
				for move in list(jsonfile[commandsetname]["Move Table"].keys()):
					FollowUpPropValues = []
					FollowUpValues = []
					FollowUpValuePointers = []
					FollowUpPointers = []
					MoveValues = []
					AnimationTableValues = []
					AnimationValues = []
					AnimationTablePointers = []
					movename = move
					movetype = jsonfile[commandsetname]["Move Table"][movename]["Move Type"]
					animtablebool = jsonfile[commandsetname]["Move Table"][movename]["Animation Table Bool"]
					if "Follow Up Table" in jsonfile[commandsetname]["Move Table"][movename]:
						numfollowups = len(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"])
						for followuptable in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"].keys()):
							temparray1 = []
							followupval = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up to"]
							temparray1.append(followupval)
							FollowUpValues.append(temparray1)
							if "Follows Up Properties" in jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]:
								temparray2 = []
								for followupprop in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"].keys()):
									#list(jsonfile.keys())[1]
									propertytype = list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop].values())[0]
									if propertytype == 11:
										if fileversion == 16:
											heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Hact Name"]
											temparray2.append([propertytype, heataction])
										elif fileversion == 17:
											heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Heat Action IDx"]
											unkpropbyte = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unknown Property Byte"]
											temparray2.append([propertytype, heataction, unkpropbyte])
									elif propertytype == 1 or propertytype == 2 or propertytype == 6:
										buttonpressStrings = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Button Press"]
										bitslist = iterateStringstoBits(ButtonPressListDE, buttonpressStrings)
										byte1 = bitlistToInteger(bitslist)
										dpadStrings = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Directional Pad"]
										bitslist = iterateStringstoBits(DirectionalPadListDE, dpadStrings)
										byte2 = bitlistToInteger(bitslist)
										conditionalsStrings = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Conditionals"]
										bitslist = iterateStringstoBits(ButtonPressConditionalsDE, conditionalsStrings)
										byte4 = bitlistToInteger(bitslist)
										temparray2.append([propertytype,byte1,byte2,0,byte4])
									elif propertytype == 3:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
										temparray2.append([propertytype,byte1,0,0,0])
									elif propertytype == 4:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
										temparray2.append([propertytype,byte1,0,0,0])
									elif propertytype == 5:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["State Type"]
										byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 4"]
										tempdict = dict([(value, key) for key, value in StateModifiersDictK2.items()]) 
										byte1 = tempdict[byte1]
										temparray2.append([propertytype,byte1,0,0,byte4])
									elif propertytype == 7:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
										temparray2.append([propertytype,byte1,0,0,0])
									elif propertytype == 9:
										byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
										temparray2.append([propertytype,0,0,0,byte4])
									elif propertytype == 12:
										short1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Enemy Distance"]
										byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 4"]
										temparray2.append([propertytype,short1,0,byte4])
									elif propertytype == 19:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte"]
										byte2 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Analog Direction"]
										byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Conditions"]
										temparray2.append([propertytype,byte1,byte2,0,byte4])
									elif propertytype == 22:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Quickstep Direction"]
										tempdict = dict([(value, key) for key, value in QuickstepDictDE.items()]) 
										byte1 = tempdict[byte1]
										temparray2.append([propertytype,byte1,0,0,0])
									elif propertytype == 23:
										propint1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Skill ID"]
										temparray2.append([propertytype,propint1])
									elif propertytype == 26:
										propint1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Timing"]
										temparray2.append([propertytype,propint1])
									else:
										byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
										byte2 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 2"]
										byte3 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 3"]
										byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 4"]
										temparray2.append([propertytype,byte1,byte2,byte3,byte4])
								FollowUpPropValues.append(temparray2)
							else:
								FollowUpPropValues.append([])
					else:
						FollowUpPropValues.append([])
						numfollowups = 0
					if animtablebool == 1:
						for animtable in list(jsonfile[commandsetname]["Move Table"][movename]["Animation Table"].keys()):
							animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Animation Used"]
							if animvalue == "Null":
								animvalue = b'\x00'
							unkuint32 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown uint32"]
							byte1 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 1"]
							byte2 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 2"]
							byte3 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 3"]
							byte4 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 4"]
							byte5 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 5"]
							byte6 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 6"]
							byte7 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 7"]
							byte8 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 8"]
							AnimationTableValues.append([animvalue, unkuint32, byte1, byte2, byte3, byte4, byte5, byte6, byte7, byte8])
					elif "Animation Used" in jsonfile[commandsetname]["Move Table"][movename]:
						animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Used"]
						if animvalue == "Null":
							animvalue = b'\x00'
						AnimationValues.append([animvalue,"Useless"])
					elif movetype == 3:
						animshort1 = byte1 = jsonfile[commandsetname]["Move Table"][movename]["Moveset IDx"]
						animshort2 = byte1 = jsonfile[commandsetname]["Move Table"][movename]["Unknown Short"]
						AnimationValues.append([animshort1, animshort2,"Useless"])
					elif movetype == 17:
						animvalue = -1
						AnimationValues.append([animvalue,"Useless"])
					elif movetype == 4:
						byte1 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 1"]
						byte2 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 2"]
						byte3 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 3"]
						byte4 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 4"]
						byte5 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 5"]
						byte6 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 6"]
						byte7 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 7"]
						byte8 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 8"]
						AnimationValues.append([byte1,byte2,byte3,byte4,byte5,byte6,byte7,byte8])
					
					
					#Writes Move to File
					x = 0
					while x < numfollowups:
						FollowUpPropValuePointers = []
						y = 0
						while y < len(FollowUpPropValues[x]):
							currentpos = newfile.tell()
							FollowUpPropValuePointers.append(currentpos)
							if FollowUpPropValues[x][y][0] == 11:
								if fileversion == 16:
									StringPointer = stringpointerdict[FollowUpPropValues[x][y][1]]
									newfile.write(int_to_bytes(StringPointer, 4))
									newfile.write(b'\x00\x00\x00\x00')
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4))
									newfile.write(b'\x00\x00\x00\x00')
								if fileversion == 17:
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 3))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][2], 1))
									newfile.write(b'\x00\x00\x00\x00')
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4))
									newfile.write(b'\x00\x00\x00\x00')
							elif FollowUpPropValues[x][y][0] == 12:
								#propertytype,short1,0,byte4
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 2))
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][2], 1))
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][3], 1))
								newfile.write(b'\x00\x00\x00\x00')
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4))
								newfile.write(b'\x00\x00\x00\x00')
							elif FollowUpPropValues[x][y][0] == 23 or FollowUpPropValues[x][y][0] == 26:
								#propertytype,propint1
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 4))
								newfile.write(b'\x00\x00\x00\x00')
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4))
								newfile.write(b'\x00\x00\x00\x00')								
							else:
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 1))
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][2], 1))
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][3], 1))
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][4], 1))
								newfile.write(b'\x00\x00\x00\x00')
								newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4))
								newfile.write(b'\x00\x00\x00\x00')
							y = y + 1
						#Writes Move Follow Up Property List to File
						FollowUpPropertyListPointer = newfile.tell()
						y = 0
						while y < len(FollowUpPropValuePointers):
							newfile.write(int_to_bytes(FollowUpPropValuePointers[y], 4))
							newfile.write(b'\x00\x00\x00\x00')
							y = y + 1
						FollowUpPointers.append(newfile.tell())
						newfile.write(int_to_bytes(len(FollowUpPropValuePointers), 2))
						newfile.write(int_to_bytes(FollowUpIdx[FollowUpValues[x][0]], 2))
						newfile.write(b'\x00\x00\x00\x00')
						newfile.write(int_to_bytes(FollowUpPropertyListPointer, 4))
						newfile.write(b'\x00\x00\x00\x00')
						x = x + 1
					if animtablebool == 1:
						x = 0
						while x < len(AnimationTableValues):
							AnimationTablePointers.append(newfile.tell())
							newfile.write(int_to_bytes(stringpointerdict[AnimationTableValues[x][0]], 4))
							newfile.write(int_to_bytes(AnimationTableValues[x][1], 4))
							newfile.write(int_to_bytes(AnimationTableValues[x][2], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][3], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][4], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][5], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][6], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][7], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][8], 1))
							newfile.write(int_to_bytes(AnimationTableValues[x][9], 1))
							x = x + 1
						AnimTableTablePointer = newfile.tell()
						x = 0
						while x < len(AnimationTablePointers):
							newfile.write(int_to_bytes(AnimationTablePointers[x], 4))
							newfile.write(b'\x00\x00\x00\x00')
							x = x + 1
						AnimTableTableTablePointer = newfile.tell()
						newfile.write(int_to_bytes(AnimTableTablePointer, 4))
						newfile.write(b'\x00\x00\x00\x00\x00')
						newfile.write(int_to_bytes(len(AnimationTableValues), 1))
						newfile.write(b'\x00\x00\x00\x00\x00\x00')
					x = 0
					FollowUpTablePointer = newfile.tell()
					while x < numfollowups:
						newfile.write(int_to_bytes(FollowUpPointers[x], 4))
						newfile.write(b'\x00\x00\x00\x00')
						x = x + 1
					MovePointers.append(newfile.tell())
					curmovepointer = newfile.tell()
					newfile.write(int_to_bytes(stringpointerdict[movename], 4))
					newfile.write(b'\x00\x00\x00\x00')
					if animtablebool == 1:
						newfile.write(int_to_bytes(AnimTableTableTablePointer, 4))
						newfile.write(b'\x00\x00\x00\x00')
					elif movetype == 3:
						newfile.write(int_to_bytes(AnimationValues[0][0], 2))
						newfile.write(int_to_bytes(AnimationValues[0][1], 2))
						newfile.write(b'\x00\x00\x00\x00')
					elif movetype == 17:
						newfile.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
					elif movetype == 4:
						newfile.write(int_to_bytes(AnimationValues[0][0], 1))
						newfile.write(int_to_bytes(AnimationValues[0][1], 1))
						newfile.write(int_to_bytes(AnimationValues[0][2], 1))
						newfile.write(int_to_bytes(AnimationValues[0][3], 1))
						newfile.write(int_to_bytes(AnimationValues[0][4], 1))
						newfile.write(int_to_bytes(AnimationValues[0][5], 1))
						newfile.write(int_to_bytes(AnimationValues[0][6], 1))
						newfile.write(int_to_bytes(AnimationValues[0][7], 1))
					else:
						newfile.write(int_to_bytes(stringpointerdict[AnimationValues[0][0]], 4))
						newfile.write(b'\x00\x00\x00\x00')
					newfile.write(int_to_bytes(FollowUpTablePointer, 4))
					newfile.write(b'\x00\x00\x00\x00')
					newfile.write(int_to_bytes(curmovepointer, 4))
					newfile.write(b'\x00\x00\x00\x00')
					newfile.write(int_to_bytes(numfollowups, 2))
					newfile.write(int_to_bytes(animtablebool, 1))
					newfile.write(int_to_bytes(movetype, 1))
					newfile.write(b'\x00\x00\x00\x00')
				x = 0
				movetablepointer = newfile.tell()
				while x < len(MovePointers):
					newfile.write(int_to_bytes(MovePointers[x], 4))
					newfile.write(b'\x00\x00\x00\x00')
					x = x + 1
					
				WeaponSetPointers = []
				WeaponMovesetListPointer = 0
				if "Weapon Moveset Table" in jsonfile[commandsetname]:
					for weaponset in list(jsonfile[commandsetname]["Weapon Moveset Table"].keys()):
						WeaponPropertyArray = []
						WeaponPropertyPointers = []
						numwepprops = len(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"])
						WeaponCommand = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Command Set ID for Weapon Moveset"]
						for weaponprops in list(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"].keys()):
							propshort1 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Weapon Category ID"]
							propshort2 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 2"]
							propshort3 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 3"]
							propshort4 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 4"]
							temparray3 = []
							temparray3.append([propshort1,propshort2,propshort3,propshort4])
							WeaponPropertyArray.append(temparray3)
						x = 0
						while x < numwepprops:
							y = 0
							while y < len(WeaponPropertyArray[x]):
								WeaponPropertyPointers.append(newfile.tell())
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][0], 2))
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][1], 2))
								newfile.write(b'\x00\x00\x00\x00')
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][2], 2))
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][3], 2))
								newfile.write(b'\x00\x00\x00\x00')
								y = y + 1
							x = x + 1
						WeaponMovesetPropListPointer = newfile.tell()
						x = 0
						while x < len(WeaponPropertyPointers):
							newfile.write(int_to_bytes(WeaponPropertyPointers[x], 4))
							newfile.write(b'\x00\x00\x00\x00')
							x = x + 1
						WeaponCommandSetPointer = newfile.tell()
						newfile.write(int_to_bytes(len(WeaponPropertyPointers), 2))
						newfile.write(int_to_bytes(WeaponCommand, 2))
						newfile.write(b'\x00\x00\x00\x00')
						newfile.write(int_to_bytes(WeaponMovesetPropListPointer, 4))
						newfile.write(b'\x00\x00\x00\x00')
						WeaponSetPointers.append(newfile.tell())
						newfile.write(int_to_bytes(WeaponCommandSetPointer, 4))
						newfile.write(b'\x00\x00\x00\x00')
						newfile.write(int_to_bytes(WeaponCommand, 4))
						newfile.write(b'\x00\x00\x00\x00')
					x = 0
					WeaponMovesetListPointer = newfile.tell()
					while x < len(WeaponSetPointers):
						newfile.write(int_to_bytes(WeaponSetPointers[x], 4))
						newfile.write(b'\x00\x00\x00\x00')
						x = x + 1				

				CommandSetPointerList.append(newfile.tell())
				currcommandsetpointer = newfile.tell()
				newfile.write(int_to_bytes(stringpointerdict[commandsetname], 4))
				newfile.write(b'\x00\x00\x00\x00')
				newfile.write(int_to_bytes(commandsetID, 4))
				newfile.write(b'\x00\x00\x00\x00')
				newfile.write(int_to_bytes(movetablepointer, 4))
				newfile.write(b'\x00\x00\x00\x00')
				if WeaponMovesetListPointer == 0:
					newfile.write(int_to_bytes(currcommandsetpointer, 4))
				else:
					newfile.write(int_to_bytes(WeaponMovesetListPointer, 4))
				newfile.write(b'\x00\x00\x00\x00')
				newfile.write(int_to_bytes(len(MovePointers), 2))
				newfile.write(int_to_bytes(len(WeaponSetPointers), 2))
				newfile.write(b'\x00\x00\x00\x00')
				CommandSetOrderIDx = CommandSetOrderIDx + 1


		x = 0
		CommandSetsListPointer = newfile.tell()
		while x < len(CommandSetPointerList):
			newfile.write(int_to_bytes(CommandSetPointerList[x], 4))
			newfile.write(b'\x00\x00\x00\x00')
			x = x + 1
		newfile.write(int_to_bytes(CommandSetsListPointer, 4))
		newfile.write(b'\x00\x00\x00\x00')
		newfile.write(int_to_bytes(len(CommandSetPointerList), 4))
		newfile.write(b'\x00\x00\x00\x00')
		filesize = newfile.tell()
		newfile.close
		newfile = open("fighter_command new.cfc", 'rb+')
		newfile.seek(12)
		newfile.write(int_to_bytes(filesize, 4))
		file.close
		newfile.close







	elif VersionDictionary[fileversion] == "Old Engine":
		if enginegame == 0:
			print("Unable to find Engine Game. Please choose which Old Engine Game you are repacking:")
			print("0 = Yakuza 0/Kiwami 1")
			print("1 = Yakuza 5")
			OEGameText = input("Enter a Number: ")
			OEGame = int(OEGameText)
			if OEGame > 1:
				print("An incorrect option was entered. Please restart the program and try again.")
				input("Press ENTER to exit... ")
				sys.exit()
			setnamekey = 1
		else:
			OEGame = OEGameDictionary[enginegame]
			setnamekey = 2
		newfile.write(b'\x43\x46\x43\x49\x02\x01\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00')#Writes header with filesize filler
		for f in os.listdir(kfile):#Loops through all Json files and collects string data
			curfile = workdir + "\\" + f
			with open(curfile, 'r', encoding='utf8') as file:
				jsonfile = json.load(file)
				fileversion = jsonfile["File Version"]
				commandsetname = list(jsonfile.keys())[setnamekey]
				stringlist.append(commandsetname)
				commandsetID = jsonfile[commandsetname]["Command Set Name"]
				if commandsetID == "Null":
					commandsetID = b'\x00'
				stringlist.append(commandsetID)
				if "Move Table" in jsonfile[commandsetname]:
					for move in list(jsonfile[commandsetname]["Move Table"].keys()):
						movename = move
						stringlist.append(movename)
						if "Animation Used" in jsonfile[commandsetname]["Move Table"][movename]:
							animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Used"]
							if animvalue == "Null":
								animvalue = b'\x00'
							stringlist.append(animvalue)
						if "Animation Table" in jsonfile[commandsetname]["Move Table"][movename]:
							for animtables in list(jsonfile[commandsetname]["Move Table"][movename]["Animation Table"].keys()):
								animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtables]["Animation Used"]
								if animvalue == "Null":
									animvalue = b'\x00'
								stringlist.append(animvalue)
						if "Follow Up Table" in jsonfile[commandsetname]["Move Table"][movename]:
							for followuptable in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"].keys()):
								if "Follows Up Properties" in jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]:
									for followupprop in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"].keys()):
										propertytype = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Property Type"]
										if propertytype == 10:
											heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Hact Name"]
											stringlist.append(heataction)
										if propertytype == 22:
											propertypointer = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Skill Name"]
											stringlist.append(propertypointer)
		stringlist = list( dict.fromkeys(stringlist) )
		x = 0
		
		#Writes string list to file collecting the string location and string in a dictionary.
		while x < len(stringlist):
			currentpos = newfile.tell()
			currentstring = stringlist[x]
			if currentstring == b'\x00':#Checks if null
				newfile.write(b'\x00')
			else:
				newfile.write(currentstring.encode('utf-8'))
				newfile.write(b'\x00')
			stringpointerdict[currentstring] = currentpos
			x = x + 1
		aligntext(newfile)#Adds the CC Byte enders to the end of the string table.
		
		
		#Parsing data from the jsons into Fighter_Command begins here.
		CommandSetPointerList = []
		numcommandsets = len(os.listdir(kfile))
		orderfile = open("Command Set Order List.json", 'rb')
		CommandSetOrderDictionary = json.load(orderfile)
		CommandSetOrderIDx = 0
		while CommandSetOrderIDx < numcommandsets:
			curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
			with open(curfile, 'r', encoding='utf8') as file:
				jsonfile = json.load(file)
				MovePointers = []
				FollowUpIdx = OrderedDict()
				fileversion = jsonfile["File Version"]
				commandsetname = list(jsonfile.keys())[setnamekey]
				commandsetID = jsonfile[commandsetname]["Command Set Name"]
				if commandsetID == "Null":
					commandsetID = b'\x00'

				#Shitty copy paste to get Move Idx's for later use
				x = 0
				if "Move Table" in jsonfile[commandsetname]:
					for move in list(jsonfile[commandsetname]["Move Table"].keys()):
						movename = move
						FollowUpIdx[movename] = x
						x = x + 1
					
				x = 0
				if "Move Table" in jsonfile[commandsetname]:
					for move in list(jsonfile[commandsetname]["Move Table"].keys()):
						FollowUpPropValues = []
						FollowUpValues = []
						FollowUpValuePointers = []
						FollowUpPointers = []
						MoveValues = []
						AnimationTableValues = []
						AnimationValues = []
						AnimationTablePointers = []
						AdditionalMoveProps = []
						AdditionalMovePropsPointers = []
						movename = move
						movetype = jsonfile[commandsetname]["Move Table"][movename]["Move Type"]
						animtablebool = jsonfile[commandsetname]["Move Table"][movename]["Animation Table Bool"]
						if "Follow Up Table" in jsonfile[commandsetname]["Move Table"][movename]:
							numfollowups = len(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"])
							for followuptable in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"].keys()):
								temparray1 = []
								followupval = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up to"]
								temparray1.append(followupval)
								FollowUpValues.append(temparray1)
								if "Follows Up Properties" in jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]:
									temparray2 = []
									for followupprop in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"].keys()):
										propertytype = list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop].values())[0]
										if propertytype == 10:
											heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Hact Name"]
											temparray2.append([propertytype, heataction])
										elif propertytype == 22:
											propertypointer = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Skill Name"]
											temparray2.append([propertytype, propertypointer])
										elif propertytype == 0 or propertytype == 1 or propertytype == 5:
											buttonpressStrings = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Button Press"]
											bitslist = iterateStringstoBits(ButtonPressListOE, buttonpressStrings)
											byte1 = bitlistToInteger(bitslist)
											dpadStrings = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Directional Pad"]
											bitslist = iterateStringstoBits(DirectionalPadListOE, dpadStrings)
											byte2 = bitlistToInteger(bitslist)
											conditionalsStrings = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Conditionals"]
											bitslist = iterateStringstoBits(ButtonPressConditionalsOE, conditionalsStrings)
											byte4 = bitlistToInteger(bitslist)
											temparray2.append([propertytype,byte1,byte2,0,byte4])
										elif propertytype == 2:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
											temparray2.append([propertytype,byte1,0,0,0])
										elif propertytype == 3:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
											temparray2.append([propertytype,byte1,0,0,0])
										elif propertytype == 4:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["State Type"]
											byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 4"]
											tempdict = dict([(value, key) for key, value in StateModifiersDictOE.items()]) 
											byte1 = tempdict[byte1]
											temparray2.append([propertytype,byte1,0,0,byte4])
										elif propertytype == 6:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
											temparray2.append([propertytype,byte1,0,0,0])
										elif propertytype == 8:
											byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
											temparray2.append([propertytype,0,0,0,byte4])
										elif propertytype == 11:
											short1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Enemy Distance"]
											byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 4"]
											temparray2.append([propertytype,short1,0,byte4])
										elif propertytype == 18:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte"]
											byte2 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Analog Direction"]
											byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Conditions"]
											temparray2.append([propertytype,byte1,byte2,0,byte4])
										elif propertytype == 21:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Quickstep Direction"]
											tempdict = dict([(value, key) for key, value in QuickstepDictOE.items()]) 
											byte1 = tempdict[byte1]
											temparray2.append([propertytype,byte1,0,0,0])
										elif propertytype == 25:
											propint1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Timing"]
											temparray2.append([propertytype,propint1])											
										else:
											byte1 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 1"]
											byte2 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 2"]
											byte3 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 3"]
											byte4 = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Unk Byte 4"]
											temparray2.append([propertytype,byte1,byte2,byte3,byte4])
									FollowUpPropValues.append(temparray2)
								else:
									FollowUpPropValues.append([])
						else:
							FollowUpPropValues.append([])
							numfollowups = 0
						if animtablebool == 1:
							for animtable in list(jsonfile[commandsetname]["Move Table"][movename]["Animation Table"].keys()):
								animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Animation Used"]
								if animvalue == "Null":
									animvalue = b'\x00'
								byte1 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 1"]
								byte2 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 2"]
								byte3 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 3"]
								byte4 = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtable]["Unknown byte 4"]
								AnimationTableValues.append([animvalue, byte1, byte2, byte3, byte4])
						elif "Animation Used" in jsonfile[commandsetname]["Move Table"][movename]:
							animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Used"]
							if animvalue == "Null":
								animvalue = b'\x00'
							AnimationValues.append([animvalue,"Useless"])
						elif movetype == 2:
							short1 = jsonfile[commandsetname]["Move Table"][movename]["Moveset IDx"]
							short2 = jsonfile[commandsetname]["Move Table"][movename]["Unknown Short"]
							AnimationValues.append([short1, short2,"Useless"])
						elif movetype == 3:
							byte1 = jsonfile[commandsetname]["Move Table"][movename]["Moveset IDx for Sync"]
							byte2 = jsonfile[commandsetname]["Move Table"][movename]["Unknown Short"]
							AnimationValues.append([byte1,byte2])
						if "Additional Properties Table" in jsonfile[commandsetname]["Move Table"][movename]:
							numadditionalprops = len(jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"])
							for moveproperty in list(jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"].keys()):
								unkshort1 = jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"][moveproperty]["Unk Short 1"]
								unkshort2 = jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"][moveproperty]["Unk Short 1"]
								AdditionalMoveProps.append([unkshort1, unkshort2])
						else:
							numadditionalprops = 0
						
						#Writes Move to File
						x = 0
						while x < numfollowups:
							FollowUpPropValuePointers = []
							y = 0
							while y < len(FollowUpPropValues[x]):
								currentpos = newfile.tell()
								FollowUpPropValuePointers.append(currentpos)
								if FollowUpPropValues[x][y][0] == 10:
									StringPointer = stringpointerdict[FollowUpPropValues[x][y][1]]
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4, "big"))
									newfile.write(int_to_bytes(StringPointer, 4, "big"))
								elif FollowUpPropValues[x][y][0] == 22:
									PropertyPointer = stringpointerdict[FollowUpPropValues[x][y][1]]
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4, "big"))
									newfile.write(int_to_bytes(PropertyPointer, 4, "big"))
								elif FollowUpPropValues[x][y][0] == 11:
									#propertytype,short1,0,byte4
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][3], 1, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][2], 1, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 2, "big"))
								elif FollowUpPropValues[x][y][0] == 25:
									#propertytype,propint
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 4, "big"))							
								else:
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][0], 4, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][4], 1, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][3], 1, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][2], 1, "big"))
									newfile.write(int_to_bytes(FollowUpPropValues[x][y][1], 1, "big"))
								y = y + 1
							#Writes Move Follow Up Property List to File
							FollowUpPropertyListPointer = newfile.tell()
							y = 0
							while y < len(FollowUpPropValuePointers):
								newfile.write(int_to_bytes(FollowUpPropValuePointers[y], 4, "big"))
								y = y + 1
							FollowUpPointers.append(newfile.tell())
							newfile.write(int_to_bytes(len(FollowUpPropValuePointers), 2, "big"))
							newfile.write(int_to_bytes(FollowUpIdx[FollowUpValues[x][0]], 2, "big"))
							newfile.write(int_to_bytes(FollowUpPropertyListPointer, 4, "big"))
							x = x + 1
						x = 0
						AdditionalMovePropsPointers = []
						while x < numadditionalprops:
							currentpos = newfile.tell()
							AdditionalMovePropsPointers.append(currentpos)
							newfile.write(int_to_bytes(AdditionalMoveProps[x][0], 2, "big"))
							newfile.write(int_to_bytes(AdditionalMoveProps[x][1], 2, "big"))
							x = x + 1
						
						if animtablebool == 1:
							x = 0
							while x < len(AnimationTableValues):
								AnimationTablePointers.append(newfile.tell())
								newfile.write(int_to_bytes(stringpointerdict[AnimationTableValues[x][0]], 4, "big"))
								newfile.write(int_to_bytes(AnimationTableValues[x][1], 1))
								newfile.write(int_to_bytes(AnimationTableValues[x][2], 1))
								newfile.write(int_to_bytes(AnimationTableValues[x][3], 1))
								newfile.write(int_to_bytes(AnimationTableValues[x][4], 1))
								x = x + 1
							AnimTableTablePointer = newfile.tell()
							x = 0
							while x < len(AnimationTablePointers):
								newfile.write(int_to_bytes(AnimationTablePointers[x], 4, "big"))
								x = x + 1
							AnimTableTableTablePointer = newfile.tell()
							if OEGame == 0:
								newfile.write(int_to_bytes(len(AnimationTableValues), 2, "big"))
							elif OEGame == 1:
								newfile.write(int_to_bytes(1, 1, "big"))
								newfile.write(int_to_bytes(len(AnimationTableValues), 1, "big"))
							newfile.write(b'\x00\x00')
							newfile.write(int_to_bytes(AnimTableTablePointer, 4, "big"))
						x = 0
						FollowUpTablePointer = newfile.tell()
						while x < numfollowups:
							newfile.write(int_to_bytes(FollowUpPointers[x], 4, "big"))
							x = x + 1
						x = 0
						AdditionalMovePropsPointer = newfile.tell()
						while x < numadditionalprops:
							#Writes Move Additional Property List to File
							newfile.write(int_to_bytes(AdditionalMovePropsPointers[x], 4, "big"))
							x = x + 1
						MovePointers.append(newfile.tell())
						curmovepointer = newfile.tell()
						newfile.write(int_to_bytes(stringpointerdict[movename], 4, "big"))
						newfile.write(int_to_bytes(numfollowups, 1, "big"))
						if OEGame == 0:
							newfile.write(int_to_bytes(numadditionalprops, 1, "big"))
							newfile.write(int_to_bytes(animtablebool, 1, "big"))
						if OEGame == 1:
							newfile.write(int_to_bytes(animtablebool, 1, "big"))
							newfile.write(int_to_bytes(numadditionalprops, 1, "big"))
						newfile.write(int_to_bytes(movetype, 1, "big"))
						if animtablebool == 1:
							newfile.write(int_to_bytes(AnimTableTableTablePointer, 4, "big"))
						elif movetype == 2:
							newfile.write(int_to_bytes(AnimationValues[0][0], 2, "big"))
							newfile.write(int_to_bytes(AnimationValues[0][1], 2, "big"))
						elif movetype == 16:
							newfile.write(b'\x00\x00\x00\x00')
						elif movetype == 3:
							newfile.write(int_to_bytes(AnimationValues[0][0], 2, "big"))
							newfile.write(int_to_bytes(AnimationValues[0][1], 2, "big"))
						else:
							newfile.write(int_to_bytes(stringpointerdict[AnimationValues[0][0]], 4, "big"))
						newfile.write(int_to_bytes(FollowUpTablePointer, 4, "big"))
						if OEGame == 0:
							newfile.write(int_to_bytes(AdditionalMovePropsPointer, 4, "big"))
				x = 0
				movetablepointer = newfile.tell()
				while x < len(MovePointers):
					newfile.write(int_to_bytes(MovePointers[x], 4, "big"))
					x = x + 1
					
				WeaponSetPointers = []
				WeaponMovesetListPointer = 0
				if "Weapon Moveset Table" in jsonfile[commandsetname]:
					for weaponset in list(jsonfile[commandsetname]["Weapon Moveset Table"].keys()):
						WeaponPropertyArray = []
						WeaponPropertyPointers = []
						numwepprops = len(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"])
						WeaponCommand = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Command Set Name for Weapon Moveset"]
						if WeaponCommand == "Null":
							WeaponCommand = b'\x00'
						for weaponprops in list(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"].keys()):
							propshort1 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Weapon Category ID"]
							propshort2 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 2"]
							propshort3 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 3"]
							propshort4 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 4"]
							temparray3 = []
							temparray3.append([propshort1,propshort2,propshort3,propshort4])
							WeaponPropertyArray.append(temparray3)
						x = 0
						while x < numwepprops:
							y = 0
							while y < len(WeaponPropertyArray[x]):
								WeaponPropertyPointers.append(newfile.tell())
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][3], 2, "big"))
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][2], 2, "big"))
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][1], 2, "big"))
								newfile.write(int_to_bytes(WeaponPropertyArray[x][y][0], 2, "big"))
								y = y + 1
							x = x + 1
						WeaponMovesetPropListPointer = newfile.tell()
						x = 0
						while x < len(WeaponPropertyPointers):
							newfile.write(int_to_bytes(WeaponPropertyPointers[x], 4, "big"))
							x = x + 1
						WeaponCommandSetPointer = newfile.tell()
						newfile.write(int_to_bytes(len(WeaponPropertyPointers), 2, "big"))
						newfile.write(b'\x00\x00')
						newfile.write(int_to_bytes(WeaponMovesetPropListPointer, 4, "big"))
						WeaponSetPointers.append(newfile.tell())
						newfile.write(int_to_bytes(WeaponCommandSetPointer, 4, "big"))
						if WeaponCommand == "Zero":
							newfile.write(b'\x00\x00\x00\x00')
						else:
							newfile.write(int_to_bytes(stringpointerdict[WeaponCommand], 4, "big"))
					x = 0
					WeaponMovesetListPointer = newfile.tell()
					while x < len(WeaponSetPointers):
						newfile.write(int_to_bytes(WeaponSetPointers[x], 4, "big"))
						x = x + 1				

				CommandSetPointerList.append(newfile.tell())
				currcommandsetpointer = newfile.tell()
				newfile.write(int_to_bytes(stringpointerdict[commandsetname], 4, "big"))
				newfile.write(int_to_bytes(stringpointerdict[commandsetID], 4, "big"))
				newfile.write(int_to_bytes(len(MovePointers), 4, "big"))
				newfile.write(int_to_bytes(movetablepointer, 4, "big"))
				newfile.write(int_to_bytes(len(WeaponSetPointers), 4, "big"))
				if WeaponMovesetListPointer == 0:
					newfile.write(int_to_bytes(currcommandsetpointer, 4, "big"))
				else:
					newfile.write(int_to_bytes(WeaponMovesetListPointer, 4, "big"))
				CommandSetOrderIDx = CommandSetOrderIDx + 1

		x = 0
		CommandSetsListPointer = newfile.tell()
		while x < len(CommandSetPointerList):
			newfile.write(int_to_bytes(CommandSetPointerList[x], 4, "big"))
			x = x + 1
		newfile.write(int_to_bytes(len(CommandSetPointerList), 4, "big"))
		newfile.write(int_to_bytes(CommandSetsListPointer, 4, "big"))
		filesize = newfile.tell()
		newfile.close
		newfile = open("fighter_command new.cfc", 'rb+')
		newfile.seek(12)
		newfile.write(int_to_bytes(filesize, 4, "big"))
		file.close
		newfile.close