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

# Standard Library Imports

# Third Party Imports
import numpy as np
import matplotlib.ticker as tck
from tkinter import messagebox

# Local Imports
from navigate.controller.sub_controllers.gui_controller import GUIController
from navigate.tools.common_functions import combine_funcs


import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


class AutofocusPopupController(GUIController):
    """Class creates the popup to configure autofocus parameters."""

    def __init__(self, view, parent_controller):
        """
        Parameters
        ----------
        view : navigate.view.popups.autofocus_setting_popup.AutofocusPopup
            The view of the autofocus popup.
        parent_controller : navigate.controller.main_controller.MainController
            The parent controller of the autofocus popup.
        """
        super().__init__(view, parent_controller)
        #: dict: The autofocus setting dictionary.
        self.widgets = self.view.get_widgets()
        #: object: The autofocus figure.
        self.autofocus_fig = self.view.fig
        #: object: The autofocus coarse plot.
        self.autofocus_coarse = self.view.coarse
        self.populate_experiment_values()
        #: object: The autofocus coarse plot.
        self.coarse_plot = None

        # add saving function to the function closing the window
        exit_func = combine_funcs(
            self.view.popup.dismiss,
            lambda: delattr(self.parent_controller, "af_popup_controller"),
        )
        self.view.popup.protocol("WM_DELETE_WINDOW", exit_func)
        self.view.autofocus_btn.configure(command=self.start_autofocus)
        self.view.inputs["device"].get_variable().trace_add(
            "write", self.update_device_ref
        )
        self.view.inputs["device_ref"].get_variable().trace_add(
            "write", self.show_autofocus_setting
        )
        for k in self.view.setting_vars:
            self.view.setting_vars[k].trace_add("write", self.update_setting_dict(k))

    def populate_experiment_values(self):
        """Populate Experiment Values

        Populates the experiment values from the experiment settings dictionary
        """
        #: dict: The autofocus setting dictionary.
        self.setting_dict = self.parent_controller.configuration["experiment"][
            "AutoFocusParameters"
        ]
        #: str: The microscope name.
        self.microscope_name = self.parent_controller.configuration["experiment"][
            "MicroscopeState"
        ]["microscope_name"]
        setting_dict = self.setting_dict[self.microscope_name]

        # Default to stages, if they exist.
        if "stage" in setting_dict:
            device = "stage"
        else:
            device = setting_dict.keys()[0]
        self.widgets["device"].widget["values"] = setting_dict.keys()
        self.widgets["device"].set(device)

        # Default to the f axis, if it exists.
        if "f" in setting_dict[device]:
            device_ref = "f"
        else:
            device_ref = setting_dict[device].keys()[0]
        self.widgets["device_ref"].widget["values"] = setting_dict[device].keys()
        self.widgets["device_ref"].set(device_ref)

        for k in self.view.setting_vars:
            self.view.setting_vars[k].set(setting_dict[device][device_ref][k])

    def showup(self):
        """Shows the popup window"""
        self.view.popup.deiconify()
        self.view.popup.attributes("-topmost", 1)

    def start_autofocus(self):
        """Starts the autofocus process."""
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "autofocus_device"
        ] = device
        self.parent_controller.configuration["experiment"]["MicroscopeState"][
            "autofocus_device_ref"
        ] = device_ref
        # verify autofocus parameters
        setting_dict = self.setting_dict[self.microscope_name][device][device_ref]
        warning_message = ""
        for k in ["coarse", "fine"]:
            if setting_dict[f"{k}_selected"]:
                try:
                    step = float(setting_dict[f"{k}_step_size"])
                    value = float(setting_dict[f"{k}_range"])
                    if step <= 0 or value < step:
                        warning_message += f"{k} settings are not correct!\n"
                except:
                    warning_message += f"{k} settings are not correct!\n"
        if warning_message:
            messagebox.showerror(
                title="Navigate",
                message=warning_message,
            )
            return
        self.parent_controller.execute("autofocus", device, device_ref)

    def update_device_ref(self, *args):
        """Update device reference name

        Parameters
        ----------
        args: tk event arguments
        """
        device = self.widgets["device"].widget.get()
        device_refs = self.setting_dict[self.microscope_name][device].keys()
        self.widgets["device_ref"].widget["values"] = device_refs
        self.widgets["device_ref"].widget.set(device_refs[0])

    def show_autofocus_setting(self, *args):
        """Show Autofocus Parameters

        Parameters
        ----------
        args: tk event arguments
        """
        device = self.widgets["device"].widget.get()
        device_ref = self.widgets["device_ref"].widget.get()
        setting_dict = self.setting_dict[self.microscope_name]
        for k in self.view.setting_vars:
            self.view.setting_vars[k].set(setting_dict[device][device_ref][k])

    def update_setting_dict(self, parameter):
        """Show Autofocus Parameters

        Parameters
        ----------
        parameter : str
            The parameter to be updated.
        """

        def func(*args):
            device = self.widgets["device"].widget.get()
            device_ref = self.widgets["device_ref"].widget.get()
            self.setting_dict[self.microscope_name][device][device_ref][
                parameter
            ] = self.view.setting_vars[parameter].get()

        return func

    def display_plot(self, data, line_plot=False, clear_data=True):
        """Displays the autofocus plot

        data : numpy.ndarray
            The data to be plotted.
        line_plot : bool
            If True, the plot will be a line plot.
            If False, the plot will be a scatter plot.
        clear_data : bool
            If True, the plot will be cleared before plotting.
            If False, the plot will be added to the existing plot.
        """

        data = np.asarray(data)
        coarse_range = self.setting_dict.get("coarse_range", 500)
        coarse_step = self.setting_dict.get("coarse_step_size", 50)
        fine_range = self.setting_dict.get("fine_range", 50)
        fine_step = self.setting_dict.get("fine_step_size", 5)

        # Calculate the coarse portion of the data
        coarse_steps = int(coarse_range) // int(coarse_step) + 1
        fine_steps = int(fine_range) // int(fine_step) + 1

        if line_plot is True:
            marker = "r-"
        else:
            marker = "k."

        if clear_data is True:
            self.autofocus_coarse.clear()

        # Plotting coarse data
        self.coarse_plot = self.autofocus_coarse.plot(
            data[:coarse_steps, 0], data[:coarse_steps, 1], marker
        )

        # Plotting fine data
        self.coarse_plot = self.autofocus_coarse.plot(
            data[fine_steps:, 0], data[fine_steps:, 1], marker
        )

        # Plot the maxima
        y_max = np.max(data[:, 1])
        peak_loc = data[np.argmax(data[:, 1]), 0]

        y_axes_limit = self.autofocus_coarse.get_ylim()
        x_axes_limit = self.autofocus_coarse.get_xlim()

        # Vertical Indicator
        self.coarse_plot = self.autofocus_coarse.plot(
            [peak_loc, peak_loc], [y_axes_limit[0], y_axes_limit[1]], "--", color="gray"
        )

        # Horizontal Indicator
        self.coarse_plot = self.autofocus_coarse.plot(
            [x_axes_limit[0], x_axes_limit[1]], [y_max, y_max], "--", color="gray"
        )

        # To redraw the plot
        self.autofocus_coarse.set_title("Discrete Cosine Transform", fontsize=18)
        self.autofocus_coarse.set_xlabel("Focus Stage Position", fontsize=16)
        self.autofocus_coarse.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))
        self.autofocus_coarse.yaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_coarse.xaxis.set_minor_locator(tck.AutoMinorLocator())
        self.autofocus_fig.tight_layout()
        self.autofocus_fig.canvas.draw_idle()
