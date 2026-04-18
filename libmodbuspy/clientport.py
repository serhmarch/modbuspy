"""
ModbusPort.py - Contains client port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from enum import IntEnum
from typing import Optional, Collection, Tuple
from time import sleep

from .statuscode import StatusCode
from .exceptions import ModbusException, getException
from .mbglobal import *
from .mbobject import ModbusObject
from .mbinterface import ModbusInterface
from .port import ModbusPort

class ModbusClientPort(ModbusObject, ModbusInterface):
    """Base class for Modbus client ports.
    
    Signals:
        * `signalOpened(source:str)` - Emitted when the port is successfully opened.
        * `signalClosed(source:str)` - Emitted when the port is closed.
        * `signalError(source:str, code:int, text:str)` - Emitted when an error occurs.
        * `signalTx(source:str, data:bytes)` - Emitted when data is transmitted.
        * `signalRx(source:str, data:bytes)` - Emitted when data is received.
    """
    
    class State(IntEnum):
        STATE_UNKNOWN            = 0
        STATE_BEGIN_OPEN         = 1
        STATE_WAIT_FOR_OPEN      = 2
        STATE_OPENED             = 3
        STATE_BEGIN_WRITE        = 4
        STATE_WRITE              = 5
        STATE_BEGIN_READ         = 6
        STATE_READ               = 7
        STATE_WAIT_FOR_CLOSE     = 8
        STATE_TIMEOUT            = 9
        STATE_CLOSED             = 10
        STATE_END                = STATE_CLOSED

    class RequestStatus(IntEnum):
        Enable  = 0
        Disable = 1
        Process = 2

    def __init__(self, port: ModbusPort):
        ModbusObject.__init__(self)
        self._port = port
        self._unit = 0
        self._func = 0
        self._offset = 0
        self._count = 0
        self._value = 0
        self._orMask = 0
        self._readDeviceIdCode = 0
        self._readDeviceIdObjectId = 0
        self._buff = bytearray()
        self._block = False
        self._currentClient = None
        self._port = port
        self._repeats = 0
        self._lastStatus = StatusCode.Status_Uncertain
        self._lastErrorStatus = StatusCode.Status_Uncertain
        self._lastErrorText = ""
        self._lastTries = 0
        self._isLastPortError = True
        self._timestamp = 0
        self._lastStatusTimestamp = 0
        self._settings_tries = 1
        self._settings_broadcastEnabled = True
        self._state = ModbusClientPort.State.STATE_UNKNOWN
        port.setServerMode(False)
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
        return self._port.type()
    
    def port(self) -> ModbusPort:
        """Returns the Modbus port instance."""
        return self._port
    
    def setPort(self, port: ModbusPort):
        """Sets the Modbus port instance."""
        self._port = port

    def open(self) -> StatusCode:
        """Opens the Modbus client port.
        
        Usually this method is called internally by the ModbusClient object.
        So, the user does not need to call it directly.
        
        Returns:
            * `StatusCode` indicating the result of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).
        """
        return self._port.open()

    def close(self) -> StatusCode:
        """Closes the Modbus client port.

        For network socket it shuts down connection (TCP) and closes the socket.
        For serial port it closes the port.
        
        Returns:
            * `StatusCode` indicating the result of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).
        """
        return self._port.close()

    def isOpen(self) -> bool:
        """Checks if the Modbus client port is open.
        
        Returns:
            True if the port is open, False otherwise.
        """
        return self._port.isOpen()
    
    def tries(self) -> int:
        """Returns the number of connection tries."""
        return self._settings_tries
    
    def setTries(self, tries: int):
        """Sets the number of tries a Modbus request is repeated if it fails."""
        self._settings_tries = tries

    def repeatCount(self) -> int:
        """Same as tries(). Used for backward compatibility.
        
        Returns:
            The number of connection tries.
        """
        return self.tries()

    def setRepeatCount(self, v: int) -> None:
        """Same as setTries(). Used for backward compatibility.
        
        Args:
            v: The number of tries to set.
        """
        self.setTries(v)

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

    def readCoils(self, unit: int, offset: int, count: int) -> bytes:
        return self._readCoils(self, unit, offset, count)
    
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes:
        return self._readDiscreteInputs(self, unit, offset, count)

    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
        return self._readHoldingRegisters(self, unit, offset, count)

    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes:
        return self._readInputRegisters(self, unit, offset, count)

    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode:
        return self._writeSingleCoil(self, unit, offset, value)

    def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode:
        return self._writeSingleRegister(self, unit, offset, value)

    def readExceptionStatus(self, unit: int) -> bytes:
        return self._readExceptionStatus(self, unit)

    def diagnosticsReturnQueryData(self, unit: int, indata: bytes) -> bytes:
        return self._diagnosticsReturnQueryData(self, unit, indata)
        
    def diagnosticsRestartCommunicationsOption(self, unit: int, clearEventLog: bool) -> StatusCode:
        return self._diagnosticsRestartCommunicationsOption(self, unit, clearEventLog)
        
    def diagnosticsReturnDiagnosticRegister(self, unit: int) -> bytes:
        return self._diagnosticsReturnDiagnosticRegister(self, unit)
        
    def diagnosticsChangeAsciiInputDelimiter(self, unit: int, delimiter: int) -> StatusCode:
        return self._diagnosticsChangeAsciiInputDelimiter(self, unit, delimiter)

    def diagnosticsForceListenOnlyMode(self, unit: int) -> StatusCode:
        return self._diagnosticsForceListenOnlyMode(self, unit)
    
    def diagnosticsClearCountersAndDiagnosticRegister(self, unit: int) -> StatusCode:
        return self._diagnosticsClearCountersAndDiagnosticRegister(self, unit)
    
    def diagnosticsReturnBusMessageCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnBusMessageCount(self, unit)
    
    def diagnosticsReturnBusCommunicationErrorCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnBusCommunicationErrorCount(self, unit)
    
    def diagnosticsReturnBusExceptionErrorCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnBusExceptionErrorCount(self, unit)
    
    def diagnosticsReturnServerMessageCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnServerMessageCount(self, unit)
    
    def diagnosticsReturnServerNoResponseCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnServerNoResponseCount(self, unit)
    
    def diagnosticsReturnServerNAKCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnServerNAKCount(self, unit)
    
    def diagnosticsReturnServerBusyCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnServerBusyCount(self, unit)
    
    def diagnosticsReturnBusCharacterOverrunCount(self, unit: int) -> bytes:
        return self._diagnosticsReturnBusCharacterOverrunCount(self, unit)
    
    def getCommEventCounter(self, unit: int) -> int:
        return self._getCommEventCounter(self, unit)
    
    def getCommEventLog(self, unit: int) -> bytes:
        return self._getCommEventLog(self, unit)
        
    def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode:
        return self._writeMultipleCoils(self, unit, offset, values, count)
        
    def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode:
        return self._writeMultipleRegisters(self, unit, offset, values)
        
    def reportServerID(self, unit: int) -> bytes:
        return self._reportServerID(self, unit)

    def readFileRecord(self, unit: int, records: Collection) -> Tuple:
        return self._readFileRecord(self, unit, records)
        
    def writeFileRecord(self, unit: int, records: Collection) -> StatusCode:
        return self._writeFileRecord(self, unit, records)
        
    def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode:
        return self._maskWriteRegister(self, unit, offset, andMask, orMask)

    def readWriteMultipleRegisters(self, unit: int,
                                   readOffset: int, readCount: int,
                                   writeOffset: int, writeValues: bytes) -> bytes:
        return self._readWriteMultipleRegisters(self, unit,
                                                readOffset, readCount,
                                                writeOffset, writeValues)

    def readFIFOQueue(self, unit: int, fifoadr: int) -> bytes:
        return self._readFIFOQueue(self, unit, fifoadr)

    def readDeviceIdentification(self, unit: int, deviceId: int, objectId: int) -> dict:
        return self._readDeviceIdentification(self, unit, deviceId, objectId)

    # formatting methods
    def readCoilsF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._readCoilsF(self, unit, offset, count, fmt=fmt)

    def readDiscreteInputsF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._readDiscreteInputsF(self, unit, offset, count, fmt=fmt)

    def readHoldingRegistersF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._readHoldingRegistersF(self, unit, offset, count, fmt=fmt)

    def readInputRegistersF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._readInputRegistersF(self, unit, offset, count, fmt=fmt)

    def writeMultipleCoilsF(self, unit: int, offset: int, values: Tuple, count: int = -1, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return self._writeMultipleCoilsF(self, unit, offset, values, count, fmt=fmt)
    
    def writeMultipleRegistersF(self, unit: int, offset: int, values: Tuple, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return self._writeMultipleRegistersF(self, unit, offset, values, fmt=fmt)
    
    def readWriteMultipleRegistersF(self, unit: int, readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: Tuple, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._readWriteMultipleRegistersF(self, unit, readOffset, readCount,
                                                 writeOffset, writeValues, fmt=fmt)
    
    # Status methods
    
    def lastStatus(self) -> StatusCode:
        """Returns the status of the last operation performed.
        
        Returns:
            StatusCode of the last operation.
        """
        return self._lastStatus

    def lastStatusTimestamp(self) -> int:
        """Returns the timestamp of the last operation performed.
        
        Returns:
            Timestamp of the last operation in milliseconds.
        """
        return self._lastStatusTimestamp

    def lastErrorStatus(self) -> StatusCode:
        """Returns the status of the last error of the performed operation.
        
        Returns:
            StatusCode of the last error.
        """
        return self._lastErrorStatus

    def lastErrorText(self) -> str:
        """Returns the text of the last error of the performed operation.
        
        Returns:
            Text description of the last error.
        """
        return self._port.lastErrorText()

    def lastTries(self) -> int:
        """Returns statistics of the count of tries already processed.
        
        Returns:
            Number of tries that were processed for the last operation.
        """
        return self._lastTries

    def lastRepeatCount(self) -> int:
        """Same as lastTries().
        
        Returns:
            Number of tries that were processed for the last operation.
        """
        return self._lastTries

    def currentClient(self) -> ModbusObject:
        """Returns a pointer to the client object whose request is currently being processed by the current port.
        
        Returns:
            The ModbusObject client currently being processed, or None if no client is active.
        """
        return self._currentClient

    def getRequestStatus(self, client: ModbusObject) -> 'RequestStatus':
        """Returns status the current request for client.
        
        The client usually calls this function to determine whether its request is 
        pending/finished/blocked.
        
        Args:
            client: The client object to check status for.
            
        Returns:
            RequestStatus indicating:
            - Enable: client has just became current and can make request to the port
            - Process: current client is already processing  
            - Disable: other client owns the port
        """
        if self._currentClient is None:
            self._currentClient = client
            return ModbusClientPort.RequestStatus.Enable
        elif self._currentClient == client:
            return ModbusClientPort.RequestStatus.Process
        else:
            return ModbusClientPort.RequestStatus.Disable

    def getName(self) -> str:
        """Returns the name of the port."""
        if self._currentClient is None:
            return self.objectName()
        return self._currentClient.objectName()
    
    def cancelRequest(self, client: ModbusObject) -> None:
        """Cancels the previous request specified by the client.
        
        Args:
            client: The client object whose request should be cancelled.
        """
        if self._currentClient == client:
            self._currentClient = None

    # formatting methods (extended)
    def _readCoilsF(self, client: ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        buff = self._readCoils(client, unit, offset, count)
        if buff is None:
            return None
        return unpack(fmt, buff)

    def _readDiscreteInputsF(self, client: ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        buff = self._readDiscreteInputs(client, unit, offset, count)
        if buff is None:
            return None
        return unpack(fmt, buff)

    def _readHoldingRegistersF(self, client: ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        buff = self._readHoldingRegisters(client, unit, offset, count)
        if buff is None:
            return None
        return unpack(fmt, buff)

    def _readInputRegistersF(self, client: ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        buff = self._readInputRegisters(client, unit, offset, count)
        if buff is None:
            return None
        return unpack(fmt, buff)

    def _writeMultipleCoilsF(self, client: ModbusObject, unit: int, offset: int, values: Tuple, count: int = -1, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        if self._currentClient is None:
            return self._writeMultipleCoils(client, unit, offset, pack(fmt, values), count)
        elif self._currentClient == client:
            return self._writeMultipleCoils(client, unit, offset, bytes(), count)
    
    def _writeMultipleRegistersF(self, client: ModbusObject, unit: int, offset: int, values: Tuple, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        if self._currentClient is None:
            return self._writeMultipleCoils(client, unit, offset, pack(fmt, values))
        elif self._currentClient == client:
            return self._writeMultipleCoils(client, unit, offset, bytes())
    
    def _readWriteMultipleRegistersF(self, client: ModbusObject, unit: int, readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: Tuple, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        if self._currentClient is None:
            buff = self._readWriteMultipleRegisters(client, unit, readOffset, readCount,
                                                    writeOffset, pack(fmt, writeValues))
        else:
            buff = self._readWriteMultipleRegisters(client, unit, readOffset, readCount,
                                                    writeOffset, bytes())
        if buff is None:
            return None
        return unpack(fmt, buff)
    
    # extended methods
    def _readCoils(self, client: ModbusObject, unit: int, offset: int, count: int) -> bytes:
        """Read coils from Modbus device.
        
        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Starting address of coils to read.
            count: Number of coils to read.
            
        Returns:
            Bytes containing the coil values.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            if count > MB_MAX_DISCRETS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readCoils(offset={offset}, count={count}): Requested count of coils is too large")
            # Prepare request buffer
            self._buff = bytearray(4)
            self._buff[0] = (offset >> 8) & 0xFF    # Start coil offset - MS BYTE
            self._buff[1] = offset & 0xFF           # Start coil offset - LS BYTE
            self._buff[2] = (count >> 8) & 0xFF     # Quantity of coils - MS BYTE
            self._buff[3] = count & 0xFF            # Quantity of coils - LS BYTE
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_COILS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "No data was received")
            fcBytes = buff[0]  # count of bytes received
            if fcBytes != len(buff) - 1:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            if fcBytes != ((self._count + 7) // 8):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' is not match received one")
            # Extract coil values from response
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(buff[1:fcBytes])
        else:
            return None
    
    def _readDiscreteInputs(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        """Read discrete inputs from Modbus device.
        
        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Starting address of discrete input to read.
            count: Number of discrete input to read.
            
        Returns:
            Bytes containing the discrete input values.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            if count > MB_MAX_DISCRETS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readDiscreteInputs(offset={offset}, count={count}): Requested count of coils is too large")
            # Prepare request buffer
            self._buff = bytearray(4)
            self._buff[0] = (offset >> 8) & 0xFF    # Start discrete input offset - MS BYTE
            self._buff[1] = offset & 0xFF           # Start discrete input offset - LS BYTE
            self._buff[2] = (count >> 8) & 0xFF     # Quantity of discrete inputs - MS BYTE
            self._buff[3] = count & 0xFF            # Quantity of discrete inputs - LS BYTE
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_DISCRETE_INPUTS, self._buff)
            if buff is None:
                return None
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "No data was received")
            fcBytes = buff[0]  # count of bytes received
            if fcBytes != len(buff) - 1:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            if fcBytes != ((self._count + 7) // 8):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' is not match received one")
            # Extract coil values from response
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(buff[1:fcBytes])
        else:
            return None
        
    def _readHoldingRegisters(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        """Read holding registers from Modbus device.
        
        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Starting address of holding registers to read.
            count: Number of holding registers to read.

        Returns:
            Bytes containing the holding register values.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            if count > MB_MAX_REGISTERS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readHoldingRegisters(offset={offset}, count={count}): Requested count of holding registers is too large")
            # Prepare request buffer
            self._buff = bytearray(4)
            self._buff[0] = (offset >> 8) & 0xFF    # Start holding register offset - MS BYTE
            self._buff[1] = offset & 0xFF           # Start holding register offset - LS BYTE
            self._buff[2] = (count >> 8) & 0xFF     # Quantity of holding registers - MS BYTE
            self._buff[3] = count & 0xFF            # Quantity of holding registers - LS BYTE
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_HOLDING_REGISTERS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "No data was received")
            fcBytes = buff[0]  # count of bytes received
            if fcBytes != len(buff) - 1:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            fcRegs = fcBytes // 2
            if fcRegs != self._count:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' is not match received one")
            # Extract holding register values from response
            values = bytearray(fcBytes)
            for i in range(fcRegs):
                values[i*2  ] = buff[2+i*2]
                values[i*2+1] = buff[1+i*2]
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(values)
        else:
            return None
        
    def _readInputRegisters(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        """Read input registers from Modbus device.
        
        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Starting address of input registers to read.
            count: Number of input registers to read.

        Returns:
            Bytes containing the input register values.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            if count > MB_MAX_REGISTERS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readInputRegisters(offset={offset}, count={count}): Requested count of holding registers is too large")
            # Prepare request buffer
            self._buff = bytearray(4)
            self._buff[0] = (offset >> 8) & 0xFF # Start input register offset - MS BYTE
            self._buff[1] = offset & 0xFF        # Start input register offset - LS BYTE
            self._buff[2] = (count >> 8) & 0xFF  # Quantity of input registers - MS BYTE
            self._buff[3] = count & 0xFF         # Quantity of input registers - LS BYTE
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_INPUT_REGISTERS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "No data was received")
            fcBytes = buff[0]  # count of bytes received
            if fcBytes != len(buff) - 1:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            fcRegs = fcBytes // 2
            if fcRegs != self._count:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' is not match received one")
            # Extract input register values from response
            values = bytearray(fcBytes)
            for i in range(fcRegs):
                values[i*2  ] = buff[2+i*2]
                values[i*2+1] = buff[1+i*2]
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(values)
        else:
            return None
        
    def _writeSingleCoil(self, client:ModbusObject, unit: int, offset: int, value: bool) -> StatusCode:
        """Write a single coil to Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Address of the coil to write.
            value: Value to write to the coil (True for ON, False for OFF).

        Returns:
            StatusCode of the operation.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray(4)
            self._buff[0] = (offset >> 8) & 0xFF # Coil offset - MS BYTE
            self._buff[1] = offset & 0xFF        # Coil offset - LS BYTE
            self._buff[2] = 0xFF if value else 0 # Value - 0xFF if true, 0x00 if false
            self._buff[3] = 0                    # Value - must always be NULL
            self._offset = offset
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_WRITE_SINGLE_COIL, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return StatusCode.Status_Good
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outOffset = buff[1] | (buff[0] << 8)
            if outOffset != self._offset:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Offset' is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None
        
    def _writeSingleRegister(self, client:ModbusObject, unit: int, offset: int, value: int) -> StatusCode:
        """Write a single register to Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Address of the register to write.
            value: Value to write to the register.

        Returns:
            StatusCode of the operation.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray(4)
            self._buff[0] = (offset >> 8) & 0xFF # Register offset - MS BYTE
            self._buff[1] = offset & 0xFF        # Register offset - LS BYTE
            self._buff[2] = (value >> 8) & 0xFF  # Value - MS BYTE
            self._buff[3] = value & 0xFF         # Value - LS BYTE
            self._offset = offset
            self._value = value
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_WRITE_SINGLE_REGISTER, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return StatusCode.Status_Good
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outOffset = buff[1] | (buff[0] << 8)
            if outOffset != self._offset:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Offset' is not match received one")
            outValue = buff[3] | (buff[2] << 8)
            if outValue != self._value:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Value' is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None
        
    def _readExceptionStatus(self, client:ModbusObject, unit: int) -> bytes:
        """Read exception status from Modbus device.

        Args:
            client: The client object making the request.

            unit: Modbus unit/slave address.

        Returns:
            `bytes` array with single byte that containing the exception status.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray()
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_EXCEPTION_STATUS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 1:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(buff)
        else:
            return None
        
    def _diagnosticsReturnQueryData(self, client:ModbusObject, unit: int, indata: bytes) -> bytes:
        """Diagnostics subfunction provides an echo of the supplied data.

        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            indata: Input data buffer for the diagnostic function.
            
        Returns:
            * `bytes` array containing the response data.
            * `None` when operation is not finished yet (only for nonblocking mode).
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_QUERY_DATA
            self._buff = bytearray(2)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2:] = indata
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) < 2:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(buff[2:])
        else:
            return None

    def _diagnosticsRestartCommunicationsOption(self, client:ModbusObject, unit: int, clearEventLog: bool) -> StatusCode:
        """Diagnostics subfunction restart communication and clears all of device's event counters.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            clearEventLog: Boolean flag to clear the event log.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RESTART_COMMUNICATIONS_OPTION
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF           # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF                  # Sub function - LS BYTE
            self._buff[2] = 0xFF if clearEventLog else 0x00 # Restart Option - 0xFF if true, 0x00 if false  
            self._buff[3] = 0x00                            # Restart Option - must always be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None

    def _diagnosticsReturnDiagnosticRegister(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns contents of the remote device's 16-bit diagnostic register.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_DIAGNOSTIC_REGISTER
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsChangeAsciiInputDelimiter(self, client:ModbusObject, unit: int, delimiter: int) -> StatusCode:
        """Diagnostics subfunction sets the character `delimiter` as the end of message delimiter.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            delimiter: ASCII character to be set as the end of message delimiter.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_CHANGE_ASCII_INPUT_DELIMITER
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF           # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF                  # Sub function - LS BYTE
            self._buff[2] = delimiter & 0xFF                # ASCII Input Delimiter
            self._buff[3] = 0x00                            # Must always be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None

    def _diagnosticsForceListenOnlyMode(self, client:ModbusObject, unit: int) -> StatusCode:
        """Diagnostics subfunction forces the addressed remote device to its Listen Only Mode for MODBUS communications.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_FORCE_LISTEN_ONLY_MODE
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF           # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF                  # Sub function - LS BYTE
            self._buff[2] = 0x00                            # Must always be 0x00
            self._buff[3] = 0x00                            # Must always be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None
        
    def _diagnosticsClearCountersAndDiagnosticRegister(self, client:ModbusObject, unit: int) -> StatusCode:
        """Diagnostics subfunction clear all counters and the diagnostic register.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_CLEAR_COUNTERS_AND_DIAGNOSTIC_REGISTER
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF           # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF                  # Sub function - LS BYTE
            self._buff[2] = 0x00                            # Must always be 0x00
            self._buff[3] = 0x00                            # Must always be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None
        
    def _diagnosticsReturnBusMessageCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages that the remote device has detected
        on the communications system since its last restart, clear counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_BUS_MESSAGE_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnBusCommunicationErrorCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of CRC errors encountered by the remote device
        since its last restart, clear counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_BUS_COMMUNICATION_ERROR_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnBusExceptionErrorCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of MODBUS exception responses returned by the
        remote device since its last restart, clear counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_BUS_EXCEPTION_ERROR_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnServerMessageCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device, or
        broadcast, that the remote device has processed since its last restart, clear counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_SERVER_MESSAGE_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnServerNoResponseCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device for
        which it has returned no response (neither a normal response nor an exception response),
        since its last restart, clear counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_SERVER_NO_RESPONSE_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnServerNAKCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device for
        which it returned a Negative Acknowledge (NAK) exception response, since its last restart,
        clear counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_SERVER_NAK_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnServerBusyCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device for
        which it returned a Server Device Busy exception response, since its last restart, clear
        counters operation, or power-up.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_SERVER_BUSY_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _diagnosticsReturnBusCharacterOverrunCount(self, client:ModbusObject, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device that
        it could not handle due to a character overrun condition, since its last restart, clear counters
        operation, or power-up. A character overrun is caused by data characters arriving at the port
        faster than they can be stored, or by the loss of a character due to a hardware malfunction.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            subfunc = MBF_DIAGNOSTICS_RETURN_BUS_CHARACTER_OVERRUN_COUNT
            self._buff = bytearray(4)
            self._buff[0] = (subfunc >> 8) & 0xFF # Sub function - MS BYTE
            self._buff[1] = subfunc & 0xFF        # Sub function - LS BYTE
            self._buff[2] = 0x00                  # Must be 0x00
            self._buff[3] = 0x00                  # Must be 0x00
            self._subfunc = subfunc
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_DIAGNOSTICS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outSubfunc = buff[1] | (buff[0] << 8)
            if outSubfunc != self._subfunc:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Diagnostics sub-function is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes([buff[3], buff[2]]) # Register value - LS BYTE first
        else:
            return None

    def _getCommEventCounter(self, client:ModbusObject, unit: int) -> bytes:
        """ Get communication event counter from Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.

        Returns:
            Bytes containing the communication status and event counter values,
            where first two bytes are status and next two bytes are event count.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray()
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_GET_COMM_EVENT_COUNTER, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            values = bytearray(4)
            values[0] = buff[1]  # Status - LS BYTE
            values[1] = buff[0]  # Status - MS BYTE
            values[2] = buff[3]  # Event count - LS BYTE
            values[3] = buff[2]  # Event count - MS BYTE
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(values)
        else:
            return None
        
    def _getCommEventLog(self, client:ModbusObject, unit: int) -> bytes:
        """Get communication event log from Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.

        Returns:
            Bytes containing the communication event log data,  
            where first two bytes are status, next two bytes are event count,
            next two bytes are message count, and the rest is event log data.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray()
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_GET_COMM_EVENT_LOG, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) < 7:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            byteCount = buff[0]
            if len(buff) != (byteCount+1):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' doesn't match with received data size")
            values = bytearray(6)
            values[0] = buff[2] # Status - LS BYTE
            values[1] = buff[1] # Status - MS BYTE
            values[2] = buff[4] # Event count - LS BYTE
            values[3] = buff[3] # Event count - MS BYTE
            values[4] = buff[5] # Message count - LS BYTE
            values[5] = buff[6] # Message count - MS BYTE
            values[6:] = buff[7:] # Event log data
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(values)
        else:
            return None
        
    def _writeMultipleCoils(self, client:ModbusObject, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode:
        """Write multiple coils to Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Starting address of the coils to write.
            count: Number of coils to write.
            values: Bytes containing the coil values to write.

        Returns:
            StatusCode of the operation.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            if count < 0:
                count = len(values) * 8
            if count > MB_MAX_DISCRETS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::writeMultipleCoils(offset={offset}, count={count}): Requested count of coils is too large")
            # Prepare request buffer
            self._buff = bytearray(5)
            self._buff[0] = (offset >> 8) & 0xFF # Start coil offset - MS BYTE
            self._buff[1] = offset & 0xFF        # Start coil offset - LS BYTE
            self._buff[2] = (count >> 8) & 0xFF  # Quantity of coils - MS BYTE
            self._buff[3] = count & 0xFF         # Quantity of coils - LS BYTE
            byteCount = (count + 7) // 8
            self._buff[4] = byteCount            # Quantity of next bytes
            self._buff[5:] = values[0:byteCount] # Coil values
            self._offset = offset
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_WRITE_MULTIPLE_COILS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return StatusCode.Status_Good
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outOffset = buff[1] | (buff[0] << 8)
            if outOffset != self._offset:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Offset' is not match received one")
            outCount = buff[3] | (buff[2] << 8)
            if outCount != self._count:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Count' is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None
        
    def _writeMultipleRegisters(self, client:ModbusObject, unit: int, offset: int, values: bytes) -> StatusCode:
        """Write multiple registers to Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Starting address of the registers to write.
            count: Number of registers to write.
            values: Bytes containing the register values to write.

        Returns:
            StatusCode of the operation.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            count = len(values) // 2
            if count > MB_MAX_REGISTERS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readCoils(offset={offset}, count={count}): Requested count of coils is too large")
            # Prepare request buffer
            byteCount = count * 2
            self._buff = bytearray(5+byteCount)
            self._buff[0] = (offset >> 8) & 0xFF # Start register offset - MS BYTE
            self._buff[1] = offset & 0xFF        # Start register offset - LS BYTE
            self._buff[2] = (count >> 8) & 0xFF  # Quantity of registers - MS BYTE
            self._buff[3] = count & 0xFF         # Quantity of registers - LS BYTE
            self._buff[4] = byteCount            # Quantity of next bytes
            for i in range(count):
                self._buff[5+i*2] = values[i*2+1] # Register value - LS BYTE
                self._buff[6+i*2] = values[i*2  ] # Register value - MS BYTE
            self._offset = offset
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_WRITE_MULTIPLE_REGISTERS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return StatusCode.Status_Good
            if len(buff) != 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outOffset = buff[1] | (buff[0] << 8)
            if outOffset != self._offset:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Offset' is not match received one")
            outCount = buff[3] | (buff[2] << 8)
            if outCount != self._count:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Count' is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None
        
    def _reportServerID(self, client:ModbusObject, unit: int) -> bytes:
        """Report server ID from Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.

        Returns:
            Bytes containing the server ID data.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray()
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_REPORT_SERVER_ID, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            byteCount = buff[0]
            if len(buff) != (byteCount+1):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' doesn't match with received data size")
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(buff[1:])
        else:
            return None

    def _readFileRecord(self, client:ModbusObject, unit: int, records: Collection) -> Tuple:
        """Function is used to read one or more file records from a remote device.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            records: Sized iterable collection of records to read, where each record is
                     a dict with keys "fileNumber", "recordNumber", "recordLength".

        Returns:
            * `list` of bytes array that represents the requested file records data.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            count = len(records)
            if count > MB_FILE_RECORD_MAX:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readFileRecord(): Requested count of records {count} is too large")
            # Prepare request buffer
            byteCount = count * 7
            self._buff = bytearray(1+byteCount)
            i = 0
            for record in records:
                fileNumber = record["fileNumber"]
                recordNumber = record["recordNumber"]
                recordLength = record["recordLength"]
                idx = 1 + i * 7
                self._buff[idx    ] = 0x06                       # Reference Type - must be 0x06
                self._buff[idx + 1] = (fileNumber >> 8) & 0xFF   # File number - MS BYTE
                self._buff[idx + 2] = fileNumber & 0xFF          # File number - LS BYTE
                self._buff[idx + 3] = (recordNumber >> 8) & 0xFF # Record number - MS BYTE
                self._buff[idx + 4] =  recordNumber & 0xFF       # Record number - LS BYTE
                self._buff[idx + 5] = (recordLength >> 8) & 0xFF # Record length - MS BYTE
                self._buff[idx + 6] = recordLength & 0xFF        # Record length - LS BYTE
                i += 1
            self._buff[0] = byteCount
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_FILE_RECORD, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return []
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            byteCount = buff[0]
            if len(buff) != (byteCount+1):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' doesn't match with received data size")
            res = []
            opos = 1
            for i in range(self._count):
                if opos + 1 > byteCount:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
                fileRespLength = buff[opos]
                if ((fileRespLength < 1) or
                    (fileRespLength > MB_FILE_RECORD_BUFF_SZ) or
                    (fileRespLength & 0x01 == 0) # Record length must NOT be even: 1+2*N
                    ):
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
                refType = buff[opos + 1]
                if refType != 0x06:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received reference type")
                if opos + fileRespLength > byteCount:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
                opos += 2
                c = (fileRespLength - 1) // 2
                b = bytearray(c)
                for j in range(c):
                    # Swap bytes in each register value
                    idx = opos + j * 2
                    b[j*2], b[j*2+1] = buff[idx+1], buff[idx]
                recData = bytes(b)
                res.append(recData)
                opos += fileRespLength
            if opos != (byteCount + 1):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            self._setStatusCompleted(StatusCode.Status_Good)
            return tuple(res)
        else:
            return None

    def _writeFileRecord(self, client:ModbusObject, unit: int, records: Collection) -> StatusCode:
        """Function is used to write one or more file records to a remote device.
        
        Args:
            client: The client object making the request.
            unit: Address of the remote Modbus device.
            records: Sized iterable collection of records to read, where each record is
                     a dict with keys "fileNumber", "recordNumber", "recordLength".

        Returns:
            * `list` of bytes array that represents the requested file records data.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            count = len(records)
            if count > MB_FILE_RECORD_MAX:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::writeFileRecord(): Requested count of records {count} is too large")
            # Prepare request buffer
            self._buff = bytearray(1)
            byteCount = 0
            for record in records:
                fileNumber = record["fileNumber"]
                recordNumber = record["recordNumber"]
                recordData = record["recordData"]
                recordLength = len(recordData) // 2
                c = recordLength * 2 + 7
                self._buff.resize(len(self._buff) + c)
                idx = 1 + byteCount
                self._buff[idx    ] = 0x06                       # Reference Type - must be 0x06
                self._buff[idx + 1] = (fileNumber >> 8) & 0xFF   # File number - MS BYTE
                self._buff[idx + 2] = fileNumber & 0xFF          # File number - LS BYTE
                self._buff[idx + 3] = (recordNumber >> 8) & 0xFF # Record number - MS BYTE
                self._buff[idx + 4] =  recordNumber & 0xFF       # Record number - LS BYTE
                self._buff[idx + 5] = (recordLength >> 8) & 0xFF # Record length - MS BYTE
                self._buff[idx + 6] = recordLength & 0xFF        # Record length - LS BYTE
                for i in range(recordLength):
                    # Swap bytes in each register value
                    self._buff[idx + 7 + i*2] = recordData[i*2+1] # Register value - LS BYTE
                    self._buff[idx + 8 + i*2] = recordData[i*2  ] # Register value - MS BYTE
                byteCount += c
            self._buff[0] = byteCount
            self._count = count
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_WRITE_FILE_RECORD, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return []
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            byteCount = buff[0]
            if len(buff) != (byteCount+1):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' doesn't match with received data size")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None

    def _maskWriteRegister(self, client:ModbusObject, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode:
        """Mask write register on Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            offset: Address of the register to write.
            andMask: AND mask to apply.
            orMask: OR mask to apply.

        Returns:
            StatusCode of the operation.
        """
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            self._buff = bytearray(6)
            self._buff[0] = (offset >> 8) & 0xFF  # Start register offset - MS BYTE
            self._buff[1] = offset & 0xFF         # Start register offset - LS BYTE
            self._buff[2] = (andMask >> 8) & 0xFF # AndMask - MS BYTE
            self._buff[3] = andMask & 0xFF        # AndMask - LS BYTE
            self._buff[4] = (orMask >> 8) & 0xFF  # OrMask - MS BYTE
            self._buff[5] = orMask & 0xFF         # OrMask - LS BYTE
            self._offset = offset
            self._andMask = andMask
            self._orMask = orMask
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_MASK_WRITE_REGISTER, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return StatusCode.Status_Good
            if len(buff) != 6:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            outOffset  = buff[1] | (buff[0] << 8)
            outAndMask = buff[3] | (buff[2] << 8)
            outOrMask  = buff[5] | (buff[4] << 8)
            if (outOffset != self._offset):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'Offset' is not match received one")
            if (outAndMask != self._andMask):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'AndMask' is not match received one")
            if (outOrMask != self._orMask):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'OrMask' is not match received one")
            self._setStatusCompleted(StatusCode.Status_Good)
            return StatusCode.Status_Good
        else:
            return None

    def _readWriteMultipleRegisters(self, client:ModbusObject, unit: int, readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: bytes) -> bytes:
        """Read/Write multiple registers on Modbus device."""
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            writeCount = len(writeValues) // 2
            if readCount > MB_MAX_REGISTERS or writeCount > MB_MAX_REGISTERS:
                self._raiseError(StatusCode.Status_BadNotCorrectRequest, f"ModbusClientPort::readWriteMultipleRegisters(): Requested count of registers is too large")
            # Prepare request buffer
            byteCount = writeCount * 2
            self._buff = bytearray(9+byteCount)
            self._buff[0] = (readOffset >> 8) & 0xFF  # read starting offset - MS BYTE
            self._buff[1] = readOffset & 0xFF         # read starting offset - LS BYTE
            self._buff[2] = (readCount >> 8) & 0xFF   # quantity to read - MS BYTE
            self._buff[3] = readCount & 0xFF          # quantity to read - LS BYTE
            self._buff[4] = (writeOffset >> 8) & 0xFF # write starting offset - MS BYTE
            self._buff[5] = writeOffset & 0xFF        # write starting offset - LS BYTE
            self._buff[6] = (writeCount >> 8) & 0xFF  # quantity to write - MS BYTE
            self._buff[7] = writeCount & 0xFF         # quantity to write - LS BYTE
            self._buff[8] = byteCount                 # quantity of next bytes
            for i in range(writeCount):
                self._buff[ 9+i*2] = writeValues[i*2+1] # Register value - LS BYTE
                self._buff[10+i*2] = writeValues[i*2  ] # Register value - MS BYTE
            self._count = readCount
            status = ModbusClientPort.RequestStatus.Process
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_WRITE_MULTIPLE_REGISTERS, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return StatusCode.Status_Good
            if len(buff) == 0:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "No data was received")
            fcBytes = buff[0]  # count of bytes received
            if fcBytes != len(buff) - 1:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            fcRegs = fcBytes // 2  # count values received
            if fcRegs != self._count:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Count registers to read is not match received one")
            # Extract input register values from response
            values = bytearray(fcRegs*2)
            for i in range(fcRegs):
                values[i*2  ] = buff[2+i*2]
                values[i*2+1] = buff[1+i*2]
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(values)
        else:
            return None
        
    def _readFIFOQueue(self, client:ModbusObject, unit: int, fifoadr: int) -> bytes:
        """Read FIFO queue from Modbus device.

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            fifoadr: Starting address of the FIFO queue to read.

        Returns:
            Bytes containing the FIFO queue values.
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray(2)
            self._buff[0] = (fifoadr >> 8) & 0xFF    # Start register offset - MS BYTE
            self._buff[1] = fifoadr & 0xFF           # Start register offset - LS BYTE
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_READ_FIFO_QUEUE, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return bytes()
            if len(buff) < 4:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            # Extract FIFO queue values from response
            bytesCount = buff[1] | (buff[0] << 8)
            if bytesCount != (len(buff) - 2):
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'ByteCount' doesn't match with received data size")
            FIFOCount = buff[3] | (buff[2] << 8)
            if bytesCount != (FIFOCount + 1) * 2:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "'FIFOCount' doesn't relate to the 'ByteCount'")
            if FIFOCount > MB_READ_FIFO_QUEUE_MAX:
                self._raiseError(StatusCode.Status_BadIllegalDataValue, "'FIFOCount' is bigger than 31")
            values = bytearray(FIFOCount * 2)
            for i in range(FIFOCount):
                values[i*2  ] = buff[5+i*2]
                values[i*2+1] = buff[4+i*2]
            self._setStatusCompleted(StatusCode.Status_Good)
            return bytes(values)
        else:
            return None

    def _readDeviceIdentification(self, client:ModbusObject, unit: int, deviceId: int, objectId: int) -> dict:
        """Function for Read Device Identification, FC43 (0x2B), MEI type 14 (0x0E).
        Reads identity objects (vendor name, product code, revision, etc.) from a remote device.
        The response is returned as list of tuples containing (objectId:int, objectData:bytes).

        Args:
            client: The client object making the request.
            unit: Modbus unit/slave address.
            deviceId: Read Device ID code: 1=Basic, 2=Regular, 3=Extended, 4=Specific.
            objectId: Starting object ID to read from (0x00-0xFF).

        Returns:
            * `dict` of values representing the requested device identification:
                - "conformityLevel" - Conformity level of the device
                - "moreFollows" - Boolean flag indicating if more objects follow
                - "nextObjectId" - Next object ID to read (if moreFollows is True)
                - "objects" - list of tuples (objectId:int, objectData:bytes) for read objects
            * `None` when operation is not finished yet (only for nonblocking mode).
        """
        
        status = self.getRequestStatus(client)        
        if status == ModbusClientPort.RequestStatus.Enable:
            # Prepare request buffer
            self._buff = bytearray(3)
            self._buff[0] = MBF_MEI_READ_DEVICE_ID # MEI type for Read Device Identification
            self._buff[1] = deviceId               # Read Device
            self._buff[2] = objectId               # Starting Object ID
            self._readDeviceIdCode = deviceId
            self._readDeviceIdObjectId = objectId
            status = ModbusClientPort.RequestStatus.Process        
        if status == ModbusClientPort.RequestStatus.Process:
            buff = self._request(unit, MBF_ENCAPSULATED_INTERFACE_TRANSPORT, self._buff)
            if buff is None:
                return None
            if self._isBroadcast():
                return dict()
            sz = len(buff)
            if sz < 6:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
            if buff[0] != MBF_MEI_READ_DEVICE_ID:
                self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect MEI type in response")
            #if buff[1] != self._readDeviceIdCode:
            #    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect device ID in response")
            conformityLevel = buff[2]
            moreFollows = bool(buff[3])
            nextObjectId = buff[4]
            #numberOfObjects = buff[5]
            objects = []
            self._setStatusCompleted(StatusCode.Status_Good)
            opos = 6
            while opos < sz:
                if opos + 2 > sz:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
                objId = buff[opos]
                objLen = buff[opos + 1]
                if opos + 2 + objLen > sz:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received data size")
                objData = bytes(buff[opos + 2 : opos + 2 + objLen])
                objects.append((objId, objData))
                opos += 2 + objLen
            # if len(objects) != numberOfObjects:
            #     self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Incorrect received number of objects")
            return {
                "conformityLevel": conformityLevel,
                "moreFollows": moreFollows,
                "nextObjectId": nextObjectId,
                "objects": tuple(objects)
            }
        else:
            return None
        
    def _request(self, unit: int, func: int, buff: bytes) -> StatusCode:
        """The function builds the packet that the write() function puts into the buffer.
        
        Args:
            unit: Modbus unit/slave address.
            func: Modbus function code.
            buff: Buffer containing the data to write.
            
        Returns:
            Status code of the operation.
        """
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if not self._isWriteBufferBlocked():
                self._unit = unit
                self._func = func
                self._lastTries = 0
                self._port.writeBuffer(unit, func, buff)
                self._blockWriteBuffer()
            r = StatusCode.Status_Good
            try:
                r = self._process()
                if r is None:
                    return None
            except ModbusException as e:
                self._repeats += 1
                #self._setPortError(e)
                if self._repeats < self._settings_tries:
                    self._port.setNextRequestRepeated(True)
                    if self._port.isNonBlocking():
                        return None
                    fRepeatAgain = True
                    continue
                self._setCompleted()
                raise e
            finally:
                if r is not None:
                    self._freeWriteBuffer()
                    self._repeats = 0
                    self._lastTries = self._repeats
                    self._currentClient = None
            if not self._isBroadcast():
                unit, func, buff = self._port.readBuffer()
                if unit != self._unit:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Not correct response. Requested unit (unit) is not equal to responsed")
                if func & MBF_EXCEPTION:
                    if func & 0x7f != self._func:
                        self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Not correct exception response. Requested function is not equal to responsed")
                    if len(buff) < 1:
                        self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Not correct exception response. Exception status missed")
                    self._raiseError(StatusCode.Status_Bad | buff[0], f"Modbus exception 0x{buff[0]:02X} received from server")
                if func != self._func:
                    self._raiseError(StatusCode.Status_BadNotCorrectResponse, "Not correct response. Requested function is not equal to responsed")
                return buff
            self._setStatus(StatusCode.Status_Good)
        return bytes()

    def _process(self) -> StatusCode:
        """The function processes the packet that the read() function puts into the buffer.
        """
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state == ModbusClientPort.State.STATE_UNKNOWN:
                if self._port.isOpen():
                    self._state = ModbusClientPort.State.STATE_OPENED
                else:
                    self._state = ModbusClientPort.State.STATE_CLOSED
                fRepeatAgain = True
                continue
            elif self._state in (ModbusClientPort.State.STATE_CLOSED,
                                 ModbusClientPort.State.STATE_BEGIN_OPEN):
                self._timestampRefresh()
                self._state = ModbusClientPort.State.STATE_WAIT_FOR_OPEN
                fRepeatAgain = True
                continue
            elif self._state == ModbusClientPort.State.STATE_WAIT_FOR_OPEN:
                try:
                    r = self._port.open()
                    if r is None:
                        return None
                except ModbusException as e:
                    #self.signalError.emit(self.getName(), e.code, str(e))
                    self._state = ModbusClientPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                self.signalOpened.emit(self.objectName())
                self._state = ModbusClientPort.State.STATE_OPENED
                fRepeatAgain = True
                continue
            elif self._state == ModbusClientPort.State.STATE_WAIT_FOR_CLOSE:
                try:
                    r = self._port.close()
                    if r is None:
                        return None
                except ModbusException as e:
                    #self.signalError.emit(self.getName(), e.code, str(e))
                    self._raisePortError(e)
                self.signalClosed.emit(self.objectName())
                self._state = ModbusClientPort.State.STATE_CLOSED
                return StatusCode.Status_Good
            elif self._state == ModbusClientPort.State.STATE_OPENED:
                if (self._port.isChanged()):
                    self._state = ModbusClientPort.State.STATE_WAIT_FOR_CLOSE
                else:
                    self._state = ModbusClientPort.State.STATE_BEGIN_WRITE
                fRepeatAgain = True
                continue
            elif self._state == ModbusClientPort.State.STATE_BEGIN_WRITE:
                self._timestampRefresh()
                if not self._port.isOpen():
                    self._state = ModbusClientPort.State.STATE_CLOSED
                else:
                    self._state = ModbusClientPort.State.STATE_WRITE
                fRepeatAgain = True
                continue
            elif self._state == ModbusClientPort.State.STATE_WRITE:
                try:
                    r = self._port.write()
                    if r is None:
                        return None
                except ModbusException as e:
                    #self.signalError.emit(self.getName(), e.code, str(e))
                    self._state = ModbusClientPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                else:
                    self.signalTx.emit(self.getName(), self._port.writeBufferData())
                    self._state = ModbusClientPort.State.STATE_BEGIN_READ
                self._setStatus(StatusCode.Status_Good)
                if (self._isBroadcast()):
                    self._state = ModbusClientPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                self._state = ModbusClientPort.State.STATE_BEGIN_READ
                fRepeatAgain = True
                continue
            elif self._state == ModbusClientPort.State.STATE_BEGIN_READ:
                self._timestampRefresh()
                self._state = ModbusClientPort.State.STATE_READ
                fRepeatAgain = True
                continue
            elif self._state == ModbusClientPort.State.STATE_READ:
                try:
                    r = self._port.read()
                    if r is None:
                        return None
                except ModbusException as e:
                    #self.signalError.emit(self.getName(), e.code, str(e))
                    self._state = ModbusClientPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                if not self._port.isOpen():
                    self.signalClosed.emit(self.objectName())
                    self._state = ModbusClientPort.State.STATE_CLOSED
                    return StatusCode.Status_Uncertain
                self.signalRx.emit(self.getName(), self._port.readBufferData())
                self._state = ModbusClientPort.State.STATE_OPENED
                return StatusCode.Status_Good
            elif self._state == ModbusClientPort.State.STATE_TIMEOUT:
                t = timer() - self._timestamp
                if t < self._port.timeout():
                    if (self._port.isBlocking()):
                        sleep((self._port.timeout() - t) / 1000.0)  # Sleep for remaining timeout
                    else:
                        return None
                self._state = ModbusClientPort.State.STATE_UNKNOWN
                fRepeatAgain = True
                continue
            else:
                if self._port.isOpen():
                    self._state = ModbusClientPort.State.STATE_OPENED
                else:
                    self._state = ModbusClientPort.State.STATE_CLOSED
                fRepeatAgain = True
                continue
        return None
    def _timestampRefresh(self):
        """Refreshes the internal timestamp to the current time."""
        self._timestamp = timer()  # Timestamp in milliseconds

    def _isBroadcast(self):
        return self._unit == 0 and self._isBroadcastEnabled()

    def _isStateClosed(self):
        return self._state == ModbusClientPort.State.STATE_CLOSED or self._state == ModbusClientPort.State.STATE_TIMEOUT

    def _isWriteBufferBlocked(self):
        return self._block

    def _blockWriteBuffer(self):
        self._block = True

    def _freeWriteBuffer(self):
        self._block = False

    def _setStatus(self, status: StatusCode):
        """Sets the status parameters of the last operation performed.
        
        Args:
            status: StatusCode of the last operation.
        """
        self._lastStatus = status
        self._lastStatusTimestamp = currentTimestamp()  

    def _setStatusCompleted(self, status: StatusCode):
        """Sets the status parameters of the last operation performed as completed.
        
        Args:
            status: StatusCode of the completed operation.
        """
        self._setStatus(status)
        self._setCompleted()

    def _setCompleted(self):
        """Sets the state of the last operation performed as completed.
        """
        self._currentClient = None

    def _setError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._isLastPortError = False
        self._setErrorBase(exc, text)

    def _raiseError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed and raises the exception.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._isLastPortError = False
        self._setCompleted()
        self._raiseErrorBase(exc, text)

    def _setPortError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed.
        
        Args:
            status: StatusCode of the last error.
            text: Text description of the error (optional).
        """
        self._isLastPortError = True
        self._setErrorBase(exc, text)

    def _raisePortError(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed and raises the exception.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._isLastPortError = True
        self._raiseErrorBase(exc, text)

    def _setErrorBase(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        if isinstance(exc, ModbusException):
            self._lastErrorStatus = exc.code
            self._lastErrorText = exc.message
        elif isinstance(exc, type) and issubclass(exc, ModbusException):
            self._lastErrorStatus = exc.code
            self._lastErrorText = text
        else: # `exc` must be integer or instance of StatusCode
            self._lastErrorStatus = exc
            self._lastErrorText = text
        self._setStatus(self._lastErrorStatus)
        self.signalError.emit(self.getName(), self._lastErrorStatus, self._lastErrorText)

    def _raiseErrorBase(self, exc, text: str = ""):
        """Sets the error parameters of the last operation performed and raises the exception.
        
        Args:
            exc: Type of the ModbusException to raise.
            text: Text description of the error (optional).
        """
        self._setErrorBase(exc, text)
        rexc = None
        if isinstance(exc, ModbusException):
            rexc = exc
        elif isinstance(exc, type) and issubclass(exc, ModbusException):
            rexc = exc(text)
        else: # `exc` must be integer or instance of StatusCode
            rexc = getException(exc, text)
        raise rexc

class ModbusAsyncClientPort(ModbusClientPort):
    """Asynchronous Modbus client port implementation.
    """

    def __init__(self, port: ModbusPort):
        """Initializes the ModbusAsyncClientPort instance.

        Args:
            port: The ModbusPort instance to use for communication.
        """
        if port.isBlocking():
            port.setBlocking(False)
        super().__init__(port)

    def open(self) -> StatusCode:
        return AwaitableMethod(super().open)
    
    def close(self) -> StatusCode:
        return AwaitableMethod(super().close)
    
    def readCoils(self, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super().readCoils, unit, offset, count)
    
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super().readDiscreteInputs, unit, offset, count)

    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super().readHoldingRegisters, unit, offset, count)

    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super().readInputRegisters, unit, offset, count)

    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode:
        return AwaitableMethod(super().writeSingleCoil, unit, offset, value)

    def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode:
        return AwaitableMethod(super().writeSingleRegister, unit, offset, value)

    def readExceptionStatus(self, unit: int) -> bytes:
        return AwaitableMethod(super().readExceptionStatus, unit)

    def diagnosticsReturnQueryData(self, unit: int, indata: Optional[bytes] = None) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnQueryData, unit, indata)
        
    def diagnosticsRestartCommunicationsOption(self, unit: int, clearEventLog: bool) -> StatusCode:
        return AwaitableMethod(super().diagnosticsRestartCommunicationsOption, unit, clearEventLog)
        
    def diagnosticsReturnDiagnosticRegister(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnDiagnosticRegister, unit)
        
    def diagnosticsChangeAsciiInputDelimiter(self, unit: int, delimiter: int) -> StatusCode:
        return AwaitableMethod(super().diagnosticsChangeAsciiInputDelimiter, unit, delimiter)

    def diagnosticsForceListenOnlyMode(self, unit: int) -> StatusCode:
        return AwaitableMethod(super().diagnosticsForceListenOnlyMode, unit)
    
    def diagnosticsClearCountersAndDiagnosticRegister(self, unit: int) -> StatusCode:
        return AwaitableMethod(super().diagnosticsClearCountersAndDiagnosticRegister, unit)

    def diagnosticsReturnBusMessageCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnBusMessageCount, unit)

    def diagnosticsReturnBusCommunicationErrorCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnBusCommunicationErrorCount, unit)

    def diagnosticsReturnBusExceptionErrorCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnBusExceptionErrorCount, unit)

    def diagnosticsReturnServerMessageCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnServerMessageCount, unit)

    def diagnosticsReturnServerNoResponseCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnServerNoResponseCount, unit)

    def diagnosticsReturnServerNAKCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnServerNAKCount, unit)
    
    def diagnosticsReturnServerBusyCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnServerBusyCount, unit)

    def diagnosticsReturnBusCharacterOverrunCount(self, unit: int) -> bytes:
        return AwaitableMethod(super().diagnosticsReturnBusCharacterOverrunCount, unit)
        
    def getCommEventCounter(self, unit: int) -> bytes:
        return AwaitableMethod(super().getCommEventCounter, unit)

    def getCommEventLog(self, unit: int) -> bytes:
        return AwaitableMethod(super().getCommEventLog, unit)
        
    def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode:
        return AwaitableMethod(super().writeMultipleCoils, unit, offset, values, count)
        
    def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode:
        return AwaitableMethod(super().writeMultipleRegisters, unit, offset, values)
        
    def reportServerID(self, unit: int) -> bytes:
        return AwaitableMethod(super().reportServerID, unit)

    def readFileRecord(self, unit: int, records: Collection) -> Tuple:
        return AwaitableMethod(super().readFileRecord, unit, records)
        
    def writeFileRecord(self, unit: int, records: Collection) -> StatusCode:
        return AwaitableMethod(super().writeFileRecord, unit, records)
        
    def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode:
        return AwaitableMethod(super().maskWriteRegister, unit, offset, andMask, orMask)

    def readWriteMultipleRegisters(self, unit: int,
                                   readOffset: int, readCount: int,
                                   writeOffset: int, writeValues: bytes) -> bytes:
        return AwaitableMethod(super().readWriteMultipleRegisters, unit,
                         readOffset, readCount,
                         writeOffset, writeValues)

    def readFIFOQueue(self, unit: int, fifoadr: int) -> bytes:
        return AwaitableMethod(super().readFIFOQueue, unit, fifoadr)
    
    def readDeviceIdentification(self, unit: int, deviceId: int, objectId: int) -> dict:
        return AwaitableMethod(super().readDeviceIdentification, unit, deviceId, objectId)

    # formatting methods
    def readCoilsF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super().readCoilsF, unit, offset, count, fmt=fmt)

    def readDiscreteInputsF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super().readDiscreteInputsF, unit, offset, count, fmt=fmt)

    def readHoldingRegistersF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super().readHoldingRegistersF, unit, offset, count, fmt=fmt)

    def readInputRegistersF(self, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super().readInputRegistersF, unit, offset, count, fmt=fmt)

    def writeMultipleCoilsF(self, unit: int, offset: int, values: Tuple, count: int = -1, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return AwaitableMethod(super().writeMultipleCoilsF, unit, offset, values, count, fmt=fmt)
    
    def writeMultipleRegistersF(self, unit: int, offset: int, values: Tuple, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return AwaitableMethod(super().writeMultipleRegistersF, unit, offset, values, fmt=fmt)
    
    def readWriteMultipleRegistersF(self, unit: int,
                                    readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: Tuple,
                                    fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super().readWriteMultipleRegistersF, unit,
                               readOffset, readCount,
                               writeOffset, writeValues,
                               fmt=fmt)

    # low-level methods
    def _readCoils(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super()._readCoils, client, unit, offset, count)
    
    def _readDiscreteInputs(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super()._readDiscreteInputs, client, unit, offset, count)

    def _readHoldingRegisters(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super()._readHoldingRegisters, client, unit, offset, count)

    def _readInputRegisters(self, client:ModbusObject, unit: int, offset: int, count: int) -> bytes:
        return AwaitableMethod(super()._readInputRegisters, client, unit, offset, count)

    def _writeSingleCoil(self, client:ModbusObject, unit: int, offset: int, value: bool) -> StatusCode:
        return AwaitableMethod(super()._writeSingleCoil, client, unit, offset, value)

    def _writeSingleRegister(self, client:ModbusObject, unit: int, offset: int, value: int) -> StatusCode:
        return AwaitableMethod(super()._writeSingleRegister, client, unit, offset, value)

    def _readExceptionStatus(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._readExceptionStatus, client, unit)

    def _diagnosticsReturnQueryData(self, client:ModbusObject, unit: int, indata: bytes) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnQueryData, client, unit, indata)
        
    def _diagnosticsRestartCommunicationsOption(self, client:ModbusObject, unit: int, clearEventLog: bool) -> StatusCode:
        return AwaitableMethod(super()._diagnosticsRestartCommunicationsOption, client, unit, clearEventLog)
        
    def _diagnosticsReturnDiagnosticRegister(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnDiagnosticRegister, client, unit)
        
    def _diagnosticsChangeAsciiInputDelimiter(self, client:ModbusObject, unit: int, delimiter: int) -> StatusCode:
        return AwaitableMethod(super()._diagnosticsChangeAsciiInputDelimiter, client, unit, delimiter)

    def _diagnosticsForceListenOnlyMode(self, client:ModbusObject, unit: int) -> StatusCode:
        return AwaitableMethod(super()._diagnosticsForceListenOnlyMode, client, unit)
    
    def _diagnosticsClearCountersAndDiagnosticRegister(self, client:ModbusObject, unit: int) -> StatusCode:
        return AwaitableMethod(super()._diagnosticsClearCountersAndDiagnosticRegister, client, unit)

    def _diagnosticsReturnBusMessageCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnBusMessageCount, client, unit)

    def _diagnosticsReturnBusCommunicationErrorCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnBusCommunicationErrorCount, client, unit)

    def _diagnosticsReturnBusExceptionErrorCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnBusExceptionErrorCount, client, unit)

    def _diagnosticsReturnServerMessageCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnServerMessageCount, client, unit)

    def _diagnosticsReturnServerNoResponseCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnServerNoResponseCount, client, unit)

    def _diagnosticsReturnServerNAKCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnServerNAKCount, client, unit)

    def _diagnosticsReturnServerBusyCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnServerBusyCount, client, unit)

    def _diagnosticsReturnBusCharacterOverrunCount(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._diagnosticsReturnBusCharacterOverrunCount, client, unit)
        
    def _getCommEventCounter(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._getCommEventCounter, client, unit)

    def _getCommEventLog(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._getCommEventLog, client, unit)
        
    def _writeMultipleCoils(self, client:ModbusObject, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode:
        return AwaitableMethod(super()._writeMultipleCoils, client, unit, offset, values, count)
        
    def _writeMultipleRegisters(self, client:ModbusObject, unit: int, offset: int, values: bytes) -> StatusCode:
        return AwaitableMethod(super()._writeMultipleRegisters, client, unit, offset, values)
        
    def _reportServerID(self, client:ModbusObject, unit: int) -> bytes:
        return AwaitableMethod(super()._reportServerID, client, unit)
        
    def _readFileRecord(self, client:ModbusObject, unit: int, records: Collection) -> Tuple:
        return AwaitableMethod(super()._readFileRecord, client, unit, records)
        
    def _writeFileRecord(self, client:ModbusObject, unit: int, records: Collection) -> StatusCode:
        return AwaitableMethod(super()._writeFileRecord, client, unit, records)
        
    def _maskWriteRegister(self, client:ModbusObject, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode:
        return AwaitableMethod(super()._maskWriteRegister, client, unit, offset, andMask, orMask)

    def _readWriteMultipleRegisters(self, client:ModbusObject, unit: int,
                                   readOffset: int, readCount: int,
                                   writeOffset: int, writeValues: bytes) -> bytes:
        return AwaitableMethod(super()._readWriteMultipleRegisters, client, unit,
                               readOffset, readCount,
                               writeOffset, writeValues)

    def _readFIFOQueue(self, client:ModbusObject, unit: int, fifoadr: int) -> bytes:
        return AwaitableMethod(super()._readFIFOQueue, client, unit, fifoadr)
    
    def _readDeviceIdentification(self, client:ModbusObject, unit: int, deviceId: int, objectId: int) -> dict:
        return AwaitableMethod(super()._readDeviceIdentification, client, unit, deviceId, objectId)

    # low-level formatting methods
    def _readCoilsF(self, client:ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super()._readCoilsF, client, unit, offset, count, fmt=fmt)

    def _readDiscreteInputsF(self, client:ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super()._readDiscreteInputsF, client, unit, offset, count, fmt=fmt)
    
    def _readHoldingRegistersF(self, client:ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super()._readHoldingRegistersF, client, unit, offset, count, fmt=fmt)

    def _readInputRegistersF(self, client:ModbusObject, unit: int, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super()._readInputRegistersF, client, unit, offset, count, fmt=fmt)

    def _writeMultipleCoilsF(self, client:ModbusObject, unit: int, offset: int, values: Tuple, count: int = -1, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return AwaitableMethod(super()._writeMultipleCoilsF, client, unit, offset, values, count, fmt=fmt)
    
    def _writeMultipleRegistersF(self, client:ModbusObject, unit: int, offset: int, values: Tuple, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return AwaitableMethod(super()._writeMultipleRegistersF, client, unit, offset, values, fmt=fmt)
    
    def _readWriteMultipleRegistersF(self, client:ModbusObject, unit: int,
                                    readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: Tuple,
                                    fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return AwaitableMethod(super()._readWriteMultipleRegistersF, client, unit,
                               readOffset, readCount,
                               writeOffset, writeValues,
                               fmt=fmt)
