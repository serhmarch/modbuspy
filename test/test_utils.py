import unittest
import sys
import os

# Make sure tests can import package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.utils import createPort, createClientPort, createServerPort
from libmodbuspy.mbglobal import ProtocolType
from libmodbuspy.port import ModbusPort
from libmodbuspy.tcpport import ModbusTcpPort
from libmodbuspy.rtuport import ModbusRtuPort
from libmodbuspy.ascport import ModbusAscPort
from libmodbuspy.clientport import ModbusClientPort
from libmodbuspy.serverport import ModbusServerPort
from libmodbuspy.mbinterface import ModbusInterface


class MockDevice(ModbusInterface):
    """Mock device for testing server port creation."""
    pass


class TestUtils(unittest.TestCase):
    """Unit tests for utils.py factory functions"""

    def test_createPort_tcp_blocking(self):
        """createPort should create ModbusTcpPort for TCP protocol in blocking mode"""
        port = createPort(ProtocolType.TCP, blocking=True)
        self.assertIsInstance(port, ModbusTcpPort)
        self.assertTrue(port.isBlocking())
        self.assertEqual(port.type(), ProtocolType.TCP)

    def test_createPort_tcp_nonblocking(self):
        """createPort should create ModbusTcpPort in non-blocking mode"""
        port = createPort(ProtocolType.TCP, blocking=False)
        self.assertIsInstance(port, ModbusTcpPort)
        self.assertFalse(port.isBlocking())

    def test_createPort_tcp_with_settings(self):
        """createPort should apply host/port settings to TCP port"""
        port = createPort(ProtocolType.TCP, blocking=True, host="192.168.1.1", port=5021)
        self.assertEqual(port.host(), "192.168.1.1")
        self.assertEqual(port.port(), 5021)

    def test_createPort_rtu_blocking(self):
        """createPort should create ModbusRtuPort for RTU protocol"""
        port = createPort(ProtocolType.RTU, blocking=True)
        self.assertIsInstance(port, ModbusRtuPort)
        self.assertTrue(port.isBlocking())
        self.assertEqual(port.type(), ProtocolType.RTU)

    def test_createPort_rtu_with_settings(self):
        """createPort should apply serial settings to RTU port"""
        port = createPort(ProtocolType.RTU, blocking=True, 
                         portName="/dev/ttyUSB0", baudRate=9600)
        self.assertEqual(port.portName(), "/dev/ttyUSB0")
        self.assertEqual(port.baudRate(), 9600)

    def test_createPort_asc_blocking(self):
        """createPort should create ModbusAscPort for ASCII protocol"""
        port = createPort(ProtocolType.ASC, blocking=True)
        self.assertIsInstance(port, ModbusAscPort)
        self.assertTrue(port.isBlocking())
        self.assertEqual(port.type(), ProtocolType.ASC)

    def test_createPort_unsupported_protocol_raises(self):
        """createPort should raise ValueError for unsupported protocol"""
        with self.assertRaises(ValueError):
            createPort(999, blocking=True)  # Invalid protocol type

    def test_createClientPort_tcp(self):
        """createClientPort should wrap port in ModbusClientPort"""
        client_port = createClientPort(ProtocolType.TCP, blocking=True, 
                                      host="127.0.0.1", port=502)
        self.assertIsInstance(client_port, ModbusClientPort)
        self.assertEqual(client_port.type(), ProtocolType.TCP)
        inner_port = client_port.port()
        self.assertIsInstance(inner_port, ModbusTcpPort)
        self.assertEqual(inner_port.host(), "127.0.0.1")

    def test_createClientPort_rtu(self):
        """createClientPort should wrap RTU port in ModbusClientPort"""
        client_port = createClientPort(ProtocolType.RTU, blocking=True,
                                      portName="COM1", baudRate=19200)
        self.assertIsInstance(client_port, ModbusClientPort)
        self.assertEqual(client_port.type(), ProtocolType.RTU)
        inner_port = client_port.port()
        self.assertEqual(inner_port.baudRate(), 19200)

    def test_createServerPort_tcp(self):
        """createServerPort should create ModbusTcpServer for TCP"""
        device = MockDevice()
        server_port = createServerPort(device, ProtocolType.TCP, blocking=True,
                                      host="0.0.0.0", port=502)
        self.assertIsInstance(server_port, ModbusServerPort)
        self.assertEqual(server_port.type(), ProtocolType.TCP)
        self.assertIs(server_port.device(), device)

    def test_createServerPort_rtu(self):
        """createServerPort should create ModbusServerResource for RTU"""
        device = MockDevice()
        server_port = createServerPort(device, ProtocolType.RTU, blocking=True,
                                      portName="COM1", baudRate=9600)
        self.assertIsInstance(server_port, ModbusServerPort)
        self.assertEqual(server_port.type(), ProtocolType.RTU)
        self.assertIs(server_port.device(), device)

    def test_createServerPort_asc(self):
        """createServerPort should create ModbusServerResource for ASCII"""
        device = MockDevice()
        server_port = createServerPort(device, ProtocolType.ASC, blocking=True,
                                      portName="/dev/ttyUSB0", baudRate=9600)
        self.assertIsInstance(server_port, ModbusServerPort)
        self.assertEqual(server_port.type(), ProtocolType.ASC)
        self.assertIs(server_port.device(), device)


if __name__ == '__main__':
    unittest.main()
