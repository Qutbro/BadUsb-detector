import threading
import keyboard

_keyboard_blocked = False
_lock = threading.Lock()

def release_all_modifiers():
    # Windows / Ctrl / Alt / Shift
    keyboard.release('left windows')
    keyboard.release('right windows')
    keyboard.release('ctrl')
    keyboard.release('alt')
    keyboard.release('shift')

def _keyboard_hook(event):
    with _lock:
        if _keyboard_blocked:
            return False
    return True


def install_keyboard_blocker():
    keyboard.hook(_keyboard_hook, suppress=True)
    print("[INFO] Keyboard hook installed")


def enable_keyboard_block():
    global _keyboard_blocked
    with _lock:
        _keyboard_blocked = True
    print("[ACTION] Keyboard input BLOCKED")


def disable_keyboard_block():
    global _keyboard_blocked
    with _lock:
        _keyboard_blocked = False
    print("[ACTION] Keyboard input UNBLOCKED")
