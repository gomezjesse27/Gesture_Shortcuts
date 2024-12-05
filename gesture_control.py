import cv2
import mediapipe as mp
import time
import pyautogui
from gesture_ui import launch_ui
import threading

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize the Hands model
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,  # Detect one hand for simplicity
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Open the webcam
cap = cv2.VideoCapture(0)

# Thread-safe variable for gesture mappings
gesture_mappings_lock = threading.Lock()
gesture_mappings = {}

def update_gesture_mappings():
    """Launch the UI and update the gesture mappings."""
    global gesture_mappings
    new_mappings = launch_ui()
    with gesture_mappings_lock:
        gesture_mappings = new_mappings

# Start by initializing the mappings
update_gesture_mappings()

def count_fingers(hand_landmarks):
    """Counts the number of fingers that are up based on hand landmarks."""
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

# Main Loop Variables
gesture_start_time = None
gesture_text = "No Gesture Detected"
last_fingers_up = -1  # To keep track of the last recognized gesture

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Clear gesture text if no hands detected
    if not results.multi_hand_landmarks:
        gesture_text = ""
        gesture_start_time = None
        last_fingers_up = -1

    # Process detected hands
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

            # If the number of fingers changes, reset timer and update text
            if fingers_up != last_fingers_up:
                last_fingers_up = fingers_up
                gesture_start_time = time.time()
                gesture_text = f"{fingers_up} Finger(s) Up"

                # Map gesture to user-defined key press
                with gesture_mappings_lock:
                    if fingers_up in gesture_mappings:
                        mapping = gesture_mappings[fingers_up]
                        if mapping['type'] == 'single':
                            pyautogui.press(mapping['keys'][0])  # Single key
                        elif mapping['type'] == 'hotkey':
                            pyautogui.hotkey(*mapping['keys'])  # Hotkey

            # Maintain the text for 2 seconds
            if gesture_start_time and time.time() - gesture_start_time >= 2:
                gesture_text = ""

            break  # Process only one hand for simplicity

    # Display text on screen
    if gesture_text:
        cv2.putText(frame, gesture_text, (frame.shape[1] - 300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # Show the frame
    cv2.imshow('Hand Tracking', frame)

    # Check for key inputs
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):  # Quit
        break
    elif key == ord('t'):  # Relaunch the UI
        threading.Thread(target=update_gesture_mappings, daemon=True).start()

cap.release()
cv2.destroyAllWindows()
hands.close()
