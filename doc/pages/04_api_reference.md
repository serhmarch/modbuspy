# API Reference

## Module: modbuspy

### Main Package Exports

```python
from modbuspy import (
    # Version information
    MBPY_VERSION_MAJOR,
    MBPY_VERSION_MINOR,
    MBPY_VERSION_PATCH,
    MBPY_VERSION_INT,
    MBPY_VERSION_STR,
    
    # Core types
    ProtocolType,
    StatusCode,
    StatusIsGood,
    StatusIsProcessing,
    
    # Exceptions
    ModbusException,
    
    # Main classes
    ModbusInterface,
    ModbusClient,
    ModbusClientPort,
    ModbusAsyncClientPort,
    ModbusServerPort,
    ModbusServerResource,
    ModbusAsyncServerResource,
    
    # Protocol implementations
    ModbusTcpPort,
    ModbusTcpServer,
    ModbusAsyncTcpServer,
    ModbusRtuPort,
    ModbusAscPort,
    ModbusSerialPort,
    
    # Factories
    createPort,
    createClientPort,
    createServerPort,
)
```

## Global Types and Constants

### ProtocolType Enum

```python
class ProtocolType(IntEnum):
    TCP = 0  # TCP/IP protocol
    RTU = 1  # RTU serial protocol
    ASC = 2  # ASCII serial protocol
```

### StatusCode Enum

```python
class StatusCode(IntEnum):
    # General status
    Status_Processing   = 0x80000000  # Operation in progress
    Status_Good         = 0x00000000  # Successful
    Status_Bad          = 0x01000000  # Error
    Status_Uncertain    = 0x02000000  # Unknown status
    
    # Standard Modbus errors (from spec)
    Status_BadIllegalFunction                    = Status_Bad | 0x01
    Status_BadIllegalDataAddress                 = Status_Bad | 0x02
    Status_BadIllegalDataValue                   = Status_Bad | 0x03
    Status_BadServerDeviceFailure                = Status_Bad | 0x04
    Status_BadAcknowledge                        = Status_Bad | 0x05
    Status_BadServerDeviceBusy                   = Status_Bad | 0x06
    Status_BadNegativeAcknowledge                = Status_Bad | 0x07
    Status_BadMemoryParityError                  = Status_Bad | 0x08
    Status_BadGatewayPathUnavailable             = Status_Bad | 0x0A
    Status_BadGatewayTargetDeviceFailedToRespond = Status_Bad | 0x0B
    
    # Common errors
    Status_BadEmptyResponse         = Status_Bad | 0x101
    Status_BadNotCorrectRequest     = Status_Bad | 0x102
    Status_BadNotCorrectResponse    = Status_Bad | 0x103
    Status_BadWriteBufferOverflow   = Status_Bad | 0x104
    Status_BadReadBufferOverflow    = Status_Bad | 0x105
    
    # Serial errors
    Status_BadSerialOpen         = Status_Bad | 0x201
    Status_BadSerialWrite        = Status_Bad | 0x202
    Status_BadSerialRead         = Status_Bad | 0x203
    Status_BadSerialReadTimeout  = Status_Bad | 0x204
    Status_BadSerialWriteTimeout = Status_Bad | 0x205
    Status_BadPortNotOpen        = Status_Bad | 0x206
    Status_BadPortWrite          = Status_Bad | 0x207
    Status_BadPortRead           = Status_Bad | 0x208
    
    # ASCII specific errors
    Status_BadAscMissColon  = Status_Bad | 0x301
    Status_BadAscMissCrLf   = Status_Bad | 0x302
    Status_BadAscChar       = Status_Bad | 0x303
    Status_BadLrc           = Status_Bad | 0x304
    
    # RTU specific errors
    Status_BadCrc = Status_Bad | 0x401
    
    # TCP specific errors
    Status_BadTcpCreate     = Status_Bad | 0x501
    Status_BadTcpConnect    = Status_Bad | 0x502
    Status_BadTcpWrite      = Status_Bad | 0x503
    Status_BadTcpRead       = Status_Bad | 0x504
    Status_BadTcpBind       = Status_Bad | 0x505
    Status_BadTcpListen     = Status_Bad | 0x506
    Status_BadTcpAccept     = Status_Bad | 0x507
    Status_BadTcpDisconnect = Status_Bad | 0x508
```

### Status Code Functions

```python
def StatusIsGood(status: StatusCode) -> bool:
    """Check if status indicates success."""
    return (status.value & 0xFF000000) == StatusCode.Status_Good

def StatusIsProcessing(status: StatusCode) -> bool:
    """Check if status indicates operation in progress."""
    return status == StatusCode.Status_Processing

def StatusIsBad(status: StatusCode) -> bool:
    """Check if status indicates error."""
    return (status.value & 0xFF000000) == StatusCode.Status_Bad

def StatusIsUncertain(status: StatusCode) -> bool:
    """Check if status is uncertain."""
    return (status.value & 0xFF000000) == StatusCode.Status_Uncertain
```

### Constants

```python
class Constants:
    STANDARD_TCP_PORT = 502
    MB_UNITMAP_SIZE = 32
    MB_REGE_SZ_BITES = 16
    MAX_MODBUS_RTU_FRAME_LENGTH = 256
```

### Modbus Function Codes

```python
MBF_READ_COILS                       = 1
MBF_READ_DISCRETE_INPUTS             = 2
MBF_READ_HOLDING_REGISTERS           = 3
MBF_READ_INPUT_REGISTERS             = 4
MBF_WRITE_SINGLE_COIL                = 5
MBF_WRITE_SINGLE_REGISTER            = 6
MBF_READ_EXCEPTION_STATUS            = 7
MBF_DIAGNOSTICS                      = 8
MBF_GET_COMM_EVENT_COUNTER           = 11
MBF_GET_COMM_EVENT_LOG               = 12
MBF_WRITE_MULTIPLE_COILS             = 15
MBF_WRITE_MULTIPLE_REGISTERS         = 16
MBF_REPORT_SERVER_ID                 = 17
MBF_READ_FILE_RECORD                 = 20
MBF_WRITE_FILE_RECORD                = 21
MBF_MASK_WRITE_REGISTER              = 22
MBF_READ_WRITE_MULTIPLE_REGISTERS    = 23
MBF_READ_FIFO_QUEUE                  = 24
MBF_ENCAPSULATED_INTERFACE_TRANSPORT = 43
```

## Exception Classes

### ModbusException

Base exception class for all modbuspy errors.

```python
class ModbusException(Exception):
    code: int = -1
    message: str
    
    def __init__(self, message: str): pass
    def __str__(self) -> str: pass
```

### Standard Modbus Exceptions

```python
class IllegalFunctionError(StandardError):
    code = 0x01

class IllegalDataAddressError(StandardError):
    code = 0x02

class IllegalDataValueError(StandardError):
    code = 0x03

class ServerDeviceFailureError(StandardError):
    code = 0x04

class AcknowledgeError(StandardError):
    code = 0x05

class ServerDeviceBusyError(StandardError):
    code = 0x06

class NegativeAcknowledgeError(StandardError):
    code = 0x07

class MemoryParityError(StandardError):
    code = 0x08

class GatewayPathUnavailableError(StandardError):
    code = 0x0A

class GatewayTargetDeviceFailedToRespondError(StandardError):
    code = 0x0B
```

### Common Modbus Exceptions

```python
class EmptyResponseError(CommonError): pass
class NotCorrectRequestError(CommonError): pass
class NotCorrectResponseError(CommonError): pass
class WriteBufferOverflowError(CommonError): pass
class ReadBufferOverflowError(CommonError): pass
```

## Port Classes

### ModbusPort (Abstract)

Base class for all port implementations.

**Methods:**
```python
class ModbusPort:
    def type(self) -> ProtocolType: pass
    def handle(self) -> int: pass
    def isOpen(self) -> bool: pass
    def open(self) -> StatusCode: pass
    def close(self) -> StatusCode: pass
    def read(self) -> StatusCode: pass
    def write(self) -> StatusCode: pass
    def isBlocking(self) -> bool: pass
    def setBlocking(self, blocking: bool) -> None: pass
```

### ModbusTcpPort

TCP port implementation.

**Constructor:**
```python
ModbusTcpPort(blocking: bool = True)
```

**Configuration Methods:**
```python
def setHost(self, host: str) -> None:
    """Set remote host IP or DNS name."""
    
def getHost(self) -> str:
    """Get remote host."""
    
def setPort(self, port: int) -> None:
    """Set remote TCP port."""
    
def getPort(self) -> int:
    """Get remote TCP port."""
    
def setTimeout(self, timeout: int) -> None:
    """Set timeout in milliseconds."""
    
def getTimeout(self) -> int:
    """Get timeout in milliseconds."""
```

**Properties:**
```python
Host: str              # Get/set host
Port: int              # Get/set port
Timeout: int           # Get/set timeout
Blocking: bool         # Get/set blocking mode
```

### ModbusRtuPort

RTU serial port implementation.

**Constructor:**
```python
ModbusRtuPort(blocking: bool = True)
```

**Configuration Methods:**
```python
def setPortName(self, port: str) -> None:
    """Set serial port name (e.g., 'COM1', '/dev/ttyUSB0')."""
    
def setBaudRate(self, baudrate: int) -> None:
    """Set baud rate."""
    
def setDataBits(self, databits: int) -> None:
    """Set data bits (5-8)."""
    
def setParity(self, parity: str) -> None:
    """Set parity ('N', 'E', 'O')."""
    
def setStopBits(self, stopbits: int) -> None:
    """Set stop bits (1, 1.5, or 2)."""
    
def setTimeoutFirstByte(self, timeout: int) -> None:
    """Set first byte timeout in milliseconds."""
    
def setTimeoutInterByte(self, timeout: int) -> None:
    """Set inter-byte timeout in milliseconds."""
```

### ModbusAscPort

ASCII serial port implementation. Uses same methods as ModbusRtuPort.

## Client Classes

### ModbusClientPort

Main client port implementation.

**Constructor:**
```python
ModbusClientPort(port: ModbusPort)
```

**Configuration Methods:**
```python
def port(self) -> ModbusPort:
    """Get underlying port."""
    
def setPort(self, port: ModbusPort) -> None:
    """Set underlying port."""
    
def setObjectName(self, name: str) -> None:
    """Set object name for logging."""
```

**Connection Methods:**
```python
def open(self) -> StatusCode:
    """Open the port connection."""
    
def close(self) -> StatusCode:
    """Close the port connection."""
    
def isOpen(self) -> bool:
    """Check if port is open."""
```

**Read Methods (FC 01-04):**
```python
def readCoils(self, unit: int, offset: int, count: int) -> bytes:
def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes:
def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes:
```

**Write Methods (FC 05-06):**
```python
def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode:
def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode:
```

**Multiple Write Methods (FC 15-16):**
```python
def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode:
def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode:
```

**Advanced Methods:**
```python
def readExceptionStatus(self, unit: int) -> bytes:
def diagnostics(self, unit: int, subfunc: int, indata: Optional[bytes]) -> bytes:
def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode:
def readWriteMultipleRegisters(self, unit: int, readOffset: int, readCount: int,
                                writeOffset: int, writeValues: bytes) -> bytes:
def reportServerID(self, unit: int) -> bytes:
def readFIFOQueue(self, unit: int, offset: int) -> bytes:
```

**Formatted Methods (with data conversion):**
```python
def readCoilsF(self, unit: int, offset: int, count: int, fmt: str = '<H') -> Tuple:
def readDiscreteInputsF(self, unit: int, offset: int, count: int, fmt: str = '<H') -> Tuple:
def readHoldingRegistersF(self, unit: int, offset: int, count: int, fmt: str = '<H') -> Tuple:
def readInputRegistersF(self, unit: int, offset: int, count: int, fmt: str = '<H') -> Tuple:
def writeMultipleCoilsF(self, unit: int, offset: int, values: Tuple, count: int = -1, fmt: str = '<H') -> StatusCode:
def writeMultipleRegistersF(self, unit: int, offset: int, values: Tuple, fmt: str = '<H') -> StatusCode:
def readWriteMultipleRegistersF(self, unit: int, readOffset: int, readCount: int,
                                 writeOffset: int, writeValues: Tuple, fmt: str = '<H') -> Tuple:
```

**Status Methods:**
```python
def lastPortStatus(self) -> StatusCode:
    """Get last operation status."""
    
def lastPortErrorStatus(self) -> StatusCode:
    """Get last error status."""
    
def lastPortErrorText(self) -> str:
    """Get last error text."""
```

**Signals:**
```python
signalOpened: Signal      # Emitted when port opens
signalClosed: Signal      # Emitted when port closes
signalTx: Signal          # Emitted before transmission (source, data)
signalRx: Signal          # Emitted after reception (source, data)
signalError: Signal       # Emitted on error (source, code, text)
```

### ModbusAsyncClientPort

Async wrapper around ModbusClientPort.

**Constructor:**
```python
ModbusAsyncClientPort(port: ModbusPort)
```

All methods are async variants:
```python
async def readCoils(self, unit: int, offset: int, count: int) -> bytes:
async def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
# ... and all other methods from ModbusClientPort
```

### ModbusClient

Client wrapper storing unit identifier.

**Constructor:**
```python
ModbusClient(unit: int, port: ModbusClientPort)
```

**Unit Methods:**
```python
def unit(self) -> int:
def setUnit(self, unit: int) -> None:

Unit: int  # Property
```

**Methods (same as ModbusClientPort but without unit parameter):**
```python
def readCoils(self, offset: int, count: int) -> bytes:
def readHoldingRegisters(self, offset: int, count: int) -> bytes:
def writeSingleCoil(self, offset: int, value: bool) -> StatusCode:
# ... all other methods
```

## Server Classes

### ModbusTcpServer

Multi-connection TCP server.

**Constructor:**
```python
ModbusTcpServer(device: ModbusInterface)
```

**Configuration Methods:**
```python
def setPort(self, port: int) -> None:
def getPort(self) -> int:
def setHost(self, host: str) -> None:
def getHost(self) -> str:
def setTimeout(self, timeout: int) -> None:
def getTimeout(self) -> int:
def setMaxConnections(self, maxconn: int) -> None:
def getMaxConnections(self) -> int:
def setDevice(self, device: ModbusInterface) -> None:
def device(self) -> ModbusInterface:
```

**Operation Methods:**
```python
def process(self) -> None:
    """Process one server cycle."""
    
def close(self) -> None:
    """Close all connections and shutdown."""
    
def type(self) -> ProtocolType:
    """Return protocol type (TCP)."""
```

**Signals:**
```python
signalNewConnection: Signal       # (address)
signalCloseConnection: Signal     # (address)
signalError: Signal               # (source, code, text)
signalTx: Signal                  # (source, data)
signalRx: Signal                  # (source, data)
```

### ModbusServerResource

Server for RTU/ASCII protocols.

**Constructor:**
```python
ModbusServerResource(port: ModbusPort, device: ModbusInterface)
```

**Methods:**
```python
def process(self) -> None:
    """Process one server cycle."""
    
def close(self) -> None:
    """Close port."""
    
def type(self) -> ProtocolType:
    """Return protocol type."""
    
def setDevice(self, device: ModbusInterface) -> None:
def device(self) -> ModbusInterface:
```

### ModbusAsyncTcpServer

Async TCP server.

**Constructor:**
```python
ModbusAsyncTcpServer(device: ModbusInterface)
```

**Methods:**
```python
async def process(self) -> None:
    """Async process one server cycle."""
```

### ModbusAsyncServerResource

Async server for RTU/ASCII.

**Constructor:**
```python
ModbusAsyncServerResource(port: ModbusPort, device: ModbusInterface)
```

**Methods:**
```python
async def process(self) -> None:
    """Async process one server cycle."""
```

## ModbusInterface

Abstract base class for device implementation.

**Methods (all raise IllegalFunctionError by default):**
```python
class ModbusInterface:
    def readCoils(self, unit: int, offset: int, count: int) -> bytes: ...
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes: ...
    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes: ...
    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes: ...
    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode: ...
    def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode: ...
    def readExceptionStatus(self, unit: int) -> bytes: ...
    def diagnostics(self, unit: int, subFunction: int, data: bytes) -> bytes: ...
    def getCommEventCounter(self, unit: int) -> bytes: ...
    def getCommEventLog(self, unit: int) -> bytes: ...
    def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode: ...
    def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode: ...
    def reportServerID(self, unit: int) -> bytes: ...
    def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode: ...
    def readWriteMultipleRegisters(self, unit: int, readOffset: int, readCount: int,
                                    writeOffset: int, writeValues: bytes) -> bytes: ...
    def readFIFOQueue(self, unit: int, offset: int) -> bytes: ...
```

## Factory Functions

### Port Creation

```python
def createPort(protocolType: ProtocolType, blocking: bool = True,
               host: str = None, port: int = None, timeout: int = None,
               portName: str = None, baudRate: int = None) -> ModbusPort:
    """Create a port of specified type."""
    pass

def createClientPort(protocolType: ProtocolType, blocking: bool = True,
                     host: str = None, port: int = None, timeout: int = None,
                     portName: str = None, baudRate: int = None) -> ModbusClientPort:
    """Create a client port with optional configuration."""
    pass

def createServerPort(device: ModbusInterface, protocolType: ProtocolType,
                     blocking: bool = False, host: str = None, port: int = None,
                     timeout: int = None, portName: str = None, 
                     baudRate: int = None, maxconn: int = None) -> Union[ModbusTcpServer, ModbusServerResource]:
    """Create a server port."""
    pass

def createAsyncClientPort(protocolType: ProtocolType,
                          host: str = None, port: int = None, timeout: int = None,
                          portName: str = None, baudRate: int = None) -> ModbusAsyncClientPort:
    """Create an async client port."""
    pass

def createAsyncServerPort(device: ModbusInterface, protocolType: ProtocolType,
                          host: str = None, port: int = None, timeout: int = None,
                          portName: str = None, baudRate: int = None,
                          maxconn: int = None) -> Union[ModbusAsyncTcpServer, ModbusAsyncServerResource]:
    """Create an async server port."""
    pass
```

## Utility Functions

### Bit Operations

```python
def getBit(bit_buff: Union[bytes, bytearray], bit_num: int) -> bool:
    """Get single bit from buffer."""

def setBit(bit_buff: bytearray, bit_num: int, value: bool) -> None:
    """Set single bit in buffer."""

def getBits(bit_buff: Union[bytes, bytearray], bit_num: int, bit_count: int) -> List[bool]:
    """Get multiple bits from buffer."""

def setBits(bit_buff: bytearray, bit_num: int, bit_count: int, bool_buff: List[bool]) -> None:
    """Set multiple bits in buffer."""
```

### Time Functions

```python
def timer() -> int:
    """Get current time in milliseconds."""

def timerDiff(start_time: int) -> int:
    """Get time difference in milliseconds since start_time."""
```

## Signal/Slot System

### Signal Class

```python
class Signal:
    def connect(self, callback: Callable) -> None:
        """Connect callback to signal."""
        
    def disconnect(self, callback: Callable) -> None:
        """Disconnect callback from signal."""
        
    def emit(self, *args) -> None:
        """Emit signal with arguments."""
```

**Example:**
```python
def on_tx(source: str, data: bytes):
    print(f"{source}: {data.hex()}")

port.signalTx.connect(on_tx)
```
