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
    *  1 (0x01) - `READ_COILS`
    *  2 (0x02) - `READ_DISCRETE_INPUTS`  
    *  3 (0x03) - `READ_HOLDING_REGISTERS`
    *  4 (0x04) - `READ_INPUT_REGISTERS`
    *  5 (0x05) - `WRITE_SINGLE_COIL`
    *  6 (0x06) - `WRITE_SINGLE_REGISTER`
    *  7 (0x07) - `READ_EXCEPTION_STATUS`
    *  8 (0x08) - `DIAGNOSTICS`
    * 11 (0x0B) - `GET_COMM_EVENT_COUNTER`
    * 12 (0x0C) - `GET_COMM_EVENT_LOG`
    * 15 (0x0F) - `WRITE_MULTIPLE_COILS`
    * 16 (0x10) - `WRITE_MULTIPLE_REGISTERS`
    * 17 (0x11) - `REPORT_SERVER_ID`
    * 22 (0x16) - `MASK_WRITE_REGISTER`
    * 23 (0x17) - `READ_WRITE_MULTIPLE_REGISTERS`
    * 24 (0x18) - `READ_FIFO_QUEUE`
    
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
        
    def diagnostics(self, unit: int, subfunc: int, indata: bytes) -> bytes:
        """Function provides a series of tests for checking the communication system
        between a client device and a server, or for checking various internal error
        conditions within a server.
        
        Args:
            unit: Address of the remote Modbus device.
            subfunc: Subfunction code.
            indata: Input data buffer for the diagnostic function.
            
        Returns:
            * `bytes` array containing the response data.
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

