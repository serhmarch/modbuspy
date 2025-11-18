# Protocol Details

## Overview

modbuspy implements three Modbus protocol variants: TCP, RTU (Remote Terminal Unit), and ASCII. Each protocol has different framing and communication characteristics while maintaining the same Modbus function codes and data formats.

## TCP Protocol

### Features

- **Transport:** TCP/IP over ethernet networks
- **Addressing:** Hostname and port number
- **Framing:** MBAP (Modbus Application Protocol) header + PDU
- **Performance:** Lowest overhead, best for network communication
- **Reliability:** Built-in TCP reliability (no CRC needed)
- **Connection:** Connection-oriented

### MBAP Header Format

```
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
| T | T | Z | Z | L | L | U | F |           PDU
| r | r | e | e | e | e | n | C | 
| n | n | r | r | n | n | i | o | 
| I | I | o | o | g | g | t | d | 
| D | D | I | I | t | t |   | e | 
|   | + | D | D | h | l |   |   | 
+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
 0   1   2   3   4   5   6   7   8   9  10  11  12  ...
```

**MBAP Fields:**
- `Transaction ID` (Bytes 0-1) - Client-generated transaction identifier
- `Protocol ID` (Bytes 2-3) - Always 0x0000 for standard Modbus
- `Length` (Bytes 4-5) - Length of Unit ID + Function Code + Data
- `Unit ID` (Byte 6) - Remote device identifier
- `Function Code` (Byte 7) - Modbus function (1-24)
- `Data` (Bytes 8+) - Function-specific data

**Example MBAP:**
```
Transaction ID: 0x0001
Protocol ID: 0x0000
Length: 0x0006
Unit ID: 0x01
Function Code: 0x03 (Read Holding Registers)
Data: Starting Address and Quantity
```

### TCP Port Configuration

```python
from modbuspy import ModbusTcpPort, ModbusClientPort

tcp = ModbusTcpPort(blocking=True)
tcp.setHost("192.168.1.100")        # IP or hostname
tcp.setPort(502)                     # Standard Modbus TCP port
tcp.setTimeout(3000)                 # Timeout in milliseconds
tcp.setBlocking(True)                # Blocking mode

port = ModbusClientPort(tcp)
```

### Advantages
- Low overhead (no CRC)
- Fast communication
- Good for local networks
- Built-in TCP error correction
- Multiple simultaneous connections

### Disadvantages
- Requires Ethernet infrastructure
- Less suitable for long distances
- Requires unique IP addresses

## RTU Protocol

### Features

- **Transport:** Serial communication (RS-232, RS-485)
- **Addressing:** Serial port + unit ID
- **Framing:** No header, direct data + CRC16
- **Performance:** Efficient, minimal overhead
- **Reliability:** CRC16 checksum for error detection
- **Connection:** Connectionless (point-to-point or multi-drop)

### RTU Frame Format

```
+-----+-----+-----+-----+     +-----+-----+-----+
| ADD | FCT | DATA    ...    | CRC | CRC |
+-----+-----+-----+-----+     +-----+-----+-----+
  Byte  Byte  Bytes        Bytes Byte  Byte
   0     1    2-251          -2    -1    
```

**Frame Fields:**
- `Address` (1 byte) - Device unit ID (0-247)
- `Function Code` (1 byte) - Modbus function (1-24)
- `Data` (0-250 bytes) - Function-specific data
- `CRC Low` (1 byte) - CRC16 LSB
- `CRC High` (1 byte) - CRC16 MSB

### CRC16 Calculation

CRC16 is calculated using:
- **Polynomial:** x^16 + x^15 + x^2 + 1
- **Initial value:** 0xFFFF
- **Byte order:** LSB first

**Example:**
```
Data: 01 03 00 64 00 02
CRC = calculate_crc16(data)
Result: Frame = 01 03 00 64 00 02 CRC_LOW CRC_HIGH
```

### RTU Port Configuration

```python
from modbuspy import ModbusRtuPort, ModbusClientPort, Parity

rtu = ModbusRtuPort(blocking=True)
rtu.setPortName("COM1")              # Windows: COM1-COM9
                                      # Linux: /dev/ttyUSB0
rtu.setBaudRate(9600)                # Common rates: 9600, 19200, 38400
rtu.setDataBits(8)                   # Typically 8
rtu.setParity(Parity.NoParity)       # 'N'=None, 'E'=Even, 'O'=Odd
rtu.setStopBits(1)                   # Typically 1 or 2
rtu.setTimeoutFirstByte(3000)        # First byte timeout (ms)
rtu.setTimeoutInterByte(5)           # Inter-byte timeout (ms)

port = ModbusClientPort(rtu)
```

### Timing Considerations

**Quiet Time (3.5 character times):**
- Required after each complete frame
- Example at 9600 baud, 11 bits per character:
  - 3.5 × 11 / 9600 ≈ 4 ms

**First Byte Timeout:**
- Waits for first byte after transmission
- Typically 3000 ms

**Inter-byte Timeout:**
- Maximum time between successive bytes
- Typically 5-50 ms

### Advantages
- Low cost (simple serial hardware)
- Long distance capability (RS-485)
- Multi-drop support (multiple devices on one bus)
- Efficient protocol
- Error detection via CRC

### Disadvantages
- Serial port required
- Lower throughput than TCP
- Requires proper termination (RS-485)
- Timing sensitivity

## ASCII Protocol

### Features

- **Transport:** Serial communication with ASCII encoding
- **Addressing:** Serial port + unit ID
- **Framing:** ASCII-encoded data + LRC checksum
- **Performance:** Lower efficiency due to ASCII encoding
- **Reliability:** LRC checksum for error detection
- **Connection:** Connectionless

### ASCII Frame Format

```
+-----+-----+-----+-----+     +-----+-----+-----+-----+-----+
| :   | ADD | FCT | DATA    ...    | LRC | CR | LF |
+-----+-----+-----+-----+     +-----+-----+-----+-----+-----+
  Char  Char  Char  Chars      Chars Char  Char Char
```

**Frame Fields:**
- `:` - Start colon (0x3A)
- `Address` - 2 ASCII hex characters (device unit ID)
- `Function Code` - 2 ASCII hex characters
- `Data` - Even number of ASCII hex characters
- `LRC` - 2 ASCII hex characters (Longitudinal Redundancy Check)
- `CR LF` - Carriage Return + Line Feed (0x0D 0x0A)

**Example:**
```
Raw bytes: 01 03 00 64 00 02
ASCII frame: :010300640002F8<CR><LF>
Breakdown:
  : (start)
  01 (address in ASCII)
  03 (function code in ASCII)
  006400 (data in ASCII)
  F8 (LRC in ASCII)
  <CR><LF> (end markers)
```

### LRC Calculation

LRC (Longitudinal Redundancy Check) is calculated by:
1. Sum all bytes in PDU (excluding LRC field)
2. Two's complement of sum
3. Lower 8 bits only

**Algorithm:**
```python
lrc = 0
for byte in pdu:
    lrc = (lrc + byte) & 0xFF
lrc = ((lrc ^ 0xFF) + 1) & 0xFF
```

### ASCII Port Configuration

```python
from modbuspy import ModbusAscPort, ModbusClientPort, Parity

asc = ModbusAscPort(blocking=True)
asc.setPortName("COM1")              # Serial port
asc.setBaudRate(9600)                # Baud rate
asc.setDataBits(8)                   # Data bits
asc.setParity(Parity.NoParity)       # Parity
asc.setStopBits(1)                   # Stop bits
asc.setTimeoutFirstByte(3000)        # First byte timeout
asc.setTimeoutInterByte(5)           # Inter-byte timeout

port = ModbusClientPort(asc)
```

### Advantages
- Visible/debuggable (ASCII characters)
- Less sensitive to transmission errors
- Good for unreliable connections
- Easy to monitor with terminal tools

### Disadvantages
- Double the frame size (ASCII encoding)
- Lower throughput
- Slower communication
- Higher CPU usage for conversion

## Function Codes

### Read Functions

#### FC 01 - Read Coils (0x01)

Reads discrete outputs (coils).

**Request:**
```
Unit ID | Function | Start Addr | Quantity Requested
  1 B   |    1 B   |    2 B    |        2 B
```

**Response:**
```
Unit ID | Function | Byte Count | Coil Values
  1 B   |    1 B   |    1 B     |  N bytes
```

**Data Format:**
- Each coil is 1 bit
- Packed 8 bits per byte (LSB first)
- Example: 8 coils in 1 byte (0xAA = 10101010 binary)

#### FC 02 - Read Discrete Inputs (0x02)

Same as FC 01 but reads input contacts (read-only).

#### FC 03 - Read Holding Registers (0x03)

Reads holding (output) registers.

**Request:**
```
Unit ID | Function | Start Addr | Quantity Requested
  1 B   |    1 B   |    2 B    |        2 B
```

**Response:**
```
Unit ID | Function | Byte Count | Register Values
  1 B   |    1 B   |    1 B     |  N*2 bytes
```

**Data Format:**
- Each register is 2 bytes (16-bit)
- Little-endian byte order
- Example: Register value 0x1234 sent as 0x34, 0x12

#### FC 04 - Read Input Registers (0x04)

Same as FC 03 but reads input registers (read-only).

### Write Functions

#### FC 05 - Write Single Coil (0x05)

**Request:**
```
Unit ID | Function | Coil Address | Value (0x0000 or 0xFF00)
  1 B   |    1 B   |     2 B      |           2 B
```

**Response:**
- Echo of request (6 bytes)

#### FC 06 - Write Single Register (0x06)

**Request:**
```
Unit ID | Function | Reg Address | Register Value
  1 B   |    1 B   |     2 B     |      2 B
```

**Response:**
- Echo of request (6 bytes)

#### FC 15 (0x0F) - Write Multiple Coils

**Request:**
```
Unit ID | Function | Start Address | Quantity | Byte Count | Coil Values
  1 B   |    1 B   |      2 B      |    2 B   |    1 B     |  N bytes
```

#### FC 16 (0x10) - Write Multiple Registers

**Request:**
```
Unit ID | Function | Start Address | Quantity | Byte Count | Register Values
  1 B   |    1 B   |      2 B      |    2 B   |    1 B     |  N*2 bytes
```

### Advanced Functions

#### FC 22 (0x16) - Mask Write Register

Performs bitwise operation on register without reading current value.

**Request:**
```
Unit ID | Function | Address | AND Mask | OR Mask
  1 B   |    1 B   |   2 B   |   2 B    |   2 B
```

**Logic:** `(CurrentValue & ANDMask) | (ORAMask & ~ANDMask)`

#### FC 23 (0x17) - Read/Write Multiple Registers

Atomically reads and writes registers in single operation.

**Request:**
```
Unit ID | Function | Read Addr | Read Qty | Write Addr | Write Qty | Byte Count | Write Values
  1 B   |    1 B   |    2 B    |    2 B   |     2 B    |    2 B    |     1 B    |  N*2 bytes
```

## Error Handling

### Exception Response

When an error occurs, the server responds with:
```
Unit ID | Function + 0x80 | Exception Code
  1 B   |      1 B        |      1 B
```

**Exception Codes:**
- 0x01 - Illegal function code
- 0x02 - Illegal data address
- 0x03 - Illegal data value
- 0x04 - Device failure
- 0x05 - Acknowledge
- 0x06 - Device busy
- 0x07 - Negative acknowledge
- 0x08 - Memory parity error
- 0x0A - Gateway path unavailable
- 0x0B - Gateway device failed to respond

### Protocol Errors

**TCP:**
- Connection refused
- Connection timeout
- Data transmission error
- Packet loss

**RTU/ASCII:**
- CRC/LRC checksum error
- Frame timeout
- Invalid character (ASCII)
- Buffer overflow

## Communication Examples

### TCP Transaction

```
Client → Server (Request MBAP):
Transaction ID: 0x0001
Protocol ID: 0x0000
Length: 0x0006
Unit ID: 0x01
Function Code: 0x03
Data: 00 64 00 02  (Read 2 registers from address 100)

Server → Client (Response MBAP):
Transaction ID: 0x0001
Protocol ID: 0x0000
Length: 0x0007
Unit ID: 0x01
Function Code: 0x03
Byte Count: 0x04
Data: 12 34 56 78  (Register values)
```

### RTU Transaction

```
Client → Server:
01 03 00 64 00 02 B8 44
├─ 01: Address
├─ 03: Function code (Read Holding Registers)
├─ 00 64: Starting address (100)
├─ 00 02: Quantity (2)
└─ B8 44: CRC16

Server → Client:
01 03 04 12 34 56 78 BD 8C
├─ 01: Address
├─ 03: Function code
├─ 04: Byte count (4 bytes of data)
├─ 12 34 56 78: Register values
└─ BD 8C: CRC16
```

### ASCII Transaction

```
Client → Server:
:010300640002B8<CR><LF>

Server → Client:
:01030412345678BD<CR><LF>
```

## Best Practices

### TCP
1. Use connection pooling for multiple operations
2. Implement proper connection timeout handling
3. Use Nagle's algorithm considerations
4. Handle keep-alive packets

### RTU
1. Respect inter-frame delay (3.5 character times)
2. Use proper RS-485 termination
3. Implement watchdog timeouts
4. Consider baud rate for distance

### ASCII
1. Use for noise-prone environments
2. Monitor with terminal tools for debugging
3. Accept lower performance overhead
4. Easier troubleshooting

### General
1. Validate all input addresses
2. Implement proper error recovery
3. Monitor response times
4. Use appropriate timeouts
5. Log all errors and unusual conditions
