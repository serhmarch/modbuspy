"""
ModbusTcpServer.py - Header file of Modbus TCP server.

Author: serhmarch
Date: November 2025 (Converted to Python November 2025)
"""

import socket
import select
from typing import List, Optional, Callable, Tuple

from .mbglobal import ProtocolType, StatusCode, Constants, timer, AwaitableMethod
from .mbinterface import ModbusInterface
from . import exceptions
from .tcpport import ModbusTcpPort
from .mbobject import ModbusObject
from .serverport import ModbusServerPort
from .serverresource import ModbusServerResource

class ModbusTcpServer(ModbusServerPort):
    """The ModbusTcpServer class implements TCP server part of the Modbus protocol.
    
    ModbusTcpServer manages multiple simultaneous TCP connections and processes
    Modbus requests from multiple clients concurrently.

    In addition to the signals inherited from ModbusServerPort, ModbusTcpServer
    provides the following signals:
        * `signalNewConnection(source:str)` - Emitted when a new client connection is established.
        * `signalCloseConnection(source:str)` - Emitted when a client connection is closed.
    """

    class Strings:
        """String keys for TCP server port settings."""
        host    = "host"    # String key of setting 'TCP host name (DNS or IP address)'
        port    = "port"    # String key of setting 'TCP port number' for the listening server
        timeout = "timeout" # String key of setting 'TCP timeout' in milliseconds
        maxconn = "maxconn" # String key of setting 'Maximum number of simultaneous connections'

    class Defaults:
        """Defaults class contains default settings values for ModbusTcpServer."""
        host   : str = ""                          # Default setting 'TCP host name (DNS or IP address)'
        port   : int = Constants.STANDARD_TCP_PORT # Default setting 'TCP port number' for the listening server
        timeout: int = 30000                       # Default setting for the read timeout of every single connection (ms)
        maxconn: int = 10                          # Default setting for the maximum number of simultaneous connections
        
    def getHostService(sock: socket.socket) -> Tuple[str, int]:
        """Returns host and service (port) of the given socket.
        
        Args:
            sock: The socket to query.
        """
        try:
            peername = sock.getpeername()
            host, port = peername[0], peername[1]
            return host, port
        except socket.error:
            return "", 0

    def __init__(self, device: ModbusInterface):
        """Constructor of the class.
        
        Args:
            device: Object which processes incoming requests for read/write memory.
        """
        super().__init__(device)
        d = self.Defaults
        # TCP server settings
        self._host    = d.host
        self._tcpPort = d.port
        self._timeout = d.timeout
        self._maxconn = d.maxconn
        # Connections
        self._connections: List['ModbusServerPort'] = []
        # vars
        self._socket = None
        # Signals
        self.signalNewConnection = ModbusObject.Signal()
        self.signalCloseConnection = ModbusObject.Signal()


    def __del__(self):
        """Destructor of the class. Clear all unclosed connections."""
        self.close()

    def type(self) -> ProtocolType:
        """Returns the Modbus protocol type. In this case it is TCP.
        
        Returns:
            ProtocolType.TCP
        """
        return ProtocolType.TCP

    def isTcpServer(self) -> bool:
        """Returns True (this is a TCP server).
        
        Returns:
            Always True for TCP server.
        """
        return True

    # Property getters and setters

    def host(self) -> str:
        """Returns the setting for the TCP host name (DNS or IP address) of the server.
        
        Returns:
            TCP host name (DNS or IP address) for the listening server.
        """
        return self._host

    def setHost(self, host: str) -> None:
        """Sets the settings for the TCP host name (DNS or IP address) of the server.
        
        Args:
            host: TCP host name (DNS or IP address) for the listening server.
        """
        self._host = host

        return self._tcpPort

    def port(self) -> int:
        """Returns the setting for the TCP port number of the server.
        
        Returns:
            TCP port number for the listening server.
        """
        return self._tcpPort

    def setPort(self, port: int) -> None:
        """Sets the settings for the TCP port number of the server.
        
        Args:
            port: TCP port number for the listening server.
        """
        self._tcpPort = port

    def timeout(self) -> int:
        """Returns the setting for the read timeout of every single connection.
        
        Returns:
            Timeout value in milliseconds.
        """
        return self._timeout

    def setTimeout(self, timeout: int) -> None:
        """Sets the setting for the read timeout of every single connection.
        
        Args:
            timeout: Timeout value in milliseconds.
        """
        self._timeout = timeout
        for c in self._connections:
            c.setTimeout(timeout)

    def maxConnections(self) -> int:
        """Returns setting for the maximum number of simultaneous connections to the server.
        
        Returns:
            Maximum number of simultaneous connections.
        """
        return self._maxconn 

    def setMaxConnections(self, maxconn: int) -> None:
        """Sets the setting for the maximum number of simultaneous connections to the server.
        
        Args:
            maxconn: Maximum number of simultaneous connections.
        """
        if maxconn > 0:
            self._maxconn = maxconn
        else:
            self._maxconn = 1

    def settings(self) -> dict:
        s = ModbusTcpServer.Strings
        return {
            s.host   : self._host   ,
            s.port   : self._tcpPort,
            s.timeout: self._timeout,
            s.maxconn: self._maxconn
        }

    def setSettings(self, settings: dict):
        s = ModbusTcpServer.Strings
        v = settings.get(s.host, None)
        if v is not None:
            self.setHost(v)
        v = settings.get(s.port, None)
        if v is not None:
            self.setPort(v)
        v = settings.get(s.timeout, None)
        if v is not None:
            self.setTimeout(v)
        v = settings.get(s.maxconn, None)
        if v is not None:
            self.setMaxConnections(v)


    # Server port interface implementations

    def setBroadcastEnabled(self, enable: bool) -> None:
        """Enables broadcast mode for '0' unit address. It is enabled by default.
        
        Args:
            enable: True to enable broadcast mode, False to disable.
        """
        super().setBroadcastEnabled(enable)
        for c in self._connections:
            c.setBroadcastEnabled(enable)

    def setUnitMap(self, unitmap: Optional[bytes]) -> None:
        """Set units map of current server. Server makes a copy of units map data.
        
        Args:
            unitmap: Units map byte array or None.
        """
        super().setUnitMap(unitmap)
        for c in self._connections:
            c.setUnitMap(unitmap)

    def open(self) -> bool:
        """Try to listen for incoming connections on TCP port that was previously set.
        
        Returns:
            - True on success
            - False when operation is not complete
            - Status_BadTcpCreate when can't create TCP socket
            - Status_BadTcpBind when can't bind TCP socket
            - Status_BadTcpListen when can't listen TCP socket
        """
        self._cmdClose = False
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state in (ModbusServerPort.State.STATE_CLOSED,
                               ModbusServerPort.State.STATE_WAIT_FOR_OPEN):
                # Create listening socket
                try:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    self._socket.setblocking(False)
                except socket.error as e:
                    self._socket = None
                    self._raiseError(exceptions.TcpCreateError, f"TCP. Socket creation error for port '{self._tcpPort}': {str(e)}")
                # Bind to port
                try:
                    self._socket.bind(('', self._tcpPort))
                except socket.error as e:
                    self._socket = None
                    self._raiseError(exceptions.TcpBindError, f"TCP. Bind error for port '{self._tcpPort}': {str(e)}")
                # Start listening
                try:
                    self._socket.listen(self._maxconn)
                except socket.error as e:
                    self._socket = None
                    self._raiseError(exceptions.TcpListenError, f"TCP. Listen error for port '{self._tcpPort}': {str(e)}")
                return True
            else:
                if not self.isOpen():
                    self._state = ModbusServerPort.State.STATE_CLOSED
                    fRepeatAgain = True
                    continue
        return None
    
    def close(self) -> StatusCode:
        """Stop listening for incoming connections and close all previously opened connections.
        
        Returns:
            - Status_Good on success
            - Status_Processing when operation is not complete
        """
        if self.isOpen():
            self._socket.close()
            self._socket = None
        self._cmdClose = True
        for c in self._connections:
            c.close()
        if self._state == ModbusServerPort.State.STATE_WAIT_FOR_CLOSE:
            for c in self._connections:
                c.process()
                if not c.isStateClosed():
                    return None
        else:
            return None
        return True

    def isOpen(self) -> bool:
        """Returns True if the server is currently listening for incoming connections.
        
        Returns:
            True if server is listening, False otherwise.
        """
        return self._socket is not None

    def process(self) -> StatusCode:
        """Main function of TCP server. Must be called in cycle to perform all incoming TCP connections.
        
        Returns:
            StatusCode indicating the processing result.
        """
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state == ModbusServerPort.State.STATE_CLOSED:
                if self._cmdClose:
                    break
                self._state = ModbusServerPort.State.STATE_BEGIN_OPEN
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State. STATE_BEGIN_OPEN:
                self._timestampRefresh()
                self._state = ModbusServerPort.State.STATE_WAIT_FOR_OPEN
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_WAIT_FOR_OPEN:
                if self._cmdClose:
                    self._state = ModbusServerPort.State.STATE_WAIT_FOR_CLOSE
                    fRepeatAgain = True
                    continue
                try:
                    r = self.open()
                    # None - open is in process
                    if r is None:
                        return None
                except exceptions.ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    self._state = ModbusServerPort.State.STATE_TIMEOUT
                    raise
                self._state = ModbusServerPort.State.STATE_OPENED
                self.signalOpened.emit(self.objectName())
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_WAIT_FOR_CLOSE:
                try:
                    r = self.close()
                    # None - open is in process
                    if r is None:
                        return None
                except exceptions.ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    raise
                self._state = ModbusServerPort.State.STATE_CLOSED
                self.signalClosed.emit(self.objectName())
                self._clearConnections()
                #setMessage("Finalized")
                break
            elif self._state == ModbusServerPort.State.STATE_OPENED:
                #setMessage("Initialized. Waiting for connections...");
                self._state = ModbusServerPort.State.STATE_PROCESS_DEVICE
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_PROCESS_DEVICE:
                if self._cmdClose:
                    self._state = ModbusServerPort.State.STATE_WAIT_FOR_CLOSE
                    fRepeatAgain = True
                    continue
                # check up new connection
                s = self._nextPendingConnection()
                if s:
                    c = self._createTcpPort(s)
                    # Connect signals of the new connection to the server signals
                    c.signalTx   .connect(self.signalTx   .emit)
                    c.signalRx   .connect(self.signalRx   .emit)
                    c.signalError.connect(self.signalError.emit)

                    c.setBroadcastEnabled(self.isBroadcastEnabled())
                    c.setUnitMap(self.unitMap())
                    self._connections.append(c)
                    self.signalNewConnection.emit(c.objectName())
                # process current connections
                for c in self._connections:
                    c.process()
                    if not c.isOpen():
                        self.signalCloseConnection.emit(c.objectName())
                        self._connections.remove(c)
                        self._deleteTcpPort(c)
            elif self._state == ModbusServerPort.State.STATE_TIMEOUT:
                if (timer() - self._timestamp) < self.timeout():
                    return None
                self._state = ModbusServerPort.State.STATE_CLOSED
                fRepeatAgain = True
                continue
            else:
                if self._cmdClose and self.isOpen():
                    self._state = ModbusServerPort.State.STATE_WAIT_FOR_CLOSE
                elif self.isOpen():
                    self._state = ModbusServerPort.State.STATE_OPENED
                else:
                    self._state = ModbusServerPort.State.STATE_CLOSED
                fRepeatAgain = True
                continue
        return None

    # Protected methods

    def _nextPendingConnection(self) -> socket.socket:
        """Checks for incoming connections and returns socket if new connection established.
        
        Returns:
            New socket for incoming connection or None if no pending connections.
        """
        if not self._socket:
            return None
        try:
            # Check if there are pending connections
            ready, _, _ = select.select([self._socket], [], [], 0.0)
            if self._socket in ready:
                client_socket, _ = self._socket.accept()
                if len(self._connections) >= self._maxconn:
                    client_socket.close()
                    return None
                client_socket.setblocking(False)
                return client_socket
        except socket.error:
            pass  # No pending connections or error
        return None

    def _clearConnections(self) -> None:
        """Clear all allocated memory for previously established connections."""
        for c in self._connections:
            self.signalCloseConnection.emit(c.objectName())
            self._deleteTcpPort(c)
        self._connections.clear()

    # Virtual methods for customization

    def _createTcpPort(self, sock: socket.socket) -> ModbusServerPort:
        """Creates ModbusServerPort for new incoming connection defined by socket.
        
        May be reimplemented in subclasses.
        
        Args:
            sock: TCP socket for the new connection.

        Returns:
            New ModbusServerPort instance
        """
        tcp = ModbusTcpPort(blocking=False, sock=sock)
        tcp.setTimeout(self.timeout())
        host, port = ModbusTcpServer.getHostService(sock)
        name = f"{host}:{port}"
        c = ModbusServerResource(tcp, self.device())
        c.setObjectName(name)
        return c

    def _deleteTcpPort(self, port: ModbusServerPort) -> None:
        """Deletes ModbusServerPort by default.
        
        May be reimplemented in subclasses.
        
        Args:
            port: The server port to delete.
        """
        port.close()
        

class ModbusAsyncTcpServer(ModbusTcpServer):
    """Asynchronous version of ModbusServerResource.
    
    All methods that can be blocking in ModbusServerResource are
    overridden here to return `AwaitableMethod` objects.
    """
    def process(self):
        return AwaitableMethod(super().process)