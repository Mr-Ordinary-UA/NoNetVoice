import queue
import json
import threading
import time
import os
import sys
import platform
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

loaded_models = []
for root, dirs, files in os.walk(models_dir):
    if "am" in dirs and "conf" in dirs:
        try:
            loaded_models.append(Model(root))
        except Exception:
            pass

if not loaded_models:
    sys.exit()

q = queue.Queue()

current_model_idx = 0
current_model = loaded_models[current_model_idx]
is_listening = False
language_changed = False

def callback(indata, frames, time_info, status):
    if is_listening:
        q.put(bytes(indata))

def toggle_listening():
    global is_listening
    is_listening = not is_listening
    if is_listening:
        play_beep(1500, 200) 
    else:
        play_beep(500, 200)
        with q.mutex:
            q.queue.clear()

def key_monitor():
    global current_model_idx, current_model, language_changed
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
                    current_model_idx = (current_model_idx + 1) % len(loaded_models)
                    current_model = loaded_models[current_model_idx]
                    language_changed = True
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

threading.Thread(target=key_monitor, daemon=True).start()
play_beep(800, 300)

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