from collections import OrderedDict
from collections import defaultdict
import json
from pathlib import Path
import Structure.Enums.common as com
import cutie
import re
import ruamel.yaml
from enum import Enum, IntEnum


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_warning(mstring):
    print(bcolors.WARNING + "WARNING: " + mstring + bcolors.ENDC)


def print_header(mstring):
    print(bcolors.HEADER + mstring + bcolors.ENDC)


def tree():
    def the_tree():
        return defaultdict(the_tree)

    return the_tree()


def get_set_bits_as_enum(value, enum):
    set_bits = []
    for bit_position in range(value.bit_length()):
        if value & (1 << bit_position) != 0:
            try:
                set_bits.append(enum(bit_position).name)
            except ValueError:
                pass
                print(f"Warning: bit {bit_position} goes beyond the enum range.")

    return ','.join(set_bits)


def map_enum_names_to_bits(mstring, enum):
    result = 0
    string_list = mstring.split(",")

    for string_value in string_list:
        try:
            if string_value == "":
                return 0
            bit_enum = enum[string_value]
            result |= (1 << bit_enum.value)
        except KeyError:
            print(f"Warning: '{string_value}' is not a enum value.")

    return result


def export_json(target_path, filename, data, is_yaml=False):  # Writes a json to a certain directory
    """
    :param target_path: Path object
    :param filename: String
    :param data: Dictionary
    """
    target_extension = r'.json' if not is_yaml else r'.yaml'
    target_path.mkdir(parents=True, exist_ok=True)
    if is_yaml:
        new_data = json.loads(json.dumps(data))
        yaml = ruamel.yaml.YAML(typ='safe', pure=True)
        yaml.sort_base_mapping_type_on_output = False
        yaml.indent(mapping=2, sequence=5, offset=4)
        yaml.default_flow_style = False
        yamlPath = target_path / (filename + r'.yaml')
        yaml.dump(new_data, yamlPath)
    else:
        jsonFile = json.dumps(data, ensure_ascii=False, indent=2)
        jsonPath = target_path / (filename + r'.json')
        jsonPath.write_text(jsonFile, encoding='utf8')
    print(f"{filename}{target_extension} created.")


def import_json(target_path, name, is_yaml=False):  # Goes through a directory, then loads json info into a dict
    """
    :param target_path: Path Object
    :param name: String
    """
    target_extension = r'.json' if not is_yaml else r'.yaml'
    import_file = target_path / (name + target_extension)
    with import_file.open(encoding='utf8') as input_file:
        if is_yaml:
            yaml = ruamel.yaml.YAML(typ='safe')
            with open(import_file, 'r') as file:
                json_array = yaml.load(file)
        else:
            json_array = json.loads(input_file.read())
        return json_array


def verify_path_info(path):
    path = Path(path).resolve()
    if not path.exists():
        print(path)
        raise Exception(f"{str(path)} does not exist")
    is_file = path.is_file()
    is_directory = path.is_dir()
    file_extension = path.suffix
    return path, is_file, is_directory, file_extension


def merge_two_dicts(x, y):
    z = x.copy()  # start with keys and values of x
    z.update(y)  # modifies z with keys and values of y
    return z


def collect_extracted_file_info(type, file_class, file_info, extra_info=None):
    mdict = {
        "Filetype": type,
        "Game Name": file_class.game.name,
        "Game Key": file_class.game.key,
        "File Version": file_class.header.version,
        "Files Directory": "Extracted",
    }

    if extra_info is not None:
        for mkey in extra_info.keys():
            mdict[mkey] = extra_info[mkey]

    mdict["File Specific Info"] = file_info

    return mdict


def parse_arg_armp_json(mpath):
    mpath, _, _, _ = verify_path_info(mpath)
    mdict = import_json(Path(mpath.parents[0]), mpath.stem)
    temp = {}
    for x, entry in enumerate(list(mdict.keys())):  # Get Movenames
        if entry.isdigit():
            temp[int(entry)] = list(mdict[entry].keys())[0]
    return temp, mpath


def json_scan(mbool, file_name, parent_directory, dict_file):
    choice = mbool
    if not mbool:
        check = [Path(x).name for x in parent_directory.glob(f"{file_name}*.json") if x.is_file()]
        if len(check) > 0:
            print(f"The following {file_name} files have been found in the file directory. Please select which to use.")
            check.append("Do not use")
            choice = check[cutie.select(check)]
            if choice != "Do not use":
                dict_file, _ = parse_arg_armp_json(choice)
                choice = Path(parent_directory / choice)
            else:
                choice = None
    return dict_file, choice


def enum_to_val(mval: str, menum):
    if menum.has_name(mval):
        output = menum[mval].value
    elif isinstance(mval, int):
        output = mval
    else:
        raise Exception(f"{mval} not in {menum.name}!")
    return output


def val_to_enum(mval: int, menum):
    if menum.has_value(mval):
        output = menum(mval).name
    else:
        output = mval
    return output


def parse_path_relativity(mval: str, base_path):
    if "/" in mval:
        return Path(mval)
    else:
        return base_path / mval


class base_enum(Enum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def has_name(cls, ename):
        return ename in cls.__members__


class base_enum_int(IntEnum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def has_name(cls, ename):
        return ename in cls.__members__
