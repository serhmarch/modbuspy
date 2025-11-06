# Configuration Guide {#configuration}

@tableofcontents

## Overview

ModbusPy provides comprehensive configuration options for different communication protocols. This guide covers all available settings for TCP, RTU, and ASCII protocols.

## TCP Configuration {#tcp_config}

### TcpSettings Class

The `TcpSettings` class is used to configure TCP/IP connections:

```python
from modbuspy import ModbusConfig

settings = ModbusConfig.TcpSettings(
    host="192.168.1.100",
    port=502,
    timeout=3000,
    maxconn=10
)
```

### TCP Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **host** | str | "localhost" | IP address or DNS name of remote device |
| **port** | int | 502 | TCP port number (standard Modbus port is 502) |
| **timeout** | int | 1000 | Connection timeout in milliseconds |
| **maxconn** | int | 10 | Maximum simultaneous connections (server only) |

### TCP Client Example

```python
from modbuspy import ModbusTcpPort, ModbusConfig

# Configure TCP connection
settings = ModbusConfig.TcpSettings(
    host="plc.example.com",
    port=502,
    timeout=5000
)

# Create TCP client port
port = ModbusTcpPort.ModbusTcpClientPort(settings, blocking=True)

# Use the port for Modbus communication
status, values = port.read_holding_registers(1, 0, 10)
```

### TCP Server Example

```python
from modbuspy import ModbusTcpServer, ModbusConfig

# Configure TCP server
settings = ModbusConfig.TcpSettings(
    port=502,
    timeout=3000,
    maxconn=5  # Allow up to 5 simultaneous connections
)

# Create TCP server with device interface
server = ModbusTcpServer.ModbusTcpServer(device_interface, settings, blocking=False)
```

## Serial Configuration {#serial_config}

### SerialSettings Class

The `SerialSettings` class is used to configure serial port communication for both RTU and ASCII protocols:

```python
from modbuspy import ModbusConfig, Parity, StopBits, FlowControl

settings = ModbusConfig.SerialSettings(
    portName="COM1",
    baudRate=9600,
    dataBits=8,
    parity=Parity.NoParity,
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=1000,
    timeoutInterByte=100
)
```

### Serial Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **portName** | str | "" | Serial port name (e.g., "COM1", "/dev/ttyUSB0") |
| **baudRate** | int | 9600 | Communication speed in bits per second |
| **dataBits** | int | 8 | Number of data bits (7 or 8) |
| **parity** | Parity | NoParity | Parity checking method |
| **stopBits** | StopBits | OneStop | Number of stop bits |
| **flowControl** | FlowControl | NoFlowControl | Flow control method |
| **timeoutFirstByte** | int | 1000 | Timeout waiting for first byte (ms) |
| **timeoutInterByte** | int | 100 | Timeout between characters (ms) |

## Enumeration Values {#enums}

### Parity Options

```python
from modbuspy import Parity

# Available parity options
Parity.NoParity      # No parity bit (most common)
Parity.EvenParity    # Even parity
Parity.OddParity     # Odd parity  
Parity.SpaceParity   # Space parity (always 0)
Parity.MarkParity    # Mark parity (always 1)
```

### Stop Bits Options

```python
from modbuspy import StopBits

# Available stop bit options
StopBits.OneStop         # 1 stop bit (most common)
StopBits.OneAndHalfStop  # 1.5 stop bits
StopBits.TwoStop         # 2 stop bits
```

### Flow Control Options

```python
from modbuspy import FlowControl

# Available flow control options
FlowControl.NoFlowControl    # No flow control (most common)
FlowControl.HardwareControl  # RTS/CTS hardware flow control
FlowControl.SoftwareControl  # XON/XOFF software flow control
```

## Protocol-Specific Settings {#protocol_settings}

### RTU Configuration

RTU protocol typically uses these settings:

```python
# Standard RTU configuration
rtu_settings = ModbusConfig.SerialSettings(
    portName="COM1",
    baudRate=9600,
    dataBits=8,              # Always 8 for RTU
    parity=Parity.NoParity,  # Or EvenParity/OddParity
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=1000,
    timeoutInterByte=100     # Critical for RTU timing
)
```

### ASCII Configuration

ASCII protocol typically uses these settings:

```python
# Standard ASCII configuration  
ascii_settings = ModbusConfig.SerialSettings(
    portName="COM1",
    baudRate=9600,
    dataBits=7,                    # Usually 7 for ASCII
    parity=Parity.EvenParity,      # Even parity common for ASCII
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=1000,
    timeoutInterByte=500           # Less critical for ASCII
)
```

## Timeout Configuration {#timeouts}

### Understanding Timeouts

Proper timeout configuration is crucial for reliable communication:

#### TCP Timeouts

- **Connection Timeout**: Time to wait for TCP connection establishment
- **Response Timeout**: Time to wait for Modbus response after sending request

```python
# Conservative settings for slow networks
tcp_settings = ModbusConfig.TcpSettings(
    host="remote.plc.com",
    timeout=10000  # 10 seconds for slow/unstable connections
)

# Fast settings for local networks
tcp_settings = ModbusConfig.TcpSettings(
    host="192.168.1.10", 
    timeout=1000   # 1 second for fast local networks
)
```

#### Serial Timeouts

- **First Byte Timeout**: Maximum time to wait for the first byte of response
- **Inter-Byte Timeout**: Maximum time between consecutive bytes

```python
# Calculate timeouts based on baud rate
baud_rate = 9600
char_time_ms = (1000 * 11) / baud_rate  # 11 bits per character (start+8data+parity+stop)

serial_settings = ModbusConfig.SerialSettings(
    baudRate=baud_rate,
    timeoutFirstByte=int(20 * char_time_ms),  # 20 character times
    timeoutInterByte=int(1.5 * char_time_ms)  # 1.5 character times for RTU
)
```

## Baud Rate Selection {#baud_rates}

### Common Baud Rates

| Baud Rate | Character Time (11 bits) | Applications |
|-----------|-------------------------|--------------|
| 1200 | 9.17 ms | Very long cables, noisy environments |
| 2400 | 4.58 ms | Long cables, legacy systems |
| 4800 | 2.29 ms | Medium distance, moderate speed |
| 9600 | 1.15 ms | Standard setting, good balance |
| 19200 | 0.57 ms | Higher speed, shorter cables |
| 38400 | 0.29 ms | High speed, short cables |
| 57600 | 0.19 ms | Very high speed, very short cables |
| 115200 | 0.095 ms | Maximum speed, minimal cable length |

### Baud Rate Guidelines

1. **Start with 9600**: Good default for most applications
2. **Lower for long cables**: Use 1200-4800 for cables > 100m
3. **Higher for short cables**: Use 19200+ for cables < 10m
4. **Match device settings**: Always match the slave device configuration

## Port Configuration {#port_config}

### Windows Port Names

```python
# Windows COM ports
settings.portName = "COM1"    # Physical COM port
settings.portName = "COM10"   # USB-to-serial adapter
settings.portName = "COM256"  # High-numbered virtual ports
```

### Linux Port Names

```python
# Linux serial ports
settings.portName = "/dev/ttyS0"    # Physical serial port
settings.portName = "/dev/ttyUSB0"  # USB-to-serial adapter
settings.portName = "/dev/ttyACM0"  # Arduino/CDC devices
```

### Port Discovery

```python
import serial.tools.list_ports

def list_serial_ports():
    """List available serial ports"""
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print(f"Port: {port.device}")
        print(f"Description: {port.description}")
        print(f"Hardware ID: {port.hwid}")
        print("---")

# Find available ports before configuring
list_serial_ports()
```

## Advanced Configuration {#advanced_config}

### RS-485 Configuration

For RS-485 networks, additional considerations:

```python
# RS-485 specific settings
rs485_settings = ModbusConfig.SerialSettings(
    portName="/dev/ttyUSB0",
    baudRate=9600,
    dataBits=8,
    parity=Parity.NoParity,
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=2000,     # Longer timeout for multi-drop
    timeoutInterByte=200       # Account for converter delays
)
```

### High-Speed Configuration

For high-speed applications:

```python
# High-speed RTU configuration
high_speed_settings = ModbusConfig.SerialSettings(
    portName="COM1",
    baudRate=115200,           # Maximum speed
    dataBits=8,
    parity=Parity.NoParity,
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=100,      # Faster timeouts
    timeoutInterByte=10        # Very tight timing
)
```

### Redundant Connection Configuration

```python
# Primary connection
primary_settings = ModbusConfig.TcpSettings(
    host="192.168.1.10",
    port=502,
    timeout=2000
)

# Backup connection  
backup_settings = ModbusConfig.TcpSettings(
    host="192.168.1.11",
    port=502,
    timeout=2000
)

# Implement connection switching logic in your application
```

## Validation and Testing {#validation}

### Configuration Validation

```python
def validate_tcp_config(settings):
    """Validate TCP configuration"""
    if not settings.host:
        raise ValueError("Host cannot be empty")
    if not (1 <= settings.port <= 65535):
        raise ValueError("Port must be between 1 and 65535")
    if settings.timeout <= 0:
        raise ValueError("Timeout must be positive")

def validate_serial_config(settings):
    """Validate serial configuration"""
    if not settings.portName:
        raise ValueError("Port name cannot be empty")
    if settings.baudRate not in [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]:
        print(f"Warning: Unusual baud rate {settings.baudRate}")
    if settings.dataBits not in [7, 8]:
        raise ValueError("Data bits must be 7 or 8")
```

### Connection Testing

```python
def test_connection(port):
    """Test Modbus connection with simple read"""
    try:
        # Try to read a single holding register
        status, values = port.read_holding_registers(1, 0, 1)
        if StatusCode.is_good(status):
            print("Connection test successful")
            return True
        else:
            print(f"Connection test failed: {port.last_error_text()}")
            return False
    except Exception as e:
        print(f"Connection test error: {e}")
        return False
```

## Troubleshooting Configuration {#config_troubleshooting}

### Common Configuration Issues

1. **Wrong Serial Port Name**
   - List available ports before configuration
   - Check device manager (Windows) or dmesg (Linux)

2. **Mismatched Serial Settings**
   - Verify baud rate, parity, stop bits match device
   - Use device documentation or configuration software

3. **TCP Connection Issues**
   - Check IP address and port accessibility
   - Verify firewall settings
   - Test with telnet or ping

4. **Timeout Too Short**
   - Increase timeouts for slow devices
   - Account for network latency and processing time

5. **RS-485 Issues**
   - Check converter configuration (auto or manual direction control)
   - Verify termination resistors
   - Ensure proper grounding

### Debug Configuration

```python
def debug_config(settings):
    """Print configuration for debugging"""
    if isinstance(settings, ModbusConfig.TcpSettings):
        print(f"TCP Config:")
        print(f"  Host: {settings.host}")
        print(f"  Port: {settings.port}")
        print(f"  Timeout: {settings.timeout} ms")
        print(f"  Max Connections: {settings.maxconn}")
    elif isinstance(settings, ModbusConfig.SerialSettings):
        print(f"Serial Config:")
        print(f"  Port: {settings.portName}")
        print(f"  Baud Rate: {settings.baudRate}")
        print(f"  Data Bits: {settings.dataBits}")
        print(f"  Parity: {settings.parity.name}")
        print(f"  Stop Bits: {settings.stopBits.name}")
        print(f"  Flow Control: {settings.flowControl.name}")
        print(f"  First Byte Timeout: {settings.timeoutFirstByte} ms")
        print(f"  Inter Byte Timeout: {settings.timeoutInterByte} ms")
```