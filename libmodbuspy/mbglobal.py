"""
@file mbglobal.py
@brief Contains general definitions of the Modbus library for Python.

This module provides the core functionality for the libmodbuspy library including:
- Status codes and error handling
- Protocol type definitions (TCP, RTU, ASCII)
- Memory type definitions (coils, discrete inputs, holding registers, input registers)
- Configuration structures for TCP and serial communications
- Utility functions for CRC16/LRC checksums and data conversion
- Base ModbusInterface class defining the Modbus protocol methods
- Address class for Modbus address representation and conversion

@author serhmarch
@date November 2025
"""

import time
from enum import IntEnum
from typing import Optional, Union, List, Tuple
import struct

from .mbconfig import *
from .statuscode import StatusCode
from . import exceptions

# --------------------------------------------------------------------------------------------------------
# ------------------------------------------- Helper functions -------------------------------------------
# --------------------------------------------------------------------------------------------------------

def getBit(bit_buff: Union[bytes, bytearray], bit_num: int) -> bool:
    """Get bit with number `bit_num` from array `bit_buff`."""
    if isinstance(bit_buff, (bytes, bytearray)):
        byte_index = bit_num // 8
        bit_index = bit_num % 8
        if byte_index < len(bit_buff):
            return (bit_buff[byte_index] & (1 << bit_index)) != 0
    return False

def setBit(bit_buff: bytearray, bit_num: int, value: bool) -> None:
    """Set bit `value` with number `bit_num` to array `bit_buff`."""
    if isinstance(bit_buff, bytearray):
        byte_index = bit_num // 8
        bit_index = bit_num % 8
        if byte_index < len(bit_buff):
            if value:
                bit_buff[byte_index] |= (1 << bit_index)
            else:
                bit_buff[byte_index] &= ~(1 << bit_index)

def getBits(bit_buff: Union[bytes, bytearray], bit_num: int, bit_count: int) -> List[bool]:
    """Get bits begins with number `bit_num` with `bit_count` from input bit array `bit_buff`."""
    bool_buff = []
    for i in range(bit_count):
        bool_buff.append(getBit(bit_buff, bit_num + i))
    return bool_buff

def setBits(bit_buff: bytearray, bit_num: int, bit_count: int, bool_buff: List[bool]) -> None:
    """Set bits begins with number `bit_num` with `bit_count` from input bool array `bool_buff` to output bit array `bit_buff`."""
    for i in range(min(bit_count, len(bool_buff))):
        setBit(bit_buff, bit_num + i, bool_buff[i])

# Unit map constants and functions
MB_UNITMAP_SIZE = 32

def mb_unitmap_get_bit(unitmap: Union[bytes, bytearray], unit: int) -> bool:
    """Get bit from unitmap for specific unit."""
    return getBit(unitmap, unit)

def mb_unitmap_set_bit(unitmap: bytearray, unit: int, value: bool) -> None:
    """Set bit in unitmap for specific unit."""
    setBit(unitmap, unit, value)

# --------------------------------------------------------------------------------------------------------
# ----------------------------------------- Modbus function codes ----------------------------------------
# --------------------------------------------------------------------------------------------------------

# Modbus Function codes
MBF_READ_COILS                       = 1
MBF_READ_DISCRETE_INPUTS             = 2
MBF_READ_HOLDING_REGISTERS           = 3
MBF_READ_INPUT_REGISTERS             = 4
MBF_WRITE_SINGLE_COIL                = 5
MBF_WRITE_SINGLE_REGISTER            = 6
MBF_READ_EXCEPTION_STATUS            = 7
MBF_DIAGNOSTICS                      = 8
MBF_GET_COMM_EVENT_COUNTER           = 11
MBF_GET_COMM_EVENT_LOG               = 12
MBF_WRITE_MULTIPLE_COILS             = 15
MBF_WRITE_MULTIPLE_REGISTERS         = 16
MBF_REPORT_SERVER_ID                 = 17
MBF_READ_FILE_RECORD                 = 20
MBF_WRITE_FILE_RECORD                = 21
MBF_MASK_WRITE_REGISTER              = 22
MBF_READ_WRITE_MULTIPLE_REGISTERS    = 23
MBF_READ_FIFO_QUEUE                  = 24
MBF_ENCAPSULATED_INTERFACE_TRANSPORT = 43
MBF_ILLEGAL_FUNCTION                 = 73
MBF_EXCEPTION                        = 128

# --------------------------------------------------------------------------------------------------------
# ---------------------------------------- Modbus count constants ----------------------------------------
# --------------------------------------------------------------------------------------------------------

# 8 = count bits in byte (byte size in bits)
MB_BYTE_SZ_BITES = 8

# 16 = count bits in 16 bit register (register size in bits) 
MB_REGE_SZ_BITES = 16

# 2 = count bytes in 16 bit register (register size in bytes) 
MB_REGE_SZ_BYTES = 2

# 255 - count_of_bytes in function readHoldingRegisters, readCoils etc
MB_MAX_BYTES = 255

# 127 = 255(count_of_bytes in function readHoldingRegisters etc) / 2 (register size in bytes)
MB_MAX_REGISTERS = 127

# 2040 = 255(count_of_bytes in function readCoils etc) * 8 (bits in byte)
MB_MAX_DISCRETS = 2040

# Same as `MB_MAX_BYTES`
MB_VALUE_BUFF_SZ = 255

# Maximum func data size: WriteMultipleCoils
# 261 = 1 byte(function) + 2 bytes (starting offset) + 2 bytes (count) + 1 bytes (byte count) + 255 bytes(maximum data length)

# 1 byte(unit) + 261 (max func data size: WriteMultipleCoils) + 2 bytes(CRC)
MB_RTU_IO_BUFF_SZ = 264

# 1 byte(start symbol ':')+(( 1 byte(unit) + 261 (max func data size: WriteMultipleCoils)) + 1 byte(LRC) ))*2+2 bytes(CR+LF)
MB_ASC_IO_BUFF_SZ = 529

# 6 bytes(tcp-prefix)+1 byte(unit)+261 (max func data size: WriteMultipleCoils)
MB_TCP_IO_BUFF_SZ = 268

# Maximum events for `GetCommEventLog` function
MB_GET_COMM_EVENT_LOG_MAX = 64

# Maximum events for `GetCommEventLog` function
MB_READ_FIFO_QUEUE_MAX = 31

# --------------------------------------------------------------------------------------------------------
# Format string constants for struct packing/unpacking
MB_FMT_INT16_BE = '>h'  # Big-endian 16-bit signed integer format
MB_FMT_INT16_LE = '<h'  # Little-endian 16-bit signed integer format
MB_FMT_UINT16_BE = '>H' # Big-endian 16-bit unsigned integer format
MB_FMT_UINT16_LE = '<H' # Little-endian 16-bit unsigned integer format
MB_FMT_INT32_BE = '>i'  # Big-endian 32-bit signed integer format
MB_FMT_INT32_LE = '<i'  # Little-endian 32-bit signed integer format
MB_FMT_UINT32_BE = '>I' # Big-endian 32-bit unsigned integer format
MB_FMT_UINT32_LE = '<I' # Little-endian 32-bit unsigned integer format
MB_FMT_INT64_BE = '>q'  # Big-endian 64-bit signed integer format
MB_FMT_INT64_LE = '<q'  # Little-endian 64-bit signed integer format
MB_FMT_UINT64_BE = '>Q' # Big-endian 64-bit unsigned integer format
MB_FMT_UINT64_LE = '<Q' # Little-endian 64-bit unsigned integer format
MB_FMT_FLOAT32_BE = '>f' # Big-endian 32-bit float format
MB_FMT_FLOAT32_LE = '<f' # Little-endian 32-bit float format
MB_FMT_FLOAT64_BE = '>d' # Big-endian 64-bit float format
MB_FMT_FLOAT64_LE = '<d' # Little-endian 64-bit float format
MB_FMT_FLOAT_BE = MB_FMT_FLOAT32_BE # Default float format (big-endian 32-bit)
MB_FMT_FLOAT_LE = MB_FMT_FLOAT32_LE # Default float format (little-endian 32-bit)
MB_FMT_DOUBLE_BE = MB_FMT_FLOAT64_BE # Default double format (big-endian 64-bit)
MB_FMT_DOUBLE_LE = MB_FMT_FLOAT64_LE # Default double format (little-endian 64-bit)

def pack(fmt: str, values: Union[tuple, list]) -> bytes:
    """Pack data into buffer using the specified format string.
    Args:
        * fmt (str): Format string for packing data.
          Same format as in `struct` module but can contain 2 characters at most:
            - (can be omitted) First character defines endianness (e.g. '>' for big-endian, '<' for little-endian)
            - Second character defines the type (e.g. 'h' for 16-bit integer, 'f' for 32-bit float).
          This format defined for each item in `values` list/tuple (in comparison with `struct` module).
        * values (Union[tuple, list]): Values to pack.
    Returns: bytes array with packed data.
    """
    #size = struct.calcsize(fmt)
    e = fmt[0]
    c = len(values)
    if e.isalpha():
        mfmt = str(c) + e
    else:
        mfmt = e + str(c) + fmt[-1]
    return struct.pack(mfmt, *values)

def unpack(fmt: str, buff: Union[bytes, bytearray]) -> Tuple:
    """Unpack data from buffer using the specified format string.

    Args:
        * fmt (str): Format string for unpacking data.
          Same format as in `struct` module but can contain 2 characters at most:
            - (can be omitted) First character defines endianness (e.g. '>' for big-endian, '<' for little-endian)
            - Second character defines the type (e.g. 'h' for 16-bit integer, 'f' for 32-bit float).
          This format defined for each item in `values` list/tuple (in comparison with `struct` module).
        * values (Union[tuple, list]): Values to pack.
    Returns: tuple with each element as format data.
    """
    sz = struct.calcsize(fmt)
    c = len(buff) // sz
    e = fmt[0]
    if e.isalpha():
        mfmt = str(c) + e
    else:
        mfmt = e + str(c) + fmt[-1]
    return struct.unpack(mfmt, buff)

# --------------------------------------------------------------------------------------------------------
# Define list of constants of Modbus protocol
class Constants:
    """Constants of Modbus protocol."""
    VALID_MODBUS_ADDRESS_BEGIN = 1    # Start of Modbus device address range according to specification
    VALID_MODBUS_ADDRESS_END = 247    # End of the Modbus protocol device address range according to the specification
    STANDARD_TCP_PORT = 502           # Standard TCP port of the Modbus protocol

# =========== Modbus protocol types ===============

class MemoryType(IntEnum):
    """Defines type of memory used in Modbus protocol."""
    Memory_Unknown = 0xFFFF             # Invalid memory type
    Memory_0x = 0                       # Memory allocated for coils/discrete outputs
    Memory_Coils = Memory_0x            # Same as `Memory_0x`.
    Memory_1x = 1                       # Memory allocated for discrete inputs
    Memory_DiscreteInputs = Memory_1x   # Same as `Memory_1x`.
    Memory_3x = 3                       # Memory allocated for analog inputs
    Memory_InputRegisters = Memory_3x   # Same as `Memory_3x`.
    Memory_4x = 4                       # Memory allocated for holding registers/analog outputs
    Memory_HoldingRegisters = Memory_4x # Same as `Memory_4x`.

class ProtocolType(IntEnum):
    """Defines type of Modbus protocol."""
    ASC = 0  # ASCII version of Modbus communication protocol.
    RTU = 1  # RTU version of Modbus communication protocol.
    TCP = 2  # TCP version of Modbus communication protocol.

class Parity(IntEnum):
    """Defines Parity for serial port."""
    NoParity = 0     # No parity bit it sent. This is the most common parity setting.
    EvenParity = 1   # The number of 1 bits in each character, including the parity bit, is always even.
    OddParity = 2    # The number of 1 bits in each character, including the parity bit, is always odd. It ensures that at least one state transition occurs in each character.
    SpaceParity = 3  # Space parity. The parity bit is sent in the space signal condition. It does not provide error detection information.
    MarkParity = 4   # Mark parity. The parity bit is always set to the mark signal condition (logical 1). It does not provide error detection information.

class StopBits(IntEnum):
    """Defines Stop Bits for serial port."""
    OneStop = 0        # 1 stop bit.
    OneAndHalfStop = 1 # 1.5 stop bit.
    TwoStop = 2        # 2 stop bits.

class FlowControl(IntEnum):
    """FlowControl for serial port."""
    NoFlowControl = 0   # No flow control.
    HardwareControl = 1 # Hardware flow control (RTS/CTS).
    SoftwareControl = 2 # Software flow control (XON/XOFF).

def crc16(byte_arr: Union[bytes, bytearray]) -> int:
    """CRC16 checksum hash function (for Modbus RTU).
    Returns a 16-bit unsigned integer value of the checksum.
    """
    crc = 0xFFFF
    for byte in byte_arr:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def lrc(byte_arr: Union[bytes, bytearray]) -> int:
    """LRC checksum hash function (for Modbus ASCII).
    Returns an 8-bit unsigned integer value of the checksum.
    """
    lrc_value = 0
    for byte in byte_arr:
        lrc_value += byte
    return ((-lrc_value) & 0xFF)

def readMemBits(bitoffset: int, bitcount: int, memBuff: bytearray) -> bytearray:
    """Function for copy (read) values from memory input `mem_buff` and return it as output buffer for discretes (bits).
    
    Args:
        offset: Memory offset to read from `memBuff` in bit size.
        count: Count of bits to read from memory `memBuff`.
        memBuff: Memory buffer which holds data.
        memBitCount: Size of memory buffer `memBuff` in bits.
    
    Returns:
        bytearray with read bits packed into bytes.
    """
    byteoffset = bitoffset // 8
    rbyteoffset = (bitoffset+bitcount-1) // 8
    bytecount = rbyteoffset-byteoffset+1
    byarray = memBuff[byteoffset:byteoffset+bytecount]
    shift = bitoffset % 8
    rem = bitcount % 8
    ri = (bitcount-1) // 8
    if shift:
        c = len(byarray)-1
        for i in range(c):
            b1 = byarray[i]
            b2 = byarray[i+1]   
            b = ((b2 << (8-shift)) | (b1 >> shift)) & 0xFF
            byarray[i] = b
    if rem:
        mask = (1 << (rem-1))
        mask |= (mask-1)
        b = byarray[ri]
        b = (b >> shift) & mask
        byarray[ri] = b
    if len(byarray) > ri+1:
        del byarray[ri+1]
    return byarray

def writeMemBits(bitoffset: int, bitcount: int, value: Union[bytes, bytearray], memBuff: bytearray):
    """Function for copy (write) values from input buffer `values` to memory `mem_buff` for discretes (bits).
    
    Args:
        bitoffset: Memory offset to write to `memBuff` in bit size.
        bitcount: Count of bits to write into memory `memBuff`.
        value: Input buffer that holds data to write.
        memBuff: Memory buffer.
        memBitCount: Size of memory buffer `memBuff` in bits.
    
    Returns:
        None
    """
    byteoffset = bitoffset // 8
    rbyteoffset = (bitoffset+bitcount-1) // 8
    bytecount = rbyteoffset-byteoffset+1
    byarray = bytearray(memBuff[byteoffset:byteoffset+bytecount])
    shift = bitoffset % 8
    c = bitcount // 8
    rem = bitcount % 8
    if shift:
        mask = 0xFF << shift
        notmask = ~mask
        for i in range(c):
            v = value[i] << shift
            b = int.from_bytes([byarray[i], byarray[i+1]], byteorder='little')
            b &= notmask
            b |= v
            tb = b.to_bytes(2, byteorder='little')
            byarray[i]   = tb[0]
            byarray[i+1] = tb[1]
    elif c > 0:
        byarray[0:c] = value[0:c]
    if rem:
        mask = (1 << (rem-1))
        mask |= (mask-1)
        mask = mask << shift
        notmask = ~mask
        v = (value[c] << shift) & mask
        if shift+rem > 8:
            b = int.from_bytes([byarray[c], byarray[c+1]], byteorder='little')
            b &= notmask
            b |= v
            tb = b.to_bytes(2, byteorder='little')
            byarray[c]   = tb[0]
            byarray[c+1] = tb[1]
        else:
            b = byarray[c] & notmask
            b |= v
            byarray[c] = b
    memBuff[byteoffset:byteoffset+bytecount] = byarray

def bytesToAscii(bytes_buff: Union[bytes, bytearray]) -> bytes:
    """Function converts byte array to ASCII repr of byte array.
    Every byte of bytes_buff are repr as two bytes in output,
    where most signified tetrabits represented as leading byte in hex digit in ASCII encoding (upper) and
    less signified tetrabits represented as tailing byte in hex digit in ASCII encoding (upper).
    
    Returns: bytes array that is twice the size of input
    """
    return bytes_buff.hex().upper().encode('ascii')

def asciiToBytes(ascii_buff: Union[bytes, bytearray]) -> bytes:
    """Function converts ASCII repr to binary byte array.
    Every byte of output are repr as two bytes in `ascii_buff`,
    where most signified tetrabits represented as leading byte in hex digit in ASCII encoding (upper) and
    less signified tetrabits represented as tailing byte in hex digit in ASCII encoding (upper).
    
    Returns: bytes array that is half the size of input
    """
    if isinstance(ascii_buff, (bytes, bytearray)):
        hex_str = ascii_buff.decode('ascii')
        return bytes.fromhex(hex_str)
    return b''

def sbytes(buff: Union[bytes, bytearray], max_len: int = 1000) -> str:
    """Make string representation of bytes array and separate bytes by space."""
    result = []
    for i, byte in enumerate(buff):
        if len(result) > max_len:
            result.append("...")
            break
        result.append(f"{byte:02X}")
    return " ".join(result)

def sascii(buff: Union[bytes, bytearray], max_len: int = 1000) -> str:
    """Make string representation of ASCII array and separate bytes by space."""
    result = []
    for i, byte in enumerate(buff):
        if len(result) > max_len:
            result.append("...")
            break
        if 32 <= byte <= 126:  # printable ASCII
            result.append(chr(byte))
        else:
            result.append(f"\\x{byte:02X}")
    return " ".join(result)

# String conversion functions for enums

def sprotocolType(protocol_type: ProtocolType) -> str:
    """Returns string representation of ProtocolType value."""
    return protocol_type.name if isinstance(protocol_type, ProtocolType) else "Unknown"

def toprotocolType(s: str) -> ProtocolType:
    """Converts string representation to ProtocolType value."""
    try:
        return ProtocolType[s.upper()]
    except (KeyError, AttributeError):
        return None

def sparity(parity: Parity) -> str:
    """Returns string representation of Parity value."""
    return parity.name if isinstance(parity, Parity) else "Unknown"

def toparity(s: str) -> Parity:
    """Converts string representation to Parity value."""
    try:
        return Parity[s]
    except (KeyError, AttributeError):
        return None

def sstopBits(stop_bits: StopBits) -> str:
    """Returns string representation of StopBits value."""
    return stop_bits.name if isinstance(stop_bits, StopBits) else "Unknown"

def tostopBits(s: str) -> StopBits:
    """Converts string representation to StopBits value."""
    try:
        return StopBits[s]
    except (KeyError, AttributeError):
        return None

def sflowControl(flow_control: FlowControl) -> str:
    """Returns string representation of FlowControl value."""
    return flow_control.name if isinstance(flow_control, FlowControl) else "Unknown"

def toflowControl(s: str) -> FlowControl:
    """Converts string representation to FlowControl value."""
    try:
        return FlowControl[s]
    except (KeyError, AttributeError):
        return None

# Timer and timestamp functions

def timer() -> int:
    """Get timer value in milliseconds."""
    return int(time.time() * 1000)

def currentTimestamp() -> int:
    """Get current timestamp in UNIX format in milliseconds."""
    return int(time.time() * 1000)

def msleep(msec: int) -> None:
    """Make current thread sleep with 'msec' milliseconds."""
    time.sleep(msec / 1000.0)

class Address:
    """
    @brief Modbus Data Address class. Represents Modbus Data Address.

    @details `Address` class is used to represent Modbus Data Address. It contains memory type and offset.
    E.g. `modbus.Address(modbus.Memory_4x, 0)` creates `400001` standard address.
    E.g. `modbus.Address(400001)` creates `Address` with type `Modbus::Memory_4x` and offset `0`, and
    `modbus.Address(1)` creates `modbus.Address` with type `modbus.Memory_0x` and offset `0`.
    Class provides convertions from/to string methods.

    Class supports next operators and standard functions:
    +, -, <, <=, >, >=, ==, !=, hash(), str(), int()
    """

    Notation_Default     = 0 ##< Default notation which is equal to Modbus notation
    Notation_Modbus      = 1 ##< Standard Modbus address notation like `000001`, `100001`, `300001`, `400001`
    Notation_IEC61131    = 2 ##< IEC-61131 address notation like `%%Q0`, `%%I0`, `%%IW0`, `%%MW0`
    Notation_IEC61131Hex = 3 ##< IEC-61131 Hex address notation like `%%Q0000h`, `%%I0000h`, `%%IW0000h`, `%%MW0000h`


    ## @brief Python set that contains supported Modbus Address types
    MemoryTypeSet = { MemoryType.Memory_0x, 
                      MemoryType.Memory_1x,
                      MemoryType.Memory_3x,
                      MemoryType.Memory_4x }

    sIEC61131Prefix0x = "%Q"  ##< IEC-61131 address notation prefix for coils
    sIEC61131Prefix1x = "%I"  ##< IEC-61131 address notation prefix for input discretes
    sIEC61131Prefix3x = "%IW" ##< IEC-61131 address notation prefix for input registers
    sIEC61131Prefix4x = "%MW" ##< IEC-61131 address notation prefix for holding registers

    cIEC61131SuffixHex = 'h'  ##< Suffix for IEC-61131 Hex address notation


    ## @brief Python set that contains supported Modbus address IEC61131 prefixes
    IEC61131PrefixMap = {
                    MemoryType.Memory_0x: sIEC61131Prefix0x,
                    MemoryType.Memory_1x: sIEC61131Prefix1x,
                    MemoryType.Memory_3x: sIEC61131Prefix3x,
                    MemoryType.Memory_4x: sIEC61131Prefix4x,
                }

    def __init__(self, value=None, offset=None):
        """
        @brief Constructor of the class.

        @details Can have next forms:
        * `Address()`  - creates invalid address class
        * `Address(MemoryType.Memory_4x, 0)`  - creates address for holding registers with `offset=0`
        * `Address("%MW0")`  - creates address for holding registers with `offset=0`
        * `Address("%Q0000h")`  - creates address for coils with `offset=0`
        * `Address("100001")`  - creates address for input discretes with `offset=0`
        * `Address(300001)`  - creates address for input registers with `offset=0`

        """
        self._type = MemoryType.Memory_Unknown
        self._offset = 0
        if value is None:
            pass
        elif isinstance(value, int) and offset is None:
            self.fromint(value)
        elif isinstance(value, str) and offset is None:
            self.fromstr(value)
        elif isinstance(value, int) and isinstance(offset, int):
            self.settype(value)
            self.setoffset(offset)
        else:
            raise ValueError("Invalid constructor parameters")

    def isvalid(self) -> bool:
        """
        @details Returns `True` if memory type is not `Modbus::Memory_Unknown`, `False` otherwise.
        """
        return self._type != MemoryType.Memory_Unknown

    def type(self) -> int:
        """
        @details Returns memory type of Modbus Data Address.
        """
        return self._type

    def settype(self, tp: int):
        """
        @details Set memory type of Modbus Data Address.
        """
        if tp not in Address.MemoryTypeSet:
            raise ValueError(f"Invalid memory type: {tp}. Memory type must be [0,1,3,4]")
        self._type = tp

    def offset(self) -> int:
        """
        @details Returns memory offset of Modbus Data Address.
        """
        return self._offset

    def setoffset(self, offset: int):
        """
        @details Set memory offset of Modbus Data Address.
        """
        if not (0 <= offset <= 65535):
            raise ValueError(f"Invalid offset: {offset}. Offset must be in range [0:65535]")
        self._offset = offset

    def number(self) -> int:
        """
        @details Returns memory number (offset+1) of Modbus Data Address.
        """
        return self._offset + 1

    def setnumber(self, number: int):
        """
        @details Set memory number (offset+1) of Modbus Data Address.
        """
        self.setoffset(number - 1)

    def fromint(self, v: int):
        """
        @details Make modbus address from integer representaion
        """
        number = v % 100000
        if number < 1 or number > 65536:
            self._type = MemoryType.Memory_Unknown
            self._offset = 0
            raise ValueError(f"Invalid integer '{v}' to convert into Address: number part '{number}' must be [1:65536]")

        mem_type = v // 100000
        if mem_type in Address.MemoryTypeSet:
            self._type = mem_type
            self.setoffset(number - 1)
        else:
            raise ValueError(f"Invalid integer '{v}' to convert into Address: memory type '{mem_type}' must be [0,1,3,4]")

    def toint(self) -> int:
        """
        @details Converts current Modbus Data Address to `int`,
        e.g. `Address(Memory_4x, 0)` will be converted to `400001`.
        """
        return (self._type * 100000) + self.number()

    def fromstr(self, s: str):
        """
        @details Make modbus address from string representaion
        """
        if s.startswith('%'):
            i = 0
            if s.startswith(Address.sIEC61131Prefix3x):
                self._type = MemoryType.Memory_3x
                i = len(Address.sIEC61131Prefix3x)
            elif s.startswith(Address.sIEC61131Prefix4x):
                self._type = MemoryType.Memory_4x
                i = len(Address.sIEC61131Prefix4x)
            elif s.startswith(Address.sIEC61131Prefix0x):
                self._type = MemoryType.Memory_0x
                i = len(Address.sIEC61131Prefix0x)
            elif s.startswith(Address.sIEC61131Prefix1x):
                self._type = MemoryType.Memory_1x
                i = len(Address.sIEC61131Prefix1x)
            else:
                raise ValueError(f"Invalid str '{s}' to convert into Address")

            offset = 0
            suffix = s[-1]
            if suffix == Address.cIEC61131SuffixHex:
                try:
                    for c in s[i:-1]:
                        offset *= 16
                        d = int(c, 16)
                        offset += d
                except ValueError:
                    raise ValueError(f"Invalid value '{s}' to convert into Address: contains non-hex-digit characters")
            else:
                try:
                    for c in s[i:]:
                        offset *= 10
                        d = int(c)
                        offset += d
                except ValueError:
                    raise ValueError(f"Invalid value '{s}' to convert into Address: contains non-dec-digit characters")
            self.setoffset(offset)
        else:
            acc = 0
            try:
                for c in s:
                    d = int(c)
                    acc = acc * 10 + d
            except ValueError:
                raise ValueError(f"Invalid value '{s}' to convert into Address: contains non-dec-digit characters")
            self.fromint(acc)

    def tostr(self, notation: int = Notation_Default) -> str:
        """
        @details Returns string repr of Modbus Data Address with specified notation:
        * `Notation_Modbus`      - `Address(MemoryType.Memory_4x, 0)` will be converted to `"400001"`.
        * `Notation_IEC61131`    - `Address(MemoryType.Memory_4x, 0)` will be converted to `"%MW0"`.
        * `Notation_IEC61131Hex` - `Address(MemoryType.Memory_4x, 0)` will be converted to `"%MW0000h"`.
        """
        def to_dec_string(n, width=0):
            return str(n).rjust(width, '0') if width else str(n)

        def to_hex_string(n):
            return format(n, 'X').rjust(4, '0')

        if not self.isvalid():
            return "Invalid address"

        if notation == Address.Notation_IEC61131:
            return Address.IEC61131PrefixMap.get(self._type, "") + to_dec_string(self._offset)
        elif notation == Address.Notation_IEC61131Hex:
            return Address.IEC61131PrefixMap.get(self._type, "") + to_hex_string(self._offset) + Address.cIEC61131SuffixHex

        else:
            return to_dec_string(self.toint(), 6)

    def __int__(self):
        """
        @details Return the integer representation of the object by calling the toint() method.
        """
        return self.toint()

    def __lt__(self, other):
        """
        @details Return self.toint() < other.toint()
        """
        return self.toint() < other.toint()
    
    def __le__(self, other):
        """
        @details Return self.toint() <= other.toint()
        """
        return self.toint() <= other.toint()

    def __eq__(self, other):
        """
        @details Return self.toint() == other.toint()
        """
        return self.toint() == other.toint()

    def __ne__(self, other):
        """
        @details Return self.toint() != other.toint()
        """
        return self.toint() != other.toint()
    
    def __gt__(self, other):
        """
        @details Return self.toint() > other.toint()
        """
        return self.toint() > other.toint()

    def __ge__(self, other):
        """
        @details Return self.toint() >= other.toint()
        """
        return self.toint() >= other.toint()

    def __hash__(self):
        """
        @details Return the hash of the object.
        """
        return self.toint()

    def __add__(self, other: int):
        """
        @details Return a new Address object with the offset increased by the given integer.
        """
        return Address(self._type, self._offset + other)

    def __sub__(self, other: int):
        """
        @details Return a new Address object with the offset decreased by the given integer.
        """
        return Address(self._type, self._offset - other)

    def __iadd__(self, other: int):
        """
        @details Increase the offset by the given integer.
        """
        self.setoffset(self._offset + other)
        return self
    
    def __isub__(self, other: int):
        """
        @details Decrease the offset by the given integer.
        """
        self.setoffset(self._offset - other)
        return self
    
    def __repr__(self):
        """
        @details Return the string representation of the object.
        """
        return self.tostr(Address.Notation_Default)

    def __str__(self):
        """
        @details Return the string representation of the object.
        """
        return self.tostr(Address.Notation_Default)

class AwaitableMethod:
    """AwaitableMethod helper class for asynchronous operations.
    """
    def __init__(self, meth, *args, **kwargs):
        self._meth = meth
        self._args = args
        self._kwargs = kwargs

    def __await__(self):
        return self
    
    def __next__(self):
        res = self._meth(*self._args, **self._kwargs)
        if res is None:
            return None
        raise StopIteration(res)
        
