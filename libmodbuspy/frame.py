"""
frame.py - Contains frame definitions of the Modbus library for Python.

Author: serhmarch
Date: May 2026
"""

from abc import ABC, abstractmethod
from typing import Tuple
from .statuscode import StatusCode
from .mbglobal import  crc16, lrc, bytesToAscii, asciiToBytes
from . import exceptions

class ModbusFrame(ABC):
    """
    Abstract base class for Modbus frames.
    """

    def __init__(self):
        self._modeServer = False
        self._errorStatus = StatusCode.Status_Good
        self._errorText = ""
        self._buff = bytearray()

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

class ModbusAscFrame(ModbusFrame):
    """
    Modbus ASCII frame implementation.
    """
    def writeBuffer(self, unit: int, func: int, data: bytes):
        # save request data for future compare
        self._unit = unit
        self._func = func
        # unit, function, data
        ibuff = bytearray()
        ibuff.append(unit)
        ibuff.append(func)
        ibuff.extend(data)
        # calculate LRC
        LRC = lrc(ibuff)
        ibuff.append(LRC)
        buff = self._buff
        buff.clear()
        # start delimiter
        buff.append(ord(':'))
        buff.extend(bytesToAscii(ibuff))
        # end delimiters CR LF
        buff.append(ord('\r'))  # CR
        buff.append(ord('\n'))  # LF
        return True


    def readBuffer(self):
        buff = self._buff
        sz = len(buff)
        if sz < 9:  # Note: 9 = 1(':')+2(unit)+2(func)+2(lrc)+1('\r')+1('\n')
            self._raiseError(exceptions.NotCorrectResponseError, "ASCII. Not correct response. Responsed data length to small")

        # Verify start colon (compare to ord(':') because buffer is bytes/ints)
        if buff[0] != ord(':'):
            self._raiseError(exceptions.AscMissColonError, "ASCII. Missed colon ':' symbol")

        # Verify CR LF ending (buffer contains integer byte values)
        if buff[sz-2] != ord('\r') or buff[sz-1] != ord('\n'):
            self._raiseError(exceptions.AscMissCrLfError, "ASCII. Missed CR-LF ending symbols")

        # Convert ASCII hex payload to binary (without ':' and CRLF)
        try:
            ibuff = asciiToBytes(buff[1:sz-2])
        except Exception:
            self._raiseError(exceptions.AscCharError, "ASCII. Bad ASCII symbol")
        if len(ibuff) == 0:
            self._raiseError(exceptions.AscCharError, "ASCII. Bad ASCII symbol")

        # Check LRC: last byte of ibuff is LRC
        if lrc(ibuff[:-1]) != ibuff[-1]:
            self._raiseError(exceptions.LrcError, "ASCII. Error LRC")

        # Prepare output data
        unit = ibuff[0]
        func = ibuff[1]
        return unit, func, ibuff[2:-1] # without unit, func and LRC


class ModbusRtuFrame(ModbusFrame):
    """
    Modbus RTU frame implementation.
    """

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


class ModbusNetFrame(ModbusFrame):
    """
    Modbus TCP/UDP frame implementation.
    """

    def __init__(self):
        super().__init__()
        self._autoIncrement = True
        self._transaction = 0

    def writeBuffer(self, unit: int, func: int, data: bytes):
        if not self._modeServer:
            self._transaction = self._transaction % 65536 + self._autoIncrement
            self._autoIncrement = True
        buff = self._buff
        buff.clear()
        # save request data for future compare
        self._unit = unit
        self._func = func
        # standart TCP message prefix
        buff.extend(self._transaction.to_bytes(2, 'big')) # transaction id (2 bytes)
        buff.append(0) # always 0 (2 bytes)
        buff.append(0) # always 0 (2 bytes)
        sz = len(data) + 2
        buff.extend(sz.to_bytes(2, 'big')) # length of the entire message (2 bytes)
        # unit, function, data
        buff.append(unit)
        buff.append(func)
        buff.extend(data)
        return True


    def readBuffer(self):
        buff = self._buff
        sz = len(buff)
        if sz < 8:
            self._raiseError(exceptions.NotCorrectResponseError, "TCP. Not correct response. Responsed data length to small")

        transaction = buff[1] | (buff[0] << 8)
        if not ((buff[2] == 0) and (buff[3] == 0)):
            self._raiseError(exceptions.NotCorrectResponseError, "TCP. Not correct read-buffer's TCP-prefix (protocol ID)")
        cBytes = buff[5] | (buff[4] << 8)
        if cBytes != (sz-6):
            return self._raiseError(exceptions.NotCorrectResponseError, "TCP. Not correct read-buffer's TCP-prefix. Size defined in TCP-prefix is not equal to actual response-size")

        if (self._modeServer):
            self._transaction = transaction
        else:
            if self._transaction != transaction:
                self._raiseError(exceptions.NotCorrectResponseError, "TCP. Not correct response. Requested transaction id is not equal to responded")

        unit = buff[6]
        func = buff[7]
        return unit, func, buff[8:]

