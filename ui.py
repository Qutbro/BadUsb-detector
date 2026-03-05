import tkinter as tk
from tkinter import ttk
import queue

on_threshold_changed = None  # будет установлен из main.py
import subprocess
import sys
import os

import time
import threading
from pynput import keyboard


from tkinter import simpledialog, messagebox
# ==================================================
# UI STATE
# ==================================================

log_queue = queue.Queue()
ADMIN_PASSWORD ='1234'
# ==================================================
# UI FUNCTIONS (используются из main.py)
# ==================================================

def log(message: str):
    """Добавить сообщение в консоль"""
    log_queue.put(message)


def set_status_active():
    status_label.config(text="🟢 Protection active")


def set_status_alert():
    status_label.config(text="🔴 Suspicious input detected")


def set_status_blocked():
    status_label.config(text="⛔ Keyboard input blocked")

from tkinter import messagebox

def show_badusb_alert(device=None):
    alert = tk.Toplevel(root)
    alert.title("SECURITY ALERT — USB Input Guard")
    alert.geometry("500x280")
    alert.resizable(False, False)

    # делаем окно модальным (его нельзя игнорировать)
    alert.transient(root)
    alert.grab_set()

    # запрет закрытия по кресту
    alert.protocol("WM_DELETE_WINDOW", lambda: None)

    ttk.Label(
        alert,
        text="⚠️ POSSIBLE BADUSB DETECTED!",
        font=("Segoe UI", 12, "bold"),
        foreground="red"
    ).pack(pady=(15, 5))

    msg = (
        "Automated keyboard behavior detected.\n"
        "Keyboard input has been temporarily BLOCKED.\n\n"
        "Remove the suspicious USB device to restore input.\n"
    )

    if device:
        msg += f"\nDevice: VID={device[0]} PID={device[1]}"

    ttk.Label(alert, text=msg, justify="center").pack(pady=10)

    ttk.Label(alert, text="Enter administrator password to dismiss:").pack(pady=5)

    password_var = tk.StringVar()
    entry = ttk.Entry(alert, textvariable=password_var, show="*")
    entry.pack(pady=5)
    entry.focus()

    def check_password(event=None):
        if password_var.get() == ADMIN_PASSWORD:
            alert.grab_release()
            alert.destroy()
            log("[SECURITY] Alert dismissed by administrator")
        else:
            messagebox.showerror("Access denied", "Incorrect password")

    ttk.Button(alert, text="Confirm", command=check_password).pack(pady=10)

    # разрешаем Enter для подтверждения пароля
    alert.bind("<Return>", check_password)

def require_admin_password(on_success):
    """
    Универсальное окно запроса пароля.
    on_success — функция, которая выполнится ТОЛЬКО если пароль верный.
    """

    win = tk.Toplevel(root)
    win.title("Administrator confirmation")
    win.geometry("420x200")
    win.resizable(False, False)

    win.transient(root)
    win.grab_set()
    win.protocol("WM_DELETE_WINDOW", lambda: None)

    ttk.Label(
        win,
        text="Enter administrator password to continue",
        font=("Segoe UI", 10, "bold")
    ).pack(pady=(20, 5))

    password_var = tk.StringVar()
    entry = ttk.Entry(win, textvariable=password_var, show="*")
    entry.pack(pady=10)
    entry.focus()

    def check(event=None):
        if password_var.get() == ADMIN_PASSWORD:
            win.grab_release()
            win.destroy()
            log("[SECURITY] Admin confirmed action")
            on_success()      # <-- ВАЖНО: выполняем действие
        else:
            messagebox.showerror("Access denied", "Incorrect password")

    ttk.Button(win, text="Confirm", command=check).pack(pady=10)
    win.bind("<Return>", check)


# ==================================================
# BUTTON CALLBACKS (UI only)
# ==================================================

def _clear_log_now():
    console.delete("1.0", "end")
    log("[UI] Log cleared by administrator")

def clear_log():
    require_admin_password(_clear_log_now)


def set_typing_threshold():
    value = simpledialog.askfloat(
        title="Typing speed threshold",
        prompt="Enter minimal allowed delay between keystrokes (seconds):\n"
               "Recommended: 0.005 – 0.02",
        minvalue=0.0001,
        maxvalue=1.0
    )

    if value is None:
        log("[UI] Typing speed threshold setup canceled")
        return

    if on_threshold_changed:
        on_threshold_changed(value)

    log(f"[UI] Typing speed threshold set to {value:.6f} s")
    status_label.config(
        text=f"🟢 Protection active | Threshold: {value:.6f} s"
    )


def test_typing_speed():
    n = simpledialog.askinteger(
        "Typing speed test",
        "How many keystrokes to measure? (50–1000)",
        minvalue=50,
        maxvalue=1000
    )

    if not n:
        log("[TEST] Typing test canceled")
        return

    log(f"[TEST] Starting typing test for {n} keystrokes")
    log("[TEST] You may type anywhere — in any application")

    stats = {
        "last_time": None,
        "deltas": [],
        "count": 0
    }

    def on_press(key):
        now = time.perf_counter()

        if stats["last_time"] is not None:
            stats["deltas"].append(now - stats["last_time"])

        stats["last_time"] = now
        stats["count"] += 1

        # когда набрали нужное количество нажатий — завершаем тест
        if stats["count"] >= n:
            return False  # останавливает слушатель

    def run_test():
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

        # считаем результаты
        if not stats["deltas"]:
            messagebox.showwarning(
                "Typing test",
                "Not enough data collected."
            )
            return

        avg = sum(stats["deltas"]) / len(stats["deltas"])
        min_delta = min(stats["deltas"])
        recommended = min_delta / 2

        result = (
            f"Typing test finished!\n\n"
            f"Keystrokes measured: {stats['count']}\n"
            f"Average interval: {avg:.6f} s\n"
            f"Minimal interval: {min_delta:.6f} s\n"
            f"Recommended threshold: {recommended:.6f} s"
        )

        messagebox.showinfo("Typing test result", result)

        log("[TEST] Typing test completed")
        log(f"[TEST] avg={avg:.6f} | min={min_delta:.6f} | rec={recommended:.6f}")

    # запускаем тест В ОТДЕЛЬНОМ ПОТОКЕ, чтобы не заморозить GUI
    threading.Thread(target=run_test, daemon=True).start()




def add_device_to_whitelist():
    log("[WHITELIST] Launching whitelist enrollment tool...")

    script_path = os.path.join(
        os.path.dirname(__file__),
        "whitelist_enroll.py"
    )

    try:
        subprocess.Popen(
            [sys.executable, script_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        log("[WHITELIST] Enrollment tool started in new window")
    except Exception as e:
        log(f"[ERROR] Failed to start enrollment tool: {e}")


# ==================================================
# TKINTER WINDOW
# ==================================================

root = tk.Tk()
root.title("USB Input Guard")
root.geometry("900x500")
root.resizable(False, False)

# ================== STATUS ==================

status_label = ttk.Label(
    root,
    text="🟢 Protection active",
    padding=10,
    font=("Segoe UI", 10, "bold")
)
status_label.pack(fill="x")

# ================== MAIN AREA ==================

main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

# ---------- CONSOLE ----------

console_frame = ttk.Frame(main_frame)
console_frame.pack(side="left", fill="both", expand=True)

ttk.Label(console_frame, text="Event log").pack(anchor="w")

console = tk.Text(
    console_frame,
    height=25,
    width=60,
    state="normal",
    bg="#0f172a",
    fg="#e5e7eb",
    insertbackground="white"
)
console.pack(fill="both", expand=True)

console.insert("end", "[INFO] Application started\n")

# ---------- CONTROLS ----------

control_frame = ttk.Frame(main_frame, padding=(20, 0))
control_frame.pack(side="right", fill="y")

ttk.Label(
    control_frame,
    text="Controls",
    font=("Segoe UI", 10, "bold")
).pack(anchor="w", pady=(0, 10))

btn_set_delta = ttk.Button(
    control_frame,
    text="Set typing speed threshold",
    command=set_typing_threshold
)
btn_set_delta.pack(fill="x", pady=5)

btn_test_delta = ttk.Button(
    control_frame,
    text="Test my typing speed",
    command=test_typing_speed
)
btn_test_delta.pack(fill="x", pady=5)

btn_add_whitelist = ttk.Button(
    control_frame,
    text="Add connected device to trusted",
    command=add_device_to_whitelist
)
btn_add_whitelist.pack(fill="x", pady=5)

btn_clear_log = ttk.Button(
    control_frame,
    text="Clear log",
    command=clear_log
)
btn_clear_log.pack(fill="x", pady=5)

# ================== FOOTER ==================

footer = ttk.Label(
    root,
    text="The system monitors USB input behavior and blocks automated attacks.",
    padding=10,
    foreground="gray"
)
footer.pack(fill="x")

# ==================================================
# LOG QUEUE POLLING
# ==================================================

def poll_log_queue():
    while not log_queue.empty():
        msg = log_queue.get()
        console.insert("end", msg + "\n")
        console.see("end")

        # простая реакция статуса
        if "BLOCKED" in msg:
            set_status_blocked()
        elif "BadUSB" in msg or "Suspicious" in msg:
            set_status_alert()
        elif "UNBLOCKED" in msg:
            set_status_active()

    root.after(100, poll_log_queue)


# ==================================================
# START UI
# ==================================================

def start_ui():
    poll_log_queue()
    root.mainloop()
