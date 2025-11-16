"""
ModbusTcpPort.py - Contains TCP port definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

from .statuscode import StatusCode
from . import exceptions
from .mbglobal import *
from .port import ModbusPort
from .exceptions import ModbusException
from . import exceptions

import socket
import select

class ModbusTcpPort(ModbusPort):
    """modbus master tcp class"""

    class Strings:
        """String keys for TCP port settings."""
        host    = "host"    # String key of setting 'TCP host name (DNS or IP address)'
        port    = "port"    # String key of setting 'TCP port number' for the listening server
        timeout = "timeout" # String key of setting 'TCP timeout' in milliseconds

    class Defaults:
        """Default tcp port settings."""
        host    = "localhost"                 # Default setting 'TCP host name (DNS or IP address)'
        port    = Constants.STANDARD_TCP_PORT # Default setting 'TCP port number' for the listening server
        timeout = 1000                        # Default setting 'TCP timeout' in milliseconds

    def __init__(self, blocking: bool = True, sock = None):
        d = ModbusTcpPort.Defaults
        super().__init__(blocking)
        self._host    = d.host
        self._port    = d.port
        self._timeout = d.timeout
        self._autoIncrement = True
        self._transaction = 0
        self._sock = sock
        if self.isOpen():
            self._state = ModbusPort.State.STATE_OPENED

    def __del__(self):
        self.close()

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type.
        
        Returns:
            The protocol type (TCP).
        """
        return ProtocolType.TCP
    
    def handle(self) -> int:
        if self._sock is not None:
            return self._sock.fileno()
        return -1
    
    def socket(self):
        """Returns the underlying socket object.
        
        Returns:
            The socket object.
        """
        return self._sock

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

    @property
    def Host(self) -> str:
        """Property. Get the host IP address or DNS name."""
        return self.host()
    
    @Host.setter
    def Host(self, host: str) -> None:
        """Property. Set the host IP address or DNS name."""
        return self.setHost(host)
    
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

    @property
    def Port(self) -> int:
        """Property. Get the TCP port number."""
        return self.port()
    
    @Port.setter
    def Port(self, port: int) -> None:
        """Property. Set the TCP port number."""
        return self.setPort(port)   
    
    def settings(self) -> dict:
        s = ModbusTcpPort.Strings
        return {
            s.host   : self._host   ,
            s.port   : self._port   ,
            s.timeout: self._timeout
        }

    def setSettings(self, settings: dict):
        s = ModbusTcpPort.Strings
        v = settings.get(s.host, None)
        if v is not None:
            self.setHost(v)
        v = settings.get(s.port, None)
        if v is not None:
            self.setPort(v)
        v = settings.get(s.timeout, None)
        if v is not None:
            self.setTimeout(v)

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
        return self._autoIncrement
    
    def transactionId(self) -> int:
        """Returns the current transaction identifier.
        
        Returns:
            The current transaction identifier.
        """
        return self._transaction
    
    def unit(self) -> int:
        """Returns the unit identifier of the last request.
        
        Returns:
            The unit identifier.
        """
        return self._unit
    
    def function(self) -> int:
        """Returns the function code of the last request.
        
        Returns:
            The function code.
        """
        return self._func
    
    def open(self) -> StatusCode:
        fRepeatAgain = True        
        while fRepeatAgain:
            fRepeatAgain = False
            
            if self._state in (ModbusPort.State.STATE_UNKNOWN, 
                               ModbusPort.State.STATE_CLOSED):
                if self.isOpen():
                    if self.isChanged():
                        self.close()
                    else:
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good                
                # Clear changed flag
                self._changed = False
                
                # Create socket if needed
                try:
                    self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                        
                except Exception as e:
                    self._raiseError(exceptions.TcpCreateError, f"TCP. Error while creating socket for '{self._host}:{self._port}'. Error: {str(e)}")
                    
                # Set timeout for blocking mode
                if self.isBlocking():
                    self._sock.settimeout(self.timeout() / 1000.0)
                else:
                    self._sock.setblocking(False)
    
                self._timestamp = timer()
                try:
                    # socket.connect_ex is non-blocking and in most cases do not raise exceptions
                    result = self._sock.connect_ex((self._host, self._port))
                    if result == 0:
                        # Connection successful
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                    if result != socket.EWOULDBLOCK:
                        raise socket.error(f"code={result}")
                except Exception as e:
                    self.close()
                    self._state = ModbusPort.State.STATE_CLOSED
                    self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Error: {str(e)}")
                # Fall through to ModbusPort.State.STATE_WAIT_FOR_OPEN
                self._state = ModbusPort.State.STATE_WAIT_FOR_OPEN
                
            if self._state == ModbusPort.State.STATE_WAIT_FOR_OPEN:
                try:
                    timeout_sec = self.timeout() / 1000.0 if self.isBlocking() else 0.0
                    _, ready_to_write, error_socks = select.select([], [self._sock], [self._sock], timeout_sec)                    
                    if error_socks:
                        # Connection failed
                        self.close()
                        self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Connection failed")                    
                    elif ready_to_write:
                        # Connection successful
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good                        
                    else:
                        # Timeout
                        if self.isNonBlocking() and (timer() - self._timestamp < self.timeout()):
                            return None
                        self.close()
                        self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Timeout")                        
                except Exception as e:
                    self.close()
                    if isinstance(e, ModbusException):
                        raise e
                    self._raiseError(exceptions.TcpConnectError, f"TCP. Error while connecting to '{self._host}:{self._port}'. Error: {str(e)}")
            else:  # Default case
                if self.isOpen() and not self.isChanged():
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                else:
                    self._state = ModbusPort.State.STATE_CLOSED
                    fRepeatAgain = True
                    continue
        return None

    def close(self) -> StatusCode:
        if self._sock is not None and self._sock.fileno() >= 0:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
                self._sock.close()
            except OSError:
                pass
        self._sock = None
        self._state = ModbusPort.State.STATE_CLOSED
        return StatusCode.Status_Good

    def isOpen(self) -> bool:
        sock = self._sock
        if sock is None or sock.fileno() < 0:
            return False
        readable, writeable, _ = select.select([sock], [sock], [], 0.0)
        return (sock in readable) or (sock in writeable)
        
    def timeout(self):
        return self._timeout        
        
    def setTimeout(self, timeout):    
        self._timeout = timeout

    def write(self) -> StatusCode:
        if self._state in (ModbusPort.State.STATE_OPENED,
                           ModbusPort.State.STATE_PREPARE_TO_WRITE,
                           ModbusPort.State.STATE_WAIT_FOR_WRITE,
                           ModbusPort.State.STATE_WAIT_FOR_WRITE_ALL):
            try:
                c = self._sock.send(self._buff)
                if c >= 0:
                    self._state = ModbusPort.State.STATE_OPENED
                    return StatusCode.Status_Good
                self.close()
                self._raiseError(exceptions.TcpWriteError, f"TCP. Error while writing to '{self._host}:{self._port}'. Connection lost.")
            except socket.error as e:
                self._raiseError(exceptions.TcpWriteError, f"TCP. Error while writing to '{self._host}:{self._port}'. {str(e)}")
        return None
    
    def read(self) -> StatusCode:
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state in (ModbusPort.State.STATE_OPENED,
                               ModbusPort.State.STATE_PREPARE_TO_READ):
                self._timestamp = timer()
                self._state = ModbusPort.State.STATE_WAIT_FOR_READ
                fRepeatAgain = True
                continue
            elif self._state in (ModbusPort.State.STATE_WAIT_FOR_READ,
                                 ModbusPort.State.STATE_WAIT_FOR_READ_ALL):
                try:
                    # Attempt to receive data from socket
                    data = self._sock.recv(1024)  # Read up to 1KB buffer size
                    c = len(data)
                    if c > 0:
                        # Data received successfully
                        self._buff = bytearray(data)
                        self._state = ModbusPort.State.STATE_OPENED
                        return StatusCode.Status_Good
                        
                    else:
                        # Connection closed by remote end (recv returned 0 bytes)
                        self.close()
                        # Note: When connection is remotely closed is not error for server side
                        if self._modeServer:
                            return StatusCode.Status_Uncertain
                        else:
                            self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Remote connection closed")
                            
                except socket.timeout:
                    # Socket timeout occurred
                    if self.isNonBlocking() and (timer() - self._timestamp < self.timeout()):
                        return None
                    self.close()
                    self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Timeout")
                    
                except socket.error as e:
                    # Socket error occurred
                    if e.errno == socket.EWOULDBLOCK:
                        # Non-blocking socket would block - check timeout
                        if self.isNonBlocking():
                            if (timer() - self._timestamp >= self.timeout()):
                                self.close()
                                self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Timeout")
                            # Return None to continue processing later
                            return None
                    # Other socket error
                    self.close()
                    self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Error: {str(e)}")
                        
                except Exception as e:
                    # Unexpected error
                    self.close()
                    if isinstance(e, ModbusException):
                        raise e
                    self._raiseError(exceptions.TcpReadError, f"TCP. Error while reading from '{self._host}:{self._port}'. Error: {str(e)}")
                    
            return None
                    

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

