# ModbusPy Examples

This directory contains example applications for the ModbusPy library.

## Client Examples

### democlient.py

A working simple demo client that demonstrates basic Modbus TCP functionality. This version uses a standalone implementation without complex module dependencies.

**Usage:**
```bash
cd examples/client
python democlient.py [options]
```

**Options:**
- `-u, --unit <unit>` - Modbus device remote address/unit (default: 1)
- `--host <host>` - DNS name or IP address for TCP (default: localhost)  
- `-p, --port <port>` - Remote TCP port (default: 502)
- `--timeout <timeout>` - Timeout for TCP in seconds (default: 3.0)
- `-o, --offset <offset>` - Modbus function data start offset (default: 0)
- `-c, --count <count>` - Modbus function data count (default: 16)

**Examples:**
```bash
# Connect to TCP server on localhost:502
python democlient.py

# Connect to specific host and port
python democlient.py --host 192.168.1.100 -p 502

# Use different unit ID and data range
python democlient.py -u 2 -o 100 -c 10

# Set custom timeout
python democlient.py --timeout 5.0
```

**Functions Tested:**
- Read Holding Registers (FC 03)
- Read Coils (FC 01)

### democlient.py

A comprehensive demo client that showcases all major Modbus functions. This is a Python translation of the original C++ `democlient.cpp` from ModbusLib. 

**Note:** This version is currently under development and requires fixing import dependencies in the modbuspy library.

**Functions Planned:**
- Read Coils (FC 01)
- Read Discrete Inputs (FC 02)
- Read Holding Registers (FC 03)
- Read Input Registers (FC 04)
- Write Single Coil (FC 05)
- Write Single Register (FC 06)
- Read Exception Status (FC 07)
- Write Multiple Coils (FC 15)
- Write Multiple Registers (FC 16)
- Mask Write Register (FC 22)
- Read/Write Multiple Registers (FC 23)

## Server Examples

### demoserver.py

A comprehensive demo server that implements a complete Modbus TCP server with simulated device memory. This is a Python translation of the original C++ `demoserver.cpp` from ModbusLib.

**Usage:**
```bash
cd examples/server
python demoserver.py [options]
```

**Options:**
- `-u, --unit <unit>` - Modbus device unit address (default: 1)
- `-t, --type <type>` - Protocol type: TCP, RTU, ASC (default: TCP)
- `-p, --port <port>` - TCP port to listen on (default: 502)
- `--tm <timeout>` - Timeout for TCP in milliseconds (default: 3000)
- `--maxconn <count>` - Maximum active TCP connections (default: 10)
- `-c, --count <count>` - Memory size (count of 16-bit registers, default: 16)

**Examples:**
```bash
# Start server on default port 502
python demoserver.py

# Start server on custom port with more memory
python demoserver.py -p 5020 -c 100

# Use different unit ID
python demoserver.py -u 2
```

**Features:**
- Complete ModbusInterface implementation with simulated memory
- All standard Modbus functions (FC 01-23)
- Real-time connection monitoring and logging
- Automatic register increment demonstration (first register increments every second)
- Multi-client connection support
- Comprehensive error handling and protocol validation

**Memory Model:**
- Registers and coils share the same memory space
- Each register is 16-bit (2 bytes)
- Coils use individual bits from the register memory
- Memory is initialized with test patterns for demonstration

## Testing Client and Server Together

You can test the client and server together:

**Terminal 1 - Start Server:**
```bash
cd examples/server
python demoserver.py -p 5020 -c 50
```

**Terminal 2 - Run Client:**
```bash
cd examples/client
python simple_democlient.py --host localhost -p 5020 -c 10
```

## Notes

- Serial protocols (RTU/ASC) are not yet implemented in the current version
- The client includes timing control to space requests 1 second apart
- The server automatically increments the first register every second for demonstration
- Error handling displays detailed error messages for debugging
- Test data patterns are used for write operations to demonstrate functionality
- Both client and server support comprehensive logging of all Modbus traffic