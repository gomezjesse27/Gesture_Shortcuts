import cv2
import mediapipe as mp

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
    # Define finger tips and base joints (PIP for all except thumb)
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

    # Check the thumb separately (horizontal alignment)
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    thumb_ip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP]
    thumb_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP]
    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

    # Thumb is up if it's to the left/right of the wrist (for flipped view)
    if thumb_tip.x < thumb_ip.x if wrist.x < thumb_mcp.x else thumb_tip.x > thumb_ip.x:
        fingers_up += 1

    # Check each finger
    for tip, pip in zip(finger_tips, finger_pips):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:  # Tip above PIP (finger is up)
            fingers_up += 1

    return fingers_up

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Flip the frame horizontally for a mirror-like view
    frame = cv2.flip(frame, 1)

    # Convert the frame to RGB (MediaPipe works with RGB images)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)
    
    # Default message
    gesture_text = "No Gesture Detected"

    # If hand landmarks are detected
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Draw hand landmarks on the frame
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )

            # Count the number of fingers up
            fingers_up = count_fingers(hand_landmarks)
            
            # Display the number of fingers detected
            gesture_text = f"{fingers_up} Finger(s) Up"

    # Display the recognized gesture at the top-right of the screen
    cv2.putText(frame, gesture_text, (frame.shape[1] - 300, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

    # Display the frame
    cv2.imshow('Hand Tracking', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
hands.close()
