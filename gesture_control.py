import cv2
import mediapipe as mp
import time
import pyautogui
from gesture_ui import launch_ui

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

# Get user-defined mappings from the UI
gesture_mappings = launch_ui()

# Main Loop Variables
gesture_start_time = None
gesture_recognized = False
cooldown_active = False

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    gesture_text = "No Gesture Detected"

    if results.multi_hand_landmarks and not cooldown_active:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )

            fingers_up = count_fingers(hand_landmarks)

            if not gesture_recognized:
                if gesture_start_time is None:
                    gesture_start_time = time.time()

                elif time.time() - gesture_start_time >= 1:
                    gesture_text = f"{fingers_up} Finger(s) Up"
                    print("Gesture recognized:", gesture_text)

                    # Map gesture to user-defined key press
                    if fingers_up in gesture_mappings:
                        mapping = gesture_mappings[fingers_up]
                        if mapping['type'] == 'single':
                            pyautogui.press(mapping['keys'][0])  # Single key
                            print(f"Pressing single key: {mapping['keys'][0]}")
                        elif mapping['type'] == 'hotkey':
                            pyautogui.hotkey(*mapping['keys'])  # Hotkey
                            print(f"Pressing hotkey: {'+'.join(mapping['keys'])}")


                    gesture_recognized = True
                    cooldown_active = True
                    gesture_start_time = None

            break

    else:
        gesture_start_time = None
        if gesture_recognized:
            gesture_text = "Gesture Recognized. Remove Hand to Reset"
            cooldown_active = False
            gesture_recognized = False

    cv2.putText(frame, gesture_text, (frame.shape[1] - 300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
    cv2.imshow('Hand Tracking', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
hands.close()
