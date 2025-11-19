import unittest
from unittest.mock import Mock, patch, MagicMock, call, PropertyMock
import serial
import sys
import os

# Add the parent directory to the path to import libmodbuspy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libmodbuspy.serialport import ModbusSerialPort
from libmodbuspy.rtuport import ModbusRtuPort
from libmodbuspy.statuscode import StatusCode
from libmodbuspy.port import ModbusPort
from libmodbuspy.mbglobal import ProtocolType, Parity, StopBits, FlowControl, timer
from libmodbuspy import exceptions


class TestModbusSerialPort(unittest.TestCase):
    """Comprehensive test cases for ModbusSerialPort class using ModbusRtuPort as concrete implementation"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.orig_serial = serial
        
        # Patch the serial module
        self.patcher_serial = patch('libmodbuspy.serialport.serial')
        self.mock_serial_module = self.patcher_serial.start()
        
        # Set up mock constants to match real serial module
        self.mock_serial_module.PARITY_NONE = serial.PARITY_NONE
        self.mock_serial_module.PARITY_ODD = serial.PARITY_ODD
        self.mock_serial_module.PARITY_EVEN = serial.PARITY_EVEN
        self.mock_serial_module.PARITY_MARK = serial.PARITY_MARK
        self.mock_serial_module.PARITY_SPACE = serial.PARITY_SPACE
        self.mock_serial_module.STOPBITS_ONE = serial.STOPBITS_ONE
        self.mock_serial_module.STOPBITS_ONE_POINT_FIVE = serial.STOPBITS_ONE_POINT_FIVE
        self.mock_serial_module.STOPBITS_TWO = serial.STOPBITS_TWO
        self.mock_serial_module.SerialException = serial.SerialException
        
        # Create a mock serial object
        self.mock_serial_obj = MagicMock()
        self.mock_serial_obj.is_open = False
        self.mock_serial_module.Serial.return_value = self.mock_serial_obj
        
        self.addCleanup(self.patcher_serial.stop)
        
        self.port = None

    def tearDown(self):
        """Clean up after each test method."""
        if self.port is not None:
            try:
                self.port.close()
            except:
                pass

    # ===== Initialization Tests =====
    
    def test_initialization_defaults_blocking(self):
        """Test ModbusSerialPort initialization with default values in blocking mode"""
        self.port = ModbusRtuPort(blocking=True)
        
        d = ModbusRtuPort.Defaults
        self.assertEqual(self.port.portName(), d.portName)
        self.assertEqual(self.port.baudRate(), d.baudRate)
        self.assertEqual(self.port.dataBits(), d.dataBits)
        self.assertEqual(self.port.parity(), d.parity)
        self.assertEqual(self.port.stopBits(), d.stopBits)
        self.assertEqual(self.port.flowControl(), d.flowControl)
        self.assertEqual(self.port.timeoutFirstByte(), d.timeoutFirstByte)
        self.assertEqual(self.port.timeoutInterByte(), d.timeoutInterByte)
        self.assertTrue(self.port.isBlocking())
        self.assertFalse(self.port.isOpen())

    def test_initialization_defaults_nonblocking(self):
        """Test ModbusSerialPort initialization with default values in non-blocking mode"""
        self.port = ModbusRtuPort(blocking=False)
        
        d = ModbusRtuPort.Defaults
        self.assertEqual(self.port.portName(), d.portName)
        self.assertEqual(self.port.baudRate(), d.baudRate)
        self.assertFalse(self.port.isBlocking())
        self.assertFalse(self.port.isOpen())

    def test_initialization_blocking_mode_sets_read_write_methods(self):
        """Test that blocking mode sets correct read/write methods"""
        self.port = ModbusRtuPort(blocking=True)
        self.assertEqual(self.port._readMethod, self.port._blockingRead)
        self.assertEqual(self.port._writeMethod, self.port._blockingWrite)

    def test_initialization_nonblocking_mode_sets_read_write_methods(self):
        """Test that non-blocking mode sets correct read/write methods"""
        self.port = ModbusRtuPort(blocking=False)
        self.assertEqual(self.port._readMethod, self.port._nonBlockingRead)
        self.assertEqual(self.port._writeMethod, self.port._nonBlockingWrite)

    # ===== Property Tests =====
    
    def test_port_name_property(self):
        """Test port name getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        # Test setter/getter methods
        self.port.setPortName("COM3")
        self.assertEqual(self.port.portName(), "COM3")
        self.assertTrue(self.port.isChanged())
        
        # Reset changed flag
        self.port._changed = False
        
        # Test property syntax
        self.port.PortName = "COM5"
        self.assertEqual(self.port.PortName, "COM5")
        self.assertTrue(self.port.isChanged())
        
        # Test no change when setting same value
        self.port._changed = False
        self.port.setPortName("COM5")
        self.assertFalse(self.port.isChanged())

    def test_baud_rate_property(self):
        """Test baud rate getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        # Test setter/getter methods
        self.port.setBaudRate(19200)
        self.assertEqual(self.port.baudRate(), 19200)
        self.assertTrue(self.port.isChanged())
        
        # Reset changed flag
        self.port._changed = False
        
        # Test property syntax
        self.port.BaudRate = 115200
        self.assertEqual(self.port.BaudRate, 115200)
        self.assertTrue(self.port.isChanged())
        
        # Test no change when setting same value
        self.port._changed = False
        self.port.setBaudRate(115200)
        self.assertFalse(self.port.isChanged())

    def test_data_bits_property(self):
        """Test data bits getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        self.port.setDataBits(7)
        self.assertEqual(self.port.dataBits(), 7)
        self.assertTrue(self.port.isChanged())
        
        # Reset and test property
        self.port._changed = False
        self.port.DataBits = 6
        self.assertEqual(self.port.DataBits, 6)
        self.assertTrue(self.port.isChanged())

    def test_parity_property(self):
        """Test parity getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        self.port.setParity(Parity.EvenParity)
        self.assertEqual(self.port.parity(), Parity.EvenParity)
        self.assertTrue(self.port.isChanged())
        
        # Reset and test property
        self.port._changed = False
        self.port.Parity = Parity.OddParity
        self.assertEqual(self.port.Parity, Parity.OddParity)
        self.assertTrue(self.port.isChanged())

    def test_stop_bits_property(self):
        """Test stop bits getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        self.port.setStopBits(StopBits.TwoStop)
        self.assertEqual(self.port.stopBits(), StopBits.TwoStop)
        self.assertTrue(self.port.isChanged())
        
        # Reset and test property
        self.port._changed = False
        self.port.StopBits = StopBits.OneAndHalfStop
        self.assertEqual(self.port.StopBits, StopBits.OneAndHalfStop)
        self.assertTrue(self.port.isChanged())

    def test_flow_control_property(self):
        """Test flow control getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        self.port.setFlowControl(FlowControl.HardwareControl)
        self.assertEqual(self.port.flowControl(), FlowControl.HardwareControl)
        self.assertTrue(self.port.isChanged())
        
        # Reset and test property
        self.port._changed = False
        self.port.FlowControl = FlowControl.SoftwareControl
        self.assertEqual(self.port.FlowControl, FlowControl.SoftwareControl)
        self.assertTrue(self.port.isChanged())

    def test_timeout_inter_byte_property(self):
        """Test inter-byte timeout getter/setter methods and properties"""
        self.port = ModbusRtuPort()
        
        self.port.setTimeoutInterByte(100)
        self.assertEqual(self.port.timeoutInterByte(), 100)
        self.assertTrue(self.port.isChanged())
        
        # Reset and test property
        self.port._changed = False
        self.port.TimeoutInterByte = 50
        self.assertEqual(self.port.TimeoutInterByte, 50)
        self.assertTrue(self.port.isChanged())

    def test_timeout_first_byte_property(self):
        """Test first byte timeout getter/setter methods"""
        self.port = ModbusRtuPort()
        
        self.port.setTimeoutFirstByte(5000)
        self.assertEqual(self.port.timeoutFirstByte(), 5000)

    # ===== Settings Tests =====
    
    def test_settings_management(self):
        """Test settings get/set functionality"""
        self.port = ModbusRtuPort()
        
        settings = {
            "portName": "COM8",
            "baudRate": 115200,
            "dataBits": 7,
            "parity": Parity.EvenParity,
            "stopBits": StopBits.TwoStop,
            "flowControl": FlowControl.HardwareControl,
            "timeoutInterByte": 100,
            "timeout": 5000
        }
        
        self.port.setSettings(settings)
        
        retrieved_settings = self.port.settings()
        
        self.assertEqual(retrieved_settings["portName"], "COM8")
        self.assertEqual(retrieved_settings["baudRate"], 115200)
        self.assertEqual(retrieved_settings["dataBits"], 7)
        self.assertEqual(retrieved_settings["parity"], Parity.EvenParity)
        self.assertEqual(retrieved_settings["stopBits"], StopBits.TwoStop)
        self.assertEqual(retrieved_settings["flowControl"], FlowControl.HardwareControl)
        self.assertEqual(retrieved_settings["timeoutInterByte"], 100)
        self.assertEqual(retrieved_settings["timeout"], 5000)

    def test_settings_partial_update(self):
        """Test partial settings update"""
        self.port = ModbusRtuPort()
        
        # Set initial values
        initial_settings = {
            "portName": "COM3",
            "baudRate": 19200
        }
        self.port.setSettings(initial_settings)
        
        # Update only port name
        partial_update = {"portName": "COM5"}
        self.port.setSettings(partial_update)
        
        settings = self.port.settings()
        self.assertEqual(settings["portName"], "COM5")
        self.assertEqual(settings["baudRate"], 19200)  # Should remain unchanged

    # ===== Parity Conversion Tests =====
    
    def test_parity_conversion_no_parity(self):
        """Test parity conversion for NoParity"""
        result = ModbusSerialPort.toSerialParity(Parity.NoParity)
        self.assertEqual(result, serial.PARITY_NONE)

    def test_parity_conversion_odd(self):
        """Test parity conversion for OddParity"""
        result = ModbusSerialPort.toSerialParity(Parity.OddParity)
        self.assertEqual(result, serial.PARITY_ODD)

    def test_parity_conversion_even(self):
        """Test parity conversion for EvenParity"""
        result = ModbusSerialPort.toSerialParity(Parity.EvenParity)
        self.assertEqual(result, serial.PARITY_EVEN)

    def test_parity_conversion_mark(self):
        """Test parity conversion for MarkParity"""
        result = ModbusSerialPort.toSerialParity(Parity.MarkParity)
        self.assertEqual(result, serial.PARITY_MARK)

    def test_parity_conversion_space(self):
        """Test parity conversion for SpaceParity"""
        result = ModbusSerialPort.toSerialParity(Parity.SpaceParity)
        self.assertEqual(result, serial.PARITY_SPACE)

    def test_parity_conversion_invalid(self):
        """Test parity conversion with invalid value defaults to NoParity"""
        result = ModbusSerialPort.toSerialParity(999)  # Invalid
        self.assertEqual(result, serial.PARITY_NONE)

    # ===== Stop Bits Conversion Tests =====
    
    def test_stopbits_conversion_one_stop(self):
        """Test stop bits conversion for OneStop"""
        result = ModbusSerialPort.toSerialStopBits(StopBits.OneStop)
        self.assertEqual(result, serial.STOPBITS_ONE)

    def test_stopbits_conversion_one_and_half_stop(self):
        """Test stop bits conversion for OneAndHalfStop"""
        result = ModbusSerialPort.toSerialStopBits(StopBits.OneAndHalfStop)
        self.assertEqual(result, serial.STOPBITS_ONE_POINT_FIVE)

    def test_stopbits_conversion_two_stop(self):
        """Test stop bits conversion for TwoStop"""
        result = ModbusSerialPort.toSerialStopBits(StopBits.TwoStop)
        self.assertEqual(result, serial.STOPBITS_TWO)

    def test_stopbits_conversion_invalid(self):
        """Test stop bits conversion with invalid value defaults to OneStop"""
        result = ModbusSerialPort.toSerialStopBits(999)  # Invalid
        self.assertEqual(result, serial.STOPBITS_ONE)

    # ===== Handle Tests =====
    
    def test_handle_method(self):
        """Test handle() method returns correct file descriptor"""
        self.port = ModbusRtuPort()
        
        # Mock fileno to return specific value
        self.mock_serial_obj.fileno.return_value = 5
        self.assertEqual(self.port.handle(), 5)
        self.mock_serial_obj.fileno.assert_called_once()

    # ===== Open Tests =====
    
    def test_open_successful_blocking(self):
        """Test successful serial port opening in blocking mode"""
        self.port = ModbusRtuPort(blocking=True)
        self.port.setPortName("COM1")
        self.port.setBaudRate(9600)
        self.port.setDataBits(8)
        self.port.setParity(Parity.NoParity)
        self.port.setStopBits(StopBits.OneStop)
        self.port.setTimeoutFirstByte(3000)
        self.port.setTimeoutInterByte(50)
        
        self.mock_serial_obj.is_open = True
        result = self.port.open()
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertTrue(self.port.isOpen())

    def test_open_successful_nonblocking(self):
        """Test successful serial port opening in non-blocking mode"""
        self.port = ModbusRtuPort(blocking=False)
        self.port.setPortName("COM2")
        
        self.mock_serial_obj.is_open = True
        
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)
        # In non-blocking mode, timeout should be 0.0
        self.assertEqual(self.mock_serial_obj.timeout, 0.0)
        self.assertEqual(self.mock_serial_obj.inter_byte_timeout, 0.0)

    def test_open_serial_exception(self):
        """Test serial port open failure with SerialException"""
        self.port = ModbusRtuPort()
        self.port.setPortName("COM99")  # Non-existent port
        
        self.mock_serial_obj.open.side_effect = self.orig_serial.SerialException("Port not found")
        
        with self.assertRaises(exceptions.SerialOpenError):
            self.port.open()

    def test_open_already_open_no_changes(self):
        """Test opening when port is already open with no changes"""
        self.port = ModbusRtuPort()
        self.port.setPortName("COM1")
        
        # First open
        self.mock_serial_obj.is_open = True
        result1 = self.port.open()
        self.assertEqual(result1, StatusCode.Status_Good)
        
        # Reset mock
        self.mock_serial_obj.reset_mock()
        self.mock_serial_obj.is_open = True
        
        # Second open (should not try to open again)
        result2 = self.port.open()
        self.assertEqual(result2, StatusCode.Status_Good)
        # open() should not be called since port is already open and unchanged
        self.mock_serial_obj.open.assert_not_called()

    def test_open_already_open_with_changes(self):
        """Test opening when port is already open but settings changed"""
        self.port = ModbusRtuPort()
        self.port.setPortName("COM1")
        
        # First open
        self.mock_serial_obj.is_open = True
        result1 = self.port.open()
        self.assertEqual(result1, StatusCode.Status_Good)
        self.mock_serial_obj.reset_mock()
        
        # Change settings
        self.port.setBaudRate(19200)
        self.mock_serial_obj.is_open = True
        
        # Second open (should close and reopen)
        result2 = self.port.open()
        self.assertEqual(result2, StatusCode.Status_Good)
        # close() should be called, then open()
        self.mock_serial_obj.close.assert_called_once()
        self.mock_serial_obj.open.assert_called_once()

    def test_open_flow_control_no_flow(self):
        """Test port open with no flow control"""
        self.port = ModbusRtuPort()
        self.port.setFlowControl(FlowControl.NoFlowControl)
        
        self.mock_serial_obj.is_open = True
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)

    def test_open_flow_control_hardware(self):
        """Test port open with hardware flow control"""
        self.port = ModbusRtuPort()
        self.port.setFlowControl(FlowControl.HardwareControl)
        
        self.mock_serial_obj.is_open = True
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)

    def test_open_flow_control_software(self):
        """Test port open with software flow control"""
        self.port = ModbusRtuPort()
        self.port.setFlowControl(FlowControl.SoftwareControl)
        
        self.mock_serial_obj.is_open = True
        result = self.port.open()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertTrue(self.mock_serial_obj.xonxoff)
        self.assertFalse(self.mock_serial_obj.rtscts)
        self.assertFalse(self.mock_serial_obj.dsrdtr)

    # ===== Close Tests =====
    
    def test_close_open_port(self):
        """Test closing an open port"""
        self.port = ModbusRtuPort()
        self.mock_serial_obj.is_open = True
        
        result = self.port.close()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.mock_serial_obj.close.assert_called_once()
        self.assertEqual(self.port._state, ModbusPort.State.STATE_CLOSED)

    def test_close_already_closed_port(self):
        """Test closing an already closed port"""
        self.port = ModbusRtuPort()
        self.mock_serial_obj.is_open = False
        
        result = self.port.close()
        
        self.assertEqual(result, StatusCode.Status_Good)

    # ===== IsOpen Tests =====
    
    def test_is_open_when_open(self):
        """Test isOpen() when port is open"""
        self.port = ModbusRtuPort()
        self.mock_serial_obj.is_open = True
        
        self.assertTrue(self.port.isOpen())

    def test_is_open_when_closed(self):
        """Test isOpen() when port is closed"""
        self.port = ModbusRtuPort()
        self.mock_serial_obj.is_open = False
        
        self.assertFalse(self.port.isOpen())

    # ===== Blocking Write Tests =====
    
    def test_blocking_write_successful(self):
        """Test successful blocking write"""
        self.port = ModbusRtuPort(blocking=True)
        self.mock_serial_obj.is_open = True
        
        # Prepare buffer
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        result = self.port.write()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.mock_serial_obj.reset_input_buffer.assert_called_once()
        self.mock_serial_obj.write.assert_called_once_with(self.port._buff)

    def test_blocking_write_serial_exception(self):
        """Test blocking write with serial exception"""
        self.port = ModbusRtuPort(blocking=True)
        self.mock_serial_obj.is_open = True
        
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        self.mock_serial_obj.write.side_effect = self.orig_serial.SerialException("Write failed")
        
        with self.assertRaises(exceptions.SerialWriteError):
            self.port.write()

    # ===== Blocking Read Tests =====
    
    def test_blocking_read_successful(self):
        """Test successful blocking read"""
        self.port = ModbusRtuPort(blocking=True)
        self.mock_serial_obj.is_open = True
        
        # Simulate receiving data
        received_data = b'\x00\x01\x00\x00\x00\x05\x01\x03\x02\x00\x01'
        self.mock_serial_obj.read.return_value = received_data
        
        result = self.port.read()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.mock_serial_obj.read.assert_called_once_with(1024)
        self.assertEqual(self.port._buff, bytearray(received_data))

    def test_blocking_read_timeout(self):
        """Test blocking read timeout"""
        self.port = ModbusRtuPort(blocking=True)
        self.mock_serial_obj.is_open = True
        
        # Simulate no data received (timeout)
        self.mock_serial_obj.read.return_value = b''
        
        with self.assertRaises(exceptions.SerialReadTimeoutError):
            self.port.read()
    def test_blocking_read_serial_exception(self):
        """Test blocking read with serial exception"""
        self.port = ModbusRtuPort(blocking=True)
        self.mock_serial_obj.is_open = True
        
        self.mock_serial_obj.read.side_effect = self.orig_serial.SerialException("Read failed")
        
        with self.assertRaises(Exception):
            self.port.read()

    # ===== Non-Blocking Write Tests =====
    
    def test_nonblocking_write_successful(self):
        """Test successful non-blocking write"""
        self.port = ModbusRtuPort(blocking=False)
        self.mock_serial_obj.is_open = True
        
        # Prepare buffer
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        
        result = self.port.write()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.mock_serial_obj.reset_input_buffer.assert_called_once()
        self.mock_serial_obj.write.assert_called_once_with(self.port._buff)

    def test_nonblocking_write_serial_exception(self):
        """Test non-blocking write with serial exception"""
        self.port = ModbusRtuPort(blocking=False)
        self.mock_serial_obj.is_open = True
        
        self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
        self.mock_serial_obj.write.side_effect = self.orig_serial.SerialException("Write failed")
        
        with self.assertRaises(exceptions.SerialWriteError):
            self.port.write()

    # ===== Non-Blocking Read Tests =====
    
    def test_nonblocking_read_first_byte_received(self):
        """Test non-blocking read with first byte received"""
        self.port = ModbusRtuPort(blocking=False)
        self.mock_serial_obj.is_open = True
        self.port.setTimeoutInterByte(0)  # No inter-byte timeout
        
        # Simulate receiving first byte
        received_data = b'\x00\x01\x00\x00\x00\x05\x01\x03'
        self.mock_serial_obj.read.return_value = received_data
        
        result = self.port.read()
        
        self.assertEqual(result, StatusCode.Status_Good)
        self.assertEqual(self.port._buff, bytearray(received_data))

    def test_nonblocking_read_timeout_first_byte(self):
        """Test non-blocking read timeout waiting for first byte"""
        with patch('libmodbuspy.serialport.timer') as mock_timer:
            self.port = ModbusRtuPort(blocking=False)
            self.mock_serial_obj.is_open = True
            
            # Simulate no data received
            self.mock_serial_obj.read.return_value = b''
            
            # Mock timer to simulate timeout
            list_timer_results = [0, self.port.timeoutFirstByte() + 100]  # Start, then past timeout
            mock_timer.side_effect = list_timer_results
            
            with self.assertRaises(exceptions.SerialReadTimeoutError):
                self.port.read()

    def test_nonblocking_read_serial_exception(self):
        """Test non-blocking read with serial exception"""
        self.port = ModbusRtuPort(blocking=False)
        self.mock_serial_obj.is_open = True
        
        self.mock_serial_obj.read.side_effect = self.orig_serial.SerialException("Read failed")
        
        with self.assertRaises(exceptions.SerialReadTimeoutError):
            self.port.read()

    # ===== Setting Blocking Mode Tests =====
    
    def test_set_blocking_true(self):
        """Test setting blocking mode to True"""
        self.port = ModbusRtuPort(blocking=False)
        self.assertEqual(self.port._readMethod, self.port._nonBlockingRead)
        
        self.port.setBlocking(True)
        self.assertTrue(self.port.isBlocking())
        self.assertEqual(self.port._readMethod, self.port._blockingRead)
        self.assertEqual(self.port._writeMethod, self.port._blockingWrite)

    def test_set_blocking_false(self):
        """Test setting blocking mode to False"""
        self.port = ModbusRtuPort(blocking=True)
        self.assertEqual(self.port._readMethod, self.port._blockingRead)
        
        self.port.setBlocking(False)
        self.assertFalse(self.port.isBlocking())
        self.assertEqual(self.port._readMethod, self.port._nonBlockingRead)
        self.assertEqual(self.port._writeMethod, self.port._nonBlockingWrite)

    # ===== Parameterized Tests for Blocking Mode =====
    
    def test_write_with_different_blocking_modes(self):
        """Test write behavior with different blocking modes"""
        for blocking in (True, False):
            with self.subTest(blocking=blocking):
                self.port = ModbusRtuPort(blocking=blocking)
                self.mock_serial_obj.is_open = True
                
                self.port._buff = bytearray(b'\x00\x01\x00\x00\x00\x06\x01\x03\x00\x00\x00\x02')
                
                result = self.port.write()
                
                self.assertEqual(result, StatusCode.Status_Good)
                self.mock_serial_obj.write.assert_called_once_with(self.port._buff)
                
                self.port = None
                self.mock_serial_obj.reset_mock()

    def test_read_with_different_blocking_modes(self):
        """Test read behavior with different blocking modes"""
        for blocking in (True, False):
            with self.subTest(blocking=blocking):
                self.port = ModbusRtuPort(blocking=blocking)
                self.mock_serial_obj.is_open = True
                
                received_data = b'\x00\x01\x00\x00\x00\x05\x01\x03'
                self.mock_serial_obj.read.return_value = received_data
                
                result = self.port.read()
                
                # For blocking mode: should return StatusCode.Status_Good
                # For non-blocking mode: may return None (waiting for first byte in state machine)
                if blocking:
                    self.assertIsNotNone(result)
                else:
                    # Non-blocking read may return None when waiting for first byte
                    # This is normal state machine behavior, not an error
                    self.assertIn(result, (None, StatusCode.Status_Good))
                
                self.port = None
                self.mock_serial_obj.reset_mock()


if __name__ == '__main__':
    unittest.main()
