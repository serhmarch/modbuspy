# modbuspy

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

Library was written in Python and uses modern Python features like type hints and context managers.
To start using this library you must import `ModbusClientPort` (`ModbusClient`) or
`ModbusServerPort` modules (of course after install the package).
These modules directly or indirectly import `ModbusGlobal` main module.
`ModbusGlobal` module contains declarations of main data types, functions and class interfaces
to work with the library.

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

### Server

Unlike client the server does not implement `ModbusInterface` directly.
It accepts pointer to `ModbusInterface` in its constructor as parameter and transfers all requests
to this interface. So user can define by itself how incoming Modbus-request will be processed:
```python
from modbuspy import ModbusServerPort, ModbusInterface, TcpSettings, ProtocolType, StatusCode
#...
class MyModbusDevice(ModbusInterface):
    MEM_SIZE = 16
    
    def __init__(self):
        super().__init__()
        self.mem4x = [0] * self.MEM_SIZE
    
    def getValue(self, offset):
        return self.mem4x[offset]
    
    def setValue(self, offset, value):
        self.mem4x[offset] = value
    
    def readHoldingRegisters(self, unit, offset, count):
        if unit != 1:
            return StatusCode.Status_BadGatewayPathUnavailable, None
        if (offset + count) <= self.MEM_SIZE:
            # Convert register values to bytes
            result = bytearray()
            for i in range(count):
                reg_value = self.mem4x[offset + i]
                result.extend(reg_value.to_bytes(2, 'big'))
            return StatusCode.Status_Good, bytes(result)
        return StatusCode.Status_BadIllegalDataAddress, None

def main():
    device = MyModbusDevice()
    settings = TcpSettings()
    settings.port = 502  # STANDARD_TCP_PORT
    settings.timeout = 3000
    settings.maxconn = 10
    port = ModbusServerPort.create(device, ProtocolType.TCP, settings, False)
    c = 0
    while True:
        port.process()
        time.sleep(0.001)
        if c % 1000 == 0:
            device.setValue(0, device.getValue(0) + 1)
        c += 1
#...
```

In this example `MyModbusDevice` ModbusInterface class was created.
It implements only single function: `readHoldingRegisters` (`0x03`).
All other functions will return `StatusCode.Status_BadIllegalFunction` by default.

This example creates Modbus TCP server that processes connections and increments
first 4x register by 1 every second. This example uses non-blocking mode.

### Signal/slot mechanism

Library has simplified Qt-like signal/slot mechanism that can use callbacks when some signal is occurred.
User can connect function(s) or class method(s) to the predefined signal.
Callbacks will be called in the order in which they were connected.

For example `ModbusClientPort` signal/slot mechanism:
```python
from modbuspy import ModbusClientPort, TcpSettings, ProtocolType

class Printable:
    def printTx(self, source, buff):
        print(f"{source} Tx: {buff.hex()}")

def printRx(source, buff):
    print(f"{source} Rx: {buff.hex()}")

def main():
    #...
    settings = TcpSettings()
    settings.host = "someadr.plc"
    settings.port = 502
    settings.timeout = 3000
    port = ModbusClientPort.create(ProtocolType.TCP, settings, False)
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

### Install from source

1. **Clone repository:**
   ```console
   $ git clone https://github.com/your-repo/modbuspy.git
   $ cd modbuspy
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

After installation, you can import and use modbuspy in your Python projects:

```python
from modbuspy import ModbusClient, ModbusTcpPort, StatusCode

# Create TCP port
port = ModbusTcpPort()
port.setHost("192.168.1.100")
port.setPort(502)

# Create client
client = ModbusClient(port)
client.setUnit(1)

# Use the client
if client.open():
    try:
        status, data = client.readHoldingRegisters(0, 10)
        if status == StatusCode.Status_Good:
            print(f"Read successful: {data}")
    finally:
        client.close()
```
