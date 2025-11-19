# libmodbuspy Examples

This directory contains comprehensive example applications demonstrating the libmodbuspy Modbus library in both synchronous and asynchronous modes.

## Structure

```
examples/
├── client/
│   ├── democlient.py           # Synchronous client with all Modbus functions
│   ├── ademoclient.py          # Asynchronous single-unit client
│   └── ademomulticlient.py     # Asynchronous multi-unit client with concurrent operations
└── server/
    ├── demoserver.py           # Synchronous server with simulated device memory
    └── ademoserver.py          # Asynchronous server with simulated device memory
```

## Client Examples

### democlient.py - Synchronous Client (Blocking Mode)

A comprehensive Modbus client demonstrating synchronous, blocking-mode operations.
This is a Python translation of the original C++ `democlient.cpp` from ModbusLib.

**Features:**
- Supports TCP, RTU, and ASCII protocols
- Implements all standard Modbus functions (FC 01-23)
- Blocking mode with polling for non-blocking operations
- Full error handling and status reporting
- Signal callbacks for Tx/Rx monitoring and diagnostics
- Comprehensive command-line argument support

**Usage:**
```bash
cd examples/client
python democlient.py [options]
```

**Command-Line Options:**
- `--block <0|1>` - Use blocking mode 1 (default) or non-blocking 0
- `-u, --unit <unit>` - Modbus device remote address/unit ID (default: 1)
- `-t, --type <TCP|RTU|ASC>` - Protocol type (default: TCP)
- `-r, --host <host>` - DNS name or IP address for TCP (default: localhost)
- `-p, --port <port>` - Remote TCP port (default: 502)
- `--tm <timeout>` - Timeout for TCP in milliseconds (default: 3000)
- `--serial, -sl <port>` - Serial port name for RTU and ASCII
- `-b, --baud <rate>` - Baud rate for serial (default: 9600)
- `-d, --data <bits>` - Data bits for serial [5-8] (default: 8)
- `--parity <N|E|O>` - Parity: None, Even, Odd (default: N)
- `-s, --stop <1|1.5|2>` - Stop bits (default: 1)
- `--tfb <ms>` - Timeout first byte for serial in ms (default: 3000)
- `--tib <ms>` - Timeout inter-byte for serial in ms (default: 5)
- `-o, --offset <offset>` - Modbus data start offset (default: 0)
- `-c, --count <count>` - Modbus data count/quantity (default: 16)

**Modbus Functions Demonstrated:**
- FC 01: Read Coils
- FC 02: Read Discrete Inputs
- FC 03: Read Holding Registers
- FC 04: Read Input Registers
- FC 05: Write Single Coil
- FC 06: Write Single Register
- FC 07: Read Exception Status
- FC 15: Write Multiple Coils
- FC 16: Write Multiple Registers
- FC 22: Mask Write Register
- FC 23: Read/Write Multiple Registers
- FC 24: Read FIFO Queue

**Example Commands:**
```bash
# Connect to TCP server on localhost:502, read 10 registers from offset 0
python democlient.py -t TCP -r localhost -p 502 -u 1 -o 0 -c 10

# Non-blocking mode with RTU serial
python democlient.py --block 0 -t RTU --serial COM3 -b 9600

# Custom timeout and ASCII protocol
python democlient.py -t ASC --serial /dev/ttyUSB0 --tm 5000
```

### ademoclient.py - Asynchronous Single-Unit Client

An asynchronous client demonstrating non-blocking async/await patterns for
single Modbus device communication. Uses `asyncio` for concurrent operations.

**Features:**
- Fully asynchronous implementation with async/await
- Non-blocking operations using `ModbusAsyncClientPort`
- Supports TCP, RTU, and ASCII protocols
- All standard Modbus functions in async variants
- Automatic task switching with `asyncio.sleep()`
- Clean sequential request handling

**Usage:**
```bash
cd examples/client
python ademoclient.py [options]
```

**Command-Line Options:**
Same as `democlient.py` (except `--block` parameter is always non-blocking)

**Key Differences from Synchronous Client:**
- Uses `await` for all Modbus operations
- No polling loops needed - cleaner, more readable code
- `asyncio.sleep()` instead of `time.sleep()` for delays
- Function calls return `AwaitableMethod` objects that can be awaited

**Example Commands:**
```bash
# Async client connecting to localhost:502
python ademoclient.py -t TCP -r localhost -p 502

# With RTU protocol and custom timeout
python ademoclient.py -t RTU --serial COM1 -b 19200 --tm 5000
```

### ademomulticlient.py - Asynchronous Multi-Unit Client

An advanced asynchronous client demonstrating concurrent operations across
multiple Modbus devices simultaneously using `asyncio.gather()`.

**Features:**
- Concurrent async operations on multiple unit IDs
- Runs 3 parallel client tasks with `asyncio.gather()`
- Each task independently communicates with its own device unit
- Each task uses a single TCP connection/serial port
- Demonstrates handling of multiple devices on same network
- Per-unit status tracking and error reporting
- All standard Modbus functions in async variants

**Usage:**
```bash
cd examples/client
python ademomulticlient.py [options]
```

**Command-Line Options:**
Same as `ademoclient.py`

**Concurrency Model:**
- Runs parallel requests across units N, N+1, and N+2 (where N is specified unit)
- Each unit's requests are sequential internally, but all three units operate concurrently
- Demonstrates utilization of async I/O for network operations
- Each client task includes full error handling and logging

**Example Commands:**
```bash
# Three concurrent clients on units 1, 2, 3
python ademomulticlient.py -t TCP -r localhost -p 502 -u 1

# Multiple units on RTU serial
python ademomulticlient.py -t RTU --serial COM1 -u 10
```

## Server Examples

### demoserver.py - Synchronous Server (Blocking Mode)

A comprehensive Modbus server implementing a complete device simulation with memory storage.
Python translation of the original C++ `demoserver.cpp` from ModbusLib.

**Features:**
- Supports TCP, RTU, and ASCII protocols
- Complete `ModbusInterface` implementation with simulated device memory
- Implements all standard Modbus functions (FC 01-23)
- Real-time connection monitoring and multi-client support
- Automatic memory updates for demonstration (register increment every cycle)
- Blocking mode operation with configurable polling intervals
- Signal callbacks for connection, transmission, and error events
- Comprehensive error handling and protocol validation

**Usage:**
```bash
cd examples/server
python demoserver.py [options]
```

**Command-Line Options:**
- `-u, --unit <unit>` - Modbus device unit address (default: 1)
- `-t, --type <TCP|RTU|ASC>` - Protocol type (default: TCP)
- `-p, --port <port>` - TCP port to listen on (default: 502)
- `--tm <timeout>` - Timeout for TCP in milliseconds (default: 3000)
- `--maxconn <count>` - Maximum active TCP connections (default: 10)
- `--serial, -sl <port>` - Serial port name for RTU and ASCII
- `-b, --baud <rate>` - Baud rate for serial (default: 9600)
- `-d, --data <bits>` - Data bits for serial [5-8] (default: 8)
- `--parity <N|E|O>` - Parity: None, Even, Odd (default: N)
- `-s, --stop <1|1.5|2>` - Stop bits (default: 1)
- `--tfb <ms>` - Timeout first byte for serial in ms (default: 3000)
- `--tib <ms>` - Timeout inter-byte for serial in ms (default: 5)
- `-c, --count <count>` - Memory size in 16-bit registers (default: 16)

**Device Memory Model:**
- Each register is 16-bit (2 bytes)
- Coils and discrete inputs share register memory as bit arrays
- Maximum address: `count * 16` bits (for coil/input operations)
- Memory initialized with test patterns
- First register automatically increments each cycle

**Example Commands:**
```bash
# Start TCP server on default port 502 with 16 registers
python demoserver.py

# Server on custom port with more memory
python demoserver.py -p 5020 -c 100

# RTU server on serial port
python demoserver.py -t RTU --serial COM1 -u 1

# ASCII server with high baud rate
python demoserver.py -t ASC --serial /dev/ttyUSB0 -b 115200
```

**Modbus Functions Supported:**
- FC 01: Read Coils
- FC 02: Read Discrete Inputs
- FC 03: Read Holding Registers
- FC 04: Read Input Registers
- FC 05: Write Single Coil
- FC 06: Write Single Register
- FC 07: Read Exception Status
- FC 15: Write Multiple Coils
- FC 16: Write Multiple Registers
- FC 22: Mask Write Register
- FC 23: Read/Write Multiple Registers

### ademoserver.py - Asynchronous Server

An asynchronous server implementing the same device simulation as `demoserver.py` but using async/await patterns with `asyncio` for non-blocking operations.

**Features:**
- Fully asynchronous implementation with async/await
- Non-blocking server operations using `ModbusAsyncTcpServer` and `ModbusAsyncServerResource`
- Supports TCP, RTU, and ASCII protocols
- Parallel task execution: server processing and device monitoring
- Uses `asyncio.gather()` for concurrent operations
- Identical device memory model and functionality as synchronous version
- All standard Modbus functions (FC 01-23)
- Handling of multiple concurrent connections

**Usage:**
```bash
cd examples/server
python ademoserver.py [options]
```

**Command-Line Options:**
Same as `demoserver.py`

**Async Architecture:**
- Two concurrent tasks: `server_process()` and `device_process()`
- `server_process()`: Continuously handles incoming client requests
- `device_process()`: Manages device state and periodic monitoring
- Tasks run concurrently using `asyncio.gather()`
- Automatic task switching via `await asyncio.sleep()`

**Example Commands:**
```bash
# Start async TCP server on port 5020
python ademoserver.py -p 5020 -c 50

# Async RTU server with large memory
python ademoserver.py -t RTU --serial COM1 -c 200

# Async ASCII server
python ademoserver.py -t ASC --serial /dev/ttyUSB0 -p 2000
```

## Testing Examples Together

You can easily test multiple examples in combination:

### Scenario 1: Single Synchronous Client with Synchronous Server

**Terminal 1 - Start Server:**
```bash
cd examples/server
python demoserver.py -p 5020 -c 50
```

**Terminal 2 - Run Client:**
```bash
cd examples/client
python democlient.py -t TCP -r localhost -p 5020 -u 1 -c 10
```

### Scenario 2: Asynchronous Client with Synchronous Server

**Terminal 1 - Start Server:**
```bash
cd examples/server
python demoserver.py -p 5020 -c 50
```

**Terminal 2 - Run Async Client:**
```bash
cd examples/client
python ademoclient.py -t TCP -r localhost -p 5020 -u 1 -c 10
```

### Scenario 3: Multiple Async Clients with Async Server

**Terminal 1 - Start Async Server:**
```bash
cd examples/server
python ademoserver.py -p 5020 -c 100
```

**Terminal 2 - Single async client:**
```bash
cd examples/client
python ademoclient.py -t TCP -r localhost -p 5020 -u 1 -c 10
```

**Terminal 3 - Multi-unit async client (runs 3 concurrent units):**
```bash
cd examples/client
python ademomulticlient.py -t TCP -r localhost -p 5020 -u 1 -c 10
```

### Scenario 4: Mixing Sync and Async Clients

**Terminal 1 - Start Server:**
```bash
cd examples/server
python demoserver.py -p 5020 -c 100
```

**Terminal 2 - Async multi-client:**
```bash
cd examples/client
python ademomulticlient.py -t TCP -r localhost -p 5020 -u 1
```

**Terminal 3 - Synchronous client:**
```bash
cd examples/client
python democlient.py -t TCP -r localhost -p 5020 -u 4
```

## Common Usage Patterns

### Serial Communication (RTU/ASCII)

```bash
# RTU server on COM1
python demoserver.py -t RTU --serial COM1 -b 9600

# ASCII client connecting to serial server
python democlient.py -t ASC --serial COM2 -b 9600
```

### Non-Blocking Operations

The synchronous client supports non-blocking mode:

```bash
# Polling loop without blocking
python democlient.py --block 0 -t TCP -r localhost -p 502
```

For truly non-blocking async operations, use the async examples:

```bash
# Async client (always non-blocking)
python ademoclient.py -t TCP -r localhost -p 502
```

### Concurrent Operations

Use the async multi-client for multiple device communication:

```bash
# Three units operating concurrently
python ademomulticlient.py -t TCP -r localhost -p 502 -u 1
```

## Implementation Notes

### Synchronous Client (`democlient.py`)
- Uses `ModbusClientPort` for blocking operations
- Non-blocking mode polls with `time.sleep(0.001)` between attempts
- Request timing: 1 second minimum between operations
- Full error handling with detailed status reporting

### Asynchronous Client (`ademoclient.py`, `ademomulticlient.py`)
- Uses `ModbusAsyncClientPort` wrapping operations in `AwaitableMethod`
- True non-blocking async/await with `asyncio`
- Clean, readable code with `await` instead of polling loops
- Concurrent operations with `asyncio.gather()`

### Synchronous Server (`demoserver.py`)
- Implements `ModbusInterface` with full device simulation
- Memory-backed register and coil storage
- Blocking loop with configurable update intervals
- Connection monitoring via signal callbacks

### Asynchronous Server (`ademoserver.py`)
- Same `ModbusInterface` implementation as sync server
- Uses `ModbusAsyncTcpServer` and `ModbusAsyncServerResource`
- Two parallel async tasks for server and device monitoring
- Automatic task switching via `await asyncio.sleep(0)`

## Requirements

- Python 3.7+ (for async features)
- libmodbuspy library (included in parent directory)
- `pyserial` library for RTU/ASCII serial support: `pip install pyserial`

## Signal and Callbacks

All examples include signal callbacks for diagnostic purposes:

```python
# Transmission callback
def print_tx(source: str, buff: bytes) -> None:
    hex_str = ' '.join(f'{b:02X}' for b in buff)
    print(f"{source} Tx: {hex_str}")

# Reception callback
def print_rx(source: str, buff: bytes) -> None:
    hex_str = ' '.join(f'{b:02X}' for b in buff)
    print(f"{source} Rx: {hex_str}")

# Error callback
def print_error(source: str, code: int, text: str) -> None:
    print(f"{source} Error {code}: {text}")
```

Connect these to the port/server for real-time monitoring of all Modbus traffic.
