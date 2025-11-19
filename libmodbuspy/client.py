"""
ModbusPort.py - Contains client definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from typing import Optional, Tuple
from .statuscode import StatusCode
from .mbglobal import MB_FMT_UINT16_LE
from .mbobject import ModbusObject
from .clientport import ModbusClientPort

class ModbusClient(ModbusObject):
    """Base class for Modbus clients

    Client objects is wrapper around ModbusClientPort instances
    to simplify usage of ModbusClientPort methods
    reducing the number of parameters needed to call them.
    ModbusClient holds the unit identifier of the Modbus device
    to which it is connected.

    Also ModbusClient can be used
    as a way to simultaneously poll 2 or more Modbus devices
    that are located in the same Modbus network
    (e.g. on the same RS485 bus).

    c1 = ModbusClient(1, clientPort)
    c2 = ModbusClient(2, clientPort)
    """

    def __init__(self, unit: int, port: ModbusClientPort):
        self._unit = unit
        self._port = port

    def unit(self) -> int:
        """Returns the unit identifier of the Modbus client"""
        return self._unit

    def setUnit(self, unit: int):
        """Sets the unit identifier of the Modbus client"""
        self._unit = unit

    @property
    def Unit(self) -> int:
        """Property. Get the unit identifier."""
        return self.unit()

    @Unit.setter
    def Unit(self, unit: int):
        """Property. Set the unit identifier."""
        return self.setUnit(unit)

    def port(self) -> ModbusClientPort:
        """Returns the Modbus client port instance"""
        return self._port
    
    def readCoils(self, offset: int, count: int) -> bytes:
        return self._port._readCoils(self, self._unit, offset, count)
    
    def readDiscreteInputs(self, offset: int, count: int) -> bytes:
        return self._port._readDiscreteInputs(self, self._unit, offset, count)

    def readHoldingRegisters(self, offset: int, count: int) -> bytes:
        return self._port._readHoldingRegisters(self, self._unit, offset, count)

    def readInputRegisters(self, offset: int, count: int) -> bytes:
        return self._port._readInputRegisters(self, self._unit, offset, count)

    def writeSingleCoil(self, offset: int, value: bool) -> bool:
        return self._port._writeSingleCoil(self, self._unit, offset, value)

    def writeSingleRegister(self, offset: int, value: int) -> bool:
        return self._port._writeSingleRegister(self, self._unit, offset, value)

    def readExceptionStatus(self) -> int:
        return self._port._readExceptionStatus(self, self._unit)

    def diagnostics(self, subfunc: int, indata: Optional[bytes] = None) -> bytes:
        return self._port._diagnostics(self, self._unit, subfunc, indata)

    def getCommEventCounter(self) -> int:
        return self._port._getCommEventCounter(self, self._unit)

    def getCommEventLog(self) -> bytes:
        return self._port._getCommEventLog(self, self._unit)

    def writeMultipleCoils(self, offset: int, values: bytes, count: int = -1) -> bool:
        return self._port._writeMultipleCoils(self, self._unit, offset, values, count)

    def writeMultipleRegisters(self, offset: int, values: bytes) -> bool:
        return self._port._writeMultipleRegisters(self, self._unit, offset, values)

    def reportServerID(self) -> bytes:
        return self._port._reportServerID(self, self._unit)

    def maskWriteRegister(self, offset: int, andMask: int, orMask: int) -> bool:
        return self._port._maskWriteRegister(self, self._unit, offset, andMask, orMask)

    def readWriteMultipleRegisters(self, readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: bytes) -> bytes:
        return self._port._readWriteMultipleRegisters(self, self._unit, readOffset, readCount,
                                                      writeOffset, writeValues)
        
    def readFIFOQueue(self, fifoadr: int) -> bytes:
        return self._port._readFIFOQueue(self, self._unit, fifoadr)

    # formatting methods
    def readCoilsF(self, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._port._readCoilsF(self, self._unit, offset, count, fmt=fmt)

    def readDiscreteInputsF(self, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._port._readDiscreteInputsF(self, self._unit, offset, count, fmt=fmt)

    def readHoldingRegistersF(self, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._port._readHoldingRegistersF(self, self._unit, offset, count, fmt=fmt)

    def readInputRegistersF(self, offset: int, count: int, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._port._readInputRegistersF(self, self._unit, offset, count, fmt=fmt)

    def writeMultipleCoilsF(self, offset: int, values: Tuple, count: int = -1, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return self._port._writeMultipleCoilsF(self, self._unit, offset, values, count, fmt=fmt)
    
    def writeMultipleRegistersF(self, offset: int, values: Tuple, fmt: str=MB_FMT_UINT16_LE) -> StatusCode:
        return self._port._writeMultipleRegistersF(self, self._unit, offset, values, fmt=fmt)
    
    def readWriteMultipleRegistersF(self, readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: Tuple, fmt: str=MB_FMT_UINT16_LE) -> Tuple:
        return self._port._readWriteMultipleRegistersF(self, self._unit,
                                                       readOffset, readCount,
                                                       writeOffset, writeValues,
                                                       fmt=fmt)
    
    # Port status methods
    
    def lastPortStatus(self) -> StatusCode:
        """Returns the status of the last operation performed.
        
        Returns:
            StatusCode of the last port operation.
        """
        return self._port.lastStatus()

    def lastPortErrorStatus(self) -> StatusCode:
        """Returns the status of the last error of the performed operation.
        
        Returns:
            StatusCode of the last port error.
        """
        return self._port.lastErrorStatus()

    def lastPortErrorText(self) -> str:
        """Returns text representation of the last error of the performed operation.
        
        Returns:
            Text description of the last port error.
        """
        return self._port.lastErrorText()
    