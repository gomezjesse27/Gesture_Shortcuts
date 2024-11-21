import tkinter as tk
from tkinter import StringVar, OptionMenu
import pyautogui


KEY_TRANSLATION_MAP = {
    'Win_L': 'winleft',
    'Control_L': 'ctrl',
    'Shift_L': 'shift',
    'Alt_L': 'alt',
    'Win_R': 'winright',
    'Control_R': 'ctrl',
    'Shift_R': 'shift',
    'Alt_R': 'alt',
    'Return': 'enter',
    'Space': 'space',
    'Tab': 'tab',
    'BackSpace': 'backspace',
    'Delete': 'delete',
    'Escape': 'esc',
    'Up': 'up',
    'Down': 'down',
    'Left': 'left',
    'Right': 'right',
    'Caps_Lock': 'capslock',
    'Page_Up': 'pageup',
    'Page_Down': 'pagedown',
    'Home': 'home',
    'End': 'end',
    'Insert': 'insert',
    'Num_Lock': 'numlock',
    'Print': 'printscreen',
    'Pause': 'pause',
    'F1': 'f1',
    'F2': 'f2',
    'F3': 'f3',
    'F4': 'f4',
    'F5': 'f5',
    'F6': 'f6',
    'F7': 'f7',
    'F8': 'f8',
    'F9': 'f9',
    'F10': 'f10',
    'F11': 'f11',
    'F12': 'f12',
    # Add letters and numbers
    **{chr(i): chr(i).lower() for i in range(65, 91)},  # A-Z
    **{str(i): str(i) for i in range(10)}              # 0-9
}

def launch_ui():
    """Launch the UI for mapping gestures to keys or hotkeys and return the mappings."""
    root = tk.Tk()
    root.title("Gesture-to-Key Mapping")

    # Default gesture mappings
    gesture_mappings = {
        1: {'type': 'single', 'keys': ['winleft']},
        2: {'type': 'single', 'keys': ['tab']},
        3: {'type': 'single', 'keys': ['enter']},
        4: {'type': 'single', 'keys': ['space']}
    }

    # UI variables
    mapping_type_vars = {fingers: tk.StringVar(value='single') for fingers in range(1, 5)}
    single_key_vars = {fingers: tk.StringVar(value=gesture_mappings[fingers]['keys'][0]) for fingers in range(1, 5)}
    hotkey_count_vars = {fingers: tk.IntVar(value=1) for fingers in range(1, 5)}
    hotkey_vars = {fingers: [] for fingers in range(1, 5)}

    def handle_keypress(event, var):
        """Set the value of the entry box based on the key pressed."""
        key = event.keysym
        translated_key = KEY_TRANSLATION_MAP.get(key, key.lower())
        var.set(translated_key)
        return "break"  #prevent propagation of the event


    def update_hotkey_fields(fingers):
        """Update hotkey entry boxes based on the selected number of keys."""
        for widget in hotkey_vars[fingers]:
            widget.destroy()  # Clear previous fields

        hotkey_vars[fingers] = []  # Reset the list
        count = hotkey_count_vars[fingers].get()
        for i in range(count):
            var = tk.StringVar(value='')
            entry = tk.Entry(root, textvariable=var, width=10, font=("Arial", 12))
            entry.grid(row=fingers * 3, column=i + 2, padx=5, pady=5)
            entry.bind('<KeyPress>', lambda event, v=var: handle_keypress(event, v))  # Capture keypresses
            hotkey_vars[fingers].append(entry)

    def save_mappings():
        """Save user-defined mappings."""
        for fingers in range(1, 5):
            if mapping_type_vars[fingers].get() == 'single':
                gesture_mappings[fingers] = {
                    'type': 'single',
                    'keys': [single_key_vars[fingers].get()]
                }
            else:
                keys = [entry.get() for entry in hotkey_vars[fingers] if entry.get()]
                gesture_mappings[fingers] = {'type': 'hotkey', 'keys': keys}
        root.destroy()

    # UI Layout
    tk.Label(root, text="Gesture Mapping", font=("Arial", 14)).grid(row=0, column=0, columnspan=5, pady=10)

    for fingers in range(1, 5):
        tk.Label(root, text=f"{fingers} Finger(s) Up:", font=("Arial", 12)).grid(row=fingers * 3 - 2, column=0, padx=10, pady=5)

        # Single key or hotkey option
        tk.OptionMenu(root, mapping_type_vars[fingers], 'single', 'hotkey').grid(row=fingers * 3 - 2, column=1, padx=10)

        # Single key input
        single_key_entry = tk.Entry(root, textvariable=single_key_vars[fingers], width=10, font=("Arial", 12))
        single_key_entry.grid(row=fingers * 3 - 2, column=2, padx=10, pady=5)
        single_key_entry.bind('<KeyPress>', lambda event, var=single_key_vars[fingers]: handle_keypress(event, var))

        # Hotkey fields 
        tk.Label(root, text="Hotkey Count:", font=("Arial", 12)).grid(row=fingers * 3 - 1, column=0, padx=10, pady=5)
        count_selector = tk.Spinbox(root, from_=1, to=10, textvariable=hotkey_count_vars[fingers], width=5,
                                    command=lambda f=fingers: update_hotkey_fields(f))
        count_selector.grid(row=fingers * 3 - 1, column=1, padx=10, pady=5)

        update_hotkey_fields(fingers)  # Initialize hotkey fields

    tk.Button(root, text="Save & Start", command=save_mappings, font=("Arial", 12)).grid(row=15, column=0, columnspan=5, pady=10)

    root.mainloop()
    return gesture_mappings
