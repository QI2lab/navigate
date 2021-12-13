'''
Luxx Laser Class
LUXX488, 200 mW, is COM19
LUXX642, 140 mW, is COM17
LIGHTHUB ULTRA, is COM20
'''

import serial
import sys
import re
from time import time, sleep

class LuxxLaser():
    def __init__(self, port='COM19', baudrate=500000):
        self.verbose = False

        """
        Open port (*auto* stands for **/dev/ttyUSB0** in Linux or **COM17**
        in Windows, because it is what I use); then get device model;
        finally, get maximum output power and store it in **pmax** variable.
        """
        try:
            # Open serial port
            self.port = serial.Serial(port, baudrate, timeout=0.3)

            # Confirm that we are operating with the appropriate firmware
            self.firmware = self.ask("GFw")
            model_vector = ['LuxX', 'BrixX', 'PhoxX', 'LHU']
            device_present = [re.findall(str(x).encode(), self.firmware)
                              for x in model_vector]
            if any(device_present[3]):
                print("This is the LightHub Ultra")
            if not any(device_present[0:2]):
                print("This is not a Luxx, BrixX, PhoxX Laser")
                sys.exit(1)
            print("The laser is connected via %s" % port)

            # Confirm the Laser Wavelength
            # Must remove non-standard ASCII codes that cause errors in the utf-8 codec
            wavelength = self.ask("GSI")
            wavelength = wavelength.replace(b"\xa7200", str(" ").encode())
            wavelength = wavelength.replace(b"\xa7140", str(" ").encode())
            wavelength = float(wavelength.decode())
            self.wavelength = wavelength
            if self.verbose:
                print("The Wavelength is:", wavelength)

            # Confirm the Laser Serial Number
            serial_number = self.ask("GSN")
            serial_number = serial_number.decode()
            self.serial = serial_number
            if self.verbose:
                print("Serial Number is: ", serial_number)

            # Confirm the Laser Working Hours
            laser_working_hours = self.ask("GWH")
            laser_working_hours = laser_working_hours.decode()
            self.hours = laser_working_hours
            if self.verbose:
                print("Laser working hours: ", laser_working_hours)

            # Confirm the Laser Maximum Power
            power_max = float(self.ask("GMP"))
            self.pmax = power_max
            if self.verbose:
                print("Laser maximum power: ", power_max)

        except serial.SerialException:
            raise OSError('Port "%s" is unavailable.\n' % port + \
                          'Maybe the laser is not connected, the wrong' + \
                          ' port is specified or the port is already opened')

    def __del__(self):
        """Close the port before exit."""
        try:
            self.port.close()
            print("Port closed")
        except serial.SerialException:
            print('Could not close the port')

    def close(self):
        """Close the port before exit."""
        try:
            self.port.close()
            if self.verbose:
                print("Port Closed")
        except serial.SerialException:
            print('could not close the port')

    def write(self, command):
        """Send *command* to device. Preceed it with "?" und end with CR."""
        command = str("?").encode() + str(command).encode() + str("\r").encode()
        self.port.write(command)

    def read(self):
        """Read all information from the port and return it as string."""
        answer = self.port.readall()
        if self.verbose:
            print("The 'read' answer = ", answer)
        answer = answer.replace(str("\r").encode(), str("\n").encode())
        answer = answer.replace(str("\xa7").encode(), str(" | ").encode())
        if self.verbose:
            print("The cleaned up read answer is:", answer)
        return answer

    def ask(self, command):
        """Write, then read. However, return only the relevant info."""
        self.write(command)
        response = self.read()
        # Use regular expressions to clean up response
        # An unknown command or an incomplete command is followed by a “!UK” answer
        search_string = str("!UK\n").encode()
        if re.findall(search_string, response):
            print("Command '%s' is unknown for this device" % command)
        else:
            search_string = "!%s(.+)\n" % command[:3]
            search_string = search_string.encode()
            if self.verbose:
                print("The search string is:", search_string)
                print("The response string is:", response)

            response = re.findall(search_string, response)[-1]
            if response[0] == "x":
                print("Laser responded with error to command '%s'" % command)
            return response

    def smart_ask(self, command):
        """
        #TODO: Not working.  Depends on broken print_hex function.
        Several commands return information coded in ASCII HEX numbers.
        The relevant are bits in the registers. For convenient
        representation, we will print(these bytes in tables.
        This is relevant for the following commands:
            * GOM
            * GFB
            * GLF
            * GLP
        For all other commands the behavior is identical to **ask** function
        """
        if command in ["GOM", "GFB", "GLF", "GLP"]:
            #command = str(command).encode()
            return print_hex(self.ask(command))
        else:
            return self.ask(command)

    def start(self):
        """Start the emission (takes about 3 seconds)"""
        self.write("LOn")

    def stop(self):
        """Stop the emission immediately"""
        self.write("LOf")

    def set_power(self, power):
        """
        Set the desired power in mW
        TODO: Intermittent failure due to list index out of range in self.ask (line 115)
        """
        # Calculate the corresponding HEX code and transmit it
        if power > self.pmax:
            print("Laser provides %imW only. The maximum power is set", self.pmax)
            self.write("SLPFFF")
        else:
            code = hex(int(4095*power/self.pmax))[2:].upper().zfill(3)
            stopwatch(self.ask, "SLP%s" % code)

    def get_power(self):
        """Get the current power value in mW"""
        code = stopwatch(self.ask, "GLP")
        return int(code, 16)*self.pmax/4095.

    def set_mode(self, mode):
        """
        The device is able to work in the following modes:
          * Standby
              Laser is ready, but no emission is produced. However, if we
              it is turned on (e.g. with **start** function), then change to
              other mode will result in immediate emission, i.e. without
              3 seconds delay.
          * CW-ACC
              constant wave, automatic current control
          * CW-APC
              constant wave, automatic power control
          * Analog
              the output power is dependent on the analog input; however,
              it cannot exceed the specified with **set_power** value.
        """
        if mode == "Standby" or mode == 0:
            mode = 0
        elif mode == "CW-ACC" or mode == 1:
            mode = 1
        elif mode == "CW-APC" or mode == 2:
            mode = 2
        elif mode == "Analog" or mode == 3:
            mode = 3
        else:
            print("**mode** must be one of 'Standby', 'CW-ACC', " + \
                        "'CW-APC', 'Analog' or number 0-3. Nothing changed.")
            return
        stopwatch(self.ask, "ROM%i" % mode)

    def get_mode(self):
        """
        Get the current mode.
        """
        mode = int(stopwatch(self.ask, "ROM"))
        if mode == 0:
            return "Standby"
        elif mode == 1:
            return "CW-ACC"
        elif mode == 2:
            return "CW-APC"
        elif mode == 3:
            return "Analog"
        else:
            return mode

    def set_autostart(self, state):
        """Decide if light is emitted on powerup."""
        if state:
            self.ask("SAS1")
        else:
            self.ask("SAS0")

    def get_autostart(self):
        """Check if light is emitted on powerup."""
        if self.ask("GAS") == "1":
            return True
        else:
            return False

    def get_parameters(self):
        """print a table showing laser status."""
        self.smart_ask("GOM")
        """Bit description:
        15  Auto PowerUP if ONE
        14  Autostart (emission at powerup) if ONE
        13  Adhoc USB - Laser sends info messages from time to time if ONE
        8   Power control (APC) mode if ONE; current control (ACC) if ZERO
        7   External analog input enabled if ONE
        4   Mod level: ONE - active; ZERO - not active
        3   Bias level: ONE - active; ZERO - not active

        Bits 0, 1, 2, 5, 6, 9, 10, 11, 12 are reserved
        """

    def get_errors(self):
        """print contents of failure byte"""
        self.smart_ask("GFB")
        """Bit description:
        15  Diode power exceeded maximum value
        14  An internal error occured
        12  The temperature at the diode exceeded the valid temperature range
        11  The ambient temperature exceeded the minimum or maximum value
        10  The current through the diode exceeded the maximum allowed value
        9   The interlock loop is not closed. Please close the interlockt loop
        8   Overvoltage or Undervoltage lockout occured. Bring supply voltage to a valid range
        4   If CDRH-Bit is set and no CDRH-Kit is connected or
            CDRH-Bit is not set but a CDRH-Kit is connected
            CDRH-Kit is a box with a key, a LED and an interlock
        0   Soft interlock: If an interlock error occurs, this bit is set. It can only be
            reset by resetting the whole system, even if the interlock error is
            not present anymore.

        Bits 1, 2, 3, 5, 6, 7, 13 are reserved
        """

    def initialize_laser(self):
        self.set_autostart(True)
        self.set_power(laser1.pmax)
        self.set_mode("Analog")
        self.start()
        print((self.wavelength, "nm Laser Initialized - Max Power: ", self.pmax, "mW"))


def stopwatch(func, *func_args, **func_kwargs):
    """Call **func** and print elapsed time"""
    start_time = time()
    result = func(*func_args, **func_kwargs)
    print("Time elapsed: %5.2f ms" % ((time() - start_time)*1000.0))
    return result

def print_hex(hex_code):
    """
    TODO: Not working.  Concatenation of list and range?
    print a nice table that represents *hex_code* (ASCII HEX string)
    in a binary code.

    Returns
    -------
    corresponding decimal numbers in array
    """
    # If the number is odd, pad it with leading zero
    length = len(hex_code)
    byte_number = (length/2) + (length % 2)
    if length % 2:
        hex_code = "0" + hex_code

    # Split it into 8-bit numbers coded in ASCII HEX
    hex_numbers = []
    for i in range(int(byte_number)):
        hex_numbers.append(hex_code[i*2 : i*2+2])

    # Convert each of them into decimal
    decimals = []
    for hex_number in hex_numbers:
        decimals.append(int(hex_number, 16))

    # print a table
    table = """BYTE ##  :  '?'
    | ## | ## | ## | ## | ## | ## | ## | ## |
    |----|----|----|----|----|----|----|----|
    |  ? |  ? |  ? |  ? |  ? |  ? |  ? |  ? |
    """
    table = table.replace("##", "%2i").replace("?", "%s")

    print("\nRepresentation of ASCII HEX '%s'" % hex_code)
    for i, number in enumerate(decimals):
        byte = len(decimals) - i - 1

        # data_range is type Range
        data_range = range(byte*8, byte*8+8)[::-1]

        # data_list is type list
        data_list = list(bin(number)[2:].zfill(8))
        print("data list:", data_list)

        content = data_range + data_list
        print(table % tuple([byte, hex_numbers[i]] + content))
    return decimals

if (__name__ == "__main__"):
    # Luxx Laser Testing.
    test_case = 2

    if test_case == 1:
        laser1 = LuxxLaser(port="COM17")
        print("LuxxLaser Class Initiated")

        laser1.set_autostart(True)
        print("Autostart:", laser1.get_autostart())

        print("Maximum laser power:", laser1.pmax)

        laser1.set_power(laser1.pmax)
        print("laser power set to:", laser1.pmax)
        print("Laser power at ", laser1.get_power())

        laser1.set_mode("CW-APC")
        print("laser mode set to CW-APC")
        print("laser mode at ", laser1.get_mode())

        laser1.start()
        print("laser started")

        sleep(10)

        laser1.stop()
        print("laser stopped")

        laser1.close()
        print('Done')
    elif test_case == 2:
        laser1 = LuxxLaser(port="COM17")
        laser1.initialize_laser()
        laser2 = LuxxLaser(port="COM19")
        laser2.initialize_laser()
        sleep(10)
        laser1.close()
        laser2.close()
        print("Done")










