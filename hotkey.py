import keyboard

def listen_hotkey(callback, key="ctrl+alt+p"):
    keyboard.add_hotkey(key, callback)
