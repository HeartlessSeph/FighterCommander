import Structure.Enums.common as com
from Structure.Common.cmd_prop import cmd_property


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

    def unassign_motion_id(self, game):
        pass

    def assign_motion_id(self, game):
        pass

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
            self.end_motion_id = com.string_dict[buffer.read_uint32()]
            self.num_properties = buffer.read_uint32()
            self.properties_offset = buffer.read_uint32()
            self.modify_flag = buffer.read_uint32()
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
        mjson[mstr]["End Motion ID"] = self.end_motion_id
        mjson[mstr]["Modify Flag"] = self.modify_flag

        for midx, property in enumerate(self.properties):
            property.build_json(mjson[mstr], midx)

    def parse_json(self, mjson, game):
        self.name = mjson["Target Name"]
        com.string_dict[self.name] = 0
        self.type = mjson["Target Type"]
        self.end_motion_id = mjson["End Motion ID"]
        self.modify_flag = mjson["Modify Flag"]
        if game.engine == com.GameEngine.OE: com.string_dict[self.end_motion_id] = 0
        if "Conditions" in mjson:
            for midx, mproperty in enumerate(mjson["Conditions"].keys()):
                cur_property = cmd_property()
                cur_property.parse_json(mjson["Conditions"][mproperty], game, midx)
                self.properties.append(cur_property)
