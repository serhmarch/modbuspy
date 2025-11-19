"""
ModbusPort.py - Contains server port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from enum import IntEnum
from typing import Optional
from time import sleep

from .statuscode import StatusCode
from .exceptions import ModbusException, getException
from .mbglobal import ProtocolType, timer
from .mbinterface import ModbusInterface
from .mbobject import ModbusObject

class ModbusServerPort(ModbusObject):
    """Base class for Modbus server ports.
        
    Signals:
        * `signalOpened(source:str)` - Emitted when the port is successfully opened.
        * `signalClosed(source:str)` - Emitted when the port is closed.
        * `signalError(source:str, code:int, text:str)` - Emitted when an error occurs.
        * `signalTx(source:str, data:bytes)` - Emitted when data is transmitted.
        * `signalRx(source:str, data:bytes)` - Emitted when data is received.
    """
    
    class State(IntEnum):
        STATE_UNKNOWN        = 0
        STATE_BEGIN_OPEN     = 1
        STATE_WAIT_FOR_OPEN  = 2
        STATE_OPENED         = 3
        STATE_BEGIN_READ     = 4
        STATE_READ           = 5
        STATE_PROCESS_DEVICE = 6
        STATE_WRITE          = 7
        STATE_BEGIN_WRITE    = 8
        STATE_WAIT_FOR_CLOSE = 9
        STATE_TIMEOUT        = 10
        STATE_CLOSED         = 11
        STATE_END            = STATE_CLOSED

    def __init__(self, device: ModbusInterface):
        ModbusObject.__init__(self)
        self._device = device
        self._state = ModbusServerPort.State.STATE_UNKNOWN
        self._cmdClose = False
        self._timestamp = 0
        self._context = None
        self._settings_broadcastEnabled = True
        self._settings_unitmap = None
        self._errorStatus = StatusCode.Status_Uncertain
        self._errorText = ""
        # Signals
        self.signalOpened = ModbusObject.Signal()
        self.signalClosed = ModbusObject.Signal()
        self.signalError = ModbusObject.Signal()
        self.signalTx = ModbusObject.Signal()
        self.signalRx = ModbusObject.Signal()


    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type.
        
        Returns:
            The protocol type (TCP, RTU, or ASC).
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def device(self) -> ModbusInterface:
        """Returns reference to `ModbusInterface` object/device that was previously passed in constructor.

        This device must process every input Modbus function request for this server port."""
        return self._device

    def timeout(self) -> int:
        """Returns the timeout value in milliseconds."""
        raise NotImplementedError("Subclasses must implement this method.")

    def setTimeout(self, timeout: int) -> None:
        """Sets the timeout value in milliseconds."""
        raise NotImplementedError("Subclasses must implement this method.")

    def setDevice(self, device: ModbusInterface):
        """Set reference to `ModbusInterface` object/device to transfer all request ot it.

        This device must process every input Modbus function request for this server port."""
        self._device = device

    def open(self):
        """Open inner port/connection to begin working and returns status of the operation."""
        raise NotImplementedError("Subclasses must implement this method.")

    def close(self):
        """Closes port/connection and returns status of the operation."""
        raise NotImplementedError("Subclasses must implement this method.")

    def isOpen(self) -> bool:
        """Checks if the Modbus client port is open.
        
        Returns:
            True if the port is open, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def isBroadcastEnabled(self) -> bool:
        """Returns True if broadcast mode for '0' unit address is enabled, False otherwise.
        
        Broadcast mode for '0' unit address is required by Modbus protocol so it is enabled by default.
        
        Returns:
            True if broadcast mode is enabled, False otherwise.
        """
        return self._settings_broadcastEnabled

    def setBroadcastEnabled(self, enable: bool) -> None:
        """Enables broadcast mode for '0' unit address. It is enabled by default.
        
        Args:
            enable: True to enable broadcast mode, False to disable.
        """
        self._settings_broadcastEnabled = enable

    def unitMap(self) -> bytes:
        """Return units map byte array of the current server. 

        By default unit map is not set so return value is `None`.
        Unit map is data type with size of 32 bytes in which every bit represents unit address from `0` to `255`.
        So bit 0 of byte 0 represents unit address `0`, bit 1 of byte 0 represents unit address `1` and so on.
        Bit 0 of byte 1 represnt unit address `8`, bit 7 of byte 31 represents unit address `255`.
        If set unit map can enable or disable (depends on respecting 1/0 bit value) unit address for further processing.
        It is not set by default and function returns `None`."""
        return self._settings_unitmap

    def setUnitMap(self, unitmap: ModbusInterface):
        """Set pointer to `ModbusInterface` object/device to transfer all request ot it.

        This device must process every input Modbus function request for this server port."""
        self._settings_unitmap = unitmap

    def isStateClosed(self) -> bool:
        """Returns True if the port state is STATE_CLOSED, False otherwise.
        
        Returns:
            True if the port state is STATE_CLOSED, False otherwise.
        """
        return self._state == ModbusServerPort.State.STATE_CLOSED
    
    def lastErrorStatus(self) -> StatusCode:
        """Returns status code of the last operation performed.
        
        Returns:
            Status code of the last operation.
        """
        return self._errorStatus
    
    def lastErrorText(self) -> str:
        """Returns text description of the last error occurred.
        
        Returns:
            Text description of the last error.
        """
        return self._errorText

    def context(self) -> Optional[object]:
        """Return context of the port previously set by setContext function or None by default.
        
        Returns:
            The context object previously set, or None if no context was set.
        """
        return getattr(self, '_context', None)

    def setContext(self, context: Optional[object]) -> None:
        """Set context of the port.
        
        Args:
            context: Context object to associate with this port, or None to clear.
        """
        self._context = context

    def process(self) -> bool:
        """Main function of the class. Must be called in the cycle.
        
        Return status code is not very useful but can indicate that inner server 
        operations are good, bad or in process.

        Returns:
            True if processing was successful, False otherwise.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def forever(self) -> None:
        """Runs the server port processing in an infinite loop."""
        while 1:
            try:
                self.process()
            except ModbusException:
                pass
            sleep(0.001)  # Sleep for 1 millisecond to prevent CPU overuse

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
        
    def _timestampRefresh(self):
        """Refreshes the internal timestamp to the current time."""
        self._timestamp = timer()  # Timestamp in milliseconds