import Structure.Enums.common as com
from Structure.CHP.Header import chpHeader as header
from Structure.CHP.Set_Table import hact_set_table


class chpFile:
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
