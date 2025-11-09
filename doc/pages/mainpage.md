# modbuspy {#mainpage}

@tableofcontents

## Overview

modbuspy is a free, open-source Modbus library written in Python.
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
`modbuspy` module contains declarations of main data types, functions and class interfaces
to work with the library.

### Blocking mode

Library supports both blocking and non-blocking modes of operation.
When creating port object user can specify `blocking` parameter in the constructor.
If `blocking` is set to `True` then port will operate in blocking mode.

Blocking mode is standard function call that waits until operation is completed
and returns result or raises an exception. 
```python
from modbuspy import ModbusClientPort, ModbusTcpPort, ModbusException
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
from modbuspy import ModbusClientPort, ModbusTcpPort, ModbusException
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

### Modbus Interface

`ModbusInterface` is the main interface that defines all supported Modbus functions.
ModbusClientPort implements this interface directly and can be used as Modbus client.
 
User can implement this interface to create own Modbus device and Modbus server will
transfer all incoming requests to this interface.

`ModbusInterface` defined as class where each function raises 
`modbuspy.exceptions.IllegalFunctionError` by default:
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
from modbuspy import ModbusClientPort, ModbusTcpPort, ModbusException
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
from modbuspy import ModbusClient, ModbusClientPort, ModbusTcpPort, ModbusException
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

### Server

Unlike client the server does not implement `ModbusInterface` directly.
It accepts reference to `ModbusInterface` in its constructor as parameter and transfers all requests
to this interface. So user can define by itself how incoming Modbus-request will be processed:
```python
from modbuspy import createServerPort, ModbusInterface, ProtocolType, StatusCode
from modbuspy import ModbusException
from modbuspy.exceptions import (IllegalDataAddressError,
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
    settings = {}
    settings['port'] = 502  # STANDARD_TCP_PORT
    settings['timeout'] = 3000
    settings['maxconn'] = 10
    port = createServerPort(device, ProtocolType.TCP, settings, False)
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

### Signal/slot mechanism

Library has simplified Qt-like signal/slot mechanism that can use callbacks when some signal is occurred.
User can connect function(s) or class method(s) to the predefined signal.
Callbacks will be called in the order in which they were connected.

For example `ModbusClientPort` signal/slot mechanism:
```python
from modbuspy import ModbusClientPort, ProtocolType, createClientPort

class Printable:
    def printTx(self, source, buff):
        print(f"{source} Tx: {buff.hex()}")

def printRx(source, buff):
    print(f"{source} Rx: {buff.hex()}")

def main():
    #...
    settings = {}
    settings['host'] = "someadr.plc"
    settings['port'] = 502
    settings['timeout'] = 3000
    port = createClientPort(ProtocolType.TCP, settings, blocking=True)
    printer = Printable()
    port.signalTx.connect(printer.printTx)
    port.signalRx.connect(printRx)
    #...
```

## Protocol Support

### TCP Protocol

`modbuspy` supports Modbus TCP protocol with the following features:
- Client and server implementations
- Multiple simultaneous connections
- Automatic connection management
- Configurable timeouts and retries

### RTU Protocol

`modbuspy` supports Modbus RTU protocol with the following features:
- Binary frame format
- CRC16 checksum validation
- Timing-based frame detection
- Configurable serial port settings (baud rate, data bits, parity, stop bits)

### ASCII Protocol

modbuspy supports Modbus ASCII protocol with the following features:
- Hexadecimal frame format with colon start and CRLF end
- LRC checksum validation
- Character-based frame detection
- Configurable serial port settings

## Examples

Examples are located in `examples` folder of root directory.

### `democlient`

`democlient` example demonstrate all implemented functions for client one by one beginning
from function with lowest number and then increasing this number with predefined period and
other parameters. 
To see list of available parameters you can print next commands:
```console
$ python democlient.py -?
$ python democlient.py -help
``` 

### `demoserver`

`demoserver` example demonstrate all implemented functions for server.
It uses single block for every type of Modbus memory (0x, 1x, 3x and 4x)
and emulates value change for the first 16 bit register by incrementing it 
by 1 every 1000 milliseconds. So user can run Modbus Client to check
first 16 bit of 000001 (100001) or first register 400001 (300001) changing
every 1 second.
To see list of available parameters you can print next commands:
```console
$ python demoserver.py -?
$ python demoserver.py -help
``` 

## Documentation

Documentation is located in `doc` directory. Documentation is
automatically generated by doxygen.

## Building and Installation

### Installation from Source

1. Clone the repository:
```console
$ git clone https://github.com/your-repo/modbuspy.git
$ cd modbuspy
```

2. Install dependencies:
```console
$ pip install pyserial
```

3. Install the package:
```console
$ pip install -e .
```

### Package Structure

The modbuspy package contains the following modules:
- `modbuspy.mbconfig` - Version information and configuration
- `modbuspy.mbglobal` - Global definitions and enumerations
- `modbuspy.statuscode` - Status code definitions
- `modbuspy.exceptions` - Modbus exception classes
- `modbuspy.mbinterface` - Modbus interface definition
- `modbuspy.port` - Base port classes
- `modbuspy.tcpport` - TCP protocol implementation
- `modbuspy.serialport` - Serial port base class
- `modbuspy.rtuport` - RTU protocol implementation
- `modbuspy.ascport` - ASCII protocol implementation
- `modbuspy.clientport` - Client port implementations
- `modbuspy.client` - High-level client interface
- `modbuspy.serverport` - Base Server port definition
- `modbuspy.serverresource` - Server resource management
- `modbuspy.tcpserver` - TCP server implementation

## Features

- **Multiple Protocol Support**: TCP, RTU, and ASCII
- **Client and Server**: Both client and server implementations
- **Blocking and Non-blocking**: Support for both modes
- **Signal/Slot Mechanism**: Qt-like event handling
- **Comprehensive Error Handling**: Detailed status codes and error messages
- **Serial Communication**: Full support for RTU and ASCII over serial
- **Configurable Settings**: Extensive configuration options
- **Python 3 Compatible**: Written for Python 3.6+

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Additional Documentation

- @subpage serial "Serial Protocols (RTU/ASCII)"
- @subpage configuration "Configuration Guide"

## Support

For questions and support, please create an issue on the project repository.