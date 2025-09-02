import os
import ctypes
from cvzone.HandTrackingModule import HandDetector
import cv2
import numpy as np
import tkinter as tk
from threading import Thread
import speech_recognition as sr
from queue import Queue
from time import sleep


folderPath = "Presentation"

# GUI Application for displaying transcription
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.start_listening()

    def create_widgets(self):
        self.text_display = tk.Text(self, wrap=tk.WORD)
        self.text_display.pack(fill=tk.BOTH, expand=True)

    def start_listening(self):
        # Dummy function to demonstrate starting some functionality
        pass

# Speech Recognition setup
def audio_processing_thread(app):
    energy_threshold = 400
    record_timeout = 1.0

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = energy_threshold
    recognizer.dynamic_energy_threshold = False
    microphone = sr.Microphone(sample_rate=16000)

    def record_callback(_, audio: sr.AudioData):
        try:
            text = recognizer.recognize_google(audio)
            app.text_display.delete(1.0, tk.END)
            app.text_display.insert(tk.END, text)
            app.text_display.update()
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
        except sr.RequestError as e:
            print("Could not request results from Speech Recognition service; {0}".format(e))

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)

    recognizer.listen_in_background(microphone, record_callback, phrase_time_limit=record_timeout)

    while True:
        # Keep the thread running
        sleep(1)

# Function to resize the image to match the screen size
def resizeToFitScreen(img, screen_width, screen_height):
    aspect_ratio = screen_width / screen_height
    img_aspect_ratio = img.shape[1] / img.shape[0]

    if img_aspect_ratio > aspect_ratio:
        # Image is wider than the screen
        new_height = int(screen_width / img_aspect_ratio)
        resized_img = cv2.resize(img, (screen_width, new_height))
    else:
        # Image is taller than the screen
        new_width = int(screen_height * img_aspect_ratio)
        resized_img = cv2.resize(img, (new_width, screen_height))

    return resized_img


def zoomImage(img, zoom_factor):
    center_x, center_y = img.shape[1] // 2, img.shape[0] // 2
    radius_x, radius_y = int(center_x / zoom_factor), int(center_y / zoom_factor)
    cropped = img[center_y - radius_y:center_y + radius_y, center_x - radius_x:center_x + radius_x]
    resized = cv2.resize(cropped, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    return resized

# Hand gesture thread
def hand_gesture_thread():
    # Camera Setup
    # Parameters
    # Detect current screen resolution for fullscreen rendering
    try:
        user32 = ctypes.windll.user32
        screen_w = int(user32.GetSystemMetrics(0))
        screen_h = int(user32.GetSystemMetrics(1))
    except Exception:
        screen_w, screen_h = 1280, 720

    width, height = screen_w, screen_h
    gestureThreshold = 300
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(3, width)
    cap.set(4, height)
    cap.set(5, 30)  # FPS target
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass

    # Hand Detector
    detectorHand = HandDetector(detectionCon=0.8, maxHands=2)

    # Variables
    delay = 30
    buttonPressed = False
    counter = 0
    imgNumber = 0
    annotations = [[]]
    annotationNumber = -1
    annotationStart = False
    startDist = None
    currentZoom = 1
    hs, ws = int(120 * 1), int(213 * 1)  # width and height of small image

    # Get list of presentation images and cache resized slides in memory
    pathImages = sorted(os.listdir(folderPath), key=len)
    slides = []
    for imgName in pathImages:
        pathFullImage = os.path.join(folderPath, imgName)
        imgOriginal = cv2.imread(pathFullImage)
        if imgOriginal is None:
            continue
        imgOriginal = resizeToFitScreen(imgOriginal, width, height)
        slides.append(imgOriginal)
    if not slides:
        print("No slides found in Presentation folder.")
        return

    # Prepare fullscreen window for slides
    cv2.namedWindow("Slides", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Slides", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        # Get image frame
        success, frame = cap.read()
        if not success:
            continue
        frame = cv2.flip(frame, 1)

        imgCurrentOriginal = slides[imgNumber]
        imgCurrent = zoomImage(imgCurrentOriginal, currentZoom)

        # Run hand detection on a downscaled frame for speed
        det_scale = 0.5
        det_w, det_h = int(imgCurrent.shape[1] * det_scale), int(imgCurrent.shape[0] * det_scale)
        det_frame = cv2.resize(frame, (det_w, det_h))

        hands, det_vis = detectorHand.findHands(det_frame, draw=True)
        cv2.line(det_vis, (0, int(gestureThreshold * det_scale)), (det_w, int(gestureThreshold * det_scale)), (0, 255, 0), 4)

        if len(hands) == 2:
            hand1 = hands[0]
            hand2 = hands[1]
            if startDist is None:
                startDist = np.linalg.norm(np.array(hand1['center']) - np.array(hand2['center']))
            else:
                currentDist = np.linalg.norm(np.array(hand1['center']) - np.array(hand2['center']))
                if currentDist > startDist + 50:
                    currentZoom += 0.1  # Zoom in
                    if currentZoom > 3:  # Max zoom limit
                        currentZoom = 3
                    imgCurrent = zoomImage(imgCurrentOriginal, currentZoom)                  
                    startDist = currentDist
                elif currentDist < startDist - 50:
                    currentZoom -= 0.1  # Zoom out
                    if currentZoom < 1:  # Min zoom limit
                        currentZoom = 1
                    imgCurrent = zoomImage(imgCurrentOriginal, currentZoom)                   
                    startDist = currentDist
        else:
            startDist = None  # Reset when not in zoom gesture

        # Processing single hand gestures
        if len(hands) == 1 and buttonPressed is False:
            hand = hands[0]
            # Determine fingers state on detection-scale hand object
            fingers = detectorHand.fingersUp(hand)
            # Scale coordinates back to presentation image space
            cx_det, cy_det = hand["center"]
            cx, cy = int(cx_det / det_scale), int(cy_det / det_scale)
            lmList_det = hand["lmList"]
            lmList = [[int(pt[0] / det_scale), int(pt[1] / det_scale)] for pt in lmList_det]

            # Constrain values for easier drawing
            xVal = int(np.interp(lmList[8][0], [0, width], [0, 2000]))
            yVal = int(np.interp(lmList[8][1], [0, height], [0, 1500]))
            indexFinger = xVal, yVal

            if cy <= gestureThreshold:  # If hand is at the height of the face
                if fingers == [1, 0, 0, 0, 0]:
                    print("Left")
                    buttonPressed = True
                    if imgNumber > 0:
                        imgNumber -= 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = False
                if fingers == [0, 0, 0, 0, 1]:
                    print("Right")
                    buttonPressed = True
                    if imgNumber < len(pathImages) - 1:
                        imgNumber += 1
                        annotations = [[]]
                        annotationNumber = -1
                        annotationStart = False

            if fingers == [0, 1, 1, 0, 0]:
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)

            if fingers == [0, 1, 0, 0, 0]:
                if annotationStart is False:
                    annotationStart = True
                    annotationNumber += 1
                    annotations.append([])
                print(annotationNumber)
                annotations[annotationNumber].append(indexFinger)
                cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)

            else:
                annotationStart = False

            if fingers == [0, 1, 1, 1, 0]:
                if annotations:
                    annotations.pop(-1)
                    annotationNumber -= 1
                    buttonPressed = True

        else:
            annotationStart = False

        if buttonPressed:
            counter += 1
            if counter > delay:
                counter = 0
                buttonPressed = False

        for i, annotation in enumerate(annotations):
            for j in range(len(annotation)):
                if j != 0:
                    cv2.line(imgCurrent, annotation[j - 1], annotation[j], (0, 0, 200), 12)

        # Embed webcam thumbnail overlay at top-right of the slide with detection overlay
        imgSmall = cv2.resize(det_vis, (ws, hs))
        h, w, _ = imgCurrent.shape
        imgCurrent[0:hs, w - ws: w] = imgSmall

        cv2.imshow("Slides", imgCurrent)

        key = cv2.waitKey(1)
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# Main function to coordinate threads
def main():
    root = tk.Tk()
    app = Application(master=root)
    Thread(target=audio_processing_thread, args=(app,)).start()
    Thread(target=hand_gesture_thread).start()
    app.mainloop()

if __name__ == "__main__":
    data_queue = Queue()
    main()
