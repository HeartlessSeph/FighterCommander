from binary_reader import Endian, Whence
from enum import Enum, IntFlag, IntEnum

endianess = {33: Endian.LITTLE, 258: Endian.BIG}
endianess_backwards = {False: 33, True: 258}

LAD_GAME_BACKWARDS = {
    'y0': 'Yakuza 0',
    'yk1': 'Yakuza Kiwami 1',
    'yk2': 'Yakuza Kiwami 2',
    'y5': 'Yakuza 5',
    'y6': 'Yakuza 6',
    'y6d': 'Yakuza 6 Demo',
    'y7': 'Yakuza Like a Dragon',
    'yish': 'Yakuza Ishin',
    'fotns': 'Fist of the North Star Lost Paradise',
    'je': 'Judgment',
    'lj': 'Lost Judgment',
    'ladg': 'Like a Dragon Gaiden',
    'ladiw': 'Like a Dragon Infinite Wealth'
}

LAD_GROUP = {
    'y0': 0,
    'yk1': 0,
    'fotns': 0,
    'y5': 1,
    'yish': 2,
    'y6d': 3,
    'y6': 4,
    'yk2': 5,
    'je': 6,
    'y7': 6,
    'lj': 6,
    'ladg': 6,
    'ladiw': 6
}


class CFC_GROUPS(IntEnum):
    OE = 0
    OE_Y5 = 1
    OE_ISHIN = 2
    DE_DEMO = 3
    DE_Y6 = 4,
    DE_K2 = 5,
    DE_CUR = 6


LAD_GAME = {v: k for k, v in LAD_GAME_BACKWARDS.items()}
LAD_OPTION = [k for k, v in LAD_GAME.items()]


class GameEngine(IntEnum):
    invalid = 0
    OE = 1
    DE = 2


class Game:
    def __init__(self):
        self.name = None
        self.type = None
        self.engine = None
        self.key = None

    def set_game(self, game_key):
        self.key = game_key
        game_str = LAD_GAME_BACKWARDS[game_key]
        game_group = LAD_GROUP[game_key]
        self.name = game_str
        self.type = CFC_GROUPS(game_group)
        if self.type > 2:
            self.engine = GameEngine.DE
        else:
            self.engine = GameEngine.OE

string_dict = {}
string_dict_other = {}
talk_param = {}
motion_gmt = {}
file_jsons = {}
file_order = {}
file_names = {}
set_id_order = {}
set_id_name = {}
last_string_offset = 0
cur_game = None
args = None


def print_pos(buffer):
    print(str(hex(buffer.pos())))


def read_string_table(buffer, s_dict):
    buffer.seek(0x10)
    while True:
        try:
            cur_pos = buffer.pos()
            null_check = buffer.read_uint8()
            if null_check == 0:
                s_dict[cur_pos] = "Null"
            else:
                buffer.seek(-0x1, Whence.CUR)
                cur_string = buffer.read_str()
                s_dict[cur_pos] = cur_string
        except:
            break


def write_string_table(buffer, s_dict, filler=b'\xCC', filler_count=16):
    for mstring in s_dict.keys():
        string_pos = buffer.pos()
        if mstring == "Null":
            buffer.write_uint8(0)
        else:
            buffer.write_str(mstring, null=True)
        s_dict[mstring] = string_pos
    cur_pos = buffer.pos()
    num_bytes = filler_count - (cur_pos % filler_count)
    if num_bytes == 0:
        num_bytes = filler_count
    buffer.write_bytes(filler * num_bytes)
