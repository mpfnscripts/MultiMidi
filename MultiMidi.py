import mido
from pynput.keyboard import Controller, Key
from threading import Thread
import customtkinter as ctk
from tkinter import (
    Text, Scrollbar, Frame, filedialog,
    END, RIGHT, Y, BOTH
)
import time
import keyboard as kb_lib
import json
import os
import ctypes
import sys

# --- Config ---
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {
        "dark_mode": False,
        "hotkey_stop": "f1",
        "hotkey_pause": "f2"
    }

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

keyboard = Controller()
stop_playing = False
paused = False
midi_path = None

button_color = None
button_hover = None

hotkey_window = None

# Declare these globally so apply_theme can check if they exist
stop_hotkey_entry = None
pause_hotkey_entry = None
save_hotkeys_button = None
hotkey_title_bar = None
hotkey_title_label = None
hotkey_close_button = None

# Global flag to stop MIDI listener thread
stop_program = False
midi_listener_thread = None
stop_listener_thread = None

def apply_theme():
    global button_color, button_hover

    if config["dark_mode"]:
        ctk.set_appearance_mode("dark")
        bg_color = "#2b2b2b"
        fg_color = "white"
        button_color = "#444444"
        button_hover = "#555555"
        scrollbar_trough = "#2b2b2b"
        scrollbar_bg = "#3a3a3a"
        console_bg = "#222222"
        console_fg = "white"
        label_text_color = "white"
    else:
        ctk.set_appearance_mode("light")
        bg_color = "SystemButtonFace"
        fg_color = "black"
        button_color = "#dddddd"
        button_hover = "#cccccc"
        scrollbar_trough = "#f0f0f0"
        scrollbar_bg = "#d9d9d9"
        console_bg = "white"
        console_fg = "black"
        label_text_color = "black"

    # Main window theme
    root.configure(bg=bg_color)
    title_bar.configure(bg=bg_color)
    title_label.configure(text_color=label_text_color, bg_color=bg_color)
    close_button.configure(fg_color="transparent", text_color=fg_color, hover_color="#cc0000")
    content_frame.configure(bg=bg_color)

    for widget in content_frame.winfo_children():
        if isinstance(widget, ctk.CTkLabel):
            if widget == stop_label:
                continue
            widget.configure(text_color=label_text_color)

    debug_console.configure(bg=console_bg, fg=console_fg, insertbackground=console_fg)
    scrollbar.configure(bg=scrollbar_trough, troughcolor=scrollbar_trough)

    themable_buttons = [
        refresh_button, select_button, toggle_dark_button,
        quit_button, toggle_extended_checkbox, toggle_hotkey_settings_button
    ]
    if save_hotkeys_button:
        themable_buttons.append(save_hotkeys_button)

    for btn in themable_buttons:
        btn.configure(fg_color=button_color, hover_color=button_hover, text_color=label_text_color)

    # Hotkey window theme if open
    if hotkey_window and hotkey_window.winfo_exists():
        hotkey_window.configure(bg=bg_color)
        if hotkey_title_bar:
            hotkey_title_bar.configure(bg=bg_color)
        if hotkey_title_label:
            hotkey_title_label.configure(text_color=label_text_color, bg_color=bg_color)
        if hotkey_close_button:
            hotkey_close_button.configure(fg_color="transparent", text_color=fg_color, hover_color="#cc0000")
        if stop_hotkey_entry:
            stop_hotkey_entry.configure(bg=button_color, fg=label_text_color, insertbackground=label_text_color, relief="flat")
        if pause_hotkey_entry:
            pause_hotkey_entry.configure(bg=button_color, fg=label_text_color, insertbackground=label_text_color, relief="flat")
        if save_hotkeys_button:
            save_hotkeys_button.configure(fg_color=button_color, hover_color=button_hover, text_color=label_text_color)

def toggle_dark_mode():
    config["dark_mode"] = not config["dark_mode"]
    save_config(config)
    apply_theme()

virtual_piano_keys = [
    '1', '!', '2', '@', '3',
    '4', '$', '5', '%', '6', '^', '7',
    '8', '*', '9', '(', '0',
    'q', 'Q', 'w', 'W', 'e', 'E', 'r',
    't', 'T', 'y', 'Y', 'u',
    'i', 'I', 'o', 'O', 'p', 'P', 'a',
    's', 'S', 'd', 'D', 'f',
    'g', 'G', 'h', 'H', 'j', 'J', 'k',
    'l', 'L', 'z', 'Z', 'x',
    'c', 'C', 'v', 'V', 'b', 'B', 'n',
    'm'
]
base_midi_note = 48

def debug_print(message):
    debug_console.insert(END, message + "\n")
    debug_console.see(END)
    print(message)

def get_key_for_midi(note):
    index = note - base_midi_note
    if 0 <= index < len(virtual_piano_keys):
        return virtual_piano_keys[index]
    return None

def press_vp_key(key):
    if key.isupper() or (not key.isalpha() and not key.isdigit()):
        keyboard.press(Key.shift)
        keyboard.press(key.lower() if key.isalpha() else key)
        keyboard.release(key.lower() if key.isalpha() else key)
        keyboard.release(Key.shift)
    else:
        keyboard.press(key)
        keyboard.release(key)

def play_midi_file():
    global stop_playing, paused
    stop_playing = False
    paused = False

    try:
        midi_file = mido.MidiFile(midi_path)
    except Exception as e:
        debug_print(f"❌ Could not load MIDI file: {e}")
        return

    debug_print(f"Playing {midi_path}...")
    debug_print(f"Press {config['hotkey_stop'].upper()} to stop playback.")
    debug_print(f"Press {config['hotkey_pause'].upper()} to pause/resume playback.")

    debounce_pause = False

    for msg in midi_file.play():
        if stop_playing:
            break

        if kb_lib.is_pressed(config["hotkey_stop"]):
            debug_print(f"Stopping playback by {config['hotkey_stop'].upper()} press...")
            break

        if kb_lib.is_pressed(config["hotkey_pause"]):
            if not debounce_pause:
                paused = not paused
                debug_print(f"{'Paused' if paused else 'Resumed'} playback by {config['hotkey_pause'].upper()} press.")
                debounce_pause = True
            time.sleep(0.1)
        else:
            debounce_pause = False

        if paused:
            time.sleep(0.1)
            continue

        if msg.type == 'note_on' and msg.velocity > 0:
            key = get_key_for_midi(msg.note)
            if key:
                press_vp_key(key)
        time.sleep(0.001)

    debug_print("Playback finished.")

def midi_listener(selected_device):
    global stop_program
    stop_program = False

    ports = mido.get_input_names()
    if selected_device not in ports:
        debug_print("❌ Error: Selected device not found.")
        return

    try:
        debug_print(f"🎹 Listening to MIDI device: {selected_device}")
        debug_print(f"Press {config['hotkey_stop'].upper()} to stop listening.")

        with mido.open_input(selected_device) as inport:
            for msg in inport:
                if stop_program:
                    break
                if msg.type == 'note_on' and msg.velocity > 0:
                    key = get_key_for_midi(msg.note)
                    if key:
                        press_vp_key(key)

        debug_print("Stopped live MIDI listener.")

    except Exception as e:
        debug_print(f"❌ Could not open MIDI device: {e}")

def stop_listener():
    global stop_program
    while True:
        if kb_lib.is_pressed(config["hotkey_stop"]):
            stop_program = True
            break
        time.sleep(0.1)

def select_file_or_device():
    update_device_list()
    if extended_mode.get() == 0:
        start_normal_mode()
    else:
        start_extended_mode()

def start_normal_mode():
    global midi_path
    midi_path = filedialog.askopenfilename(
        title="Select a MIDI file",
        filetypes=[("MIDI files", "*.mid *.midi")]
    )
    if midi_path:
        play_midi_file()

def start_extended_mode():
    global midi_listener_thread, stop_listener_thread
    selected_device = midi_device_var.get()
    if not selected_device or selected_device == "No MIDI devices found":
        debug_print("❌ Please select a valid MIDI device.")
        return

    if midi_listener_thread is None or not midi_listener_thread.is_alive():
        midi_listener_thread = Thread(target=midi_listener, args=(selected_device,), daemon=True)
        midi_listener_thread.start()
    if stop_listener_thread is None or not stop_listener_thread.is_alive():
        stop_listener_thread = Thread(target=stop_listener, daemon=True)
        stop_listener_thread.start()

def update_device_list():
    devices = mido.get_input_names()
    if not devices:
        devices = ["No MIDI devices found"]
    midi_device_var.set(devices[0])
    midi_device_menu.configure(values=devices)

def save_hotkeys():
    global save_hotkeys_button
    new_stop = stop_hotkey_entry.get().strip().lower()
    new_pause = pause_hotkey_entry.get().strip().lower()

    if not new_stop:
        debug_print("❌ Stop hotkey cannot be empty!")
        return
    if not new_pause:
        debug_print("❌ Pause hotkey cannot be empty!")
        return
    if new_stop == new_pause:
        debug_print("❌ Stop and Pause hotkeys cannot be the same!")
        return

    config["hotkey_stop"] = new_stop
    config["hotkey_pause"] = new_pause
    save_config(config)
    debug_print(f"✅ Hotkeys saved! Stop: {new_stop.upper()}, Pause: {new_pause.upper()}")

def toggle_hotkey_window():
    global hotkey_window
    global stop_hotkey_entry, pause_hotkey_entry, save_hotkeys_button
    global hotkey_title_bar, hotkey_title_label, hotkey_close_button

    if hotkey_window and hotkey_window.winfo_exists():
        hotkey_window.destroy()
        hotkey_window = None
        stop_hotkey_entry = None
        pause_hotkey_entry = None
        save_hotkeys_button = None
        hotkey_title_bar = None
        hotkey_title_label = None
        hotkey_close_button = None
        return

    hotkey_window = ctk.CTkToplevel(root)
    hotkey_window.geometry("400x220")
    hotkey_window.resizable(False, False)
    hotkey_window.title("Hotkey Settings")
    hotkey_window.overrideredirect(True)

    # Custom title bar
    hotkey_title_bar = ctk.CTkFrame(hotkey_window, height=30)
    hotkey_title_bar.pack(fill="x")

    hotkey_title_label = ctk.CTkLabel(hotkey_title_bar, text="Hotkey Settings", font=("Arial", 12, "bold"))
    hotkey_title_label.pack(side="left", padx=10)

    def close_hotkey():
        hotkey_window.destroy()

    hotkey_close_button = ctk.CTkButton(hotkey_title_bar, text="X", width=30, height=20, corner_radius=8,
                                        fg_color="transparent",
                                        hover_color="#cc0000",
                                        command=close_hotkey)
    hotkey_close_button.pack(side="right", padx=5)

    def start_move(event):
        hotkey_window.x = event.x
        hotkey_window.y = event.y

    def do_move(event):
        deltax = event.x - hotkey_window.x
        deltay = event.y - hotkey_window.y
        x = hotkey_window.winfo_x() + deltax
        y = hotkey_window.winfo_y() + deltay
        hotkey_window.geometry(f"+{x}+{y}")

    hotkey_title_bar.bind("<Button-1>", start_move)
    hotkey_title_bar.bind("<B1-Motion>", do_move)

    hotkey_content = ctk.CTkFrame(hotkey_window)
    hotkey_content.pack(fill=BOTH, expand=True, padx=10, pady=(10, 10))

    # Frame for inputs and button horizontally
    inputs_frame = ctk.CTkFrame(hotkey_content)
    inputs_frame.pack(fill="x", expand=True)

    # Left side labels and entries stacked vertically
    labels_entries_frame = ctk.CTkFrame(inputs_frame)
    labels_entries_frame.pack(side="left", fill="both", expand=True)

    stop_label = ctk.CTkLabel(labels_entries_frame, text="Stop Playback Hotkey:")
    stop_label.pack(anchor="w", pady=(0,5))
    stop_hotkey_entry = ctk.CTkEntry(labels_entries_frame, width=120)
    stop_hotkey_entry.pack(pady=(0,10))
    stop_hotkey_entry.insert(0, config.get("hotkey_stop", "f1"))

    pause_label = ctk.CTkLabel(labels_entries_frame, text="Pause Playback Hotkey:")
    pause_label.pack(anchor="w", pady=(0,5))
    pause_hotkey_entry = ctk.CTkEntry(labels_entries_frame, width=120)
    pause_hotkey_entry.pack(pady=(0,10))
    pause_hotkey_entry.insert(0, config.get("hotkey_pause", "f2"))

    # Save button on right side vertically centered
    save_hotkeys_button = ctk.CTkButton(inputs_frame, text="Save Hotkeys", command=save_hotkeys, corner_radius=10, width=100)
    save_hotkeys_button.pack(side="right", padx=10, pady=20)

    apply_theme()


def start_move_main(event):
    root.x = event.x
    root.y = event.y

def do_move_main(event):
    deltax = event.x - root.x
    deltay = event.y - root.y
    x = root.winfo_x() + deltax
    y = root.winfo_y() + deltay
    root.geometry(f"+{x}+{y}")

def stop_midi_listener():
    global stop_program
    if not stop_program:
        debug_print("Stopping MIDI device listener because extended mode was disabled.")
    stop_program = True

# --- Main Window ---
root = ctk.CTk()

try:
    root.iconbitmap("Logo.ico")
except Exception as e:
    print("iconbitmap failed:", e)

root.overrideredirect(True)

if sys.platform == "win32":
    hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
    style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -20)
    style = style | 0x00040000  # WS_EX_APPWINDOW
    ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, style)
    style2 = ctypes.windll.user32.GetWindowLongPtrW(hwnd, -20)
    style2 = style2 & ~0x00000080  # WS_EX_TOOLWINDOW
    ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, style2)
    ctypes.windll.user32.ShowWindow(hwnd, 5)

root.title("MIDI to Virtual Piano")

title_bar = Frame(root, relief="raised", bd=0)
title_label = ctk.CTkLabel(title_bar, text="MIDI to Virtual Piano", font=("Arial", 12, "bold"))
close_button = ctk.CTkButton(title_bar, text="X", width=30, height=20, corner_radius=8,
                             fg_color="transparent",
                             hover_color="#cc0000",
                             command=root.destroy)

title_bar.pack(fill="x")
title_label.pack(side="left", padx=5)
close_button.pack(side="right", padx=5)

title_bar.bind("<Button-1>", start_move_main)
title_bar.bind("<B1-Motion>", do_move_main)

content_frame = Frame(root)
content_frame.pack(fill=BOTH, expand=True)

extended_mode = ctk.IntVar(value=0)

stop_label = ctk.CTkLabel(content_frame, text="Press your configured stop/pause hotkeys during playback", text_color="red", font=("Arial", 9, "italic"))
stop_label.pack(pady=(5,0))

midi_device_var = ctk.StringVar()
midi_device_menu = ctk.CTkOptionMenu(content_frame, variable=midi_device_var, values=[])
midi_device_menu.pack(pady=5)

refresh_button = ctk.CTkButton(content_frame, text="Refresh Device List", command=update_device_list, corner_radius=10)
refresh_button.pack(pady=2)

select_button = ctk.CTkButton(content_frame, text="Select MIDI File", command=select_file_or_device, corner_radius=10)
select_button.pack(pady=2)

def update_select_button_text(*args):
    if extended_mode.get() == 1:
        select_button.configure(text="Start MIDI Device")
    else:
        select_button.configure(text="Select MIDI File")

def on_extended_mode_changed(*args):
    update_select_button_text()
    if extended_mode.get() == 0:
        stop_midi_listener()

extended_mode.trace_add("write", on_extended_mode_changed)
update_select_button_text()

toggle_extended_checkbox = ctk.CTkCheckBox(content_frame, text="Toggle Extended Mode (MIDI Device)", variable=extended_mode, corner_radius=10)
toggle_extended_checkbox.pack(pady=2)

toggle_dark_button = ctk.CTkButton(content_frame, text="Toggle Dark Mode", command=toggle_dark_mode, corner_radius=10)
toggle_dark_button.pack(pady=2)

toggle_hotkey_settings_button = ctk.CTkButton(content_frame, text="Hotkey Settings", command=toggle_hotkey_window, corner_radius=10)
toggle_hotkey_settings_button.pack(pady=2)

quit_button = ctk.CTkButton(content_frame, text="Quit", command=root.destroy, corner_radius=10)
quit_button.pack(pady=2)

debug_console = Text(content_frame, height=10, wrap="word")
scrollbar = Scrollbar(content_frame, command=debug_console.yview)
debug_console.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side=RIGHT, fill=Y)
debug_console.pack(fill=BOTH, expand=True)

update_device_list()
apply_theme()

root.geometry("520x510")
root.mainloop()
