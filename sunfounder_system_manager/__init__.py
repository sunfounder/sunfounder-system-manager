from .service_node import create_luancher
from .system_manager import SystemManager

main = create_luancher(SystemManager, "system_manager", "SunFounder System manager")
