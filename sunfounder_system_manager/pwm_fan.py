import os
from enum import StrEnum
from sunfounder_service_node.configtxt import ConfigTxt

FAN_LEVELS = {
    "quiet": {
        "fan_temp0": 50000, # 50'C
        "fan_temp1": 60000, # 60'C
        "fan_temp2": 67500, # 67.5'C
        "fan_temp3": 75000, # 75'C
    },
    "normal": {
        "fan_temp0": 45000, # 45'C
        "fan_temp1": 55000, # 55'C
        "fan_temp2": 62500, # 62.5'C
        "fan_temp3": 70000, # 70'C
    },
    "performance": {
        "fan_temp0": 40000, # 40'C
        "fan_temp1": 50000, # 50'C
        "fan_temp2": 57500, # 57.5'C
        "fan_temp3": 65000, # 65'C
    }
}

class FanMode(StrEnum):
    """
    PWM fan mode
    """
    QUIET = "quiet"
    NORMAL = "normal"
    PERFORMANCE = "performance"

class PWMFan():
    """
    PWM fan class
    """
    INTERVAL = 1

    @staticmethod
    def is_supported():
        """
        Check if PWM fan is supported
        """
        from os import path
        return path.exists('/sys/class/thermal/cooling_device0/cur_state') and path.exists('/sys/devices/platform/cooling_fan')

    def get_state(self):
        """
        Get PWM fan state
        """
        path = '/sys/class/thermal/cooling_device0/cur_state'
        try:
            with open(path, 'r') as f:
                cur_state = int(f.read())
            return cur_state
        except Exception as e:
            self.log.error(f'read pwm fan state error: {e}')
            return 0

    def set_state(self, level: int):
        '''
        level: 0 ~ 3
        '''
        if (isinstance(level, int)):
            if level > 3:
                level = 3
            elif level < 0:
                level = 0

            cmd = f"echo '{level}' | tee -a /sys/class/thermal/cooling_device0/cur_state"
            result = subprocess.check_output(cmd, shell=True)

            return result

    def get_speed(self):
        '''
        Get PWM fan speed
        path =  '/sys/devices/platform/cooling_fan/hwmon/*/fan1_input'
        '''
        dir = '/sys/devices/platform/cooling_fan/hwmon/'
        secondary_dir = os.listdir(dir)
        path = f'{dir}/{secondary_dir[0]}/fan1_input'

        os.listdir
        try:
            with open(path, 'r') as f:
                speed = int(f.read())
            return speed
        except Exception as e:
            self.log.error(f'read fan1 speed error: {e}')
            return 0

    def set_mode(self, mode: FanMode):
        """
        Set PWM fan mode
        """
        config = ConfigTxt()
        for name, value in FAN_LEVELS[mode].items():
            config.set_dt_param(name, str(value))
        config.save()

    def close(self):
        pass