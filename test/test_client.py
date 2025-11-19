import unittest
from unittest.mock import Mock, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.client import ModbusClient
from libmodbuspy.clientport import ModbusClientPort, ModbusAsyncClientPort
from libmodbuspy.mbglobal import ProtocolType, AwaitableMethod
from libmodbuspy.port import ModbusPort
from libmodbuspy.statuscode import StatusCode


class MockClientPort(ModbusClientPort):
    """Mock client port for testing ModbusClient"""
    def __init__(self):
        self._port = None
        self._unit = 0
        self._settings_tries = 1
        self._settings_broadcastEnabled = True
    
    def _readCoils(self, client, unit, offset, count):
        return b'\x01\x02\x03'
    
    def _readDiscreteInputs(self, client, unit, offset, count):
        return b'\x04\x05\x06'
    
    def _readHoldingRegisters(self, client, unit, offset, count):
        return b'\x00\x10\x00\x20'
    
    def _readInputRegisters(self, client, unit, offset, count):
        return b'\x00\x30\x00\x40'
    
    def _writeSingleCoil(self, client, unit, offset, value):
        return True
    
    def _writeSingleRegister(self, client, unit, offset, value):
        return True
    
    def _readExceptionStatus(self, client, unit):
        return 0
    
    def _diagnostics(self, client, unit, subfunc, indata):
        return b'\x00\x01'
    
    def _getCommEventCounter(self, client, unit):
        return 100
    
    def _getCommEventLog(self, client, unit):
        return b'\x00\x01\x02'
    
    def _writeMultipleCoils(self, client, unit, offset, values, count):
        return True
    
    def _writeMultipleRegisters(self, client, unit, offset, values):
        return True
    
    def _reportServerID(self, client, unit):
        return b'\x01\x02'
    
    def _maskWriteRegister(self, client, unit, offset, andMask, orMask):
        return True
    
    def _readWriteMultipleRegisters(self, client, unit, readOffset, readCount, writeOffset, writeValues):
        return b'\x00\x10'
    
    def _readFIFOQueue(self, client, unit, fifoadr):
        return b'\x00\x00\x00'
    
    def lastStatus(self):
        return 0
    
    def lastErrorStatus(self):
        return 0
    
    def lastErrorText(self):
        return ""


class TestModbusClient(unittest.TestCase):
    """Unit tests for ModbusClient class"""

    def setUp(self):
        self.mock_port = MockClientPort()
        self.client = ModbusClient(unit=1, port=self.mock_port)

    def tearDown(self):
        self.client = None
        self.mock_port = None

    def test_initialization(self):
        """ModbusClient initialization stores unit and port"""
        self.assertEqual(self.client._unit, 1)
        self.assertIs(self.client._port, self.mock_port)

    def test_unit_getter_setter(self):
        """unit() and setUnit() manage unit identifier"""
        self.assertEqual(self.client.unit(), 1)
        self.client.setUnit(5)
        self.assertEqual(self.client.unit(), 5)

    def test_unit_property(self):
        """Unit property works correctly"""
        self.assertEqual(self.client.Unit, 1)
        self.client.Unit = 3
        self.assertEqual(self.client.Unit, 3)

    def test_port_method(self):
        """port() returns underlying client port"""
        self.assertIs(self.client.port(), self.mock_port)

    def test_readCoils_calls_port(self):
        """readCoils delegates to port with correct unit"""
        result = self.client.readCoils(offset=10, count=8)
        self.assertEqual(result, b'\x01\x02\x03')

    def test_readDiscreteInputs_calls_port(self):
        """readDiscreteInputs delegates to port"""
        result = self.client.readDiscreteInputs(offset=0, count=16)
        self.assertEqual(result, b'\x04\x05\x06')

    def test_readHoldingRegisters_calls_port(self):
        """readHoldingRegisters delegates to port"""
        result = self.client.readHoldingRegisters(offset=100, count=10)
        self.assertEqual(result, b'\x00\x10\x00\x20')

    def test_readInputRegisters_calls_port(self):
        """readInputRegisters delegates to port"""
        result = self.client.readInputRegisters(offset=50, count=5)
        self.assertEqual(result, b'\x00\x30\x00\x40')

    def test_writeSingleCoil_calls_port(self):
        """writeSingleCoil delegates to port"""
        result = self.client.writeSingleCoil(offset=10, value=True)
        self.assertTrue(result)

    def test_writeSingleRegister_calls_port(self):
        """writeSingleRegister delegates to port"""
        result = self.client.writeSingleRegister(offset=20, value=0x1234)
        self.assertTrue(result)

    def test_readExceptionStatus_calls_port(self):
        """readExceptionStatus delegates to port"""
        result = self.client.readExceptionStatus()
        self.assertEqual(result, 0)

    def test_diagnostics_calls_port(self):
        """diagnostics delegates to port"""
        result = self.client.diagnostics(subfunc=0, indata=None)
        self.assertEqual(result, b'\x00\x01')

    def test_getCommEventCounter_calls_port(self):
        """getCommEventCounter delegates to port"""
        result = self.client.getCommEventCounter()
        self.assertEqual(result, 100)

    def test_getCommEventLog_calls_port(self):
        """getCommEventLog delegates to port"""
        result = self.client.getCommEventLog()
        self.assertEqual(result, b'\x00\x01\x02')

    def test_writeMultipleCoils_calls_port(self):
        """writeMultipleCoils delegates to port"""
        result = self.client.writeMultipleCoils(offset=0, values=b'\xFF\x00')
        self.assertTrue(result)

    def test_writeMultipleRegisters_calls_port(self):
        """writeMultipleRegisters delegates to port"""
        result = self.client.writeMultipleRegisters(offset=100, values=b'\x00\x10\x00\x20')
        self.assertTrue(result)

    def test_reportServerID_calls_port(self):
        """reportServerID delegates to port"""
        result = self.client.reportServerID()
        self.assertEqual(result, b'\x01\x02')

    def test_maskWriteRegister_calls_port(self):
        """maskWriteRegister delegates to port"""
        result = self.client.maskWriteRegister(offset=50, andMask=0x00FF, orMask=0xFF00)
        self.assertTrue(result)

    def test_readWriteMultipleRegisters_calls_port(self):
        """readWriteMultipleRegisters delegates to port"""
        result = self.client.readWriteMultipleRegisters(readOffset=0, readCount=10, 
                                                        writeOffset=100, writeValues=b'\x00\x01')
        self.assertEqual(result, b'\x00\x10')

    def test_readFIFOQueue_calls_port(self):
        """readFIFOQueue delegates to port"""
        result = self.client.readFIFOQueue(fifoadr=10)
        self.assertEqual(result, b'\x00\x00\x00')

    def test_lastPortStatus(self):
        """lastPortStatus delegates to port"""
        result = self.client.lastPortStatus()
        self.assertEqual(result, 0)

    def test_lastPortErrorStatus(self):
        """lastPortErrorStatus delegates to port"""
        result = self.client.lastPortErrorStatus()
        self.assertEqual(result, 0)

    def test_lastPortErrorText(self):
        """lastPortErrorText delegates to port"""
        result = self.client.lastPortErrorText()
        self.assertEqual(result, "")


class TestModbusAsyncClient(unittest.TestCase):
    """Unit tests for ModbusClient (async) class"""

    def setUp(self):
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
        self.port = ModbusAsyncClientPort(self.mock_port)
        self.client = ModbusClient(unit=2, port=self.port)

    def tearDown(self):
        self.client = None
        self.mock_port = None

    def test_initialization(self):
        """ModbusAsyncClient initialization stores unit and port"""
        self.assertEqual(self.client._unit, 2)
        self.assertIs(self.client._port, self.port)

    def test_unit_getter_setter(self):
        """unit() and setUnit() manage unit identifier"""
        self.assertEqual(self.client.unit(), 2)
        self.client.setUnit(7)
        self.assertEqual(self.client.unit(), 7)

    def test_unit_property(self):
        """Unit property works correctly"""
        self.assertEqual(self.client.Unit, 2)
        self.client.Unit = 4
        self.assertEqual(self.client.Unit, 4)

    def test_port_method(self):
        """port() returns underlying client port"""
        self.assertIs(self.client.port(), self.port)

    def test_async_readCoils_returns_awaitable(self):
        """Async readCoils returns AwaitableMethod"""
        result = self.client.readCoils(offset=10, count=8)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_readDiscreteInputs_returns_awaitable(self):
        """Async readDiscreteInputs returns AwaitableMethod"""
        result = self.client.readDiscreteInputs(offset=0, count=16)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_readHoldingRegisters_returns_awaitable(self):
        """Async readHoldingRegisters returns AwaitableMethod"""
        result = self.client.readHoldingRegisters(offset=100, count=10)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_readInputRegisters_returns_awaitable(self):
        """Async readInputRegisters returns AwaitableMethod"""
        result = self.client.readInputRegisters(offset=50, count=5)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_writeSingleCoil_returns_awaitable(self):
        """Async writeSingleCoil returns AwaitableMethod"""
        result = self.client.writeSingleCoil(offset=10, value=True)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_writeSingleRegister_returns_awaitable(self):
        """Async writeSingleRegister returns AwaitableMethod"""
        result = self.client.writeSingleRegister(offset=20, value=0x5678)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_readExceptionStatus_returns_awaitable(self):
        """Async readExceptionStatus returns AwaitableMethod"""
        result = self.client.readExceptionStatus()
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_diagnostics_returns_awaitable(self):
        """Async diagnostics returns AwaitableMethod"""
        result = self.client.diagnostics(subfunc=0, indata=None)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_getCommEventCounter_returns_awaitable(self):
        """Async getCommEventCounter returns AwaitableMethod"""
        result = self.client.getCommEventCounter()
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_getCommEventLog_returns_awaitable(self):
        """Async getCommEventLog returns AwaitableMethod"""
        result = self.client.getCommEventLog()
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_writeMultipleCoils_returns_awaitable(self):
        """Async writeMultipleCoils returns AwaitableMethod"""
        result = self.client.writeMultipleCoils(offset=0, values=b'\xFF\x00')
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_writeMultipleRegisters_returns_awaitable(self):
        """Async writeMultipleRegisters returns AwaitableMethod"""
        result = self.client.writeMultipleRegisters(offset=100, values=b'\x00\x10\x00\x20')
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_reportServerID_returns_awaitable(self):
        """Async reportServerID returns AwaitableMethod"""
        result = self.client.reportServerID()
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_maskWriteRegister_returns_awaitable(self):
        """Async maskWriteRegister returns AwaitableMethod"""
        result = self.client.maskWriteRegister(offset=50, andMask=0x00FF, orMask=0xFF00)
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_readWriteMultipleRegisters_returns_awaitable(self):
        """Async readWriteMultipleRegisters returns AwaitableMethod"""
        result = self.client.readWriteMultipleRegisters(readOffset=0, readCount=10,
                                                        writeOffset=100, writeValues=b'\x00\x01')
        self.assertIsInstance(result, AwaitableMethod)

    def test_async_readFIFOQueue_returns_awaitable(self):
        """Async readFIFOQueue returns AwaitableMethod"""
        result = self.client.readFIFOQueue(fifoadr=10)
        self.assertIsInstance(result, AwaitableMethod)


if __name__ == '__main__':
    unittest.main()
