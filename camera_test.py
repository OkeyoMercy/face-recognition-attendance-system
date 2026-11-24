import cv2

# Try multiple camera indices
for cam_index in range(3):  # checks 0, 1, 2
    cam = cv2.VideoCapture(cam_index)
    ret, frame = cam.read()
    if ret:
        print(f"Using camera index: {cam_index}")
        break
else:
    print("No camera found!")
    exit()

# Create a resizable window
cv2.namedWindow("Face Detection Test", cv2.WINDOW_NORMAL)

# Load face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame!")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Face Detection Test", frame)

    # Press ESC to exit
    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()
