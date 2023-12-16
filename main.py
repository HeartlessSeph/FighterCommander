from Structure.CFC.File import cfcFile
from Structure.CHP.File import chpFile
from binary_reader import Whence, Endian
from Utilities.bin_reader import BinaryReader
from Utilities.util import *
import Structure.Enums.common as com
import cutie
import argparse
from pathlib import Path
import shutil


def unpack_cfc(args, reader):
    cfc_game = com.Game()
    cfc_game.set_game(args.game)
    reader.set_engine(cfc_game.engine)

    cfc_file = cfcFile()
    cfc_file.set_game(cfc_game)
    cfc_file.set_name(args.path.stem)
    cfc_file.read_file(reader)
    cfc_file.assign_all_follow_ups()
    cfc_file.build_jsons()

    if args.output_name:
        out_name = args.output_name
    else:
        out_name = f"Fighter Command ({cfc_game.name})"

    order_dict = {"Set Order": {cset.name: cset.id for cset in cfc_file.command_set_table.command_sets}}
    extra_dict = {"Motion GMT File": "", "Talk Param File": ""}
    out_folder = Path(args.path.parents[0] / out_name)
    out_folder.mkdir(parents=True, exist_ok=True)
    if args.motion_gmt:
        extra_dict["Motion GMT File"] = args.motion_gmt.name
        shutil.copy(str(args.motion_gmt), str(out_folder / args.motion_gmt.name))
    if args.talk_param:
        extra_dict["Talk Param File"] = args.talk_param.name
        shutil.copy(str(args.talk_param), str(out_folder / args.talk_param.name))

    info_dict = collect_extracted_file_info(file_extension, cfc_file, order_dict, extra_dict)

    for idx, cfc_json in enumerate(cfc_file.command_set_table.cfc_jsons):
        cur_name = cfc_file.command_set_table.command_sets[idx].name
        export_json(out_folder / "Extracted", cur_name, cfc_json)

    export_json(out_folder, "File Information", info_dict)


def repack_cfc():
    # TODO: Clean this code up, it's a mess
    cfc_file = cfcFile()
    cfc_file.set_game(game)
    cfc_file.header.set_version(file_info_dict["File Version"])
    cfc_file.header.write_header(writer)
    cfc_file.command_set_table.parse_jsons(com.file_jsons, game)
    com.write_string_table(writer, com.string_dict)
    cfc_file.deassign_all_follow_ups()

    command_set_pointers = []
    # Write data
    for cset in cfc_file.command_set_table.command_sets:
        print(cset.name)
        move_pointers = []
        for cmove in cset.moves:
            fol_pointers = []
            add_prop_pointers = []
            for cfollow_up in cmove.follow_ups:
                condition_offsets = []
                for cprop in cfollow_up.properties:
                    cprop.cmd_trigger.write_to_buffer()
                    cur_buffer = cprop.cmd_trigger.Prop_Buffer
                    cur_bytes = cur_buffer.read_bytes(cur_buffer.size())
                    if game.engine == com.GameEngine.OE: cur_bytes = cur_bytes[::-1]
                    condition_offsets.append(writer.pos())
                    writer.write_bytes(cur_bytes)  # Writes props
                condition_offsets_pointer = writer.pos()
                for mpointer in condition_offsets: writer.write_uint_var(mpointer)
                fol_pointers.append(writer.pos())
                writer.write_uint16(len(condition_offsets))
                writer.write_uint16(cfollow_up.follow_up_move_idx)
                if game.engine == com.GameEngine.DE: writer.write_uint32(0)
                writer.write_uint_var(condition_offsets_pointer)

            for add_prop in cmove.add_props:
                add_prop_pointers.append(writer.pos())
                writer.write_uint32(add_prop)

            anim_table_offsets = []
            move_json = cmove.battle_mode.prop_dict
            cmove_buffer = cmove.battle_mode.prop_class.write_property(move_json, game)
            cmove_buffer.seek(0)
            if cmove_buffer.size() > (4 * game.engine):
                while cmove_buffer.pos() < cmove_buffer.size():
                    temp_val_1 = cmove_buffer.read_uint_var()
                    temp_val_2 = cmove_buffer.read_bytes(4 * game.engine)
                    anim_table_offsets.append(writer.pos())
                    writer.write_uint_var(temp_val_1)
                    writer.write_bytes(temp_val_2)
            else:
                anim_val = cmove_buffer.read_uint_var()

            move_follow_up_offsets_pointer = writer.pos()
            for fol_pointer in fol_pointers:
                writer.write_uint_var(fol_pointer)

            anim_tables_pointer = writer.pos()
            for anim_table_pointer in anim_table_offsets:
                writer.write_uint_var(anim_table_pointer)
            if len(anim_table_offsets) > 0:
                anim_val = writer.pos()
                if game.engine == com.GameEngine.DE: writer.write_uint_var(anim_tables_pointer)
                # The below is generally 0. In the original program, I wrote it as 1 if the following games for whatever reason.
                # unk_val = int(game.type in [com.CFC_GROUPS.OE_Y5, com.CFC_GROUPS.OE_ISHIN])
                writer.write_uint8(0)
                writer.write_uint8(len(anim_table_offsets))
                writer.write_uint16(0)
                if game.engine == com.GameEngine.OE: writer.write_uint_var(anim_tables_pointer)
                if game.engine == com.GameEngine.DE: writer.write_uint32(0)

            add_prop_offsets_pointer = writer.pos()
            for add_prop_pointer in add_prop_pointers:
                writer.write_uint_var(add_prop_pointer)

            move_pointers.append(writer.pos())
            writer.write_uint_var(com.string_dict[cmove.name])
            if game.engine == com.GameEngine.DE:
                writer.write_uint_var(anim_val)
                writer.write_uint_var(move_follow_up_offsets_pointer)
                writer.write_uint_var(add_prop_offsets_pointer)
                writer.write_uint8(len(fol_pointers))
                writer.write_uint8(len(add_prop_pointers))
                writer.write_uint8(int(len(anim_table_offsets) > 0))
                writer.write_uint8(cmove.type)
                writer.write_uint32(0)
            else:
                writer.write_uint8(len(fol_pointers))
                if game.type in [com.CFC_GROUPS.OE, com.CFC_GROUPS.OE_ISHIN]:
                    writer.write_uint8(len(add_prop_pointers))
                    writer.write_uint8(int(len(anim_table_offsets) > 0))
                else:
                    writer.write_uint8(int(len(anim_table_offsets) > 0))
                    writer.write_uint8(len(add_prop_pointers))
                writer.write_uint8(cmove.type)
                writer.write_uint_var(anim_val)
                writer.write_uint_var(move_follow_up_offsets_pointer)
                if game.type != com.CFC_GROUPS.OE_Y5: writer.write_uint_var(add_prop_offsets_pointer)
        move_table_pointer = writer.pos()
        for move_pointer in move_pointers:
            writer.write_uint_var(move_pointer)

        moveset_pointers = []
        for cmoveset in cset.movesets:
            condition_offsets = []
            for cprop in cmoveset.properties:
                cprop.cmd_trigger.write_to_buffer()
                cur_buffer = cprop.cmd_trigger.Prop_Buffer
                cur_bytes = cur_buffer.read_bytes(cur_buffer.size())
                if game.engine == com.GameEngine.OE: cur_bytes = cur_bytes[::-1]
                condition_offsets.append(writer.pos())
                writer.write_bytes(cur_bytes)  # Writes props
            condition_offsets_pointer = writer.pos()
            for mpointer in condition_offsets: writer.write_uint_var(mpointer)
            moveset_pointer = writer.pos()
            writer.write_uint16(len(condition_offsets))
            writer.write_uint16(cmoveset.id)
            if game.engine == com.GameEngine.DE: writer.write_uint32(0)
            writer.write_uint_var(condition_offsets_pointer)
            moveset_pointers.append(writer.pos())
            writer.write_uint_var(moveset_pointer)
            if game.type in [com.CFC_GROUPS.DE_CUR, com.CFC_GROUPS.DE_K2]:
                writer.write_uint_var(cmoveset.id)
            else:
                writer.write_uint_var(cmoveset.name)
        moveset_list_pointer = writer.pos()
        for moveset_pointer in moveset_pointers:
            writer.write_uint_var(moveset_pointer)

        command_set_pointers.append(writer.pos())
        writer.write_uint_var(com.string_dict[cset.name])
        if game.type in [com.CFC_GROUPS.DE_CUR, com.CFC_GROUPS.DE_K2]:
            writer.write_uint_var(com.set_id_name[cset.name])
        elif game.type == com.CFC_GROUPS.DE_Y6:
            writer.write_uint_var(0)
        else:
            writer.write_uint_var(com.string_dict[cset.id])
        if game.engine == com.GameEngine.DE:
            writer.write_uint_var(move_table_pointer)
            writer.write_uint_var(moveset_list_pointer)
            writer.write_uint16(len(move_pointers))
            writer.write_uint16(len(moveset_pointers))
            writer.write_uint32(0)
        else:
            writer.write_uint32(len(move_pointers))
            writer.write_uint_var(move_table_pointer)
            writer.write_uint32(len(moveset_pointers))
            writer.write_uint_var(moveset_list_pointer)
    command_set_table_pointer = writer.pos()
    for command_set_pointer in command_set_pointers:
        writer.write_uint_var(command_set_pointer)
    if game.engine == com.GameEngine.DE:
        writer.write_uint_var(command_set_table_pointer)
        writer.write_uint_var(len(command_set_pointers))
    else:
        writer.write_uint_var(len(command_set_pointers))
        writer.write_uint_var(command_set_table_pointer)

    writer.seek(0xC)
    writer.write_uint32(writer.size())

    if args.output_name:
        out_name = args.output_name
    else:
        out_name = "fighter_command_new"

    file_name = str(args.path.parent) + f"/{out_name}.cfc"
    with open(file_name, 'wb') as f:
        f.write(writer.buffer())


def unpack_chp(args, reader):
    chp_game = com.Game()
    chp_game.set_game(args.game)
    com.cur_game = chp_game
    reader.set_engine(chp_game.engine)

    chp_file = chpFile()
    chp_file.set_game(chp_game)
    chp_file.set_name(args.path.stem)
    chp_file.read_file(reader)
    chp_file.build_jsons()

    if args.output_name:
        out_name = args.output_name
    else:
        out_name = f"HAct ({chp_game.name})"

    order_dict = {"Set Order": {cset.name: "" for cset in chp_file.hact_set_table.hact_sets}}
    extra_dict = {"Motion GMT File": "", "Talk Param File": ""}
    out_folder = Path(args.path.parents[0] / out_name)
    out_folder.mkdir(parents=True, exist_ok=True)
    if args.motion_gmt:
        extra_dict["Motion GMT File"] = args.motion_gmt.name
        shutil.copy(str(args.motion_gmt), str(out_folder / args.motion_gmt.name))
    if args.talk_param:
        extra_dict["Talk Param File"] = args.talk_param.name
        shutil.copy(str(args.talk_param), str(out_folder / args.talk_param.name))

    info_dict = collect_extracted_file_info(file_extension, chp_file, order_dict, extra_dict)

    for idx, cfc_json in enumerate(chp_file.hact_set_table.chp_jsons):
        cur_name = chp_file.hact_set_table.hact_sets[idx].name
        export_json(out_folder / "Extracted", cur_name, cfc_json)

    export_json(out_folder, "File Information", info_dict)


def repack_chp(args, file_info_dict):
    chp_file = chpFile()
    chp_file.set_game(game)
    chp_file.header.set_version(file_info_dict["File Version"])
    chp_file.header.write_header(writer)
    chp_file.hact_set_table.parse_jsons(com.file_jsons, game)
    com.write_string_table(writer, com.string_dict, b'\xCC', 4 * game.engine)

    hact_set_pointers = []
    # Write data
    for hset in chp_file.hact_set_table.hact_sets:
        print(hset.name)
        target_pointers = []
        for htarget in hset.targets:
            condition_offsets = []
            for cprop in htarget.properties:
                cprop.cmd_trigger.write_to_buffer()
                cur_buffer = cprop.cmd_trigger.Prop_Buffer
                cur_bytes = cur_buffer.read_bytes(cur_buffer.size())
                if game.engine == com.GameEngine.OE: cur_bytes = cur_bytes[::-1]
                condition_offsets.append(writer.pos())
                writer.write_bytes(cur_bytes)  # Writes props

            condition_offsets_pointer = writer.pos()
            for mpointer in condition_offsets: writer.write_uint_var(mpointer)
            target_pointers.append(writer.pos())
            writer.write_uint_var(com.string_dict[htarget.name])
            if game.engine == com.GameEngine.DE:
                writer.write_uint_var(condition_offsets_pointer)
                writer.write_uint32(htarget.type)
                writer.write_uint32(htarget.end_motion_id)
                writer.write_uint32(len(condition_offsets))
                writer.write_uint32(htarget.modify_flag)
            else:
                writer.write_uint32(htarget.type)
                writer.write_uint32(com.string_dict[htarget.end_motion_id])
                writer.write_uint32(len(condition_offsets))
                writer.write_uint32(condition_offsets_pointer)
                writer.write_uint32(htarget.modify_flag)
        target_table_offset = writer.pos()
        for target_pointer in target_pointers:
            writer.write_uint_var(target_pointer)
        hact_set_pointers.append(writer.pos())
        if game.type == com.CFC_GROUPS.DE_CUR:
            writer.write_uint32(hset.id)
            writer.write_uint32(hset.sub)
        else:
            writer.write_uint_var(com.string_dict[hset.name])
        if game.engine == com.GameEngine.DE:
            writer.write_uint_var(target_table_offset)
            if game.type == com.CFC_GROUPS.DE_CUR:
                writer.write_uint_var(com.string_dict[hset.special_effect])
                writer.write_uint32(hset.comp_flag)
                writer.write_uint32(len(target_pointers))
                writer.write_uint32(hset.play_area_type)
            else:
                if game.type in [com.CFC_GROUPS.DE_DEMO, com.CFC_GROUPS.DE_Y6]:
                    writer.write_uint_var(com.string_dict[hset.id])
                else:
                    writer.write_uint32(hset.play_area_type)
                    writer.write_uint32(hset.id)
                writer.write_uint_var(com.string_dict[hset.comp_flag])
                writer.write_uint32(len(target_pointers))

            writer.write_float(hset.x)
            writer.write_float(hset.y)
            writer.write_float(hset.z)
            writer.write_float(hset.rot)

            if game.type != com.CFC_GROUPS.DE_CUR:
                writer.write_float(hset.unk_target_val)
                writer.write_uint32(com.string_dict[hset.hact_base])
            writer.write_uint32(0)
        else:
            writer.write_uint32(len(target_pointers))
            writer.write_uint32(target_table_offset)
            writer.write_uint32(hset.unk_target_val)
            writer.write_uint32(com.string_dict[hset.comp_flag])
            writer.write_float(hset.x)
            writer.write_float(hset.y)
            writer.write_float(hset.z)
            if game.type != com.CFC_GROUPS.OE_Y5:
                writer.write_uint32(com.string_dict[hset.condition])
                writer.write_uint32(hset.unk_int_3)
                writer.write_uint32(hset.unk_int_4)
                writer.write_uint32(0)  # Unk Int 5
    hact_table_offset = writer.pos()
    for hact_set_pointer in hact_set_pointers:
        writer.write_uint_var(hact_set_pointer)
    writer.write_uint_var(len(hact_set_pointers))
    writer.write_uint_var(hact_table_offset)
    writer.seek(0xC)
    writer.write_uint32(writer.size())

    if args.output_name:
        out_name = args.output_name
    else:
        out_name = "hact_new"

    file_name = str(args.path.parent) + f"/{out_name}.chp"
    with open(file_name, 'wb') as f:
        f.write(writer.buffer())


# Main file begins starting from here below
parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("path", help="Path to file or folder")
parser.add_argument('-game', '--game', action='store', help='Game for file being extracted')
parser.add_argument('-gmt', '--motion_gmt', action='store', help='Path to motion_gmt.json')
parser.add_argument('-talk', '--talk_param', action='store', help='Path to motion_gmt.json')
parser.add_argument('-out', '--output_name', action='store', help='Name of the output file/folder')
parser.add_argument('-cid', '--cset_id', action='store_true', help='DEBUG: Use CSET ID for sync extraction. For mods that did not correctly assign moveset idx for syncs post-Y6 DE.')

args = parser.parse_args()
com.args = args

try:

    args.path, is_file, is_directory, file_extension = verify_path_info(args.path)
    parent_directory = Path(args.path).parent
    if args.motion_gmt: com.motion_gmt, args.motion_gmt = parse_arg_armp_json(args.motion_gmt)
    if args.talk_param: com.talk_param, args.talk_param = parse_arg_armp_json(args.talk_param)
    if not args.game and is_file:
        print("Select the game that is being extracted.")
        choice = com.LAD_OPTION[cutie.select(com.LAD_OPTION)]
        args.game = com.LAD_GAME[choice]

    if not is_file and is_directory:
        file_info_dict = import_json(args.path, "File Information")
        file_extension = file_info_dict["Filetype"]
        json_directory = file_info_dict["Files Directory"]
        if not args.motion_gmt:
            if file_info_dict["Motion GMT File"] != "":
                com.motion_gmt, args.motion_gmt = parse_arg_armp_json(parse_path_relativity(file_info_dict["Motion GMT File"], args.path))
        if not args.talk_param:
            if file_info_dict["Talk Param File"] != "":
                com.talk_param, args.talk_param = parse_arg_armp_json(parse_path_relativity(file_info_dict["Talk Param File"], args.path))
        com.motion_gmt = {v: k for k, v in com.motion_gmt.items()}
        com.talk_param = {v: k for k, v in com.talk_param.items()}
        game = com.Game()
        game.set_game(file_info_dict["Game Key"])
        writer = BinaryReader()
        writer.set_encoding('Shift-JIS')
        writer.set_engine(game.engine)
        writer.set_endian(game.engine == com.GameEngine.OE)
        for idx, file_name in enumerate(file_info_dict["File Specific Info"]["Set Order"].keys()):
            com.file_order[file_name] = idx
            com.file_names[idx] = file_name
            com.set_id_order[idx] = file_info_dict["File Specific Info"]["Set Order"][file_name]
            com.set_id_name[file_name] = file_info_dict["File Specific Info"]["Set Order"][file_name]
            print(f"Importing {file_name} json")
            cur_json = import_json(args.path / json_directory, file_name)
            com.file_jsons[file_name] = cur_json
        if file_extension == ".chp":
            repack_chp(args, file_info_dict)
        elif file_extension == ".cfc":
            repack_cfc()

    if is_file:
        com.motion_gmt, args.motion_gmt = json_scan(args.motion_gmt, "motion_gmt", parent_directory, com.motion_gmt)
        com.talk_param, args.talk_param = json_scan(args.talk_param, "talk_param", parent_directory, com.talk_param)
        with args.path.open('rb') as f:
            reader = BinaryReader(f.read())
            reader.set_encoding('Shift-JIS')
        if file_extension == ".chp":
            unpack_chp(args, reader)
        elif file_extension == ".cfc":
            unpack_cfc(args, reader)

    input("Program run successfully. Press enter to exit.")

except:
    import traceback

    traceback.print_exc()
    input("Program crashed; press Enter to exit")
