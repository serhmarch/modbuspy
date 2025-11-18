"""
ModbusServerResource.py - The module defines the class that controls specific port

Author: serhmarch
Date: November 2025
"""

from typing import Optional, Tuple

from .statuscode import StatusCode, StatusIsStandardError, StatusIsBad

from . import exceptions
from .exceptions import ModbusException
from .mbglobal import *
from .mbinterface import ModbusInterface
from .serverport import ModbusServerPort
from .port import ModbusPort


class ModbusServerResource(ModbusServerPort):
    """Implements direct control for ModbusPort derived classes (TCP or serial) for server side.

    ModbusServerResource derived from ModbusServerPort and makes ModbusPort object behaves 
    like server port. Pointer to ModbusPort object is passed to ModbusServerResource constructor.

    Also ModbusServerResource have ModbusInterface object as second parameter of constructor which
    processes every Modbus function request.
    """

    def __init__(self, port: ModbusPort, device: ModbusInterface):
        """Constructor of the class.
        
        Args:
            port: Pointer to the ModbusPort which is managed by the current class object.
            device: Pointer to the ModbusInterface implementation to which all requests 
                   for Modbus functions are forwarded.
        """
        super().__init__(device)
        self._isErrorPort = False
        self._port = port
        self._port.setServerMode(True)
        self._unit = 0
        self._func = 0
        self._offset = 0
        self._subfunc = 0
        self._status = 0
        self._count = 0
        self._byteCount = 0
        self._messageCount = 0
        self._andMask = 0
        self._orMask = 0
        self._writeOffset = 0
        self._outByteCount = 0
        self._valueBuff = bytearray()
        self._value = 0

    def port(self) -> ModbusPort:
        """Returns pointer to inner port which was previously passed in constructor.
        
        Returns:
            The ModbusPort instance managed by this resource.
        """
        return self._port

    # Server port interface implementations

    def type(self) -> ProtocolType:
        """Returns type of Modbus protocol. Same as port().type().
        
        Returns:
            The protocol type (TCP, RTU, or ASC).
        """
        return self._port.type()

    def timeout(self) -> int:
        return self._port.timeout()

    def setTimeout(self, timeout: int) -> None:
        self._port.setTimeout(timeout)

    def open(self) -> StatusCode:
        """Opens the underlying port for server operations.
        
        Returns:
            StatusCode indicating the result of the operation.
        """
        self._cmdClose = False
        return StatusCode.Status_Good

    def close(self) -> StatusCode:
        """Closes the underlying port.

        Returns:
            StatusCode indicating the result of the operation.
        """
        self._cmdClose = True
        return StatusCode.Status_Good

    def isOpen(self) -> bool:
        """Checks if the underlying port is open.
        
        Returns:
            True if the port is open, False otherwise.
        """
        return self._port.isOpen()

    def process(self) -> StatusCode:
        """Main processing function that must be called in the cycle.

        Returns:
            StatusCode indicating the result of the operation.
        """
        fRepeatAgain = True
        while fRepeatAgain:
            fRepeatAgain = False
            if self._state == ModbusServerPort.State.STATE_CLOSED:
                if self._cmdClose:
                    break
                self._state = ModbusServerPort.State.STATE_BEGIN_OPEN
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_BEGIN_OPEN:
                self._timestampRefresh()
                self._state = ModbusServerPort.State.STATE_WAIT_FOR_OPEN
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_WAIT_FOR_OPEN:
                if self._cmdClose:
                    self._state = ModbusServerPort.State.STATE_WAIT_FOR_CLOSE
                    fRepeatAgain = True
                    continue
                try:
                    r = self._port.open()
                    if r is None:
                        return None
                except ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    self._state = ModbusServerPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                self.signalOpened.emit(self.objectName())
                self._state = ModbusServerPort.State.STATE_OPENED
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_WAIT_FOR_CLOSE:
                try:
                    r = self._port.close()
                    if r is None:
                        return None
                except ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    self._state = ModbusServerPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                self.signalClosed.emit(self.objectName())
                self._state = ModbusServerPort.State.STATE_CLOSED
                return StatusCode.Status_Good
            elif self._state in (ModbusServerPort.State.STATE_OPENED,
                                 ModbusServerPort.State.STATE_BEGIN_READ):
                self._timestampRefresh()
                self._state = ModbusServerPort.State.STATE_READ
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_READ:
                if self._cmdClose:
                    self._state = ModbusServerPort.State.STATE_WAIT_FOR_CLOSE
                    fRepeatAgain = True
                    continue
                try:
                    r = self._port.read()
                    if r is None:
                        return None
                except ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    self._state = ModbusServerPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                if not self._port.isOpen():
                    self.signalClosed.emit(self.objectName())
                    self._state = ModbusServerPort.State.STATE_CLOSED
                    return StatusCode.Status_Uncertain
                self.signalRx.emit(self.objectName(), self._port.readBufferData())
                try:
                    self._unit, self._func, buff = self._port.readBuffer()
                    r = self._processInputData(buff)
                except ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    if StatusIsStandardError(e.code):
                        self._state = ModbusServerPort.State.STATE_BEGIN_WRITE
                        fRepeatAgain = True
                        continue
                    else:
                        self._state = ModbusServerPort.State.STATE_BEGIN_READ
                        self._raisePortError(e)
                self._state = ModbusServerPort.State.STATE_PROCESS_DEVICE
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_PROCESS_DEVICE:
                toRead = False
                try:
                    r = self._processDevice()
                    if r is None:
                        return None                    
                except ModbusException as e:
                    toRead = (e.code == StatusCode.Status_BadGatewayPathUnavailable)
                    r = e.code
                else:
                    r = StatusCode.Status_Good
                toRead = toRead or self._isBroadcast()
                if toRead:
                    self._state = ModbusServerPort.State.STATE_BEGIN_READ
                    return StatusCode.Status_Good
                self._state = ModbusServerPort.State.STATE_BEGIN_WRITE
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_BEGIN_WRITE:
                self._timestampRefresh()
                func = self._func
                if StatusIsBad(r):
                    self.signalError.emit(self.objectName(), r, self._errorText)
                    func |= MBF_EXCEPTION
                    buff = bytearray(1)
                    if StatusIsStandardError(r):
                        buff[0] = r & 0xFF
                    else:
                        buff[0] = StatusCode.Status_BadServerDeviceFailure & 0xFF
                else:
                    buff = self._processOutputData()
                self._port.writeBuffer(self._unit, func, buff)
                self._state = ModbusServerPort.State.STATE_WRITE
                fRepeatAgain = True
                continue
            elif self._state == ModbusServerPort.State.STATE_WRITE:
                try:
                    r = self._port.write()
                    if r is None:
                        return None
                except ModbusException as e:
                    self.signalError.emit(self.objectName(), e.code, str(e))
                    self._state = ModbusServerPort.State.STATE_TIMEOUT
                    self._raisePortError(e)
                else:
                    self.signalTx.emit(self.objectName(), self._port.writeBufferData())
                    self._state = ModbusServerPort.State.STATE_BEGIN_READ
                return StatusCode.Status_Good
            elif self._state == ModbusServerPort.State.STATE_TIMEOUT:
                if (timer() - self._timestamp < self._port.timeout()):
                    return None
                self._state = ModbusServerPort.State.STATE_UNKNOWN
                fRepeatAgain = True
                continue
            else:
                if self.isOpen():
                    if self._cmdClose:
                       self._state = ModbusServerPort.State.STATE_WAIT_FOR_CLOSE
                    else:
                       self._state = ModbusServerPort.State.STATE_OPENED
                else:
                    self._state = ModbusServerPort.State.STATE_CLOSED
                fRepeatAgain = True
                continue
        return None
    # Protected processing methods

    def _processInputData(self, buff: bytes) -> StatusCode:
        """Process input data buff with size and returns status of the operation.

        Args:
            buff: Input data buffer to process.
        """
        if self._func in (MBF_READ_COILS,
                          MBF_READ_DISCRETE_INPUTS):
            if len(buff) != 4: # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset = buff[1] | (buff[0] << 8)
            self._count  = buff[3] | (buff[2] << 8)
            if (self._count > MB_MAX_DISCRETS): # prevent valueBuff overflow
                return self._raiseError(exceptions.IllegalDataValueError, "Incorrect data value")
        elif self._func in (MBF_READ_HOLDING_REGISTERS,
                            MBF_READ_INPUT_REGISTERS):
            if len(buff) != 4: # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset = buff[1] | (buff[0] << 8)
            self._count  = buff[3] | (buff[2] << 8)
            if (self._count > MB_MAX_REGISTERS): # prevent valueBuff overflow
                return self._raiseError(exceptions.IllegalDataValueError, "Incorrect data value")
        elif self._func == MBF_WRITE_SINGLE_COIL:
            if len(buff) != 4: # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if not (buff[2] == 0x00 or buff[2] == 0xFF) or (buff[3] != 0):  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect data value")
            self._offset = buff[1] | (buff[0]<<8)
            self._value = buff[2]
        elif self._func == MBF_WRITE_SINGLE_REGISTER:
            if len(buff) != 4: # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset = buff[1] | (buff[0]<<8)
            self._value = buff[3] | (buff[2]<<8)
        elif self._func == MBF_READ_EXCEPTION_STATUS:
            if len(buff) > 0:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
        elif self._func == MBF_DIAGNOSTICS:
            if len(buff) < 2:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._subfunc = buff[1] | (buff[0]<<8)
            self._count = len(buff) - 2
            self._valueBuff = buff[2:]
        elif self._func == MBF_GET_COMM_EVENT_COUNTER:
            if len(buff) > 0:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
        elif self._func == MBF_GET_COMM_EVENT_LOG:
            if len(buff) > 0:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
        elif self._func == MBF_WRITE_MULTIPLE_COILS:
            if len(buff) < 5:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if len(buff) != buff[4]+5:  # don't match readed bytes and number of data bytes to follow
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset = buff[1] | (buff[0]<<8)
            self._count  = buff[3] | (buff[2]<<8)
            if (self._count+7)//8 != buff[4]:  # don't match count bites and bytes
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if (self._count > MB_MAX_DISCRETS):  # prevent valueBuff overflow
                return self._raiseError(exceptions.IllegalDataValueError, "Incorrect data value")
            self._valueBuff = buff[5:(5 + (self._count + 7) // 8)]
        elif self._func == MBF_WRITE_MULTIPLE_REGISTERS:
            if len(buff) < 5:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if len(buff) != buff[4]+5:  # don't match readed bytes and number of data bytes to follow
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset = buff[1] | (buff[0]<<8)
            self._count = buff[3] | (buff[2]<<8)
            if (self._count*2 != buff[4]):  # don't match count values and bytes
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if (self._count > MB_MAX_REGISTERS):  # prevent valueBuff overflow
                return self._raiseError(exceptions.IllegalDataValueError, "Incorrect data value")
            self._valueBuff = bytearray(self._count*2)
            for i in range(self._count):
                self._valueBuff[i*2]   = buff[6+i*2]
                self._valueBuff[i*2+1] = buff[5+i*2]
        elif self._func == MBF_REPORT_SERVER_ID:
            if len(buff) > 0:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
        elif self._func == MBF_MASK_WRITE_REGISTER:
            if len(buff) != 6:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset  = buff[1] | (buff[0]<<8)
            self._andMask = buff[3] | (buff[2]<<8)
            self._orMask  = buff[5] | (buff[4]<<8)
        elif self._func == MBF_READ_WRITE_MULTIPLE_REGISTERS:
            if len(buff) < 9:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if len(buff) != buff[8]+9:  # don't match readed bytes and number of data bytes to follow
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset      = buff[1] | (buff[0]<<8)
            self._count       = buff[3] | (buff[2]<<8)
            self._writeOffset = buff[5] | (buff[4]<<8)
            self._writeCount  = buff[7] | (buff[6]<<8)
            if (self._writeCount*2 != buff[8]):  # don't match count values and bytes
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            if ((self._count > MB_MAX_REGISTERS) or (self._writeCount > MB_MAX_REGISTERS)):  # prevent valueBuff overflow
                return self._raiseError(exceptions.IllegalDataValueError, "Incorrect data value")
            self._valueBuff = bytearray(self._count*2)
            for i in range(self._count):
                self._valueBuff[i*2  ] = buff[10+i*2]
                self._valueBuff[i*2+1] = buff[ 9+i*2]
        elif self._func == MBF_READ_FIFO_QUEUE:
            if len(buff) < 2:  # Incorrect request from client - don't respond
                return self._raiseError(exceptions.NotCorrectRequestError, "Incorrect received data size")
            self._offset  = buff[1] | (buff[0]<<8)
        else:
            return self._raiseError(exceptions.IllegalFunctionError, "Unsupported function")


    # Protected processing methods

    def _processDevice(self) -> StatusCode:
        """Transfer input request Modbus function to inner device and returns status of the operation.
        
        Returns:
            StatusCode indicating the result of device processing.
        """
        res = None
        if self._func == MBF_READ_COILS:
            res = self._device.readCoils(self._unit, self._offset, self._count)
        elif self._func == MBF_READ_DISCRETE_INPUTS:
            res = self._device.readDiscreteInputs(self._unit, self._offset, self._count)
        elif self._func == MBF_READ_HOLDING_REGISTERS:
            res = self._device.readHoldingRegisters(self._unit, self._offset, self._count)
        elif self._func == MBF_READ_INPUT_REGISTERS:
            res = self._device.readInputRegisters(self._unit, self._offset, self._count)
        elif self._func == MBF_WRITE_SINGLE_COIL:
            return self._device.writeSingleCoil(self._unit, self._offset, self._value)
        elif self._func == MBF_WRITE_SINGLE_REGISTER:
            return self._device.writeSingleRegister(self._unit, self._offset, self._value)
        elif self._func == MBF_READ_EXCEPTION_STATUS:
            res = self._device.readExceptionStatus(self._unit)
        elif self._func == MBF_DIAGNOSTICS:
            res = self._device.diagnostics(self._unit, self._subfunc, self._byteCount, self._valueBuff, self._outByteCount, self._valueBuff)
        elif self._func == MBF_GET_COMM_EVENT_COUNTER:
            res = self._device.getCommEventCounter(self._unit, self._status, self._count)
        elif self._func == MBF_GET_COMM_EVENT_LOG:
            res = self._device.getCommEventLog(self._unit, self._status, self._count, self._messageCount, self._outByteCount, self._valueBuff)
        elif self._func == MBF_WRITE_MULTIPLE_COILS:
            return self._device.writeMultipleCoils(self._unit, self._offset, self._valueBuff, self._count)
        elif self._func == MBF_WRITE_MULTIPLE_REGISTERS:
            return self._device.writeMultipleRegisters(self._unit, self._offset, self._valueBuff)
        elif self._func == MBF_REPORT_SERVER_ID:
            res = self._device.reportServerID(self._unit)
        elif self._func == MBF_MASK_WRITE_REGISTER:
            return self._device.maskWriteRegister(self._unit, self._offset, self._andMask, self._orMask)
        elif self._func == MBF_READ_WRITE_MULTIPLE_REGISTERS:
            res = self._device.readWriteMultipleRegisters(self._unit,
                                                          self._offset, self._count,
                                                          self._writeOffset, self._valueBuff)
        elif self._func == MBF_READ_FIFO_QUEUE:
            res = self._device.readFIFOQueue(self._unit, self._offset)
        else:
            self._raiseError(exceptions.IllegalFunctionError, "Unsupported function")
        if res is None:
            return None
        self._valueBuff = res
        return StatusCode.Status_Good

    def _processOutputData(self) -> bytearray:
        """Process output data buff with size and returns status of the operation.
        
        Returns:
            The output data buffer to send.
        """
        if self._func in (MBF_READ_COILS,
                          MBF_READ_DISCRETE_INPUTS):
            buff = bytearray(1)
            buff[0] = (self._count+7) // 8
            buff[1:] = self._valueBuff[0:buff[0]]
        elif self._func in (MBF_READ_HOLDING_REGISTERS,
                            MBF_READ_INPUT_REGISTERS,
                            MBF_READ_WRITE_MULTIPLE_REGISTERS):
            buff = bytearray(self._count * 2 + 1)
            buff[0] = (self._count * 2) & 0xFF
            for i in range(self._count):
                buff[2 + i * 2] = self._valueBuff[i * 2    ]
                buff[1 + i * 2] = self._valueBuff[i * 2 + 1]
        elif self._func == MBF_WRITE_SINGLE_COIL:
            buff = bytearray(4)
            buff[0] = (self._offset >> 8) & 0xFF     # address of coil (Hi-byte)
            buff[1] = (self._offset & 0xFF)          # address of coil (Lo-byte)
            buff[2] = 0xFF if self._value else 0x00  # value (Hi-byte)
            buff[3] = 0                              # value (Lo-byte)
        elif self._func == MBF_WRITE_SINGLE_REGISTER:
            buff = bytearray(4)
            buff[0] = (self._offset >> 8) & 0xFF # address of register (Hi-byte)
            buff[1] = (self._offset & 0xFF)      # address of register (Lo-byte)
            buff[2] = (self._value >> 8) & 0xFF  # value (Hi-byte)
            buff[3] = self._value & 0xFF         # value (Lo-byte)
        elif self._func == MBF_READ_EXCEPTION_STATUS:
            buff = bytearray(1)
            buff[0] = self._valueBuff[0]
        elif self._func == MBF_DIAGNOSTICS:
            buff = bytearray(2)
            buff[0] = (self._subfunc >> 8) & 0xFF # address of register (Hi-byte)
            buff[1] = (self._subfunc & 0xFF)      # address of register (Lo-byte)
            buff[2:] = self._valueBuff[0:]
        elif self._func == MBF_GET_COMM_EVENT_COUNTER:
            buff = bytearray(4)
            buff[0] = (self._status >> 8) & 0xFF # status of counter (Hi-byte)
            buff[1] = (self._status & 0xFF)      # status of counter (Lo-byte)
            buff[2] = (self._count >> 8) & 0xFF  # event counter value (Hi-byte)
            buff[3] = (self._count & 0xFF)       # event counter value (Lo-byte)
        elif self._func == MBF_GET_COMM_EVENT_LOG:
            buff = bytearray(7)
            buff[0] = (len(self._valueBuff) + 6) & 0xFF  # output bytes count
            buff[1] = (self._status >> 8) & 0xFF         # status of counter (Hi-byte)
            buff[2] = (self._status & 0xFF)              # status of counter (Lo-byte)
            buff[3] = (self._count >> 8) & 0xFF          # event counter value (Hi-byte)
            buff[4] = (self._count & 0xFF)               # event counter value (Lo-byte)
            buff[5] = (self._messageCount >> 8) & 0xFF   # message counter value (Hi-byte)
            buff[6] = (self._messageCount & 0xFF)        # message counter value (Lo-byte)
            buff[7:] = self._valueBuff[0:]
        elif self._func in (MBF_WRITE_MULTIPLE_COILS,
                            MBF_WRITE_MULTIPLE_REGISTERS):
            buff = bytearray(4)
            buff[0] = (self._offset >> 8) & 0xFF   # offset of written values (Hi-byte)
            buff[1] = (self._offset & 0xFF) & 0xFF # offset of written values (Lo-byte)
            buff[2] = (self._count >> 8) & 0xFF    # count of written values (Hi-byte)
            buff[3] = (self._count & 0xFF) & 0xFF  # count of written values (Lo-byte)
        elif self._func == MBF_REPORT_SERVER_ID:
            buff[0] = self._outByteCount            # output bytes count
            buff[1:] = self._valueBuff[0:self._outByteCount]
        elif self._func == MBF_MASK_WRITE_REGISTER:
            buff = bytearray(6)
            buff[0] = (self._offset >> 8) & 0xFF      # address of register (Hi-byte)
            buff[1] = (self._offset & 0xFF) & 0xFF    # address of register (Lo-byte)
            buff[2] = (self._andMask >> 8) & 0xFF     # And mask (Hi-byte)
            buff[3] = (self._andMask & 0xFF) & 0xFF   # And mask (Lo-byte)
            buff[4] = (self._orMask >> 8) & 0xFF      # Or mask (Hi-byte)
            buff[5] = (self._orMask & 0xFF) & 0xFF    # Or mask (Lo-byte)
        elif self._func == MBF_READ_FIFO_QUEUE:
            byteCount = (self._count * 2) + 2
            buff = bytearray(byteCount + 2)
            buff[0] = (byteCount >> 8) & 0xFF      # status of counter (Hi-byte)
            buff[1] = (byteCount & 0xFF) & 0xFF    # status of counter (Lo-byte)
            buff[2] = (self._count >> 8) & 0xFF    # event counter value (Hi-byte)
            buff[3] = (self._count & 0xFF) & 0xFF  # event counter value (Lo-byte)
            for i in range(self._count):
                buff[4+i*2] = self._valueBuff[i*2+1]
                buff[5+i*2] = self._valueBuff[i*2  ]
        else:
            buff = bytearray(0)
        return buff


    def _isBroadcast(self):
        """Returns True if the current request is a broadcast request, False otherwise.
        
        Returns:
            True if the current request is a broadcast, False otherwise.
        """
        return self._unit == 0 and self.isBroadcastEnabled()
    
    def _setError(self, e, text: Optional[str] = None):
        self._isErrorPort = False
        super()._setError(e, text)

    def _raiseError(self, e, text: Optional[str] = None):
        self._isErrorPort = False
        super()._raiseError(e, text)

    def _setPortError(self, e, text: Optional[str] = None):
        self._isErrorPort = True
        super()._setError(e, text)

    def _raisePortError(self, e, text: Optional[str] = None):
        self._isErrorPort = True
        super()._raiseError(e, text)


class ModbusAsyncServerResource(ModbusServerResource):
    """Asynchronous version of ModbusServerResource.
    
    All methods that can be blocking in ModbusServerResource are
    overridden here to return `AwaitableMethod` objects.
    """
    def __init__(self, port: ModbusPort, device: ModbusInterface):
        if port.isBlocking():
            port.setBlocking(False)
        super().__init__(port, device)

    def process(self):
        return AwaitableMethod(super().process)