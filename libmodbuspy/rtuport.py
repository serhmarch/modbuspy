"""
ModbusRtuPort.py - Contains RTU port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from .serialport import ModbusSerialPort
from .mbglobal import ProtocolType, crc16
from . import exceptions


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
    
    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. For ModbusRtuPort returns RTU."""
        return ProtocolType.RTU

    def writeBuffer(self, unit: int, func: int, data: bytes):
        buff = self._buff
        buff.clear()
        # save request data for future compare
        self._unit = unit
        self._func = func
        # unit, function, data
        buff.append(unit)
        buff.append(func)
        buff.extend(data)
        # calculate CRC16
        crc = crc16(buff)
        buff.extend(crc.to_bytes(2, 'little'))  # append CRC16 (2 bytes)
        return True


    def readBuffer(self):
        buff = self._buff
        sz = len(buff)
        # Check minimum size (unit + function + CRC16)
        if sz < 4:
            self._raiseError(exceptions.NotCorrectResponseError, "RTU. Not correct input. Input data length is too small")
        # Check CRC16
        crc = buff[sz-2] | (buff[sz-1] << 8)
        if crc16(buff[:sz-2]) != crc:
            return self._raiseError(exceptions.NotCorrectResponseError, "RTU. Wrong CRC")
        # Prepare output data
        unit = buff[0]
        func = buff[1]
        return unit, func, buff[2:sz-2]
