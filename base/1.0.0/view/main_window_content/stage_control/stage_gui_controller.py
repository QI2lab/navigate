from view.notebooks.stage_control.gui_controller import GUI_Controller

class Stage_GUI_Controller(GUI_Controller):
    def __init__(self, view, parent_controller):
        super().__init__(view, parent_controller)

        # gui event bind
        self.view.x_y_frame.positive_x_btn.configure(
            command=self.up_btn_handler('x')
        )
        self.view.x_y_frame.negative_x_btn.configure(
            command=self.down_btn_handler('x')
        )
        self.view.x_y_frame.positive_y_btn.configure(
            command=self.up_btn_handler('y')
        )
        self.view.x_y_frame.negative_y_btn.configure(
            command=self.down_btn_handler('y')
        )
        self.view.x_y_frame.zero_x_y_btn.configure(
            command=self.xy_zero_btn_handler()
        )
        self.view.z_frame.up_btn.configure(
            command=self.up_btn_handler('z')
        )
        self.view.z_frame.down_btn.configure(
            command=self.down_btn_handler('z')
        )
        self.view.z_frame.zero_btn.configure(
            command=self.zero_btn_handler('z')
        )
        self.view.theta_frame.up_btn.configure(
            command=self.up_btn_handler('theta')
        )
        self.view.theta_frame.down_btn.configure(
            command=self.down_btn_handler('theta')
        )
        self.view.theta_frame.zero_btn.configure(
            command=self.zero_btn_handler('theta')
        )
        self.view.focus_frame.up_btn.configure(
            command=self.up_btn_handler('f')
        )
        self.view.focus_frame.down_btn.configure(
            command=self.down_btn_handler('f')
        )
        self.view.focus_frame.zero_btn.configure(
            command=self.zero_btn_handler('f')
        )
        self.view.position_frame.x_val.trace_add('write', self.position_callback('x'))
        self.view.position_frame.y_val.trace_add('write', self.position_callback('y'))
        self.view.position_frame.z_val.trace_add('write', self.position_callback('z'))
        self.view.position_frame.theta_val.trace_add('write', self.position_callback('theta'))
        self.view.position_frame.focus_val.trace_add('write', self.position_callback('f'))

        self.event_id = {
            'x': None,
            'y': None,
            'z': None,
            'theta': None,
            'f': None
        }

    def set_position(self, postion):
        '''
        # This function is to populate(set) position
        # position should be a dict
        # {'x': value, 'y': value, 'z': value, 'theta': value, 'f': value}
        '''
        for axis in postion:
            val = self.get_position_val(axis)
            if val:
                val.set(postion[axis])

    def get_position(self):
        '''
        # This function returns current postion
        '''
        position = {
            'x': self.get_position_val('x').get(),
            'y': self.get_position_val('y').get(),
            'z': self.get_position_val('z').get(),
            'theta': self.get_position_val('theta').get(),
            'f': self.get_position_val('f').get()
        }
        return position

    def set_step_size(self, steps):
        '''
        # This function is to populate(set) step sizes
        # steps should be a dict
        # {'x': value, 'z': value, 'theta': value, 'f': value}
        '''
        for axis in steps:
            val = self.get_step_val(axis)
            if val:
                val.set(steps[axis])

    def up_btn_handler(self, axis):
        '''
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis += step_axis
        '''
        position_val = self.get_position_val(axis)
        step_val = self.get_step_val(axis)
        def handler():
            position_val.set(position_val.get() + step_val.get())
        return handler

    def down_btn_handler(self, axis):
        '''
        # This function generates command functions according to axis
        # axis should be one of 'x', 'y', 'z', 'theta', 'f'
        # position_axis -= step_axis
        '''
        position_val = self.get_position_val(axis)
        step_val = self.get_step_val(axis)
        def handler():
            position_val.set(position_val.get() - step_val.get())
        return handler

    def zero_btn_handler(self, axis):
        '''
        # This function generates command functions according to axis
        # axis should be one of 'z', 'theta', 'f'
        # position_axis = 0
        '''
        position_val = self.get_position_val(axis)
        def handler():
            position_val.set(0)
        return handler

    def xy_zero_btn_handler(self):
        '''
        # This function generates command functions to set xy postion to zero
        '''
        x_val = self.get_position_val('x')
        y_val = self.get_position_val('y')
        def handler():
            x_val.set(0)
            y_val.set(0)
        return handler

    def position_callback(self, axis):
        '''
        # callback functions bind to position variables
        # axis can be 'x', 'y', 'z', 'theta', 'f'
        # this function considers debouncing user inputs(or click buttons)
        # to reduce time costs of moving stage device
        '''
        position_var = self.get_position_val(axis)

        def handler(*args):
            if self.event_id[axis]:
                self.view.after_cancel(self.event_id[axis])
            self.event_id[axis] = self.view.after(1000, \
                lambda: self.parent_controller.execute('stage', position_var.get(), axis))
        
        return handler

    def get_step_val(self, axis):
        '''
        # get increment step variable accroding to axis name
        # axis can be: 'x', 'y', 'z', 'theta', 'f'
        '''
        if axis == 'x' or axis == 'y':
            return self.view.x_y_frame.spinval
        elif axis == 'z':
            return self.view.z_frame.spinval
        elif axis == 'theta':
            return self.view.theta_frame.spinval
        elif axis == 'f':
            return self.view.focus_frame.spinval
        return None

    def get_position_val(self, axis):
        '''
        # get position variable according to axis name
        # axis can be 'x', 'y', 'z', 'theta', 'f'
        '''
        if axis == 'x':
            return self.view.position_frame.x_val
        elif axis == 'y':
            return self.view.position_frame.y_val
        elif axis == 'z':
            return self.view.position_frame.z_val
        elif axis == 'theta':
            return self.view.position_frame.theta_val
        elif axis == 'f':
            return self.view.position_frame.focus_val