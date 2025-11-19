"""
ModbusPort.py - Contains port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
from enum import IntEnum

from .mbglobal import ProtocolType
from .statuscode import StatusCode
from .exceptions import ModbusException, getException

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

    def __init__(self, blocking: bool = True):
        """Initialize ModbusPort with default values."""
        self._state = ModbusPort.State.STATE_UNKNOWN
        self._changed = False
        self._modeServer = False
        self._modeBlocking = blocking
        self._errorStatus = StatusCode.Status_Good
        self._errorText = ""
        self._timeout = 0
        self._buff = bytearray()
    
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
        return self._modeServer
    
    def setServerMode(self, mode: bool) -> None:
        """Sets server mode if True, False for client mode.
        
        Args:
            mode: True for server mode, False for client mode.
        """
        if self._modeServer != mode:
            self._modeServer = mode
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
        return self._errorStatus
    
    def lastErrorText(self) -> str:
        """Returns the text description of the last error of the performed operation.
        
        Returns:
            Text description of the last error.
        """
        return self._errorText
    
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
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def readBuffer(self) -> Tuple[int, int, bytes]:
        """The function parses the packet that the read() function puts into the buffer.
        
        Checks it for correctness, extracts its parameters.
        
        Returns:
            Tuple of (unit, func, buff) where:
            - unit: Modbus unit address
            - func: Modbus function code
            - buff: Buffer containing the extracted data
        """
        pass
    
    # Buffer access methods
    
    def readBufferData(self) -> bytes:
        """Returns data of read buffer.
        
        Returns:
            Read buffer data or None if empty.
        """
        return self._buff
    
    def readBufferSize(self) -> int:
        """Returns size of data of read buffer.
        
        Returns:
            Size of read buffer data.`
        """
        return len(self._buff)
    
    def writeBufferData(self) -> bytes:
        """Returns data of write buffer.
        
        Returns:
            Write buffer data or None if empty.
        """
        return self._buff
    
    def writeBufferSize(self) -> int:
        """Returns size of data of write buffer.
        
        Returns:
            Size of write buffer data.
        """
        return len(self._buff)
    
    # Protected method for error handling
    
    def _setError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        if isinstance(exc, ModbusException):
            self._errorStatus = exc.code
            self._errorText = exc.message
        elif isinstance(exc, type) and issubclass(exc, ModbusException):
            self._errorStatus = exc.code
            self._errorText = text
        else: # `exc` must be integer or instance of StatusCode
            self._errorStatus = exc
            self._errorText = text
        
    def _raiseError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed and raises the exception.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._setError(exc, text)
        rexc = None
        if isinstance(exc, ModbusException):
            rexc = exc
        elif isinstance(exc, type) and issubclass(exc, ModbusException):
            rexc = exc(text)
        else: # `exc` must be integer or instance of StatusCode
            rexc = getException(exc, text)
        raise rexc
