import time
import json
import re
import win32com.client
from pathlib import Path

WHITELIST_FILE = "usb_whitelist.json"


def extract_vid_pid(device_id):
    match = re.search(r"VID_([0-9A-F]{4})&PID_([0-9A-F]{4})", device_id)
    if match:
        return match.group(1), match.group(2)
    return None, None


def load_whitelist():
    if Path(WHITELIST_FILE).exists():
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_current_usb_devices(wmi):
    devices = {}
    for dev in wmi.InstancesOf("Win32_PnPEntity"):
        if not dev.DeviceID.startswith("USB"):
            continue

        vid, pid = extract_vid_pid(dev.DeviceID)
        if not vid or not pid:
            continue

        key = f"{vid}:{pid}"
        devices[key] = {
            "vid": vid,
            "pid": pid,
            "name": dev.Name,
            "device_id": dev.DeviceID
        }
    return devices


def enroll_device():
    wmi = win32com.client.GetObject("winmgmts:")
    whitelist = load_whitelist()

    print("[INFO] USB whitelist enrollment started")
    print("[INFO] Connect the device you want to TRUST\n")

    before = get_current_usb_devices(wmi)

    while True:
        time.sleep(1)
        after = get_current_usb_devices(wmi)

        new_keys = set(after.keys()) - set(before.keys())
        if new_keys:
            for key in new_keys:
                dev = after[key]

                print("\n[NEW DEVICE DETECTED]")
                print(f"Name : {dev['name']}")
                print(f"VID  : {dev['vid']}")
                print(f"PID  : {dev['pid']}")

                answer = input("Add this device to whitelist? (yes/no): ").strip().lower()
                if answer == "yes":
                    whitelist.append({
                        "vid": dev["vid"],
                        "pid": dev["pid"],
                        "name": dev["name"]
                    })
                    save_whitelist(whitelist)
                    print("[OK] Device added to whitelist")

                else:
                    print("[INFO] Device ignored")

                return  # обучаем по одному устройству

        before = after


if __name__ == "__main__":
    enroll_device()
