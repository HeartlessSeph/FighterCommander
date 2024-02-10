from binary_reader import Whence
import Structure.Enums.common as com
from Structure.Enums.common import CFC_GROUPS, GameEngine
from Structure.CFC.Set import command_set
from Utilities.util import tree
import re


class command_set_table:
    def __init__(self):
        self.command_sets = []
        self.offset = None
        self.num_sets = None
        self.cfc_jsons = []

    def read_header(self, buffer, game):
        if game.engine == GameEngine.DE:
            buffer.seek(-0x10, Whence.CUR)
            table_pointer = buffer.read_uint64()
            num_sets = buffer.read_uint64()
        else:
            buffer.seek(-0x08, Whence.CUR)
            num_sets = buffer.read_uint32()
            table_pointer = buffer.read_uint32()
        self.offset = table_pointer
        self.num_sets = num_sets
        buffer.seek(table_pointer)

    def read_table(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_sets):
            buffer.seek(self.offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_set = command_set()
            cur_set.read_file(buffer, game)
            self.command_sets.append(cur_set)

    def build_json(self):
        for c_set in self.command_sets:
            cfc_json = tree()
            c_set.build_json(cfc_json)
            self.cfc_jsons.append(cfc_json)

    def parse_jsons(self, json, game):
        for cset_json in com.file_jsons.keys():
            cur_set = command_set()
            cur_set.name = cset_json
            com.string_dict[cset_json] = 0
            cur_set.parse_json(com.file_jsons[cset_json], game)
            self.command_sets.append(cur_set)

    def find_by_set_id(self, set_id):
        for cidx, cset in enumerate(self.command_sets):
            if cset.id == set_id:
                return cset, cidx
        return None, None

    def find_by_set_name(self, set_name):
        for cidx, cset in enumerate(self.command_sets):
            if cset.name == set_name:
                return cset, cidx
        return None, None

    def add_set(self, new_set: command_set, game):
        if game.type < com.CFC_GROUPS.DE_K2:
            cset, cidx = self.find_by_set_name(new_set.name)
        else:
            cset, cidx = self.find_by_set_id(new_set.id)
        # TODO: Finish this function
        pass


    def assign_moveset_link_names(self, game):
        command_set_dict = {cidx: {"Name": cset.name, "Move": cset.idx_dict, "ID": cset.id} for cidx, cset in enumerate(self.command_sets)}
        command_set_dict3 = {cset.id: {"Name": cset.name, "Move": cset.idx_dict, "ID": cset.id} for cidx, cset in enumerate(self.command_sets)}
        command_set_dict2 = {cset.id: cset.name for cset in self.command_sets}
        command_set_dict2[0] = "Previous Moveset"
        for command_set in self.command_sets:
            for move in command_set.moves:
                if com.args.cset_id:
                    move.battle_mode.prop_class.idx_to_name(move.battle_mode.prop_dict, command_set_dict3)
                else:
                    move.battle_mode.prop_class.idx_to_name(move.battle_mode.prop_dict, command_set_dict)
            for moveset in command_set.movesets:
                if moveset.name is None:
                    if moveset.id not in command_set_dict2:
                        moveset.name = moveset.id
                    else:
                        moveset.name = command_set_dict2[moveset.id]

    def deassign_moveset_link_names(self, game):
        command_set_dict = {cset.name: {"Name": cidx, "Move": cset.idx_dict, "ID": cset.id} for cidx, cset in enumerate(self.command_sets)}
        command_set_dict2 = {cset.name: cset.id for cset in self.command_sets}
        command_set_dict2["Previous Moveset"] = 0
        for command_set in self.command_sets:
            for move in command_set.moves:
                move.battle_mode.prop_class.idx_to_name(move.battle_mode.prop_dict, command_set_dict)
            for moveset in command_set.movesets:
                if game.type in [CFC_GROUPS.DE_CUR, CFC_GROUPS.DE_K2]:
                    if isinstance(moveset.name, int):
                        moveset.id = moveset.name
                    else:
                        moveset.id = command_set_dict2[moveset.name]
                else:
                    moveset.name = com.string_dict[moveset.name]
                    moveset.id = 0

    def update_num_sets(self):
        self.num_sets = len(self.command_sets)
