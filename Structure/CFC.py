from binary_reader import Whence, Endian
from Utilities.bin_reader import BinaryReader
import Structure.Enums.common as com
from Structure.Enums.common import CFC_GROUPS, GameEngine, endianess
from Types.battle.properties import battle_command
from Types.battle.moves import battle_mode
from Utilities.util import tree
import cutie
import re


class CFC:
    def __init__(self):
        self.name = ""
        self.version = None
        self.game = None
        self.header = header()
        self.command_set_table = command_set_table()
        self.filesize = None

    def read_file(self, buffer):
        buffer.set_engine = self.game.engine
        self.filesize = self.header.read_header(buffer)
        com.read_string_table(buffer, com.string_dict)
        buffer.seek(self.filesize)
        self.command_set_table.read_header(buffer, self.game)
        self.command_set_table.read_table(buffer, self.game)

    def set_game(self, game):
        self.game = game

    def set_name(self, string):
        self.name = string

    def get_name(self):
        return self.name

    def assign_all_follow_ups(self):
        for command_set in self.command_set_table.command_sets:
            command_set.assign_follow_up_names()
        self.command_set_table.assign_moveset_link_names(self.game)

    def deassign_all_follow_ups(self):
        for command_set in self.command_set_table.command_sets:
            command_set.deassign_follow_up_names()
        self.command_set_table.deassign_moveset_link_names(self.game)

    def build_jsons(self):
        self.command_set_table.build_json()


class header:
    def __init__(self):
        self.version = None
        self.endian = None
        self.magic = "CFCI"

    def read_header(self, buffer):
        magic = buffer.read_str(4)
        if magic != self.magic:
            raise Exception("File is not a CFC File.")
        endian = buffer.read_uint32()
        self.endian = endianess[endian]
        buffer.set_endian(self.endian)
        self.version = buffer.read_uint32()
        return buffer.read_uint32()

    def set_version(self, version):
        self.version = version

    def write_header(self, buffer):
        self.endian = buffer.get_endian()
        buffer.set_endian(Endian.LITTLE)
        buffer.write_str(self.magic)
        buffer.write_uint32(com.endianess_backwards[self.endian])
        buffer.set_endian(self.endian)
        buffer.write_uint32(self.version)
        buffer.write_uint32(0)


class command_set_table:
    def __init__(self):
        self.command_sets = []
        self.offset = None
        self.num_sets = None
        self.cfc_jsons = []

    def read_header(self, buffer, game):
        if game.engine == GameEngine.DE:
            buffer.seek(-0x10, Whence.CUR)
            table_pointer = buffer.read_uint64()
            num_sets = buffer.read_uint64()
        else:
            buffer.seek(-0x08, Whence.CUR)
            num_sets = buffer.read_uint32()
            table_pointer = buffer.read_uint32()
        self.offset = table_pointer
        self.num_sets = num_sets
        buffer.seek(table_pointer)

    def assign_moveset_link_names(self, game):
        command_set_dict = {cidx: {"Name": cset.name, "Move": cset.idx_dict, "ID": cset.id} for cidx, cset in enumerate(self.command_sets)}
        command_set_dict3 = {cset.id: {"Name": cset.name, "Move": cset.idx_dict, "ID": cset.id} for cidx, cset in enumerate(self.command_sets)}
        command_set_dict2 = {cset.id: cset.name for cset in self.command_sets}
        command_set_dict2[0] = "Previous Moveset"
        for command_set in self.command_sets:
            for move in command_set.moves:
                if com.args.cset_id:
                    move.battle_mode.prop_class.idx_to_name(move.battle_mode.prop_dict, command_set_dict3)
                else:
                    move.battle_mode.prop_class.idx_to_name(move.battle_mode.prop_dict, command_set_dict)
            for moveset in command_set.movesets:
                if moveset.name is None:
                    if moveset.id not in command_set_dict2:
                        moveset.name = f"LiteralVal[{moveset.id}]"
                    else:
                        moveset.name = command_set_dict2[moveset.id]

    def deassign_moveset_link_names(self, game):
        command_set_dict = {cset.name: {"Name": cidx, "Move": cset.idx_dict, "ID": cset.id} for cidx, cset in enumerate(self.command_sets)}
        command_set_dict2 = {cset.name: cset.id for cset in self.command_sets}
        command_set_dict2["Previous Moveset"] = 0
        for command_set in self.command_sets:
            for move in command_set.moves:
                move.battle_mode.prop_class.idx_to_name(move.battle_mode.prop_dict, command_set_dict)
            for moveset in command_set.movesets:
                if game.type in [CFC_GROUPS.DE_CUR, CFC_GROUPS.DE_K2]:
                    if "literalval" in moveset.name.lower():
                        moveset.id = int(re.findall(r'\[(.*?)\]', moveset.name)[0])
                    else:
                        moveset.id = command_set_dict2[moveset.name]
                else:
                    moveset.name = com.string_dict[moveset.name]
                    moveset.id = 0

    def read_table(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_sets):
            buffer.seek(self.offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_set = command_set()
            cur_set.read_file(buffer, game)
            self.command_sets.append(cur_set)

    def update_num_sets(self):
        self.num_sets = len(self.command_sets)

    def build_json(self):
        for c_set in self.command_sets:
            cfc_json = tree()
            c_set.build_json(cfc_json)
            self.cfc_jsons.append(cfc_json)

    def parse_jsons(self, json, game):
        for cset_json in com.file_jsons.keys():
            cur_set = command_set()
            cur_set.name = cset_json
            com.string_dict[cset_json] = 0
            cur_set.parse_json(com.file_jsons[cset_json], game)
            self.command_sets.append(cur_set)


class command_set:
    def __init__(self):
        self.name = None
        self.id = None
        self.offset = None
        self.moves = []
        self.movesets = []
        self.num_moves = None
        self.num_movesets = None
        self.moveset_table_offset = None
        self.move_table_offset = None
        self.idx_dict = None

    def read_file(self, buffer, game):
        self.offset = buffer.pos()
        buffer.seek(buffer.read_uint32())
        self.name = buffer.read_str()
        print(f"Reading set: {self.name}")
        buffer.seek(self.offset)
        self.read_set(buffer, game)

    def read_set(self, buffer, game):
        buffer.read_uint_var()
        set_id = buffer.read_uint_var()
        if game.engine == GameEngine.OE:
            cur_pos = buffer.pos()
            buffer.seek(set_id)
            self.id = buffer.read_str()
            buffer.seek(cur_pos)
        else:
            self.id = set_id
        if game.engine == GameEngine.OE:
            self.__OE_SET__(buffer)
        else:
            self.__DE__SET__(buffer)
        self.read_moves(buffer, game)
        self.read_movesets(buffer, game)

    def __OE_SET__(self, buffer):
        self.num_moves = buffer.read_uint32()
        self.move_table_offset = buffer.read_uint32()
        self.num_movesets = buffer.read_uint32()
        self.moveset_table_offset = buffer.read_uint32()

    def __DE__SET__(self, buffer):
        self.move_table_offset = buffer.read_uint64()
        self.moveset_table_offset = buffer.read_uint64()
        self.num_moves = buffer.read_uint16()
        self.num_movesets = buffer.read_uint16()

    def read_moves(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_moves):
            buffer.seek(self.move_table_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_move = move()
            cur_move.read_move(buffer, game)
            self.moves.append(cur_move)

    def read_movesets(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_movesets):
            buffer.seek(self.moveset_table_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_moveset = moveset()
            cur_moveset.read_moveset(buffer, game)
            self.movesets.append(cur_moveset)

    def assign_follow_up_names(self):
        self.set_idx_dict()
        for move in self.moves:
            for follow_up in move.follow_ups:
                follow_up.follow_up_move = self.idx_dict[follow_up.follow_up_move_idx]

    def deassign_follow_up_names(self):
        self.set_name_dict()
        for move in self.moves:
            for follow_up in move.follow_ups:
                follow_up.follow_up_move_idx = self.idx_dict[follow_up.follow_up_move]

    def set_idx_dict(self):
        self.idx_dict = {idx: move.name for idx, move in enumerate(self.moves)}

    def set_name_dict(self):
        self.idx_dict = {move.name: idx for idx, move in enumerate(self.moves)}

    def build_json(self, mjson):
        for move in self.moves:
            move.build_json(mjson)
        for midx, moveset in enumerate(self.movesets):
            moveset.build_json(mjson, midx)

    def parse_json(self, mjson, game):
        self.id = com.set_id_name[self.name]
        if game.engine == com.GameEngine.OE: com.string_dict[self.id] = 0

        if "Move Table" in mjson:
            for mmove in mjson["Move Table"].keys():
                cur_move = move()
                cur_move.name = mmove
                com.string_dict[mmove] = 0
                cur_move.parse_json(mjson["Move Table"][mmove], game)
                self.moves.append(cur_move)
        if "Moveset Change Table" in mjson:
            for mmoveset in mjson["Moveset Change Table"]:
                cur_moveset = moveset()
                cur_moveset.parse_json(mjson["Moveset Change Table"][mmoveset], game)
                self.movesets.append(cur_moveset)


class move:
    def __init__(self):
        self.name = None
        self.offset = None
        self.type = None

        self.anim = None
        self.anim_offset = None
        self.anim_table = None
        self.has_anim_table = None

        self.add_props = []
        self.add_prop_offset = None
        self.num_add_props = None

        self.follow_ups = []
        self.num_follow_ups = None
        self.follow_up_offset = None

        self.battle_mode = battle_mode()

    def read_move(self, buffer, game):
        self.offset = buffer.pos()
        buffer.seek(buffer.read_uint_var())
        self.name = buffer.read_str()
        buffer.seek(self.offset)
        buffer.read_uint_var()
        if game.engine == GameEngine.DE:
            self.__DE_MOVE__(buffer, game)
        else:
            self.__OE_MOVE__(buffer, game)

        self.battle_mode.set_mode(self.type)
        self.battle_mode.set_game(game)
        self.battle_mode.convert_category_extract()
        self.battle_mode.get_mode_class()
        self.battle_mode.read_to_dict(buffer, game, self.anim_offset, self.has_anim_table)

        self.read_add_props(buffer, game)

        self.read_follow_up(buffer, game)

    def read_add_props(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_add_props):
            buffer.seek(self.add_prop_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            self.add_props.append(buffer.read_uint32())

    def read_follow_up(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_follow_ups):
            buffer.seek(self.follow_up_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_follow_up = follow_up()
            cur_follow_up.read_follow_up(buffer, game)
            self.follow_ups.append(cur_follow_up)

    def __OE_MOVE__(self, buffer, game):
        self.num_follow_ups = buffer.read_uint8()
        if game.type in [CFC_GROUPS.OE, CFC_GROUPS.OE_ISHIN]:
            self.num_add_props = buffer.read_uint8()
            self.has_anim_table = buffer.read_uint8() == 1
        else:
            self.has_anim_table = buffer.read_uint8() == 1
            self.num_add_props = buffer.read_uint8()
        self.type = buffer.read_uint8()
        self.anim_offset = buffer.read_uint32()
        self.follow_up_offset = buffer.read_uint32()
        self.add_prop_offset = buffer.read_uint32()

    def __DE_MOVE__(self, buffer, game):
        self.anim_offset = buffer.read_uint64()
        self.follow_up_offset = buffer.read_uint64()
        self.add_prop_offset = buffer.read_uint64()
        self.num_follow_ups = buffer.read_uint8()
        self.num_add_props = buffer.read_uint8()
        self.has_anim_table = buffer.read_uint8() == 1
        self.type = buffer.read_uint8()

    def build_json(self, mjson):
        mjson["Move Table"][self.name] = self.battle_mode.prop_dict

        for idx, follow_up in enumerate(self.follow_ups):
            follow_up.build_json(mjson["Move Table"][self.name], idx)

        for idx, add_prop in enumerate(self.add_props):
            idx_str = "Property " + str(idx + 1)
            mjson["Move Table"][self.name]["Properties"][idx_str]["Unk Short 1"] = add_prop & 0xFF
            mjson["Move Table"][self.name]["Properties"][idx_str]["Unk Short 2"] = (add_prop & 0xFF00) >> 8

    def parse_json(self, mjson, game):
        self.type = mjson["Move Type"]
        self.battle_mode.set_mode(self.type)
        self.battle_mode.set_game(game)
        self.battle_mode.set_dict(mjson)
        self.battle_mode.get_dict_anim()
        self.battle_mode.get_dict_mode()
        self.battle_mode.get_mode_class()
        self.battle_mode.convert_category_repack()
        self.type = self.battle_mode.Category
        self.battle_mode.prop_class.parse_strings(mjson, game)
        if "Follow Ups" in mjson:
            for midx, mfollow_up in enumerate(mjson["Follow Ups"].keys()):
                cur_follow_up = follow_up()
                cur_follow_up.name = mfollow_up
                cur_follow_up.parse_json(mjson["Follow Ups"][mfollow_up], game, midx + 1)
                self.follow_ups.append(cur_follow_up)
        if "Properties" in mjson:
            for mprop in mjson["Properties"].keys():
                prop_val = mjson["Properties"][mprop]["Unk Short 1"] + (mjson["Properties"][mprop]["Unk Short 2"] << 8)
                self.add_props.append(prop_val)


class moveset:
    def __init__(self):
        self.name = None
        self.id = None
        self.id_check = None
        self.properties = []
        self.num_properties = None
        self.properties_offset = None
        self.offset = None

    def read_moveset(self, buffer, game):
        self.offset = buffer.pos()
        moveset_table = buffer.read_uint_var()
        self.id = buffer.read_uint_var()
        if game.type not in [com.CFC_GROUPS.DE_CUR, com.CFC_GROUPS.DE_K2]:
            if self.id == 0:
                self.name = "Null"
            else:
                self.name = com.string_dict[self.id]
        buffer.seek(moveset_table)
        self.num_properties = buffer.read_uint16()
        self.id_check = buffer.read_uint16()
        if game.engine == GameEngine.DE: buffer.read_uint32()
        self.properties_offset = buffer.read_uint_var()
        self.read_properties(buffer, game)

    def read_properties(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_properties):
            buffer.seek(self.properties_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_property = cmd_property()
            cur_property.read_property(buffer, game)
            self.properties.append(cur_property)

    def get_prop_data(self, buffer):
        pass

    def build_json(self, mjson, idx):
        moveset_string = "Moveset " + str(idx + 1)
        mjson["Moveset Change Table"][moveset_string]["Moveset Name"] = self.name
        for midx, property in enumerate(self.properties):
            property.build_json(mjson["Moveset Change Table"][moveset_string], midx)

    def parse_json(self, mjson, game):
        self.name = mjson["Moveset Name"]
        if game.type not in [CFC_GROUPS.DE_CUR, CFC_GROUPS.DE_K2]: com.string_dict[self.name] = 0
        if "Conditions" in mjson:
            for midx, mproperty in enumerate(mjson["Conditions"].keys()):
                cur_property = cmd_property()
                cur_property.parse_json(mjson["Conditions"][mproperty], game, midx)
                self.properties.append(cur_property)


class follow_up:
    def __init__(self):
        self.follow_up_move = None
        self.follow_up_move_idx = None
        self.idx = None
        self.properties = []
        self.num_properties = None
        self.properties_offset = None
        self.offset = None

    def read_follow_up(self, buffer, game):
        self.offset = buffer.pos()
        self.num_properties = buffer.read_uint16()
        self.follow_up_move_idx = buffer.read_uint16()
        if game.engine == GameEngine.DE: buffer.read_uint32()
        self.properties_offset = buffer.read_uint_var()
        self.read_properties(buffer, game)

    def read_properties(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_properties):
            buffer.seek(self.properties_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_property = cmd_property()
            cur_property.read_property(buffer, game)
            self.properties.append(cur_property)

    def get_prop_data(self, buffer):
        pass

    def build_json(self, mjson, idx):
        follow_up_string = "Follow Up " + str(idx + 1)
        mjson["Follow Ups"][follow_up_string]["Follows Up to"] = self.follow_up_move
        for midx, property in enumerate(self.properties):
            property.build_json(mjson["Follow Ups"][follow_up_string], midx)

    def parse_json(self, mjson, game, idx):
        self.follow_up_move = mjson["Follows Up to"]
        self.idx = idx
        if "Conditions" in mjson:
            for midx, mproperty in enumerate(mjson["Conditions"].keys()):
                cur_property = cmd_property()
                cur_property.parse_json(mjson["Conditions"][mproperty], game, midx)
                self.properties.append(cur_property)


class cmd_property:
    def __init__(self):
        self.offset = None
        self.cmd_trigger = None
        self.buffer = None
        self.idx = None

    @staticmethod
    def split_prop_buffer(buffer, game):
        buffer_1 = BinaryReader(endianness=Endian.LITTLE)
        if game.engine == GameEngine.DE:
            buffer_1.write_uint32(buffer.read_uint32())
            buffer.seek(0x4, Whence.CUR)
            buffer_1.write_uint32(buffer.read_uint32())
            buffer.seek(-0x8, Whence.CUR)
            buffer_2 = BinaryReader()
            buffer_2.write_uint32(buffer.read_uint32())
            buffer_2.seek(0)
        else:
            buffer_1.write_uint64(buffer.read_uint64())
            buffer_2 = None
        buffer_1.seek(0)
        return buffer_1, buffer_2

    def read_property(self, buffer, game):
        buffer_1, buffer_2 = self.split_prop_buffer(buffer, game)
        cmd_trigger = battle_command()
        cmd_trigger.set_buffers(buffer_1, buffer_2)
        cmd_trigger.get_buffer_property()
        cmd_trigger.set_game(game)
        cmd_trigger.convert_category_extract()
        cmd_trigger.check_trigger()
        cmd_trigger.get_property_class()
        cmd_trigger.read_to_dict()
        self.cmd_trigger = cmd_trigger

    def build_json(self, mjson, idx):
        prop_name_string = "Condition " + str(idx + 1) + "| " + self.cmd_trigger.Display_Name
        mjson["Conditions"][prop_name_string] = self.cmd_trigger.prop_dict

    def parse_json(self, mjson, game, idx):
        self.idx = idx
        cmd_trigger = battle_command()
        cmd_trigger.set_dict(mjson)
        cmd_trigger.get_dict_property()
        cmd_trigger.set_game(game)
        cmd_trigger.check_trigger()
        cmd_trigger.get_property_class()
        cmd_trigger.convert_category_repack()
        cmd_trigger.parse_json_strings()
        self.cmd_trigger = cmd_trigger
        # cmd_trigger.write_to_buffer()
