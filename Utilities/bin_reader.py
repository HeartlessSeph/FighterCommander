from binary_reader import BinaryReader as BREAD
from binary_reader import Endian
from typing import Tuple, Union


class BinaryReader(BREAD):
    def __init__(self, buffer: bytearray = bytearray(), endianness: Endian = Endian.LITTLE, encoding='utf-8'):
        super().__init__(buffer, endianness, encoding)
        self.engine = 1

    def set_engine(self, engine):
        self.engine = engine

    def get_endian(self) -> Endian:
        """Sets the endianness of the BinaryReader."""
        return self.__endianness

    def read_int_var(self) -> Union[int, Tuple[int]]:
        if self.engine == 2:
            return self.__read_type("q")[0]
        else:
            return self.__read_type("i")[0]

    def read_uint_var(self) -> Union[int, Tuple[int]]:
        if self.engine == 2:
            return self.__read_type("Q")[0]
        else:
            return self.__read_type("I")[0]

    def write_int_var(self, value: int) -> None:
        if self.engine == 2:
            self.__write_type("q", value, self.is_iterable(value))
        else:
            self.__write_type("i", value, self.is_iterable(value))

    def write_uint_var(self, value: int) -> None:
        if self.engine == 2:
            self.__write_type("Q", value, self.is_iterable(value))
        else:
            self.__write_type("I", value, self.is_iterable(value))
