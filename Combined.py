import tkinter as tk
from tkinter import StringVar, OptionMenu
import pyautogui
import cv2
import mediapipe as mp
import time
import threading
import json
import os

SETTINGS_FILE = "settings.json"

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
    **{chr(i): chr(i).lower() for i in range(65, 91)},  # A-Z
    **{str(i): str(i) for i in range(10)}              # 0-9
}

def load_gesture_mappings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
        # Convert keys back to int
        gesture_mappings = {int(k): v for k, v in data.items()}
        return gesture_mappings
    else:
        return {
            1: {'type': 'single', 'keys': ['winleft']},
            2: {'type': 'single', 'keys': ['tab']},
            3: {'type': 'single', 'keys': ['enter']},
            4: {'type': 'single', 'keys': ['space']}
        }

def save_gesture_mappings(mappings):
    # Convert keys to strings before saving
    data = {str(k): v for k, v in mappings.items()}
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f)

def launch_ui(current_mappings):
    """Launch the UI for mapping gestures to keys or hotkeys and return the mappings."""
    root = tk.Tk()
    root.title("Gesture-to-Key Mapping")

    # Use existing mappings as defaults
    gesture_mappings = current_mappings.copy()

    mapping_type_vars = {}
    single_key_vars = {}
    hotkey_count_vars = {}
    hotkey_vars = {}

    for fingers in range(1, 5):
        mtype = gesture_mappings[fingers]['type']
        keys = gesture_mappings[fingers]['keys']

        mapping_type_vars[fingers] = tk.StringVar(value=mtype)
        if mtype == 'single':
            single_key = keys[0] if keys else 'space'
        else:
            single_key = keys[0] if keys else 'space'

        single_key_vars[fingers] = tk.StringVar(value=single_key)
        hotkey_count_vars[fingers] = tk.IntVar(value=len(keys) if mtype == 'hotkey' else 1)
        hotkey_vars[fingers] = []

    def handle_keypress(event, var):
        key = event.keysym
        translated_key = KEY_TRANSLATION_MAP.get(key, key.lower())
        var.set(translated_key)
        return "break"

    def update_hotkey_fields(fingers):
        for widget in hotkey_vars[fingers]:
            widget.destroy()

        hotkey_vars[fingers] = []
        count = hotkey_count_vars[fingers].get()
        for i in range(count):
            var = tk.StringVar(value='')
            entry = tk.Entry(root, textvariable=var, width=10, font=("Arial", 12))
            entry.grid(row=fingers * 3, column=i + 2, padx=5, pady=5)
            entry.bind('<KeyPress>', lambda event, v=var: handle_keypress(event, v))
            hotkey_vars[fingers].append(entry)

        if gesture_mappings[fingers]['type'] == 'hotkey':
            existing_keys = gesture_mappings[fingers]['keys']
            for i, k in enumerate(existing_keys):
                if i < len(hotkey_vars[fingers]):
                    hotkey_vars[fingers][i].delete(0, tk.END)
                    hotkey_vars[fingers][i].insert(0, k)

    def on_mapping_type_change(*args):
        for fingers in range(1, 5):
            if mapping_type_vars[fingers].get() == 'hotkey':
                update_hotkey_fields(fingers)
            else:
                for widget in hotkey_vars[fingers]:
                    widget.destroy()
                hotkey_vars[fingers] = []

    def save_mappings():
        for fingers in range(1, 5):
            if mapping_type_vars[fingers].get() == 'single':
                gesture_mappings[fingers] = {
                    'type': 'single',
                    'keys': [single_key_vars[fingers].get()]
                }
            else:
                keys = [entry.get() for entry in hotkey_vars[fingers] if entry.get()]
                gesture_mappings[fingers] = {'type': 'hotkey', 'keys': keys}
        save_gesture_mappings(gesture_mappings)
        root.destroy()

    tk.Label(root, text="Gesture Mapping", font=("Arial", 14)).grid(row=0, column=0, columnspan=5, pady=10)

    for fingers in range(1, 5):
        mapping_type_vars[fingers].trace_add("write", on_mapping_type_change)

    for fingers in range(1, 5):
        tk.Label(root, text=f"{fingers} Finger(s) Up:", font=("Arial", 12)).grid(row=fingers * 3 - 2, column=0, padx=10, pady=5)
        tk.OptionMenu(root, mapping_type_vars[fingers], 'single', 'hotkey').grid(row=fingers * 3 - 2, column=1, padx=10)

        single_key_entry = tk.Entry(root, textvariable=single_key_vars[fingers], width=10, font=("Arial", 12))
        single_key_entry.grid(row=fingers * 3 - 2, column=2, padx=10, pady=5)
        single_key_entry.bind('<KeyPress>', lambda event, var=single_key_vars[fingers]: handle_keypress(event, var))

        tk.Label(root, text="Hotkey Count:", font=("Arial", 12)).grid(row=fingers * 3 - 1, column=0, padx=10, pady=5)
        count_selector = tk.Spinbox(root, from_=1, to=10, textvariable=hotkey_count_vars[fingers], width=5,
                                    command=lambda f=fingers: update_hotkey_fields(f))
        count_selector.grid(row=fingers * 3 - 1, column=1, padx=10, pady=5)

        if gesture_mappings[fingers]['type'] == 'hotkey':
            update_hotkey_fields(fingers)
        else:
            for widget in hotkey_vars[fingers]:
                widget.destroy()
            hotkey_vars[fingers] = []

    tk.Button(root, text="Save & Start", command=save_mappings, font=("Arial", 12)).grid(row=15, column=0, columnspan=5, pady=10)

    root.mainloop()
    return gesture_mappings

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

gesture_mappings_lock = threading.Lock()
gesture_mappings = load_gesture_mappings()

def update_gesture_mappings():
    global gesture_mappings
    with gesture_mappings_lock:
        current_mappings = gesture_mappings
    new_mappings = launch_ui(current_mappings)
    with gesture_mappings_lock:
        gesture_mappings = new_mappings

def count_fingers(hand_landmarks):
    finger_tips = [
        mp_hands.HandLandmark.INDEX_FINGER_TIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp_hands.HandLandmark.RING_FINGER_TIP,
        mp_hands.HandLandmark.PINKY_TIP
    ]
    finger_pips = [
        mp_hands.HandLandmark.INDEX_FINGER_PIP,
        mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp_hands.HandLandmark.RING_FINGER_PIP,
        mp_hands.HandLandmark.PINKY_PIP
    ]

    fingers_up = 0
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
    thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

    # Check thumb
    if thumb_tip.x < thumb_ip.x if wrist.x < thumb_mcp.x else thumb_tip.x > thumb_ip.x:
        fingers_up += 1

    # Check other fingers
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1

    return fingers_up

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)

gesture_start_time = None
gesture_text = "No Gesture Detected"
last_fingers_up = -1

# Introduce a cooldown time (in seconds)
COOLDOWN_TIME = 2.0
last_recognition_time = 0.0  # Time when we last recognized a gesture

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    if not results.multi_hand_landmarks:
        gesture_text = ""
        gesture_start_time = None
        last_fingers_up = -1

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )

            fingers_up = count_fingers(hand_landmarks)

            current_time = time.time()

            # Only recognize a new gesture if cooldown has passed
            if fingers_up != last_fingers_up and (current_time - last_recognition_time) >= COOLDOWN_TIME:
                last_fingers_up = fingers_up
                gesture_start_time = current_time
                gesture_text = f"{fingers_up} Finger(s) Up"
                last_recognition_time = current_time  # Update the last recognition time

                with gesture_mappings_lock:
                    if fingers_up in gesture_mappings:
                        mapping = gesture_mappings[fingers_up]
                        if mapping['type'] == 'single':
                            pyautogui.press(mapping['keys'][0])
                        elif mapping['type'] == 'hotkey':
                            pyautogui.hotkey(*mapping['keys'])

            if gesture_start_time and current_time - gesture_start_time >= 2:
                gesture_text = ""

            break

    if gesture_text:
        cv2.putText(frame, gesture_text, (frame.shape[1] - 300, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    cv2.imshow('Hand Tracking', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('t'):
        threading.Thread(target=update_gesture_mappings, daemon=True).start()

cap.release()
cv2.destroyAllWindows()
hands.close()
