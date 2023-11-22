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
from binary_reader import BinaryReader


def bitfield(num):
	#bitfieldlist = [1 if x=='1' else 0 for x in "{:08b}".format(num)]
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
				curstring = curstring + "," + List[x]
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
	
def aligntext(myfile, byte = b'\xCC'):
	currentpos = myfile.tell()
	numfiller = 8 - (currentpos % 8)
	if numfiller == 0:
		numfiller = 8
	x = 0
	while x < numfiller:
		myfile.write(byte)
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
				stringver = stringver.decode('shift-jis')
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
			stringver = stringver.decode('shift-jis')
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
#
def jsonKeys2int(x):
    if isinstance(x, dict):
            return {int(k):v for k,v in x.items()}
    return x
	
def stringlistEntryAdd(stringname, stringlist):
	if stringname == "Null":
		stringname = b'\x00'
	stringlist.append(stringname)
	
	
CommandSetDictionary = tree() #Stores Data for Command Sets
print(CommandSetDictionary)
CommandSetIDDictionary = OrderedDict() #Stores a list of Command Sets and their ID's for reference.
CommandSetOrderIDxDictionary = OrderedDict()
VersionDictionary = OrderedDict() #Stores a list of Version Numbers and their Associated Engine
VersionDictionary[7] = "Old Engine"
VersionDictionary[16] = "Dragon Engine"
VersionDictionary[17] = "Dragon Engine"
VersionDictionaryHact = {3: "Old Engine",5: "Dragon Engine", 6: "Dragon Engine"}
OEGameDictionary = {"Yakuza 0 / Kiwami 1": 0, "Yakuza 5": 1, "Yakuza Ishin": 2,}
DEGameDictionary = {"Yakuza 6": 0, "Yakuza Kiwami 2 / Judgement": 1, "Yakuza 6 Blue Jacket Demo": 2,}
jsonfile = OrderedDict() #Stores the dumped json from file.
FollowUpMoveIdx = [] #Stores Id's of Moves for follow ups
ButtonPressListDE = ["Unknown7","Unknown6","Unknown5","D-Pad Right","D-Pad Left","D-Pad Down","D-Pad Up","R2","R1", "L2", "L1", "Cross", "Circle", "Triangle", "Square", "Unknown8"]
ButtonPressListOE = ["Unknown8","Unknown7","Unknown6","Unknown5","D-Pad Right","D-Pad Left","D-Pad Down","D-Pad Up","L2","R2", "R1", "L1", "Cross", "Circle", "Triangle", "Square"]
StateModifiersDict = {1: "In Heat Mode", 3: "Run Startup to Full Run", 4: "Enemy Down, Including getting up Animation", 5: "Enemy Standing", 7: "Enemy Down from the Front", 8: "Enemy Down from Behind", 19: "Near Wall", 29: "Lock-On", 30: "Attack Punch", 31: "Full Run", 38: "Full Health", 39: "Extreme Heat", 40: "Yakuza 6 Charge State"}
QuickstepDict = {0: "Front Quickstep", 1: "Left Quickstep", 2: "Back Quickstep", 3: "Right Quickstep"}
PropertyTypeDictDE = {1: "Button Press", 2: "Button Hold", 3: "Follow Up Start Lock", 4: "Follow Up Lifetime Lock",
                      5: "Fighter Status", 6: "Button Press (Buffered Input)", 7: "Follow Up On Hit", 8: "Outer",
                      9: "Analog Deadzone", 10: "Weapon Category", 11: "Heat Action", 12: "Distance Limit",
                      13: "Angle Limit", 14: "Target Status", 15: "Target Change", 16: "Range", 17: "Weapon ID",
                      18: "Height", 19: "Analog Direction", 20: "Charge", 21: "Change Auth", 22: "Quickstep",
                      23: "Skill Required", 24: "Have Item", 25: "Ctrl Type", 26: "Timing", 27: "Pickup",
                      28: "Button Renda", 29: "Combo Number", 30: "Sync Role", 31: "Custom", 32: "Combo Speed",
                      33: "Battle Style", 34: "Heat Gear Level", 35: "Height Param", 36: "Damage Hit",
                      37: "Motion ID", 38: "Stun", 39: "Heat Level", 40: "Push Fighter", 41: "Unknown Hact Property",
                      41: "Range ID", 42: "Pickup Narrow", 43: "Charge Time", 44: "Charge Level", 45: "Buff Style",
                      46: "Player Skill", 47: "Charge Type", 48: "Hact not used", 49: "Reaction Type", 50: "Item Buff",
                      51: "Dist Area", 52: "Defence Success", 53: "Skill Success", 54: "Skill Failed", 55: "Player ID", 56: "Num"}
PropertyTypeDictOE = downgradeDictToOE(PropertyTypeDictDE)
Conditionals = ["NOT", "Upon Action Completion","Unknown3","Unknown4","Unknown5","Unknown6","Unknown7","Unknown8"]
TargetEntityDict = {0: "User", 1: "Enemy"}
TargetConditional = {1: "Anywhere?", 2: "Target in Front", 6: "Target Behind"}
ListList = ["ButtonPressListDE","ButtonPressListOE","Conditionals"]
DictList = ["StateModifiersDict","QuickstepDict","PropertyTypeDictDE", "TargetEntityDict", "TargetConditional"]
ListFin = []



print ('''
   +------------------------+
   |   FIGHTER  COMMANDER   |
   +------------------------+\n
   TEST VERSION - EXPECT ERRORS\n''')

if (len(sys.argv) <= 1):
	print ("Usage: Drag and drop fighter_command.cfc onto Fighter Commander to extract to json")
	print ("Drag and drop folder containing jsons onto Fighter Commander to rebuild fighter_command.cfc")
	print ("Additional information can be obtained by typing -help")
	print ("")
	print ("Would you like to dump editable dictionary definitions?")
	temp = input("Type y to dump, else press ENTER to exit... ")
	if temp == "y":
		curdir =  os.getcwd()
		mypath = curdir + "\\Dictionaries"
		ButtonPressListDE = {k: v for v, k in enumerate(ButtonPressListDE)}
		ButtonPressListOE = {k: v for v, k in enumerate(ButtonPressListOE)}
		Conditionals = {k: v for v, k in enumerate(Conditionals)}
		if not os.path.isdir(mypath):
			os.makedirs(mypath)
		with open(mypath + "\\" + "ButtonPressListDE" + ".json", 'w') as outfile:
			json.dump(ButtonPressListDE, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "ButtonPressListOE" + ".json", 'w') as outfile:
			json.dump(ButtonPressListOE, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "Conditionals" + ".json", 'w') as outfile:
			json.dump(Conditionals, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "StateModifiersDict" + ".json", 'w') as outfile:
			json.dump(StateModifiersDict, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "QuickstepDict" + ".json", 'w') as outfile:
			json.dump(QuickstepDict, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "PropertyTypeDictDE" + ".json", 'w') as outfile:
			json.dump(PropertyTypeDictDE, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "TargetEntityDict" + ".json", 'w') as outfile:
			json.dump(TargetEntityDict, outfile, indent=2, ensure_ascii=False)
		with open(mypath + "\\" + "TargetConditional" + ".json", 'w') as outfile:
			json.dump(TargetConditional, outfile, indent=2, ensure_ascii=False)
	sys.exit()
	

def propertyExtraction(f, extract, d, CurrentPropDict, PropertyDictionary, EngineVersion, fileversion, typedes, jsonfile, ButtonPressList = ButtonPressListDE, hactnamedict = [], Conditionals = Conditionals, StateModifiersDict = StateModifiersDict, QuickstepDict = QuickstepDict, TargetEntityDict = TargetEntityDict, TargetConditional = TargetConditional):
	if EngineVersion == "Dragon Engine":
		OEMod = 0
	elif EngineVersion == "Old Engine":
		OEMod = 1	
	if extract == True: PropType = PropertyDictionary["propint2"] + OEMod
	else: 
		PropType = list(jsonfile.values())[0] + OEMod
		propertytype = list(jsonfile.values())[0]
	temparray = []
	
	if PropType == 11:
		if fileversion == 16:
			if extract == True:
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Hact Name"] = GetStringFromPointer(f, PropertyDictionary["propint1"])
			else:
				heataction = jsonfile["Hact Name"]
				extracttype = "Pointer"
				temparray.extend((extracttype,propertytype, heataction))
		elif fileversion == 17:
			if extract == True:
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Heat Action IDx"] = PropertyDictionary["propint1ver17"]
				CurrentPropDict["Property "+ str(d) + typedes]["Unknown Property Byte"] = PropertyDictionary["propbyte4"]
			else:
				heataction = jsonfile["Heat Action IDx"]
				unkpropbyte = jsonfile["Unknown Property Byte"]
				extracttype = "Judgement Hact"
				temparray.extend((extracttype,propertytype, heataction, unkpropbyte))
		else:
			if extract == True:
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Hact Name"] = GetStringFromPointer(f, PropertyDictionary["propint1"])
			else:
				heataction = jsonfile["Hact Name"]
				extracttype = "Pointer"
				temparray.extend((extracttype,propertytype, heataction))
				
	elif PropType in [1,2,6]:
		if extract == True:
			ButtonPressBitmask1 = bitfield(PropertyDictionary["propbyte1"])
			ButtonPressBitmask2 = bitfield(PropertyDictionary["propbyte2"])
			ButtonPressBitmask2.extend(ButtonPressBitmask1)
			ButtonPressBitmask = ButtonPressBitmask2
			ConditionalsBitmask = bitfield(PropertyDictionary["propbyte4"])
			buttonpress = bitfieldListMask(ButtonPressBitmask, ButtonPressList)
			conditional = bitfieldListMask(ConditionalsBitmask, Conditionals)
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Button Press"] = buttonpress
			CurrentPropDict["Property "+ str(d) + typedes]["Conditionals"] = conditional
			CurrentPropDict["Property "+ str(d) + typedes]["Additional Conditional"] = PropertyDictionary["propbyte3"]
		else:
			buttonpressStrings = jsonfile["Button Press"]
			bitslist = iterateStringstoBits(ButtonPressList, buttonpressStrings)
			short1 = bitlistToInteger(bitslist)
			byte3 = jsonfile["Additional Conditional"]

			conditionalsStrings = jsonfile["Conditionals"]
			bitslist = iterateStringstoBits(Conditionals, conditionalsStrings)
			byte4 = bitlistToInteger(bitslist)
			extracttype = "Short & 2 Bytes"
			temparray.extend((extracttype,propertytype,short1,byte3,byte4))
			
	elif PropType in [3,4]:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 1"] = PropertyDictionary["propbyte1"]
		else:
			byte1 = jsonfile["Unk Byte 1"]
			extracttype = "4 Bytes"
			temparray.extend((extracttype,propertytype,byte1,0,0,0))
			
	elif PropType == 5:
		if extract == True:
			ConditionalsBitmask = bitfield(PropertyDictionary["propbyte4"])
			conditional = bitfieldListMask(ConditionalsBitmask, Conditionals)
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			if PropertyDictionary["propbyte1"] in StateModifiersDict:
				CurrentPropDict["Property "+ str(d) + typedes]["State Type"] = StateModifiersDict[PropertyDictionary["propbyte1"]]
			else: CurrentPropDict["Property "+ str(d) + typedes]["State Type"] = "unk" + str(PropertyDictionary["propbyte1"])
			CurrentPropDict["Property "+ str(d) + typedes]["Conditionals"] = conditional
		else:
			byte1 = jsonfile["State Type"]
			tempdict = dict([(value, key) for key, value in StateModifiersDict.items()])
			if byte1 in tempdict: byte1 = tempdict[byte1]
			else: byte1 = int(byte1[3:])
			conditionalsStrings = jsonfile["Conditionals"]
			bitslist = iterateStringstoBits(Conditionals, conditionalsStrings)
			byte4 = bitlistToInteger(bitslist)
			extracttype = "4 Bytes"
			temparray.extend((extracttype,propertytype,byte1,0,0,byte4))
			
	elif PropType == 7:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 1"] = PropertyDictionary["propbyte1"]
		else:
			byte1 = jsonfile["Unk Byte 1"]
			extracttype = "4 Bytes"
			temparray.extend((extracttype,propertytype,byte1,0,0,0))
			
	elif PropType == 9:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 1"] = PropertyDictionary["propbyte4"]
		else:
			byte4 = jsonfile["Unk Byte 1"]
			extracttype = "4 Bytes"
			temparray.extend((extracttype, propertytype,0,0,0,byte4))
			
	elif PropType == 10:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Weapon Category ID"] = PropertyDictionary["propshort1"]
			ConditionalsBitmask = bitfield(PropertyDictionary["propbyte4"])
			conditional = bitfieldListMask(ConditionalsBitmask, Conditionals)
			CurrentPropDict["Property "+ str(d) + typedes]["Bitmask Byte 1"] = PropertyDictionary["propbyte3"]
			CurrentPropDict["Property "+ str(d) + typedes]["Bitmask Byte 2"] = conditional
		else:
			short1 = jsonfile["Weapon Category ID"]
			byte3 = jsonfile["Bitmask Byte 1"] 
			conditionalsStrings = jsonfile["Bitmask Byte 2"]
			bitslist = iterateStringstoBits(Conditionals, conditionalsStrings)
			byte4 = bitlistToInteger(bitslist)
			extracttype = "Short & 2 Bytes"
			temparray.extend((extracttype, propertytype,short1,byte3,byte4))
			
	elif PropType == 12:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Enemy Distance"] = PropertyDictionary["propshort1"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 4"] = PropertyDictionary["propbyte4"]
		else:
			short1 = jsonfile["Enemy Distance"]
			byte4 = jsonfile["Unk Byte 4"]
			extracttype = "Short & 2 Bytes"
			temparray.extend((extracttype, propertytype,short1,0,byte4))
			
	elif PropType == 15:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Target"] = TargetEntityDict[PropertyDictionary["propbyte1"]]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 2"] = PropertyDictionary["propbyte2"]
			if PropertyDictionary["propbyte3"] in TargetConditional:
				CurrentPropDict["Property "+ str(d) + typedes]["Target Position"] = TargetConditional[PropertyDictionary["propbyte3"]]
			else: CurrentPropDict["Property "+ str(d) + typedes]["Target Position"] = "unk" + str(PropertyDictionary["propbyte3"])
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 4"] = PropertyDictionary["propbyte4"]
		else:
			byte1 = jsonfile["Target"]
			tempdict = dict([(value, key) for key, value in TargetEntityDict.items()]) 
			byte1 = tempdict[byte1]
			byte2 = jsonfile["Unk Byte 2"]
			byte3 = jsonfile["Target Position"]
			tempdict = dict([(value, key) for key, value in TargetConditional.items()]) 
			if byte3 in tempdict: byte3 = tempdict[byte3]
			else: byte3 = int(byte3[3:])
			byte4 = jsonfile["Unk Byte 4"]
			extracttype = "4 Bytes"
			temparray.extend((extracttype, propertytype,byte1,byte2,byte3,byte4))
	elif PropType == 17:
		if extract == True:
			if EngineVersion == "Old Engine":
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Weapon Name"] = GetStringFromPointer(f, PropertyDictionary["propint1"])
			elif EngineVersion == "Dragon Engine":
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Weapon ID"] = PropertyDictionary["propint1"]
		else:
			if EngineVersion == "Old Engine":
				propstring = jsonfile["Weapon Name"]
				extracttype = "Pointer"
				temparray.extend((extracttype,propertytype, propstring))
			elif EngineVersion == "Dragon Engine":
				propint1 = jsonfile["Weapon ID"]
				extracttype = "Integer"
				temparray.extend((extracttype, propertytype,propint1))
	elif PropType == 19:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte"] = PropertyDictionary["propbyte1"]
			CurrentPropDict["Property "+ str(d) + typedes]["Analog Direction"] = PropertyDictionary["propbyte2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Conditions"] = PropertyDictionary["propbyte4"]
		else:
			byte1 = jsonfile["Unk Byte"]
			byte2 = jsonfile["Analog Direction"]
			byte4 = jsonfile["Conditions"]
			extracttype = "4 Bytes"
			temparray.extend((extracttype, propertytype,byte1,byte2,0,byte4))
			
	elif PropType == 22:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Quickstep Direction"] = QuickstepDict[PropertyDictionary["propbyte1"]]
		else:
			byte1 = jsonfile["Quickstep Direction"]
			tempdict = dict([(value, key) for key, value in QuickstepDict.items()]) 
			byte1 = tempdict[byte1]
			extracttype = "4 Bytes"
			temparray.extend((extracttype, propertytype,byte1,0,0,0))
			
	elif PropType == 23:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			if OEMod == 1: CurrentPropDict["Property "+ str(d) + typedes]["Skill Name"] = GetStringFromPointer(f, PropertyDictionary["propint1"], "big")
			else: CurrentPropDict["Property "+ str(d) + typedes]["Skill ID"] = PropertyDictionary["propint1"]
		else:
			if OEMod == 0:
				propint1 = jsonfile["Skill ID"]
				extracttype = "Integer"
				temparray.extend((extracttype, propertytype,propint1))
			else:
				propertypointer = jsonfile["Skill Name"]
				extracttype = "Pointer"
				temparray.extend((extracttype, propertytype, propertypointer))
				
	elif PropType == 24:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			if OEMod == 1: CurrentPropDict["Property "+ str(d) + typedes]["Item Name"] = GetStringFromPointer(f, PropertyDictionary["propint1"], "big")
			else: CurrentPropDict["Property "+ str(d) + typedes]["Item ID"] = PropertyDictionary["propint1"]
		else:
			if OEMod == 0:
				propint1 = jsonfile["Item ID"]
				extracttype = "Integer"
				temparray.extend((extracttype, propertytype,propint1))
			else:
				propertypointer = jsonfile["Item Name"]
				extracttype = "Pointer"
				temparray.extend((extracttype, propertytype, propertypointer))
				
	elif PropType == 26:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Timing"] = PropertyDictionary["propint1"]
		else:
			propint1 = jsonfile["Timing"]
			extracttype = "Integer"
			temparray.extend((extracttype, propertytype,propint1))
			
	elif PropType == 37:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			if OEMod == 1: CurrentPropDict["Property "+ str(d) + typedes]["Motion Name"] = GetStringFromPointer(f, PropertyDictionary["propint1"], "big")
			else: CurrentPropDict["Property "+ str(d) + typedes]["Motion ID"] = PropertyDictionary["propint1"]
		else:
			if OEMod == 0:
				propint1 = jsonfile["Motion ID"]
				extracttype = "Integer"
				temparray.extend((extracttype, propertytype,propint1))
			else:
				propertypointer = jsonfile["Motion Name"]
				extracttype = "Pointer"
				temparray.extend((extracttype, propertytype, propertypointer))
			
	elif PropType == 31:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["String"] = GetStringFromPointer(f, PropertyDictionary["propint1"])
		else:
			propstring = jsonfile["String"]
			extracttype = "Pointer"
			temparray.extend((extracttype,propertytype, propstring))
			
	elif PropType == 34:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Heat Gear"] = PropertyDictionary["propbyte1"] + 1
		else:
			byte1 = jsonfile["Heat Gear"] - 1
			extracttype = "4 Bytes"
			temparray.extend((extracttype, propertytype,byte1,0,0,0))
			
	elif PropType == 41:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 1"] = PropertyDictionary["propbyte1"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 2"] = PropertyDictionary["propbyte2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 3"] = PropertyDictionary["propbyte3"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 4"] = PropertyDictionary["propbyte4"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 5"] = PropertyDictionary["propbyteex1"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 6"] = PropertyDictionary["propbyteex2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 7"] = PropertyDictionary["propbyteex3"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 8"] = PropertyDictionary["propbyteex4"]
		else:
			byte1 = jsonfile["Unk Byte 1"]
			byte2 = jsonfile["Unk Byte 2"]
			byte3 = jsonfile["Unk Byte 3"]
			byte4 = jsonfile["Unk Byte 4"]
			byte5 = jsonfile["Unk Byte 5"]
			byte6 = jsonfile["Unk Byte 6"]
			byte7 = jsonfile["Unk Byte 7"]
			byte8 = jsonfile["Unk Byte 8"]
			extracttype = "8 Bytes"
			temparray.extend((extracttype, propertytype,byte1,byte2,byte3,byte4,byte5,byte6,byte7,byte8))
			
	elif PropType == 48:
		if extract == True:
			if fileversion == 6:
				temp = list(hactnamedict[str(PropertyDictionary["propint1"])].keys())[0]
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Hact (Property)"] = temp
			else:
				temp = GetStringFromPointer(f, PropertyDictionary["propint1"])
				CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
				CurrentPropDict["Property "+ str(d) + typedes]["Hact (Property)"] = temp
		else:
			hactpointer = jsonfile["Hact (Property)"]
			extracttype = "Pointer"
			temparray.extend((extracttype, propertytype, hactpointer))
			
	else:
		if extract == True:
			CurrentPropDict["Property "+ str(d) + typedes]["Property Type"] = PropertyDictionary["propint2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 1"] = PropertyDictionary["propbyte1"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 2"] = PropertyDictionary["propbyte2"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 3"] = PropertyDictionary["propbyte3"]
			CurrentPropDict["Property "+ str(d) + typedes]["Unk Byte 4"] = PropertyDictionary["propbyte4"]
		else:
			byte1 = jsonfile["Unk Byte 1"]
			byte2 = jsonfile["Unk Byte 2"]
			byte3 = jsonfile["Unk Byte 3"]
			byte4 = jsonfile["Unk Byte 4"]
			extracttype = "4 Bytes"
			temparray.extend((extracttype, propertytype,byte1,byte2,byte3,byte4))
	if extract == False:
		return temparray
	
def writePropertiestoFile(newfile, FollowUpPropValues, EngineVersion, fileversion, stringpointerdict):
	ExtractType = FollowUpPropValues[0]
	if ExtractType == "Pointer":
		if EngineVersion == "Old Engine":
			PropertyPointer = stringpointerdict[FollowUpPropValues[2]]
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4, "big"))
			newfile.write(int_to_bytes(PropertyPointer, 4, "big"))
		elif EngineVersion == "Dragon Engine":
			StringPointer = stringpointerdict[FollowUpPropValues[2]]
			newfile.write(int_to_bytes(StringPointer, 4))
			newfile.write(b'\x00\x00\x00\x00')
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4))
			newfile.write(b'\x00\x00\x00\x00')
	elif ExtractType == "Short & 2 Bytes":
		if EngineVersion == "Old Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[4], 1, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[3], 1, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[2], 2, "big"))
		elif EngineVersion == "Dragon Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[2], 2))
			newfile.write(int_to_bytes(FollowUpPropValues[3], 1))
			newfile.write(int_to_bytes(FollowUpPropValues[4], 1))
			newfile.write(b'\x00\x00\x00\x00')
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4))
			newfile.write(b'\x00\x00\x00\x00')
	elif ExtractType == "Integer":
		if EngineVersion == "Old Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[2], 4, "big"))
		elif EngineVersion == "Dragon Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[2], 4))
			newfile.write(b'\x00\x00\x00\x00')
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4))
			newfile.write(b'\x00\x00\x00\x00')
	elif ExtractType == "4 Bytes":
		if EngineVersion == "Old Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[5], 1, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[4], 1, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[3], 1, "big"))
			newfile.write(int_to_bytes(FollowUpPropValues[2], 1, "big"))
		elif EngineVersion == "Dragon Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[2], 1))
			newfile.write(int_to_bytes(FollowUpPropValues[3], 1))
			newfile.write(int_to_bytes(FollowUpPropValues[4], 1))
			newfile.write(int_to_bytes(FollowUpPropValues[5], 1))
			newfile.write(b'\x00\x00\x00\x00')
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4))
			newfile.write(b'\x00\x00\x00\x00')
	elif ExtractType == "8 Bytes":
		if EngineVersion == "Dragon Engine":
			newfile.write(int_to_bytes(FollowUpPropValues[2], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[3], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[4], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[5], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[6], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[7], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[8], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[9], 1, "little"))
			newfile.write(int_to_bytes(FollowUpPropValues[1], 4, "little"))
			newfile.write(b'\x00\x00\x00\x00')
		elif EngineVersion == "Old Engine":
			print("Incompatible type?")
	elif ExtractType == "Judgement Hact":
			if EngineVersion == "Dragon Engine":
				newfile.write(int_to_bytes(FollowUpPropValues[2], 3))
				newfile.write(int_to_bytes(FollowUpPropValues[3], 1))
				newfile.write(b'\x00\x00\x00\x00')
				newfile.write(int_to_bytes(FollowUpPropValues[1], 4))
				newfile.write(b'\x00\x00\x00\x00')
			elif EngineVersion == "Old Engine":
				print("Incompatible type?")
	else:
		print("Extract type missing?")
		print(FollowUpPropValues)
	
	
curdir =  os.getcwd()
mypath = curdir + "\\Dictionaries"
if not os.path.isdir(mypath):
	print("No Dictionaries folder detected. Using internal Dictionaries.")
else:
	x = 0
	while x < len(ListList):
		curfile = ListList[x]
		if os.path.exists(mypath + "\\" + curfile+ ".json"):
			with open(mypath + "\\" + curfile+ ".json", 'r', encoding='utf8') as file:
				temp = json.load(file)
				ListFin.append(list(temp.keys()))
		else: 
			print(curfile + ".json not found. Using internal Dictionary.")
			if x == 0: ListFin.append(ButtonPressListDE)
			if x == 1: ListFin.append(ButtonPressListOE)
			if x == 2: ListFin.append(Conditionals)
		x = x + 1
	ButtonPressListDE = ListFin[0]
	ButtonPressListOE = ListFin[1]
	Conditionals = ListFin[2]
	
	x = 0
	while x < len(DictList):
		curfile = DictList[x]
		if os.path.exists(mypath + "\\" + curfile+ ".json"):
			with open(mypath + "\\" + curfile+ ".json", 'r', encoding='utf8') as file:
				if x == 0: StateModifiersDict = json.load(file, object_hook=jsonKeys2int)
				if x == 1: QuickstepDict = json.load(file, object_hook=jsonKeys2int)
				if x == 2: PropertyTypeDictDE = json.load(file, object_hook=jsonKeys2int)
				if x == 3: TargetEntityDict = json.load(file, object_hook=jsonKeys2int)
				if x == 4: TargetConditional = json.load(file, object_hook=jsonKeys2int)
		else: 
			print(curfile + ".json not found. Using internal Dictionary.")
		x = x + 1




CommandSetOrderIDx = 0

parser = argparse.ArgumentParser(description="Fighter_cfc extraction tool")
parser.add_argument("file", help=".cfc file")
parser.add_argument("-sn", "--simplenames", help="Shorten property names to not include the type of property", action="store_true")
args = parser.parse_args()
kfile = args.file
filecheck = os.path.isfile(kfile)
extension = os.path.splitext(kfile)[-1].lower()
nameonly = os.path.splitext(kfile)[0]







#File Extract
if filecheck == True:
	f = open(kfile, 'rb')
	
	if extension == ".chp":
		byte1 = int.from_bytes(f.read(4),"big")
		if byte1 != 1128812617:
			print("Fileheader not equal to CHPI. Not a valid CHP file?")
			input("Press ENTER to exit... ")
			sys.exit()			
		patchedFile = "" #Init patched file	
		curdir =  os.getcwd()
		mypath = curdir + "\\Hact CHP"
		if not os.path.isdir(mypath):
		   os.makedirs(mypath)
			
			
		f.seek(4, 1)#skips endianess
		fileversion = int.from_bytes(f.read(1),"little")
		if fileversion == 0:
			f.seek(2, 1)
			fileversion = fileversion = int.from_bytes(f.read(1),"big")
		else:
			f.seek(3, 1)
			
			
		if VersionDictionaryHact[fileversion] == "Dragon Engine":
			print("Please choose which Dragon Engine Game you are extracting from:")
			print("0 = Yakuza 6")
			print("1 = Yakuza Kiwami 2/ Judgement")
			print("2 = Yakuza 6 Blue Jacket Demo")
			DEGameText = input("Enter a Number: ")
			DEGame = int(DEGameText)
			if DEGame > 2:
				print("An incorrect option was entered. Please restart the program and try again.")
				input("Press ENTER to exit... ")
				sys.exit()
			if DEGame == 2: JacketMod = 1
			else: JacketMod = 0
			if fileversion == 6:
				print("An extracted talk_param is needed to extract this file.")
				talkparam = input("Please enter the name of the talk param file: ")
				talkparam = open(talkparam, 'rb')
				talkparamfile = json.load(talkparam)
			else:
				talkparamfile = []
			filesize = int.from_bytes(f.read(4),"little")
			f.seek(filesize)
			f.seek(-8, 1)
			HactSetTable = int.from_bytes(f.read(4),"little")
			f.seek(-12, 1)
			NumHactSets = int.from_bytes(f.read(4),"little")
			f.seek(HactSetTable)

			a = 0
			while a < NumHactSets:
				CommandSetDictionary["File Version"] = fileversion
				tempdict = dict([(value, key) for key, value in DEGameDictionary.items()])
				CommandSetDictionary["Dragon Engine Game"] = tempdict[DEGame]
				if fileversion == 5:
					setname = GetCommandSetName(f)
					FollowUpMoveIdx = []
					nextset = f.tell() + 8
					GoToPointer(f)
					f.seek(8, 1)
				elif fileversion == 6:
					FollowUpMoveIdx = []
					nextset = f.tell() + 8
					GoToPointer(f)
					setID = int.from_bytes(f.read(4),"little")
					setname = list(talkparamfile[str(setID)].keys())[0]
					subnumber = int.from_bytes(f.read(4),"little")
					if subnumber > 0:
						setname = setname + "#" + str(subnumber)
				HactTargetPointer = int.from_bytes(f.read(4),"little")
				f.seek(4,1)
				if DEGame == 0:
					HactType = GetStringFromPointer(f)
					f.seek(4, 1)
				elif DEGame == 1:
					HactType = int.from_bytes(f.read(4),"little")
				elif DEGame == 2:
					print("Feature Incomplete!")
					f.seek(4, 1)
				CommandSetID = int.from_bytes(f.read(4),"little")
				CommandSetIDDictionary[(setname)]= CommandSetID#
				if fileversion == 5: CommandSetDictionary[(setname)]["Hact ID"] = CommandSetID
				elif fileversion == 6: pass#CommandSetDictionary[(setname)]["Hact ID"] = setID
				CommandSetDictionary[(setname)]["Hact Type"] = HactType
				if fileversion == 5:
					UnkListing = GetStringFromPointer(f)
					f.seek(8, 1)
					NumTargets = int.from_bytes(f.read(4),"little")
				elif fileversion == 6: 
					UnkListing = int.from_bytes(f.read(4),"little")
					NumTargets = int.from_bytes(f.read(4),"little")
					f.seek(4, 1)
				UnkInt1 = int.from_bytes(f.read(4),"little")
				UnkInt2 = int.from_bytes(f.read(4),"little")
				UnkInt3 = int.from_bytes(f.read(4),"little")
				UnkInt4 = int.from_bytes(f.read(4),"little")
				UnkInt5 = int.from_bytes(f.read(4),"little")
				if fileversion == 5:
					HactBase = GetStringFromPointer(f)
					f.seek(4,1)
				elif fileversion == 6:
					HactBase = int.from_bytes(f.read(4),"little")
				CommandSetDictionary[(setname)]["Base Hact"] = HactBase
				CommandSetDictionary[(setname)]["Unknown String"] = UnkListing
				CommandSetDictionary[(setname)]["Unknown Int 1"] = UnkInt1
				CommandSetDictionary[(setname)]["Unknown Int 2"] = UnkInt2
				CommandSetDictionary[(setname)]["Unknown Int 3"] = UnkInt3
				CommandSetDictionary[(setname)]["Unknown Int 4"] = UnkInt4
				CommandSetDictionary[(setname)]["Unknown Int 5"] = UnkInt5
				f.seek(HactTargetPointer)
				
				c = 1
				while c < NumTargets + 1:
					nexttarget = f.tell() + 8
					GoToPointer(f)
					TargetName = GetStringFromPointer(f)
					f.seek(8, 1)
					targetproppointer = int.from_bytes(f.read(4),"little")
					f.seek(4, 1)
					targetproptype = int.from_bytes(f.read(4),"little")
					CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Target Name"] = TargetName
					CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Target Type"] = targetproptype
					f.seek(4,1)
					numfollowupprops = int.from_bytes(f.read(4),"little")
					f.seek(targetproppointer)
					d = 1
					while d < numfollowupprops + 1:
						nextproperty = f.tell() + 8
						PropertyDictionary = OrderedDict()
						GoToPointer(f)
						PropertyDictionary["propint1"] = int.from_bytes(f.read(4),"little")
						f.seek(-4, 1)
						PropertyDictionary["propint1ver17"] = int.from_bytes(f.read(3),"little")
						f.seek(-3, 1)
						PropertyDictionary["propbyte1"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte2"] = int.from_bytes(f.read(1),"little")
						f.seek(-2,1)
						PropertyDictionary["propshort1"] = int.from_bytes(f.read(2),"little")
						PropertyDictionary["propbyte3"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte4"] = int.from_bytes(f.read(1),"little")
						f.seek(-2,1)
						PropertyDictionary["propshort2"] = int.from_bytes(f.read(2),"little")
						PropertyDictionary["propbyteex1"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyteex2"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyteex3"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyteex4"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propint2"] = int.from_bytes(f.read(4),"little")
						f.seek(-4, 1)
						PropertyDictionary["propbyte5"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte6"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte7"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte8"] = int.from_bytes(f.read(1),"little")
						
						if args.simplenames: typedes = ""
						else: 
							if PropertyDictionary["propint2"] in PropertyTypeDictDE:
								typedes = "| Type " + str(PropertyDictionary["propint2"]) + " = " + PropertyTypeDictDE[PropertyDictionary["propint2"]]
							else: typedes = ""			
						propertyExtraction(f, True, d, CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Target Properties"], PropertyDictionary, VersionDictionaryHact[fileversion], fileversion, typedes, OrderedDict(), ButtonPressListDE, talkparamfile)
						f.seek(nextproperty)
						d = d + 1
					c = c + 1
					f.seek(nexttarget)

				f.seek(nextset)
				
				with open(mypath + "\\" + str(setname) + ".json", 'w') as outfile:
					json.dump(CommandSetDictionary, outfile, indent=2, ensure_ascii=False)
				CommandSetDictionary.clear()
				a = a + 1
				
				CommandSetOrderIDxDictionary[CommandSetOrderIDx] = setname
				CommandSetOrderIDx = CommandSetOrderIDx + 1
				
			with open("Hact List (Reference Only).json", 'w') as outfile:
				json.dump(CommandSetIDDictionary, outfile, indent=1, ensure_ascii=False)
				
			with open("Hact Order List.json", 'w') as outfile:
				json.dump(CommandSetOrderIDxDictionary, outfile, indent=1, ensure_ascii=False)
			f.close
			
		if VersionDictionaryHact[fileversion] == "Old Engine":
			print("Please choose which Old Engine Game you are extracting from:")
			print("0 = Yakuza 0/Kiwami 1")
			print("1 = Yakuza 5")
			print("2 = Yakuza Ishin")
			OEGameText = input("Enter a Number: ")
			OEGame = int(OEGameText)
			if OEGame > 2:
				print("An incorrect option was entered. Please restart the program and try again.")
				input("Press ENTER to exit... ")
				sys.exit()
			filesize = int.from_bytes(f.read(4),"big")
			f.seek(filesize)
			f.seek(-8, 1)
			NumHactSets = int.from_bytes(f.read(4),"big")
			HactSetTable = int.from_bytes(f.read(4),"big")
			f.seek(HactSetTable)

			a = 0
			while a < NumHactSets:
				CommandSetDictionary["File Version"] = fileversion
				tempdict = dict([(value, key) for key, value in OEGameDictionary.items()])
				CommandSetDictionary["Old Engine Game"] = tempdict[OEGame]
				setname = GetCommandSetName(f, "big")
				print(setname)
				FollowUpMoveIdx = []
				nextset = f.tell() + 4
				GoToPointer(f, 0, "big")
				f.seek(4, 1)
				NumTargets = int.from_bytes(f.read(4),"big")
				HactTargetPointer = int.from_bytes(f.read(4),"big")
				unktargetval = int.from_bytes(f.read(4),"big")
				CompletionName = GetStringFromPointer(f, 0, "big")
				f.seek(4, 1)
				UnkInt0 = int.from_bytes(f.read(4),"big")
				UnkInt1 = int.from_bytes(f.read(4),"big")
				UnkInt2 = int.from_bytes(f.read(4),"big")
				if OEGame != 1:
					ConditionName = GetStringFromPointer(f, 0, "big")
					f.seek(4, 1)
					UnkInt3 = int.from_bytes(f.read(4),"big")
					UnkInt4 = int.from_bytes(f.read(4),"big")
					UnkInt5 = int.from_bytes(f.read(4),"big")
				
				CommandSetDictionary[(setname)]["Unknown Target Value"] = unktargetval
				CommandSetDictionary[(setname)]["Completion Name"] = CompletionName
				CommandSetDictionary[(setname)]["Unknown Int 0"] = UnkInt0
				CommandSetDictionary[(setname)]["Unknown Int 1"] = UnkInt1
				CommandSetDictionary[(setname)]["Unknown Int 2"] = UnkInt2
				if OEGame != 1:
					CommandSetDictionary[(setname)]["Condition Name"] = ConditionName
					CommandSetDictionary[(setname)]["Unknown Int 3"] = UnkInt3
					CommandSetDictionary[(setname)]["Unknown Int 4"] = UnkInt4
					CommandSetDictionary[(setname)]["Unknown Int 5"] = UnkInt5
				f.seek(HactTargetPointer)
				
				c = 1
				while c < NumTargets + 1:
					nexttarget = f.tell() + 4
					GoToPointer(f, 0, "big")
					TargetName = GetStringFromPointer(f, 0, "big")
					f.seek(4, 1)
					targetproptype = int.from_bytes(f.read(4),"big")
					UnkTargetName = GetStringFromPointer(f, 0, "big")
					f.seek(4, 1)
					numfollowupprops = int.from_bytes(f.read(4),"big")
					targetproppointer = int.from_bytes(f.read(4),"big")
					UnkTargetInteger = int.from_bytes(f.read(4),"big")
					
					CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Target Name"] = TargetName
					CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Target Type"] = targetproptype
					CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Unk Target Name"] = UnkTargetName
					CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Unk Target Integer"] = UnkTargetInteger
					
					
					f.seek(targetproppointer)
					d = 1
					while d < numfollowupprops + 1:
						nextproperty = f.tell() + 4
						PropertyDictionary = OrderedDict()
						GoToPointer(f, 0, "big")
						PropertyDictionary["propint2"] = int.from_bytes(f.read(4),"big")
						f.seek(-4, 1)
						PropertyDictionary["propbyte8"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte7"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte6"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte5"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propint1"] = int.from_bytes(f.read(4),"big")
						f.seek(-4, 1)
						PropertyDictionary["propbyte4"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte3"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte2"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte1"] = int.from_bytes(f.read(1),"big")
						f.seek(-4,1)
						PropertyDictionary["propshort2"] = int.from_bytes(f.read(2),"big")
						PropertyDictionary["propshort1"] = int.from_bytes(f.read(2),"big")
						
						if args.simplenames: typedes = ""
						else: 
							if PropertyDictionary["propint2"] in PropertyTypeDictOE:
								typedes = "| Type " + str(PropertyDictionary["propint2"]) + " = " + PropertyTypeDictOE[PropertyDictionary["propint2"]]
							else: typedes = ""			
						propertyExtraction(f, True, d, CommandSetDictionary[(setname)]["Target Table"]["Target " + str(c)]["Target Properties"], PropertyDictionary, VersionDictionaryHact[fileversion], fileversion, typedes, OrderedDict(), ButtonPressListOE, [])
						f.seek(nextproperty)
						d = d + 1
					c = c + 1
					f.seek(nexttarget)

				f.seek(nextset)
				
				with open(mypath + "\\" + str(setname) + ".json", 'w', encoding = 'shift-jis') as outfile:
					json.dump(CommandSetDictionary, outfile, indent=2, ensure_ascii=False)
				CommandSetDictionary.clear()
				a = a + 1
				
				CommandSetOrderIDxDictionary[CommandSetOrderIDx] = setname
				CommandSetOrderIDx = CommandSetOrderIDx + 1
				
			with open("Hact Order List.json", 'w') as outfile:
				json.dump(CommandSetOrderIDxDictionary, outfile, indent=1, ensure_ascii=False)
			f.close
			
	if extension == ".json":
		with open(kfile, 'r', encoding='shift-jis') as file:
			jsonfile = json.load(file)
			if "Old Engine Game" in jsonfile: commandsetname = list(jsonfile.keys())[2] 
			else: commandsetname = list(jsonfile.keys())[2]
			x = 0
			MoveIDXDict = OrderedDict()
			for move in list(jsonfile[commandsetname]["Move Table"].keys()):
				MoveIDXDict[x] = move
				x = x + 1
			with open(nameonly + " Move Order ID List.json", 'w') as outfile:
				json.dump(MoveIDXDict, outfile, indent=1, ensure_ascii=False)			
			
	
	if extension == ".cfc":
		byte1 = int.from_bytes(f.read(4),"big")
		if byte1 != 1128678217:
			print("Fileheader not equal to CFCI. Not a valid CFC file?")
			input("Press ENTER to exit... ")
			sys.exit()			
		patchedFile = "" #Init patched file

		curdir =  os.getcwd()
		mypath = curdir + "\\Fighter Command"
		if not os.path.isdir(mypath):
		   os.makedirs(mypath)
			
			
		f.seek(4, 1)#skips endianess
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
			print("2 = Yakuza Ishin")
			OEGameText = input("Enter a Number: ")
			OEGame = int(OEGameText)
			if OEGame > 2:
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
				elif OEGame == 2:
					CommandSetDictionary["Old Engine Game"] = "Yakuza Ishin"
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
					if OEGame == 0 or OEGame == 2:
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
					if OEGame == 0 or OEGame == 2:
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
						elif OEGame == 1 or OEGame == 2:
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
						CommandSetDictionary[(setname)]["Move Table"][movename]["Move IDx to Play in Moveset"] = animshort2
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
							PropertyDictionary = OrderedDict()
							GoToPointer(f, 0, "big")
							PropertyDictionary["propint2"] = int.from_bytes(f.read(4),"big")
							f.seek(-4, 1)
							PropertyDictionary["propbyte8"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propbyte7"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propbyte6"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propbyte5"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propint1"] = int.from_bytes(f.read(4),"big")
							f.seek(-4, 1)
							PropertyDictionary["propbyte4"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propbyte3"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propbyte2"] = int.from_bytes(f.read(1),"big")
							PropertyDictionary["propbyte1"] = int.from_bytes(f.read(1),"big")
							f.seek(-4,1)
							PropertyDictionary["propshort2"] = int.from_bytes(f.read(2),"big")
							PropertyDictionary["propshort1"] = int.from_bytes(f.read(2),"big")
							if args.simplenames: typedes = ""
							else: 
								if PropertyDictionary["propint2"] in PropertyTypeDictOE:
									typedes = "| Type " + str(PropertyDictionary["propint2"]) + " = " + PropertyTypeDictOE[PropertyDictionary["propint2"]]
								else: typedes = ""
								
							propertyExtraction(f, True, d, CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"], PropertyDictionary, VersionDictionary[fileversion], fileversion, typedes, OrderedDict(), ButtonPressListOE)
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
						PropertyDictionary = OrderedDict()
						GoToPointer(f, 0, "big")
						PropertyDictionary["propint2"] = int.from_bytes(f.read(4),"big")
						f.seek(-4, 1)
						PropertyDictionary["propbyte8"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte7"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte6"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte5"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propint1"] = int.from_bytes(f.read(4),"big")
						f.seek(-4, 1)
						PropertyDictionary["propbyte4"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte3"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte2"] = int.from_bytes(f.read(1),"big")
						PropertyDictionary["propbyte1"] = int.from_bytes(f.read(1),"big")
						f.seek(-4,1)
						PropertyDictionary["propshort2"] = int.from_bytes(f.read(2),"big")
						PropertyDictionary["propshort1"] = int.from_bytes(f.read(2),"big")
						if args.simplenames: typedes = ""
						else: 
							if PropertyDictionary["propint2"] in PropertyTypeDictOE:
								typedes = "| Type " + str(PropertyDictionary["propint2"]) + " = " + PropertyTypeDictOE[PropertyDictionary["propint2"]]
							else: typedes = ""
							

						propertyExtraction(f, True, c, CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"], PropertyDictionary, VersionDictionary[fileversion], fileversion, typedes, OrderedDict, ButtonPressListOE)
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
			print("Please choose which Dragon Engine Game you are extracting from:")
			print("0 = Yakuza 6")
			print("1 = Yakuza Kiwami 2/ Judgement")
			print("2 = Yakuza 6 Blue Jacket Demo")
			DEGameText = input("Enter a Number: ")
			DEGame = int(DEGameText)
			if DEGame > 2:
				print("An incorrect option was entered. Please restart the program and try again.")
				input("Press ENTER to exit... ")
				sys.exit()
			if DEGame == 2: JacketMod = 1
			else: JacketMod = 0
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
				tempdict = dict([(value, key) for key, value in DEGameDictionary.items()])
				CommandSetDictionary["Dragon Engine Game"] = tempdict[DEGame]
				setname = GetCommandSetName(f)
				#print(setname)
				FollowUpMoveIdx = []
				nextset = f.tell() + 8
				GoToPointer(f)
				f.seek(8, 1)
				#DEGameDictionary = {"Yakuza 6": 0, "Yakuza Kiwami 2 / Judgement": 1, "Yakuza 6 Blue Jacket Demo": 2,}
				if DEGame == 1:
					CommandSetID = int.from_bytes(f.read(4),"little")
					CommandSetIDDictionary[(setname)]= CommandSetID#
					CommandSetDictionary[(setname)]["Command Set ID"] = CommandSetID
				else: f.seek(4, 1)
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
					#print(movename)
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
					f.seek(-4,1)
					animshort3 = int.from_bytes(f.read(2),"little")
					animshort4 = int.from_bytes(f.read(2),"little")
					FollowUpsPointer = int.from_bytes(f.read(4),"little")
					f.seek(4, 1)
					AdditionalPropsPointer = int.from_bytes(f.read(4),"little")
					f.seek(4, 1)
					NumFollowUps = int.from_bytes(f.read(1),"little")
					NumAdditionalProps = int.from_bytes(f.read(1),"little")
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
					elif movetype == 4 - JacketMod:
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 1"] = animbyte1
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 2"] = animbyte2
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 3"] = animbyte3
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 4"] = animbyte4
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 5"] = animbyte5
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 6"] = animbyte6
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 7"] = animbyte7
						CommandSetDictionary[(setname)]["Move Table"][movename]["Animation Related Byte 8"] = animbyte8
					elif movetype == 3 - JacketMod:
						CommandSetDictionary[(setname)]["Move Table"][movename]["Moveset IDx"] = animshort2
						CommandSetDictionary[(setname)]["Move Table"][movename]["Move IDx to Play in Moveset"] = animshort1
						CommandSetDictionary[(setname)]["Move Table"][movename]["Command Set ID"] = animshort3
					elif movetype == 17 - JacketMod:
						CommandSetDictionary[(setname)]["Move Table"][movename]["Unk Value"] = AnimPointer
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
							PropertyDictionary = OrderedDict()
							GoToPointer(f)
							PropertyDictionary["propint1"] = int.from_bytes(f.read(4),"little")
							f.seek(-4, 1)
							PropertyDictionary["propint1ver17"] = int.from_bytes(f.read(3),"little")
							f.seek(-3, 1)
							PropertyDictionary["propbyte1"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyte2"] = int.from_bytes(f.read(1),"little")
							f.seek(-2,1)
							PropertyDictionary["propshort1"] = int.from_bytes(f.read(2),"little")
							PropertyDictionary["propbyte3"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyte4"] = int.from_bytes(f.read(1),"little")
							f.seek(-2,1)
							PropertyDictionary["propshort2"] = int.from_bytes(f.read(2),"little")
							PropertyDictionary["propbyteex1"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyteex2"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyteex3"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyteex4"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propint2"] = int.from_bytes(f.read(4),"little")
							f.seek(-4, 1)
							PropertyDictionary["propbyte5"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyte6"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyte7"] = int.from_bytes(f.read(1),"little")
							PropertyDictionary["propbyte8"] = int.from_bytes(f.read(1),"little")
							f.seek(-4, 1)
							PropertyDictionary["propshort3"] = int.from_bytes(f.read(2),"little")
							PropertyDictionary["propshort4"] = int.from_bytes(f.read(2),"little")
							if args.simplenames: typedes = ""
							else: 
								if PropertyDictionary["propint2"] in PropertyTypeDictDE:
									typedes = "| Type " + str(PropertyDictionary["propint2"]) + " = " + PropertyTypeDictDE[PropertyDictionary["propint2"]]
								else: typedes = ""
							
							propertyExtraction(f, True, d, CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"], PropertyDictionary, VersionDictionary[fileversion], fileversion, typedes, OrderedDict())
							f.seek(nextproperty)
							d = d + 1
						c = c + 1
						f.seek(nextfollowup)
					
			#Additional Move Properties-------------------------------------------------------------------------------
					f.seek(AdditionalPropsPointer)
					c = 1
					while c < NumAdditionalProps + 1:
						nextadditionalprop = f.tell() + 8
						GoToPointer(f, 0, "little")
						movepropshort1 = int.from_bytes(f.read(2),"little")
						movepropshort2 = int.from_bytes(f.read(2),"little")
						CommandSetDictionary[(setname)]["Move Table"][movename]["Additional Properties Table"]["Additional Property " + str(c)]["Unk Short 1"] = movepropshort1
						CommandSetDictionary[(setname)]["Move Table"][movename]["Additional Properties Table"]["Additional Property " + str(c)]["Unk Short 2"] = movepropshort2
						c = c + 1
						f.seek(nextadditionalprop)		
			#Additional Move Properties-------------------------------------------------------------------------------
					
			#Follow Up Tables-----------------------------------------------------------------------------------------
					f.seek(nextmove)
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
					NumFollowUps = int.from_bytes(f.read(1),"little")
					FollowUpRelatedByte = int.from_bytes(f.read(1),"little")
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
					if DEGame == 0 or DEGame == 2:
						f.seek(8, 1)
						wepcommandset = GetStringFromPointer(f)
						f.seek(-8, 1)
					GoToPointer(f)
					numwepproperties = int.from_bytes(f.read(2),"little")
					if DEGame == 1: wepcommandset = int.from_bytes(f.read(2),"little")
					else: f.seek(2, 1)
					f.seek(4, 1)
					WepPropertiesPointer = int.from_bytes(f.read(4),"little")
					f.seek(WepPropertiesPointer)
					if DEGame == 1: CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Command Set ID for Weapon Moveset"] = wepcommandset
					elif DEGame == 0 or DEGame == 2: CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Command Set Name for Weapon Moveset"] = wepcommandset
					c = 1
					while c < numwepproperties + 1:
						nextweppos = f.tell() + 8
						PropertyDictionary = OrderedDict()
						GoToPointer(f)
						PropertyDictionary["propbyte1"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte2"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte3"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte4"] = int.from_bytes(f.read(1),"little")
						f.seek(-4,1)
						PropertyDictionary["propshort1"] = int.from_bytes(f.read(2),"little")
						PropertyDictionary["propshort2"] = int.from_bytes(f.read(2),"little")
						f.seek(-4,1)
						PropertyDictionary["propint1"] = int.from_bytes(f.read(4),"little")
						f.seek(4, 1)
						PropertyDictionary["propshort3"] = int.from_bytes(f.read(2),"little")
						PropertyDictionary["propshort4"] = int.from_bytes(f.read(2),"little")
						f.seek(-4,1)
						PropertyDictionary["propint2"] = int.from_bytes(f.read(4),"little")
						f.seek(-4,1)
						PropertyDictionary["propbyte5"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte6"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte7"] = int.from_bytes(f.read(1),"little")
						PropertyDictionary["propbyte8"] = int.from_bytes(f.read(1),"little")
						if args.simplenames: typedes = ""
						else: 
							if PropertyDictionary["propint2"] in PropertyTypeDictDE:
								typedes = "| Type " + str(PropertyDictionary["propint2"]) + " = " + PropertyTypeDictDE[PropertyDictionary["propint2"]]
							else: typedes = ""
							
						
						propertyExtraction(f, True, c, CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"], PropertyDictionary, VersionDictionary[fileversion], fileversion, typedes, OrderedDict, ButtonPressListDE)
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
			if DEGame == 1:
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
	for f in os.listdir(kfile):#Gets file version
		curfile = workdir + "\\" + f
		with open(curfile, 'r', encoding='shift-jis') as file:
			jsonfile = json.load(file)
			fileversion = jsonfile["File Version"]
			tempkey = list(jsonfile.keys())[2]
			if "Hact ID" in jsonfile[tempkey] or "Completion Name" in jsonfile[tempkey] or "Condition Name" in jsonfile[tempkey]:
				filetype = "CHP"
				if "Old Engine Game" in jsonfile: enginegame = jsonfile["Old Engine Game"]
				elif "Dragon Engine Game" in jsonfile: enginegame = jsonfile["Dragon Engine Game"]
			elif "Old Engine Game" in jsonfile:
				filetype = "CFC"
				enginegame = jsonfile["Old Engine Game"]
			elif "Dragon Engine Game" in jsonfile:
				filetype = "CFC"
				enginegame = jsonfile["Dragon Engine Game"]
			else:
				filetype = "CFC"
				enginegame = 0
	
	if filetype == "CHP":
		newfile = open("hact new.chp", 'w+b')
		if VersionDictionaryHact[fileversion] == "Dragon Engine":
			DEGame = DEGameDictionary[enginegame]
			newfile.write(b'\x43\x48\x50\x49\x21\x00\x00\x00')#Writes fileheader
			newfile.write(int_to_bytes(fileversion, 4))
			newfile.write(b'\x00\x00\x00\x00')#Writes filler for filesize
			numcommandsets = len(os.listdir(kfile))
			orderfile = open("Hact Order List.json", 'rb')
			CommandSetOrderDictionary = json.load(orderfile)
			CommandSetOrderIDx = 0
			while CommandSetOrderIDx < numcommandsets:#Loops through all Json files and collects string data
				curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
				with open(curfile, 'r', encoding='utf8') as file:
					jsonfile = json.load(file)
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					stringlistEntryAdd(commandsetname, stringlist)

					commandsetID = jsonfile[commandsetname]["Hact ID"]
					if DEGame == 0:
						hacttype = jsonfile[commandsetname]["Hact Type"]
						stringlistEntryAdd(hacttype, stringlist)
						
					commandsetnamebase = jsonfile[commandsetname]["Base Hact"]
					stringlistEntryAdd(commandsetnamebase, stringlist)
					
					unknownstring = jsonfile[commandsetname]["Unknown String"]
					stringlistEntryAdd(unknownstring, stringlist)
					
					if "Target Table" in jsonfile[commandsetname]:
						for target in list(jsonfile[commandsetname]["Target Table"].keys()):
							targetname = jsonfile[commandsetname]["Target Table"][target]["Target Name"]
							stringlistEntryAdd(targetname, stringlist)
							if "Target Properties" in jsonfile[commandsetname]["Target Table"][target]:
								for property in list(jsonfile[commandsetname]["Target Table"][target]["Target Properties"].keys()):
									propertytype = jsonfile[commandsetname]["Target Table"][target]["Target Properties"][property]["Property Type"]
									if propertytype in [31,48]:
										string = list(jsonfile[commandsetname]["Target Table"][target]["Target Properties"][property].keys())[1]
										stringlistEntryAdd(string, stringlist)
					CommandSetOrderIDx = CommandSetOrderIDx + 1
			stringlist = list( dict.fromkeys(stringlist) )
			
			#Writes string list to file collecting the string location and string in a dictionary.
			x = 0
			while x < len(stringlist):
				currentpos = newfile.tell()
				currentstring = stringlist[x]
				if currentstring == b'\x00':
					newfile.write(b'\x00')
				else:
					newfile.write(currentstring.encode('utf-8'))
					newfile.write(b'\x00')
				stringpointerdict[currentstring] = currentpos
				x = x + 1
			aligntext(newfile)#Adds the CC Byte enders to the end of the string table.
			
			#Parsing data from the jsons into hact begins here.
			CommandSetPointerList = []
			numcommandsets = len(os.listdir(kfile))
			orderfile = open("Hact Order List.json", 'rb')
			CommandSetOrderDictionary = json.load(orderfile)
			CommandSetOrderIDx = 0
			print("Beginning string extraction...")
			print("")
			while CommandSetOrderIDx < numcommandsets:
				curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
				print(CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json")
				with open(curfile, 'r', encoding='utf8') as file:
					jsonfile = json.load(file)
					hactdata = []
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					hacttype = jsonfile[commandsetname]["Hact Type"]
					if DEGame == 0:
						if hacttype == "Null":
							hacttype = b'\x00'
					commandsetID = jsonfile[commandsetname]["Hact ID"]
					commandsetnamebase = jsonfile[commandsetname]["Base Hact"]
					hactunkint1 = unknownstring = jsonfile[commandsetname]["Unknown String"]
					if hactunkint1 == "Null":
						hactunkint1 = b'\x00'					
					hactunkint2 = jsonfile[commandsetname]["Unknown Int 1"]
					hactunkint3 = jsonfile[commandsetname]["Unknown Int 2"]
					hactunkint4 = jsonfile[commandsetname]["Unknown Int 3"]
					hactunkint5 = jsonfile[commandsetname]["Unknown Int 4"]
					hactunkint6 = jsonfile[commandsetname]["Unknown Int 5"]
					hactdata.append([commandsetname, hacttype, commandsetID,commandsetnamebase,hactunkint1,hactunkint2,hactunkint3,hactunkint4,hactunkint5, hactunkint6])
					TargetPointers = []
					if "Target Table" in jsonfile[commandsetname]:
						numtargets = len(jsonfile[commandsetname]["Target Table"])
					else:
						numtargets = 0
					
					if "Target Table" in jsonfile[commandsetname]:
						for target in list(jsonfile[commandsetname]["Target Table"].keys()):
							TargetValues = []
							TargetPropValues = []
							TargetValuePointers = []
							targetname = jsonfile[commandsetname]["Target Table"][target]["Target Name"]
							targettype = jsonfile[commandsetname]["Target Table"][target]["Target Type"]
							if "Target Properties" in jsonfile[commandsetname]["Target Table"][target]:
								numtargetprops = len(jsonfile[commandsetname]["Target Table"][target]["Target Properties"])
							else: numtargetprops = 0
							TargetValues.append([targetname, targettype])
							if "Target Properties" in jsonfile[commandsetname]["Target Table"][target]:
								for property in list(jsonfile[commandsetname]["Target Table"][target]["Target Properties"].keys()):
									temparray2 = []
									temparray2.append(propertyExtraction(f, False, 0, [], [], VersionDictionaryHact[fileversion], fileversion, "", jsonfile[commandsetname]["Target Table"][target]["Target Properties"][property], ButtonPressListDE))
									TargetPropValues.append(temparray2)
								
							x = 0
							TargetPropValuePointers = []
							while x < numtargetprops:
								y = 0
								while y < len(TargetPropValues[x]):
									currentpos = newfile.tell()
									TargetPropValuePointers.append(currentpos)
									writePropertiestoFile(newfile, TargetPropValues[x][y], VersionDictionaryHact[fileversion], fileversion, stringpointerdict)
									y = y + 1
								#Writes Move Target Property List to File
								x = x + 1
							TargetPropertyListPointer = newfile.tell()
							y = 0
							while y < len(TargetPropValuePointers):
								newfile.write(int_to_bytes(TargetPropValuePointers[y], 4))
								newfile.write(b'\x00\x00\x00\x00')
								y = y + 1
							TargetPointers.append(newfile.tell())
							newfile.write(int_to_bytes(stringpointerdict[TargetValues[0][0]], 4))
							newfile.write(b'\x00\x00\x00\x00')
							newfile.write(int_to_bytes(TargetPropertyListPointer, 4))
							newfile.write(b'\x00\x00\x00\x00')
							newfile.write(int_to_bytes(TargetValues[0][1], 4))
							newfile.write(b'\x00\x00\x00\x00')
							newfile.write(int_to_bytes(len(TargetPropValuePointers), 4))
							newfile.write(b'\x00\x00\x00\x00')
						x = 0
						TargetTablePointer = newfile.tell()
						while x < numtargets:
							newfile.write(int_to_bytes(TargetPointers[x], 4))
							newfile.write(b'\x00\x00\x00\x00')
							x = x + 1
					else:
						TargetTablePointer = newfile.tell()
						numtargetprops = 0
					CommandSetPointerList.append(newfile.tell())
					#commandsetname,hacttype, commandsetID,commandsetnamebase,hactunkint1,hactunkint2,hactunkint3,hactunkint4,hactunkint5,hactunkint6
					newfile.write(int_to_bytes(stringpointerdict[hactdata[0][0]], 4))
					newfile.write(b'\x00\x00\x00\x00')
					newfile.write(int_to_bytes(TargetTablePointer, 4))
					newfile.write(b'\x00\x00\x00\x00')
					if DEGame == 0:
						newfile.write(int_to_bytes(stringpointerdict[hactdata[0][1]], 4))
					elif DEGame == 1:
						newfile.write(int_to_bytes(hactdata[0][1], 4))
					newfile.write(int_to_bytes(hactdata[0][2], 4))
					newfile.write(int_to_bytes(stringpointerdict[hactdata[0][4]], 4))
					newfile.write(b'\x00\x00\x00\x00')
					newfile.write(int_to_bytes(numtargets, 4))
					newfile.write(int_to_bytes(hactdata[0][5], 4))
					newfile.write(int_to_bytes(hactdata[0][6], 4))
					newfile.write(int_to_bytes(hactdata[0][7], 4))
					newfile.write(int_to_bytes(hactdata[0][8], 4))
					newfile.write(int_to_bytes(hactdata[0][9], 4))
					newfile.write(int_to_bytes(stringpointerdict[hactdata[0][3]], 4))
					newfile.write(b'\x00\x00\x00\x00')
					CommandSetOrderIDx = CommandSetOrderIDx + 1
			x = 0
			CommandSetsListPointer = newfile.tell()
			while x < len(CommandSetPointerList):
				newfile.write(int_to_bytes(CommandSetPointerList[x], 4))
				newfile.write(b'\x00\x00\x00\x00')
				x = x + 1
			newfile.write(int_to_bytes(len(CommandSetPointerList), 4))
			newfile.write(b'\x00\x00\x00\x00')
			newfile.write(int_to_bytes(CommandSetsListPointer, 4))
			newfile.write(b'\x00\x00\x00\x00')
			filesize = newfile.tell()
			newfile.close
			newfile = open("hact new.chp", 'rb+')
			newfile.seek(12)
			newfile.write(int_to_bytes(filesize, 4))
			file.close
			newfile.close
			
			
		if VersionDictionaryHact[fileversion] == "Old Engine":
			OEGame = OEGameDictionary[enginegame]
			newfile.write(b'\x43\x48\x50\x49\x02\x01\x00\x00')#Writes fileheader
			newfile.write(int_to_bytes(fileversion, 4, "big"))
			newfile.write(b'\x00\x00\x00\x00')#Writes filler for filesize
			numcommandsets = len(os.listdir(kfile))
			orderfile = open("Hact Order List.json", 'rb')
			CommandSetOrderDictionary = json.load(orderfile)
			CommandSetOrderIDx = 0
			while CommandSetOrderIDx < numcommandsets:#Loops through all Json files and collects string data
				curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
				with open(curfile, 'r', encoding='shift-jis') as file:
					jsonfile = json.load(file)
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					stringlistEntryAdd(commandsetname, stringlist)
					
					completionname = jsonfile[commandsetname]["Completion Name"]
					stringlistEntryAdd(completionname, stringlist)
					
					if OEGame != 1:
						conditionname = jsonfile[commandsetname]["Condition Name"]
						stringlistEntryAdd(conditionname, stringlist)
					
					if "Target Table" in jsonfile[commandsetname]:
						for target in list(jsonfile[commandsetname]["Target Table"].keys()):
							targetname = jsonfile[commandsetname]["Target Table"][target]["Target Name"]
							stringlistEntryAdd(targetname, stringlist)
							
							unktargetname = jsonfile[commandsetname]["Target Table"][target]["Unk Target Name"]
							stringlistEntryAdd(unktargetname, stringlist)
							
							if "Target Properties" in jsonfile[commandsetname]["Target Table"][target]:
								for property in list(jsonfile[commandsetname]["Target Table"][target]["Target Properties"].keys()):
									propertytype = jsonfile[commandsetname]["Target Table"][target]["Target Properties"][property]["Property Type"]
									if propertytype in [16,22,23,30,36,47]:
										string = list(jsonfile[commandsetname]["Target Table"][target]["Target Properties"][property].values())[1]
										stringlistEntryAdd(string, stringlist)
					CommandSetOrderIDx = CommandSetOrderIDx + 1
			stringlist = list( dict.fromkeys(stringlist) )
			x = 0
			
			#Writes string list to file collecting the string location and string in a dictionary.
			while x < len(stringlist):
				currentpos = newfile.tell()
				currentstring = stringlist[x]
				if currentstring == b'\x00':#Checks if null
					newfile.write(b'\x00')
				else:
					newfile.write(currentstring.encode('shift-jis'))
					newfile.write(b'\x00')
				stringpointerdict[currentstring] = currentpos
				x = x + 1
			if OEGame == 1: 
				alignbyte = b'\x00'
			else: alignbyte = b'\xCC'
			aligntext(newfile, alignbyte)#Adds the CC Byte enders to the end of the string table.
			if b'\x00' in stringpointerdict: stringpointerdict["Null"] = stringpointerdict[b'\x00']
			
			#Parsing data from the jsons into hact begins here.
			CommandSetPointerList = []
			numcommandsets = len(os.listdir(kfile))
			orderfile = open("Hact Order List.json", 'rb')
			CommandSetOrderDictionary = json.load(orderfile)
			CommandSetOrderIDx = 0
			print("Beginning string extraction...")
			print("")
			while CommandSetOrderIDx < numcommandsets:
				curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
				print(CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json")
				with open(curfile, 'r', encoding='shift-jis') as file:
					jsonfile = json.load(file)
					hactdata = []
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					hactunktgt = jsonfile[commandsetname]["Unknown Target Value"]
					completionname = jsonfile[commandsetname]["Completion Name"]
					if completionname == "Null":
						completionname = b'\x00'
					hactunkint0 = jsonfile[commandsetname]["Unknown Int 0"]
					hactunkint1 = jsonfile[commandsetname]["Unknown Int 1"]
					hactunkint2 = jsonfile[commandsetname]["Unknown Int 2"]
					if OEGame != 1:
						conditionname = jsonfile[commandsetname]["Condition Name"]
						if conditionname == "Null":
							conditionname = b'\x00'
						hactunkint3 = jsonfile[commandsetname]["Unknown Int 3"]
						hactunkint4 = jsonfile[commandsetname]["Unknown Int 4"]
						hactunkint5 = jsonfile[commandsetname]["Unknown Int 5"]
						hactdata.append([commandsetname, hactunktgt, completionname,hactunkint0,hactunkint1,hactunkint2,conditionname,hactunkint3,hactunkint4,hactunkint5])
					else: hactdata.append([commandsetname, hactunktgt, completionname,hactunkint0,hactunkint1,hactunkint2])
					TargetPointers = []
					if "Target Table" in jsonfile[commandsetname]:
						numtargets = len(jsonfile[commandsetname]["Target Table"])
					else:
						numtargets = 0
					
					if "Target Table" in jsonfile[commandsetname]:
						for target in list(jsonfile[commandsetname]["Target Table"].keys()):
							TargetValues = []
							TargetPropValues = []
							TargetValuePointers = []
							targetname = jsonfile[commandsetname]["Target Table"][target]["Target Name"]
							targettype = jsonfile[commandsetname]["Target Table"][target]["Target Type"]
							unktargetname = jsonfile[commandsetname]["Target Table"][target]["Unk Target Name"]
							unktargetinteger = jsonfile[commandsetname]["Target Table"][target]["Unk Target Integer"]
							if targetname == "Null":
								targetname = b'\x00'
							if unktargetname == "Null":
								unktargetname = b'\x00'
							if "Target Properties" in jsonfile[commandsetname]["Target Table"][target]:
								numtargetprops = len(jsonfile[commandsetname]["Target Table"][target]["Target Properties"])
							else: numtargetprops = 0
							TargetValues.append([targetname, targettype, unktargetname, unktargetinteger])
							if "Target Properties" in jsonfile[commandsetname]["Target Table"][target]:
								for property in list(jsonfile[commandsetname]["Target Table"][target]["Target Properties"].keys()):
									temparray2 = []
									temparray2.append(propertyExtraction(f, False, 0, [], [], VersionDictionaryHact[fileversion], fileversion, "", jsonfile[commandsetname]["Target Table"][target]["Target Properties"][property], ButtonPressListOE))
									TargetPropValues.append(temparray2)
								
							x = 0
							TargetPropValuePointers = []
							while x < numtargetprops:
								y = 0
								while y < len(TargetPropValues[x]):
									currentpos = newfile.tell()
									TargetPropValuePointers.append(currentpos)
									writePropertiestoFile(newfile, TargetPropValues[x][y], VersionDictionaryHact[fileversion], fileversion, stringpointerdict)
									y = y + 1
								#Writes Move Target Property List to File
								x = x + 1
							TargetPropertyListPointer = newfile.tell()
							y = 0
							while y < len(TargetPropValuePointers):
								newfile.write(int_to_bytes(TargetPropValuePointers[y], 4, "big"))
								y = y + 1
							TargetPointers.append(newfile.tell())
					
							newfile.write(int_to_bytes(stringpointerdict[TargetValues[0][0]], 4, "big"))
							newfile.write(int_to_bytes(TargetValues[0][1], 4, "big"))
							newfile.write(int_to_bytes(stringpointerdict[TargetValues[0][2]], 4, "big"))
							newfile.write(int_to_bytes(len(TargetPropValuePointers), 4, "big"))
							newfile.write(int_to_bytes(TargetPropertyListPointer, 4, "big"))
							newfile.write(int_to_bytes(TargetValues[0][3], 4, "big"))
						x = 0
						TargetTablePointer = newfile.tell()
						while x < numtargets:
							newfile.write(int_to_bytes(TargetPointers[x], 4, "big"))
							x = x + 1
					else:
						TargetTablePointer = newfile.tell()
						numtargetprops = 0
					CommandSetPointerList.append(newfile.tell())
					#commandsetname, hactunktgt, completionname,hactunkint0,hactunkint1,hactunkint2,conditionname,hactunkint3,hactunkint4,hactunkint5
					newfile.write(int_to_bytes(stringpointerdict[hactdata[0][0]], 4, "big"))
					newfile.write(int_to_bytes(numtargets, 4, "big"))
					newfile.write(int_to_bytes(TargetTablePointer, 4, "big"))
					newfile.write(int_to_bytes(hactdata[0][1], 4, "big"))
					newfile.write(int_to_bytes(stringpointerdict[hactdata[0][2]], 4, "big"))
					newfile.write(int_to_bytes(hactdata[0][3], 4, "big"))
					newfile.write(int_to_bytes(hactdata[0][4], 4, "big"))
					newfile.write(int_to_bytes(hactdata[0][5], 4, "big"))
					if OEGame != 1:
						newfile.write(int_to_bytes(stringpointerdict[hactdata[0][6]], 4, "big"))
						newfile.write(int_to_bytes(hactdata[0][7], 4, "big"))
						newfile.write(int_to_bytes(hactdata[0][8], 4, "big"))
						newfile.write(int_to_bytes(hactdata[0][9], 4, "big"))

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
			newfile = open("hact new.chp", 'rb+')
			newfile.seek(12)
			newfile.write(int_to_bytes(filesize, 4, "big"))
			file.close
			newfile.close
			
			
	

	if filetype == "CFC":
		newfile = open("fighter_command new.cfc", 'w+b')
		if VersionDictionary[fileversion] == "Dragon Engine":
			DEGame = DEGameDictionary[enginegame]
			if DEGame == 2: JacketMod = 1
			else: JacketMod = 0
			newfile.write(b'\x43\x46\x43\x49\x21\x00\x00\x00')#Writes header
			newfile.write(int_to_bytes(fileversion, 4))
			newfile.write(b'\x00\x00\x00\x00')#Writes filesize filler
			print("")
			print("Beginning String Extraction...")
			print("")
			for f in os.listdir(kfile):#Loops through all Json files and collects string data
				curfile = workdir + "\\" + f
				print(f)
				with open(curfile, 'r', encoding='utf8') as file:
					jsonfile = json.load(file)
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					stringlistEntryAdd(commandsetname, stringlist)
			for f in os.listdir(kfile):#Loops through all Json files and collects string data
				curfile = workdir + "\\" + f
				print(f)
				with open(curfile, 'r', encoding='utf8') as file:
					jsonfile = json.load(file)
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					#stringlist.append(commandsetname)
					#commandsetID = jsonfile[commandsetname]["Command Set ID"]
					for move in list(jsonfile[commandsetname]["Move Table"].keys()):
						movename = move
						stringlistEntryAdd(movename, stringlist)
						if "Animation Used" in jsonfile[commandsetname]["Move Table"][movename]:
							animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Used"]
							stringlistEntryAdd(animvalue, stringlist)
						if "Animation Table" in jsonfile[commandsetname]["Move Table"][movename]:
							for animtables in list(jsonfile[commandsetname]["Move Table"][movename]["Animation Table"].keys()):
								animvalue = jsonfile[commandsetname]["Move Table"][movename]["Animation Table"][animtables]["Animation Used"]
								stringlistEntryAdd(animvalue, stringlist)
						if "Follow Up Table" in jsonfile[commandsetname]["Move Table"][movename]:
							for followuptable in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"].keys()):
								if "Follows Up Properties" in jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]:
									for followupprop in list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"].keys()):
										propertytype = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Property Type"]
										if propertytype in [31]:
											string = list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop].values())[1]
											stringlistEntryAdd(string, stringlist)
										elif propertytype == 11 and fileversion == 16:
											heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Hact Name"]
											stringlistEntryAdd(heataction, stringlist)
					if DEGame == 0:
						if "Weapon Moveset Table" in jsonfile[commandsetname]:
							for weaponset in list(jsonfile[commandsetname]["Weapon Moveset Table"].keys()):
								WeaponCommand = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Command Set Name for Weapon Moveset"]
								if WeaponCommand == "Null":
									WeaponCommand = b'\x00'
								stringlist.append(WeaponCommand)
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
			print("")
			print("Beginning Data Extraction...")
			print("")
			while CommandSetOrderIDx < numcommandsets:
				curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
				print(CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json")
				with open(curfile, 'r', encoding='utf8') as file:
					jsonfile = json.load(file)
					print(curfile)
					MovePointers = []
					FollowUpIdx = OrderedDict()
					fileversion = jsonfile["File Version"]
					commandsetname = list(jsonfile.keys())[2]
					if DEGame == 1: commandsetID = jsonfile[commandsetname]["Command Set ID"]

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
										#list(jsonfile.keys())[1]
										temparray2.append(propertyExtraction(f, False, 0, [], [], VersionDictionary[fileversion], fileversion, "", jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop], ButtonPressListDE))
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
						elif movetype == 3 - JacketMod:
							animshort2 = jsonfile[commandsetname]["Move Table"][movename]["Moveset IDx"]
							animshort1 = jsonfile[commandsetname]["Move Table"][movename]["Move IDx to Play in Moveset"]
							animshort3 = jsonfile[commandsetname]["Move Table"][movename]["Command Set ID"]
							AnimationValues.append([animshort1, animshort2,animshort3])
						elif movetype == 17 - JacketMod:
							animvalue = jsonfile[commandsetname]["Move Table"][movename]["Unk Value"]
							AnimationValues.append([animvalue])
						elif movetype == 4 - JacketMod:
							byte1 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 1"]
							byte2 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 2"]
							byte3 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 3"]
							byte4 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 4"]
							byte5 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 5"]
							byte6 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 6"]
							byte7 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 7"]
							byte8 = jsonfile[commandsetname]["Move Table"][movename]["Animation Related Byte 8"]
							AnimationValues.append([byte1,byte2,byte3,byte4,byte5,byte6,byte7,byte8])
						if "Additional Properties Table" in jsonfile[commandsetname]["Move Table"][movename]:
							numadditionalprops = len(jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"])
							for moveproperty in list(jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"].keys()):
								unkshort1 = jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"][moveproperty]["Unk Short 1"]
								unkshort2 = jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"][moveproperty]["Unk Short 2"]
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
								writePropertiestoFile(newfile, FollowUpPropValues[x][y], VersionDictionary[fileversion], fileversion, stringpointerdict)
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
							
						x = 0
						AdditionalMovePropsPointers = []
						while x < numadditionalprops:
							currentpos = newfile.tell()
							AdditionalMovePropsPointers.append(currentpos)
							newfile.write(int_to_bytes(AdditionalMoveProps[x][0], 2, "little"))
							newfile.write(int_to_bytes(AdditionalMoveProps[x][1], 2, "little"))
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
						x = 0
						AdditionalMovePropsPointer = newfile.tell()
						while x < numadditionalprops:
							#Writes Move Additional Property List to File
							newfile.write(int_to_bytes(AdditionalMovePropsPointers[x], 4, "little"))
							newfile.write(b'\x00\x00\x00\x00')
							x = x + 1
						MovePointers.append(newfile.tell())
						curmovepointer = newfile.tell()
						newfile.write(int_to_bytes(stringpointerdict[movename], 4))
						newfile.write(b'\x00\x00\x00\x00')
						if animtablebool == 1:
							newfile.write(int_to_bytes(AnimTableTableTablePointer, 4))
							newfile.write(b'\x00\x00\x00\x00')
						elif movetype == 3 - JacketMod:
							newfile.write(int_to_bytes(AnimationValues[0][0], 2))
							newfile.write(int_to_bytes(AnimationValues[0][1], 2))
							newfile.write(int_to_bytes(AnimationValues[0][2], 2))
							newfile.write(b'\x00\x00')
						elif movetype == 17 - JacketMod:
							newfile.write(int_to_bytes(AnimationValues[0][0], 4))
							newfile.write(b'\x00\x00\x00\x00')
						elif movetype == 4 - JacketMod:
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
						newfile.write(int_to_bytes(AdditionalMovePropsPointer, 4))
						newfile.write(b'\x00\x00\x00\x00')
						newfile.write(int_to_bytes(numfollowups, 1))
						newfile.write(int_to_bytes(numadditionalprops, 1))
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
							if DEGame == 0 or DEGame == 2: 
								WeaponCommand = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Command Set Name for Weapon Moveset"]
								if WeaponCommand == "Null":
									WeaponCommand = b'\x00'
							elif DEGame == 1: WeaponCommand = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Command Set ID for Weapon Moveset"]
							for weaponprops in list(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"].keys()):
								temparray3 = []
								temparray3.append(propertyExtraction(f, False, 0, [], [], VersionDictionary[fileversion], fileversion, "", jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops], ButtonPressListDE))
								WeaponPropertyArray.append(temparray3)
							x = 0
							while x < numwepprops:
								y = 0
								while y < len(WeaponPropertyArray[x]):
									WeaponPropertyPointers.append(newfile.tell())
									writePropertiestoFile(newfile, WeaponPropertyArray[x][y], VersionDictionary[fileversion], fileversion, stringpointerdict)
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
							if DEGame == 1: newfile.write(int_to_bytes(WeaponCommand, 2))
							else: newfile.write(b'\x00\x00')
							newfile.write(b'\x00\x00\x00\x00')
							newfile.write(int_to_bytes(WeaponMovesetPropListPointer, 4))
							newfile.write(b'\x00\x00\x00\x00')
							WeaponSetPointers.append(newfile.tell())
							newfile.write(int_to_bytes(WeaponCommandSetPointer, 4))
							newfile.write(b'\x00\x00\x00\x00')
							if DEGame == 1: newfile.write(int_to_bytes(WeaponCommand, 4))
							elif DEGame == 0: newfile.write(int_to_bytes(stringpointerdict[WeaponCommand], 4))
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
					if DEGame == 1: newfile.write(int_to_bytes(commandsetID, 4))
					else: newfile.write(b'\x00\x00\x00\x00')
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
				print("2 = Yakuza Ishin")
				OEGameText = input("Enter a Number: ")
				OEGame = int(OEGameText)
				if OEGame > 2:
					print("An incorrect option was entered. Please restart the program and try again.")
					input("Press ENTER to exit... ")
					sys.exit()
				setnamekey = 1
			else:
				OEGame = OEGameDictionary[enginegame]
				setnamekey = 2
			newfile.write(b'\x43\x46\x43\x49\x02\x01\x00\x00\x00\x00\x00\x07\x00\x00\x00\x00')#Writes header with filesize filler
			print("")
			print("Beginning String Extraction...")
			print("")
			for f in os.listdir(kfile):#Loops through all Json files and collects string data
				curfile = workdir + "\\" + f
				print(f)
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
											if propertytype in [10,16,22,23,30,36,47]:
												string = list(jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop].values())[1]
												stringlistEntryAdd(string, stringlist)
					if "Weapon Moveset Table" in jsonfile[commandsetname]:
						for weaponset in list(jsonfile[commandsetname]["Weapon Moveset Table"].keys()):
							WeaponCommand = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Command Set Name for Weapon Moveset"]
							if WeaponCommand == "Null":
								WeaponCommand = b'\x00'
							stringlist.append(WeaponCommand)
							for weaponprops in list(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"].keys()):
								propertytype = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Property Type"]
								if propertytype in [10,16,22,23,30,36,47]:
									string = list(jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops].values())[1]
									stringlistEntryAdd(string, stringlist)
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
			print("")
			print("Beginning Data Extraction...")
			print("")
			while CommandSetOrderIDx < numcommandsets:
				curfile = workdir + "\\" + CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json"
				print(CommandSetOrderDictionary[str(CommandSetOrderIDx)] + ".json")
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
											temparray2.append(propertyExtraction(f, False, 0, [], [], VersionDictionary[fileversion], fileversion, "", jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop], ButtonPressListOE))
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
								short2 = jsonfile[commandsetname]["Move Table"][movename]["Move IDx to Play in Moveset"]
								AnimationValues.append([short1, short2,"Useless"])
							elif movetype == 3:
								byte1 = jsonfile[commandsetname]["Move Table"][movename]["Moveset IDx for Sync"]
								byte2 = jsonfile[commandsetname]["Move Table"][movename]["Unknown Short"]
								AnimationValues.append([byte1,byte2])
							if "Additional Properties Table" in jsonfile[commandsetname]["Move Table"][movename]:
								numadditionalprops = len(jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"])
								for moveproperty in list(jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"].keys()):
									unkshort1 = jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"][moveproperty]["Unk Short 1"]
									unkshort2 = jsonfile[commandsetname]["Move Table"][movename]["Additional Properties Table"][moveproperty]["Unk Short 2"]
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
									writePropertiestoFile(newfile, FollowUpPropValues[x][y], VersionDictionary[fileversion], fileversion, stringpointerdict)
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
								elif OEGame == 1 or OEGame == 2:
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
							if OEGame == 0 or OEGame == 2:
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
							if OEGame == 0 or OEGame == 2:
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
								temparray3 = []								
								temparray3.append(propertyExtraction(f, False, 0, [], [], VersionDictionary[fileversion], fileversion, "", jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops], ButtonPressListOE))
								WeaponPropertyArray.append(temparray3)
							x = 0
							while x < numwepprops:
								y = 0
								while y < len(WeaponPropertyArray[x]):
									WeaponPropertyPointers.append(newfile.tell())
									writePropertiestoFile(newfile, WeaponPropertyArray[x][y], VersionDictionary[fileversion], fileversion, stringpointerdict)
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