import cv2
import face_recognition
import os
import django
import sys

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_project.settings')
django.setup()

from attendance_app.models import Student

def bulk_register_from_photos(photo_dir="student_photos"):
    print(f"--- Bulk Registration from '{photo_dir}' ---")

    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
        print(f"📁 Created directory '{photo_dir}'.")
        print("Please place student photos in this directory named as:")
        print("Format: 'FirstName LastName_RegNumber_CourseName.jpg'")
        print("Example: 'John Doe_CS101_Computer Science.jpg'")
        return

    files = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not files:
        print(f"❌ No photos found in '{photo_dir}'. Please add some photos and run again.")
        return

    for filename in files:
        filepath = os.path.join(photo_dir, filename)
        name_no_ext = os.path.splitext(filename)[0]

        try:
            name, reg_number, course = name_no_ext.split("_")
        except ValueError:
            print(f"⚠️ Skipping '{filename}': Invalid name format. Use 'Name_RegNum_Course.jpg'")
            continue

        if Student.objects.filter(reg_number=reg_number).exists():
            print(f"⏭️ Skipping {name}: Registration number {reg_number} already exists.")
            continue

        print(f"📷 Processing photo for {name} ({reg_number})...")
        image = face_recognition.load_image_file(filepath)
        # Resize for faster processing
        image = cv2.resize(image, (640, 480))
        face_locations = face_recognition.face_locations(image)

        if len(face_locations) == 1:
            encoding = face_recognition.face_encodings(image, face_locations, num_jitters=0)[0]
            encoding_bytes = encoding.tobytes()

            Student.objects.create(
                name=name.replace("-", " "),
                reg_number=reg_number,
                course=course.replace("-", " "),
                face_encoding=encoding_bytes
            )
            print(f"✅ Successfully registered {name}!")
        elif len(face_locations) > 1:
            print(f"❌ Skipping {name}: Multiple faces detected in the photo.")
        else:
            print(f"❌ Skipping {name}: No faces detected in the photo.")

if __name__ == "__main__":
    pwd = input("Enter admin password: ")
    stored_password = os.environ.get("ATTENDANCE_ADMIN_PASSWORD")

    if stored_password and pwd == stored_password:
        bulk_register_from_photos()
    else:
        print("❌ Unauthorized! Incorrect admin password.")