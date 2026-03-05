import json
from pathlib import Path

WHITELIST_FILE = "usb_whitelist.json"
MIN_ALLOWED_DELTA = 0.005  # сек


def load_whitelist():
    if not Path(WHITELIST_FILE).exists():
        print("[WARN] Whitelist file not found, using empty whitelist")
        return set()

    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    wl = set()
    for item in data:
        wl.add((item["vid"].upper(), item["pid"].upper()))

    print(f"[INFO] Loaded {len(wl)} trusted USB device(s)")
    return wl
