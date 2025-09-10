from sunfounder_service_node import ServiceNode
from sunfounder_service_node.lazy_caller import LazyCaller
import time
from typing import Dict, Any

# 导入系统监控相关函数
from sf_rpi_status import (
    get_cpu_temperature, get_gpu_temperature, get_cpu_percent,
    get_cpu_freq, get_cpu_count, get_memory_info, get_disks,
    get_disks_info, get_boot_time, get_ips, get_macs,
    get_network_connection_type, get_network_speed, shutdown
)

from .pi5_power_button import Pi5PowerButton, ButtonStatus
from .pwm_fan import FanMode, PWMFan

class SystemManager(ServiceNode):
    """树莓派系统监控节点，基于新的ServiceNode核心库实现"""
    
    def __init__(self, *args, **kwargs):
        # 配置节点基础信息
        node_id = "system-manager"
        super().__init__(node_id, *args, **kwargs)
        self.power_button = None
        self.pwm_fan

        # 初始化任务调度器和命令处理器
        self.subscribe("system/shutdown", self.handle_shutdown)
        
        """初始化任务调度器"""
        self.task_1s_caller = LazyCaller(self.task_1s, interval=1)
        self.task_3s_caller = LazyCaller(self.task_3s, interval=3)
        self.task_5s_caller = LazyCaller(self.task_5s, interval=5)
    
    # ------------------------------
    # 命令处理器
    # ------------------------------
    def init_pi5_power_button(self):
        if self.power_button is None:
            self.power_button = Pi5PowerButton()
            self.power_button.set_button_callback(self.handle_power_button)
            self.power_button.start()

    def init_pwm_fan(self):
        if self.pwm_fan is None:
            try:
                self.pwm_fan = PWMFan()
            except Exception as e:
                self.log.error(f"PWM fan not supported: {str(e)}")

    def handle_shutdown(self, data: Dict) -> Dict:
        """处理关机命令"""
        reason = data.get("reason", "No reason provided")
        initiator = data.get("initiator", "unknown")
        
        # 发布关机前事件
        self.publish("system/before_shutdown", {
                "reason": reason,
                "initiator": initiator,
            }
        )
        
        time.sleep(5)
        
        try:
            shutdown()
        except Exception as e:
            self.log.error(f"Shutdown failed: {str(e)}")

    def handle_power_button(self, status: ButtonStatus) -> None:
        """处理电源按钮事件"""
        if status == ButtonStatus.CLICK:
            self.log.debug("Pi5 power button click")
            self.publish('system/pi5_power_button_click', status)
        elif status == ButtonStatus.DOUBLE_CLICK:
            self.log.debug("Pi5 power button double click")
            self.publish('system/pi5_power_button_double_click', status)
        elif status == ButtonStatus.LONG_PRESS_2S:
            self.log.debug("Pi5 power button long press")
            self.publish('system/pi5_power_button_long_press', status)
        elif status == ButtonStatus.LONG_PRESS_2S_RELEASED:
            self.log.debug("Pi5 power button long press released")
            self.publish('system/pi5_power_button_long_press_released', status)

    def on_config_changed(self, config: Dict[str, Any], init=False) -> None:
        """当配置改变时调用"""
        patch = {}
        if "pwm_fan_mode" in config:
            if config["pwm_fan_mode"] in FanMode:
                if self.pwm_fan:
                    self.pwm_fan.set_mode(config["pwm_fan_mode"])
                patch["pwm_fan_mode"] = config["pwm_fan_mode"]
            else:
                self.log.error(f"Invalid PWM fan mode: {config['pwm_fan_mode']}")
        return patch

    def on_peripherals_changed(self, peripherals: Dict[str, Any]) -> None:
        """当外设配置改变时调用"""
        if "power_button" in peripherals:
            self.init_pi5_power_button()
        if "pwm_fan" in peripherals:
            self.init_pwm_fan()

    # ------------------------------
    # 定时任务（数据采集与发布）
    # ------------------------------
    def task_once(self) -> None:
        """只执行一次的初始化任务"""
        data = {}
        
        # 收集CPU核心数
        if "cpu" in self.peripherals:
            data["cpu_count"] = int(get_cpu_count())
        
        # 收集MAC地址
        if "mac_address" in self.peripherals:
            for name, addr in get_macs().items():
                data[f"mac_{name}"] = addr
        
        self.publish_data(data)
        
    def task_1s(self) -> None:
        """每秒执行一次的高频任务"""
        data = {}
        
        # 收集CPU温度
        if "cpu_temperature" in self.peripherals:
            cpu_temp = get_cpu_temperature()
            data["cpu_temperature"] = float(cpu_temp) if cpu_temp else None
        
        # 收集GPU温度
        if "gpu_temperature" in self.peripherals:
            gpu_temp = get_gpu_temperature()
            data["gpu_temperature"] = float(gpu_temp) if gpu_temp else None
        
        # 收集CPU使用率和频率
        if "cpu" in self.peripherals:
            data["cpu_percent"] = float(get_cpu_percent())
            
            for i, percent in enumerate(get_cpu_percent(percpu=True)):
                data[f"cpu_{i}_percent"] = float(percent)
            
            cpu_freq = get_cpu_freq()
            data["cpu_freq_current"] = float(cpu_freq.current)
            data["cpu_freq_min"] = float(cpu_freq.min)
            data["cpu_freq_max"] = float(cpu_freq.max)
        
        # 收集内存信息
        if "memory" in self.peripherals:
            memory = get_memory_info()
            data["memory_total"] = int(memory.total)
            data["memory_available"] = int(memory.available)
            data["memory_percent"] = float(memory.percent)
        
        # 收集网络速度
        if "network" in self.peripherals:
            net_speed = get_network_speed()
            data["network_upload"] = int(net_speed.upload)
            data["network_download"] = int(net_speed.download)
        
        # PWM风扇
        if self.pwm_fan:
            data["pwm_fan_speed"] = self.pwm_fan.get_speed()
            data["pwm_fan_state"] = self.pwm_fan.get_state()

        # 发布数据
        self.publish_data(data)
    
    def task_3s(self) -> None:
        """每3秒执行一次的中频任务"""
        data = {}
        
        # 收集IP地址
        if "ip_address" in self.peripherals:
            ips = get_ips()
            data["ips"] = ips
            for name, addr in ips.items():
                data[f"ip_{name}"] = addr
        
        # 收集网络连接类型
        if "network" in self.peripherals:
            net_type = get_network_connection_type()
            data["network_type"] = "&".join(net_type)
        
        # 发布数据
        self.publish_data(data)
    
    def task_5s(self) -> None:
        """每5秒执行一次的低频任务"""
        data = {}
        
        # 收集启动时间
        data["boot_time"] = float(get_boot_time())
        
        # 收集存储信息
        if 'storage' in self.peripherals:
            data['disk_list'] = get_disks()
            disks = get_disks_info(temperature=True)
            # data['disks'] = disks
            for disk_name in disks:
                disk = disks[disk_name]
                data[f'disk_{disk_name}_mounted'] = int(disk.mounted)
                data[f'disk_{disk_name}_total'] = int(disk.total)
                data[f'disk_{disk_name}_used'] = int(disk.used)
                data[f'disk_{disk_name}_free'] = int(disk.free)
                data[f'disk_{disk_name}_percent'] = float(disk.percent)
        
        # 发布数据
        self.publish_data(data)
    
    # ------------------------------
    # 节点运行与生命周期管理
    # ------------------------------

    def on_start(self) -> None:
        self.task_once()

    def on_stop(self) -> None:
        if self.power_button:
            self.power_button.stop()

    async def main(self) -> None:
        # 执行定时任务
        while True:
            self.task_1s_caller()
            self.task_3s_caller()
            self.task_5s_caller()
            await self.sleep(1)

