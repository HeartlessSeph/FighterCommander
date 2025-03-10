from enum import Enum, IntEnum, Flag
from typing import List
import Structure.Enums.common as com
from Structure.Enums.common import CFC_GROUPS, GameEngine
from Types.battle.ladpih.Enums.conditions import *
from binary_reader import Whence, Endian
from Utilities.bin_reader import BinaryReader
from Utilities.util import map_enum_names_to_bits, get_set_bits_as_enum, merge_two_dicts
from Utilities.util import val_to_enum, enum_to_val


class CommandTrigger(IntEnum):
    invalid = 0,
    ButtonPush = 1,
    ButtonNow = 2,
    ButtonRenda = 3,
    ButtonCommand = 4,
    MotionShift = 5,
    MotionEnd = 6,
    FighterStatus = 7,
    TargetStatus = 8,
    TargetChange = 9,
    Custom = 10,
    AttackHit = 11,
    Outer = 12,
    Lever = 13,
    Weapon = 14,
    WeaponID = 15,
    HaveItem = 16,
    HAct = 17,
    HActNotUsed = 18,
    DistLimit = 19,
    AngLimit = 20,
    Range = 21,
    Height = 22,
    LeverAng = 23,
    Tame = 24,
    ChangeAuth = 25,
    DirParam = 26,
    Skill = 27,
    CtrlType = 28,
    PlayerID = 29,
    AttackFrame = 30,
    Pickup = 31,
    ComboNum = 32,
    SyncRole = 33,
    ComboSpeed = 34,
    BattleStyle = 35,
    HeatLevel = 36,
    HeightParam = 37,
    MotionID = 38,
    Stun = 39,
    PushFighter = 40,
    RangeID = 41,
    ChargeTime = 42,
    ChargeLevel = 43,
    ChargeType = 44,
    PlayerSkill = 45,
    ReactionType = 46,
    ItemBuff = 47,
    DistArea = 48,
    SkillSuccess = 49,
    SkillFailed = 50,
    SyncNode = 51,
    WallHit = 52,
    AiCustomEventFlag = 53,
    AiOpenActionFlag = 54,
    Debug = 55,
    LCASuccess = 56,
    SpeedUpBuff = 57,
    HeightScale = 58,
    PickupNarrow = 59,
    DamageHit = 60,
    DefenceSuccess = 61,
    BoxSkill = 62,
    BoxDownValue = 63,
    TougijoSkill = 64,
    GadgetAvailable = 65,
    GadgetLv = 66,
    ForceDisable = 67,
    WeaponL = 68,
    WeaponR = 69,
    CommandLoopNum = 70


CommandTriggerNames = \
    {
        "invalid": "invalid",
        "ButtonPush": "Button Press",
        "ButtonNow": "Button Hold",
        "ButtonRenda": "Button Renda",
        "ButtonCommand": "Button Press (Buffered Input)",
        "MotionShift": "Follow Up Window Start",
        "MotionEnd": "Follow Up Window End",
        "FighterStatus": "Fighter Status",
        "TargetStatus": "Target Status",
        "TargetChange": "Target Change",
        "Custom": "Custom",
        "AttackHit": "Follow Up On Hit",
        "Outer": "Outer",
        "Lever": "Analog Deadzone",
        "Weapon": "Weapon Category",
        "WeaponID": "Weapon ID",
        "HaveItem": "Have Item",
        "HAct": "Heat Action",
        "HActNotUsed": "Hact not used",
        "DistLimit": "Distance Limit",
        "AngLimit": "Angle Limit",
        "Range": "Range",
        "Height": "Height",
        "LeverAng": "Analog Direction",
        "Tame": "Charge",
        "ChangeAuth": "Change Auth",
        "DirParam": "Quickstep",
        "Skill": "Skill Required",
        "CtrlType": "Ctrl Type",
        "PlayerID": "Player ID",
        "AttackFrame": "Timing",
        "Pickup": "Pickup",
        "ComboNum": "Combo Number",
        "SyncRole": "Sync Role",
        "ComboSpeed": "Combo Speed",
        "BattleStyle": "Battle Style",
        "HeatLevel": "Heat Level",
        "HeightParam": "Height Param",
        "MotionID": "Motion ID",
        "Stun": "Stun",
        "PushFighter": "Push Fighter",
        "RangeID": "Range ID",
        "ChargeTime": "Charge Time",
        "ChargeLevel": "Charge Level",
        "ChargeType": "Charge Type",
        "PlayerSkill": "Player Skill",
        "ReactionType": "Reaction Type",
        "ItemBuff": "Item Buff",
        "DistArea": "Dist Area",
        "SkillSuccess": "Skill Success",
        "SkillFailed": "Skill Failed",
        "SyncNode": "Sync Node",
        "WallHit": "Wall Hit",
        "AiCustomEventFlag": "Ai Custom Event Flag",
        "AiOpenActionFlag": "Ai Open Action Flag",
        "Debug": "Debug",
        "LCASuccess": "LCA Success",
        "SpeedBuff": "Speed Buff",
        "HeightScale": "Height Scale",
        "PickupNarrow" : "PickupNarrow",
        "DamageHit" : "DamageHit",
        "DefenceSuccess" : "DefenceSuccess",
        "BoxSkill" : "BoxSkill",
        "BoxDownValue" : "BoxDownValue",
        "TougijoSkill" : "TougijoSkill",
        "GadgetAvailable" : "GadgetAvailable",
        "GadgetLv" : "GadgetLv",
        "ForceDisable" : "ForceDisable",
        "WeaponL" : "WeaponL",
        "WeaponR" : "WeaponR",
        "CommandLoopNum" : "CommandLoopNum"
    }


class battle_command:
    def __init__(self):
        self.Category = None
        self.Trigger = None
        self.Display_Name = ""
        self.offset = 0
        self.Prop_Buffer = None
        self.Prop_Buffer_2 = None
        self.game = None
        self.prop_class = generic_prop()
        self.prop_dict = None

    def __check_trigger__(self, category):
        if category in CommandTrigger._value2member_map_:
            self.Trigger = CommandTrigger(category)
            if self.Trigger.name in CommandTriggerNames:
                self.Display_Name = CommandTriggerNames[self.Trigger.name]
            else:
                self.Display_Name = self.Trigger.Name
        else:
            self.Display_Name = "Unknown Type (" + str(category) + ")"

    def __check_dict_props__(self):
        pass

    def set_buffers(self, prop_buffer, prop_buffer_2):
        self.Prop_Buffer = prop_buffer
        self.Prop_Buffer_2 = prop_buffer_2

    def set_dict(self, prop_dict):
        self.prop_dict = prop_dict

    def get_buffer_property(self):
        self.Prop_Buffer.seek(0x4)
        self.Category = self.Prop_Buffer.read_uint32()
        self.Prop_Buffer.seek(0)

    def get_dict_property(self):
        self.Category = self.prop_dict["Property Type"]

    def check_trigger(self):
        self.__check_trigger__(self.Category)

    def write_to_buffer(self):
        cur_buffer = self.prop_class.write_property(self.prop_dict, self.game)
        cur_buffer.write_uint_var(self.Category)
        cur_buffer.seek(0)
        self.Prop_Buffer = cur_buffer

    def parse_json_strings(self):
        self.prop_class.parse_strings(self.prop_dict, self.game)

    def read_to_dict(self):
        temp_dict = {"Property Type": self.Category}
        prop_dict = self.prop_class.read_property(self.Prop_Buffer, self.Prop_Buffer_2, self.game)
        self.prop_dict = merge_two_dicts(temp_dict, prop_dict)

    def convert_category_extract(self):
        if self.game.engine == com.GameEngine.OE or self.game.type == com.CFC_GROUPS.DE_DEMO:
            self.Category += 1

    def convert_category_repack(self):
        if self.game.engine == com.GameEngine.OE or self.game.type == com.CFC_GROUPS.DE_DEMO:
            self.Category -= 1

    def get_property_class(self):
        if self.Category in prop_classes:
            self.prop_class = prop_classes[self.Category]

    def set_game(self, game):
        self.game = game


class generic_prop:
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint8(prop_dict["Unk Byte 1"])
        buffer.write_uint8(prop_dict["Unk Byte 2"])
        buffer.write_uint8(prop_dict["Unk Byte 3"])
        buffer.write_uint8(prop_dict["Unk Byte 4"])
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Unk Byte 1"] = buffer1.read_uint8()
        prop_dict["Unk Byte 2"] = buffer1.read_uint8()
        prop_dict["Unk Byte 3"] = buffer1.read_uint8()
        prop_dict["Unk Byte 4"] = buffer1.read_uint8()
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        pass


class ButtonPush(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        button_val = map_enum_names_to_bits(prop_dict["Button Press"], ButtonsDE)

        conditionals = map_enum_names_to_bits(prop_dict["Conditionals"], Conditionals)
        additional_conditional = prop_dict["Additional Conditional"]

        unk_val1 = prop_dict["Unk Value 1"]
        unk_val2 = prop_dict["Unk Value 2"]
        unk_val3 = prop_dict["Unk Value 3"]
        unk_val4 = prop_dict["Unk Value 4"]

        buffer.write_uint16(button_val)
        buffer.write_uint8(additional_conditional)
        buffer.write_uint8(conditionals)
        buffer.write_uint8(unk_val1)
        buffer.write_uint8(unk_val2)
        buffer.write_uint8(unk_val3)
        buffer.write_uint8(unk_val4)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        buffer2.seek(0)
        prop_dict = {}
        ButtonPress = buffer1.read_uint8() + (buffer1.read_uint8() << 0x8)
        AdditionalConditional = buffer1.read_uint8()
        conditional = buffer1.read_uint8()
        prop_dict["Button Press"] = get_set_bits_as_enum(ButtonPress, ButtonsDE)
        prop_dict["Conditionals"] = get_set_bits_as_enum(conditional, Conditionals)
        prop_dict["Additional Conditional"] = AdditionalConditional
        prop_dict["Unk Value 1"] = buffer2.read_uint8()
        prop_dict["Unk Value 2"] = buffer2.read_uint8()
        prop_dict["Unk Value 3"] = buffer2.read_uint8()
        prop_dict["Unk Value 4"] = buffer2.read_uint8()
        return prop_dict


class ButtonNow(ButtonPush):
    pass


class ButtonCommand(ButtonPush):
    pass


class ButtonRenda(ButtonPush):
    pass


class FighterStatus(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)
        try:
            state = enum_to_val(prop_dict["State Type"], Status)
        except:
            state = 0
        conditional = map_enum_names_to_bits(prop_dict["Conditionals"], Conditionals)

        buffer.write_uint8(state)
        buffer.write_uint16(0)
        buffer.write_uint8(conditional)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        state = buffer1.read_uint8()
        buffer1.read_uint16()
        conditional = buffer1.read_uint8()
        prop_dict["State Type"] = val_to_enum(state, Status)
        prop_dict["Conditionals"] = get_set_bits_as_enum(conditional, Conditionals)
        return prop_dict


class TargetStatus(FighterStatus):
    pass


class Weapon(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)
        weapon_category = prop_dict["Weapon Category ID"]
        conditional = map_enum_names_to_bits(prop_dict["Conditionals"], Conditionals)
        bitmask = prop_dict["Bitmask Byte"]

        buffer.write_uint16(weapon_category)
        buffer.write_uint8(bitmask)
        buffer.write_uint8(conditional)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        weapon_category = buffer1.read_uint16()
        bitmask = buffer1.read_uint8()
        conditional = buffer1.read_uint8()

        prop_dict["Weapon Category ID"] = weapon_category
        prop_dict["Bitmask Byte"] = bitmask
        prop_dict["Conditionals"] = get_set_bits_as_enum(conditional, Conditionals)
        return prop_dict


class Pickup(Weapon):
    pass


class DistLimit(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)
        buffer.write_uint16(prop_dict["Enemy Distance"])
        buffer.write_uint8(0)
        buffer.write_uint8(prop_dict["Unk Byte 4"])
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Enemy Distance"] = buffer1.read_uint16()
        buffer1.read_uint8()
        prop_dict["Unk Byte 4"] = buffer1.read_uint8()
        return prop_dict


class TargetChange(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint8(prop_dict["Target"])
        buffer.write_uint8(prop_dict["Unk Byte 2"])
        buffer.write_uint8(prop_dict["Target Position"])
        buffer.write_uint8(prop_dict["Unk Byte 4"])
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Target"] = buffer1.read_uint8()
        prop_dict["Unk Byte 2"] = buffer1.read_uint8()
        prop_dict["Target Position"] = buffer1.read_uint8()
        prop_dict["Unk Byte 4"] = buffer1.read_uint8()
        return prop_dict


class WeaponID(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if game.engine == com.GameEngine.OE:
            weapon_id = com.string_dict[prop_dict["Weapon ID"]]
        elif game.engine == GameEngine.DE:
            weapon_id = prop_dict["Weapon ID"]

        buffer.write_uint32(weapon_id)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        weapon_id = buffer1.read_uint32()
        if game.engine == com.GameEngine.OE:
            prop_dict["Weapon ID"] = com.string_dict[weapon_id]
        elif game.engine == GameEngine.DE:
            prop_dict["Weapon ID"] = weapon_id
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        if game.engine == com.GameEngine.OE:
            com.string_dict[prop_dict["Weapon ID"]] = 0


class LeverAng(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint8(prop_dict["Unk Byte"])
        buffer.write_uint8(prop_dict["Analog Direction"])
        buffer.write_uint8(0)
        buffer.write_uint8(prop_dict["Conditions"])
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Unk Byte"] = buffer1.read_uint8()
        prop_dict["Analog Direction"] = buffer1.read_uint8()
        buffer1.read_uint8()
        prop_dict["Conditions"] = buffer1.read_uint8()
        return prop_dict


class DirParam(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)
        sway_direction = enum_to_val(prop_dict["Direction"], Directions)

        buffer.write_uint8(sway_direction)
        buffer.write_uint16(0)
        buffer.write_uint8(0)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Direction"] = val_to_enum(buffer1.read_uint8(), Directions)
        return prop_dict


class Skill(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if game.engine == GameEngine.OE:
            buffer.write_uint32(com.string_dict[prop_dict["Skill ID"]])
        elif game.engine == GameEngine.DE:
            buffer.write_uint32(prop_dict["Skill ID"])

        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        skill_id = buffer1.read_uint32()
        if game.engine == GameEngine.OE:
            prop_dict["Skill ID"] = com.string_dict[skill_id]
        elif game.engine == GameEngine.DE:
            prop_dict["Skill ID"] = skill_id
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        if game.engine == com.GameEngine.OE:
            com.string_dict[prop_dict["Skill ID"]] = 0


class HaveItem(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if game.engine == GameEngine.OE:
            buffer.write_uint32(com.string_dict[prop_dict["Item ID"]])
        elif game.engine == GameEngine.DE:
            buffer.write_uint32(prop_dict["Item ID"])

        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        item_id = buffer1.read_uint32()
        if game.engine == GameEngine.OE:
            prop_dict["Item ID"] = com.string_dict[item_id]
        elif game.engine == GameEngine.DE:
            prop_dict["Item ID"] = item_id
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        if game.engine == com.GameEngine.OE:
            com.string_dict[prop_dict["Item ID"]] = 0


class AttackFrame(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint32(prop_dict["Timing"])
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {"Timing": buffer1.read_uint32()}
        return prop_dict


class MotionID(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if game.engine == GameEngine.OE:
            buffer.write_uint32(com.string_dict[prop_dict["Motion ID"]])
        elif game.engine == GameEngine.DE:
            conditional = map_enum_names_to_bits(prop_dict["Conditionals"], Conditionals)
            motion_id = prop_dict["Motion ID"]
            if str(motion_id).isdigit():
                motion_id = (conditional << 24) + motion_id
            elif len(com.motion_gmt) != 0:
                motion_id = (conditional << 24) + com.motion_gmt[motion_id]
            else:
                raise Exception(f"No motion_json supplied for {motion_id}. Please re-run with -gmt option.")
            buffer.write_uint32(motion_id)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        motion_id = buffer1.read_uint32()
        if game.engine == GameEngine.OE:
            prop_dict["Motion ID"] = com.string_dict[motion_id]
        elif game.engine == GameEngine.DE:
            conditional = (motion_id & 0xFF000000) >> 24
            motion_id = motion_id & 0xFFFFFF
            if len(com.motion_gmt) != 0:
                prop_dict["Motion ID"] = com.motion_gmt[motion_id]
            else:
                prop_dict["Motion ID"] = motion_id
            prop_dict["Conditionals"] = get_set_bits_as_enum(conditional, Conditionals)
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        if game.engine == com.GameEngine.OE:
            com.string_dict[prop_dict["Motion ID"]] = 0


class Custom(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if not isinstance(prop_dict["String"], int):
            buffer.write_uint32(com.string_dict[prop_dict["String"]])
        else:
            buffer.write_uint32(prop_dict["String"])

        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        string_pointer = buffer1.read_uint32()
        if string_pointer in com.string_dict:
            prop_dict = {"String": com.string_dict[string_pointer]}
        else:
            print(f"Property string (offset {str(hex(string_pointer))}) not present in string list.")
            prop_dict = {"String": string_pointer}
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        if not isinstance(prop_dict["String"], int):
            com.string_dict[prop_dict["String"]] = 0


class GearLevel(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint8(prop_dict["Gear Level"])
        buffer.write_uint16(0)
        buffer.write_uint8(0)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Gear Level"] = buffer1.read_uint8()
        return prop_dict


class RangeID(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        buffer.write_uint8(prop_dict["Unk Byte 1"])
        buffer.write_uint8(prop_dict["Unk Byte 2"])
        buffer.write_uint8(prop_dict["Unk Byte 3"])
        buffer.write_uint8(prop_dict["Unk Byte 4"])
        if game.engine == com.GameEngine.DE:
            buffer.write_uint8(prop_dict["Unk Byte 5"])
            buffer.write_uint8(prop_dict["Unk Byte 6"])
            buffer.write_uint8(prop_dict["Unk Byte 7"])
            buffer.write_uint8(prop_dict["Unk Byte 8"])
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        prop_dict["Unk Byte 1"] = buffer1.read_uint8()
        prop_dict["Unk Byte 2"] = buffer1.read_uint8()
        prop_dict["Unk Byte 3"] = buffer1.read_uint8()
        prop_dict["Unk Byte 4"] = buffer1.read_uint8()
        if game.engine == GameEngine.DE:
            buffer2.seek(0)
            prop_dict["Unk Byte 5"] = buffer2.read_uint8()
            prop_dict["Unk Byte 6"] = buffer2.read_uint8()
            prop_dict["Unk Byte 7"] = buffer2.read_uint8()
            prop_dict["Unk Byte 8"] = buffer2.read_uint8()
        return prop_dict


class HAct(generic_prop):
    @staticmethod
    def write_property(prop_dict, game):
        buffer = BinaryReader()
        buffer.set_engine(game.engine)

        if game.type != CFC_GROUPS.DE_CUR:
            buffer.write_uint32(com.string_dict[prop_dict["HAct ID"]])
        else:
            if "HAct Prop" in prop_dict:
                unk_data = prop_dict["HAct Prop"]
            else:
                unk_data = 0
            hact_id = prop_dict["HAct ID"]
            if str(hact_id).isdigit():
                hact_id = (unk_data << 24) + hact_id
            elif len(com.talk_param) != 0:
                hact_id = (unk_data << 24) + com.talk_param[hact_id]
            else:
                raise Exception(f"No talk_param supplied for {hact_id}. Please re-run with -chp option.")
            buffer.write_uint32(hact_id)
        if game.engine == com.GameEngine.DE: buffer.write_uint32(0)
        return buffer

    @staticmethod
    def read_property(buffer1, buffer2, game):
        buffer1.seek(0)
        prop_dict = {}
        hact_id = buffer1.read_uint32()
        if game.type == CFC_GROUPS.DE_CUR:
            unk_data = (hact_id & 0xFF000000) >> 24
            hact_id = hact_id & 0xFFFFFF
            if len(com.talk_param) != 0:
                hact_id = com.talk_param[hact_id]
            prop_dict["HAct ID"] = hact_id
            prop_dict["HAct Prop"] = unk_data
        else:
            prop_dict["HAct ID"] = com.string_dict[hact_id]
        return prop_dict

    @staticmethod
    def parse_strings(prop_dict, game):
        if game.type != CFC_GROUPS.DE_CUR:
            com.string_dict[prop_dict["HAct ID"]] = 0


class HActNotUsed(HAct):
    pass


prop_classes = {prop.value: globals()[prop.name] for prop in CommandTrigger if str(prop.name) in globals()}
