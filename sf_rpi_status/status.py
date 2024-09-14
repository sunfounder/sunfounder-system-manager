

def get_cpu_temperature():
    from psutil import sensors_temperatures
    return sensors_temperatures()['cpu_thermal'][0].current

def get_cpu_percent(percpu=False):
    from psutil import cpu_percent
    return cpu_percent(percpu=percpu)

class CPUFreq:
    def __init__(self, data):
        self._current = data.current
        self._min = data.min
        self._max = data.max

    def __repr__(self):
        return f'CPUFreq(current: {self.current} MHz, min: {self.min} MHz, max: {self.max} MHz)'

    def __str__(self):
        return f'CPUFreq(current: {self.current} MHz, min: {self.min} MHz, max: {self.max} MHz)'

    @property
    def current(self):
        return self._current
    
    @property
    def min(self):
        return self._min
    
    @property
    def max(self):
        return self._max

def get_cpu_freq():
    from psutil import cpu_freq
    return CPUFreq(cpu_freq())

def get_cpu_count():
    from psutil import cpu_count
    return cpu_count()

class MemoryInfo:
    def __init__(self, data):
        self._total = data.total
        self._available = data.available
        self._percent = data.percent
        self._used = data.used
        self._free = data.free

    def __repr__(self):
        return f'MemoryInfo(total: {self.total} B, available: {self.available} B, percent: {self.percent}%, used: {self.used} B, free: {self.free} B)'

    def __str__(self):
        return f'MemoryInfo(total: {self.total} B, available: {self.available} B, percent: {self.percent}%, used: {self.used} B, free: {self.free} B)'

    @property
    def total(self):
        return self._total
    
    @property
    def available(self):
        return self._available
    
    @property
    def percent(self):
        return self._percent
    
    @property
    def used(self):
        return self._total-self._available
    
    @property
    def free(self):
        return self._free

def get_memory_info():
    from psutil import virtual_memory
    return MemoryInfo(virtual_memory())

class DiskInfo:
    def __init__(self, total=0, used=0, free=0, percent=0, path=None, mounted=False):
        self._total = total
        self._used = used
        self._free = free
        self._percent = percent
        self._path = path
        self._mounted = mounted
    
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        from psutil._common import bytes2human
        if self.mounted:
            return f'Disk {self._path}: total: {bytes2human(self.total)}B, used: {bytes2human(self.used)}B, free: {bytes2human(self.free)}B, percent: {self.percent}%'
        else:
            return f'Disk {self._path} not mounted, total: {bytes2human(self.total)}B'

    @property
    def total(self):
        return self._total
    
    @property
    def used(self):
        return self._used
    
    @property
    def free(self):
        return self._free
    
    @property
    def percent(self):
        return self._percent

    @property
    def path(self):
        return self._path
    
    @property
    def mounted(self):
        return self._mounted

def get_disk_info(mountpoint='/'):
    from psutil import disk_usage
    disk_info = disk_usage(mountpoint)
    return DiskInfo(
        total=disk_info.total,
        used=disk_info.used,
        free=disk_info.free,
        percent=disk_info.percent,
        path='total',
        mounted=True,
    )

def get_disks():
    import subprocess
    disks = []
    output = subprocess.check_output(["lsblk", "-o", "NAME,TYPE", "-n", "-l"]).decode().strip().split('\n')
    
    for line in output:
        disk_name, disk_type = line.split()
        if disk_type == "disk":
            disks.append(disk_name)
    return disks

def get_disk_total(disk):
    import subprocess
    from .utils import human2bytes
    total = subprocess.check_output(f"lsblk -o NAME,TYPE,SIZE -n -l | grep {disk} | grep disk | awk '{{print $3}}'", shell=True).decode().strip()
    total = human2bytes(total)
    return total

def get_disks_info():
    from psutil import disk_usage
    import subprocess
    disk_info = {}
    disks = get_disks()
    
    for disk in disks:
        mountpoints = subprocess.check_output(f"lsblk -o NAME,TYPE,MOUNTPOINTS -n -l |grep {disk}|grep part|awk '{{print $3}}'", shell=True).decode().strip().split('\n')
        
        try:
            total = 0
            used = 0
            free = 0
            percent = 0
            if len(mountpoints) == 0 or mountpoints[0] == '':
                total = get_disk_total(disk)
                disk_info[disk] = DiskInfo(
                    total=total,
                    path=disk,
                    mounted=False
                )
            else:
                for mountpoint in mountpoints:
                    if mountpoint == '':
                        continue
                    usage = disk_usage(mountpoint)
                    total += usage.total
                    used += usage.used
                    free += usage.free
                if total == 0:
                    continue
                percent = used / total * 100
                percent = round(percent, 2)
                disk_info[disk] = DiskInfo(
                    total=total,
                    used=used,
                    free=free,
                    percent=percent,
                    path=disk,
                    mounted=True
                )
        except Exception as e:
            print(f"Failed to get disk information for {disk}: {str(e)}")
    
    return disk_info

def get_boot_time():
    from psutil import boot_time
    return boot_time()

def _get_ips():
    import psutil
    import socket
    IPs = {}

    try:
        NIC_devices = psutil.net_if_addrs()
        for name, NIC in NIC_devices.items():
            if name == 'lo':
                continue
            try:
                for af in NIC:
                    if af.family == socket.AF_INET: # 2:'IPV4'
                        IPs[name] = af.address
            except:
                continue
    except Exception as e:
        print(f"Failed to get ips: {str(e)}")
    
    return IPs

def get_ips():
    from . import ha_api
    ips = None
    if ha_api.is_homeassistant_addon():
        ips = ha_api.get_ips()
    else:
        ips = _get_ips()

    result = {}
    for key in ips:
        if ips[key] != '' and ips[key] != None:
            result[key] = ips[key]

    return result

def get_macs():
    from os import listdir
    MACs = {}
    NIC_devices = []
    NIC_devices = listdir('/sys/class/net/')
    for NIC in NIC_devices:
        if NIC == 'lo':
            continue
        try:
            with open('/sys/class/net/' + NIC + '/address', 'r') as f:
                MACs[NIC] = f.readline().strip()
        except:
            continue

    return MACs

net_io_counter = None
net_io_counter_time = None

def get_network_connection_type():
    from psutil import net_if_stats
    interfaces = net_if_stats()
    connection_type = []
    
    for interface, stats in interfaces.items():
        if stats.isup:
            if "eth" in interface or "enp" in interface or "ens" in interface:
                connection_type.append("Wired")
            if "wlan" in interface or "wlp" in interface or "wls" in interface:
                connection_type.append("Wireless")
    
    return connection_type

class NetworkSpeed:
    def __init__(self):
        self._upload = 0
        self._download = 0

    def __str__(self):
        return f'NetworkSpeed(upload: {self.upload} B/s, download: {self.download} B/s)'

    def set_upload(self, speed):
        self._upload = speed

    def set_download(self, speed):
        self._download = speed

    @property
    def upload(self):
        return self._upload
    
    @property
    def download(self):
        return self._download


def get_network_speed():
    from psutil import net_io_counters
    from time import time
    global net_io_counter, net_io_counter_time
    network_speed = NetworkSpeed()
    # 获取初始网络计数器信息
    current_net_io_counter = net_io_counters()
    current_net_io_counter_time = time()

    if net_io_counter is None:
        net_io_counter = current_net_io_counter
        net_io_counter_time = current_net_io_counter_time
        return network_speed

    # 计算速度差异
    bytes_sent = current_net_io_counter.bytes_sent - net_io_counter.bytes_sent
    bytes_recv = current_net_io_counter.bytes_recv - net_io_counter.bytes_recv
    interval = current_net_io_counter_time - net_io_counter_time

    # 计算速度（每秒字节数）
    upload_speed = bytes_sent / interval
    download_speed = bytes_recv / interval

    network_speed.set_upload(round(upload_speed))
    network_speed.set_download(round(download_speed))

    net_io_counter = current_net_io_counter
    net_io_counter_time = current_net_io_counter_time

    return network_speed

def shutdown():
    from . import ha_api
    if ha_api.is_homeassistant_addon():
        ha_api.shutdown()
    else:
        from os import system
        system('sudo shutdown -h now')
