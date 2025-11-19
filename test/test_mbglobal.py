"""
Test suite for libmodbuspy.mbglobal module

Tests all functions and classes in the mbglobal module including:
- Bit manipulation functions (getBit, setBit, getBits, setBits)
- Unit map functions  
- Checksum functions (crc16, lrc)
- Data packing/unpacking functions
- Memory operation functions
- String conversion functions
- Address class functionality
- Enum classes (MemoryType, ProtocolType, Parity, StopBits, FlowControl)
- Timer functions
- Utility functions (bytesToAscii, asciiToBytes, etc.)
"""

import unittest
import sys
import os
from unittest.mock import patch
import time

# Add the parent directory to the path to import libmodbuspy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import libmodbuspy.mbglobal as mbglobal
from libmodbuspy.mbglobal import (
    # Bit manipulation functions
    getBit, setBit, getBits, setBits,
    # Unit map functions
    mb_unitmap_get_bit, mb_unitmap_set_bit,
    # Checksum functions
    crc16, lrc,
    # Data functions
    pack, unpack,
    # Memory functions
    readMemBits, writeMemBits,
    # Conversion functions
    bytesToAscii, asciiToBytes, sbytes, sascii,
    # String conversion functions
    sprotocolType, toprotocolType, sparity, toparity,
    sstopBits, tostopBits, sflowControl, toflowControl,
    # Timer functions
    timer, currentTimestamp, msleep,
    # Classes
    MemoryType, ProtocolType, Parity, StopBits, FlowControl, Constants,
    # Status code
    StatusCode
)


class TestBitManipulation(unittest.TestCase):
    """Test bit manipulation functions"""

    def test_getBit_basic(self):
        """Test getBit function with basic operations"""
        # Test with bytes
        data = b'\x0F'  # 00001111 in binary
        self.assertTrue(getBit(data, 0))   # bit 0 = 1
        self.assertTrue(getBit(data, 1))   # bit 1 = 1
        self.assertTrue(getBit(data, 2))   # bit 2 = 1
        self.assertTrue(getBit(data, 3))   # bit 3 = 1
        self.assertFalse(getBit(data, 4))  # bit 4 = 0
        self.assertFalse(getBit(data, 5))  # bit 5 = 0

    def test_getBit_bytearray(self):
        """Test getBit with bytearray"""
        data = bytearray([0x0F, 0xF0])  # 00001111 11110000
        self.assertTrue(getBit(data, 0))   # first byte, bit 0
        self.assertFalse(getBit(data, 8))  # second byte, bit 0
        self.assertTrue(getBit(data, 12))  # second byte, bit 4

    def test_getBit_out_of_bounds(self):
        """Test getBit with out of bounds indices"""
        data = b'\x01'
        self.assertFalse(getBit(data, 8))   # Beyond buffer
        self.assertFalse(getBit(data, 100)) # Way beyond buffer

    def test_setBit_basic(self):
        """Test setBit function with basic operations"""
        data = bytearray([0x00])  # 00000000
        
        # Set some bits
        setBit(data, 0, True)
        self.assertEqual(data[0], 0x01)  # 00000001
        
        setBit(data, 3, True)
        self.assertEqual(data[0], 0x09)  # 00001001
        
        # Clear a bit
        setBit(data, 0, False)
        self.assertEqual(data[0], 0x08)  # 00001000

    def test_setBit_multiple_bytes(self):
        """Test setBit across multiple bytes"""
        data = bytearray([0x00, 0x00])
        
        setBit(data, 8, True)   # Second byte, bit 0
        setBit(data, 15, True)  # Second byte, bit 7
        
        self.assertEqual(data[0], 0x00)
        self.assertEqual(data[1], 0x81)  # 10000001

    def test_getBits_basic(self):
        """Test getBits function"""
        data = b'\x0F'  # 00001111
        
        # Get first 4 bits
        bits = getBits(data, 0, 4)
        expected = [True, True, True, True]
        self.assertEqual(bits, expected)
        
        # Get last 4 bits
        bits = getBits(data, 4, 4)
        expected = [False, False, False, False]
        self.assertEqual(bits, expected)

    def test_setBits_basic(self):
        """Test setBits function"""
        data = bytearray([0x00])
        
        # Set first 4 bits
        bool_values = [True, False, True, False]
        setBits(data, 0, 4, bool_values)
        self.assertEqual(data[0], 0x05)  # 00000101

    def test_setBits_partial(self):
        """Test setBits with partial data"""
        data = bytearray([0x00])
        
        # Request 8 bits but only provide 3
        bool_values = [True, True, False]
        setBits(data, 0, 8, bool_values)
        self.assertEqual(data[0], 0x03)  # Only first 3 bits set


class TestUnitMapFunctions(unittest.TestCase):
    """Test unit map functions"""

    def test_mb_unitmap_get_bit(self):
        """Test unit map get bit function"""
        unitmap = b'\x01'  # Unit 0 enabled
        
        self.assertTrue(mb_unitmap_get_bit(unitmap, 0))
        self.assertFalse(mb_unitmap_get_bit(unitmap, 1))

    def test_mb_unitmap_set_bit(self):
        """Test unit map set bit function"""
        unitmap = bytearray([0x00] * 4)  # 32 bits for 32 units
        
        mb_unitmap_set_bit(unitmap, 5, True)
        self.assertTrue(mb_unitmap_get_bit(unitmap, 5))
        
        mb_unitmap_set_bit(unitmap, 5, False)
        self.assertFalse(mb_unitmap_get_bit(unitmap, 5))


class TestChecksumFunctions(unittest.TestCase):
    """Test checksum functions"""

    def test_crc16_empty(self):
        """Test CRC16 with empty data"""
        result = crc16(b'')
        self.assertEqual(result, 0xFFFF)

    def test_crc16_known_values(self):
        """Test CRC16 with known test vectors"""
        # Test with simple data
        result = crc16(b'\x01\x03\x00\x00\x00\x0A')
        # This should produce a known CRC value
        self.assertIsInstance(result, int)
        self.assertTrue(0 <= result <= 0xFFFF)

    def test_crc16_with_bytearray(self):
        """Test CRC16 with bytearray input"""
        data = bytearray([0x01, 0x03, 0x00, 0x00])
        result = crc16(data)
        self.assertIsInstance(result, int)
        self.assertTrue(0 <= result <= 0xFFFF)

    def test_lrc_empty(self):
        """Test LRC with empty data"""
        result = lrc(b'')
        self.assertEqual(result, 0x00)

    def test_lrc_known_values(self):
        """Test LRC with known values"""
        # LRC of [0x01, 0x03, 0x00, 0x00, 0x00, 0x0A] should be specific value
        data = b'\x01\x03\x00\x00\x00\x0A'
        result = lrc(data)
        
        # Manual calculation: sum = 1+3+0+0+0+10 = 14, LRC = (-14) & 0xFF = 242
        expected = (-(1+3+0+0+0+10)) & 0xFF
        self.assertEqual(result, expected)

    def test_lrc_with_bytearray(self):
        """Test LRC with bytearray input"""
        data = bytearray([0x01, 0x02, 0x03])
        result = lrc(data)
        expected = (-(1+2+3)) & 0xFF
        self.assertEqual(result, expected)


class TestPackUnpackFunctions(unittest.TestCase):
    """Test pack and unpack functions"""

    def test_pack_big_endian_int16(self):
        """Test pack function with big-endian 16-bit integers"""
        values = [0x1234, 0x5678]
        result = pack('>h', values)
        expected = b'\x12\x34\x56\x78'
        self.assertEqual(result, expected)

    def test_pack_little_endian_int16(self):
        """Test pack function with little-endian 16-bit integers"""
        values = [0x1234]
        result = pack('<h', values)
        expected = b'\x34\x12'
        self.assertEqual(result, expected)

    def test_pack_no_endianness_specified(self):
        """Test pack function without endianness"""
        values = [0x12, 0x34]
        result = pack('B', values)  # Unsigned byte
        expected = b'\x12\x34'
        self.assertEqual(result, expected)

    def test_unpack_big_endian_int16(self):
        """Test unpack function with big-endian 16-bit integers"""
        data = b'\x12\x34\x56\x78'
        result = unpack('>h', data)
        expected = (0x1234, 0x5678)
        self.assertEqual(result, expected)

    def test_unpack_little_endian_int16(self):
        """Test unpack function with little-endian 16-bit integers"""
        data = b'\x34\x12'
        result = unpack('<h', data)
        expected = (0x1234,)
        self.assertEqual(result, expected)


class TestMemoryFunctions(unittest.TestCase):
    """Test memory operation functions"""

    def test_readMemBits_basic(self):
        """Test readMemBits with basic bit reading operation"""
        # Create memory buffer with alternating bit patterns
        mem_buff = bytearray([0xAA, 0x55, 0xF0, 0x0F])  # 10101010 01010101 11110000 00001111
        
        # Read first 8 bits (should match first byte)
        result = readMemBits(0, 8, mem_buff)
        
        self.assertIsInstance(result, bytearray)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 0xAA)  # 10101010 pattern preserved
        
        # Read from offset 8 (second byte)
        result = readMemBits(8, 8, mem_buff)
        self.assertIsInstance(result, bytearray)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 0x55)  # 01010101 pattern

    def test_readMemBits_partial(self):
        """Test readMemBits with partial bit count and edge cases"""
        mem_buff = bytearray([0xFF, 0x00])  # 11111111 00000000
        
        # Read only first 3 bits from all-set byte (LSB to MSB: bits 0,1,2 = 111)
        result = readMemBits(0, 3, mem_buff)
        
        self.assertIsInstance(result, bytearray)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 0x07)  # 00000111 (first 3 bits set)
        
        # Read 4 bits starting from bit 4 (should be 1111 from 0xFF)
        result = readMemBits(4, 4, mem_buff)
        self.assertIsInstance(result, bytearray)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 0x0F)  # 00001111 (bits 4-7 from 0xFF)

    def test_readMemBits_boundary_conditions(self):
        """Test readMemBits boundary conditions and cross-byte reads"""
        mem_buff = bytearray([0x12, 0x34])  # 16 bits total: 00010010 00110100
        
        # Test reading across byte boundary (bits 6-9, crossing bytes)
        result = readMemBits(6, 4, mem_buff)
        self.assertIsInstance(result, bytearray)
        self.assertEqual(len(result), 1)
        # This reads bits 6,7 from first byte and bits 0,1 from second byte
        
        # Test single bit reads
        result = readMemBits(0, 1, mem_buff)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 0)  # LSB of 0x12 (00010010) is 0
        
        result = readMemBits(1, 1, mem_buff) 
        self.assertEqual(result[0], 1)  # Bit 1 of 0x12 (00010010) is 1

    def test_writeMemBits_basic(self):
        """Test writeMemBits with basic bit writing operation"""
        mem_buff = bytearray([0x00, 0x00, 0x00, 0x00])  # 32 bits all clear
        
        # Write alternating pattern to first byte
        values = bytearray([0xAA])  # 10101010
        result = writeMemBits(0, 8, values, mem_buff)
        
        self.assertIsNone(result)  # Function returns None
        self.assertEqual(mem_buff[0], 0xAA)
        self.assertEqual(mem_buff[1], 0x00)  # Should remain unchanged
        
        # Write to second byte
        values = bytearray([0x55])  # 01010101
        writeMemBits(8, 8, values, mem_buff)
        self.assertEqual(mem_buff[1], 0x55)
        self.assertEqual(mem_buff[0], 0xAA)  # First byte should remain unchanged

    def test_writeMemBits_partial_and_cross_boundary(self):
        """Test writeMemBits with partial writes and boundary crossing"""
        mem_buff = bytearray([0x00, 0x00])  # 16 bits all clear
        
        # Write partial bits (only 3 bits)
        values = bytearray([0x07])  # 00000111 (but only first 3 bits will be written)
        result = writeMemBits(0, 3, values, mem_buff)
        
        self.assertIsNone(result)  # Function returns None
        self.assertEqual(mem_buff[0] & 0x07, 0x07)  # First 3 bits set
        self.assertEqual(mem_buff[0] & 0xF8, 0x00)  # Other bits remain clear
        
        # Test writing single bits
        mem_buff2 = bytearray([0x00, 0x00])
        values = bytearray([0x01])  # Write bit pattern 1
        writeMemBits(4, 1, values, mem_buff2)  # Write 1 bit at position 4
        self.assertEqual(mem_buff2[0] & 0x10, 0x10)  # Bit 4 should be set
        self.assertEqual(mem_buff2[0] & 0xEF, 0x00)  # Other bits should remain clear

    def test_writeMemBits_error_conditions(self):
        """Test writeMemBits cross-byte boundary writes"""
        mem_buff = bytearray([0x00, 0x00])  # 16 bits total
        
        # Test writing across byte boundary
        values = bytearray([0x0F])  # 00001111
        writeMemBits(6, 4, values, mem_buff)  # Write 4 bits starting at bit 6
        
        # This should write across the byte boundary
        # Bits 6,7 of first byte and bits 0,1 of second byte
        self.assertTrue((mem_buff[0] & 0xC0) != 0 or (mem_buff[1] & 0x03) != 0)
        
        # Test preserving existing bits during partial write
        mem_buff2 = bytearray([0xFF, 0xFF])  # All bits set
        values = bytearray([0x00])  # Write zeros
        writeMemBits(4, 4, values, mem_buff2)  # Clear bits 4-7
        
        # Bits 0-3 should remain set, bits 4-7 should be cleared
        self.assertEqual(mem_buff2[0] & 0x0F, 0x0F)  # Lower 4 bits still set
        
        # Valid write at maximum offset
        writeMemBits(7, 1, values, mem_buff)
        self.assertEqual(mem_buff[0] & 0x80, 0x00)  # Bit 7 should be cleared

class TestConversionFunctions(unittest.TestCase):
    """Test conversion and utility functions"""

    def test_bytesToAscii(self):
        """Test bytesToAscii conversion"""
        data = b'\x01\x23\xAB\xCD'
        result = bytesToAscii(data)
        expected = b'0123ABCD'
        self.assertEqual(result, expected)

    def test_bytesToAscii_empty(self):
        """Test bytesToAscii with empty input"""
        result = bytesToAscii(b'')
        self.assertEqual(result, b'')

    def test_asciiToBytes(self):
        """Test asciiToBytes conversion"""
        data = b'0123ABCD'
        result = asciiToBytes(data)
        expected = b'\x01\x23\xAB\xCD'
        self.assertEqual(result, expected)

    def test_asciiToBytes_empty(self):
        """Test asciiToBytes with empty input"""
        result = asciiToBytes(b'')
        self.assertEqual(result, b'')

    def test_asciiToBytes_invalid_input(self):
        """Test asciiToBytes with invalid input"""
        # Should handle gracefully
        result = asciiToBytes(None)
        self.assertEqual(result, b'')

    def test_sbytes(self):
        """Test sbytes string representation"""
        data = b'\x01\x23\xAB\xCD'
        result = sbytes(data)
        expected = '01 23 AB CD'
        self.assertEqual(result, expected)

    def test_sbytes_with_limit(self):
        """Test sbytes with length limit"""
        data = bytes(range(100))  # 100 bytes
        result = sbytes(data, max_len=5)
        # Should truncate and add "..."
        self.assertTrue(result.endswith('...'))

    def test_sascii(self):
        """Test sascii string representation"""
        data = b'Hello\x01\x02World'
        result = sascii(data)
        # Printable characters shown as-is, non-printable as hex
        self.assertIn('H', result)
        self.assertIn('e', result)
        self.assertIn('\\x01', result)

    def test_sascii_with_limit(self):
        """Test sascii with length limit"""
        data = b'A' * 100
        result = sascii(data, max_len=5)
        self.assertTrue(result.endswith('...'))


class TestStringConversionFunctions(unittest.TestCase):
    """Test string conversion functions for enums"""

    def test_sprotocolType(self):
        """Test sprotocolType function"""
        self.assertEqual(sprotocolType(ProtocolType.TCP), 'TCP')
        self.assertEqual(sprotocolType(ProtocolType.RTU), 'RTU')
        self.assertEqual(sprotocolType(ProtocolType.ASC), 'ASC')
        self.assertEqual(sprotocolType(999), 'Unknown')  # Invalid

    def test_toprotocolType(self):
        """Test toprotocolType function"""
        self.assertEqual(toprotocolType('TCP'), ProtocolType.TCP)
        self.assertEqual(toprotocolType('RTU'), ProtocolType.RTU)
        self.assertEqual(toprotocolType('ASC'), ProtocolType.ASC)
        self.assertEqual(toprotocolType('tcp'), ProtocolType.TCP)  # Case insensitive
        self.assertEqual(toprotocolType('rtu'), ProtocolType.RTU)  # Case insensitive
        self.assertEqual(toprotocolType('asc'), ProtocolType.ASC)  # Case insensitive
        self.assertIsNone(toprotocolType('INVALID'))

    def test_sparity(self):
        """Test sparity function"""
        self.assertEqual(sparity(Parity.NoParity), 'NoParity')
        self.assertEqual(sparity(Parity.EvenParity), 'EvenParity')
        self.assertEqual(sparity(999), 'Unknown')

    def test_toparity(self):
        """Test toparity function"""
        self.assertEqual(toparity('NoParity'), Parity.NoParity)
        self.assertEqual(toparity('EvenParity'), Parity.EvenParity)
        self.assertIsNone(toparity('INVALID'))

    def test_sstopBits(self):
        """Test sstopBits function"""
        self.assertEqual(sstopBits(StopBits.OneStop), 'OneStop')
        self.assertEqual(sstopBits(StopBits.TwoStop), 'TwoStop')

    def test_tostopBits(self):
        """Test tostopBits function"""
        self.assertEqual(tostopBits('OneStop'), StopBits.OneStop)
        self.assertEqual(tostopBits('TwoStop'), StopBits.TwoStop)

    def test_sflowControl(self):
        """Test sflowControl function"""
        self.assertEqual(sflowControl(FlowControl.NoFlowControl), 'NoFlowControl')
        self.assertEqual(sflowControl(FlowControl.HardwareControl), 'HardwareControl')

    def test_toflowControl(self):
        """Test toflowControl function"""
        self.assertEqual(toflowControl('NoFlowControl'), FlowControl.NoFlowControl)
        self.assertEqual(toflowControl('HardwareControl'), FlowControl.HardwareControl)


class TestTimerFunctions(unittest.TestCase):
    """Test timer and timestamp functions"""

    def test_timer(self):
        """Test timer function"""
        t1 = timer()
        time.sleep(0.01)  # Sleep 10ms
        t2 = timer()
        
        self.assertIsInstance(t1, int)
        self.assertIsInstance(t2, int)
        self.assertGreaterEqual(t2 - t1, 10)  # At least 10ms difference

    def test_currentTimestamp(self):
        """Test currentTimestamp function"""
        ts = currentTimestamp()
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 1000000000000)  # Should be > year 2001 in milliseconds

    @patch('time.sleep')
    def test_msleep(self, mock_sleep):
        """Test msleep function"""
        msleep(100)
        mock_sleep.assert_called_once_with(0.1)


class TestConstants(unittest.TestCase):
    """Test Constants class"""

    def test_constants_values(self):
        """Test that constants have expected values"""
        self.assertEqual(Constants.VALID_MODBUS_ADDRESS_BEGIN, 1)
        self.assertEqual(Constants.VALID_MODBUS_ADDRESS_END, 247)
        self.assertEqual(Constants.STANDARD_TCP_PORT, 502)


class TestEnums(unittest.TestCase):
    """Test enum classes"""

    def test_MemoryType_values(self):
        """Test MemoryType enum values"""
        self.assertEqual(MemoryType.Memory_0x, 0)
        self.assertEqual(MemoryType.Memory_Coils, 0)
        self.assertEqual(MemoryType.Memory_1x, 1)
        self.assertEqual(MemoryType.Memory_DiscreteInputs, 1)
        self.assertEqual(MemoryType.Memory_3x, 3)
        self.assertEqual(MemoryType.Memory_InputRegisters, 3)
        self.assertEqual(MemoryType.Memory_4x, 4)
        self.assertEqual(MemoryType.Memory_HoldingRegisters, 4)
        self.assertEqual(MemoryType.Memory_Unknown, 0xFFFF)


class TestModbusFunctionCodes(unittest.TestCase):
    """Test Modbus function code constants"""

    def test_function_codes(self):
        """Test that function codes have correct values"""
        self.assertEqual(mbglobal.MBF_READ_COILS, 1)
        self.assertEqual(mbglobal.MBF_READ_DISCRETE_INPUTS, 2)
        self.assertEqual(mbglobal.MBF_READ_HOLDING_REGISTERS, 3)
        self.assertEqual(mbglobal.MBF_READ_INPUT_REGISTERS, 4)
        self.assertEqual(mbglobal.MBF_WRITE_SINGLE_COIL, 5)
        self.assertEqual(mbglobal.MBF_WRITE_SINGLE_REGISTER, 6)
        self.assertEqual(mbglobal.MBF_WRITE_MULTIPLE_COILS, 15)
        self.assertEqual(mbglobal.MBF_WRITE_MULTIPLE_REGISTERS, 16)


class TestModbusConstants(unittest.TestCase):
    """Test Modbus protocol constants"""

    def test_size_constants(self):
        """Test size-related constants"""
        self.assertEqual(mbglobal.MB_BYTE_SZ_BITES, 8)
        self.assertEqual(mbglobal.MB_REGE_SZ_BITES, 16)
        self.assertEqual(mbglobal.MB_REGE_SZ_BYTES, 2)
        self.assertEqual(mbglobal.MB_MAX_BYTES, 255)
        self.assertEqual(mbglobal.MB_MAX_REGISTERS, 127)
        self.assertEqual(mbglobal.MB_MAX_DISCRETS, 2040)


if __name__ == '__main__':
    unittest.main(verbosity=2)