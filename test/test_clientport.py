import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modbuspy.clientport import ModbusClientPort
from modbuspy.port import ModbusPort
from modbuspy.statuscode import StatusCode
from modbuspy.mbglobal import ProtocolType
from modbuspy import exceptions


class MockPort(ModbusPort):
    """Mock port for testing ModbusClientPort"""
    def __init__(self):
        super().__init__(blocking=True)
        self._is_open = False
    
    def type(self) -> ProtocolType:
        return ProtocolType.TCP
    
    def handle(self) -> int:
        return 0
    
    def isOpen(self) -> bool:
        return self._is_open
    
    def open(self) -> StatusCode:
        self._is_open = True
        return StatusCode.Status_Good
    
    def close(self) -> StatusCode:
        self._is_open = False
        return StatusCode.Status_Good
    
    def write(self) -> StatusCode:
        return StatusCode.Status_Good
    
    def read(self) -> StatusCode:
        return StatusCode.Status_Good
    
    def writeBuffer(self, unit: int, func: int, data: bytes):
        pass
    
    def readBuffer(self):
        return (1, 3, b'\x00\x01')


class TestModbusClientPort(unittest.TestCase):
    """Unit tests for ModbusClientPort class"""

    def setUp(self):
        self.mock_port = MockPort()
        self.client_port = ModbusClientPort(self.mock_port)

    def tearDown(self):
        self.client_port = None
        self.mock_port = None

    def test_initialization(self):
        """ModbusClientPort initialization sets up port and signals"""
        self.assertIs(self.client_port._port, self.mock_port)
        self.assertEqual(self.client_port._unit, 0)
        self.assertEqual(self.client_port._settings_tries, 1)
        self.assertTrue(self.client_port._settings_broadcastEnabled)
        self.assertFalse(self.mock_port.isServerMode())

    def test_port_property(self):
        """port() and setPort() methods work correctly"""
        self.assertIs(self.client_port.port(), self.mock_port)
        new_port = MockPort()
        self.client_port.setPort(new_port)
        self.assertIs(self.client_port.port(), new_port)

    def test_type_returns_port_type(self):
        """type() returns underlying port type"""
        self.assertEqual(self.client_port.type(), ProtocolType.TCP)

    def test_open_delegates_to_port(self):
        """open() delegates to underlying port"""
        result = self.client_port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertTrue(self.client_port.isOpen())

    def test_close_delegates_to_port(self):
        """close() delegates to underlying port"""
        self.client_port.open()
        result = self.client_port.close()
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertFalse(self.client_port.isOpen())

    def test_isOpen_reflects_port_state(self):
        """isOpen() reflects underlying port state"""
        self.assertFalse(self.client_port.isOpen())
        self.client_port.open()
        self.assertTrue(self.client_port.isOpen())

    def test_tries_getter_setter(self):
        """tries() and setTries() manage retry count"""
        self.assertEqual(self.client_port.tries(), 1)
        self.client_port.setTries(3)
        self.assertEqual(self.client_port.tries(), 3)

    def test_repeatCount_backward_compatibility(self):
        """repeatCount() is alias for tries()"""
        self.client_port.setRepeatCount(5)
        self.assertEqual(self.client_port.repeatCount(), 5)
        self.assertEqual(self.client_port.tries(), 5)

    def test_broadcast_enabled_default(self):
        """Broadcast is enabled by default"""
        self.assertTrue(self.client_port.isBroadcastEnabled())

    def test_broadcast_setter(self):
        """setBroadcastEnabled() toggles broadcast mode"""
        self.client_port.setBroadcastEnabled(False)
        self.assertFalse(self.client_port.isBroadcastEnabled())
        self.client_port.setBroadcastEnabled(True)
        self.assertTrue(self.client_port.isBroadcastEnabled())

    def test_signal_creation(self):
        """Client port has signal objects for events"""
        self.assertIsNotNone(self.client_port.signalOpened)
        self.assertIsNotNone(self.client_port.signalClosed)
        self.assertIsNotNone(self.client_port.signalError)
        self.assertIsNotNone(self.client_port.signalTx)
        self.assertIsNotNone(self.client_port.signalRx)

    def test_port_server_mode_set_false(self):
        """Client port sets underlying port to client mode"""
        self.assertFalse(self.mock_port.isServerMode())


if __name__ == '__main__':
    unittest.main()
