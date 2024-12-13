# GestureShortcuts

A Python application that uses a webcam feed and MediaPipe to recognize hand gestures and map them to keyboard shortcuts. This allows users to control their computer using specific gestures, either by simulating single key presses or by sending hotkey combinations.

---

## Features
    
- **Predefined Mappings**: By default, the application recognizes gestures with 1 to 4 fingers up and maps them to certain keyboard keys.
- **Custom Gestures**: Capture and define your own custom gestures and map them to either single keys or hotkey sequences.
- **Graphical UI**: A Tkinter-based GUI allows you to configure and save gesture-to-key mappings easily.
- **Toggle Between UI and Gesture Capture**: Switch between editing gestures and actively using them.

---

## How It Works

### Gesture Recognition

The code uses OpenCV and MediaPipe Hands to detect a single hand in the webcam feed. It then normalizes and compares the hand landmarks to known gestures.

### Default Finger Counting Gestures

The default logic counts how many fingers are extended (ignoring the thumb for simplicity) and maps that number (1-4) to predefined key actions. You can change these mappings in the GUI.

### Custom Gestures

After adding a new gesture through the GUI, the application captures your hand pose and stores it. This stored gesture can then be associated with any key or hotkey combination.

### Key Simulation

Pressing recognized gestures triggers PyAutoGUI commands to simulate keypresses and hotkeys, allowing you to perform common computer actions hands-free.

---

## Requirements

- **Python 3.7 or newer**
- **Mediapipe**
- **OpenCV**
- **Tkinter** (usually included with Python)
- **PyAutoGUI**

Install the required packages using:

```bash
pip install opencv-python mediapipe pyautogui
```
Note: Tkinter comes bundled with most standard Python installations. If it's not available, install it through your system’s package manager.

## Using the GUI

### Set or Modify Gesture Mappings
1. In the GUI window, choose a gesture (1-4 fingers or a custom gesture).
2. Set it to either:
   - **Single:** Press a single key.
   - **Hotkey:** Press multiple keys simultaneously (e.g., `Ctrl+Alt+Delete`).

### Add New Gesture
1. Click **Add Gesture** to enter capture mode.
2. In capture mode:
   - A new window allows you to name the gesture.
   - A live webcam feed displays your hand gesture in real-time.
3. Position your hand in the desired gesture and press **Capture**.

### Save & Start
When done configuring, click **Save & Start** to begin the gesture recognition loop.

---

## Gesture Recognition Loop
- The application shows the live feed with recognized gestures.
- Press `q` to quit the application.
- Press `t` to return to the GUI and adjust settings.

---

## Settings File
- The application stores mappings and custom gestures in a `settings.json` file.
- If the file is deleted, default mappings are restored.

## Setup and run
- After dependency installation simply run
    python NewGesture.py
