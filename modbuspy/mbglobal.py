"""
@file mbglobal.py
@brief Contains general definitions of the Modbus library for Python.

This module provides the core functionality for the ModbusPy library including:
- Status codes and error handling
- Protocol type definitions (TCP, RTU, ASCII)
- Memory type definitions (coils, discrete inputs, holding registers, input registers)
- Configuration structures for TCP and serial communications
- Utility functions for CRC16/LRC checksums and data conversion
- Base ModbusInterface class defining the Modbus protocol methods
- Address class for Modbus address representation and conversion

@author serhmarch
@date November 2025
@version 1.0.0
"""

import time
from enum import IntEnum
from typing import Optional, Union, List, Tuple
from dataclasses import dataclass

from .mbconfig import *
from .statuscode import StatusCode

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

def read_mem_regs(offset: int, count: int, mem_buff: Union[bytes, bytearray], 
                  mem_reg_count: int) -> Tuple[StatusCode, bytes, int]:
    """Function for copy (read) values from memory input `mem_buff` and put it to the output buffer for 16 bit registers.
    
    Args:
        offset: Memory offset to read from `mem_buff` in 16-bit registers size.
        count: Count of 16-bit registers to read from memory `mem_buff`.
        mem_buff: Memory buffer which holds data.
        mem_reg_count: Size of memory buffer `mem_buff` in 16-bit registers.
    
    Returns:
        Tuple of (StatusCode, values_bytes, actual_count)
    """
    if offset >= mem_reg_count:
        return StatusCode.Status_BadIllegalDataAddress, b'', 0
    
    actual_count = min(count, mem_reg_count - offset)
    if actual_count <= 0:
        return StatusCode.Status_BadIllegalDataAddress, b'', 0
    
    start_byte = offset * 2
    end_byte = start_byte + (actual_count * 2)
    
    if end_byte > len(mem_buff):
        return StatusCode.Status_BadIllegalDataAddress, b'', 0
    
    values = mem_buff[start_byte:end_byte]
    return StatusCode.Status_Good, values, actual_count

def write_mem_regs(offset: int, count: int, values: Union[bytes, bytearray], 
                   mem_buff: bytearray, mem_reg_count: int) -> Tuple[StatusCode, int]:
    """Function for copy (write) values from input buffer `values` to memory `mem_buff` for 16 bit registers.
    
    Args:
        offset: Memory offset to write to `mem_buff` in 16-bit registers size.
        count: Count of 16-bit registers to write into memory `mem_buff`.
        values: Input buffer that holds data to write.
        mem_buff: Memory buffer.
        mem_reg_count: Size of memory buffer `mem_buff` in 16-bit registers.
    
    Returns:
        Tuple of (StatusCode, actual_count)
    """
    if offset >= mem_reg_count:
        return StatusCode.Status_BadIllegalDataAddress, 0
    
    actual_count = min(count, mem_reg_count - offset)
    if actual_count <= 0:
        return StatusCode.Status_BadIllegalDataAddress, 0
    
    start_byte = offset * 2
    values_needed = actual_count * 2
    
    if len(values) < values_needed:
        return StatusCode.Status_BadIllegalDataValue, 0
    
    if start_byte + values_needed > len(mem_buff):
        return StatusCode.Status_BadIllegalDataAddress, 0
    
    mem_buff[start_byte:start_byte + values_needed] = values[:values_needed]
    return StatusCode.Status_Good, actual_count

def read_mem_bits(offset: int, count: int, mem_buff: Union[bytes, bytearray], 
                  mem_bit_count: int) -> Tuple[StatusCode, bytes, int]:
    """Function for copy (read) values from memory input `mem_buff` and put it to the output buffer for discretes (bits).
    
    Args:
        offset: Memory offset to read from `mem_buff` in bit size.
        count: Count of bits to read from memory `mem_buff`.
        mem_buff: Memory buffer which holds data.
        mem_bit_count: Size of memory buffer `mem_buff` in bits.
    
    Returns:
        Tuple of (StatusCode, values_bytes, actual_count)
    """
    if offset >= mem_bit_count:
        return StatusCode.Status_BadIllegalDataAddress, b'', 0
    
    actual_count = min(count, mem_bit_count - offset)
    if actual_count <= 0:
        return StatusCode.Status_BadIllegalDataAddress, b'', 0
    
    # Calculate how many bytes we need for the output
    bytes_needed = (actual_count + 7) // 8
    result = bytearray(bytes_needed)
    
    # Get the bits and pack them into bytes
    for i in range(actual_count):
        if getBit(mem_buff, offset + i):
            byte_index = i // 8
            bit_index = i % 8
            result[byte_index] |= (1 << bit_index)
    
    return StatusCode.Status_Good, bytes(result), actual_count

def write_mem_bits(offset: int, count: int, values: Union[bytes, bytearray], 
                   mem_buff: bytearray, mem_bit_count: int) -> Tuple[StatusCode, int]:
    """Function for copy (write) values from input buffer `values` to memory `mem_buff` for discretes (bits).
    
    Args:
        offset: Memory offset to write to `mem_buff` in bit size.
        count: Count of bits to write into memory `mem_buff`.
        values: Input buffer that holds data to write.
        mem_buff: Memory buffer.
        mem_bit_count: Size of memory buffer `mem_buff` in bits.
    
    Returns:
        Tuple of (StatusCode, actual_count)
    """
    if offset >= mem_bit_count:
        return StatusCode.Status_BadIllegalDataAddress, 0
    
    actual_count = min(count, mem_bit_count - offset)
    if actual_count <= 0:
        return StatusCode.Status_BadIllegalDataAddress, 0
    
    # Set the bits from the input values
    for i in range(actual_count):
        byte_index = i // 8
        bit_index = i % 8
        if byte_index < len(values):
            bit_value = (values[byte_index] & (1 << bit_index)) != 0
            setBit(mem_buff, offset + i, bit_value)
    
    return StatusCode.Status_Good, actual_count

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
        * `Address(Memory_4x, 0)`  - creates address for holding registers with `offset=0`
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
        def dec_digit(c):
            return int(c) if c.isdigit() else -1

        def hex_digit(c):
            try:
                return int(c, 16)
            except ValueError:
                return -1

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
                for c in s[i:-1]:
                    offset *= 16
                    d = hex_digit(c)
                    if d < 0:
                        return Address()
                    offset += d
            else:
                for c in s[i:]:
                    offset *= 10
                    d = dec_digit(c)
                    if d < 0:
                        return Address()
                    offset += d
            self.setoffset(offset)
        else:
            acc = 0
            for c in s:
                d = dec_digit(c)
                if d < 0:
                    return Address()
                acc = acc * 10 + d
            self.fromint(acc)

    def tostr(self, notation: int = Notation_Default) -> str:
        """
        @details Returns string repr of Modbus Data Address with specified notation:
        * `Notation_Modbus`      - `Address(Memory_4x, 0)` will be converted to `"400001"`.
        * `Notation_IEC61131`    - `Address(Memory_4x, 0)` will be converted to `"%MW0"`.
        * `Notation_IEC61131Hex` - `Address(Memory_4x, 0)` will be converted to `"%MW0000h"`.
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

class ModbusInterface:
    """Main interface of Modbus communication protocol.
    
    `ModbusInterface` contains list of functions that modbuspy is supported.
    There are such functions as:
    * 1  (0x01) - `READ_COILS`
    * 2  (0x02) - `READ_DISCRETE_INPUTS`  
    * 3  (0x03) - `READ_HOLDING_REGISTERS`
    * 4  (0x04) - `READ_INPUT_REGISTERS`
    * 5  (0x05) - `WRITE_SINGLE_COIL`
    * 6  (0x06) - `WRITE_SINGLE_REGISTER`
    * 7  (0x07) - `READ_EXCEPTION_STATUS`
    * 8  (0x08) - `DIAGNOSTICS`
    * 11 (0x0B) - `GET_COMM_EVENT_COUNTER`
    * 12 (0x0C) - `GET_COMM_EVENT_LOG`
    * 15 (0x0F) - `WRITE_MULTIPLE_COILS`
    * 16 (0x10) - `WRITE_MULTIPLE_REGISTERS`
    * 17 (0x11) - `REPORT_SERVER_ID`
    * 22 (0x16) - `MASK_WRITE_REGISTER`
    * 23 (0x17) - `READ_WRITE_MULTIPLE_REGISTERS`
    * 24 (0x18) - `READ_FIFO_QUEUE`
    
    Each method returns `Modbus::StatusCode` for result. Default implementations
    return `Status_BadIllegalFunction`.
    """
    
    def readCoils(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read discrete outputs (coils, 0x bits).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of coils (bits).
            
        Returns:
            Tuple of (StatusCode, values) where values is a bit array with read values.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
    
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read digital inputs (1x bits).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of inputs (bits).
            
        Returns:
            Tuple of (StatusCode, values) where values is a bit array with read values.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read holding (output) 16-bit registers (4x regs).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of registers.
            
        Returns:
            Tuple of (StatusCode, values) where values is a list of 16-bit integers.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read input 16-bit registers (3x regs).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of registers.
            
        Returns:
            Tuple of (StatusCode, values) where values is a list of 16-bit integers.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> bool:
        """Function for write one separate discrete output (0x coil).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            value: Boolean value to be set.
            
        Returns:
            The result StatusCode of the operation.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction
        
    def writeSingleRegister(self, unit: int, offset: int, value: int) -> bool:
        """Function for write one separate 16-bit holding register (4x).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            value: 16-bit unsigned integer value to be set.
            
        Returns:
            The result StatusCode of the operation.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction
        
    def readExceptionStatus(self, unit: int) -> int:
        """Function to read ExceptionStatus.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            Tuple of (StatusCode, status) where status is a byte with exception status.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def diagnostics(self, unit: int, subfunc: int, indata: Optional[bytes] = None) -> bytes:
        """Function provides a series of tests for checking the communication system
        between a client device and a server, or for checking various internal error
        conditions within a server.
        
        Args:
            unit: Address of the remote Modbus device.
            subfunc: Subfunction code.
            indata: Input data buffer for the diagnostic function.
            
        Returns:
            Tuple of (StatusCode, outdata) where outdata is the output data buffer.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def getCommEventCounter(self, unit: int) -> int:
        """Function is used to get a status word and an event count from the
        remote device's communication event counter.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            Tuple of (StatusCode, status, eventCount).
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None, None
        
    def getCommEventLog(self, unit: int) -> bytes:
        """Function is used to get a status word, event count, message count and event log
        from the remote device's communication event counter.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            Tuple of (StatusCode, status, eventCount, messageCount, eventBuff).
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None, None, None, None
        
    def writeMultipleCoils(self, unit: int, offset: int, count: int, values: bytes) -> bool:
        """Function for write coils (discrete outputs, 1-bit values) (0x data).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of coils (bits).
            values: Input buffer (bit array) which values must be written.
            
        Returns:
            The result StatusCode of the operation.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction
        
    def writeMultipleRegisters(self, unit: int, offset: int, count: int, values: bytes) -> bool:
        """Function for write holding (output) 16-bit registers (4x regs).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of registers.
            values: Input buffer which values must be written.
            
        Returns:
            The result StatusCode of the operation.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction
        
    def reportServerID(self, unit: int) -> bytes:
        """Function to read the description of the type, the current status,
        and other information specific to a remote device.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            Tuple of (StatusCode, data) where data contains server identification.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> bool:
        """Function is used to modify the contents of a specified holding register
        using a combination of an AND mask, an OR mask, and the register's current contents.
        The function's algorithm is:
        Result = (Current Contents AND And_Mask) OR (Or_Mask AND (NOT And_Mask))
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            and_mask: 16-bit unsigned integer value AND mask.
            or_mask: 16-bit unsigned integer value OR mask.
            
        Returns:
            The result StatusCode of the operation.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction
        
    def readWritMultipleRegisters(self, unit: int, readOffset: int, readCount: int,
                                  writeOffset: int, writeCount: int, writeValues: bytes) -> bytes:
        """This function code performs a combination of one read operation and one
        write operation in a single MODBUS transaction.
        
        Args:
            unit: Address of the remote Modbus device.
            read_offset: Starting offset for read (0-based).
            read_count: Count of registers to read.
            write_offset: Starting offset for write (0-based).
            write_count: Count of registers to write.
            write_values: Input buffer which values must be written.
            
        Returns:
            Tuple of (StatusCode, read_values) where read_values contains the read registers.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None
        
    def readFIFOQueue(self, unit: int, fifoadr: int) -> bytes:
        """Function for read the contents of a First-In-First-Out (FIFO) queue
        of register in a remote device.
        
        Args:
            unit: Address of the remote Modbus device.
            fifo_addr: Address of FIFO (0-based).
            
        Returns:
            Tuple of (StatusCode, values) where values contains the FIFO queue contents.
            Default implementation returns Status_BadIllegalFunction.
        """
        return StatusCode.Status_BadIllegalFunction, None

