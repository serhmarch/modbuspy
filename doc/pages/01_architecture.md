# modbuspy Architecture

## Overview

modbuspy is a comprehensive Modbus library for Python that implements client and server functionality for TCP, RTU, and ASCII protocols. The library is structured following object-oriented principles with clear separation of concerns.

## Core Design Principles

### 1. **Protocol Abstraction**
All protocol implementations (TCP, RTU, ASCII) share a common interface through abstract base classes:
- `ModbusPort` - Abstract interface for low-level communication
- `ModbusClientPort` - Abstract interface for client-side operations
- `ModbusServerPort` - Abstract interface for server-side operations

### 2. **Interface-Based Design**
- `ModbusInterface` - Defines all supported Modbus functions (FC 01-24)
- Client implementations delegate to this interface
- Server implementations accept objects implementing this interface

### 3. **Blocking and Non-Blocking Modes**
- All operations support both blocking and non-blocking modes
- Blocking mode: Waits for completion, returns result or raises exception
- Non-blocking mode: Returns `None` if operation incomplete, continues execution

### 4. **Async/Await Support**
- `ModbusAsyncClientPort` - Async wrapper around `ModbusClientPort`
- `ModbusAsyncTcpServer` - Async version of TCP server
- Uses Python's `asyncio` for true asynchronous operations

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│         Application Layer                       │
│  (User code, examples, applications)            │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│         Client/Server Layer                     │
│  ModbusClient, ModbusClientPort                 │
│  ModbusTcpServer, ModbusServerResource          │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│         Protocol Layer                          │
│  ModbusTcpPort, ModbusRtuPort, ModbusAscPort    │
│  Handles framing, checksums, serialization      │
└──────────────┬──────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────┐
│         Transport Layer                         │
│  Socket (TCP), Serial Port (RTU/ASCII)          │
│  Low-level I/O operations                       │
└─────────────────────────────────────────────────┘
```

## Core Components

### Port Classes

#### Base Classes
- **`ModbusPort`** - Abstract base class for all port types
  - Handles connection state management
  - Defines protocol-independent interface
  - Supports blocking/non-blocking modes

- **`ModbusClientPort`** - Base client port implementation
  - Implements `ModbusInterface`
  - Manages request/response state machine
  - Handles error recovery and timeouts
  - Provides signal/slot callbacks

- **`ModbusServerPort`** - Base server port implementation
  - Accepts `ModbusInterface` for request processing
  - Manages incoming connections
  - Handles protocol parsing and response generation

#### Protocol-Specific Implementations

**TCP Protocol:**
- `ModbusTcpPort` - Client TCP port
- `ModbusTcpServer` - Multi-connection TCP server
- Uses socket I/O for communication

**Serial Protocol (RTU/ASCII):**
- `ModbusSerialPort` - Base serial port class
- `ModbusRtuPort` - RTU protocol implementation
- `ModbusAscPort` - ASCII protocol implementation
- Uses `pyserial` library for I/O

### Client Classes

#### `ModbusClient`
- Wrapper around `ModbusClientPort`
- Stores unit identifier (slave address)
- Simplifies API by eliminating unit parameter
- Enables multiple clients on single port

```python
# Example: Multiple clients sharing single port
port = ModbusClientPort(tcp_port)
client1 = ModbusClient(unit=1, port=port)
client2 = ModbusClient(unit=2, port=port)
```

#### `ModbusClientPort`
- Implements Modbus client functionality
- Manages request/response lifecycle
- Supports all Modbus function codes via `ModbusInterface`
- Handles blocking and non-blocking modes
- Internally controls inner `ModbusPort` object
  in protocol-independent manner

#### `ModbusAsyncClientPort`
- Async wrapper around `ModbusClientPort`
- Returns `AwaitableMethod` objects
- Integrates with Python's `asyncio`
- True non-blocking async/await syntax

### Server Classes

#### `ModbusServerPort`
- Base server port implementation
- Manages incoming requests
- Delegates processing to `ModbusInterface` implementation

#### `ModbusTcpServer`
- Manages multiple concurrent TCP connections
- Inherits from `ModbusServerPort`
- Handles client acceptance and routing
- Per-connection state management

#### `ModbusServerResource`
- Generic server resource for RTU/ASCII
- Inherits from `ModbusServerPort`
- Manages serial port communication
- Manages single TCP connection

#### `ModbusAsyncTcpServer` / `ModbusAsyncServerResource`
- Async versions of server implementations
- Support parallel connection handling
- Integrate with `asyncio` event loop

### Interface Classes

#### `ModbusInterface`
- Abstract base defining all supported Modbus functions
- Default implementations raise `IllegalFunctionError`
- User implementations handle actual data processing
- Supports both sync and async operations

Methods include:
- Read functions: `readCoils`, `readDiscreteInputs`, `readHoldingRegisters`, `readInputRegisters`
- Write functions: `writeSingleCoil`, `writeSingleRegister`, `writeMultipleCoils`, `writeMultipleRegisters`
- Advanced: `diagnostics`, `maskWriteRegister`, `readWriteMultipleRegisters`, `readFIFOQueue`

## Data Flow

### Client Request Flow (Synchronous)

```
User Code
    ↓
ModbusClient / ModbusClientPort (blocking mode)
    ↓
Protocol Layer (ModbusTcpPort / ModbusRtuPort / ModbusAscPort)
    ↓
Frame construction (serialization)
    ↓
CRC/LRC calculation
    ↓
Transport Layer (Socket / Serial)
    ↓
[Network / Serial Line]
    ↓
Server receives request
    ↓
Response generation
    ↓
Frame transmission back to client
    ↓
Client receives response
    ↓
Response validation (CRC/LRC)
    ↓
Data extraction and return to user
```

### Server Request Processing Flow

```
Accept Connection
    ↓
Read incoming data
    ↓
Parse frame (CRC/LRC validation)
    ↓
Extract function code and parameters
    ↓
Call ModbusInterface method
    ↓
Generate response
    ↓
Frame construction
    ↓
CRC/LRC calculation
    ↓
Send response
    ↓
Close or await next request
```

## State Machine Design

### Client Port State Machine

The client port operates through distinct states:
- **Idle** - Port is open, no operation in progress
- **Waiting** - Request sent, awaiting server response
- **Processing** - Response received, validating and extracting data
- **Error** - Error occurred, error state active until cleared
- **Closed** - Port is closed, no operations allowed

Transitions occur based on operation calls, timeouts, and response completion. In blocking mode, the state machine advances automatically until completion. In non-blocking mode, the application checks state between poll cycles.

### Server Port State Machine

The server port manages connection and request handling:
- **Listening** - Server accepting incoming connections
- **Connected** - Client connection established
- **Receiving** - Reading incoming request data
- **Processing** - Parsing request and executing interface method
- **Transmitting** - Sending response back to client
- **Closed** - Connection or server closed

For TCP servers, each connection maintains independent state. For serial resources, a single connection state is managed. State transitions are event-driven by socket/serial I/O completion and timeout conditions.

## Signal/Slot Mechanism

modbuspy implements a Qt-like signal/slot system for event callbacks:

**Port Signals:**
- `signalOpened` - Emitted when port opens
- `signalClosed` - Emitted when port closes
- `signalTx` - Emitted before transmitting data
- `signalRx` - Emitted after receiving data
- `signalError` - Emitted on error

**Callback Signature:**
```python
def callback(source: str, buff: bytes) -> None:
    pass

# For error signal:
def on_error(source: str, code: int, text: str) -> None:
    pass
```

## Error Handling

### Exception Hierarchy

```
ModbusException (Base)
├── StandardError (Modbus standard exceptions)
│   ├── IllegalFunctionError
│   ├── IllegalDataAddressError
│   ├── IllegalDataValueError
│   ├── ServerDeviceFailureError
│   └── ... (more standard errors)
├── CommonError (Common errors)
│   ├── EmptyResponseError
│   ├── NotCorrectRequestError
│   └── ... (more common errors)
└── ProtocolError (Protocol-specific)
    ├── SerialError
    │   ├── AscError
    │   └── RtuError
    ├── TCPError
    └── ... (protocol-specific)
```

### Status Codes

`StatusCode` enum provides detailed status information:
- `Status_Good` - Successful operation
- `Status_Processing` - Operation in progress (non-blocking mode)
- `Status_Bad` - Error occurred
- `Status_Uncertain` - Unknown status

## Module Organization

```
modbuspy/
├── __init__.py              # Package exports
├── mbglobal.py              # Global definitions, constants, utilities
├── mbconfig.py              # Configuration structures
├── mbobject.py              # Base object class with signals
├── statuscode.py            # Status codes and utilities
├── exceptions.py            # Exception classes
├── mbinterface.py           # ModbusInterface base class
├── port.py                  # ModbusPort abstract base
├── clientport.py            # ModbusClientPort implementation
├── client.py                # ModbusClient wrapper
├── tcpport.py               # TCP protocol implementation
├── serialport.py            # Serial port base class
├── rtuport.py               # RTU protocol implementation
├── ascport.py               # ASCII protocol implementation
├── serverport.py            # ModbusServerPort base
├── serverresource.py        # Server resource for RTU/ASCII
├── tcpserver.py             # TCP server implementation
└── utils.py                 # Utility functions
```

## Key Design Patterns

### 1. **State Machine Pattern**
All port implementations use state machines for managing connection and operation lifecycle.

### 2. **Factory Pattern**
`utils.py` provides factory functions for creating ports:
- `createPort()`
- `createClientPort()`
- `createServerPort()`
- `createAsyncClientPort()`
- `createAsyncServerPort()`

### 3. **Template Method Pattern**
Base classes define operation flow, subclasses implement protocol-specific details.

### 4. **Observer Pattern**
Signal/slot mechanism provides event notification similar to Qt's observer pattern.

### 5. **Wrapper Pattern**
- `ModbusClient` wraps `ModbusClientPort`
- `ModbusAsyncClientPort` wraps `ModbusClientPort` for async operations

## Performance Considerations

### Blocking Mode
- Suitable for single-threaded applications
- Entire thread blocks until operation completes
- Simple to implement and debug

### Non-Blocking Mode
- Polling-based operation checking
- Application maintains control loop
- Higher CPU usage due to polling
- Suitable for embedded systems

### Async Mode
- True async/await integration with `asyncio`
- Efficient for I/O-bound operations
- Supports concurrent operations
- Recommended for modern Python applications

## Thread Safety

Currently, modbuspy is **not thread-safe**:
- Each port instance should be used by single thread
- Multiple threads require separate port instances
- For concurrent operations, use async implementations

## Summary

The modbuspy architecture provides:
- **Flexibility** through multiple abstraction layers
- **Extensibility** via inheritance and factory patterns
- **Compatibility** with blocking, non-blocking, and async modes
- **Maintainability** through clear separation of concerns
- **Reliability** with comprehensive error handling
