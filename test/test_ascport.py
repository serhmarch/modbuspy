import unittest
import sys
import os

# Make sure tests can import package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.ascport import ModbusAscPort
from libmodbuspy.mbglobal import ProtocolType, lrc, bytesToAscii, asciiToBytes
from libmodbuspy import exceptions


class TestModbusAscPort(unittest.TestCase):
    """Unit tests for ModbusAscPort (ASCII-specific framing & LRC)"""

    def setUp(self):
        self.port = ModbusAscPort()

    def tearDown(self):
        self.port = None

    def test_type_returns_ascii(self):
        """type() returns ProtocolType.ASC"""
        self.assertEqual(self.port.type(), ProtocolType.ASC)

    def test_writeBuffer_constructs_ascii_frame_and_returns_true(self):
        """writeBuffer should build ASCII frame: ':' + ascii(hex(unit+func+data+LRC)) + CR LF"""
        unit = 0x10
        func = 0x02
        data = b"\x00\x05"

        result = self.port.writeBuffer(unit, func, data)
        self.assertTrue(result)

        buff = self.port._buff
        # starts with ':'
        self.assertEqual(buff[0], ord(':'))
        # ends with CR LF
        self.assertEqual(buff[-2], ord('\r'))
        self.assertEqual(buff[-1], ord('\n'))

        # ascii payload between ':' and CRLF
        ascii_payload = bytes(buff[1:-2])
        ibuff = bytearray()
        ibuff.append(unit)
        ibuff.append(func)
        ibuff.extend(data)
        expected_lrc = lrc(ibuff)
        ibuff.append(expected_lrc)

        # decode ascii payload back to bytes and compare
        decoded = asciiToBytes(ascii_payload)
        self.assertEqual(decoded, bytes(ibuff))

    def test_readBuffer_valid_frame(self):
        """readBuffer returns (unit, func, data) for a valid ASCII frame"""
        unit = 0x01
        func = 0x04
        data = b"\x02\xAA\xBB"

        ibuff = bytearray()
        ibuff.append(unit)
        ibuff.append(func)
        ibuff.extend(data)
        checksum = lrc(ibuff)
        ibuff.append(checksum)

        payload = bytesToAscii(ibuff)
        frame = bytearray()
        frame.append(ord(':'))
        frame.extend(payload)
        frame.append(ord('\r'))
        frame.append(ord('\n'))

        # place frame into port's buffer
        self.port._buff = frame

        # Expect parser to decode and return unit, func, data
        u, f, d = self.port.readBuffer()
        self.assertEqual(u, unit)
        self.assertEqual(f, func)
        self.assertEqual(bytes(d), bytes(data))

    def test_readBuffer_too_small_raises(self):
        """readBuffer should raise NotCorrectResponseError for frames smaller than minimum"""
        # Create an obviously too-small buffer (just ':')
        self.port._buff = bytearray(b":")
        with self.assertRaises(exceptions.NotCorrectResponseError):
            self.port.readBuffer()

    def test_readBuffer_missing_colon_raises(self):
        """Missing leading ':' should raise AscMissColonError"""
        # Build a valid-looking frame but change first character
        unit = 0x01
        func = 0x03
        data = b"\x00\x01"
        ibuff = bytearray([unit, func])
        ibuff.extend(data)
        ibuff.append(lrc(ibuff))
        payload = bytesToAscii(ibuff)
        frame = bytearray()
        frame.append(ord('#'))  # wrong start symbol
        frame.extend(payload)
        frame.append(ord('\r'))
        frame.append(ord('\n'))

        self.port._buff = frame
        with self.assertRaises(exceptions.AscMissColonError):
            self.port.readBuffer()

    def test_readBuffer_missing_crlf_raises(self):
        """Missing CRLF should raise AscMissCrLfError"""
        unit = 0x01
        func = 0x03
        data = b"\x00\x01"
        ibuff = bytearray([unit, func])
        ibuff.extend(data)
        ibuff.append(lrc(ibuff))
        payload = bytesToAscii(ibuff)
        frame = bytearray()
        frame.append(ord(':'))
        frame.extend(payload)
        # omit CRLF

        self.port._buff = frame
        with self.assertRaises(exceptions.AscMissCrLfError):
            self.port.readBuffer()

    def test_readBuffer_bad_ascii_raises(self):
        """Non-hex ASCII payload should raise AscCharError"""
        frame = bytearray()
        frame.append(ord(':'))
        frame.extend(b"GARBAGE")  # invalid hex
        frame.append(ord('\r'))
        frame.append(ord('\n'))
        self.port._buff = frame
        with self.assertRaises(exceptions.AscCharError):
            self.port.readBuffer()

    def test_readBuffer_wrong_lrc_raises(self):
        """Incorrect LRC checksum should raise LrcError"""
        unit = 0x02
        func = 0x06
        data = b"\x00\x02"
        ibuff = bytearray([unit, func])
        ibuff.extend(data)
        # append incorrect checksum
        ibuff.append((lrc(ibuff) ^ 0xFF) & 0xFF)

        payload = bytesToAscii(ibuff)
        frame = bytearray()
        frame.append(ord(':'))
        frame.extend(payload)
        frame.append(ord('\r'))
        frame.append(ord('\n'))

        self.port._buff = frame
        with self.assertRaises(exceptions.LrcError):
            self.port.readBuffer()


if __name__ == '__main__':
    unittest.main()
