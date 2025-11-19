import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.clientport import ModbusClientPort, ModbusAsyncClientPort
from libmodbuspy.port import ModbusPort
from libmodbuspy.statuscode import StatusCode
from libmodbuspy.mbglobal import ProtocolType
from libmodbuspy import exceptions
from libmodbuspy.mbglobal import AwaitableMethod

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

class TestModbusAsyncClientPort(unittest.TestCase):
    """Unit tests for ModbusAsyncClientPort class"""

    def setUp(self):
        """Set up test fixtures for async client port"""
        from libmodbuspy.port import ModbusPort
        from libmodbuspy.mbglobal import ProtocolType
        from libmodbuspy.statuscode import StatusCode
        
        # Create a minimal mock port
        class MockAsyncPort(ModbusPort):
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
        
        self.mock_port = MockAsyncPort()
        self.async_port = ModbusAsyncClientPort(self.mock_port)

    def tearDown(self):
        self.async_port = None
        self.mock_port = None

    def test_initialization_sets_nonblocking(self):
        """ModbusAsyncClientPort initialization sets port to non-blocking mode"""
        # The port should be set to non-blocking in __init__
        self.assertFalse(self.mock_port.isBlocking())

    def test_open_returns_awaitable(self):
        """open() returns AwaitableMethod"""
        result = self.async_port.open()
        self.assertIsInstance(result, AwaitableMethod)

    def test_close_returns_awaitable(self):
        """close() returns AwaitableMethod"""
        result = self.async_port.close()
        self.assertIsInstance(result, AwaitableMethod)

    def test_readCoils_returns_awaitable(self):
        """readCoils() returns AwaitableMethod"""
        result = self.async_port.readCoils(unit=1, offset=0, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readDiscreteInputs_returns_awaitable(self):
        """readDiscreteInputs() returns AwaitableMethod"""
        result = self.async_port.readDiscreteInputs(unit=1, offset=0, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readHoldingRegisters_returns_awaitable(self):
        """readHoldingRegisters() returns AwaitableMethod"""
        result = self.async_port.readHoldingRegisters(unit=1, offset=0, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readInputRegisters_returns_awaitable(self):
        """readInputRegisters() returns AwaitableMethod"""
        result = self.async_port.readInputRegisters(unit=1, offset=0, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_writeSingleCoil_returns_awaitable(self):
        """writeSingleCoil() returns AwaitableMethod"""
        result = self.async_port.writeSingleCoil(unit=1, offset=10, value=True)
        self.assertIsInstance(result, AwaitableMethod)

    def test_writeSingleRegister_returns_awaitable(self):
        """writeSingleRegister() returns AwaitableMethod"""
        result = self.async_port.writeSingleRegister(unit=1, offset=20, value=100)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readExceptionStatus_returns_awaitable(self):
        """readExceptionStatus() returns AwaitableMethod"""
        result = self.async_port.readExceptionStatus(unit=1)
        self.assertIsInstance(result, AwaitableMethod)

    def test_diagnostics_returns_awaitable(self):
        """diagnostics() returns AwaitableMethod"""
        result = self.async_port.diagnostics(unit=1, subfunc=0, indata=None)
        self.assertIsInstance(result, AwaitableMethod)

    def test_getCommEventCounter_returns_awaitable(self):
        """getCommEventCounter() returns AwaitableMethod"""
        result = self.async_port.getCommEventCounter(unit=1)
        self.assertIsInstance(result, AwaitableMethod)

    def test_getCommEventLog_returns_awaitable(self):
        """getCommEventLog() returns AwaitableMethod"""
        result = self.async_port.getCommEventLog(unit=1)
        self.assertIsInstance(result, AwaitableMethod)

    def test_writeMultipleCoils_returns_awaitable(self):
        """writeMultipleCoils() returns AwaitableMethod"""
        result = self.async_port.writeMultipleCoils(unit=1, offset=0, values=b'\xFF\x00')
        self.assertIsInstance(result, AwaitableMethod)

    def test_writeMultipleRegisters_returns_awaitable(self):
        """writeMultipleRegisters() returns AwaitableMethod"""
        result = self.async_port.writeMultipleRegisters(unit=1, offset=100, values=b'\x00\x10')
        self.assertIsInstance(result, AwaitableMethod)

    def test_reportServerID_returns_awaitable(self):
        """reportServerID() returns AwaitableMethod"""
        result = self.async_port.reportServerID(unit=1)
        self.assertIsInstance(result, AwaitableMethod)

    def test_maskWriteRegister_returns_awaitable(self):
        """maskWriteRegister() returns AwaitableMethod"""
        result = self.async_port.maskWriteRegister(unit=1, offset=50, andMask=0xFF, orMask=0x00)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readWriteMultipleRegisters_returns_awaitable(self):
        """readWriteMultipleRegisters() returns AwaitableMethod"""
        result = self.async_port.readWriteMultipleRegisters(unit=1, readOffset=0, readCount=10,
                                                           writeOffset=100, writeValues=b'\x00\x01')
        self.assertIsInstance(result, AwaitableMethod)

    def test_readFIFOQueue_returns_awaitable(self):
        """readFIFOQueue() returns AwaitableMethod"""
        result = self.async_port.readFIFOQueue(unit=1, fifoadr=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readCoilsF_returns_awaitable(self):
        """readCoilsF() returns AwaitableMethod"""
        result = self.async_port.readCoilsF(unit=1, offset=0, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readDiscreteInputsF_returns_awaitable(self):
        """readDiscreteInputsF() returns AwaitableMethod"""
        result = self.async_port.readDiscreteInputsF(unit=1, offset=0, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readHoldingRegistersF_returns_awaitable(self):
        """readHoldingRegistersF() returns AwaitableMethod"""
        result = self.async_port.readHoldingRegistersF(unit=1, offset=0, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_readInputRegistersF_returns_awaitable(self):
        """readInputRegistersF() returns AwaitableMethod"""
        result = self.async_port.readInputRegistersF(unit=1, offset=0, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_writeMultipleCoilsF_returns_awaitable(self):
        """writeMultipleCoilsF() returns AwaitableMethod"""
        result = self.async_port.writeMultipleCoilsF(unit=1, offset=0, values=(True, False, True))
        self.assertIsInstance(result, AwaitableMethod)

    def test_writeMultipleRegistersF_returns_awaitable(self):
        """writeMultipleRegistersF() returns AwaitableMethod"""
        result = self.async_port.writeMultipleRegistersF(unit=1, offset=100, values=(100, 200))
        self.assertIsInstance(result, AwaitableMethod)

    def test_readWriteMultipleRegistersF_returns_awaitable(self):
        """readWriteMultipleRegistersF() returns AwaitableMethod"""
        result = self.async_port.readWriteMultipleRegistersF(unit=1, readOffset=0, readCount=10,
                                                            writeOffset=100, writeValues=(100, 200))
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_readCoils_returns_awaitable(self):
        """Low-level _readCoils() returns AwaitableMethod"""
        result = self.async_port._readCoils(self, unit=1, offset=0, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_readDiscreteInputs_returns_awaitable(self):
        """Low-level _readDiscreteInputs() returns AwaitableMethod"""
        result = self.async_port._readDiscreteInputs(self, unit=1, offset=0, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_readHoldingRegisters_returns_awaitable(self):
        """Low-level _readHoldingRegisters() returns AwaitableMethod"""
        result = self.async_port._readHoldingRegisters(self, unit=1, offset=0, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_readInputRegisters_returns_awaitable(self):
        """Low-level _readInputRegisters() returns AwaitableMethod"""
        result = self.async_port._readInputRegisters(self, unit=1, offset=0, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_writeSingleCoil_returns_awaitable(self):
        """Low-level _writeSingleCoil() returns AwaitableMethod"""
        result = self.async_port._writeSingleCoil(self, unit=1, offset=10, value=True)
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_writeSingleRegister_returns_awaitable(self):
        """Low-level _writeSingleRegister() returns AwaitableMethod"""
        result = self.async_port._writeSingleRegister(self, unit=1, offset=20, value=100)
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_writeMultipleCoils_returns_awaitable(self):
        """Low-level _writeMultipleCoils() returns AwaitableMethod"""
        result = self.async_port._writeMultipleCoils(self, unit=1, offset=0, values=b'\xFF')
        self.assertIsInstance(result, AwaitableMethod)

    def test_low_level_writeMultipleRegisters_returns_awaitable(self):
        """Low-level _writeMultipleRegisters() returns AwaitableMethod"""
        result = self.async_port._writeMultipleRegisters(self, unit=1, offset=100, values=b'\x00\x10')
        self.assertIsInstance(result, AwaitableMethod)



if __name__ == '__main__':
    unittest.main()
