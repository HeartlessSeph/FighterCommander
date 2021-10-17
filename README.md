# Fighter Commander
A work in progress Fighter Command.cfc & Hact.chp extractor and repacker for Yakuza games.

This tool exports fighter_command.cfc command sets and Hact.chp heat actions into editable json files that can then repacked and imported into the game. This allows full control of moveset strings, follow ups, move conditions, weapon movesets, heat action conditions and more. 



**COMPATABILITY:**

The tool currently supports:

• Yakuza 5

• Yakuza Ishin

• Yakuza 0

• Yakuza Kiwami 1

• Yakuza 6

• Yakuza Kiwami 2

• Fist of the North Star Lost Paradise (Hact.chp support currently unknown)

• Judgment (Hact.chp can be extracted but repacking is currently not supported)



**USAGE:**

• fighter_command.cfc: Drag and drop the cfc file of the game you are extracting onto Fighter_Commander.exe and select the appropriate game option. After extracting, a new folder named "Fighter Command" will be created with all the movesets in the game represented by multiple json files. After making the edits you want to make to the movesets, drag and drop the "Fighter Command" folder onto Fighter_Commander.exe to repack the cfc file. The newly created file will be named "fighter_command new.cfc". You can then rename the file and insert it into the game.

• hact.chp: Drag and drop the chp file of the game you are extracting onto Fighter_Commander.exe and select the appropriate game option. If you are extracting hact.chp from Judgment or Yakuza Like a Dragon, you will first need to extract talk_param.bin using reARMP by Retraso (download from https://github.com/CapitanRetraso/reARMP). Place the extract talk_param.bin in the same folder as Fighter Commander and follow the instructions given by Fighter Commander. After extracting, a new folder named "Hact CHP" will be created with all the heat actions in the game represented by multiple json files. After making the edits you want to make to the movesets, drag and drop the "Hact CHP" folder onto Fighter_Commander.exe to repack the chp file. The newly created file will be named "hact new.chp". You can then rename the file and insert it into the game.



**MISC USAGE**:

• Dragging and dropping a json file from an extracted Fighter_Command.cfc will give a list of moves from that command set and the idx of that move (for use with move types that references move idx's)

• Running Fighter_Commander.exe by itself will ask if you want to extract the internal dictionaries. Doing this will allow you to edit the enums used in the extracted files (for example, if you find out what the actual usage for an "unknown" enum is you can extract the dictionaries and add the name of it to the dictionaries. Re-extracting the file will then show the added enums you added.)



**DISCLAIMER:**

Please note that there are still a bunch of undocumented variables. Values or bytes that are documented will be included in updates to this tool as they are found. As such, if you release a moveset mod, please include the exact version of the tool used if you are including only the json as future updates of the tool might become incompatible.



**CREDITS:**

Massive thanks to Capitan Retraso for his Fighter Command notes and for helping me out on finding the move table.

Also a massive thanks to ChuckP, who has done a lot of documentation for follow up property types.

Thank you to Draxx182 for documenting Hact.chp for all of the Old Engine games. Support for those files likely would not have been added otherwise.
