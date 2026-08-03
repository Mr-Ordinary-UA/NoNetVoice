import queue
import json
import threading
import time
import os
import sys
import platform
import tkinter as tk
from tkinter import ttk
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import keyboard

os_name = platform.system()

if os_name == "Windows":
    import ctypes
    import winsound
    VK_RMENU = 0xA5

def play_beep(freq, duration):
    if os_name == "Windows":
        winsound.Beep(freq, duration)
    else:
        sys.stdout.write('\a')
        sys.stdout.flush()

def is_right_alt_pressed():
    if os_name == "Windows":
        return (ctypes.windll.user32.GetAsyncKeyState(VK_RMENU) & 0x8000) != 0
    else:
        return keyboard.is_pressed('right alt')

current_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(current_dir, "models")

if not os.path.exists(models_dir):
    os.makedirs(models_dir)
    sys.exit()

loaded_models = {}
for item in os.listdir(models_dir):
    item_path = os.path.join(models_dir, item)
    if os.path.isdir(item_path):
        if "am" in os.listdir(item_path) and "conf" in os.listdir(item_path):
            try:
                loaded_models[item] = Model(item_path)
            except Exception:
                pass

if not loaded_models:
    sys.exit()

model_names = list(loaded_models.keys())
current_model_idx = 0
current_model_name = model_names[current_model_idx]
current_model = loaded_models[current_model_name]
is_listening = False
language_changed = False
q = queue.Queue()
popup_is_open = False
show_popup = True
visual_feedback = False

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() - 40 
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.attributes('-topmost', True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def show_osd(text):
    osd = tk.Toplevel(root)
    osd.wm_overrideredirect(True)
    osd.attributes('-topmost', True)
    
    screen_width = osd.winfo_screenwidth()
    screen_height = osd.winfo_screenheight()
    x = int(screen_width / 2 - 100)
    y = int(screen_height - 150)
    
    osd.geometry(f"+{x}+{y}")
    label = tk.Label(osd, text=text, font=("Arial", 12), bg="black", fg="white", padx=10, pady=5)
    label.pack()
    osd.after(1500, osd.destroy)

def popup_selector():
    global popup_is_open, show_popup
    if popup_is_open:
        return
    popup_is_open = True
    
    top = tk.Toplevel(root)
    top.title("Language")
    
    window_width = 200
    window_height = 150
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    bottom_y = int(screen_height - window_height - 60)
    
    top.geometry(f'{window_width}x{window_height}+{center_x}+{bottom_y}')
    top.attributes('-topmost', True)

    def on_close():
        global popup_is_open
        popup_is_open = False
        top.destroy()

    top.protocol("WM_DELETE_WINDOW", on_close)

    label = ttk.Label(top, text="Select language package:")
    label.pack(pady=5)

    combo = ttk.Combobox(top, values=model_names, state="readonly")
    combo.set(current_model_name)
    combo.pack(pady=5)

    def on_select(event):
        global current_model, current_model_name, current_model_idx, language_changed, popup_is_open
        selected = combo.get()
        if selected in loaded_models and selected != current_model_name:
            current_model_name = selected
            current_model_idx = model_names.index(selected)
            current_model = loaded_models[selected]
            language_changed = True
            if visual_feedback:
                root.after(0, lambda: show_osd(f"language: {current_model_name}"))
            play_beep(1000, 150)
            time.sleep(0.05)
            play_beep(1000, 150)
        popup_is_open = False
        top.destroy()

    combo.bind("<<ComboboxSelected>>", on_select)

    var_checkbox = tk.BooleanVar(value=show_popup)
    
    def on_checkbox_toggle():
        global show_popup
        show_popup = var_checkbox.get()

    chk = ttk.Checkbutton(top, text="Show this menu", variable=var_checkbox, command=on_checkbox_toggle)
    chk.pack(pady=2)

    ToolTip(chk, "If you uncheck the box, the menu will no longer appear.\nYou must restart the script to return.")

    var_visual = tk.BooleanVar(value=visual_feedback)
    
    def on_visual_toggle():
        global visual_feedback
        visual_feedback = var_visual.get()

    chk_visual = ttk.Checkbutton(top, text="Visual feedback", variable=var_visual, command=on_visual_toggle)
    chk_visual.pack(pady=2)

    ToolTip(chk_visual, "Show temporary text windows about the recording state and selected language.")

    top.focus_force()

def trigger_popup():
    root.after(0, popup_selector)

def callback(indata, frames, time_info, status):
    if is_listening:
        q.put(bytes(indata))

def toggle_listening():
    global is_listening
    is_listening = not is_listening
    if is_listening:
        if visual_feedback:
            root.after(0, lambda: show_osd(f"Recording: {current_model_name}"))
        play_beep(1500, 200) 
    else:
        if visual_feedback:
            root.after(0, lambda: show_osd("Recording stopped"))
        play_beep(500, 200)
        with q.mutex:
            q.queue.clear()

def audio_processing():
    global language_changed, current_model, is_listening, q
    rec = KaldiRecognizer(current_model, 16000)
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while True:
            if language_changed:
                rec = KaldiRecognizer(current_model, 16000)
                language_changed = False
                with q.mutex:
                    q.queue.clear()
            
            if not is_listening:
                time.sleep(0.1)
                continue
            
            try:
                data = q.get(timeout=0.1)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text:
                        keyboard.write(text + " ")
            except queue.Empty:
                pass

def key_monitor():
    global current_model_idx, current_model_name, current_model, language_changed
    right_alt_pressed_state = False
    last_release_time = 0
    press_start_time = 0

    while True:
        is_pressed = is_right_alt_pressed()

        if is_pressed and not right_alt_pressed_state:
            right_alt_pressed_state = True
            press_start_time = time.time()
        elif not is_pressed and right_alt_pressed_state:
            right_alt_pressed_state = False
            duration = time.time() - press_start_time
            
            if duration >= 1.0:
                if len(loaded_models) > 1:
                    if show_popup:
                        trigger_popup()
                    else:
                        current_model_idx = (current_model_idx + 1) % len(loaded_models)
                        current_model_name = model_names[current_model_idx]
                        current_model = loaded_models[current_model_name]
                        language_changed = True
                        if visual_feedback:
                            root.after(0, lambda: show_osd(f"language: {current_model_name}"))
                        play_beep(1000, 150)
                        time.sleep(0.05)
                        play_beep(1000, 150)
            else:
                now = time.time()
                if now - last_release_time < 0.4:
                    toggle_listening()
                    last_release_time = 0
                else:
                    last_release_time = now
        time.sleep(0.01)

root = tk.Tk()
root.withdraw()
threading.Thread(target=audio_processing, daemon=True).start()
threading.Thread(target=key_monitor, daemon=True).start()
play_beep(800, 300)
root.mainloop()