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

## Notes

- Serial protocols (RTU/ASC) are not yet implemented in the current version of ModbusPy
- The client includes timing control to space requests 1 second apart
- Error handling displays detailed error messages for debugging
- Test data patterns are used for write operations to demonstrate functionality