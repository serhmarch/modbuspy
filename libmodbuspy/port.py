"""
port.py - Contains port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

import os
import socket
import select
import serial

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
from enum import IntEnum

from .mbglobal import *
from .statuscode import StatusCode
from .exceptions import ModbusException, getException
from .frame import ModbusFrame, ModbusAscFrame, ModbusRtuFrame, ModbusNetFrame
from . import exceptions

class ModbusPort(ABC):
    """Abstract base class for Modbus port communication.
    
    This class defines the interface for Modbus communication ports,
    supporting TCP, RTU, and ASCII protocols.
    """

    class State(IntEnum):
        STATE_UNKNOWN            = 0
        STATE_WAIT_FOR_OPEN      = 1
        STATE_OPENED             = 2
        STATE_PREPARE_TO_READ    = 3
        STATE_WAIT_FOR_READ      = 4
        STATE_WAIT_FOR_READ_ALL  = 5
        STATE_PREPARE_TO_WRITE   = 6
        STATE_WAIT_FOR_WRITE     = 7
        STATE_WAIT_FOR_WRITE_ALL = 8
        STATE_WAIT_FOR_CLOSE     = 9
        STATE_CLOSED             = 10
        STATE_END                = STATE_CLOSED

    def __init__(self, frame: ModbusFrame, blocking: bool = True):
        """Initialize ModbusPort with default values."""
        self._frame = frame
        self._state = ModbusPort.State.STATE_UNKNOWN
        self._changed = False
        self._modeBlocking = blocking
        self._timeout = 0
    
    # Abstract methods that must be implemented by subclasses
    
    @abstractmethod
    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type.
        
        Returns:
            The protocol type (TCP, RTU, or ASC).
        """
        pass
    
    @abstractmethod
    def handle(self) -> int:
        """Returns the native handle value that depend on OS used.
        
        For TCP it is socket handle, for serial port - file handle.
        
        Returns:
            Native handle value as integer.
        """
        pass
    
    def setNextRequestRepeated(self, v: bool) -> None:
        """For the TCP version of the Modbus protocol.
        
        The identifier of each subsequent parcel is automatically increased by 1.
        If you set setNextRequestRepeated(True) then the next ID will not be 
        increased by 1 but for only one next parcel.
        
        Args:
            v: True to repeat next request ID, False otherwise.
        """
        pass
    
    # Concrete methods with default implementations
    
    def isChanged(self) -> bool:
        """Returns True if the port settings have been changed.
        
        Returns:
            True if port needs to be reopened/reestablished communication, False otherwise.
        """
        return self._changed
    
    def isServerMode(self) -> bool:
        """Returns True if the port works in server mode, False otherwise.
        
        Returns:
            True for server mode, False for client mode.
        """
        return self._frame._modeServer
    
    def setServerMode(self, mode: bool) -> None:
        """Sets server mode if True, False for client mode.
        
        Args:
            mode: True for server mode, False for client mode.
        """
        frame = self._frame
        if frame._modeServer != mode:
            frame._modeServer = mode
            self._changed = True
    
    def isBlocking(self) -> bool:
        """Returns True if the port works in synch (blocking) mode, False otherwise.
        
        Returns:
            True for blocking mode, False for non-blocking mode.
        """
        return self._modeBlocking
    
    def isNonBlocking(self) -> bool:
        """Returns True if the port works in asynch (nonblocking) mode, False otherwise.
        
        Returns:
            True for non-blocking mode, False for blocking mode.
        """
        return not self._modeBlocking
    
    def setBlocking(self, blocking: bool):
        """Sets blocking mode if True, False for non-blocking mode.
        
        Args:
            blocking: True for blocking mode, False for non-blocking mode.
        """
        if self._modeBlocking != blocking:
            self._modeBlocking = blocking
            self._changed = True
    
    def unit(self) -> int:
        """Returns the unit identifier of the last request.
        
        Returns:
            The unit identifier.
        """
        return self._frame._unit
    
    def function(self) -> int:
        """Returns the function code of the last request.
        
        Returns:
            The function code.
        """
        return self._frame._func
    

    def timeout(self) -> int:
        """Returns the setting for the connection timeout of the remote device.
        
        Returns:
            Timeout value in milliseconds.
        """
        return self._timeout
    
    def setTimeout(self, timeout: int) -> None:
        """Sets the setting for the connection timeout of the remote device.
        
        Args:
            timeout: Timeout value in milliseconds.
        """
        if self._timeout != timeout:
            self._timeout = timeout
            self._changed = True
    
    @property
    def Timeout(self) -> int:
        """Property. Get the timeout value in milliseconds."""
        return self.timeout()
    
    @Timeout.setter
    def Timeout(self, timeout: int) -> None:
        """Property. Set the timeout value in milliseconds."""
        self.setTimeout(timeout)
        
    def settings(self) -> dict:
        """Returns the current port settings as a dictionary.
        
        Returns:
            Dictionary containing current port settings.
        """
        raise NotImplementedError("Subclasses must implement settings() method.") 
    
    def setSettings(self, settings: dict):
        """Sets the current port settings from a dictionary.
        
        Args:
            settings: Dictionary containing port settings.
        """
        raise NotImplementedError("Subclasses must implement settings() method.") 
    
    # Error handling methods
    
    def lastErrorStatus(self) -> StatusCode:
        """Returns the status of the last error of the performed operation.
        
        Returns:
            StatusCode of the last error.
        """
        return self._frame._errorStatus
    
    def lastErrorText(self) -> str:
        """Returns the text description of the last error of the performed operation.
        
        Returns:
            Text description of the last error.
        """
        return self._frame._errorText
    
    # Abstract buffer and I/O methods
    
    @abstractmethod
    def isOpen(self) -> bool:
        """Returns True if the port is open/communication with the remote device is established.
        
        Returns:
            True if port is open, False otherwise.
        """
        pass
    
    @abstractmethod
    def open(self) -> StatusCode:
        """Opens port (create connection) for further operations.
        
        Returns:
            `StatusCode` indicating the result of the operation.
        """
        pass
    
    @abstractmethod
    def close(self) -> StatusCode:
        """Closes the port (breaks the connection).
        
        Returns:
            `True` if the operation was successful, `None` if operation is not yet completed,
            or `ModbusException` is raised if error occurs.
        """
        pass
    
    @abstractmethod
    def write(self) -> StatusCode:
        """Implements the algorithm for writing to the port.
        
        Returns:
            Status code of the operation.
        """
        pass
    
    @abstractmethod
    def read(self) -> StatusCode:
        """Implements the algorithm for reading from the port.
        
        Returns:
            Status code of the operation.
        """
        pass
    
    def writeBuffer(self, unit: int, func: int, data: bytes, szInBuff: int) -> StatusCode:
        """The function directly generates a packet and places it in the buffer for further sending.
        
        Args:
            unit: Modbus unit/slave address.
            func: Modbus function code.
            buff: Buffer containing the data to write.
            szInBuff: Size of input buffer.
            
        Returns:
            Status code of the operation.
        """
        return self._frame.writeBuffer(unit, func, data, szInBuff)
    
    def readBuffer(self) -> Tuple[int, int, bytes]:
        """The function parses the packet that the read() function puts into the buffer.
        
        Checks it for correctness, extracts its parameters.
        
        Returns:
            Tuple of (unit, func, buff) where:
            - unit: Modbus unit address
            - func: Modbus function code
            - buff: Buffer containing the extracted data
        """
        return self._frame.readBuffer()
    
    # Buffer access methods
    
    def readBufferData(self) -> bytes:
        """Returns data of read buffer.
        
        Returns:
            Read buffer data or None if empty.
        """
        return self._frame._buff
    
    def readBufferSize(self) -> int:
        """Returns size of data of read buffer.
        
        Returns:
            Size of read buffer data.`
        """
        return len(self._frame._buff)
    
    def writeBufferData(self) -> bytes:
        """Returns data of write buffer.
        
        Returns:
            Write buffer data or None if empty.
        """
        return self._frame._buff
    
    def writeBufferSize(self) -> int:
        """Returns size of data of write buffer.
        
        Returns:
            Size of write buffer data.
        """
        return len(self._frame._buff)
    
    # Protected method for error handling
    
    def _setError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._frame._setError(exc, text)
        
    def _raiseError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed and raises the exception.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._frame._raiseError(exc, text)


class ModbusSerialPort(ModbusPort):
    """
    Base class for Modbus serial port implementations.
    
    This abstract class defines the interface for serial port communication
    including configuration for port settings like baud rate, data bits, etc.
    """

    class Strings:
        """String keys for serial port settings."""
        portName         = "portName"         # String key of setting 'Serial port name'
        baudRate         = "baudRate"         # String key of setting 'Serial port baud rate'
        dataBits         = "dataBits"         # String key of setting 'Serial port data bits'
        parity           = "parity"           # String key of setting 'Serial port parity'
        stopBits         = "stopBits"         # String key of setting 'Serial port stop bits'
        flowControl      = "flowControl"      # String key of setting 'Serial port flow control'
        timeoutFirstByte = "timeoutFirstByte" # String key of setting 'Serial port timeout waiting first byte of packet'
        timeoutInterByte = "timeoutInterByte" # String key of setting 'Serial port timeout waiting next byte of packet'
        timeout          = "timeout"          # String key of setting 'Serial port timeout waiting first byte of packet'

    class Defaults:
        """Default serial port settings."""
        portName         = "COM1" if os.name == 'nt' else "/dev/ttyS0"  # Default value for the serial port name
        baudRate         = 9600                                         # Default value for the serial port's baud rate
        dataBits         = 8                                            # Default value for the serial port's data bits
        parity           = Parity.NoParity                              # Default value for the serial port's parity
        stopBits         = StopBits.OneStop                             # Default value for the serial port's stop bits
        flowControl      = FlowControl.NoFlowControl                    # Default value for the serial port's flow control
        timeoutFirstByte = 3000                                         # Default value for the serial port's timeout waiting first byte of packet
        timeoutInterByte = 50                                           # Default value for the serial port's timeout waiting next byte of packet

    @staticmethod
    def toSerialParity(parity:Parity) -> str:
        """Convert Modbus Parity enum to pySerial parity value."""
        if parity == Parity.NoParity:
            return serial.PARITY_NONE
        elif parity == Parity.OddParity:
            return serial.PARITY_ODD
        elif parity == Parity.EvenParity:
            return serial.PARITY_EVEN
        elif parity == Parity.MarkParity:
            return serial.PARITY_MARK
        elif parity == Parity.SpaceParity:
            return serial.PARITY_SPACE
        else:
            return serial.PARITY_NONE

    @staticmethod
    def toSerialStopBits(stopBits:StopBits) -> float:
        """Convert Modbus StopBits enum to pySerial stop bits value."""
        if stopBits == StopBits.OneStop:
            return serial.STOPBITS_ONE
        elif stopBits == StopBits.OneAndHalfStop:
            return serial.STOPBITS_ONE_POINT_FIVE
        elif stopBits == StopBits.TwoStop:
            return serial.STOPBITS_TWO
        else:
            return serial.STOPBITS_ONE
        
    def __init__(self, frame: ModbusFrame, blocking: bool = True):
        super().__init__(frame, blocking)
        d = ModbusSerialPort.Defaults
        # Serial port configuration
        self._portName         = d.portName        
        self._baudRate         = d.baudRate        
        self._dataBits         = d.dataBits        
        self._parity           = d.parity          
        self._stopBits         = d.stopBits        
        self._flowControl      = d.flowControl     
        self._timeout          = d.timeoutFirstByte
        self._timeoutInterByte = d.timeoutInterByte
        # Serial object
        self._serial = serial.Serial()
        # Other internal variables
        self._timestamp = 0
        # Blocking mode
        self.setBlocking(blocking)

    def handle(self):
        return self._serial.fileno()
    
    def setBlocking(self, blocking):
        super().setBlocking(blocking)
        if blocking:
            self._readMethod  = self._blockingRead
            self._writeMethod = self._blockingWrite
        else:
            self._readMethod  = self._nonBlockingRead
            self._writeMethod = self._nonBlockingWrite

    
    def portName(self) -> str:
        """Get the serial port name (e.g., 'COM1', '/dev/ttyUSB0')."""
        return self._portName

    def setPortName(self, value: str):
        """Set the serial port name."""
        if self._portName != value:
            self._portName = value
            self._changed = True

    @property
    def PortName(self) -> str:
        """Property. Get the serial port name (e.g., 'COM1', '/dev/ttyUSB0')."""
        return self.portName()

    @PortName.setter
    def PortName(self, value: str) -> None:
        """Property. Set the serial port name."""
        return self.setPortName(value)

    def baudRate(self) -> int:
        """Get the baud rate."""
        return self._baudRate

    def setBaudRate(self, value: int):
        """Set the baud rate."""
        if self._baudRate != value:
            self._baudRate = value
            self._changed = True

    @property
    def BaudRate(self) -> int:
        """Property. Get the baud rate."""
        return self.baudRate()

    @BaudRate.setter
    def BaudRate(self, value: int) -> None:
        """Property. Set the baud rate."""
        return self.setBaudRate(value)

    def dataBits(self) -> int:
        """Get the number of data bits."""
        return self._dataBits

    def setDataBits(self, value: int):
        """Set the number of data bits."""
        if self._dataBits != value:
            self._dataBits = value
            self._changed = True

    @property
    def DataBits(self) -> int:
        """Property. Get the number of data bits."""
        return self.dataBits()

    @DataBits.setter
    def DataBits(self, value: int) -> None:
        """Property. Set the number of data bits."""
        return self.setDataBits(value)

    def parity(self) -> Parity:
        """Get the parity setting."""
        return self._parity

    def setParity(self, value: Parity):
        """Set the parity setting."""
        if self._parity != value:
            self._parity = value
            self._changed = True

    @property
    def Parity(self) -> Parity:
        """Property. Get the parity setting."""
        return self.parity()

    @Parity.setter
    def Parity(self, value: Parity) -> None:
        """Property. Set the parity setting."""
        return self.setParity(value)

    def stopBits(self) -> StopBits:
        """Get the number of stop bits."""
        return self._stopBits

    def setStopBits(self, value: StopBits):
        """Set the number of stop bits."""
        if self._stopBits != value:
            self._stopBits = value
            self._changed = True

    @property
    def StopBits(self) -> StopBits:
        """Property. Get the number of stop bits."""
        return self.stopBits()

    @StopBits.setter
    def StopBits(self, value: StopBits) -> None:
        """Property. Set the number of stop bits."""
        return self.setStopBits(value)

    def flowControl(self) -> FlowControl:
        """Get the flow control setting."""
        return self._flowControl

    def setFlowControl(self, value: FlowControl):
        """Set the flow control setting."""
        if self._flowControl != value:
            self._flowControl = value
            self._changed = True

    @property
    def FlowControl(self) -> FlowControl:
        """Property. Get the flow control setting."""
        return self.flowControl()

    @FlowControl.setter
    def FlowControl(self, value: FlowControl) -> None:
        """Property. Set the flow control setting."""
        return self.setFlowControl(value)

    def timeoutFirstByte(self) -> int:
        """Get the timeout for the first byte."""
        return self.timeout()

    def setTimeoutFirstByte(self, value: int):
        """Set the timeout for the first byte."""
        self.setTimeout(value)

    @property
    def TimeoutFirstByte(self) -> int:
        """Property. Get the timeout for the first byte."""
        return self.timeoutFirstByte()

    @TimeoutFirstByte.setter
    def TimeoutFirstByte(self, value: int) -> None:
        """Property. Set the timeout for the first byte."""
        return self.setTimeoutFirstByte(value)

    def timeoutInterByte(self) -> int:
        """Get the inter-byte timeout setting."""
        return self._timeoutInterByte

    def setTimeoutInterByte(self, value: int):
        """Set the timeout for the inter-byte delay."""
        if self._timeoutInterByte != value:
            self._timeoutInterByte = value
            self._changed = True

    @property
    def TimeoutInterByte(self) -> int:
        """Property. Get the inter-byte timeout setting."""
        return self.timeoutInterByte()

    @TimeoutInterByte.setter
    def TimeoutInterByte(self, value: int) -> None:
        """Property. Set the timeout for the inter-byte delay."""
        return self.setTimeoutInterByte(value)

    def settings(self) -> dict:
        s = ModbusSerialPort.Strings
        return {
            s.portName         : self._portName         ,
            s.baudRate         : self._baudRate         ,
            s.dataBits         : self._dataBits         ,
            s.parity           : self._parity           ,
            s.stopBits         : self._stopBits         ,
            s.flowControl      : self._flowControl      ,
           #s.timeoutFirstByte : self._timeoutFirstByte ,
            s.timeoutInterByte : self._timeoutInterByte ,
            s.timeout          : self._timeout
        }

    def setSettings(self, settings: dict):
        s = ModbusSerialPort.Strings
        v = settings.get(s.portName, None)
        if v is not None:
            self.setPortName(v)
        v = settings.get(s.baudRate, None)
        if v is not None:
            self.setBaudRate(v)
        v = settings.get(s.dataBits, None)
        if v is not None:
            self.setDataBits(v)
        v = settings.get(s.parity, None)
        if v is not None:
            self.setParity(v)
        v = settings.get(s.stopBits, None)
        if v is not None:
            self.setStopBits(v)
        v = settings.get(s.flowControl, None)
        if v is not None:
            self.setFlowControl(v)
        v = settings.get(s.timeoutFirstByte, None)
        if v is not None:
            self.setTimeoutFirstByte(v)
        v = settings.get(s.timeoutInterByte, None)
        if v is not None:
            self.setTimeoutInterByte(v)
        v = settings.get(s.timeout, None)
        if v is not None:
            self.setTimeout(v)

    def isOpen(self) -> bool:
        """Check if the serial port is open."""
        return self._serial.is_open

    def open(self) -> StatusCode:
        fRepeatAgain = True        
        while fRepeatAgain:
            fRepeatAgain = False            
            if self._state in (ModbusPort.State.STATE_UNKNOWN, 
                               ModbusPort.State.STATE_CLOSED,
                               ModbusPort.State.STATE_WAIT_FOR_OPEN):
                if self.isOpen():
                    if self.isChanged():
                        self.close()
                    else:
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good                
                # Clear changed flag
                self._changed = False
                
                # Configure serial port settings
                self._serial.port     = self._portName
                self._serial.baudrate = self._baudRate
                self._serial.bytesize = self._dataBits
                self._serial.parity   = ModbusSerialPort.toSerialParity(self._parity)
                self._serial.stopbits = ModbusSerialPort.toSerialStopBits(self._stopBits)
                if self._flowControl == FlowControl.NoFlowControl:
                    self._serial.xonxoff = False
                    self._serial.rtscts  = False
                    self._serial.dsrdtr  = False
                elif self._flowControl == FlowControl.HardwareControl:
                    self._serial.xonxoff = False
                    self._serial.rtscts  = True
                    self._serial.dsrdtr  = True
                elif self._flowControl == FlowControl.SoftwareControl:
                    self._serial.xonxoff = True
                    self._serial.rtscts  = False
                    self._serial.dsrdtr  = False
                if self.isBlocking():
                    self._serial.timeout            = self._timeout          / 1000.0  # Convert ms to seconds
                    self._serial.inter_byte_timeout = self._timeoutInterByte / 1000.0  # Convert ms to seconds
                else:
                    self._serial.timeout            = 0.0
                    self._serial.inter_byte_timeout = 0.0
                self._serial.write_timeout = 0.0  # Blocking write
                # try to open serial port
                try:
                    self._serial.open()                        
                except serial.SerialException as e:
                    self._raiseError(exceptions.SerialOpenError, 
                                    f"Failed to open '{self._portName}' serial port. Error: {str(e)}")
                return StatusCode.Status_Good
            else:  # Default case
                if self.isOpen() and not self.isChanged():
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                else:
                    self._state = ModbusPort.State.STATE_CLOSED
                    fRepeatAgain = True
                    continue
        return None
    
    def close(self) -> StatusCode:
        self._serial.close()
        self._state = ModbusPort.State.STATE_CLOSED
        return StatusCode.Status_Good
    
    def write(self) -> StatusCode:
        return self._writeMethod()
    
    def read(self) -> StatusCode:
        return self._readMethod()

    def _blockingWrite(self) -> StatusCode:    
        self._state = ModbusPort.State.STATE_OPENED
        try:
            self._serial.reset_input_buffer()
            self._serial.write(self._buff)
        except serial.SerialException as e:
            self._raiseError(StatusCode.Status_BadSerialWrite, f"Error while writing '{self._portName}' serial port. Error: {str(e)}")
        return StatusCode.Status_Good

    def _blockingRead(self) -> StatusCode:    
        self._state = ModbusPort.State.STATE_OPENED
        self._buff.clear()
        try:
            buff = self._serial.read(1024) # Read up to 1K bytes
            if len(buff) == 0:
                self._state = ModbusPort.State.STATE_OPENED
                self._raiseError(exceptions.SerialReadTimeoutError, f"Error while reading '{self._portName}' serial port. Timeout")
            self._buff.extend(buff)
        except serial.SerialException as e:
            self._raiseError(StatusCode.Status_BadSerialRead, f"Error while reading '{self._portName}' serial port. Error: {str(e)}")
        return StatusCode.Status_Good

    def _nonBlockingWrite(self) -> StatusCode:
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state in (ModbusPort.State.STATE_OPENED,
                               ModbusPort.State.STATE_PREPARE_TO_WRITE):
                self._timestampRefresh()
                self._state = ModbusPort.State.STATE_WAIT_FOR_WRITE
                fRepeatAgain = True
                continue
            elif self._state in (ModbusPort.State.STATE_WAIT_FOR_WRITE,
                                 ModbusPort.State.STATE_WAIT_FOR_WRITE_ALL):
                # Note: clean read buffer from garbage before write
                try:
                    self._serial.reset_input_buffer()
                    self._serial.write(self._buff)
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                except serial.SerialException as e:
                    self._raiseError(exceptions.SerialWriteError, f"Error while writing '{self._portName}' serial port. Error: {str(e)}")
            else:
                if self.isOpen():
                    self._state = ModbusPort.State.STATE_OPENED
                    fRepeatAgain = True
                else:
                    self._raiseError(exceptions.SerialWriteError, "Internal error")
        return None

    def  _nonBlockingRead(self) -> StatusCode:
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state in (ModbusPort.State.STATE_OPENED,
                               ModbusPort.State.STATE_PREPARE_TO_READ):
                self._timestampRefresh()
                self._buff.clear()
                self._state = ModbusPort.State.STATE_WAIT_FOR_READ
                fRepeatAgain = True
                continue
            elif self._state == ModbusPort.State.STATE_WAIT_FOR_READ:
                # read first byte state
                try:
                    buff = self._serial.read(1024) # Read up to 1K bytes
                    c = len(buff)
                    if c > 0:
                        self._buff.extend(buff)
                        if self._timeoutInterByte == 0:
                            self._state = ModbusPort.State.STATE_OPENED
                            return StatusCode.Status_Good
                    elif timer() - self._timestamp >= self._timeout:  # waiting timeout read first byte elapsed
                        self._state = ModbusPort.State.STATE_OPENED
                        self._raiseError(exceptions.SerialReadTimeoutError, f"Error while reading '{self._portName}' serial port. Timeout")
                    else:
                        return None
                except serial.SerialException as e:
                    self._state = ModbusPort.State.STATE_OPENED
                    self._raiseError(exceptions.SerialReadTimeoutError, f"Error while reading '{self._portName}' serial port. Error: {str(e)}")
                self._timestampRefresh()
                self._state = ModbusPort.State.STATE_WAIT_FOR_READ_ALL
                fRepeatAgain = True
                continue
            elif self._state == ModbusPort.State.STATE_WAIT_FOR_READ_ALL:
                # next bytes state
                try:
                    buff = self._serial.read(1024) # Read up to 1K bytes
                    c = len(buff)
                    if c > 0:
                        self._buff.extend(buff)
                        self._timestampRefresh()
                    elif timer() - self._timestamp >= self._timeoutInterByte:  # waiting timeout read next bytes
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                    else:
                        return None
                except serial.SerialException as e:
                    self._state = ModbusPort.State.STATE_OPENED
                    self._raiseError(exceptions.SerialReadTimeoutError, f"Error while reading '{self._portName}' serial port. Error: {str(e)}")
                return None
            else:
                if self.isOpen():
                    self._state = ModbusPort.State.STATE_OPENED
                    fRepeatAgain = True
                    continue
                else:
                    self._raiseError(exceptions.SerialReadTimeoutError, "Internal error")
                break
        return None
    
    def _timestampRefresh(self):
        """Refreshes the internal timestamp to the current time."""
        self._timestamp = timer()  # Timestamp in milliseconds


class ModbusAscPort(ModbusSerialPort):
    """
    Implements ASCII version of the Modbus communication protocol.
    
    ModbusAscPort derives from ModbusSerialPort and implements writeBuffer and readBuffer
    for ASCII version of Modbus communication protocol.
    
    ASCII format:
    - Starts with ':' character
    - Data is encoded as hexadecimal ASCII characters
    - Ends with CR LF (\r\n)
    - Uses LRC (Longitudinal Redundancy Check) for error detection
    """
    
    def __init__(self, blocking: bool = True):
        """Initialize ModbusPort with default values."""
        super().__init__(ModbusAscFrame(), blocking)

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. For ModbusAscPort returns ASCII."""
        return ProtocolType.ASC


class ModbusRtuPort(ModbusSerialPort):
    """
    Implements RTU version of the Modbus communication protocol.
    
    ModbusRtuPort derives from ModbusSerialPort and implements writeBuffer and readBuffer
    for RTU version of Modbus communication protocol.
    
    RTU format:
    - Binary data transmission
    - Uses CRC16 for error detection
    - No start/end delimiters (uses timing gaps)
    - More compact than ASCII format
    """
    
    def __init__(self, blocking: bool = True):
        """Initialize ModbusPort with default values."""
        super().__init__(ModbusRtuFrame(), blocking)

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. For ModbusRtuPort returns RTU."""
        return ProtocolType.RTU


class ModbusNetPort(ModbusPort):
    """
    Base class for Modbus network port implementations.
    
    This abstract class defines the interface for network port communication
    including configuration for port settings like IP address, port number, etc.
    """

    class Strings:
        """String keys for network port settings."""
        host    = "host"    # String key of setting 'Network port IP/DNS address'
        port    = "port"    # String key of setting 'Network port number'
        timeout = "timeout" # String key of setting 'Network port timeout'

    class Defaults:
        """Default network port settings."""
        host    = "localhost"                   # Default value for the network port IP/DNS address
        port    = Constants.STANDARD_TCP_PORT   # Default value for the network port number
        timeout = 3000                          # Default value for the network port timeout in milliseconds

    def __init__(self, frame: ModbusFrame, blocking: bool = True, sock = None):
        super().__init__(frame, blocking)
        d = ModbusNetPort.Defaults
        # Network port configuration
        self._host    = d.host        
        self._port    = d.port        
        self._timeout = d.timeout        
        self._sock = sock
        if self.isOpen():
            self._state = ModbusPort.State.STATE_OPENED

    def __del__(self):
        self.close()

    def host(self) -> str:
        """Returns the settings for the IP address or DNS name of the remote device.
        
        Returns:
            The host IP address or DNS name.
        """
        return self._host

    def setHost(self, host: str) -> None:
        """Sets the settings for the IP address or DNS name of the remote device.
        
        Args:
            host: The IP address or DNS name of the remote device.
        """
        if self._host != host:
            self._host = host
            self._changed = True

    @property
    def Host(self) -> str:
        """Property. Get the host IP address or DNS name."""
        return self.host()
    
    @Host.setter
    def Host(self, host: str) -> None:
        """Property. Set the host IP address or DNS name."""
        return self.setHost(host)
    
    def port(self) -> int:
        """Returns the setting for the network port number of the remote device.
        
        Returns:
            The network port number.
        """
        return self._port

    def setPort(self, port: int) -> None:
        """Sets the settings for the network port number of the remote device.
        
        Args:
            port: The network port number of the remote device.
        """
        if self._port != port:
            self._port = port
            self._changed = True

    @property
    def Port(self) -> int:
        """Property. Get the network port number."""
        return self.port()
    
    @Port.setter
    def Port(self, port: int) -> None:
        """Property. Set the network port number."""
        return self.setPort(port)   
    
    def settings(self) -> dict:
        s = ModbusNetPort.Strings
        return {
            s.host   : self._host   ,
            s.port   : self._port   ,
            s.timeout: self._timeout
        }

    def setSettings(self, settings: dict):
        s = ModbusNetPort.Strings
        v = settings.get(s.host, None)
        if v is not None:
            self.setHost(v)
        v = settings.get(s.port, None)
        if v is not None:
            self.setPort(v)
        v = settings.get(s.timeout, None)
        if v is not None:
            self.setTimeout(v)

    def socket(self):
        """Returns the underlying socket object.
        
        Returns:
            The socket object.
        """
        return self._sock

    def handle(self) -> int:
        if self._sock is not None:
            return self._sock.fileno()
        return -1
    
    def close(self) -> StatusCode:
        if self._sock is not None and self._sock.fileno() >= 0:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._state = ModbusPort.State.STATE_CLOSED
        return StatusCode.Status_Good

    def isOpen(self) -> bool:
        sock = self._sock
        if sock is None or sock.fileno() < 0:
            return False
        readable, writeable, _ = select.select([sock], [sock], [], 0.0)
        return (sock in readable) or (sock in writeable)
        

class ModbusTcpPortBase(ModbusNetPort):
    """Base class for Modbus TCP port implementation."""

    def open(self) -> StatusCode:
        fRepeatAgain = True        
        while fRepeatAgain:
            fRepeatAgain = False
            
            if self._state in (ModbusPort.State.STATE_UNKNOWN, 
                               ModbusPort.State.STATE_CLOSED):
                if self.isOpen():
                    if self.isChanged():
                        self.close()
                    else:
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good                
                # Clear changed flag
                self._changed = False
                
                # Create socket if needed
                try:
                    self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                        
                except Exception as e:
                    self._raiseError(exceptions.TcpCreateError, f"TCP. Error while creating socket for '{self._host}:{self._port}'. Error: {str(e)}")
                    
                # Set timeout for blocking mode
                if self.isBlocking():
                    self._sock.settimeout(self.timeout() / 1000.0)
                else:
                    self._sock.setblocking(False)
    
                self._timestamp = timer()
                try:
                    # socket.connect_ex is non-blocking and in most cases do not raise exceptions
                    result = self._sock.connect_ex((self._host, self._port))
                    if result == 0:
                        # Connection successful
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                    if result != socket.EWOULDBLOCK:
                        raise socket.error(f"code={result}")
                except Exception as e:
                    self.close()
                    self._state = ModbusPort.State.STATE_CLOSED
                    self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Error: {str(e)}")
                # Fall through to ModbusPort.State.STATE_WAIT_FOR_OPEN
                self._state = ModbusPort.State.STATE_WAIT_FOR_OPEN
                
            if self._state == ModbusPort.State.STATE_WAIT_FOR_OPEN:
                try:
                    timeout_sec = self.timeout() / 1000.0 if self.isBlocking() else 0.0
                    _, ready_to_write, error_socks = select.select([], [self._sock], [self._sock], timeout_sec)                    
                    if error_socks:
                        # Connection failed
                        self.close()
                        self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Connection failed")                    
                    elif ready_to_write:
                        # Connection successful
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good                        
                    else:
                        # Timeout
                        if self.isNonBlocking() and (timer() - self._timestamp < self.timeout()):
                            return None
                        self.close()
                        self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Timeout")                        
                except Exception as e:
                    self.close()
                    if isinstance(e, ModbusException):
                        raise e
                    self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Error: {str(e)}")
            else:  # Default case
                if self.isOpen() and not self.isChanged():
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                else:
                    self._state = ModbusPort.State.STATE_CLOSED
                    fRepeatAgain = True
                    continue
        return None

    def write(self) -> StatusCode:
        if self._state in (ModbusPort.State.STATE_OPENED,
                           ModbusPort.State.STATE_PREPARE_TO_WRITE,
                           ModbusPort.State.STATE_WAIT_FOR_WRITE,
                           ModbusPort.State.STATE_WAIT_FOR_WRITE_ALL):
            try:
                c = self._sock.send(self._buff)
                if c >= 0:
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                self.close()
                self._raiseError(exceptions.TcpWriteError, f"TCP. Error while writing to '{self._host}:{self._port}'. Connection lost.")
            except socket.error as e:
                self._raiseError(exceptions.TcpWriteError, f"TCP. Error while writing to '{self._host}:{self._port}'. {str(e)}")
        return None
    
    def read(self) -> StatusCode:
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state in (ModbusPort.State.STATE_OPENED,
                               ModbusPort.State.STATE_PREPARE_TO_READ):
                self._timestamp = timer()
                self._state = ModbusPort.State.STATE_WAIT_FOR_READ
                fRepeatAgain = True
                continue
            elif self._state in (ModbusPort.State.STATE_WAIT_FOR_READ,
                                 ModbusPort.State.STATE_WAIT_FOR_READ_ALL):
                try:
                    # Attempt to receive data from socket
                    data = self._sock.recv(1024)  # Read up to 1KB buffer size
                    c = len(data)
                    if c > 0:
                        # Data received successfully
                        self._buff = bytearray(data)
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                        
                    else:
                        # Connection closed by remote end (recv returned 0 bytes)
                        self.close()
                        # Note: When connection is remotely closed is not error for server side
                        if self._modeServer:
                            return StatusCode.Status_Uncertain
                        else:
                            self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Remote connection closed")
                            
                except socket.timeout:
                    # Socket timeout occurred
                    if self.isNonBlocking() and (timer() - self._timestamp < self.timeout()):
                        return None
                    self.close()
                    self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Timeout")
                    
                except socket.error as e:
                    # Socket error occurred
                    if e.errno == socket.EWOULDBLOCK:
                        # Non-blocking socket would block - check timeout
                        if self.isNonBlocking():
                            if (timer() - self._timestamp >= self.timeout()):
                                self.close()
                                self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Timeout")
                            # Return None to continue processing later
                            return None
                    # Other socket error
                    self.close()
                    self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Error: {str(e)}")
                        
                except Exception as e:
                    # Unexpected error
                    self.close()
                    if isinstance(e, ModbusException):
                        raise e
                    self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Error: {str(e)}")
                    
            return None
                    
class ModbusTcpPort(ModbusTcpPortBase):
    """
    Implements TCP version of the Modbus communication protocol.
    
    ModbusTcpPort derives from ModbusTcpPortBase and implements writeBuffer and readBuffer
    for TCP version of Modbus communication protocol.
    
    TCP format:
    - Uses standard TCP/IP for communication
    - Includes a transaction identifier for request/response matching
    - Uses a protocol identifier (always 0 for Modbus)
    - Includes length field for the entire message
    - More suitable for networked environments
    """
    
    def __init__(self, blocking: bool = True, sock = None):
        """Initialize ModbusPort with default values."""
        super().__init__(ModbusNetFrame(), blocking, sock)

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. For ModbusTcpPort returns TCP."""
        return ProtocolType.TCP
    
    def setNextRequestRepeated(self, v: bool) -> None:
        """Repeat next request parameters (for Modbus TCP transaction Id).
        
        Args:
            v: True to repeat next request ID, False otherwise.
        """
        self._frame._autoIncrement = v

    def autoIncrement(self) -> bool:
        """Returns True if the identifier of each subsequent parcel is automatically incremented by 1.
        
        Returns:
            True if auto-increment is enabled, False otherwise.
        """
        return self._frame._autoIncrement
    
    def transactionId(self) -> int:
        """Returns the current transaction identifier.
        
        Returns:
            The current transaction identifier.
        """
        return self._frame._transaction


class ModbusUdpPortBase(ModbusNetPort):
    """Base class for Modbus UDP port implementation."""

    def __init__(self, frame: ModbusFrame, blocking: bool = True, sock = None):
        super().__init__(frame, blocking, sock)
        self._addr = None  # Remote address for UDP communication

    def open(self) -> StatusCode:
        fRepeatAgain = True        
        while fRepeatAgain:
            fRepeatAgain = False
            
            if self._state in (ModbusPort.State.STATE_UNKNOWN, 
                               ModbusPort.State.STATE_CLOSED,
                               ModbusPort.State.STATE_WAIT_FOR_OPEN):
                if self.isOpen():
                    if self.isChanged():
                        self.close()
                    else:
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good                
                # Clear changed flag
                self._changed = False
                
                # Create socket if needed
                try:
                    self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)                        
                except Exception as e:
                    self._raiseError(exceptions.UdpCreateError, f"UDP. Error while creating socket for '{self._host}:{self._port}'. Error: {str(e)}")
                    
                # Set timeout for blocking mode
                if self.isBlocking():
                    self._sock.setblocking(True)
                    self._sock.settimeout(self.timeout() / 1000.0)
                else:
                    self._sock.setblocking(False)

                if self.isServerMode():
                    # Bind to any available interface on the given port
                    try:
                        self._sock.bind((self._host, self._port))
                    except socket.error as e:
                        self.close()
                        self._state = ModbusPort.State.STATE_CLOSED
                        self._raiseError(exceptions.UdpBindError, f"UDP. Bind error for port '{self._port}'. Error: {str(e)}")
                else:
                    # Resolve host address and connect socket to set default remote endpoint
                    try:
                        addr_info = socket.getaddrinfo(self._host, self._port, socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                        if not addr_info:
                            self._raiseError(exceptions.UdpCreateError, f"UDP. Error while getting address info for '{self._host}:{self._port}'")
                        self._addr = addr_info[0][4]  # Get the first resolved address
                    except socket.gaierror as e:
                        self._raiseError(exceptions.UdpCreateError, f"UDP. Error while getting address info for '{self._host}:{self._port}'. Error: {str(e)}")
                self._state = ModbusPort.State.STATE_OPENED
                return StatusCode.Status_Good               
            else:  # Default case
                if self.isOpen() and not self.isChanged():
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                else:
                    self._state = ModbusPort.State.STATE_CLOSED
                    fRepeatAgain = True
                    continue
        return None

    def write(self) -> StatusCode:
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False

            if self._state in  (ModbusPort.State.STATE_OPENED,
                                ModbusPort.State.STATE_PREPARE_TO_WRITE,
                                ModbusPort.State.STATE_WAIT_FOR_WRITE,
                                ModbusPort.State.STATE_WAIT_FOR_WRITE_ALL):
                try:
                    c = self._sock.sendto(self._buff, self._addr)
                    if c >= 0:
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                    self.close()
                    self._raiseError(exceptions.UdpWriteError, f"UDP. Error while writing to '{self._host}:{self._port}'. 'socket.sendto' returned negative value.")
                except socket.error as e:
                    self._raiseError(exceptions.UdpWriteError, f"UDP. Error while writing to '{self._host}:{self._port}'. {str(e)}")
            else:
                if self.isOpen():
                    self._state = ModbusPort.State.STATE_OPENED
                    fRepeatAgain = True
                    continue
                else:
                    self._raiseError(exceptions.UdpWriteError, "Internal state error")
        return None
    
    def read(self) -> StatusCode:
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state in (ModbusPort.State.STATE_OPENED,
                               ModbusPort.State.STATE_PREPARE_TO_READ):
                self._timestamp = timer()
                self._state = ModbusPort.State.STATE_WAIT_FOR_READ
                fRepeatAgain = True
                continue
            elif self._state in (ModbusPort.State.STATE_WAIT_FOR_READ,
                                 ModbusPort.State.STATE_WAIT_FOR_READ_ALL):
                try:
                    # Attempt to receive data from socket
                    data, _ = self._sock.recvfrom(1024)  # Read up to 1KB buffer size
                    c = len(data)
                    if c > 0:
                        # Data received successfully
                        self._buff = bytearray(data)
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                        
                    else:
                        # Connection closed by remote end (recv returned 0 bytes)
                        self.close()
                        # Note: When connection is remotely closed is not error for server side
                        if self._modeServer:
                            return StatusCode.Status_Uncertain
                        else:
                            self._raiseError(exceptions.UdpReadError, f"UDP. Error while reading from '{self._host}:{self._port}'. Remote connection closed")
                            
                except socket.timeout:
                    # Socket timeout occurred
                    if self.isNonBlocking() and (timer() - self._timestamp < self.timeout()):
                        return None
                    self.close()
                    self._raiseError(exceptions.UdpReadError, f"UDP. Error while reading from '{self._host}:{self._port}'. Timeout")
                    
                except socket.error as e:
                    # Socket error occurred
                    if e.errno == socket.EWOULDBLOCK:
                        # Non-blocking socket would block - check timeout
                        if self.isNonBlocking():
                            if (timer() - self._timestamp >= self.timeout()):
                                self.close()
                                self._raiseError(exceptions.UdpReadError, f"UDP. Error while reading from '{self._host}:{self._port}'. Timeout")
                            # Return None to continue processing later
                            return None
                    # Other socket error
                    self.close()
                    self._raiseError(exceptions.UdpReadError, f"UDP. Error while reading from '{self._host}:{self._port}'. Error: {str(e)}")
                        
                except Exception as e:
                    # Unexpected error
                    self.close()
                    if isinstance(e, ModbusException):
                        raise e
                    self._raiseError(exceptions.UdpReadError, f"UDP. Error while reading from '{self._host}:{self._port}'. Error: {str(e)}")
            else:
                if self.isOpen():
                    self._state = ModbusPort.State.STATE_OPENED
                    fRepeatAgain = True
                    continue
                else:
                    self._raiseError(exceptions.UdpWriteError, "Internal state error")
                    
            return None
                    
class ModbusUdpPort(ModbusUdpPortBase):
    """
    Implements UDP version of the Modbus communication protocol.
    
    ModbusUdpPort derives from ModbusUdpPortBase and implements writeBuffer and readBuffer
    for UDP version of Modbus communication protocol.
    
    UDP format:
    - Uses UDP/IP for communication
    - Similar to TCP format but without connection-oriented features
    - More suitable for simple, low-latency communication where reliability is not critical
    """
    
    def __init__(self, blocking: bool = True, sock = None):
        """Initialize ModbusPort with default values."""
        super().__init__(ModbusNetFrame(), blocking, sock)

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. For ModbusUdpPort returns UDP."""
        return ProtocolType.UDP
    
    def setNextRequestRepeated(self, v: bool) -> None:
        """Repeat next request parameters (for Modbus UDP transaction Id).
        
        Args:
            v: True to repeat next request ID, False otherwise.
        """
        self._frame._autoIncrement = v

    def autoIncrement(self) -> bool:
        """Returns True if the identifier of each subsequent parcel is automatically incremented by 1.
        
        Returns:
            True if auto-increment is enabled, False otherwise.
        """
        return self._frame._autoIncrement
    
    def transactionId(self) -> int:
        """Returns the current transaction identifier.
        
        Returns:
            The current transaction identifier.
        """
        return self._frame._transaction
    
