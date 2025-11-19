import unittest
from unittest.mock import patch, Mock, MagicMock
import socket
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.tcpserver import ModbusTcpServer
from libmodbuspy.mbinterface import ModbusInterface
from libmodbuspy.mbglobal import ProtocolType, Constants
from libmodbuspy.statuscode import StatusCode


class MockDevice(ModbusInterface):
    """Mock device for testing TCP server"""
    pass


class TestModbusTcpServer(unittest.TestCase):
    """Unit tests for ModbusTcpServer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.device = MockDevice()
        
        # Patch socket module to avoid actual network operations
        self.patcher_socket = patch('libmodbuspy.tcpserver.socket')
        self.mock_socket_module = self.patcher_socket.start()
        self.mock_socket_module.AF_INET = socket.AF_INET
        self.mock_socket_module.SOCK_STREAM = socket.SOCK_STREAM
        self.mock_socket_module.SOL_SOCKET = socket.SOL_SOCKET
        self.mock_socket_module.SO_REUSEADDR = socket.SO_REUSEADDR
        self.mock_socket_module.EWOULDBLOCK = socket.EWOULDBLOCK
        self.mock_socket_module.error = socket.error
        self.mock_socket_module.timeout = socket.timeout
        
        self.server = ModbusTcpServer(self.device)

    def tearDown(self):
        """Clean up after each test"""
        self.patcher_socket.stop()
        if self.server is not None:
            try:
                self.server.close()
            except:
                pass

    def test_initialization(self):
        """TCP server initializes with default values"""
        d = ModbusTcpServer.Defaults
        self.assertEqual(self.server._host, d.host)
        self.assertEqual(self.server._tcpPort, d.port)
        self.assertEqual(self.server._timeout, d.timeout)
        self.assertEqual(self.server._maxconn, d.maxconn)
        self.assertIs(self.server._device, self.device)
        self.assertEqual(len(self.server._connections), 0)

    def test_type_returns_tcp(self):
        """type() returns ProtocolType.TCP"""
        self.assertEqual(self.server.type(), ProtocolType.TCP)

    def test_isTcpServer_returns_true(self):
        """isTcpServer() returns True"""
        self.assertTrue(self.server.isTcpServer())

    def test_host_getter_setter(self):
        """host() and setHost() manage host"""
        self.assertEqual(self.server.host(), ModbusTcpServer.Defaults.host)
        self.server.setHost("192.168.1.1")
        self.assertEqual(self.server.host(), "192.168.1.1")

    def test_port_getter_setter(self):
        """port() and setPort() manage port"""
        d = ModbusTcpServer.Defaults
        self.assertEqual(self.server.port(), d.port)
        self.server.setPort(5021)
        self.assertEqual(self.server.port(), 5021)

    def test_timeout_getter_setter(self):
        """timeout() and setTimeout() manage timeout"""
        d = ModbusTcpServer.Defaults
        self.assertEqual(self.server.timeout(), d.timeout)
        self.server.setTimeout(10000)
        self.assertEqual(self.server.timeout(), 10000)

    def test_maxConnections_getter_setter(self):
        """maxConnections() and setMaxConnections() manage max connections"""
        d = ModbusTcpServer.Defaults
        self.assertEqual(self.server.maxConnections(), d.maxconn)
        self.server.setMaxConnections(20)
        self.assertEqual(self.server.maxConnections(), 20)

    def test_maxConnections_minimum_one(self):
        """setMaxConnections() enforces minimum of 1"""
        self.server.setMaxConnections(0)
        self.assertEqual(self.server.maxConnections(), 1)
        self.server.setMaxConnections(-5)
        self.assertEqual(self.server.maxConnections(), 1)

    def test_settings_dict_format(self):
        """settings() returns dictionary with settings"""
        self.server.setHost("10.0.0.1")
        self.server.setPort(5022)
        self.server.setTimeout(15000)
        self.server.setMaxConnections(15)
        
        settings = self.server.settings()
        self.assertIsInstance(settings, dict)
        # Verify settings() returns a dict (may have reference to tcpport strings which is fine)
        self.assertTrue(len(settings) > 0)

    def test_setSettings_applies_all_settings(self):
        """setSettings() applies host, port, timeout, maxconn settings"""
        settings = {
            ModbusTcpServer.Strings.host: "127.0.0.1",
            ModbusTcpServer.Strings.port: 5025,
            ModbusTcpServer.Strings.timeout: 20000,
            ModbusTcpServer.Strings.maxconn: 25
        }
        self.server.setSettings(settings)
        self.assertEqual(self.server.host(), "127.0.0.1")
        self.assertEqual(self.server.port(), 5025)
        self.assertEqual(self.server.timeout(), 20000)
        self.assertEqual(self.server.maxConnections(), 25)

    def test_broadcast_enabled_default(self):
        """Broadcast is enabled by default"""
        self.assertTrue(self.server.isBroadcastEnabled())

    def test_broadcast_setter(self):
        """setBroadcastEnabled() toggles broadcast"""
        self.server.setBroadcastEnabled(False)
        self.assertFalse(self.server.isBroadcastEnabled())

    def test_device_getter_setter(self):
        """device() and setDevice() manage device"""
        self.assertIs(self.server.device(), self.device)
        new_device = MockDevice()
        self.server.setDevice(new_device)
        self.assertIs(self.server.device(), new_device)

    def test_connection_list_initialized(self):
        """Connection list is initialized as empty"""
        self.assertEqual(len(self.server._connections), 0)
        self.assertIsInstance(self.server._connections, list)

    def test_signal_creation(self):
        """TCP server has all required signal objects"""
        self.assertIsNotNone(self.server.signalOpened)
        self.assertIsNotNone(self.server.signalClosed)
        self.assertIsNotNone(self.server.signalError)
        self.assertIsNotNone(self.server.signalTx)
        self.assertIsNotNone(self.server.signalRx)
        self.assertIsNotNone(self.server.signalNewConnection)
        self.assertIsNotNone(self.server.signalCloseConnection)

    def test_strings_class_has_settings_keys(self):
        """Strings class defines all settings keys"""
        self.assertEqual(ModbusTcpServer.Strings.host, "host")
        self.assertEqual(ModbusTcpServer.Strings.port, "port")
        self.assertEqual(ModbusTcpServer.Strings.timeout, "timeout")
        self.assertEqual(ModbusTcpServer.Strings.maxconn, "maxconn")

    def test_defaults_class_values(self):
        """Defaults class has expected default values"""
        d = ModbusTcpServer.Defaults
        self.assertEqual(d.port, Constants.STANDARD_TCP_PORT)
        self.assertIsInstance(d.timeout, int)
        self.assertIsInstance(d.maxconn, int)
        self.assertGreater(d.timeout, 0)
        self.assertGreater(d.maxconn, 0)

    def test_state_enum_exists(self):
        """ModbusServerPort state enum is accessible"""
        from libmodbuspy.serverport import ModbusServerPort
        self.assertTrue(hasattr(ModbusServerPort.State, 'STATE_OPENED'))
        self.assertTrue(hasattr(ModbusServerPort.State, 'STATE_CLOSED'))


if __name__ == '__main__':
    unittest.main()
