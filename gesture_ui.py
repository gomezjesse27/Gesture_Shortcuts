import tkinter as tk
from tkinter import StringVar, OptionMenu
import pyautogui

def launch_ui():
    """Launch the UI for mapping gestures to keys and return the mappings."""
    root = tk.Tk()
    root.title("Gesture-to-Key Mapping")

    # Default gesture mappings
    gesture_mappings = {
        1: 'winleft',  # Default: Windows key
        2: 'tab',      # Default: Tab key
        3: 'enter',    # Default: Enter key
        4: 'space'     # Default: Space key
    }

    # UI variables for each gesture
    mappings_vars = {fingers: StringVar(value=gesture_mappings[fingers]) for fingers in range(1, 5)}

    def save_mappings():
        """Save user-defined mappings."""
        for fingers, var in mappings_vars.items():
            gesture_mappings[fingers] = var.get()
        root.destroy()

    # UI Layout
    tk.Label(root, text="Gesture Mapping", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)

    for fingers in range(1, 5):
        tk.Label(root, text=f"{fingers} Finger(s) Up:", font=("Arial", 12)).grid(row=fingers, column=0, padx=10, pady=5)
        OptionMenu(root, mappings_vars[fingers], *pyautogui.KEYBOARD_KEYS).grid(row=fingers, column=1, padx=10, pady=5)

    tk.Button(root, text="Save & Start", command=save_mappings, font=("Arial", 12)).grid(row=5, column=0, columnspan=2, pady=10)

    root.mainloop()
    return gesture_mappings
