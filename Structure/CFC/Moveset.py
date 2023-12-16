import Structure.Enums.common as com
from Structure.Enums.common import CFC_GROUPS, GameEngine
from Structure.Common.cmd_prop import cmd_property

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