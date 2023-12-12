from binary_reader import Whence, BinaryReader, Endian
import Structure.Enums.common as com
from Structure.Enums.common import CFC_GROUPS, GameEngine, endianess
from Types.battle.properties import battle_command
from Types.battle.moves import battle_mode
from Utilities.util import tree
import cutie
import re




class CHP:
    def __init__(self):
        self.name = ""
        self.version = None
        self.game = None
        self.header = header()
        self.hact_set_table = hact_set_table()
        self.filesize = None

    def read_file(self, buffer):
        buffer.set_engine = self.game.engine
        self.filesize = self.header.read_header(buffer)
        com.read_string_table(buffer, com.string_dict)
        buffer.seek(self.filesize)
        self.hact_set_table.read_header(buffer, self.game)
        self.hact_set_table.read_table(buffer, self.game)

    def set_game(self, game):
        self.game = game

    def set_name(self, string):
        self.name = string

    def get_name(self):
        return self.name

    def build_jsons(self):
        self.hact_set_table.build_json()


class header:
    def __init__(self):
        self.version = None
        self.endian = None
        self.magic = "CHPI"

    def read_header(self, buffer):
        magic = buffer.read_str(4)
        if magic != self.magic:
            raise Exception("File is not a CHP File.")
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


class hact_set_table:
    def __init__(self):
        self.hact_sets = []
        self.offset = None
        self.num_sets = None
        self.chp_jsons = []

    def read_header(self, buffer, game):
        buffer.seek(-0x08 * game.engine, Whence.CUR)
        num_sets = buffer.read_uint_var()
        table_pointer = buffer.read_uint_var()
        self.offset = table_pointer
        self.num_sets = num_sets
        buffer.seek(table_pointer)

    def read_table(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_sets):
            buffer.seek(self.offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_set = hact_set()
            cur_set.read_file(buffer, game)
            self.hact_sets.append(cur_set)

    def update_num_sets(self):
        self.num_sets = len(self.hact_sets)

    def build_json(self):
        for c_set in self.hact_sets:
            chp_json = tree()
            c_set.build_json(chp_json)
            self.chp_jsons.append(chp_json)

    def parse_jsons(self, json, game):
        for cset_json in com.file_jsons.keys():
            cur_set = hact_set()
            cur_set.name = cset_json
            com.string_dict[cset_json] = 0
            cur_set.parse_json(com.file_jsons[cset_json], game)
            self.hact_sets.append(cur_set)


class hact_set:
    def __init__(self):
        self.name = None
        self.id = None
        self.sub = None
        self.offset = None
        self.targets = []
        self.num_targets = None
        self.target_table_offset = None
        self.special_effect = None
        self.comp_flag = None
        self.x = None
        self.y = None
        self.z = None
        self.rot = None
        self.unk_int_3 = None
        self.unk_int_4 = None
        self.unk_int_5 = None
        self.hact_base = None
        self.play_area_type = None
        self.unk_target_val = None
        self.condition = None

    def read_file(self, buffer, game):
        self.offset = buffer.pos()
        self.read_set(buffer, game)

        #buffer.seek(self.offset)
        #self.read_set(buffer, game)

    def read_set(self, buffer, game):
        if game.type == com.CFC_GROUPS.DE_CUR:
            set_ID = buffer.read_uint32()
            sub_number = buffer.read_uint32()
            self.id = set_ID
            self.sub = sub_number
            name_append = f"#{sub_number}" if sub_number > 0 else ""
            if len(com.talk_param) > 0:
                self.name = f"{com.talk_param[set_ID]}{name_append}"
            else:
                self.name = f"{set_ID}{name_append}"
        else:
            self.name = com.string_dict[buffer.read_uint_var()]

        if game.engine == GameEngine.OE:
            self.__OE_SET__(buffer, game)
        else:
            self.__DE__SET__(buffer, game)

        print(f"Reading set: {self.name}")
        self.read_targets(buffer, game)

    def __OE_SET__(self, buffer, game):
        self.num_targets = buffer.read_uint32()
        self.target_table_offset = buffer.read_uint32()
        self.unk_target_val = buffer.read_uint32()
        self.comp_flag = com.string_dict[buffer.read_uint32()]
        self.x = buffer.read_float()
        self.y = buffer.read_float()
        self.z = buffer.read_float()
        if game.type != com.CFC_GROUPS.OE_Y5:
            self.condition = com.string_dict[buffer.read_uint32()]
            self.unk_int_3 = buffer.read_uint32()
            self.unk_int_4 = buffer.read_uint32()
            self.unk_int_5 = buffer.read_uint32()

    def __DE__SET__(self, buffer, game):
        self.target_table_offset = buffer.read_uint_var()

        if game.type == com.CFC_GROUPS.DE_CUR:
            self.special_effect = com.string_dict[buffer.read_uint_var()]
            self.comp_flag = buffer.read_uint32()
            self.num_targets = buffer.read_uint32()
            self.play_area_type = buffer.read_uint32()
        else:
            if game.type in [com.CFC_GROUPS.DE_DEMO, com.CFC_GROUPS.DE_Y6]:
                self.id = com.string_dict[buffer.read_uint_var()]
            else:
                self.play_area_type = buffer.read_uint32()
                self.id = buffer.read_uint32()
            self.comp_flag = com.string_dict[buffer.read_uint_var()]
            self.num_targets = buffer.read_uint32()

        self.x = buffer.read_float()
        self.y = buffer.read_float()
        self.z = buffer.read_float()
        self.rot = buffer.read_float()

        if game.type != com.CFC_GROUPS.DE_CUR:
            self.unk_target_val = buffer.read_float()
            self.hact_base = com.string_dict[buffer.read_uint32()]


    def read_targets(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_targets):
            buffer.seek(self.target_table_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_target = target()
            cur_target.read_target(buffer, game)
            self.targets.append(cur_target)

    def build_json(self, mjson):
        if com.cur_game.engine == com.GameEngine.DE:
            self.__DE_JSON__(mjson)
        else:
            self.__OE_JSON__(mjson)

        for midx, target in enumerate(self.targets):
            target.build_json(mjson["Targets"], midx)

    def __OE_JSON__(self, mjson):
        mjson["Unknown Target Value"] = self.unk_target_val
        mjson["Completion Name"] = self.comp_flag
        mjson["X?"] = self.x
        mjson["Y?"] = self.y
        mjson["Z?"] = self.z
        if com.cur_game.type != com.CFC_GROUPS.OE_Y5:
            mjson["Condition Name"] = self.condition
            mjson["Unknown Int 3"] = self.unk_int_3
            mjson["Unknown Int 4"] = self.unk_int_4
            # Below should always be 0
            # mjson["Unknown Int 5"] = self.unk_int_5

    def __DE_JSON__(self, mjson):
        if com.cur_game.type == com.CFC_GROUPS.DE_K2:
            mjson["Talk_Param ID"] = self.id
        elif com.cur_game.type in [com.CFC_GROUPS.DE_Y6, com.CFC_GROUPS.DE_Y6]:
            mjson["HAct ID"] = self.id
        if com.cur_game.type == com.CFC_GROUPS.DE_CUR:
            mjson["Special Effect"] = self.special_effect
        mjson["Completion Flag"] = self.comp_flag
        if com.cur_game.type not in [com.CFC_GROUPS.DE_Y6, com.CFC_GROUPS.DE_Y6]:
            mjson["Play Area Type"] = self.play_area_type
        mjson["X"] = self.x
        mjson["Y"] = self.y
        mjson["Z"] = self.z
        mjson["Rotation"] = self.rot
        if com.cur_game.type != com.CFC_GROUPS.DE_CUR:
            mjson["Unk Float"] = self.unk_target_val
            mjson["Base HAct"] = self.hact_base

    def parse_json(self, mjson, game):
        self.id = com.set_id_name[self.name]
        if game.engine == com.GameEngine.OE: com.string_dict[self.id] = 0

        if "Targets" in mjson:
            for mtarget in mjson["Targets"].keys():
                cur_target = target()
                cur_target.name = mtarget
                com.string_dict[target] = 0
                cur_target.parse_json(mjson["Targets"][mtarget], game)
                self.targets.append(cur_target)


class target:
    def __init__(self):
        self.name = None
        self.offset = None
        self.type = None
        self.end_motion_id = None
        self.modify_flag = None

        self.properties = []
        self.num_properties = None
        self.properties_offset = None
        self.offset = None
        self.unk_target = None
        self.unk_target_int = None

    def read_target(self, buffer, game):
        self.offset = buffer.pos()
        self.name = com.string_dict[buffer.read_uint_var()]
        if game.engine == com.GameEngine.DE:
            self.properties_offset = buffer.read_uint_var()
            self.type = buffer.read_uint32()
            self.end_motion_id = buffer.read_uint32()
            self.num_properties = buffer.read_uint32()
            self.modify_flag = buffer.read_uint32()
        else:
            self.type = buffer.read_uint32()
            self.unk_target = com.string_dict[buffer.read_uint32()]
            self.num_properties = buffer.read_uint32()
            self.properties_offset = buffer.read_uint32()
            self.unk_target_int = buffer.read_uint32()
        self.read_properties(buffer, game)

    def read_properties(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_properties):
            buffer.seek(self.properties_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_property = cmd_property()
            cur_property.read_property(buffer, game)
            self.properties.append(cur_property)

    def build_json(self, mjson, idx):
        mstr = f"Target {idx + 1}"
        mjson[mstr]["Target Name"] = self.name
        mjson[mstr]["Target Type"] = self.type
        if com.cur_game.engine == com.GameEngine.DE:
            mjson[mstr]["End Motion ID"] = self.end_motion_id
            mjson[mstr]["Modify Flag"] = self.modify_flag

        for midx, property in enumerate(self.properties):
            property.build_json(mjson[mstr], midx)

    def parse_json(self, mjson, game):
        self.type = mjson["Target Type"]
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
