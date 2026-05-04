import time

import psutil

_server_start_time = time.time()


def get_system_metrics() -> dict:
    return {
        "cpu_usage": psutil.cpu_percent(interval=None),
        "memory_usage": psutil.virtual_memory().percent,
        "uptime": round(time.time() - _server_start_time, 2),
    }
