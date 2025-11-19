import unittest
from unittest.mock import Mock, patch, MagicMock, call
import socket
import select
import sys
import os

# Add the parent directory to the path to import libmodbuspy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy import port
from libmodbuspy.tcpport import ModbusTcpPort
from libmodbuspy.statuscode import StatusCode
from libmodbuspy.port import ModbusPort
from libmodbuspy.mbglobal import ProtocolType, Constants, timer
from libmodbuspy import exceptions

class TestModbusTcpPort(unittest.TestCase):
    """Comprehensive test cases for ModbusTcpPort class"""
    
    #@classmethod
    #def setUpClass(cls):
    #    """Set up class-level patches to prevent destructor issues."""
    #    # Patch the __del__ method to prevent select.select calls with mock objects
    #    cls.del_patcher = patch.object(ModbusTcpPort, '__del__', lambda self: None)
    #    cls.del_patcher.start()
    #
    #@classmethod
    #def tearDownClass(cls):
    #    """Clean up class-level patches."""
    #    cls.del_patcher.stop()
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.orig_socket = socket
        self.orig_select = select

        self.patcher_socket = patch('libmodbuspy.tcpport.socket')
        self.mock_socket_module = self.patcher_socket.start()
        self.mock_socket_module.EWOULDBLOCK = socket.EWOULDBLOCK
        self.mock_socket_module.SHUT_RDWR = socket.SHUT_RDWR
        self.mock_socket_module.errno = socket.errno
        self.mock_socket_module.error = socket.error
        self.mock_socket_module.timeout = socket.timeout

        self.addCleanup(self.patcher_socket.stop)

        self.patcher_select = patch('libmodbuspy.tcpport.select')
        self.mock_select_module = self.patcher_select.start()
        self.addCleanup(self.patcher_select.stop)

        mock_sock = Mock() 
        mock_sock.fileno.return_value = 10
        self.mock_sock = mock_sock

        # prevent select.select calls raising errors when called in destructor
        self.mock_select_module.select.return_value = ([], [], [])

        self.port = None

    def tearDown(self):
        """Clean up after each test method."""
        # Avoid destructor call non mock select
        # in inappropriate garbage collection cleanup time
        # which lead to calls to select.select with mock objects
        if self.port is not None:
            self.port.close()

    def test_initialization_defaults(self):
        """Test ModbusTcpPort initialization with default values"""
        #port = ModbusTcpPort()
        
        d = ModbusTcpPort.Defaults
        self.port = ModbusTcpPort()
        # Test default values
        self.assertEqual(self.port.host(), d.host)
        self.assertEqual(self.port.port(), d.port)
        self.assertEqual(self.port.timeout(), d.timeout)
        self.assertEqual(self.port.type(), ProtocolType.TCP)
        self.assertTrue(self.port.autoIncrement())
        self.assertEqual(self.port.transactionId(), 0)
        self.assertFalse(self.port.isOpen())

    def test_settings_management(self):
        """Test settings get/set functionality"""
        settings = {
            "host": "192.168.1.10",
            "port": 5020,
            "timeout": 2000
        }
        
        self.port = ModbusTcpPort()
        self.port.setSettings(settings)
        
        retrieved_settings = self.port.settings()
        
        self.assertEqual(retrieved_settings["host"], "192.168.1.10")
        self.assertEqual(retrieved_settings["port"], 5020)
        self.assertEqual(retrieved_settings["timeout"], 2000)
        
        # Test partial settings update
        partial_settings = {"host": "127.0.0.1"}
        self.port.setSettings(partial_settings)
        
        updated_settings = self.port.settings()
        self.assertEqual(updated_settings["host"], "127.0.0.1")
        self.assertEqual(updated_settings["port"], 5020)  # Should remain unchanged

    def test_initialization_with_socket(self):
        """Test ModbusTcpPort initialization with existing socket"""
        mock_sock = Mock() 
        mock_sock.fileno.return_value = 10
            #    
        # Mock select for isOpen check
        self.mock_select_module.select.return_value = ([], [mock_sock], [])
        self.port = ModbusTcpPort(sock=mock_sock)
        self.assertIs(self.port.socket(), mock_sock)
        self.assertTrue(self.port.isOpen())
        del self.port
        self.port = None

    def test_initialization_blocking_mode(self):
        """Test ModbusTcpPort initialization in different blocking modes"""
        # Test blocking mode (default)
        port_blocking = ModbusTcpPort(blocking=True)
        self.assertTrue(port_blocking.isBlocking())
        
        # Test non-blocking mode
        port_nonblocking = ModbusTcpPort(blocking=False)
        self.assertFalse(port_nonblocking.isBlocking())
#
    def test_handle_method(self):
        """Test handle() method returns correct file descriptor"""
        self.port = ModbusTcpPort()
        self.assertEqual(self.port.handle(), -1)
        
        # Test with mock socket
        self.port._sock = self.mock_sock
        self.mock_sock.fileno.return_value = 42        
        self.assertEqual(self.port.handle(), 42)
        self.mock_sock.fileno.assert_called_once()

        self.mock_sock.fileno.return_value = 333        
        self.assertEqual(self.port.handle(), 333)
        self.assertEqual(self.mock_sock.fileno.call_count, 2)

    def test_host_property_methods(self):
        """Test host getter/setter methods and properties"""
        self.port = ModbusTcpPort()
        # Test setter/getter methods
        self.port.setHost("192.168.1.100")
        self.assertEqual(self.port.host(), "192.168.1.100")
        self.assertTrue(self.port.isChanged())
        
        # Reset changed flag for next test
        self.port._changed = False
        
        # Test property syntax
        self.port.Host = "10.0.0.1"
        self.assertEqual(self.port.Host, "10.0.0.1")
        self.assertTrue(self.port.isChanged())
        
        # Test no change when setting same value
        self.port._changed = False
        self.port.setHost("10.0.0.1")
        self.assertFalse(self.port.isChanged())

    def test_port_property_methods(self):
        """Test port getter/setter methods and properties"""
        self.port = ModbusTcpPort()
        # Test setter/getter methods
        self.port.setPort(5020)
        self.assertEqual(self.port.port(), 5020)
        self.assertTrue(self.port.isChanged())
        
        # Reset changed flag
        self.port._changed = False
        
        # Test property syntax
        self.port.Port = 1502
        self.assertEqual(self.port.Port, 1502)
        self.assertTrue(self.port.isChanged())
        
        # Test no change when setting same value
        self.port._changed = False
        self.port.setPort(1502)
        self.assertFalse(self.port.isChanged())

    def test_timeout_methods(self):
        """Test timeout getter/setter methods"""
        d = ModbusTcpPort.Defaults
        self.port = ModbusTcpPort()
        self.assertEqual(self.port.timeout(), d.timeout)  # Default value
        self.assertEqual(self.port.Timeout, d.timeout)  # Property

        self.port.setTimeout(5000)
        self.assertEqual(self.port.timeout(), 5000)
        self.assertEqual(self.port.Timeout, 5000)  # Property

    def test_auto_increment_methods(self):
        """Test auto-increment and transaction ID behavior"""
        # Test default auto-increment behavior
        self.port = ModbusTcpPort()
        self.assertTrue(self.port.autoIncrement())
        
        # Test setting next request repeated
        self.port.setNextRequestRepeated(False)
        self.assertFalse(self.port.autoIncrement())

        self.port.setNextRequestRepeated(True)
        self.assertTrue(self.port.autoIncrement())
        
    def test_open_successful_connection_blocking(self):
        """Test successful TCP connection opening in blocking mode"""
        self.port = ModbusTcpPort()
        self.mock_sock.connect_ex.return_value = 0  # Success
        socket = self.mock_socket_module
        socket.socket.return_value = self.mock_sock
        
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)
        
        # Verify socket creation and configuration
        socket.socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        self.mock_sock.settimeout.assert_called_once_with(self.port.Timeout / 1000.0)  # 1000ms = 1.0s
        self.mock_sock.connect_ex.assert_called_once_with((self.port.Host, self.port.Port))

    def test_open_successful_connection_nonblocking(self):
        """Test successful TCP connection opening in non-blocking mode"""
        self.port = ModbusTcpPort(blocking=False)
        self.mock_sock.connect_ex.return_value = 0  # Success
        socket = self.mock_socket_module
        socket.socket.return_value = self.mock_sock
        
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertEqual(self.port._state, ModbusPort.State.STATE_OPENED)
        
        # Verify non-blocking mode set
        self.mock_sock.setblocking.assert_called_once_with(False)
        self.mock_sock.connect_ex.assert_called_once_with((self.port.Host, self.port.Port))
        
        #port.__del__ # indirectly call `select.select` with mock objects
        self.port.close()

    def test_open_connection_failure(self):
        """Test TCP connection failure"""
        self.port = ModbusTcpPort()
        self.mock_sock.connect_ex.return_value = self.orig_socket.errno.ECONNREFUSED  # Connection refused
        socket = self.mock_socket_module
        socket.socket.return_value = self.mock_sock
        
        with self.assertRaises(exceptions.TcpConnectError):
            self.port.open()
            
        self.assertFalse(self.port.isOpen())
        self.assertEqual(self.port._state, ModbusPort.State.STATE_CLOSED)

    def test_open_socket_creation_error(self):
        """Test socket creation error"""
        self.port = ModbusTcpPort()
        socket = self.mock_socket_module
        socket.socket.side_effect = OSError("Socket creation failed")
        
        with self.assertRaises(exceptions.TcpCreateError):
            self.port.open()

    def test_open_non_blocking_success_after_wait(self):
        """Test non-blocking connection success after waiting"""
        self.port = ModbusTcpPort(blocking=False)
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = self.orig_socket.EWOULDBLOCK
        
        # First call to select returns socket ready for write
        self.mock_select_module.select.return_value = ([], [self.mock_sock], [])
        
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertEqual(self.port._state, ModbusPort.State.STATE_OPENED)

        self.port.close() # prevent destructor call non mock select
        
    def test_open_non_blocking_timeout(self):
        """Test non-blocking connection timeout"""
        with patch('libmodbuspy.tcpport.timer') as mock_timer:
            self.port = ModbusTcpPort(blocking=False)
            self.mock_socket_module.socket.return_value = self.mock_sock
            self.mock_sock.connect_ex.return_value = self.orig_socket.EWOULDBLOCK
            
            # Mock select to return no ready sockets (timeout)
            self.mock_select_module.select.return_value = ([], [], [])
            
            # Mock timer to simulate timeout
            list_timer_results = [0, self.port.Timeout//2, self.port.Timeout]  # Start time, then middle and past timeout
            mock_timer.side_effect = list_timer_results
            
            with self.assertRaises(exceptions.TcpConnectError):
                for _ in range(len(list_timer_results)):  # Simulate multiple attempts
                    self.port.open()
                
            self.mock_sock.close.assert_called_once()

            self.port.close() # prevent destructor call non mock select

    def test_open_connection_error_in_select(self):
        """Test connection error detected by select"""
        self.port = ModbusTcpPort(blocking=False)
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = self.orig_socket.EWOULDBLOCK
        
        # Mock select to return error socket
        self.mock_select_module.select.return_value = ([], [], [self.mock_sock])
        
        with self.assertRaises(exceptions.TcpConnectError):
            for _ in range(2):  # Attempt to open
                self.port.open()
            
        self.mock_sock.close.assert_called_once()
        self.port.close() # prevent destructor call non mock select

    def test_open_already_open_unchanged(self):
        """Test opening already opened connection with no changes"""
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(sock=self.mock_sock)
        result = self.port.open()            
        self.assertEqual(result, StatusCode.Status_Good)
        self.port.close() # prevent destructor call non mock select

    def test_close_open_connection(self):
        """Test closing an open connection"""
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(sock=self.mock_sock)
        result = self.port.close()
            
        self.assertEqual(result, StatusCode.Status_Good)
        self.mock_sock.shutdown.assert_called_once_with(socket.SHUT_RDWR)
        self.mock_sock.close.assert_called_once()
        self.assertIsNone(self.port._sock)
        self.assertEqual(self.port._state, ModbusPort.State.STATE_CLOSED)

    def test_close_with_socket_error(self):
        """Test closing connection when socket operations fail"""
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(sock=self.mock_sock)
        # Should not raise exception
        result = self.port.close()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertIsNone(self.port._sock)

    def test_close_no_connection(self):
        """Test closing when no connection exists"""
        self.port = ModbusTcpPort()
        result = self.port.close()
        self.assertEqual(result, StatusCode.Status_Good)

    def test_is_open_with_valid_socket(self):
        """Test isOpen() with valid socket"""
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(sock=self.mock_sock)
        
        self.assertTrue(self.port.isOpen())
        self.port.close() # prevent destructor call non mock select

    def test_is_open_invalid_socket(self):
        """Test isOpen() with invalid socket file descriptor"""
        self.mock_sock.fileno.return_value = -1  # Invalid fd
        self.port = ModbusTcpPort(sock=self.mock_sock)        
        self.assertFalse(self.port.isOpen())
        self.port.close() # prevent destructor call non mock select

    def test_is_open_not_ready(self):
        """Test isOpen() when socket is not ready"""
        self.mock_select_module.select.return_value = ([], [], [])
        self.port = ModbusTcpPort(sock=self.mock_sock)        
        self.assertFalse(self.port.isOpen())

    def test_writeBuffer_client_mode(self):
        """Test writeBuffer() method functionality in client mode"""
        self.port = ModbusTcpPort()
        self.port.setServerMode(False)
        unit = 1
        func = 3
        data = b'\x00\x00\x00\x02'  # Read 2 registers from address 0
        
        result = self.port.writeBuffer(unit, func, data)
        
        self.assertTrue(result)
        self.assertEqual(self.port.transactionId(), 1)  # Should increment
        self.assertEqual(self.port.unit(), unit)
        self.assertEqual(self.port.function(), func)
        
        buff = self.port.writeBufferData()
        self.assertEqual(len(buff), 12)  # 6-byte TCP header + 1 unit + 1 func + 4 data
        
        # Check TCP header format
        transaction_id = (buff[0] << 8) | buff[1]
        self.assertEqual(transaction_id, 1)
        
        protocol_id = (buff[2] << 8) | buff[3]
        self.assertEqual(protocol_id, 0)
        
        length = (buff[4] << 8) | buff[5]
        self.assertEqual(length, 6)  # unit + func + data length
        
        self.assertEqual(buff[6], unit)
        self.assertEqual(buff[7], func)
        self.assertEqual(buff[8:], data)

    def test_writeBuffer_server_mode(self):
        """Test writeBuffer() method functionality in server mode"""
        self.port = ModbusTcpPort()
        self.port.setServerMode(True)
        initial_transaction = 42
        self.port._transaction = initial_transaction
        
        unit = 1
        func = 3
        data = b'\x02\x00\x01'  # Response data
        
        result = self.port.writeBuffer(unit, func, data)
        
        self.assertTrue(result)
        self.assertEqual(self.port.transactionId(), initial_transaction)  # Should not increment
        self.assertEqual(self.port.unit(), unit)
        self.assertEqual(self.port.function(), func)
        
        buff = self.port.writeBufferData()
        self.assertEqual(len(buff), 11)  # 6-byte TCP header + 1 unit + 1 func + 3 data
        
        # Check TCP header format
        transaction_id = (buff[0] << 8) | buff[1]
        self.assertEqual(transaction_id, initial_transaction)
        
        protocol_id = (buff[2] << 8) | buff[3]
        self.assertEqual(protocol_id, 0)
        
        length = (buff[4] << 8) | buff[5]
        self.assertEqual(length, 5)  # unit + func + data length
        
        self.assertEqual(buff[6], unit)
        self.assertEqual(buff[7], func)
        self.assertEqual(buff[8:], data)

    def test_readBuffer_client_mode(self):
        """Test readBuffer() method functionality in client mode"""
        self.port = ModbusTcpPort()
        self.port.setServerMode(False)
        # Prepare buffer with sample data
        self.port._buff = bytearray([
             0x00, 0x01,  # Transaction ID
             0x00, 0x00,  # Protocol ID
             0x00, 0x05,  # Length (5 bytes)
             0x01,        # Unit ID
             0x03,        # Function code
             0x02,        # Byte count
             0x00, 0x01   # Data (register value)
         ])
        
        self.port._transaction = 1  # Expected transaction ID
        unit, func, data = self.port.readBuffer()
        self.assertEqual(self.port.transactionId(), 1)
        self.assertEqual(unit, 1)
        self.assertEqual(func, 3)
        self.assertEqual(data, b'\x02\x00\x01')  # Data portion
        # Buffer size is too small
        self.port._buff = bytearray([0x00, 0x01, 0x00])
        with self.assertRaises(exceptions.ModbusException):
            self.port.readBuffer()
        # Not correct transaction ID
        self.port._buff = bytearray([
             0x00, 0x02,  # Transaction ID - not correct
             0x00, 0x00,  # Protocol ID
             0x00, 0x05,  # Length (5 bytes)
             0x01,        # Unit ID
             0x03,        # Function code
             0x02,        # Byte count
             0x00, 0x01   # Data (register value)
         ])
        with self.assertRaises(exceptions.ModbusException):
            self.port.readBuffer()
        # Not correct Protocol ID
        self.port._buff = bytearray([
             0x00, 0x01,  # Transaction ID
             0x00, 0x01,  # Protocol ID - not correct
             0x00, 0x05,  # Length (5 bytes)
             0x01,        # Unit ID
             0x03,        # Function code
             0x02,        # Byte count
             0x00, 0x01   # Data (register value)
         ])
        # Not correct buffer length
        self.port._buff = bytearray([
             0x00, 0x01,  # Transaction ID
             0x00, 0x00,  # Protocol ID
             0x00, 0x06,  # Length (6 bytes) - not correct
             0x01,        # Unit ID
             0x03,        # Function code
             0x02,        # Byte count
             0x00, 0x01   # Data (register value)
         ])
        with self.assertRaises(exceptions.ModbusException):
            self.port.readBuffer()

    def test_write_successful_blocking(self):
        """Test successful data writing in blocking mode"""
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = 0  # Success
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort()
        result = self.port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        self.mock_sock.send.return_value = len(self.port._buff)  # All bytes sent
        
        result = self.port.write()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertEqual(self.port._state, ModbusPort.State.STATE_OPENED)
        self.mock_sock.send.assert_called_once_with(self.port._buff)

    def test_write_successful_nonblocking(self):
        """Test successful data writing in nonblocking mode"""
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = 0  # Success
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(blocking=False)
        result = self.port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        self.mock_sock.send.return_value = len(self.port._buff)  # All bytes sent
        
        result = self.port.write()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertEqual(self.port._state, ModbusPort.State.STATE_OPENED)
        self.mock_sock.send.assert_called_once_with(self.port._buff)
        
    def test_write_socket_error_blocking(self):
        """Test blocking write failure due to socket error"""
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = 0  # Success
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort()
        result = self.port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        self.mock_sock.send.side_effect = self.orig_socket.error("Connection lost")
        
        with self.assertRaises(exceptions.TcpWriteError):
            self.port.write()
        self.mock_sock.send.assert_called_once()

    def test_write_socket_error_nonblocking(self):
        """Test nonblocking write failure due to socket error"""
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = 0  # Success
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(blocking=False)
        result = self.port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        self.mock_sock.send.side_effect = self.orig_socket.error("Connection lost")
        
        with self.assertRaises(exceptions.TcpWriteError):
            self.port.write()
        self.mock_sock.send.assert_called_once()

    def test_write_connection_lost(self):
        """Test write when connection is lost (send returns negative)"""
        self.mock_socket_module.socket.return_value = self.mock_sock
        self.mock_sock.connect_ex.return_value = 0  # Success
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort()
        result = self.port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        self.mock_sock.send.return_value = -1  # Connection lost
        
        with self.assertRaises(exceptions.TcpWriteError):
            self.port.write()
        self.mock_sock.send.assert_called_once()

    def test_read_successful(self):
        for blocking in (True, False):
            with self.subTest(blocking=blocking):
                self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
                self.port = ModbusTcpPort(blocking=blocking, sock=self.mock_sock)
                test_data = b'\x00\x01\x00\x00\x00\x05\x01\x03\x02\x00\x01'
                self.mock_sock.recv.return_value = test_data

                result = self.port.read()
                self.assertEqual(result, StatusCode.Status_Good)
                self.assertEqual(self.port._buff, bytearray(test_data))
                self.mock_sock.recv.assert_called_once()

                self.port.close()  # avoid destructor calling real select

                # reset mock for the next subTest iteration
                self.mock_sock.recv.reset_mock()

    def test_read_connection_closed_client_mode(self):
        """Test read when connection is closed by remote (client mode)"""
        for blocking in (True, False):
            with self.subTest(blocking=blocking):
                self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
                self.port = ModbusTcpPort(blocking=blocking, sock=self.mock_sock)
                test_data = b''
                self.mock_sock.recv.return_value = test_data
                
                with patch.object(self.port, 'close') as mock_close:
                    with self.assertRaises(exceptions.TcpReadError):
                        self.port.read()
                    mock_close.assert_called()

                    self.mock_sock.recv.reset_mock()

    def test_read_connection_closed_server_mode(self):
        """Test read when connection is closed by remote (server mode)"""
        for blocking in (True, False):
            with self.subTest(blocking=blocking):
                self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
                self.port = ModbusTcpPort(blocking=blocking, sock=self.mock_sock)
                self.port.setServerMode(True)
                test_data = b''
                self.mock_sock.recv.return_value = test_data # Connection closed
                with patch.object(self.port, 'close') as mock_close:
                    result = self.port.read()
                    self.assertEqual(result, StatusCode.Status_Uncertain)
                    mock_close.assert_called()

    def test_read_timeout_blocking(self):
        """Test read timeout in blocking mode"""
        for blocking in (True, False):
            with self.subTest(blocking=blocking):
                with patch('libmodbuspy.tcpport.timer') as mock_timer:
                    self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
                    self.port = ModbusTcpPort(blocking=blocking, sock=self.mock_sock)
                    self.port.setServerMode(True)
                    self.mock_sock.recv.side_effect = socket.timeout("Timeout")
                    mock_timer.side_effect = [0, self.port.Timeout + 1]  # Simulate timeout exceeded
                    with patch.object(self.port, 'close') as mock_close:
                        with self.assertRaises(exceptions.TcpReadError):
                            self.port.read()
                        mock_close.assert_called()

    def test_read_would_block_within_timeout(self):
        """Test read EWOULDBLOCK within timeout period"""
        with patch('libmodbuspy.tcpport.timer') as mock_timer:
            self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
            self.port = ModbusTcpPort(blocking=False, sock=self.mock_sock)
            # Create socket error with EWOULDBLOCK
            socket_error = socket.error()
            socket_error.errno = socket.EWOULDBLOCK
            self.mock_sock.recv.side_effect = socket_error
            # Mock timer to show we're still within timeout
            mock_timer.side_effect = [0, self.port.Timeout // 2]  # Start time, current time
            result = self.port.read()
            self.assertIsNone(result)  # Should return None to continue later

    def test_read_would_block_timeout_exceeded(self):
        """Test read EWOULDBLOCK when timeout exceeded"""
        with patch('libmodbuspy.tcpport.timer') as mock_timer:
            self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
            self.port = ModbusTcpPort(blocking=False, sock=self.mock_sock)
            # Create socket error with EWOULDBLOCK
            socket_error = socket.error()
            socket_error.errno = socket.EWOULDBLOCK
            self.mock_sock.recv.side_effect = socket_error
            
            # Mock timer to show timeout exceeded
            mock_timer.side_effect = [0, self.port.Timeout+1]  # Start time, current time (timeout=1000ms)
            
            with patch.object(self.port, 'close') as mock_close:
                with self.assertRaises(exceptions.TcpReadError):
                    self.port.read()
                mock_close.assert_called()

    def test_read_other_socket_error(self):
        """Test read with other socket errors"""
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(blocking=False, sock=self.mock_sock)
        # Create socket error with different errno
        socket_error = socket.error("Connection reset")
        socket_error.errno = socket.errno.ECONNRESET
        self.mock_sock.recv.side_effect = socket_error
        
        with patch.object(self.port, 'close') as mock_close:
            with self.assertRaises(exceptions.TcpReadError):
                self.port.read()
            mock_close.assert_called()

    def test_destructor_calls_close(self):
        """Test that destructor calls close method"""
        # Temporarily unpatch the __del__ method for this specific test
        self.mock_select_module.select.return_value = ([self.mock_sock], [self.mock_sock], [])
        self.port = ModbusTcpPort(blocking=False, sock=self.mock_sock)
        with patch.object(self.port, 'close') as mock_close:
            self.port.__del__()
            self.port = None  # Avoid further references
            mock_close.assert_called_once()

if __name__ == '__main__':
    unittest.main()