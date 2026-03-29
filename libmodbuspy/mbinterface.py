"""
@file mbinterface.py
@brief Main interface of Modbus communication protocol.

This module defines the main interface for Modbus communication,
including the supported function codes and their corresponding methods.
This interface serves as a base class for implementing Modbus clients and servers.
The class provides a standardized interface for both synchronous and asynchronous
Modbus operations, supporting all standard Modbus function codes defined in the
specification.

All methods can operate in blocking or non-blocking mode depending on the implementation.
In non-blocking mode, methods may return `None` to indicate that the operation is
still in progress.

The interface follows the Modbus specification and uses 0-based addressing internally,
though implementations may provide 1-based addressing options for compatibility.

Data is returned as raw bytes objects, allowing flexibility in how the data is
interpreted by the calling code. Register data uses little-endian byte ordering
for consistency across different platforms.

@author serhmarch
@date November 2025
"""

from . import exceptions
from .statuscode import StatusCode

class ModbusInterface:
    """Main interface of Modbus communication protocol.
    
    `ModbusInterface` contains list of functions that is supported by libmodbuspy library.

    There are such functions as:
    * 1  (0x01) - `READ_COILS`
    * 2  (0x02) - `READ_DISCRETE_INPUTS`
    * 3  (0x03) - `READ_HOLDING_REGISTERS`
    * 4  (0x04) - `READ_INPUT_REGISTERS`
    * 5  (0x05) - `WRITE_SINGLE_COIL`
    * 6  (0x06) - `WRITE_SINGLE_REGISTER`
    * 7  (0x07) - `READ_EXCEPTION_STATUS`
    * 8  (0x08) - `DIAGNOSTICS`
    * 11 (0x0B) - `GET_COMM_EVENT_COUNTER`
    * 12 (0x0C) - `GET_COMM_EVENT_LOG`
    * 15 (0x0F) - `WRITE_MULTIPLE_COILS`
    * 16 (0x10) - `WRITE_MULTIPLE_REGISTERS`
    * 17 (0x11) - `REPORT_SERVER_ID`
    * 20 (0x14) - `READ_FILE_RECORD`
    * 21 (0x15) - `WRITE_FILE_RECORD`
    * 22 (0x16) - `MASK_WRITE_REGISTER`
    * 23 (0x17) - `READ_WRITE_MULTIPLE_REGISTERS`
    * 24 (0x18) - `READ_FIFO_QUEUE`
    * 43 (0x2B) - `ENCAPSULATED_INTERFACE_TRANSPORT` (Read Device Identification, MEI type 0x0E)
    
    Each method returns `StatusCode` for result.
    Default implementations raises `exceptions.IllegalFunctionError`.
    """
    
    def readCoils(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read discrete outputs (coils, 0x bits).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of coils (bits).
            
        Returns:
            * `bytes` object that is a bit array for read values.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
    
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read digital inputs (1x bits).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of inputs (bits).
            
        Returns:
            * `bytes` object that is a bit array for read values.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read holding (output) 16-bit registers (4x regs).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of registers.
            
        Returns:
            * `bytes` object that is uint16 (little-endian) array for read values.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes:
        """Function for read input 16-bit registers (3x regs).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of registers.
            
        Returns:
            * `bytes` object that is uint16 (little-endian) array for read values.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode:
        """Function for write one separate discrete output (0x coil).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            value: Boolean value to be set.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode:
        """Function for write one separate 16-bit holding register (4x).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            value: 16-bit unsigned integer value to be set.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def readExceptionStatus(self, unit: int) -> bytes:
        """Function to read ExceptionStatus.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array with single byte that containing the exception status.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnQueryData(self, unit: int, indata: bytes) -> bytes:
        """Diagnostics subfunction provides an echo of the supplied data.
        
        Args:
            unit: Address of the remote Modbus device.
            indata: Input data buffer for the diagnostic function.
            
        Returns:
            * `bytes` array containing the response data.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsRestartCommunicationsOption(self, unit: int, clearEventLog: bool) -> StatusCode:
        """Diagnostics subfunction restart communication and clears all of device's event counters.
        
        Args:
            unit: Address of the remote Modbus device.
            clearEventLog: Boolean flag to clear the event log.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnDiagnosticRegister(self, unit: int) -> bytes:
        """Diagnostics subfunction returns contents of the remote device's 16-bit diagnostic register.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsChangeAsciiInputDelimiter(self, unit: int, delimiter: int) -> StatusCode:
        """Diagnostics subfunction sets the character `delimiter` as the end of message delimiter.
        
        Args:
            unit: Address of the remote Modbus device.
            delimiter: ASCII character to be set as the end of message delimiter.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsForceListenOnlyMode(self, unit: int) -> StatusCode:
        """Diagnostics subfunction forces the addressed remote device to its Listen Only Mode for MODBUS communications.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsClearCountersAndDiagnosticRegister(self, unit: int) -> StatusCode:
        """Diagnostics subfunction clear all counters and the diagnostic register.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnBusMessageCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages that the remote device has detected
        on the communications system since its last restart, clear counters operation, or power –up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnBusCommunicationErrorCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of CRC errors encountered by the remote device
        since its last restart, clear counters operation, or power-up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnBusExceptionErrorCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of MODBUS exception responses returned by the
        remote device since its last restart, clear counters operation, or power-up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnServerMessageCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device, or
        broadcast, that the remote device has processed since its last restart, clear counters operation, or power-up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnServerNoResponseCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device for
        which it has returned no response (neither a normal response nor an exception response),
        since its last restart, clear counters operation, or power-up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnServerNAKCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device for
        which it returned a Negative Acknowledge (NAK) exception response, since its last restart,
        clear counters operation, or power-up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnServerBusyCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device for
        which it returned a Server Device Busy exception response, since its last restart, clear
        counters operation, or power-up.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsReturnBusCharacterOverrunCount(self, unit: int) -> bytes:
        """Diagnostics subfunction returns the quantity of messages addressed to the remote device that
        it could not handle due to a character overrun condition, since its last restart, clear counters
        operation, or power-up. A character overrun is caused by data characters arriving at the port
        faster than they can be stored, or by the loss of a character due to a hardware malfunction.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array of size 2 containing the register value.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def diagnosticsClearOverrunCounterAndFlag(self, unit: int) -> StatusCode:
        """Diagnostics subfunction clears the overrun error counter and reset the error flag.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def getCommEventCounter(self, unit: int) -> bytes:
        """Function is used to get a status word and an event count from the
        remote device's communication event counter.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array containing 2 uint16 (little-endian) values:
               * status word
               * event counter
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def getCommEventLog(self, unit: int) -> bytes:
        """Function is used to get a status word, event count, message count and event log
        from the remote device's communication event counter.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array containing values:
               * status word (uint16, little-endian)
               * event counter (uint16, little-endian)
               * message count (uint16, little-endian)
               * event log (each event is one byte)
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode:
        """Function for write coils (discrete outputs, 1-bit values) (0x data).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            values: Input buffer (bit array) which values must be written.
            count: Count of coils (bits). If `count` parameter is ommited (or =-1),
                   the count is calculated from the length of `values` buffer
                   as `count = len(values) * 8`.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode:
        """Function for write holding (output) 16-bit registers (4x regs).
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            count: Count of registers.
            values: Input buffer which values must be written.
            
        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")
        
    def reportServerID(self, unit: int) -> bytes:
        """Function to read the description of the type, the current status,
        and other information specific to a remote device.
        
        Args:
            unit: Address of the remote Modbus device.
            
        Returns:
            * `bytes` array that represents the server ID.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

    def readFileRecord(self, unit: int, records: list) -> list:
        """Function is used to read one or more file records from a remote device.
        
        Args:
            unit: Address of the remote Modbus device.
            records: list of records to read, where each record is
                     a dict of keys "fileNumber", "recordNumber", "recordLength".

        Returns:
            * `list` of bytes array that represents the requested file records data.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

    def writeFileRecord(self, unit: int, records: list) -> StatusCode:
        """Function is used to write one or more file records to a remote device.
        
        Args:
            unit: Address of the remote Modbus device.
            records: list of records to write, where each record is
                     a dict of keys "fileNumber", "recordNumber", "recordData".

        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

    def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode:
        """Function is used to modify the contents of a specified holding register
        using a combination of an AND mask, an OR mask, and the register's current contents.
        The function's algorithm is:
        Result = (Current Contents AND And_Mask) OR (Or_Mask AND (NOT And_Mask))
        
        Args:
            unit: Address of the remote Modbus device.
            offset: Starting offset (0-based).
            andMask: 16-bit unsigned integer value AND mask.
            orMask: 16-bit unsigned integer value OR mask.

        Returns:
            * The result StatusCode of the operation.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

    def readWriteMultipleRegisters(self, unit: int,
                                   readOffset: int, readCount: int,
                                   writeOffset: int, writeValues: bytes) -> bytes:
        """This function code performs a combination of one read operation and one
        write operation in a single MODBUS transaction.
        
        Args:
            unit: Address of the remote Modbus device.
            read_offset: Starting offset for read (0-based).
            read_count: Count of registers to read.
            write_offset: Starting offset for write (0-based).
            write_count: Count of registers to write.
            write_values: Input buffer which values must be written.
            
        Returns:
            * `bytes` object that is uint16 (little-endian) array for read values.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

    def readFIFOQueue(self, unit: int, fifoadr: int) -> bytes:
        """Function for read the contents of a First-In-First-Out (FIFO) queue
        of register in a remote device.
        
        Args:
            unit: Address of the remote Modbus device.
            fifoadr: Address of FIFO (0-based).
            
        Returns:
            * `bytes` object that is uint16 (little-endian) array for FIFO values.
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

    def readDeviceIdentification(self, unit: int, deviceId: int, objectId: int) -> dict:
        """Function for Read Device Identification, FC43 (0x2B), MEI type 14 (0x0E).
        Reads identity objects (vendor name, product code, revision, etc.) from a remote device.
        The response is returned as list of tuples containing (objectId:int, objectData:bytes).
        
        Args:
            unit: Address of the remote Modbus device.
            deviceId: Read Device ID code: 1=Basic, 2=Regular, 3=Extended, 4=Specific.
            objectId: Starting object ID to read from (0x00-0xFF).

        Returns:
            * `dict` of values representing the requested device identification:
                - "conformityLevel" - Conformity level of the device
                - "moreFollows" - Boolean flag indicating if more objects follow
                - "nextObjectId" - Next object ID to read (if moreFollows is True)
                - "objects" - list of tuples (objectId:int, objectData:bytes) for read objects
            * `None` when operation is not finished yet (only for nonblocking mode).

        Raises:
            Exceptions with base class `libmodbuspy.ModbusException` on error.
        """
        raise exceptions.IllegalFunctionError("Function not supported")

