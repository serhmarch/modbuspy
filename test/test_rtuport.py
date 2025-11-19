import unittest
import sys
import os

# Make sure tests can import package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.rtuport import ModbusRtuPort
from libmodbuspy.mbglobal import ProtocolType, crc16
from libmodbuspy import exceptions


class TestModbusRtuPort(unittest.TestCase):
    """Unit tests for ModbusRtuPort (RTU-specific framing & CRC)"""

    def setUp(self):
        self.port = ModbusRtuPort()

    def tearDown(self):
        self.port = None

    def test_type_returns_rtu(self):
        """type() returns ProtocolType.RTU"""
        self.assertEqual(self.port.type(), ProtocolType.RTU)

    def test_writeBuffer_constructs_crc_and_returns_true(self):
        """writeBuffer should build buffer: unit, func, data, CRC16 (little-endian)"""
        unit = 0x11
        func = 0x03
        data = b"\x00\x10\x00\x02"

        result = self.port.writeBuffer(unit, func, data)
        self.assertTrue(result)

        buff = self.port._buff
        # Buffer length = 1(unit)+1(func)+len(data)+2(crc)
        self.assertEqual(len(buff), 1 + 1 + len(data) + 2)
        self.assertEqual(buff[0], unit)
        self.assertEqual(buff[1], func)
        self.assertEqual(bytes(buff[2:2+len(data)]), data)

        # Verify CRC matches crc16 of first bytes (unit+func+data)
        crc_from_buff = buff[-2] | (buff[-1] << 8)
        expected_crc = crc16(buff[:-2])
        self.assertEqual(crc_from_buff, expected_crc)

    def test_readBuffer_valid_frame(self):
        """readBuffer returns (unit, func, data) for a valid RTU frame"""
        unit = 0x01
        func = 0x04
        data = b"\x02\xAA\xBB"
        frame = bytearray()
        frame.append(unit)
        frame.append(func)
        frame.extend(data)
        crc = crc16(frame)
        frame.extend(crc.to_bytes(2, 'little'))

        # place frame into port's buffer
        self.port._buff = frame

        u, f, d = self.port.readBuffer()
        self.assertEqual(u, unit)
        self.assertEqual(f, func)
        self.assertEqual(bytes(d), bytes(data))

    def test_readBuffer_too_small_raises(self):
        """readBuffer should raise NotCorrectResponseError for frames smaller than 4 bytes"""
        self.port._buff = bytearray(b"\x01\x02")  # only 2 bytes
        with self.assertRaises(exceptions.NotCorrectResponseError):
            self.port.readBuffer()

    def test_readBuffer_wrong_crc_raises(self):
        """readBuffer should raise NotCorrectResponseError when CRC is invalid"""
        unit = 0x01
        func = 0x06
        data = b"\x00\x01\x00\x02"
        frame = bytearray()
        frame.append(unit)
        frame.append(func)
        frame.extend(data)
        # append an incorrect CRC (zero)
        frame.extend((0).to_bytes(2, 'little'))

        self.port._buff = frame
        with self.assertRaises(exceptions.NotCorrectResponseError):
            self.port.readBuffer()


if __name__ == '__main__':
    unittest.main()
