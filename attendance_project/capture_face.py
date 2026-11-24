import cv2
import face_recognition
import os
import numpy as np
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_project.settings')
django.setup()

from attendance_app.models import Student

def register_student():
    print("--- New Student Registration (Admin Only) ---")
    admin_password = input("Enter Admin Password: ")
    stored_password = os.environ.get("ATTENDANCE_ADMIN_PASSWORD")

    if not stored_password or admin_password != stored_password:
        print("❌ Unauthorized! Incorrect password.")
        return

    name = input("Enter student name: ")
    reg_number = input("Enter registration number: ")
    course = input("Enter course: ")

    # Check if student already exists
    if Student.objects.filter(reg_number=reg_number).exists():
        print("❌ Student with this registration number already exists!")
        return

    # Initialize webcam
    video_capture = cv2.VideoCapture(0)
    print("Opening webcam... Look at the camera and press 'q' to capture your face.")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame from webcam. Exiting...")
            break

        cv2.imshow('Capture Face - Press Q to capture', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            # Convert BGR (OpenCV) to RGB (face_recognition)
            rgb_frame = frame[:, :, ::-1]
            # Resize for faster processing
            rgb_frame = cv2.resize(rgb_frame, (640, 480))
            face_locations = face_recognition.face_locations(rgb_frame)

            if len(face_locations) == 1:
                print("Face detected! Extracting encoding...")
                encoding = face_recognition.face_encodings(rgb_frame, face_locations, num_jitters=0)[0]

                # Convert numpy array to binary for database storage
                encoding_bytes = encoding.tobytes()

                # Save directly to Django DB
                Student.objects.create(
                    name=name,
                    reg_number=reg_number,
                    course=course,
                    face_encoding=encoding_bytes
                )
                print(f"✅ Face captured and {name} registered successfully for course: {course}!")
            else:
                print("❌ No face detected! Please try again.")
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    register_student()
