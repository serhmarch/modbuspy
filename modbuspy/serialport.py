"""
ModbusSerialPort.py - Contains serial port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

import os
import serial

from .port import ModbusPort
from .mbglobal import (ProtocolType, StatusCode, timer,
                       Parity, StopBits, FlowControl)
from . import exceptions


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
        
    def __init__(self, blocking: bool = True):
        super().__init__(blocking)
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

