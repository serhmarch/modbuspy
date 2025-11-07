# modbuspy {#mainpage}

@tableofcontents

## Overview

modbuspy is a free, open-source Modbus library written in Python. 
It implements client and server functions for TCP, RTU and ASCII versions of Modbus Protocol.
Library can work in both blocking and non-blocking mode.

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

### Common usage (Python)

Library was written in Python and provides a clean, object-oriented interface. 
To start using this library you must import `ModbusClientPort` or 
`ModbusServerPort` modules (of course after adding the library to your Python path).
These modules directly or indirectly include `ModbusGlobal` main module.
`ModbusGlobal` module contains definitions of main data types, functions and class interfaces
to work with the library.

It contains definition of `StatusCode` enumeration that defines result of 
library operations, `ModbusInterface` class interface that contains list of functions
which the library implements, `create_client_port` and `create_server_port`
functions, that creates corresponding `ModbusClientPort` and
`ModbusServerPort` main working classes.
Those classes that implements Modbus functions for the
library for client and server version of protocol, respectively.

### Client

`ModbusClientPort` implements Modbus interface directly and can be used very
simple:
```python
from modbuspy import ModbusTcpPort, ModbusConfig, StatusCode

def main():
    settings = ModbusConfig.TcpSettings(
        host="someadr.plc",
        port=502,
        timeout=3000
    )
    port = ModbusTcpPort.ModbusTcpClientPort(settings, blocking=True)
    unit = 1
    offset = 0
    count = 10
    
    status, values = port.read_holding_registers(unit, offset, count)
    if StatusCode.is_good(status):
        # process values list...
        print(f"Read values: {values}")
    else:
        print(f"Error: {port.last_error_text()}")

if __name__ == "__main__":
    main()
```

User don't need to create any connection or open any port, library makes it automatically.

User can use `ModbusClient` class to simplify Modbus function's interface (don't need to
use `unit` parameter):
```python
from modbuspy import ModbusTcpPort, ModbusClient, ModbusConfig

def main():
    settings = ModbusConfig.TcpSettings(
        host="someadr.plc",
        port=502,
        timeout=3000
    )
    port = ModbusTcpPort.ModbusTcpClientPort(settings, blocking=True)
    
    c1 = ModbusClient.ModbusClient(1, port)
    c2 = ModbusClient.ModbusClient(2, port)
    c3 = ModbusClient.ModbusClient(3, port)
    
    while True:
        s1, values1 = c1.read_holding_registers(0, 10)
        s2, values2 = c2.read_holding_registers(0, 10)
        s3, values3 = c3.read_holding_registers(0, 10)
        time.sleep(0.001)
```

In this example 3 clients with unit address 1, 2, 3 are used. 
User don't need to manage its common resource `port`.
Library make it automatically.
First `c1` client owns `port`, than when finished
resource transferred to `c2` and so on.

#### Non blocking mode

In non blocking mode Modbus function exits immediately even if remote connection 
processing is not finished. In this case function returns `StatusCode.PROCESSING`.
This is 'Arduino'-style of programming, when function must not be blocked and 
return intermediate value that indicates that function is not finished. 
Then external code call this function again and again until Good or Bad status 
will not be returned. 

Example of non blocking client:
```python
from modbuspy import ModbusTcpPort, ModbusClient, ModbusConfig, StatusCode
import time

def main():
    settings = ModbusConfig.TcpSettings(
        host="someadr.plc",
        port=502,
        timeout=3000
    )
    port = ModbusTcpPort.ModbusTcpClientPort(settings, blocking=False)
    
    c1 = ModbusClient.ModbusClient(1, port)
    c2 = ModbusClient.ModbusClient(2, port)
    c3 = ModbusClient.ModbusClient(3, port)
    
    while True:
        s1, values1 = c1.read_holding_registers(0, 10)
        s2, values2 = c2.read_holding_registers(0, 10)
        s3, values3 = c3.read_holding_registers(0, 10)
        do_some_other_stuff_in_current_thread()
        time.sleep(0.001)

if __name__ == "__main__":
    main()
```

So if user needs to check is function finished he can write:
```python
s1, values1 = c1.read_holding_registers(0, 10)
if not StatusCode.is_processing(s1):
    # function is completed...
```

#### Signal/slot mechanism

Library has simplified Qt-like signal/slot mechanism that can use callbacks when
some signal is occurred.
User can connect function(s) or class method(s) to the
predefined signal. 
Callbacks will be called in the order in which they were
connected.

For example `ModbusClientPort` signal/slot mechanism:
```python
from modbuspy import ModbusTcpPort, ModbusConfig

class Printable:
    def print_tx(self, source, buff):
        print(f"{source} Tx: {buff.hex()}")

def print_rx(source, buff):
    print(f"{source} Rx: {buff.hex()}")

def main():
    settings = ModbusConfig.TcpSettings(
        host="someadr.plc",
        port=502,
        timeout=3000
    )
    port = ModbusTcpPort.ModbusTcpClientPort(settings, blocking=False)
    printer = Printable()
    
    port.connect_signal_tx(printer.print_tx)
    port.connect_signal_rx(print_rx)

if __name__ == "__main__":
    main()
```

### Server

Unlike client the server do not implement `ModbusInterface` directly. 
It accepts pointer to `ModbusInterface` in its constructor as parameter and transfer all requests
to this interface.
So user can define by itself how incoming Modbus-request will be
processed:
```python
from modbuspy import ModbusServerPort, ModbusInterface, ModbusConfig, StatusCode

class MyModbusDevice(ModbusInterface):
    MEM_SIZE = 16
    
    def __init__(self):
        super().__init__()
        self.mem4x = [0] * self.MEM_SIZE
    
    def get_value(self, offset):
        return self.mem4x[offset]
    
    def set_value(self, offset, value):
        self.mem4x[offset] = value
    
    def read_holding_registers(self, unit, offset, count):
        if unit != 1:
            return StatusCode.BAD_GATEWAY_PATH_UNAVAILABLE, []
        if (offset + count) <= self.MEM_SIZE:
            values = self.mem4x[offset:offset + count]
            return StatusCode.GOOD, values
        return StatusCode.BAD_ILLEGAL_DATA_ADDRESS, []

def main():
    device = MyModbusDevice()
    settings = ModbusConfig.TcpSettings(
        port=502,
        timeout=3000
    )
    port = ModbusServerPort.ModbusTcpServerPort(device, settings, blocking=False)
    
    c = 0
    while True:
        port.process()
        time.sleep(0.001)
        if c % 1000 == 0:
            current_val = device.get_value(0)
            device.set_value(0, current_val + 1)
        c += 1

if __name__ == "__main__":
    main()
```

In this example `MyModbusDevice` ModbusInterface class was created.
It implements only single function: `read_holding_registers` (`0x03`).
All other functions will return `StatusCode.BAD_ILLEGAL_FUNCTION` by default.

This example creates Modbus TCP server that process connections and increment 
first 4x register by 1 every second. This example uses non blocking mode.

## Protocol Support

### TCP Protocol

modbuspy supports Modbus TCP protocol with the following features:
- Client and server implementations
- Multiple simultaneous connections
- Automatic connection management
- Configurable timeouts and retries

### RTU Protocol

modbuspy supports Modbus RTU protocol with the following features:
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

### Serial Port Examples

Serial port examples demonstrate RTU and ASCII protocol implementations:

#### `test_serial_ports.py`

Comprehensive test script showing both RTU and ASCII protocol usage:
```console
$ python test_serial_ports.py
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

- `ModbusGlobal` - Global definitions and enumerations
- `ModbusConfig` - Configuration classes for different protocols
- `ModbusPort` - Base port classes
- `ModbusTcpPort` - TCP protocol implementation
- `ModbusSerialPort` - Serial port base class
- `ModbusRtuPort` - RTU protocol implementation
- `ModbusAscPort` - ASCII protocol implementation
- `ModbusClientPort` - Client port implementations
- `ModbusClient` - High-level client interface
- `ModbusServerPort` - Server port implementations
- `ModbusServerResource` - Server resource management
- `ModbusTcpServer` - TCP server implementation
- `ModbusStatusCode` - Status code definitions

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