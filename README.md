# UPDATE:

An overhaul of Fighter Commander's code was done to make updating some stuff easier. This began as me attempting to make the code super clean and eventually spiraled out of control. It's still 1000 times better than what I was dealing with before.

This is an early release as I'm experiencing some burnout. Hact.chp repacking support is not yet supported for any games. Use the prior version if you want to edit hact.chp for earlier games.

# Fighter Commander

A work in progress Fighter Command.cfc & Hact.chp extractor and repacker for Yakuza games.

This tool exports fighter_command.cfc command sets and Hact.chp heat actions into editable json files that can then repacked and imported into the game. This allows full control of moveset strings, follow ups, move conditions, weapon movesets, heat action conditions and more. 



**COMPATABILITY:**

The tool currently supports all fighter_command.cfc files from each game that has a .cfc file. Hact.chp is not supported on the current version but will be included soon.



**USAGE:**

Drag and drop the cfc file you are extracting onto Fighter_Commander.exe. It is recommended to extract motion_gmt.bin and talk_param.bin with reARMP and placing them into the same directory as the file you are extracting as they will allow names for games that use IDs for heat actions and motions.



**DISCLAIMER:**

Please note that there are still a bunch of undocumented variables. Values or bytes that are documented will be included in updates to this tool as they are found. As such, if you release a moveset mod, please include the exact version of the tool used if you are including only the json as future updates of the tool might become incompatible.



**CREDITS:**

Massive thanks to Capitan Retraso for his Fighter Command notes and for helping me out on finding the move table.

Also a massive thanks to ChuckP, who has done a lot of documentation for follow up property types.

Thank you to Draxx182 for documenting Hact.chp for all of the Old Engine games. Support for those files likely would not have been added otherwise.

Jhrino for a ton of stuff.
