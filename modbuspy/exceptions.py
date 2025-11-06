"""
ModbusException.py - Contains exception definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from .statuscode import StatusCode

# ==============================================
# Modbus Exception Classes
# ==============================================

class ModbusException(Exception):
    """Base class for all errors of Modbus library.

    It takes one arguments - message.
    """
    code = -1
    
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return f"Modbus exception (code={self.code}): {self.message}"
        
        
# ==============================================
# Modbus Standard Error Classes
# ==============================================

class StandardError(ModbusException):
    """Base class for Standard Modbus errors"""

class IllegalFunctionError(StandardError):
    """Illegal function standard Modbus exception"""
    code = StatusCode.Status_BadIllegalFunction

class IllegalDataAddressError(StandardError):
    """Illegal data address standard Modbus exception"""
    code = StatusCode.Status_BadIllegalDataAddress

class IllegalDataValueError(StandardError):
    """Illegal data value standard Modbus exception"""
    code = StatusCode.Status_BadIllegalDataValue

class ServerDeviceFailureError(StandardError):
    """Server device failure standard Modbus exception"""
    code = StatusCode.Status_BadServerDeviceFailure

class AcknowledgeError(StandardError):
    """Acknowledge standard Modbus exception"""
    code = StatusCode.Status_BadAcknowledge

class ServerDeviceBusyError(StandardError):
    """Server device busy standard Modbus exception"""
    code = StatusCode.Status_BadServerDeviceBusy

class NegativeAcknowledgeError(StandardError):
    """Negative acknowledge standard Modbus exception"""
    code = StatusCode.Status_BadNegativeAcknowledge

class MemoryParityError(StandardError):
    """Memory parity error standard Modbus exception"""
    code = StatusCode.Status_BadMemoryParityError

class GatewayPathUnavailableError(StandardError):
    """Gateway path unavailable standard Modbus exception"""
    code = StatusCode.Status_BadGatewayPathUnavailable

class GatewayTargetDeviceFailedToRespondError(StandardError):
    """Gateway target device failed to respond standard Modbus exception"""
    code = StatusCode.Status_BadGatewayTargetDeviceFailedToRespond

# ==============================================
# Modbus Common Error Classes
# ==============================================

class CommonError(ModbusException):
    """Base class for Common Modbus errors"""
    pass

class EmptyResponseError(CommonError):
    """Empty response common Modbus exception"""
    code = StatusCode.Status_BadEmptyResponse

class NotCorrectRequestError(CommonError):
    """Not correct request standard Modbus exception"""
    code = StatusCode.Status_BadNotCorrectRequest

class NotCorrectResponseError(CommonError):
    """Not correct response standard Modbus exception"""
    code = StatusCode.Status_BadNotCorrectResponse

class WriteBufferOverflowError(CommonError):
    """Write buffer overflow common Modbus exception"""
    code = StatusCode.Status_BadWriteBufferOverflow

class ReadBufferOverflowError(CommonError):
    """Read buffer overflow common Modbus exception"""
    code = StatusCode.Status_BadReadBufferOverflow

# ==============================================
# Modbus Serial Error Classes
# ==============================================

class SerialError(ModbusException):
    """Base class for serial (RTU- and ASCII-mode) Modbus exception"""

class SerialOpenError(SerialError):
    """Serial open Modbus exception"""
    code = StatusCode.Status_BadSerialOpen

class SerialWriteError(SerialError):
    """Serial write Modbus exception"""
    code = StatusCode.Status_BadSerialWrite

class SerialReadError(SerialError):
    """Serial read Modbus exception"""
    code = StatusCode.Status_BadSerialRead

class SerialReadTimeoutError(SerialError):
    """Serial read timeout Modbus exception"""
    code = StatusCode.Status_BadSerialReadTimeout

class SerialWriteTimeoutError(SerialError):
    """Serial write timeout Modbus exception"""
    code = StatusCode.Status_BadSerialWriteTimeout

# ==============================================
# Modbus ASCII Error Classes
# ==============================================

class AscError(SerialError):
    """Base class for serial ASCII-mode Modbus exception"""

class AscMissColonError(AscError):
    """Missed ':' begin-of-ASCII-frame marker Modbus exception"""
    code = StatusCode.Status_BadAscMissColon


class AscMissCrLfError(AscError):
    """Missed CR-LF end-of-ASCII-frame marker Modbus exception"""
    code = StatusCode.Status_BadAscMissCrLf


class AscCharError(AscError):
    """Bad char error of serial ASCII-mode Modbus exception"""
    code = StatusCode.Status_BadAscChar


class LrcError(AscError):
    """LRC error of serial ASCII-mode Modbus exception"""
    code = StatusCode.Status_BadLrc


# ==============================================
# Modbus RTU Error Classes
# ==============================================

class RtuError(SerialError):
    """Base class for serial RTU-mode Modbus exception"""


class CrcError(RtuError):
    """CRC error of serial RTU-mode Modbus exception"""
    code = StatusCode.Status_BadCrc


# ===========================
# Modbus TCP Error Classes
# ===========================

class TcpError(ModbusException):
    """Base class for TCP Modbus exception"""

class TcpCreateError(TcpError):
    """Socket creation Modbus exception"""
    code = StatusCode.Status_BadTcpConnect

class TcpConnectError(TcpError):
    """Socket connection Modbus exception"""
    code = StatusCode.Status_BadTcpConnect

class TcpWriteError(TcpError):
    """Socket write Modbus exception"""
    code = StatusCode.Status_BadTcpWrite

class TcpReadError(TcpError):
    """Socket read Modbus exception"""
    code = StatusCode.Status_BadTcpRead

class TcpBindError(TcpError):
    """Socket bind Modbus exception"""
    code = StatusCode.Status_BadTcpBind

class TcpListenError(TcpError):
    """Socket listen Modbus exception"""
    code = StatusCode.Status_BadTcpListen

class TcpAcceptError(TcpError):
    """Socket accept Modbus exception"""
    code = StatusCode.Status_BadTcpAccept

class TcpDisconnectError(TcpError):
    """Socket disconnect Modbus exception"""
    code = StatusCode.Status_BadTcpDisconnect

def getException(status: StatusCode, text: str) -> ModbusException:
    """Returns appropriate ModbusException instance for the given StatusCode.
    
    Args:
        status: The StatusCode for which to get the exception.

    Returns:
        ModbusException instance corresponding to the given StatusCode.
    """
    exception_map = {
        StatusCode.Status_BadNotCorrectResponse : NotCorrectResponseError ,
        StatusCode.Status_BadWriteBufferOverflow: WriteBufferOverflowError,
        StatusCode.Status_BadReadBufferOverflow : ReadBufferOverflowError ,
        StatusCode.Status_BadSerialOpen         : SerialOpenError         ,
        StatusCode.Status_BadSerialWrite        : SerialWriteError        ,
        StatusCode.Status_BadSerialRead         : SerialReadError         ,
        StatusCode.Status_BadSerialReadTimeout  : SerialReadTimeoutError  ,
        StatusCode.Status_BadSerialWriteTimeout : SerialWriteTimeoutError ,
        StatusCode.Status_BadAscMissColon       : AscMissColonError       ,
        StatusCode.Status_BadAscMissCrLf        : AscMissCrLfError        ,
        StatusCode.Status_BadAscChar            : AscCharError            ,
        StatusCode.Status_BadLrc                : LrcError                ,
        StatusCode.Status_BadCrc                : CrcError                ,
        StatusCode.Status_BadTcpConnect         : TcpConnectError         ,
        StatusCode.Status_BadTcpWrite           : TcpWriteError           ,
        StatusCode.Status_BadTcpRead            : TcpReadError            ,
        StatusCode.Status_BadTcpBind            : TcpBindError            ,
        StatusCode.Status_BadTcpListen          : TcpListenError          ,
        StatusCode.Status_BadTcpAccept          : TcpAcceptError          ,
        StatusCode.Status_BadTcpDisconnect      : TcpDisconnectError      ,
    }
    exctype = exception_map.get(status, None)
    if exctype is None:
        exc = ModbusException(text)
        exc.code = status
        return exc
    return exctype(text)