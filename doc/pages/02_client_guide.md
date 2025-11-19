# Client Implementation Guide

## Overview

The libmodbuspy client implementation provides comprehensive support for 
Modbus communication with devices. The library offers both synchronous 
and asynchronous client interfaces through multiple abstraction levels.

## Client Classes

### ModbusClientPort

`ModbusClientPort` is the core client implementation that directly 
implements the `ModbusInterface`. It manages the complete 
request-response cycle, including error handling, timeouts, and state 
management.

**Key Features:**
- Implements all Modbus function codes (FC 01-24)
- Blocking and non-blocking operation modes
- Automatic connection management
- Comprehensive error handling
- Signal/slot event system
- Formatting variants for data conversion

**Constructor:**
```python
ModbusClientPort(port: ModbusPort)
```

**Parameters:**
- `port` - A `ModbusPort` instance (TCP, RTU, or ASCII)

**Example - Basic Usage:**
```python
from libmodbuspy import ModbusClientPort, ModbusTcpPort

# Create TCP port
tcp_port = ModbusTcpPort(blocking=True)
tcp_port.setHost("192.168.1.100")
tcp_port.setPort(502)

# Create client port
client_port = ModbusClientPort(tcp_port)

# Read holding registers (FC 03)
data = client_port.readHoldingRegisters(unit=1, offset=0, count=10)
print(f"Read {len(data)} bytes: {data.hex()}")
```

### ModbusClient

`ModbusClient` is a convenience wrapper around `ModbusClientPort` that eliminates the need to specify the unit identifier for every operation. It's especially useful when managing multiple Modbus devices on the same network.

**Key Features:**
- Stores unit identifier internally
- Simplified method signatures
- Support for multiple clients on single port
- Automatic port resource sharing

**Constructor:**
```python
ModbusClient(unit: int, port: ModbusClientPort)
```

**Parameters:**
- `unit` - Modbus device unit/slave address
- `port` - A `ModbusClientPort` instance

**Example - Multiple Devices:**
```python
from libmodbuspy import ModbusClient, ModbusClientPort, ModbusTcpPort

tcp_port = ModbusTcpPort(blocking=True)
tcp_port.setHost("192.168.1.100")
port = ModbusClientPort(tcp_port)

# Create clients for different units
client1 = ModbusClient(unit=1, port=port)
client2 = ModbusClient(unit=2, port=port)
client3 = ModbusClient(unit=3, port=port)

# Access devices without specifying unit each time
data1 = client1.readHoldingRegisters(0, 10)
data2 = client2.readHoldingRegisters(0, 10)
data3 = client3.readHoldingRegisters(0, 10)
```

## Port Types

### TCP Client Port

**ModbusTcpPort** - TCP protocol implementation for network communication.

**Constructor:**
```python
ModbusTcpPort(blocking: bool = True)
```

**Settings:**
```python
port = ModbusTcpPort(blocking=True)
port.setHost("192.168.1.100")    # Device IP or hostname
port.setPort(502)                 # Modbus TCP port (default: 502)
port.setTimeout(3000)             # Timeout in milliseconds
```

**Default Values:**
```python
host = "localhost"
port = 502
timeout = 3000
```

### RTU Serial Port

**ModbusRtuPort** - RTU protocol implementation for serial communication.

**Constructor:**
```python
ModbusRtuPort(blocking: bool = True)
```

**Settings:**
```python
port = ModbusRtuPort(blocking=True)
port.setPortName("COM1")          # Serial port
port.setBaudRate(9600)            # Baud rate
port.setDataBits(8)               # Data bits (5-8)
port.setParity('N')               # Parity: N/E/O
port.setStopBits(1)               # Stop bits: 1/1.5/2
port.setTimeoutFirstByte(3000)    # First byte timeout (ms)
port.setTimeoutInterByte(5)       # Inter-byte timeout (ms)
```

**Default Values:**
```python
portName = "COM1"
baudRate = 9600
dataBits = 8
parity = 'N'
stopBits = 1
timeoutFirstByte = 3000
timeoutInterByte = 5
```

### ASCII Serial Port

**ModbusAscPort** - ASCII protocol implementation for serial communication.

Uses same configuration as RTU but with ASCII frame encoding.

**Constructor:**
```python
ModbusAscPort(blocking: bool = True)
```

## Operation Modes

### Blocking Mode

In blocking mode, method calls wait until the operation completes and returns the result directly.

**Characteristics:**
- Simpler to understand and debug
- Entire thread blocks during I/O
- Returns result or raises exception immediately
- Suitable for synchronous applications

**Example:**
```python
from libmodbuspy import ModbusClientPort, ModbusTcpPort, ModbusException

tcp = ModbusTcpPort(blocking=True)
tcp.setHost("192.168.1.100")
port = ModbusClientPort(tcp)

try:
    # Method blocks until response received
    data = port.readHoldingRegisters(unit=1, offset=0, count=10)
    print(f"Success: {data.hex()}")
except ModbusException as e:
    print(f"Error: {e}")
```

### Non-Blocking Mode

In non-blocking mode, method calls return immediately. If the operation is incomplete, they return `None`. The caller must retry the operation.

**Characteristics:**
- Application maintains control loop
- Returns `None` if operation incomplete
- Allows concurrent operations in polling loop
- Higher CPU usage due to polling
- Requires polling logic in application

**Example:**
```python
import time
from libmodbuspy import ModbusClientPort, ModbusTcpPort, ModbusException

tcp = ModbusTcpPort(blocking=False)  # Non-blocking mode
tcp.setHost("192.168.1.100")
port = ModbusClientPort(tcp)

while True:
    try:
        data = port.readHoldingRegisters(unit=1, offset=0, count=10)
        if data is not None:
            print(f"Success: {data.hex()}")
            break
        # Data not ready yet, do other work
        time.sleep(0.001)
    except ModbusException as e:
        print(f"Error: {e}")
        break
```

### Async/Await Mode

Asynchronous mode provides true non-blocking I/O using Python's `asyncio`.

**ModbusAsyncClientPort** wraps the synchronous port and provides async methods.

**Characteristics:**
- True async/await syntax
- Integrates with `asyncio` event loop
- Efficient concurrent operations
- No polling overhead
- Recommended for modern applications

**Example:**
```python
import asyncio
from libmodbuspy import ModbusAsyncClientPort, ModbusTcpPort

async def main():
    tcp = ModbusTcpPort(blocking=False)
    tcp.setHost("192.168.1.100")
    port = ModbusAsyncClientPort(tcp)
    
    try:
        # await blocks coroutine, not thread
        data = await port.readHoldingRegisters(unit=1, offset=0, count=10)
        print(f"Success: {data.hex()}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
```

## Modbus Functions

### Read Functions

#### readCoils (Function Code 01)

Reads discrete outputs (coils, 0x bits).

**Signature:**
```python
def readCoils(self, unit: int, offset: int, count: int) -> bytes
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Starting coil offset (0-based)
- `count` - Number of coils to read

**Returns:**
- `bytes` - Bit array (packed 8 bits per byte)
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
# Read 16 coils starting at offset 0
coil_data = client.readCoils(0, 16)
if coil_data:
    for i in range(16):
        byte_idx = i // 8
        bit_idx = i % 8
        bit_val = (coil_data[byte_idx] >> bit_idx) & 1
        print(f"Coil {i}: {bool(bit_val)}")
```

#### readDiscreteInputs (Function Code 02)

Reads digital inputs (1x bits). Read-only version of coils.

**Signature:**
```python
def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Starting input offset (0-based)
- `count` - Number of inputs to read

**Returns:**
- `bytes` - Bit array
- `None` - In non-blocking mode if operation incomplete

#### readHoldingRegisters (Function Code 03)

Reads holding (output) 16-bit registers (4x regs).

**Signature:**
```python
def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Starting register offset (0-based)
- `count` - Number of registers to read

**Returns:**
- `bytes` - Register data (count * 2 bytes, little-endian)
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
import struct

# Read 10 registers
data = client.readHoldingRegisters(0, 10)
if data:
    # Extract as 16-bit unsigned integers (little-endian)
    registers = struct.unpack('<' + 'H' * 10, data)
    for i, value in enumerate(registers):
        print(f"Register {i}: {value}")
```

#### readInputRegisters (Function Code 04)

Reads input 16-bit registers (3x regs). Read-only version of holding registers.

**Signature:**
```python
def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Starting register offset (0-based)
- `count` - Number of registers to read

**Returns:**
- `bytes` - Register data
- `None` - In non-blocking mode if operation incomplete

### Write Functions

#### writeSingleCoil (Function Code 05)

Writes single coil (discrete output).

**Signature:**
```python
def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Coil offset (0-based)
- `value` - Boolean value to write

**Returns:**
- `StatusCode` - Operation status
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
from libmodbuspy import StatusIsGood

status = client.writeSingleCoil(0, True)
if status is not None and StatusIsGood(status):
    print("Coil written successfully")
```

#### writeSingleRegister (Function Code 06)

Writes single 16-bit register.

**Signature:**
```python
def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Register offset (0-based)
- `value` - 16-bit value to write

**Returns:**
- `StatusCode` - Operation status
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
status = client.writeSingleRegister(0, 1234)
if status is not None and StatusIsGood(status):
    print("Register written successfully")
```

#### writeMultipleCoils (Function Code 15)

Writes multiple coils.

**Signature:**
```python
def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Starting coil offset (0-based)
- `values` - Bit array (packed 8 bits per byte)
- `count` - Number of coils (-1 = determine from values size)

**Returns:**
- `StatusCode` - Operation status
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
# Write 8 coils: on, off, on, off, on, off, on, off
coil_values = bytes([0b01010101])
status = client.writeMultipleCoils(0, coil_values, 8)
```

#### writeMultipleRegisters (Function Code 16)

Writes multiple 16-bit registers.

**Signature:**
```python
def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `offset` - Starting register offset (0-based)
- `values` - Register data (count * 2 bytes, little-endian)

**Returns:**
- `StatusCode` - Operation status
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
import struct

# Write 3 registers with values 1000, 2000, 3000
register_values = struct.pack('<HHH', 1000, 2000, 3000)
status = client.writeMultipleRegisters(0, register_values)
```

### Advanced Functions

#### maskWriteRegister (Function Code 22)

Performs bitwise AND/OR mask operation on single register.

**Signature:**
```python
def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode
```

**Logic:** `(current_value & and_mask) | (or_mask & ~and_mask)`

**Example:**
```python
# Set bits 4-7, clear bits 0-3
and_mask = 0x00F0  # Keep high nibble
or_mask = 0x00F0   # Set high nibble
status = client.maskWriteRegister(0, and_mask, or_mask)
```

#### readWriteMultipleRegisters (Function Code 23)

Atomically reads and writes registers in single operation.

**Signature:**
```python
def readWriteMultipleRegisters(self, unit: int, readOffset: int, readCount: int,
                                writeOffset: int, writeValues: bytes) -> bytes
```

**Parameters:**
- `unit` - Remote device unit/slave address
- `readOffset` - Starting read offset
- `readCount` - Number of registers to read
- `writeOffset` - Starting write offset
- `writeValues` - Register data to write

**Returns:**
- `bytes` - Read data
- `None` - In non-blocking mode if operation incomplete

**Example:**
```python
import struct

write_data = struct.pack('<HH', 100, 200)
read_data = client.readWriteMultipleRegisters(
    readOffset=0, readCount=5,
    writeOffset=10, writeValues=write_data
)
```

#### readExceptionStatus (Function Code 07)

Reads exception status (diagnostic function).

**Signature:**
```python
def readExceptionStatus(self, unit: int) -> bytes
```

#### diagnostics (Function Code 08)

Sends diagnostic command to device.

**Signature:**
```python
def diagnostics(self, unit: int, subfunc: int, indata: Optional[bytes]) -> bytes
```

#### readFIFOQueue (Function Code 24)

Reads contents of FIFO queue.

**Signature:**
```python
def readFIFOQueue(self, unit: int, offset: int) -> bytes
```

#### reportServerID (Function Code 17)

Gets server identification information.

**Signature:**
```python
def reportServerID(self, unit: int) -> bytes
```

## Data Formatting

### Formatting Methods

All read/write methods have corresponding formatting variants with suffix `F` that use `struct` module format strings.

**Formatting Methods:**
- `readCoilsF`
- `readDiscreteInputsF`
- `readHoldingRegistersF`
- `readInputRegistersF`
- `writeMultipleCoilsF`
- `writeMultipleRegistersF`
- `readWriteMultipleRegistersF`

**Signature Example:**
```python
def readHoldingRegistersF(self, unit: int, offset: int, count: int, fmt: str = '<H') -> Tuple
```

**Parameters:**
- `fmt` - Struct format string (default: '<H' = little-endian unsigned short, format for each tuple element)

**Returns:**
- `tuple` - Unpacked values

**Example:**
```python
# Read 3 registers as 16-bit unsigned integers (little-endian)
registers = client.readHoldingRegistersF(0, count=3, fmt='<H')
# Result: (value1, value2, value3)

# Read as signed integers
registers = client.readHoldingRegistersF(0, count=3, fmt='<h')

# Read as float (IEEE 754, 32-bit)
# Requires 2 registers per float
floats = client.readHoldingRegistersF(0, count=2, fmt='<f')
```

**Supported Format Codes:**
- `H` - Unsigned short (16-bit)
- `h` - Signed short (16-bit)
- `I` - Unsigned int (32-bit)
- `i` - Signed int (32-bit)
- `f` - Float (32-bit)
- `d` - Double (64-bit)
- `B` - Unsigned char (8-bit)
- `b` - Signed char (8-bit)

**Byte Order Prefixes:**
- `<` - Little-endian
- `>` - Big-endian
- `@` - Native

## Error Handling

### Exception Handling

```python
from libmodbuspy import ModbusClientPort, ModbusTcpPort, ModbusException

tcp = ModbusTcpPort(blocking=True)
port = ModbusClientPort(tcp)

try:
    data = port.readHoldingRegisters(unit=1, offset=0, count=10)
except ModbusException as e:
    print(f"Modbus error: {e}")
    print(f"Error code: {e.code}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Status Codes

Status codes indicate the status of last operation.
It is contained in exception as `ModbusException.code`.
Also it can be retrieved using `ModbusClientPort.lastErrorStatus()`
and `ModbusServerPort.lastErrorStatus()`.

Defintions of status codes is located in `libmodbuspy.statuscode` module.

## Signal and Callback System

### Connecting Callbacks

```python
def on_tx(source: str, buffer: bytes):
    print(f"{source} Tx: {buffer.hex()}")

def on_rx(source: str, buffer: bytes):
    print(f"{source} Rx: {buffer.hex()}")

def on_error(source: str, code: int, text: str):
    print(f"{source} Error {code}: {text}")

port.signalTx.connect(on_tx)
port.signalRx.connect(on_rx)
port.signalError.connect(on_error)
```

## Complete Examples

### TCP Client Example

```python
#!/usr/bin/env python3
from libmodbuspy import (ModbusClient, ModbusClientPort, ModbusTcpPort, 
                      ModbusException, StatusIsGood)

def main():
    # Create TCP port
    tcp = ModbusTcpPort(blocking=True)
    tcp.setHost("192.168.1.100")
    tcp.setPort(502)
    tcp.setTimeout(3000)
    
    # Create port and client
    port = ModbusClientPort(tcp)
    client = ModbusClient(unit=1, port=port)
    
    try:
        # Read 10 holding registers
        data = client.readHoldingRegisters(0, 10)
        print(f"Read data: {data.hex()}")
        
        # Write single register
        status = client.writeSingleRegister(100, 5678)
        if StatusIsGood(status):
            print("Write successful")
    except ModbusException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

### RTU Client Example

```python
#!/usr/bin/env python3
from libmodbuspy import ModbusClient, ModbusClientPort, ModbusRtuPort

def main():
    # Create RTU port
    rtu = ModbusRtuPort(blocking=True)
    rtu.setPortName("COM1")
    rtu.setBaudRate(19200)
    
    # Create port and client
    port = ModbusClientPort(rtu)
    client = ModbusClient(unit=1, port=port)
    
    # Read holding registers
    data = client.readHoldingRegisters(0, 10)
    print(f"Data: {data.hex()}")

if __name__ == "__main__":
    main()
```

### Async Client Example

```python
#!/usr/bin/env python3
import asyncio
from libmodbuspy import ModbusClient, ModbusAsyncClientPort, ModbusTcpPort

async def main():
    tcp = ModbusTcpPort(blocking=False)
    tcp.setHost("192.168.1.100")
    
    port = ModbusAsyncClientPort(tcp)
    client = ModbusClient(unit=1, port=port)
    
    try:
        data = await client.readHoldingRegisters(0, 10)
        print(f"Data: {data.hex()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```
