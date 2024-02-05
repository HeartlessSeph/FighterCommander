from binary_reader import Endian
import Structure.Enums.common as com
from Structure.Enums.common import endianess

class cfcHeader:
    def __init__(self):
        self.version = None
        self.endian = None
        self.magic = "CFCI"

    def read_header(self, buffer):
        magic = buffer.read_str(4)
        if magic != self.magic:
            raise Exception("File is not a CFC File.")
        endian = buffer.read_uint32()
        self.endian = endianess[endian]
        buffer.set_endian(self.endian)
        self.version = buffer.read_uint32()
        return buffer.read_uint32()

    def set_version(self, version):
        self.version = version

    def write_header(self, buffer):
        self.endian = buffer.get_endian()
        buffer.set_endian(Endian.LITTLE)
        buffer.write_str(self.magic)
        buffer.write_uint32(com.endianess_backwards[self.endian])
        buffer.set_endian(self.endian)
        buffer.write_uint32(self.version)
        buffer.write_uint32(0)
