
import os

def is_homeassistant_addon():
    return 'SUPERVISOR_TOKEN' in os.environ

base_url="http://supervisor/"
token = None
if is_homeassistant_addon():
    token = os.environ['SUPERVISOR_TOKEN']
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

def get(endpoint):
    from requests import get
    url = f"{base_url}{endpoint}"
    r = get(url, headers=headers)
    return r.json()

def set(endpoint, data=None):
    from requests import post
    url = f"{base_url}{endpoint}"
    post(url, headers=headers)

def get_ips():
    ips = {}
    data = get("network/info")
    interfaces = data["data"]["interfaces"]
    for interface in interfaces:
        name = interface['interface']
        ip = interface['ipv4']['address']
        if len(ip) == 0:
            continue
        ip = ip[0]
        if ip == '':
            continue
        if "/" in ip:
            ip = ip.split("/")[0]
        ips[name] = ip
    return ips

def get_network_connection_type():
    connection_type_map = {
        "ethernet": "Wired",
        "wireless": "Wireless",
    }
    connection_type = []
    data = get("network/info")
    interfaces = data["data"]["interfaces"]
    for interface in interfaces:
        if interface['connected']:
            connection_type.append(connection_type_map[interface['type']])
    return connection_type

def shutdown():
    '''shutdown homeassistant host'''
    set("host/shutdown")
