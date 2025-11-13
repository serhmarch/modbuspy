import unittest
from unittest.mock import Mock, patch, MagicMock, call
import socket
import select
import sys
import os

# Add the parent directory to the path to import modbuspy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modbuspy.tcpport import ModbusTcpPort
from modbuspy.statuscode import StatusCode
from modbuspy.port import ModbusPort
from modbuspy.mbglobal import ProtocolType, Constants, timer
from modbuspy import exceptions

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

        self.patcher_socket = patch('modbuspy.tcpport.socket')
        self.mock_socket_module = self.patcher_socket.start()
        self.mock_socket_module.EWOULDBLOCK = socket.EWOULDBLOCK

        self.addCleanup(self.patcher_socket.stop)

        self.patcher_select = patch('modbuspy.tcpport.select')
        self.mock_select_module = self.patcher_select.start()
        self.addCleanup(self.patcher_select.stop)

        mock_sock = Mock() 
        mock_sock.fileno.return_value = 10            #    
        self.mock_sock = mock_sock

        # prevent select.select calls raising errors when called in destructor
        self.mock_select_module.select.return_value = ([], [], [])

        self.port = ModbusTcpPort()

    def tearDown(self):
        """Clean up after each test method."""
        # Avoid destructor call non mock select
        # in inappropriate garbage collection cleanup time
        # which lead to calls to select.select with mock objects
        self.port.close()

    def test_initialization_defaults(self):
        """Test ModbusTcpPort initialization with default values"""
        #port = ModbusTcpPort()
        
        d = ModbusTcpPort.Defaults
        # Test default values
        self.assertEqual(self.port.host(), d.host)
        self.assertEqual(self.port.port(), d.port)
        self.assertEqual(self.port.timeout(), d.timeout)
        self.assertEqual(self.port.type(), ProtocolType.TCP)
        self.assertTrue(self.port.autoIncrement())
        self.assertEqual(self.port.transactionId(), 0)

    def test_settings_management(self):
        """Test settings get/set functionality"""
        settings = {
            "host": "192.168.1.10",
            "port": 5020,
            "timeout": 2000
        }
        
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

    #def test1(self):
    #    with patch('select.select') as mock_select:
    #        mock_sock = Mock() 
    #        mock_sock.fileno.return_value = 10
    #            #    
    #        # Mock select for isOpen check
    #        mock_select.return_value = ([], [mock_sock], [])
    #        port = ModbusTcpPort(sock=mock_sock)
    #        self.assertEqual(port._sock, mock_sock)
    #        self.assertEqual(port._state, ModbusPort.State.STATE_OPENED)
    #        del port

    def test_initialization_with_socket(self):
        """Test ModbusTcpPort initialization with existing socket"""
        mock_sock = Mock() 
        mock_sock.fileno.return_value = 10
            #    
        # Mock select for isOpen check
        self.mock_select_module.select.return_value = ([], [mock_sock], [])
        port = ModbusTcpPort(sock=mock_sock)
        self.assertIs(port.socket(), mock_sock)
        self.assertTrue(port.isOpen())
        del port

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
        # Test with no socket
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
        self.assertEqual(self.port.timeout(), d.timeout)  # Default value
        self.assertEqual(self.port.Timeout, d.timeout)  # Property

        self.port.setTimeout(5000)
        self.assertEqual(self.port.timeout(), 5000)
        self.assertEqual(self.port.Timeout, 5000)  # Property

    def test_auto_increment_methods(self):
        """Test auto-increment and transaction ID behavior"""
        # Test default auto-increment behavior
        self.assertTrue(self.port.autoIncrement())
        
        # Test setting next request repeated
        self.port.setNextRequestRepeated(False)
        self.assertFalse(self.port.autoIncrement())

        self.port.setNextRequestRepeated(True)
        self.assertTrue(self.port.autoIncrement())
        
    def test_open_successful_connection_blocking(self):
        """Test successful TCP connection opening in blocking mode"""
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
        port = ModbusTcpPort(blocking=False)
        self.mock_sock.connect_ex.return_value = 0  # Success
        socket = self.mock_socket_module
        socket.socket.return_value = self.mock_sock
        
        result = port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertEqual(port._state, ModbusPort.State.STATE_OPENED)
        
        # Verify non-blocking mode set
        self.mock_sock.setblocking.assert_called_once_with(False)
        self.mock_sock.connect_ex.assert_called_once_with((self.port.Host, self.port.Port))
        
        #port.__del__ # indirectly call `select.select` with mock objects
        port.close()

    def test_open_connection_failure(self):
        """Test TCP connection failure"""
        self.mock_sock.connect_ex.return_value = self.orig_socket.errno.ECONNREFUSED  # Connection refused
        socket = self.mock_socket_module
        socket.socket.return_value = self.mock_sock
        
        with self.assertRaises(exceptions.TcpConnectError):
            self.port.open()
            
        self.assertFalse(self.port.isOpen())
        self.assertEqual(self.port._state, ModbusPort.State.STATE_CLOSED)
#
    #@patch('socket.socket')
    #def test_open_socket_creation_error(self, mock_socket_class):
    #    """Test socket creation error"""
    #    mock_socket_class.side_effect = OSError("Socket creation failed")
    #    
    #    with self.assertRaises(exceptions.TcpCreateError):
    #        self.port.open()
#
    #@patch('socket.socket')
    #@patch('select.select')
    #def test_open_non_blocking_success_after_wait(self, mock_select, mock_socket_class):
    #    """Test non-blocking connection success after waiting"""
    #    port = ModbusTcpPort(blocking=False)
    #    mock_sock = Mock()
    #    mock_socket_class.return_value = mock_sock
    #    mock_sock.connect_ex.return_value = socket.EWOULDBLOCK
    #    mock_sock.fileno.return_value = 10
    #    
    #    # First call to select returns socket ready for write
    #    mock_select.return_value = ([], [mock_sock], [])
    #    
    #    result = port.open()
    #    
    #    self.assertEqual(result, StatusCode.Status_Good)
    #    self.assertEqual(port._state, ModbusPort.State.STATE_OPENED)
    #    
    #    # Verify select was called with correct parameters
    #    mock_select.assert_called_with([], [mock_sock], [mock_sock], 0.0)
#
    #@patch('socket.socket')
    #@patch('select.select')
    #@patch('modbuspy.mbglobal.timer')
    #def test_open_non_blocking_timeout(self, mock_timer, mock_select, mock_socket_class):
    #    """Test non-blocking connection timeout"""
    #    port = ModbusTcpPort(blocking=False)
    #    mock_sock = Mock()
    #    mock_socket_class.return_value = mock_sock
    #    mock_sock.connect_ex.return_value = socket.EWOULDBLOCK
    #    mock_sock.fileno.return_value = 10
    #    
    #    # Mock select to return no ready sockets (timeout)
    #    mock_select.return_value = ([], [], [])
    #    
    #    # Mock timer to simulate timeout
    #    mock_timer.side_effect = [0, 2000]  # Start time, then past timeout
    #    
    #    with self.assertRaises(exceptions.TcpConnectError):
    #        port.open()
    #        
    #    mock_sock.close.assert_called_once()
#
    #@patch('socket.socket')
    #@patch('select.select')
    #def test_open_connection_error_in_select(self, mock_select, mock_socket_class):
    #    """Test connection error detected by select"""
    #    port = ModbusTcpPort(blocking=False)
    #    mock_sock = Mock()
    #    mock_socket_class.return_value = mock_sock
    #    mock_sock.connect_ex.return_value = socket.EWOULDBLOCK
    #    mock_sock.fileno.return_value = 10
    #    
    #    # Mock select to return error socket
    #    mock_select.return_value = ([], [], [mock_sock])
    #    
    #    with self.assertRaises(exceptions.TcpConnectError):
    #        port.open()
    #        
    #    mock_sock.close.assert_called_once()
#
    #def test_open_already_open_unchanged(self):
    #    """Test opening already opened connection with no changes"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = 10
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._changed = False
    #    
    #    with patch('select.select', return_value=([], [mock_sock], [])):
    #        result = self.port.open()
    #        
    #    self.assertEqual(result, StatusCode.Status_Good)
#
    #def test_open_already_open_but_changed(self):
    #    """Test opening already opened connection but settings changed"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = 10
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._changed = True
    #    
    #    # Should close existing connection
    #    result = self.port.close()
    #    self.assertEqual(result, StatusCode.Status_Good)
    #    self.assertIsNone(self.port._sock)
#
    #def test_close_open_connection(self):
    #    """Test closing an open connection"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = 10
    #    self.port._sock = mock_sock
    #    
    #    with patch('select.select', return_value=([], [mock_sock], [])):
    #        result = self.port.close()
    #        
    #    self.assertEqual(result, StatusCode.Status_Good)
    #    mock_sock.shutdown.assert_called_once_with(socket.SHUT_RDWR)
    #    mock_sock.close.assert_called_once()
    #    self.assertIsNone(self.port._sock)
    #    self.assertEqual(self.port._state, ModbusPort.State.STATE_CLOSED)
#
    #def test_close_with_socket_error(self):
    #    """Test closing connection when socket operations fail"""
    #    mock_sock = Mock()
    #    mock_sock.shutdown.side_effect = OSError("Socket error")
    #    mock_sock.close.side_effect = OSError("Socket error")
    #    self.port._sock = mock_sock
    #    
    #    # Should not raise exception
    #    result = self.port.close()
    #    
    #    self.assertEqual(result, StatusCode.Status_Good)
    #    self.assertIsNone(self.port._sock)
#
    #def test_close_no_connection(self):
    #    """Test closing when no connection exists"""
    #    self.port._sock = None
    #    
    #    result = self.port.close()
    #    
    #    self.assertEqual(result, StatusCode.Status_Good)
#
    #@patch('select.select')
    #def test_is_open_with_valid_socket(self, mock_select):
    #    """Test isOpen() with valid socket"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = 10
    #    self.port._sock = mock_sock
    #    
    #    # Mock select to return socket as readable/writable
    #    mock_select.return_value = ([mock_sock], [], [])
    #    
    #    self.assertTrue(self.port.isOpen())
    #    mock_select.assert_called_once_with([mock_sock], [mock_sock], [], 0.0)
#
    #@patch('select.select')
    #def test_is_open_with_writable_socket(self, mock_select):
    #    """Test isOpen() with writable socket"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = 10
    #    self.port._sock = mock_sock
    #    
    #    # Mock select to return socket as writable only
    #    mock_select.return_value = ([], [mock_sock], [])
    #    
    #    self.assertTrue(self.port.isOpen())
#
    #def test_is_open_no_socket(self):
    #    """Test isOpen() with no socket"""
    #    self.port._sock = None
    #    
    #    self.assertFalse(self.port.isOpen())
#
    #def test_is_open_invalid_socket(self):
    #    """Test isOpen() with invalid socket file descriptor"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = -1  # Invalid fd
    #    self.port._sock = mock_sock
    #    
    #    self.assertFalse(self.port.isOpen())
#
    #@patch('select.select')
    #def test_is_open_not_ready(self, mock_select):
    #    """Test isOpen() when socket is not ready"""
    #    mock_sock = Mock()
    #    mock_sock.fileno.return_value = 10
    #    self.port._sock = mock_sock
    #    
    #    # Mock select to return no ready sockets
    #    mock_select.return_value = ([], [], [])
    #    
    #    self.assertFalse(self.port.isOpen())
#
    #def test_write_successful(self):
    #    """Test successful data writing"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
    #    
    #    mock_sock.send.return_value = 12  # All bytes sent
    #    
    #    result = self.port.write()
    #    
    #    self.assertEqual(result, StatusCode.Status_Good)
    #    self.assertEqual(self.port._state, ModbusPort.State.STATE_OPENED)
    #    mock_sock.send.assert_called_once_with(self.port._buff)
#
    #def test_write_socket_error(self):
    #    """Test write failure due to socket error"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
    #    
    #    mock_sock.send.side_effect = socket.error("Connection lost")
    #    
    #    with self.assertRaises(exceptions.TcpWriteError):
    #        self.port.write()
#
    #def test_write_connection_lost(self):
    #    """Test write when connection is lost (send returns negative)"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
    #    
    #    mock_sock.send.return_value = -1  # Connection lost
    #    
    #    with patch.object(self.port, 'close') as mock_close:
    #        with self.assertRaises(exceptions.TcpWriteError):
    #            self.port.write()
    #        mock_close.assert_called_once()
#
    #def test_write_invalid_state(self):
    #    """Test write in invalid state"""
    #    self.port._state = ModbusPort.State.STATE_CLOSED
    #    
    #    result = self.port.write()
    #    
    #    self.assertIsNone(result)
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_successful(self, mock_timer):
    #    """Test successful data reading"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    
    #    test_data = b'\x00\x01\x00\x00\x00\x05\x01\x03\x02\x00\x01'
    #    mock_sock.recv.return_value = test_data
    #    mock_timer.return_value = 1000
    #    
    #    result = self.port.read()
    #    
    #    self.assertEqual(result, StatusCode.Status_Good)
    #    self.assertEqual(self.port._buff, bytearray(test_data))
    #    self.assertEqual(self.port._state, ModbusPort.State.STATE_OPENED)
    #    mock_sock.recv.assert_called_once_with(1024)
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_connection_closed_client_mode(self, mock_timer):
    #    """Test read when connection is closed by remote (client mode)"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._modeServer = False  # Client mode
    #    
    #    mock_sock.recv.return_value = b''  # Connection closed
    #    mock_timer.return_value = 1000
    #    
    #    with patch.object(self.port, 'close') as mock_close:
    #        with self.assertRaises(exceptions.TcpReadError):
    #            self.port.read()
    #        mock_close.assert_called_once()
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_connection_closed_server_mode(self, mock_timer):
    #    """Test read when connection is closed by remote (server mode)"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    self.port._modeServer = True  # Server mode
    #    
    #    mock_sock.recv.return_value = b''  # Connection closed
    #    mock_timer.return_value = 1000
    #    
    #    with patch.object(self.port, 'close') as mock_close:
    #        result = self.port.read()
    #        self.assertEqual(result, StatusCode.Status_Uncertain)
    #        mock_close.assert_called_once()
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_timeout_blocking(self, mock_timer):
    #    """Test read timeout in blocking mode"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    
    #    mock_sock.recv.side_effect = socket.timeout("Timeout")
    #    mock_timer.return_value = 1000
    #    
    #    with patch.object(self.port, 'close') as mock_close:
    #        with self.assertRaises(exceptions.TcpReadError):
    #            self.port.read()
    #        mock_close.assert_called_once()
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_would_block_within_timeout(self, mock_timer):
    #    """Test read EWOULDBLOCK within timeout period"""
    #    port = ModbusTcpPort(blocking=False)
    #    mock_sock = Mock()
    #    port._sock = mock_sock
    #    port._state = ModbusPort.State.STATE_OPENED
    #    
    #    # Create socket error with EWOULDBLOCK
    #    socket_error = socket.error()
    #    socket_error.errno = socket.EWOULDBLOCK
    #    mock_sock.recv.side_effect = socket_error
    #    
    #    # Mock timer to show we're still within timeout
    #    mock_timer.side_effect = [1000, 1500]  # Start time, current time
    #    
    #    result = port.read()
    #    
    #    self.assertIsNone(result)  # Should return None to continue later
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_would_block_timeout_exceeded(self, mock_timer):
    #    """Test read EWOULDBLOCK when timeout exceeded"""
    #    port = ModbusTcpPort(blocking=False)
    #    mock_sock = Mock()
    #    port._sock = mock_sock
    #    port._state = ModbusPort.State.STATE_OPENED
    #    
    #    # Create socket error with EWOULDBLOCK
    #    socket_error = socket.error()
    #    socket_error.errno = socket.EWOULDBLOCK
    #    mock_sock.recv.side_effect = socket_error
    #    
    #    # Mock timer to show timeout exceeded
    #    mock_timer.side_effect = [1000, 2500]  # Start time, current time (timeout=1000ms)
    #    
    #    with patch.object(port, 'close') as mock_close:
    #        with self.assertRaises(exceptions.TcpReadError):
    #            port.read()
    #        mock_close.assert_called_once()
#
    #@patch('modbuspy.mbglobal.timer')
    #def test_read_other_socket_error(self, mock_timer):
    #    """Test read with other socket errors"""
    #    mock_sock = Mock()
    #    self.port._sock = mock_sock
    #    self.port._state = ModbusPort.State.STATE_OPENED
    #    
    #    # Create socket error with different errno
    #    socket_error = socket.error("Connection reset")
    #    socket_error.errno = socket.ECONNRESET
    #    mock_sock.recv.side_effect = socket_error
    #    mock_timer.return_value = 1000
    #    
    #    with patch.object(self.port, 'close') as mock_close:
    #        with self.assertRaises(exceptions.TcpReadError):
    #            self.port.read()
    #        mock_close.assert_called_once()
#
    #def test_read_invalid_state(self):
    #    """Test read in invalid state"""
    #    self.port._state = ModbusPort.State.STATE_CLOSED
    #    
    #    result = self.port.read()
    #    
    #    self.assertIsNone(result)
#
    #def test_write_buffer_client_mode(self):
    #    """Test writeBuffer method in client mode"""
    #    self.port._modeServer = False
    #    self.port._transaction = 0
    #    
    #    unit = 1
    #    func = 3
    #    data = b'\x00\x00\x00\x02'  # Read 2 registers from address 0
    #    
    #    result = self.port.writeBuffer(unit, func, data)
    #    
    #    self.assertTrue(result)
    #    self.assertEqual(self.port._transaction, 1)  # Should increment
    #    self.assertEqual(self.port._unit, unit)
    #    self.assertEqual(self.port._func, func)
    #    
    #    buff = self.port._buff
    #    self.assertEqual(len(buff), 12)  # 6-byte TCP header + 1 unit + 1 func + 4 data
    #    
    #    # Check TCP header format
    #    transaction_id = (buff[0] << 8) | buff[1]
    #    self.assertEqual(transaction_id, 1)
    #    
    #    protocol_id = (buff[2] << 8) | buff[3]
    #    self.assertEqual(protocol_id, 0)
    #    
    #    length = (buff[4] << 8) | buff[5]
    #    self.assertEqual(length, 6)  # unit + func + data length
    #    
    #    self.assertEqual(buff[6], unit)
    #    self.assertEqual(buff[7], func)
    #    self.assertEqual(buff[8:], data)
#
    #def test_write_buffer_server_mode(self):
    #    """Test writeBuffer method in server mode"""
    #    self.port._modeServer = True
    #    initial_transaction = 42
    #    self.port._transaction = initial_transaction
    #    
    #    unit = 1
    #    func = 3
    #    data = b'\x02\x00\x01'  # Response data
    #    
    #    result = self.port.writeBuffer(unit, func, data)
    #    
    #    self.assertTrue(result)
    #    # In server mode, transaction ID should not increment
    #    self.assertEqual(self.port._transaction, initial_transaction)
#
    #def test_write_buffer_transaction_rollover(self):
    #    """Test writeBuffer transaction ID rollover at 65536"""
    #    self.port._modeServer = False
    #    self.port._transaction = 65535  # Max value
    #    
    #    result = self.port.writeBuffer(1, 3, b'\x00\x00')
    #    
    #    self.assertTrue(result)
    #    self.assertEqual(self.port._transaction, 1)  # Should rollover to 1
#
    #def test_read_buffer_valid_response(self):
    #    """Test readBuffer method with valid TCP response"""
    #    # Create a valid TCP response
    #    response = bytearray([
    #        0x00, 0x01,  # Transaction ID
    #        0x00, 0x00,  # Protocol ID
    #        0x00, 0x05,  # Length (5 bytes)
    #        0x01,        # Unit ID
    #        0x03,        # Function code
    #        0x02,        # Byte count
    #        0x00, 0x01   # Data (register value)
    #    ])
    #    
    #    self.port._buff = response
    #    self.port._transaction = 1  # Set expected transaction ID
    #    self.port._modeServer = False
    #    
    #    unit, func, data = self.port.readBuffer()
    #    
    #    self.assertEqual(unit, 1)
    #    self.assertEqual(func, 3)
    #    self.assertEqual(data, bytearray([0x02, 0x00, 0x01]))
#
    #def test_read_buffer_server_mode(self):
    #    """Test readBuffer method in server mode"""
    #    response = bytearray([
    #        0x00, 0x05,  # Transaction ID
    #        0x00, 0x00,  # Protocol ID  
    #        0x00, 0x06,  # Length
    #        0x01,        # Unit ID
    #        0x03,        # Function code
    #        0x00, 0x00,  # Start address
    #        0x00, 0x02   # Quantity
    #    ])
    #    
    #    self.port._buff = response
    #    self.port._modeServer = True
    #    
    #    unit, func, data = self.port.readBuffer()
    #    
    #    self.assertEqual(unit, 1)
    #    self.assertEqual(func, 3)
    #    self.assertEqual(data, bytearray([0x00, 0x00, 0x00, 0x02]))
    #    # In server mode, transaction should be updated from received data
    #    self.assertEqual(self.port._transaction, 5)
#
    #def test_read_buffer_too_short(self):
    #    """Test readBuffer with too short response"""
    #    self.port._buff = bytearray([0x00, 0x01])  # Only 2 bytes
    #    
    #    with self.assertRaises(exceptions.NotCorrectResponseError):
    #        self.port.readBuffer()
#
    #def test_read_buffer_invalid_protocol_id(self):
    #    """Test readBuffer with invalid protocol ID"""
    #    response = bytearray([
    #        0x00, 0x01,  # Transaction ID
    #        0x00, 0x01,  # Invalid Protocol ID (should be 0x00, 0x00)
    #        0x00, 0x05,  # Length
    #        0x01,        # Unit ID
    #        0x03,        # Function code
    #        0x02, 0x00, 0x01  # Data
    #    ])
    #    
    #    self.port._buff = response
    #    
    #    with self.assertRaises(exceptions.NotCorrectResponseError):
    #        self.port.readBuffer()
#
    #def test_read_buffer_incorrect_length(self):
    #    """Test readBuffer with incorrect length field"""
    #    response = bytearray([
    #        0x00, 0x01,  # Transaction ID
    #        0x00, 0x00,  # Protocol ID
    #        0x00, 0x10,  # Incorrect Length (should be 5)
    #        0x01,        # Unit ID
    #        0x03,        # Function code
    #        0x02, 0x00, 0x01  # Data
    #    ])
    #    
    #    self.port._buff = response
    #    
    #    with self.assertRaises(exceptions.NotCorrectResponseError):
    #        self.port.readBuffer()
#
    #def test_read_buffer_wrong_transaction_id(self):
    #    """Test readBuffer with wrong transaction ID in client mode"""
    #    response = bytearray([
    #        0x00, 0x05,  # Wrong Transaction ID
    #        0x00, 0x00,  # Protocol ID
    #        0x00, 0x05,  # Length
    #        0x01,        # Unit ID
    #        0x03,        # Function code
    #        0x02, 0x00, 0x01  # Data
    #    ])
    #    
    #    self.port._buff = response
    #    self.port._transaction = 1  # Expected transaction ID
    #    self.port._modeServer = False
    #    
    #    with self.assertRaises(exceptions.NotCorrectResponseError):
    #        self.port.readBuffer()
#
    #def test_destructor_calls_close(self):
    #    """Test that destructor calls close method"""
    #    # Temporarily unpatch the __del__ method for this specific test
    #    self.del_patcher.stop()
    #    
    #    try:
    #        # Create a new port instance for this test
    #        port = ModbusTcpPort()
    #        mock_sock = Mock()
    #        port._sock = mock_sock
    #        
    #        # Mock isOpen to prevent select.select calls
    #        with patch.object(port, 'isOpen', return_value=False):
    #            with patch.object(port, 'close') as mock_close:
    #                port.__del__()
    #                mock_close.assert_called_once()
    #    finally:
    #        # Restart the patcher
    #        self.del_patcher.start()

if __name__ == '__main__':
    unittest.main()