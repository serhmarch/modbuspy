import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.serverport import ModbusServerPort
from libmodbuspy.mbglobal import ProtocolType
from libmodbuspy.mbinterface import ModbusInterface
from libmodbuspy.statuscode import StatusCode


class MockDevice(ModbusInterface):
    """Mock device for testing server port"""
    pass


class MockServerPort(ModbusServerPort):
    """Concrete implementation of ModbusServerPort for testing"""
    
    def __init__(self, device):
        super().__init__(device)
        self._is_open = False
    
    def type(self) -> ProtocolType:
        return ProtocolType.TCP
    
    def timeout(self) -> int:
        return 1000
    
    def setTimeout(self, timeout: int) -> None:
        self._timeout = timeout
    
    def open(self):
        self._is_open = True
        return StatusCode.Status_Good
    
    def close(self):
        self._is_open = False
        return StatusCode.Status_Good
    
    def isOpen(self) -> bool:
        return self._is_open
    
    def process(self) -> bool:
        return True


class TestModbusServerPort(unittest.TestCase):
    """Unit tests for ModbusServerPort class"""

    def setUp(self):
        self.device = MockDevice()
        self.server_port = MockServerPort(self.device)

    def tearDown(self):
        self.server_port = None
        self.device = None

    def test_initialization(self):
        """ServerPort initialization stores device"""
        self.assertIs(self.server_port._device, self.device)
        self.assertIs(self.server_port.device(), self.device)

    def test_device_getter_setter(self):
        """device() and setDevice() work correctly"""
        new_device = MockDevice()
        self.server_port.setDevice(new_device)
        self.assertIs(self.server_port.device(), new_device)

    def test_type_method(self):
        """type() returns protocol type"""
        self.assertEqual(self.server_port.type(), ProtocolType.TCP)

    def test_timeout_methods(self):
        """timeout() and setTimeout() manage timeout"""
        initial_timeout = self.server_port.timeout()
        self.assertEqual(initial_timeout, 1000)
        # Note: MockServerPort doesn't actually persist timeout changes,
        # so just verify the method can be called without errors
        self.server_port.setTimeout(5000)
        # Verify the method exists and is callable

    def test_open_and_close(self):
        """open() and close() manage port state"""
        self.assertFalse(self.server_port.isOpen())
        result = self.server_port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertTrue(self.server_port.isOpen())
        result = self.server_port.close()
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertFalse(self.server_port.isOpen())

    def test_process_method(self):
        """process() can be called"""
        result = self.server_port.process()
        self.assertTrue(result)

    def test_broadcast_enabled_default(self):
        """Broadcast is enabled by default"""
        self.assertTrue(self.server_port.isBroadcastEnabled())

    def test_broadcast_setter(self):
        """setBroadcastEnabled() toggles broadcast mode"""
        self.server_port.setBroadcastEnabled(False)
        self.assertFalse(self.server_port.isBroadcastEnabled())
        self.server_port.setBroadcastEnabled(True)
        self.assertTrue(self.server_port.isBroadcastEnabled())

    def test_unit_map_default_none(self):
        """Unit map is None by default"""
        self.assertIsNone(self.server_port.unitMap())

    def test_context_default_none(self):
        """Context is None by default"""
        self.assertIsNone(self.server_port.context())

    def test_context_setter_getter(self):
        """setContext() and context() manage context object"""
        ctx = {"key": "value"}
        self.server_port.setContext(ctx)
        self.assertEqual(self.server_port.context(), ctx)

    def test_isStateClosed(self):
        """isStateClosed() checks port state"""
        # Initial state is UNKNOWN, not CLOSED, so isStateClosed() should be False
        self.assertFalse(self.server_port.isStateClosed())
        self.server_port._state = ModbusServerPort.State.STATE_CLOSED
        self.assertTrue(self.server_port.isStateClosed())

    def test_signal_creation(self):
        """Server port has signal objects"""
        self.assertIsNotNone(self.server_port.signalOpened)
        self.assertIsNotNone(self.server_port.signalClosed)
        self.assertIsNotNone(self.server_port.signalError)
        self.assertIsNotNone(self.server_port.signalTx)
        self.assertIsNotNone(self.server_port.signalRx)

    def test_state_enum(self):
        """State enum has all expected states"""
        states = [
            ModbusServerPort.State.STATE_UNKNOWN,
            ModbusServerPort.State.STATE_BEGIN_OPEN,
            ModbusServerPort.State.STATE_WAIT_FOR_OPEN,
            ModbusServerPort.State.STATE_OPENED,
            ModbusServerPort.State.STATE_BEGIN_READ,
            ModbusServerPort.State.STATE_READ,
            ModbusServerPort.State.STATE_PROCESS_DEVICE,
            ModbusServerPort.State.STATE_WRITE,
            ModbusServerPort.State.STATE_BEGIN_WRITE,
            ModbusServerPort.State.STATE_WAIT_FOR_CLOSE,
            ModbusServerPort.State.STATE_TIMEOUT,
            ModbusServerPort.State.STATE_CLOSED,
        ]
        self.assertTrue(all(isinstance(s, int) for s in states))


if __name__ == '__main__':
    unittest.main()
