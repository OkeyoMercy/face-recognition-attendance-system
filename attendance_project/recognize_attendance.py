import cv2
import face_recognition
import os
import datetime
import numpy as np
import django
import time

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_project.settings')
django.setup()

from attendance_app.models import Student, AttendanceRecord, Timetable

def get_current_session(venue):
    """Find if there is a class currently scheduled in this venue."""
    now = datetime.datetime.now()
    session = Timetable.objects.filter(
        venue=venue,
        day=now.strftime("%A"),
        start_time__lte=now.time(),
        end_time__gte=now.time()
    ).first()
    return session

def get_all_students():
    """Load all registered students with face encodings."""
    students = Student.objects.exclude(face_encoding__isnull=True)
    known_encodings = []
    known_students = []
    for student in students:
        if student.face_encoding:
            try:
                encoding = np.frombuffer(student.face_encoding, dtype=np.float64)
                if len(encoding) == 128:
                    known_encodings.append(encoding)
                    known_students.append(student)
            except:
                pass
    return known_encodings, known_students

def mark_attendance():
    print("--- Multi-Face Attendance Scanner ---")
    venue = input("Enter current venue (TB2, NL5, or LAB3): ").upper()

    known_encodings, known_students = get_all_students()
    if not known_encodings:
        print("❌ No registered students found.")
        return
    print(f"✅ Loaded {len(known_students)} student profiles.")

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("❌ Webcam not detected.")
        return

    face_locations = []
    face_names = []
    face_colors = []
    process_this_frame = 0

    current_session = get_current_session(venue)
    last_session_check = time.time()

    print(f"\n🚀 Scanner ONLINE at {venue}")
    print("Marking all recognized faces. Press 'ESC' to stop.")

    while True:
        # Update session every 30 seconds
        if time.time() - last_session_check > 30:
            current_session = get_current_session(venue)
            last_session_check = time.time()

        ret, frame = video_capture.read()
        if not ret: break

        if process_this_frame % 2 == 0:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = np.ascontiguousarray(small_frame[:, :, ::-1])

            face_locations = face_recognition.face_locations(rgb_small_frame)
            encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            face_colors = []

            for encoding in encodings:
                matches = face_recognition.compare_faces(known_encodings, encoding, tolerance=0.45)
                name, color = "Unknown", (0, 0, 255)

                face_distances = face_recognition.face_distance(known_encodings, encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        student = known_students[best_match_index]

                        if current_session:
                            name, color = f"{student.name}", (0, 255, 0)

                            # Mark Attendance
                            today = datetime.date.today()
                            already_marked = AttendanceRecord.objects.filter(
                                student=student, unit=current_session.unit, date=today
                            ).exists()

                            if not already_marked:
                                AttendanceRecord.objects.create(
                                    student=student,
                                    unit=current_session.unit,
                                    venue=venue,
                                    status="Present"
                                )
                                print(f"✅ [MARKED] {student.name} present for {current_session.unit.code}")
                        else:
                            name, color = f"{student.name} (No Class)", (0, 255, 255)

                face_names.append(name)
                face_colors.append(color)

        process_this_frame += 1

        # Draw results
        for (top, right, bottom, left), name, color in zip(face_locations, face_names, face_colors):
            top *= 4; right *= 4; bottom *= 4; left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        # UI Overlay
        cv2.putText(frame, f"VENUE: {venue} | PRESS 'ESC' TO STOP", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        if current_session:
            cv2.putText(frame, f"SESSION: {current_session.unit.code}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow('Face Attendance System', frame)

        # Check for ESC key (keycode 27)
        if cv2.waitKey(1) & 0xFF == 27:
            print("👋 Stopped by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    mark_attendance()
