"""
ModbusPort.py - Contains TCP port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from ModbusStatusCode import StatusCode
import ModbusExceptions
from ModbusGlobal import ProtocolType, Constants, timer, MBF_EXCEPTION
from ModbusPort import ModbusPort

import time
import socket
import select
import traceback

# ==============================================
# MODBUS TCP MASTER
# ==============================================

STANDARD_TCP_PORT = 502
DEFAULT_TIMEOUT = 10.0

class ModbusTcpPort(ModbusPort):
    """modbus master tcp class"""

    def __init__(self, blocking: bool = True):
        super().__init__(blocking)
        self._host = "localhost"
        self._port = Constants.STANDARD_TCP_PORT
        self._autoIncrement = True
        self._transaction = 0
        self._buff = bytearray()
        self._sock = None

    def __del__(self):
        self.disconnect()

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type.
        
        Returns:
            The protocol type (TCP).
        """
        return ProtocolType.TCP
    
    def host(self) -> str:
        """Returns the settings for the IP address or DNS name of the remote device.
        
        Returns:
            The host IP address or DNS name.
        """
        return self._host

    def setHost(self, host: str) -> None:
        """Sets the settings for the IP address or DNS name of the remote device.
        
        Args:
            host: The IP address or DNS name of the remote device.
        """
        if self._host != host:
            self._host = host
            self._changed = True

    def port(self) -> int:
        """Returns the setting for the TCP port number of the remote device.
        
        Returns:
            The TCP port number.
        """
        return self._port

    def setPort(self, port: int) -> None:
        """Sets the settings for the TCP port number of the remote device.
        
        Args:
            port: The TCP port number of the remote device.
        """
        if self._port != port:
            self._port = port
            self._changed = True

    def setNextRequestRepeated(self, v: bool) -> None:
        """Repeat next request parameters (for Modbus TCP transaction Id).
        
        Args:
            v: True to repeat next request ID, False otherwise.
        """
        self._autoIncrement = v

    def autoIncrement(self) -> bool:
        """Returns True if the identifier of each subsequent parcel is automatically incremented by 1.
        
        Returns:
            True if auto-increment is enabled, False otherwise.
        """
        return not self._autoIncrement
    
    def open(self) -> bool:
        fRepeatAgain = True
        
        while fRepeatAgain:
            fRepeatAgain = False
            
            if self._state in (ModbusPort.State.STATE_UNKNOWN, 
                               ModbusPort.State.STATE_CLOSED):
                # Clear changed flag
                self._changed = False
                
                # Check if already open
                if self.isOpen():
                    self._state = ModbusPort.State.STATE_OPENED
                    return True
                
                # Create socket if needed
                try:
                    self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._sock.setblocking(False)  # Start with non-blocking
                    
                    # Set timeout for blocking mode
                    if self.isBlocking():
                        self._sock.settimeout(self.timeout() / 1000.0)
                        
                except Exception as e:
                    return self.setError(ModbusExceptions.TcpCreateError, 
                                        f"TCP. Error while creating socket for '{self._host}:{self._port}'. Error: {str(e)}")
                
                # Set timestamp and state
                self._timestamp = timer()
                self._state = ModbusPort.State.STATE_WAIT_FOR_OPEN
                # Fall through to ModbusPort.State.STATE_WAIT_FOR_OPEN
                
            if self._state == ModbusPort.State.STATE_WAIT_FOR_OPEN:
                try:
                    # Attempt connection
                    result = self._sock.connect_ex((self._host, self._port))
                    
                    if result == 0:
                        # Connection successful
                        if self.isBlocking():
                            self._sock.setblocking(True)
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                        
                    elif result in (socket.EINPROGRESS, socket.EWOULDBLOCK, socket.EALREADY):
                        # Connection in progress
                        if self.isNonBlocking():
                            # For non-blocking mode, check timeout
                            current_time = timer()
                            if current_time - self._timestamp >= self.timeout():
                                self._sock.close()
                                self._state = ModbusPort.State.STATE_CLOSED
                                return self.setError(StatusCode.Status_BadTcpConnect,
                                                   f"TCP. Error while connecting to '{self._host}:{self._port}'. Timeout")
                            # Return processing - will try again later
                            return StatusCode.Status_Processing
                        else:
                            # For blocking mode, use select to wait for connection
                            try:
                                timeout_sec = self.timeout() / 1000.0
                                ready_to_write, _, error_socks = select.select([], [self._sock], [self._sock], timeout_sec)
                                
                                if error_socks:
                                    # Connection failed
                                    self._sock.close()
                                    self._state = ModbusPort.State.STATE_CLOSED
                                    return self.setError(StatusCode.Status_BadTcpConnect,
                                                       f"TCP. Error while connecting to '{self._host}:{self._port}'. Connection failed")
                                
                                elif ready_to_write:
                                    # Check for socket errors
                                    error = self._sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                                    if error:
                                        self._sock.close()
                                        self._state = ModbusPort.State.STATE_CLOSED
                                        return self.setError(StatusCode.Status_BadTcpConnect,
                                                           f"TCP. Error while connecting to '{self._host}:{self._port}'. Error code: {error}")
                                    
                                    # Connection successful
                                    self._sock.setblocking(True)
                                    self._state = ModbusPort.State.STATE_OPENED
                                    return StatusCode.Status_Good
                                    
                                else:
                                    # Timeout
                                    self._sock.close()
                                    self._state = ModbusPort.State.STATE_CLOSED
                                    return self.setError(StatusCode.Status_BadTcpConnect,
                                                       f"TCP. Error while connecting to '{self._host}:{self._port}'. Timeout")
                                    
                            except Exception as e:
                                self._sock.close()
                                self._state = ModbusPort.State.STATE_CLOSED
                                return self.setError(StatusCode.Status_BadTcpConnect,
                                                   f"TCP. Error while connecting to '{self._host}:{self._port}'. Error: {str(e)}")
                    else:
                        # Immediate connection error
                        self._sock.close()
                        self._state = ModbusPort.State.STATE_CLOSED
                        return self.setError(StatusCode.Status_BadTcpConnect,
                                           f"TCP. Error while connecting to '{self._host}:{self._port}'. Error code: {result}")
                        
                except Exception as e:
                    if hasattr(self, '_sock') and self._sock:
                        self._sock.close()
                    self._state = ModbusPort.State.STATE_CLOSED
                    return self.setError(StatusCode.Status_BadTcpConnect,
                                       f"TCP. Error while connecting to '{self._host}:{self._port}'. Error: {str(e)}")
            
            else:  # Default case
                if not self.isOpen():
                    self._state = ModbusPort.State.STATE_CLOSED
                    fRepeatAgain = True
                    continue
                else:
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
        
        return StatusCode.Status_Processing

    def disconnect(self):
        sock = self._sock
        print("Disconnection", sock)
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()
        return True        

    def isConnected(self):
        sock = self._sock
        readable, writeable, errored = select.select([sock], [sock], [], 0)
        return (sock in readable) or (sock in writeable)
        
    def timeout(self):
        return self._timeout        
        
    def setTimeout(self, timeout):    
        self._timeout = timeout

    def _write(self):
        fRepeatAgain = True
        sock = self._sock
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state == ModbusPort.State.STATE_PREPARE_TO_WRITE:
                self._stop = time.time() + self._timeout
                self._state = ModbusPort.State.STATE_WAIT_FOR_WRITE
                fRepeatAgain = True
            elif self._state == ModbusPort.State.STATE_WAIT_FOR_WRITE:
                readable, writeable, errored = select.select([], [sock], [sock], 0)
                if sock in errored:
                    raise modbus.TCPWriteError("Error while try to write")
                elif time.time() >= self._stop:
                    raise modbus.TCPWriteError("Timeout while try to write")
                elif sock in writeable:
                    self._state = ModbusPort.State.STATE_WAIT_FOR_WRITE_ALL
                    fRepeatAgain = True
                else:
                    return None
            elif self._state == ModbusPort.State.STATE_WAIT_FOR_WRITE_ALL:
                buff = self._buff
                sent = sock.send(buff)
                del buff[:sent]
                if not len(buff):
                    return True
                        

    def _read(self):
        fRepeatAgain = True
        sock = self._sock
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state == ModbusPort.State.STATE_PREPARE_TO_READ:
                self._buff.clear()
                self._stop = time.time() + self._timeout
                self._state = ModbusPort.State.STATE_WAIT_FOR_READ
                fRepeatAgain = True
            elif self._state == ModbusPort.State.STATE_WAIT_FOR_READ:
                readable, writeable, errored = select.select([sock], [], [sock], 0)
                if sock in readable:
                    self._state = ModbusPort.State.STATE_WAIT_FOR_READ_ALL
                    fRepeatAgain = True
                elif sock in errored:
                    raise modbus.TCPReadError("Error while try to read")
                elif time.time() >= self._stop:
                    raise modbus.TCPReadError("Timeout while try to read")
                else:
                    return None
            elif self._state == ModbusPort.State.STATE_WAIT_FOR_READ_ALL:
                readable, writeable, errored = select.select([sock], [], [sock], 0)
                if sock in errored:
                    raise modbus.TCPReadError("Error while try to read")
                elif sock in readable:
                    data = bytearray(sock.recv(1024))
                    if len(data) == 0 and len(self._buff) == 0: # that means remotely closed connection
                        raise modbus.TCPReadError("Connection was cloes remotely when try to read")
                    self._buff.extend(data)
                else:
                    return True
                    

    def writeBuffer(self, unit: int, func: int, data: bytes):
        if not self._modeServer:
            self._transaction = self._transaction % 65536 + self._autoIncrement
            self._autoIncrement = True
        buff = self._buff
        buff.clear()
        # save request data for future compare
        self._transaction = self._transaction % 65536 + 1
        self._unit = unit
        self._func = func
        # standart TCP message prefix
        buff.extend(self._transaction.to_bytes(2, 'big')) # transaction id
        buff.append(0)
        buff.append(0)
        buff.append(0)
        buff.append(len(data)+2); # quantity of next bytes
        # unit, function, data
        buff.append(unit)
        buff.append(func)
        buff.extend(data)
        return True


    def readBuffer(self):
        buff = self._buff
        sz = len(buff)
        if sz < 8:
            self._setError(ModbusExceptions.TcpReadError, "Not correct response. Responsed data length to small")

        transaction = buff[1] | (buff[0] << 8)
        if not ((buff[2] == 0) and (buff[3] == 0)):
            self._setError(ModbusExceptions.TcpReadError, "Not correct response. Requested transaction id is not equal to responded")

        cBytes = buff[5] | (buff[4] << 8)
        if cBytes != (sz-6):
            return self._setError(ModbusExceptions.NotCorrectResponseError, "TCP. Not correct read-buffer's TCP-prefix. Size defined in TCP-prefix is not equal to actual response-size")
        
        if (self._modeServer):
            self._transaction = transaction
        else:
            if self._transaction != transaction:
                self._setError(ModbusExceptions.NotCorrectResponseError, "Not correct response. Requested transaction id is not equal to responded")

        unit = buff[6]
        func = buff[7]

        if func & MBF_EXCEPTION: # exception response
            mexc = func & 0x7F
            self._raiseError(ModbusExceptions.getException(StatusCode.Status_Bad | mexc, f"Modbus exception 0x{mexc:02X} received from server"))
        return unit, func, buff[8:]

