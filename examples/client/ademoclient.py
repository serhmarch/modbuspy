#!/usr/bin/env python3
"""
ademoclient.py - Asynchronous Python Modbus Client Demo

This is an asynchronous version of democlient.py that demonstrates how to use
the ModbusAsyncClientPort class for non-blocking Modbus operations.

Author: serhmarch
Date: November 2025
"""

import sys
import os
import argparse
import time
import asyncio
from typing import List, Optional

from libmodbuspy.port import ModbusRtuOverTcpPort, ModbusTcpPort

# Add the libmodbuspy library path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import libmodbuspy modules
from libmodbuspy import StatusCode, StatusIsGood
from libmodbuspy.mbglobal import (ProtocolType, Constants,
                               MBF_READ_COILS, MBF_READ_DISCRETE_INPUTS, 
                               MBF_READ_HOLDING_REGISTERS, MBF_READ_INPUT_REGISTERS,
                               MBF_WRITE_SINGLE_COIL, MBF_WRITE_SINGLE_REGISTER,
                               MBF_READ_EXCEPTION_STATUS, MBF_WRITE_MULTIPLE_COILS,
                               MBF_WRITE_MULTIPLE_REGISTERS, MBF_REPORT_SERVER_ID, MBF_MASK_WRITE_REGISTER,
                               MBF_READ_WRITE_MULTIPLE_REGISTERS, MBF_READ_FIFO_QUEUE)
from libmodbuspy import (
                         ModbusClient,
                         ModbusAsyncClientPort,
                         ModbusException,
                         ModbusTcpPort,
                         ModbusUdpPort,
                         ModbusRtuPort,
                         ModbusAscPort,
                         ModbusRtuOverTcpPort,
                         ModbusAscOverTcpPort,
                         ModbusRtuOverUdpPort,
                         ModbusAscOverUdpPort
                        )

def print_regs(count: int, buff: bytes) -> None:
    """Print register values from buffer."""
    for i in range(count):
        val = (buff[i*2+1] << 8) | buff[i*2]
        print(val, end=' ')
    print()

def print_bools(count: int, buff: bytes) -> None:
    """Print boolean values from buffer."""
    for i in range(count):
        byte_idx = i // 8
        bit_idx = i % 8
        if byte_idx < len(buff):
            val = (buff[byte_idx] >> bit_idx) & 1
            print(bool(val), end=' ')
        else:
            print(False, end=' ')
    print()

def print_opened(source: str) -> None:
    """Print opened port message."""
    print(f"{source} opened.")

def print_closed(source: str) -> None:
    """Print closed port message."""
    print(f"{source} closed.")

def print_error(source: str, code: int, text: str) -> None:
    """Print error message."""
    print(f"{source} Error {code}: {text}")

def print_tx(source: str, buff: bytes) -> None:
    """Print transmitted data."""
    hex_str = ' '.join(f'{b:02X}' for b in buff)
    print(f"{source} Tx: {hex_str}")

def print_rx(source: str, buff: bytes) -> None:
    """Print received data."""
    hex_str = ' '.join(f'{b:02X}' for b in buff)
    print(f"{source} Rx: {hex_str}")

class Options:
    """Configuration options for the demo client."""
    
    def __init__(self):
        self.blocking = False  # Always non-blocking for async
        # Protocol settings
        self.type = ProtocolType.TCP
        self.unit = 1        
        # TCP settings
        self.host    = ModbusTcpPort.Defaults.host
        self.port    = ModbusTcpPort.Defaults.port
        self.timeout = ModbusTcpPort.Defaults.timeout        
        # Serial settings (not implemented in current libmodbuspy)
        self.serial_port = ModbusRtuPort.Defaults.portName
        self.baud_rate = ModbusRtuPort.Defaults.baudRate
        self.data_bits = ModbusRtuPort.Defaults.dataBits
        self.parity = ModbusRtuPort.Defaults.parity
        self.stop_bits = ModbusRtuPort.Defaults.stopBits
        self.timeout_first_byte = ModbusRtuPort.Defaults.timeoutFirstByte
        self.timeout_inter_byte = ModbusRtuPort.Defaults.timeoutInterByte
        # Function parameters
        self.offset = 0
        self.count = 16

def parse_arguments() -> Options:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Asynchronous Modbus Demo Client - Python version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ademoclient.py -t TCP -r 192.168.1.100 -p 502
  ademoclient.py -u 2 -o 100 -c 10
        """
    )
    
    parser.add_argument('-u', '--unit', type=int, default=1,
                       help='Modbus device remote address/unit (default: 1)')
    parser.add_argument('-t', '--type', choices=['TCP', 'UDP', 'RTU', 'ASC', 'RTUvTCP', 'ASCvTCP', 'RTUvUDP', 'ASCvUDP'], default='TCP',
                       help='Protocol type (default: TCP)')
    parser.add_argument('-r', '--host', '--remote', default='localhost',
                       help='DNS name or IP address for TCP (default: localhost)')
    parser.add_argument('-p', '--port', type=int, default=Constants.STANDARD_TCP_PORT,
                       help=f'Remote TCP port (default: {Constants.STANDARD_TCP_PORT})')
    parser.add_argument('--tm', type=int, default=3000,
                       help='Timeout for TCP in milliseconds (default: 3000)')
    parser.add_argument('--serial', '-sl',
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
    parser.add_argument('-o', '--offset', type=int, default=0,
                       help='Modbus function data start offset (default: 0)')
    parser.add_argument('-c', '--count', type=int, default=16,
                       help='Modbus function data count (default: 16)')
    
    args = parser.parse_args()
    
    options = Options()
    # Note: blocking is always False for async operations

    # Set protocol type
    if args.type == 'TCP':
        options.type = ProtocolType.TCP
    elif args.type == 'UDP':
        options.type = ProtocolType.UDP
    elif args.type == 'RTU':
        options.type = ProtocolType.RTU
    elif args.type == 'ASC':
        options.type = ProtocolType.ASC
    elif args.type == 'RTUvTCP':
        options.type = ProtocolType.RTUvTCP
    elif args.type == 'ASCvTCP':
        options.type = ProtocolType.ASCvTCP
    elif args.type == 'RTUvUDP':
        options.type = ProtocolType.RTUvUDP
    elif args.type == 'ASCvUDP':
        options.type = ProtocolType.ASCvUDP
    else:
        options.type = ProtocolType.TCP  # Fallback to TCP
    
    options.unit = args.unit

    ## TCP settings
    options.host = args.host
    options.port = args.port
    options.timeout = args.tm
    
    # Serial settings
    if args.serial:
        options.serial_port = args.serial
    options.baud_rate = args.baud
    options.data_bits = args.data
    
    options.offset = args.offset
    options.count = args.count
    
    return options

class RequestParams:
    """Parameters for a Modbus request."""
    def __init__(self, func: int, offset: int, count: int):
        self.func = func
        self.offset = offset
        self.count = count

async def async_main():
    """Asynchronous main function."""
    options = parse_arguments()
    
    # Create client port based on protocol type
    blocking = False  # Always False for async
    client_port = None
    
    if options.type == ProtocolType.TCP:
        port = ModbusTcpPort(blocking)
        port.setHost(options.host)
        port.setPort(options.port)
        port.setTimeout(options.timeout)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncTCP")
    elif options.type == ProtocolType.UDP:
        port = ModbusUdpPort(blocking)
        port.setHost(options.host)
        port.setPort(options.port)
        port.setTimeout(options.timeout)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncUDP")
    elif options.type == ProtocolType.RTU:
        port = ModbusRtuPort(blocking)
        port.setPortName(options.serial_port)
        port.setBaudRate(options.baud_rate)
        port.setDataBits(options.data_bits)
        port.setParity(options.parity)
        port.setStopBits(options.stop_bits)
        port.setTimeoutFirstByte(options.timeout_first_byte)
        port.setTimeoutInterByte(options.timeout_inter_byte)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncRTU")
    elif options.type == ProtocolType.ASC:
        port = ModbusAscPort(blocking)
        port.setPortName(options.serial_port)
        port.setBaudRate(options.baud_rate)
        port.setDataBits(options.data_bits)
        port.setParity(options.parity)
        port.setStopBits(options.stop_bits)
        port.setTimeoutFirstByte(options.timeout_first_byte)
        port.setTimeoutInterByte(options.timeout_inter_byte)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncASC")
    elif options.type == ProtocolType.RTUvTCP:
        port = ModbusRtuOverTcpPort(blocking)
        port.setHost(options.host)
        port.setPort(options.port)
        port.setTimeout(options.timeout)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncRTUvTCP")
    elif options.type == ProtocolType.ASCvTCP:
        port = ModbusAscOverTcpPort(blocking)
        port.setHost(options.host)
        port.setPort(options.port)
        port.setTimeout(options.timeout)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncASCvTCP")
    elif options.type == ProtocolType.RTUvUDP:
        port = ModbusRtuOverUdpPort(blocking)
        port.setHost(options.host)
        port.setPort(options.port)
        port.setTimeout(options.timeout)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncRTUvUDP")
    elif options.type == ProtocolType.ASCvUDP:
        port = ModbusAscOverUdpPort(blocking)
        port.setHost(options.host)
        port.setPort(options.port)
        port.setTimeout(options.timeout)
        client_port = ModbusAsyncClientPort(port)
        client_port.setObjectName("AsyncASCvUDP")
    else:
        print(f"Unsupported protocol type: {options.type}")
        sys.exit(1)
    
    # Connect signals
    client_port.signalOpened.connect(print_opened)
    client_port.signalClosed.connect(print_closed)
    client_port.signalError.connect(print_error)
    client_port.signalTx.connect(print_tx)
    client_port.signalRx.connect(print_rx)

    # Define test requests
    requests = [
        RequestParams(MBF_READ_COILS, options.offset, options.count),
        RequestParams(MBF_READ_DISCRETE_INPUTS, options.offset, options.count),
        RequestParams(MBF_READ_HOLDING_REGISTERS, options.offset, options.count),
        RequestParams(MBF_READ_INPUT_REGISTERS, options.offset, options.count),
        RequestParams(MBF_WRITE_SINGLE_COIL, options.offset, 0),
        RequestParams(MBF_WRITE_SINGLE_REGISTER, options.offset, 0),
        RequestParams(MBF_READ_EXCEPTION_STATUS, options.offset, 0),
        RequestParams(MBF_WRITE_MULTIPLE_COILS, options.offset, options.count),
        RequestParams(MBF_WRITE_MULTIPLE_REGISTERS, options.offset, options.count),
        RequestParams(MBF_REPORT_SERVER_ID, 0, 0),
        RequestParams(MBF_MASK_WRITE_REGISTER, options.offset, 0),
        RequestParams(MBF_READ_WRITE_MULTIPLE_REGISTERS, options.offset, options.count),
        RequestParams(MBF_READ_FIFO_QUEUE, options.offset, 0)
    ]
    
    # Create test data buffer
    buff = bytearray(options.count * 2)  # Buffer for register data
    for i in range(len(buff)):
        buff[i] = i % 256  # Fill with test pattern
    
    # Create async client
    client = ModbusClient(options.unit, client_port)
    client.setObjectName(f"asyncdemo({client.unit()})")
    
    # Execute test requests asynchronously
    for req in requests:
        start_time = time.time()
        
        try:
            if req.func == MBF_READ_COILS:
                print(f"READ_COILS(offset={req.offset}, count={req.count})")
                result = await client.readCoils(req.offset, req.count)
                print_bools(req.count, result)
                    
            elif req.func == MBF_READ_DISCRETE_INPUTS:
                print(f"READ_DISCRETE_INPUTS(offset={req.offset}, count={req.count})")
                result = await client.readDiscreteInputs(req.offset, req.count)
                print_bools(req.count, result)
                    
            elif req.func == MBF_READ_HOLDING_REGISTERS:
                print(f"READ_HOLDING_REGISTERS(offset={req.offset}, count={req.count})")
                result = await client.readHoldingRegisters(req.offset, req.count)
                print_regs(req.count, result)
                    
            elif req.func == MBF_READ_INPUT_REGISTERS:
                print(f"READ_INPUT_REGISTERS(offset={req.offset}, count={req.count})")
                result = await client.readInputRegisters(req.offset, req.count)
                print_regs(req.count, result)

            elif req.func == MBF_WRITE_SINGLE_COIL:
                print(f"WRITE_SINGLE_COIL(offset={req.offset})")
                test_value = True  # Test value
                print(f"Writing: {test_value}")
                status = await client.writeSingleCoil(req.offset, test_value)
                if StatusIsGood(status):
                    print("Good")
                else:
                    print(f"Error: status={status}, {client_port.lastErrorText()}")
                    
            elif req.func == MBF_WRITE_SINGLE_REGISTER:
                print(f"WRITE_SINGLE_REGISTER(offset={req.offset})")
                test_value = 12345  # Test value
                print(f"Writing: {test_value}")
                status = await client.writeSingleRegister(req.offset, test_value)
                if StatusIsGood(status):
                    print("Good")
                else:
                    print(f"Error: status={status}, {client_port.lastErrorText()}")
                    
            elif req.func == MBF_READ_EXCEPTION_STATUS:
                print("READ_EXCEPTION_STATUS")
                result = await client.readExceptionStatus()
                print(f"Exception status: {result[0] if len(result) > 0 else 0}")
                    
            elif req.func == MBF_WRITE_MULTIPLE_COILS:
                print(f"WRITE_MULTIPLE_COILS(offset={req.offset}, count={req.count})")
                # Create test coil data
                coil_data = bytearray((req.count + 7) // 8)
                for i in range(len(coil_data)):
                    coil_data[i] = 0xAA  # Alternating pattern
                print_bools(req.count, coil_data)
                status = await client.writeMultipleCoils(req.offset, coil_data, req.count)
                if StatusIsGood(status):
                    print("Good")
                else:
                    print(f"Error: status={status}, {client_port.lastErrorText()}")
                    
            elif req.func == MBF_WRITE_MULTIPLE_REGISTERS:
                print(f"WRITE_MULTIPLE_REGISTERS(offset={req.offset}, count={req.count})")
                # Create test register data
                reg_data = bytearray(req.count * 2)
                for i in range(req.count):
                    val = i + 1000  # Test values starting from 1000
                    reg_data[i*2+1] = (val >> 8) & 0xFF
                    reg_data[i*2] = val & 0xFF
                print_regs(req.count, reg_data)
                status = await client.writeMultipleRegisters(req.offset, reg_data)
                if StatusIsGood(status):
                    print("Good")
                else:
                    print(f"Error: status={status}, {client_port.lastErrorText()}")
                    
            elif req.func == MBF_REPORT_SERVER_ID:
                print("REPORT_SERVER_ID")
                result = await client.reportServerID()
                print(f"Server ID: {str(result)}")
                    
            elif req.func == MBF_MASK_WRITE_REGISTER:
                print(f"MASK_WRITE_REGISTER(offset={req.offset})")
                and_mask = 0x00FF  # Test masks
                or_mask = 0x0F00
                print(f"AND mask: {and_mask:04X}, OR mask: {or_mask:04X}")
                status = await client.maskWriteRegister(req.offset, and_mask, or_mask)
                if StatusIsGood(status):
                    print("Good")
                else:
                    print(f"Error: status={status}, {client_port.lastErrorText()}")
                    
            elif req.func == MBF_READ_WRITE_MULTIPLE_REGISTERS:
                print(f"READ_WRITE_MULTIPLE_REGISTERS(offset={req.offset}, count={req.count})")
                # Create test write data
                write_data = bytearray(req.count * 2)
                for i in range(req.count):
                    val = i + 2000  # Test values starting from 2000
                    write_data[i*2+1] = (val >> 8) & 0xFF
                    write_data[i*2] = val & 0xFF
                print(f"Writing: ", end="")
                print_regs(req.count, write_data)
                result = await client.readWriteMultipleRegisters(req.offset, req.count, 
                                                                 req.offset, write_data)
                print(f"Read: ", end="")
                print_regs(req.count, result)

            elif req.func == MBF_READ_FIFO_QUEUE:
                print(f"READ_FIFO_QUEUE(offset={req.offset})")
                result = await client.readFIFOQueue(req.offset)
                fifo_count = len(result) // 2
                print(f"FIFO: ", end="")
                print_regs(fifo_count, result)

        except ModbusException as e:
            print(f"Modbus Exception: {e}")
        except Exception as e:
            print(f"Exception occurred: {e}")
        
        # Timing control - wait at least 1 second between requests
        exec_time = time.time() - start_time
        period = 1.0  # 1 second
        if exec_time < period:
            await asyncio.sleep(period - exec_time)
        else:
            await asyncio.sleep(0.001)  # Small delay
    
    # Cleanup
    if client_port:
        client_port.close()
    
    #print(f"{client.Name} completed.")
    print(f"Example completed.")

def main():
    """Main entry point that runs the async main function."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()