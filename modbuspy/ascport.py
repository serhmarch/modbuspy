"""
ModbusAscPort.py - Contains ASCII port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from .serialport import ModbusSerialPort
from .mbglobal import ProtocolType, lrc, bytesToAscii, asciiToBytes
from . import exceptions


class ModbusAscPort(ModbusSerialPort):
    """
    Implements ASCII version of the Modbus communication protocol.
    
    ModbusAscPort derives from ModbusSerialPort and implements writeBuffer and readBuffer
    for ASCII version of Modbus communication protocol.
    
    ASCII format:
    - Starts with ':' character
    - Data is encoded as hexadecimal ASCII characters
    - Ends with CR LF (\r\n)
    - Uses LRC (Longitudinal Redundancy Check) for error detection
    """
    
    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. For ModbusAscPort returns ASCII."""
        return ProtocolType.ASC

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
