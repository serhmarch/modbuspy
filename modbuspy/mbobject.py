"""
ModbusObject.py - Contains object definitions of the Modbus library for Python.

Author: serhmarch
Date: November 2025
"""
from typing import Callable, List, Any
from weakref import WeakMethod, WeakKeyDictionary

class ModbusObject:
    """Base class for Modbus objects"""

    class Signal:
        """Qt-like signal implementation for Python."""
        
        def __init__(self):
            self._slots: List[Callable] = []
            
        def connect(self, slot: Callable) -> None:
            """Connect a slot (function/method) to this signal."""
            if slot not in self._slots:
                # Use weak references for methods to avoid memory leaks
                if hasattr(slot, '__self__'):
                    self._slots.append(WeakMethod(slot, self._cleanup))
                else:
                    self._slots.append(slot)
        
        def disconnect(self, slot: Callable = None) -> None:
            """Disconnect a slot or all slots if slot is None."""
            if slot is None:
                self._slots.clear()
            else:
                self._slots = [s for s in self._slots if s != slot and 
                            (not isinstance(s, WeakMethod) or s() != slot)]
        
        def emit(self, *args, **kwargs) -> None:
            """Emit the signal, calling all connected slots."""
            # Create a copy to avoid modification during iteration
            slots_copy = self._slots.copy()
            for slot in slots_copy:
                try:
                    if isinstance(slot, WeakMethod):
                        method = slot()
                        if method is not None:
                            method(*args, **kwargs)
                        # If method is None, weak reference died, remove it
                        else:
                            self._slots.remove(slot)
                    else:
                        slot(*args, **kwargs)
                except Exception as e:
                    print(f"Error calling slot {slot}: {e}")
        
        def _cleanup(self, weak_ref):
            """Clean up dead weak references."""
            if weak_ref in self._slots:
                self._slots.remove(weak_ref)


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

    @property
    def Name(self) -> str:
        """Property. Get the name of the Modbus object."""
        return self.objectName()

    @Name.setter
    def Name(self, name: str) -> None:
        """Property. Set the name of the Modbus object."""
        return self.setObjectName(name)

