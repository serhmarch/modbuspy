# Serial Protocols {#serial}

@tableofcontents

## Overview

ModbusPy supports both RTU and ASCII versions of Modbus serial communication protocols. These protocols are designed for communication over serial interfaces such as RS-232, RS-485, and RS-422.

## RTU Protocol {#rtu}

Modbus RTU (Remote Terminal Unit) is a binary representation of Modbus protocol data.

### Features

- **Binary Encoding**: All data is transmitted in binary format
- **CRC16 Checksum**: Uses CRC16 for error detection
- **Timing-based Frame Detection**: Uses silence periods to detect frame boundaries
- **Compact Format**: More efficient than ASCII protocol

### Frame Format

```
| Device Address | Function Code | Data    | CRC16 Low | CRC16 High |
|     1 byte     |    1 byte     | N bytes |  1 byte   |   1 byte   |
```

### Configuration Example

```python
from modbuspy import ModbusConfig, Parity, StopBits, FlowControl

settings = ModbusConfig.SerialSettings(
    portName="/dev/ttyUSB0",  # or "COM1" on Windows
    baudRate=9600,
    dataBits=8,
    parity=Parity.NoParity,
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=1000,
    timeoutInterByte=100
)

# Create RTU client port
from modbuspy import ModbusRtuPort
port = ModbusRtuPort.ModbusRtuClientPort(settings, blocking=True)
```

### Timing Requirements

RTU protocol relies on timing to detect frame boundaries:
- **Inter-frame delay**: Minimum 3.5 character times of silence
- **Inter-character timeout**: Maximum 1.5 character times between characters
- Character time = (1 start bit + 8 data bits + 1 parity bit + 1 stop bit) / baud rate

## ASCII Protocol {#ascii}

Modbus ASCII (American Standard Code for Information Interchange) uses hexadecimal ASCII characters to represent data.

### Features

- **ASCII Encoding**: All data transmitted as hexadecimal ASCII characters  
- **LRC Checksum**: Uses Longitudinal Redundancy Check for error detection
- **Character-based Frame Detection**: Uses colon (:) start and CRLF end delimiters
- **Human Readable**: Easier to debug and monitor

### Frame Format

```
| : | Device Address | Function Code | Data | LRC | CR | LF |
|1B |     2 bytes    |   2 bytes     |2N B  | 2B  |1B  |1B  |
```

Where:
- `:` - Colon character (0x3A) marks start of frame
- All data fields are represented as 2 ASCII hex characters
- `LRC` - Longitudinal Redundancy Check (2 ASCII hex characters)
- `CR LF` - Carriage Return (0x0D) + Line Feed (0x0A) marks end of frame

### Configuration Example

```python
from modbuspy import ModbusConfig, Parity, StopBits, FlowControl

settings = ModbusConfig.SerialSettings(
    portName="/dev/ttyUSB0",  # or "COM1" on Windows
    baudRate=9600,
    dataBits=7,  # Usually 7 bits for ASCII
    parity=Parity.EvenParity,  # Even parity is common for ASCII
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=1000,
    timeoutInterByte=100
)

# Create ASCII client port
from modbuspy import ModbusAscPort
port = ModbusAscPort.ModbusAscClientPort(settings, blocking=True)
```

## Serial Port Configuration {#serial_config}

### Common Serial Settings

Both RTU and ASCII protocols share the same serial port configuration structure:

| Parameter | Description | Common Values |
|-----------|-------------|---------------|
| **portName** | Serial port device name | Linux: `/dev/ttyUSB0`, `/dev/ttyS0`<br>Windows: `COM1`, `COM2`, etc. |
| **baudRate** | Communication speed | 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200 |
| **dataBits** | Number of data bits | 7 (ASCII), 8 (RTU) |
| **parity** | Parity checking | `NoParity`, `EvenParity`, `OddParity` |
| **stopBits** | Number of stop bits | `OneStop`, `TwoStop` |
| **flowControl** | Flow control method | `NoFlowControl`, `HardwareControl`, `SoftwareControl` |
| **timeoutFirstByte** | Timeout for first byte (ms) | 1000-5000 |
| **timeoutInterByte** | Inter-character timeout (ms) | 50-500 |

### Recommended Settings

#### RTU Protocol
```python
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

#### ASCII Protocol
```python
settings = ModbusConfig.SerialSettings(
    portName="COM1", 
    baudRate=9600,
    dataBits=7,
    parity=Parity.EvenParity,
    stopBits=StopBits.OneStop,
    flowControl=FlowControl.NoFlowControl,
    timeoutFirstByte=1000,
    timeoutInterByte=100
)
```

## Error Detection {#error_detection}

### CRC16 (RTU)

The CRC16 checksum used in RTU protocol:
- Polynomial: 0xA001 (reverse of 0x8005)
- Initial value: 0xFFFF
- Calculated over device address, function code, and data fields
- Transmitted as low byte first, then high byte

```python
from modbuspy.ModbusGlobal import crc16

data = b'\x01\x03\x00\x00\x00\x02'  # Example RTU frame without CRC
checksum = crc16(data)
print(f"CRC16: 0x{checksum:04X}")
```

### LRC (ASCII)

The LRC checksum used in ASCII protocol:
- Simple sum of all bytes (address + function + data)
- Two's complement of the sum
- Only the least significant byte is used

```python
from modbuspy.ModbusGlobal import lrc

data = b'\x01\x03\x00\x00\x00\x02'  # Example data
checksum = lrc(data)
print(f"LRC: 0x{checksum:02X}")
```

## Usage Examples {#serial_examples}

### RTU Client Example

```python
from modbuspy import ModbusRtuPort, ModbusConfig, StatusCode

def rtu_client_example():
    # Configure serial port
    settings = ModbusConfig.SerialSettings(
        portName="COM1",
        baudRate=9600,
        dataBits=8,
        parity=Parity.NoParity,
        stopBits=StopBits.OneStop
    )
    
    # Create RTU client port
    port = ModbusRtuPort.ModbusRtuClientPort(settings, blocking=True)
    
    try:
        # Read holding registers
        unit = 1
        offset = 0
        count = 10
        
        status, values = port.read_holding_registers(unit, offset, count)
        if StatusCode.is_good(status):
            print(f"Read values: {values}")
        else:
            print(f"Error: {port.last_error_text()}")
            
    finally:
        port.close()
```

### ASCII Client Example

```python
from modbuspy import ModbusAscPort, ModbusConfig, StatusCode

def ascii_client_example():
    # Configure serial port
    settings = ModbusConfig.SerialSettings(
        portName="COM1",
        baudRate=9600,
        dataBits=7,
        parity=Parity.EvenParity,
        stopBits=StopBits.OneStop
    )
    
    # Create ASCII client port
    port = ModbusAscPort.ModbusAscClientPort(settings, blocking=True)
    
    try:
        # Write single coil
        unit = 1
        offset = 0
        value = True
        
        status = port.write_single_coil(unit, offset, value)
        if StatusCode.is_good(status):
            print("Coil written successfully")
        else:
            print(f"Error: {port.last_error_text()}")
            
    finally:
        port.close()
```

## Protocol Comparison {#protocol_comparison}

| Aspect | RTU | ASCII |
|--------|-----|-------|
| **Encoding** | Binary | Hexadecimal ASCII |
| **Frame Detection** | Timing-based | Character delimiters (: and CRLF) |
| **Error Detection** | CRC16 | LRC |
| **Efficiency** | Higher (binary) | Lower (ASCII overhead) |
| **Readability** | Difficult to debug | Human readable |
| **Typical Data Bits** | 8 | 7 |
| **Typical Parity** | None/Even/Odd | Even |
| **Frame Overhead** | 4 bytes (addr+func+crc16) | 7 bytes (:+addr+func+lrc+crlf) |

## Troubleshooting {#serial_troubleshooting}

### Common Issues

1. **No Response from Device**
   - Check serial port name and availability
   - Verify baud rate, data bits, parity, and stop bits match device
   - Ensure proper RS-485 wiring and termination
   - Check device address and unit ID

2. **CRC/LRC Errors**
   - Verify data integrity on serial line
   - Check for electromagnetic interference
   - Ensure proper grounding
   - Consider lower baud rates for long cables

3. **Timeout Errors**
   - Increase timeout values for slower devices
   - Check inter-character timing for RTU
   - Verify device response time specifications

4. **Frame Errors**
   - For RTU: Check timing requirements and inter-frame delays
   - For ASCII: Verify start/end delimiters and character encoding
   - Check serial port buffer sizes

### Debugging Tips

1. **Enable Logging**: Use signal/slot mechanism to monitor transmitted and received data
2. **Protocol Analyzer**: Use serial port monitors to capture raw data
3. **Loopback Testing**: Test serial port configuration with loopback connector
4. **Step-by-step**: Start with simple functions (read single register) before complex operations