import tkinter as tk
from tkinter import StringVar, OptionMenu, messagebox
import pyautogui
import cv2
import mediapipe as mp
import time
import threading
import json
import os
import math
import copy
import sys

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

default_gesture_mappings = {
    1: {'type': 'single', 'keys': ['winleft']},
    2: {'type': 'single', 'keys': ['tab']},
    3: {'type': 'single', 'keys': ['enter']},
    4: {'type': 'single', 'keys': ['space']}
}

def load_gesture_mappings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            data = json.load(f)
        gesture_mappings = {int(k): v for k, v in data.get("gesture_mappings", default_gesture_mappings).items()}
        custom_gestures = data.get("custom_gestures", {})
        return gesture_mappings, custom_gestures
    else:
        return copy.deepcopy(default_gesture_mappings), {}

def save_gesture_mappings(mappings, custom_gestures):
    data = {
        "gesture_mappings": {str(k): v for k, v in mappings.items()},
        "custom_gestures": custom_gestures
    }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(data, f)

gesture_mappings_lock = threading.Lock()
gesture_mappings, custom_gestures = load_gesture_mappings()

def normalize_landmarks(landmarks):
    coords = [(lm.x, lm.y, lm.z) for lm in landmarks.landmark]
    wrist = coords[0]
    coords = [(x - wrist[0], y - wrist[1], z - wrist[2]) for (x,y,z) in coords]

    max_dist = max(math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)
                    for i,(x1,y1,z1) in enumerate(coords)
                    for j,(x2,y2,z2) in enumerate(coords) if i!=j)
    if max_dist > 0:
        coords = [(x/max_dist, y/max_dist, z/max_dist) for (x,y,z) in coords]
    return coords

def recognize_custom_gesture(landmarks):
    global custom_gestures
    if not custom_gestures:
        return None
    normalized = normalize_landmarks(landmarks)
    best_gesture = None
    best_dist = float('inf')
    for g_name, g_data in custom_gestures.items():
        ref = g_data['landmarks']
        dist_sum = 0
        for (x1,y1,z1),(x2,y2,z2) in zip(normalized, ref):
            dist_sum += math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
        avg_dist = dist_sum / len(normalized)
        if avg_dist < best_dist:
            best_dist = avg_dist
            best_gesture = g_name
    if best_dist < 0.2: # threshold .2 works well
        return best_gesture
    return None

def launch_ui(current_mappings, current_custom):
    root = tk.Tk()
    root.title("Gesture-to-Key Mapping")

    gesture_mappings_local = copy.deepcopy(current_mappings)
    custom_gestures_local = copy.deepcopy(current_custom)

    mapping_type_vars = {}
    single_key_vars = {}
    hotkey_count_vars = {}
    hotkey_vars = {}

    mapping_type_vars_custom = {}
    single_key_vars_custom = {}
    hotkey_count_vars_custom = {}
    hotkey_vars_custom = {}

    def handle_keypress(event, var):
        key = event.keysym
        translated_key = KEY_TRANSLATION_MAP.get(key, key.lower())
        var.set(translated_key)
        return "break"

    def update_hotkey_fields(fingers=None, gesture_name=None):
        if fingers is not None:
            parent_type_vars = mapping_type_vars
            parent_hotkey_vars = hotkey_vars
            parent_hotkey_count = hotkey_count_vars
            gesture_dict = gesture_mappings_local[fingers]
            base_row = fingers * 3
            identifier = fingers
        else:
            parent_type_vars = mapping_type_vars_custom
            parent_hotkey_vars = hotkey_vars_custom
            parent_hotkey_count = hotkey_count_vars_custom
            gesture_dict = custom_gestures_local[gesture_name]
            base_row = custom_start_row + custom_gesture_names.index(gesture_name)*3
            identifier = gesture_name

        for widget in parent_hotkey_vars[identifier]:
            widget.destroy()

        parent_hotkey_vars[identifier] = []
        count = parent_hotkey_count[identifier].get()
        for i in range(count):
            var = tk.StringVar(value='')
            entry = tk.Entry(root, textvariable=var, width=10, font=("Arial", 12))
            entry.grid(row=base_row, column=i + 2, padx=5, pady=5)
            entry.bind('<KeyPress>', lambda event, v=var: handle_keypress(event, v))
            parent_hotkey_vars[identifier].append(entry)

        if gesture_dict['type'] == 'hotkey':
            existing_keys = gesture_dict['keys']
            for i, k in enumerate(existing_keys):
                if i < len(parent_hotkey_vars[identifier]):
                    parent_hotkey_vars[identifier][i].delete(0, tk.END)
                    parent_hotkey_vars[identifier][i].insert(0, k)

    def on_mapping_type_change(*args):
        for fingers in range(1, 5):
            if mapping_type_vars[fingers].get() == 'hotkey':
                update_hotkey_fields(fingers=fingers)
            else:
                for widget in hotkey_vars[fingers]:
                    widget.destroy()
                hotkey_vars[fingers] = []

        for g_name in custom_gesture_names:
            if mapping_type_vars_custom[g_name].get() == 'hotkey':
                update_hotkey_fields(gesture_name=g_name)
            else:
                for widget in hotkey_vars_custom[g_name]:
                    widget.destroy()
                hotkey_vars_custom[g_name] = []

    def save_mappings():
        for fingers in range(1, 5):
            if mapping_type_vars[fingers].get() == 'single':
                gesture_mappings_local[fingers] = {
                    'type': 'single',
                    'keys': [single_key_vars[fingers].get()]
                }
            else:
                keys = [entry.get() for entry in hotkey_vars[fingers] if entry.get()]
                gesture_mappings_local[fingers] = {'type': 'hotkey', 'keys': keys}

        for g_name in custom_gesture_names:
            if mapping_type_vars_custom[g_name].get() == 'single':
                custom_gestures_local[g_name]['type'] = 'single'
                custom_gestures_local[g_name]['keys'] = [single_key_vars_custom[g_name].get()]
            else:
                keys = [entry.get() for entry in hotkey_vars_custom[g_name] if entry.get()]
                custom_gestures_local[g_name]['type'] = 'hotkey'
                custom_gestures_local[g_name]['keys'] = keys

        save_gesture_mappings(gesture_mappings_local, custom_gestures_local)
        root.destroy()
        # After destroying, we go to main capture loop again

    def add_gesture():
        root.destroy()
        # After this window is closed, we capture a new gesture
        global mode
        mode = "capture_gesture"

    def delete_gesture(g_name):
        if messagebox.askyesno("Delete Gesture", f"Are you sure you want to delete gesture '{g_name}'?"):
            del custom_gestures_local[g_name]
            save_gesture_mappings(gesture_mappings_local, custom_gestures_local)
            root.destroy()
            # Relaunch UI
            global mode
            mode = "ui_relaunch"

    tk.Label(root, text="Gesture Mapping", font=("Arial", 14)).grid(row=0, column=0, columnspan=5, pady=10)

    for fingers in range(1, 5):
        mtype = gesture_mappings_local[fingers]['type']
        keys = gesture_mappings_local[fingers]['keys']

        mapping_type_vars[fingers] = tk.StringVar(value=mtype)
        if mtype == 'single':
            single_key = keys[0] if keys else 'space'
        else:
            single_key = keys[0] if keys else 'space'

        single_key_vars[fingers] = tk.StringVar(value=single_key)
        hotkey_count_vars[fingers] = tk.IntVar(value=len(keys) if mtype == 'hotkey' else 1)
        hotkey_vars[fingers] = []

    custom_gesture_names = sorted(custom_gestures_local.keys())
    custom_start_row = 15
    for g_name in custom_gesture_names:
        mtype = custom_gestures_local[g_name]['type']
        keys = custom_gestures_local[g_name]['keys']

        mapping_type_vars_custom[g_name] = tk.StringVar(value=mtype)
        if mtype == 'single':
            single_key = keys[0] if keys else 'space'
        else:
            single_key = keys[0] if keys else 'space'

        single_key_vars_custom[g_name] = tk.StringVar(value=single_key)
        hotkey_count_vars_custom[g_name] = tk.IntVar(value=len(keys) if mtype == 'hotkey' else 1)
        hotkey_vars_custom[g_name] = []

    for fingers in range(1, 5):
        mapping_type_vars[fingers].trace_add("write", on_mapping_type_change)
    for g_name in custom_gesture_names:
        mapping_type_vars_custom[g_name].trace_add("write", on_mapping_type_change)

    for fingers in range(1, 5):
        tk.Label(root, text=f"{fingers} Finger(s) Up:", font=("Arial", 12)).grid(row=fingers * 3 - 2, column=0, padx=10, pady=5)
        tk.OptionMenu(root, mapping_type_vars[fingers], 'single', 'hotkey').grid(row=fingers * 3 - 2, column=1, padx=10)

        single_key_entry = tk.Entry(root, textvariable=single_key_vars[fingers], width=10, font=("Arial", 12))
        single_key_entry.grid(row=fingers * 3 - 2, column=2, padx=10, pady=5)
        single_key_entry.bind('<KeyPress>', lambda event, var=single_key_vars[fingers]: handle_keypress(event, var))

        tk.Label(root, text="Hotkey Count:", font=("Arial", 12)).grid(row=fingers * 3 - 1, column=0, padx=10, pady=5)
        count_selector = tk.Spinbox(root, from_=1, to=10, textvariable=hotkey_count_vars[fingers], width=5,
                                    command=lambda f=fingers: update_hotkey_fields(fingers=f))
        count_selector.grid(row=fingers * 3 - 1, column=1, padx=10, pady=5)

        if gesture_mappings_local[fingers]['type'] == 'hotkey':
            update_hotkey_fields(fingers=fingers)
        else:
            for widget in hotkey_vars[fingers]:
                widget.destroy()
            hotkey_vars[fingers] = []

    offset = 0
    for g_name in custom_gesture_names:
        base_row = custom_start_row + offset*3
        tk.Label(root, text=f"Custom: {g_name}", font=("Arial", 12)).grid(row=base_row-2, column=0, padx=10, pady=5)
        tk.OptionMenu(root, mapping_type_vars_custom[g_name], 'single', 'hotkey').grid(row=base_row-2, column=1, padx=10)

        single_key_entry = tk.Entry(root, textvariable=single_key_vars_custom[g_name], width=10, font=("Arial", 12))
        single_key_entry.grid(row=base_row-2, column=2, padx=10, pady=5)
        single_key_entry.bind('<KeyPress>', lambda event, var=single_key_vars_custom[g_name]: handle_keypress(event, var))

        tk.Label(root, text="Hotkey Count:", font=("Arial", 12)).grid(row=base_row-1, column=0, padx=10, pady=5)
        count_selector = tk.Spinbox(root, from_=1, to=10, textvariable=hotkey_count_vars_custom[g_name], width=5,
                                    command=lambda name=g_name: update_hotkey_fields(gesture_name=name))
        count_selector.grid(row=base_row-1, column=1, padx=10, pady=5)

        del_button = tk.Button(root, text="Delete", command=lambda name=g_name: delete_gesture(name), font=("Arial", 12))
        del_button.grid(row=base_row-1, column=3, padx=10, pady=5)

        if custom_gestures_local[g_name]['type'] == 'hotkey':
            update_hotkey_fields(gesture_name=g_name)
        else:
            for widget in hotkey_vars_custom[g_name]:
                widget.destroy()
            hotkey_vars_custom[g_name] = []
        offset += 1

    tk.Button(root, text="Add Gesture", command=add_gesture, font=("Arial", 12)).grid(row=custom_start_row+offset*3, column=0, columnspan=1, pady=10)
    tk.Button(root, text="Save & Start", command=save_mappings, font=("Arial", 12)).grid(row=custom_start_row+offset*3, column=2, columnspan=2, pady=10)

    root.mainloop()
    return gesture_mappings_local, custom_gestures_local

def start_gesture_capture():
    # Gesture capture mode
    # simple vlocking approach to capture a new gesture as it seems to be a blocking operation
    # open a new window with a text entry for gesture name
    # use OpenCV in another window in a loop - for video
    #  break when capture button is pressed or window closed

    cap = cv2.VideoCapture(0)
    hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    captured_landmarks = [None]
    done = [False]

    def on_closing():
        done[0] = True
        if window.winfo_exists():
            window.destroy()

    def capture_gesture_action():
        if captured_landmarks[0] is not None:
            g_name = name_var.get().strip()
            if not g_name:
                messagebox.showerror("Error", "Please enter a gesture name.")
                return
            if g_name in custom_gestures:
                messagebox.showerror("Error", "Gesture name already exists.")
                return
            custom_gestures[g_name] = {
                'type': 'single',
                'keys': ['space'],
                'landmarks': normalize_landmarks(captured_landmarks[0])
            }
            save_gesture_mappings(gesture_mappings, custom_gestures)
            done[0] = True
            if window.winfo_exists():
                window.destroy()
        else:
            messagebox.showerror("Error", "No hand detected. Please ensure a hand is visible.")

    window = tk.Tk()
    window.title("Add New Gesture")

    tk.Label(window, text="Enter Gesture Name:").pack(pady=5)
    name_var = tk.StringVar()
    tk.Entry(window, textvariable=name_var).pack(pady=5)

    capture_button = tk.Button(window, text="Capture", command=capture_gesture_action)
    capture_button.pack(pady=10)

    window.protocol("WM_DELETE_WINDOW", on_closing)

    def loop_capture():
        if done[0]:
            return
        ret, frame = cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp.solutions.drawing_utils.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp.solutions.hands.HAND_CONNECTIONS,
                        mp.solutions.drawing_utils.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                        mp.solutions.drawing_utils.DrawingSpec(color=(0, 0, 255), thickness=2)
                    )
                    captured_landmarks[0] = hand_landmarks
                    break
            cv2.imshow("Capture Gesture", frame)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                on_closing()
        if not done[0]:
            window.after(30, loop_capture)

    loop_capture()
    window.mainloop()

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

def count_fingers(hand_landmarks):
    finger_tips = [
        mp.solutions.hands.HandLandmark.INDEX_FINGER_TIP,
        mp.solutions.hands.HandLandmark.MIDDLE_FINGER_TIP,
        mp.solutions.hands.HandLandmark.RING_FINGER_TIP,
        mp.solutions.hands.HandLandmark.PINKY_TIP
    ]
    finger_pips = [
        mp.solutions.hands.HandLandmark.INDEX_FINGER_PIP,
        mp.solutions.hands.HandLandmark.MIDDLE_FINGER_PIP,
        mp.solutions.hands.HandLandmark.RING_FINGER_PIP,
        mp.solutions.hands.HandLandmark.PINKY_PIP
    ]

    fingers_up = 0
    """thumb_tip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP]
    thumb_ip = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_IP]
    thumb_mcp = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_MCP]
    wrist = hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST]

    # Check thumb
    if thumb_tip.x < thumb_ip.x if wrist.x < thumb_mcp.x else thumb_tip.x > thumb_ip.x:
        fingers_up += 1"""

    # Check other fingers
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            fingers_up += 1

    return fingers_up

def main_capture_loop():
    global gesture_mappings, custom_gestures

    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils

    hands = mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(0)
    gesture_start_time = None
    gesture_text = "No Gesture Detected"
    Instruction = "Press 'q' to quit, 't' to go back to UI"
    last_fingers_up = -1

    COOLDOWN_TIME = 2.0
    last_recognition_time = 0.0

    while cap.isOpened():
        global mode
        if mode != "capture":
            break

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        detected_gesture = None

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
                # Try to recognize custom gestures
                custom_g = recognize_custom_gesture(hand_landmarks)
                if custom_g:
                    detected_gesture = custom_g
                else:
                    detected_gesture = fingers_up

                current_time = time.time()

                if detected_gesture != last_fingers_up and (current_time - last_recognition_time) >= COOLDOWN_TIME:
                    last_fingers_up = detected_gesture
                    gesture_start_time = current_time
                    if isinstance(detected_gesture, int):
                        gesture_text = f"{detected_gesture} Finger(s) Up"
                    else:
                        gesture_text = f"Custom: {detected_gesture}"
                    last_recognition_time = current_time

                    with gesture_mappings_lock:
                        if isinstance(detected_gesture, int) and detected_gesture in gesture_mappings:
                            mapping = gesture_mappings[detected_gesture]
                            if mapping['type'] == 'single':
                                pyautogui.press(mapping['keys'][0])
                            elif mapping['type'] == 'hotkey':
                                pyautogui.hotkey(*mapping['keys'])
                        elif isinstance(detected_gesture, str) and detected_gesture in custom_gestures:
                            mapping = custom_gestures[detected_gesture]
                            if mapping['type'] == 'single':
                                pyautogui.press(mapping['keys'][0])
                            elif mapping['type'] == 'hotkey':
                                pyautogui.hotkey(*mapping['keys'])

                if gesture_start_time and current_time - gesture_start_time >= 2:
                    gesture_text = ""

                break
        else:
            gesture_text = ""
            gesture_start_time = None
            last_fingers_up = -1

        if gesture_text:
            cv2.putText(frame, gesture_text, (frame.shape[1] - 300, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
        cv2.putText(frame, Instruction, (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        cv2.imshow('Hand Tracking', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            mode = "exit"
            break
        elif key == ord('t'):
            # Switch to UI mode
            mode = "ui_relaunch"
            break

    cap.release()
    cv2.destroyAllWindows()
    hands.close()

def run():
    global gesture_mappings, custom_gestures, mode
    mode = "ui_relaunch"  # start with UI

    while True:
        if mode == "ui_relaunch":
            # Relaunch UI
            mode = None
            gesture_mappings_local, custom_gestures_local = launch_ui(gesture_mappings, custom_gestures)
            with gesture_mappings_lock:
                gesture_mappings = gesture_mappings_local
                custom_gestures = custom_gestures_local
            if mode is None:
                # If no mode changed, means Save & Start pressed
                mode = "capture"
        elif mode == "capture_gesture":
            # Capture a new gesture
            mode = None
            start_gesture_capture()
            # After capturing a gesture, go back to UI
            mode = "ui_relaunch"
        elif mode == "capture":
            # Start capturing gestures
            main_capture_loop()
            if mode == "exit":
                break
            # if loop ends with ui_relaunch or capture_gesture, continue loop
        elif mode == "exit":
            break
        else:
            # If none of the above, break to avoid infinite loops
            break

if __name__ == "__main__":
    run()
