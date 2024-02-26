from sf_rpi_status import *

def main():
    print(f'CPU temperature: {get_cpu_temperature()} °C')
    print(f'CPU percent: {get_cpu_percent()} %')
    print(f'CPU percent(per CPU): {get_cpu_percent(True)}')
    print(f'CPU frequency: {get_cpu_freq()}')
    print(f'CPU count: {get_cpu_count()}')
    print(f'Memory info: {get_memory_info()}')
    print(f'Disk info: {get_disk_info()}')
    print(f'Disk info(per disk): {get_disks_info()}')
    print(f'Boot time: {get_boot_time()}')
    print(f'IP addresses: {get_ips()}')
    print(f'MAC addresses: {get_macs()}')
    print(f'Network connection type: {get_network_connection_type()}')
    print(f'Network speed: {get_network_speed()}')


if __name__ == '__main__':
    main()