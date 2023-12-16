import Structure.Enums.common as com
from Structure.CHP.Set import hact_set
from Utilities.util import tree
from binary_reader import Whence


class hact_set_table:
    def __init__(self):
        self.hact_sets = []
        self.offset = None
        self.num_sets = None
        self.chp_jsons = []

    def read_header(self, buffer, game):
        buffer.seek(-0x08 * game.engine, Whence.CUR)
        num_sets = buffer.read_uint_var()
        table_pointer = buffer.read_uint_var()
        self.offset = table_pointer
        self.num_sets = num_sets
        buffer.seek(table_pointer)

    def read_table(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_sets):
            buffer.seek(self.offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_set = hact_set()
            cur_set.read_file(buffer, game)
            self.hact_sets.append(cur_set)

    def update_num_sets(self):
        self.num_sets = len(self.hact_sets)

    def build_json(self):
        for c_set in self.hact_sets:
            chp_json = tree()
            c_set.build_json(chp_json)
            self.chp_jsons.append(chp_json)

    def parse_jsons(self, json, game):
        for cset_json in com.file_jsons.keys():
            cur_set = hact_set()
            cur_set.name = cset_json
            if game.type != com.CFC_GROUPS.DE_CUR: com.string_dict[cset_json] = 0
            cur_set.parse_json(com.file_jsons[cset_json], game)
            self.hact_sets.append(cur_set)