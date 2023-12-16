from binary_reader import Whence, Endian
from Utilities.bin_reader import BinaryReader
from Structure.Enums.common import GameEngine
from Types.battle.properties import battle_command


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
