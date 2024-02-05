import Structure.Enums.common as com
from Structure.Enums.common import GameEngine
from Structure.CFC.Move import move
from Structure.CFC.Moveset import moveset


class command_set:
    def __init__(self):
        self.name = None
        self.id = None
        self.offset = None
        self.moves = []
        self.movesets = []
        self.num_moves = None
        self.num_movesets = None
        self.moveset_table_offset = None
        self.move_table_offset = None
        self.idx_dict = None

    def read_file(self, buffer, game):
        self.offset = buffer.pos()
        buffer.seek(buffer.read_uint32())
        self.name = buffer.read_str()
        print(f"Reading set: {self.name}")
        buffer.seek(self.offset)
        self.read_set(buffer, game)

    def read_set(self, buffer, game):
        buffer.read_uint_var()
        set_id = buffer.read_uint_var()
        if game.engine == GameEngine.OE:
            cur_pos = buffer.pos()
            buffer.seek(set_id)
            self.id = buffer.read_str()
            buffer.seek(cur_pos)
        else:
            self.id = set_id
        if game.engine == GameEngine.OE:
            self.__OE_SET__(buffer)
        else:
            self.__DE__SET__(buffer)
        self.read_moves(buffer, game)
        self.read_movesets(buffer, game)

    def __OE_SET__(self, buffer):
        self.num_moves = buffer.read_uint32()
        self.move_table_offset = buffer.read_uint32()
        self.num_movesets = buffer.read_uint32()
        self.moveset_table_offset = buffer.read_uint32()

    def __DE__SET__(self, buffer):
        self.move_table_offset = buffer.read_uint64()
        self.moveset_table_offset = buffer.read_uint64()
        self.num_moves = buffer.read_uint16()
        self.num_movesets = buffer.read_uint16()

    def read_moves(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_moves):
            buffer.seek(self.move_table_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_move = move()
            cur_move.read_move(buffer, game)
            self.moves.append(cur_move)

    def read_movesets(self, buffer, game):
        offsetter = 4 * game.engine
        for i in range(self.num_movesets):
            buffer.seek(self.moveset_table_offset + (i * offsetter))
            buffer.seek(buffer.read_uint_var())
            cur_moveset = moveset()
            cur_moveset.read_moveset(buffer, game)
            self.movesets.append(cur_moveset)

    def assign_follow_up_names(self):
        self.set_idx_dict()
        for move in self.moves:
            for follow_up in move.follow_ups:
                follow_up.follow_up_move = self.idx_dict[follow_up.follow_up_move_idx]

    def deassign_follow_up_names(self):
        self.set_name_dict()
        for move in self.moves:
            for follow_up in move.follow_ups:
                follow_up.follow_up_move_idx = self.idx_dict[follow_up.follow_up_move]

    def set_idx_dict(self):
        self.idx_dict = {idx: move.name for idx, move in enumerate(self.moves)}

    def set_name_dict(self):
        self.idx_dict = {move.name: idx for idx, move in enumerate(self.moves)}

    def build_json(self, mjson):
        for move in self.moves:
            move.build_json(mjson)
        for midx, moveset in enumerate(self.movesets):
            moveset.build_json(mjson, midx)

    def parse_json(self, mjson, game):
        self.id = com.set_id_name[self.name]
        if game.engine == com.GameEngine.OE: com.string_dict[self.id] = 0

        if "Move Table" in mjson:
            for mmove in mjson["Move Table"].keys():
                cur_move = move()
                cur_move.name = mmove
                com.string_dict[mmove] = 0
                cur_move.parse_json(mjson["Move Table"][mmove], game)
                self.moves.append(cur_move)
        if "Moveset Change Table" in mjson:
            for mmoveset in mjson["Moveset Change Table"]:
                cur_moveset = moveset()
                cur_moveset.parse_json(mjson["Moveset Change Table"][mmoveset], game)
                self.movesets.append(cur_moveset)
