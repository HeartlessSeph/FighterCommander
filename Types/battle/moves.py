from Types.battle.Enums.properties import *
from Utilities.bin_reader import BinaryReader
from Utilities.util import *


class CommandMode(IntEnum):
    invalid = 0
    Ready = 1
    Attack = 2
    Change = 3
    Sync = 4
    Move = 5
    Hact = 6
    Down = 7
    Weapon = 8
    Action = 9
    Provoke = 10
    Wall = 11
    Piyori = 12
    SyncF = 13
    SyncB = 14
    DownHard = 15
    Stand = 16
    CustomAction = 17
    PickAttack = 18
    OneShotGuard = 19
    TougijoSkillAttack = 20
    TougijoSkillProvoke = 21


CommandModeNames = \
    {
        "invalid": "invalid",
        "Ready": "Ready",
        "Attack": "Attack",
        "Change": "Change",
        "Sync": "Sync",
        "Move": "Move",
        "Hact": "HAct",
        "Down": "Down",
        "Weapon": "Weapon",
        "Action": "Action",
        "Provoke": "Provoke",
        "Wall": "Wall",
        "Piyori": "Stun",
        "SyncF": "Sync F",
        "SyncB": "Sync B",
        "DownHard": "Down Hard",
        "Stand": "Stand",
        "CustomAction": "Custom Action",
        "PickAttack": "Pick Attack",
        "OneShotGuard": "One Shot Guard",
        "TougijoSkillAttack": "Coliseum Skill Attack",
        "TougijoSkillProvoke": "Coliseum Skill Provoke"
    }


class battle_mode:
    def __init__(self):
        self.Category = 0
        self.Trigger = None
        self.Display_Name = ""
        self.offset = 0
        self.Anim_Value = None
        self.Anim_Table_Offset = None
        self.Has_Anim_Table = None
        self.game = None
        self.prop_class = generic_prop()
        self.prop_dict = {}

    def __check_trigger__(self, category):
        if category in CommandMode._value2member_map_:
            self.Trigger = CommandMode(category)
            self.Display_Name = CommandModeNames[self.Trigger.name]
        else:
            self.Display_Name = "Unknown Type (" + str(category) + ")"

    def __check_dict_props__(self):
        pass

    def set_mode(self, mode):
        self.Category = mode

    def set_dict(self, prop_dict):
        self.prop_dict = prop_dict

    def get_dict_mode(self):
        self.Category = self.prop_dict["Move Type"]

    def get_buffer_property(self):
        self.Prop_Buffer.seek(0x4)
        self.Category = self.Prop_Buffer.read_uint32()
        self.Prop_Buffer.seek(0)

    def check_trigger(self):
        self.__check_trigger__(self.Category)

    def get_dict_anim(self):
        if "Animation Used" in self.prop_dict:
            self.Anim_Value = self.prop_dict["Animation Used"]

    def write_to_buffer(self):
        self.Prop_Buffer, self.Prop_Buffer_2 = self.prop_class.write_property(self.prop_dict, self.game)

    def read_to_dict(self, buffer, game, anim, anim_bool):
        temp_dict = tree()
        temp_dict["Move Type"] = self.Category
        prop_dict = self.prop_class.read_property(buffer, game, anim, anim_bool)
        self.prop_dict = merge_two_dicts(temp_dict, prop_dict)

    def convert_category_extract(self):
        if self.game.engine == com.GameEngine.OE or self.game.type == com.CFC_GROUPS.DE_DEMO:
            self.Category += 1

    def convert_category_repack(self):
        if self.game.engine == com.GameEngine.OE or self.game.type == com.CFC_GROUPS.DE_DEMO:
            self.Category -= 1

    def get_mode_class(self):
        if self.Category in mode_classes:
            self.prop_class = mode_classes[self.Category]

    def set_game(self, game):
        self.game = game


class generic_prop:
    @staticmethod
    def write_property(mjson, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if "Animation Used" in mjson:
            buffer.write_uint_var(com.string_dict[mjson["Animation Used"]])
        if "Animation Table" in mjson:
            for anim in mjson["Animation Table"].keys():
                cur_anim = mjson["Animation Table"][anim]["Animation Used"]
                buffer.write_uint_var(com.string_dict[cur_anim])
                buffer.write_uint8(mjson["Animation Table"][anim]["Unknown Byte 1"])
                buffer.write_uint8(mjson["Animation Table"][anim]["Unknown Byte 2"])
                buffer.write_uint8(mjson["Animation Table"][anim]["Unknown Byte 3"])
                buffer.write_uint8(mjson["Animation Table"][anim]["Unknown Byte 4"])
                if game.engine == com.GameEngine.DE:
                    if len(com.motion_gmt) > 0:
                        if cur_anim in com.motion_gmt:
                            buffer.write_uint32(com.motion_gmt[mjson["Animation Table"][anim]["Animation Used"]])
                        else:
                            print_warning(f"Anim_table entry {cur_anim} not present in motion_gmt! Game may crash when using this anim!")
                            buffer.write_uint32(0)
                    else:
                        buffer.write_uint32(mjson["Animation Table"][anim]["Motion ID"])
        return buffer

    @staticmethod
    def read_property(buffer, game, a_val, a_bool):
        buffer_pos = buffer.pos()
        move_dict = {}
        if not a_bool:
            move_dict["Animation Used"] = com.string_dict[a_val]
        else:
            move_dict["Animation Table"] = {}
            buffer.seek(a_val)
            if game.engine == com.GameEngine.OE:
                unk_val = buffer.read_uint8()
                num_anims = buffer.read_uint8()
                buffer.read_uint16()
                anim_table_offset = buffer.read_uint32()
            else:
                anim_table_offset = buffer.read_uint64()
                unk_val = buffer.read_uint8()
                num_anims = buffer.read_uint8()
            offsetter = 4 * game.engine
            for i in range(num_anims):
                anim_idx = "Animation " + str(i + 1)
                move_dict["Animation Table"][anim_idx] = {}

                buffer.seek(anim_table_offset + (i * offsetter))
                buffer.seek(buffer.read_uint_var())
                anim_offset = buffer.read_uint_var()
                byte_vals = buffer.read_bytes(4)
                move_dict["Animation Table"][anim_idx]["Animation Used"] = com.string_dict[anim_offset]
                for idx, byte_val in enumerate(byte_vals):
                    move_dict["Animation Table"][anim_idx]["Unknown Byte " + str(idx + 1)] = int(byte_val)
                if game.engine == com.GameEngine.DE and len(com.motion_gmt) == 0:
                    move_dict["Animation Table"][anim_idx]["Motion ID"] = buffer.read_uint32()
        return move_dict


    @staticmethod
    def idx_to_name(mdict, idx_list):
        pass

    @staticmethod
    def parse_strings(mjson, game):
        if "Animation Used" in mjson:
            com.string_dict[mjson["Animation Used"]] = 0
        if "Animation Table" in mjson:
            for anim in mjson["Animation Table"].keys():
                com.string_dict[mjson["Animation Table"][anim]["Animation Used"]] = 0


class Change(generic_prop):
    @staticmethod
    def write_property(mjson, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        move_to_play = mjson["Move to Play in Set"]
        command_set = mjson["Command Set"]

        a_val = move_to_play + (command_set << 16)

        buffer.write_uint32(a_val)
        if game.engine == com.GameEngine.DE:
            if game.type not in [com.CFC_GROUPS.DE_DEMO, com.CFC_GROUPS.DE_Y6] and command_set != 65535:
                if command_set in com.set_id_order:
                    buffer.write_uint32(com.set_id_order[command_set])
                else:
                    print_warning(f"{command_set} ID is not in this cfc. This command set may crash if this move is used.")
                    buffer.write_uint32(0)
            else:
                buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer, game, a_val, a_bool):
        move_dict = {}
        if com.args.cset_id:
            move_dict["Command Set"] = (a_val & 0xFFFF00000000) >> 32
        else:
            move_dict["Command Set"] = (a_val & 0xFFFF0000) >> 16
        move_dict["Move to Play in Set"] = a_val & 0xFFFF
        return move_dict

    @staticmethod
    def idx_to_name(mdict, idx_dict):
        set_idx = mdict["Command Set"]
        move_idx = mdict["Move to Play in Set"]
        if set_idx in idx_dict:
            mdict["Command Set"] = idx_dict[set_idx]["Name"]
            mdict["Move to Play in Set"] = idx_dict[set_idx]["Move"][move_idx]


class Sync(Change):
    pass


class CustomAction(generic_prop):
    @staticmethod
    def write_property(mjson, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint_var(mjson["Unknown Value"])

        return buffer

    @staticmethod
    def read_property(buffer, game, a_val, a_bool):
        move_dict = {}
        move_dict["Unknown Value"] = a_val
        return move_dict


mode_classes = {prop.value: globals()[prop.name] for prop in CommandMode if prop.name in globals()}
