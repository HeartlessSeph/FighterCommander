from Structure.Enums.common import CFC_GROUPS, GameEngine
from Structure.CFC.Follow_up import follow_up
import importlib


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

        self.battle_mode = None

    def set_battle_mode(self, game_name: str = "Default"):
        module_instance = None
        try:
            module_instance = importlib.import_module(f"Types.battle.{game_name}.moves")
        except ImportError:
            # print(f"No module exists for Types.battle.{game_name}.moves")
            module_instance = importlib.import_module("Types.battle.Default.moves")

        cur_class = module_instance.battle_mode()
        self.battle_mode = cur_class

    def read_move(self, buffer, game):
        self.set_battle_mode(game.key)
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
        if "Move Table" in mjson:
            cur_name = self.name
            my_enumerator = 0
            while cur_name in mjson["Move Table"]:
                cur_name = f"{self.name}[DUPLICATE-{my_enumerator}]"
                if cur_name not in mjson["Move Table"]:
                    self.name = cur_name

        mjson["Move Table"][self.name] = self.battle_mode.prop_dict

        for idx, follow_up in enumerate(self.follow_ups):
            follow_up.build_json(mjson["Move Table"][self.name], idx)

        for idx, add_prop in enumerate(self.add_props):
            idx_str = "Property " + str(idx + 1)
            mjson["Move Table"][self.name]["Properties"][idx_str]["Unk Short 1"] = add_prop & 0xFFFF
            mjson["Move Table"][self.name]["Properties"][idx_str]["Unk Short 2"] = (add_prop & 0xFFFF0000) >> 16

    def parse_json(self, mjson, game):
        self.type = mjson["Move Type"]
        self.set_battle_mode(game.key)
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
                prop_val = mjson["Properties"][mprop]["Unk Short 1"] + (mjson["Properties"][mprop]["Unk Short 2"] << 16)
                self.add_props.append(prop_val)
