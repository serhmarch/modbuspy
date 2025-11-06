#!/usr/bin/env python3
"""
democlient.py - Python translation of ModbusLib democlient.cpp example

Author: serhmarch (translated from C++)
Date: November 2025
"""

import sys
import os
import argparse
import time
from typing import List, Optional

# Add the modbuspy library path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import modbuspy modules
from modbuspy.ModbusStatusCode import StatusCode, StatusIsGood
from modbuspy.ModbusGlobal import (ProtocolType, Constants,
                                   MBF_READ_COILS, MBF_READ_DISCRETE_INPUTS, 
                                   MBF_READ_HOLDING_REGISTERS, MBF_READ_INPUT_REGISTERS,
                                   MBF_WRITE_SINGLE_COIL, MBF_WRITE_SINGLE_REGISTER,
                                   MBF_READ_EXCEPTION_STATUS, MBF_WRITE_MULTIPLE_COILS,
                                   MBF_WRITE_MULTIPLE_REGISTERS, MBF_REPORT_SERVER_ID, MBF_MASK_WRITE_REGISTER,
                                   MBF_READ_WRITE_MULTIPLE_REGISTERS, MBF_READ_FIFO_QUEUE)
from modbuspy.ModbusClient import ModbusClient
from modbuspy.ModbusTcpPort import ModbusTcpPort
from modbuspy.ModbusRtuPort import ModbusRtuPort
from modbuspy.ModbusAscPort import ModbusAscPort
from modbuspy.ModbusClientPort import ModbusClientPort
from modbuspy.ModbusExceptions import ModbusException

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
        self.blocking = True    
        # Protocol settings
        self.type = ProtocolType.TCP
        self.unit = 1
        
        # TCP settings
        self.host    = ModbusTcpPort.Defaults.host
        self.port    = ModbusTcpPort.Defaults.port
        self.timeout = ModbusTcpPort.Defaults.timeout
        
        # Serial settings (not implemented in current modbuspy)
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
        description="Modbus Demo Client - Python version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  democlient.py -t TCP -r 192.168.1.100 -p 502
  democlient.py -u 2 -o 100 -c 10
        """
    )
    
    parser.add_argument('--block', type=int, default=1,
                       help='Use blocking mode (1) or non-blocking (0) (default: 1)')
    parser.add_argument('-u', '--unit', type=int, default=1,
                       help='Modbus device remote address/unit (default: 1)')
    parser.add_argument('-t', '--type', choices=['TCP', 'RTU', 'ASC'], default='TCP',
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
    options.blocking = args.block

    # Set protocol type
    if args.type == 'TCP':
        options.type = ProtocolType.TCP
    elif args.type == 'RTU':
        options.type = ProtocolType.RTU
    elif args.type == 'ASC':
        options.type = ProtocolType.ASC
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
    #options.parity = args.parity
    #options.stop_bits = float(args.stop)
    #options.timeout_first_byte = args.tfb
    #options.timeout_inter_byte = args.tib
    
    options.offset = args.offset
    options.count = args.count
    
    return options

class RequestParams:
    """Parameters for a Modbus request."""
    def __init__(self, func: int, offset: int, count: int):
        self.func = func
        self.offset = offset
        self.count = count

def main():
    """Main function."""
    options = parse_arguments()
    
    # Create client port based on protocol type
    blocking = bool(options.blocking)
    client_port = None
    
    if options.type == ProtocolType.TCP:
        tcp_port = ModbusTcpPort(blocking)
        tcp_port.setHost(options.host)
        tcp_port.setPort(options.port)
        tcp_port.setTimeout(options.timeout)
        client_port = ModbusClientPort(tcp_port)
        client_port.setObjectName("TCP")
    elif options.type == ProtocolType.RTU:
        rtu_port = ModbusRtuPort(blocking)
        rtu_port.setPortName(options.serial_port)
        rtu_port.setBaudRate(options.baud_rate)
        rtu_port.setDataBits(options.data_bits)
        rtu_port.setParity(options.parity)
        rtu_port.setStopBits(options.stop_bits)
        rtu_port.setTimeoutFirstByte(options.timeout_first_byte)
        rtu_port.setTimeoutInterByte(options.timeout_inter_byte)
        client_port = ModbusClientPort(rtu_port)
        client_port.setObjectName("RTU")
    elif options.type == ProtocolType.ASC:
        asc_port = ModbusAscPort(blocking)
        asc_port.setPortName(options.serial_port)
        asc_port.setBaudRate(options.baud_rate)
        asc_port.setDataBits(options.data_bits)
        asc_port.setParity(options.parity)
        asc_port.setStopBits(options.stop_bits)
        asc_port.setTimeoutFirstByte(options.timeout_first_byte)
        asc_port.setTimeoutInterByte(options.timeout_inter_byte)
        client_port = ModbusClientPort(asc_port)
        client_port.setObjectName("ASC")
    else:
        print(f"Unsupported protocol type: {options.type}")
        sys.exit(1)
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
    
    # Create client
    client = ModbusClient(options.unit, client_port)
    client.setObjectName(f"democlient({client.unit()})")

    # Execute test requests
    for req in requests:
        start_time = time.time()
        
        try:
            if req.func == MBF_READ_COILS:
                print(f"READ_COILS(offset={req.offset}, count={req.count})")
                while 1:
                    result = client.readCoils(req.offset, req.count)
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print_bools(req.count, result)
                    break
                    
            elif req.func == MBF_READ_DISCRETE_INPUTS:
                print(f"READ_DISCRETE_INPUTS(offset={req.offset}, count={req.count})")
                while 1:
                    result = client.readDiscreteInputs(req.offset, req.count)
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print_bools(req.count, result)
                    break
                    
            elif req.func == MBF_READ_HOLDING_REGISTERS:
                print(f"READ_HOLDING_REGISTERS(offset={req.offset}, count={req.count})")
                while 1:
                    result = client.readHoldingRegisters(req.offset, req.count)
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print_regs(req.count, result)
                    break
                    
            elif req.func == MBF_READ_INPUT_REGISTERS:
                print(f"READ_INPUT_REGISTERS(offset={req.offset}, count={req.count})")
                while 1:
                    result = client.readInputRegisters(req.offset, req.count)
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print_regs(req.count, result)
                    break

            elif req.func == MBF_WRITE_SINGLE_COIL:
                print(f"WRITE_SINGLE_COIL(offset={req.offset})")
                test_value = True  # Test value
                print(f"Writing: {test_value}")
                while 1:
                    status = client.writeSingleCoil(req.offset, test_value)
                    if status is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    if StatusIsGood(status):
                        print("Good")
                    else:
                        print(f"Error: status={status}, {client_port.lastErrorText()}")
                    break
                    
            elif req.func == MBF_WRITE_SINGLE_REGISTER:
                print(f"WRITE_SINGLE_REGISTER(offset={req.offset})")
                test_value = 12345  # Test value
                print(f"Writing: {test_value}")
                while 1:
                    status = client.writeSingleRegister(req.offset, test_value)
                    if status is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    if StatusIsGood(status):
                        print("Good")
                    else:
                        print(f"Error: status={status}, {client_port.lastErrorText()}")
                    break
                    
            elif req.func == MBF_READ_EXCEPTION_STATUS:
                print("READ_EXCEPTION_STATUS")
                while 1:
                    result = client.readExceptionStatus()
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print(f"Exception status: {result[0] if len(result) > 0 else 0}")
                    break
                    
            elif req.func == MBF_WRITE_MULTIPLE_COILS:
                print(f"WRITE_MULTIPLE_COILS(offset={req.offset}, count={req.count})")
                # Create test coil data
                coil_data = bytearray((req.count + 7) // 8)
                for i in range(len(coil_data)):
                    coil_data[i] = 0xAA  # Alternating pattern
                print_bools(req.count, coil_data)
                while 1:
                    status = client.writeMultipleCoils(req.offset, req.count, coil_data)
                    if status is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    if StatusIsGood(status):
                        print("Good")
                    else:
                        print(f"Error: status={status}, {client_port.lastErrorText()}")
                    break
                    
            elif req.func == MBF_WRITE_MULTIPLE_REGISTERS:
                print(f"WRITE_MULTIPLE_REGISTERS(offset={req.offset}, count={req.count})")
                # Create test register data
                reg_data = bytearray(req.count * 2)
                for i in range(req.count):
                    val = i + 1000  # Test values starting from 1000
                    reg_data[i*2] = (val >> 8) & 0xFF
                    reg_data[i*2+1] = val & 0xFF
                print_regs(req.count, reg_data)
                while 1:
                    status = client.writeMultipleRegisters(req.offset, req.count, reg_data)
                    if status is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    if StatusIsGood(status):
                        print("Good")
                    else:
                        print(f"Error: status={status}, {client_port.lastErrorText()}")
                    break
                    
            elif req.func == MBF_REPORT_SERVER_ID:
                print("REPORT_SERVER_ID")
                while 1:
                    result = client.reportServerID()
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print(f"Server ID: {str(result)}")
                    break
                    
            elif req.func == MBF_MASK_WRITE_REGISTER:
                print(f"MASK_WRITE_REGISTER(offset={req.offset})")
                and_mask = 0x00FF  # Test masks
                or_mask = 0x0F00
                print(f"AND mask: {and_mask:04X}, OR mask: {or_mask:04X}")
                while 1:
                    status = client.maskWriteRegister(req.offset, and_mask, or_mask)
                    if status is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    if StatusIsGood(status):
                        print("Good")
                    else:
                        print(f"Error: status={status}, {client_port.lastErrorText()}")
                    break
                    
            elif req.func == MBF_READ_WRITE_MULTIPLE_REGISTERS:
                print(f"READ_WRITE_MULTIPLE_REGISTERS(offset={req.offset}, count={req.count})")
                # Create test write data
                write_data = bytearray(req.count * 2)
                for i in range(req.count):
                    val = i + 2000  # Test values starting from 2000
                    write_data[i*2] = (val >> 8) & 0xFF
                    write_data[i*2+1] = val & 0xFF
                print(f"Writing: ", end="")
                print_regs(req.count, write_data)
                while 1:
                    result = client.readWriteMultipleRegisters(req.offset, req.count, 
                                                            req.offset, req.count, write_data)
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    print(f"Read: ", end="")
                    print_regs(req.count, result)
                    break

            elif req.func == MBF_READ_FIFO_QUEUE:
                print(f"READ_FIFO_QUEUE(offset={req.offset})")
                while 1:
                    result = client.readFIFOQueue(req.offset)
                    if result is None: # for non-blocking mode
                        time.sleep(0.001)
                        continue
                    fifo_count = len(result) // 2
                    print(f"FIFO: ", end="")
                    print_regs(fifo_count, result)
                    break

        except ModbusException as e:
            #print(f"Exception occurred: {e}")
            pass
        
        # Timing control - wait at least 1 second between requests
        exec_time = time.time() - start_time
        period = 1.0  # 1 second
        if exec_time < period:
            time.sleep(period - exec_time)
        else:
            time.sleep(0.001)  # Small delay
    
    # Cleanup
    if client_port:
        client_port.close()
    
    print("Demo client completed.")


if __name__ == "__main__":
    main()