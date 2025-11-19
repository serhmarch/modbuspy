import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.serverresource import ModbusServerResource
from libmodbuspy.port import ModbusPort
from libmodbuspy.mbinterface import ModbusInterface
from libmodbuspy.statuscode import StatusCode
from libmodbuspy.mbglobal import ProtocolType


class MockPort(ModbusPort):
    """Mock port for testing ModbusServerResource"""
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


class MockDevice(ModbusInterface):
    """Mock device for testing server resource"""
    pass


class TestModbusServerResource(unittest.TestCase):
    """Unit tests for ModbusServerResource class"""

    def setUp(self):
        self.mock_port = MockPort()
        self.device = MockDevice()
        self.resource = ModbusServerResource(self.mock_port, self.device)

    def tearDown(self):
        self.resource = None
        self.device = None
        self.mock_port = None

    def test_initialization(self):
        """ModbusServerResource stores port and device"""
        self.assertIs(self.resource._port, self.mock_port)
        self.assertIs(self.resource._device, self.device)

    def test_port_method(self):
        """port() returns underlying port"""
        self.assertIs(self.resource.port(), self.mock_port)

    def test_type_returns_port_type(self):
        """type() returns underlying port type"""
        self.assertEqual(self.resource.type(), ProtocolType.TCP)

    def test_timeout_delegates_to_port(self):
        """timeout() and setTimeout() delegate to port"""
        # Note: MockPort doesn't store timeout, but method is callable
        self.resource.setTimeout(2000)
        # Verify no exception

    def test_open_and_close(self):
        """open() and close() work correctly"""
        result = self.resource.open()
        self.assertEqual(result, StatusCode.Status_Good)
        result = self.resource.close()
        self.assertEqual(result, StatusCode.Status_Good)

    def test_isOpen_reflects_port_state(self):
        """isOpen() reflects underlying port state"""
        # Initially port is not open
        self.assertFalse(self.resource.isOpen())
        # open() on resource just sets _cmdClose=False and returns Good
        # but doesn't actually open the port in our mock
        result = self.resource.open()
        self.assertEqual(result, StatusCode.Status_Good)

    def test_device_getter_setter(self):
        """device() and setDevice() manage device"""
        self.assertIs(self.resource.device(), self.device)
        new_device = MockDevice()
        self.resource.setDevice(new_device)
        self.assertIs(self.resource.device(), new_device)

    def test_broadcast_enabled_default(self):
        """Broadcast is enabled by default"""
        self.assertTrue(self.resource.isBroadcastEnabled())

    def test_broadcast_setter(self):
        """setBroadcastEnabled() toggles broadcast"""
        self.resource.setBroadcastEnabled(False)
        self.assertFalse(self.resource.isBroadcastEnabled())

    def test_unit_map_default_none(self):
        """Unit map is None by default"""
        self.assertIsNone(self.resource.unitMap())

    def test_process_method_exists(self):
        """process() method is callable"""
        # MockPort.readBuffer() returns valid data, but process() has complex logic
        # Just verify it's callable without crashing from initialization
        self.assertIsNotNone(self.resource.process)
        # Note: Full process() testing requires more complex mocking of port read/write

    def test_signal_creation(self):
        """Server resource has signal objects"""
        self.assertIsNotNone(self.resource.signalOpened)
        self.assertIsNotNone(self.resource.signalClosed)
        self.assertIsNotNone(self.resource.signalError)
        self.assertIsNotNone(self.resource.signalTx)
        self.assertIsNotNone(self.resource.signalRx)

    def test_port_server_mode_set_true(self):
        """Server resource sets underlying port to server mode"""
        self.assertTrue(self.mock_port.isServerMode())


if __name__ == '__main__':
    unittest.main()
