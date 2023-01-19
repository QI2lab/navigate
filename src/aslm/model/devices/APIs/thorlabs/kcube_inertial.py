"""
API for connection to Thorlabs.MotionControl.KCube.InertialMotor.dll.
See Thorlabs.MotionControl.KCube.InertialMotor.h for more functions to implement.

Tested on Thorlabs KIM001.
"""


import ctypes
import ctypes.wintypes
from enum import IntEnum

CODING = "ascii"

__dll = ctypes.WinDLL(
    "C:\Program Files\Thorlabs\Kinesis\Thorlabs.MotionControl.KCube.InertialMotor.dll"
)


class TLFTDICommunicationError(Exception):
    """Exception for Thorlabs FTDI communications module or supporting code."""


class TLDLLError(Exception):
    """Exception for general Thorlabs DLL control errors."""


class TLMotorDLLError(Exception):
    """Exception for motor-specific Thorlabs DLL errors."""


class FT_Status(IntEnum):
    """The following errors are generated from the FTDI communications module,
    supporting code or device libraries."""

    FT_OK = 0  # No error
    FT_InvalidHandle = 1  # The FTDI functions have not been initialized.
    FT_DeviceNotFound = 2  # The Device could not be found. This can be generated if the
    # function TLI_BuildDeviceList() has not been called.
    FT_DeviceNotOpened = 3  # The Device must be opened before it can be accessed
    FT_IOError = 4  # An I/O Error has occured in the FTDI chip.
    FT_InsufficientResources = (
        5  # There are Insufficient resources to run this application.
    )
    FT_InvalidParameter = 6  # An invalid parameter has been supplied to the device.
    FT_DeviceNotPresent = 7  # The Device is no longer present. The device may have been
    # disconnected since the last TLI_BuildDeviceList() call.
    FT_IncorrectDevice = 8  # The device detected does not match that expected
    FT_NoDLLLoaded = 16  # The library for this device could not be found
    FT_NoFunctionsAvailable = 17  # No functions available for this device
    FT_FunctionNotAvailable = 18  # The function is not available for this device.
    FT_BadFunctionPointer = 19  # Bad function pointer detected
    FT_GenericFunctionFail = 20  # The function failed to complete successfully.
    FT_SpecificFunctionFail = 21  # The function failed to complete successfully.


FT_Status_Description = {
    FT_Status.FT_OK: "No error",
    FT_Status.FT_InvalidHandle: "The FTDI functions have not been initialized.",
    FT_Status.FT_DeviceNotFound: "The Device could not be found. This can be generated "
    "if the function TLI_BuildDeviceList() has not been called.",
    FT_Status.FT_DeviceNotOpened: "The Device must be opened before it can "
    "be accessed.",
    FT_Status.FT_IOError: "An I/O Error has occured in the FTDI chip.",
    FT_Status.FT_InsufficientResources: "There are Insufficient resources to run "
    "this application.",
    FT_Status.FT_InvalidParameter: "An invalid parameter has been supplied to "
    "the device.",
    FT_Status.FT_DeviceNotPresent: "The Device is no longer present. The device may "
    "have been disconnected "
    "since the last TLI_BuildDeviceList() call.",
    FT_Status.FT_IncorrectDevice: "The device detected does not match that expected.",
    FT_Status.FT_NoDLLLoaded: "The library for this device could not be found.",
    FT_Status.FT_FunctionNotAvailable: "The function is not available for this device.",
    FT_Status.FT_NoFunctionsAvailable: "No functions available for this device.",
    FT_Status.FT_BadFunctionPointer: "Bad function pointer detected.",
    FT_Status.FT_GenericFunctionFail: "The function failed to complete successfully.",
    FT_Status.FT_SpecificFunctionFail: "The function failed to complete successfully.",
}


class TL_DLL_Error(IntEnum):
    """The following errors are general errors generated by all DLLs."""

    TL_ALREADY_OPEN = 32  # Attempt to open a device that was already open.
    TL_NO_RESPONSE = 33  # The device has stopped responding.
    TL_NOT_IMPLEMENTED = 34  # This function has not been implemented.
    TL_FAULT_REPORTED = 35  # The device has reported a fault.
    TL_INVALID_OPERATION = 36  # The function could not be completed at this time.
    TL_DISCONNECTING = (
        40  # The function could not be completed because the device is disconnected.
    )
    TL_FIRMWARE_BUG = 41  # The firmware has thrown an error.
    TL_INITIALIZATION_FAILURE = 42  # The device has failed to initialize
    TL_INVALID_CHANNEL = 43  # An Invalid channel address was supplied


TL_DLL_Error_Description = {
    TL_DLL_Error.TL_ALREADY_OPEN: "Attempt to open a device that was already open.",
    TL_DLL_Error.TL_NO_RESPONSE: "The device has stopped responding.",
    TL_DLL_Error.TL_NOT_IMPLEMENTED: "This function has not been implemented.",
    TL_DLL_Error.TL_FAULT_REPORTED: "The device has reported a fault.",
    TL_DLL_Error.TL_INVALID_OPERATION: "The function could not be completed at "
    "this time.",
    TL_DLL_Error.TL_DISCONNECTING: "The function could not be completed because the "
    "device is disconnected.",
    TL_DLL_Error.TL_FIRMWARE_BUG: "The firmware has thrown an error.",
    TL_DLL_Error.TL_INITIALIZATION_FAILURE: "The device has failed to initialize.",
    TL_DLL_Error.TL_INVALID_CHANNEL: "An Invalid channel address was supplied.",
}


class Motor_DLL_Error(IntEnum):
    """The following errors are motor specific errors generated by the Motor DLLs."""

    TL_UNHOMED = 37  # The device cannot perform this function until it has been Homed.
    TL_INVALID_POSITION = 38  # The function cannot be performed as it would result in
    # an illegal position.
    TL_INVALID_VELOCITY_PARAMETER = 39  # An invalid velocity parameter was supplied.
    # The velocity must be greater than zero.
    TL_CANNOT_HOME_DEVICE = 44  # This device does not support Homing. Check the Limit
    # switch parameters are correct.
    TL_JOG_CONTINOUS_MODE = 45  # An invalid jog mode was supplied for the jog function.
    TL_NO_MOTOR_INFO = (
        46  # There is no Motor Parameters available to convert Real World Units.
    )
    TL_CMD_TEMP_UNAVAILABLE = 47  # Command temporarily unavailable, Device may be busy.


Motor_DLL_Error_Description = {
    Motor_DLL_Error.TL_UNHOMED: "The device cannot perform this function until it has "
    "been Homed.",
    Motor_DLL_Error.TL_INVALID_POSITION: "The function cannot be performed as it would "
    "result in an illegal position.",
    Motor_DLL_Error.TL_INVALID_VELOCITY_PARAMETER: "An invalid velocity parameter was "
    "supplied. The velocity must be greater than zero.",
    Motor_DLL_Error.TL_CANNOT_HOME_DEVICE: "This device does not support Homing. Check "
    "the Limit switch parameters are correct.",
    Motor_DLL_Error.TL_JOG_CONTINOUS_MODE: "An invalid jog mode was supplied for the "
    "jog function.",
    Motor_DLL_Error.TL_NO_MOTOR_INFO: "There is no Motor Parameters available to "
    " convert Real World Units.",
    Motor_DLL_Error.TL_CMD_TEMP_UNAVAILABLE: "Command temporarily unavailable, Device "
    "may be busy.",
}


def in_enum(value, enum):
    values = set(item.value for item in enum)
    return value in values


def errcheck(result, func, args):
    """
    Wraps the call to DLL functions.

    Parameters
    ----------
    result : ctypes.c_short
        Error code or 0 if successful.
    func : function
        DLL function
    args : tuple
        Arguments passed to the DLL function, defined in argtypes

    Returns
    -------
    result : int
        Error code or 0 if successful.
    """
    if result:
        # returned a non-zero value
        if in_enum(result, FT_Status):
            raise TLFTDICommunicationError(FT_Status_Description[result])
        elif in_enum(result, TL_DLL_Error):
            raise TLDLLError(TL_DLL_Error_Description[result])
        elif in_enum(result, Motor_DLL_Error):
            raise TLMotorDLLError(Motor_DLL_Error_Description[result])
        else:
            raise Exception(f"Unknown error {result} in Thorlabs device.")
    return int(result)


__dll.TLI_BuildDeviceList.restype = ctypes.c_short
__dll.TLI_BuildDeviceList.errcheck = errcheck


def TLI_BuildDeviceList():
    """This function builds an internal collection of all devices found on the USB that
    are not currently open.

    Returns
    -------
    int
        The error code or 0 if successful.
    """
    return __dll.TLI_BuildDeviceList()


__dll.TLI_GetDeviceListSize.restype = ctypes.c_short


def TLI_GetDeviceListSize():
    """
    Gets the device list size.

    Returns
    -------
    int
        Number of devices in device list.
    """
    return __dll.TLI_GetDeviceListSize()


__dll.TLI_GetDeviceListExt.argtypes = [ctypes.c_char_p, ctypes.wintypes.DWORD]
__dll.TLI_GetDeviceListExt.restype = ctypes.c_short
__dll.TLI_GetDeviceListExt.errcheck = errcheck


def TLI_GetDeviceListExt():
    """Get the entire contents of the device list.

    Returns
    -------
    List
        List of device serial numbers as strings.
    """

    c_buf_len = 256
    c_buf = ctypes.create_string_buffer(c_buf_len)
    __dll.TLI_GetDeviceListExt(c_buf, c_buf_len)

    return str(c_buf.value.decode(CODING)).split(",")[:-1]


__dll.TLI_GetDeviceListByTypeExt.argtypes = [
    ctypes.c_char_p,
    ctypes.wintypes.DWORD,
    ctypes.c_int,
]
__dll.TLI_GetDeviceListByTypeExt.restype = ctypes.c_short
__dll.TLI_GetDeviceListByTypeExt.errcheck = errcheck


def TLI_GetDeviceListByTypeExt(type_id):
    """Get the contents of the device list which match the supplied type_id.

    Parameters
    ----------
    type_id : int
        Device type.

    Returns
    -------
    List
        List of device serial numbers as strings.
    """

    c_buf_len = 256
    c_buf = ctypes.create_string_buffer(c_buf_len)
    __dll.TLI_GetDeviceListByTypeExt(c_buf, c_buf_len, type_id)

    return str(c_buf.value.decode(CODING)).split(",")[:-1]


class MOT_MotorTypes(IntEnum):
    """Values that represent THORLABSDEVICE_API."""

    MOT_NotMotor = 0
    MOT_DCMotor = 1
    MOT_StepperMotor = 2
    MOT_BrushlessMotor = 3
    MOT_CustomMotor = 100


class TLI_DeviceInfo(ctypes.Structure):
    """Information about the device generated from serial number."""

    _pack_ = 1
    _fields_ = [
        ("typeID", ctypes.wintypes.DWORD),  # The device Type ID
        ("description", ctypes.c_char * 65),  # The device description.
        ("serialNo", ctypes.c_char * 16),  # The device serial number.
        ("PID", ctypes.wintypes.DWORD),  # The USB PID number.
        (
            "isKnownType",
            ctypes.wintypes.BOOL,
        ),  # True if this object is a type known to the Motion Control software.
        ("motorType", ctypes.c_int),  # The motor type (if a motor)
        (
            "isPiezoDevice",
            ctypes.wintypes.BOOL,
        ),  # True if the device is a piezo device.
        ("isLaser", ctypes.wintypes.BOOL),  # True if the device is a laser.
        ("isCustomType", ctypes.wintypes.BOOL),  # True if the device is a custom type.
        ("isRack", ctypes.wintypes.BOOL),  # True if the device is a rack.
        (
            "maxChannels",
            ctypes.c_short,
        ),  # Defines the number of channels available in this device.
    ]


__dll.TLI_GetDeviceInfo.argtypes = [ctypes.c_char_p, ctypes.POINTER(TLI_DeviceInfo)]
__dll.TLI_GetDeviceInfo.restype = ctypes.c_short


def TLI_GetDeviceInfo(serial_no):
    """Get the device information from the USB port.

    The Device Info is read from the USB port not from the device itself.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.

    Returns
    -------
    TLI_DeviceInfo
        The device information.
    """

    info = TLI_DeviceInfo()

    __dll.TLI_GetDeviceInfo(
        serial_no.encode(CODING), ctypes.byref(info)
    )  # 1 if successful, 0 if not

    return info


__dll.KIM_Open.argtypes = [ctypes.c_char_p]
__dll.KIM_Open.restype = ctypes.c_short
__dll.KIM_Open.errcheck = errcheck


def KIM_Open(serial_no):
    """Open the device for communications.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.

    Returns
    -------
    int
        The error code or 0 if successful.
    """

    return __dll.KIM_Open(serial_no.encode(CODING))


__dll.KIM_Close.argtypes = [ctypes.c_char_p]


def KIM_Close(serial_no):
    """Disconnect and close the device.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.

    Returns
    -------
    None
    """

    __dll.KIM_Close(serial_no.encode(CODING))


__dll.KIM_StartPolling.argtypes = [ctypes.c_char_p, ctypes.c_int]
__dll.KIM_StartPolling.restype = ctypes.wintypes.BOOL


def KIM_StartPolling(serial_no, milliseconds):
    """Starts the internal polling loop which continuously requests position and status.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    milliseconds : int
        The milliseconds polling rate.

    Returns
    -------
    bool
        True if successful, False otherwise
    """
    return bool(__dll.KIM_StartPolling(serial_no.encode(CODING), milliseconds))


__dll.KIM_StopPolling.argtypes = [ctypes.c_char_p]


def KIM_StopPolling(serial_no):
    """Stops the internal polling loop.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.

    Returns
    -------
    None
    """
    __dll.KIM_StopPolling(serial_no.encode(CODING))


class KIM_Channels(IntEnum):  # unsigned short
    Channel1 = 1
    Channel2 = 2
    Channel3 = 3
    Channel4 = 4


__dll.KIM_RequestCurrentPosition.argtypes = [ctypes.c_char_p, ctypes.c_ushort]
__dll.KIM_RequestCurrentPosition.restype = ctypes.c_int
__dll.KIM_RequestCurrentPosition.errcheck = errcheck


def KIM_RequestCurrentPosition(serial_no, channel):
    """Gets current position.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    channel : int
        The device channel. One of KIM_Channels.

    Returns
    -------
    int
        The error code or 0 if successful.
    """

    return __dll.KIM_RequestCurrentPosition(serial_no.encode(CODING), channel)


__dll.KIM_GetCurrentPosition.argtypes = [ctypes.c_char_p, ctypes.c_ushort]
__dll.KIM_GetCurrentPosition.restype = ctypes.c_int


def KIM_GetCurrentPosition(serial_no, channel):
    """Gets current position.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    channel : int
        The device channel. One of KIM_Channels.

    Returns
    -------
    int
        Current position.
    """

    return __dll.KIM_GetCurrentPosition(serial_no.encode(CODING), channel)


__dll.KIM_MoveAbsolute.argtypes = [ctypes.c_char_p, ctypes.c_ushort, ctypes.c_int]
__dll.KIM_MoveAbsolute.restype = ctypes.c_short
__dll.KIM_MoveAbsolute.errcheck = errcheck


def KIM_MoveAbsolute(serial_no, channel, position):
    """Move absolute.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    channel : int
        The device channel. One of KIM_Channels.
    position : int
        The position to move to.

    Returns
    -------
    int
        The error code or 0 if successful.
    """

    return __dll.KIM_MoveAbsolute(serial_no.encode(CODING), channel, position)


__dll.KIM_SetPosition.argtypes = [ctypes.c_char_p, ctypes.c_ushort, ctypes.c_long]
__dll.KIM_SetPosition.restype = ctypes.c_short
__dll.KIM_SetPosition.errcheck = errcheck


def KIM_SetPosition(serial_no, channel, position):
    """Set the current position to position.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    channel : int
        The device channel. One of KIM_Channels.
    position : int
        The value the current position is mapped to.

    Returns
    -------
    int
        The error code or 0 if successful.
    """

    return __dll.KIM_SetPosition(serial_no.encode(CODING), channel, position)


class KIM_TravelDirection(IntEnum):  # byte
    Forward = 1  # An enum constant representing the forward option.
    Reverse = 2  # An enum constant representing the reverse option.


__dll.KIM_MoveJog.argtypes = [ctypes.c_char_p, ctypes.c_ushort, ctypes.c_byte]
__dll.KIM_MoveJog.restype = ctypes.c_short
__dll.KIM_MoveJog.errcheck = errcheck


def KIM_MoveJog(serial_no, channel, jog_direction):
    """Move jog.

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    channel : int
        The device channel. One of KIM_Channels.
    jog_direction : int
        The jog direction. One of KIM_TravelDirection.

    Returns
    -------
    int
        The error code or 0 if successful.
    """

    return __dll.KIM_MoveJog(serial_no.encode(CODING), channel, jog_direction)


__dll.KIM_MoveStop.argtypes = [ctypes.c_char_p, ctypes.c_ushort]
__dll.KIM_MoveStop.restype = ctypes.c_short
__dll.KIM_MoveAbsolute.errcheck = errcheck


def KIM_MoveStop(serial_no, channel):
    """Halt motion

    Parmeters
    ---------
    serial_number : str
        Serial number of Thorlabs Kinesis Inertial Motor (KIM) device.
    channel : int
        The device channel. One of KIM_Channels.

    Returns
    -------
    int
        The error code or 0 if successful.
    """

    return __dll.KIM_MoveStop(serial_no.encode(CODING), channel)
