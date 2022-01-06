"""
NI Synthetic DAQ Class
"""

# Standard Imports
import os
import numpy as np
import csv
import time

# Third Party Imports
import nidaqmx
from nidaqmx.constants import AcquisitionType, TaskMode
from nidaqmx.constants import LineGrouping, DigitalWidthUnits
from nidaqmx.types import CtrTime

# Local Imports
from .waveforms import *
from .DAQBase import DAQBase as DAQBase

class DAQ(DAQBase):
    def __init__(self, session, verbose):
        self.verbose = True

        #TODO: Load the ETL configuration file.
        # Will need to move the ETL configuration file to the config folder
        cfg_file = session.StartupParameters['ETL_cfg_file']
        self.update_etl_parameters_from_csv(cfg_file, self.state['laser'], self.state['zoom'])

        # Specify the Galvo Waveform Parameters
        self.state['galvo_l_amplitude'] = session.StartupParameters['galvo_l_amplitude']
        self.state['galvo_r_amplitude'] = session.StartupParameters['galvo_r_amplitude']
        self.state['galvo_l_frequency'] = session.StartupParameters['galvo_l_frequency']
        self.state['galvo_r_frequency'] = session.StartupParameters['galvo_r_frequency']
        self.state['galvo_l_offset'] = session.StartupParameters['galvo_l_offset']
        self.state['galvo_r_offset'] = session.StartupParameters['galvo_r_offset']

    def state_request_handler(self, dict):
        for key, value in zip(dict.keys(), dict.values()):
            if key in ('samplerate',
                       'sweeptime',
                       'intensity',
                       'etl_l_delay_percent',
                       'etl_l_ramp_rising_percent',
                       'etl_l_ramp_falling_percent',
                       'etl_l_amplitude',
                       'etl_l_offset',
                       'etl_r_delay_percent',
                       'etl_r_ramp_rising_percent',
                       'etl_r_ramp_falling_percent',
                       'etl_r_amplitude',
                       'etl_r_offset',
                       'galvo_l_frequency',
                       'galvo_l_amplitude',
                       'galvo_l_offset',
                       'galvo_l_duty_cycle',
                       'galvo_l_phase',
                       'galvo_r_frequency',
                       'galvo_r_amplitude',
                       'galvo_r_offset',
                       'galvo_r_duty_cycle',
                       'galvo_r_phase',
                       'laser_l_delay_percent',
                       'laser_l_pulse_percent',
                       'laser_l_max_amplitude',
                       'laser_r_delay_percent',
                       'laser_r_pulse_percent',
                       'laser_r_max_amplitude',
                       'camera_delay_percent',
                       'camera_pulse_percent'):

                # Update the state
                self.state[key] = value
                self.create_waveforms()

            elif key in ('ETL_cfg_file'):
                self.state[key] = value
                self.update_etl_parameters_from_csv(value, self.state['laser'], self.state['zoom'])
                if self.verbose:
                    print('ETL CFG File changed')

            elif key in ('set_etls_according_to_zoom'):
                self.update_etl_parameters_from_zoom(value)
                if self.verbose:
                    print('Updated ETL Parameters Owing to Zoom Change')

            elif key in ('set_etls_according_to_laser'):
                self.state['laser'] = value
                self.create_waveforms()
                self.update_etl_parameters_from_laser(value)
                if self.verbose:
                    print('Updated ETL Parameters Owing to Laser Change')

            elif key in ('laser'):
                self.state['laser'] = value
                self.create_waveforms()

            elif key == 'state':
                if value == 'live':
                    print('Live mode')

    def calculate_samples(self):
        # Calculate the number of samples for the waveforms.
        # Simply the sampling frequency times the duration of the waveform.
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate', 'sweeptime'])
        self.samples = int(samplerate*sweeptime)
        if self.verbose:
            print('Number of samples: ' + str(self.samples))

    def create_waveforms(self):
        # Create the waveforms for the ETL, Galvos, and Lasers.
        self.calculate_samples()
        self.create_etl_waveforms()
        self.create_galvo_waveforms()
        self.create_laser_waveforms()

        # Bundle the waveforms into a single waveform.
        self.bundle_galvo_and_etl_waveforms()

    def create_etl_waveforms(self):
        # Calculate the waveforms for the ETLs.
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])
        etl_l_delay, etl_l_ramp_rising, etl_l_ramp_falling, etl_l_amplitude, etl_l_offset = \
            self.state.get_parameter_list(['etl_l_delay_percent','etl_l_ramp_rising_percent','etl_l_ramp_falling_percent',
                                           'etl_l_amplitude','etl_l_offset'])

        etl_r_delay, etl_r_ramp_rising, etl_r_ramp_falling, etl_r_amplitude, etl_r_offset = \
            self.state.get_parameter_list(['etl_r_delay_percent','etl_r_ramp_rising_percent','etl_r_ramp_falling_percent',
                                           'etl_r_amplitude','etl_r_offset'])

        self.etl_l_waveform = tunable_lens_ramp(samplerate=samplerate,
                                                sweeptime=sweeptime,
                                                delay=etl_l_delay,
                                                rise=etl_l_ramp_rising,
                                                fall=etl_l_ramp_falling,
                                                amplitude=etl_l_amplitude,
                                                offset=etl_l_offset)

        self.etl_r_waveform = tunable_lens_ramp(samplerate=samplerate,
                                                sweeptime=sweeptime,
                                                delay=etl_r_delay,
                                                rise=etl_r_ramp_rising,
                                                fall=etl_r_ramp_falling,
                                                amplitude=etl_r_amplitude,
                                                offset=etl_r_offset)

    def create_low_res_galvo_waveforms(self):
        # Calculate the sawtooth waveforms for the low-resolution digitally scanned galvo.
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])

        galvo_l_frequency, galvo_l_amplitude, galvo_l_offset, galvo_l_duty_cycle, galvo_l_phase = \
            self.state.get_parameter_list(['galvo_l_frequency', 'galvo_l_amplitude', 'galvo_l_offset',
                                           'galvo_l_duty_cycle', 'galvo_l_phase'])

        self.galvo_l_waveform = sawtooth(samplerate=samplerate,
                                         sweeptime=sweeptime,
                                         frequency=galvo_l_frequency,
                                         amplitude=galvo_l_amplitude,
                                         offset=galvo_l_offset,
                                         dutycycle=galvo_l_duty_cycle,
                                         phase=galvo_l_phase)

    def create_high_res_galvo_waveforms(self):
        # Calculate the DC waveform for the resonant galvanometer drive signal.
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])
        self.galvo_r_waveform = dc_value(samplerate=samplerate,
                                         sweeptime=sweeptime,
                                         amplitude=0.5,
                                         offset=0)


    def create_laser_waveforms(self):
        # Calculate the waveforms for the lasers.
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])

        # Get the laser parameters.
        laser_l_delay, laser_l_pulse, max_laser_voltage, intensity = \
            self.state.get_parameter_list(['laser_l_delay_percent','laser_l_pulse_percent',
                                           'max_laser_voltage','intensity'])

        # Create a zero waveform
        self.zero_waveform = np.zeros((self.samples))

        # Update the laser intensity waveform
        # This could be improved: create a list with as many zero arrays as analog out lines for ETL and Lasers
        self.laser_waveform_list = [self.zero_waveform for i in self.cfg.laser_designation]

        # Convert from intensity to voltage
        laser_voltage = max_laser_voltage * intensity / 100

        self.laser_template_waveform = single_pulse(samplerate=samplerate,
                                                    sweeptime=sweeptime,
                                                    delay=laser_l_delay,
                                                    pulsewidth=laser_l_pulse,
                                                    amplitude=laser_voltage,
                                                    offset=0)

        # The key: replace the waveform in the waveform list with this new template
        current_laser_index = self.cfg.laser_designation[self.state['laser']]
        self.laser_waveform_list[current_laser_index] = self.laser_template_waveform
        self.laser_waveforms = np.stack(self.laser_waveform_list)

    def bundle_galvo_and_etl_waveforms(self):
        ''' Stacks the Galvo and ETL waveforms into a numpy array adequate for
        the NI cards. In here, the assignment of output channels of the Galvo / ETL card to the
        corresponding output channel is hardcoded: This could be improved.
        '''
        self.galvo_and_etl_waveforms = np.stack((self.galvo_l_waveform,
                                                 self.galvo_r_waveform,
                                                 self.etl_l_waveform,
                                                 self.etl_r_waveform))

    def update_etl_parameters_from_zoom(self, zoom):
        ''' Little helper method: Because the multiscale core is not handling
        the serial Zoom connection. '''
        laser = self.state['laser']
        etl_cfg_file = self.state['ETL_cfg_file']
        self.update_etl_parameters_from_csv(etl_cfg_file, laser, zoom)

    def update_etl_parameters_from_laser(self, laser):
        ''' Little helper method: Because laser changes need an ETL parameter update '''
        zoom = self.state['zoom']
        etl_cfg_file = self.state['ETL_cfg_file']
        self.update_etl_parameters_from_csv(etl_cfg_file, laser, zoom)

    def update_etl_parameters_from_csv(self, cfg_path, laser, zoom):
        '''
        Updates the internal ETL left/right offsets and amplitudes from the
        values in the ETL csv files. The .csv file needs to contain the following columns:

        Wavelength
        Zoom
        ETL-Left-Offset
        ETL-Left-Amp
        ETL-Right-Offset
        ETL-Right-Amp
        '''
        if self.verbose:
            print('Updating ETL parameters from file:', cfg_path)

        with open(cfg_path) as file:
            reader = csv.DictReader(file, delimiter=';')
            if self.verbose:
                print('Opened ETL Configuration File')
            for row in reader:
                if row['Wavelength'] == laser and row['Zoom'] == zoom:
                    if self.verbose:
                        print(row)
                        print('updating parameters')
                        print(self.etl_l['amplitude'])

                    # Update the internal state.
                    etl_l_offset = float(row['ETL-Left-Offset'])
                    etl_l_amplitude = float(row['ETL-Left-Amp'])
                    etl_r_offset = float(row['ETL-Right-Offset'])
                    etl_r_amplitude = float(row['ETL-Right-Amp'])

                    parameter_dict = {'etl_l_offset':etl_l_offset,
                                      'etl_l_amplitude':etl_l_amplitude,
                                      'etl_r_offset':etl_r_offset,
                                      'etl_r_amplitude':etl_r_amplitude}

                    if self.verbose:
                        print('Parameters Updated from ETL Configuration File')

                    # Update the internal state.
                    self.state.set_parameters(parameter_dict)

        self.create_waveforms()
        # self.sig_update_gui_from_state.emit(False)

    def save_etl_parameters_to_csv(self):
        ''' Saves the current ETL left/right offsets and amplitudes '''

        etl_cfg_file, laser, zoom, etl_l_offset, etl_l_amplitude, etl_r_offset, etl_r_amplitude = \
            self.state.get_parameter_list(['ETL_cfg_file', 'laser', 'zoom',
                                           'etl_l_offset', 'etl_l_amplitude', 'etl_r_offset','etl_r_amplitude'])

        # Generate the temporary file name
        tmp_etl_cfg_file = etl_cfg_file+'_tmp'

        if self.verbose:
            print('saving current ETL parameters')

        with open(etl_cfg_file,'r') as input_file, open(tmp_etl_cfg_file,'w') as outputfile:
            reader = csv.DictReader(input_file,delimiter=';')
            if self.verbose:
                print('Opened DictReader')
            fieldnames = ['Objective',
                          'Wavelength',
                          'Zoom',
                          'ETL-Left-Offset',
                          'ETL-Left-Amp',
                          'ETL-Right-Offset',
                          'ETL-Right-Amp']

            writer = csv.DictWriter(outputfile,fieldnames=fieldnames,dialect='excel',delimiter=';')
            if self.verbose:
                print('Opened DictWriter')

            writer.writeheader()
            if self.verbose:
                print('Wrotet he header')

            for row in reader:
                if row['Wavelength'] == laser and row['Zoom'] == zoom:

                    writer.writerow({'Objective':'1x',
                                     'Wavelength':laser,
                                     'Zoom':zoom,
                                     'ETL-Left-Offset':etl_l_offset,
                                     'ETL-Left-Amp':etl_l_amplitude,
                                     'ETL-Right-Offset':etl_r_offset,
                                     'ETL-Right-Amp':etl_r_amplitude,
                                     })

                else:
                    writer.writerow(row)
            writer.writerows(reader)
        os.remove(etl_cfg_file)
        os.rename(tmp_etl_cfg_file, etl_cfg_file)
        if self.verbose:
            print('Saved current ETL parameters')

    def create_tasks(self):
        '''
        Creates a total of four tasks for the microscope:
        These are:
        - the master trigger task, a digital out task that only provides a trigger pulse for the others
        - the camera trigger task, a counter task that triggers the camera in lightsheet mode
        - the galvo task (analog out) that controls the left & right galvos for creation of
          the light-sheet and shadow avoidance
        - the ETL & Laser task (analog out) that controls all the laser intensities (Laser should only
          be on when the camera is acquiring) and the left/right ETL waveforms
        '''

        # TODO: Get the Acquisition Hardware from the Configuration File
        ah = self.cfg.acquisition_hardware

        self.calculate_samples()
        samplerate, sweeptime = self.state.get_parameter_list(['samplerate','sweeptime'])
        samples = self.samples
        camera_pulse_percent, camera_delay_percent = self.state.get_parameter_list(['camera_pulse_percent','camera_delay_percent'])

        # Create the master trigger, camera trigger, etl, and laser tasks
        self.master_trigger_task = nidaqmx.Task()
        self.camera_trigger_task = nidaqmx.Task()
        self.galvo_etl_task = nidaqmx.Task()
        self.laser_task = nidaqmx.Task()

        # Set up the DO master trigger task
        self.master_trigger_task.do_channels.add_do_chan(ah['master_trigger_out_line'],
                                                         line_grouping=LineGrouping.CHAN_FOR_ALL_LINES)

        # Calculate camera high time and initial delay.
        # Disadvantage: high time and delay can only be set after a task has been created
        self.camera_high_time = camera_pulse_percent*0.01*sweeptime
        self.camera_delay = camera_delay_percent*0.01*sweeptime

        # Set up the camera trigger
        self.camera_trigger_task.co_channels.add_co_pulse_chan_time(ah['camera_trigger_out_line'],
                                                                    high_time=self.camera_high_time,
                                                                    initial_delay=self.camera_delay)

        # Configure camera to be triggered by the master trigger
        self.camera_trigger_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['camera_trigger_source'])

        # Set up the Galvo and setting the trigger input
        self.galvo_etl_task.ao_channels.add_ao_voltage_chan(ah['galvo_etl_task_line'])
        self.galvo_etl_task.timing.cfg_samp_clk_timing(rate=samplerate,
                                                       sample_mode=AcquisitionType.FINITE,
                                                       samps_per_chan=samples)

        # Set up the ETL to be triggered by the master trigger
        self.galvo_etl_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['galvo_etl_task_trigger_source'])

        # Set up the ETL and lasers
        self.laser_task.ao_channels.add_ao_voltage_chan(ah['laser_task_line'])
        self.laser_task.timing.cfg_samp_clk_timing(rate=samplerate,
                                                   sample_mode=AcquisitionType.FINITE,
                                                   samps_per_chan=samples)

        # Configure ETL and Lasers to ber triggered by the master trigger
        self.laser_task.triggers.start_trigger.cfg_dig_edge_start_trig(ah['laser_task_trigger_source'])

    def write_waveforms_to_tasks(self):
        '''
        Write the waveforms to the slave tasks
        '''
        self.galvo_etl_task.write(self.galvo_and_etl_waveforms)
        self.laser_task.write(self.laser_waveforms)

    def start_tasks(self):
        '''
        Start the tasks for camera triggering and analog outputs
        If the tasks are configured to be triggered, they won't output any signals until run_tasks() is called.
        '''
        self.camera_trigger_task.start()
        self.galvo_etl_task.start()
        self.laser_task.start()

    def run_tasks(self):
        '''
        Run the tasks for triggering, analog and counter outputs.
        the master trigger initiates all other tasks via a shared trigger
        For this to work, all analog output and counter tasks have to be started so
        that they are waiting for the trigger signal.
        '''

        self.master_trigger_task.write([False, True, True, True, False], auto_start=True)
        # Wait until waveforms have been output
        self.galvo_etl_task.wait_until_done()
        self.laser_task.wait_until_done()
        self.camera_trigger_task.wait_until_done()

    def stop_tasks(self):
        # Stop the tasks for triggering, analog and counter outputs.
        self.galvo_etl_task.stop()
        self.laser_task.stop()
        self.camera_trigger_task.stop()
        self.master_trigger_task.stop()

    def close_tasks(self):
        # Close the tasks for triggering, analog, and counter outputs.
        self.galvo_etl_task.close()
        self.laser_task.close()
        self.camera_trigger_task.close()
        self.master_trigger_task.close()

if (__name__ == "__main__"):
    print("Testing Mode - WaveFormGenerator Class")
    print(constants.AcquisitionHardware.hardware_type)