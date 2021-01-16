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
   +-------------------------+
   |     FIGHTER  COMMANDER     |
   +-------------------------+\n
   TEST VERSION - EXPECT ERRORS\n''')

if (len(sys.argv) <= 1):
	print ("Usage: Drag and drop fighter_command.cfc onto Fighter Commander to extract to json")
	print ("Drag and drop folder containing jsons onto Fighter Commander to rebuild fighter_command.cfc")
	input("Press ENTER to exit... ")
	sys.exit()
	

def int_to_bytes(n, minlen=0):
	""" Convert integer to bytearray with optional minimum length. 
	"""
	if isinstance(n, float) == True:
		n = int(n)
	if n > 0:
		if n > 16777215:
			b = 0
			b = int.to_bytes(n, 4, "little")
		elif n > 65535:
			b = 0
			b = int.to_bytes(n, 3, "little")
		elif n > 255:
			b = 0
			b = int.to_bytes(n, 2, "little")
		else:
			b = 0
			b = int.to_bytes(n, 1, "little")
	elif n == 0:
		b = bytearray(b'\x00')
	elif n < 0:
		if n < -16777215:
			n = 4294967296 + n
			b = 0
			b = int.to_bytes(n, 4, "little")
		elif n < -65535:
			n = 16777216 + n
			b = 0
			b = int.to_bytes(n, 3, "little")
		elif n < -255:
			n = 65536 + n
			b = 0
			b = int.to_bytes(n, 2, "little")
		else:
			n = 256 + n
			b = 0
			b = int.to_bytes(n, 1, "little")

	if minlen > 0 and len(b) < minlen: # zero padding needed?
		padding = bytearray((minlen-len(b)))
		b = bytearray(b)
		b.extend((padding))
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
def GetStringFromPointer(myfile, pointerval = 0):
	chars = []
	h = myfile.tell()
	if pointerval != 0:
		pointercheck = pointerval
	else:
		pointercheck = int.from_bytes(myfile.read(4),"little")
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
def GetCommandSetName(myfile):
	chars = []
	h = myfile.tell()
	pointercheck1 = int.from_bytes(myfile.read(4),"little")
	myfile.seek(pointercheck1)
	pointercheck2 = int.from_bytes(myfile.read(4),"little")
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
def GoToPointer(myfile, pointerval = 0):
	if pointerval != 0:
		myfile.seek(pointerval)
	else:
		pointer = int.from_bytes(myfile.read(4),"little")
		myfile.seek(pointer)
#	
def GetMovefromIDx(Idx, FollowUpMoveIdx):
	y = 0
	while y < len(FollowUpMoveIdx):
		if Idx == FollowUpMoveIdx[y][0]:
			return FollowUpMoveIdx[y][1]
		else:
			y = y + 1
	
CommandSetDictionary = tree() #Stores Data for Command Sets
CommandSetIDDictionary = OrderedDict() #Stores a list of Command Sets and their ID's for reference.
jsonfile = OrderedDict() #Stores the dumped json from file.
FollowUpMoveIdx = [] #Stores Id's of Moves for follow ups

parser = argparse.ArgumentParser(description="Fighter_cfc extraction tool")
parser.add_argument("file", help=".cfc file")
args = parser.parse_args()
kfile = args.file
filecheck = os.path.isfile(kfile)

if filecheck == True:
	f = open(kfile, 'rb')

	patchedFile = "" #Init patched file

	curdir =  os.getcwd()
	mypath = curdir + "\\Fighter Command"
	if not os.path.isdir(mypath):
	   os.makedirs(mypath)
		
		
	f.seek(8, 1)#skips filetype and endianess
	fileversion = int.from_bytes(f.read(4),"little")
	filesize = int.from_bytes(f.read(4),"little")
	f.seek(filesize)
	f.seek(-8, 1)
	NumCommandSets = int.from_bytes(f.read(4),"little")
	f.seek(-12, 1)
	CommandSetTable = int.from_bytes(f.read(4),"little")
	f.seek(CommandSetTable)

	a = 0
	while a < NumCommandSets:
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
				CommandSetDictionary[(setname)]["Move Table"][movename]["No Anim? Equal to FF FF FF FF"] = -1
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
					propbyte1 = int.from_bytes(f.read(1),"little")
					propbyte2 = int.from_bytes(f.read(1),"little")
					propbyte3 = int.from_bytes(f.read(1),"little")
					propbyte4 = int.from_bytes(f.read(1),"little")
					f.seek(4, 1)
					propint2 = int.from_bytes(f.read(4),"little")
					f.seek(-4, 1)
					propbyte5 = int.from_bytes(f.read(1),"little")
					propbyte6 = int.from_bytes(f.read(1),"little")
					propbyte7 = int.from_bytes(f.read(1),"little")
					propbyte8 = int.from_bytes(f.read(1),"little")
					
					if propint2 == 11:
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Heat Action"] = GetStringFromPointer(f, propint1)
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Property Type"] = propint2
					else:
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 1"] = propbyte1
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 2"] = propbyte2
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 3"] = propbyte3
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Unk Byte 4"] = propbyte4
						CommandSetDictionary[(setname)]["Move Table"][movename]["Follow Up Table"]["Follow Up " + str(c)]["Follows Up Properties"]["Property "+ str(d)]["Property Type"] = propint2
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
				CommandSetDictionary[(setname)]["Weapon Moveset Table"]["Weapon Moveset " + str(b)]["Weapon Moveset Properties"]["Property " + str(c)]["Short Property 1"] = wepshort1
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
		
	with open("Command Set List.json", 'w') as outfile:
		json.dump(CommandSetIDDictionary, outfile, indent=1, ensure_ascii=False)
	f.close
#End of File extract










else:
	stringlist = []
	stringpointerdict = OrderedDict()#Stores location of Strings written to file
	curdir =  os.getcwd()
	workdir = sys.argv[1]
	newfile = open("fighter_command new.cfc", 'w+b')
	newfile.write(b'\x43\x46\x43\x49\x21\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00')#Writes header with filesize filler
	
	for f in os.listdir(kfile):#Loops through all Json files and collects string data
		curfile = workdir + "\\" + f
		with open(curfile, 'r', encoding='utf8') as file:
			jsonfile = json.load(file)
			
			commandsetname = list(jsonfile.keys())[0]
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
									heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Heat Action"]
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
	for f in os.listdir(kfile):#Loops through all Json files and collects data.
		curfile = workdir + "\\" + f
		with open(curfile, 'r', encoding='utf8') as file:
			jsonfile = json.load(file)
			MovePointers = []
			FollowUpIdx = OrderedDict()
			
			commandsetname = list(jsonfile.keys())[0]
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
								propertytype = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Property Type"]
								if propertytype == 11:
									heataction = jsonfile[commandsetname]["Move Table"][movename]["Follow Up Table"][followuptable]["Follows Up Properties"][followupprop]["Heat Action"]
									temparray2.append([propertytype, heataction])
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
							StringPointer = stringpointerdict[FollowUpPropValues[x][y][1]]
							newfile.write(int_to_bytes(StringPointer, 4))
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
					newfile.write(int_to_bytes(AnimationValues[0][0], 4))
					newfile.write(b'\x00\x00\x00\x00')
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
						propshort1 = jsonfile[commandsetname]["Weapon Moveset Table"][weaponset]["Weapon Moveset Properties"][weaponprops]["Short Property 1"]
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