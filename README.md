# libmodbuspy

## Overview

`libmodbuspy` is a free, open-source Modbus library written in Python.
It implements client and server functions for TCP, RTU and ASCII versions of Modbus Protocol.
It is a Python implementation of the [ModbusLib](https://github.com/serhmarch/ModbusLib) C++ library.

Library implements such Modbus functions as:
* `1`  (`0x01`) - `READ_COILS`
* `2`  (`0x02`) - `READ_DISCRETE_INPUTS`
* `3`  (`0x03`) - `READ_HOLDING_REGISTERS`
* `4`  (`0x04`) - `READ_INPUT_REGISTERS`
* `5`  (`0x05`) - `WRITE_SINGLE_COIL`
* `6`  (`0x06`) - `WRITE_SINGLE_REGISTER`
* `7`  (`0x07`) - `READ_EXCEPTION_STATUS`
* `8`  (`0x08`) - `DIAGNOSTICS`
* `11` (`0x0B`) - `GET_COMM_EVENT_COUNTER`
* `12` (`0x0C`) - `GET_COMM_EVENT_LOG`
* `15` (`0x0F`) - `WRITE_MULTIPLE_COILS`
* `16` (`0x10`) - `WRITE_MULTIPLE_REGISTERS`
* `17` (`0x11`) - `REPORT_SERVER_ID`
* `22` (`0x16`) - `MASK_WRITE_REGISTER`
* `23` (`0x17`) - `READ_WRITE_MULTIPLE_REGISTERS`
* `24` (`0x18`) - `READ_FIFO_QUEUE`

## Using Library

### Common usage

To start using this library you must import `ModbusClientPort` (`ModbusClient`) or
`ModbusServerResource`(`ModbusTcpServer`) classes (of course after install the package).
`libmodbuspy` module contains declarations of main data types, functions and class interfaces
to work with the library.

Here are some common ways to use `libmodbuspy`:

* **TCP, RTU, ASCII Clients** - Communicate with devices over TCP/IP or serial ports
* **TCP, RTU, ASCII Servers** - Create Modbus TCP, RTU, or ASCII servers to handle client requests
* **Blocking Mode** - Simple synchronous operations that wait for completion
* **Non-blocking Mode** - If function can not complete operation immediately it returns `None`
* **Async/await** - Use `asyncio` for modern Python async programming
* **Signal/Slot** - Connect callbacks to monitor data transmission and events
* **Formatting Functions** - Use `struct` module format strings for data conversion
* **Multiple Clients** - Manage multiple Modbus units through a single port connection

The library provides several features applicable to both client and server implementations:

* **Multiple Protocol Support** - TCP, RTU, and ASCII protocols
* **Flexible Port Configuration** - Customizable TCP and serial port settings
* **Blocking and Non-blocking Modes** - Choose blocking or non-blocking operation
* **Comprehensive Error Handling** - Detailed exception types and status codes
* **Signal/Slot Mechanism** - Qt-like callbacks for monitoring events and data transmission
* **Data Formatting** - Built-in struct module integration for data conversion
* **Automatic Resource Management** - Simplified connection and resource handling
* **CRC/LRC Validation** - Automatic checksum calculation and validation
* **Configurable Timeouts** - Set custom timeout values for operations
* **Exception Handling** - Standardized Modbus exception support
* **Python 3.7+ Compatible** - Modern Python async/await support available

### Blocking mode

Library supports both blocking and non-blocking modes of operation.
When creating port object user can specify `blocking` parameter in the constructor.
If `blocking` is set to `True` then port will operate in blocking mode.

Blocking mode is standard function call that waits until operation is completed
and returns result or raises an exception. 
```python
from libmodbuspy import ModbusClientPort, ModbusTcpPort, ModbusException
tcp = ModbusTcpPort(blocking=True)
port = ModbusClientPort(tcp)
try:
    # `buff` is `bytes` object that contains uint16 (little-endian) array of read values
    buff = port.readHoldingRegisters(unit=1, offset=0, count=10)
    print(f"Read data: {buff}")
    # process `buff` e.g. using `struct` module
except ModbusException as ex:
    print(f"Modbus error: {ex}")
```

### Non-blocking mode

When `blocking` parameter is set to `False` then port will operate in non-blocking mode.
Non-blocking mode is much the same as blocking mode, but function call returns immediately
with `None` value if operation is not completed yet and user must call the function again
later until resulting data is returned or an exception raises in case of error.

```python
import time
from libmodbuspy import ModbusClientPort, ModbusTcpPort, ModbusException
tcp = ModbusTcpPort(blocking=False)
port = ModbusClientPort(tcp)
while True:
    try:
        buff = port.readHoldingRegisters(unit=1, offset=0, count=10)
        # `buff` is `bytes` object that contains uint16 (little-endian) array of read values
        if buff is not None:
            print(f"Read data: {buff}")
        # process `buff` e.g. using `struct` module
    except ModbusException as ex:
        print(f"Modbus error: {ex}")
    do_some_other_work()
    time.sleep(0.001)
```

TCP server is designed to work in single thread so it uses only non-blocking mode.

### asyncio

Library supports `asyncio` module to work with asynchronous programming.
The library provides async-compatible functions and coroutines that integrate seamlessly with
Python's event loop, allowing non-blocking I/O operations.
You can use the library's async APIs to handle concurrent tasks efficiently without spawning multiple threads. 
The implementation follows standard `asyncio` patterns, making it easy to combine with other async libraries 
and frameworks.

### Modbus Interface

`ModbusInterface` is the main interface that defines all supported Modbus functions.
ModbusClientPort implements this interface directly and can be used as Modbus client.
 
User can implement this interface to create own Modbus device and Modbus server will
transfer all incoming requests to this interface.

`ModbusInterface` defined as class where each function raises 
`libmodbuspy.exceptions.IllegalFunctionError` by default:
```python
class ModbusInterface:
    def readCoils(self, unit: int, offset: int, count: int) -> bytes: # ...
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes: # ...
    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes: # ...
    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes: # ...
    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode: # ...
    def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode: # ...
    def readExceptionStatus(self, unit: int) -> bytes: # ...
    def diagnostics(self, unit: int, subFunction: int, data: bytes) -> bytes: # ...
    def getCommEventCounter(self, unit: int) -> bytes: # ...
    def getCommEventLog(self, unit: int) -> bytes: # ...
    def writeMultipleCoils(self, unit: int, offset: int, values: bytes, count: int = -1) -> StatusCode: # ...
    def writeMultipleRegisters(self, unit: int, offset: int, values: bytes) -> StatusCode: # ...
    def reportServerId(self, unit: int) -> bytes: # ...
    def maskWriteRegister(self, unit: int, offset: int, andMask: int, orMask: int) -> StatusCode: # ...
    def readWriteMultipleRegisters(self, unit: int, readOffset: int, readCount: int, writeOffset: int, writeValues: bytes) -> bytes: # ...
    def readFifoQueue(self, unit: int, offset: int) -> bytes: # ...
```
### Client

`ModbusClientPort` implements Modbus interface directly and can be used very simple:
```python
from libmodbuspy import ModbusClientPort, ModbusTcpPort, ModbusException
#...
def main():
    tcp = ModbusTcpPort(blocking=True)
    tcp.Host = "someadr.plc"
    tcp.Port = 502  # STANDARD_TCP_PORT
    tcp.Timeout = 3000
    port = ModbusClientPort(tcp)
    unit = 1
    offset = 0
    count = 10
    try:
        # `buff` is `bytes` object that contains uint16 (little-endian) array of read values
        buff = port.readHoldingRegisters(unit, offset, count)
        # process `buff` e.g. using `struct` module
        # ...
    except ModbusException as ex:
        print(f"Modbus error: {ex}")
#...
```

User doesn't need to create any connection or open any port manually,
library makes it automatically.

User can use `ModbusClient` class to simplify Modbus function's interface (don't need to use `unit` parameter):
```python
from libmodbuspy import ModbusClient, ModbusClientPort, ModbusTcpPort, ModbusException
#...
def main():
    #...
    tcp = ModbusTcpPort(blocking=True)
    tcp.Host = "someadr.plc"
    tcp.Port = 502  # STANDARD_TCP_PORT
    tcp.Timeout = 3000
    port = ModbusClientPort(tcp)
    c1 = ModbusClient(1, port)
    c2 = ModbusClient(2, port)
    c3 = ModbusClient(3, port)
    while True:
        try:
            buff1 = c1.readHoldingRegisters(0, 10)
            buff2 = c2.readHoldingRegisters(0, 10)
            buff3 = c3.readHoldingRegisters(0, 10)
            # process results...
            time.sleep(0.001)
        except ModbusException as ex:
            print(f"Modbus error: {ex}")
    #...
#...
```
In this example 3 clients with unit address 1, 2, 3 are used.
User doesn't need to manage their common resource `port`. Library makes it automatically.
First `c1` client owns `port`, then when finished resource transferred to `c2` and so on.

#### Formatting methods

`ModbusClientPort` and `ModbusClient` classes have special formatting versions 
of Modbus interface functions which have suffix `F` in their names:
```python
def readCoilsF(self, unit: int, offset: int, count: int, fmt: str='<H') -> Tuple: #...
def readDiscreteInputsF(self, unit: int, offset: int, count: int, fmt: str='<H') -> Tuple: #...
def readHoldingRegistersF(self, unit: int, offset: int, count: int, fmt: str='<H') -> Tuple: #...
def readInputRegistersF(self, unit: int, offset: int, count: int, fmt: str='<H') -> Tuple: #...
def writeMultipleCoilsF(self, unit: int, offset: int, values: Tuple, count: int = -1, fmt: str='<H') -> StatusCode: #...
def writeMultipleRegistersF(self, unit: int, offset: int, values: Tuple, fmt: str='<H') -> StatusCode: 
def readWriteMultipleRegistersF(self, unit: int, readOffset: int, readCount: int,
                                writeOffset: int, writeValues: Tuple, fmt: str='<H') -> Tuple: #...
```

Specified `fmt` parameter is used to pack/unpack data using `struct` module format strings.
Format is defined using 1 or 2 symbol string for each value in the output tuple of formatted values.
Formatted values are returned as Python `tuple` object for read-methods,
and accepted as tuple `values` parameter for write-methods.

For example `'<H'` format string means little-endian (`<`) unsigned short (`H`).

#### Async client

`ModbusClientPort` class has special async counterpart: `ModbusAsyncClientPort`.
Thise class implements same Modbus interface functions as their synchronous counterpart,
but defined as `async` coroutines.
```python
import asyncio
from libmodbuspy import createAsyncClientPort, ModbusClient, ProtocolType

async def main():
    port = createAsyncClientPort(protocolType=ProtocolType.TCP, host="192.168.1.100")
    client = ModbusClient(unit=1, port=port)    
    buff = await client.readHoldingRegisters(0, 10)
    print(f"Read data: {buff}")

asyncio.run(main())
```

### Server

Unlike client the server does not implement `ModbusInterface` directly.
It accepts reference to `ModbusInterface` in its constructor as parameter and transfers all requests
to this interface. So user can define by itself how incoming Modbus-request will be processed:
```python
from libmodbuspy import createServerPort, ModbusInterface, ProtocolType, StatusCode
from libmodbuspy import ModbusException
from libmodbuspy.exceptions import (IllegalDataAddressError,
                                 GatewayPathUnavailableError)
#...
class MyModbusDevice(ModbusInterface):
    MEM_SIZE = 100
    
    def __init__(self):
        super().__init__()
        self.mem4x = [0] * self.MEM_SIZE
    
    def getValue(self, offset):
        return self.mem4x[offset]
    
    def setValue(self, offset, value):
        self.mem4x[offset] = value
    
    def readHoldingRegisters(self, unit, offset, count):
        if unit != 1:
            raise GatewayPathUnavailableError(f"Invalid unit: {unit}")
        if (offset + count) <= self.MEM_SIZE:
            # Convert register values to bytes
            result = bytearray()
            for i in range(count):
                reg_value = self.mem4x[offset + i]
                result.extend(reg_value.to_bytes(2, 'big'))
            return bytes(result)
        raise IllegalDataAddressError(f"Invalid readHoldingRegisters params: offset={offset}, count={count}")
#...

def main():
    device = MyModbusDevice()
    port = createServerPort(device, ProtocolType.TCP, blocking=False, port=502, # STANDARD_TCP_PORT
                                                                      timeout=3000,
                                                                      maxconn=10)
    c = 0
    while True:
        try:
            port.process()
        except ModbusException as ex:
            print(f"Error: {ex}")
        c = (c + 1) % 65536
        device.setValue(0, c)
        time.sleep(0.001)
#...
```

In this example `MyModbusDevice` ModbusInterface class was created.
It implements only single function: `readHoldingRegisters` (`0x03`).
All other functions will raise `modpuspy.exceptions.IllegalFunctionError` by default.

This example creates Modbus TCP server that processes connections and increments
first 4x register by 1 every cycle. This example uses non-blocking mode.

#### Async server

`ModbusServerResource` and `ModbusTcpServer` classes have special async counterparts: 
`ModbusAsyncServerResource` and `ModbusAsyncTcpServer` respectively.
These classes derived from their synchronous counterparts reimplementing `process` method
as `async` coroutine. `ModbusAsyncServerResource` accepts reference to `ModbusInterface`
in its constructor as parameter and transfers all requests to this interface.
So user can define by itself how incoming Modbus-request will be processed.
```python
import asyncio
from libmodbuspy import createAsyncServerPort, ModbusInterface, ProtocolType, StatusCode
from libmodbuspy.exceptions import IllegalDataAddressError

class MyExampleDevice(ModbusInterface):
    def __init__(self):
        self.registers = [0] * 100
    
    def readHoldingRegisters(self, unit, offset, count):
        if offset + count > len(self.registers):
            raise IllegalDataAddressError("Invalid address")
        result = bytearray()
        for i in range(count):
            result.extend(self.registers[offset + i].to_bytes(2, 'little'))
        return bytes(result)
    
    def writeMultipleRegisters(self, unit, offset, values):
        count = len(values) // 2
        for i in range(count):
            self.registers[offset + i] = int.from_bytes(values[i*2:i*2+2], 'little')
        return StatusCode.Status_Good

async def main():
    device = MyExampleDevice()
    port = createAsyncServerPort(device, ProtocolType.TCP, port=502)
    while True:
        await port.process()
        await asyncio.sleep(0.001)

asyncio.run(main())
```

### Signal/slot mechanism

Library has simplified Qt-like signal/slot mechanism that can use callbacks when some signal is occurred.
User can connect function(s) or class method(s) to the predefined signal.
Callbacks will be called in the order in which they were connected.

For example `ModbusClientPort` signal/slot mechanism:
```python
from libmodbuspy import ModbusClientPort, ProtocolType, createClientPort

class Printable:
    def printTx(self, source, buff):
        print(f"{source} Tx: {buff.hex()}")

def printRx(source, buff):
    print(f"{source} Rx: {buff.hex()}")
`
def main():
    #...
    port = createClientPort(ProtocolType.TCP, blocking=True, host="someadr.plc",
                                                             port=502,
                                                             timeout=3000)
    printer = Printable()
    port.signalTx.connect(printer.printTx)
    port.signalRx.connect(printRx)
    #...
```

## Installation and Setup

### Requirements

- Python 3.7 or higher
- `pyserial` library (for serial communication)

### Install dependencies

```console
$ pip install pyserial
```

### Install library

```console
$ pip install libmodbuspy
```

### Install from source

1. **Clone repository:**
   ```console
   $ git clone https://github.com/serhmarch/libmodbuspy.git
   $ cd libmodbuspy
   ```

2. **Install in development mode:**
   ```console
   $ pip install -e .
   ```

3. **Run examples:**
   ```console
   # TCP Client
   $ cd examples/client
   $ python democlient.py --host 192.168.1.100 --port 502 --unit 1
   
   # TCP Server
   $ cd examples/server
   $ python demoserver.py --port 502   
   ```

### Using in your project

After installation, you can import and use libmodbuspy in your Python projects:

```python
from libmodbuspy import (ModbusClient,
                      ModbusClientPort,
                      ModbusTcpPort,
                      ModbusException) 

# Create TCP port
tcp = ModbusTcpPort(blocking=True)
tcp.setHost("192.168.1.100")
tcp.setPort(502)

# Create client port
port = ModbusClientPort(tcp)

# Create client
client = ModbusClient(unit=1, port=port)

# Use the client.
# No need to open port (connection) manually, library does it automatically.
try:
    data = client.readHoldingRegisters(1000, 10)
    print(f"Data bytes: {data}")
except ModbusException as e:
    print(f"Error: {e}")
```
