"""
@file utils.py
@brief Utility functions for modbuspy library.

@author serhmarch
@date November 2025
"""

from .mbglobal import ProtocolType, ModbusInterface
from .port import ModbusPort
from .tcpport import ModbusTcpPort
from .rtuport import ModbusRtuPort
from .ascport import ModbusAscPort
from .clientport import ModbusClientPort
from .serverport import ModbusServerPort
from .serverresource import ModbusServerResource
from .tcpserver import ModbusTcpServer

def createPort(protocolType: ProtocolType, blocking: bool, **settings) -> ModbusPort:
    """Factory function to create ModbusPort instance based on specified protocol type and settings.
    
    Args:
        protocolType: Protocol type (ProtocolType enum).
        blocking: Blocking mode (True/False).
        **settings: Additional settings for the port.

    Returns:
        An instance of ModbusPort.
    """
    if protocolType == ProtocolType.TCP:
        p = ModbusTcpPort(blocking=blocking)
        p.setSettings(settings)
        return p
    elif protocolType == ProtocolType.RTU:
        p = ModbusRtuPort(blocking=blocking)
        p.setSettings(settings)
        return p
    elif protocolType == ProtocolType.ASC:
        p = ModbusAscPort(blocking=blocking)
        p.setSettings(settings)
        return p
    else:
        raise ValueError(f"Unsupported protocol type: {protocolType}")
    
def createClientPort(protocolType :ProtocolType, blocking: bool, **settings) -> ModbusClientPort:
    """Factory function to create ModbusClientPort instance based on specified protocol type and settings.

    Args:
        protocolType: Protocol type (ProtocolType enum).
        blocking: Blocking mode (True/False).
        **settings: Additional settings for the client port.

    Returns:
        An instance of ModbusClientPort.
    """
    port = createPort(protocolType, blocking, **settings)
    return ModbusClientPort(port)

def createServerPort(device: ModbusInterface, protocolType: ProtocolType, blocking: bool, **settings) -> ModbusServerPort:
    """Factory function to create ModbusServerPort instance based on specified protocol type and settings.
    
    Args:
        device: ModbusInterface device instance.
        protocolType: Protocol type (ProtocolType enum).
        blocking: Blocking mode (True/False).
        **settings: Additional settings for the server port.
        
    Returns:
        An instance of ModbusServerPort.
    """
    serv = None
    if protocolType == ProtocolType.TCP:
        tcp = ModbusTcpServer(device)
        tcp.setSettings(settings)
        serv = tcp
    else:
        port = createPort(protocolType, blocking, **settings)
        serv = ModbusServerResource(port, device)
    return serv