"""
ModbusException.py - Contains exception definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from enum import IntEnum

# ==============================================
# Modbus Exception Status Codes
# ==============================================

class StatusCode(IntEnum):
    """Defines status of executed Modbus functions."""
    Status_Processing   = 0x80000000 # The operation is not complete. Further operation is required
    Status_Good         = 0x00000000 # Successful result
    Status_Bad          = 0x01000000 # Error. General
    Status_Uncertain    = 0x02000000 # The status is undefined

    # ------ Modbus standard errors begin -------
    # from 0 to 255 
    Status_BadIllegalFunction                    = Status_Bad | 0x01 # Standard error. The function is not supported
    Status_BadIllegalDataAddress                 = Status_Bad | 0x02 # Standard error. Invalid data address
    Status_BadIllegalDataValue                   = Status_Bad | 0x03 # Standard error. Invalid data value
    Status_BadServerDeviceFailure                = Status_Bad | 0x04 # Standard error. Failure during a specified operation
    Status_BadAcknowledge                        = Status_Bad | 0x05 # Standard error. The server has accepted the request and is processing it, but it will take a long time
    Status_BadServerDeviceBusy                   = Status_Bad | 0x06 # Standard error. The server is busy processing a long command. The request must be repeated later
    Status_BadNegativeAcknowledge                = Status_Bad | 0x07 # Standard error. The programming function cannot be performed
    Status_BadMemoryParityError                  = Status_Bad | 0x08 # Standard error. The server attempted to read a record file but detected a parity error in memory
    Status_BadGatewayPathUnavailable             = Status_Bad | 0x0A # Standard error. Indicates that the gateway was unable to allocate an internal communication path from the input port o the output port for processing the request. Usually means that the gateway is misconfigured or overloaded
    Status_BadGatewayTargetDeviceFailedToRespond = Status_Bad | 0x0B # Standard error. Indicates that no response was obtained from the target device. Usually means that the device is not present on the network
    # ------- Modbus standard errors end --------

    # ------- Modbus common errors begin ---------
    Status_BadEmptyResponse         = Status_Bad | 0x101 # Error. Empty request/response body
    Status_BadNotCorrectRequest     = Status_Bad | 0x102 # Error. Invalid request
    Status_BadNotCorrectResponse    = Status_Bad | 0x103 # Error. Invalid response
    Status_BadWriteBufferOverflow   = Status_Bad | 0x104 # Error. Write buffer overflow
    Status_BadReadBufferOverflow    = Status_Bad | 0x105 # Error. Request receive buffer overflow

    # -------- Modbus common errors end ---------

    # --_ Modbus serial specified errors begin --
    Status_BadSerialOpen         = Status_Bad | 0x201 # Error. Serial port cannot be opened
    Status_BadSerialWrite        = Status_Bad | 0x202 # Error. Cannot send a parcel to the serial port
    Status_BadSerialRead         = Status_Bad | 0x203 # Error. Reading the serial port (timeout)
    Status_BadSerialReadTimeout  = Status_Bad | 0x204 # Error. Reading the serial port (timeout)
    Status_BadSerialWriteTimeout = Status_Bad | 0x205 # Error. Writing the serial port (timeout)
    Status_BadPortNotOpen        = Status_Bad | 0x206 # Error. Serial port is not open
    Status_BadPortWrite          = Status_Bad | 0x207 # Error. Cannot write to serial port
    Status_BadPortRead           = Status_Bad | 0x208 # Error. Cannot read from serial port
    # ---_ Modbus serial specified errors end ---
                                                          
    # ---- Modbus ASC specified errors begin ----         
    Status_BadAscMissColon  = Status_Bad | 0x301 # Error (ASC). Missing packet start character ':'
    Status_BadAscMissCrLf   = Status_Bad | 0x302 # Error (ASC). '\r\n' end of packet character missing
    Status_BadAscChar       = Status_Bad | 0x303 # Error (ASC). Invalid ASCII character
    Status_BadLrc           = Status_Bad | 0x304 # Error (ASC). Invalid checksum
    # ---- Modbus ASC specified errors end ----           
                                                          
    # ---- Modbus RTU specified errors begin ----         
    Status_BadCrc = Status_Bad | 0x401 # Error (RTU). Wrong checksum
    # ----- Modbus RTU specified errors end -----         
                                                          
    # --_ Modbus TCP specified errors begin --            
    Status_BadTcpCreate     = Status_Bad | 0x501 # Error. Unable to create a TCP socket
    Status_BadTcpConnect    = Status_Bad | 0x502 # Error. Unable to create a TCP connection
    Status_BadTcpWrite      = Status_Bad | 0x503 # Error. Unable to send a TCP packet
    Status_BadTcpRead       = Status_Bad | 0x504 # Error. Unable to receive a TCP packet
    Status_BadTcpBind       = Status_Bad | 0x505 # Error. Unable to bind a TCP socket (server side)
    Status_BadTcpListen     = Status_Bad | 0x506 # Error. Unable to listen a TCP socket (server side)
    Status_BadTcpAccept     = Status_Bad | 0x507 # Error. Unable accept bind a TCP socket (server side)
    Status_BadTcpDisconnect = Status_Bad | 0x508 # Error. Bad disconnection result
    # ---_ Modbus TCP specified errors end ---


# Status Code Utility Functions

def StatusIsProcessing(status: StatusCode) -> bool:
    """Returns a general indication that the result of the operation is incomplete.
    
    Args:
        status: The StatusCode to check.
        
    Returns:
        True if the status indicates processing is ongoing, False otherwise.
    """
    return status == StatusCode.Status_Processing


def StatusIsGood(status: StatusCode) -> bool:
    """Returns a general indication that the operation result is successful.
    
    Args:
        status: The StatusCode to check.
        
    Returns:
        True if the status indicates success, False otherwise.
    """
    return (status.value & 0xFF000000) == StatusCode.Status_Good


def StatusIsBad(status: StatusCode) -> bool:
    """Returns a general indication that the operation result is unsuccessful.
    
    Args:
        status: The StatusCode to check.
        
    Returns:
        True if the status indicates an error, False otherwise.
    """
    return (status.value & StatusCode.Status_Bad) != 0


def StatusIsUncertain(status: StatusCode) -> bool:
    """Returns a general sign that the result of the operation is undefined.
    
    Args:
        status: The StatusCode to check.
        
    Returns:
        True if the status indicates uncertainty, False otherwise.
    """
    return (status.value & StatusCode.Status_Uncertain) != 0


def StatusIsStandardError(status: StatusCode) -> bool:
    """Returns a general sign that the result is standard error.
    
    Args:
        status: The StatusCode to check.
        
    Returns:
        True if the status indicates a standard Modbus error (codes 0-255), False otherwise.
    """
    return bool((status.value & StatusCode.Status_Bad) and ((status.value & 0xFF00) == 0))
