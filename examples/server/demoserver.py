#!/usr/bin/env python3
"""
demoserver.py - Python translation of ModbusLib demoserver.cpp example

This is a complete Modbus server demonstration that implements:
- TCP, RTU, and ASCII protocols
- Full ModbusInterface with simulated memory
- All standard Modbus functions
- Connection monitoring and logging

Author: serhmarch (translated from C++)
Date: November 2025
"""

import sys
import os
import argparse
import time
import struct
from typing import Optional, List

# Add the modbuspy library path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import modbuspy modules
from modbuspy.ModbusStatusCode import StatusCode
from modbuspy.ModbusGlobal import (ProtocolType, timer,
                                   Constants,
                                   MB_REGE_SZ_BITES)

from modbuspy.ModbusTcpServer import ModbusTcpServer
from modbuspy.ModbusServerResource import ModbusServerResource
from modbuspy.ModbusRtuPort import ModbusRtuPort
from modbuspy.ModbusAscPort import ModbusAscPort
from modbuspy.ModbusExceptions import (ModbusException,
                                       IllegalDataAddressError,
                                       GatewayPathUnavailableError)

def print_tx(source: str, buff: bytes, size: int) -> None:
    """Print transmitted data."""
    hex_str = ' '.join(f'{b:02X}' for b in buff[:size])
    print(f"{source} Tx: {hex_str}")

def print_rx(source: str, buff: bytes, size: int) -> None:
    """Print received data."""
    hex_str = ' '.join(f'{b:02X}' for b in buff[:size])
    print(f"{source} Rx: {hex_str}")

def print_tx_asc(source: str, buff: bytes, size: int) -> None:
    """Print transmitted ASCII data."""
    try:
        ascii_str = buff[:size].decode('ascii', errors='replace')
        print(f"{source} Tx: {ascii_str}")
    except:
        print_tx(source, buff, size)

def print_rx_asc(source: str, buff: bytes, size: int) -> None:
    """Print received ASCII data."""
    try:
        ascii_str = buff[:size].decode('ascii', errors='replace')
        print(f"{source} Rx: {ascii_str}")
    except:
        print_rx(source, buff, size)

def print_new_connection(source: str) -> None:
    """Print new connection message."""
    print(f"New connection: {source}")

def print_close_connection(source: str) -> None:
    """Print connection close message."""
    print(f"Close connection: {source}")

class Device:
    """
    Modbus device simulation with memory storage.
    
    This class implements a complete ModbusInterface that simulates
    a Modbus device with register and coil memory.
    """
    
    def __init__(self, unit: int, reg_count: int):
        """
        Initialize the device.
        
        Args:
            unit: Modbus unit/slave address
            reg_count: Number of 16-bit registers to allocate
        """
        self.unit = unit
        self.memory = [0] * reg_count  # 16-bit registers
        self.memory[0] = 1000  # Initialize first register with a value
        
    def reg_count(self) -> int:
        """Return the number of registers."""
        return len(self.memory)
    
    def bit_count(self) -> int:
        """Return the number of bits (registers * 16)."""
        return len(self.memory) * MB_REGE_SZ_BITES
    
    def increment(self):
        """Increment the first register (for demonstration)."""
        self.memory[0] = (self.memory[0] + 1) % 65536
    
    def _read_mem_regs(self, offset: int, count: int) -> bytes:
        """Read registers from memory and return as bytes."""
        if offset + count > len(self.memory):
            return None
        result = bytearray(count * 2)
        for i in range(count):
            val = self.memory[offset + i]
            result[i*2] = val & 0xFF          # Low byte
            result[i*2+1] = (val >> 8) & 0xFF # High byte
        return bytes(result)
    
    def _write_mem_regs(self, offset: int, count: int, values: bytes) -> bool:
        """Write registers to memory from bytes."""
        if offset + count > len(self.memory):
            return False
        if len(values) < count * 2:
            return False
        for i in range(count):
            val = (values[i*2] << 8) | values[i*2+1]
            self.memory[offset + i] = val
        return True
    
    def _read_mem_bits(self, offset: int, count: int) -> bytes:
        """Read bits from memory (treating registers as bit arrays)."""
        if offset + count > self.bit_count():
            return None
        byte_count = (count + 7) // 8
        result = bytearray(byte_count)
        for i in range(count):
            bit_addr = offset + i
            reg_idx = bit_addr // 16
            bit_idx = bit_addr % 16
            if reg_idx < len(self.memory):
                if (self.memory[reg_idx] >> bit_idx) & 1:
                    byte_idx = i // 8
                    bit_pos = i % 8
                    result[byte_idx] |= (1 << bit_pos)
        return bytes(result)
    
    def _write_mem_bits(self, offset: int, count: int, values: bytes) -> bool:
        """Write bits to memory."""
        if offset + count > self.bit_count():
            return False
        for i in range(count):
            bit_addr = offset + i
            reg_idx = bit_addr // 16
            bit_idx = bit_addr % 16
            if reg_idx >= len(self.memory):
                return False
            byte_idx = i // 8
            bit_pos = i % 8
            if byte_idx < len(values):
                bit_val = (values[byte_idx] >> bit_pos) & 1
                if bit_val:
                    self.memory[reg_idx] |= (1 << bit_idx)
                else:
                    self.memory[reg_idx] &= ~(1 << bit_idx)
        return True
    
    # ModbusInterface implementation
    def readCoils(self, unit: int, offset: int, count: int) -> bytes:
        """Read coils (FC 01)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        res = self._read_mem_bits(offset, count)
        if not res:
            raise IllegalDataAddressError("Invalid data address")
        return res
    
    def readDiscreteInputs(self, unit: int, offset: int, count: int) -> bytes:
        """Read discrete inputs (FC 02)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        res = self._read_mem_bits(offset, count)
        if not res:
            raise IllegalDataAddressError("Invalid data address")
        return res
    
    def readHoldingRegisters(self, unit: int, offset: int, count: int) -> bytes:
        """Read holding registers (FC 03)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        res = self._read_mem_regs(offset, count)
        if not res:
            raise IllegalDataAddressError("Invalid data address")
        return res
    
    def readInputRegisters(self, unit: int, offset: int, count: int) -> bytes:
        """Read input registers (FC 04)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        res = self._read_mem_regs(offset, count)
        if not res:
            raise IllegalDataAddressError("Invalid data address")
        return res
    
    def writeSingleCoil(self, unit: int, offset: int, value: bool) -> StatusCode:
        """Write single coil (FC 05)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        bit_data = bytes([0xFF if value else 0x00])
        if not self._write_mem_bits(offset, 1, bit_data):
            raise IllegalDataAddressError("Invalid data address")
        return StatusCode.Status_Good
    
    def writeSingleRegister(self, unit: int, offset: int, value: int) -> StatusCode:
        """Write single register (FC 06)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        reg_data = struct.pack('>H', value)
        if not self._write_mem_regs(offset, 1, reg_data):
            raise IllegalDataAddressError("Invalid data address")
        return StatusCode.Status_Good

    def readExceptionStatus(self, unit: int) -> bytes:
        """Read exception status (FC 07)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")
        
        # Return first register as exception status
        if len(self.memory) > 0:
            return bytes([self.memory[0] & 0xFF])
        return bytes([0])
    
    def writeMultipleCoils(self, unit: int, offset: int, count: int, values: bytes) -> StatusCode:
        """Write multiple coils (FC 15)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")        
        if not self._write_mem_bits(offset, count, values):
            raise IllegalDataAddressError("Invalid data address")
        return StatusCode.Status_Good
    
    def writeMultipleRegisters(self, unit: int, offset: int, count: int, values: bytes) -> StatusCode:
        """Write multiple registers (FC 16)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")        
        if not self._write_mem_regs(offset, count, values):
            raise IllegalDataAddressError("Invalid data address")
        return StatusCode.Status_Good
    
    def maskWriteRegister(self, unit: int, offset: int, and_mask: int, or_mask: int) -> StatusCode:
        """Mask write register (FC 22)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")        
        if offset >= len(self.memory):
            raise IllegalDataAddressError("Invalid data address")        
        current = self.memory[offset]
        result = (current & and_mask) | (or_mask & ~and_mask)
        self.memory[offset] = result        
        return StatusCode.Status_Good
    
    def readWriteMultipleRegisters(self, unit: int, read_offset: int, read_count: int,
                                   write_offset: int, write_count: int, write_values: bytes) -> bytes:
        """Read/Write multiple registers (FC 23)."""
        if unit != self.unit:
            raise GatewayPathUnavailableError("Unit address mismatch")        
        # Perform write first
        if not self._write_mem_regs(write_offset, write_count, write_values):
            raise IllegalDataAddressError("Invalid data address")
        # Then perform read
        res = self._read_mem_regs(read_offset, read_count)
        if not res:
            raise IllegalDataAddressError("Invalid data address")
        return res

class Options:
    """Configuration options for the demo server."""
    
    def __init__(self):
        # Protocol settings
        self.type = ProtocolType.TCP
        self.unit = 1
        
        # TCP settings
        self.host = ""  # Listen on all interfaces
        self.port = Constants.STANDARD_TCP_PORT
        self.timeout = 3000  # milliseconds
        self.max_connections = 10
        
        # Serial settings (for future RTU/ASC support)
        self.serial_port = ""
        self.baud_rate = 9600
        self.data_bits = 8
        self.parity = 'N'
        self.stop_bits = 1
        self.timeout_first_byte = 3000
        self.timeout_inter_byte = 5
        
        # Memory size
        self.count = 16

def parse_arguments() -> Options:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Modbus Demo Server - Python version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  demoserver.py -t TCP -p 502
  demoserver.py -u 2 -c 100
        """
    )
    parser.add_argument('-u', '--unit', type=int, default=1,
                       help='Modbus device unit address (default: 1)')
    parser.add_argument('-t', '--type', choices=['TCP', 'RTU', 'ASC'], default='TCP',
                       help='Protocol type (default: TCP)')
    parser.add_argument('-p', '--port', type=int, default=Constants.STANDARD_TCP_PORT,
                       help=f'TCP port to listen on (default: {Constants.STANDARD_TCP_PORT})')
    parser.add_argument('--tm', type=int, default=3000,
                       help='Timeout for TCP in milliseconds (default: 3000)')
    parser.add_argument('--maxconn', type=int, default=10,
                       help='Maximum active TCP connections (default: 10)')
    parser.add_argument('--serial', '--sl',
                       help='Serial port name for RTU and ASC')
    parser.add_argument('-b', '--baud', type=int, default=9600,
                       help='Baud rate for RTU and ASC (default: 9600)')
    parser.add_argument('-d', '--data', type=int, choices=[5,6,7,8], default=8,
                       help='Data bits for RTU and ASC (default: 8)')
    parser.add_argument('--parity', choices=['N', 'E', 'O'], default='N',
                       help='Parity: N (none), E (even), O (odd) (default: N)')
    parser.add_argument('-s', '--stop', choices=['1', '1.5', '2'], default='1',
                       help='Stop bits (default: 1)')
    parser.add_argument('--tfb', type=int, default=3000,
                       help='Timeout first byte for RTU/ASC in ms (default: 3000)')
    parser.add_argument('--tib', type=int, default=5,
                       help='Timeout inter byte for RTU/ASC in ms (default: 5)')
    parser.add_argument('-c', '--count', type=int, default=16,
                       help='Memory size (count of 16-bit registers, default: 16)')
    args = parser.parse_args()
    options = Options()
    options.unit = args.unit
    # Set protocol type
    if args.type == 'TCP':
        options.type = ProtocolType.TCP
    elif args.type == 'RTU':
        options.type = ProtocolType.RTU
    elif args.type == 'ASC':
        options.type = ProtocolType.ASC
    # Tcp settings
    options.port = args.port
    options.timeout = args.tm
    options.max_connections = args.maxconn    
    # Serial settings
    if args.serial:
        options.serial_port = args.serial
    options.baud_rate = args.baud
    options.data_bits = args.data
    options.parity = args.parity
    options.stop_bits = float(args.stop)
    options.timeout_first_byte = args.tfb
    options.timeout_inter_byte = args.tib    
    options.count = max(1, args.count)  # Ensure at least 1 register    
    return options

def main():
    """Main function."""
    options = parse_arguments()
    
    print("Modbus Demo Server - Python version")
    print(f"Protocol: {['TCP', 'RTU', 'ASC'][options.type]}")
    print(f"Unit: {options.unit}, Memory size: {options.count} registers")
    
    # Create device with simulated memory
    device = Device(options.unit, options.count)
    server = None
    if options.type == ProtocolType.TCP:
        server = ModbusTcpServer(device)
        server.setPort(options.port)
        server.setTimeout(options.timeout)
        server.setMaxConnections(options.max_connections)
        print(f"Listening on port {options.port}")
    elif options.type == ProtocolType.RTU:
        rtu_port = ModbusRtuPort(blocking=False)
        rtu_port.setPortName(options.serial_port)
        rtu_port.setBaudRate(options.baud_rate)
        rtu_port.setDataBits(options.data_bits)
        rtu_port.setParity(options.parity)
        rtu_port.setStopBits(options.stop_bits)
        rtu_port.setTimeoutFirstByte(options.timeout_first_byte)
        rtu_port.setTimeoutInterByte(options.timeout_inter_byte)
        server = ModbusServerResource(rtu_port, device)
    elif options.type == ProtocolType.ASC:
        asc_port = ModbusAscPort(blocking=False)
        asc_port.setPortName(options.serial_port)
        asc_port.setBaudRate(options.baud_rate)
        asc_port.setDataBits(options.data_bits)
        asc_port.setParity(options.parity)
        asc_port.setStopBits(options.stop_bits)
        asc_port.setTimeoutFirstByte(options.timeout_first_byte)
        asc_port.setTimeoutInterByte(options.timeout_inter_byte)
        server = ModbusServerResource(asc_port, device)
    else:
        print(f"Unsupported protocol type: {options.type}")
        sys.exit(1)

    # Create and start server
    print("-" * 50)     
    try:
        print("demoserver starts ...")
        tmr = timer()
        counter = 0
        while True:
            try:
                server.process()
            except ModbusException as e:
                print(f"Modbus Exception: {e}")
            # Increment first register every second (for demonstration)
            counter =  (counter + 1) % 65536
            if timer() - tmr >= 1000:
                device.increment()
                tmr = timer()
                device.memory[0] = counter
                print(f"Register[0] value: {device.memory[0]}")
            
            time.sleep(0.001)  # Small delay to prevent 100% CPU usage
            
    except KeyboardInterrupt:
        print("Server stopped.")

if __name__ == "__main__":
    main()