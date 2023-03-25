# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only
# (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from aslm.controller.sub_controllers.gui_controller import GUIController
from aslm.tools.file_functions import save_yaml_file
from aslm.tools.common_functions import combine_funcs

import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class WaveformPopupController(GUIController):
    """Controller for the waveform popup window.

    This controller is responsible for the waveform popup window. It is responsible for
    updating the waveform constants in the configuration file and saving the waveform
    constants to a file.

    Attributes
    ----------
    view : object
        GUI element containing widgets and variables to control.
        Likely tk.Toplevel-derived.
    parent_controller : ASLM_controller
        The main controller.
    waveform_constants_path : str
        Location of file where remote_focus_dict is read from/saved to.

    Methods
    -------
    update_popup_lasers()
        Checks if number of lasers in remote_focus_constants matches config file.
    show_magnification(event)
        Updates the magnification options based on the mode selected.
    show_laser_info(event)
        Updates the laser information based on the magnification selected.
    update_remote_focus_settings(variable_name, laser, setting)
        Updates the remote focus settings in the configuration file.
    update_galvo_setting(galvo, setting, setting_name)
        Updates the galvo settings in the configuration file.
    update_waveform_constants()
        Updates the waveform constants in the configuration file.
    save_waveform_constants()
        Saves the waveform constants to a file.
    """

    def __init__(self, view, parent_controller, waveform_constants_path):
        super().__init__(view, parent_controller)

        # Microscope information
        self.resolution_info = self.parent_controller.configuration[
            "waveform_constants"
        ]
        self.galvo_setting = self.resolution_info["galvo_constants"]
        self.configuration_controller = self.parent_controller.configuration_controller
        self.waveform_constants_path = waveform_constants_path

        # Get mode and mag widgets
        self.widgets = self.view.get_widgets()
        self.variables = self.view.get_variables()

        # Get configuration
        self.lasers = self.configuration_controller.lasers_info

        # Initialize variables
        self.resolution = None
        self.mag = None
        self.mode = "stop"
        self.remote_focus_experiment_dict = None
        self.update_galvo_device_flag = None
        self.waveforms_enabled = True
        self.amplitude_dict = None

        # event id list
        self.event_id = None

        # Event Binding
        # Switching microscopes modes (e.g., meso, nano, etc.)
        self.widgets["Mode"].widget.bind(
            "<<ComboboxSelected>>", self.show_magnification
        )

        # Switching magnifications (e.g., 10x, 20x, etc.)
        self.widgets["Mag"].widget.bind("<<ComboboxSelected>>", self.show_laser_info)

        # Changes to the waveform constants (amplitude, offset, etc.)
        for laser in self.lasers:
            self.variables[laser + " Amp"].trace_add(
                "write",
                self.update_remote_focus_settings(laser + " Amp", laser, "amplitude"),
            )
            self.variables[laser + " Off"].trace_add(
                "write",
                self.update_remote_focus_settings(laser + " Off", laser, "offset"),
            )

        # Changes to the galvo constants (amplitude, offset, etc.)
        for i in range(self.configuration_controller.galvo_num):
            galvo = f"Galvo {i}"
            self.variables[galvo + " Amp"].trace_add(
                "write", self.update_galvo_setting(galvo, " Amp", "amplitude")
            )
            self.variables[galvo + " Off"].trace_add(
                "write", self.update_galvo_setting(galvo, " Off", "offset")
            )
            self.variables[galvo + " Freq"].trace_add(
                "write", self.update_galvo_setting(galvo, " Freq", "frequency")
            )

        # Changes in the delay, duty cycle, and smoothing waveform parameters
        # Delay, Duty, and Smoothing
        self.variables["Delay"].trace_add("write", self.update_waveform_parameters)
        self.variables["Duty"].trace_add("write", self.update_waveform_parameters)
        self.variables["Smoothing"].trace_add("write", self.update_waveform_parameters)

        # Save waveform constants
        self.view.get_buttons()["Save"].configure(command=self.save_waveform_constants)

        # Temporarily disable waveforms
        self.view.get_buttons()["toggle_waveform_button"].configure(
            command=self.toggle_waveform_state
        )

        # Save waveform constants upon closing the popup window
        self.view.popup.protocol(
            "WM_DELETE_WINDOW",
            combine_funcs(
                self.restore_amplitude,
                self.save_waveform_constants,
                self.view.popup.dismiss,
                lambda: delattr(self.parent_controller, "waveform_popup_controller"),
            ),
        )

        # Populate widgets
        self.widgets["Mode"].widget["values"] = list(
            self.resolution_info["remote_focus_constants"].keys()
        )
        self.widgets["Mode"].widget["state"] = "readonly"
        self.widgets["Mag"].widget["state"] = "readonly"

    def configure_widget_range(self):
        """Update widget ranges and precisions based on the current resolution mode.

        TODO: Hard-coded values for increment and precision.

        TODO: Other parameters we wish to enable/disable based on configuration?

        TODO: Should we instead change galvo amp/offset behavior based on a waveform
        type passed in the configuration? That is, should we pass galvo_l_waveform:
        sawtooth and galvo_r_waveform: dc_value? And then adjust the
        ETL_Popup_Controller accordingly? We could do the same for ETL vs. voice coil.


        This function updates the widget ranges and precisions based on the current
        resolution mode. The precision is set to -3 for high and nanoscale modes and -2
        for low mode. The increment is set to 0.001 for high and nanoscale modes and
        0.01 for low mode.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.resolution == "high" or self.resolution == "Nanoscale":
            precision = -3
            increment = 0.001
        else:
            # resolution is low
            precision = -2
            increment = 0.01

        laser_min = self.configuration_controller.remote_focus_dict["hardware"]["min"]
        laser_max = self.configuration_controller.remote_focus_dict["hardware"]["max"]

        # set ranges of value for those lasers
        for laser in self.lasers:
            self.widgets[laser + " Amp"].widget.configure(from_=laser_min)
            self.widgets[laser + " Amp"].widget.configure(to=laser_max)
            self.widgets[laser + " Amp"].widget.configure(increment=increment)
            self.widgets[laser + " Amp"].widget.set_precision(precision)
            # TODO: The offset bounds should adjust based on the amplitude bounds,
            #       so that amp + offset does not exceed the bounds. Can be done
            #       in update_remote_focus_settings()
            self.widgets[laser + " Off"].widget.configure(from_=laser_min)
            self.widgets[laser + " Off"].widget.configure(to=laser_max)
            self.widgets[laser + " Off"].widget.configure(increment=increment)
            self.widgets[laser + " Off"].widget.set_precision(precision)

        for galvo, d in zip(self.galvos, self.galvo_dict):
            galvo_min = d["hardware"]["min"]
            galvo_max = d["hardware"]["max"]
            self.widgets[galvo + " Amp"].widget.configure(from_=galvo_min)
            self.widgets[galvo + " Amp"].widget.configure(to=galvo_max)
            self.widgets[galvo + " Amp"].widget.configure(increment=increment)
            self.widgets[galvo + " Amp"].widget.set_precision(precision)
            self.widgets[galvo + " Amp"].widget["state"] = "normal"
            # TODO: The offset bounds should adjust based on the amplitude bounds,
            #       so that amp + offset does not exceed the bounds. Can be done
            #       in update_remote_focus_settings()
            self.widgets[galvo + " Off"].widget.configure(from_=galvo_min)
            self.widgets[galvo + " Off"].widget.configure(to=galvo_max)
            self.widgets[galvo + " Off"].widget.configure(increment=increment)
            self.widgets[galvo + " Off"].widget.set_precision(precision)
            self.widgets[galvo + " Off"].widget["state"] = "normal"

            self.widgets[galvo + " Freq"].widget.configure(from_=0)
            self.widgets[galvo + " Freq"].widget.configure(increment=increment)
            self.widgets[galvo + " Freq"].widget.set_precision(precision)
            self.widgets[galvo + " Freq"].widget["state"] = "normal"

        for i in range(len(self.galvos), self.configuration_controller.galvo_num):
            galvo_name = f"Galvo {i}"
            self.widgets[galvo_name + " Amp"].widget["state"] = "disabled"
            self.widgets[galvo_name + " Off"].widget["state"] = "disabled"
            self.widgets[galvo_name + " Freq"].widget["state"] = "disabled"

        # The galvo by default uses a sawtooth waveform.
        # However, sometimes we have a resonant galvo.
        # In the case of the resonant galvo, amplitude is zero and only the offset
        # can be controlled. We only define the offset in the configuration.yml file.
        # If only the offset is defined for galvo_{focus_prefix}, we disable the
        # amplitude.
        #

    def populate_experiment_values(self):
        """Set experiment values.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.remote_focus_experiment_dict = self.parent_controller.configuration[
            "experiment"
        ]["MicroscopeState"]
        resolution_value = self.remote_focus_experiment_dict["microscope_name"]
        zoom_value = self.remote_focus_experiment_dict["zoom"]
        mag = zoom_value
        if (
            self.widgets["Mode"].get() == resolution_value
            and self.widgets["Mag"].get() == mag
        ):
            return
        self.widgets["Mode"].set(resolution_value)
        self.show_magnification(mag)

        # Load waveform parameters from configuration - Smooth, Delay, Duty Cycle.
        # Provide defaults should loading fail.
        waveform_parameters = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][resolution_value]["remote_focus_device"]
        self.widgets["Smoothing"].set(waveform_parameters.get("smoothing", 0))
        self.widgets["Delay"].set(waveform_parameters.get("delay_percent", 7.5))
        self.widgets["Duty"].set(waveform_parameters.get("ramp_rising_percent", 85))

    def showup(self):
        """This function will let the popup window show in front.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def show_magnification(self, *args):
        """Show magnification options when the user changes the focus mode.

        Parameters
        ----------
        *args : tuple
            The first element is the new focus mode.

        Returns
        -------
        None
        """
        # restore amplitude before change resolution if needed
        self.restore_amplitude()
        # get resolution setting
        self.resolution = self.widgets["Mode"].widget.get()
        temp = list(
            self.resolution_info["remote_focus_constants"][self.resolution].keys()
        )
        self.widgets["Mag"].widget["values"] = temp

        if args[0] in temp:
            self.widgets["Mag"].widget.set(args[0])
        else:
            self.widgets["Mag"].widget.set(temp[0])

        # update laser info
        self.show_laser_info()

    def show_laser_info(self, *args):
        """Show laser info when the user changes magnification setting.

        Parameters
        ----------
        *args : tuple
            The first element is the new magnification setting.

        Returns
        -------
        None
        """
        # get galvo dict for the specified microscope/magnification
        self.galvo_dict = self.parent_controller.configuration["configuration"][
            "microscopes"
        ][self.resolution]["galvo"]
        self.galvos = [f"Galvo {i}" for i in range(len(self.galvo_dict))]
        # restore amplitude before change mag if needed
        self.restore_amplitude()
        # get magnification setting
        self.mag = self.widgets["Mag"].widget.get()
        for laser in self.lasers:
            self.variables[laser + " Amp"].set(
                self.resolution_info["remote_focus_constants"][self.resolution][
                    self.mag
                ][laser]["amplitude"]
            )
            self.variables[laser + " Off"].set(
                self.resolution_info["remote_focus_constants"][self.resolution][
                    self.mag
                ][laser]["offset"]
            )

        # do not tell the model to update galvo
        self.update_galvo_device_flag = False
        for galvo in self.galvos:
            self.variables[galvo + " Amp"].set(
                self.galvo_setting[galvo][self.resolution][self.mag].get("amplitude", 0)
            )
            self.variables[galvo + " Off"].set(
                self.galvo_setting[galvo][self.resolution][self.mag].get("offset", 0)
            )
            self.variables[galvo + " Freq"].set(
                self.galvo_setting[galvo][self.resolution][self.mag].get("frequency", 0)
            )
        self.update_galvo_device_flag = True

        # update resolution value in central controller (menu)
        value = f"{self.resolution} {self.mag}"
        if self.parent_controller.resolution_value.get() != value:
            self.parent_controller.resolution_value.set(value)

        # reconfigure widgets
        self.configure_widget_range()

    def update_remote_focus_settings(self, name, laser, remote_focus_name):
        """Update remote focus settings in memory.

        Parameters
        ----------
        name : str
            The name of the variable.
        laser : str
            The name of the laser.
        remote_focus_name : str
            The name of the remote focus setting.

        Returns
        -------
        None
        """
        variable = self.variables[name]

        # TODO: Is this still a bug?
        # BUG Upon startup this will always run 0.63x,
        # and when changing magnification it will run 0.63x
        # before whatever mag is selected
        def func_laser(*args):
            value = self.resolution_info["remote_focus_constants"][self.resolution][
                self.mag
            ][laser][remote_focus_name]

            # Will only run code if value in constants does not match whats in GUI
            # for Amp or Off AND in Live mode
            # TODO: Make also work in the 'single' acquisition mode.
            variable_value = variable.get()
            logger.debug(
                f"Remote Focus Amplitude/Offset Changed pre if statement: "
                f"{variable_value}"
            )
            if value != variable_value and variable_value != "":
                self.resolution_info["remote_focus_constants"][self.resolution][
                    self.mag
                ][laser][remote_focus_name] = variable_value
                logger.debug(
                    f"Remote Focus Amplitude/Offset Changed:, {variable_value}"
                )
                # tell parent controller (the device)
                if self.event_id:
                    self.view.popup.after_cancel(self.event_id)

                # Delay feature.
                self.event_id = self.view.popup.after(
                    500,
                    lambda: self.parent_controller.execute(
                        "update_setting", "resolution"
                    ),
                )

        return func_laser

    def update_waveform_parameters(self, *args, **wargs):
        """Update the waveform parameters for delay, duty cycle, and smoothing.

        Communicate changes to the parent controller.

        Parameters
        ----------
        *args : tuple
            The first element is the new waveform.
        **wargs : dict
            The key is the name of the waveform and the value is the waveform

        Returns
        -------
        None
        """
        # Get the waveform parameters.
        try:
            delay = float(self.widgets["Delay"].widget.get())
            duty_cycle = float(self.widgets["Duty"].widget.get())
            smoothing = float(self.widgets["Smoothing"].widget.get())
            waveform_parameters = {
                "delay": delay,
                "duty_cycle": duty_cycle,
                "smoothing": smoothing,
            }

            # Pass the values to the parent controller.
            self.event_id = self.view.popup.after(
                500,
                lambda: self.parent_controller.execute(
                    "update_setting", "waveform_parameters", waveform_parameters
                ),
            )
        except ValueError:
            logger.debug("Waveform parameters not updated by waveform_popup_controller")

    def update_galvo_setting(self, galvo_name, widget_name, parameter):
        """Update galvo settings in memory.

        Parameters
        ----------
        galvo_name : str
            The name of the galvo.
        widget_name : str
            The name of the widget.
        parameter : str
            The name of the parameter.

        Returns
        -------
        None
        """
        name = galvo_name + widget_name
        variable = self.variables[name]

        def func_galvo(*args):
            if not self.update_galvo_device_flag:
                return
            try:
                value = self.galvo_setting[galvo_name][self.resolution][self.mag][
                    parameter
                ]
            except KeyError:
                # Special case for galvo amplitude not being defined
                value = 0
            variable_value = variable.get()
            logger.debug(
                f"Galvo parameter {parameter} changed: "
                f"{variable_value} pre if statement"
            )
            if value != variable_value and variable_value != "":
                self.galvo_setting[galvo_name][self.resolution][self.mag][
                    parameter
                ] = variable_value
                logger.debug(f"Galvo parameter {parameter} changed: {variable_value}")
                # change any galvo parameters as one event
                try:
                    if self.event_id:
                        self.view.popup.after_cancel(self.event_id)
                except KeyError:
                    pass

                self.event_id = self.view.popup.after(
                    500,
                    lambda: self.parent_controller.execute("update_setting", "galvo"),
                )

        return func_galvo

    def save_waveform_constants(self):
        """Save updated waveform parameters to yaml file.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # errors = self.get_errors()
        # if errors:
        #     return  # Dont save if any errors TODO needs testing
        save_yaml_file("", self.resolution_info, self.waveform_constants_path)

    """
    Example for preventing submission of a field/controller. So if there is an error in
    any field that is supposed to have validation then the config cannot be saved.
    """
    # TODO needs testing may also need to be moved to the remote_focus_popup class.
    #  Opinions welcome
    # def get_errors(self):
    #     """
    #     Get a list of field errors in popup
    #     """

    #     errors = {}
    #     for key, labelInput in self.widgets.items():
    #         if hasattr(labelInput.widget, 'trigger_focusout_validation'):
    #             labelInput.widget.trigger_focusout_validation()
    #         if labelInput.error.get():
    #             errors[key] = labelInput.error.get()
    #     return errors
    def toggle_waveform_state(self):
        """Temporarily disable waveform amplitude for quick alignment on stationary
        beam.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.waveforms_enabled is True:
            self.view.buttons["toggle_waveform_button"].config(state="disabled")
            self.view.buttons["toggle_waveform_button"].config(text="Enable Waveforms")
            self.amplitude_dict = {}
            self.amplitude_dict["resolution"] = self.resolution
            self.amplitude_dict["mag"] = self.mag
            for laser in self.lasers:
                self.amplitude_dict[laser] = self.resolution_info[
                    "remote_focus_constants"
                ][self.resolution][self.mag][laser]["amplitude"]
                self.variables[laser + " Amp"].set(0)
                self.widgets[laser + " Amp"].widget.config(state="disabled")
            # galvo
            for galvo in self.galvos:
                self.amplitude_dict[galvo] = self.resolution_info["galvo_constants"][
                    galvo
                ][self.resolution][self.mag]["amplitude"]
                self.variables[galvo + " Amp"].set(0)
                self.widgets[galvo + " Amp"].widget.config(state="disabled")
                # Need to update main controller.
            self.waveforms_enabled = False
            self.view.popup.after(
                500,
                lambda: self.view.buttons["toggle_waveform_button"].config(
                    state="normal"
                ),
            )
        else:
            self.view.buttons["toggle_waveform_button"].config(state="disabled")
            self.show_laser_info()
            # call the parent controller the amplitude values are updated
            try:
                if self.event_id:
                    self.view.popup.after_cancel(self.event_id)
            except KeyError:
                pass

            self.event_id = self.view.popup.after(
                500,
                lambda: self.parent_controller.execute("update_setting", "galvo"),
            )
            self.view.popup.after(
                500,
                lambda: self.view.buttons["toggle_waveform_button"].config(
                    state="normal"
                ),
            )

    def restore_amplitude(self):
        """Restore amplitude values to previous values.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.view.buttons["toggle_waveform_button"].config(text="Disable Waveforms")
        self.waveforms_enabled = True
        if self.amplitude_dict is None:
            return
        resolution = self.amplitude_dict["resolution"]
        mag = self.amplitude_dict["mag"]
        for laser in self.lasers:
            self.resolution_info["remote_focus_constants"][resolution][mag][laser][
                "amplitude"
            ] = self.amplitude_dict[laser]
            self.widgets[laser + " Amp"].widget.config(state="normal")
        for galvo in self.galvos:
            self.resolution_info["galvo_constants"][galvo][resolution][mag][
                "amplitude"
            ] = self.amplitude_dict[galvo]
            self.widgets[galvo + " Amp"].widget.config(state="normal")
        self.amplitude_dict = None
