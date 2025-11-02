"""
ModbusObject.py - Contains object definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""

class ModbusObject:
    """Base class for Modbus objects"""
    def __init__(self, name = ""):
        self._name = name

    def __repr__(self):
        return f"ModbusObject(name={self._name})"

    def objectName(self):
        """Returns the name of the Modbus object"""
        return self._name
    
    def setObjectName(self, name):
        """Sets the name of the Modbus object"""
        self._name = name

    def connect(self):
        """Connects the Modbus object"""
        pass

    def disconnect(self):
        """Disconnects the Modbus object"""
        pass