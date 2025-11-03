"""
ModbusPort.py - Contains client definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from typing import Optional
from .ModbusStatusCode import StatusCode
from .ModbusObject import ModbusObject
from .ModbusClientPort import ModbusClientPort

class ModbusClient(ModbusObject):
    """Base class for Modbus clients"""

    def __init__(self, unit: int, port: ModbusClientPort):
        self._unit = unit
        self._port = port

    def unit(self) -> int:
        """Returns the unit identifier of the Modbus client"""
        return self._unit

    def setUnit(self, unit: int):
        """Sets the unit identifier of the Modbus client"""
        self._unit = unit

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

    def readExceptionStatus(self) -> bytes:
        return self._port._readExceptionStatus(self, self._unit)

    def diagnostics(self, subfunc: int, indata: Optional[bytes] = None) -> bytes:
        return self._port._diagnostics(self, self._unit, subfunc, indata)

    def getCommEventCounter(self) -> bytes:
        return self._port._getCommEventCounter(self, self._unit)

    def getCommEventLog(self) -> bytes:
        return self._port._getCommEventLog(self, self._unit)

    def writeMultipleCoils(self, offset: int, count: int, values: bytes) -> bool:
        return self._port.writeMultipleCoils(self, self._unit, offset, count, values)

    def writeMultipleRegisters(self, offset: int, count: int, values: bytes) -> bool:
        return self._port._writeMultipleRegisters(self, self._unit, offset, count, values)

    def reportServerID(self) -> bytes:
        return self._port._reportServerID(self, self._unit)

    def maskWriteRegister(self, offset: int, andMask: int, orMask: int) -> bool:
        return self._port.maskWriteRegister(self, self._unit, offset, andMask, orMask)

    def readWriteMultipleRegisters(self, readOffset: int, readCount: int,
                                    writeOffset: int, writeCount: int, writeValues: bytes) -> bytes:
        return self._port._readWriteMultipleRegisters(self, self._unit, readOffset, readCount,
                                                     writeOffset, writeCount, writeValues)
        
    def readFIFOQueue(self, fifoadr: int) -> bytes:
        return self._port._readFIFOQueue(self, self._unit, fifoadr)

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