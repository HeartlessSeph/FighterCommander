from Structure.Enums.common import GameEngine
from Structure.Common.cmd_prop import cmd_property


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
