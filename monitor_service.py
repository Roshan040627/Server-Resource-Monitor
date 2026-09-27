import psutil  # type: ignore
import socket
import platform
import time
from datetime import datetime

from dashboard_logger import generate_dashboard_html
from email_alert import send_email_alert
from config import RAM_WARNING_LIMIT, CHECK_INTERVAL_SECONDS


last_dashboard_ram_percent = None
RAM_INCREASE_TRIGGER_PERCENT = 5


def get_ip_address():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception:
        return "Unknown"


def get_processes():
    processes = []
    process_list = []

    for proc in psutil.process_iter(
        ["pid", "username", "name", "cmdline", "memory_info", "status"]
    ):
        try:
            proc.cpu_percent(interval=None)
            process_list.append(proc)
        except Exception:
            continue

    time.sleep(2)

    for proc in process_list:
        try:
            info = proc.info

            cpu = proc.cpu_percent(interval=None)
            cpu = min(cpu, 100.0)

            memory_mb = info["memory_info"].rss / (1024 * 1024)

            cmdline_list = info.get("cmdline") or []
            cmdline = " ".join(cmdline_list)

            if not cmdline:
                cmdline = info["name"] or "Unknown"

            processes.append({
                "pid": info["pid"],
                "username": info.get("username", "Unknown"),
                "name": info["name"] or "Unknown",
                "program": cmdline,
                "cpu": round(cpu, 2),
                "memory_mb": round(memory_mb, 2),
                "status": info["status"]
            })

        except Exception:
            continue

    return processes


def get_dashboard_data():
    processes = get_processes()

    top_memory = sorted(
        processes,
        key=lambda x: x["memory_mb"],
        reverse=True
    )[:10]

    top_cpu = sorted(
        processes,
        key=lambda x: x["cpu"],
        reverse=True
    )[:10]

    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=2)

    running = len([p for p in processes if p["status"] == "running"])
    sleeping = len(processes) - running

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "ip_address": get_ip_address(),
        "os": platform.platform(),
        "total_processes": len(processes),
        "running": running,
        "sleeping": sleeping,
        "cpu_percent": round(cpu_percent, 2),
        "cpu_idle_percent": round(100 - cpu_percent, 2),
        "ram_percent": round(memory.percent, 2),
        "ram_free_percent": round(100 - memory.percent, 2),
        "ram_used_gb": round(memory.used / (1024 ** 3), 2),
        "ram_total_gb": round(memory.total / (1024 ** 3), 2),
        "top_memory": top_memory,
        "top_cpu": top_cpu
    }


def main():
    global last_dashboard_ram_percent

    print("Server Resource Monitor started.")
    print(f"Dashboard will only be created when RAM is {RAM_WARNING_LIMIT}% or above.")

    while True:
        data = get_dashboard_data()
        ram_percent = data["ram_percent"]

        checked_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[{checked_time}] RAM checked: {ram_percent}%")

        if ram_percent < RAM_WARNING_LIMIT:
            last_dashboard_ram_percent = None
            time.sleep(CHECK_INTERVAL_SECONDS)
            continue

        should_create_dashboard = False

        if last_dashboard_ram_percent is None:
            should_create_dashboard = True

        elif ram_percent >= (
            last_dashboard_ram_percent + RAM_INCREASE_TRIGGER_PERCENT
        ):
            should_create_dashboard = True

        if should_create_dashboard:
            print(
                f"[{checked_time}] RAM exceeded warning limit "
                f"({RAM_WARNING_LIMIT}%). Creating dashboard..."
            )

            dashboard_html, chart_images = generate_dashboard_html(data)

            email_sent = send_email_alert(
                data,
                dashboard_html,
                chart_images
            )

            last_dashboard_ram_percent = ram_percent

            print(f"[{checked_time}] Dashboard created successfully.")

            if email_sent:
                print(f"[{checked_time}] Email alert sent successfully.")
            else:
                print(f"[{checked_time}] Email alert failed.")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()