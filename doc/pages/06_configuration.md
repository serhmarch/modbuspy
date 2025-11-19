# Configuration & Settings Reference

## Overview

libmodbuspy provides comprehensive configuration options for different port 
types and operation modes. This guide covers all available settings, 
their defaults, and their impact on communication.

## Port Types and Base Configuration

### Common Port Settings

All port types inherit from `ModbusPort` and share these core settings:

```python
from libmodbuspy import ModbusTcpPort, ModbusRtuPort, ModbusAscPort

# Available for all port types
port.setBlocking(True)  # Blocking vs non-blocking mode
port.setTimeout(5000)   # Operation timeout (ms)
```

## TCP Port Configuration

### Connection Settings

```python
from libmodbuspy import ModbusTcpPort, ModbusClientPort

tcp = ModbusTcpPort()
client = ModbusClientPort(tcp)
client.setTries(3)           # Number of attempts

# Host and Port
tcp.setHost("192.168.1.100") # IP address or hostname
tcp.setPort(502)             # Modbus TCP port (default: 502)
                             # Secure Modbus: 802 (not standard)

# Connection Timeouts
tcp.setTimeout(3000)         # Default: 3000 ms
```

### Performance Settings

```python
tcp.setBlocking(True) # True: blocking, False: non-blocking
```

### Example: TCP Configuration

```python
from libmodbuspy import ModbusTcpPort, ModbusClientPort, ProtocolType

# Create port with configuration
tcp = ModbusTcpPort(blocking=True)
tcp.setHost("192.168.1.100")
tcp.setPort(502)
tcp.setTimeout(5000)

# Create client
client = ModbusClientPort(tcp)

# Connect
if not client.connectPort():
    print(f"Connection failed: {client.lastErrorText()}")
```

## RTU Port Configuration

### Serial Port Settings

```python
from libmodbuspy import ModbusRtuPort, ModbusClientPort

rtu = ModbusRtuPort()
client = ModbusClientPort(rtu)

# Port Selection
rtu.setPortName("COM1") # Windows: COM1-COM256
                        # Linux: /dev/ttyUSB0, /dev/ttyS0
                        # macOS: /dev/tty.usbserial-*

# Baud Rate (bits per second)
rtu.setBaudRate(9600) # Common: 9600 (default)
                      # Other: 1200, 2400, 4800, 19200, 
                      # 38400, 57600, 115200

# Data Format
from libmodbuspy import Parity, StopBits

rtu.setDataBits(8)             # Data bits: 5-8 (default: 8)
rtu.setParity(Parity.NoParity) # Parity enum values:
                               # Parity.NoParity, Parity.EvenParity,
                               # Parity.OddParity, Parity.MarkParity,
                               # Parity.SpaceParity
rtu.setStopBits(StopBits.OneStop) # Stop bits enum values:
                                  # StopBits.OneStop,
                                  # StopBits.OneAndHalfStop,
                                  # StopBits.TwoStop
```

### Timing Settings

```python
# Critical for RTU reliability
rtu.setTimeoutFirstByte(3000)        # Wait for first byte (ms)
rtu.setTimeoutInterByte(5)           # Between bytes (ms)

# Calculate timing based on baud rate
# Character time = (1 + DataBits + Parity + StopBits) / BaudRate
# At 9600 baud, 8 data bits, 1 stop bit: ~1.04 ms per character
# Quiet time = 3.5 * 1.04 ≈ 3.6 ms
```

### RTU Port Example

```python
from libmodbuspy import (ModbusRtuPort, ModbusClientPort,
                      Parity, StopBits,
                      ModbusException)

# Create and configure RTU port
rtu = ModbusRtuPort()
rtu.setPortName("COM1")
rtu.setBaudRate(9600)
rtu.setDataBits(8)
rtu.setParity(Parity.NoParity)
rtu.setStopBits(StopBits.OneStop)
rtu.setTimeoutFirstByte(3000)
rtu.setTimeoutInterByte(5)

# Create client
client = ModbusClientPort(rtu)

# Connect
try:
    # Read holding registers
    values = client.readHoldingRegisters(0, 10)
    if values:
        print(f"Registers: {values}")
except ModbusException as e:
    print(f"RTU operation failed: {client.getLastStatusCode()}")
```

## ASCII Port Configuration

### Serial Port Settings

```python
from libmodbuspy import ModbusAscPort, ModbusClientPort, Parity, StopBits

asc = ModbusAscPort()
client = ModbusClientPort(asc)

# Same serial settings as RTU
asc.setPortName("COM1")
asc.setBaudRate(9600)
asc.setDataBits(8)
asc.setParity(Parity.NoParity)
asc.setStopBits(StopBits.OneStop)

# ASCII-specific settings
asc.setTimeoutFirstByte(3000)
asc.setTimeoutInterByte(5)
```

### Data Format

```python
# ASCII automatically handles:
# - Conversion to/from ASCII hex encoding
# - LRC checksum calculation
# - CR LF line termination
# - All transparent to user
```

## Client Port Configuration

### ModbusClientPort Settings

```python
from libmodbuspy import ModbusClientPort, ModbusTcpPort

port = ModbusTcpPort()
client = ModbusClientPort(port)

# Request Management
client.setTries(3)                   # Number of retry attempts
client.setBroadcastEnabled(True)     # Enable/disable broadcast mode for unit ID 0
```

## Wrapper Client Configuration

The `ModbusClient` class provides a simplified interface wrapping the port and client port classes. It automatically manages connection lifecycle and is the recommended way to interact with Modbus devices for most use cases.

## Async Client Configuration

### ModbusAsyncClientPort Settings

```python
from libmodbuspy import ModbusAsyncClientPort, ModbusTcpPort

tcp = ModbusTcpPort()
async_client = ModbusAsyncClientPort(tcp)

# Same as ModbusClientPort with async support
# All settings inherited from underlying port
async_client.setTries(3)
async_client.setBroadcastEnabled(True)
```

## Server Configuration

### TCP Server Settings

```python
from libmodbuspy import ModbusTcpServer, ModbusServerResource, 
                     ModbusInterface

class MyDevice(ModbusInterface):
    # ... implementation ...
    pass

device = MyDevice()
server = ModbusTcpServer(device)

# Server Binding
server.setHost("0.0.0.0")   # Listen on all interfaces
server.setPort(502)                  # Modbus TCP port
server.setMaxConnections(10)         # Concurrent connections
server.setTimeout(30000)   # Client inactivity timeout (ms)
```

### Serial Server Settings

```python
from libmodbuspy import (ModbusRtuPort,
                      ModbusServerResource,
                      Parity, StopBits)

rtu = ModbusRtuPort()
device = MyDevice()

# Serial Port
rtu.setPortName("COM1") # Serial port to listen on
rtu.setBaudRate(9600)
rtu.setDataBits(8)
rtu.setParity(Parity.NoParity)
rtu.setStopBits(StopBits.OneStop)

# Timing
rtu.setTimeoutFirstByte(3000)
rtu.setTimeoutInterByte(5)

# Create server port
server = ModbusServerResource(rtu, device)

```

## Global Configuration

`libmodbuspy` provides global configuration through the port classes and 
their settings. Most configuration is done on the port and client 
instances.
