import Structure.Enums.common as com
from Structure.CFC.Set_Table import command_set_table
from Structure.CFC.Header import cfcHeader as header


class cfcFile:
    def __init__(self):
        self.name = ""
        self.version = None
        self.game = None
        self.header = header()
        self.command_set_table = command_set_table()
        self.filesize = None

    def read_file(self, buffer):
        buffer.set_engine = self.game.engine
        self.filesize = self.header.read_header(buffer)
        com.read_string_table(buffer, com.string_dict)
        buffer.seek(self.filesize)
        self.command_set_table.read_header(buffer, self.game)
        self.command_set_table.read_table(buffer, self.game)

    def set_game(self, game):
        self.game = game

    def set_name(self, string):
        self.name = string

    def get_name(self):
        return self.name

    def assign_all_follow_ups(self):
        for command_set in self.command_set_table.command_sets:
            command_set.assign_follow_up_names()
        self.command_set_table.assign_moveset_link_names(self.game)

    def deassign_all_follow_ups(self):
        for command_set in self.command_set_table.command_sets:
            print(f"De-assigning {command_set.name} string references")
            command_set.deassign_follow_up_names()
        self.command_set_table.deassign_moveset_link_names(self.game)

    def build_jsons(self):
        self.command_set_table.build_json()
