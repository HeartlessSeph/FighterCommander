import Structure.Enums.common as com
from Structure.CHP.Target import target


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

        # buffer.seek(self.offset)
        # self.read_set(buffer, game)

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

        if game.engine == com.GameEngine.OE:
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

        for midx, mtarget in enumerate(self.targets):
            mtarget.build_json(mjson["Targets"], midx)

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
        elif com.cur_game.type in [com.CFC_GROUPS.DE_Y6, com.CFC_GROUPS.DE_DEMO]:
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

    def __OE_JSON_PARSE(self, mjson, game):
        self.unk_target_val = mjson["Unknown Target Value"]
        self.comp_flag = mjson["Completion Name"]
        com.string_dict[self.comp_flag] = 0
        self.x = mjson["X?"]
        self.y = mjson["Y?"]
        self.z = mjson["Z?"]
        if game.type != com.CFC_GROUPS.OE_Y5:
            self.condition = mjson["Condition Name"]
            com.string_dict[self.condition] = 0
            self.unk_int_3 = mjson["Unknown Int 3"]
            self.unk_int_4 = mjson["Unknown Int 4"]

    def __DE_JSON_PARSE(self, mjson, game):
        if game.type == com.CFC_GROUPS.DE_CUR:
            parts = self.name.split('#')
            self.id = com.talk_param[parts[0]] if len(com.talk_param) > 0 else parts[0]
            self.sub = int(parts[1]) if len(parts) == 2 else 0
        elif game.type == com.CFC_GROUPS.DE_K2:
            self.id = mjson["Talk_Param ID"]
        elif game.type in [com.CFC_GROUPS.DE_Y6, com.CFC_GROUPS.DE_DEMO]:
            self.id = mjson["HAct ID"]
            com.string_dict[self.id] = 0

        if game.type == com.CFC_GROUPS.DE_CUR:
            self.special_effect = mjson["Special Effect"]
            com.string_dict[self.special_effect] = 0
        self.comp_flag = mjson["Completion Flag"]
        if game.type not in [com.CFC_GROUPS.DE_Y6, com.CFC_GROUPS.DE_Y6]:
            self.play_area_type = mjson["Play Area Type"]
        self.x = mjson["X"]
        self.y = mjson["Y"]
        self.z = mjson["Z"]
        self.rot = mjson["Rotation"]
        if game.type != com.CFC_GROUPS.DE_CUR:
            self.unk_target_val = mjson["Unk Float"]
            self.hact_base = mjson["Base HAct"]
            com.string_dict[self.hact_base] = 0
            com.string_dict[self.comp_flag] = 0

    def parse_json(self, mjson, game):
        if game.engine == com.GameEngine.DE:
            self.__DE_JSON_PARSE(mjson, game)
        else:
            self.__OE_JSON_PARSE(mjson, game)

        if "Targets" in mjson:
            for mtarget in mjson["Targets"].keys():
                cur_target = target()
                cur_target.parse_json(mjson["Targets"][mtarget], game)
                self.targets.append(cur_target)
