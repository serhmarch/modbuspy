# Server Implementation Guide

## Overview

The libmodbuspy server implementation allows you to create Modbus servers 
that respond to client requests. The library provides both synchronous 
and asynchronous server implementations, supporting TCP, RTU, and ASCII 
protocols.

## Server Architecture

### Design Principle

Server implementations in libmodbuspy follow a clean separation of concerns:

1. **Server Port** - Handles protocol, framing, connection management
2. **ModbusInterface** - User-implemented device logic

The server accepts user-defined objects implementing `ModbusInterface` 
and delegates all Modbus function requests to them.

```
Client Request
    ↓
Server Port (ModbusTcpServer / ModbusServerResource)
    ↓
Protocol Processing (TCP/RTU/ASCII)
    ↓
User ModbusInterface Implementation
    ↓
Device Logic / Memory Access
    ↓
Response Generation
    ↓
Client Response
```

## Server Classes

### ModbusTcpServer

Multi-connection TCP server that handles multiple simultaneous client connections.

**Features:**
- Multi-client support
- Asynchronous connection handling (via socket polling)
- Configurable connection limits
- Automatic connection cleanup
- Connection event notifications

**Constructor:**
```python
ModbusTcpServer(device: ModbusInterface)
```

**Parameters:**
- `device` - Object implementing `ModbusInterface`

**Key Methods:**
```python
# Configuration
server.setPort(502)              # TCP listening port
server.setTimeout(3000)          # Timeout in milliseconds
server.setMaxConnections(10)     # Maximum simultaneous connections
server.setHost("0.0.0.0")        # Listening interface

# Operation
server.process()                 # Process one cycle

# Signals
server.signalNewConnection.connect(callback)
server.signalCloseConnection.connect(callback)
server.signalError.connect(callback)
server.signalTx.connect(callback)
server.signalRx.connect(callback)
```

**Example:**
```python
from libmodbuspy import ModbusTcpServer, ModbusInterface, StatusCode
from libmodbuspy.exceptions import IllegalDataAddressError

class MyDevice(ModbusInterface):
    def __init__(self):
        self.memory = [0] * 100
    
    def readHoldingRegisters(self, unit, offset, count):
        if offset + count > len(self.memory):
            raise IllegalDataAddressError("Invalid address")
        result = bytearray()
        for i in range(count):
            value = self.memory[offset + i]
            result.extend(value.to_bytes(2, 'little'))
        return bytes(result)

device = MyDevice()
server = ModbusTcpServer(device)
server.setPort(502)
server.setTimeout(3000)
server.setMaxConnections(10)

# Main loop
while True:
    server.process()
    time.sleep(0.001)
```

### ModbusServerResource

Generic server implementation for RTU and ASCII protocols over serial connections.

**Features:**
- Serial port communication
- Single-connection support
- Protocol-specific framing (RTU/ASCII)
- CRC/LRC validation

**Constructor:**
```python
ModbusServerResource(port: ModbusPort, device: ModbusInterface)
```

**Parameters:**
- `port` - Serial port instance (ModbusRtuPort or ModbusAscPort)
- `device` - Object implementing `ModbusInterface`

**Key Methods:**
```python
server.process()                 # Process one cycle
server.close()                   # Close serial port
```

**Example - RTU Server:**
```python
from libmodbuspy import ModbusServerResource, ModbusRtuPort, ModbusInterface, StatusCode

class MyDevice(ModbusInterface):
    def __init__(self):
        self.memory = [0] * 100
    
    def readHoldingRegisters(self, unit, offset, count):
        # Implementation...
        pass

rtu_port = ModbusRtuPort(blocking=False)
rtu_port.setPortName("COM1")
rtu_port.setBaudRate(9600)

device = MyDevice()
server = ModbusServerResource(rtu_port, device)

while True:
    server.process()
    time.sleep(0.001)
```

### Async Server Classes

#### ModbusAsyncTcpServer

Async version of ModbusTcpServer using `asyncio`.

**Constructor:**
```python
ModbusAsyncTcpServer(device: ModbusInterface)
```

**Key Methods:**
```python
async def process():             # Async process method
    await server.process()
```

**Example:**
```python
import asyncio
from libmodbuspy import ModbusAsyncTcpServer, ModbusInterface

class MyDevice(ModbusInterface):
    # Implementation...
    pass

async def main():
    device = MyDevice()
    server = ModbusAsyncTcpServer(device)
    server.setPort(502)
    
    while True:
        await server.process()
        await asyncio.sleep(0.001)

asyncio.run(main())
```

#### ModbusAsyncServerResource

Async version of ModbusServerResource for RTU/ASCII.

**Constructor:**
```python
ModbusAsyncServerResource(port: ModbusPort, device: ModbusInterface)
```

**Example:**
```python
import asyncio
from libmodbuspy import ModbusAsyncServerResource, ModbusRtuPort, ModbusInterface

class MyDevice(ModbusInterface):
    # Implementation...
    pass

async def main():
    rtu = ModbusRtuPort(blocking=False)
    rtu.setPortName("COM1")
    
    device = MyDevice()
    server = ModbusAsyncServerResource(rtu, device)
    
    while True:
        await server.process()
        await asyncio.sleep(0.001)

asyncio.run(main())
```

## Implementing ModbusInterface

To create a server, you must implement the `ModbusInterface` class. This class defines the actual device behavior and data storage.

### Interface Methods

#### Read Methods

##### readCoils (Function Code 01)

Reads discrete outputs (coils, 0x bits).

**Signature:**
```python
def readCoils(self, unit: int, offset: int, count: int) -> bytes
```

**Returns:**
- `bytes` - Bit array (packed 8 bits per byte)

**Raises:**
- `ModbusException` - On error (e.g., `IllegalDataAddressError`)

**Example:**
```python
def readCoils(self, unit, offset, count):
    if unit != 1:
        raise GatewayPathUnavailableError("Invalid unit")
    if offset + count > len(self.coils):
        raise IllegalDataAddressError("Invalid address")
    
    # Pack bits into bytes
    byte_count = (count + 7) // 8
    result = bytearray(byte_count)
    for i in range(count):
        bit_idx = i % 8
        byte_idx = i // 8
        if self.coils[offset + i]:
            result[byte_idx] |= (1 << bit_idx)
    
    return bytes(result)
```

##### readDiscreteInputs (Function Code 02)

Reads digital inputs (1x bits). Read-only version of coils.

**Signature:**
```python
def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes
```

##### readHoldingRegisters (Function Code 03)

Reads holding registers (4x regs).

**Signature:**
```python
def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes
```

**Returns:**
- `bytes` - Register data (count * 2 bytes, little-endian)

**Example:**
```python
def readHoldingRegisters(self, unit, offset, count):
    if unit != 1:
        raise GatewayPathUnavailableError("Invalid unit")
    if offset + count > len(self.registers):
        raise IllegalDataAddressError("Invalid address")
    
    result = bytearray(count * 2)
    for i in range(count):
        value = self.registers[offset + i]
        result[i*2] = value & 0xFF
        result[i*2+1] = (value >> 8) & 0xFF
    
    return bytes(result)
```

##### readInputRegisters (Function Code 04)

Reads input registers (3x regs). Read-only version of holding registers.

**Signature:**
```python
def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes
```

#### Write Methods

##### writeSingleCoil (Function Code 05)

Writes single coil.

**Signature:**
```python
def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode
```

**Returns:**
- `StatusCode.Status_Good` - Success
- Other `StatusCode` - Error

**Raises:**
- `ModbusException` - On error

**Example:**
```python
from libmodbuspy import StatusCode

def writeSingleCoil(self, unit, offset, value):
    if unit != 1:
        raise GatewayPathUnavailableError("Invalid unit")
    if offset >= len(self.coils):
        raise IllegalDataAddressError("Invalid address")
    
    self.coils[offset] = bool(value)
    return StatusCode.Status_Good
```

##### writeSingleRegister (Function Code 06)

Writes single 16-bit register.

**Signature:**
```python
def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode
```

**Example:**
```python
def writeSingleRegister(self, unit, offset, value):
    if unit != 1:
        raise GatewayPathUnavailableError("Invalid unit")
    if offset >= len(self.registers):
        raise IllegalDataAddressError("Invalid address")
    
    self.registers[offset] = value & 0xFFFF
    return StatusCode.Status_Good
```

##### writeMultipleCoils (Function Code 15)

Writes multiple coils.

**Signature:**
```python
def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode
```

**Example:**
```python
def writeMultipleCoils(self, unit, offset, values, count=-1):
    if unit != 1:
        raise GatewayPathUnavailableError("Invalid unit")
    if count < 0:
        count = len(values) * 8
    if offset + count > len(self.coils):
        raise IllegalDataAddressError("Invalid address")
    
    for i in range(count):
        byte_idx = i // 8
        bit_idx = i % 8
        if byte_idx < len(values):
            bit_val = (values[byte_idx] >> bit_idx) & 1
            self.coils[offset + i] = bool(bit_val)
    
    return StatusCode.Status_Good
```

##### writeMultipleRegisters (Function Code 16)

Writes multiple registers.

**Signature:**
```python
def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode
```

**Example:**
```python
def writeMultipleRegisters(self, unit, offset, values):
    if unit != 1:
        raise GatewayPathUnavailableError("Invalid unit")
    count = len(values) // 2
    if offset + count > len(self.registers):
        raise IllegalDataAddressError("Invalid address")
    
    for i in range(count):
        value = (values[i*2] & 0xFF) | ((values[i*2+1] & 0xFF) << 8)
        self.registers[offset + i] = value
    
    return StatusCode.Status_Good
```

#### Advanced Methods

##### maskWriteRegister (Function Code 22)

Performs bitwise AND/OR mask on register.

**Signature:**
```python
def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode
```

**Logic:** `(current_value & and_mask) | (or_mask & ~and_mask)`

##### readWriteMultipleRegisters (Function Code 23)

Atomically reads and writes registers.

**Signature:**
```python
def readWriteMultipleRegisters(self, unit: int, readOffset: int, readCount: int,
                                writeOffset: int, writeValues: bytes) -> bytes
```

##### readExceptionStatus (Function Code 07)

Returns exception status bits.

**Signature:**
```python
def readExceptionStatus(self, unit: int) -> bytes
```

##### diagnostics (Function Code 08)

Handles diagnostic subfunctions.

**Signature:**
```python
def diagnostics(self, unit: int, subFunction: int, data: bytes) -> bytes
```

##### reportServerID (Function Code 17)

Returns server identification.

**Signature:**
```python
def reportServerID(self, unit: int) -> bytes
```

##### readFIFOQueue (Function Code 24)

Reads FIFO queue contents.

**Signature:**
```python
def readFIFOQueue(self, unit: int, offset: int) -> bytes
```

## Complete Server Examples

### TCP Server with Memory

```python
#!/usr/bin/env python3
"""
Complete Modbus TCP server with simulated device memory.
"""

import time
from libmodbuspy import (ModbusTcpServer, ModbusInterface, StatusCode, 
                      Constants, timer)
from libmodbuspy.exceptions import (IllegalDataAddressError,
                                 GatewayPathUnavailableError)

class SimulatedDevice(ModbusInterface):
    """Simulated Modbus device with memory storage."""
    
    def __init__(self, memory_size=100):
        self.memory = [0] * memory_size
        self.memory[0] = 1000  # Initialize first register
        self.last_write = 0
    
    def readCoils(self, unit, offset, count):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        if offset + count > len(self.memory) * 16:
            raise IllegalDataAddressError("Address out of range")
        
        byte_count = (count + 7) // 8
        result = bytearray(byte_count)
        for i in range(count):
            bit_addr = offset + i
            reg_idx = bit_addr // 16
            bit_idx = bit_addr % 16
            if (self.memory[reg_idx] >> bit_idx) & 1:
                byte_idx = i // 8
                bit_pos = i % 8
                result[byte_idx] |= (1 << bit_pos)
        
        return bytes(result)
    
    def readHoldingRegisters(self, unit, offset, count):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        if offset + count > len(self.memory):
            raise IllegalDataAddressError("Address out of range")
        
        result = bytearray(count * 2)
        for i in range(count):
            value = self.memory[offset + i]
            result[i*2] = value & 0xFF
            result[i*2+1] = (value >> 8) & 0xFF
        
        return bytes(result)
    
    def writeSingleRegister(self, unit, offset, value):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        if offset >= len(self.memory):
            raise IllegalDataAddressError("Address out of range")
        
        self.memory[offset] = value & 0xFFFF
        self.last_write = value
        return StatusCode.Status_Good
    
    def writeMultipleRegisters(self, unit, offset, values):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        count = len(values) // 2
        if offset + count > len(self.memory):
            raise IllegalDataAddressError("Address out of range")
        
        for i in range(count):
            value = (values[i*2] & 0xFF) | ((values[i*2+1] & 0xFF) << 8)
            self.memory[offset + i] = value
        
        return StatusCode.Status_Good

def on_new_connection(addr):
    print(f"New connection: {addr}")

def on_close_connection(addr):
    print(f"Closed connection: {addr}")

def on_error(source, code, text):
    print(f"Error {source} ({code}): {text}")

def main():
    # Create device
    device = SimulatedDevice(memory_size=100)
    
    # Create server
    server = ModbusTcpServer(device)
    server.setPort(502)
    server.setTimeout(3000)
    server.setMaxConnections(10)
    
    # Connect signals
    server.signalNewConnection.connect(on_new_connection)
    server.signalCloseConnection.connect(on_close_connection)
    server.signalError.connect(on_error)
    
    print("Modbus TCP Server started on port 502")
    print("-" * 50)
    
    # Main loop
    tmr = timer()
    try:
        while True:
            server.process()
            
            # Increment first register every second
            if timer() - tmr >= 1000:
                tmr = timer()
                device.memory[0] = (device.memory[0] + 1) % 65536
                print(f"Register[0]: {device.memory[0]}")
            
            time.sleep(0.001)
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    main()
```

### RTU Server

```python
#!/usr/bin/env python3
"""
Modbus RTU server over serial port.
"""

import time
from libmodbuspy import (ModbusServerResource, ModbusRtuPort, ModbusInterface,
                      StatusCode)
from libmodbuspy.exceptions import IllegalDataAddressError, GatewayPathUnavailableError

class SimpleDevice(ModbusInterface):
    def __init__(self):
        self.registers = [0] * 50
    
    def readHoldingRegisters(self, unit, offset, count):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        if offset + count > len(self.registers):
            raise IllegalDataAddressError("Invalid address")
        
        result = bytearray(count * 2)
        for i in range(count):
            value = self.registers[offset + i]
            result[i*2] = value & 0xFF
            result[i*2+1] = (value >> 8) & 0xFF
        
        return bytes(result)
    
    def writeMultipleRegisters(self, unit, offset, values):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        count = len(values) // 2
        if offset + count > len(self.registers):
            raise IllegalDataAddressError("Invalid address")
        
        for i in range(count):
            value = values[i*2] | (values[i*2+1] << 8)
            self.registers[offset + i] = value
        
        return StatusCode.Status_Good

def main():
    device = SimpleDevice()
    
    rtu = ModbusRtuPort(blocking=False)
    rtu.setPortName("COM1")      # Linux: /dev/ttyUSB0
    rtu.setBaudRate(9600)
    
    server = ModbusServerResource(rtu, device)
    
    print("RTU Server started on COM1, 9600 baud")
    
    try:
        while True:
            server.process()
            time.sleep(0.001)
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    main()
```

### Async TCP Server

```python
#!/usr/bin/env python3
"""
Asynchronous Modbus TCP server with concurrent connections.
"""

import asyncio
from libmodbuspy import ModbusAsyncTcpServer, ModbusInterface, StatusCode
from libmodbuspy.exceptions import IllegalDataAddressError

class AsyncDevice(ModbusInterface):
    def __init__(self):
        self.registers = [0] * 100
    
    def readHoldingRegisters(self, unit, offset, count):
        if offset + count > len(self.registers):
            raise IllegalDataAddressError("Invalid address")
        
        result = bytearray(count * 2)
        for i in range(count):
            value = self.registers[offset + i]
            result[i*2] = value & 0xFF
            result[i*2+1] = (value >> 8) & 0xFF
        
        return bytes(result)
    
    def writeMultipleRegisters(self, unit, offset, values):
        count = len(values) // 2
        if offset + count > len(self.registers):
            raise IllegalDataAddressError("Invalid address")
        
        for i in range(count):
            value = values[i*2] | (values[i*2+1] << 8)
            self.registers[offset + i] = value
        
        return StatusCode.Status_Good

async def main():
    device = AsyncDevice()
    server = ModbusAsyncTcpServer(device)
    server.setPort(502)
    server.setMaxConnections(20)
    
    print("Async TCP Server started on port 502")
    
    try:
        # Main event loop
        while True:
            await server.process()
            await asyncio.sleep(0.001)
    except KeyboardInterrupt:
        print("\nServer stopped")

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

### Exception Types

When implementing `ModbusInterface`, raise appropriate exceptions:

```python
from libmodbuspy.exceptions import (IllegalDataAddressError,
                                 IllegalDataValueError,
                                 GatewayPathUnavailableError,
                                 ServerDeviceFailureError)

def readHoldingRegisters(self, unit, offset, count):
    if unit not in [1, 2, 3]:
        raise GatewayPathUnavailableError(f"Unknown unit: {unit}")
    
    if offset + count > len(self.memory):
        raise IllegalDataAddressError(f"Address out of range")
    
    if offset < 0 or count <= 0:
        raise IllegalDataValueError(f"Invalid parameters")
    
    # Process request...
```

## Best Practices

### 1. Resource Management
- Always properly close ports
- Implement context managers if needed
- Clean up connections on error

### 2. Thread Safety
- libmodbuspy is not thread-safe
- Use async implementation for concurrent operations
- Or use separate port instances per thread

### 3. Performance
- Keep ModbusInterface methods fast
- Avoid I/O operations within interface methods
- Use non-blocking servers for embedded systems
- Use async servers for high-concurrency scenarios

### 4. Reliability
- Validate all input parameters
- Raise appropriate exceptions
- Implement proper error handling
- Log important events

### 5. Testing
- Test with real Modbus clients
- Use example clients to verify behavior
- Monitor network traffic for debugging
